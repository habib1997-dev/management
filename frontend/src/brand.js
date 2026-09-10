// Single source of branding for the web app.
// The school name, tagline, colours and logo come from the backend's
// /api/v1/settings/brand endpoint (which the PDF generator reads directly),
// so the app and the printed reports can never disagree.

export const BRAND_DEFAULTS = {
  name: 'Usman Public School',
  tagline: 'Knowledge, Character, Excellence',
  primary_color: '#0B6B4F',
  secondary_color: '#D9A441',
  demo: true,
  logo_url: '/api/v1/settings/brand/logo',
}

let cache = null
let loading = null

export async function fetchBrand(force = false) {
  if (cache && !force) return cache
  if (loading) return loading
  loading = (async () => {
    try {
      const res = await fetch('/api/v1/settings/brand')
      cache = res.ok ? await res.json() : { ...BRAND_DEFAULTS }
    } catch {
      cache = { ...BRAND_DEFAULTS }
    } finally {
      loading = null
    }
    return cache
  })()
  return loading
}

export function getCachedBrand() {
  return cache || BRAND_DEFAULTS
}

function shade(hex, factor) {
  const n = parseInt(hex.slice(1), 16)
  const r = Math.round(((n >> 16) & 255) * factor)
  const g = Math.round(((n >> 8) & 255) * factor)
  const b = Math.round((n & 255) * factor)
  return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)}`
}

export function applyBrand(brand) {
  const root = document.documentElement
  root.style.setProperty('--primary', brand.primary_color)
  root.style.setProperty('--primary-dark', shade(brand.primary_color, 0.82))
  root.style.setProperty('--accent', brand.secondary_color)
  root.style.setProperty('--sidebar-bg', shade(brand.primary_color, 0.82))
  root.style.setProperty('--active-nav', shade(brand.primary_color, 1.0))
  document.title = `${brand.name} — Student Management`
}