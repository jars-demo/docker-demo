"""02: the build context, and keeping secrets and clutter out of an image."""

import os
import secrets
from pathlib import Path

from dock import docker as d

TITLE = "The secret that shipped with the image"
HINTS = [
    "Read the line 'transferring context' in the build output. What is being sent, and why?",
    "COPY . . copies everything the build context holds. The context is the whole folder.",
    "A .dockerignore file keeps .env, testdata/ and tests/ out of the context, and so out of "
    "the image. Pass the key at run time with --env-file .env.",
]
TAG = "dockerlab/02"
BASE = "python:3.13.16-slim-trixie"
SNAPSHOTS = 4
SNAPSHOT_MB = 24


def prepare(path: Path) -> None:
    """Create what a real project folder has but git does not: a .env and a test data dump."""
    env = path / ".env"
    if not env.exists():
        env.write_text(f"API_KEY=sk_dockerlab_{secrets.token_hex(12)}\n")
    data = path / "testdata"
    data.mkdir(exist_ok=True)
    for index in range(1, SNAPSHOTS + 1):
        snapshot = data / f"snapshot-{index}.db"
        if not snapshot.exists() or snapshot.stat().st_size != SNAPSHOT_MB * 1_000_000:
            snapshot.write_bytes(os.urandom(SNAPSHOT_MB * 1_000_000))


def api_key(path: Path) -> str:
    return (path / ".env").read_text().strip().split("=", 1)[1]


def run(path: Path) -> None:
    prepare(path)
    build = d.build(path, TAG)
    if not build.ok:
        print(f"the build failed: {build.error()}")
        return
    added = d.image_bytes(TAG) - d.image_bytes(BASE)
    print(f"build context: {d.mb(d.context_bytes(path))}, all of it sent to every fresh builder")
    print(f"image size: {d.mb(d.image_bytes(TAG))}, of which this Dockerfile added {d.mb(added)}")
    print()
    print("$ docker run --rm dockerlab/02 cat .env")
    print(d.docker("run", "--rm", TAG, "cat", ".env", check=False).stdout.strip())
    print()
    print("Anyone who can pull this image can read the API key.")


def check(path: Path) -> list[tuple[str, bool]]:
    prepare(path)
    name = "dockerlab-02-check"
    tag = f"{TAG}:check"
    build = d.build(path, tag)
    if not build.ok:
        return [(f"the image builds ({build.error()})", False)]
    sent = d.context_bytes(path)
    added = d.image_bytes(tag) - d.image_bytes(BASE)
    env_files = d.files_in_image(tag, r"(^|/)\.env$")
    key_found = d.find_in_image(tag, api_key(path))
    d.run(tag, name, "-p", "127.0.0.1::8000", "--env-file", str(path / ".env"))
    try:
        port = d.host_port(name)
        health = d.wait_http(f"http://127.0.0.1:{port}/healthz", 10) if port else d.Reply(0, "")
        return [
            (f"the build context is under 1 MB (it holds {d.mb(sent)})", sent < 1_000_000),
            ("no .env file in any layer of the image", not env_files),
            (
                "the API key's value appears nowhere in the image"
                + (f" (found in {', '.join(key_found)})" if key_found else ""),
                not key_found,
            ),
            (f"the image adds under 1 MB to its base (adds {d.mb(added)})", added < 1_000_000),
            (
                "the API still gets API_KEY at run time, from --env-file",
                health.status == 200 and health.json().get("api_key_set") is True,
            ),
        ]
    finally:
        d.remove(name)
