"""Case 03: the image that shrank too far.

The orders image was 364 MB, most of it a C compiler that only the build needs. So the team split
the Dockerfile in two: a build stage that compiles the Postgres driver into a wheel, and a slim
runtime stage that installs the wheel. The image is small now. It also crashes on start.
Run it: uv run python -m dock run 3
"""

from dock.engine import Build, Builder, Image, mb, start

# Before: one stage. It works, and ships gcc and the Postgres headers to production.
ONE_STAGE = """\
FROM python:3.13-slim
RUN apt-get update && apt-get install -y build-essential libpq-dev
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
"""

# After: two stages. Small, and broken.
DOCKERFILE = """\
FROM python:3.13-slim AS build
RUN apt-get update && apt-get install -y build-essential libpq-dev
WORKDIR /src
COPY requirements.txt .
RUN pip wheel -r requirements.txt -w /wheels

FROM python:3.13-slim
WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install /wheels/*.whl
COPY app.py .
CMD ["python", "app.py"]
"""

PROJECT = {
    "requirements.txt": "flask==3.1.1\npsycopg2==2.9.10\n",
    "app.py": "import flask, psycopg2\nprint('orders: serving on :8080')\n",
}

NEEDS = ["flask", "psycopg2"]

TOOLS = ("/usr/bin/gcc", "/usr/bin/make", "/usr/include/postgresql/libpq-fe.h")


def release() -> Build:
    return Builder().build(DOCKERFILE, PROJECT)


def boot(image: Image) -> str:
    try:
        return start(image, NEEDS).splitlines()[-1].removeprefix("print('").removesuffix("')")
    except (ImportError, RuntimeError) as error:
        return f"crashed: {type(error).__name__}: {error}"


def run() -> None:
    before = Builder().build(ONE_STAGE, PROJECT).image
    after = release().image
    for name, image in (("one stage", before), ("two stages", after)):
        tools = [path.rsplit("/", 1)[1] for path in TOOLS if path in image.filesystem()]
        print(f"{name}:")
        print(f"  image size:          {mb(image.bytes)}")
        print(f"  build tools inside:  {', '.join(tools) or 'none'}")
        print(f"  docker run orders:   {boot(image)}")
