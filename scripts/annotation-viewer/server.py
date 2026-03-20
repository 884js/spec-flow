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
import subprocess
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


def register_plan_remote(port, feature, project=None):
    """Register a plan with an already-running server."""
    if project is None:
        project = os.path.basename(os.getcwd())
    url = f"http://127.0.0.1:{port}/api/plans/register"
    data = json.dumps({"feature": feature, "project": project}).encode("utf-8")
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


def resolve_project_id(conn, project_name=None):
    """Resolve project_id from project name (or cwd as fallback)."""
    if project_name is None:
        project_name = os.path.basename(os.getcwd())
    row = conn.execute(
        "SELECT id FROM projects WHERE name = ?", (project_name,)
    ).fetchone()
    if row:
        return row["id"]
    # Auto-register (only for cwd-based resolution)
    if project_name == os.path.basename(os.getcwd()):
        cur = conn.execute(
            "INSERT INTO projects (name, path) VALUES (?, ?) RETURNING id",
            (project_name, os.getcwd()),
        )
        conn.commit()
        return cur.fetchone()[0]
    return None


# Shared plan registry: set of "project/feature" keys
plan_registry: set[str] = set()
registry_lock = threading.Lock()


class AnnotationHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        reset_timeout()
        if self.path == "/":
            self._serve_viewer()
        elif self.path == "/api/plans":
            self._serve_plan_list()
        elif m := re.match(r"^/api/plans/([^/]+)/([^/]+)/plan$", self.path):
            self._serve_plan(m.group(1), m.group(2))
        elif m := re.match(r"^/api/plans/([^/]+)/([^/]+)/status$", self.path):
            self._serve_plan_status(m.group(1), m.group(2))
        elif m := re.match(r"^/api/plans/([^/]+)/([^/]+)/review-status$", self.path):
            self._serve_review_status(m.group(1), m.group(2))
        else:
            self.send_error(404)

    def do_POST(self):
        reset_timeout()
        if self.path == "/api/plans/register":
            self._register_plan()
        elif self.path == "/api/plans/unregister":
            self._unregister_plan()
        elif m := re.match(r"^/api/plans/([^/]+)/([^/]+)/comments$", self.path):
            self._save_comments(m.group(1), m.group(2))
        elif m := re.match(r"^/api/plans/([^/]+)/([^/]+)/finish$", self.path):
            self._finish_review(m.group(1), m.group(2))
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
            rows = conn.execute(
                "SELECT p.feature_name, p.title, p.updated_at, pr.name as project_name, "
                "  CASE "
                "    WHEN lr.judgment = 'NEEDS_FIX' THEN '要修正' "
                "    WHEN lr.judgment = 'PARTIAL' THEN '部分合格' "
                "    WHEN lr.judgment = 'PASS' THEN '検証済み' "
                "    WHEN t_total.cnt > 0 AND t_total.cnt = t_done.cnt THEN '実装完了' "
                "    WHEN t_ip.cnt > 0 THEN '実装中' "
                "    WHEN t_total.cnt > 0 THEN '未着手' "
                "    ELSE '仕様作成済み' "
                "  END as computed_status "
                "FROM plans p "
                "JOIN projects pr ON p.project_id = pr.id "
                "LEFT JOIN ("
                "  SELECT plan_id, judgment FROM results r1 "
                "  WHERE r1.created_at = (SELECT MAX(r2.created_at) FROM results r2 WHERE r2.plan_id = r1.plan_id)"
                ") lr ON lr.plan_id = p.id "
                "LEFT JOIN ("
                "  SELECT plan_id, COUNT(*) as cnt FROM tasks GROUP BY plan_id"
                ") t_total ON t_total.plan_id = p.id "
                "LEFT JOIN ("
                "  SELECT plan_id, COUNT(*) as cnt FROM tasks WHERE status = 'done' GROUP BY plan_id"
                ") t_done ON t_done.plan_id = p.id "
                "LEFT JOIN ("
                "  SELECT plan_id, COUNT(*) as cnt FROM tasks WHERE status = 'in_progress' GROUP BY plan_id"
                ") t_ip ON t_ip.plan_id = p.id "
                "ORDER BY pr.name, p.updated_at DESC",
            ).fetchall()
            plans = []
            for row in rows:
                registry_key = f"{row['project_name']}/{row['feature_name']}"
                plans.append({
                    "project": row["project_name"],
                    "feature": row["feature_name"],
                    "title": row["title"],
                    "status": row["computed_status"],
                    "reviewing": registry_key in reviewing_set,
                })
            plans.sort(key=lambda p: (not p["reviewing"],))
            self._send_json({"plans": plans})
        finally:
            conn.close()

    def _serve_plan(self, project, feature):
        conn = get_db()
        try:
            project_id = resolve_project_id(conn, project)
            if project_id is None:
                self.send_error(404, "Project not found")
                return
            row = conn.execute(
                "SELECT body, prev_body FROM plans WHERE feature_name = ? AND project_id = ?",
                (feature, project_id),
            ).fetchone()
            if not row or not row["body"]:
                self.send_error(404, "Plan body not found")
                return
            content = base64.b64decode(row["body"]).decode("utf-8")
            old = base64.b64decode(row["prev_body"]).decode("utf-8") if row["prev_body"] else None
            self._send_json({"content": content, "old": old})
        finally:
            conn.close()

    def _serve_plan_status(self, project, feature):
        conn = get_db()
        try:
            project_id = resolve_project_id(conn, project)
            if project_id is None:
                self.send_error(404, "Project not found")
                return
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
        project = data.get("project", os.path.basename(os.getcwd()))
        registry_key = f"{project}/{feature}"
        with registry_lock:
            plan_registry.add(registry_key)
        self._send_json({"status": "ok"})

    def _unregister_plan(self):
        data = self._read_body()
        feature = data["feature"]
        project = data.get("project", os.path.basename(os.getcwd()))
        registry_key = f"{project}/{feature}"
        with registry_lock:
            plan_registry.discard(registry_key)
        self._send_json({"status": "ok"})

    def _save_comments(self, project, feature):
        data = self._read_body()
        conn = get_db()
        try:
            project_id = resolve_project_id(conn, project)
            if project_id is None:
                self.send_error(404, f"Project '{project}' not found")
                return
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

    def _finish_review(self, project, feature):
        # Write review-done flag for CLI polling
        signal_path = Path(SIGNAL_DIR) / feature
        signal_path.mkdir(parents=True, exist_ok=True)
        flag_path = signal_path / "review-done.flag"
        flag_path.write_text("done", encoding="utf-8")
        self._send_json({"status": "ok"})
        print(f"EVENT:review_done:{feature}", flush=True)
        registry_key = f"{project}/{feature}"
        with registry_lock:
            plan_registry.discard(registry_key)

    def _serve_review_status(self, project, feature):
        registry_key = f"{project}/{feature}"
        with registry_lock:
            reviewing = registry_key in plan_registry
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


def cleanup_orphan_processes():
    """Find and kill orphaned server.py processes not tracked by the lock file."""
    lock_pid = None
    _, existing_pid = read_lock_file()
    if existing_pid:
        lock_pid = int(existing_pid)

    my_pid = os.getpid()
    script_path = os.path.abspath(__file__)

    try:
        result = subprocess.run(
            ["pgrep", "-f", script_path],
            capture_output=True, text=True, timeout=5,
        )
        pids = [int(p) for p in result.stdout.strip().split("\n") if p.strip()]
    except Exception:
        return

    for pid in pids:
        if pid == my_pid or pid == lock_pid:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
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

    project_name = os.path.basename(os.getcwd())

    if feature:
        conn = get_db()
        try:
            project_id = resolve_project_id(conn, project_name)
            if project_id is None:
                print(f"Error: Project '{project_name}' not found in DB", file=sys.stderr)
                sys.exit(1)
            row = conn.execute(
                "SELECT id FROM plans WHERE feature_name = ? AND project_id = ?",
                (feature, project_id),
            ).fetchone()
            if not row:
                print(f"Error: Plan '{feature}' not found in DB", file=sys.stderr)
                sys.exit(1)
        finally:
            conn.close()

    # Check if a server is already running (lock file + health check)
    existing_port, existing_pid = read_lock_file()
    if existing_port and is_server_running(existing_port):
        if feature:
            register_plan_remote(existing_port, feature)
            print(f"EVENT:registered:{feature}", flush=True)
        print(f"PORT:{existing_port}", flush=True)
        return

    # Lock file exists but server is dead — clean up
    if existing_port:
        remove_lock_file()

    # Kill any orphaned server.py processes before starting
    cleanup_orphan_processes()

    # Start new server on fixed port with fallback
    port = find_available_port()
    if feature:
        plan_registry.add(f"{project_name}/{feature}")
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
    signal.signal(signal.SIGINT, shutdown_handler)

    print(f"PORT:{port}", flush=True)

    try:
        server.serve_forever()
    finally:
        remove_lock_file()


if __name__ == "__main__":
    main()
