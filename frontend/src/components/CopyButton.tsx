'use client'

import { useState } from 'react'

export function CopyButton({ text, label = 'Copy' }: { text: string; label?: string }) {
  const [state, setState] = useState<'idle' | 'copied' | 'blocked'>('idle')
  return (
    <button
      type="button"
      aria-label={state === 'idle' ? label : undefined}
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text)
          setState('copied')
        } catch {
          setState('blocked')
        }
        window.setTimeout(() => setState('idle'), 1600)
      }}
      className="inline-flex h-9 min-w-16 items-center justify-center rounded-md px-2.5 font-mono text-[11px] font-medium tracking-[0.08em] text-code-muted uppercase hover:bg-code-bg hover:text-code-ink"
    >
      <span aria-live="polite">
        {state === 'copied' ? 'Copied' : state === 'blocked' ? 'Select to copy' : 'Copy'}
      </span>
    </button>
  )
}
