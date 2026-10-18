# What a layer remembers

> Deleting a file in a later layer hides it. The bytes stay in the layer below, in every copy of the image.

**Time:** 20 minutes

## Goal

Know what the build context is and how `.dockerignore` shapes it, understand why a deleted file is still inside an image, and keep secrets out of images, both at build time and at run time.

## The case

```bash
uv run python -m dock run 2
```

```text
final filesystem has /app/.env: False
payments at run time:           connected
but docker save writes out every layer, and the token is still there:
  layer 3 (COPY . .): /app/.env  PAYMENT_TOKEN=tp-prod-4f9a2c71
anyone who can pull tidepool/orders can read the payment token
```

The orders service needs a payment token. On a laptop it lives in `.env`. In compose, `env_file` hands it to the container at run time, and payments connect. Someone spotted `.env` inside the image and added `RUN rm -f .env`. Now a shell in the container finds no `.env`. Open `lab/cases/case02_secret_layer.py` and read the Dockerfile and the ignore list.

## The build context

When you run `docker build .`, the dot is the **build context**: the folder whose files the build may use. The builder runs apart from your shell, often in another process, sometimes on another machine. It can only see what the client gives it.

The classic builder packed the whole context into a tar and sent all of it before the first step. BuildKit, the builder in current Docker, is smarter: it transfers files as `COPY` and `ADD` ask for them. But `COPY . .` asks for everything.

So the context decides two things: how much work every build does before the cache can answer, and what can end up in the image. Measure the first one:

```bash
uv run python -m dock try context
```

```text
Python 3.13.16, Linux, 4 CPUs
A pretend project: source, templates, a .git folder, node_modules and two data dumps.

  context                    files    tar size   tar + sha256
  everything                  4555     93.3 MB        1316 ms
  with .dockerignore            53      0.3 MB           6 ms

.dockerignore here: .git, node_modules, data. The classic builder sends the whole tar
on every build. BuildKit sends files as COPY asks for them, and COPY . . asks for all.
```

Over a second of packing and hashing on every build, for files the app never reads, against 6 ms. On a remote builder, add the time to send 93 MB.

## .dockerignore

`.dockerignore` sits next to the Dockerfile and lists what to leave out of the context. A few rules surprise people:

- Patterns are matched from the root of the context. `*.pyc` matches `app.pyc` at the top, not `src/app.pyc`. Write `**/*.pyc` for every level.
- A pattern that names a folder leaves out everything inside it.
- A line starting with `!` adds a file back, and the last matching line wins.

A good default for most projects: `.git`, dependency folders such as `node_modules` and `.venv`, build output, local data, and every file that holds a secret: `.env`, `*.pem`, `*.key`, cloud credentials.

## Deleted is not gone

Here is the part that matters most. Each layer is a set of changes on top of the one below. When `RUN rm -f .env` deletes a file that came from an earlier layer, it cannot change that earlier layer. Layers are read only, and identified by the hash of their contents. Instead, the new layer records a **whiteout**: a marker that says "hide this path from here up".

A container sees the merged view, so the file looks gone. The image still carries layer 3, byte for byte. Anyone who can pull the image can unpack it:

```bash
docker image save tidepool/orders -o orders.tar   # every layer, as a tar of tars
docker history --no-trunc tidepool/orders          # every instruction, with its arguments
```

The same is true of size. Download a 200 MB file in one `RUN`, delete it in the next, and the image is 200 MB bigger. Clean up in the same `RUN` that made the mess, or the cleanup only hides it.

So treat every layer as published. If a secret was ever in one, and the image was ever pushed, the secret is out. Rotate it. Rebuilding without it removes it from new images, not from copies already pulled.

## Other places secrets leak

- **`ENV`** puts the value in the image config, readable with `docker inspect`. It also sets it for every process in every container.
- **`ARG`** values used by a `RUN` are recorded in the image history.
- **A `RUN` that echoes the secret into a file** leaves it in that layer, even if a later step deletes the file.

For a secret the **build** needs, such as a token for a private package index, BuildKit has secret mounts. The file exists only while that one `RUN` runs and is never written to a layer:

```dockerfile
RUN --mount=type=secret,id=pip_token PIP_INDEX_URL="https://$(cat /run/secrets/pip_token)@pypi.example/simple" pip install -r requirements.txt
```

For a secret the app needs at **run time**, give it to the container when it starts: environment variables from the orchestrator, `env_file` in compose, a mounted secret file, or a secret manager the app asks at boot. The image stays the same in every environment, and holds nothing worth stealing.

## Fix the case

The token reached the image because it was sent to the builder in the first place. Stop sending it. The app must still get its token at run time, so the file stays in the project. Keep everything the current ignore list already keeps out.

## Check it works

```bash
uv run python -m dock check 2
```

```text
  PASS  no layer, history line or ENV holds the token (found 0)
  PASS  the app gets its token at run time: payments connected
  PASS  the image holds the app: app.py and templates/menu.html
  PASS  the git history stays out of the image
```

## Exercise

Your fix kept the token out of the context. Write a second Dockerfile that would also be safe even if `.dockerignore` were deleted tomorrow. Which instructions does it use instead of `COPY . .`? What does it cost you when someone adds a new folder the app needs?

### More to try

- Put `ENV PAYMENT_TOKEN=...` in the Dockerfile and run the check. Which line fails, and where would `docker inspect` show the value?
- If you have Docker, build any image with a `RUN rm` of a big file, then compare `docker image ls` before and after removing the `rm`. The size does not move.
