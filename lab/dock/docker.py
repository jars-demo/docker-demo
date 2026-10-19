"""Small helpers over the docker CLI.

Everything the lab creates is named dockerlab-* (images: dockerlab/*) and labelled dockerlab=1,
so `dock clean` removes exactly what the lab made and nothing else on your machine.
"""

import json
import os
import re
import shutil
import socket
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.client import HTTPException
from pathlib import Path

LABEL = "dockerlab=1"
LAB = Path(__file__).resolve().parent.parent
EXERCISES = LAB / "exercises"
SOLUTIONS = LAB / "solutions"


class DockerError(RuntimeError):
    pass


def docker(
    *args: str,
    check: bool = True,
    timeout: float = 900,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["docker", *args],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env={**os.environ, **env} if env else None,
        cwd=cwd,
    )
    if check and proc.returncode != 0:
        raise DockerError(f"docker {' '.join(args[:2])} failed:\n{proc.stderr.strip()}")
    return proc


def available() -> str | None:
    """None when Docker is ready, otherwise what is wrong."""
    if shutil.which("docker") is None:
        return "the docker command is not installed"
    if docker("info", "--format", "{{.ServerVersion}}", check=False, timeout=30).returncode:
        return "the Docker engine is not running (start Docker Desktop, or the docker service)"
    return None


# ---------- builds ----------


@dataclass
class Step:
    name: str
    cached: bool = False
    seconds: float = 0.0


@dataclass
class Build:
    ok: bool
    seconds: float
    log: str
    steps: dict[str, Step] = field(default_factory=dict)

    def step(self, contains: str) -> Step | None:
        """The build step whose instruction contains this text."""
        return next((s for s in self.steps.values() if contains in s.name), None)

    def error(self) -> str:
        lines = [line for line in self.log.splitlines() if "ERROR" in line or "error:" in line]
        return lines[-1].strip() if lines else self.log.strip().splitlines()[-1:][0]


def parse_steps(log: str) -> dict[str, Step]:
    """Read BuildKit's plain progress output: '#7 [3/5] RUN ...', '#7 CACHED', '#7 DONE 1.2s'."""
    steps: dict[str, Step] = {}
    for line in log.splitlines():
        if match := re.match(r"#(\d+) \[(?:[\w-]+ )?\d+/\d+\] (.+)$", line):
            steps.setdefault(match[1], Step(match[2].strip()))
        elif (match := re.match(r"#(\d+) CACHED$", line)) and match[1] in steps:
            steps[match[1]].cached = True
        elif (match := re.match(r"#(\d+) DONE ([\d.]+)s$", line)) and match[1] in steps:
            steps[match[1]].seconds = float(match[2])
    return steps


def build(context: Path, tag: str, *extra: str, env: dict[str, str] | None = None) -> Build:
    start = time.perf_counter()
    proc = docker(
        "build",
        "--progress=plain",
        "--label",
        LABEL,
        "-t",
        tag,
        *extra,
        str(context),
        check=False,
        env=env,
    )
    log = proc.stderr + proc.stdout
    return Build(proc.returncode == 0, time.perf_counter() - start, log, parse_steps(log))


def context_bytes(context: Path) -> int:
    """How big the build context is, after .dockerignore: copy it into an empty image and weigh it.

    The build log's "transferring context" line is no use here: BuildKit only sends files that
    changed since the last build, so a second build of the same folder shows almost nothing.
    """
    tag = "dockerlab/context-probe"
    docker(
        "build",
        "-q",
        "--label",
        LABEL,
        "-t",
        tag,
        "-f",
        "-",
        str(context),
        stdin="FROM scratch\nCOPY . /context/\n",
    )
    try:
        return image_bytes(tag)
    finally:
        docker("image", "rm", "-f", tag, check=False)


def image_bytes(tag: str) -> int:
    return int(docker("image", "inspect", tag, "--format", "{{.Size}}").stdout.strip())


def mb(size: int) -> str:
    """A size the way docker prints it: decimal kB and MB."""
    return f"{size / 1e3:,.1f} kB" if abs(size) < 1e6 else f"{size / 1e6:,.1f} MB"


# ---------- containers ----------


def run(image: str, name: str, *flags: str, args: tuple[str, ...] = ()) -> None:
    remove(name)
    docker("run", "-d", "--name", name, "--label", LABEL, *flags, image, *args)


def remove(*names: str) -> None:
    if names:
        docker("rm", "-f", "-v", *names, check=False)


def inspect(name: str, template: str) -> str:
    proc = docker("inspect", name, "--format", template, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def running(name: str) -> bool:
    return inspect(name, "{{.State.Running}}") == "true"


def logs(name: str, tail: int = 20) -> str:
    proc = docker("logs", "--tail", str(tail), name, check=False)
    return (proc.stdout + proc.stderr).strip()


def host_port(name: str, port: int = 8000) -> int | None:
    """The host port Docker published for this container port, if any."""
    out = docker("port", name, f"{port}/tcp", check=False).stdout.strip().splitlines()
    return int(out[0].rsplit(":", 1)[1]) if out else None


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# ---------- http ----------


@dataclass
class Reply:
    status: int  # 0 when no HTTP answer came back at all
    body: dict | str

    def json(self) -> dict:
        return self.body if isinstance(self.body, dict) else {}


def http(url: str, method: str = "GET", data: dict | None = None, timeout: float = 5) -> Reply:
    payload = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(url, data=payload, method=method)
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return Reply(response.status, _decode(response.read()))
    except urllib.error.HTTPError as error:
        return Reply(error.code, _decode(error.read()))
    except (OSError, ValueError, HTTPException) as error:
        return Reply(0, f"{type(error).__name__}: {error}")


def _decode(raw: bytes) -> dict | str:
    try:
        return json.loads(raw)
    except ValueError:
        return raw.decode(errors="replace")


def wait_for(condition: Callable[[], bool], seconds: float, every: float = 0.25) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(every)
    return condition()


def wait_http(url: str, seconds: float, alive: Callable[[], bool] = lambda: True) -> Reply:
    """Poll url until it answers 200, the deadline passes, or alive() turns false."""
    deadline = time.monotonic() + seconds
    reply = http(url, timeout=2)
    while reply.status != 200 and time.monotonic() < deadline and alive():
        time.sleep(0.25)
        reply = http(url, timeout=2)
    return reply


# ---------- images, inside out ----------


def find_in_image(tag: str, needle: str) -> list[str]:
    """Every place the text appears in an image: its history, its config and its layer files."""
    found: list[str] = []
    history = docker("history", "--no-trunc", "--format", "{{.CreatedBy}}", tag).stdout
    if needle in history:
        found.append("docker history")
    if needle in docker("image", "inspect", tag).stdout:
        found.append("the image config")
    for layer in layers(tag):
        for member in layer.getmembers():
            if member.isfile() and member.size < 20_000_000:
                data = layer.extractfile(member)
                if data is not None and needle.encode() in data.read():
                    found.append(f"layer file {member.name}")
    return found


def files_in_image(tag: str, pattern: str) -> list[str]:
    """Paths in any layer whose name matches the pattern, including files a later layer deleted."""
    return [
        member.name
        for layer in layers(tag)
        for member in layer.getmembers()
        if re.search(pattern, member.name)
    ]


def layers(tag: str) -> Iterator[tarfile.TarFile]:
    """Each layer of an image as a tar archive, read from docker save."""
    with tempfile.TemporaryDirectory(prefix="dockerlab-") as tmp:
        archive = Path(tmp) / "image.tar"
        docker("save", "-o", str(archive), tag)
        with tarfile.open(archive) as outer:
            for member in outer.getmembers():
                blob = outer.extractfile(member) if member.isfile() else None
                if blob is None:
                    continue
                try:
                    with tarfile.open(fileobj=blob, mode="r:*") as layer:
                        yield layer
                except tarfile.TarError:  # the image config and manifests are JSON, not tar
                    continue


# ---------- exercises ----------


def exercise_dir(number: int) -> Path:
    matches = sorted(EXERCISES.glob(f"{number:02d}-*"))
    if not matches:
        raise SystemExit(f"no exercise {number}")
    return matches[0]


@contextmanager
def workcopy(path: Path) -> Iterator[Path]:
    """A throwaway copy of an exercise, so a check can edit files without touching yours."""
    with tempfile.TemporaryDirectory(prefix="dockerlab-") as tmp:
        target = Path(tmp) / path.name
        shutil.copytree(path, target)
        yield target


def clean() -> list[str]:
    """Remove every container, volume, network and image the lab created."""
    removed: list[str] = []
    for kind, listing, removal in [
        ("container", ["container", "ls", "-a", "--format", "{{.Names}}"], ["rm", "-f", "-v"]),
        ("volume", ["volume", "ls", "--format", "{{.Name}}"], ["volume", "rm", "-f"]),
        ("network", ["network", "ls", "--format", "{{.Name}}"], ["network", "rm"]),
    ]:
        names = [
            name
            for name in docker(*listing, "--filter", "name=dockerlab", check=False).stdout.split()
            if name.startswith("dockerlab")
        ]
        if names:
            docker(*removal, *names, check=False)
            removed += [f"{kind} {name}" for name in names]
    images = docker("images", "--format", "{{.Repository}}:{{.Tag}}", check=False).stdout.split()
    ours = [image for image in images if "dockerlab/" in image and not image.endswith(":<none>")]
    if ours:
        docker("image", "rm", "-f", *ours, check=False)
        removed += [f"image {image}" for image in ours]
    return removed
