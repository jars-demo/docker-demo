# Health checks

> A health check is a program Docker runs inside your container, with only the tools your image has. It must pass when the service works and fail when it does not.

**Time:** 20 minutes

## Goal

By the end of this chapter you can write a `HEALTHCHECK` that works in a slim image, tune its timing, and prove that it reports failures as well as success.

## The idea

### What a health check is

```dockerfile
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD <command>
```

Docker runs the command inside the container every `interval`. Exit code 0 is a pass, anything else a failure. After `retries` failures in a row, the container's health turns from `healthy` to `unhealthy`. Failures during `start-period` do not count, which gives slow starters time.

The result shows in `docker ps` and in `docker inspect`, and other tools act on it: Compose's `condition: service_healthy` (chapter 06), Docker Swarm replacing unhealthy tasks, and your own monitoring.

### It runs inside the container

The check is not run from your machine. It runs in the container's filesystem, with the container's tools. `curl` is the usual example in tutorials, and the slim Python image does not have it.

### What it should check

- **Liveness:** "is this process able to do its job, or is it stuck?" A health endpoint that answers from inside the app (not a static file) catches deadlocks and exhausted pools.
- Keep it cheap. It runs forever, every few seconds.
- Be careful with dependencies. If every API container reports unhealthy because the database is briefly down, a restart policy will restart all of them at once, which helps nobody. Kubernetes separates this into liveness (restart me) and readiness (do not send me traffic).

### A check that always passes is worse than none

`CMD curl ... || exit 0` turns every failure into a pass. Monitoring then shows green while the service is broken.

## The exercise

Open `lab/exercises/10-health-checks/`. The API has a real health endpoint: it returns 503 when its worker pool is stuck, and `POST /debug/break` simulates that.

```dockerfile
FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY server.py .
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1
CMD ["python", "server.py"]
```

The lab runs it with faster timing (`--health-interval 1s` and friends), so you do not wait half a minute per answer:

```bash
uv run python -m dock run 10
```

```text
GET /healthz from your machine: {'status': 'ok'}
Docker says the container is: unhealthy

the health check's last run:
  exit code 1: /bin/sh: 1: curl: not found
```

To read the check's own output by hand:

```bash
docker inspect --format '{{json .State.Health}}' dockerlab-10
```

## Reasoning towards the fix

The service is fine. The check cannot run. The image already has a perfectly good HTTP client: Python. A one-line script that calls `urlopen` raises an exception on a refused connection, a timeout or any non-2xx status, and Python exits 1 when an exception goes unhandled.

Use the exec form, a JSON array, so no shell is involved:

```dockerfile
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]
```

## Check your fix

```bash
uv run python -m dock check 10
```

As shipped:

```text
  FAIL  Docker reports the container healthy within 15 s (unhealthy)
  FAIL  Docker reports it unhealthy within 15 s once /healthz fails
```

The checker waits for `healthy`, then breaks the service and waits for `unhealthy`. Both directions matter: `|| exit 0` passes the first and fails the second. Installing curl with apt also passes, at the cost of a few megabytes and one more package to patch.

## In production

- **Docker alone does not restart unhealthy containers.** A restart policy reacts to exits, not to health. Swarm, Kubernetes probes, or an external watchdog act on health.
- Kubernetes ignores the `HEALTHCHECK` instruction. It uses `livenessProbe`, `readinessProbe` and `startupProbe` in the pod spec, often against the same endpoint.
- Give `start-period` (or a startup probe) enough time for migrations and cache warm-up, so a slow start is not mistaken for a broken one.
- Log why a check fails. "unhealthy" alone is hard to act on at 3 a.m.

## Key points

- A health check is a command run inside the container, so it can only use tools in the image.
- Exit 0 is healthy. After `retries` failures in a row the container is unhealthy.
- Prove both directions: healthy when it works, unhealthy when it does not.
- Docker records health, and other tools act on it.
