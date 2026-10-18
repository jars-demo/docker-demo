"""The chapters quote the lab exactly. Every case is deterministic, so the output a chapter shows
for `dock run N`, and the PASS lines it shows after the fix, must be what the lab prints now."""

import contextlib
import importlib
import io
from pathlib import Path

import pytest

from dock.__main__ import CASES
from dock.checks import CHECKS

WORKSHOP = Path(__file__).parent.parent.parent / "workshop"


def chapter(number: int) -> str:
    (path,) = WORKSHOP.glob(f"{number:02d}-*.md")
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("number", list(CASES))
def test_chapter_shows_the_run_output(number):
    case = importlib.import_module(f"cases.{CASES[number][0]}")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        case.run()

    assert f"```text\n{out.getvalue()}```" in chapter(number)


@pytest.mark.parametrize("number", list(CASES))
def test_chapter_shows_the_check_passing(number):
    fixed = importlib.import_module(f"tests.solutions.{CASES[number][0]}")
    lines = "".join(f"  PASS  {label}\n" for label, _ in CHECKS[number](fixed))

    assert f"```text\n{lines}```" in chapter(number)
