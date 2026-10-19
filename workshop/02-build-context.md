# The build context and .dockerignore

> `COPY . .` copies whatever the build context holds, and the build context is the whole folder unless you say otherwise. That is how secrets and gigabytes end up in images.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain what the build context is, write a `.dockerignore` file, and prove that a file is not in any layer of an image.

## The idea

### The client and the builder

`docker build -t app .` has two halves. The `docker` command is a client. The builder (BuildKit, part of the Docker engine) does the work, and it may run on another machine: a CI runner, a remote builder, or the Linux virtual machine inside Docker Desktop.

The `.` at the end is the **build context**: the folder whose files the builder may use. The client packs that folder up and sends it to the builder. A `COPY` instruction can only copy files from the context.

### What COPY . . really copies

`COPY . .` means "every file in the build context". In a real project folder, that includes:

- `.env` files with API keys and database passwords
- test data, database dumps and recordings
- `.git/`, with the full history of every file ever committed
- `node_modules/`, `.venv/` and build output from your own machine

Each of those becomes part of an image layer. Anyone who can pull the image can read them, with nothing more than `docker run` or `docker save`.

### .dockerignore

A `.dockerignore` file in the context's root lists paths to leave out, with the same kind of patterns as `.gitignore`:

```text
.env
.env.*
testdata/
.git/
__pycache__/
```

Ignored files never leave your machine. The builder cannot see them, so no instruction can copy them by accident.

### Deleting a file does not remove it

Every instruction that changes files adds a **layer**: a diff on top of the layers below. If one layer adds `.env` and a later `RUN rm .env` deletes it, the later layer only hides the file. The layer that added it still ships with the image. Try it: `uv run python -m dock try layers` measures exactly this.

## The exercise

Open `lab/exercises/02-build-context/`. It is an ordinary project folder: the API, its tests, and a Dockerfile that copies everything.

```dockerfile
FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY . .
EXPOSE 8000
CMD ["python", "server.py"]
```

`dock run 2` first creates what a real folder has and git does not: a `.env` with an API key, and 96 MB of test snapshots in `testdata/`. Then it builds:

```bash
uv run python -m dock run 2
```

```text
build context: 96.0 MB, all of it sent to every fresh builder
image size: 214.3 MB, of which this Dockerfile added 96.0 MB

$ docker run --rm dockerlab/02 cat .env
API_KEY=sk_dockerlab_6e50aac08080d1c62dc6a9b9

Anyone who can pull this image can read the API key.
```

The key is a random one the lab made up, but the leak is real. Push this image to a registry and the key goes with it.

## Reasoning towards the fix

Two things are wrong, and one file fixes both:

- The context is 96 MB, so every fresh build (every CI run) uploads 96 MB before it starts. BuildKit sends only what changed since the last build of the same folder, so you may only notice on a clean machine.
- `.env` and `testdata/` end up in a layer.

Add a `.dockerignore` next to the Dockerfile that leaves out secrets, test data and tooling. The server still needs its key at run time, so pass it when the container starts, not when the image is built:

```bash
docker run --env-file exercises/02-build-context/.env dockerlab/02
```

## Check your fix

```bash
uv run python -m dock check 2
```

As shipped:

```text
  FAIL  the build context is under 1 MB (it holds 96.0 MB)
  FAIL  no .env file in any layer of the image
  FAIL  the API key's value appears nowhere in the image (found in layer file app/.env)
  FAIL  the image adds under 1 MB to its base (adds 96.0 MB)
  PASS  the API still gets API_KEY at run time, from --env-file
```

The checker measures the context by copying it into an empty image, so it sees exactly what Docker sees after `.dockerignore`. It then saves the image with `docker save` and opens every layer, looking for any file named `.env` and for the key's value anywhere: in files, in the image config and in `docker history`. That is why adding `RUN rm .env` does not pass. The file is still in the layer below.

## In production

- Treat every image as public. Registries get misconfigured, images get copied to laptops, and old tags live for years.
- Secrets belong to the running container: environment variables from your orchestrator, mounted secret files, or a secrets manager. Chapter 07 covers secrets that the build itself needs.
- Prefer copying what you need over copying everything: `COPY pyproject.toml uv.lock ./` then `COPY src/ src/`. A `.dockerignore` is still worth having, because it also keeps the context small.
- If a secret has ever been in a pushed image, rotate it. Deleting the tag does not delete the copies.

## Key points

- The build context is the folder you pass to `docker build`. `COPY` can only copy from it.
- `COPY . .` copies everything in the context, secrets and junk included.
- `.dockerignore` keeps files out of the context, and so out of every layer.
- Deleting a file in a later layer hides it but does not remove it from the image.
