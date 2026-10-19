// The layer cache simulator's rules, the same ones BuildKit follows in exercise 03:
//
// - A step's cache key is its parent's key plus its own instruction.
// - COPY also hashes the files it copies, so changing a copied file misses the cache.
// - Once one step misses, every step after it misses, because its parent is new.
//
// The pip install time is the real one measured in chapter 03.

import { MEASURED } from './site'

export type FileName = 'app/main.py' | 'requirements.txt'
export type Order = 'shipped' | 'fixed'

type Step = { text: string; copies: readonly FileName[]; install?: boolean }

const ALL: readonly FileName[] = ['app/main.py', 'requirements.txt']

export const DOCKERFILES: Record<Order, readonly Step[]> = {
  shipped: [
    { text: 'FROM python:3.13.16-slim-trixie', copies: [] },
    { text: 'WORKDIR /app', copies: [] },
    { text: 'COPY . .', copies: ALL },
    { text: 'RUN pip install --no-cache-dir -r requirements.txt', copies: [], install: true },
    { text: 'CMD ["uvicorn", "app.main:app", ...]', copies: [] },
  ],
  fixed: [
    { text: 'FROM python:3.13.16-slim-trixie', copies: [] },
    { text: 'WORKDIR /app', copies: [] },
    { text: 'COPY requirements.txt .', copies: ['requirements.txt'] },
    { text: 'RUN pip install --no-cache-dir -r requirements.txt', copies: [], install: true },
    { text: 'COPY . .', copies: ALL },
    { text: 'CMD ["uvicorn", "app.main:app", ...]', copies: [] },
  ],
}

export type Versions = Record<FileName, number>
export type Row = { text: string; state: 'base' | 'cached' | 'ran' }
export type Build = { rows: Row[]; installRan: boolean }
export type State = {
  order: Order
  versions: Versions
  cache: ReadonlySet<string>
  last: Build | null
  builds: number
  installs: number
  changed: FileName | null
}

export const FIRST: Versions = { 'app/main.py': 1, 'requirements.txt': 1 }

export function start(order: Order): State {
  return {
    order,
    versions: FIRST,
    cache: new Set(),
    last: null,
    builds: 0,
    installs: 0,
    changed: null,
  }
}

function run(order: Order, versions: Versions, cache: ReadonlySet<string>) {
  const next = new Set(cache)
  const rows: Row[] = []
  let key = ''
  let installRan = false
  for (const step of DOCKERFILES[order]) {
    const inputs = step.copies.map((file) => `${file}@${versions[file]}`).join(',')
    key = `${key}|${step.text}${inputs ? `:${inputs}` : ''}`
    const base = step.text.startsWith('FROM')
    const cached = !base && next.has(key)
    next.add(key)
    if (step.install && !cached) installRan = true
    rows.push({ text: step.text, state: base ? 'base' : cached ? 'cached' : 'ran' })
  }
  return { build: { rows, installRan }, cache: next }
}

/** Build the image. Pass a file to change it first, the way a commit would. */
export function build(state: State, change: FileName | null = null): State {
  const versions = change
    ? { ...state.versions, [change]: state.versions[change] + 1 }
    : state.versions
  const { build: last, cache } = run(state.order, versions, state.cache)
  return {
    ...state,
    versions,
    cache,
    last,
    builds: state.builds + 1,
    installs: state.installs + (last.installRan ? 1 : 0),
    changed: change,
  }
}

export function installSeconds(state: State): number {
  return Math.round(state.installs * MEASURED.pipInstallSeconds * 10) / 10
}

/** What the last build means, in a sentence. */
export function verdict(state: State): string {
  if (!state.last) return 'Nothing built yet. Build once to fill the cache.'
  if (state.builds === 1) return 'First build: every step ran, and every layer is now in the cache.'
  if (state.changed === 'app/main.py' && state.last.installRan)
    return 'One line of code changed, and pip install ran again anyway.'
  if (state.changed === 'app/main.py')
    return 'One line of code changed. pip install came from the cache.'
  if (state.changed === 'requirements.txt')
    return 'The dependencies changed, so pip install ran again. That is the cache doing its job.'
  return 'Nothing changed, so every step came from the cache.'
}
