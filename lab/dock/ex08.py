"""08: multi-stage builds, smaller and safer images."""

from pathlib import Path

from dock import docker as d

TITLE = "1.1 GB to ship one small API"
HINTS = [
    "Run docker history on the image. Which layer is the biggest, and does the API need it?",
    "The compiler and headers are only needed while psycopg-c builds. Build in one stage, run in "
    "another, and copy across only the result.",
    "Install into a virtual environment in a build stage on the full image. In a slim stage, "
    "install libpq5, copy /opt/venv across, and switch to a non-root USER.",
]
TAG = "dockerlab/08"
LIMIT = 200_000_000
TOOLS = "for tool in gcc cc make pg_config; do command -v $tool; done; true"


def facts(tag: str) -> tuple[int, list[str], str]:
    tools = d.docker("run", "--rm", "--entrypoint", "sh", tag, "-c", TOOLS, check=False)
    user = d.docker("run", "--rm", "--entrypoint", "id", tag, "-u", check=False).stdout.strip()
    return d.image_bytes(tag), tools.stdout.split(), user


def run(path: Path) -> None:
    build = d.build(path, TAG)
    if not build.ok:
        print(f"the build failed: {build.error()}")
        return
    size, tools, user = facts(TAG)
    print(f"image size: {d.mb(size)}")
    print(f"build tools inside: {', '.join(tools) or 'none'}")
    print(f"runs as uid: {user}")
    print()
    print("$ docker history dockerlab/08 (largest layers)")
    history = d.docker("history", "--no-trunc", "--format", "{{.Size}}\t{{.CreatedBy}}", TAG).stdout
    rows = [line.split("\t", 1) for line in history.splitlines() if "\t" in line]
    for size_text, created in rows:
        if size_text.endswith("GB") or (size_text.endswith("MB") and float(size_text[:-2]) >= 10):
            command = " ".join(created.replace("/bin/sh -c ", "").split())
            print(f"  {size_text:>8}  {command[:84]}")


def check(path: Path) -> list[tuple[str, bool]]:
    name, tag = "dockerlab-08-check", f"{TAG}:check"
    build = d.build(path, tag)
    if not build.ok:
        return [(f"the image builds ({build.error()})", False)]
    size, tools, user = facts(tag)
    d.run(tag, name, "-p", "127.0.0.1::8000")
    try:
        port = d.host_port(name)
        health = d.wait_http(f"http://127.0.0.1:{port}/healthz", 15, lambda: d.running(name))
        impl = health.json().get("psycopg", "-")
        return [
            (f"the image is under {d.mb(LIMIT)} (it is {d.mb(size)})", size < LIMIT),
            (
                f"no compiler or build tools in the final image ({', '.join(tools) or 'none'})",
                not tools,
            ),
            (f"it runs as a non-root user (uid {user or '-'})", user not in ("", "0")),
            ("the API starts and answers /healthz", health.status == 200),
            (f"psycopg uses its compiled C build (loaded: {impl})", impl == "c"),
        ]
    finally:
        d.remove(name)
