"""Every exercise fails as it ships and passes with its solution, on real Docker."""

import importlib

import pytest

from tests.conftest import needs_docker

pytestmark = needs_docker


@pytest.mark.parametrize("number", range(1, 13))
def test_exercise_fails_as_shipped(exercise, number: int) -> None:
    results = importlib.import_module(f"dock.ex{number:02d}").check(exercise(number))

    assert not all(ok for _, ok in results), results


@pytest.mark.parametrize("number", range(1, 13))
def test_exercise_passes_with_its_solution(exercise, number: int) -> None:
    results = importlib.import_module(f"dock.ex{number:02d}").check(exercise(number, solved=True))

    assert all(ok for _, ok in results), results
