import Link from 'next/link'

import { REPO_URL } from '@/lib/site'

import { Companion } from './Companion'

// The harbour header, the footer and Pip, shared by every page.

export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="4" fill="#143149" />
      <rect x="6" y="19" width="20" height="6" rx="1" fill="#1d5a85" />
      <rect x="8" y="12" width="18" height="6" rx="1" fill="#4a86b3" />
      <rect x="10" y="5" width="16" height="6" rx="1" fill="#ff8a3d" />
    </svg>
  )
}

const NAV = [
  { href: '/workshop', label: 'Chapters', phone: true },
  { href: '/#build', label: 'The build', phone: false },
]

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="on-navy border-b border-navy-line bg-navy text-on-navy">
        <nav
          aria-label="Main"
          className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4"
        >
          <Link href="/" className="inline-flex min-h-10 items-center gap-2.5 rounded">
            <LogoMark />
            <span className="display text-[21px] leading-none">Docker</span>
            <span className="hidden pt-0.5 font-mono text-[12px] tracking-[0.08em] text-on-navy-muted uppercase sm:inline">
              without the magic
            </span>
          </Link>
          <ul className="flex items-center gap-1">
            {NAV.map((item) => (
              <li key={item.href} className={item.phone ? '' : 'hidden sm:block'}>
                <Link
                  href={item.href}
                  className="inline-flex h-10 items-center rounded-[4px] px-3.5 text-[14.5px] font-medium text-on-navy hover:bg-navy-2"
                >
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <a
                href={REPO_URL}
                className="ml-1 inline-flex h-10 items-center rounded-[4px] border border-signal-fill px-4 text-[14.5px] font-medium text-signal-fill hover:bg-signal-fill hover:text-navy"
              >
                GitHub
              </a>
            </li>
          </ul>
        </nav>
      </header>
      <main id="main" className="flex-1">
        {children}
      </main>
      <footer className="on-navy border-t-[3px] border-signal-fill bg-navy text-on-navy-muted">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 pt-7 pb-24 text-[13.5px] sm:flex-row sm:justify-between">
          <span>Docker without the magic · MIT licensed</span>
          <a href={REPO_URL} className="inline-flex min-h-10 items-center hover:text-on-navy">
            Source on GitHub
          </a>
        </div>
      </footer>
      <Companion />
    </>
  )
}
