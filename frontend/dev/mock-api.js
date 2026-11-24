/**
 * 개발 전용 가짜 백엔드(vite --mode mock 일 때만 붙는다. 운영 빌드에는 들어가지 않는다).
 *
 * blog-api(FastAPI) 로컬 환경이 아직 없을 때 작성·메모·챗봇 UI를 끝까지 눌러 보려고 만든 것이다.
 * 데이터는 메모리에만 있다(서버를 다시 띄우면 초기화). 계약은 H1의 blog-api와 같게 맞췄다:
 *   인증 /api/auth/{login,refresh,me}/ · 글 /api/posts/ · 업로드 /api/upload/
 *   메모 /api/notes/ (+ /tags/, /{id}/convert-to-post/) · 챗 /api/chat/ (SSE/JSON), /api/chat/feedback/
 * 로그인: 아무 비밀번호나 됨. 사용자명 hj → staff, guest → 일반 사용자(가드 확인용).
 * 챗: 질문에 "에러"가 있으면 503, "바빠"면 busy 이벤트, "느리게"면 천천히 흘린다.
 */
import { randomUUID } from 'node:crypto'

const now = () => new Date().toISOString()
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const SLUG_RE = /^[-a-zA-Z0-9_]+$/

const USERS = {
  hj: { id: 1, username: 'hj', email: 'hj@local', is_staff: true },
  guest: { id: 2, username: 'guest', email: 'guest@local', is_staff: false },
}

const categories = [
  { id: 1, name: 'AI/ML', slug: 'ai-ml', color: '#8b5cf6', parent: null, children: [
    { id: 11, name: 'LLM', slug: 'llm', color: '#8b5cf6', parent: 1, children: [] },
    { id: 12, name: 'Paper Review', slug: 'paper', color: '#8b5cf6', parent: 1, children: [] },
  ] },
  { id: 2, name: 'Cloud', slug: 'cloud', color: '#0ea5e9', parent: null, children: [
    { id: 21, name: 'Kubernetes', slug: 'kubernetes', color: '#0ea5e9', parent: 2, children: [] },
  ] },
]
const flatCats = categories.flatMap((c) => [c, ...c.children])
const tags = [
  { id: 1, name: 'llm', slug: 'llm', post_count: 1 },
  { id: 2, name: 'k8s', slug: 'k8s', post_count: 1 },
]
const series = [{ id: 1, name: 'LLM 서빙 노트', slug: 'llm-serving', description: '', order: 0, post_count: 1 }]
const templates = [
  { id: 1, name: '논문 리뷰', description: '요약 · 방법 · 실험 · 생각', post_type: 'paper_review', category: null,
    content_template: '## 한 줄 요약\n\n## 문제 정의\n\n## 방법\n\n## 실험\n\n## 생각\n' },
  { id: 2, name: 'TIL', description: '오늘 배운 것', post_type: 'til', category: null,
    content_template: '## 오늘 배운 것\n\n## 왜 중요한가\n\n## 참고\n' },
]

let postSeq = 3
const posts = new Map()
function seedPost(p) { posts.set(p.slug, p) }
seedPost({
  id: 1, title: 'vLLM으로 LLM 서빙하기', slug: 'vllm-serving', status: 'published', post_type: 'article',
  summary: 'PagedAttention과 연속 배칭으로 처리량을 끌어올리는 방법.', category: 11, tags: [1], series: 1, series_order: 1,
  content: '## 왜 vLLM인가\n\nPagedAttention 덕분에 KV 캐시 낭비가 줄어든다.\n\n## 설정\n\n```bash\npip install vllm\n```\n',
  created_at: '2026-11-01T09:00:00Z', updated_at: '2026-11-02T09:00:00Z', published_at: '2026-11-02T09:00:00Z',
  view_count: 120, cover: null, arxiv_url: '', venue: '', paper_year: null, paper_authors: '',
})
seedPost({
  id: 2, title: 'k3s 클러스터 메모(초안)', slug: 'k3s-cluster-notes', status: 'draft', post_type: 'til',
  summary: '', category: 21, tags: [2], series: null, series_order: 0,
  content: '쓰다 만 초안입니다.\n\n- traefik 대신 nginx ingress\n',
  created_at: '2026-11-20T09:00:00Z', updated_at: '2026-11-23T09:00:00Z', published_at: null,
  view_count: 0, cover: null, arxiv_url: '', venue: '', paper_year: null, paper_authors: '',
})

let noteSeq = 4
const notes = [
  { id: 1, title: '블로그 글감', content: '- RAG 평가 지표 정리\n- k8s 비용 줄이기', tags: ['idea'], pinned: true, archived: false, color: 'yellow', linked_post_id: null, linked_post_slug: null, created_at: '2026-11-20T01:00:00Z', updated_at: '2026-11-24T01:00:00Z' },
  { id: 2, title: '회의 메모', content: '배포 창: 목요일 오후', tags: ['work'], pinned: false, archived: false, color: '', linked_post_id: null, linked_post_slug: null, created_at: '2026-11-21T01:00:00Z', updated_at: '2026-11-22T01:00:00Z' },
  { id: 3, title: '지난 분기 회고', content: '보관해 둔 메모', tags: ['retro'], pinned: false, archived: true, color: 'gray', linked_post_id: null, linked_post_slug: null, created_at: '2026-10-01T01:00:00Z', updated_at: '2026-10-02T01:00:00Z' },
]

const media = new Map() // id → { type, buf }

// ── 직렬화(blog-api 응답 모양) ──────────────────────────
const catObj = (id) => {
  const c = flatCats.find((x) => String(x.id) === String(id))
  if (!c) return null
  const parent = c.parent ? flatCats.find((x) => x.id === c.parent) : null
  return { id: c.id, name: c.name, slug: c.slug, color: c.color, parent: parent ? { id: parent.id, name: parent.name, slug: parent.slug } : null }
}
const tagObjs = (ids) => (ids || []).map((id) => tags.find((t) => t.id === Number(id))).filter(Boolean)
const seriesObj = (id) => series.find((s) => String(s.id) === String(id)) || null
const listPost = (p) => ({
  id: p.id, title: p.title, slug: p.slug, summary: p.summary, category: catObj(p.category), categories: [],
  tags: tagObjs(p.tags), series_name: seriesObj(p.series)?.name || null, series_order: p.series_order,
  post_type: p.post_type, status: p.status, reading_time: 1, view_count: p.view_count, quality_score: null,
  is_pinned: false, cover_image_url: p.cover, figure_url: null, created_at: p.created_at, published_at: p.published_at,
  updated_at: p.updated_at,
})
const detailPost = (p) => ({
  ...listPost(p), content: p.content, series: seriesObj(p.series), arxiv_url: p.arxiv_url, venue: p.venue,
  paper_year: p.paper_year, paper_authors: p.paper_authors, related_posts: [], outgoing_links: [], incoming_links: [],
  author: { id: 1, username: 'hj' },
})

// ── HTTP 도우미 ────────────────────────────────────────
function send(res, status, body, headers = {}) {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json; charset=utf-8')
  for (const [k, v] of Object.entries(headers)) res.setHeader(k, v)
  res.end(body === undefined ? '' : JSON.stringify(body))
}
async function readBody(req) {
  const chunks = []
  for await (const c of req) chunks.push(c)
  return Buffer.concat(chunks)
}
async function readJson(req) {
  const buf = await readBody(req)
  if (!buf.length) return {}
  try { return JSON.parse(buf.toString('utf8')) } catch { return null }
}
/** multipart/form-data에서 첫 파일 하나만 꺼낸다(개발용 최소 구현). */
function firstFile(buf, contentType) {
  const m = /boundary=(?:"([^"]+)"|([^;]+))/.exec(contentType || '')
  if (!m) return null
  const boundary = Buffer.from(`--${m[1] || m[2]}`)
  let pos = buf.indexOf(boundary)
  while (pos !== -1) {
    const next = buf.indexOf(boundary, pos + boundary.length)
    if (next === -1) break
    const part = buf.subarray(pos + boundary.length + 2, next - 2)
    const sep = part.indexOf('\r\n\r\n')
    if (sep !== -1) {
      const head = part.subarray(0, sep).toString('utf8')
      if (/filename="/.test(head)) {
        const type = /content-type:\s*([^\r\n]+)/i.exec(head)?.[1] || 'application/octet-stream'
        const name = /filename="([^"]*)"/.exec(head)?.[1] || 'file'
        return { type, name, buf: Buffer.from(part.subarray(sep + 4)) }
      }
    }
    pos = next
  }
  return null
}
function authUser(req) {
  const h = req.headers.authorization || ''
  const m = /^Bearer mock-access-(\w+)$/.exec(h)
  return m ? USERS[m[1]] || null : null
}
const paginate = (items, page, size, base) => {
  const p = Math.max(1, Number(page) || 1)
  const start = (p - 1) * size
  return {
    count: items.length,
    next: start + size < items.length ? `${base}?page=${p + 1}` : null,
    previous: p > 1 ? `${base}?page=${p - 1}` : null,
    results: items.slice(start, start + size),
  }
}

// ── 챗(SSE) ────────────────────────────────────────────
async function chat(req, res, body) {
  const message = String(body?.message || '').trim()
  if (!message) return send(res, 400, { error: 'message_required', message: 'Message is required' })
  if (message.includes('에러')) return send(res, 503, { error: 'not_ready', message: '서비스를 준비 중이에요. 잠시 후 다시 시도해 주세요.' })
  if (message.includes('제한')) return send(res, 429, { error: 'rate_limited', message: '요청이 많아요. 잠시 후 다시 시도해 주세요.' }, { 'Retry-After': '20' })
  const sessionId = body.session_id || randomUUID()
  const sources = [...posts.values()].filter((p) => p.status === 'published').slice(0, 2).map((p) => ({ title: p.title, slug: p.slug }))
  const answer = `**모의 답변**이에요. "${message.slice(0, 40)}"에 대해 블로그 글을 찾아봤어요.\n\n- vLLM은 PagedAttention으로 KV 캐시를 아껴요.\n- 자세한 내용은 아래 참고 글을 보세요.\n\n[내부 링크 예시](/series)`
  const messageId = randomUUID().replace(/-/g, '')
  const done = { type: 'done', session_id: sessionId, message_id: messageId, feedback_token: `fb-${messageId.slice(0, 12)}`, grounded: true }
  const accept = req.headers.accept || ''
  if (!accept.includes('text/event-stream')) {
    await sleep(600)
    return send(res, 200, { session_id: sessionId, message: answer, sources, web_sources: [], message_id: messageId, feedback_token: done.feedback_token, grounded: true })
  }
  res.statusCode = 200
  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('X-Accel-Buffering', 'no')
  const ev = (o) => res.write(`data: ${JSON.stringify(o)}\n\n`)
  let closed = false
  req.on('close', () => { closed = true })
  await sleep(500)
  if (message.includes('바빠')) {
    ev({ type: 'error', content: '지금 질문이 몰려 있어요. 잠시 후 다시 물어봐 주세요.', code: 'busy' })
    ev({ ...done, grounded: null })
    return res.end()
  }
  ev({ type: 'sources', sources })
  const delay = message.includes('느리게') ? 250 : 40
  for (let i = 0; i < answer.length && !closed; i += 6) {
    ev({ type: 'token', content: answer.slice(i, i + 6) })
    await sleep(delay)
  }
  if (!closed) ev(done)
  res.end()
}

// ── 라우터 ─────────────────────────────────────────────
async function handle(req, res) {
  const url = new URL(req.url, 'http://mock')
  const path = url.pathname
  const q = url.searchParams
  const method = req.method
  const user = authUser(req)
  await sleep(120)

  if (path.startsWith('/media/mock/')) {
    const m = media.get(path.slice('/media/mock/'.length))
    if (!m) return send(res, 404, { detail: 'Not found.' })
    res.setHeader('Content-Type', m.type)
    return res.end(m.buf)
  }

  // 인증
  if (path === '/api/auth/login/' && method === 'POST') {
    const b = await readJson(req)
    const u = USERS[b?.username]
    if (!u || !b?.password) return send(res, 401, { detail: 'No active account found with the given credentials' })
    return send(res, 200, { access: `mock-access-${u.username}`, refresh: `mock-refresh-${u.username}` })
  }
  if (path === '/api/auth/refresh/' && method === 'POST') {
    const b = await readJson(req)
    const m = /^mock-refresh-(\w+)$/.exec(b?.refresh || '')
    if (!m) return send(res, 401, { detail: 'Token is invalid or expired' })
    return send(res, 200, { access: `mock-access-${m[1]}` })
  }
  if (path === '/api/auth/me/') return user ? send(res, 200, user) : send(res, 401, { detail: 'Authentication credentials were not provided.' })

  // 챗
  if (path === '/api/chat/' && method === 'POST') return chat(req, res, await readJson(req))
  if (path === '/api/chat/feedback/' && method === 'POST') {
    const b = await readJson(req)
    if (!b?.message_id || !b?.feedback_token) return send(res, 422, { detail: 'invalid' })
    return send(res, 200, { ok: true, recorded: true })
  }

  // 분류
  if (path === '/api/categories/' && method === 'GET') return send(res, 200, categories)
  if (path === '/api/tags/' && method === 'GET') return send(res, 200, tags)
  if (path === '/api/series/' && method === 'GET') return send(res, 200, { count: series.length, next: null, previous: null, results: series })
  if (path === '/api/templates/' && method === 'GET') return send(res, 200, templates)

  // 업로드
  if (path === '/api/upload/' && method === 'POST') {
    if (!user) return send(res, 401, { detail: 'Authentication credentials were not provided.' })
    const f = firstFile(await readBody(req), req.headers['content-type'])
    if (!f) return send(res, 400, { image: ['No file was submitted.'] })
    const id = randomUUID()
    media.set(id, f)
    return send(res, 201, { id: media.size, image: `/media/mock/${id}`, image_type: 'general', caption: '', created_at: now() })
  }

  // 글
  const postM = /^\/api\/posts\/([^/]+)\/(?:(cover)\/)?$/.exec(path)
  if (path === '/api/posts/' && method === 'GET') {
    let list = [...posts.values()]
    if (!user) list = list.filter((p) => p.status === 'published')
    if (q.get('status')) list = list.filter((p) => p.status === q.get('status'))
    if (q.get('search')) list = list.filter((p) => (p.title + p.content).includes(q.get('search')))
    list.sort((a, b) => b.created_at.localeCompare(a.created_at))
    return send(res, 200, paginate(list.map(listPost), q.get('page'), Number(q.get('page_size')) || 10, '/api/posts/'))
  }
  if (path === '/api/posts/' && method === 'POST') {
    if (!user?.is_staff) return send(res, 403, { detail: 'You do not have permission to perform this action.' })
    const b = (await readJson(req)) || {}
    const errs = {}
    if (!b.title?.trim()) errs.title = ['This field may not be blank.']
    if (!b.content?.trim()) errs.content = ['This field may not be blank.']
    if (!b.slug) errs.slug = ['This field is required.']
    else if (!SLUG_RE.test(b.slug)) errs.slug = ['Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.']
    else if (posts.has(b.slug)) errs.slug = ['post with this slug already exists.']
    if (Object.keys(errs).length) return send(res, 400, errs)
    const p = {
      id: postSeq++, title: b.title, slug: b.slug, content: b.content, summary: b.summary || '', category: b.category || null,
      tags: b.tags || [], series: b.series || null, series_order: b.series_order || 0, post_type: b.post_type || 'article',
      status: b.status || 'draft', published_at: b.published_at || null, created_at: now(), updated_at: now(), view_count: 0, cover: null,
      arxiv_url: b.arxiv_url || '', venue: b.venue || '', paper_year: b.paper_year || null, paper_authors: b.paper_authors || '',
    }
    posts.set(p.slug, p)
    return send(res, 201, { ...b, slug: p.slug })
  }
  if (postM) {
    const slug = decodeURIComponent(postM[1])
    const p = posts.get(slug)
    if (!p || (!user && p.status !== 'published')) return send(res, 404, { detail: 'Not found.' })
    if (postM[2] === 'cover' && method === 'POST') {
      const f = firstFile(await readBody(req), req.headers['content-type'])
      if (!f) return send(res, 400, { detail: 'file이 필요합니다.' })
      const id = randomUUID()
      media.set(id, f)
      p.cover = `/media/mock/${id}`
      return send(res, 200, { cover_image_url: p.cover })
    }
    if (method === 'GET') return send(res, 200, detailPost(p))
    if (!user?.is_staff) return send(res, 403, { detail: 'You do not have permission to perform this action.' })
    if (method === 'PATCH' || method === 'PUT') {
      const b = (await readJson(req)) || {}
      if (b.slug !== undefined && b.slug !== slug) {
        if (!SLUG_RE.test(b.slug)) return send(res, 400, { slug: ['Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.'] })
        if (posts.has(b.slug)) return send(res, 400, { slug: ['post with this slug already exists.'] })
      }
      if (b.title !== undefined && !String(b.title).trim()) return send(res, 400, { title: ['This field may not be blank.'] })
      Object.assign(p, b, { updated_at: now() })
      if (b.slug && b.slug !== slug) { posts.delete(slug); posts.set(b.slug, p) }
      return send(res, 200, { ...b, slug: p.slug })
    }
    if (method === 'DELETE') { posts.delete(slug); res.statusCode = 204; return res.end() }
  }

  // 메모 (staff 전용)
  if (path.startsWith('/api/notes/')) {
    if (!user) return send(res, 401, { detail: 'Authentication credentials were not provided.' })
    if (!user.is_staff) return send(res, 403, { detail: 'You do not have permission to perform this action.' })
    if (path === '/api/notes/tags/' && method === 'GET') {
      const counts = {}
      notes.forEach((n) => n.tags.forEach((t) => { counts[t] = (counts[t] || 0) + 1 }))
      return send(res, 200, Object.entries(counts).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count))
    }
    if (path === '/api/notes/' && method === 'GET') {
      let list = [...notes]
      const archived = q.get('archived')
      if (archived === 'true') list = list.filter((n) => n.archived)
      else if (archived === 'false' || archived === null) list = list.filter((n) => !n.archived)
      if (q.get('pinned') === 'true') list = list.filter((n) => n.pinned)
      if (q.get('tag')) list = list.filter((n) => n.tags.includes(q.get('tag')))
      if (q.get('q')) { const s = q.get('q').toLowerCase(); list = list.filter((n) => (n.title + n.content).toLowerCase().includes(s)) }
      list.sort((a, b) => (b.pinned - a.pinned) || b.updated_at.localeCompare(a.updated_at))
      return send(res, 200, paginate(list, q.get('page'), 20, '/api/notes/'))
    }
    if (path === '/api/notes/' && method === 'POST') {
      const b = (await readJson(req)) || {}
      const n = {
        id: noteSeq++, title: String(b.title ?? '').slice(0, 200), content: String(b.content ?? ''), tags: Array.isArray(b.tags) ? b.tags : [],
        pinned: Boolean(b.pinned), archived: Boolean(b.archived), color: b.color || null, linked_post_id: null, linked_post_slug: null, created_at: now(), updated_at: now(),
      }
      notes.unshift(n)
      return send(res, 201, n)
    }
    const nm = /^\/api\/notes\/(\d+)\/(?:(convert-to-post)\/)?$/.exec(path)
    if (nm) {
      const n = notes.find((x) => x.id === Number(nm[1]))
      if (!n) return send(res, 404, { detail: 'Not found.' })
      if (nm[2] && method === 'POST') {
        const slug = `note-${n.id}-${Date.now().toString(36)}`
        posts.set(slug, {
          id: postSeq++, title: n.title || '메모에서 만든 글', slug, content: n.content || '(본문 없음)', summary: '', category: null, tags: [],
          series: null, series_order: 0, post_type: 'article', status: 'draft', published_at: null, created_at: now(), updated_at: now(),
          view_count: 0, cover: null, arxiv_url: '', venue: '', paper_year: null, paper_authors: '',
        })
        n.linked_post_id = postSeq - 1
        n.linked_post_slug = slug
        n.updated_at = now()
        return send(res, 201, { slug })
      }
      if (method === 'GET') return send(res, 200, n)
      if (method === 'PATCH') {
        const b = (await readJson(req)) || {}
        for (const k of ['title', 'content', 'tags', 'pinned', 'archived', 'color']) if (k in b) n[k] = k === 'color' && b[k] === '' ? null : b[k]
        n.updated_at = now()
        return send(res, 200, n)
      }
      if (method === 'DELETE') { notes.splice(notes.indexOf(n), 1); res.statusCode = 204; return res.end() }
    }
  }

  // 대시보드·기타
  if (path === '/api/dashboard/stats/') {
    const all = [...posts.values()]
    return send(res, 200, {
      total_posts: all.length, published: all.filter((p) => p.status === 'published').length,
      drafts: all.filter((p) => p.status === 'draft').length, total_views: 120,
      image_coverage: { missing_image: all.filter((p) => !p.cover).length },
    })
  }
  if (path === '/api/audit/results/') return send(res, 200, { results: [], total_issues: 0 })
  if (path === '/api/posts/search/') return send(res, 200, { results: [] })
  if (method === 'GET') return send(res, 200, { count: 0, next: null, previous: null, results: [] })
  return send(res, 404, { detail: 'Not found. (mock)' })
}

export default function mockApi() {
  return {
    name: 'blog-mock-api',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (!req.url.startsWith('/api/') && !req.url.startsWith('/media/mock/')) return next()
        handle(req, res).catch((err) => {
          server.config.logger.error(`[mock-api] ${err.stack || err}`)
          if (!res.headersSent) send(res, 500, { detail: 'mock error' })
          else res.end()
        })
      })
      server.config.logger.info('  [mock-api] 가짜 백엔드 사용 중 · 로그인: hj(staff) / guest(일반), 비밀번호 아무거나')
    },
  }
}
