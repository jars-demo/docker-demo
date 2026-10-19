"""A JSON API that runs a pool of worker processes, two per CPU plus one.

Each worker holds 48 MB in memory, the way a real one holds a model, a cache or a connection
pool. If any worker dies, the service shuts down so the orchestrator can restart it.
"""

import json
import math
import multiprocessing
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WORKER_MB = 48


def cgroup_cpu_quota() -> float | None:
    """The CPU limit set with docker run --cpus, in CPUs, or None when there is no limit.

    os.cpu_count() counts the host's CPUs. A container limit is a time quota per period,
    which the kernel publishes in the cgroup filesystem: cgroup v2 in cpu.max, v1 in two files.
    """
    try:
        with open("/sys/fs/cgroup/cpu.max") as file:  # cgroup v2: "150000 100000" or "max 100000"
            quota, period = file.read().split()
        return None if quota == "max" else int(quota) / int(period)
    except OSError:
        pass
    try:
        with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us") as file:  # cgroup v1: -1 means no limit
            quota = int(file.read())
        with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us") as file:
            period = int(file.read())
        return None if quota <= 0 else quota / period
    except OSError:
        return None


def available_cpus() -> int:
    """How many CPUs this process may use: the cgroup quota, rounded up, but never more than
    the CPUs it is allowed to run on."""
    cpus = os.process_cpu_count() or 1
    quota = cgroup_cpu_quota()
    return cpus if quota is None else max(1, min(cpus, math.ceil(quota)))


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
