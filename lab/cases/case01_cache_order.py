"""Case 01: the rebuild that reinstalled everything.

Tidepool Tea sells loose-leaf tea online. The orders service ships as an image built from the
Dockerfile below. Change one price in app.py and the rebuild should take a second. Instead it
reinstalls every Python package, every time, and takes over a minute and a half.
Run it: uv run python -m dock run 1
"""

import re

from dock.engine import Builder, Image, installed, start

DOCKERFILE = """\
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["gunicorn", "app:app"]
"""

PROJECT = {
    "requirements.txt": "flask==3.1.1\ngunicorn==23.0.0\njinja2==3.1.6\n"
    "requests==2.32.4\npydantic==2.11.7\nbabel==2.17.0\n",
    "app.py": 'MENU = {"sencha": "4.50", "hojicha": "5.20"}\n',
    "templates/menu.html": "<h1>Today's teas</h1>\n",
}

NEEDS = ["flask", "gunicorn", "jinja2", "requests", "pydantic", "babel"]


def edit(project: dict[str, str], path: str, old: str, new: str) -> dict[str, str]:
    changed = dict(project)
    changed[path] = changed[path].replace(old, new)
    return changed


def sencha(image: Image) -> str:
    """What the running container charges for sencha."""
    return re.search(r'"sencha": "([\d.]+)"', start(image, NEEDS))[1]


def morning(builder: Builder | None = None):
    """Build once, then change the price of sencha and build again with the same cache."""
    builder = builder or Builder()
    first = builder.build(DOCKERFILE, PROJECT)
    second = builder.build(DOCKERFILE, edit(PROJECT, "app.py", '"4.50"', '"4.80"'))
    return first, second


def run() -> None:
    first, second = morning()
    print(f"first build, empty cache:   {first.seconds:5.1f} s")
    print("edit app.py: sencha 4.50 -> 4.80, then build again:")
    for step in second.steps:
        mark = "CACHED" if step.cached else "RAN   "
        print(f"  {mark}  {step.instruction:<38} {step.seconds:5.1f} s")
    pip = sum(s.seconds for s in second.steps if "pip install" in s.instruction)
    print(f"rebuild after a one-line edit: {second.seconds:.1f} s")
    print(f"of that, reinstalling {len(installed(second.image))} unchanged packages: {pip:.1f} s")
    print(f"the new image charges {sencha(second.image)} for sencha")
