#!/usr/bin/env python3
"""Annotation Viewer — Local HTTP server for plan.md review.

Serves plan.md as rendered Markdown with a comment UI.
Supports multiple plans with tab-based navigation.
Uses only Python 3 standard library.
"""

import http.server
import json
import os
import re
import signal
import socket
import sys
import threading
import urllib.request
from pathlib import Path

TIMEOUT_SECONDS = 30 * 60  # 30 minutes
LOCK_FILE = "/tmp/annotation-viewer.lock"


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


def register_plan_remote(port, feature, plan_dir):
    """Register a plan with an already-running server."""
    url = f"http://127.0.0.1:{port}/api/plans/register"
    data = json.dumps({"feature": feature, "planDir": plan_dir}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


# Shared plan registry: {feature-name: plan-dir-path}
plan_registry: dict[str, str] = {}
registry_lock = threading.Lock()


class AnnotationHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
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
            plans = []
            for f, d in plan_registry.items():
                title = f
                plan_path = Path(d) / "plan.md"
                if plan_path.exists():
                    for line in plan_path.read_text(encoding="utf-8").splitlines():
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip().strip('"').strip("'")
                            break
                plans.append({"feature": f, "planDir": d, "title": title})
        self._send_json({"plans": plans})

    def _serve_plan(self, feature):
        with registry_lock:
            plan_dir = plan_registry.get(feature)
        if not plan_dir:
            self.send_error(404, f"Plan '{feature}' not registered")
            return
        plan_path = Path(plan_dir) / "plan.md"
        if not plan_path.exists():
            self.send_error(404, "plan.md not found")
            return
        content = plan_path.read_text(encoding="utf-8")
        bak_path = Path(plan_dir) / "plan.md.bak"
        old = bak_path.read_text(encoding="utf-8") if bak_path.exists() else None
        self._send_json({"content": content, "old": old})

    def _serve_plan_status(self, feature):
        with registry_lock:
            plan_dir = plan_registry.get(feature)
        if not plan_dir:
            self.send_error(404, f"Plan '{feature}' not registered")
            return
        plan_path = Path(plan_dir) / "plan.md"
        if not plan_path.exists():
            self.send_error(404, "plan.md not found")
            return
        self._send_json({"lastModified": os.path.getmtime(str(plan_path))})

    def _register_plan(self):
        data = self._read_body()
        feature = data["feature"]
        plan_dir = data["planDir"]
        with registry_lock:
            plan_registry[feature] = plan_dir
        self._send_json({"status": "ok"})

    def _unregister_plan(self):
        data = self._read_body()
        feature = data["feature"]
        with registry_lock:
            plan_registry.pop(feature, None)
            remaining = len(plan_registry)
        self._send_json({"status": "ok"})
        if remaining == 0:
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _save_comments(self, feature):
        with registry_lock:
            plan_dir = plan_registry.get(feature)
        if not plan_dir:
            self.send_error(404, f"Plan '{feature}' not registered")
            return
        data = self._read_body()
        comments_path = Path(plan_dir) / "comments.json"
        with open(comments_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._send_json({"status": "ok"})
        print(f"EVENT:comments_saved:{feature}", flush=True)

    def _finish_review(self, feature):
        self._send_json({"status": "ok"})
        print(f"EVENT:review_done:{feature}", flush=True)
        with registry_lock:
            plan_registry.pop(feature, None)
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
    if len(sys.argv) < 2:
        print("Usage: python3 server.py <plan-directory>", file=sys.stderr)
        sys.exit(1)

    plan_dir = os.path.abspath(sys.argv[1])
    if not os.path.isfile(os.path.join(plan_dir, "plan.md")):
        print(f"Error: plan.md not found in {plan_dir}", file=sys.stderr)
        sys.exit(1)

    # Extract feature name from directory path
    feature = os.path.basename(plan_dir)

    # Check if a server is already running
    existing_port = read_lock_file()
    if existing_port and is_server_running(existing_port):
        # Register with existing server
        register_plan_remote(existing_port, feature, plan_dir)
        print(f"PORT:{existing_port}", flush=True)
        print(f"EVENT:registered:{feature}", flush=True)
        return

    # Start new server
    port = find_free_port()
    plan_registry[feature] = plan_dir
    write_lock_file(port)

    server = http.server.HTTPServer(("127.0.0.1", port), AnnotationHandler)

    # Auto-timeout to prevent zombie processes
    timer = threading.Timer(TIMEOUT_SECONDS, server.shutdown)
    timer.daemon = True
    timer.start()

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
