"""The notes API, backed by Postgres.

It connects once at startup, the way most apps do before they run migrations or warm a pool.
If the database is not there, it exits.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]


class Handler(BaseHTTPRequestHandler):
    db: psycopg.Connection

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.reply(200, {"status": "ok"})
        elif self.path == "/readyz":
            try:
                count = self.db.execute("SELECT count(*) FROM notes").fetchone()[0]
                self.reply(200, {"status": "ready", "notes": count})
            except psycopg.Error as error:
                self.reply(503, {"status": "not ready", "error": str(error).strip()})
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
    try:
        Handler.db = psycopg.connect(DATABASE_URL, autocommit=True, connect_timeout=5)
    except psycopg.OperationalError as error:
        print(f"could not connect to the database: {str(error).strip()}", flush=True)
        sys.exit(1)
    print("connected to the database; api listening on :8000", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
