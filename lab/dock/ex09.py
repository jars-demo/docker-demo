"""09: PID 1, signals and graceful shutdown."""

import threading
import time
from pathlib import Path

from dock import docker as d

TITLE = "The ten-second stop"
HINTS = [
    "Which process is PID 1 in the container? Run: docker exec <name> cat /proc/1/cmdline",
    "docker stop sends SIGTERM to PID 1 only. A shell waiting for its child does not pass the "
    "signal on, so after 10 s Docker sends SIGKILL.",
    "Make the shell hand over to the server on the last line: exec python server.py.",
]
TAG = "dockerlab/09"


def pid_one(name: str) -> str:
    raw = d.docker("exec", name, "cat", "/proc/1/cmdline", check=False).stdout
    return raw.replace("\x00", " ").strip()


def stop(name: str) -> float:
    start = time.perf_counter()
    d.docker("stop", "-t", "10", name, check=False)
    return time.perf_counter() - start


def run(path: Path) -> None:
    name = "dockerlab-09"
    build = d.build(path, TAG)
    if not build.ok:
        print(f"the build failed: {build.error()}")
        return
    d.run(TAG, name, "-p", "127.0.0.1::8000")
    try:
        port = d.host_port(name)
        d.wait_http(f"http://127.0.0.1:{port}/healthz", 10)
        print(f"PID 1 in the container: {pid_one(name)}")
        print()
        print("$ time docker stop dockerlab-09")
        took = stop(name)
        code = d.inspect(name, "{{.State.ExitCode}}")
        print(f"took {took:.1f} s, exit code {code}")
        print()
        print("$ docker logs dockerlab-09")
        print(d.logs(name))
        print()
        print("The server never heard SIGTERM. Docker waited 10 s, then killed it with SIGKILL.")
    finally:
        d.remove(name)


def check(path: Path) -> list[tuple[str, bool]]:
    name, tag = "dockerlab-09-check", f"{TAG}:check"
    build = d.build(path, tag)
    if not build.ok:
        return [(f"the image builds ({build.error()})", False)]
    d.run(tag, name, "-p", "127.0.0.1::8000")
    try:
        port = d.host_port(name)
        d.wait_http(f"http://127.0.0.1:{port}/healthz", 10)
        answers: list[d.Reply] = []
        request = threading.Thread(
            target=lambda: answers.append(
                d.http(f"http://127.0.0.1:{port}/slow?seconds=2", timeout=15)
            )
        )
        request.start()
        time.sleep(0.5)
        took = stop(name)
        request.join()
        code = d.inspect(name, "{{.State.ExitCode}}")
        in_flight = answers[0].status if answers else 0
        return [
            (f"docker stop finishes in under 4 s (took {took:.1f} s)", took < 4),
            (f"the server exits cleanly (exit code {code})", code == "0"),
            (
                f"a request in flight when the stop begins still gets its answer "
                f"({in_flight or 'none'})",
                in_flight == 200,
            ),
        ]
    finally:
        d.remove(name)
