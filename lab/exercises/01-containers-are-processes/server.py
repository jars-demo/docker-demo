"""A small JSON API on port 8000. GET /healthz answers while the process is alive."""

import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.reply(200, {"status": "ok", "pid": os.getpid(), "hostname": socket.gethostname()})
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/debug/exit":
            # Stands in for a fatal error: a crash in the main loop, a lost connection pool.
            self.reply(202, {"status": "exiting"})
            print("fatal error, exiting", flush=True)
            os._exit(1)
        self.reply(404, {"error": "not found"})

    def reply(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        self.wfile.flush()

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.command} {self.path} {args[1]}", flush=True)


if __name__ == "__main__":
    print(f"api listening on :8000 as pid {os.getpid()}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
