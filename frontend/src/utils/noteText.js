/**
 * 빠른 메모 한 줄에서 `#태그`를 뽑아낸다.
 * "회의 정리 #work #k8s" → { text: "회의 정리", tags: ["work", "k8s"] }
 * 태그는 공백 전까지(한글 허용), 중복은 한 번만, 소문자로 맞춘다.
 * URL 조각(예: page#section)은 태그로 보지 않도록 앞이 공백이거나 줄 처음일 때만 인정한다.
 */
const TAG_RE = /(^|\s)#([\p{L}\p{N}_\-/.]+)/gu

export function parseQuickNote(input) {
  const tags = []
  const text = String(input || '')
    .replace(TAG_RE, (_m, lead, tag) => {
      const t = tag.replace(/[.\-/]+$/, '').toLowerCase()
      if (t && !tags.includes(t)) tags.push(t)
      return lead
    })
    .replace(/\s{2,}/g, ' ')
    .trim()
  return { text, tags }
}

/** 메모 제목: 첫 줄을 최대 max자까지. 비면 "제목 없는 메모". */
export function noteTitleFrom(text, max = 80) {
  const first = String(text || '').split('\n').find((l) => l.trim()) || ''
  const clean = first.replace(/^#+\s*/, '').trim()
  if (!clean) return '제목 없는 메모'
  return clean.length > max ? `${clean.slice(0, max - 1)}…` : clean
}

/**
 * 글 slug. 서버(blog-api/Django DRF SlugField)는 `^[-a-zA-Z0-9_]+$`만 받는다(한글 불가).
 * 그래서 제목에서 영문 소문자·숫자만 남기고 나머지는 하이픈 하나로 묶는다.
 */
export function slugify(title, max = 120) {
  return String(title || '')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, max)
    .replace(/-+$/g, '')
}

/** 서버가 받아 주는 slug 형식(blog-api fields.SlugField와 같은 규칙). */
export const SLUG_RE = /^[-a-zA-Z0-9_]+$/

/**
 * 새 글의 자동 slug. 한글 제목은 영문이 거의 안 남으므로 날짜 꼬리(suffix)를 붙여 겹치지 않게 한다.
 * suffix는 편집 세션마다 한 번 정해 두고 넘겨야 타이핑할 때마다 바뀌지 않는다.
 */
export function autoSlug(title, suffix) {
  const base = slugify(title, 80)
  const hasNonAscii = /[^\x00-\x7f]/.test(String(title || ''))
  if (!base) return `post-${suffix}`
  return hasNonAscii || base.length < 4 ? `${base}-${suffix}` : base
}

/** autoSlug용 꼬리: YYYYMMDD-HHMM */
export function slugSuffix(d = new Date()) {
  const p = (n) => String(n).padStart(2, 0)
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`
}

/** "방금", "12초 전", "3분 전", "2시간 전", 그 이상은 날짜. */
export function timeAgo(date, now = Date.now()) {
  if (!date) return ''
  const t = typeof date === 'number' ? date : new Date(date).getTime()
  if (Number.isNaN(t)) return ''
  const s = Math.max(0, Math.round((now - t) / 1000))
  if (s < 5) return '방금'
  if (s < 60) return `${s}초 전`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}분 전`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}시간 전`
  const d = new Date(t)
  return `${d.getMonth() + 1}월 ${d.getDate()}일`
}

/** 내부 글 slug로 쓸 수 있는 값인지(챗봇 출처 링크를 /post/:slug로만 보내기 위함). */
export function isSafeSlug(slug) {
  return typeof slug === 'string' && slug.length > 0 && slug.length <= 300
    && !/[/?#\\\s]/.test(slug) && !slug.startsWith('.')
}

/** 입력 중인지: 단축키는 이때 꺼야 한다. */
export function isTypingTarget(el) {
  if (!el || typeof el !== 'object') return false
  const tag = (el.tagName || '').toUpperCase()
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
  return Boolean(el.isContentEditable)
}
