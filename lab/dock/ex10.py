"""10: health checks that tell the truth."""

import json
from pathlib import Path

from dock import docker as d

TITLE = "Unhealthy, though nothing is wrong"
HINTS = [
    "Read the health check's own output: docker inspect --format '{{json .State.Health}}' <name>",
    "The check runs inside the container, with the tools the image has. Does the slim image "
    "have curl?",
    'Use what is already there: CMD ["python", "-c", "import urllib.request; '
    "urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)\"]",
]
TAG = "dockerlab/10"
# Check every second in the lab, so the exercise does not wait 30 s per answer.
FAST = [
    "--health-interval",
    "1s",
    "--health-timeout",
    "2s",
    "--health-retries",
    "2",
    "--health-start-period",
    "1s",
]


def health(name: str) -> str:
    return d.inspect(name, "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}")


def run(path: Path) -> None:
    name = "dockerlab-10"
    build = d.build(path, TAG)
    if not build.ok:
        print(f"the build failed: {build.error()}")
        return
    d.run(TAG, name, "-p", "127.0.0.1::8000", *FAST)
    try:
        d.wait_for(lambda: health(name) != "starting", 15)
        port = d.host_port(name)
        print(f"GET /healthz from your machine: {d.http(f'http://127.0.0.1:{port}/healthz').body}")
        print(f"Docker says the container is: {health(name)}")
        print()
        state = json.loads(d.inspect(name, "{{json .State.Health}}") or "{}")
        last = (state.get("Log") or [{}])[-1]
        print("the health check's last run:")
        print(f"  exit code {last.get('ExitCode')}: {str(last.get('Output', '')).strip()}")
    finally:
        d.remove(name)


def check(path: Path) -> list[tuple[str, bool]]:
    name, tag = "dockerlab-10-check", f"{TAG}:check"
    build = d.build(path, tag)
    if not build.ok:
        return [(f"the image builds ({build.error()})", False)]
    d.run(tag, name, "-p", "127.0.0.1::8000", *FAST)
    try:
        healthy = d.wait_for(lambda: health(name) == "healthy", 15)
        first = health(name)
        unhealthy = False
        if healthy:
            d.http(f"http://127.0.0.1:{d.host_port(name)}/debug/break", "POST")
            unhealthy = d.wait_for(lambda: health(name) == "unhealthy", 15)
        return [
            (f"Docker reports the container healthy within 15 s ({first})", healthy),
            ("Docker reports it unhealthy within 15 s once /healthz fails", unhealthy),
        ]
    finally:
        d.remove(name)
