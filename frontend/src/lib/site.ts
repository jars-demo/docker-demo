// Facts shown on the site. Every symptom and number is real output from the lab, measured on a
// 4-CPU Docker Desktop engine (Docker 28.2.2). Unit tests compare each one with the chapters.

export const REPO_URL = 'https://github.com/jars-demo/docker-demo'
export const SITE_URL = 'https://docker.jishanahmed.in'
export const TITLE = 'Docker, from first container to production'
export const SHORT_TITLE = 'Docker, first container to production'
export const TAGLINE =
  'A hands-on Docker workshop in twelve chapters. Real builds, real containers and a real registry: the build cache, secrets, networking, volumes, Compose, multi-stage builds, signals, health checks, cgroup limits and digests.'

export type Level = 'Foundations' | 'Services and data' | 'Production'

export const LEVELS: readonly { name: Level; chapters: readonly number[]; about: string }[] = [
  {
    name: 'Foundations',
    chapters: [1, 2, 3, 4],
    about: 'What a container is, what goes into an image, the build cache and networking.',
  },
  {
    name: 'Services and data',
    chapters: [5, 6, 7],
    about: 'Volumes and ownership, Compose with a real Postgres, and secrets at build time.',
  },
  {
    name: 'Production',
    chapters: [8, 9, 10, 11, 12],
    about: 'Small images, graceful shutdown, health checks, cgroup limits and digests.',
  },
]

export function levelOf(chapter: number): Level {
  return LEVELS.find((level) => level.chapters.includes(chapter))?.name ?? 'Foundations'
}

/** What goes wrong in each exercise, as the lab prints it. */
export const SYMPTOMS: Record<string, string> = {
  '01': 'dockerlab-01   Exited (0) 3 seconds ago',
  '02': 'API_KEY=sk_dockerlab_6e50aac08080d1c62dc6a9b9',
  '03': 'ran     6.2 s  RUN pip install --no-cache-dir -r requirements.txt',
  '04': 'RemoteDisconnected: Remote end closed connection without response',
  '05': 'sqlite3.OperationalError: unable to open database file',
  '06': 'api       Exited (1) 7 seconds ago',
  '07': 'ARG PACKAGE_TOKEN=pkg_dockerlab_99b7b8ab9421e672b516dab8',
  '08': 'image size: 1,138.5 MB',
  '09': 'took 10.6 s, exit code 137',
  '10': 'exit code 1: /bin/sh: 1: curl: not found',
  '11': 'container: exited, exit code 1, OOMKilled=true',
  '12': 'the running version is 1.5.0',
}

/** Real measurements from the chapters and from `dock try`. */
export const MEASURED = {
  pipInstallSeconds: 6.2,
  cachedRebuildSeconds: 0.4,
  processMs: 38,
  containerMs: 541,
  stopShippedSeconds: 10.6,
  stopFixedSeconds: 1.9,
  imageShippedMb: '1,138.5',
  imageFixedMb: '149.8',
  layerHiddenMb: '100.0',
  bases: [
    { image: 'python:3.13.16-trixie', size: '1,112.0 MB' },
    { image: 'python:3.13.16-slim-trixie', size: '118.3 MB' },
    { image: 'python:3.13.16-alpine', size: '51.9 MB' },
  ],
} as const

export const QUICKSTART = `git clone https://github.com/jars-demo/docker-demo.git
cd docker-demo/lab
uv sync
uv run python -m dock run 1`
