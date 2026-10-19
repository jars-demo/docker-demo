"""07: build-time secrets."""

import secrets
from pathlib import Path

from dock import docker as d

TITLE = "The token in the image history"
HINTS = [
    "Run docker history --no-trunc on the image and read the RUN line.",
    "Build arguments are recorded with every RUN step that uses them. Anyone who can pull the "
    "image can read them.",
    "Mount the token as a build secret for that one RUN step: "
    "RUN --mount=type=secret,id=package_token,env=PACKAGE_TOKEN ...",
]
TAG = "dockerlab/07"


def build(path: Path, tag: str, token: str) -> d.Build:
    """Offer the token both ways, as a build argument and as a secret. The Dockerfile decides."""
    return d.build(
        path,
        tag,
        "--build-arg",
        "PACKAGE_TOKEN",
        "--secret",
        "id=package_token,env=PACKAGE_TOKEN",
        env={"PACKAGE_TOKEN": token},
    )


def new_token() -> str:
    return f"pkg_dockerlab_{secrets.token_hex(12)}"


def run(path: Path) -> None:
    token = new_token()
    result = build(path, TAG, token)
    if not result.ok:
        print(f"the build failed: {result.error()}")
        return
    print(f"built with PACKAGE_TOKEN={token}")
    print()
    print("$ docker history --no-trunc dockerlab/07 | grep PACKAGE_TOKEN")
    history = d.docker("history", "--no-trunc", "--format", "{{.CreatedBy}}", TAG).stdout
    for line in history.splitlines():
        if token in line:
            print(f"  {line.strip()[:150]}")
    print()
    print(f"the token is in: {', '.join(d.find_in_image(TAG, token)) or 'nowhere'}")


def check(path: Path) -> list[tuple[str, bool]]:
    name, tag, token = "dockerlab-07-check", f"{TAG}:check", new_token()
    result = build(path, tag, token)
    if not result.ok:
        return [(f"the image builds ({result.error()})", False)]
    found = d.find_in_image(tag, token)
    d.run(tag, name, "-p", "127.0.0.1::8000")
    try:
        port = d.host_port(name)
        health = d.wait_http(f"http://127.0.0.1:{port}/healthz", 10, lambda: d.running(name))
        return [
            (
                "the private package was fetched during the build",
                health.json().get("billing_sdk") == "2.4.1",
            ),
            ("the token is not in docker history", "docker history" not in found),
            ("the token is not in the image config", "the image config" not in found),
            (
                "the token is not in any layer's files",
                not any(place.startswith("layer") for place in found),
            ),
        ]
    finally:
        d.remove(name)
