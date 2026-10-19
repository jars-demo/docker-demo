"""Experiments that measure real Docker behaviour on your machine.

Each one builds or runs real containers, prints what it measured, and cleans up after itself.
"""

import statistics
import subprocess
import sys
import time

from dock import docker as d

SLIM = "python:3.13.16-slim-trixie"
RUNS = 5


def timed(command: list[str]) -> float:
    start = time.perf_counter()
    subprocess.run(command, capture_output=True, check=True)
    return time.perf_counter() - start


def startup() -> None:
    """How long a container takes to start, next to a plain process."""
    print(f"median of {RUNS} runs each\n")
    timed(["docker", "run", "--rm", SLIM, "true"])  # warm up: the image is on disk
    rows = [
        (
            "a process on this machine: python -c pass",
            [timed([sys.executable, "-c", "pass"]) for _ in range(RUNS)],
        ),
        (
            "a container: docker run --rm python:slim true",
            [timed(["docker", "run", "--rm", SLIM, "true"]) for _ in range(RUNS)],
        ),
        (
            "a container running Python: docker run --rm python:slim python -c pass",
            [timed(["docker", "run", "--rm", SLIM, "python", "-c", "pass"]) for _ in range(RUNS)],
        ),
    ]
    for label, samples in rows:
        print(f"  {statistics.median(samples) * 1000:7.0f} ms  {label}")
    print("\nA container is a process with walls around it. Most of the extra time is Docker")
    print("setting up the walls: namespaces, a network interface, the filesystem layers.")


def layers() -> None:
    """Deleting a file in a later layer does not make the image smaller."""
    blob = "head -c 100000000 /dev/urandom > /blob"
    variants = [
        (
            "create a 100 MB file in one RUN, delete it in the next",
            f"FROM {SLIM}\nRUN {blob}\nRUN rm /blob\n",
        ),
        ("create and delete it in the same RUN", f"FROM {SLIM}\nRUN {blob} && rm /blob\n"),
    ]
    base = d.image_bytes(SLIM)
    print(f"base image {SLIM}: {d.mb(base)}\n")
    for index, (label, dockerfile) in enumerate(variants, 1):
        tag = f"dockerlab/try-layers-{index}"
        d.docker(
            "build",
            "-q",
            "--label",
            d.LABEL,
            "-t",
            tag,
            "-f",
            "-",
            ".",
            stdin=dockerfile,
            cwd=d.LAB / "dock",
        )
        print(f"  adds {d.mb(d.image_bytes(tag) - base):>9}  {label}")
        d.docker("image", "rm", "-f", tag, check=False)
    print("\nEvery layer is a diff stacked on the one below. A later layer can hide a file,")
    print("but the layer that added it still ships with the image.")


def sizes() -> None:
    """The same small server on three base images."""
    server = d.exercise_dir(4) / "server.py"
    print("the API from exercise 04, on three Python 3.13.16 bases\n")
    for base in ("python:3.13.16-trixie", SLIM, "python:3.13.16-alpine"):
        tag = "dockerlab/try-sizes"
        build = d.docker(
            "build",
            "-q",
            "--label",
            d.LABEL,
            "-t",
            tag,
            "-f",
            "-",
            str(server.parent),
            stdin=f'FROM {base}\nWORKDIR /app\nCOPY server.py .\nCMD ["python", "server.py"]\n',
            check=False,
        )
        if build.returncode:
            print(f"  could not build on {base}: {build.stderr.strip().splitlines()[-1]}")
            continue
        size = d.image_bytes(tag)
        tools = d.docker(
            "run",
            "--rm",
            "--entrypoint",
            "sh",
            tag,
            "-c",
            "for t in gcc curl apt-get apk; do command -v $t >/dev/null && echo $t; done; true",
            check=False,
        ).stdout.split()
        print(f"  {d.mb(size):>10}  {base:<28} tools: {', '.join(tools) or 'none'}")
        d.docker("image", "rm", "-f", tag, check=False)
    print("\nSmaller images pull faster, start sooner and carry fewer packages to patch.")
    print("Alpine uses musl instead of glibc: test your dependencies on it before you switch.")


def network() -> None:
    """Containers find each other by name on a user-defined network, not on the default one."""
    lookup = "import socket; print(socket.gethostbyname('dockerlab-try-server'))"
    names = ["dockerlab-try-server", "dockerlab-try-client"]
    try:
        for network_flags, label in [
            ([], "the default bridge network"),
            (["--network", "dockerlab-try-net"], "a user-defined network"),
        ]:
            d.remove(*names)
            if network_flags:
                d.docker("network", "create", "--label", d.LABEL, "dockerlab-try-net", check=False)
            for name in names:
                d.run(SLIM, name, *network_flags, args=("sleep", "60"))
            result = d.docker("exec", names[1], "python", "-c", lookup, check=False)
            answer = result.stdout.strip() or result.stderr.strip().splitlines()[-1]
            print(f"  on {label}: dockerlab-try-server resolves to {answer}")
    finally:
        d.remove(*names)
        d.docker("network", "rm", "dockerlab-try-net", check=False)
    print("\nUser-defined networks, which Compose creates for you, run Docker's DNS server.")
    print("On the default bridge network, containers can only reach each other by IP address.")


EXPERIMENTS = {"startup": startup, "layers": layers, "sizes": sizes, "network": network}
