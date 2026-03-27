import { useState } from 'react'
import { ChevronDown, ChevronRight, Reply, Pencil, Trash2, Check, X } from 'lucide-react'
import useAuth from '../../hooks/useAuth'
import CommentForm from './CommentForm'

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '방금 전'
  if (mins < 60) return `${mins}분 전`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}시간 전`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}일 전`
  return new Date(dateStr).toLocaleDateString('ko-KR')
}

function AuthorInfo({ author }) {
  const avatar = author.avatar_url
  const name = author.display_name || author.username

  return (
    <div className="flex items-center gap-2">
      {avatar ? (
        <img src={avatar} alt={name} className="w-7 h-7 rounded-full" />
      ) : (
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
          style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
        >
          {name[0]?.toUpperCase()}
        </div>
      )}
      {author.profile_url ? (
        <a
          href={author.profile_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium hover:underline"
          style={{ color: 'var(--text)' }}
        >
          {name}
        </a>
      ) : (
        <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>{name}</span>
      )}
      {author.provider && (
        <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-tertiary)' }}>
          {author.provider}
        </span>
      )}
    </div>
  )
}

export default function CommentItem({ comment, isReply = false, onReply, onEdit, onDelete }) {
  const user = useAuth((s) => s.user)
  const [repliesOpen, setRepliesOpen] = useState(comment.reply_count <= 3)
  const [showReplyForm, setShowReplyForm] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState(comment.content)

  const isAuthor = user?.id === comment.author.id
  const isAdmin = user?.is_staff
  const replies = comment.replies || []

  const handleEdit = async () => {
    if (!editContent.trim()) return
    await onEdit(comment.id, editContent.trim())
    setEditing(false)
  }

  return (
    <div className={isReply ? 'ml-8 pl-4 border-l-2' : ''} style={isReply ? { borderColor: 'var(--border)' } : {}}>
      <div className="py-3">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <AuthorInfo author={comment.author} />
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
              {timeAgo(comment.created_at)}
            </span>
            {comment.is_edited && (
              <span className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>(수정됨)</span>
            )}
          </div>

          {/* 액션 버튼 */}
          {!comment.is_deleted && user && (
            <div className="flex items-center gap-1">
              {!isReply && (
                <button
                  onClick={() => setShowReplyForm(!showReplyForm)}
                  className="p-1.5 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                  style={{ color: 'var(--text-tertiary)' }}
                  title="답글"
                >
                  <Reply size={14} />
                </button>
              )}
              {isAuthor && (
                <button
                  onClick={() => { setEditing(true); setEditContent(comment.content) }}
                  className="p-1.5 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                  style={{ color: 'var(--text-tertiary)' }}
                  title="수정"
                >
                  <Pencil size={14} />
                </button>
              )}
              {(isAuthor || isAdmin) && (
                <button
                  onClick={() => onDelete(comment.id)}
                  className="p-1.5 rounded-lg hover:bg-red-500/10 transition-colors text-red-400"
                  title="삭제"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          )}
        </div>

        {/* 본문 */}
        {editing ? (
          <div className="flex gap-2 items-end">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              maxLength={2000}
              rows={3}
              className="flex-1 resize-none rounded-lg px-3 py-2 text-sm border focus:outline-none focus:ring-2 focus:ring-blue-500/30"
              style={{ background: 'var(--bg-secondary)', color: 'var(--text)', borderColor: 'var(--border)' }}
            />
            <button onClick={handleEdit} className="p-2 rounded-lg text-green-500 hover:bg-green-500/10">
              <Check size={16} />
            </button>
            <button onClick={() => setEditing(false)} className="p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/5" style={{ color: 'var(--text-tertiary)' }}>
              <X size={16} />
            </button>
          </div>
        ) : (
          <p
            className="text-sm whitespace-pre-wrap"
            style={{ color: comment.is_deleted ? 'var(--text-tertiary)' : 'var(--text-secondary)' }}
          >
            {comment.content}
          </p>
        )}

        {/* 답글 토글 */}
        {!isReply && replies.length > 0 && (
          <button
            onClick={() => setRepliesOpen(!repliesOpen)}
            className="flex items-center gap-1 mt-2 text-xs hover:underline"
            style={{ color: 'var(--text-tertiary)' }}
          >
            {repliesOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            답글 {replies.length}개
          </button>
        )}

        {/* 답글 작성 폼 */}
        {showReplyForm && (
          <div className="mt-3 ml-8">
            <CommentForm
              placeholder={`@${comment.author.display_name || comment.author.username} 에게 답글...`}
              initialValue={`@${comment.author.display_name || comment.author.username} `}
              autoFocus
              onSubmit={async (content) => {
                await onReply(comment.id, content)
                setShowReplyForm(false)
              }}
            />
          </div>
        )}
      </div>

      {/* 답글 목록 */}
      {!isReply && repliesOpen && replies.map((reply) => (
        <CommentItem
          key={reply.id}
          comment={reply}
          isReply
          onReply={onReply}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}
