import { useCallback, useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { X, Send, Square, MessageSquarePlus, Bot, Maximize2, Minimize2 } from 'lucide-react'
import ChatMessage from './ChatMessage'
import TurnstileWidget, { turnstileEnabled } from './TurnstileWidget'
import useFocusTrap from '../../hooks/useFocusTrap'
import { streamChat, sendFeedback, currentPage } from '../../api/chat'
import { isCoarsePointer } from '../../utils/pointer'

const STORE_KEY = 'chat:v1'
const MAX_INPUT = 2000
const GREETING = { id: 'greet', role: 'assistant', status: 'done', content: '안녕하세요! 블로그 글에 대해 궁금한 걸 물어보세요. 답변 아래에 참고한 글을 달아 드려요.' }

// 데스크톱(sm 이상) 창 크기. 왼쪽 아래(left-6, bottom-24)에 붙어 있으므로 오른쪽·위로 넓어진다.
const SIZE_KEY = 'chat:size:v1'
const DEFAULT_SIZE = { w: 480, h: 704 }   // 30rem × 44rem
const MIN_SIZE = { w: 340, h: 420 }
const LARGE_MARGIN = { x: 48, y: 120 }    // 화면에서 좌우 24px씩, 위 24px·아래 96px(여는 버튼 자리)을 남긴다
const LARGE_MAX_W = 960                   // "크게"여도 한 줄이 너무 길면 읽기 어렵다
const isDesktop = () => typeof window !== 'undefined' && window.matchMedia('(min-width: 640px)').matches
const maxSize = () => ({ w: window.innerWidth - LARGE_MARGIN.x, h: window.innerHeight - LARGE_MARGIN.y })
const clampSize = ({ w, h }) => {
  const m = maxSize()
  return { w: Math.round(Math.max(MIN_SIZE.w, Math.min(w, m.w))), h: Math.round(Math.max(MIN_SIZE.h, Math.min(h, m.h))) }
}
function loadSize() {
  try {
    const d = JSON.parse(localStorage.getItem(SIZE_KEY) || 'null')
    if (d && Number.isFinite(d.w) && Number.isFinite(d.h)) return d
  } catch { /* 무시 */ }
  return DEFAULT_SIZE
}

const uid = () => (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`)

/** 대화는 탭을 닫기 전까지(sessionStorage) 이어진다. 진행 중이던 답변은 저장하지 않는다. */
function loadStore() {
  try {
    const d = JSON.parse(sessionStorage.getItem(STORE_KEY) || 'null')
    if (d?.messages?.length) return d
  } catch { /* 무시 */ }
  return { sessionId: null, messages: [GREETING] }
}
function saveStore(sessionId, messages) {
  try {
    const keep = messages.filter((m) => !m.queued && m.status !== 'connecting' && m.status !== 'streaming').slice(-40)
    sessionStorage.setItem(STORE_KEY, JSON.stringify({ sessionId, messages: keep }))
  } catch { /* 무시 */ }
}

/**
 * 블로그 챗봇 패널.
 * - SSE 스트리밍(fetch + ReadableStream), 안 되면 JSON 폴백(api/chat.js).
 * - 답변 중에 또 보내면 대기열에 쌓았다가 차례로 보낸다("대기 중" 표시).
 * - ESC로 닫기, Tab 포커스는 패널 안에서만 돈다. 닫으면 여는 버튼으로 포커스가 돌아간다.
 */
export default function ChatModal({ onClose }) {
  const init = useRef(loadStore()).current
  const [desktop, setDesktop] = useState(isDesktop)
  const [size, setSize] = useState(() => (isDesktop() ? clampSize(loadSize()) : DEFAULT_SIZE))
  const largeSize = () => clampSize({ w: Math.min(LARGE_MAX_W, maxSize().w), h: 99999 })
  const large = desktop && (() => { const l = largeSize(); return Math.abs(size.w - l.w) <= 4 && Math.abs(size.h - l.h) <= 4 })()
  const prevSizeRef = useRef(null)

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 640px)')
    const onMq = () => setDesktop(mq.matches)
    const onResize = () => setSize((s) => clampSize(s))
    mq.addEventListener('change', onMq)
    window.addEventListener('resize', onResize)
    return () => { mq.removeEventListener('change', onMq); window.removeEventListener('resize', onResize) }
  }, [])
  useEffect(() => {
    if (!desktop) return
    try { localStorage.setItem(SIZE_KEY, JSON.stringify(size)) } catch { /* 무시 */ }
  }, [size, desktop])

  // 오른쪽 위 모서리를 끌어서 크기 조절(포인터 캡처로 창 밖으로 나가도 계속 따라간다)
  const startResize = (axis) => (e) => {
    if (!desktop || e.button !== 0) return
    e.preventDefault()
    const start = { x: e.clientX, y: e.clientY, ...size }
    const el = e.currentTarget
    el.setPointerCapture?.(e.pointerId)
    const prevSelect = document.body.style.userSelect
    document.body.style.userSelect = "none"  // 끄는 동안 본문 글자가 선택되지 않게
    const move = (ev) => setSize(clampSize({
      w: axis.includes('x') ? start.w + (ev.clientX - start.x) : start.w,
      h: axis.includes('y') ? start.h - (ev.clientY - start.y) : start.h,
    }))
    const up = () => { document.body.style.userSelect = prevSelect; el.removeEventListener('pointermove', move); el.removeEventListener('pointerup', up); el.removeEventListener('pointercancel', up) }
    el.addEventListener('pointermove', move)
    el.addEventListener('pointerup', up)
    el.addEventListener('pointercancel', up)
  }
  const onResizeKey = (e) => {
    const step = e.shiftKey ? 64 : 16
    const d = { ArrowRight: [step, 0], ArrowLeft: [-step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] }[e.key]
    if (!d) return
    e.preventDefault()
    setSize((s) => clampSize({ w: s.w + d[0], h: s.h + d[1] }))
  }
  const toggleLarge = () => {
    if (large) setSize(clampSize(prevSizeRef.current || DEFAULT_SIZE))
    else { prevSizeRef.current = size; setSize(largeSize()) }
  }
  const [messages, setMessages] = useState(init.messages)
  const [sessionId, setSessionId] = useState(init.sessionId)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [tsToken, setTsToken] = useState('')
  const [tsReset, setTsReset] = useState(0)
  const boxRef = useRef(null)
  const inputRef = useRef(null)
  const logRef = useRef(null)
  const abortRef = useRef(null)
  const sessionRef = useRef(sessionId)
  const tsRef = useRef('')
  useEffect(() => { sessionRef.current = sessionId }, [sessionId])
  useEffect(() => { tsRef.current = tsToken }, [tsToken])

  useFocusTrap(boxRef, true, onClose)
  useEffect(() => { setTimeout(() => inputRef.current?.focus(), 50) }, [])
  useEffect(() => () => abortRef.current?.abort(), [])
  useEffect(() => { saveStore(sessionId, messages) }, [sessionId, messages])

  // 맨 아래 근처에 있을 때만 따라 내려간다(위로 올려 읽는 중이면 그대로 둔다).
  useEffect(() => {
    const el = logRef.current
    if (!el) return
    if (el.scrollHeight - el.scrollTop - el.clientHeight < 120) el.scrollTop = el.scrollHeight
  }, [messages])

  const patch = useCallback((id, fn) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...(typeof fn === 'function' ? fn(m) : fn) } : m)))
  }, [])

  const run = useCallback(async (userMsg) => {
    const aid = uid()
    setBusy(true)
    setMessages((prev) => [
      ...prev.map((m) => (m.id === userMsg.id ? { ...m, queued: false } : m)),
      { id: aid, role: 'assistant', status: 'connecting', content: '', sources: [], replyTo: userMsg.id },
    ])
    const controller = new AbortController()
    abortRef.current = controller
    let serverError = null
    try {
      await streamChat({
        message: userMsg.content,
        sessionId: sessionRef.current,
        turnstileToken: tsRef.current,
        signal: controller.signal,
        onEvent: (ev) => {
          if (ev.type === 'sources') patch(aid, { sources: ev.sources || [] })
          else if (ev.type === 'token') patch(aid, (m) => ({ content: m.content + (ev.content || ''), status: 'streaming' }))
          else if (ev.type === 'error') serverError = ev
          else if (ev.type === 'done') {
            if (ev.session_id) setSessionId(ev.session_id)
            patch(aid, (m) => (serverError && !m.content
              ? { status: 'error', error: serverError.content || '답변하지 못했어요.', code: serverError.code }
              : { status: 'done', messageId: ev.message_id, feedbackToken: ev.feedback_token }))
          }
        },
      })
    } catch (err) {
      if (err.name === 'AbortError') {
        patch(aid, (m) => ({ status: 'done', content: m.content ? `${m.content}\n\n_(중단함)_` : '_(중단함)_' }))
      } else {
        patch(aid, { status: 'error', error: err.message || '답변을 받지 못했어요.', retryAfter: err.retryAfter, code: err.code })
      }
    } finally {
      abortRef.current = null
      setBusy(false)
      if (turnstileEnabled) { setTsToken(''); setTsReset((n) => n + 1) }
    }
  }, [patch])

  // 대기열: 바쁘지 않고 대기 중인 질문이 있으면 다음 것을 보낸다.
  useEffect(() => {
    if (busy) return
    if (turnstileEnabled && !tsToken) return
    const next = messages.find((m) => m.role === 'user' && m.queued)
    if (next) run(next)
  }, [busy, messages, run, tsToken])

  const send = () => {
    const text = input.trim().slice(0, MAX_INPUT)
    if (!text) return
    setMessages((prev) => [...prev, { id: uid(), role: 'user', content: text, queued: true }])
    setInput('')
  }

  const retry = useCallback((assistantMsg) => {
    setMessages((prev) => {
      const without = prev.filter((m) => m.id !== assistantMsg.id)
      return without.map((m) => (m.id === assistantMsg.replyTo ? { ...m, queued: true } : m))
    })
  }, [])

  const feedback = useCallback(async (msg, value) => {
    patch(msg.id, { feedback: value })
    try {
      await sendFeedback({ messageId: msg.messageId, feedbackToken: msg.feedbackToken, value })
    } catch {
      patch(msg.id, { feedback: null })
      toast.error('피드백을 보내지 못했어요')
    }
  }, [patch])

  const reset = () => {
    abortRef.current?.abort()
    setMessages([GREETING])
    setSessionId(null)
  }

  const queuedCount = messages.filter((m) => m.role === 'user' && m.queued).length
  const waitingForBot = turnstileEnabled && !tsToken

  return (
    <motion.div
      ref={boxRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="chat-title"
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 40 }}
      transition={{ duration: 0.18 }}
      className="fixed z-50 inset-x-0 bottom-0 top-16 sm:top-auto sm:inset-x-auto sm:bottom-24 sm:left-6
        group/chat flex flex-col rounded-t-2xl sm:rounded-2xl shadow-2xl border overflow-hidden"
      style={{ background: 'var(--card-bg)', borderColor: 'var(--border)', ...(desktop ? { width: size.w, height: size.h } : {}) }}
    >
      {desktop && (
        <>
          {/* 크기 조절: 위·오른쪽 가장자리와 오른쪽 위 모서리. 평소엔 안 보이고, 올리면 얇은 강조선만 뜬다. */}
          <div aria-hidden="true" onPointerDown={startResize('y')} onDoubleClick={toggleLarge}
            className="group/rs absolute top-0 left-5 right-5 h-3 z-20 cursor-ns-resize touch-none select-none">
            <span className="absolute inset-x-0 top-0 h-0.5 rounded-full bg-primary-500 opacity-0 transition-opacity duration-150 group-hover/rs:opacity-60" />
          </div>
          <div aria-hidden="true" onPointerDown={startResize('x')} onDoubleClick={toggleLarge}
            className="group/rs absolute right-0 top-5 bottom-5 w-3 z-20 cursor-ew-resize touch-none select-none">
            <span className="absolute inset-y-0 right-0 w-0.5 rounded-full bg-primary-500 opacity-0 transition-opacity duration-150 group-hover/rs:opacity-60" />
          </div>
          <div
            role="separator"
            aria-orientation="horizontal"
            aria-label="채팅창 크기 조절 (방향키, Shift로 크게)"
            tabIndex={0}
            onPointerDown={startResize('xy')}
            onKeyDown={onResizeKey}
            onDoubleClick={toggleLarge}
            className="absolute top-0 right-0 w-5 h-5 z-30 cursor-nesw-resize touch-none select-none rounded-tr-2xl
              focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-primary-500"
          />
        </>
      )}
      {desktop && (
        <span aria-hidden="true"
          className="pointer-events-none absolute top-1.5 left-1/2 -translate-x-1/2 h-1 w-9 rounded-full opacity-40 transition-opacity duration-150 group-hover/chat:opacity-80"
          style={{ background: 'var(--border)' }} />
      )}
      <div className="px-4 pt-4 pb-3 sm:pt-4 border-b flex items-center gap-2" style={{ borderColor: 'var(--border)' }}>
        <Bot size={18} className="text-accent" />
        <h2 id="chat-title" className="font-semibold text-sm" style={{ color: 'var(--text)' }}>블로그에 물어보기</h2>
        <button onClick={reset} className="ml-auto p-1.5 rounded-lg hover:bg-black/5" title="새 대화" aria-label="새 대화"
          style={{ color: 'var(--text-secondary)' }}>
          <MessageSquarePlus size={16} />
        </button>
        {desktop && (
          <button onClick={toggleLarge} className="p-1.5 rounded-lg hover:bg-black/5" aria-pressed={large}
            title={large ? '작게 보기' : '크게 보기'} aria-label={large ? '작게 보기' : '크게 보기'} style={{ color: 'var(--text-secondary)' }}>
            {large ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
        )}
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-black/5" aria-label="닫기 (Esc)" title="닫기 (Esc)"
          style={{ color: 'var(--text-secondary)' }}>
          <X size={18} />
        </button>
      </div>

      <div ref={logRef} className="flex-1 overflow-y-auto p-4 space-y-3" role="log" aria-live="polite" aria-relevant="additions text">
        {messages.map((m) => (
          <ChatMessage key={m.id} msg={m} onFeedback={feedback} onRetry={retry} />
        ))}
      </div>

      <TurnstileWidget onToken={setTsToken} resetKey={tsReset} />

      <div className="p-3 border-t" style={{ borderColor: 'var(--border)' }}>
        {(queuedCount > 0 || waitingForBot) && (
          <p className="text-[11px] mb-1.5" style={{ color: 'var(--text-secondary)' }} aria-live="polite">
            {waitingForBot ? '봇 확인 중이에요…' : `앞 답변이 끝나면 보낼게요 · 대기 ${queuedCount}개`}
          </p>
        )}
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            maxLength={MAX_INPUT}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              // 한글 입력 중(조합 중) Enter는 글자 확정용이라 보내지 않는다.
              // 터치 기기에서는 Enter=줄바꿈, 보내기는 버튼(모바일 키보드엔 Shift+Enter가 없다).
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing && !isCoarsePointer()) { e.preventDefault(); send() }
            }}
            placeholder={(currentPage()?.post_slug ? '이 글에 대해 물어보세요 (예: 핵심만 요약해줘)' : '질문을 입력하세요') + (isCoarsePointer() ? '' : ' · Shift+Enter 줄바꿈')}
            aria-label="질문"
            className="flex-1 max-h-32 resize-none px-3 py-2 rounded-xl text-sm border outline-none focus:ring-2 focus:ring-primary-500"
            style={{ background: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)', fieldSizing: 'content' }}
          />
          {busy ? (
            <button onClick={() => abortRef.current?.abort()} className="p-2.5 rounded-xl border" aria-label="답변 중단"
              title="답변 중단" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
              <Square size={16} />
            </button>
          ) : null}
          <button onClick={send} disabled={!input.trim()} aria-label="보내기"
            className="p-2.5 rounded-xl bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40">
            <Send size={16} />
          </button>
        </div>
      </div>
    </motion.div>
  )
}
