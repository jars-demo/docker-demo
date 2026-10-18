# Volumes and ownership

> A container is disposable, and so is everything written inside it. Data lives in volumes, and a volume only helps if the app can write to it.

**Time:** 20 minutes

## Goal

Know where a container's writes go, how named volumes and bind mounts differ, how a new named volume gets its owner, and how to run as a non-root user without losing your data.

## The case

```bash
uv run python -m dock run 8
```

```text
startup warning: /data is not writable by uid 10001 (owner uid 0, mode 755); saving orders to /tmp
orders taken today:                    42
docker compose up --build (new container, same volume)
orders on file after the redeploy:     0
```

Orders are saved in SQLite under `/data`, and compose mounts a named volume there. The image runs as the user `tidepool` (uid 10001), as it should. After a redeploy, the day's 42 orders are gone, and the volume is empty. The app warned at start-up, once, in a log nobody read. Open `lab/cases/case08_volume.py`.

## Where writes go

Chapter 01 described the thin **writable layer** each container gets on top of its image. Every file the app writes outside a mount lands there. It lives exactly as long as the container.

And containers are replaced all the time. `docker compose up` recreates a container whenever its image or configuration changed. A deploy, a node failure or a scale-down does the same. Anything in the writable layer goes with it. That is good for temporary files, and fatal for data.

## Volumes and bind mounts

There are two common ways to give a container storage that outlives it.

- A **named volume** (`orders-data:/data`) is storage that Docker creates and manages. It survives the container, is reused by the next one with the same mount, and is only deleted on purpose: `docker volume rm`, or `docker compose down -v`. Leave off the `-v` unless you mean it.
- A **bind mount** (`./data:/data`) shows a folder from the host inside the container, as it is. Good for source code in development. In production it ties the container to one host's paths.

A third kind, **tmpfs**, lives in memory and vanishes when the container stops. Good for scratch files and secrets, never for data.

## Who owns a new volume

Linux checks permissions by number. A process running as uid 10001 can write to a folder if it owns the folder and the owner can write, or if the folder is writable by everyone. Names such as `tidepool` exist only in `/etc/passwd` inside the image.

When a container mounts a named volume that is **empty**, Docker first fills it from the image: the files at that path in the image, and the **owner and mode of the folder itself**. That is a feature. It means the image decides how a new volume starts out.

In the case, the Dockerfile runs `mkdir -p /data` as root, so the folder in the image belongs to uid 0 with mode 755. The new volume copies that. The app, running as uid 10001, cannot write to it, falls back to `/tmp`, and `/tmp` is in the writable layer.

So the folder must belong to the app user in the image, before the `USER` line drops root. Chapter 02 still applies: do it in the same `RUN` that creates the folder.

## Traps that survive the fix

**Existing volumes keep their owner.** Docker only fills a volume from the image when the volume is empty. A volume created by the broken image still belongs to root after you fix the Dockerfile. Either change the ownership once by hand, or do what the official Postgres image does: start as root, fix ownership of the data folder, then drop to the app user with `exec gosu`, which keeps PID 1 right (chapter 05).

**Bind mounts are not filled.** A bind mount shows the host folder exactly, with the host's numbers. If the host folder belongs to uid 1000 and the app runs as 10001, the app cannot write. Match the uid, use a group both share, or use a named volume. Docker Desktop on macOS and Windows translates ownership on shared folders, so this often works on a laptop and fails on a Linux server.

**chmod 777 is not a fix.** It works, and it lets every process in the container write the data, including anything an attacker runs. Give the folder to the one user that needs it.

**Running as root is not a fix either.** It works too. It also means a bug in the app runs as root in the container, and with a careless mount, as root on the host. Run as a fixed, numbered, non-root user.

## A volume is not a backup

A named volume survives redeploys. It does not survive `docker compose down -v`, a lost disk, or a bad migration. Back up the data with the tools for that data, such as `pg_dump` or the SQLite backup API, and test a restore.

## Fix the case

The app is right to run as uid 10001, and right to save in `/data`. Make a brand new volume start out writable by that user and nobody else, by changing how the image creates the folder.

## Check it works

```bash
uv run python -m dock check 8
```

```text
  PASS  orders survive a redeploy (42 before, 42 after)
  PASS  the app runs as uid 10001, not root (uid 10001)
  PASS  /data is not world-writable (mode 755)
  PASS  orders are saved on the volume, not in the container
```

## Exercise

The volume `orders-data` already exists in production, created by the broken image. Today's orders sit in `/tmp` in the running container, and none are in the volume. Write the steps, in order, to deploy your fix without losing those orders. Which step needs root, and where does it run?

### More to try

- Change `DATA_DIR` to `/app/data` and run the check. Which mounts would you need for that to work?
- Change the app's fallback so it refuses to start when `/data` is not writable, instead of quietly using `/tmp`. Which behaviour would have caught this bug on the first deploy?
