# Layers and the build cache

> An image is a stack of layers, and the build cache reuses every layer it can, until the first step that changed.

**Time:** 15 minutes

## Goal

Know what an image is made of, predict which steps of a build will run again after a change, and order a Dockerfile so that the slow steps only run when their inputs change.

## The case

```bash
uv run python -m dock run 1
```

```text
first build, empty cache:    96.3 s
edit app.py: sencha 4.50 -> 4.80, then build again:
  CACHED  FROM python:3.13-slim                    0.0 s
  CACHED  WORKDIR /app                             0.0 s
  RAN     COPY . .                                 0.3 s
  RAN     RUN pip install -r requirements.txt     96.0 s
  RAN     CMD ["gunicorn", "app:app"]              0.0 s
rebuild after a one-line edit: 96.3 s
of that, reinstalling 6 unchanged packages: 96.0 s
the new image charges 4.80 for sencha
```

Tidepool Tea sells loose-leaf tea, and its orders service ships as an image. Someone changed the price of sencha, one line in `app.py`, and the rebuild took as long as the first build ever did. Open `lab/cases/case01_cache_order.py`. The Dockerfile is five lines. One of them is in the wrong place.

The lab does not need Docker. `lab/dock/engine.py` is a small pretend builder that follows the real rules for layers and the cache, with pretend time, so every run prints the same seconds.

## What an image is

An image is not one file. It is an ordered list of **layers** plus a small config: the command to run, the environment, the working directory, the user.

Each layer is a set of file changes: files added, files changed, files deleted. Most Dockerfile instructions that touch files make one layer: `COPY`, `ADD` and `RUN`. Instructions such as `WORKDIR`, `ENV` and `CMD` only change the config, and show up in the history with no size.

When a container starts, the runtime stacks the layers with a union filesystem (overlayfs on Linux), so the process sees one tree. On top it adds one thin **writable layer** that belongs to that container alone. Everything below is read only and shared: ten containers from the same image share one copy of its layers on disk.

That sharing is why layers matter. A layer is stored, pushed and pulled once per digest. If two images start `FROM python:3.13-slim`, a machine that has one already has most of the other.

## How the build cache decides

The builder walks the Dockerfile top to bottom. For each step it asks one question: have I built exactly this step, on exactly this parent, before?

- For most instructions, "exactly this step" means the same instruction text on the same parent layer. `RUN pip install -r requirements.txt` has the same text every time, so the text alone never misses.
- For `COPY` and `ADD`, the builder also hashes the contents of the files being copied. Change one byte in one copied file and the step misses. Timestamps are not part of that hash.
- Once one step misses, every step after it misses too, because its parent is new.

That last rule is the whole case. `COPY . .` copies the entire project, so any edit to any file changes its hash. It misses, and so does the expensive `pip install` below it, even though `requirements.txt` did not change.

Notice what the cache does **not** do. It does not look inside a `RUN` command to see which files it reads. It cannot know that pip only cares about one file. You tell it, by what you copy before the `RUN`.

## Order by how often things change

The rule of thumb: put the steps whose inputs change least at the top, and the steps whose inputs change most at the bottom.

For most applications that order is:

1. The base image.
2. System packages.
3. The dependency manifest alone (`requirements.txt`, `package.json` and its lock file, `go.mod` and `go.sum`), then the install.
4. The application code.

Dependencies change every few weeks. Code changes every few minutes. Copying the manifest on its own gives the install step an input that only changes when the dependencies do.

## When the cache is wrong, or missing

The cache is a speed-up, and it has two classic traps.

**A cached step can be stale.** `RUN apt-get update` has the same text every day, so it is cached forever, and the package lists inside it grow old. If a later step installs packages from those lists, you get old versions, or a "404 Not Found" when the mirror has moved on. That is why `apt-get update` and `apt-get install` belong in the same `RUN`. To force a fresh build, use `docker build --no-cache`, or `--no-cache-filter` for one stage.

**The cache may not be there at all.** On a laptop the cache survives between builds. On many CI systems every job starts on a fresh machine with an empty cache, so a well-ordered Dockerfile still rebuilds everything. BuildKit can export the cache and import it on the next run (`--cache-to` and `--cache-from`, to a registry or to the CI system's own cache). Without that, the order of your Dockerfile only helps on your own machine.

BuildKit also offers **cache mounts**: `RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt` keeps pip's download cache between builds without putting it in a layer. Even when the install step does run, it does not download everything again.

## Fix the case

Only edit `DOCKERFILE`. Give the install step an input that changes only when the dependencies change, and copy the rest of the project after it. The image still needs every file the app uses.

## Check it works

```bash
uv run python -m dock check 1
```

```text
  PASS  the rebuilt image starts and charges 4.80 for sencha (4.80)
  PASS  a one-line edit to app.py rebuilds in under 5 s (took 0.3 s)
  PASS  a change to requirements.txt is installed: flask 3.1.2
  PASS  the image holds the whole app: app.py and templates/menu.html
```

The third check is why "never reinstall" is not a fix. When `requirements.txt` does change, the install must run again, and the cache has to notice.

## Exercise

Write down, before you run anything, which steps of your fixed Dockerfile would say RAN after each of these changes: an edit to `templates/menu.html`; a new line in `requirements.txt`; a change of the base image to `python:3.13-slim-bookworm`. Then explain why the third one rebuilds everything, even though no file of yours changed.

### More to try

- Swap the fix for `RUN pip install -r requirements.txt` above any `COPY`. Run the check and read the error. What does a `RUN` step see of your project before anything is copied?
- Run `uv run python -m dock try context` and look at how long it takes to pack and hash a context with `node_modules` and `.git` in it. That time is spent on every build, before the cache can even answer. Chapter 02 explains how to cut it.
