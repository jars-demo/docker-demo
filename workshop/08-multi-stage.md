# Multi-stage builds

> The tools you need to build an app are not the tools you need to run it. Build in one stage, run in another, and copy across only the result.

**Time:** 25 minutes

## Goal

By the end of this chapter you can read where an image's size comes from, split a Dockerfile into a build stage and a runtime stage, and ship a small image that runs as a non-root user with no compiler inside.

## The idea

### Why size and contents matter

A large image costs time on every pull: on every deploy, every autoscaling event, every new CI runner. Worse, every package in it is a package you have to patch. A compiler, a package manager and development headers in a production image are tools an attacker can use, and vulnerability scanners will report every one of their CVEs against your service.

`uv run python -m dock try sizes` builds the same small server on three bases:

```text
  1,112.0 MB  python:3.13.16-trixie        tools: gcc, curl, apt-get
    118.3 MB  python:3.13.16-slim-trixie   tools: apt-get
     51.9 MB  python:3.13.16-alpine        tools: apk
```

### Stages

A Dockerfile can have several `FROM` lines. Each starts a new **stage**, and only the last stage becomes the image. `COPY --from=<stage>` copies files out of an earlier stage:

```dockerfile
FROM python:3.13.16-trixie AS build
# ...compile and install everything here...

FROM python:3.13.16-slim-trixie
COPY --from=build /opt/venv /opt/venv
```

The build stage can be as big as it likes. None of its layers ship.

### Build dependencies and runtime dependencies

Native code needs different things at different times. psycopg's C build, used in this exercise, needs:

| When | What | Debian package |
| --- | --- | --- |
| building | a C compiler and make | `gcc`, `make` |
| building | libpq's headers and `pg_config` | `libpq-dev` |
| running | the libpq shared library | `libpq5` |

The runtime stage needs only the last row. Leave it out and the image is small and broken: `ImportError: libpq.so.5: cannot open shared object file`.

Why build psycopg from source at all, when a `psycopg[binary]` wheel exists? The binary wheel bundles its own copy of libpq, which only changes when psycopg releases. The C build links to the system's libpq, which gets security fixes with your base image. psycopg's own documentation recommends the local build for production.

## The exercise

Open `lab/exercises/08-multi-stage/`:

```dockerfile
FROM python:3.13.16-trixie
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
EXPOSE 8000
CMD ["python", "server.py"]
```

```bash
uv run python -m dock run 8
```

```text
image size: 1,138.5 MB
build tools inside: /usr/bin/gcc, /usr/bin/cc, /usr/bin/make, /usr/bin/pg_config
runs as uid: 0
```

followed by the largest layers from `docker history`. To see them yourself:

```bash
docker history dockerlab/08
```

## Reasoning towards the fix

The full Python image is right for building psycopg and wrong for running it. Split the work:

1. **Build stage**, on the full image: create a virtual environment in `/opt/venv` and install the requirements into it. psycopg-c compiles here.
2. **Runtime stage**, on the slim image: install `libpq5` (and clean the apt lists in the same `RUN`), create a user, copy `/opt/venv` from the build stage, put it on `PATH`, copy the server, and switch to the user.

A virtual environment works well as the unit to copy, because it is one directory with everything installed. Both stages use the same Python version at the same path, so the venv's interpreter link still works.

## Check your fix

```bash
uv run python -m dock check 8
```

As shipped:

```text
  FAIL  the image is under 200.0 MB (it is 1,138.5 MB)
  FAIL  no compiler or build tools in the final image (/usr/bin/gcc, /usr/bin/cc, /usr/bin/make, /usr/bin/pg_config)
  FAIL  it runs as a non-root user (uid 0)
  PASS  the API starts and answers /healthz
  PASS  psycopg uses its compiled C build (loaded: c)
```

With the two-stage Dockerfile, the same app measured **149.8 MB**, with no build tools, running as uid 10001.

Two wrong fixes fail on purpose. Switching to `psycopg[binary]` on the slim image is small, but fails the last check. Copying the venv without installing `libpq5` builds fine, then fails to import: the image that shrank too far.

## In production

- **Distroless and scratch.** For compiled languages like Go and Rust, the runtime stage can be `gcr.io/distroless/static` or even `scratch`: no shell and no package manager at all, often under 20 MB.
- **Target a stage.** `docker build --target build` stops at a stage, which is handy for a stage that runs the tests.
- **Scan what you ship.** Tools like `docker scout cves` and Trivy list known vulnerabilities in an image. Fewer packages, fewer findings.
- **Read-only root filesystem.** A runtime image that never writes outside its volumes can run with `--read-only`, which makes tampering much harder.

## Key points

- Only the last stage of a Dockerfile becomes the image.
- Build in a stage with compilers and headers. Run in a slim stage with only runtime libraries.
- Copy across a self-contained result, such as a virtual environment.
- Check the result: size, no build tools, a non-root user, and that the native code still loads.
