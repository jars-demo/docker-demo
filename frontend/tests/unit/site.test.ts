import fs from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { headingsOf, slugify } from '@/components/Markdown'
import { NOTE_SLUGS, notesFor } from '@/lib/pip'
import { CASE_SIX, CASES, CHECKLIST, LAYERS, MEASURED } from '@/lib/site'
import { CHAPTERS, findChapter } from '@/lib/workshop'

const ROOT = path.join(process.cwd(), '..')
const read = (file: string) => fs.readFileSync(path.join(ROOT, file), 'utf8')
const body = (slug: string) => findChapter(slug)?.body ?? ''
const escape = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const row = (...cells: string[]) => new RegExp(cells.map(escape).join('\\s+'))

describe('chapters', () => {
  it('has nine chapters numbered in order', () => {
    expect(CHAPTERS.map((chapter) => Number(chapter.number))).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9])
  })

  it.each(CHAPTERS.map((chapter) => [chapter.slug, chapter] as const))(
    '%s has a summary, a time, the standard sections and its own case',
    (_slug, chapter) => {
      expect(chapter.summary.length).toBeGreaterThan(10)
      expect(chapter.minutes).toBeGreaterThan(0)
      for (const section of ['Goal', 'The case', 'Fix the case', 'Check it works', 'Exercise']) {
        expect(chapter.body).toMatch(new RegExp(`^## ${section}$`, 'm'))
      }
      expect(chapter.body).toContain(`dock run ${Number(chapter.number)}`)
      expect(chapter.body).toContain(`dock check ${Number(chapter.number)}`)
    },
  )

  it('adds up to two hours and three quarters', () => {
    expect(CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)).toBe(165)
  })

  it('never uses a dash where a full stop would do', () => {
    for (const chapter of CHAPTERS) expect(chapter.body, chapter.slug).not.toMatch(/[–—]/)
  })

  it('only mentions lab files that exist', () => {
    const mentioned = new Set(
      CHAPTERS.flatMap((chapter) =>
        [...chapter.body.matchAll(/`(lab\/[\w./-]+\.\w+)`/g)].map((m) => m[1] ?? ''),
      ),
    )
    expect(mentioned.size).toBeGreaterThan(8)
    for (const file of mentioned) {
      expect(fs.existsSync(path.join(ROOT, file)), `${file} is missing`).toBe(true)
    }
  })

  it('shows check output exactly as the checker words it', () => {
    // Every label in checks.py, as a pattern: an f-string's {...} parts match anything.
    const patterns = [...read('lab/dock/checks.py').matchAll(/f?"([^"\n]{12,})"/g)].map(
      (m) =>
        new RegExp(
          `^${(m[1] ?? '')
            .split(/\{[^}]*\}/)
            .map(escape)
            .join('.+')}$`,
        ),
    )
    const labels = CHAPTERS.flatMap((chapter) =>
      [...chapter.body.matchAll(/^ {2}PASS {2}(.+)$/gm)].map((m) => m[1] ?? ''),
    )
    expect(labels.length).toBeGreaterThan(30)
    for (const label of labels) {
      expect(
        patterns.some((pattern) => pattern.test(label)),
        label,
      ).toBe(true)
    }
  })

  it('names only experiments the lab has', () => {
    const experiments = read('lab/dock/experiments.py')
    const named = CHAPTERS.flatMap((chapter) =>
      [...chapter.body.matchAll(/dock try ([\w-]+)/g)].map((m) => m[1] ?? ''),
    )
    expect(new Set(named)).toEqual(new Set(['context', 'digest', 'ports', 'stop']))
    for (const name of named) expect(experiments).toContain(`"${name}":`)
  })

  it('ends with the same checklist the home page shows', () => {
    const last = body('09-resource-limits').replace(/`/g, '')
    expect(CHECKLIST).toHaveLength(11)
    for (const item of CHECKLIST) expect(last).toContain(item)
  })
})

describe('cases', () => {
  it('has one case per chapter, titled as the lab titles it', () => {
    const cli = read('lab/dock/__main__.py')
    expect(CASES.map((item) => item.number)).toEqual(CHAPTERS.map((chapter) => chapter.number))
    for (const item of CASES) expect(cli).toContain(`"${item.title}"`)
  })

  it('shows each symptom as it appears in its chapter', () => {
    for (const item of CASES) {
      const chapter = CHAPTERS.find((c) => c.number === item.number)
      expect(chapter?.body, item.number).toContain(item.symptom)
    }
  })

  it('shows the case 06 walkthrough as the lab prints and fixes it', () => {
    for (const line of CASE_SIX.run) expect(body('06-container-networking')).toContain(line)
    for (const line of CASE_SIX.check)
      expect(body('06-container-networking')).toContain(`  ${line}`)
    for (const line of CASE_SIX.fix) {
      expect(read('lab/tests/solutions/case06_localhost.py')).toContain(line)
    }
  })

  it('draws the case 02 layers as the lab builds them', () => {
    const chapter = body('02-what-a-layer-remembers')
    const case02 = read('lab/cases/case02_secret_layer.py')
    expect(LAYERS.map((layer) => layer.number)).toEqual([5, 4, 3, 2, 1])
    for (const layer of LAYERS.slice(0, 4)) expect(case02).toContain(layer.instruction)
    expect(chapter).toContain('layer 3 (COPY . .): /app/.env  PAYMENT_TOKEN=tp-prod-4f9a2c71')
    expect(LAYERS[2]?.note).toContain('PAYMENT_TOKEN=tp-prod-4f9a2c71')
  })

  it('links headings by a stable slug', () => {
    expect(slugify('Same commit, different digest')).toBe('same-commit-different-digest')
    expect(
      headingsOf('## Goal\n```\n## not a heading\n```\n## Check it works').map((h) => h.id),
    ).toEqual(['goal', 'check-it-works'])
  })
})

describe('measured numbers', () => {
  it('quotes the context experiment exactly as chapter 02 prints it', () => {
    const chapter = body('02-what-a-layer-remembers')
    expect(chapter).toContain(MEASURED.machine)
    for (const r of MEASURED.context) {
      expect(chapter).toMatch(row(r.label, r.files, r.size, r.time))
    }
  })

  it('quotes the stop experiment exactly as chapter 05 prints it', () => {
    const chapter = body('05-pid-one-and-signals')
    expect(chapter).toContain(MEASURED.machine)
    for (const r of MEASURED.stop) {
      expect(chapter).toMatch(row(r.label, r.took, r.ended, r.worker))
      expect(r.good).toBe(r.worker === 'finished its work')
    }
  })

  it('quotes the ports experiment exactly as chapter 06 prints it', () => {
    const chapter = body('06-container-networking')
    expect(chapter).toContain(MEASURED.machine)
    for (const r of MEASURED.ports) {
      expect(chapter).toMatch(row(r.bind, r.target, r.result, r.time))
    }
  })
})

describe("Pip's notes", () => {
  it('has notes for every chapter and none for chapters that do not exist', () => {
    expect([...NOTE_SLUGS].sort()).toEqual(CHAPTERS.map((chapter) => chapter.slug))
  })

  it('picks the notes for the page you are on', () => {
    expect(notesFor('/workshop/05-pid-one-and-signals').note).toContain('137')
    expect(notesFor('/workshop').quiz.length).toBe(2)
    expect(notesFor('/')).toBe(notesFor('/no-such-page'))
  })

  it.each([
    ['/', '/'],
    ['/workshop', '/workshop'],
    ...NOTE_SLUGS.map((slug) => [slug, `/workshop/${slug}`]),
  ])('asks %s two questions with exactly one right answer each', (_name, pathname) => {
    const { quiz } = notesFor(pathname)
    expect(quiz).toHaveLength(2)
    for (const item of quiz) {
      expect(item.options.length).toBeGreaterThanOrEqual(3)
      expect(new Set(item.options).size).toBe(item.options.length)
      expect(item.options[item.answer], item.q).toBeDefined()
      expect(item.why.length).toBeGreaterThan(20)
    }
  })
})
