# Docker without the magic

A hands-on Docker workshop. Nine chapters take an image from its first build to a busy production box. Each one explains an idea in depth and hands you a small program for Tidepool Tea's orders service with one real container bug to fix: the build cache, secrets left in layers, multi-stage builds, tags and digests, PID 1 and signals, networking, readiness, volume ownership and CPU limits. **Pip**, a hermit crab who lives in a borrowed shipping container, quizzes you along the way. You do not need Docker to start: the lab follows the real rules in plain Python.

**Workshop site:** [docker.jishanahmed.in](https://docker.jishanahmed.in)

## Quick start

You need [uv](https://docs.astral.sh/uv/) and git. uv installs Python for you. The lab uses the Python standard library only.

```bash
git clone https://github.com/jars-demo/docker-demo.git
cd docker-demo/lab
uv sync
uv run python -m dock run 1
```

## How a case works

| Command                             | What it does                                                    |
| ----------------------------------- | --------------------------------------------------------------- |
| `uv run python -m dock list`        | every case, and which ones are fixed                            |
| `uv run python -m dock run N`       | run case N and watch the bug happen                             |
| `uv run python -m dock check N`     | check your fix: the bug is gone and the job still gets done     |
| `uv run python -m dock hint N`      | a nudge from Pip                                                |
| `uv run python -m dock try context` | pack and hash a build context, with and without .dockerignore   |
| `uv run python -m dock try digest`  | which changes alter a layer digest when the bytes stay the same |
| `uv run python -m dock try ports`   | real sockets bound to 127.0.0.1 and to 0.0.0.0                  |
| `uv run python -m dock try stop`    | SIGTERM, a grace period and SIGKILL against real processes      |

Fix the code in `lab/cases/`. Start a case over with `git restore cases/` from `lab/`.

Every check tests the job as well as the bug, so a quick fix that only hides the symptom, such as running as root or skipping the install, never passes. `dock try stop` needs Linux, macOS or WSL.

## The chapters

| #   | Chapter                                                           | The case                                |
| --- | ----------------------------------------------------------------- | --------------------------------------- |
| 01  | [Layers and the build cache](workshop/01-layers-and-the-cache.md) | The rebuild that reinstalled everything |
| 02  | [What a layer remembers](workshop/02-what-a-layer-remembers.md)   | The token in layer three                |
| 03  | [Multi-stage builds](workshop/03-multi-stage-builds.md)           | The image that shrank too far           |
| 04  | [Tags and digests](workshop/04-tags-and-digests.md)               | The rollback that rolled forward        |
| 05  | [PID 1 and signals](workshop/05-pid-one-and-signals.md)           | The ten-second goodbye                  |
| 06  | [Container networking](workshop/06-container-networking.md)       | Listening, and unreachable              |
| 07  | [Health and readiness](workshop/07-health-and-readiness.md)       | Started is not ready                    |
| 08  | [Volumes and ownership](workshop/08-volumes-and-ownership.md)     | The orders that vanished on redeploy    |
| 09  | [Resource limits](workshop/09-resource-limits.md)                 | Sixty-five workers in a two-CPU box     |

About 2 hours 45 minutes in total. The last chapter ends with a checklist to keep.

## Layout

```text
lab/cases/            the nine cases: one real container bug each
lab/dock/             the CLI, the checks, the pretend builder and the four experiments
lab/tests/            every case fails as shipped and passes with the fix in tests/solutions/
workshop/             the chapters, in Markdown
frontend/             the workshop site (Next.js), which renders workshop/
```

Run the lab's tests with `cd lab && uv run pytest`. The solutions are in `lab/tests/solutions/`: peek only when truly stuck.

## Run the site locally

```bash
cd frontend
npm ci
npm run dev
```

`npm run verify` runs lint, types, formatting, unit tests and a production build. The browser tests run against a production server:

```bash
npm run build && npx next start -p 3114
E2E_BASE_URL=http://localhost:3114 npm run test:e2e
```

## License

[MIT](LICENSE)
