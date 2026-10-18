// Facts shown on the site. Every symptom and number is real output from the lab:
// `uv run python -m dock run N` and `dock try`. Unit tests compare each one with the chapters.

export const REPO_URL = 'https://github.com/jars-demo/docker-demo'
export const SITE_URL = 'https://docker.jishanahmed.in'

export type Case = {
  number: string
  title: string
  topics: string
  symptom: string
}

export const CASES: readonly Case[] = [
  {
    number: '01',
    title: 'The rebuild that reinstalled everything',
    topics: 'layers, build cache, step order',
    symptom: 'rebuild after a one-line edit: 96.3 s',
  },
  {
    number: '02',
    title: 'The token in layer three',
    topics: 'build context, .dockerignore, secrets',
    symptom: 'layer 3 (COPY . .): /app/.env  PAYMENT_TOKEN=tp-prod-4f9a2c71',
  },
  {
    number: '03',
    title: 'The image that shrank too far',
    topics: 'multi-stage builds, runtime libraries',
    symptom: 'crashed: ImportError: libpq.so.5: cannot open shared object file',
  },
  {
    number: '04',
    title: 'The rollback that rolled forward',
    topics: 'tags, digests, reproducible builds',
    symptom: '11:10 rollback  node-1 7d40  node-2 7d40  node-3 7d40   sencha 0.00',
  },
  {
    number: '05',
    title: 'The ten-second goodbye',
    topics: 'PID 1, SIGTERM, exec, init',
    symptom: 'docker stop took 10.0 s; exit code 137',
  },
  {
    number: '06',
    title: 'Listening, and unreachable',
    topics: 'namespaces, published ports, DNS',
    symptom: 'laptop  -> curl http://localhost:8080/menu  connection reset by peer',
  },
  {
    number: '07',
    title: 'Started is not ready',
    topics: 'depends_on, healthchecks, retries',
    symptom: 'orders served: 0 of 20',
  },
  {
    number: '08',
    title: 'The orders that vanished on redeploy',
    topics: 'volumes, uid, ownership',
    symptom: 'orders on file after the redeploy:     0',
  },
  {
    number: '09',
    title: 'Sixty-five workers in a two-CPU box',
    topics: 'cgroups, CPU quota, OOM kills',
    symptom: 'gunicorn workers: 65 (2 x 32 + 1)',
  },
]

// The image from case 02, as `docker image save` would unpack it. Real layers from the lab.
export const LAYERS = [
  { number: 5, instruction: 'CMD ["python", "app.py"]', files: [], note: 'config only' },
  {
    number: 4,
    instruction: 'RUN rm -f .env',
    files: [{ path: '/app/.env', hidden: true }],
    note: 'a whiteout: hides .env from here up',
  },
  {
    number: 3,
    instruction: 'COPY . .',
    files: [
      { path: '/app/.env', hidden: false, secret: true },
      { path: '/app/app.py', hidden: false },
      { path: '/app/templates/menu.html', hidden: false },
    ],
    note: 'still holds PAYMENT_TOKEN=tp-prod-4f9a2c71',
  },
  { number: 2, instruction: 'WORKDIR /app', files: [], note: 'config only' },
  { number: 1, instruction: 'FROM python:3.13-slim', files: [], note: '124 MB, shared' },
] as const

// Case 06 from start to finish: what `run` prints, the one line that fixes it, what `check` says.
export const CASE_SIX = {
  run: [
    'orders log:   Running on http://127.0.0.1:8080',
    'laptop  -> curl http://localhost:8080/menu  connection reset by peer',
    'worker  -> GET  http://orders:8080/menu     connection refused',
  ],
  fix: ['ORDERS_CMD = ["flask", "run", "--host", "0.0.0.0", "--port", "8080"]'],
  check: [
    'PASS  from the laptop, curl localhost:8080/menu works (connected)',
    'PASS  the worker reaches http://orders:8080 (connected)',
    'PASS  orders keeps its own network namespace (no network_mode: host)',
  ],
}

// Measured with `dock try context`, `dock try ports` and `dock try stop` on one machine, and
// quoted in chapters 02, 06 and 05. Your numbers will differ; the shape will not.
export const MEASURED = {
  machine: 'Python 3.13.16, Linux, 4 CPUs',
  context: [
    { label: 'everything', files: '4555', size: '93.3 MB', time: '1316 ms' },
    { label: 'with .dockerignore', files: '53', size: '0.3 MB', time: '6 ms' },
  ],
  stop: [
    {
      label: 'python, handles SIGTERM',
      took: '0.22 s',
      ended: 'exit 0',
      worker: 'finished its work',
      good: true,
    },
    {
      label: 'python, SIGTERM ignored',
      took: '2.00 s',
      ended: 'SIGKILL',
      worker: 'killed mid-work',
      good: false,
    },
    {
      label: "sh -c 'python ...; true'",
      took: '0.00 s',
      ended: 'SIGTERM',
      worker: 'never told, still running',
      good: false,
    },
    {
      label: "sh -c 'exec python ...'",
      took: '0.21 s',
      ended: 'exit 0',
      worker: 'finished its work',
      good: true,
    },
  ],
  ports: [
    { bind: '127.0.0.1', target: '127.0.0.1', result: 'accepted', time: '132 µs' },
    { bind: '127.0.0.1', target: '192.0.2.2', result: 'refused', time: '24 µs' },
    { bind: '0.0.0.0', target: '127.0.0.1', result: 'accepted', time: '142 µs' },
    { bind: '0.0.0.0', target: '192.0.2.2', result: 'accepted', time: '139 µs' },
  ],
}

export const CHECKLIST = [
  'Order the Dockerfile from what changes least to what changes most, and copy the dependency manifest before the code.',
  'Keep the build context small with .dockerignore, and never send a secret to the builder.',
  'Remember that a later layer can only hide a file. Clean up in the same RUN that made the mess.',
  'Give secrets to the container at run time, or to one RUN with a secret mount, never with ENV or ARG.',
  'Build in one stage and run in another, and install the run-time libraries, not the -dev packages.',
  'Deploy and record images by digest, and use tags only as names for people.',
  'Make sure SIGTERM reaches your app: exec in entrypoint scripts, exec form in CMD, and a handler in the app.',
  'Listen on 0.0.0.0 inside the container, and publish only the ports that must be reached from outside.',
  'Wait for readiness with a healthcheck that asks the service itself, and let apps retry their dependencies.',
  'Keep data on volumes, and give the data folder to a fixed non-root user in the image.',
  "Size worker pools from the cgroup limits, not from the host's CPU count.",
]

export const QUICKSTART = `git clone ${REPO_URL}.git
cd docker-demo/lab
uv sync
uv run python -m dock run 1`
