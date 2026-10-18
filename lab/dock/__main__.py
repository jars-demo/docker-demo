"""dock: nine container bugs in one small tea shop.

list        every case, and which ones are fixed
run N       run case N and watch the bug happen
check N     check your fix: the bug is gone and the job still gets done
hint N      a nudge from Pip
try NAME    run an experiment: context, digest, ports or stop
"""

import argparse
import importlib
import sys

from dock.checks import CHECKS
from dock.experiments import EXPERIMENTS

CASES = {
    1: ("case01_cache_order", "The rebuild that reinstalled everything"),
    2: ("case02_secret_layer", "The token in layer three"),
    3: ("case03_multistage", "The image that shrank too far"),
    4: ("case04_tags", "The rollback that rolled forward"),
    5: ("case05_pid_one", "The ten-second goodbye"),
    6: ("case06_localhost", "Listening, and unreachable"),
    7: ("case07_healthcheck", "Started is not ready"),
    8: ("case08_volume", "The orders that vanished on redeploy"),
    9: ("case09_cpu_limits", "Sixty-five workers in a two-CPU box"),
}

HINTS = {
    1: [
        "Look at which step is the first to say RAN. Everything after it runs too.",
        "COPY . . changes whenever any file changes. What does pip install actually read?",
        "Copy requirements.txt on its own, install, and only then COPY . . for the rest.",
    ],
    2: [
        "RUN rm adds a new layer that hides the file. Does it change the layer below?",
        "The safest secret in an image is one that was never sent to the builder.",
        "Add .env to .dockerignore. The app still gets the token from env_file at run time.",
    ],
    3: [
        "Read the error. Which file is missing, and which package puts it there?",
        "libpq-dev is for building against libpq. What does running against it need?",
        "Install libpq5 in the runtime stage. Clean the apt lists in the same RUN line.",
    ],
    4: [
        "Print cluster.history. What does a release remember about what it ran?",
        "A tag is a name that moves. A digest is the image itself.",
        "In record, resolve the tag once and keep name@digest: registry.resolve(ref).",
    ],
    5: [
        "Who is PID 1 in this container? Does it have a SIGTERM handler?",
        "The shell starts the worker as a child and waits. It never passes the signal on.",
        "Make the last line of start.sh replace the shell: exec python worker.py.",
    ],
    6: [
        "The log says Running on http://127.0.0.1:8080. Whose 127.0.0.1 is that?",
        "A published port forwards to the container's bridge address, not its loopback.",
        "Tell flask to listen on every interface: --host 0.0.0.0.",
    ],
    7: [
        "service_started means the container started. Is that what orders needs?",
        "Give db a healthcheck that asks Postgres itself, and wait for it to pass.",
        "healthcheck test pg_isready, interval 1 s; depends_on condition: service_healthy.",
    ],
    8: [
        "Read the startup warning. Who owns /data, and who is the app running as?",
        "A new named volume copies the owner of the folder from the image.",
        "Before USER, give the folder to the app user: chown tidepool:tidepool /data.",
    ],
    9: [
        "What does os.cpu_count() count inside a container with --cpus 2?",
        "A CPU limit is a quota. Read it from /sys/fs/cgroup/cpu.max.",
        "CPUs = ceil(quota / period), or the host count when the quota is max.",
    ],
}


def say(text: str) -> None:
    print("    \\/  \\/")
    print(f"    (o)(o)    {text}")
    print("   /(____)\\", flush=True)


def module(number: int):
    name = f"cases.{CASES[number][0]}"
    sys.modules.pop(name, None)  # always the code as it is on disk now
    return importlib.import_module(name)


def fixed(number: int) -> bool:
    return all(ok for _, ok in CHECKS[number](module(number)))


def cmd_list(args: argparse.Namespace) -> None:
    for number, (_, title) in CASES.items():
        print(f"  {number}  {title:<38} {'fixed' if fixed(number) else ''}", flush=True)


def cmd_run(args: argparse.Namespace) -> None:
    say(f"Case {args.n}: {CASES[args.n][1]}.")
    print()
    module(args.n).run()


def cmd_check(args: argparse.Namespace) -> None:
    results = CHECKS[args.n](module(args.n))
    for label, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    print()
    if all(ok for _, ok in results):
        say(f"Case {args.n} fixed. Ship it.")
    else:
        say(f"Not yet. Try: uv run python -m dock hint {args.n}")
        sys.exit(1)


def cmd_hint(args: argparse.Namespace) -> None:
    say("Here is where I would look:")
    for hint in HINTS[args.n]:
        print(f"  - {hint}")


def cmd_try(args: argparse.Namespace) -> None:
    EXPERIMENTS[args.name]()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # the same output on every terminal
    parser = argparse.ArgumentParser(prog="dock", description="Nine container bugs.")
    sub = parser.add_subparsers(required=True)
    sub.add_parser("list", help="every case and which are fixed").set_defaults(func=cmd_list)
    for name, func, text in [
        ("run", cmd_run, "run case N and watch the bug"),
        ("check", cmd_check, "check your fix"),
        ("hint", cmd_hint, "a nudge from Pip"),
    ]:
        p = sub.add_parser(name, help=text)
        p.add_argument("n", type=int, choices=CASES, metavar="N")
        p.set_defaults(func=func)
    p = sub.add_parser("try", help="run an experiment: " + ", ".join(EXPERIMENTS))
    p.add_argument("name", choices=EXPERIMENTS)
    p.set_defaults(func=cmd_try)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
