# AGENTS.md

Guidance for AI coding agents and developers. Humans: start with [README.md](README.md).

## What this is

"Docker without the magic": nine chapters, each a container idea explained in depth and a real bug
in the orders service of a small tea shop that shows it. `lab/` holds the cases and the checker;
`workshop/` the chapters; `frontend/` the site.

## Map

```text
lab/cases/caseNN_*.py       one deliberate container bug each; run() shows the symptom
lab/dock/engine.py          a pretend builder: layers, whiteouts, build cache, stages, apt, pip
lab/dock/checks.py          check_NN(module) -> [(label, ok)]; tests the job as well as the bug
lab/dock/experiments.py     `dock try context | digest | ports | stop`, all measured live
lab/dock/__main__.py        CLI: list, run, check, hint, try; case titles and hints live here
lab/tests/                  cases fail as shipped, pass with solutions/, reject wrong fixes,
                            and match the output quoted in the chapters
frontend/src/lib/site.ts    cases and measured numbers: every value is real lab output
frontend/src/lib/buildcache.ts  the build simulator's rules, unit tested against chapter 01
frontend/src/lib/pip.ts     Pip's note and quiz for each page
frontend/src/lib/tokens.ts  colour pairs; a test checks them against globals.css and WCAG AA
```

## Commands

```bash
cd lab && uv sync && uv run pytest && uv run ruff check . && uv run ruff format --check .
cd frontend && npm ci && npm run verify
cd frontend && npm run build && npx next start -p 3114   # then, in another shell:
cd frontend && E2E_BASE_URL=http://localhost:3114 npm run test:e2e
```

Set `CHROMIUM_PATH` to use an already installed Chromium for the browser tests.

## Rules

1. **The bugs are the product.** Never fix a bug in `lab/cases/`. Change a case, its check, its
   solution and its chapter together, and keep `test_case_is_broken_as_shipped` passing.
2. **Checks test the job.** A lazy fix (run as root, skip the install, hard-code a number) must
   fail. Add it to `WRONG` in `lab/tests/test_mutations.py`, and add other right fixes to `RIGHT`.
3. **Bugs must be deterministic.** Pretend clocks, a pretend kernel and pretend builds, never real
   timing or a Docker daemon on the core path.
4. **Standard library only** in `lab/`.
5. **Every number is real.** Output and timings in chapters and on the site come from real runs.
   `lab/tests/test_chapters.py` and `frontend/tests/unit/site.test.ts` compare them.
6. **Colours mean one thing.** Green passes or is cached, red fails, ochre is work that ran, blue
   is a layer, orange is something you can press. Status always has an icon and text too.
7. **Writing style.** Plain English, short sentences, no em dashes. Conventional Commits, no AI
   attribution trailers.
