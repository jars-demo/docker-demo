"""A small JSON API that talks to Postgres through psycopg's compiled C build.

GET /healthz reports which psycopg implementation loaded and the libpq it links against.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import psycopg


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.reply(
                200,
                {
                    "status": "ok",
                    "psycopg": psycopg.pq.__impl__,
                    "libpq": psycopg.pq.version(),
                    "uid": os.getuid(),
                },
            )
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
        print(f"{self.command} {self.path} {args[1]}", flush=True)


if __name__ == "__main__":
    print(f"api listening on :8000 (psycopg {psycopg.pq.__impl__})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
