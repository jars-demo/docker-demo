"""Case 06: listening, and unreachable.

On a laptop, `flask run` serves the menu at localhost:8080. In compose, the orders container
starts, logs that it is listening on port 8080, and the port is published. Yet curl from the
laptop gets a reset, and the packing worker gets connection refused.
Run it: uv run python -m dock run 6
"""

# The command the orders image runs. flask run listens on 127.0.0.1 unless told otherwise.
ORDERS_CMD = ["flask", "run", "--host", "0.0.0.0", "--port", "8080"]

COMPOSE = {
    "orders": {"command": ORDERS_CMD, "ports": ["8080:8080"]},
    "worker": {"environment": {"ORDERS_URL": "http://orders:8080"}},
    "db": {"command": ["postgres", "-c", "listen_addresses=*"]},
}

HOST_IP = "192.168.1.20"
LISTENS = {"db": 5432}


class Network:
    """One laptop and a compose network. Each container has its own network namespace: its
    own loopback (127.0.0.1) and one interface on the bridge. Names resolve through Docker's
    DNS to bridge addresses. A published port forwards from the laptop to the container's
    bridge address, never to its loopback."""

    def __init__(self, compose: dict) -> None:
        self.compose = compose
        self.ips: dict[str, str] = {"laptop": HOST_IP}
        self.listening: dict[str, list[tuple[str, int]]] = {"laptop": []}
        for n, (name, service) in enumerate(compose.items(), start=2):
            on_host = service.get("network_mode") == "host"
            self.ips[name] = HOST_IP if on_host else f"172.18.0.{n}"
            space = "laptop" if on_host else name
            self.listening.setdefault(space, [])
            command = service.get("command", [])
            if command[:2] == ["flask", "run"]:
                self.listening[space].append((self.bind(command), self.port(command)))
            elif name in LISTENS:
                self.listening[space].append(("0.0.0.0", LISTENS[name]))

    @staticmethod
    def option(command: list[str], name: str, default: str) -> str:
        for i, word in enumerate(command):
            if word == name and i + 1 < len(command):
                return command[i + 1]
            if word.startswith(name + "="):
                return word.split("=", 1)[1]
        return default

    def bind(self, command: list[str]) -> str:
        return self.option(command, "--host", "127.0.0.1")

    def port(self, command: list[str]) -> int:
        return int(self.option(command, "--port", "5000"))

    def space(self, name: str) -> str:
        return "laptop" if self.ips[name] == HOST_IP else name

    def accepts(self, space: str, ip: str, port: int) -> bool:
        """Does anything in this namespace listen on ip:port? 0.0.0.0 means every interface."""
        return any(p == port and addr in ("0.0.0.0", ip) for addr, p in self.listening[space])

    def published(self) -> dict[int, tuple[str, int]]:
        out = {}
        for name, service in self.compose.items():
            for mapping in service.get("ports", []):
                *_, outside, inside = mapping.split(":")
                out[int(outside)] = (name, int(inside))
        return out

    def connect(self, source: str, host: str, port: int) -> str:
        """What a client in `source` sees when it opens host:port."""
        here = self.space(source)
        if host in ("localhost", "127.0.0.1"):
            if self.accepts(here, "127.0.0.1", port):
                return "connected"
            if here == "laptop" and port in self.published():
                # docker-proxy takes the connection, then cannot reach the container's app
                name, inside = self.published()[port]
                if self.accepts(self.space(name), self.ips[name], inside):
                    return "connected"
                return "connection reset by peer"
            return "connection refused"
        if host not in self.ips or (self.space(host) == "laptop" and here != "laptop"):
            return f"could not resolve host {host}"  # host-network services leave Docker's DNS
        target = self.space(host)
        return "connected" if self.accepts(target, self.ips[host], port) else "connection refused"


def up() -> Network:
    return Network(COMPOSE)


def run() -> None:
    net = up()
    for address, port in net.listening[net.space("orders")]:
        print(f"orders log:   Running on http://{address}:{port}")
    for source, host, verb in [
        ("laptop", "localhost", "curl"),
        ("worker", "orders", "GET "),
        ("orders", "localhost", "curl"),
    ]:
        url = f"http://{host}:8080/menu"
        print(f"{source:<7} -> {verb} {url:<27} {net.connect(source, host, 8080)}")
    print("the app is up and answering, but only to itself")
