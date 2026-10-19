import { describe, expect, it } from 'vitest'

import { build, installSeconds, start, verdict } from '@/lib/cache'

const states = (state: ReturnType<typeof start>) => state.last?.rows.map((row) => row.state)

describe('the build cache simulator', () => {
  it('runs every step on the first build', () => {
    const first = build(start('shipped'))

    expect(states(first)).toEqual(['base', 'ran', 'ran', 'ran', 'ran'])
  })

  it('reinstalls after a code change when COPY . . comes first', () => {
    const rebuilt = build(build(start('shipped')), 'app/main.py')

    expect(states(rebuilt)).toEqual(['base', 'cached', 'ran', 'ran', 'ran'])
    expect(verdict(rebuilt)).toContain('pip install ran again anyway')
  })

  it('keeps the install cached after a code change when requirements are copied first', () => {
    const rebuilt = build(build(start('fixed')), 'app/main.py')

    expect(states(rebuilt)).toEqual(['base', 'cached', 'cached', 'cached', 'ran', 'ran'])
    expect(verdict(rebuilt)).toContain('came from the cache')
  })

  it('reinstalls when requirements.txt changes, in both orders', () => {
    expect(build(build(start('fixed')), 'requirements.txt').last?.installRan).toBe(true)
    expect(build(build(start('shipped')), 'requirements.txt').last?.installRan).toBe(true)
  })

  it('counts the seconds spent in pip install with the measured time', () => {
    const twice = build(build(start('shipped')), 'app/main.py')

    expect(installSeconds(twice)).toBe(12.4)
  })
})
