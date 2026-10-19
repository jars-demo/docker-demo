import fs from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { headingsOf, slugify } from '@/components/Markdown'
import { QUIZ } from '@/lib/quiz'
import { LEVELS, MEASURED, SYMPTOMS } from '@/lib/site'
import { CHAPTERS, findChapter } from '@/lib/workshop'

const ROOT = path.join(process.cwd(), '..')
const body = (number: string) => CHAPTERS.find((chapter) => chapter.number === number)?.body ?? ''
const all = CHAPTERS.map((chapter) => chapter.body).join('\n')

describe('chapters', () => {
  it('has twelve chapters numbered in order', () => {
    expect(CHAPTERS.map((chapter) => Number(chapter.number))).toEqual([
      1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
    ])
  })

  it.each(CHAPTERS.map((chapter) => [chapter.slug, chapter] as const))(
    '%s has a summary, a time, the standard sections and its exercise',
    (slug, chapter) => {
      expect(chapter.summary.length).toBeGreaterThan(20)
      expect(chapter.minutes).toBeGreaterThan(0)
      for (const section of [
        'Goal',
        'The idea',
        'The exercise',
        'Check your fix',
        'In production',
        'Key points',
      ]) {
        expect(chapter.body).toMatch(new RegExp(`^## ${section}$`, 'm'))
      }
      expect(chapter.body).toContain(`dock run ${Number(chapter.number)}`)
      expect(chapter.body).toContain(`dock check ${Number(chapter.number)}`)
      expect(fs.existsSync(path.join(ROOT, 'lab', 'exercises', slug))).toBe(true)
    },
  )

  it('adds up to four hours and twenty five minutes', () => {
    expect(CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)).toBe(265)
  })

  it('never uses a long dash', () => {
    for (const chapter of CHAPTERS) expect(chapter.body, chapter.slug).not.toMatch(/[–—]/)
  })

  it('only mentions lab files that exist', () => {
    const mentioned = new Set(
      [...all.matchAll(/`(lab\/[\w./-]+)`/g)].map((match) => match[1] ?? ''),
    )
    expect(mentioned.size).toBeGreaterThan(10)
    for (const file of mentioned) expect(fs.existsSync(path.join(ROOT, file)), file).toBe(true)
  })

  it('finds chapters by slug and builds an outline from their headings', () => {
    const chapter = findChapter('09-graceful-shutdown')
    expect(chapter?.title).toBe('PID 1 and graceful shutdown')
    expect(headingsOf(chapter?.body ?? '').map((h) => h.id)).toContain(slugify('Check your fix'))
  })
})

describe('the numbers on the site come from the chapters', () => {
  it.each(Object.entries(SYMPTOMS))('chapter %s prints its symptom', (number, symptom) => {
    expect(body(number)).toContain(symptom)
  })

  it('quotes the measured times and sizes', () => {
    expect(body('03')).toContain(`ran     ${MEASURED.pipInstallSeconds} s  RUN pip install`)
    expect(body('03')).toContain(`measured ${MEASURED.cachedRebuildSeconds} s`)
    expect(body('09')).toContain(`took ${MEASURED.stopShippedSeconds} s, exit code 137`)
    expect(body('09')).toContain(`measured ${MEASURED.stopFixedSeconds} s, with exit code 0`)
    expect(body('08')).toContain(`image size: ${MEASURED.imageShippedMb} MB`)
    expect(body('08')).toContain(`**${MEASURED.imageFixedMb} MB**`)
    for (const base of MEASURED.bases)
      expect(body('08')).toMatch(new RegExp(`${base.size}\\s+${base.image}`))
  })

  it('quotes the experiments as the lab prints them', () => {
    const experiments = fs.readFileSync(path.join(ROOT, 'lab/dock/experiments.py'), 'utf8')
    expect(experiments).toContain('python -c pass')
    expect(experiments).toContain('head -c 100000000 /dev/urandom')
    expect(MEASURED.containerMs).toBeGreaterThan(MEASURED.processMs)
  })
})

describe('levels and quiz', () => {
  it('puts every chapter in exactly one level', () => {
    expect(LEVELS.flatMap((level) => level.chapters)).toEqual([
      1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
    ])
  })

  it.each(CHAPTERS.map((chapter) => chapter.number))(
    'chapter %s has two answerable questions',
    (number) => {
      const questions = QUIZ[number] ?? []
      expect(questions).toHaveLength(2)
      for (const question of questions) {
        expect(question.options[question.answer]).toBeDefined()
        expect(question.why.length).toBeGreaterThan(20)
      }
    },
  )
})
