"""03: layers and the build cache."""

import re
import secrets
from pathlib import Path

from dock import docker as d

TITLE = "Every rebuild reinstalls everything"
HINTS = [
    "Look at the second build. Which is the first step that ran instead of coming from the cache?",
    "A COPY step misses the cache when any file it copies changes. COPY . . copies every file.",
    "Copy requirements.txt on its own and install it, then COPY . . for the code.",
]
TAG = "dockerlab/03"


def bump_version(path: Path) -> str:
    """Change the code the way a commit would: the next VERSION.

    The comment makes every change unique, so no earlier build can have cached it.
    """
    main = path / "app" / "main.py"
    text = main.read_text()
    current = int(re.search(r'VERSION = "(\d+)"', text)[1])  # type: ignore[index]
    text = text.replace(f'VERSION = "{current}"', f'VERSION = "{current + 1}"')
    main.write_text(f"{text}# commit {secrets.token_hex(4)}\n")
    return str(current + 1)


def show(build: d.Build) -> None:
    for step in build.steps.values():
        if step.name.startswith("FROM"):
            state = "base image"
        else:
            state = "cached" if step.cached else f"ran   {step.seconds:5.1f} s"
        print(f"  {state:<14} {step.name[:70]}")
    print(f"  total {build.seconds:.1f} s")


def run(path: Path) -> None:
    with d.workcopy(path) as work:
        print("build 1: the first build of this Dockerfile")
        first = d.build(work, TAG)
        if not first.ok:
            print(f"the build failed: {first.error()}")
            return
        show(first)
        bump_version(work)
        print()
        print("build 2: after changing one line in app/main.py")
        second = d.build(work, TAG)
        show(second)
        install = second.step("pip install")
        print()
        if install and not install.cached:
            print(
                f"One changed line of code reinstalled every dependency: {install.seconds:.1f} s "
                "of pip install on every commit."
            )


def check(path: Path) -> list[tuple[str, bool]]:
    name = "dockerlab-03-check"
    tag = f"{TAG}:check"
    with d.workcopy(path) as work:
        first = d.build(work, tag)
        if not first.ok:
            return [(f"the image builds ({first.error()})", False)]
        version = bump_version(work)
        code_change = d.build(work, tag)
        install = code_change.step("pip install")
        d.run(tag, name, "-p", "127.0.0.1::8000")
        try:
            port = d.host_port(name)
            url = f"http://127.0.0.1:{port}/version"
            reply = d.wait_http(url, 20, lambda: d.running(name)) if port else d.Reply(0, "")
        finally:
            d.remove(name)
        with (work / "requirements.txt").open("a") as requirements:
            requirements.write(f"# dependency change {secrets.token_hex(4)}\n")
        deps_change = d.build(work, tag)
        reinstall = deps_change.step("pip install")
    return [
        (
            f"after a code change, pip install comes from the cache "
            f"(the rebuild took {code_change.seconds:.1f} s)",
            install is not None and install.cached,
        ),
        (
            f"the new code is in the image (/version says {reply.json().get('version', '-')})",
            reply.json().get("version") == version,
        ),
        (
            "a change to requirements.txt still re-runs pip install",
            reinstall is not None and not reinstall.cached,
        ),
    ]
