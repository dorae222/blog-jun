import { memo } from 'react'
import { Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { FileText, ThumbsUp, ThumbsDown, RotateCcw, Clock } from 'lucide-react'
import { isSafeSlug } from '../../utils/noteText'

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

        <div className="mt-1 flex items-center gap-1 min-h-[1.25rem]">
          {msg.status === 'error' && onRetry && (
            <button onClick={() => onRetry(msg)} className="inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded hover:bg-black/5"
              style={{ color: 'var(--text-secondary)' }}>
              <RotateCcw size={11} /> 다시 시도
            </button>
          )}
          {msg.status === 'done' && msg.messageId && msg.feedbackToken && onFeedback && (
            <>
              <button onClick={() => onFeedback(msg, 'up')} disabled={Boolean(msg.feedback)}
                aria-label="도움이 됐어요" aria-pressed={msg.feedback === 'up'}
                className={`p-1 rounded hover:bg-black/5 disabled:cursor-default ${msg.feedback === 'up' ? 'text-primary-600' : ''}`}
                style={msg.feedback === 'up' ? undefined : { color: 'var(--text-secondary)' }}>
                <ThumbsUp size={12} />
              </button>
              <button onClick={() => onFeedback(msg, 'down')} disabled={Boolean(msg.feedback)}
                aria-label="아쉬워요" aria-pressed={msg.feedback === 'down'}
                className={`p-1 rounded hover:bg-black/5 disabled:cursor-default ${msg.feedback === 'down' ? 'text-red-500' : ''}`}
                style={msg.feedback === 'down' ? undefined : { color: 'var(--text-secondary)' }}>
                <ThumbsDown size={12} />
              </button>
              {msg.feedback && <span className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>고마워요</span>}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default memo(ChatMessage)
