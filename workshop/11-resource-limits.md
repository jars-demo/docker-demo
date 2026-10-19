# CPU and memory limits

> `--cpus 1` does not hide the host's other CPUs from your program. It sets a quota, and a program that sizes itself by counting CPUs will start too many workers and run out of memory.

**Time:** 25 minutes

## Goal

By the end of this chapter you can set CPU and memory limits, read them from inside a container through cgroups, and recognise an out-of-memory kill.

## The idea

### Limits are cgroups

`docker run --cpus 1 --memory 256m` puts the container in a **cgroup** with two limits:

- **CPU:** a quota of CPU time per period. `--cpus 1` means 100,000 microseconds of CPU time per 100,000-microsecond period: one CPU's worth, spread over any of the host's CPUs. `--cpus 1.5` gives 150,000.
- **Memory:** a hard ceiling on the memory the container's processes may use. Over it, the kernel's out-of-memory (OOM) killer kills a process in the container with SIGKILL.

Docker also allows swap equal to the memory limit unless you set `--memory-swap` to the same value. With swap, an app over its limit slows to a crawl instead of being killed. The lab turns swap off, as most production setups do.

### What the program sees

The limits do not change what the system reports. `/proc/cpuinfo` still lists every host CPU, and so does `os.cpu_count()`:

```text
$ docker run --rm --cpus 1 python:3.13.16-slim-trixie python -c "import os; print(os.cpu_count(), os.process_cpu_count())"
4 4
```

`os.process_cpu_count()` only honours CPU affinity (`--cpuset-cpus`), not the quota. The quota is published in the cgroup filesystem:

| cgroup version | file | example with `--cpus 1` | no limit |
| --- | --- | --- | --- |
| v2 (most current Linux) | `/sys/fs/cgroup/cpu.max` | `100000 100000` | `max 100000` |
| v1 (older hosts, some Docker Desktop setups) | `/sys/fs/cgroup/cpu/cpu.cfs_quota_us` and `cpu.cfs_period_us` | `100000` and `100000` | `-1` |

The machine this lab was written on runs cgroup v1, so code that only reads `cpu.max` would quietly fall back to the host count there. Read both.

### Why it matters

Servers size their pools from the CPU count: gunicorn's usual advice is `2 x CPUs + 1` workers, and many thread pools default to the CPU count. In a container on a 64-CPU node with `--cpus 2`, that is 129 workers where 5 make sense: lots of memory, constant context switching, and CPU throttling as the quota runs out within each period.

## The exercise

Open `lab/exercises/11-resource-limits/`. The server starts `2 x CPUs + 1` worker processes, and each worker holds 48 MB, the way a real one holds a model or a cache. If a worker dies, the server shuts down so the orchestrator can restart it.

```python
def available_cpus() -> int:
    """How many CPUs this process may use."""
    return os.cpu_count() or 1
```

```bash
uv run python -m dock run 11
```

```text
the Docker host has 4 CPUs
$ docker run --cpus 1 --memory 256m --memory-swap 256m dockerlab/11
4 CPUs available: starting 9 workers of 48 MB
worker 8 died (exit code -9), shutting down

container: exited, exit code 1, OOMKilled=true
```

Nine workers of 48 MB do not fit in 256 MB. The kernel killed one with SIGKILL (-9), and Docker recorded `OOMKilled=true`.

## Reasoning towards the fix

The container has one CPU's worth of time, so the server should start 3 workers: about 150 MB. Rewrite `available_cpus()` to:

1. read the quota and period from `cpu.max` (v2), or from the two v1 files
2. return `ceil(quota / period)` when there is a quota, at least 1
3. fall back to `os.process_cpu_count()` when there is no quota, and never return more than that

## Check your fix

```bash
uv run python -m dock check 11
```

As shipped:

```text
  FAIL  with --cpus 1 --memory 256m it stays up (it was OOM-killed)
  FAIL  it starts 3 workers for 1 CPU (started -)
  FAIL  with --cpus 2 it starts 5 workers (started 9)
  PASS  with no CPU limit it uses all 4 host CPUs (started 9 workers)
```

The checker runs your image three times: with one CPU, with two, and with no limit. Hard-coding 3 workers passes the first two checks and fails the third, and ignoring the no-limit case fails the last.

## In production

- Many runtimes now read cgroups for you: the JVM since Java 10, Go's `GOMAXPROCS` with Go 1.25, .NET. Python does not. Set worker counts explicitly from configuration, or compute them as above.
- Set memory **requests and limits** in Kubernetes. A pod without a memory limit can take memory from its neighbours until the node itself runs out.
- Exit code 137 with `OOMKilled=true` is a memory kill. Exit code 137 without it is usually `docker stop`'s SIGKILL (chapter 09).
- CPU limits cause throttling rather than kills. Watch the cgroup's `nr_throttled` counter, or your platform's throttling metric, when latency spikes for no visible reason.

## Key points

- `--cpus` sets a CPU time quota. It does not change how many CPUs a program sees.
- `--memory` is a hard ceiling. Over it, the kernel kills a process with SIGKILL.
- Read the quota from the cgroup filesystem, v2 and v1, and size pools from it.
- `OOMKilled=true` in `docker inspect` tells a memory kill apart from other exits.
