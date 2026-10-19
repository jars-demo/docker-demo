"""A small JSON API. It listens on HOST:8000, which defaults to the loopback address."""

import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("HOST", "127.0.0.1")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.reply(200, {"status": "ok", "hostname": socket.gethostname()})
        else:
            self.reply(404, {"error": "not found"})

    def reply(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.client_address[0]} {self.command} {self.path} {args[1]}", flush=True)


if __name__ == "__main__":
    print(f"api listening on http://{HOST}:8000", flush=True)
    ThreadingHTTPServer((HOST, 8000), Handler).serve_forever()
