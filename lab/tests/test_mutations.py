"""The checks reject plausible wrong fixes and accept other right ones.

Each variant is a case as shipped with a few lines changed, the way a learner might change them.
A wrong fix makes the symptom go away, or half of it, without doing the job. A right fix that
differs from the one in solutions/ must pass, so the checks test the goal and not one answer."""

import sys
import types
from pathlib import Path

import pytest

from dock.__main__ import CASES
from dock.checks import CHECKS

ROOT = Path(__file__).parent.parent

WRONG = [
    (
        1,
        "pin the packages by hand, before COPY",
        [
            (
                "COPY . .\nRUN pip install -r requirements.txt\n",
                "RUN pip install flask==3.1.1 gunicorn==23.0.0 jinja2==3.1.6 requests==2.32.4"
                " pydantic==2.11.7 babel==2.17.0\nCOPY . .\n",
            ),
        ],
    ),
    (
        1,
        "install before copying anything",
        [
            (
                "COPY . .\nRUN pip install -r requirements.txt\n",
                "RUN pip install -r requirements.txt\nCOPY . .\n",
            ),
        ],
    ),
    (
        1,
        "copy requirements and app.py, forget the templates",
        [
            (
                "COPY . .\nRUN pip install -r requirements.txt\n",
                "COPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY app.py .\n",
            ),
        ],
    ),
    (2, "drop the rm line", [("RUN rm -f .env\n", "")]),
    (
        2,
        "ignore .env, then bake the token in with ENV",
        [
            ('DOCKERIGNORE = """\\\n', 'DOCKERIGNORE = """\\\n.env\n'),
            ("RUN rm -f .env\n", "ENV PAYMENT_TOKEN=tp-prod-4f9a2c71\n"),
        ],
    ),
    (2, "delete .env from the project", [('    ".env": f"PAYMENT_TOKEN={TOKEN}\\n",\n', "")]),
    (
        2,
        "replace the ignore list with just .env",
        [
            (
                'DOCKERIGNORE = """\\\n.git\n__pycache__\n*.pyc\n"""',
                'DOCKERIGNORE = """\\\n.env\n"""',
            ),
        ],
    ),
    (
        3,
        "install libpq-dev in the runtime stage",
        [
            (
                "FROM python:3.13-slim\nWORKDIR /app",
                "FROM python:3.13-slim\nRUN apt-get update && apt-get install -y libpq-dev"
                " && rm -rf /var/lib/apt/lists/*\nWORKDIR /app",
            ),
        ],
    ),
    (
        3,
        "install libpq5 but keep the apt lists",
        [
            (
                "FROM python:3.13-slim\nWORKDIR /app",
                "FROM python:3.13-slim\nRUN apt-get update && apt-get install -y libpq5\n"
                "WORKDIR /app",
            ),
        ],
    ),
    (
        3,
        "clean the apt lists in a separate RUN",
        [
            (
                "FROM python:3.13-slim\nWORKDIR /app",
                "FROM python:3.13-slim\nRUN apt-get update && apt-get install -y libpq5\n"
                "RUN rm -rf /var/lib/apt/lists/*\nWORKDIR /app",
            ),
        ],
    ),
    (
        3,
        "run from the build stage",
        [("FROM python:3.13-slim\nWORKDIR /app", "FROM build\nWORKDIR /app")],
    ),
    (
        4,
        "roll back to the first release ever",
        [
            ("        self.rollout(self.history[-1])", "        self.rollout(self.history[0])"),
        ],
    ),
    (
        4,
        "pin the good build's digest by hand",
        [
            (
                "        return ref\n",
                '        good = hashlib.sha256(BUILDS["a1f3"].encode()).hexdigest()\n'
                '        return f"{IMAGE}@sha256:{good}"\n',
            ),
        ],
    ),
    (
        4,
        "resolve each tag once and remember it forever",
        [
            (
                "        return ref\n",
                "        self.pinned = getattr(self, 'pinned', {})\n"
                "        self.pinned.setdefault(ref, IMAGE + '@' + self.registry.resolve(ref))\n"
                "        return self.pinned[ref]\n",
            ),
        ],
    ),
    (5, "give docker stop longer", [("GRACE = 10.0", "GRACE = 60.0")]),
    (
        5,
        "run the worker directly and skip the migrations",
        [
            ('CMD = ["/start.sh"]', 'CMD = ["python", "worker.py"]'),
        ],
    ),
    (5, "exec the migration instead", [("python migrate.py\n", "exec python migrate.py\n")]),
    (
        6,
        "put orders on the host network",
        [
            ('"ports": ["8080:8080"]}', '"ports": ["8080:8080"], "network_mode": "host"}'),
        ],
    ),
    (
        6,
        "listen on localhost by name",
        [('"run", "--port"', '"run", "--host", "localhost", "--port"')],
    ),
    (6, "publish the port on 127.0.0.1 only", [('"8080:8080"', '"127.0.0.1:8080:8080"')]),
    (7, "restart orders until it works", [('"restart": "no"', '"restart": "always"')]),
    (
        7,
        "a healthcheck that only asks whether postgres is running",
        [
            (
                '"image": "postgres:17",',
                '"image": "postgres:17", "healthcheck": {"test": ["CMD", "pgrep", "postgres"],'
                ' "interval": 1.0, "retries": 10},',
            ),
            ('"condition": "service_started"', '"condition": "service_healthy"'),
        ],
    ),
    (
        7,
        "pg_isready, but the default 30 s interval",
        [
            (
                '"image": "postgres:17",',
                '"image": "postgres:17", "healthcheck": {"test": ["CMD", "pg_isready"]},',
            ),
            ('"condition": "service_started"', '"condition": "service_healthy"'),
        ],
    ),
    (8, "run as root", [("USER tidepool", "USER root")]),
    (
        8,
        "make /data writable by everyone",
        [
            ("RUN mkdir -p /data\n", "RUN mkdir -p /data && chmod 777 /data\n"),
        ],
    ),
    (8, "save under /app/data instead", [('DATA_DIR = "/data"', 'DATA_DIR = "/app/data"')]),
    (
        9,
        "use os.process_cpu_count()",
        [
            ("return machine.cpu_count() * 2 + 1", "return machine.process_cpu_count() * 2 + 1"),
        ],
    ),
    (9, "hard-code five workers", [("return machine.cpu_count() * 2 + 1", "return 5")]),
    (
        9,
        "read the quota but forget max",
        [
            (
                "return machine.cpu_count() * 2 + 1",
                'quota, period = machine.read("/sys/fs/cgroup/cpu.max").split()\n'
                "    return math.ceil(int(quota) / int(period)) * 2 + 1",
            ),
        ],
    ),
]

RIGHT = [
    (
        1,
        "copy requirements to an absolute path",
        [
            (
                "COPY . .\nRUN pip install -r requirements.txt\n",
                "COPY requirements.txt /app/\nRUN pip install -r requirements.txt\nCOPY . .\n",
            ),
        ],
    ),
    (
        1,
        "copy the app and templates explicitly",
        [
            (
                "COPY . .\nRUN pip install -r requirements.txt\n",
                "COPY requirements.txt ./\nRUN pip install -r requirements.txt\n"
                "COPY app.py ./\nCOPY templates ./templates\n",
            ),
        ],
    ),
    (
        2,
        "copy only what the app needs",
        [
            ("COPY . .\nRUN rm -f .env\n", "COPY app.py ./\nCOPY templates ./templates\n"),
        ],
    ),
    (
        3,
        "libpq5 with --no-install-recommends",
        [
            (
                "FROM python:3.13-slim\nWORKDIR /app",
                "FROM python:3.13-slim\nRUN apt-get update && apt-get install -y"
                " --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*\nWORKDIR /app",
            ),
        ],
    ),
    (
        4,
        "pin the digest in deploy",
        [
            (
                "        entry = self.record(ref)",
                '        entry = f"{IMAGE}@{self.registry.resolve(ref)}"',
            ),
        ],
    ),
    (
        5,
        "an sh -c command that ends in exec",
        [
            (
                'CMD = ["/start.sh"]',
                'CMD = ["sh", "-c", "python migrate.py && exec python worker.py"]',
            ),
        ],
    ),
    (6, "--host=0.0.0.0 as one word", [('"run", "--port"', '"run", "--host=0.0.0.0", "--port"')]),
    (7, "retry the connection in the app", [("CONNECT_ATTEMPTS = 1", "CONNECT_ATTEMPTS = 30")]),
    (
        7,
        "pg_isready with a start period",
        [
            (
                '"image": "postgres:17",',
                '"image": "postgres:17", "healthcheck": {'
                '"test": ["CMD-SHELL", "pg_isready -U tidepool"], "interval": 0.5,'
                ' "retries": 3, "start_period": 10},',
            ),
            ('"condition": "service_started"', '"condition": "service_healthy"'),
        ],
    ),
    (
        8,
        "install -d with an owner",
        [("RUN mkdir -p /data\n", "RUN install -d -o tidepool /data\n")],
    ),
    (8, "chown by uid", [("RUN mkdir -p /data\n", "RUN mkdir -p /data && chown 10001 /data\n")]),
    (
        9,
        "round the quota down",
        [
            (
                "return machine.cpu_count() * 2 + 1",
                'quota, period = machine.read("/sys/fs/cgroup/cpu.max").split()\n'
                '    if quota == "max":\n'
                "        return machine.cpu_count() * 2 + 1\n"
                "    return max(1, int(quota) // int(period)) * 2 + 1",
            ),
        ],
    ),
]


def variant(number: int, changes: list[tuple[str, str]]) -> types.ModuleType:
    name = CASES[number][0]
    source = (ROOT / "cases" / f"{name}.py").read_text()
    for old, new in changes:
        assert source.count(old) == 1, f"{name}: {old!r} is not in the case exactly once"
        source = source.replace(old, new)
    module = types.ModuleType(f"variant_{name}")
    sys.modules[module.__name__] = module  # dataclasses look their module up here
    try:
        exec(compile(source, f"{name}.py", "exec"), module.__dict__)
    finally:
        sys.modules.pop(module.__name__)
    return module


def describe(cases: list) -> list:
    return [pytest.param(n, changes, id=f"{n:02d}-{label}") for n, label, changes in cases]


@pytest.mark.parametrize(("number", "changes"), describe(WRONG))
def test_check_rejects_a_wrong_fix(number, changes):
    results = CHECKS[number](variant(number, changes))

    assert not all(ok for _, ok in results)


@pytest.mark.parametrize(("number", "changes"), describe(RIGHT))
def test_check_accepts_another_right_fix(number, changes):
    failed = [label for label, ok in CHECKS[number](variant(number, changes)) if not ok]

    assert failed == []


def test_every_case_has_wrong_fixes_to_reject():
    assert {n for n, _, _ in WRONG} == set(CASES)
    assert all(sum(1 for n, _, _ in WRONG if n == case) >= 2 for case in CASES)
