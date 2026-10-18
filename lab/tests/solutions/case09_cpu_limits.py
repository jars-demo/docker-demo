"""Case 09: sixty-five workers in a two-CPU box.

In production the orders container is limited to 2 CPUs and 1 GB of memory. gunicorn sizes its
worker pool with the usual rule, two workers per CPU plus one. The container keeps being killed
a few seconds after it starts, with exit code 137 and OOMKilled: true.
Run it: uv run python -m dock run 9
"""

import math
from dataclasses import dataclass, field

WORKER_MB = 60
MASTER_MB = 80


@dataclass
class Machine:
    """What a process inside the container can find out about where it runs.

    cpu_count() reports the host's CPUs and process_cpu_count() the CPUs this process may run
    on. A CPU limit is neither: it is a time quota, in /sys/fs/cgroup/cpu.max, as
    "<quota> <period>" in microseconds, or "max <period>" for no limit."""

    host_cpus: int
    files: dict[str, str] = field(default_factory=dict)

    def cpu_count(self) -> int:
        return self.host_cpus

    def process_cpu_count(self) -> int:
        return self.host_cpus  # docker --cpus does not change the CPU affinity

    def read(self, path: str) -> str:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]


def limits(cpus: str, memory: str, host_cpus: int) -> Machine:
    return Machine(
        host_cpus,
        {"/sys/fs/cgroup/cpu.max": cpus + "\n", "/sys/fs/cgroup/memory.max": memory + "\n"},
    )


PRODUCTION = limits("200000 100000", str(1024 * 2**20), host_cpus=32)


def cpus(machine: Machine) -> int:
    """The CPUs this container may use: its cgroup quota, rounded up, or the host's."""
    try:
        quota, period = machine.read("/sys/fs/cgroup/cpu.max").split()
    except FileNotFoundError:
        return machine.cpu_count()
    if quota == "max":
        return machine.cpu_count()
    return max(1, math.ceil(int(quota) / int(period)))


def worker_count(machine: Machine) -> int:
    """gunicorn's rule of thumb: two workers per CPU, plus one."""
    return cpus(machine) * 2 + 1


def memory_limit_mb(machine: Machine) -> float:
    raw = machine.read("/sys/fs/cgroup/memory.max").strip()
    return math.inf if raw == "max" else int(raw) / 2**20


def boot(machine: Machine, count=None) -> tuple[int, int | None, float]:
    """Start the master, then the workers one by one. Returns (workers, oom_at, peak_mb)."""
    workers = (count or worker_count)(machine)
    limit = memory_limit_mb(machine)
    used = MASTER_MB
    for n in range(1, workers + 1):
        used += WORKER_MB
        if used > limit:
            return workers, n, used
    return workers, None, used


def run() -> None:
    workers, oom_at, used = boot(PRODUCTION)
    print(f"cpu.max inside the container: {PRODUCTION.read('/sys/fs/cgroup/cpu.max').strip()}")
    print(f"os.cpu_count() inside the container: {PRODUCTION.cpu_count()}")
    print(f"gunicorn workers: {workers} (2 x {PRODUCTION.cpu_count()} + 1)")
    if oom_at:
        limit = memory_limit_mb(PRODUCTION)
        print(f"worker {oom_at} took memory to {used:.0f} MB, over the {limit:.0f} MB limit")
        print("the kernel kills the container: OOMKilled true, exit code 137")
