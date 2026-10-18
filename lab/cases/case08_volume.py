"""Case 08: the orders that vanished on redeploy.

Orders are saved in SQLite under /data, and compose mounts a named volume there so they outlive
the container. The image runs as an ordinary user, as it should. After a redeploy, every order
from the day is gone. The volume is still there. It is empty.
Run it: uv run python -m dock run 8
"""

import shlex

DOCKERFILE = """\
FROM python:3.13-slim
RUN useradd --uid 10001 tidepool
WORKDIR /app
COPY app.py .
RUN mkdir -p /data
USER tidepool
CMD ["python", "app.py"]
"""

COMPOSE = {"orders": {"volumes": ["orders-data:/data"]}}

DATA_DIR = "/data"
ORDERS_TODAY = 42


class Image:
    """Just what this case needs from a build: users, folders with owner and mode, the user."""

    def __init__(self, dockerfile: str) -> None:
        self.users = {"root": 0}
        self.dirs: dict[str, tuple[int, int]] = {"/": (0, 0o755), "/tmp": (0, 0o1777)}
        self.user = "root"
        for line in dockerfile.splitlines():
            op, _, arg = line.strip().partition(" ")
            if op == "USER":
                self.user = arg.strip()
            elif op == "WORKDIR":
                self.dirs.setdefault(arg.strip(), (0, 0o755))
            elif op == "RUN":
                for command in arg.split("&&"):
                    self.run(shlex.split(command))

    def uid(self, name: str) -> int:
        return int(name) if name.isdigit() else self.users[name]

    def run(self, words: list[str]) -> None:
        if words[0] == "useradd":
            self.users[words[-1]] = int(words[words.index("--uid") + 1])
        elif words[:2] == ["mkdir", "-p"]:
            for path in words[2:]:
                self.dirs.setdefault(path, (0, 0o755))
        elif words[0] == "chown":
            owner = words[-2].split(":")[0]
            self.dirs[words[-1]] = (self.uid(owner), self.dirs[words[-1]][1])
        elif words[0] == "chmod":
            self.dirs[words[-1]] = (self.dirs[words[-1]][0], int(words[-2], 8))
        elif words[:2] == ["install", "-d"]:
            owner = words[words.index("-o") + 1]
            self.dirs[words[-1]] = (self.uid(owner), 0o755)
        else:
            raise ValueError(f"RUN {shlex.join(words)}: this pretend builder does not know it")


class Docker:
    """Named volumes live on the host. On first use an empty volume is filled from the image:
    its files, and the owner and mode of the folder it is mounted on. A container's own
    writable layer is thrown away when the container is replaced."""

    def __init__(self) -> None:
        self.volumes: dict[str, dict] = {}

    def start(self, image: Image, compose: dict) -> "Container":
        mounts = {}
        for spec in compose["orders"].get("volumes", []):
            name, target = spec.split(":")[:2]
            if name not in self.volumes:
                owner, mode = image.dirs.get(target, (0, 0o755))
                self.volumes[name] = {"owner": owner, "mode": mode, "orders": []}
            mounts[target] = self.volumes[name]
        return Container(image, mounts)


class Container:
    def __init__(self, image: Image, mounts: dict) -> None:
        self.uid = image.uid(image.user)
        self.mounts = mounts
        self.layer: dict[str, list[int]] = {}  # the container's writable layer
        self.image = image
        self.warnings: list[str] = []
        self.path = self.choose(DATA_DIR)

    def stat(self, path: str) -> tuple[int, int]:
        if path in self.mounts:
            return self.mounts[path]["owner"], self.mounts[path]["mode"]
        return self.image.dirs.get(path, (0, 0o755))

    def writable(self, path: str) -> bool:
        owner, mode = self.stat(path)
        return self.uid == 0 or (owner == self.uid and mode & 0o200) or bool(mode & 0o002)

    def choose(self, wanted: str) -> str:
        """The app's start-up: use DATA_DIR, or fall back to /tmp with a warning."""
        if self.writable(wanted):
            return wanted
        owner, mode = self.stat(wanted)
        self.warnings.append(
            f"{wanted} is not writable by uid {self.uid} (owner uid {owner}, mode {mode:o}); "
            "saving orders to /tmp"
        )
        return "/tmp"

    def orders(self) -> list[int]:
        if self.path in self.mounts:
            return self.mounts[self.path]["orders"]
        return self.layer.setdefault(self.path, [])

    def take(self, count: int) -> None:
        self.orders().extend(range(1, count + 1))


def redeploy(dockerfile: str | None = None, compose: dict | None = None):
    """A day of orders, then docker compose up --build: a new container, the same volume."""
    docker = Docker()
    image = Image(dockerfile or DOCKERFILE)
    first = docker.start(image, compose or COMPOSE)
    first.take(ORDERS_TODAY)
    before = len(first.orders())
    second = docker.start(Image(dockerfile or DOCKERFILE), compose or COMPOSE)
    return docker, first, before, second


def run() -> None:
    _, first, before, second = redeploy()
    for warning in first.warnings:
        print(f"startup warning: {warning}")
    print(f"orders taken today:                    {before}")
    print("docker compose up --build (new container, same volume)")
    print(f"orders on file after the redeploy:     {len(second.orders())}")
