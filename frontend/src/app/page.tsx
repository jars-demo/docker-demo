import Link from 'next/link'

import { BuildSim } from '@/components/BuildSim'
import { ChapterList } from '@/components/ChapterList'
import { CopyButton } from '@/components/CopyButton'
import { LayerStack } from '@/components/LayerStack'
import { Pip } from '@/components/Pip'
import { CASE_SIX, CHECKLIST, MEASURED, QUICKSTART, REPO_URL } from '@/lib/site'
import { CHAPTERS } from '@/lib/workshop'

function SectionHead({
  id,
  eyebrow,
  title,
  children,
}: {
  id: string
  eyebrow: string
  title: string
  children?: React.ReactNode
}) {
  return (
    <div className="flex max-w-2xl flex-col gap-3">
      <span className="eyebrow">{eyebrow}</span>
      <h2 id={id} className="display text-[32px] leading-[1.08] text-ink sm:text-[40px]">
        {title}
      </h2>
      {children ? <p className="text-[17px] leading-relaxed text-ink-2">{children}</p> : null}
    </div>
  )
}

const LEARN = [
  [
    'Build',
    'Read an image as layers, predict the build cache, and keep secrets and compilers out.',
  ],
  ['Ship', 'Name images by digest, so a rollback runs exactly what ran before.'],
  ['Run', 'Get SIGTERM to your app, listen on the right address, and wait for real readiness.'],
  ['Live', 'Keep data on volumes with the right owner, and size workers from the cgroup limits.'],
] as const

export default function Home() {
  const minutes = CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)
  const hours = Math.floor(minutes / 60)
  return (
    <>
      <section className="on-navy bg-navy text-on-navy">
        <div className="mx-auto grid max-w-6xl gap-12 px-4 pt-14 pb-20 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] lg:items-center lg:gap-16 lg:pt-20 lg:pb-24">
          <div className="flex min-w-0 flex-col gap-6">
            <span className="eyebrow">
              A hands-on workshop · {CHAPTERS.length} chapters ·{' '}
              <span className="whitespace-nowrap">
                {hours} h {minutes % 60} min
              </span>
            </span>
            <h1 className="display text-[46px] leading-[0.98] text-balance sm:text-[68px]">
              Docker without the magic.
            </h1>
            <p className="max-w-xl text-[19px] leading-relaxed text-on-navy-muted sm:text-[20px]">
              A container is a process with a few walls around it. Learn what each wall does by
              fixing nine real bugs in the orders service of a small tea shop. No Docker needed to
              start: the lab follows the real rules in plain Python.
            </p>
            <div className="flex flex-wrap gap-3 pt-1">
              <Link
                href={`/workshop/${CHAPTERS[0]?.slug ?? ''}`}
                className="inline-flex h-12 items-center rounded-[4px] bg-signal-fill px-6 text-[15.5px] font-semibold text-navy hover:bg-signal-hover"
              >
                Start chapter 01
              </Link>
              <a
                href="#start"
                className="inline-flex h-12 items-center rounded-[4px] border border-on-navy-muted px-6 text-[15.5px] font-semibold text-on-navy hover:border-on-navy"
              >
                Quick start
              </a>
            </div>
          </div>
          <div className="min-w-0">
            <LayerStack />
          </div>
        </div>
      </section>

      <section aria-labelledby="learn" className="mx-auto flex max-w-6xl flex-col gap-8 px-4 pt-20">
        <SectionHead id="learn" eyebrow="What you will learn" title="Build, ship, run, live">
          The chapters follow an image through its life, from the first build to a busy production
          box, and stop at each place where teams lose an afternoon.
        </SectionHead>
        <dl className="grid gap-x-10 border-t-2 border-navy sm:grid-cols-2">
          {LEARN.map(([stage, text]) => (
            <div key={stage} className="flex gap-4 border-b border-rule py-4">
              <dt className="w-14 shrink-0 font-mono text-[12.5px] font-semibold tracking-[0.1em] text-signal uppercase">
                {stage}
              </dt>
              <dd className="text-[16px] leading-relaxed text-ink">{text}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section
        aria-labelledby="chapters"
        className="mx-auto flex max-w-6xl flex-col gap-10 px-4 pt-20"
      >
        <SectionHead id="chapters" eyebrow="The manifest" title="Nine chapters, nine bugs">
          Each chapter explains one idea in depth, then hands you a program that gets it wrong. Next
          to each one is what you will see when you run it.
        </SectionHead>
        <ChapterList />
      </section>

      <section
        id="build"
        aria-labelledby="build-title"
        className="mx-auto flex max-w-6xl scroll-mt-6 flex-col gap-8 px-4 pt-20 [&>*]:min-w-0"
      >
        <div className="flex flex-col gap-5">
          <SectionHead id="build-title" eyebrow="Try it" title="The build cache">
            The orders service&apos;s Dockerfile, with the lab&apos;s timings. Build it, edit a
            file, and build again.
          </SectionHead>
          <ol className="grid gap-3 text-[15.5px] leading-relaxed text-ink-2 md:grid-cols-3 md:gap-8">
            <li>
              <strong className="font-mono text-signal">1.</strong> With the Dockerfile as shipped,
              press Build, then edit app.py. pip install runs again for a file it never reads.
            </li>
            <li>
              <strong className="font-mono text-signal">2.</strong> Switch to Fixed and do the same.
              Only the last COPY runs.
            </li>
            <li>
              <strong className="font-mono text-signal">3.</strong> Move the steps around and find
              the orders that break the build. Then fix it for real in{' '}
              <Link
                href="/workshop/01-layers-and-the-cache"
                className="font-medium text-ink underline decoration-signal-fill decoration-2 underline-offset-3"
              >
                chapter 01
              </Link>
              .
            </li>
          </ol>
        </div>
        <BuildSim />
      </section>

      <section
        aria-labelledby="method"
        className="mx-auto flex max-w-6xl flex-col gap-10 px-4 pt-24"
      >
        <SectionHead id="method" eyebrow="How a case works" title="Run it, fix it, prove it">
          Every case is a short Python program with one bug in it and no dependencies to install.
          Here is case 06 from start to finish.
        </SectionHead>
        <ol className="grid gap-4 lg:grid-cols-3 [&>*]:min-w-0">
          {[
            {
              step: 'Run it',
              command: 'uv run python -m dock run 6',
              lines: CASE_SIX.run,
              tone: 'text-code-fail',
              note: 'The app is up and listening. Nobody outside can reach it.',
            },
            {
              step: 'Fix it',
              command: 'lab/cases/case06_localhost.py',
              lines: CASE_SIX.fix,
              tone: 'text-code-ink',
              note: 'Listen where published ports and other containers arrive.',
            },
            {
              step: 'Prove it',
              command: 'uv run python -m dock check 6',
              lines: CASE_SIX.check,
              tone: 'text-code-pass',
              note: 'Reachable from the laptop and the worker, still isolated.',
            },
          ].map((card, index) => (
            <li key={card.step} className="flex flex-col gap-3">
              <div className="flex items-baseline gap-3">
                <span className="display text-[28px] leading-none text-signal">{index + 1}</span>
                <span className="text-[17px] font-semibold text-ink">{card.step}</span>
              </div>
              <div className="code flex flex-1 flex-col overflow-hidden rounded-[4px]">
                <div className="truncate border-b border-code-rule px-3.5 py-2 text-[12px] text-code-muted">
                  {card.command}
                </div>
                <pre
                  className={`px-3.5 py-3 text-[12.5px] leading-relaxed whitespace-pre-wrap [overflow-wrap:anywhere] ${card.tone}`}
                >
                  {card.lines.join('\n')}
                </pre>
              </div>
              <p className="text-[14.5px] text-ink-2">{card.note}</p>
            </li>
          ))}
        </ol>
      </section>

      <section
        aria-labelledby="measured"
        className="mx-auto flex max-w-6xl flex-col gap-10 px-4 pt-24"
      >
        <SectionHead
          id="measured"
          eyebrow="Measured, not guessed"
          title="Real processes, real sockets"
        >
          Two of the four experiments, run on a real machine with no Docker at all. The same rules
          apply inside a container, with one twist each.
        </SectionHead>
        <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
          <figure className="plate overflow-hidden">
            <figcaption className="flex flex-col gap-0.5 border-b border-rule bg-surface-2 px-4 py-3">
              <span className="display text-[19px] text-ink">SIGTERM, then SIGKILL after 2 s</span>
              <span className="font-mono text-[12px] text-muted">dock try stop</span>
            </figcaption>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[30rem] text-[14px]">
                <thead>
                  <tr className="border-b border-rule text-left font-mono text-[11.5px] tracking-[0.06em] text-ink-2 uppercase">
                    <th scope="col" className="px-4 py-2.5 font-semibold">
                      How the worker runs
                    </th>
                    <th scope="col" className="px-3 py-2.5 text-right font-semibold">
                      Stop took
                    </th>
                    <th scope="col" className="px-4 py-2.5 font-semibold">
                      The worker
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {MEASURED.stop.map((row) => (
                    <tr key={row.label} className="border-b border-rule last:border-0">
                      <th
                        scope="row"
                        className="px-4 py-2.5 text-left font-mono text-[12.5px] font-normal text-ink"
                      >
                        {row.label}
                      </th>
                      <td className="px-3 py-2.5 text-right font-mono text-[13px] text-ink-2">
                        {row.took}
                      </td>
                      <td
                        className={`px-4 py-2.5 text-[13.5px] font-medium ${row.good ? 'text-pass' : 'text-fail'}`}
                      >
                        <span className="inline-flex items-center gap-1.5">
                          <svg width="12" height="12" viewBox="0 0 14 14" aria-hidden="true">
                            {row.good ? (
                              <path
                                d="M2.5 7.5l3 3 6-7"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2.2"
                              />
                            ) : (
                              <path
                                d="M3 3l8 8M11 3l-8 8"
                                stroke="currentColor"
                                strokeWidth="2.2"
                                strokeLinecap="round"
                              />
                            )}
                          </svg>
                          {row.worker}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </figure>
          <figure className="plate overflow-hidden">
            <figcaption className="flex flex-col gap-0.5 border-b border-rule bg-surface-2 px-4 py-3">
              <span className="display text-[19px] text-ink">Packing a build context</span>
              <span className="font-mono text-[12px] text-muted">dock try context</span>
            </figcaption>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[24rem] text-[14px]">
                <thead>
                  <tr className="border-b border-rule text-left font-mono text-[11.5px] tracking-[0.06em] text-ink-2 uppercase">
                    <th scope="col" className="px-4 py-2.5 font-semibold">
                      Context
                    </th>
                    <th scope="col" className="px-3 py-2.5 text-right font-semibold">
                      Files
                    </th>
                    <th scope="col" className="px-3 py-2.5 text-right font-semibold">
                      Size
                    </th>
                    <th scope="col" className="px-4 py-2.5 text-right font-semibold">
                      Tar + hash
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {MEASURED.context.map((row, index) => (
                    <tr key={row.label} className="border-b border-rule last:border-0">
                      <th scope="row" className="px-4 py-2.5 text-left font-medium text-ink">
                        {row.label}
                      </th>
                      <td className="px-3 py-2.5 text-right font-mono text-[13px] text-ink-2">
                        {row.files}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono text-[13px] text-ink-2">
                        {row.size}
                      </td>
                      <td
                        className={`px-4 py-2.5 text-right font-mono text-[13px] font-semibold ${index === 0 ? 'text-work' : 'text-pass'}`}
                      >
                        {row.time}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="border-t border-rule px-4 py-3 text-[13.5px] leading-relaxed text-ink-2">
              Leaving out .git, node_modules and two data dumps cuts the work before every build
              from {MEASURED.context[0]?.time} to {MEASURED.context[1]?.time}.
            </p>
          </figure>
        </div>
        <p className="max-w-2xl text-[14.5px] leading-relaxed text-muted">
          Measured on {MEASURED.machine}. Your numbers will differ. Chapters 02 and 05 explain each
          row, and <code className="font-mono text-[13px] text-ink">dock try ports</code> and{' '}
          <code className="font-mono text-[13px] text-ink">dock try digest</code> are in chapters 06
          and 04.
        </p>
      </section>

      <section
        aria-labelledby="checklist"
        className="mx-auto flex max-w-6xl flex-col gap-10 px-4 pt-24"
      >
        <SectionHead id="checklist" eyebrow="Keep this" title="The container checklist">
          Eleven rules, one for every way a container went wrong in the workshop.
        </SectionHead>
        <ol className="grid gap-x-12 md:grid-cols-2">
          {CHECKLIST.map((item, index) => (
            <li
              key={item}
              className="flex gap-4 border-t border-rule py-4 text-[16px] leading-relaxed text-ink"
            >
              <span className="w-7 shrink-0 font-mono text-[15px] leading-7 font-semibold text-layer">
                {String(index + 1).padStart(2, '0')}
              </span>
              {item}
            </li>
          ))}
        </ol>
      </section>

      <section
        id="start"
        aria-labelledby="start-title"
        className="mx-auto grid max-w-6xl scroll-mt-6 gap-10 px-4 pt-24 pb-28 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-center [&>*]:min-w-0"
      >
        <div className="flex flex-col gap-6">
          <SectionHead id="start-title" eyebrow="Quick start" title="Ten minutes to your first fix">
            You need uv and git. uv installs Python for you, the lab uses the standard library only,
            and none of it needs Docker.
          </SectionHead>
          <div className="code overflow-hidden rounded-[4px]">
            <div className="flex items-center justify-between border-b border-code-rule py-1 pr-1 pl-4">
              <span className="text-[11.5px] font-semibold tracking-[0.1em] text-code-muted uppercase">
                Shell
              </span>
              <CopyButton text={QUICKSTART} />
            </div>
            <pre className="overflow-x-auto px-4 py-3.5 text-[13px] leading-relaxed">
              {QUICKSTART}
            </pre>
          </div>
          <p className="text-[14.5px] text-ink-2">
            Then <code className="font-mono text-[13px] text-ink">uv run python -m dock list</code>{' '}
            shows every case, and{' '}
            <a
              href={REPO_URL}
              className="font-medium text-ink underline decoration-signal-fill decoration-2 underline-offset-3"
            >
              the README
            </a>{' '}
            has every command.
          </p>
        </div>
        <figure className="flex flex-col items-center gap-4 sm:flex-row sm:items-end lg:justify-center">
          <Pip className="w-52 shrink-0 sm:w-60" />
          <figcaption className="plate relative max-w-xs border-t-[3px] border-t-signal-fill p-4 text-[16px] leading-relaxed text-ink">
            <span className="mb-1 block font-mono text-[12px] font-semibold tracking-[0.1em] text-signal uppercase">
              Pip
            </span>
            Stuck on a case? Ask me in the corner of any page, or run{' '}
            <code className="font-mono text-[13px]">dock hint 1</code>. I live in a container. I
            know where the walls are.
          </figcaption>
        </figure>
      </section>
    </>
  )
}
