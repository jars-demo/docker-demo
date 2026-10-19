# Ports and networks

> Inside a container, 127.0.0.1 is the container's own loopback. A server that listens there is working perfectly and can never be reached from outside.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain what a published port does, why a server in a container must listen on 0.0.0.0, and how containers find each other by name.

## The idea

### Every container has its own network stack

The network namespace gives each container its own interfaces, routing table and ports. A container typically has two interfaces:

- `lo`, the loopback, at 127.0.0.1. Only processes in that same container can reach it.
- `eth0`, a virtual interface on a Docker network, at an address like 172.18.0.2.

When your laptop's browser talks to `localhost`, that is your laptop's loopback. When a process in a container talks to `localhost`, that is the container's loopback. They are different places.

### Publishing a port

`docker run -p 127.0.0.1:8080:8000` tells Docker: accept connections on the host at 127.0.0.1:8080 and forward them to port 8000 on the container's `eth0` address. The traffic arrives on `eth0`, not on `lo`. A server listening only on 127.0.0.1 never sees it.

Two details worth knowing:

- `-p 8080:8000` without an address listens on **every** host interface, so anyone on your network (or the internet, on a server) can connect. Bind to 127.0.0.1 unless you mean it.
- `EXPOSE 8000` in a Dockerfile publishes nothing. It is documentation, and a default for `-P`.

### Container to container

Containers on the same **user-defined** network can reach each other directly, without publishing anything, and Docker runs a DNS server that resolves container names and aliases. Compose creates one such network per project, which is why `db` works as a hostname there. The default `bridge` network has no DNS. `uv run python -m dock try network` shows both:

```text
  on the default bridge network: dockerlab-try-server resolves to socket.gaierror: [Errno -2] Name or service not known
  on a user-defined network: dockerlab-try-server resolves to 172.25.0.2
```

## The exercise

Open `lab/exercises/04-ports-and-networks/`. The server reads its listen address from `HOST`, with a default that is very common in development:

```python
HOST = os.environ.get("HOST", "127.0.0.1")
```

```bash
uv run python -m dock run 4
```

```text
$ docker logs dockerlab-04
api listening on http://127.0.0.1:8000

from your machine, http://127.0.0.1:56870/healthz:
  RemoteDisconnected: Remote end closed connection without response

from inside the container, http://127.0.0.1:8000/healthz:
  {"status": "ok", "hostname": "73eb466fa74b"}

The server works. It only listens where nothing from outside can reach it.
```

From inside, the API answers. From outside, Docker accepts the connection on the host, tries to forward it to the container's `eth0`, finds nothing listening there, and the connection closes without a response. The host port changes on every run because the lab lets Docker pick a free one.

## Reasoning towards the fix

The server is listening on the wrong interface. It needs to accept connections on `eth0` too, and the simplest correct way is to listen on all interfaces: `0.0.0.0`. That is safe inside a container, because the container's network namespace is already isolated. What the outside world can reach is decided by `-p`, on the host.

Set `HOST=0.0.0.0` in the Dockerfile with `ENV`, so the image is correct however it is started.

## Check your fix

```bash
uv run python -m dock check 4
```

As shipped:

```text
  FAIL  the API answers on the published port
  FAIL  another container on the same network reaches it at http://api:8000
```

The checker creates a user-defined network, starts your API on it with the alias `api`, and starts a second container on the same network to call `http://api:8000/healthz`, exactly as another service in Compose would. Setting `HOST=localhost` fails both checks, because `localhost` is still the loopback.

## In production

- Behind Kubernetes, a load balancer or a service mesh, traffic always arrives on the pod's interface. The same rule applies: listen on 0.0.0.0 (or `::` for IPv6) inside the container.
- Publish ports only for traffic that comes from outside. Services that only talk to each other need a shared network, not published ports.
- Bind published ports to 127.0.0.1 on developer machines and anything that should be private. On Linux, Docker writes its own firewall rules, and `-p 8080:8000` can open a port that your host firewall seems to block.
- Use service names, not IP addresses. Container addresses change on every restart.

## Key points

- Each container has its own loopback. 127.0.0.1 inside is not 127.0.0.1 on the host.
- Published ports forward to the container's network interface, so the server must listen on 0.0.0.0.
- `EXPOSE` publishes nothing.
- Containers on a user-defined network reach each other by name, through Docker's DNS.
