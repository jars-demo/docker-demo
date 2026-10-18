"""Case 02: the token in layer three.

The orders service needs a payment token. On a laptop it lives in .env, and at run time the
container gets it from env_file in compose. Someone noticed .env being copied into the image, so
they added a line that deletes it. The final image has no .env. Every pulled copy still does.
Run it: uv run python -m dock run 2
"""

from dock.engine import Build, Builder, start

TOKEN = "tp-prod-4f9a2c71"

DOCKERIGNORE = """\
.git
__pycache__
*.pyc
"""

DOCKERFILE = """\
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN rm -f .env
CMD ["python", "app.py"]
"""

PROJECT = {
    ".git/HEAD": "ref: refs/heads/main\n",
    ".git/objects/pack/pack-3f1c.pack": "git history\n",
    ".env": f"PAYMENT_TOKEN={TOKEN}\n",
    "app.py": 'import os\nTOKEN = os.environ["PAYMENT_TOKEN"]\n',
    "templates/menu.html": "<h1>Today's teas</h1>\n",
    "__pycache__/app.cpython-313.pyc": "bytecode\n",
}


def env_file(text: str) -> dict[str, str]:
    """Read a .env file the way compose does: one NAME=value per line."""
    pairs = (line.split("=", 1) for line in text.splitlines() if "=" in line)
    return {name.strip(): value.strip() for name, value in pairs}


def release() -> Build:
    return Builder().build(DOCKERFILE, PROJECT, DOCKERIGNORE)


def container_env(build: Build) -> dict[str, str]:
    """The environment the running container sees: the image's ENV, then compose's env_file."""
    return {**build.image.env, **env_file(PROJECT.get(".env", ""))}


def payments(build: Build) -> str:
    start(build.image, [])
    token = container_env(build).get("PAYMENT_TOKEN")
    return "connected" if token == TOKEN else f"refused (token {token!r})"


def leaks(build: Build) -> list[tuple[int, str, str]]:
    """Every place an attacker with `docker save` finds the token: (layer, instruction, path)."""
    found = []
    for number, layer in enumerate(build.image.layers, 1):
        if TOKEN in layer.instruction:
            found.append((number, layer.instruction, "history"))
        for path, f in layer.files.items():
            if f is not None and TOKEN in f.content:
                found.append((number, layer.instruction, path))
    if any(TOKEN in value for value in build.image.env.values()):
        found.append((0, "image config", "ENV"))
    return found


def run() -> None:
    build = release()
    print(f"final filesystem has /app/.env: {'/app/.env' in build.image.filesystem()}")
    print(f"payments at run time:           {payments(build)}")
    print("but docker save writes out every layer, and the token is still there:")
    for number, instruction, path in leaks(build):
        print(f"  layer {number} ({instruction}): {path}  PAYMENT_TOKEN={TOKEN}")
    print("anyone who can pull tidepool/orders can read the payment token")
