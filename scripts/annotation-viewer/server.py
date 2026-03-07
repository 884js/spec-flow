#!/usr/bin/env python3
"""Annotation Viewer — Local HTTP server for plan.md review.

Serves plan.md as rendered Markdown with a comment UI.
Uses only Python 3 standard library.
"""

import http.server
import json
import os
import signal
import socket
import sys
import threading
from pathlib import Path

TIMEOUT_SECONDS = 30 * 60  # 30 minutes


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class AnnotationHandler(http.server.SimpleHTTPRequestHandler):
    plan_dir: str = ""

    def do_GET(self):
        if self.path == "/":
            self._serve_viewer()
        elif self.path == "/api/plan":
            self._serve_plan()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/done":
            self._save_comments()
        else:
            self.send_error(404)

    def _serve_viewer(self):
        viewer_path = Path(__file__).parent / "viewer.html"
        content = viewer_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_plan(self):
        plan_path = Path(self.plan_dir) / "plan.md"
        if not plan_path.exists():
            self.send_error(404, "plan.md not found")
            return
        content = plan_path.read_text(encoding="utf-8")
        bak_path = Path(self.plan_dir) / "plan.md.bak"
        old = bak_path.read_text(encoding="utf-8") if bak_path.exists() else None
        body = json.dumps({"content": content, "old": old}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _save_comments(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        data = json.loads(raw)

        comments_path = Path(self.plan_dir) / "comments.json"
        with open(comments_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        body = json.dumps({"status": "ok"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

        # Shutdown server after response
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, format, *args):
        pass  # Suppress access logs


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 server.py <plan-directory>", file=sys.stderr)
        sys.exit(1)

    plan_dir = os.path.abspath(sys.argv[1])
    if not os.path.isfile(os.path.join(plan_dir, "plan.md")):
        print(f"Error: plan.md not found in {plan_dir}", file=sys.stderr)
        sys.exit(1)

    AnnotationHandler.plan_dir = plan_dir
    port = find_free_port()

    server = http.server.HTTPServer(("127.0.0.1", port), AnnotationHandler)

    # Auto-timeout to prevent zombie processes
    timer = threading.Timer(TIMEOUT_SECONDS, server.shutdown)
    timer.daemon = True
    timer.start()

    # Handle SIGTERM gracefully
    signal.signal(signal.SIGTERM, lambda *_: server.shutdown())

    # Print port for caller to parse
    print(f"PORT:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
