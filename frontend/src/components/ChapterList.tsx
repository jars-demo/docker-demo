import Link from 'next/link'

import { Inline } from '@/components/Inline'
import { LEVELS, SYMPTOMS } from '@/lib/site'
import { CHAPTERS } from '@/lib/workshop'

// The twelve chapters, grouped into the three levels, each with the real symptom of its bug.

export function ChapterList() {
  return (
    <div className="flex flex-col gap-12">
      {LEVELS.map((level, index) => {
        const chapters = CHAPTERS.filter((chapter) =>
          level.chapters.includes(Number(chapter.number)),
        )
        const minutes = chapters.reduce((sum, chapter) => sum + chapter.minutes, 0)
        return (
          <section
            key={level.name}
            aria-labelledby={`level-${index}`}
            className="flex flex-col gap-4"
          >
            <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
              <h3 id={`level-${index}`} className="text-[20px] font-semibold tracking-[-0.01em]">
                <span className="mr-2 font-mono text-[13px] text-blue-text">Level {index + 1}</span>
                {level.name}
              </h3>
              <p className="text-[14px] text-muted">
                {chapters.length} chapters, {minutes} minutes
              </p>
            </div>
            <p className="max-w-2xl text-[15px] text-ink-2">{level.about}</p>
            <ol className="grid gap-3 md:grid-cols-2">
              {chapters.map((chapter) => (
                <li key={chapter.slug}>
                  <Link
                    href={`/workshop/${chapter.slug}`}
                    className="card group flex h-full flex-col gap-3 p-4 hover:border-blue sm:p-5"
                  >
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="font-mono text-[13px] text-blue-text">{chapter.number}</span>
                      <span className="text-[13px] text-muted">{chapter.minutes} min</span>
                    </div>
                    <h4 className="text-[18px] leading-snug font-semibold text-ink group-hover:text-blue-text">
                      {chapter.title}
                    </h4>
                    <p className="text-[14.5px] leading-relaxed text-ink-2">
                      <Inline text={chapter.summary} />
                    </p>
                    <code className="mt-auto block rounded bg-code-bg px-3 py-2 font-mono text-[12.5px] leading-relaxed whitespace-pre-wrap text-code-fail [overflow-wrap:anywhere]">
                      {SYMPTOMS[chapter.number]}
                    </code>
                  </Link>
                </li>
              ))}
            </ol>
          </section>
        )
      })}
    </div>
  )
}
