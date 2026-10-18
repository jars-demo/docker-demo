import fs from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { contrast, TEXT_PAIRS, TOKENS } from '@/lib/tokens'

const css = fs.readFileSync(path.join(process.cwd(), 'src/app/globals.css'), 'utf8')
const cssName = (token: string) => `--${token.replace(/([A-Z0-9])/g, '-$1').toLowerCase()}`

describe('colour tokens', () => {
  it.each(Object.entries(TOKENS))('%s mirrors globals.css', (token, value) => {
    expect(css).toContain(`${cssName(token)}: ${value};`)
  })

  it.each(TEXT_PAIRS)('%s text on %s meets WCAG AA', (fg, bg) => {
    expect(contrast(TOKENS[fg], TOKENS[bg])).toBeGreaterThanOrEqual(4.5)
  })
})
