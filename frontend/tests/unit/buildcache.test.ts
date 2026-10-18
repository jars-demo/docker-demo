import fs from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import {
  build,
  edit,
  FIRST,
  FIXED,
  move,
  reinstalledForNothing,
  SHIPPED,
  STEPS,
} from '@/lib/buildcache'

const chapter = fs.readFileSync(
  path.join(process.cwd(), '..', 'workshop', '01-layers-and-the-cache.md'),
  'utf8',
)
const engine = fs.readFileSync(path.join(process.cwd(), '..', 'lab', 'dock', 'engine.py'), 'utf8')

function twice(order: typeof SHIPPED, file: 'app.py' | 'requirements.txt') {
  const first = build(order, FIRST, new Set())
  const second = build(order, edit(FIRST, file), first.cache)
  return { first: first.result, second: second.result }
}

describe('the build cache simulator', () => {
  it('runs every step on an empty cache, except pulling the base image', () => {
    const { result } = build(SHIPPED, FIRST, new Set())
    expect(result.rows.map((row) => row.cached)).toEqual([true, false, false, false, false])
    expect(result.error).toBeNull()
  })

  it('as shipped, an edit to app.py reinstalls every package, as chapter 01 shows', () => {
    const { first, second } = twice(SHIPPED, 'app.py')
    expect(chapter).toContain(`first build, empty cache:    ${first.seconds.toFixed(1)} s`)
    expect(chapter).toContain(`rebuild after a one-line edit: ${second.seconds.toFixed(1)} s`)
    expect(second.rows.map((row) => [row.text, row.cached])).toEqual([
      ['FROM python:3.13-slim', true],
      ['WORKDIR /app', true],
      ['COPY . .', false],
      ['RUN pip install -r requirements.txt', false],
      ['CMD ["gunicorn", "app:app"]', false],
    ])
    expect(reinstalledForNothing(second, 'app.py')).toBe(true)
  })

  it('fixed, an edit to app.py only runs the last COPY, as the chapter 01 check shows', () => {
    const { second } = twice(FIXED, 'app.py')
    expect(chapter).toContain(`rebuilds in under 5 s (took ${second.seconds.toFixed(1)} s)`)
    expect(second.rows.filter((row) => !row.cached).map((row) => row.text)).toEqual([
      'COPY . .',
      'CMD ["gunicorn", "app:app"]',
    ])
    expect(reinstalledForNothing(second, 'app.py')).toBe(false)
  })

  it('fixed, a change to requirements.txt still reinstalls', () => {
    const { second } = twice(FIXED, 'requirements.txt')
    expect(second.rows.find((row) => row.id === 'install')?.cached).toBe(false)
    expect(reinstalledForNothing(second, 'requirements.txt')).toBe(false)
  })

  it('a rebuild with nothing changed is all cache hits', () => {
    const first = build(FIXED, FIRST, new Set())
    const again = build(FIXED, FIRST, first.cache)
    expect(again.result.rows.every((row) => row.cached)).toBe(true)
    expect(again.result.seconds).toBe(0)
  })

  it('fails like pip when the install comes before requirements.txt is copied', () => {
    const order = move(SHIPPED, 'install', -1)
    expect(order).toEqual(['from', 'workdir', 'install', 'copyAll', 'cmd'])
    const { result, cache } = build(order, FIRST, new Set())
    expect(result.error).toBe('pip: could not open requirements file: /app/requirements.txt')
    expect(engine).toContain('pip: could not open requirements file')
    expect(cache.size).toBe(0)
  })

  it('keeps FROM first, and does not move past either end', () => {
    expect(move(FIXED, 'from', 1)).toEqual([...FIXED])
    expect(move(FIXED, 'workdir', -1)).toEqual([...FIXED])
    expect(move(FIXED, 'cmd', 1)).toEqual([...FIXED])
  })

  it('uses the lab engine timings', () => {
    expect(engine).toContain('PIP_SECONDS_PER_PACKAGE = 16.0')
    expect(STEPS.install.seconds).toBe(16 * 6)
    expect(engine).toContain('return 0.3')
    expect(STEPS.copyAll.seconds).toBe(0.3)
  })
})
