import shutil
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from pathlib import Path

import pytest

from dock import docker as d

needs_docker = pytest.mark.skipif(d.available() is not None, reason="Docker is not running")


@pytest.fixture
def exercise() -> Iterator[Callable[..., Path]]:
    """A throwaway copy of exercise N, with its solution and any given files written over it."""
    with ExitStack() as stack:

        def make(number: int, solved: bool = False, files: dict[str, str] | None = None) -> Path:
            source = d.exercise_dir(number)
            path = stack.enter_context(d.workcopy(source))
            if solved:
                shutil.copytree(d.SOLUTIONS / source.name, path, dirs_exist_ok=True)
            for name, text in (files or {}).items():
                (path / name).write_text(text)
            return path

        yield make
