"""A notes API that keeps its data in SQLite at /data/notes.db.

POST /notes {"text": "..."} saves a note. GET /notes lists them.
"""

import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB_PATH = os.environ.get("DB_PATH", "/data/notes.db")


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
    db.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, text TEXT NOT NULL)")
    return db


class Handler(BaseHTTPRequestHandler):
    db: sqlite3.Connection

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.reply(200, {"status": "ok", "uid": os.getuid()})
        elif self.path == "/notes":
            rows = self.db.execute("SELECT id, text FROM notes ORDER BY id").fetchall()
            self.reply(200, {"notes": [{"id": i, "text": t} for i, t in rows]})
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/notes":
            self.reply(404, {"error": "not found"})
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        cursor = self.db.execute("INSERT INTO notes (text) VALUES (?)", (str(body["text"]),))
        self.reply(201, {"id": cursor.lastrowid})

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
    Handler.db = connect()
    print(f"api listening on :8000, data in {DB_PATH}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
