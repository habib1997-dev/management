import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { BRAND_DEFAULTS, fetchBrand, getCachedBrand, applyBrand } from '../brand.js'

function resetBrandModule() {
  vi.resetModules()
  window.localStorage.clear()
}

describe('fetchBrand', () => {
  beforeEach(resetBrandModule)
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('returns cached brand on subsequent calls', async () => {
    const { fetchBrand } = await import('../brand.js')
    const payload = { name: 'Test School', primary_color: '#111111' }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    const first = await fetchBrand()
    const second = await fetchBrand()

    expect(first).toEqual(payload)
    expect(second).toEqual(payload)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('forces a refresh when asked', async () => {
    const { fetchBrand } = await import('../brand.js')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 200 })))
    await fetchBrand()
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"name":"B"}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    const refreshed = await fetchBrand(true)
    expect(refreshed.name).toBe('B')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('falls back to defaults when the response is not ok', async () => {
    const { fetchBrand } = await import('../brand.js')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('"error"', { status: 500 })))

    const brand = await fetchBrand(true)
    expect(brand).toEqual(BRAND_DEFAULTS)
  })

  it('falls back to defaults when the network rejects', async () => {
    const { fetchBrand } = await import('../brand.js')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network down')))

    const brand = await fetchBrand(true)
    expect(brand).toEqual(BRAND_DEFAULTS)
  })

  it('deduplicates concurrent calls into one fetch', async () => {
    const { fetchBrand } = await import('../brand.js')
    let resolveFetch
    const fetchMock = vi.fn(() => new Promise((r) => { resolveFetch = r }))
    vi.stubGlobal('fetch', fetchMock)

    const p1 = fetchBrand(true)
    const p2 = fetchBrand(true)
    resolveFetch(new Response('{"name":"X"}', { status: 200 }))
    const [r1, r2] = await Promise.all([p1, p2])

    expect(r1).toEqual(r2)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})

describe('getCachedBrand', () => {
  it('returns defaults before anything is fetched', () => {
    expect(getCachedBrand()).toEqual(BRAND_DEFAULTS)
  })
})

describe('applyBrand', () => {
  it('sets CSS variables and the document title', () => {
    applyBrand({
      name: 'Greenfield High',
      primary_color: '#0B6B4F',
      secondary_color: '#D9A441',
    })

    const root = document.documentElement
    expect(root.style.getPropertyValue('--primary')).toBe('#0B6B4F')
    expect(root.style.getPropertyValue('--accent')).toBe('#D9A441')
    // shade('#0B6B4F', 0.82) = #095841 (round(11*0.82)=9, round(107*0.82)=88, round(79*0.82)=65)
    expect(root.style.getPropertyValue('--sidebar-bg')).toBe('#095841')
    // shade always emits lowercase hex
    expect(root.style.getPropertyValue('--active-nav')).toBe('#0b6b4f')
    expect(document.title).toBe('Greenfield High — Student Management')
  })
})