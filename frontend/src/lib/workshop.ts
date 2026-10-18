import fs from 'node:fs'
import path from 'node:path'

// Workshop chapters live in workshop/NN-slug.md (the source of truth). They are read once at
// module scope, so every chapter page can be prerendered.

export type Chapter = {
  slug: string
  number: string
  title: string
  summary: string
  minutes: number
  body: string
}

// Chapters live at the repository root, next to lab/ and frontend/.
const DIR = path.join(process.cwd(), '..', 'workshop')

function parse(file: string): Chapter {
  const raw = fs.readFileSync(path.join(DIR, file), 'utf8')
  const slug = file.replace(/\.md$/, '')
  const number = slug.slice(0, 2)
  const lines = raw.split('\n')
  const title = (lines.find((l) => l.startsWith('# ')) ?? `# ${slug}`).slice(2).trim()
  const summary = (lines.find((l) => l.startsWith('> ')) ?? '> ').slice(2).trim()
  const minutes = Number(/(\d+)\s*minutes/i.exec(raw)?.[1] ?? 10)
  const body = lines
    // The title, summary and time are shown in the page header, so they are left out of the body.
    .filter((l) => !l.startsWith('# ') && l !== `> ${summary}` && !l.startsWith('**Time:**'))
    .join('\n')
    .trim()
  return { slug, number, title, summary, minutes, body }
}

export const CHAPTERS: Chapter[] = fs
  .readdirSync(DIR)
  .filter((file) => /^\d{2}-[a-z0-9-]+\.md$/.test(file))
  .sort()
  .map(parse)

export function findChapter(slug: string): Chapter | undefined {
  return CHAPTERS.find((chapter) => chapter.slug === slug)
}
