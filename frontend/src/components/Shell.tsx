import Link from 'next/link'

import { BackToTop } from '@/components/BackToTop'
import { Mark } from '@/components/Mark'
import { REPO_URL, SHORT_TITLE } from '@/lib/site'

function GitHub() {
  return (
    <svg viewBox="0 0 16 16" className="size-[18px]" aria-hidden="true">
      <path
        fill="currentColor"
        d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
      />
    </svg>
  )
}

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="on-navy sticky top-0 z-40 bg-navy text-on-navy">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4">
          <Link href="/" className="flex min-w-0 items-center gap-2.5">
            <Mark className="size-8 shrink-0" />
            <span className="hidden truncate text-[16px] font-semibold tracking-[-0.01em] sm:inline">
              {SHORT_TITLE}
            </span>
            <span className="text-[16px] font-semibold tracking-[-0.01em] sm:hidden">
              Docker workshop
            </span>
          </Link>
          <nav aria-label="Main" className="flex shrink-0 items-center gap-1 text-[15px]">
            <Link
              href="/workshop"
              className="inline-flex h-10 items-center rounded-md px-3 text-on-navy-muted hover:bg-navy-2 hover:text-on-navy"
            >
              Chapters
            </Link>
            <a
              href={REPO_URL}
              className="inline-flex h-10 items-center gap-2 rounded-md px-3 text-on-navy-muted hover:bg-navy-2 hover:text-on-navy"
            >
              <GitHub />
              <span className="hidden sm:inline">GitHub</span>
              <span className="sr-only sm:hidden">GitHub</span>
            </a>
          </nav>
        </div>
      </header>
      <main id="main" className="flex-1">
        {children}
      </main>
      <footer className="border-t border-rule bg-canvas-2">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-10 text-[14px] text-muted sm:flex-row sm:items-center sm:justify-between">
          <p className="flex items-center gap-2">
            <Mark className="size-5" />
            {SHORT_TITLE}. An independent, open-source workshop. MIT licensed.
          </p>
          <p>Not affiliated with Docker, Inc. Docker is a trademark of Docker, Inc.</p>
        </div>
      </footer>
      <div className="fixed right-[max(1rem,env(safe-area-inset-right))] bottom-[max(1rem,env(safe-area-inset-bottom))] z-30">
        <BackToTop />
      </div>
    </>
  )
}
