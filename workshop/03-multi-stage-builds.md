# Multi-stage builds

> Build with everything, ship with nothing extra. The hard part is knowing what "nothing extra" still has to include.

**Time:** 20 minutes

## Goal

Split a build into stages, copy only the results into a small runtime image, and tell build-time dependencies from run-time ones, so the small image still starts.

## The case

```bash
uv run python -m dock run 3
```

```text
one stage:
  image size:          364 MB
  build tools inside:  gcc, make, libpq-fe.h
  docker run orders:   orders: serving on :8080
two stages:
  image size:          134 MB
  build tools inside:  none
  docker run orders:   crashed: ImportError: libpq.so.5: cannot open shared object file
```

The orders service talks to Postgres through `psycopg2`, which has C code. Building it needs a compiler and the Postgres headers. The one-stage image works, and ships gcc to production. The team moved to two stages. The image shrank by almost two thirds, and now it will not start. Open `lab/cases/case03_multistage.py`.

## Why small images matter

Size is not vanity. Every byte in an image is:

- **Pulled** by every node that runs it, at the worst moment: when you scale out under load, or replace a failed node.
- **Scanned**, and every package is a place for a known vulnerability to turn up in a report you then have to triage.
- **Available to an attacker** who gets a shell. A compiler, a package manager and `curl` make the next step easy.

But smaller is not always better, and the goal is not the smallest number. Very bare images have no shell and no tools, so debugging needs other means (`docker debug`, or an ephemeral debug container in Kubernetes). And layers you share with other images cost nothing extra on a node that already has them.

## How stages work

Each `FROM` starts a new **stage** with its own filesystem. A stage can be named with `AS`. Only the last stage becomes the image, unless you pick another with `docker build --target`.

`COPY --from=build /wheels /wheels` copies files out of an earlier stage. Nothing else crosses over: not its packages, not its environment, not its layers. That is the whole point. The build stage can be as heavy as it likes, and none of it ships.

```text
build stage                          runtime stage
python:3.13-slim                     python:3.13-slim
+ build-essential, libpq-dev         + ?
+ requirements.txt                   + /wheels  (copied from build)
+ pip wheel  ->  /wheels/*.whl       + pip install /wheels/*.whl
                                     + app.py
```

The builder also gains something: stages that the final stage does not depend on are skipped, and independent stages can build in parallel.

## Build-time and run-time dependencies

Compiled code depends on other code in two different ways.

- **To build** it, you need the compiler and the **headers**: the `.h` files that describe a library's functions. On Debian these come in `-dev` packages such as `libpq-dev`.
- **To run** it, you need the **shared library** itself: `libpq.so.5`, which the compiled extension loads when Python imports it. On Debian that is the plain library package, `libpq5`.

A wheel built in the first stage carries the compiled extension, but not the libraries it links to. The dynamic loader looks for them when the module is imported, and in the runtime stage they are not there. That is the error in the case, word for word: the loader could not open `libpq.so.5`.

You can see a binary's needs with `ldd`. In a build stage, `ldd` on the compiled `.so` files lists every shared library the runtime stage must provide.

## Clean up in the same layer

Installing a system package usually starts with `apt-get update`, which downloads package lists. In this lab they are 48 MB. They are needed to install, and useless after.

Chapter 02 showed why `RUN rm -rf /var/lib/apt/lists/*` in its own `RUN` does not help: the lists stay in the layer below. Update, install and clean belong in one `RUN`, joined with `&&`, so the layer that is saved never contained the lists. `--no-install-recommends` keeps apt from pulling in optional extras.

## Choosing a base

- **Debian slim** images (`python:3.13-slim`) are a good default: glibc, apt, a shell, and a fraction of the full image.
- **Alpine** is smaller still, but uses musl instead of glibc. Wheels built for glibc will not install there, so pip may compile from source, and some code behaves differently under musl.
- **Distroless** images hold a runtime and almost nothing else: no shell, no package manager. Good for production, harder to debug.

Whichever you choose, the build stage and the runtime stage should agree on the C library and its version. A wheel built against one and run on another is a crash waiting for the first import.

## Fix the case

The runtime stage needs one thing it does not have. Read the error, find the package that provides that file and nothing more, and install it in the runtime stage without growing the image by what apt downloads to find it. The build stage is fine as it is.

## Check it works

```bash
uv run python -m dock check 3
```

```text
  PASS  the container starts and serves (orders: serving on :8080)
  PASS  no compiler or headers in the image (found none)
  PASS  the image is under 150 MB (it is 135 MB)
```

The second and third checks are why the quick fixes fail. Installing `libpq-dev` in the runtime stage brings the headers back. Leaving the apt lists behind makes the image 183 MB.

## Exercise

Your image now runs. List every file in the runtime stage that came from a package you installed, and say whether the app would still start without each one. Then add `curl` to the runtime stage for a healthcheck (chapter 07), and decide: is it worth its size and the attack surface, or would a few lines of Python do the same job?

### More to try

- Change the runtime stage to `FROM build` and run the check. Everything works, and two checks fail. Which ones, and why is that a real problem and not a technicality?
- If you have Docker, run `docker history` on an image you use at work. Which layer is the largest, and does the running app need it?
