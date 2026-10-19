# PID 1 and graceful shutdown

> `docker stop` sends SIGTERM to PID 1 and nothing else. If PID 1 is a shell that does not pass it on, your server is killed ten seconds later, mid-request.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain what `docker stop` does, why PID 1 is special, and make a container shut down in under two seconds without dropping requests in flight.

## The idea

### What docker stop does

1. Docker sends **SIGTERM** to the container's PID 1 (or the signal named by `STOPSIGNAL`).
2. It waits for the grace period: 10 seconds by default, `-t` to change it.
3. If PID 1 is still running, it sends **SIGKILL**, which cannot be caught. The container exits with code 137 (128 + 9).

Every deploy, scale-down and node drain does this. A well-behaved server uses the SIGTERM to stop accepting new connections, finish the requests it has, close its database connections and exit 0.

### PID 1 is special

PID 1 in a process namespace plays the role of `init`. The kernel protects it: a signal whose action is the **default** action (such as SIGTERM's default, "terminate") is not delivered to PID 1. Only signals that PID 1 has installed a handler for reach it. So:

- a program that handles SIGTERM works as PID 1
- a program that relies on the default action ignores `docker stop` as PID 1

### The shell in the middle

A start script is run by a shell. While the shell waits for a foreground child, it does not forward SIGTERM to it. The shell is PID 1, the server is PID 8, and the signal stops at the shell.

`exec` fixes this. `exec python server.py` replaces the shell process with the server, keeping the same PID. The server becomes PID 1 and receives SIGTERM directly. The same goes for the `CMD` form: `CMD ["python", "server.py"]` (exec form) runs Python as PID 1, while `CMD python server.py` (shell form) runs `/bin/sh -c` first.

## The exercise

Open `lab/exercises/09-graceful-shutdown/`. `server.py` already does the right thing on SIGTERM: it stops accepting connections, waits for requests in flight and exits 0. The start script runs migrations, then the server:

```bash
#!/bin/sh
# Run migrations, then start the API.
set -e
python migrate.py
python server.py
```

```bash
uv run python -m dock run 9
```

```text
PID 1 in the container: sh start.sh

$ time docker stop dockerlab-09
took 10.6 s, exit code 137

$ docker logs dockerlab-09
migrations: up to date
api listening on :8000 as pid 8
GET /healthz 200

The server never heard SIGTERM. Docker waited 10 s, then killed it with SIGKILL.
```

The server's log never says "SIGTERM received". It was killed without ever knowing a shutdown had started.

## Reasoning towards the fix

PID 1 is `sh start.sh`. The server is pid 8. SIGTERM went to the shell, which is waiting for its child and ignores it. Ten seconds later, SIGKILL took down everything.

The script has one more job after migrations: become the server. Put `exec` in front of the last command, so the shell hands PID 1 over to Python.

## Check your fix

```bash
uv run python -m dock check 9
```

As shipped:

```text
  FAIL  docker stop finishes in under 4 s (took 10.5 s)
  FAIL  the server exits cleanly (exit code 137)
  PASS  a request in flight when the stop begins still gets its answer (200)
```

With the fix, the stop measured 1.9 s, with exit code 0. That 1.9 s is the server finishing a two-second request that was already in flight when the stop began, which is exactly what graceful means.

The checker starts a slow request, calls `docker stop` half a second later, and checks the timing, the exit code and the request's answer. `STOPSIGNAL SIGKILL` makes the stop fast, but fails the exit code and drops the request.

## In production

- **`--init` or tini.** `docker run --init` (Compose: `init: true`) puts a tiny init process at PID 1 that forwards signals to your process and reaps zombie child processes. Useful when your program cannot be PID 1 or spawns children it does not wait for.
- **Kubernetes** sends SIGTERM the same way, after a `preStop` hook, and waits `terminationGracePeriodSeconds` (30 by default). Load balancers may still send a few requests after SIGTERM, so stop accepting new work only after a short delay, or use a `preStop` sleep.
- **Workers and queues.** A queue worker should finish or hand back its current job on SIGTERM. Otherwise every deploy loses work.
- Set the grace period to longer than your slowest legitimate request.

## Key points

- `docker stop` sends SIGTERM to PID 1, waits 10 s, then sends SIGKILL (exit 137).
- The kernel does not deliver default-action signals to PID 1. Handle SIGTERM explicitly.
- A shell running your server as a child does not forward SIGTERM. Use `exec`, or the exec form of `CMD`.
- Graceful means: stop accepting, finish what is in flight, exit 0.
