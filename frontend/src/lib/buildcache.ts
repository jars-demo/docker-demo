// The build cache simulator's rules, the same ones as lab/dock/engine.py:
//
// - A step's cache key is its parent's key plus its own instruction.
// - COPY also hashes the files it copies, so editing a copied file misses.
// - Once one step misses, every step after it misses, because its parent is new.
// - pip install reads requirements.txt, so it fails if no earlier step copied it.
//
// Times are the lab's pretend seconds, so the site and chapter 01 show the same numbers.

export type FileName = 'requirements.txt' | 'app.py' | 'templates/menu.html'

export const FILES: readonly FileName[] = ['requirements.txt', 'app.py', 'templates/menu.html']

export type StepId = 'from' | 'workdir' | 'copyReqs' | 'install' | 'copyAll' | 'cmd'

type Step = { text: string; copies: readonly FileName[]; seconds: number }

export const STEPS: Record<StepId, Step> = {
  from: { text: 'FROM python:3.13-slim', copies: [], seconds: 0 },
  workdir: { text: 'WORKDIR /app', copies: [], seconds: 0 },
  copyReqs: { text: 'COPY requirements.txt .', copies: ['requirements.txt'], seconds: 0.3 },
  install: { text: 'RUN pip install -r requirements.txt', copies: [], seconds: 96 },
  copyAll: { text: 'COPY . .', copies: FILES, seconds: 0.3 },
  cmd: { text: 'CMD ["gunicorn", "app:app"]', copies: [], seconds: 0 },
}

export const SHIPPED: readonly StepId[] = ['from', 'workdir', 'copyAll', 'install', 'cmd']
export const FIXED: readonly StepId[] = ['from', 'workdir', 'copyReqs', 'install', 'copyAll', 'cmd']

export type Versions = Record<FileName, number>
export type Row = { id: StepId; text: string; cached: boolean; seconds: number }
export type Result = { rows: Row[]; seconds: number; error: string | null }

export const FIRST: Versions = { 'requirements.txt': 1, 'app.py': 1, 'templates/menu.html': 1 }

export function build(
  order: readonly StepId[],
  versions: Versions,
  cache: ReadonlySet<string>,
): { result: Result; cache: Set<string> } {
  const next = new Set(cache)
  const rows: Row[] = []
  const copied = new Set<FileName>()
  let key = ''
  let error: string | null = null
  for (const id of order) {
    const step = STEPS[id]
    if (id === 'install' && !copied.has('requirements.txt')) {
      error = 'pip: could not open requirements file: /app/requirements.txt'
      break
    }
    for (const file of step.copies) copied.add(file)
    const inputs = step.copies.map((file) => `${file}@${versions[file]}`).join(',')
    key = `${key}|${step.text}${inputs ? `:${inputs}` : ''}`
    // FROM is always a hit: the base image is already on the machine.
    const cached = id === 'from' || next.has(key)
    next.add(key)
    rows.push({ id, text: step.text, cached, seconds: cached ? 0 : step.seconds })
  }
  const seconds = Math.round(rows.reduce((sum, row) => sum + row.seconds, 0) * 10) / 10
  return { result: { rows, seconds, error }, cache: error ? new Set(cache) : next }
}

export function edit(versions: Versions, file: FileName): Versions {
  return { ...versions, [file]: versions[file] + 1 }
}

/** Move a step one place up or down. FROM stays first. */
export function move(order: readonly StepId[], id: StepId, by: -1 | 1): StepId[] {
  const out = [...order]
  const from = out.indexOf(id)
  const to = from + by
  if (id === 'from' || from < 0 || to < 1 || to >= out.length) return out
  ;[out[from], out[to]] = [out[to] as StepId, out[from] as StepId]
  return out
}

/** Did pip install run again even though requirements.txt did not change? */
export function reinstalledForNothing(result: Result, changed: FileName | null): boolean {
  const install = result.rows.find((row) => row.id === 'install')
  return changed !== null && changed !== 'requirements.txt' && install?.cached === false
}
