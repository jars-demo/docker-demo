"""11: CPU and memory limits, as the process inside sees them."""

import time
from pathlib import Path

from dock import docker as d

TITLE = "Nine workers in a one-CPU container"
HINTS = [
    "Read the first log line. How many CPUs does the server think it has?",
    "os.cpu_count() counts the host's CPUs. --cpus sets a quota in the cgroup filesystem.",
    "Read the quota: /sys/fs/cgroup/cpu.max on cgroup v2, cpu/cpu.cfs_quota_us and "
    "cpu/cpu.cfs_period_us on v1. CPUs = ceil(quota / period); no quota means no limit.",
]
TAG = "dockerlab/11"
ONE_CPU = ["--cpus", "1", "--memory", "256m", "--memory-swap", "256m"]
TWO_CPUS = ["--cpus", "2", "--memory", "512m", "--memory-swap", "512m"]


def start(tag: str, name: str, *limits: str) -> dict:
    """Run with these limits. Returns /healthz once it answers, or {} if it died first."""
    d.run(tag, name, "-p", "127.0.0.1::8000", *limits)
    port = d.host_port(name)
    if port is None:
        return {}
    reply = d.wait_http(f"http://127.0.0.1:{port}/healthz", 15, lambda: d.running(name))
    time.sleep(2)  # give the workers time to fill their memory
    return reply.json() if reply.status == 200 and d.running(name) else {}


def run(path: Path) -> None:
    name = "dockerlab-11"
    build = d.build(path, TAG)
    if not build.ok:
        print(f"the build failed: {build.error()}")
        return
    host_cpus = d.docker("info", "--format", "{{.NCPU}}").stdout.strip()
    print(f"the Docker host has {host_cpus} CPUs")
    print(f"$ docker run {' '.join(ONE_CPU)} dockerlab/11")
    try:
        start(TAG, name, *ONE_CPU)
        time.sleep(1)
        print(d.logs(name))
        print()
        state = d.inspect(
            name, "{{.State.Status}}, exit code {{.State.ExitCode}}, OOMKilled={{.State.OOMKilled}}"
        )
        print(f"container: {state}")
    finally:
        d.remove(name)


def check(path: Path) -> list[tuple[str, bool]]:
    name, tag = "dockerlab-11-check", f"{TAG}:check"
    build = d.build(path, tag)
    if not build.ok:
        return [(f"the image builds ({build.error()})", False)]
    host_cpus = int(d.docker("info", "--format", "{{.NCPU}}").stdout.strip())
    try:
        one = start(tag, name, *ONE_CPU)
        oom = d.inspect(name, "{{.State.OOMKilled}}") == "true"
        two = start(tag, name, *TWO_CPUS)
        unlimited = start(tag, name)
        return [
            (
                "with --cpus 1 --memory 256m it stays up" + (" (it was OOM-killed)" if oom else ""),
                bool(one) and not oom,
            ),
            (
                f"it starts 3 workers for 1 CPU (started {one.get('workers', '-')})",
                one.get("workers") == 3,
            ),
            (
                f"with --cpus 2 it starts 5 workers (started {two.get('workers', '-')})",
                two.get("workers") == 5,
            ),
            (
                f"with no CPU limit it uses all {host_cpus} host CPUs "
                f"(started {unlimited.get('workers', '-')} workers)",
                unlimited.get("workers") == host_cpus * 2 + 1,
            ),
        ]
    finally:
        d.remove(name)
