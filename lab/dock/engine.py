"""A tiny pretend Docker builder, so the build cases run anywhere, fast, with no daemon.

It follows the real rules where they matter for the workshop:

- Every instruction makes a layer. A layer is a set of file changes on top of the one below.
- Deleting a file in a later layer only hides it. The bytes stay in the earlier layer.
- The build cache key of a step is its parent's key plus its own instruction. For COPY it also
  includes a hash of the files copied. Once one step misses, every step after it misses.
- The build context is the project folder minus whatever .dockerignore matches.
- FROM starts a new stage. Only the last stage becomes the image. COPY --from reads another stage.

Time is pretend time, so every build prints the same seconds on every machine.
"""

import hashlib
import shlex
from dataclasses import dataclass, field
from fnmatch import fnmatchcase

MB = 1_000_000


@dataclass(frozen=True)
class File:
    content: str
    size: int = 0  # bytes; 0 means the length of the content

    @property
    def bytes(self) -> int:
        return self.size or len(self.content.encode())


GONE = None  # a whiteout: the file is hidden from this layer up
Files = dict[str, File | None]

PYTHON = "/usr/local/lib/python3.13/site-packages"

BASES: dict[str, Files] = {
    "python:3.13-slim": {
        "/bin/sh": File("dash", 125_000),
        "/usr/local/bin/python3": File("python 3.13", 18 * MB),
        "/usr/local/lib/python3.13/os.py": File("stdlib", 104 * MB),
        "/usr/lib/x86_64-linux-gnu/libc.so.6": File("glibc", 2 * MB),
    },
}

# apt packages: the files each one installs, and what it pulls in.
APT: dict[str, tuple[Files, list[str]]] = {
    "build-essential": (
        {"/usr/bin/gcc": File("gcc 12", 182 * MB), "/usr/bin/make": File("make", 1 * MB)},
        [],
    ),
    "libpq-dev": (
        {"/usr/include/postgresql/libpq-fe.h": File("libpq headers", 3 * MB)},
        ["libpq5"],
    ),
    "libpq5": ({"/usr/lib/x86_64-linux-gnu/libpq.so.5": File("libpq 16", 1 * MB)}, []),
    "curl": ({"/usr/bin/curl": File("curl 7.88", 2 * MB)}, []),
}
APT_LISTS = "/var/lib/apt/lists/index"

# pip packages: wheel size, and for packages with C code, what building and importing need.
PYPI: dict[str, dict] = {
    "flask": {"size": 3 * MB},
    "gunicorn": {"size": 1 * MB},
    "jinja2": {"size": 2 * MB},
    "requests": {"size": 1 * MB},
    "pydantic": {"size": 9 * MB},
    "babel": {"size": 32 * MB},
    "psycopg2": {
        "size": 2 * MB,
        "build_needs": ["/usr/bin/gcc", "/usr/include/postgresql/libpq-fe.h"],
        "links": "/usr/lib/x86_64-linux-gnu/libpq.so.5",
    },
}
PIP_SECONDS_PER_PACKAGE = 16.0
COMPILE_SECONDS = 38.0


class BuildError(Exception):
    pass


@dataclass
class Layer:
    instruction: str
    files: Files

    @property
    def bytes(self) -> int:
        return sum(f.bytes for f in self.files.values() if f is not None)


@dataclass
class Image:
    layers: list[Layer]
    env: dict[str, str] = field(default_factory=dict)
    cmd: str = ""
    workdir: str = "/"

    def filesystem(self) -> dict[str, File]:
        """What a container sees: every layer applied in order, whiteouts hiding files."""
        view: Files = {}
        for layer in self.layers:
            view.update(layer.files)
        return {path: f for path, f in sorted(view.items()) if f is not None}

    @property
    def bytes(self) -> int:
        """What you pull and store: the sum of every layer, hidden files included."""
        return sum(layer.bytes for layer in self.layers)

    def history(self) -> list[str]:
        return [layer.instruction for layer in self.layers]


@dataclass
class Step:
    instruction: str
    cached: bool
    seconds: float


@dataclass
class Build:
    image: Image
    steps: list[Step]

    @property
    def seconds(self) -> float:
        return sum(step.seconds for step in self.steps)


def instructions(dockerfile: str) -> list[str]:
    lines = [line.strip() for line in dockerfile.replace("\\\n", " ").splitlines()]
    return [" ".join(line.split()) for line in lines if line and not line.startswith("#")]


def ignored(path: str, patterns: list[str]) -> bool:
    """True if .dockerignore leaves path out. A pattern matches a path or any folder above it."""
    parts = path.split("/")
    for pattern in patterns:
        wanted = pattern.strip("/").split("/")
        for depth in range(1, len(parts) + 1):
            prefix = parts[:depth]
            if len(prefix) == len(wanted) and all(map(fnmatchcase, prefix, wanted)):
                return True
    return False


def context(project: dict[str, str], dockerignore: str = "") -> dict[str, str]:
    """The files sent to the builder: the project minus what .dockerignore matches."""
    patterns = [p.strip() for p in dockerignore.splitlines() if p.strip() and p[0] != "#"]
    return {path: text for path, text in project.items() if not ignored(path, patterns)}


def digest(files: dict) -> str:
    h = hashlib.sha256()
    for path in sorted(files):
        f = files[path]
        h.update(path.encode() + b"\0" + (b"-" if f is None else repr(f).encode()) + b"\0")
    return h.hexdigest()


def resolve(cwd: str, path: str) -> str:
    if path.startswith("/"):
        return path.rstrip("/") or "/"
    joined = f"{cwd.rstrip('/')}/{path}"
    parts: list[str] = []
    for part in joined.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            parts and parts.pop()
        else:
            parts.append(part)
    return "/" + "/".join(parts)


class Stage:
    def __init__(self, base: str, name: str) -> None:
        self.name = name
        self.layers = [Layer(f"FROM {base}", dict(BASES[base]))]
        self.env: dict[str, str] = {}
        self.cmd = ""
        self.workdir = "/"

    def view(self) -> dict[str, File]:
        return Image(self.layers).filesystem()

    def image(self) -> Image:
        return Image(list(self.layers), dict(self.env), self.cmd, self.workdir)


class Builder:
    """Builds a Dockerfile. Keep one Builder to keep its cache between builds."""

    def __init__(self) -> None:
        self.cache: dict[str, Stage] = {}

    def build(self, dockerfile: str, project: dict[str, str], dockerignore: str = "") -> Build:
        sent = context(project, dockerignore)
        stages: dict[str, Stage] = {}
        stage: Stage | None = None
        key = ""
        steps: list[Step] = []
        for line in instructions(dockerfile):
            op, _, arg = line.partition(" ")
            op = op.upper()
            if op == "FROM":
                base, _, name = arg.partition(" AS ")
                if stage is not None:
                    stages[stage.name] = stage
                name = name.strip() or str(len(stages))
                if base in stages:  # FROM an earlier stage carries on from where it ended
                    stage = self.restore(stages[base], name)
                    steps.append(Step(line, True, 0.0))
                    continue
                if base not in BASES:
                    raise BuildError(f"FROM {base}: no such base image in this pretend registry")
                key = hashlib.sha256(base.encode()).hexdigest()
                stage = Stage(base, name)
                steps.append(Step(line, True, 0.0))
                continue
            if stage is None:
                raise BuildError(f"{line}: a Dockerfile starts with FROM")
            key = hashlib.sha256((key + line + self.inputs(op, arg, stage, stages, sent)).encode())
            key = key.hexdigest()
            if key in self.cache:
                stage = self.restore(self.cache[key], stage.name)
                steps.append(Step(line, True, 0.0))
                continue
            seconds = self.execute(op, arg, line, stage, stages, sent)
            self.cache[key] = self.restore(stage, stage.name)
            steps.append(Step(line, False, seconds))
        if stage is None:
            raise BuildError("the Dockerfile is empty")
        return Build(stage.image(), steps)

    @staticmethod
    def restore(saved: Stage, name: str) -> Stage:
        copy = Stage.__new__(Stage)
        copy.name = name
        copy.layers = list(saved.layers)
        copy.env = dict(saved.env)
        copy.cmd = saved.cmd
        copy.workdir = saved.workdir
        return copy

    def inputs(self, op: str, arg: str, stage: Stage, stages: dict, sent: dict) -> str:
        """What a COPY reads, so that changing a copied file misses the cache."""
        if op != "COPY":
            return ""
        return digest(self.copied(arg, stage, stages, sent))

    def copied(self, arg: str, stage: Stage, stages: dict, sent: dict) -> Files:
        words = shlex.split(arg)
        source: dict = {f"/{path}": File(text) for path, text in sent.items()}
        if words and words[0].startswith("--from="):
            name = words.pop(0).removeprefix("--from=")
            if name not in stages:
                raise BuildError(f"COPY --from={name}: no stage called {name}")
            source = stages[name].view()
        if len(words) < 2:
            raise BuildError(f"COPY {arg}: needs a source and a destination")
        *sources, dest = words
        into_folder = dest.endswith("/") or dest in (".", "./") or len(sources) > 1
        out: Files = {}
        for src in sources:
            here = resolve("/", src)
            inside = here.rstrip("/") + "/"
            matched = {p: f for p, f in source.items() if p == here or p.startswith(inside)}
            if not matched:
                raise BuildError(f"COPY {src}: not found in the build context")
            for path, f in matched.items():
                if path == here:
                    name = path.rsplit("/", 1)[1]
                    target = f"{dest.rstrip('/')}/{name}" if into_folder else dest
                else:
                    target = f"{dest.rstrip('/')}/{path[len(inside) :]}"
                out[resolve(stage.workdir, target)] = f
        return out

    def execute(
        self, op: str, arg: str, line: str, stage: Stage, stages: dict, sent: dict
    ) -> float:
        if op == "WORKDIR":
            stage.workdir = resolve(stage.workdir, arg)
            stage.layers.append(Layer(line, {}))
            return 0.0
        if op == "ENV":
            name, _, value = arg.partition("=")
            stage.env[name.strip()] = value.strip().strip('"')
            stage.layers.append(Layer(line, {}))
            return 0.0
        if op == "CMD":
            stage.cmd = arg
            stage.layers.append(Layer(line, {}))
            return 0.0
        if op == "COPY":
            stage.layers.append(Layer(line, self.copied(arg, stage, stages, sent)))
            return 0.3
        if op == "RUN":
            changes: Files = {}
            seconds = 0.0
            for command in arg.split("&&"):
                seconds += self.run(command.strip(), stage, changes)
            stage.layers.append(Layer(line, changes))
            return seconds
        raise BuildError(f"{op}: this pretend builder does not know that instruction")

    def run(self, command: str, stage: Stage, changes: Files) -> float:
        view: Files = dict(stage.view())
        view.update(changes)
        present = {path for path, f in view.items() if f is not None}
        words = shlex.split(command)
        if words[:2] == ["apt-get", "update"]:
            changes[APT_LISTS] = File("package lists", 48 * MB)
            return 4.0
        if words[:3] == ["apt-get", "install", "-y"]:
            if APT_LISTS not in present:
                raise BuildError("apt-get install: unable to locate package (run apt-get update)")
            todo = [w for w in words[3:] if not w.startswith("-")]
            seconds = 0.0
            while todo:
                name = todo.pop(0)
                if name not in APT:
                    raise BuildError(f"apt-get install: unable to locate package {name}")
                files, needs = APT[name]
                changes.update(files)
                todo.extend(needs)
                seconds += 6.0
            return seconds
        if words[:2] == ["rm", "-f"] or words[:2] == ["rm", "-rf"]:
            for target in words[2:]:
                full = resolve(stage.workdir, target.removesuffix("*"))
                for path in present:
                    if path == full or path.startswith(full.rstrip("/") + "/"):
                        changes[path] = GONE
            return 0.1
        if words[:2] == ["pip", "install"] and "-r" in words:
            return self.pip(self.requirements(words, view, stage), changes, present)
        if words[:2] == ["pip", "install"] and any(w.endswith(".whl") for w in words):
            folder = resolve(stage.workdir, words[2].rsplit("/", 1)[0])
            wheels = [p for p in present if p.startswith(folder + "/") and p.endswith(".whl")]
            if not wheels:
                raise BuildError(f"pip install: no wheels found in {folder}")
            for path in wheels:
                name, version = path.rsplit("/", 1)[1].removesuffix(".whl").rsplit("-", 1)
                f = view[path]
                changes[f"{PYTHON}/{name}-{version}"] = File(version, f.size if f else 0)
            return 1.0 * len(wheels)
        if words[:2] == ["pip", "install"]:
            return self.pip([w for w in words[2:] if not w.startswith("-")], changes, present)
        if words[:2] == ["pip", "wheel"] and "-r" in words and "-w" in words:
            folder = resolve(stage.workdir, words[words.index("-w") + 1])
            seconds = 0.0
            for requirement in self.requirements(words, view, stage):
                name, _, version = requirement.partition("==")
                info = PYPI.get(name)
                if info is None:
                    raise BuildError(f"pip: no matching distribution for {requirement}")
                missing = [p for p in info.get("build_needs", []) if p not in present]
                if missing:
                    raise BuildError(f"building {name} failed: {missing[0]} not found")
                if "build_needs" in info:
                    seconds += COMPILE_SECONDS
                changes[f"{folder}/{name}-{version}.whl"] = File(name, info["size"])
                seconds += 2.0
            return seconds
        if words[:2] == ["mkdir", "-p"]:
            for target in words[2:]:
                changes[resolve(stage.workdir, target) + "/.keep"] = File("")
            return 0.1
        raise BuildError(f"RUN {command}: this pretend builder does not know that command")

    @staticmethod
    def requirements(words: list[str], view: Files, stage: Stage) -> list[str]:
        path = resolve(stage.workdir, words[words.index("-r") + 1])
        f = view.get(path)
        if f is None:
            raise BuildError(f"pip: could not open requirements file: {path}")
        return [line.strip() for line in f.content.splitlines() if line.strip()]

    @staticmethod
    def pip(requirements: list[str], changes: Files, present: set[str]) -> float:
        seconds = PIP_SECONDS_PER_PACKAGE * len(requirements)
        for requirement in requirements:
            name, _, version = requirement.partition("==")
            info = PYPI.get(name)
            if info is None:
                raise BuildError(f"pip: no matching distribution for {requirement}")
            missing = [p for p in info.get("build_needs", []) if p not in present]
            if missing:
                raise BuildError(f"building {name} failed: {missing[0]} not found")
            if "build_needs" in info:
                seconds += COMPILE_SECONDS
            changes[f"{PYTHON}/{name}-{version}"] = File(version, info["size"])
        return seconds


def installed(image: Image) -> dict[str, str]:
    """The pip packages in an image, by name: {"flask": "3.1.1"}."""
    out = {}
    for path in image.filesystem():
        if path.startswith(PYTHON + "/") and "-" in path:
            name, version = path.removeprefix(PYTHON + "/").rsplit("-", 1)
            out[name] = version
    return out


def start(image: Image, needs: list[str]) -> str:
    """Start the container's app. Raises if a package or a shared library it needs is missing."""
    files = image.filesystem()
    if not image.cmd:
        raise RuntimeError("no CMD: the container has nothing to run")
    app = resolve(image.workdir, "app.py")
    if app not in files:
        raise RuntimeError(f"python: can't open file '{app}': No such file or directory")
    have = installed(image)
    for name in needs:
        if name not in have:
            raise ImportError(f"No module named '{name}'")
        lib = PYPI[name].get("links")
        if lib and lib not in files:
            raise ImportError(f"{lib.rsplit('/', 1)[1]}: cannot open shared object file")
    return files[app].content


def mb(size: int) -> str:
    return f"{size / MB:.0f} MB"
