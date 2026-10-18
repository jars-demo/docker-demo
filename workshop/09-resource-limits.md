# Resource limits

> A container is a process with a budget. Most runtimes do not read the budget, so they plan for the whole machine and get killed for it.

**Time:** 20 minutes

## Goal

Know what CPU and memory limits are under the hood, why `os.cpu_count()` lies inside a container, what exit code 137 means, and how to size a worker pool from the limits the container really has.

## The case

```bash
uv run python -m dock run 9
```

```text
cpu.max inside the container: 200000 100000
os.cpu_count() inside the container: 32
gunicorn workers: 65 (2 x 32 + 1)
worker 16 took memory to 1040 MB, over the 1024 MB limit
the kernel's OOM killer steps in: SIGKILL, exit code 137 (128 + 9)
```

In production the orders container gets 2 CPUs and 1 GB of memory. gunicorn sizes its pool with the usual rule, two workers per CPU plus one. It counts 32 CPUs, starts 65 workers at 60 MB each, and is killed as the sixteenth one starts. Open `lab/cases/case09_cpu_limits.py`.

## Limits are cgroups

A container's limits are not a smaller computer. They are a **control group** (cgroup): a set of rules the kernel applies to a group of processes. With cgroup v2, which current Linux distributions use, the rules are files under `/sys/fs/cgroup` inside the container.

- **`cpu.max`** holds a quota and a period, in microseconds. `docker run --cpus 2` writes `200000 100000`: the group may use 200 ms of CPU time in every 100 ms window, which is two CPUs' worth. No limit reads `max 100000`.
- **`memory.max`** holds a limit in bytes, or `max`.

On the older cgroup v1, the same numbers live in `cpu.cfs_quota_us`, `cpu.cfs_period_us` and `memory.limit_in_bytes`.

## Why the CPU count is wrong

A CPU **quota** is a time budget, not a set of CPUs. The process can still run on all 32 cores of the host; it just gets stopped once the group has used its share of the window. So every way of asking "how many CPUs?" that looks at the machine gets 32:

- `os.cpu_count()` counts the host's CPUs.
- `os.process_cpu_count()`, new in Python 3.13, counts the CPUs this process may be scheduled on. `--cpus` does not change that. Only `--cpuset-cpus` does.
- `nproc` and Node's `os.availableParallelism()` look at the same affinity.

Some runtimes read the cgroup: recent JVMs, and Go since 1.25 for `GOMAXPROCS`. Python and Node do not. Python 3.13 lets you override the count with the `PYTHON_CPU_COUNT` environment variable, and most servers take a worker count in their config. Either way, somebody has to read the limit.

## Throttling

A quota has a second effect that surprises people. Say a container has 2 CPUs of quota and runs 8 busy threads. Together they use 200 ms of CPU time in the first 25 ms of a 100 ms window. Then the whole group is **throttled**, stopped, for the remaining 75 ms. Average CPU use looks fine, and latency has a 75 ms hole in it.

Too many workers for the quota make this worse, not better: more threads burn the budget faster. The cgroup file `cpu.stat` counts it in `nr_throttled` and `throttled_usec`. If those climb, either the pool is too big for the quota, or the quota is too small for the load. This is why some teams set CPU requests in Kubernetes but no CPU limits for latency-sensitive services.

## Memory: the hard limit

Memory is not throttled. When the group goes over `memory.max` and the kernel cannot reclaim enough, the **OOM killer** chooses a process in the group and sends it SIGKILL. If that process is PID 1, the container exits with **137**, and `docker inspect` shows `OOMKilled: true`. If it is a worker, a master like gunicorn may start a new one, which grows, and is killed again.

Two points matter when sizing:

- **Count every process.** Each worker is a separate process with its own memory. 65 workers at 60 MB, plus the master, is almost 4 GB, whatever the CPU count says.
- **Page cache counts too.** Files the app reads are cached in memory and charged to the group. The kernel can reclaim that cache, but a limit set right at the app's own peak leaves no room for it.

## Size from the budget

A pool sized for the container uses its real limits:

1. Read the CPU quota from `cpu.max`. Divide quota by period. When it says `max`, there is no CPU limit, so fall back to the host count.
2. Apply your rule of thumb to that number.
3. Check the result against the memory limit, with room to spare for the master and the page cache.

The rule of thumb itself depends on the work. Two per CPU plus one assumes workers that wait on I/O half the time. Pure CPU work wants about one per CPU. And remember the limits can differ in every environment, so read them at start-up instead of hard-coding a number.

## Fix the case

Make `worker_count` use the CPUs the container may really use. It must also work on a machine with no CPU limit at all, and with a limit that is not a whole number of CPUs.

## Check it works

```bash
uv run python -m dock check 9
```

```text
  PASS  2 CPUs and 1 GB: no OOM kill (5 workers, 380 MB)
  PASS  2 CPUs: between 2 and 5 workers, to use both (got 5)
  PASS  no CPU limit on an 8-CPU host: between 8 and 17 workers (got 17)
  PASS  1.5 CPUs and 512 MB: between 2 and 5 workers, no OOM kill (got 5)
```

Hard-coding five workers passes the first two lines and fails the third: on a bigger machine with no limit, it leaves most of the CPUs idle.

## Exercise

Extend `worker_count` so it also respects memory: never more workers than fit in `memory.max` with 20% left over. Which scenario in the check changes, and what would you log at start-up so that the next person can see why the pool has the size it has?

### More to try

- Use `os.process_cpu_count()` instead and run the check. Then explain what `--cpuset-cpus 0,1` would change.
- If you have Docker, run `docker run --rm --cpus 1.5 python:3.13-slim cat /sys/fs/cgroup/cpu.max` and `python -c "import os; print(os.cpu_count())"` in the same image.

## The container checklist

You have now met every way a container went wrong in this workshop. Keep this list:

1. Order the Dockerfile from what changes least to what changes most, and copy the dependency manifest before the code.
2. Keep the build context small with `.dockerignore`, and never send a secret to the builder.
3. Remember that a later layer can only hide a file. Clean up in the same `RUN` that made the mess.
4. Give secrets to the container at run time, or to one `RUN` with a secret mount, never with `ENV` or `ARG`.
5. Build in one stage and run in another, and install the run-time libraries, not the `-dev` packages.
6. Deploy and record images by digest, and use tags only as names for people.
7. Make sure SIGTERM reaches your app: `exec` in entrypoint scripts, exec form in `CMD`, and a handler in the app.
8. Listen on `0.0.0.0` inside the container, and publish only the ports that must be reached from outside.
9. Wait for readiness with a healthcheck that asks the service itself, and let apps retry their dependencies.
10. Keep data on volumes, and give the data folder to a fixed non-root user in the image.
11. Size worker pools from the cgroup limits, not from the host's CPU count.
