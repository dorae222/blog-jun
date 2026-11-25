import { memo, useState } from 'react'
import { Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { FileText, ThumbsUp, ThumbsDown, RotateCcw, Clock } from 'lucide-react'
import { isSafeSlug } from '../../utils/noteText'
import { FEEDBACK_COMMENT_MAX } from '../../utils/feedback'

/**
 * 챗 말풍선. 답변은 마크다운으로 그리되 원시 HTML은 받지 않는다(react-markdown 기본값).
 * 답변 안의 링크도 내부 경로(/로 시작)만 라우터 링크로, 나머지는 새 창으로 연다.
 * 출처는 내부 글(/post/:slug)만 보여 준다.
 */
function MdLink({ href = '', children }) {
  if (href.startsWith('/') && !href.startsWith('//')) return <Link to={href} className="text-primary-600 underline">{children}</Link>
  if (/^https?:\/\//.test(href)) return <a href={href} target="_blank" rel="noopener noreferrer nofollow" className="text-primary-600 underline">{children}</a>
  return <span>{children}</span>
}

const mdComponents = { a: MdLink, img: () => null }

const voteBase = 'tap-target inline-flex items-center justify-center gap-1 h-8 px-2.5 rounded-lg border text-xs font-medium '
  + '[@media(pointer:coarse)]:min-w-[44px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500'

/**
 * 답변 아래 피드백 줄. 끝난 답변(message_id·feedback_token이 있는 것)에만 붙는다.
 * 👎는 누르는 즉시 기록하고, 의견은 원하면 덧붙여 한 번 더 보낸다(서버는 같은 답변에 여러 번 받는다).
 */
function Feedback({ msg, onFeedback }) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)

  const vote = (value) => {
    if (msg.feedback === value) return
    setOpen(value === 'down')
    onFeedback(msg, value)
  }
  const submit = async () => {
    const comment = text.trim().slice(0, FEEDBACK_COMMENT_MAX)
    if (!comment || sending) return
    setSending(true)
    const ok = await onFeedback(msg, 'down', comment)
    setSending(false)
    if (ok) { setOpen(false); setText('') }
  }
  const idle = { borderColor: 'var(--border)', color: 'var(--text)', background: 'var(--card-bg)' }
  const showForm = open && msg.feedback === 'down' && !msg.commentSent

  return (
    <div className="mt-1.5" role="group" aria-label="답변 피드백">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
          {msg.commentSent ? '의견을 보냈습니다. 고맙습니다.' : msg.feedback ? '고맙습니다.' : '도움이 됐나요?'}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <button type="button" onClick={() => vote('up')} aria-label="도움이 됐어요" aria-pressed={msg.feedback === 'up'}
            className={`${voteBase} ${msg.feedback === 'up' ? 'border-primary-600 bg-primary-600 text-white' : 'hover:bg-black/5'}`}
            style={msg.feedback === 'up' ? undefined : idle}>
            <ThumbsUp size={16} aria-hidden /> 네
          </button>
          <button type="button" onClick={() => vote('down')} aria-label="도움이 안 됐어요" aria-pressed={msg.feedback === 'down'}
            className={`${voteBase} ${msg.feedback === 'down' ? 'border-red-500 bg-red-500 text-white' : 'hover:bg-black/5'}`}
            style={msg.feedback === 'down' ? undefined : idle}>
            <ThumbsDown size={16} aria-hidden /> 아니요
          </button>
        </span>
      </div>
      {showForm && (
        <div className="mt-1.5 flex items-center gap-1.5">
          <input type="text" value={text} maxLength={FEEDBACK_COMMENT_MAX}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.nativeEvent.isComposing) { e.preventDefault(); submit() } }}
            placeholder="아쉬운 점을 적어 주세요 (선택)" aria-label="아쉬운 점 (선택, 300자까지)"
            className="tap-target flex-1 min-w-0 w-56 h-8 px-2.5 rounded-lg text-xs border outline-none focus:ring-2 focus:ring-primary-500"
            style={{ background: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
          <button type="button" onClick={submit} disabled={!text.trim() || sending}
            className="tap-target shrink-0 h-8 px-3 rounded-lg text-xs font-medium bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40">
            보내기
          </button>
        </div>
      )}
    </div>
  )
}

function ChatMessage({ msg, onFeedback, onRetry }) {
  const isUser = msg.role === 'user'
  const sources = (msg.sources || []).filter((s) => isSafeSlug(s?.slug))

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%]">
          <div className={`px-3 py-2 rounded-2xl rounded-br-md text-sm whitespace-pre-wrap break-words text-white ${msg.queued ? 'bg-primary-400' : 'bg-primary-600'}`}>
            {msg.content}
          </div>
          {msg.queued && (
            <p className="mt-0.5 text-[10px] text-right inline-flex items-center gap-1 w-full justify-end" style={{ color: 'var(--text-secondary)' }}>
              <Clock size={10} /> 대기 중
            </p>
          )}
        </div>
      </div>
    )
  }

  const streaming = msg.status === 'streaming' || msg.status === 'connecting'
  return (
    <div className="flex justify-start">
      <div className="max-w-[90%] min-w-0 sm:max-w-[min(90%,52rem)]">
        <div className="px-3 py-2 rounded-2xl rounded-bl-md text-sm break-words border"
          style={{ background: 'var(--bg-secondary)', borderColor: msg.status === 'error' ? '#fecaca' : 'var(--border)', color: 'var(--text)' }}>
          {msg.status === 'connecting' && !msg.content && (
            <span className="inline-flex items-center gap-1" style={{ color: 'var(--text-secondary)' }} aria-label="답변 준비 중">
              <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" />
              <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce [animation-delay:120ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce [animation-delay:240ms]" />
            </span>
          )}
          {msg.content && (
            <div className="chat-md prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-pre:my-1 prose-headings:my-1.5">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>{msg.content}</ReactMarkdown>
              {streaming && <span className="inline-block w-1.5 h-3.5 align-middle bg-current animate-pulse ml-0.5" aria-hidden />}
            </div>
          )}
          {msg.status === 'error' && (
            <div className="mt-1 text-xs text-red-600">
              {msg.error}
              {msg.retryAfter ? ` (${msg.retryAfter}초 뒤에 다시 시도해 주세요)` : ''}
            </div>
          )}
          {sources.length > 0 && (
            <div className="mt-2 pt-2 border-t space-y-0.5" style={{ borderColor: 'var(--border)' }}>
              <span className="text-[10px] uppercase font-semibold" style={{ color: 'var(--text-secondary)' }}>참고한 글</span>
              {sources.map((s, i) => (
                <Link key={`${s.slug}-${i}`} to={`/post/${encodeURIComponent(s.slug)}`}
                  className="flex items-center gap-1 text-xs text-primary-600 hover:underline">
                  <FileText size={10} className="shrink-0" /> <span className="truncate">{s.title || s.slug}</span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {msg.status === 'error' && onRetry && (
          <div className="mt-1 flex items-center gap-1">
            <button onClick={() => onRetry(msg)} className="inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded hover:bg-black/5"
              style={{ color: 'var(--text-secondary)' }}>
              <RotateCcw size={11} /> 다시 시도
            </button>
          </div>
        )}
        {msg.status === 'done' && msg.messageId && msg.feedbackToken && onFeedback && (
          <Feedback msg={msg} onFeedback={onFeedback} />
        )}
      </div>
    </div>
  )
}

export default memo(ChatMessage)
