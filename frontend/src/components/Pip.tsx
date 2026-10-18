// Pip, a hermit crab who lives in a borrowed shipping container. Drawn as one inline SVG, so it
// scales cleanly and needs no image request. `face` crops to the eyes and claws, for small spaces.

export function Pip({ className = '', face = false }: { className?: string; face?: boolean }) {
  return (
    <svg
      viewBox={face ? '14 14 72 72' : '0 0 140 110'}
      className={className}
      role="img"
      aria-label="Pip the hermit crab"
    >
      {face ? null : (
        <g>
          {/* the shell: a small container with corrugated sides and corner castings */}
          <rect x="58" y="22" width="74" height="54" rx="3" fill="#143149" />
          {[66, 76, 86, 96, 106, 116].map((x) => (
            <rect key={x} x={x} y="28" width="4" height="42" rx="1" fill="#1d5a85" />
          ))}
          <rect x="58" y="22" width="8" height="8" fill="#ff8a3d" />
          <rect x="124" y="22" width="8" height="8" fill="#ff8a3d" />
          <rect x="58" y="68" width="8" height="8" fill="#ff8a3d" />
          <rect x="124" y="68" width="8" height="8" fill="#ff8a3d" />
          {/* legs */}
          {[44, 54, 64].map((x) => (
            <path
              key={x}
              d={`M${x} 78 q-6 10 -12 14`}
              stroke="#c4471a"
              strokeWidth="4"
              strokeLinecap="round"
              fill="none"
            />
          ))}
        </g>
      )}
      {/* body */}
      <ellipse cx="50" cy="64" rx="24" ry="18" fill="#e2632a" />
      <ellipse cx="46" cy="60" rx="14" ry="8" fill="#f08a52" />
      {/* eye stalks and eyes */}
      <path d="M40 50 L36 32" stroke="#c4471a" strokeWidth="3.5" strokeLinecap="round" />
      <path d="M54 50 L58 32" stroke="#c4471a" strokeWidth="3.5" strokeLinecap="round" />
      <g className="pip-blink">
        <circle cx="36" cy="29" r="6" fill="#ffffff" />
        <circle cx="58" cy="29" r="6" fill="#ffffff" />
        <circle cx="37" cy="30" r="3" fill="#0c1722" />
        <circle cx="57" cy="30" r="3" fill="#0c1722" />
      </g>
      {/* claws: the left one waves */}
      <g className="pip-wave">
        <path d="M30 66 q-10 -4 -12 -14" stroke="#c4471a" strokeWidth="4" fill="none" />
        <path d="M18 52 q-8 -2 -6 -10 q6 2 8 6 q4 -6 10 -4 q-2 8 -12 8z" fill="#e2632a" />
      </g>
      <path d="M70 66 q10 -2 14 -10" stroke="#c4471a" strokeWidth="4" fill="none" />
      <path d="M84 56 q8 -2 8 -10 q-6 0 -8 4 q-4 -6 -10 -3 q2 8 10 9z" fill="#e2632a" />
      {/* a small smile */}
      <path
        d="M43 68 q4 4 8 0"
        stroke="#0c1722"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  )
}
