"""A JSON API with a health endpoint.

GET /healthz is 200 while the service can do its job and 503 when it cannot.
POST /debug/break stands in for a real fault: a deadlocked worker pool, a lost connection.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

broken = False


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            if broken:
                self.reply(503, {"status": "failing", "reason": "worker pool is stuck"})
            else:
                self.reply(200, {"status": "ok"})
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self) -> None:
        global broken
        if self.path == "/debug/break":
            broken = True
            self.reply(202, {"status": "broken"})
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
    print("api listening on :8000", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
