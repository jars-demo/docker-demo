import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { CopyButton } from '@/components/CopyButton'
import { headingsOf, Markdown } from '@/components/Markdown'
import { Inline } from '@/components/Inline'
import { Quiz } from '@/components/Quiz'
import { QUIZ } from '@/lib/quiz'
import { LEVELS } from '@/lib/site'
import { type Chapter, CHAPTERS, findChapter } from '@/lib/workshop'

export function generateStaticParams() {
  return CHAPTERS.map((chapter) => ({ slug: chapter.slug }))
}

export async function generateMetadata(props: PageProps<'/workshop/[slug]'>): Promise<Metadata> {
  const { slug } = await props.params
  const chapter = findChapter(slug)
  return { title: chapter ? `${chapter.number}. ${chapter.title}` : 'Chapter' }
}

function Contents({ current }: { current: Chapter }) {
  return (
    <nav aria-label="Chapters" className="flex flex-col gap-5 text-[14px]">
      {LEVELS.map((level) => (
        <div key={level.name} className="flex flex-col gap-1">
          <span className="px-2 pb-1 font-mono text-[11px] tracking-[0.08em] text-muted uppercase">
            {level.name}
          </span>
          <ol className="flex flex-col gap-0.5">
            {CHAPTERS.filter((chapter) => level.chapters.includes(Number(chapter.number))).map(
              (chapter) => {
                const here = chapter.slug === current.slug
                return (
                  <li key={chapter.slug}>
                    <Link
                      href={`/workshop/${chapter.slug}`}
                      aria-current={here ? 'page' : undefined}
                      className={`flex gap-2.5 rounded-md px-2 py-1.5 ${
                        here
                          ? 'bg-blue-wash font-semibold text-ink'
                          : 'text-ink-2 hover:bg-canvas-2 hover:text-ink'
                      }`}
                    >
                      <span className="w-5 shrink-0 font-mono text-blue-text">
                        {chapter.number}
                      </span>
                      {chapter.title}
                    </Link>
                  </li>
                )
              },
            )}
          </ol>
        </div>
      ))}
    </nav>
  )
}

function Command({ text }: { text: string }) {
  return (
    <div className="terminal flex items-center justify-between gap-2 py-1 pr-1 pl-3.5 text-[13.5px]">
      <code className="min-w-0 overflow-x-auto py-1.5 whitespace-nowrap">
        <span className="text-code-blue">$ </span>
        {text}
      </code>
      <CopyButton text={text} label={`Copy ${text}`} />
    </div>
  )
}

export default async function ChapterPage(props: PageProps<'/workshop/[slug]'>) {
  const { slug } = await props.params
  const chapter = findChapter(slug)
  if (!chapter) notFound()
  const index = CHAPTERS.indexOf(chapter)
  const previous = CHAPTERS[index - 1]
  const next = CHAPTERS[index + 1]
  const number = Number(chapter.number)

  return (
    <div className="mx-auto grid max-w-6xl gap-10 px-4 pt-10 pb-24 lg:grid-cols-[230px_minmax(0,1fr)] xl:grid-cols-[230px_minmax(0,1fr)_200px]">
      <aside className="hidden lg:block">
        <div className="sticky top-24">
          <Contents current={chapter} />
        </div>
      </aside>

      <article className="flex min-w-0 flex-col gap-8">
        <header className="flex flex-col gap-4 border-b border-rule pb-8">
          <span className="eyebrow">
            Chapter {chapter.number} · {chapter.level} · {chapter.minutes} minutes
          </span>
          <h1 className="text-[36px] leading-[1.1] font-bold tracking-[-0.025em] text-balance sm:text-[44px]">
            {chapter.title}
          </h1>
          <p className="text-[19px] leading-relaxed text-ink-2">
            <Inline text={chapter.summary} />
          </p>
          <div className="flex flex-col gap-2 rounded-lg border border-rule bg-canvas-2 p-4">
            <span className="text-[14px] text-ink-2">
              Exercise in{' '}
              <code className="font-mono text-[13px] text-ink">lab/exercises/{chapter.slug}</code>,
              from <code className="font-mono text-[13px] text-ink">lab/</code>:
            </span>
            <Command text={`uv run python -m dock run ${number}`} />
            <Command text={`uv run python -m dock check ${number}`} />
          </div>
        </header>

        <div className="prose-docker">
          <Markdown>{chapter.body}</Markdown>
        </div>

        {QUIZ[chapter.number] ? <Quiz questions={QUIZ[chapter.number] ?? []} /> : null}

        <nav aria-label="Chapter navigation" className="grid gap-3 sm:grid-cols-2">
          {previous ? (
            <Link
              href={`/workshop/${previous.slug}`}
              className="card flex flex-col gap-1 p-4 hover:border-blue"
            >
              <span className="text-[13px] text-muted">Previous</span>
              <span className="font-semibold text-ink">
                {previous.number}. {previous.title}
              </span>
            </Link>
          ) : (
            <span />
          )}
          {next ? (
            <Link
              href={`/workshop/${next.slug}`}
              className="card flex flex-col gap-1 p-4 text-right hover:border-blue"
            >
              <span className="text-[13px] text-muted">Next</span>
              <span className="font-semibold text-ink">
                {next.number}. {next.title}
              </span>
            </Link>
          ) : null}
        </nav>
      </article>

      <aside className="hidden xl:block">
        <div className="sticky top-24 flex flex-col gap-3">
          <span className="font-mono text-[11px] tracking-[0.08em] text-muted uppercase">
            On this page
          </span>
          <ul className="flex flex-col gap-1.5 text-[14px]">
            {headingsOf(chapter.body).map((heading) => (
              <li key={heading.id}>
                <a href={`#${heading.id}`} className="text-ink-2 hover:text-blue-text">
                  {heading.text}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  )
}
