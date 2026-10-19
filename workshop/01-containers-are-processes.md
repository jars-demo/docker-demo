# Containers are processes

> A container is not a small virtual machine. It is one process, with walls around it, and it lives exactly as long as that process does.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain what a container is in terms of processes and the kernel, run and inspect one, and say why a container that "just exits" is almost always a process that finished.

## The idea

### An image and a container

An **image** is a read-only bundle: a filesystem (the files a program needs) plus some settings (which command to run, which user, which environment variables). It does nothing on its own.

A **container** is a running process started from an image. Docker asks the Linux kernel to start that process with three kinds of walls around it:

| Wall | Kernel feature | What the process sees |
| --- | --- | --- |
| Its own view of the system | namespaces | its own process list, hostname, network interfaces and mounts |
| Its own share of the machine | cgroups | a limit on CPU, memory and number of processes |
| Its own files | a layered filesystem | the image's files, plus a thin writable layer on top |

There is no second kernel and no hardware emulation. That is why a container starts in well under a second and why it can only run programs built for the host's kernel. On macOS and Windows, Docker Desktop runs a small Linux virtual machine and your containers run inside it.

### The main process is the container

The command in the image (`CMD`, or what you pass to `docker run`) becomes **PID 1** inside the container's process namespace. Docker watches that one process:

- while PID 1 runs, the container is **Up**
- when PID 1 exits, the container is **Exited**, with PID 1's exit code
- anything else running inside is killed along with it

So "my container keeps exiting" nearly always means "my main process finished". A web server should never finish on its own. A script that starts the server in the background and then reaches its last line does finish.

### The commands you will use all day

```bash
docker build -t myapp .          # build an image from the Dockerfile in this folder
docker run -d --name web myapp   # start a container in the background
docker ps                        # running containers
docker ps -a                     # all containers, including ones that exited
docker logs web                  # what the main process wrote to stdout and stderr
docker exec -it web sh           # run another process inside the same walls
docker stop web                  # ask the main process to stop
docker rm web                    # delete the stopped container and its writable layer
```

## The exercise

The lab lives in `lab/`. Each exercise is a folder you edit, and `dock` checks your work with real builds and containers.

```bash
cd lab
uv sync
uv run python -m dock list
```

Open `lab/exercises/01-containers-are-processes/`. It holds a small JSON API (`server.py`), a start script and a Dockerfile:

```dockerfile
FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY server.py start.sh ./
EXPOSE 8000
CMD ["sh", "start.sh"]
```

```bash
#!/bin/sh
# Start the API.
echo "starting the api"
python server.py &
echo "api started"
```

Build it and run it yourself:

```bash
docker build -t dockerlab/01 exercises/01-containers-are-processes
docker run -d --name dockerlab-01 -p 127.0.0.1:8001:8000 dockerlab/01
docker ps -a --filter name=dockerlab-01
```

Or let the lab do it and show you the result:

```bash
uv run python -m dock run 1
```

```text
$ docker ps -a --filter name=dockerlab-01
NAMES          STATUS
dockerlab-01   Exited (0) 3 seconds ago

$ docker logs dockerlab-01
starting the api
api started

three seconds after docker run, the container is exited (exit code 0).
```

Exit code 0 means nothing crashed. The script did exactly what it says. Notice that the server never even printed its first line: the container was gone before Python finished starting.

## Reasoning towards the fix

Walk through what happens:

1. Docker starts `sh start.sh` as PID 1.
2. `python server.py &` starts the server as a child process, in the background, and returns at once.
3. The shell prints "api started" and reaches the end of the script.
4. PID 1 exits with code 0, so the container stops, and the kernel kills the child server with it.

The container is behaving correctly. It is the start script that is wrong for a container. On a server with a process supervisor, a background `&` is how you start a daemon. In a container, Docker is the supervisor, and it supervises exactly one process.

Fix `start.sh` so the server runs in the foreground and the script only ends when the server does. Then check:

```bash
uv run python -m dock check 1
```

## Check your fix

The checker builds your image, runs it, waits three seconds, calls the API, then makes the server die on purpose with `POST /debug/exit`. As shipped:

```text
  FAIL  the container is still running 3 s after docker run
  FAIL  the API answers on the published port
  FAIL  when the server dies, the container stops with it (exit code -)
```

The last check matters. A common wrong fix keeps the container alive with `tail -f /dev/null` after starting the server in the background. The container then stays **Up** even after the server crashes, so nothing ever restarts it, and every request fails while Docker reports that all is well. The container's life must be the server's life.

## In production

- Orchestrators (Docker's restart policies, Compose, Kubernetes) restart a container when its main process exits. That only works if the main process is the thing that can fail.
- Log to stdout and stderr, not to files. `docker logs` and every log collector read the main process's output streams.
- One concern per container. If you need a web server and a worker, run two containers from the same image with different commands, not two processes in one.
- Chapter 09 returns to PID 1: it has special signal rules, and a shell between Docker and your server causes slow, unclean shutdowns.

## Key points

- An image is files plus settings. A container is a process started from it, with namespaces, cgroups and a layered filesystem around it.
- The container lives exactly as long as PID 1. When it exits, the container stops with its exit code.
- Never background your server in a container's start command. Run it in the foreground.
- Keeping a container alive with `tail -f` hides crashes from the thing that would restart it.
