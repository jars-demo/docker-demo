"""05: volumes, and who owns the files in them."""

import time
from pathlib import Path

from dock import docker as d

TITLE = "Permission denied on a fresh volume"
HINTS = [
    "Run ls -ld /data in the container. Who owns it, and who is the app running as?",
    "Docker creates a mount point that is missing from the image as root. A new named volume "
    "copies the owner of the directory it is mounted on.",
    "Before USER app, create /data and give it to the app user: "
    "mkdir /data && chown app:app /data.",
]
TAG = "dockerlab/05"


def start(tag: str, name: str, volume: str) -> int | None:
    """Start the API on the volume. Returns the host port once it answers, or None."""
    d.run(tag, name, "-v", f"{volume}:/data", "-p", "127.0.0.1::8000")
    port = d.host_port(name)
    if port is None:
        return None
    reply = d.wait_http(f"http://127.0.0.1:{port}/healthz", 10, lambda: d.running(name))
    return port if reply.status == 200 else None


def run(path: Path) -> None:
    name, volume = "dockerlab-05", "dockerlab-05-data"
    build = d.build(path, TAG)
    if not build.ok:
        print(f"the build failed: {build.error()}")
        return
    d.docker("volume", "rm", "-f", volume, check=False)
    d.docker("volume", "create", "--label", d.LABEL, volume)
    try:
        d.run(TAG, name, "-v", f"{volume}:/data")
        time.sleep(2)
        print("$ docker ps -a --filter name=dockerlab-05")
        print(
            d.docker(
                "ps", "-a", "--filter", f"name={name}$", "--format", "table {{.Names}}\t{{.Status}}"
            ).stdout.rstrip()
        )
        print()
        print("$ docker logs dockerlab-05")
        print(d.logs(name, 2))
        print()
        print("$ docker run --rm -v dockerlab-05-data:/data dockerlab/05 ls -ld /data")
        print(
            d.docker(
                "run", "--rm", "-v", f"{volume}:/data", TAG, "ls", "-ld", "/data"
            ).stdout.strip()
        )
        print("$ docker run --rm dockerlab/05 id")
        print(d.docker("run", "--rm", TAG, "id").stdout.strip())
    finally:
        d.remove(name)
        d.docker("volume", "rm", "-f", volume, check=False)


def check(path: Path) -> list[tuple[str, bool]]:
    name, volume = "dockerlab-05-check", "dockerlab-05-check-data"
    tag = f"{TAG}:check"
    build = d.build(path, tag)
    if not build.ok:
        return [(f"the image builds ({build.error()})", False)]
    d.remove(name)
    d.docker("volume", "rm", "-f", volume, check=False)
    d.docker("volume", "create", "--label", d.LABEL, volume)
    try:
        port = start(tag, name, volume)
        uid = d.http(f"http://127.0.0.1:{port}/healthz").json().get("uid") if port else None
        kept = False
        if port:
            d.http(f"http://127.0.0.1:{port}/notes", "POST", {"text": "survives a redeploy"})
            d.remove(name)  # a redeploy: the container goes, the volume stays
            port = start(tag, name, volume)
            notes = d.http(f"http://127.0.0.1:{port}/notes").json().get("notes", []) if port else []
            kept = any(note["text"] == "survives a redeploy" for note in notes)
        return [
            ("the API starts on a new, empty named volume", uid is not None),
            (f"it runs as a non-root user (uid {uid if uid is not None else '-'})", bool(uid)),
            ("a note saved before a redeploy is still there after it", kept),
        ]
    finally:
        d.remove(name)
        d.docker("volume", "rm", "-f", volume, check=False)
