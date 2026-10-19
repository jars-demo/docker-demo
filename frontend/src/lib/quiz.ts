// Two questions at the end of every chapter, each with one right answer and the reason.

export type Question = {
  q: string
  options: readonly string[]
  answer: number
  why: string
}

export const QUIZ: Record<string, readonly Question[]> = {
  '01': [
    {
      q: 'What decides how long a container runs?',
      options: ['Its restart policy', 'How long its PID 1 runs', 'The size of its image'],
      answer: 1,
      why: 'Docker supervises one process. When PID 1 exits, the container stops with its exit code.',
    },
    {
      q: 'Why is tail -f /dev/null a bad way to keep a container up?',
      options: [
        'It uses too much CPU',
        'The container stays up after the real server dies, so nothing restarts it',
        'It fills the log',
      ],
      answer: 1,
      why: 'The container must die with the server. Otherwise every request fails while Docker reports Up.',
    },
  ],
  '02': [
    {
      q: 'A later RUN rm .env deletes a copied secret. Is it gone from the image?',
      options: ['Yes', 'No, the layer that added it still ships', 'Only on Linux'],
      answer: 1,
      why: 'Layers are diffs. A later layer can hide a file, but the earlier layer still contains it.',
    },
    {
      q: 'What does .dockerignore control?',
      options: [
        'Which files are sent to the builder as the build context',
        'Which files git ignores',
        'Which layers are cached',
      ],
      answer: 0,
      why: 'Ignored files never leave your machine, so no COPY can put them in an image.',
    },
  ],
  '03': [
    {
      q: 'Step 3 of 6 misses the cache. Which steps run?',
      options: ['Only step 3', 'Steps 3 to 6', 'All six'],
      answer: 1,
      why: 'Each key includes its parent. Once a step misses, every step after it has a new parent.',
    },
    {
      q: 'RUN pip install fastapi is cached. A new fastapi is released. Does the next build get it?',
      options: ['Yes', 'No, RUN caches on its text, not its result', 'Only with --pull'],
      answer: 1,
      why: 'The instruction did not change, so its key did not change. Use --no-cache or change the line.',
    },
  ],
  '04': [
    {
      q: 'Where does a published port deliver traffic inside the container?',
      options: [
        "The container's loopback, 127.0.0.1",
        "The container's network interface",
        'The host',
      ],
      answer: 1,
      why: 'Docker forwards to the container address on its network, so a server on 127.0.0.1 never sees it.',
    },
    {
      q: 'What does EXPOSE 8000 publish?',
      options: ['Port 8000 on every interface', 'Port 8000 on localhost', 'Nothing'],
      answer: 2,
      why: 'EXPOSE is documentation and a default for -P. Only -p or ports: publishes a port.',
    },
  ],
  '05': [
    {
      q: 'A new named volume is mounted on a path the image does not have. Who owns it?',
      options: ['The USER in the Dockerfile', 'root', 'Whoever runs docker'],
      answer: 1,
      why: 'Docker creates the missing mount point as root, and the new volume copies that.',
    },
    {
      q: 'Where must RUN mkdir /data && chown app:app /data go?',
      options: ['After USER app', 'Before USER app', 'Anywhere'],
      answer: 1,
      why: 'Only root can change ownership, so it has to run before the image switches user.',
    },
  ],
  '06': [
    {
      q: 'What does the short form depends_on: [db] wait for?',
      options: ['Postgres to accept connections', 'The db container to start', 'A health check'],
      answer: 1,
      why: 'It only orders container starts. Use condition: service_healthy to wait for readiness.',
    },
    {
      q: 'Why does the health check use pg_isready -h 127.0.0.1?',
      options: [
        'It is faster',
        'During a first start, Postgres answers on its socket before TCP opens',
        'pg_isready needs a host',
      ],
      answer: 1,
      why: 'The API connects over TCP, so the check must test TCP. The socket passes seconds too early.',
    },
  ],
  '07': [
    {
      q: 'Where does a build argument used by a RUN step end up?',
      options: ['Nowhere', 'In the image history', 'Only in the build cache'],
      answer: 1,
      why: 'docker history --no-trunc prints it next to every RUN step that used it.',
    },
    {
      q: 'What does RUN --mount=type=secret do with the secret?',
      options: [
        'Writes it to a layer and deletes it',
        'Makes it available to that one step without storing it in the image',
        'Encrypts it in the image',
      ],
      answer: 1,
      why: 'The secret is mounted for the step only. It is not in the layer, the config or the history.',
    },
  ],
  '08': [
    {
      q: 'Which stage becomes the image?',
      options: ['The first', 'The last', 'The biggest'],
      answer: 1,
      why: 'Earlier stages only exist to produce files that later stages copy with COPY --from.',
    },
    {
      q: 'The slim runtime stage copies the venv but not libpq5. What happens?',
      options: [
        'Nothing, psycopg bundles it',
        'import psycopg fails: libpq.so.5 cannot be found',
        'The build fails',
      ],
      answer: 1,
      why: 'The C build links to the system libpq at run time. Build headers are not enough.',
    },
  ],
  '09': [
    {
      q: 'A container takes exactly 10 s to stop and exits 137. What happened?',
      options: [
        'It crashed',
        'PID 1 ignored SIGTERM and Docker sent SIGKILL after the grace period',
        'It ran out of memory',
      ],
      answer: 1,
      why: '137 is 128 + 9, SIGKILL. Ten seconds is the default grace period.',
    },
    {
      q: 'What does exec python server.py do in a start script?',
      options: [
        'Runs the server in the background',
        'Replaces the shell with the server, so the server becomes PID 1',
        'Restarts the server on failure',
      ],
      answer: 1,
      why: 'exec keeps the PID and swaps the program, so SIGTERM reaches the server directly.',
    },
  ],
  '10': [
    {
      q: 'Where does a HEALTHCHECK command run?',
      options: ['On the host', 'Inside the container, with its tools', 'In the registry'],
      answer: 1,
      why: 'That is why curl fails in a slim image: the container does not have it.',
    },
    {
      q: 'Does Docker on its own restart an unhealthy container?',
      options: ['Yes, always', 'No, restart policies react to exits', 'Only with --init'],
      answer: 1,
      why: 'Docker records health. Swarm, Kubernetes probes or a watchdog act on it.',
    },
  ],
  '11': [
    {
      q: 'With --cpus 1 on an 8-CPU host, what does os.cpu_count() return?',
      options: ['1', '8', '0'],
      answer: 1,
      why: '--cpus sets a time quota. The CPU count still reports the host. Read the cgroup quota.',
    },
    {
      q: 'Exit code 137 with OOMKilled=true means...',
      options: [
        'docker stop sent SIGKILL',
        'the kernel killed a process for going over the memory limit',
        'the health check failed',
      ],
      answer: 1,
      why: 'Both send SIGKILL. OOMKilled tells a memory kill apart from a stop.',
    },
  ],
  '12': [
    {
      q: 'What can a push to app:stable change?',
      options: ['Nothing, tags are permanent', 'Which image app:stable points to', 'Old digests'],
      answer: 1,
      why: 'A tag is a movable pointer. A digest always means the same bytes.',
    },
    {
      q: 'Where does the registry report the digest a tag points at?',
      options: ['In the Docker-Content-Digest header', 'In the image config', 'In docker logs'],
      answer: 0,
      why: 'A HEAD request to /v2/<repository>/manifests/<tag> returns it, without downloading anything.',
    },
  ],
}
