import { useEffect, useMemo, useState } from 'react'

const INDEX_URL = '/media/_variants/manifests/latest-webp-index.json'
const MEDIA_PREFIX = '/media/'
const SUPPORTED_EXTENSIONS = new Set(['.jpg', '.jpeg', '.png'])
const VARIANT_ORDER = ['thumb', 'medium', 'large']
const VARIANT_WIDTHS = {
  thumb: 480,
  medium: 960,
  large: 1600,
}

let indexPromise = null
let cachedIndex = null

function encodeObjectKey(key) {
  return key.split('/').map((part) => encodeURIComponent(part)).join('/')
}

function extensionOf(key) {
  const idx = key.lastIndexOf('.')
  return idx >= 0 ? key.slice(idx).toLowerCase() : ''
}

function loadVariantIndex() {
  if (cachedIndex) return Promise.resolve(cachedIndex)
  if (!indexPromise) {
    indexPromise = fetch(INDEX_URL, { credentials: 'same-origin' })
      .then((res) => {
        if (!res.ok) return { sources: {} }
        return res.json()
      })
      .then((data) => {
        cachedIndex = data?.sources ? data : { sources: {} }
        return cachedIndex
      })
      .catch(() => {
        cachedIndex = { sources: {} }
        return cachedIndex
      })
  }
  return indexPromise
}

export function mediaSourceKey(src) {
  if (!src || src.startsWith('data:') || src.startsWith('blob:')) return null

  let url
  try {
    url = new URL(src, window.location.origin)
  } catch {
    return null
  }

  if (!url.pathname.startsWith(MEDIA_PREFIX)) return null

  const key = decodeURIComponent(url.pathname.slice(MEDIA_PREFIX.length))
  if (!key || key.startsWith('_variants/')) return null
  if (!SUPPORTED_EXTENSIONS.has(extensionOf(key))) return null
  return key
}

function variantUrl(originalSrc, variantKey) {
  let url
  try {
    url = new URL(originalSrc, window.location.origin)
  } catch {
    return `${MEDIA_PREFIX}${encodeObjectKey(variantKey)}`
  }

  const encodedKey = encodeObjectKey(variantKey)
  if (/^https?:\/\//i.test(originalSrc) || originalSrc.startsWith('//')) {
    return `${url.origin}${MEDIA_PREFIX}${encodedKey}`
  }
  return `${MEDIA_PREFIX}${encodedKey}`
}

function normalizeVariants(src, index) {
  const sourceKey = mediaSourceKey(src)
  if (!sourceKey) return null

  const webp = index?.sources?.[sourceKey]?.webp
  if (!webp) return null

  const variants = VARIANT_ORDER
    .map((name) => {
      const entry = webp[name]
      if (!entry?.key) return null
      return {
        name,
        width: entry.width || VARIANT_WIDTHS[name],
        url: variantUrl(src, entry.key),
      }
    })
    .filter(Boolean)

  return variants.length ? variants : null
}

export function useMediaVariants(src) {
  const [index, setIndex] = useState(cachedIndex)

  useEffect(() => {
    let mounted = true
    if (!mediaSourceKey(src)) return undefined
    loadVariantIndex().then((loaded) => {
      if (mounted) setIndex(loaded)
    })
    return () => {
      mounted = false
    }
  }, [src])

  return useMemo(() => normalizeVariants(src, index), [src, index])
}

export function OptimizedImage({ src, alt, className, sizes, loading = 'lazy', ...props }) {
  const variants = useMediaVariants(src)
  const webpSrcSet = variants
    ?.map((variant) => `${variant.url} ${variant.width}w`)
    .join(', ')

  return (
    <picture>
      {webpSrcSet && <source type="image/webp" srcSet={webpSrcSet} sizes={sizes} />}
      <img src={src} alt={alt || ''} className={className} loading={loading} {...props} />
    </picture>
  )
}
