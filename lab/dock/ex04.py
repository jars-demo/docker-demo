"""04: ports, interfaces and container networks."""

import time
from pathlib import Path

from dock import docker as d

TITLE = "Listening, and unreachable"
HINTS = [
    "Read the first log line. Which address is the server listening on?",
    "Inside a container, 127.0.0.1 is the container's own loopback, not your machine's.",
    "Listen on 0.0.0.0, every interface: set HOST=0.0.0.0 in the Dockerfile.",
]
TAG = "dockerlab/04"
PROBE = "import urllib.request; print(urllib.request.urlopen('{url}', timeout=3).read().decode())"


def from_inside(container: str, url: str) -> str:
    """Make a request with Python inside a container, the way another service would."""
    proc = d.docker("exec", container, "python", "-c", PROBE.format(url=url), check=False)
    return proc.stdout.strip() or proc.stderr.strip().splitlines()[-1]


def run(path: Path) -> None:
    name = "dockerlab-04"
    build = d.build(path, TAG)
    if not build.ok:
        print(f"the build failed: {build.error()}")
        return
    d.run(TAG, name, "-p", "127.0.0.1::8000")
    try:
        time.sleep(1.5)
        port = d.host_port(name)
        print("$ docker logs dockerlab-04")
        print(d.logs(name))
        print()
        print(f"from your machine, http://127.0.0.1:{port}/healthz:")
        print(f"  {d.http(f'http://127.0.0.1:{port}/healthz').body}")
        print()
        print("from inside the container, http://127.0.0.1:8000/healthz:")
        print(f"  {from_inside(name, 'http://127.0.0.1:8000/healthz')}")
        print()
        print("The server works. It only listens where nothing from outside can reach it.")
    finally:
        d.remove(name)


def check(path: Path) -> list[tuple[str, bool]]:
    name, client, network = "dockerlab-04-check", "dockerlab-04-client", "dockerlab-04-net"
    tag = f"{TAG}:check"
    build = d.build(path, tag)
    if not build.ok:
        return [(f"the image builds ({build.error()})", False)]
    d.docker("network", "rm", network, check=False)
    d.docker("network", "create", "--label", d.LABEL, network)
    try:
        d.run(tag, name, "--network", network, "--network-alias", "api", "-p", "127.0.0.1::8000")
        d.run(tag, client, "--network", network)
        port = d.host_port(name)
        published = d.wait_http(f"http://127.0.0.1:{port}/healthz", 10) if port else d.Reply(0, "")
        by_name = from_inside(client, "http://api:8000/healthz")
        return [
            ("the API answers on the published port", published.status == 200),
            (
                "another container on the same network reaches it at http://api:8000",
                '"status": "ok"' in by_name,
            ),
        ]
    finally:
        d.remove(name, client)
        d.docker("network", "rm", network, check=False)
