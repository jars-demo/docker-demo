'use client'

import { useState } from 'react'

import { build, DOCKERFILES, installSeconds, type Order, start, verdict } from '@/lib/cache'
import { MEASURED } from '@/lib/site'

// Build a Dockerfile, change a file, build again, and see which layers come from the cache.

const ORDERS: { id: Order; label: string }[] = [
  { id: 'shipped', label: 'As shipped' },
  { id: 'fixed', label: 'Fixed' },
]

const LOOK = {
  base: ['bg-code-head text-code-muted', 'Base'],
  cached: ['bg-pass-wash text-pass', 'Cached'],
  ran: ['bg-fail-wash text-fail', 'Ran'],
  idle: ['bg-code-head text-code-muted', '...'],
} as const

function Badge({ state }: { state: keyof typeof LOOK }) {
  const [look, text] = LOOK[state]
  return (
    <span
      className={`inline-flex h-6 w-16 shrink-0 items-center justify-center rounded font-mono text-[11px] font-medium tracking-[0.04em] uppercase ${look}`}
    >
      {text}
    </span>
  )
}

export function CacheSim() {
  const [state, setState] = useState(() => start('shipped'))
  const rows =
    state.last?.rows ??
    DOCKERFILES[state.order].map((step) => ({ text: step.text, state: 'idle' as const }))

  return (
    <div className="card overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-rule bg-canvas-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <fieldset className="flex items-center gap-2">
          <legend className="sr-only">Dockerfile</legend>
          <span aria-hidden="true" className="text-[14px] font-medium text-ink-2">
            Dockerfile
          </span>
          <div className="inline-flex rounded-md border border-rule-strong bg-surface p-0.5">
            {ORDERS.map((order) => (
              <label
                key={order.id}
                className={`inline-flex h-9 cursor-pointer items-center rounded px-3 text-[14px] font-medium has-focus-visible:outline-2 has-focus-visible:outline-blue ${
                  state.order === order.id ? 'bg-blue text-on-blue' : 'text-ink-2 hover:text-ink'
                }`}
              >
                <input
                  type="radio"
                  name="order"
                  value={order.id}
                  checked={state.order === order.id}
                  onChange={() => setState(start(order.id))}
                  className="sr-only"
                />
                {order.label}
              </label>
            ))}
          </div>
        </fieldset>
        <p className="text-[13px] text-muted">
          pip install measured at {MEASURED.pipInstallSeconds} s in chapter 03
        </p>
      </div>

      <ol
        aria-label="Build steps"
        className="terminal m-4 flex flex-col gap-1.5 p-3 text-[13px] sm:text-[14px]"
      >
        {rows.map((row, index) => (
          <li
            key={`${state.builds}-${index}`}
            className="step-in flex items-center gap-3"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <Badge state={row.state} />
            <code
              className={`min-w-0 truncate ${row.state === 'ran' ? 'text-code-ink' : 'text-code-muted'}`}
            >
              {row.text}
            </code>
          </li>
        ))}
      </ol>

      <div className="flex flex-wrap gap-2 px-4">
        <button
          type="button"
          onClick={() => setState(build(state))}
          className="inline-flex h-10 items-center rounded-md bg-blue px-4 text-[14px] font-medium text-on-blue hover:bg-blue-hover"
        >
          Build
        </button>
        {(['app/main.py', 'requirements.txt'] as const).map((file) => (
          <button
            key={file}
            type="button"
            disabled={!state.last}
            onClick={() => setState(build(state, file))}
            className="inline-flex h-10 items-center rounded-md border border-rule-strong bg-surface px-4 text-[14px] font-medium text-ink hover:border-blue disabled:cursor-not-allowed disabled:opacity-50"
          >
            Change {file}, rebuild
          </button>
        ))}
      </div>

      <p
        role="status"
        className="mx-4 mt-4 rounded-md bg-blue-wash px-3.5 py-2.5 text-[14.5px] text-ink"
      >
        {verdict(state)}
      </p>

      <dl className="m-4 grid grid-cols-3 gap-px overflow-hidden rounded-md border border-rule bg-rule">
        {[
          ['Builds', String(state.builds)],
          ['pip install runs', String(state.installs)],
          ['Seconds in pip install', installSeconds(state).toFixed(1)],
        ].map(([term, value]) => (
          <div key={term} className="flex flex-col gap-0.5 bg-surface px-3 py-2.5">
            <dt className="text-[12px] text-muted">{term}</dt>
            <dd className="font-mono text-[18px] text-ink" data-testid={term}>
              {value}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
