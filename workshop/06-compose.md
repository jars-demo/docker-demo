# Compose and start-up order

> `depends_on` waits for a container to start, not for the service in it to be ready. Readiness has to be checked, and checked the same way your app connects.

**Time:** 25 minutes

## Goal

By the end of this chapter you can describe a multi-service app in `compose.yaml`, connect services by name, and make one service wait until another is really ready.

## The idea

### One file for the whole app

`compose.yaml` describes services, the networks they share and the volumes they keep. `docker compose up` builds and starts all of it; `docker compose down -v` removes all of it, volumes included.

```yaml
services:
  db:
    image: postgres:18.6-alpine
    volumes:
      - pgdata:/var/lib/postgresql
  api:
    build: ./api
    environment:
      DATABASE_URL: postgresql://app:app@db:5432/app
volumes:
  pgdata:
```

Compose puts every service on one user-defined network, so `db` resolves to the database container (chapter 04). Postgres 18 images keep their data under `/var/lib/postgresql/18/docker`, so the volume is mounted on `/var/lib/postgresql`, one level up.

### Started is not ready

`depends_on: [db]` only orders the starts: Compose starts the `db` container, then the `api` container. Nothing waits for Postgres to accept connections.

On its first start, Postgres does a lot before that: it initialises the data directory and runs every script in `/docker-entrypoint-initdb.d`, which can take seconds or minutes. It also does all of this with a **temporary server that only listens on its Unix socket**. Over TCP, the port is closed until the real server starts.

### Health checks and conditions

A **health check** is a command Docker runs inside the container every few seconds. Its exit code decides the container's health: `starting`, `healthy` or `unhealthy`. With the long form of `depends_on`, a service can wait for that:

```yaml
depends_on:
  db:
    condition: service_healthy
```

The check has to test what the dependent service actually needs. This lab measured what `pg_isready` reports during a first start, once a second:

```text
1 socket:  | tcp:
2 socket: /var/run/postgresql:5432 - accepting connections | tcp:
3 socket: /var/run/postgresql:5432 - accepting connections | tcp:
4 socket: /var/run/postgresql:5432 - accepting connections | tcp: 127.0.0.1:5432 - accepting connections
```

For two seconds, the socket check says "accepting connections" while TCP, which is what the API uses, is still closed.

## The exercise

Open `lab/exercises/06-compose/`. The API connects to Postgres once at start-up, like most apps that run migrations or warm a connection pool, and exits if it cannot. The init script loads seed data and then waits four seconds, standing in for a slow first start such as restoring a snapshot.

```bash
uv run python -m dock run 6
```

```text
$ docker compose -p dockerlab-06 ps -a
SERVICE   STATUS
api       Exited (1) 7 seconds ago
db        Up 8 seconds

$ docker compose -p dockerlab-06 logs api
could not connect to the database: connection failed: connection to server at "172.25.0.2", port 5432 failed: Connection refused
	Is the server running on that host and accepting TCP/IP connections?

The API gave up while Postgres was still running its first-start scripts.
```

Note that the hostname `db` resolved fine: the request reached the right container. Nothing was listening yet.

## Reasoning towards the fix

The API needs Postgres to accept TCP connections from other containers. So:

1. Give `db` a health check that asks over TCP: `pg_isready -h 127.0.0.1 -U app -d app`. The `-h` makes it use TCP instead of the socket.
2. Check often while starting, with a short `interval`. The default interval is 30 seconds, so the first result arrives late.
3. Make `api` wait with `condition: service_healthy`.

## Check your fix

```bash
uv run python -m dock check 6
```

As shipped:

```text
  FAIL  the API is up and ready (/readyz answers 200)
  FAIL  the API never failed to connect on the way up (failed 1 times, restarted 0 times)
  FAIL  the database is healthy by its own health check (no health check)
```

The checker runs `docker compose up --wait`, calls `/readyz` (which queries the database), and reads the API's logs for failed connections. Two wrong fixes fail on purpose:

- `restart: on-failure` gets the API up in the end, after crashing and restarting. The checker counts the failed connections.
- A health check without `-h 127.0.0.1` passes during the temporary server, the API starts too early and fails to connect.

## In production

- Apps should still retry their first connection with backoff. Databases restart, fail over and get upgraded long after start-up, and an orchestrator like Kubernetes has no `depends_on` at all.
- Kubernetes splits the idea in two: a **readiness probe** decides whether a pod gets traffic, a **liveness probe** decides whether it gets restarted. Chapter 10 covers health checks in images.
- Use `docker compose up --wait` in CI, so tests start only when every service with a health check is healthy.
- Keep credentials out of `compose.yaml` in real projects: use an `.env` file that is not committed, or Compose `secrets`.

## Key points

- `compose.yaml` describes the whole app. Services reach each other by service name.
- `depends_on` orders container starts. It does not wait for readiness.
- `condition: service_healthy` waits for a health check, so the check must test what the dependent service needs.
- During its first start, Postgres answers on its socket before TCP. Check over TCP.
