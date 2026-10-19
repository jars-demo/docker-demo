import type { Metadata, Viewport } from 'next'
import { Roboto_Flex, Roboto_Mono } from 'next/font/google'

import { Shell } from '@/components/Shell'
import { SITE_URL, TAGLINE, TITLE } from '@/lib/site'

import './globals.css'

const sans = Roboto_Flex({ variable: '--font-roboto-flex', subsets: ['latin'], axes: ['opsz'] })
const mono = Roboto_Mono({ variable: '--font-roboto-mono', subsets: ['latin'] })

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: TITLE, template: `%s · ${TITLE}` },
  description: TAGLINE,
}

export const viewport: Viewport = {
  themeColor: '#00084d',
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
}

export default function RootLayout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <a
          href="#main"
          className="sr-only rounded bg-navy px-4 py-2 text-on-navy focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50"
        >
          Skip to content
        </a>
        <Shell>{children}</Shell>
      </body>
    </html>
  )
}
