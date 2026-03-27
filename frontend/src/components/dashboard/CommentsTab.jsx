import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Trash2, Search, MessageCircle, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import { getAdminComments, getAdminCommentStats, bulkDeleteComments } from '../../api/comments'

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

export default function CommentsTab() {
  const [comments, setComments] = useState([])
  const [stats, setStats] = useState(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [filterDeleted, setFilterDeleted] = useState('')
  const [selected, setSelected] = useState(new Set())

  const loadComments = useCallback(() => {
    const params = { page, page_size: 15 }
    if (search) params.search = search
    if (filterDeleted) params.is_deleted = filterDeleted
    getAdminComments(params).then(r => {
      setComments(r.data.results || [])
      setTotal(r.data.count || 0)
      setSelected(new Set())
    }).catch(() => toast.error('댓글 로드 실패'))
  }, [page, search, filterDeleted])

  const loadStats = useCallback(() => {
    getAdminCommentStats().then(r => setStats(r.data)).catch(() => {})
  }, [])

  useEffect(() => { loadComments() }, [loadComments])
  useEffect(() => { loadStats() }, [])

  // 검색 디바운스
  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput); setPage(1) }, 400)
    return () => clearTimeout(t)
  }, [searchInput])

  const toggleSelect = (id) => {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (selected.size === comments.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(comments.map(c => c.id)))
    }
  }

  const handleBulkDelete = async () => {
    if (!selected.size) return
    if (!confirm(`선택한 ${selected.size}개 댓글을 삭제할까요?`)) return
    try {
      const r = await bulkDeleteComments([...selected])
      toast.success(`${r.data.deleted}개 삭제 완료`)
      loadComments()
      loadStats()
    } catch {
      toast.error('삭제 실패')
    }
  }

  const totalPages = Math.ceil(total / 15)

  return (
    <div className="space-y-6">
      {/* 통계 카드 */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: '전체 댓글', value: stats.total, color: '#6366f1' },
            { label: '활성', value: stats.active, color: '#10b981' },
            { label: '삭제됨', value: stats.deleted, color: '#ef4444' },
            { label: '최근 7일', value: stats.recent_7d, color: '#3b82f6' },
          ].map(s => (
            <div key={s.label} className="p-3 sm:p-4 rounded-xl border" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)', borderTop: `3px solid ${s.color}` }}>
              <p className="text-xs mb-1" style={{ color: 'var(--text-tertiary)' }}>{s.label}</p>
              <p className="text-lg sm:text-xl font-bold" style={{ color: 'var(--text)' }}>{s.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* 필터 + 액션 바 */}
      <div className="flex flex-wrap gap-2 sm:gap-3 items-center">
        <div className="relative flex-1 min-w-[160px] max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-tertiary)' }} />
          <input
            type="text"
            placeholder="댓글/작성자 검색..."
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30"
            style={{ background: 'var(--bg-secondary)', color: 'var(--text)', borderColor: 'var(--border)' }}
          />
        </div>

        <select
          value={filterDeleted}
          onChange={e => { setFilterDeleted(e.target.value); setPage(1) }}
          className="border rounded-lg px-3 py-2 text-sm"
          style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
        >
          <option value="">전체 상태</option>
          <option value="false">활성</option>
          <option value="true">삭제됨</option>
        </select>

        {selected.size > 0 && (
          <button
            onClick={handleBulkDelete}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-red-500 border border-red-200 hover:bg-red-50 transition-colors"
          >
            <Trash2 size={14} /> {selected.size}개 삭제
          </button>
        )}
      </div>

      {/* 댓글 테이블 — 모바일에서는 카드, 데스크톱에서는 테이블 */}
      {/* 데스크톱 테이블 */}
      <div className="hidden sm:block rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: 'var(--bg-secondary)' }}>
              <th className="w-8 p-3">
                <input type="checkbox" checked={selected.size === comments.length && comments.length > 0} onChange={toggleAll} />
              </th>
              <th className="text-left p-3 font-medium" style={{ color: 'var(--text-secondary)' }}>작성자</th>
              <th className="text-left p-3 font-medium" style={{ color: 'var(--text-secondary)' }}>댓글</th>
              <th className="text-left p-3 font-medium hidden md:table-cell" style={{ color: 'var(--text-secondary)' }}>포스트</th>
              <th className="text-left p-3 font-medium" style={{ color: 'var(--text-secondary)' }}>상태</th>
              <th className="text-right p-3 font-medium" style={{ color: 'var(--text-secondary)' }}>시간</th>
            </tr>
          </thead>
          <tbody>
            {comments.map(c => (
              <tr key={c.id} className="border-t hover:bg-black/[0.02] dark:hover:bg-white/[0.02]" style={{ borderColor: 'var(--border)' }}>
                <td className="p-3">
                  <input type="checkbox" checked={selected.has(c.id)} onChange={() => toggleSelect(c.id)} />
                </td>
                <td className="p-3">
                  <div className="flex items-center gap-2">
                    {c.author.avatar_url ? (
                      <img src={c.author.avatar_url} alt="" className="w-6 h-6 rounded-full" />
                    ) : (
                      <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>
                        {(c.author.display_name || c.author.username)[0]?.toUpperCase()}
                      </div>
                    )}
                    <span style={{ color: 'var(--text)' }}>{c.author.display_name || c.author.username}</span>
                  </div>
                </td>
                <td className="p-3 max-w-[200px]">
                  <p className="truncate" style={{ color: c.is_deleted ? 'var(--text-tertiary)' : 'var(--text-secondary)' }}>
                    {c.is_deleted ? '[삭제됨] ' : ''}{c.content}
                  </p>
                </td>
                <td className="p-3 hidden md:table-cell">
                  <Link to={`/post/${c.post_slug}`} className="text-blue-500 hover:underline truncate block max-w-[180px]">
                    {c.post_title}
                  </Link>
                </td>
                <td className="p-3">
                  {c.is_deleted ? (
                    <span className="flex items-center gap-1 text-xs text-red-400">
                      <AlertTriangle size={12} /> 삭제됨
                    </span>
                  ) : (
                    <span className="text-xs text-green-500">활성</span>
                  )}
                </td>
                <td className="p-3 text-right whitespace-nowrap" style={{ color: 'var(--text-tertiary)' }}>
                  {timeAgo(c.created_at)}
                </td>
              </tr>
            ))}
            {comments.length === 0 && (
              <tr>
                <td colSpan={6} className="p-8 text-center" style={{ color: 'var(--text-tertiary)' }}>
                  <MessageCircle size={24} className="mx-auto mb-2 opacity-40" />
                  댓글이 없습니다
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* 모바일 카드 뷰 */}
      <div className="sm:hidden space-y-2">
        {/* 전체 선택 */}
        <div className="flex items-center gap-2 px-1 py-2">
          <input type="checkbox" checked={selected.size === comments.length && comments.length > 0} onChange={toggleAll} />
          <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>전체 선택</span>
        </div>

        {comments.map(c => (
          <div key={c.id} className="rounded-xl border p-3" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
            <div className="flex items-start gap-2">
              <input type="checkbox" checked={selected.has(c.id)} onChange={() => toggleSelect(c.id)} className="mt-1 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    {c.author.avatar_url ? (
                      <img src={c.author.avatar_url} alt="" className="w-5 h-5 rounded-full shrink-0" />
                    ) : (
                      <div className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>
                        {(c.author.display_name || c.author.username)[0]?.toUpperCase()}
                      </div>
                    )}
                    <span className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>
                      {c.author.display_name || c.author.username}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {c.is_deleted ? (
                      <span className="text-[11px] text-red-400">삭제됨</span>
                    ) : (
                      <span className="text-[11px] text-green-500">활성</span>
                    )}
                    <span className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>{timeAgo(c.created_at)}</span>
                  </div>
                </div>
                <p className="text-sm mb-1.5 line-clamp-2" style={{ color: c.is_deleted ? 'var(--text-tertiary)' : 'var(--text-secondary)' }}>
                  {c.is_deleted ? '[삭제됨] ' : ''}{c.content}
                </p>
                <Link to={`/post/${c.post_slug}`} className="text-xs text-blue-500 hover:underline truncate block">
                  {c.post_title}
                </Link>
              </div>
            </div>
          </div>
        ))}

        {comments.length === 0 && (
          <div className="p-8 text-center" style={{ color: 'var(--text-tertiary)' }}>
            <MessageCircle size={24} className="mx-auto mb-2 opacity-40" />
            댓글이 없습니다
          </div>
        )}
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => p - 1)}
            className="px-3 py-2 rounded-lg border text-sm disabled:opacity-40"
            style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
          >
            이전
          </button>
          <span className="px-3 py-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
            {page} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(p => p + 1)}
            className="px-3 py-2 rounded-lg border text-sm disabled:opacity-40"
            style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
          >
            다음
          </button>
        </div>
      )}
    </div>
  )
}
