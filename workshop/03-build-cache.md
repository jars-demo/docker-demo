# Layers and the build cache

> The build cache reuses a layer only if everything before it is unchanged. Put what changes rarely first and what changes on every commit last.

**Time:** 25 minutes

## Goal

By the end of this chapter you can predict which steps of a Dockerfile will come from the cache, order a Dockerfile so that code changes rebuild in under a second, and read BuildKit's output to confirm it.

## The idea

### Every instruction is a layer, and every layer has a key

BuildKit runs a Dockerfile top to bottom. For each instruction it computes a **cache key** from:

- the key of the step before it (its parent)
- the instruction's own text, such as `RUN pip install -r requirements.txt`
- for `COPY` and `ADD`, a checksum of every file being copied

If a layer with that key already exists, the step is **CACHED** and takes no time. If not, the step runs and its result is stored under the new key.

### One miss, and everything after it misses

Because each key includes its parent's key, a miss is contagious. If step 3 misses, step 4's parent is new, so step 4 misses even if its own text is unchanged, and so on to the end.

That gives the one rule of Dockerfile ordering:

> Order instructions from the ones that change least often to the ones that change most often.

Base image, system packages, dependency manifests, dependency install: rarely. Your source code: on every commit.

### What RUN does not see

A `RUN` step's key is its text and its parent, not the result. `RUN pip install fastapi` stays cached forever, even when a new fastapi is released. `RUN apt-get update` stays cached too, which is why it should always share a line with `apt-get install`. If you need a fresh run, change the instruction or build with `--no-cache`.

## The exercise

Open `lab/exercises/03-build-cache/`: a FastAPI service with pinned dependencies.

```dockerfile
FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`dock run 3` builds it, changes one line in `app/main.py` the way a commit would, and builds again:

```bash
uv run python -m dock run 3
```

```text
build 1: the first build of this Dockerfile
  base image     FROM docker.io/library/python:3.13.16-slim-trixie
  cached         WORKDIR /app
  ran     0.0 s  COPY . .
  ran     6.6 s  RUN pip install --no-cache-dir -r requirements.txt
  total 7.3 s

build 2: after changing one line in app/main.py
  base image     FROM docker.io/library/python:3.13.16-slim-trixie
  cached         WORKDIR /app
  ran     0.0 s  COPY . .
  ran     6.2 s  RUN pip install --no-cache-dir -r requirements.txt
  total 6.8 s

One changed line of code reinstalled every dependency: 6.2 s of pip install on every commit.
```

To see the same thing by hand, build with plain progress output and look for the word `CACHED`:

```bash
docker build --progress=plain -t dockerlab/03 exercises/03-build-cache
```

Six seconds is this small service on a fast connection. On a real project with compiled dependencies, it is often minutes, on every push, for every developer and every CI run.

## Reasoning towards the fix

Follow the keys. `COPY . .` copies `app/main.py`, so editing it changes that step's checksum. The step misses. `pip install` comes after it, so its parent changed, and it misses too.

`pip install` only reads one file: `requirements.txt`. If only that file is copied before the install, the install's key depends only on the dependencies. Copy the rest of the code afterwards.

Reorder the Dockerfile, then check.

## Check your fix

```bash
uv run python -m dock check 3
```

As shipped:

```text
  FAIL  after a code change, pip install comes from the cache (the rebuild took 8.3 s)
  PASS  the new code is in the image (/version says 2)
  PASS  a change to requirements.txt still re-runs pip install
```

With the fix, the rebuild after a code change measured 0.4 s on the same machine.

The checker builds a copy of your exercise, changes the code, rebuilds, and starts the image to make sure the new code is really in it. Then it changes `requirements.txt` and confirms that the install runs again. That last check catches a tempting wrong fix: hard-coding the packages in `RUN pip install fastapi==... uvicorn==...` before `COPY . .`. It caches well, but it never notices when the dependency file changes.

Try the same ordering in the simulator on the home page, and see how many seconds of pip install a day of commits costs each way.

## In production

- **Cache mounts.** `RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt` keeps pip's download cache between builds, so even a real dependency change only downloads what is new. The cache lives in the builder, never in the image.
- **CI has no cache by default.** A fresh runner starts empty. Use `docker buildx build --cache-from type=registry,ref=... --cache-to type=registry,ref=...,mode=max`, or your CI's cache backend, to share layers between runs.
- **Lock files.** Copy the lock file (`uv.lock`, `poetry.lock`, `package-lock.json`) with the manifest, so the dependency layer changes exactly when the resolved versions change.
- **Base image updates.** A pinned base never changes, so security fixes never arrive. Rebuild on a schedule with `--pull`, or pin by digest and let a bot propose updates (chapter 12).

## Key points

- Each step's cache key comes from its parent, its instruction and, for `COPY`, the files it copies.
- A miss invalidates every step after it.
- Copy dependency manifests and install them before copying the code.
- `RUN` steps cache on their text, not their result. Change the text or use `--no-cache` to force a fresh run.
