# Docker, from first container to production

A hands-on Docker workshop in twelve chapters, from what a container really is to shipping a release by digest. Each chapter explains one idea in depth and hands you a broken Dockerfile, Compose file or release script that fails the way real projects do. You fix it, and a checker proves the fix with real builds, real containers, a real Postgres and a real registry.

**Workshop site:** [docker.jishanahmed.in](https://docker.jishanahmed.in)

## Quick start

You need [Docker](https://docs.docker.com/get-started/get-docker/) (Docker Desktop, or Docker Engine on Linux), [uv](https://docs.astral.sh/uv/) and git. uv installs Python for you, and the lab uses only Python's standard library.

```bash
git clone https://github.com/jars-demo/docker-demo.git
cd docker-demo/lab
uv sync
uv run python -m dock run 1
```

## How an exercise works

| Command | What it does |
| --- | --- |
| `uv run python -m dock list` | every exercise and its folder |
| `uv run python -m dock run N` | build and run exercise N as it ships, and show what goes wrong |
| `uv run python -m dock check N` | check your fix with real builds and containers |
| `uv run python -m dock hint N` | a nudge, one step at a time |
| `uv run python -m dock try startup` | a container's start time next to a plain process |
| `uv run python -m dock try layers` | a file deleted in a later layer still ships |
| `uv run python -m dock try sizes` | the same server on three base images |
| `uv run python -m dock try network` | name lookup on the default network and on a user-defined one |
| `uv run python -m dock clean` | remove everything the lab created |

Edit the files in `lab/exercises/NN-*/`. Start an exercise over with `git restore exercises/` from `lab/`. Everything the lab creates is named `dockerlab`, so `dock clean` never touches your other images or containers.

## The chapters

| # | Chapter | What goes wrong |
| --- | --- | --- |
| | **Foundations** | |
| 01 | [Containers are processes](workshop/01-containers-are-processes.md) | The container that would not stay up |
| 02 | [The build context and .dockerignore](workshop/02-build-context.md) | The secret that shipped with the image |
| 03 | [Layers and the build cache](workshop/03-build-cache.md) | Every rebuild reinstalls everything |
| 04 | [Ports and networks](workshop/04-ports-and-networks.md) | Listening, and unreachable |
| | **Services and data** | |
| 05 | [Volumes and file ownership](workshop/05-volumes.md) | Permission denied on a fresh volume |
| 06 | [Compose and start-up order](workshop/06-compose.md) | The API that started before its database |
| 07 | [Secrets at build time](workshop/07-build-secrets.md) | The token in the image history |
| | **Production** | |
| 08 | [Multi-stage builds](workshop/08-multi-stage.md) | 1.1 GB to ship one small API |
| 09 | [PID 1 and graceful shutdown](workshop/09-graceful-shutdown.md) | The ten-second stop |
| 10 | [Health checks](workshop/10-health-checks.md) | Unhealthy, though nothing is wrong |
| 11 | [CPU and memory limits](workshop/11-resource-limits.md) | Nine workers in a one-CPU container |
| 12 | [Tags, digests and registries](workshop/12-tags-and-digests.md) | The rollback that rolled forward |

About four and a half hours in total. Chapter 12 ends with a production checklist.

## Layout

```text
lab/exercises/        the twelve exercises you edit
lab/solutions/        the files that fix each exercise: peek only when truly stuck
lab/dock/             the CLI, one module per exercise (run and check), the experiments
lab/tests/            every exercise fails as shipped, passes when fixed, and rejects wrong fixes
workshop/             the chapters, in Markdown
frontend/             the workshop site (Next.js), which renders workshop/
```

Run the lab's tests with `cd lab && uv run pytest`. They need Docker running and take about fifteen minutes, because every check builds and runs real containers.

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

An independent workshop, not affiliated with Docker, Inc.

## License

[MIT](LICENSE)
