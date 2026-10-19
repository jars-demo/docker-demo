// The site's mark: three stacked layers, the shape every image is made of.

export function Mark({ className = 'size-7' }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect x="4" y="19" width="24" height="7" rx="1.5" fill="#1d63ed" />
      <rect x="7" y="11.5" width="18" height="6" rx="1.5" fill="#1d63ed" opacity="0.75" />
      <rect x="10" y="5" width="12" height="5" rx="1.5" fill="#1d63ed" opacity="0.5" />
    </svg>
  )
}
