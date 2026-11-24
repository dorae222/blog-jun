import client from '../api/client'
import { CATEGORY_TREE as FALLBACK } from './categories'

/**
 * 카테고리 트리의 진실 원천은 DB다.
 *
 * 예전에는 프런트에 트리를 하드코딩해 뒀는데, 서버에서 카테고리를 만들거나 지울 때마다
 * 두 곳이 어긋났다. `/posts/data/graphdb`가 빈 화면이던 것도, 프런트에만 있는
 * `big-data`가 목록에 뜨던 것도 전부 그 드리프트였다.
 *
 * 그래서 목록은 API에서 받아 쓰고, 첫 렌더가 비지 않도록 정적 파일을 초기값으로만 쓴다.
 * 글이 없는 카테고리는 네비게이션에서 감춘다 - 눌렀는데 아무것도 없는 칸을 만들지 않는다.
 */

// 대탭을 9개로 쪼개면서 슬러그가 곧 URL 조각이 됐다. 별칭은 옛 주소 호환용으로만 남긴다.
const SLUG_TO_ROUTE = {}
export const LEGACY_ROUTE_ALIAS = {
  ai: 'llm', 'ai-ml': 'llm', cloud: 'aws', 'data-engineering': 'data',
}
const ROUTE_TO_SLUG = Object.fromEntries(
  Object.entries(SLUG_TO_ROUTE).map(([slug, route]) => [route, slug]),
)

export function routeKeyOf(slug) {
  return SLUG_TO_ROUTE[slug] || slug
}

export function categorySlugOf(routeKey) {
  return ROUTE_TO_SLUG[routeKey] || LEGACY_ROUTE_ALIAS[routeKey] || routeKey
}

const PALETTE = {
  'ai-ml': '#FF6F00', ml: '#10B981', cloud: '#4A9EE0',
  'data-engineering': '#336791', tool: '#7C3AED',
}

function shape(rows) {
  return rows
    .filter((c) => !c.parent)
    .map((c) => {
      const key = routeKeyOf(c.slug)
      const subs = (c.children || [])
        .filter((k) => ((k.total_count ?? k.post_count) || 0) > 0)   // 빈 소분류는 감춘다
        .map((k) => ({ key: k.slug, label: k.name, count: k.total_count ?? k.post_count ?? 0 }))
      return {
        key,
        slug: c.slug,
        label: c.name,
        color: c.color || PALETTE[c.slug] || '#64748b',
        path: `/posts/${key}`,
        count: c.total_count ?? c.post_count ?? 0,
        subs,
      }
    })
    .filter((c) => c.count > 0 || c.subs.length > 0)
}

// 분류 개편으로 옛 캐시가 남아 목록이 0건으로 보였다. 키에 버전을 박아 버린다.
const CACHE_KEY = 'categoryTree.v2'

let cached = null
let inflight = null

export function getCachedTree() {
  if (cached) return cached
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length) {
        cached = parsed
        return cached
      }
    }
  } catch { /* 저장소가 막혀 있으면 그냥 기본값을 쓴다 */ }
  return FALLBACK
}

export function loadCategoryTree() {
  if (cached) return Promise.resolve(cached)
  if (!inflight) {
    inflight = client.get('/categories/', { params: { page_size: 200 } })
      .then((r) => {
        const rows = r.data?.results ?? r.data ?? []
        const tree = shape(rows)
        if (tree.length) {
          cached = tree
          try { localStorage.setItem(CACHE_KEY, JSON.stringify(tree)) } catch { /* 무시 */ }
        }
        return cached || FALLBACK
      })
      .catch(() => FALLBACK)
      .finally(() => { inflight = null })
  }
  return inflight
}
