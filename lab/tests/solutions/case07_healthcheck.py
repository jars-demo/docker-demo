"""Case 07: started is not ready.

Compose starts the database first, because orders says depends_on: db. Orders boots, connects to
the database, and is refused: Postgres is running but still setting itself up. Orders exits with
code 1 and stays down. Twenty customers try to order and none of them can.
Run it: uv run python -m dock run 7
"""

COMPOSE = {
    "db": {
        "image": "postgres:17",
        "healthcheck": {
            "test": ["CMD", "pg_isready", "-U", "tidepool"],
            "interval": 1.0,
            "retries": 10,
        },
    },
    "orders": {
        "depends_on": {"db": {"condition": "service_healthy"}},
        "restart": "no",
    },
}

# How the orders app connects at boot: how many tries, and how long it waits between them.
CONNECT_ATTEMPTS = 1
CONNECT_WAIT = 1.0

DB_PROCESS_UP = 0.3  # the postgres process exists from here (pgrep finds it)
DB_READY = 6.8  # it accepts connections from here (pg_isready says yes)
ORDERS_BOOT = 0.4  # orders imports and reads config before its first connect
ORDERS_WARMUP = 0.5  # from connected to serving
CUSTOMERS = [10.0 + n for n in range(20)]  # one order a second, from t=10 s


class Compose:
    """docker compose up, on a pretend clock, for the two services above."""

    def __init__(self, compose: dict, attempts: int, wait: float) -> None:
        self.compose = compose
        self.attempts = attempts
        self.wait = wait
        self.log: list[tuple[float, str]] = []
        self.restarts = 0
        self.ready_at: float | None = None
        self.down_at: float | None = None

    def say(self, when: float, who: str, text: str) -> None:
        self.log.append((round(when, 1), f"{who:<7} {text}"))

    def probe(self, test: list[str], when: float) -> bool:
        """Run a healthcheck command inside the db container at time `when`."""
        command = " ".join(test[1:]) if test and test[0] in ("CMD", "CMD-SHELL") else ""
        if "pg_isready" in command:
            return when >= DB_READY
        if "pgrep" in command or "ps " in command:
            return when >= DB_PROCESS_UP
        raise ValueError(f"healthcheck {test}: this pretend db only knows pg_isready and pgrep")

    def healthy_at(self) -> float | None:
        check = self.compose["db"].get("healthcheck")
        if not check:
            return None
        interval = float(check.get("interval", 30.0))
        retries = int(check.get("retries", 3))
        start_period = float(check.get("start_period", 0.0))
        when, failures = interval, 0
        while when < 600:
            if self.probe(check["test"], when):
                return when
            if when >= start_period:
                failures += 1
                if failures >= retries:
                    self.say(when, "db", f"unhealthy after {retries} failed checks")
                    return None
            when += interval
        return None

    def up(self) -> "Compose":
        self.say(0.0, "db", "container started")
        self.say(DB_PROCESS_UP, "db", "postgres process running, initialising the database")
        self.say(DB_READY, "db", "database system is ready to accept connections")
        condition = self.compose["orders"]["depends_on"]["db"]["condition"]
        start = 0.0
        if condition == "service_healthy":
            healthy = self.healthy_at()
            if healthy is None:
                self.say(0.0, "orders", "not started: db has no healthcheck, or failed it")
                return self
            self.say(healthy, "db", "healthcheck passed: healthy")
            start = healthy
        delay = 0.1  # Docker's restart delay starts at 100 ms and doubles
        while True:
            self.say(start, "orders", "container started")
            if self.boot(start + ORDERS_BOOT):
                return self
            policy = self.compose["orders"].get("restart", "no")
            if policy not in ("always", "on-failure", "unless-stopped") or self.restarts >= 50:
                return self
            self.restarts += 1
            start = self.down_at + delay
            delay = min(delay * 2, 60.0)

    def boot(self, when: float) -> bool:
        for attempt in range(self.attempts):
            if when >= DB_READY:
                self.say(when, "orders", "connected to db:5432")
                self.ready_at = when + ORDERS_WARMUP
                self.say(self.ready_at, "orders", "serving on :8080")
                return True
            self.say(when, "orders", "connect db:5432: connection refused")
            if attempt + 1 < self.attempts:
                when += self.wait
        self.down_at = when
        self.say(when, "orders", "exited with code 1")
        return False

    def served(self) -> int:
        return sum(1 for t in CUSTOMERS if self.ready_at is not None and t >= self.ready_at)


def morning(compose: dict | None = None) -> Compose:
    return Compose(compose or COMPOSE, CONNECT_ATTEMPTS, CONNECT_WAIT).up()


def run() -> None:
    stack = morning()
    for when, text in sorted(stack.log, key=lambda item: item[0]):
        print(f"  t={when:5.1f}s  {text}")
    print(f"orders served: {stack.served()} of {len(CUSTOMERS)}")
