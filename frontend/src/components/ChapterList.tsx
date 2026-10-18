import Link from 'next/link'

import { CASES } from '@/lib/site'
import { CHAPTERS } from '@/lib/workshop'

// The chapters as a cargo manifest: one row per chapter, with its case and the symptom you will
// see when you run it. The symptom is real lab output, set in red because it is a failure.

export function ChapterList() {
  return (
    <ol className="plate divide-y divide-rule overflow-hidden">
      {CHAPTERS.map((chapter) => {
        const item = CASES.find((c) => c.number === chapter.number)
        return (
          <li key={chapter.slug}>
            <Link
              href={`/workshop/${chapter.slug}`}
              className="group grid grid-cols-[2.5rem_minmax(0,1fr)] gap-x-4 gap-y-2 px-4 py-4 hover:bg-surface-2 sm:grid-cols-[3.25rem_minmax(0,1fr)_4.5rem] sm:px-5 lg:grid-cols-[3.25rem_minmax(0,1fr)_minmax(0,24rem)_4.5rem] lg:items-center"
            >
              <span className="display pt-0.5 text-[26px] leading-none text-layer">
                {chapter.number}
              </span>
              <span className="flex min-w-0 flex-col gap-1">
                <span className="display text-[20px] leading-snug text-ink group-hover:underline group-hover:decoration-signal-fill group-hover:decoration-2 group-hover:underline-offset-4">
                  {chapter.title}
                </span>
                <span className="text-[14.5px] text-ink-2">
                  Case {chapter.number}: {item?.title}
                </span>
                <span className="text-[13px] text-muted">{item?.topics}</span>
              </span>
              <span className="col-start-2 flex min-w-0 items-start gap-2 lg:col-start-auto">
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 14 14"
                  aria-hidden="true"
                  className="mt-1 shrink-0 text-fail"
                >
                  <path
                    d="M3 3l8 8M11 3l-8 8"
                    stroke="currentColor"
                    strokeWidth="2.2"
                    strokeLinecap="round"
                  />
                </svg>
                <span className="sr-only">Symptom:</span>
                <code className="min-w-0 font-mono text-[12.5px] leading-snug text-fail [overflow-wrap:anywhere]">
                  {item?.symptom}
                </code>
              </span>
              <span className="col-start-2 font-mono text-[12.5px] text-muted sm:col-start-auto sm:row-start-1 sm:text-right lg:row-start-auto">
                {chapter.minutes} min
              </span>
            </Link>
          </li>
        )
      })}
    </ol>
  )
}
