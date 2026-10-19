"""06: Compose, service names and start-up order."""

import subprocess
import time
from pathlib import Path

from dock import docker as d

TITLE = "The API that started before its database"
HINTS = [
    "Read the API's log. What was the database doing when the API tried to connect?",
    "depends_on only waits for the db container to start. Started is not the same as ready.",
    "Give db a healthcheck that runs pg_isready over TCP (-h 127.0.0.1), and make api wait for "
    "it with condition: service_healthy.",
]


def compose(
    project: str, path: Path, *args: str, timeout: float = 300
) -> subprocess.CompletedProcess[str]:
    return d.docker(
        "compose",
        "-p",
        project,
        "-f",
        str(path / "compose.yaml"),
        *args,
        check=False,
        cwd=path,
        timeout=timeout,
    )


def container(project: str, path: Path, service: str) -> str:
    return compose(project, path, "ps", "-a", "-q", service).stdout.strip()


def run(path: Path) -> None:
    project = "dockerlab-06"
    compose(project, path, "down", "-v")
    try:
        up = compose(project, path, "up", "-d", "--build")
        if up.returncode:
            print(up.stderr.strip()[-600:])
            return
        time.sleep(8)
        print(f"$ docker compose -p {project} ps -a")
        print(
            compose(
                project, path, "ps", "-a", "--format", "table {{.Service}}\t{{.Status}}"
            ).stdout.rstrip()
        )
        print()
        print(f"$ docker compose -p {project} logs api")
        print(d.logs(container(project, path, "api"), 5))
        print()
        print("The API gave up while Postgres was still running its first-start scripts.")
    finally:
        compose(project, path, "down", "-v")


def check(path: Path) -> list[tuple[str, bool]]:
    project = "dockerlab-06-check"
    compose(project, path, "down", "-v")
    try:
        compose(project, path, "up", "-d", "--build", "--wait", "--wait-timeout", "120")
        api, db = container(project, path, "api"), container(project, path, "db")
        port = compose(project, path, "port", "api", "8000").stdout.strip().rsplit(":", 1)[-1]
        ready = d.wait_http(f"http://127.0.0.1:{port}/readyz", 10) if port.isdigit() else None
        restarts = int(d.inspect(api, "{{.RestartCount}}") or 0)
        failures = d.logs(api, 200).count("could not connect")
        health = d.inspect(db, "{{if .State.Health}}{{.State.Health.Status}}{{end}}")
        return [
            (
                "the API is up and ready (/readyz answers 200)",
                ready is not None and ready.status == 200,
            ),
            (
                f"the API never failed to connect on the way up "
                f"(failed {failures} times, restarted {restarts} times)",
                failures == 0 and restarts == 0 and d.running(api),
            ),
            (
                f"the database is healthy by its own health check ({health or 'no health check'})",
                health == "healthy",
            ),
        ]
    finally:
        compose(project, path, "down", "-v")
