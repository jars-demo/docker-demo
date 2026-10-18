# Container networking

> Every container has its own localhost. An app that listens there answers no one but itself.

**Time:** 15 minutes

## Goal

Know what a network namespace gives a container, how a published port reaches it, how containers find each other by name, and which address a server must listen on.

## The case

```bash
uv run python -m dock run 6
```

```text
orders log:   Running on http://127.0.0.1:8080
laptop  -> curl http://localhost:8080/menu  connection reset by peer
worker  -> GET  http://orders:8080/menu     connection refused
orders  -> curl http://localhost:8080/menu  connected
the app is up and answering, but only to itself
```

The orders container is running, its log says it is listening, and port 8080 is published. From the laptop, curl gets a reset. From the worker container, the connection is refused. From inside the orders container itself, it works. Open `lab/cases/case06_localhost.py` and read `ORDERS_CMD`.

## One namespace per container

A **network namespace** is a private copy of the network stack: its own interfaces, addresses, routes and ports. Each container gets one. Inside it are two interfaces:

- **`lo`**, the loopback, with `127.0.0.1`. It is the container's own, not the host's, and not any other container's.
- **`eth0`**, one end of a virtual cable to a bridge on the host, with an address such as `172.18.0.3`.

So `localhost` means a different place in every container. Inside the orders container, `127.0.0.1:8080` reaches the orders app. Inside the worker, `127.0.0.1:8080` reaches nothing, because nothing in the worker listens there.

This is also why a container cannot reach a database on your laptop at `localhost:5432`. That address is the container's own loopback. On Docker Desktop, `host.docker.internal` names the host. On Linux you can add it with `--add-host=host.docker.internal:host-gateway`.

## Where a published port arrives

`ports: ["8080:8080"]` (or `-p 8080:8080`) tells Docker to forward port 8080 on the host to port 8080 of the container. The traffic arrives on the container's **`eth0` address**, not on its loopback. It has to: the loopback is not reachable from outside the namespace by design.

A server bound to `127.0.0.1` only accepts connections that arrive on the loopback. Traffic on `eth0` finds no listener. Depending on the path, the client sees "connection refused", or a reset when Docker's proxy accepted the connection and then could not pass it on.

Prove it with real sockets on your machine:

```bash
uv run python -m dock try ports
```

```text
Python 3.13.16, Linux, 4 CPUs
loopback 127.0.0.1, and this machine's own address: 192.0.2.2

  server bound to   client connects to    result            time
  127.0.0.1         127.0.0.1             accepted        132 µs
  127.0.0.1         192.0.2.2             refused          24 µs
  0.0.0.0           127.0.0.1             accepted        142 µs
  0.0.0.0           192.0.2.2             accepted        139 µs
```

`0.0.0.0` means "every interface". Inside a container that is what a server must listen on, or on its `eth0` address, if you know it. Many development servers default to the loopback for safety on a laptop: `flask run`, Django's `runserver` and Vite all do, and each has a flag to change it.

One more trap: `localhost` can resolve to `::1`, the IPv6 loopback. A client that tries `::1` first and a server bound to `127.0.0.1` only can miss each other even on the same machine.

## Finding each other by name

Compose puts all the services of a project on one network and runs a small DNS server inside each container. Every service name resolves to that service's `eth0` address, so the worker reaches orders at `http://orders:8080`. Containers on the same network can reach each other on any port the app listens on. Publishing a port is only needed for traffic from outside, such as your browser.

`EXPOSE` in a Dockerfile publishes nothing. It is documentation.

## Publishing safely

By default `-p 8080:8080` listens on every interface of the **host**. On a laptop in a café, that is everyone on the café's Wi-Fi. On Linux, Docker adds its own firewall rules, which run before tools such as ufw, so a port you thought you had blocked can be open. To publish for yourself only, bind the host side to the loopback: `127.0.0.1:8080:8080`.

And publish only what must be reached from outside. The database in this case is not published at all, and the check makes sure it stays that way.

## Host networking

`network_mode: host` skips the namespace and puts the container on the host's network stack. `127.0.0.1` then means the host, and the case's symptom disappears. It also removes the isolation, gives up name lookup between services, and works differently on Docker Desktop, where the "host" is a virtual machine. It is a tool for special cases, not a fix for a bind address.

## Fix the case

Make the orders app listen where published ports and other containers arrive. Keep the container on its own network, and keep the database private.

## Check it works

```bash
uv run python -m dock check 6
```

```text
  PASS  from the laptop, curl localhost:8080/menu works (connected)
  PASS  the worker reaches http://orders:8080 (connected)
  PASS  orders keeps its own network namespace (no network_mode: host)
  PASS  the database stays private: the laptop cannot reach port 5432
```

## Exercise

A teammate runs the orders app on their laptop, outside Docker, and the database in a container with `ports: ["5432:5432"]`. The app connects to `localhost:5432`, and it works. Then they move the app into compose and it fails. Explain why, and say what `DATABASE_HOST` should be in each setup.

### More to try

- Put `"network_mode": "host"` on orders and run the check. Which line still fails, and why can the worker no longer find orders by name?
- On a Linux machine with Docker, run `docker run --rm -p 8080:80 nginx` and look at `ss -ltnp` on the host. Which address is Docker listening on?
