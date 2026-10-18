import type { Metadata, Viewport } from 'next'
import { Bricolage_Grotesque, Instrument_Sans, Red_Hat_Mono } from 'next/font/google'

import { Shell } from '@/components/Shell'
import { SITE_URL } from '@/lib/site'

import './globals.css'

const display = Bricolage_Grotesque({
  variable: '--font-bricolage',
  subsets: ['latin'],
  axes: ['opsz', 'wdth'],
})
const sans = Instrument_Sans({ variable: '--font-instrument', subsets: ['latin'], axes: ['wdth'] })
const mono = Red_Hat_Mono({ variable: '--font-redhat-mono', subsets: ['latin'] })

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'Docker without the magic',
    template: '%s · Docker without the magic',
  },
  description:
    'A hands-on Docker workshop: nine real container bugs in one small tea shop. Layers and the build cache, secrets in layers, multi-stage builds, tags and digests, PID 1, networking, healthchecks, volumes and cgroup limits.',
}

export const viewport: Viewport = { themeColor: '#0b2133' }

export default function RootLayout({ children }: LayoutProps<'/'>) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${sans.variable} ${mono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col">
        <a
          href="#main"
          className="sr-only rounded bg-ink px-4 py-2 text-surface focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50"
        >
          Skip to content
        </a>
        <Shell>{children}</Shell>
      </body>
    </html>
  )
}
