"""dock: twelve Docker exercises, from a first container to a production release.

list        every exercise and its folder
run N       build and run exercise N as it ships, and show what goes wrong
check N     check your fix with real builds and containers
hint N      a nudge, one step at a time
try NAME    run an experiment: startup, layers, sizes or network
clean       remove every container, image, volume and network the lab created
"""

import argparse
import importlib
import sys
from types import ModuleType

from dock import docker as d
from dock.experiments import EXPERIMENTS

COUNT = 12
LEVELS = {1: "Foundations", 5: "Services and data", 8: "Production"}


def exercise(number: int) -> ModuleType:
    if not 1 <= number <= COUNT:
        raise SystemExit(f"there is no exercise {number}: pick 1 to {COUNT}")
    return importlib.import_module(f"dock.ex{number:02d}")


def need_docker() -> None:
    problem = d.available()
    if problem:
        raise SystemExit(f"Docker is not ready: {problem}.")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    parser = argparse.ArgumentParser(prog="dock", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    for name in ("run", "check", "hint"):
        sub.add_parser(name).add_argument("number", type=int)
    sub.add_parser("try").add_argument("name", choices=sorted(EXPERIMENTS))
    sub.add_parser("clean")
    args = parser.parse_args()

    if args.command == "list":
        for number in range(1, COUNT + 1):
            if number in LEVELS:
                print(f"\n{LEVELS[number]}")
            module = exercise(number)
            print(f"  {number:2d}  {module.TITLE:<44} exercises/{d.exercise_dir(number).name}")
        return

    if args.command == "hint":
        print()
        for step, hint in enumerate(exercise(args.number).HINTS, 1):
            print(f"  {step}. {hint}")
        print()
        return

    need_docker()
    if args.command == "clean":
        removed = d.clean()
        print("\n".join(removed) if removed else "nothing to clean")
    elif args.command == "try":
        EXPERIMENTS[args.name]()
    elif args.command == "run":
        module = exercise(args.number)
        print(f"exercise {args.number:02d}: {module.TITLE}\n")
        module.run(d.exercise_dir(args.number))
    elif args.command == "check":
        module = exercise(args.number)
        print(f"checking exercise {args.number:02d}: {module.TITLE}\n")
        results = module.check(d.exercise_dir(args.number))
        for label, ok in results:
            print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print()
        if all(ok for _, ok in results):
            print("fixed. On to the next one.")
        else:
            print(f"not yet. Try: uv run python -m dock hint {args.number}")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
