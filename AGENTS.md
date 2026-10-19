# AGENTS.md

Guidance for AI coding agents and developers. Humans: start with [README.md](README.md).

## What this is

"Docker, from first container to production": twelve chapters, each a Docker idea explained in
depth, with an exercise that runs on real Docker. `lab/` holds the exercises and the checker;
`workshop/` the chapters; `frontend/` the site.

## Map

```text
lab/exercises/NN-*/         what the learner edits: Dockerfiles, compose.yaml, scripts, small apps
lab/solutions/NN-*/         only the files that change; copied over an exercise, it passes
lab/dock/exNN.py            TITLE, HINTS, run(path) shows the symptom, check(path) -> [(label, ok)]
lab/dock/docker.py          docker CLI helpers: build log parsing, layer scanning, cleanup
lab/dock/experiments.py     `dock try startup | layers | sizes | network`, all measured live
lab/tests/                  shipped fails, solved passes, wrong fixes fail, other real fixes pass
frontend/src/lib/site.ts    symptoms and measured numbers: each one is real lab output
frontend/src/lib/cache.ts   the build cache simulator's rules, unit tested
frontend/src/lib/quiz.ts    two questions per chapter
frontend/src/lib/tokens.ts  colour pairs; a test checks them against globals.css and WCAG AA
```

## Commands

```bash
cd lab && uv sync && uv run pytest && uv run ruff check .   # needs Docker running
cd frontend && npm ci && npm run verify
```

## Rules

1. **The bugs are the product.** Never fix an exercise. Change an exercise, its check and its
   solution together, and keep the tests passing.
2. **Real Docker only.** Checks build and run real images and containers. No simulations in `lab/`.
3. **Checks test the goal, not the symptom.** Each one must reject the fix that only hides the
   problem; add it to `tests/test_wrong_fixes.py`.
4. **Only touch what the lab made.** Every name starts with `dockerlab` and carries the label
   `dockerlab=1`. Never prune or remove anything else.
5. **Every number is real.** Output in chapters and on the site comes from real runs, and unit
   tests compare the site's numbers with the chapters.
6. **Writing style.** Plain English, short sentences, no em dashes. Conventional Commits, no AI
   attribution trailers.
