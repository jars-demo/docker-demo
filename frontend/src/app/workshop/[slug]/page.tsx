import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { CopyButton } from '@/components/CopyButton'
import { headingsOf, Markdown } from '@/components/Markdown'
import { CASES } from '@/lib/site'
import { type Chapter, CHAPTERS, findChapter } from '@/lib/workshop'

export function generateStaticParams() {
  return CHAPTERS.map((chapter) => ({ slug: chapter.slug }))
}

export async function generateMetadata(props: PageProps<'/workshop/[slug]'>): Promise<Metadata> {
  const { slug } = await props.params
  const chapter = findChapter(slug)
  return { title: chapter ? `${chapter.number}. ${chapter.title}` : 'Chapter' }
}

function Outline({ chapter }: { chapter: Chapter }) {
  return (
    <ul className="flex flex-col gap-1.5 text-[14px]">
      {headingsOf(chapter.body).map((heading) => (
        <li key={heading.id}>
          <a
            href={`#${heading.id}`}
            className="inline-flex min-h-8 items-center text-ink-2 hover:text-ink hover:underline"
          >
            {heading.text}
          </a>
        </li>
      ))}
    </ul>
  )
}

function Chapters({ current }: { current: Chapter }) {
  return (
    <ol className="flex flex-col gap-1 text-[14px]">
      {CHAPTERS.map((chapter) => {
        const here = chapter.slug === current.slug
        return (
          <li key={chapter.slug}>
            <Link
              href={`/workshop/${chapter.slug}`}
              aria-current={here ? 'page' : undefined}
              className={`flex gap-2.5 rounded-[3px] px-2 py-1.5 ${
                here ? 'bg-surface-2 font-semibold text-ink' : 'text-ink-2 hover:text-ink'
              }`}
            >
              <span className="w-5 shrink-0 font-mono text-layer">{chapter.number}</span>
              {chapter.title}
            </Link>
          </li>
        )
      })}
    </ol>
  )
}

export default async function ChapterPage(props: PageProps<'/workshop/[slug]'>) {
  const { slug } = await props.params
  const chapter = findChapter(slug)
  if (!chapter) notFound()
  const index = CHAPTERS.indexOf(chapter)
  const previous = CHAPTERS[index - 1]
  const next = CHAPTERS[index + 1]
  const item = CASES.find((c) => c.number === chapter.number)
  const n = Number(chapter.number)
  const commands = `uv run python -m dock run ${n}\nuv run python -m dock check ${n}\nuv run python -m dock hint ${n}`

  return (
    <div className="mx-auto max-w-6xl px-4 pt-10 pb-24">
      <nav aria-label="Breadcrumb" className="text-[14px] text-muted">
        <Link
          href="/workshop"
          className="inline-flex min-h-10 items-center hover:text-ink hover:underline"
        >
          Chapters
        </Link>
        <span aria-hidden="true"> / </span>
        <span className="text-ink-2">{chapter.number}</span>
      </nav>

      <header className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem] lg:gap-14">
        <div className="flex min-w-0 flex-col gap-4">
          <span className="eyebrow">
            Chapter {chapter.number} · {chapter.minutes} minutes
          </span>
          <h1 className="display text-[42px] leading-[1.02] text-balance sm:text-[58px]">
            {chapter.title}
          </h1>
          <p className="max-w-2xl text-[20px] leading-relaxed text-ink-2">{chapter.summary}</p>
        </div>
        {item ? (
          <aside
            aria-label={`Case ${chapter.number}`}
            className="plate min-w-0 self-end border-t-[3px] border-t-fail p-4"
          >
            <div className="flex items-baseline justify-between gap-3 border-b border-rule pb-2">
              <span className="font-mono text-[12px] font-semibold tracking-[0.1em] text-signal uppercase">
                Case {chapter.number}
              </span>
              <span className="text-[12px] text-muted">what you will see</span>
            </div>
            <p className="display mt-3 text-[19px] leading-snug text-ink">{item.title}</p>
            <pre className="mt-3 flex gap-2 rounded-[3px] bg-fail-wash px-3 py-2 font-mono text-[12.5px] leading-relaxed whitespace-pre-wrap text-fail [overflow-wrap:anywhere]">
              <svg
                width="12"
                height="12"
                viewBox="0 0 14 14"
                aria-hidden="true"
                className="mt-1 shrink-0"
              >
                <path
                  d="M3 3l8 8M11 3l-8 8"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                />
              </svg>
              <span className="sr-only">Symptom: </span>
              <span className="min-w-0">{item.symptom}</span>
            </pre>
          </aside>
        ) : null}
      </header>

      <div className="mt-12 grid gap-10 border-t border-rule pt-4 lg:grid-cols-[minmax(0,1fr)_14rem] lg:gap-14">
        <article className="min-w-0">
          <details className="plate mt-4 lg:hidden">
            <summary className="flex min-h-11 cursor-pointer items-center px-4 text-[14.5px] font-semibold">
              On this page
            </summary>
            <div className="border-t border-rule px-4 py-3">
              <Outline chapter={chapter} />
            </div>
          </details>

          <div className="prose-dock max-w-[42rem]">
            <Markdown>{chapter.body}</Markdown>
          </div>

          <section
            aria-labelledby="commands"
            className="code mt-14 max-w-[42rem] overflow-hidden rounded-[4px]"
          >
            <div className="flex items-center justify-between border-b border-code-rule py-1 pr-1 pl-4">
              <h2
                id="commands"
                className="text-[11.5px] font-semibold tracking-[0.1em] text-code-muted uppercase"
              >
                Chapter {chapter.number} · commands, from lab/
              </h2>
              <CopyButton text={commands} />
            </div>
            <pre className="overflow-x-auto px-4 py-4 text-[13px] leading-relaxed">{commands}</pre>
          </section>

          <nav
            aria-label="Previous and next"
            className="mt-8 grid max-w-[42rem] gap-3 sm:grid-cols-2"
          >
            {previous ? (
              <Link
                href={`/workshop/${previous.slug}`}
                className="plate flex flex-col gap-1 p-4 hover:border-signal"
              >
                <span className="eyebrow">Previous</span>
                <span className="display text-[18px]">
                  {previous.number}. {previous.title}
                </span>
              </Link>
            ) : (
              <span />
            )}
            {next ? (
              <Link
                href={`/workshop/${next.slug}`}
                className="plate flex flex-col gap-1 p-4 text-right hover:border-signal"
              >
                <span className="eyebrow">Next</span>
                <span className="display text-[18px]">
                  {next.number}. {next.title}
                </span>
              </Link>
            ) : (
              <Link
                href="/#checklist"
                className="plate flex flex-col gap-1 p-4 text-right hover:border-signal"
              >
                <span className="eyebrow">All nine fixed</span>
                <span className="display text-[18px]">The container checklist</span>
              </Link>
            )}
          </nav>
        </article>

        <aside className="hidden lg:block">
          <div className="sticky top-6 flex flex-col gap-8 pt-6">
            <nav aria-label="On this page" className="flex flex-col gap-3">
              <span className="eyebrow">On this page</span>
              <Outline chapter={chapter} />
            </nav>
            <nav aria-label="Chapters" className="flex flex-col gap-3">
              <span className="eyebrow">Chapters</span>
              <Chapters current={chapter} />
            </nav>
          </div>
        </aside>
      </div>
    </div>
  )
}
