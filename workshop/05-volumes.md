# Volumes and file ownership

> A container's own files disappear with it. Data belongs in a volume, and the user your app runs as must be allowed to write there.

**Time:** 20 minutes

## Goal

By the end of this chapter you can choose between a named volume, a bind mount and tmpfs, explain who owns a new volume and why, and run a stateful app as a non-root user.

## The idea

### The writable layer is temporary

Every container gets a thin writable layer on top of its image. Files the app writes go there, and `docker rm` deletes them. A redeploy is a new container, so anything written to the container's own filesystem is gone after every release.

### Three ways to mount storage

| Kind | Syntax | Lives in | Use it for |
| --- | --- | --- | --- |
| Named volume | `-v notes-data:/data` | Docker's storage area | databases, uploads, anything the app owns |
| Bind mount | `-v ./config:/etc/app:ro` | a folder on the host | source code in development, config files |
| tmpfs | `--tmpfs /tmp` | memory | scratch files that should never touch disk |

A named volume outlives every container that uses it. `docker volume ls` lists them and `docker volume rm` deletes them.

### Who owns a new volume

Linux checks permissions with numbers: a user id (uid) and a group id. Names like `app` are only labels inside one image's `/etc/passwd`.

When you mount a **new, empty** named volume, Docker copies the mount point's contents, owner and mode from the image into it. If the image has no such directory, Docker creates the mount point itself, owned by root (uid 0) with mode 755. A process running as uid 10001 can read it but not write to it.

### Why not just run as root

Running as root makes the permission error go away. It also means that any bug that lets an attacker run code gives them root inside the container, which is one kernel bug away from root on the host, and full write access to every mounted volume. Production images run as a non-root user.

## The exercise

Open `lab/exercises/05-volumes/`: a notes API that stores its data in SQLite at `/data/notes.db`, and runs as a non-root user.

```dockerfile
FROM python:3.13.16-slim-trixie
RUN useradd --system --uid 10001 --no-create-home app
WORKDIR /app
COPY server.py .
USER app
VOLUME /data
EXPOSE 8000
CMD ["python", "server.py"]
```

```bash
uv run python -m dock run 5
```

```text
$ docker ps -a --filter name=dockerlab-05
NAMES          STATUS
dockerlab-05   Exited (1) 1 second ago

$ docker logs dockerlab-05
db = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
sqlite3.OperationalError: unable to open database file

$ docker run --rm -v dockerlab-05-data:/data dockerlab/05 ls -ld /data
drwxr-xr-x 2 root root 4096 Oct 19 06:00 /data
$ docker run --rm dockerlab/05 id
uid=10001(app) gid=999(app) groups=999(app)
```

## Reasoning towards the fix

The two last commands tell the whole story. `/data` belongs to root. The app is uid 10001. The image never created `/data`, so Docker made the mount point as root, and the new volume copied that.

Create the directory in the image and give it to the app user before switching to it:

```dockerfile
RUN mkdir /data && chown app:app /data
```

The next time a new volume is mounted on `/data`, it copies that owner. Note the order: it must run before `USER app`, because only root can change ownership.

## Check your fix

```bash
uv run python -m dock check 5
```

As shipped:

```text
  FAIL  the API starts on a new, empty named volume
  FAIL  it runs as a non-root user (uid -)
  FAIL  a note saved before a redeploy is still there after it
```

The checker starts your API on a brand new volume, saves a note, deletes the container, starts a new one on the same volume, and reads the note back. Removing `USER app` makes the API start, but fails the non-root check. Writing the database somewhere else, such as `/tmp`, fails the redeploy check.

## In production

- Copying ownership only happens for **new, empty** volumes. Changing the Dockerfile later does not fix volumes that already exist: you need a one-off `chown` with a root container, or a migration.
- **Bind mounts never copy anything.** They show the host folder exactly as it is, with the host's uids. That is why files created in a container on Linux often turn up owned by root or by an unknown uid on the host.
- Kubernetes solves the same problem with `securityContext.fsGroup`, which makes the volume group-writable for a given group id.
- Databases in containers are fine with a volume and backups. Without a volume, they are a demo.

## Key points

- The container's writable layer is deleted with the container. Put data in volumes.
- A new, empty named volume copies the owner and mode of the mount point in the image.
- If the image has no mount point, Docker creates it as root.
- Create and `chown` data directories in the image, before `USER`, and run as non-root.
