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

TIMEOUT_SECONDS = 30 * 60  # 30 minutes
LOCK_FILE = "/tmp/annotation-viewer.lock"
DB_PATH = os.path.expanduser("~/.claude/spec-flow.db")
SIGNAL_DIR = "/tmp/spec-flow-review"

# Global timer for activity-based timeout reset
_timer = None
_timer_lock = threading.Lock()
_server_ref = None


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


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
    """Reset the auto-shutdown timer on activity."""
    global _timer
    with _timer_lock:
        if _timer is not None:
            _timer.cancel()
        if _server_ref is not None:
            _timer = threading.Timer(TIMEOUT_SECONDS, _server_ref.shutdown)
            _timer.daemon = True
            _timer.start()


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
            features = list(plan_registry)
        conn = get_db()
        try:
            project_id = resolve_project_id(conn)
            plans = []
            for f in features:
                row = conn.execute(
                    "SELECT title FROM plans WHERE feature_name = ? AND project_id = ?",
                    (f, project_id),
                ).fetchone()
                title = row["title"] if row else f
                plans.append({"feature": f, "title": title})
            self._send_json({"plans": plans})
        finally:
            conn.close()

    def _serve_plan(self, feature):
        with registry_lock:
            if feature not in plan_registry:
                self.send_error(404, f"Plan '{feature}' not registered")
                return
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
        with registry_lock:
            if feature not in plan_registry:
                self.send_error(404, f"Plan '{feature}' not registered")
                return
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
            remaining = len(plan_registry)
        self._send_json({"status": "ok"})
        if remaining == 0:
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _save_comments(self, feature):
        with registry_lock:
            if feature not in plan_registry:
                self.send_error(404, f"Plan '{feature}' not registered")
                return
        data = self._read_body()
        # Write comments to signal dir for CLI polling
        signal_path = Path(SIGNAL_DIR) / feature
        signal_path.mkdir(parents=True, exist_ok=True)
        comments_path = signal_path / "comments.json"
        with open(comments_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
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
            remaining = len(plan_registry)
        if remaining == 0:
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, format, *args):
        pass  # Suppress access logs


def write_lock_file(port):
    with open(LOCK_FILE, "w") as f:
        f.write(str(port))


def read_lock_file():
    try:
        with open(LOCK_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def remove_lock_file():
    try:
        os.remove(LOCK_FILE)
    except FileNotFoundError:
        pass


def main():
    global _timer, _server_ref

    if len(sys.argv) < 3 or sys.argv[1] != "--feature":
        print("Usage: python3 server.py --feature <feature-name>", file=sys.stderr)
        sys.exit(1)

    feature = sys.argv[2]

    # Verify DB and plan exist
    if not os.path.isfile(DB_PATH):
        print(f"Error: DB not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

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
    existing_port = read_lock_file()
    if existing_port and is_server_running(existing_port):
        register_plan_remote(existing_port, feature)
        print(f"PORT:{existing_port}", flush=True)
        print(f"EVENT:registered:{feature}", flush=True)
        return

    # Start new server
    port = find_free_port()
    plan_registry.add(feature)
    write_lock_file(port)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), AnnotationHandler)
    _server_ref = server

    # Auto-timeout to prevent zombie processes (resets on activity)
    _timer = threading.Timer(TIMEOUT_SECONDS, server.shutdown)
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
