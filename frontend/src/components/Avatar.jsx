export function initials(name = '') {
  return (
    name
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((w) => w[0]?.toUpperCase())
      .join('') || '?'
  )
}

export default function Avatar({ name, className = '' }) {
  return <span className={`avatar ${className}`}>{initials(name)}</span>
}