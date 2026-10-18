# PID 1 and signals

> The first process in a container has a special job, and the kernel treats it differently. A shell in that seat quietly swallows your shutdown.

**Time:** 20 minutes

## Goal

Know what `docker stop` does, why the first process in a container ignores signals it has no handler for, how a wrapper script can stop your app from hearing SIGTERM, and how to shut down without losing work.

## The case

```bash
uv run python -m dock run 5
```

```text
  t=  0.0s  PID 1  /bin/sh /start.sh
  t=  0.0s  PID 2  python migrate.py
  t=  2.0s  PID 3  python worker.py
  t=  5.0s  packed order 1043
  t=  8.0s  packed order 1044
  t=  9.5s  docker stop: SIGTERM to PID 1
  t=  9.5s  PID 1 (/bin/sh /start.sh) has no SIGTERM handler, so the kernel drops it
  t= 11.0s  packed order 1045
  t= 14.0s  packed order 1046
  t= 17.0s  packed order 1047
  t= 19.5s  still running after 10 s: SIGKILL
  t= 19.5s  order 1048 cut off mid-pack: paid for, never packed
docker stop took 10.0 s; exit code 137
orders packed: [1043, 1044, 1045, 1046, 1047]; cut off: [1048]
```

The packing worker does the right thing on SIGTERM: it finishes the order in hand and exits. It never gets the chance. Every deploy waits ten seconds, then kills it in the middle of an order. Open `lab/cases/case05_pid_one.py` and read `START_SH`.

## What docker stop does

`docker stop` sends one signal to one process: SIGTERM (or the image's `STOPSIGNAL`) to the container's main process. Then it waits, 10 seconds by default. If the container is still running, it sends SIGKILL, which cannot be caught.

Exit codes tell you which happened. A process killed by a signal exits with 128 plus the signal number: **143** for SIGTERM (15) and **137** for SIGKILL (9). A 137 on every deploy means your app is never shutting down by itself. A 137 at a random time often means the out-of-memory killer (chapter 09).

Kubernetes works the same way with different numbers: SIGTERM, then `terminationGracePeriodSeconds` (30 by default), then SIGKILL.

## PID 1 is special

A container has its own **PID namespace**. Its first process is PID 1 inside it, whatever its number on the host. On a normal Linux machine PID 1 is the init system, and the kernel protects it: a signal whose action is the **default** is not delivered to PID 1. For an ordinary process the default action of SIGTERM is to die. For PID 1 there is no default action. If it has not installed a handler, SIGTERM does nothing at all.

So two things must be true for a graceful stop:

1. The process that receives SIGTERM is your app, or something that passes the signal to your app.
2. Your app has a handler for it.

Python has no SIGTERM handler by default, so a plain script as PID 1 ignores `docker stop` completely. Servers such as gunicorn and uvicorn install one, and so does the JVM. Node does not, so a Node app as PID 1 needs its own `process.on("SIGTERM", ...)`. Your own workers need one too.

## The shell in the middle

The case breaks rule 1. The image runs `/start.sh`, so PID 1 is a shell. The shell runs the migration, then starts the worker as a **child** and waits for it. SIGTERM goes to the shell, which has no handler, so the kernel drops it. The worker never hears a thing.

The same happens with the **shell form** of `CMD`. `CMD python worker.py` really runs `/bin/sh -c "python worker.py"`. Some shells replace themselves with a single simple command, and some do not, and anything with `&&` or a second line keeps the shell in charge.

Outside a container the picture is different but no better. Measure it on your machine:

```bash
uv run python -m dock try stop
```

```text
Python 3.13.16, Linux, 4 CPUs
Each process gets SIGTERM, then SIGKILL if it is still running after 2 s.

  how the worker runs          stop took   ended by  the worker
  python, handles SIGTERM         0.22 s   exit 0    finished its work
  python, SIGTERM ignored         2.00 s   SIGKILL   killed mid-work
  sh -c 'python ...; true'        0.00 s   SIGTERM   never told, still running
  sh -c 'exec python ...'         0.21 s   exit 0    finished its work
```

Row three: the shell is not PID 1 here, so SIGTERM kills it at once, and the worker runs on as an orphan. Row four is the fix in one word. `exec` replaces the shell with the program, keeping its PID, so the program receives the signal directly.

## Init processes and zombies

PID 1 has a second job. When a process dies, its parent must collect its exit status, or it lingers as a **zombie**. When a parent dies first, its children are handed to PID 1, which must collect them too. An app that spawns subprocesses and runs as PID 1 can fill the process table with zombies if it never does.

A tiny init solves this: `docker run --init` (or `init: true` in compose) runs **tini** as PID 1. It reaps zombies and forwards signals to its child. It does not fix a shell that never passes the signal on. If tini's child is `/start.sh` without `exec`, the worker still does not hear SIGTERM.

## Shutting down well

Hearing the signal is half the job. A good shutdown:

- **Stops taking new work**, then finishes what is in hand.
- **Fits the grace period.** If a job can take longer, make it resumable, or raise the timeout with `stop_grace_period` in compose.
- **Keeps serving briefly behind a load balancer.** In Kubernetes, SIGTERM and the removal from the service's endpoints happen at the same time, so requests can still arrive for a second or two. A short `preStop` sleep or a delay before closing the listener avoids dropped requests.

## Fix the case

The worker is fine. Make SIGTERM reach it, while the migration still runs first. Leave `GRACE` alone: a longer wait only makes the deploy slower and still ends in SIGKILL.

## Check it works

```bash
uv run python -m dock check 5
```

```text
  PASS  docker stop finishes in under 5 s (took 1.5 s)
  PASS  the container exits cleanly with code 0, not 137 (code 0)
  PASS  no order is cut off mid-pack (cut off: [])
  PASS  migrations still run before the worker starts
  PASS  docker stop still waits 10 s before SIGKILL (keep GRACE)
```

Stop now takes 1.5 s: the time to finish the order in hand.

## Exercise

Change the case so the migration runs as its own one-off container before the worker starts, instead of inside `start.sh`. What does the worker's `CMD` become? List one advantage and one cost of moving migrations out of the image's start-up.

### More to try

- Set `CMD = ["sh", "-c", "python migrate.py && python worker.py"]` and run the case. Then add `exec` in the right place and run the check.
- Look at the entrypoint script of an official image, for example the Postgres image's `docker-entrypoint.sh`. Find the `exec` at the end, and the reason it is there.
