'use client'

import { useState } from 'react'

import {
  build,
  edit,
  type FileName,
  FIRST,
  FIXED,
  move,
  reinstalledForNothing,
  type Result,
  SHIPPED,
  type StepId,
  STEPS,
  type Versions,
} from '@/lib/buildcache'

// The build cache, to play with: pick a Dockerfile, build it, edit a file, build again, and see
// which steps come from the cache. The rules live in lib/buildcache.ts and are unit tested.

type Preset = 'shipped' | 'fixed'

const PRESETS: Record<Preset, { name: string; order: readonly StepId[] }> = {
  shipped: { name: 'As shipped', order: SHIPPED },
  fixed: { name: 'Fixed', order: FIXED },
}

type State = {
  preset: Preset
  order: StepId[]
  versions: Versions
  cache: Set<string>
  result: Result | null
  changed: FileName | null
  builds: number
}

function fresh(preset: Preset): State {
  return {
    preset,
    order: [...PRESETS[preset].order],
    versions: FIRST,
    cache: new Set(),
    result: null,
    changed: null,
    builds: 0,
  }
}

function Icon({ kind }: { kind: 'cached' | 'ran' | 'error' }) {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" className="shrink-0">
      {kind === 'cached' ? (
        <path d="M2.5 7.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="2" />
      ) : kind === 'ran' ? (
        <path d="M7 1.5v5.5l3.5 2" fill="none" stroke="currentColor" strokeWidth="2" />
      ) : (
        <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      )}
    </svg>
  )
}

function verdict(state: State): string {
  const { result, changed, builds } = state
  if (!result) return 'Press Build for the first build. The cache starts empty, so every step runs.'
  if (result.error) return `The build failed: ${result.error}. Nothing was copied before pip ran.`
  if (builds === 1 || changed === null) {
    return `Built in ${result.seconds.toFixed(1)} s. Now edit a file and build again.`
  }
  const ran = result.rows.filter((row) => !row.cached)
  if (reinstalledForNothing(result, changed)) {
    return `You changed ${changed}, and pip install ran again anyway: ${result.seconds.toFixed(1)} s, almost all of it reinstalling packages that did not change.`
  }
  if (changed === 'requirements.txt') {
    return `requirements.txt changed, so pip install had to run: ${result.seconds.toFixed(1)} s. That is the cache doing its job.`
  }
  return `You changed ${changed}. Only ${ran.map((row) => row.text).join(', ')} ran: ${result.seconds.toFixed(1)} s.`
}

export function BuildSim() {
  const [state, setState] = useState<State>(() => fresh('shipped'))

  const run = (file: FileName | null) =>
    setState((current) => {
      const versions = file ? edit(current.versions, file) : current.versions
      const { result, cache } = build(current.order, versions, current.cache)
      return { ...current, versions, cache, result, changed: file, builds: current.builds + 1 }
    })

  const reorder = (id: StepId, by: -1 | 1) =>
    setState((current) => ({ ...current, order: move(current.order, id, by), result: null }))

  const ready = state.builds > 0 && !state.result?.error
  const result = state.result

  return (
    <div className="plate flex flex-col">
      <div className="flex flex-col gap-3 border-b border-rule p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
        <fieldset className="flex flex-wrap items-center gap-2">
          <legend className="sr-only">Dockerfile</legend>
          <span aria-hidden="true" className="mr-1 text-[13px] font-semibold text-ink-2">
            Dockerfile
          </span>
          {(Object.keys(PRESETS) as Preset[]).map((preset) => (
            <label
              key={preset}
              className={`inline-flex h-10 cursor-pointer items-center rounded-[4px] border px-4 text-[14px] font-semibold has-focus-visible:outline-3 has-focus-visible:outline-signal ${
                state.preset === preset
                  ? 'border-navy bg-navy text-on-navy'
                  : 'border-rule-strong bg-surface text-ink hover:border-signal'
              }`}
            >
              <input
                type="radio"
                name="dockerfile"
                value={preset}
                checked={state.preset === preset}
                onChange={() => setState(fresh(preset))}
                className="sr-only"
              />
              {PRESETS[preset].name}
            </label>
          ))}
        </fieldset>
        <button
          type="button"
          onClick={() =>
            setState((current) => ({ ...fresh(current.preset), order: current.order }))
          }
          className="inline-flex h-10 items-center self-start rounded-[4px] px-1 text-[14px] font-medium text-ink-2 underline decoration-rule-strong underline-offset-4 hover:text-ink sm:self-auto"
        >
          Empty the cache
        </button>
      </div>

      <div className="grid grid-cols-[minmax(0,1fr)] lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="border-b border-rule p-4 sm:p-5 lg:border-r lg:border-b-0">
          <p className="mb-3 font-mono text-[12px] tracking-[0.08em] text-muted uppercase">
            Steps, top to bottom
          </p>
          <ol className="code flex flex-col rounded-[4px] py-1.5" aria-label="Dockerfile steps">
            {state.order.map((id, index) => (
              <li key={id} className="flex items-center gap-1 pr-1 pl-3">
                <span aria-hidden="true" className="w-5 shrink-0 text-[12px] text-code-muted">
                  {index + 1}
                </span>
                <span className="min-w-0 flex-1 truncate text-[13px] leading-10">
                  {STEPS[id].text}
                </span>
                {id === 'from' ? null : (
                  <span className="flex shrink-0">
                    {([-1, 1] as const).map((by) => {
                      const blocked = index + by < 1 || index + by >= state.order.length
                      return (
                        <button
                          key={by}
                          type="button"
                          disabled={blocked}
                          onClick={() => reorder(id, by)}
                          aria-label={`Move ${STEPS[id].text} ${by < 0 ? 'up' : 'down'}`}
                          className="grid size-10 place-items-center rounded-[3px] text-code-muted hover:bg-navy-2 hover:text-code-ink disabled:opacity-30"
                        >
                          <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
                            <path
                              d={by < 0 ? 'M2 8l4-4 4 4' : 'M2 4l4 4 4-4'}
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.8"
                            />
                          </svg>
                        </button>
                      )
                    })}
                  </span>
                )}
              </li>
            ))}
          </ol>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => run(null)}
              className="on-navy inline-flex h-11 items-center rounded-[4px] bg-signal-fill px-5 text-[15px] font-semibold text-navy hover:bg-signal-hover"
            >
              Build
            </button>
            {(['app.py', 'requirements.txt'] as const).map((file) => (
              <button
                key={file}
                type="button"
                disabled={!ready}
                onClick={() => run(file)}
                className="inline-flex h-11 items-center rounded-[4px] border border-rule-strong bg-surface px-4 text-[14.5px] font-semibold text-ink hover:border-signal disabled:cursor-not-allowed disabled:opacity-45"
              >
                Edit {file}, rebuild
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-3 p-4 sm:p-5">
          <div className="flex items-baseline justify-between gap-3">
            <p className="font-mono text-[12px] tracking-[0.08em] text-muted uppercase">
              Build {state.builds || ''}
            </p>
            <p className="text-[13px] text-ink-2">
              Took{' '}
              <span data-testid="Build time" className="font-mono font-semibold text-ink">
                {result && !result.error ? result.seconds.toFixed(1) : '0.0'}
              </span>{' '}
              s
            </p>
          </div>
          <ol className="flex flex-col gap-1.5" aria-label="Build output">
            {result
              ? result.rows.map((row, index) => (
                  <li
                    key={`${state.builds}-${row.id}`}
                    style={{ ['--at' as string]: `${index * 60}ms` }}
                    className={`row-in flex items-center gap-2.5 rounded-[3px] border px-2.5 py-2 text-[13.5px] ${
                      row.cached
                        ? 'border-pass/25 bg-pass-wash text-pass'
                        : 'border-work/25 bg-work-wash text-work'
                    }`}
                  >
                    <Icon kind={row.cached ? 'cached' : 'ran'} />
                    <span className="w-14 shrink-0 font-mono text-[11.5px] font-semibold tracking-[0.06em] uppercase">
                      {row.cached ? 'Cached' : 'Ran'}
                    </span>
                    <span className="min-w-0 flex-1 truncate font-mono text-[12.5px] text-ink">
                      {row.text}
                    </span>
                    <span className="shrink-0 font-mono text-[12.5px]">
                      {row.seconds.toFixed(1)} s
                    </span>
                  </li>
                ))
              : null}
            {result?.error ? (
              <li className="flex items-start gap-2.5 rounded-[3px] border border-fail/30 bg-fail-wash px-2.5 py-2 text-[13.5px] text-fail">
                <span className="pt-0.5">
                  <Icon kind="error" />
                </span>
                <span className="w-14 shrink-0 font-mono text-[11.5px] font-semibold tracking-[0.06em] uppercase">
                  Error
                </span>
                <span className="min-w-0 flex-1 font-mono text-[12.5px] [overflow-wrap:anywhere]">
                  {result.error}
                </span>
              </li>
            ) : null}
            {!result ? (
              <li className="rounded-[3px] border border-dashed border-rule-strong px-3 py-6 text-center text-[14px] text-muted">
                No build yet
              </li>
            ) : null}
          </ol>
          <p role="status" className="text-[14.5px] leading-relaxed text-ink-2">
            {verdict(state)}
          </p>
        </div>
      </div>
    </div>
  )
}
