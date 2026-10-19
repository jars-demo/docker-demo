// Short text with `code` spans, such as a chapter summary.

export function Inline({ text }: { text: string }) {
  return text.split(/(`[^`]+`)/).map((part, index) =>
    part.startsWith('`') ? (
      <code key={index} className="rounded bg-canvas-2 px-1 font-mono text-[0.88em] text-ink">
        {part.slice(1, -1)}
      </code>
    ) : (
      part
    ),
  )
}
