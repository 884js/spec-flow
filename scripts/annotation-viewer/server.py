#!/usr/bin/env python3
"""Annotation Viewer — Local HTTP server for plan review.

Serves plan content from SQLite DB as rendered Markdown with a comment UI.
Supports multiple plans with tab-based navigation.
Uses only Python 3 standard library.
"""

import base64
import http.server
import json
import os
import re
import signal
import socket
import sqlite3
import sys
import threading
import urllib.request
from pathlib import Path

DEFAULT_PORT = 19840
MAX_PORT_ATTEMPTS = 10
IDLE_TIMEOUT = int(os.environ.get("IDLE_TIMEOUT", 7200))  # 2 hours default
LOCK_FILE = "/tmp/annotation-viewer.lock"
DB_PATH = os.path.expanduser("~/.claude/spec-flow.db")
SIGNAL_DIR = "/tmp/spec-flow-review"

# Global timer for activity-based timeout reset
_timer = None
_timer_lock = threading.Lock()
_server_ref = None


def find_available_port():
    """Try fixed ports 19840-19849, return first available."""
    for port in range(DEFAULT_PORT, DEFAULT_PORT + MAX_PORT_ATTEMPTS):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    print("Error: All ports 19840-19849 are in use", file=sys.stderr)
    sys.exit(1)


def is_server_running(port):
    """Check if a server is responding on the given port."""
    try:
        url = f"http://127.0.0.1:{port}/api/plans"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except Exception:
        return False


def register_plan_remote(port, feature):
    """Register a plan with an already-running server."""
    url = f"http://127.0.0.1:{port}/api/plans/register"
    data = json.dumps({"feature": feature}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def reset_timeout():
    """Reset the idle auto-shutdown timer on activity."""
    global _timer
    with _timer_lock:
        if _timer is not None:
            _timer.cancel()
        if _server_ref is not None:
            _timer = threading.Timer(IDLE_TIMEOUT, _shutdown_server)
            _timer.daemon = True
            _timer.start()


def _shutdown_server():
    """Gracefully shutdown the server."""
    if _server_ref is not None:
        remove_lock_file()
        _server_ref.shutdown()


def get_db():
    """Get a thread-local DB connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def resolve_project_id(conn):
    """Resolve project_id from cwd."""
    project_name = os.path.basename(os.getcwd())
    row = conn.execute(
        "SELECT id FROM projects WHERE name = ?", (project_name,)
    ).fetchone()
    if row:
        return row["id"]
    # Auto-register
    cur = conn.execute(
        "INSERT INTO projects (name, path) VALUES (?, ?) RETURNING id",
        (project_name, os.getcwd()),
    )
    conn.commit()
    return cur.fetchone()[0]


# Shared plan registry: set of feature-names
plan_registry: set[str] = set()
registry_lock = threading.Lock()


class AnnotationHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        reset_timeout()
        if self.path == "/":
            self._serve_viewer()
        elif self.path == "/api/plans":
            self._serve_plan_list()
        elif m := re.match(r"^/api/plans/([^/]+)/plan$", self.path):
            self._serve_plan(m.group(1))
        elif m := re.match(r"^/api/plans/([^/]+)/status$", self.path):
            self._serve_plan_status(m.group(1))
        elif m := re.match(r"^/api/plans/([^/]+)/review-status$", self.path):
            self._serve_review_status(m.group(1))
        else:
            self.send_error(404)

    def do_POST(self):
        reset_timeout()
        if self.path == "/api/plans/register":
            self._register_plan()
        elif self.path == "/api/plans/unregister":
            self._unregister_plan()
        elif m := re.match(r"^/api/plans/([^/]+)/comments$", self.path):
            self._save_comments(m.group(1))
        elif m := re.match(r"^/api/plans/([^/]+)/finish$", self.path):
            self._finish_review(m.group(1))
        elif self.path == "/api/shutdown":
            self._shutdown()
        else:
            self.send_error(404)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length))

    def _serve_viewer(self):
        viewer_path = Path(__file__).parent / "viewer.html"
        content = viewer_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_plan_list(self):
        with registry_lock:
            reviewing_set = set(plan_registry)
        conn = get_db()
        try:
            project_id = resolve_project_id(conn)
            rows = conn.execute(
                "SELECT feature_name, title, status, updated_at FROM plans WHERE project_id = ? ORDER BY updated_at DESC",
                (project_id,),
            ).fetchall()
            plans = []
            for row in rows:
                plans.append({
                    "feature": row["feature_name"],
                    "title": row["title"],
                    "status": row["status"],
                    "reviewing": row["feature_name"] in reviewing_set,
                })
            # Sort: reviewing first, then by original order (updated_at DESC)
            plans.sort(key=lambda p: (not p["reviewing"],))
            self._send_json({"plans": plans})
        finally:
            conn.close()

    def _serve_plan(self, feature):
        conn = get_db()
        try:
            project_id = resolve_project_id(conn)
            row = conn.execute(
                "SELECT body FROM plans WHERE feature_name = ? AND project_id = ?",
                (feature, project_id),
            ).fetchone()
            if not row or not row["body"]:
                self.send_error(404, "Plan body not found")
                return
            content = base64.b64decode(row["body"]).decode("utf-8")
            # Check for .bak content in signal dir
            bak_path = Path(SIGNAL_DIR) / feature / "plan.md.bak"
            old = bak_path.read_text(encoding="utf-8") if bak_path.exists() else None
            self._send_json({"content": content, "old": old})
        finally:
            conn.close()

    def _serve_plan_status(self, feature):
        conn = get_db()
        try:
            project_id = resolve_project_id(conn)
            row = conn.execute(
                "SELECT updated_at FROM plans WHERE feature_name = ? AND project_id = ?",
                (feature, project_id),
            ).fetchone()
            if not row:
                self.send_error(404, "Plan not found")
                return
            self._send_json({"lastModified": row["updated_at"]})
        finally:
            conn.close()

    def _register_plan(self):
        data = self._read_body()
        feature = data["feature"]
        with registry_lock:
            plan_registry.add(feature)
        self._send_json({"status": "ok"})

    def _unregister_plan(self):
        data = self._read_body()
        feature = data["feature"]
        with registry_lock:
            plan_registry.discard(feature)
        self._send_json({"status": "ok"})

    def _save_comments(self, feature):
        data = self._read_body()
        conn = get_db()
        try:
            project_id = resolve_project_id(conn)
            row = conn.execute(
                "SELECT id FROM plans WHERE feature_name = ? AND project_id = ?",
                (feature, project_id),
            ).fetchone()
            if not row:
                self.send_error(404, f"Plan '{feature}' not found in DB")
                return
            plan_id = row["id"]
            # Clear existing comments and insert new ones
            conn.execute("DELETE FROM comments WHERE plan_id = ?", (plan_id,))
            for c in data.get("comments", []):
                conn.execute(
                    "INSERT INTO comments (plan_id, section_heading, selected_text, comment) VALUES (?, ?, ?, ?)",
                    (plan_id, c.get("sectionHeading"), c.get("selectedText"), c["comment"]),
                )
            conn.commit()
        finally:
            conn.close()
        # Write signal file for CLI polling detection
        signal_path = Path(SIGNAL_DIR) / feature
        signal_path.mkdir(parents=True, exist_ok=True)
        (signal_path / "comments.json").write_text('{"saved": true}', encoding="utf-8")
        self._send_json({"status": "ok"})
        print(f"EVENT:comments_saved:{feature}", flush=True)

    def _finish_review(self, feature):
        # Write review-done flag for CLI polling
        signal_path = Path(SIGNAL_DIR) / feature
        signal_path.mkdir(parents=True, exist_ok=True)
        flag_path = signal_path / "review-done.flag"
        flag_path.write_text("done", encoding="utf-8")
        self._send_json({"status": "ok"})
        print(f"EVENT:review_done:{feature}", flush=True)
        with registry_lock:
            plan_registry.discard(feature)

    def _serve_review_status(self, feature):
        with registry_lock:
            reviewing = feature in plan_registry
        self._send_json({"reviewing": reviewing})

    def _shutdown(self):
        self._send_json({"status": "ok"})
        threading.Thread(target=_shutdown_server, daemon=True).start()

    def log_message(self, format, *args):
        pass  # Suppress access logs


def write_lock_file(port, pid):
    with open(LOCK_FILE, "w") as f:
        json.dump({"port": port, "pid": pid}, f)


def read_lock_file():
    try:
        with open(LOCK_FILE) as f:
            data = json.load(f)
            return data.get("port"), data.get("pid")
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return None, None


def remove_lock_file():
    try:
        os.remove(LOCK_FILE)
    except FileNotFoundError:
        pass


def main():
    global _timer, _server_ref

    # Parse args: optional --feature <name>
    feature = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--feature" and i + 1 < len(args):
            feature = args[i + 1]
            i += 2
        else:
            i += 1

    # Verify DB exists
    if not os.path.isfile(DB_PATH):
        print(f"Error: DB not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    if feature:
        conn = get_db()
        try:
            project_id = resolve_project_id(conn)
            row = conn.execute(
                "SELECT id FROM plans WHERE feature_name = ? AND project_id = ?",
                (feature, project_id),
            ).fetchone()
            if not row:
                print(f"Error: Plan '{feature}' not found in DB", file=sys.stderr)
                sys.exit(1)
        finally:
            conn.close()

    # Check if a server is already running
    existing_port, _ = read_lock_file()
    if existing_port and is_server_running(existing_port):
        if feature:
            register_plan_remote(existing_port, feature)
            print(f"EVENT:registered:{feature}", flush=True)
        print(f"PORT:{existing_port}", flush=True)
        return

    # Start new server on fixed port with fallback
    port = find_available_port()
    if feature:
        plan_registry.add(feature)
    write_lock_file(port, os.getpid())

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), AnnotationHandler)
    _server_ref = server

    # Idle auto-shutdown (resets on any API activity)
    _timer = threading.Timer(IDLE_TIMEOUT, _shutdown_server)
    _timer.daemon = True
    _timer.start()

    def shutdown_handler(*_):
        remove_lock_file()
        server.shutdown()

    signal.signal(signal.SIGTERM, shutdown_handler)

    print(f"PORT:{port}", flush=True)

    try:
        server.serve_forever()
    finally:
        remove_lock_file()


if __name__ == "__main__":
    main()
