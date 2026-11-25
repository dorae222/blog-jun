import client from './client'
import { createSSEParser } from '../utils/sse'
import { feedbackPayload } from '../utils/feedback'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

/** 비스트리밍(JSON) 호출. 스트리밍이 안 될 때의 폴백. */

/**
 * 지금 보고 있는 화면. 챗봇이 "여기/이 글"을 해석하는 데 쓴다(서버가 slug를 DB로 다시 확인한다).
 * - /post/<slug> → post_slug, /series?s=<slug> → series_slug
 */
export function currentPage() {
  if (typeof window === 'undefined') return undefined
  const { pathname, search } = window.location
  const page = { path: (pathname + search).slice(0, 300) }
  const m = pathname.match(/^\/post\/([^/]+)\/?$/)
  if (m) {
    try { page.post_slug = decodeURIComponent(m[1]).slice(0, 200) } catch { /* 잘못된 인코딩은 무시 */ }
  }
  if (pathname.replace(/\/$/, '') === '/series') {
    const s = new URLSearchParams(search).get('s')
    if (s) page.series_slug = s.slice(0, 200)
  }
  const title = (document.title || '').replace(/\s*[·|-]\s*HJ Tech.*$/i, '').trim()
  if (title) page.title = title.slice(0, 300)
  return page
}

export const sendMessage = (message, sessionId, turnstileToken) =>
  client.post('/chat/', { message, session_id: sessionId || undefined, page: currentPage() }, {
    headers: turnstileToken ? { 'X-Turnstile-Token': turnstileToken } : {},
    timeout: 120000,
  })

export const sendFeedback = (args) => client.post('/chat/feedback/', feedbackPayload(args))

/** 서버가 돌려준 오류를 화면에 쓸 형태로 맞춘다. */
export class ChatError extends Error {
  constructor(message, { status, code, retryAfter } = {}) {
    super(message)
    this.status = status
    this.code = code
    this.retryAfter = retryAfter
  }
}

const STATUS_MESSAGES = {
  403: '봇 확인에 실패했어요. 다시 시도해 주세요.',
  413: '질문이 너무 길어요. 조금 줄여 주세요.',
  429: '요청이 많아 잠시 제한됐어요.',
  503: '서비스를 준비 중이에요. 잠시 후 다시 시도해 주세요.',
}

async function toChatError(res) {
  let body = {}
  try { body = await res.json() } catch { /* 본문이 JSON이 아니면 상태 코드로만 안내 */ }
  const retryAfter = Number(res.headers.get('Retry-After')) || undefined
  return new ChatError(body.message || STATUS_MESSAGES[res.status] || '답변을 받지 못했어요.', {
    status: res.status, code: body.error, retryAfter,
  })
}

/**
 * SSE 스트리밍 호출. 이벤트(sources/token/error/done)마다 onEvent를 부른다.
 *
 * 스트림을 못 여는 환경(프록시가 버퍼링하거나 body가 없는 경우)에서는 JSON으로 다시 묻고
 * 같은 이벤트 모양으로 흉내 내서 화면 코드는 한 갈래만 다루게 한다.
 * 이미 토큰을 받기 시작한 뒤 끊기면 재요청하지 않는다(답이 두 번 섞이지 않게).
 */
export async function streamChat({ message, sessionId, turnstileToken, signal, onEvent }) {
  const headers = { 'Content-Type': 'application/json', Accept: 'text/event-stream' }
  const token = localStorage.getItem('access_token')
  if (token) headers.Authorization = `Bearer ${token}`
  if (turnstileToken) headers['X-Turnstile-Token'] = turnstileToken

  let res
  try {
    res = await fetch(`${API_BASE}/chat/`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message, session_id: sessionId || undefined, page: currentPage() }),
      signal,
    })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    return jsonFallback({ message, sessionId, turnstileToken, onEvent })
  }

  if (!res.ok) throw await toChatError(res)

  const type = res.headers.get('content-type') || ''
  if (!type.includes('text/event-stream') || !res.body) {
    // 서버가 JSON으로 답했으면 그걸 그대로 쓴다.
    const data = await res.json()
    emitJson(data, onEvent)
    return { mode: 'json' }
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let gotDone = false
  const parser = createSSEParser((ev) => {
    if (ev.type === 'done') gotDone = true
    onEvent(ev)
  })
  try {
    for (;;) {
      const { value, done } = await reader.read()
      if (done) break
      parser.push(decoder.decode(value, { stream: true }))
    }
    parser.push(decoder.decode())
    parser.end()
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new ChatError('연결이 끊겼어요. 다시 시도해 주세요.', { code: 'stream_broken' })
  }
  if (!gotDone) onEvent({ type: 'done' })
  return { mode: 'sse' }
}

async function jsonFallback({ message, sessionId, turnstileToken, onEvent }) {
  try {
    const { data } = await sendMessage(message, sessionId, turnstileToken)
    emitJson(data, onEvent)
    return { mode: 'json' }
  } catch (err) {
    const status = err.response?.status
    const body = err.response?.data || {}
    throw new ChatError(body.message || STATUS_MESSAGES[status] || '서버에 연결하지 못했어요.', {
      status, code: body.error || 'network',
      retryAfter: Number(err.response?.headers?.['retry-after']) || undefined,
    })
  }
}

function emitJson(data, onEvent) {
  onEvent({ type: 'sources', sources: data.sources || [] })
  if (data.message) onEvent({ type: 'token', content: data.message })
  onEvent({
    type: 'done',
    session_id: data.session_id,
    message_id: data.message_id,
    feedback_token: data.feedback_token,
  })
}
