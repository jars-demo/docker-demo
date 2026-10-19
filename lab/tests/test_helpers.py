"""The lab's own helpers and layout. These run without Docker."""

import importlib

import pytest

from dock import docker as d

LOG = """\
#5 [1/4] FROM docker.io/library/python:3.13.16-slim-trixie@sha256:70729b46
#5 DONE 0.0s
#6 [2/4] WORKDIR /app
#6 CACHED
#7 [3/4] COPY . .
#7 DONE 0.1s
#8 [4/4] RUN pip install --no-cache-dir -r requirements.txt
#8 DONE 6.2s
"""


def test_parse_steps_reads_cached_and_timed_steps() -> None:
    steps = d.parse_steps(LOG)

    assert [(s.name[:12], s.cached, s.seconds) for s in steps.values()] == [
        ("FROM docker.", False, 0.0),
        ("WORKDIR /app", True, 0.0),
        ("COPY . .", False, 0.1),
        ("RUN pip inst", False, 6.2),
    ]


def test_build_step_finds_a_step_by_its_instruction() -> None:
    build = d.Build(True, 6.3, LOG, d.parse_steps(LOG))

    assert build.step("pip install").seconds == 6.2


def test_mb_prints_sizes_the_way_docker_does() -> None:
    assert (d.mb(118_317_450), d.mb(4_096)) == ("118.3 MB", "4.1 kB")


@pytest.mark.parametrize("number", range(1, 13))
def test_every_exercise_has_a_title_three_hints_and_a_solution(number: int) -> None:
    module = importlib.import_module(f"dock.ex{number:02d}")
    folder = d.exercise_dir(number)

    assert module.TITLE and len(module.HINTS) == 3
    assert any((d.SOLUTIONS / folder.name).iterdir())


@pytest.mark.parametrize("number", range(1, 13))
def test_every_solution_file_replaces_or_adds_to_its_exercise(number: int) -> None:
    folder = d.exercise_dir(number)
    solution = d.SOLUTIONS / folder.name

    changed = [
        path.relative_to(solution)
        for path in solution.rglob("*")
        if path.is_file()
        and (
            not (folder / path.relative_to(solution)).exists()
            or (folder / path.relative_to(solution)).read_bytes() != path.read_bytes()
        )
    ]

    assert changed, f"solution {folder.name} changes nothing"
