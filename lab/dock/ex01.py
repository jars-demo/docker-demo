"""01: a container lives exactly as long as its main process."""

import time
from pathlib import Path

from dock import docker as d

TITLE = "The container that would not stay up"
HINTS = [
    "Run docker ps -a. What exit code did the container stop with, and how long did it run?",
    "The container runs sh start.sh. What does the & at the end of a line do in a shell script?",
    "Start the server in the foreground, so the script only ends when the server does.",
]
TAG = "dockerlab/01"


def run(path: Path) -> None:
    name = "dockerlab-01"
    build = d.build(path, TAG)
    if not build.ok:
        print(f"the build failed: {build.error()}")
        return
    d.run(TAG, name, "-p", "127.0.0.1::8000")
    time.sleep(3)
    print("$ docker ps -a --filter name=dockerlab-01")
    print(
        d.docker(
            "ps", "-a", "--filter", f"name={name}", "--format", "table {{.Names}}\t{{.Status}}"
        ).stdout.rstrip()
    )
    print()
    print("$ docker logs dockerlab-01")
    print(d.logs(name))
    print()
    status = d.inspect(name, "{{.State.Status}}")
    code = d.inspect(name, "{{.State.ExitCode}}")
    print(f"three seconds after docker run, the container is {status} (exit code {code}).")
    d.remove(name)


def check(path: Path) -> list[tuple[str, bool]]:
    name = "dockerlab-01-check"
    build = d.build(path, f"{TAG}:check")
    if not build.ok:
        return [(f"the image builds ({build.error()})", False)]
    d.run(f"{TAG}:check", name, "-p", "127.0.0.1::8000")
    try:
        time.sleep(3)
        alive = d.running(name)
        port = d.host_port(name)
        health = d.http(f"http://127.0.0.1:{port}/healthz") if port else d.Reply(0, "")
        dies = False
        code = ""
        if health.status == 200:
            d.http(f"http://127.0.0.1:{port}/debug/exit", method="POST")
            dies = d.wait_for(lambda: not d.running(name), 5)
            code = d.inspect(name, "{{.State.ExitCode}}")
        return [
            ("the container is still running 3 s after docker run", alive),
            ("the API answers on the published port", health.status == 200),
            (
                f"when the server dies, the container stops with it (exit code {code or '-'})",
                dies and code not in ("", "0"),
            ),
        ]
    finally:
        d.remove(name)
