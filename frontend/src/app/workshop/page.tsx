import type { Metadata } from 'next'

import { ChapterList } from '@/components/ChapterList'
import { CHAPTERS } from '@/lib/workshop'

export const metadata: Metadata = { title: 'Chapters' }

export default function Workshop() {
  const minutes = CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-12 px-4 pt-14 pb-24">
      <header className="flex max-w-3xl flex-col gap-4">
        <span className="eyebrow">
          {CHAPTERS.length} chapters · {minutes} minutes
        </span>
        <h1 className="text-[40px] leading-[1.1] font-bold tracking-[-0.025em] sm:text-[48px]">
          The chapters
        </h1>
        <p className="text-[18px] leading-relaxed text-ink-2">
          Work through them in order: each level builds on the one before. Every chapter ends with
          an exercise you fix and a checker that proves it, using real Docker.
        </p>
      </header>
      <ChapterList />
    </div>
  )
}
