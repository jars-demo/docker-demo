# Health and readiness

> A container that has started is not a service that is ready. Wait for the thing you need, not for the thing that is easy to see.

**Time:** 20 minutes

## Goal

Know what `depends_on` waits for, write a healthcheck that tests readiness, choose sensible timings, and decide when an app should retry by itself instead.

## The case

```bash
uv run python -m dock run 7
```

```text
  t=  0.0s  db      container started
  t=  0.0s  orders  container started
  t=  0.3s  db      postgres process running, initialising the database
  t=  0.4s  orders  connect db:5432: connection refused
  t=  0.4s  orders  exited with code 1
  t=  6.8s  db      database system is ready to accept connections
orders served: 0 of 20
```

Orders says `depends_on: db`, so compose starts the database first. A few hundred milliseconds later it starts orders, which connects, is refused, and exits. The database is ready 6.4 seconds after that, and nobody is listening for it. Twenty customers try to order and none of them can. Open `lab/cases/case07_healthcheck.py`.

## What depends_on waits for

The short form, `depends_on: [db]`, waits for one thing: that the db **container has started**. A container has started when its main process has been launched. That says nothing about whether the program inside has finished starting.

Postgres is a good example of the gap. On first start it creates a database cluster, runs any init scripts, and restarts itself, all before it accepts a single connection. That can take seconds, or minutes for a large init script.

The long form lets you choose the condition:

- `service_started`, the same as the short form.
- `service_healthy`: wait until the dependency's **healthcheck** reports healthy.
- `service_completed_successfully`: wait until it has run and exited with code 0. Useful for a one-off migration container.

## Healthchecks

A healthcheck is a command the runtime runs inside the container, again and again. Exit code 0 means healthy. You can set it in the Dockerfile with `HEALTHCHECK`, or per service in compose:

```yaml
healthcheck:
  test: ["CMD", "pg_isready", "-U", "tidepool"]
  interval: 2s
  timeout: 3s
  retries: 5
  start_period: 30s
```

A container's health goes from `starting` to `healthy` after a check passes, and to `unhealthy` after `retries` checks fail in a row. Failures during `start_period` do not count, which gives slow starters room.

The defaults are worth knowing because they are slow: a 30 second interval, a 30 second timeout, 3 retries. With the default interval, the first check runs 30 seconds after start, so a dependent service waits at least that long even if the database was ready in two.

## Test readiness, not existence

The command you choose decides what "healthy" means. `pgrep postgres` passes as soon as the process exists, which in the case is 0.3 seconds in, long before it accepts connections. `pg_isready` asks the server itself whether it is accepting connections. For a web service, the equivalent is a request to an endpoint that answers only once the app has loaded its configuration and can do its job.

A good readiness check is:

- **Cheap.** It runs every few seconds, forever.
- **Local.** It tests this service. If it also tests every dependency, one slow database marks every service unhealthy at once.
- **Honest.** It fails when the service cannot serve, not just when the process has died.

## Health, liveness and restarts

Plain Docker records health and lets compose wait on it. It does not restart an unhealthy container by itself. Swarm does, and Kubernetes ignores `HEALTHCHECK` entirely in favour of its own probes:

- A **readiness** probe decides whether a pod gets traffic. Failing it takes the pod out of rotation, and nothing restarts.
- A **liveness** probe decides whether to restart the container. Failing it kills the container.
- A **startup** probe holds the other two off while a slow app boots.

The classic mistake is a liveness probe that checks the database. When the database has a bad minute, every app container fails liveness, and Kubernetes restarts all of them at once, which makes the bad minute much worse. Liveness should ask "is this process stuck?", and nothing else.

## Restart policies

`restart: always` or `on-failure` makes the case look fixed: orders crashes, restarts, crashes, and eventually connects. Docker waits between restarts, starting at 100 ms and doubling each time, so the delays add up. In the case it serves at 9.6 seconds instead of 7.9, after six crashes, each one logged as a failure. A restart policy is a safety net for real crashes, not a way to wait for a dependency.

## The app should retry anyway

`depends_on` only orders the **first** start, on one machine, in compose. In production, databases restart, fail over and get upgraded while the app keeps running. An app that exits the first time the database is unreachable will fail then too.

So the most robust fix is in the app: retry the connection with a short wait, up to a limit, and only then give up. With that in place, start-up order matters much less. The healthcheck is still worth having, so that compose and humans can see when the database is ready.

## Fix the case

There are two good fixes. One waits for the database to be truly ready before orders starts. The other makes orders patient on its own. Either one must have orders serving within two seconds of the database being ready, without crashing first, and without changing how long the database takes.

## Check it works

```bash
uv run python -m dock check 7
```

```text
  PASS  all 20 customers can order (served 20)
  PASS  orders serves within 2 s of the database being ready (at 7.9 s, db at 6.8 s)
  PASS  no crash loop: orders starts once (restarts: 0)
  PASS  the database still takes 6.8 s to get ready
```

## Exercise

Do both fixes: a healthcheck with `service_healthy`, and retries in the app. Then explain which of the two protects you when the database restarts at 15:00 on a Tuesday, with orders already running, and why.

### More to try

- Give the healthcheck `pg_isready` but no `interval`. Run the check and read when orders starts.
- Write the readiness endpoint for the orders service in a few lines of pseudocode. What does it check, and what does it deliberately not check?
