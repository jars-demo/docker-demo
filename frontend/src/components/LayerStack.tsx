import { LAYERS } from '@/lib/site'

// Fig. 1: the image from case 02, layer by layer. The container's merged view hides .env, and
// layer 3 still carries it to everyone who pulls the image.

export function LayerStack() {
  return (
    <figure className="flex flex-col gap-3">
      <div className="rounded-[4px] border border-navy-line bg-navy-2 px-4 py-3">
        <p className="font-mono text-[11.5px] tracking-[0.1em] text-on-navy-muted uppercase">
          What a shell in the container sees
        </p>
        <p className="mt-1.5 font-mono text-[13px] text-on-navy [overflow-wrap:anywhere]">
          /app/app.py · /app/templates/menu.html
        </p>
      </div>
      <ol aria-label="Image layers, top to bottom" className="flex flex-col gap-1.5">
        {LAYERS.map((layer) => (
          <li
            key={layer.number}
            className={`rounded-[4px] border px-3.5 py-2.5 ${
              layer.number === 3 ? 'border-signal-fill bg-deck-hot' : 'border-navy-line bg-deck'
            }`}
          >
            <div className="flex items-baseline gap-3">
              <span className="w-6 shrink-0 font-mono text-[12px] text-on-navy-muted">
                L{layer.number}
              </span>
              <span className="min-w-0 flex-1 truncate font-mono text-[13px] text-on-navy">
                {layer.instruction}
              </span>
            </div>
            {layer.files.length ? (
              <ul className="mt-2 flex flex-wrap gap-1.5 pl-9">
                {layer.files.map((file) => (
                  <li
                    key={file.path}
                    className={`inline-flex items-center gap-1.5 rounded-[3px] px-1.5 py-0.5 font-mono text-[11.5px] ${
                      file.hidden
                        ? 'border border-dashed border-on-navy-muted text-on-navy-muted line-through'
                        : 'secret' in file && file.secret
                          ? 'bg-signal-fill font-semibold text-navy'
                          : 'bg-navy-2 text-on-navy'
                    }`}
                  >
                    {'secret' in file && file.secret ? (
                      <svg width="10" height="10" viewBox="0 0 14 14" aria-hidden="true">
                        <path d="M7 1l6 11H1z" fill="none" stroke="currentColor" strokeWidth="2" />
                      </svg>
                    ) : null}
                    {file.path}
                    {file.hidden ? <span className="sr-only"> (hidden by a whiteout)</span> : null}
                  </li>
                ))}
              </ul>
            ) : null}
            <p
              className={`mt-1.5 pl-9 text-[12.5px] ${layer.number === 3 ? 'font-semibold text-signal-fill' : 'text-on-navy-muted'}`}
            >
              {layer.note}
            </p>
          </li>
        ))}
      </ol>
      <figcaption className="text-[13px] leading-relaxed text-on-navy-muted">
        Fig. 1. The image from case 02, as <code className="font-mono">docker image save</code>{' '}
        unpacks it. Deleting .env in layer 4 only hides it.
      </figcaption>
    </figure>
  )
}
