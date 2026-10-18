"""Four experiments to run on your own machine. None of them needs Docker. Every number they
print is measured or computed there and then.

context   how long it takes to pack and hash a build context, with and without .dockerignore
digest    which changes alter a layer's digest when the file contents stay the same
ports     what a server bound to 127.0.0.1 or to 0.0.0.0 accepts, over real sockets
stop      SIGTERM, a grace period and SIGKILL against real processes, with and without a shell
"""

import gzip
import hashlib
import io
import os
import platform
import random
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

from dock.engine import context as kept


def describe() -> str:
    return f"Python {sys.version.split()[0]}, {platform.system()}, {os.cpu_count()} CPUs"


# context

TREE = {  # folder: (files, bytes each). A real project after a few months.
    "src": (40, 4_000),
    "templates": (12, 3_000),
    ".git/objects": (1_500, 12_000),
    "node_modules": (3_000, 9_000),
    "data": (2, 20_000_000),
}
IGNORE = ".git\nnode_modules\ndata\n"


def make_tree(root: Path) -> dict[str, str]:
    rng = random.Random(7)
    files = {}
    for folder, (count, size) in TREE.items():
        (root / folder).mkdir(parents=True, exist_ok=True)
        for n in range(count):
            relative = f"{folder}/f{n:05d}.bin"
            (root / relative).write_bytes(rng.randbytes(size))
            files[relative] = ""
    (root / "Dockerfile").write_text("FROM python:3.13-slim\n")
    files["Dockerfile"] = ""
    return files


def pack(root: Path, names: list[str]) -> tuple[int, str]:
    """Tar the files, as the client does before sending a context, and hash the tar."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name in names:
            tar.add(root / name, arcname=name)
    data = buffer.getvalue()
    return len(data), hashlib.sha256(data).hexdigest()


def timed(fn, rounds: int = 3) -> float:
    times = []
    for _ in range(rounds):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return statistics.median(times)


def context() -> None:
    print(describe())
    print("A pretend project: source, templates, a .git folder, node_modules and two data dumps.")
    print()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        files = make_tree(root)
        everything = sorted(files)
        ignored = sorted(kept(files, IGNORE))
        print(f"  {'context':<24}{'files':>8}{'tar size':>12}{'tar + sha256':>15}")
        for label, names in (("everything", everything), ("with .dockerignore", ignored)):
            size, _ = pack(root, names)
            seconds = timed(lambda names=names: pack(root, names))
            print(f"  {label:<24}{len(names):>8}{size / 1e6:>9.1f} MB{seconds * 1e3:>12.0f} ms")
    print()
    print(".dockerignore here: .git, node_modules, data. The client sends this tar on every build,")
    print("and COPY . . hashes all of it to decide whether the cache still holds.")


# digest


def layer(root: Path, names: list[str], mtime: float | None) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name in names:
            info = tar.gettarinfo(root / name, arcname=name)
            if mtime is not None:
                info.mtime = mtime
                info.uid = info.gid = 0
                info.uname = info.gname = ""
            with open(root / name, "rb") as handle:
                tar.addfile(info, handle)
    return buffer.getvalue()


def short(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()[:16]


def digest() -> None:
    print(describe())
    print("One layer: the same three files, with the same bytes, packed in different ways.")
    print()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        names = ["app.py", "menu.html", "requirements.txt"]
        for name in names:
            (root / name).write_text(f"contents of {name}\n")
        now = time.time()
        for name in names:
            os.utime(root / name, (now, now))
        rows = [("as found", layer(root, names, None))]
        rows.append(("as found, packed again", layer(root, names, None)))
        rows.append(("names in another order", layer(root, list(reversed(names)), None)))
        os.utime(root / "app.py", (now + 60, now + 60))
        rows.append(("app.py touched, bytes unchanged", layer(root, names, None)))
        rows.append(("mtime set to 0, names sorted", layer(root, sorted(names), 0)))
        os.utime(root / "app.py", (now + 3600, now + 3600))
        rows.append(("touched again, mtime set to 0", layer(root, sorted(names), 0)))
        clean = rows[-1][1]
        rows.append(("gzip of that, header time now", gzip.compress(clean, mtime=int(now))))
        rows.append(("gzip of that, header time + 1 s", gzip.compress(clean, mtime=int(now) + 1)))
        rows.append(("gzip of that, header time 0", gzip.compress(clean, mtime=0)))
        rows.append(("gzip of that, header time 0 again", gzip.compress(clean, mtime=0)))
        print(f"  {'how the layer was packed':<36}digest")
        for label, data in rows:
            print(f"  {label:<36}{short(data)}")
    print()
    print("Same bytes, different digest, whenever a timestamp or the order of the files changes.")
    print("Pin those (SOURCE_DATE_EPOCH, sorted files) and the digest only moves with the content.")


# ports


def own_address() -> str | None:
    """This machine's address on its main network. Connecting a UDP socket sends nothing."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("10.255.255.255", 1))
        address = probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()
    return None if address.startswith("127.") else address


def attempt_connect(host: str, port: int) -> tuple[str, float]:
    """Connect five times after one warm-up, and return the result and the median time."""
    times, result = [], ""
    for round_ in range(6):
        start = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=1.0):
                result = "accepted"
        except ConnectionRefusedError:
            result = "refused"
        except OSError as error:
            result = type(error).__name__
        if round_:
            times.append(time.perf_counter() - start)
    return result, statistics.median(times)


def ports() -> None:
    print(describe())
    outside = own_address()
    print(f"loopback 127.0.0.1, and this machine's own address: {outside or 'none found'}")
    print()
    servers = []
    for bind in ("127.0.0.1", "0.0.0.0"):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((bind, 0))
        server.listen(16)
        servers.append((bind, server))
    print(f"  {'server bound to':<18}{'client connects to':<22}{'result':<12}{'time':>10}")
    try:
        for bind, server in servers:
            port = server.getsockname()[1]
            targets = ["127.0.0.1"] + ([outside] if outside else [])
            for target in targets:
                result, seconds = attempt_connect(target, port)
                print(f"  {bind:<18}{target:<22}{result:<12}{seconds * 1e6:>7.0f} µs")
    finally:
        for _, server in servers:
            server.close()
    print()
    print("A container's published port arrives on its bridge address, like the second row of")
    print("each pair here. Only a server bound to 0.0.0.0 (or to that address) accepts it.")


# stop

HANDLES = """
import signal, sys, time
def done(*_):
    time.sleep(0.2)  # finish the order in hand
    sys.exit(0)
signal.signal(signal.SIGTERM, done)
print("ready", flush=True)
while True:
    time.sleep(0.05)
"""

IGNORES = """
import signal, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)  # what PID 1 without a handler amounts to
print("ready", flush=True)
while True:
    time.sleep(0.05)
"""

CHILD = """
import os, signal, sys, time
def done(*_):
    time.sleep(0.2)  # finish the order in hand
    sys.exit(0)
signal.signal(signal.SIGTERM, done)
print(os.getpid(), flush=True)
while True:
    time.sleep(0.05)
"""

GRACE = 2.0


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def stop_one(command: list[str], child_pid_first: bool) -> tuple[float, str, str]:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True, start_new_session=True)
    first = process.stdout.readline().strip()
    child = int(first) if child_pid_first else None
    start = time.perf_counter()
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=GRACE)
        how = f"exit {process.returncode}" if process.returncode >= 0 else "SIGTERM"
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        how = "SIGKILL"
    took = time.perf_counter() - start
    app = "finished its work" if how == "exit 0" else "killed mid-work"
    if child is not None and child != process.pid:
        time.sleep(0.3)
        if alive(child):
            app = "never told, still running"
            os.kill(child, signal.SIGKILL)  # tidy up the orphan
    return took, how, app


def stop() -> None:
    print(describe())
    if os.name != "posix" or shutil.which("sh") is None:
        print("This experiment needs POSIX signals and sh. Run it on Linux or macOS, or in WSL.")
        return
    print(f"Each process gets SIGTERM, then SIGKILL if it is still running after {GRACE:.0f} s.")
    print()
    python = sys.executable
    rows = [
        ("python, handles SIGTERM", [python, "-c", HANDLES], False),
        ("python, SIGTERM ignored", [python, "-c", IGNORES], False),
        ("sh -c 'python ...; true'", ["sh", "-c", f'"{python}" -c "$0"; true', CHILD], True),
        ("sh -c 'exec python ...'", ["sh", "-c", f'exec "{python}" -c "$0"', CHILD], True),
    ]
    print(f"  {'how the worker runs':<28}{'stop took':>10}   {'ended by':<10}{'the worker'}")
    for label, command, wrapped in rows:
        took, how, app = stop_one(command, wrapped)
        print(f"  {label:<28}{took:>8.2f} s   {how:<10}{app}")
    print()
    print("Here the shell dies and leaves the worker running. As PID 1 in a container, the shell")
    print("would ignore SIGTERM instead, like row two. Either way the worker is never told.")


EXPERIMENTS = {
    "context": context,
    "digest": digest,
    "ports": ports,
    "stop": stop,
}
