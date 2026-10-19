"""The checks reject the fixes that only hide a symptom, and accept other real fixes."""

import importlib

import pytest

from tests.conftest import needs_docker

pytestmark = needs_docker

BASE = "FROM python:3.13.16-slim-trixie\n"

WRONG = {
    "01 keep the container alive with tail": (
        1,
        {"start.sh": "#!/bin/sh\npython server.py &\ntail -f /dev/null\n"},
    ),
    "02 delete the secret in a later layer": (
        2,
        {
            "Dockerfile": BASE + "WORKDIR /app\nCOPY . .\nRUN rm -rf .env testdata tests\n"
            'CMD ["python", "server.py"]\n'
        },
    ),
    "03 install a hard-coded list before copying": (
        3,
        {
            "Dockerfile": BASE + "WORKDIR /app\n"
            "RUN pip install --no-cache-dir fastapi==0.142.2 uvicorn==0.54.0\n"
            "COPY . .\n"
            'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]\n'
        },
    ),
    "04 listen on localhost by name": (
        4,
        {
            "Dockerfile": BASE + "WORKDIR /app\nCOPY server.py .\nENV HOST=localhost\n"
            'CMD ["python", "server.py"]\n'
        },
    ),
    "05 run as root": (
        5,
        {
            "Dockerfile": BASE + "WORKDIR /app\nCOPY server.py .\nVOLUME /data\n"
            'CMD ["python", "server.py"]\n'
        },
    ),
    "06 restart until the database is up": (
        6,
        {
            "compose.yaml": (
                "services:\n  db:\n    image: postgres:18.6-alpine\n    environment:\n"
                "      POSTGRES_USER: app\n      POSTGRES_PASSWORD: app\n      POSTGRES_DB: app\n"
                "    volumes:\n      - ./db/initdb:/docker-entrypoint-initdb.d:ro\n"
                "  api:\n    build: ./api\n    restart: on-failure\n    environment:\n"
                "      DATABASE_URL: postgresql://app:app@db:5432/app\n"
                '    ports:\n      - "127.0.0.1::8000"\n    depends_on:\n      - db\n'
            )
        },
    ),
    "06 health check over the Unix socket": (
        6,
        {
            "compose.yaml": (
                "services:\n  db:\n    image: postgres:18.6-alpine\n    environment:\n"
                "      POSTGRES_USER: app\n      POSTGRES_PASSWORD: app\n      POSTGRES_DB: app\n"
                "    volumes:\n      - ./db/initdb:/docker-entrypoint-initdb.d:ro\n"
                '    healthcheck:\n      test: ["CMD", "pg_isready", "-U", "app", "-d", "app"]\n'
                "      interval: 1s\n      retries: 30\n"
                "  api:\n    build: ./api\n    environment:\n"
                "      DATABASE_URL: postgresql://app:app@db:5432/app\n"
                '    ports:\n      - "127.0.0.1::8000"\n'
                "    depends_on:\n      db:\n        condition: service_healthy\n"
            )
        },
    ),
    "07 pass the token as ENV": (
        7,
        {
            "Dockerfile": BASE
            + "WORKDIR /app\nARG PACKAGE_TOKEN\nENV PACKAGE_TOKEN=$PACKAGE_TOKEN\n"
            "COPY fetch_package.py .\nRUN python fetch_package.py\n"
            'COPY server.py .\nCMD ["python", "server.py"]\n'
        },
    ),
    "08 multi-stage without the runtime libpq": (
        8,
        {
            "Dockerfile": "FROM python:3.13.16-trixie AS build\nRUN python -m venv /opt/venv\n"
            "ENV PATH=/opt/venv/bin:$PATH\nCOPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            + BASE
            + "RUN useradd --system --uid 10001 app\n"
            "COPY --from=build /opt/venv /opt/venv\nENV PATH=/opt/venv/bin:$PATH\n"
            'WORKDIR /app\nCOPY server.py .\nUSER app\nCMD ["python", "server.py"]\n'
        },
    ),
    "09 stop with SIGKILL": (
        9,
        {
            "Dockerfile": BASE + "WORKDIR /app\nCOPY migrate.py server.py start.sh ./\n"
            'STOPSIGNAL SIGKILL\nCMD ["sh", "start.sh"]\n'
        },
    ),
    "10 a health check that always passes": (
        10,
        {
            "Dockerfile": BASE + "WORKDIR /app\nCOPY server.py .\n"
            "HEALTHCHECK CMD curl -fsS http://127.0.0.1:8000/healthz || exit 0\n"
            'CMD ["python", "server.py"]\n'
        },
    ),
}

RIGHT = {
    "01 run the server directly as the command": (
        1,
        {"Dockerfile": BASE + 'WORKDIR /app\nCOPY server.py .\nCMD ["python", "server.py"]\n'},
    ),
    "10 install curl for the health check": (
        10,
        {
            "Dockerfile": BASE
            + "RUN apt-get update && apt-get install -y --no-install-recommends curl"
            " && rm -rf /var/lib/apt/lists/*\nWORKDIR /app\nCOPY server.py .\n"
            "HEALTHCHECK CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1\n"
            'CMD ["python", "server.py"]\n'
        },
    ),
    "12 read the digest Docker recorded after the push": (
        12,
        {
            "release.py": (
                "import subprocess\n\n\ndef pin(reference: str) -> str:\n"
                "    name = reference.rpartition(':')[0]\n"
                "    digests = subprocess.run(\n"
                "        ['docker', 'image', 'inspect', reference, '--format',\n"
                "         '{{range .RepoDigests}}{{println .}}{{end}}'],\n"
                "        capture_output=True, text=True, check=True,\n"
                "    ).stdout.split()\n"
                "    return next(d for d in digests if d.startswith(name + '@'))\n"
            )
        },
    ),
}


@pytest.mark.parametrize("case", WRONG)
def test_check_rejects_a_wrong_fix(exercise, case: str) -> None:
    number, files = WRONG[case]

    results = importlib.import_module(f"dock.ex{number:02d}").check(exercise(number, files=files))

    assert not all(ok for _, ok in results), results


@pytest.mark.parametrize("case", RIGHT)
def test_check_accepts_another_real_fix(exercise, case: str) -> None:
    number, files = RIGHT[case]

    results = importlib.import_module(f"dock.ex{number:02d}").check(exercise(number, files=files))

    assert all(ok for _, ok in results), results
