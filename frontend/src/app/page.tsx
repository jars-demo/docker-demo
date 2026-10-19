import Link from 'next/link'

import { CacheSim } from '@/components/CacheSim'
import { ChapterList } from '@/components/ChapterList'
import { CopyButton } from '@/components/CopyButton'
import { MEASURED, QUICKSTART, REPO_URL, TITLE } from '@/lib/site'
import { CHAPTERS } from '@/lib/workshop'

const hours = (minutes: number) => `${Math.floor(minutes / 60)} h ${minutes % 60} min`

function Before() {
  return (
    <figure className="terminal overflow-hidden text-[13px] leading-relaxed shadow-2xl sm:text-[14px]">
      <figcaption className="flex items-center justify-between bg-code-head px-4 py-2.5 text-[12px] tracking-[0.06em] text-code-muted uppercase">
        <span>Measured in the lab</span>
        <span>before, after</span>
      </figcaption>
      <div className="flex flex-col gap-4 overflow-x-auto p-4">
        <div>
          <p className="text-code-muted"># chapter 09: stopping the API</p>
          <p>
            <span className="text-code-blue">$</span> docker stop api
          </p>
          <p className="text-code-fail">took {MEASURED.stopShippedSeconds} s, exit code 137</p>
          <p className="text-code-pass">took {MEASURED.stopFixedSeconds} s, exit code 0</p>
        </div>
        <div>
          <p className="text-code-muted"># chapter 08: the image you ship</p>
          <p>
            <span className="text-code-blue">$</span> docker image ls api
          </p>
          <p className="text-code-fail">{MEASURED.imageShippedMb} MB, gcc inside, runs as root</p>
          <p className="text-code-pass">{MEASURED.imageFixedMb} MB, no compiler, uid 10001</p>
        </div>
        <div>
          <p className="text-code-muted"># chapter 03: rebuild after a one-line change</p>
          <p className="text-code-fail">pip install ran again: {MEASURED.pipInstallSeconds} s</p>
          <p className="text-code-pass">every layer cached: {MEASURED.cachedRebuildSeconds} s</p>
        </div>
      </div>
    </figure>
  )
}

const FACTS = [
  {
    label: 'Start a process',
    value: `${MEASURED.processMs} ms`,
    note: 'python -c pass, on the host',
  },
  {
    label: 'Start a container',
    value: `${MEASURED.containerMs} ms`,
    note: 'docker run --rm python:slim true',
  },
  {
    label: 'A file deleted in a later layer',
    value: `${MEASURED.layerHiddenMb} MB`,
    note: 'still shipped with the image',
  },
]

export default function Home() {
  const minutes = CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)
  return (
    <>
      <section className="on-navy hero-grid bg-navy text-on-navy">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 pt-14 pb-16 lg:grid-cols-[1.1fr_1fr] lg:items-center lg:pt-20 lg:pb-24">
          <div className="flex min-w-0 flex-col gap-6">
            <span className="eyebrow">
              A hands-on workshop · {CHAPTERS.length} chapters · {hours(minutes)}
            </span>
            <h1 className="text-[40px] leading-[1.05] font-bold tracking-[-0.03em] text-balance sm:text-[56px]">
              {TITLE}
            </h1>
            <p className="max-w-xl text-[18px] leading-relaxed text-on-navy-muted">
              Twelve chapters that explain how Docker really works, each with a broken Dockerfile,
              Compose file or release script to fix. Real builds, real containers, a real Postgres
              and a real registry. Every number on this site was measured.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href={`/workshop/${CHAPTERS[0]?.slug}`}
                className="inline-flex h-12 items-center rounded-md bg-blue px-5 text-[16px] font-semibold text-on-blue hover:bg-blue-hover"
              >
                Start chapter 01
              </Link>
              <a
                href={REPO_URL}
                className="inline-flex h-12 items-center rounded-md border border-on-navy-muted/40 px-5 text-[16px] font-semibold text-on-navy hover:bg-navy-2"
              >
                Get the lab on GitHub
              </a>
            </div>
          </div>
          <div className="min-w-0">
            <Before />
          </div>
        </div>
      </section>

      <section aria-labelledby="chapters" className="mx-auto max-w-6xl px-4 py-16 sm:py-20">
        <div className="mb-10 flex max-w-3xl flex-col gap-3">
          <span className="eyebrow">The path</span>
          <h2 id="chapters" className="text-[32px] leading-tight font-bold tracking-[-0.02em]">
            From one container to a production release
          </h2>
          <p className="text-[17px] leading-relaxed text-ink-2">
            Each chapter explains one idea in depth, then hands you an exercise that gets it wrong
            in a way real teams do. You fix it, and a checker proves the fix with real containers.
            The red line on each card is what the exercise prints before you start.
          </p>
        </div>
        <ChapterList />
      </section>

      <section aria-labelledby="cache" className="border-y border-rule bg-canvas-2">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:py-20 lg:grid-cols-[1fr_1.25fr]">
          <div className="flex flex-col gap-4">
            <span className="eyebrow">Try it: chapter 03</span>
            <h2 id="cache" className="text-[32px] leading-tight font-bold tracking-[-0.02em]">
              The build cache, one step at a time
            </h2>
            <p className="text-[17px] leading-relaxed text-ink-2">
              BuildKit reuses a layer only when the step and everything before it are unchanged.
              Build once, then change a line of code and build again. In the Dockerfile as shipped,
              <code className="mx-1 rounded bg-surface px-1.5 font-mono text-[14px]">COPY . .</code>
              comes before the install, so every commit reinstalls every dependency.
            </p>
            <p className="text-[17px] leading-relaxed text-ink-2">
              Switch to the fixed Dockerfile and do the same. Then change requirements.txt and watch
              the install run again, which is exactly when it should.
            </p>
          </div>
          <div className="min-w-0">
            <CacheSim />
          </div>
        </div>
      </section>

      <section aria-labelledby="measured" className="mx-auto max-w-6xl px-4 py-16 sm:py-20">
        <div className="mb-8 flex max-w-3xl flex-col gap-3">
          <span className="eyebrow">Measured, not quoted</span>
          <h2 id="measured" className="text-[32px] leading-tight font-bold tracking-[-0.02em]">
            Run the experiments on your own machine
          </h2>
          <p className="text-[17px] leading-relaxed text-ink-2">
            <code className="font-mono text-[15px]">uv run python -m dock try</code> measures real
            Docker behaviour where you run it. These are the numbers from the machine the workshop
            was written on: Docker Desktop with 4 CPUs.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {FACTS.map((fact) => (
            <div key={fact.label} className="card flex flex-col gap-1 p-5">
              <span className="text-[14px] text-muted">{fact.label}</span>
              <span className="font-mono text-[30px] font-medium tracking-[-0.02em] text-ink">
                {fact.value}
              </span>
              <span className="text-[14px] text-ink-2">{fact.note}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 overflow-x-auto rounded-lg border border-rule">
          <table className="w-full text-left text-[15px]">
            <caption className="sr-only">The same small server on three base images</caption>
            <thead className="bg-canvas-2">
              <tr>
                <th className="px-4 py-3 font-semibold">Base image, same server</th>
                <th className="px-4 py-3 text-right font-semibold">Image size</th>
              </tr>
            </thead>
            <tbody>
              {MEASURED.bases.map((base) => (
                <tr key={base.image} className="border-t border-rule">
                  <td className="px-4 py-3 font-mono text-[14px] whitespace-nowrap">
                    {base.image}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-[14px] whitespace-nowrap">
                    {base.size}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="start" className="bg-navy text-on-navy on-navy">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:py-20 lg:grid-cols-2 lg:items-center">
          <div className="flex flex-col gap-4">
            <span className="eyebrow">Quick start</span>
            <h2 id="start" className="text-[32px] leading-tight font-bold tracking-[-0.02em]">
              You need Docker, uv and git
            </h2>
            <p className="text-[17px] leading-relaxed text-on-navy-muted">
              Docker Desktop on macOS or Windows, or Docker Engine on Linux. uv installs Python for
              you, and the lab itself uses only Python&apos;s standard library. Everything the lab
              creates is named dockerlab, and <code className="font-mono">dock clean</code> removes
              it all.
            </p>
          </div>
          <div className="terminal min-w-0 overflow-hidden">
            <div className="flex items-center justify-between bg-code-head py-1 pr-1 pl-4 text-[12px] tracking-[0.06em] text-code-muted uppercase">
              <span>shell</span>
              <CopyButton text={QUICKSTART} label="Copy the quick start" />
            </div>
            <pre className="overflow-x-auto p-4 text-[14px] leading-relaxed">{QUICKSTART}</pre>
          </div>
        </div>
      </section>
    </>
  )
}
