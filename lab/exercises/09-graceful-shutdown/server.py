"""A JSON API that shuts down gracefully.

On SIGTERM it stops accepting new connections, lets requests in flight finish, and exits 0.
GET /slow?seconds=N stands in for a slow request: a report, an upload, a payment.
"""

import json
import os
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        url = urlsplit(self.path)
        if url.path == "/healthz":
            self.reply(200, {"status": "ok", "pid": os.getpid()})
        elif url.path == "/slow":
            seconds = float(parse_qs(url.query).get("seconds", ["2"])[0])
            time.sleep(seconds)
            self.reply(200, {"status": "done", "seconds": seconds})
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


class Server(ThreadingHTTPServer):
    daemon_threads = False  # so server_close() waits for requests still in flight


def main() -> None:
    server = Server(("0.0.0.0", 8000), Handler)

    def on_sigterm(signum: int, frame: object) -> None:
        print("SIGTERM received: finishing requests in flight", flush=True)
        # shutdown() waits for serve_forever() to return, so it must run on another thread.
        threading.Thread(target=server.shutdown).start()

    signal.signal(signal.SIGTERM, on_sigterm)
    print(f"api listening on :8000 as pid {os.getpid()}", flush=True)
    server.serve_forever()
    server.server_close()
    print("stopped cleanly", flush=True)


if __name__ == "__main__":
    main()
