"""Case 05: the ten-second goodbye.

The packing worker takes paid orders off a queue and packs them. It handles SIGTERM properly:
finish the order in hand, then exit. Yet every deploy, `docker stop` hangs for ten seconds, then
kills it, and an order that was paid for is left half packed.
Run it: uv run python -m dock run 5
"""

import shlex
from dataclasses import dataclass, field

# The image runs this script as its entrypoint: CMD ["/start.sh"].
CMD = ["/start.sh"]

START_SH = """\
#!/bin/sh
set -e
python migrate.py
exec python worker.py
"""

GRACE = 10.0  # docker stop waits this long after SIGTERM, then sends SIGKILL
PACK_SECONDS = 3.0
MIGRATE_SECONDS = 2.0
STOP_AT = 9.5  # when the deploy calls docker stop, seconds after the container started


@dataclass
class Process:
    """A process in the container's own PID namespace, as the kernel sees it."""

    pid: int
    command: str
    handles: set[str] = field(default_factory=set)  # signals it has a handler for
    alive: bool = True
    exit_code: int | None = None


class Container:
    """A container with a pretend kernel and a pretend clock.

    The kernel rule that matters: a signal whose action is the default is NOT delivered to
    PID 1. A normal process dies on SIGTERM by default. PID 1 only reacts if it set a handler.
    SIGKILL cannot be handled or ignored, and when PID 1 dies, every process in it dies too."""

    def __init__(self, cmd: list[str], script: str) -> None:
        self.clock = 0.0
        self.log: list[tuple[float, str]] = []
        self.processes: dict[int, Process] = {}
        self.next_pid = 1
        self.worker: Process | None = None
        self.packing: tuple[int, float] | None = None  # (order, when it started)
        self.next_order = 1043
        self.packed: list[int] = []
        self.cut_off: list[int] = []
        self.stopping = False
        self.migrated_before_worker = False
        self.migrated = False
        self.launch(cmd, script)

    def say(self, text: str) -> None:
        self.log.append((round(self.clock, 1), text))

    def spawn(self, command: str) -> Process:
        process = Process(self.next_pid, command)
        self.processes[process.pid] = process
        self.next_pid += 1
        return process

    def launch(self, cmd: list[str], script: str) -> None:
        if cmd[:2] == ["sh", "-c"] or cmd[:2] == ["/bin/sh", "-c"]:
            lines = [part.strip() for part in cmd[2].split("&&")]
        elif cmd[0] == "/start.sh":
            lines = [line.strip() for line in script.splitlines()]
        else:
            lines = ["exec " + shlex.join(cmd)]
        shell = self.spawn("/bin/sh /start.sh" if cmd[0] == "/start.sh" else shlex.join(cmd))
        if not lines[0].startswith("exec "):
            self.say(f"PID {shell.pid}  {shell.command}")
        for line in lines:
            if not line or line.startswith("#") or line.startswith("set "):
                continue
            replace = line.startswith("exec ")
            command = line.removeprefix("exec ").strip()
            if replace:  # exec: the shell becomes the program, keeping its PID
                shell.command = command
                self.start(shell)
                break  # the shell is gone, so the rest of the script never runs
            self.start(self.spawn(command))  # no exec: the shell starts a child and waits

    def start(self, process: Process) -> None:
        self.say(f"PID {process.pid}  {process.command}")
        if process.command == "python migrate.py":
            self.clock += MIGRATE_SECONDS
            self.migrated = True
            self.end(process, 0)
        elif process.command == "python worker.py":
            process.handles.add("SIGTERM")
            self.worker = process
            self.migrated_before_worker = self.migrated
            self.take_order()
        else:
            raise RuntimeError(f"{process.command}: not found")

    def end(self, process: Process, code: int) -> None:
        process.alive = False
        process.exit_code = code

    def take_order(self) -> None:
        self.packing = (self.next_order, self.clock)
        self.next_order += 1

    def tick(self, seconds: float) -> None:
        """Let the worker pack orders for a while."""
        end = self.clock + seconds
        while self.packing and self.worker and self.worker.alive:
            order, began = self.packing
            done = began + PACK_SECONDS
            if done > end:
                break
            self.clock = done
            self.packed.append(order)
            self.say(f"packed order {order}")
            if self.stopping:
                self.packing = None
                self.end(self.worker, 0)
                self.say("worker: SIGTERM handled, last order packed, exit 0")
            else:
                self.take_order()
        self.clock = max(self.clock, end)

    def signal(self, pid: int, sig: str) -> None:
        process = self.processes[pid]
        if sig == "SIGKILL":
            for other in self.processes.values():
                if other.alive:
                    self.end(other, 137)
            if self.packing:
                self.cut_off.append(self.packing[0])
                self.say(f"order {self.packing[0]} cut off mid-pack: paid for, never packed")
                self.packing = None
            return
        if sig in process.handles:
            self.say(f"PID {pid} ({process.command}) caught {sig}")
            if process is self.worker:
                self.stopping = True
        elif pid == 1:
            self.say(f"PID 1 ({process.command}) has no {sig} handler, so the kernel drops it")
        else:
            self.end(process, 143)

    def main(self) -> Process:
        return self.processes[1]

    def stop(self, grace: float = GRACE) -> float:
        """docker stop: SIGTERM to PID 1, wait up to `grace`, then SIGKILL everything."""
        began = self.clock
        self.say("docker stop: SIGTERM to PID 1")
        self.signal(1, "SIGTERM")
        while self.main().alive and (self.worker is None or self.worker.alive):
            if self.clock - began >= grace:
                self.say(f"still running after {grace:.0f} s: SIGKILL")
                self.signal(1, "SIGKILL")
                break
            self.tick(min(0.5, grace - (self.clock - began)))
        if self.main().alive:  # the worker exited; a waiting shell exits with it
            self.end(self.main(), self.worker.exit_code if self.worker else 0)
        return self.clock - began


def deploy(cmd: list[str] | None = None, script: str | None = None):
    container = Container(cmd or CMD, START_SH if script is None else script)
    container.tick(STOP_AT - container.clock)
    took = container.stop()
    return container, took


def run() -> None:
    container, took = deploy()
    for when, text in container.log:
        print(f"  t={when:5.1f}s  {text}")
    print(f"docker stop took {took:.1f} s; exit code {container.main().exit_code}")
    print(f"orders packed: {container.packed}; cut off: {container.cut_off}")
