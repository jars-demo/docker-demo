// Pip, the hermit crab who lives in a borrowed shipping container. For each page: a short note
// and two quiz questions, each with one right answer and the reason it is right.

export type Question = {
  q: string
  options: readonly string[]
  answer: number
  why: string
}

export type Notes = { note: string; quiz: readonly Question[] }

const HOME: Notes = {
  note: 'I am Pip. Hermit crabs move into a shell someone else built, and carry it everywhere, so containers feel like home. Try the build on this page: rebuild after an edit to app.py with each Dockerfile, and watch which steps run again.',
  quiz: [
    {
      q: 'You edit one file that a COPY step copies. Which steps run again?',
      options: [
        'Only that COPY step',
        'That COPY step and every step after it',
        'Every step, from FROM down',
      ],
      answer: 1,
      why: 'The COPY misses because its input changed. Every later step has a new parent layer, so it misses too. Steps above it stay cached.',
    },
    {
      q: 'What is a container, underneath?',
      options: [
        'A small virtual machine with its own kernel',
        'Ordinary processes, with namespaces and cgroups around them',
        'A compressed copy of the host',
      ],
      answer: 1,
      why: 'Containers share the host kernel. Namespaces give them their own view of processes, network and files, and cgroups limit what they may use.',
    },
  ],
}

const WORKSHOP: Notes = {
  note: 'Nine chapters, one bug each, in the order you meet them: build, ship, run, then live in production. Chapter 05 makes more sense once chapter 01 has shown you what a layer is.',
  quiz: [
    {
      q: 'Do you need Docker installed for the lab?',
      options: [
        'Yes, Docker Desktop or Docker Engine',
        'No, a pretend builder and kernel follow the real rules',
        'Only for the experiments',
      ],
      answer: 1,
      why: 'The cases model the real rules in plain Python, so every symptom is the same on any machine. The experiments use real sockets and processes, not Docker.',
    },
    {
      q: 'Why does every check test the job, not just the bug?',
      options: [
        'To make the checks longer',
        'So a lazy fix, such as running as root, cannot pass',
        'Because the bugs are random',
      ],
      answer: 1,
      why: 'Most container bugs have a quick fix that hides the symptom and causes a new problem. The checks reject those, so only a real fix passes.',
    },
  ],
}

const CHAPTERS: Record<string, Notes> = {
  '01-layers-and-the-cache': {
    note: 'Read the case output top to bottom and find the first RAN. Everything below it ran for one reason: its parent changed.',
    quiz: [
      {
        q: 'What does the cache compare for RUN pip install -r requirements.txt?',
        options: [
          'The contents of requirements.txt',
          'The instruction text and the parent layer',
          'The packages already installed',
        ],
        answer: 1,
        why: 'The builder does not look inside a RUN. Only the text and the parent matter, which is why you copy requirements.txt in a step of its own just before it.',
      },
      {
        q: 'Your CI rebuilds everything on every job, even with a good Dockerfile. Why?',
        options: [
          'CI ignores the Dockerfile order',
          'Each job starts on a fresh machine with an empty cache',
          'COPY hashes timestamps on CI',
        ],
        answer: 1,
        why: 'The build cache lives on the machine that built. Export it with --cache-to and import it with --cache-from, or a CI job has nothing to reuse.',
      },
    ],
  },
  '02-what-a-layer-remembers': {
    note: 'A later layer can only hide a file. If a secret ever reached a layer that was pushed, rotate it: deleting it in a new build does not reach copies already pulled.',
    quiz: [
      {
        q: 'COPY . . then RUN rm -f .env. Where is .env?',
        options: [
          'Gone from the image',
          'Hidden in the merged view, still whole in the COPY layer',
          'Only in the build cache',
        ],
        answer: 1,
        why: 'The rm makes a whiteout in a new layer. The COPY layer is read only and ships with every pull, .env included.',
      },
      {
        q: 'Which keeps a build-time token out of every layer?',
        options: ['ENV TOKEN=...', 'ARG TOKEN', 'RUN --mount=type=secret'],
        answer: 2,
        why: 'A secret mount exists only while that one RUN runs. ENV lands in the image config, and ARG values used by a RUN land in the history.',
      },
    ],
  },
  '03-multi-stage-builds': {
    note: 'Headers are for building, shared libraries are for running. When an import fails with "cannot open shared object file", the runtime stage is missing the library, not the -dev package.',
    quiz: [
      {
        q: 'What crosses from one stage to the next?',
        options: [
          'Everything the earlier stage installed',
          'Only what COPY --from copies',
          'The environment and the packages',
        ],
        answer: 1,
        why: 'Each FROM starts a fresh filesystem. Only files you copy with COPY --from come across, which is how the compiler stays behind.',
      },
      {
        q: 'Why clean the apt lists in the same RUN as the install?',
        options: [
          'apt needs it',
          'A later RUN only hides them, and the layer below keeps their size',
          'It makes the build faster',
        ],
        answer: 1,
        why: 'Same rule as chapter 02. In the lab, cleaning in a separate RUN leaves the image at 183 MB instead of 135 MB.',
      },
    ],
  },
  '04-tags-and-digests': {
    note: 'Look at what the release history stores. If it is a tag, a rollback means "whatever that tag points at now", which is the opposite of a rollback.',
    quiz: [
      {
        q: 'What does the latest tag mean?',
        options: [
          'The newest image in the registry',
          'The last stable release',
          'Nothing special: it is the default tag name',
        ],
        answer: 2,
        why: 'latest is only what Docker uses when you give no tag. It moves when someone pushes to it, and can point at anything.',
      },
      {
        q: 'Touch a file without changing it and rebuild the layer. The digest:',
        options: [
          'Stays the same',
          'Changes, because the tar records the timestamp',
          'Changes only if compressed',
        ],
        answer: 1,
        why: 'A digest hashes the layer bytes, and a tar entry includes its mtime. dock try digest shows it, and shows that pinned timestamps give the same digest.',
      },
    ],
  },
  '05-pid-one-and-signals': {
    note: 'If docker stop always takes exactly the grace period and ends in exit code 137, the app never heard SIGTERM. Look at who PID 1 is.',
    quiz: [
      {
        q: 'PID 1 has no SIGTERM handler. docker stop sends SIGTERM. What happens?',
        options: [
          'It dies, as any process would',
          'Nothing: the kernel does not deliver default-action signals to PID 1',
          'It forwards the signal to its children',
        ],
        answer: 1,
        why: 'The kernel protects init. PID 1 only reacts to signals it has a handler for, so after the grace period it gets SIGKILL.',
      },
      {
        q: 'What does exec do as the last line of an entrypoint script?',
        options: [
          'Runs the command in the background',
          'Replaces the shell with the command, keeping PID 1',
          'Restarts the container',
        ],
        answer: 1,
        why: 'With exec the program becomes PID 1 and receives SIGTERM itself. Without it, the shell keeps PID 1 and the signal stops there.',
      },
    ],
  },
  '06-container-networking': {
    note: 'Whose localhost? Every container has its own loopback. A published port arrives on the eth0 address of the container, so a server bound to 127.0.0.1 never sees it.',
    quiz: [
      {
        q: 'Inside the worker container, what does localhost:8080 reach?',
        options: ['The host', 'The orders container', "The worker's own loopback"],
        answer: 2,
        why: 'Each network namespace has its own 127.0.0.1. To reach orders, use its service name: http://orders:8080.',
      },
      {
        q: 'You publish -p 8080:8080 on a Linux server. Who can reach it?',
        options: [
          'Only the server itself',
          'Anyone who can reach the server, even past ufw rules',
          'Only other containers',
        ],
        answer: 1,
        why: 'By default Docker listens on every host interface, and its firewall rules run before ufw. Use 127.0.0.1:8080:8080 to keep it local.',
      },
    ],
  },
  '07-health-and-readiness': {
    note: 'depends_on without a condition waits for the container to start, not for the database to accept connections. Ask Postgres itself: pg_isready.',
    quiz: [
      {
        q: 'What is the default healthcheck interval?',
        options: ['1 second', '10 seconds', '30 seconds'],
        answer: 2,
        why: 'The defaults are a 30 s interval, a 30 s timeout and 3 retries. With them, a dependent service waits at least 30 s even if the database was ready in 2.',
      },
      {
        q: 'Should a liveness probe check the database?',
        options: [
          'Yes, a service without its database is useless',
          'No: one bad minute for the database restarts every app at once',
          'Only in production',
        ],
        answer: 1,
        why: 'Liveness decides restarts. Keep it to "is this process stuck?" and put dependency checks in readiness, which only stops traffic.',
      },
    ],
  },
  '08-volumes-and-ownership': {
    note: 'A new named volume copies the owner of the folder from the image. Read the start-up warning: who owns /data, and who is the app?',
    quiz: [
      {
        q: 'You fix the Dockerfile. Does the existing volume get the new owner?',
        options: [
          'Yes, on the next start',
          'No: Docker only fills a volume from the image when it is empty',
          'Only after docker compose down',
        ],
        answer: 1,
        why: 'Population happens once, into an empty volume. An existing one keeps root ownership until you change it, or start as root, chown and drop privileges.',
      },
      {
        q: 'Which is the right fix for "permission denied" on /data?',
        options: ['chmod 777 /data', 'USER root', 'chown the folder to the app user before USER'],
        answer: 2,
        why: 'Give the folder to the one user that needs it. 777 lets every process write the data, and root turns any app bug into a root bug.',
      },
    ],
  },
  '09-resource-limits': {
    note: 'os.cpu_count() counts the host. A CPU limit is a quota in /sys/fs/cgroup/cpu.max: divide quota by period, and fall back to the host count when it says max.',
    quiz: [
      {
        q: 'docker run --cpus 2 on a 32-core host. What does os.process_cpu_count() return?',
        options: ['2', '32', 'It raises an error'],
        answer: 1,
        why: '--cpus sets a time quota, not the CPU affinity. process_cpu_count() reads the affinity, so it still sees all 32 cores.',
      },
      {
        q: 'A container exits with 137 at a random moment, not during a deploy. The likely cause?',
        options: [
          'A normal docker stop',
          'The OOM killer: SIGKILL after going over memory.max',
          'A failed healthcheck',
        ],
        answer: 1,
        why: '137 is 128 + 9, SIGKILL. During a deploy it means a missed SIGTERM; at a random time, look at memory and docker inspect for OOMKilled.',
      },
    ],
  },
}

export const NOTE_SLUGS = Object.keys(CHAPTERS)

export function notesFor(pathname: string): Notes {
  if (pathname === '/workshop') return WORKSHOP
  const slug = /^\/workshop\/([^/]+)$/.exec(pathname)?.[1]
  return (slug && CHAPTERS[slug]) || HOME
}
