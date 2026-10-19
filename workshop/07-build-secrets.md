# Secrets at build time

> Build arguments are written into the image's history. A secret the build needs must be mounted for one step and never become part of the image.

**Time:** 20 minutes

## Goal

By the end of this chapter you can find a leaked secret in an image's history, explain why `ARG` and `ENV` are not for secrets, and pass a secret to a single build step with BuildKit.

## The idea

### Secrets the build needs

Some builds need a credential: a token for a private package index, an SSH key for a private Git dependency, a key for an internal artifact store. Chapter 02 kept the app's own secrets out of the image. This chapter is about secrets the build itself uses.

### Where ARG and ENV end up

| Instruction | Where the value is recorded |
| --- | --- |
| `ENV TOKEN=...` | the image config. Every container starts with it, and `docker inspect` prints it. |
| `ARG TOKEN` used by a `RUN` | the image history, next to every `RUN` step that uses it. `docker history --no-trunc` prints it. |
| a file written by `RUN` | the layer that `RUN` created, even if a later step deletes it (chapter 02) |

The history is part of the image. It is pushed with it and pulled with it.

### Secret mounts

BuildKit can mount a secret for exactly one `RUN` step:

```dockerfile
RUN --mount=type=secret,id=package_token,env=PACKAGE_TOKEN python fetch_package.py
```

and you provide it when you build:

```bash
PACKAGE_TOKEN=... docker build --secret id=package_token,env=PACKAGE_TOKEN .
```

During that step, the value is in the `PACKAGE_TOKEN` variable (or in a file under `/run/secrets/`, if you leave out `env=`). It is not part of the step's cache key, not written to the layer and not recorded in the history.

## The exercise

Open `lab/exercises/07-build-secrets/`. The build fetches a private billing SDK with a token. `fetch_package.py` stands in for `pip install` against a private index: it refuses to run without a token.

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.13.16-slim-trixie
WORKDIR /app
ARG PACKAGE_TOKEN
COPY fetch_package.py .
RUN PACKAGE_TOKEN=$PACKAGE_TOKEN python fetch_package.py
COPY server.py .
EXPOSE 8000
CMD ["python", "server.py"]
```

```bash
uv run python -m dock run 7
```

```text
built with PACKAGE_TOKEN=pkg_dockerlab_99b7b8ab9421e672b516dab8

$ docker history --no-trunc dockerlab/07 | grep PACKAGE_TOKEN
  RUN |1 PACKAGE_TOKEN=pkg_dockerlab_99b7b8ab9421e672b516dab8 /bin/sh -c PACKAGE_TOKEN=$PACKAGE_TOKEN python fetch_package.py # buildkit
  ARG PACKAGE_TOKEN=pkg_dockerlab_99b7b8ab9421e672b516dab8

the token is in: docker history
```

The lab makes up a new random token for every build. In a real project, this is the token to your company's packages.

## Reasoning towards the fix

The token appears twice: on the `ARG` line and on the `RUN` line, as `|1 PACKAGE_TOKEN=...`. Docker records the build arguments a `RUN` step used, because they are part of how that layer was made.

Remove the `ARG`, and mount the token as a secret for the one step that needs it. The lab's build command already offers the token both ways, as a build argument and as a secret called `package_token`, so your Dockerfile decides which one it uses.

## Check your fix

```bash
uv run python -m dock check 7
```

As shipped:

```text
  PASS  the private package was fetched during the build
  FAIL  the token is not in docker history
  PASS  the token is not in the image config
  PASS  the token is not in any layer's files
```

The checker builds with a fresh random token, starts the API to prove the package really was fetched, then looks for the token in the history, in the config from `docker image inspect` and in every file of every layer from `docker save`. Moving the token to `ENV` fails the config check.

## In production

- In CI, pass secrets from the CI's secret store: `docker/build-push-action` takes `secrets: |` and BuildKit mounts them the same way.
- For private Git dependencies, `RUN --mount=type=ssh` forwards your SSH agent instead of copying a key.
- Some tools write credentials into files: `pip config`, `.npmrc`, `.netrc`. Mount those as secrets too, with `target=`, rather than copying them.
- If a token has ever been in an image's history or layers, rotate it. Rebuilding does not recall the images already pushed.

## Key points

- `ENV` values live in the image config, and `ARG` values used by `RUN` live in the image history.
- Both ship with the image to anyone who can pull it.
- `RUN --mount=type=secret` gives one step a secret without writing it anywhere in the image.
- Check with `docker history --no-trunc`, `docker image inspect` and `docker save`.
