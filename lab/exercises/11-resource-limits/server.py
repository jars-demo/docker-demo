"""A JSON API that runs a pool of worker processes, two per CPU plus one.

Each worker holds 48 MB in memory, the way a real one holds a model, a cache or a connection
pool. If any worker dies, the service shuts down so the orchestrator can restart it.
"""

import json
import multiprocessing
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WORKER_MB = 48


def available_cpus() -> int:
    """How many CPUs this process may use."""
    return os.cpu_count() or 1


def worker() -> None:
    memory = bytearray(WORKER_MB * 1024 * 1024)
    for page in range(0, len(memory), 4096):  # touch every page so it is really in memory
        memory[page] = 1
    while True:
        time.sleep(60)


class Handler(BaseHTTPRequestHandler):
    status: dict = {}

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.reply(200, self.status)
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
        pass


def watch(pool: list[multiprocessing.Process]) -> None:
    while True:
        for process in pool:
            if not process.is_alive():
                print(
                    f"worker {process.pid} died (exit code {process.exitcode}), shutting down",
                    flush=True,
                )
                os._exit(1)
        time.sleep(0.2)


if __name__ == "__main__":
    cpus = available_cpus()
    count = cpus * 2 + 1
    print(f"{cpus} CPUs available: starting {count} workers of {WORKER_MB} MB", flush=True)
    pool = [multiprocessing.Process(target=worker, daemon=True) for _ in range(count)]
    for process in pool:
        process.start()
    Handler.status = {"status": "ok", "cpus": cpus, "workers": count}
    threading.Thread(target=watch, args=(pool,), daemon=True).start()
    try:
        ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
