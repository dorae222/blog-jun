import { Link } from 'react-router-dom'
import {
  CheckCircle, Eye, AlertTriangle, Pencil, Trash2,
  LayoutGrid, Cloud, Brain, Database, Code2, FolderOpen, Terminal, BookOpen,
  Archive, ImageOff, Search, ChevronLeft, ChevronRight,
} from 'lucide-react'

// 이슈 배지 색상
const ISSUE_COLORS = {
  HTML_TAG:     'bg-orange-100 text-orange-700',
  JUPYTER:      'bg-purple-100 text-purple-700',
  SHORT:        'bg-gray-100 text-gray-500',
  META_REMNANT: 'bg-yellow-100 text-yellow-700',
  ENCODING:     'bg-red-100 text-red-700',
}

const STATUS_DOT = { published: '#10b981', draft: '#f59e0b', archived: '#94a3b8' }

export default function PostsTab({
  // 필터 상태
  categoryFilter, setCategoryFilter,
  statusFilter, setStatusFilter,
  postTypeFilter, setPostTypeFilter,
  noImageFilter, setNoImageFilter,
  auditFilter, setAuditFilter,
  searchInput, setSearchInput,
  setPage,
  // 데이터
  visiblePosts, totalPosts, page, totalPages,
  pageSize, setPageSize,
  auditMap, selected,
  // 콜백
  toggleSelect, toggleAll,
  handleDelete, handleBulkDelete, handleBulkStatus,
  loadAudit,
  // 상수
  CATEGORIES, STATUS_META, POST_TYPES, CAT_ICONS,
}) {
  return (
    <div className="flex gap-6">
      {/* 모바일 필터 드롭다운 */}
      <div className="md:hidden mb-4 flex gap-2">
        <select
          value={categoryFilter}
          onChange={e => { setCategoryFilter(e.target.value); setPage(1) }}
          className="flex-1 text-sm px-3 py-2 rounded-lg border"
          style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
        >
          {CATEGORIES.map(cat => (
            <option key={cat.slug} value={cat.slug}>{cat.label}</option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
          className="flex-1 text-sm px-3 py-2 rounded-lg border"
          style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
        >
          {STATUS_META.map(s => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      </div>

      {/* 사이드바 (데스크탑) */}
      <aside className="hidden md:block w-44 shrink-0">
        <p className="text-xs font-semibold mb-2 uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>카테고리</p>
        <ul className="space-y-1">
          {CATEGORIES.map(cat => {
            const CatIcon = CAT_ICONS[cat.slug] || LayoutGrid
            return (
              <li key={cat.slug}>
                <button
                  onClick={() => { setCategoryFilter(cat.slug); setPage(1) }}
                  className={`w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                    categoryFilter === cat.slug
                      ? 'bg-primary-50 text-primary-700 font-semibold border border-primary-200'
                      : 'hover:bg-gray-50'
                  }`}
                  style={categoryFilter !== cat.slug ? { color: 'var(--text)' } : {}}>
                  <CatIcon size={14} style={{ flexShrink: 0 }} />
                  {cat.label}
                </button>
              </li>
            )
          })}
        </ul>

        <div className="mt-6 space-y-1">
          <p className="text-xs font-semibold mb-2 uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>상태</p>
          {STATUS_META.map(({ value, label, Icon, dot }) => (
            <button
              key={value}
              onClick={() => { setStatusFilter(value); setPage(1) }}
              className={`w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                statusFilter === value
                  ? 'bg-primary-50 text-primary-700 font-semibold border border-primary-200'
                  : 'hover:bg-gray-50'
              }`}
              style={statusFilter !== value ? { color: 'var(--text)' } : {}}>
              {dot
                ? <span style={{ width: 8, height: 8, borderRadius: '50%', background: dot, flexShrink: 0 }} />
                : <Icon size={14} style={{ flexShrink: 0 }} />
              }
              {label}
            </button>
          ))}
        </div>

        <div className="mt-6 space-y-1">
          <p className="text-xs font-semibold mb-2 uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>타입</p>
          <select
            value={postTypeFilter}
            onChange={e => { setPostTypeFilter(e.target.value); setPage(1) }}
            className="w-full text-sm px-3 py-1.5 rounded-lg border"
            style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
          >
            {POST_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <div className="mt-6 space-y-1">
          <button
            onClick={() => { setNoImageFilter(v => !v); setPage(1) }}
            className={`w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              noImageFilter ? 'bg-orange-50 text-orange-700 font-medium border border-orange-200' : 'hover:bg-gray-50'
            }`}
            style={!noImageFilter ? { color: 'var(--text)' } : {}}>
            <ImageOff size={14} />
            이미지 없음
          </button>
          <button
            onClick={() => setAuditFilter(v => !v)}
            className={`w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              auditFilter ? 'bg-red-50 text-red-700 font-medium border border-red-200' : 'hover:bg-gray-50'
            }`}
            style={!auditFilter ? { color: 'var(--text)' } : {}}>
            <AlertTriangle size={14} />
            이슈 있는 것만
          </button>
          <button
            onClick={loadAudit}
            className="w-full text-left px-3 py-1.5 rounded-lg text-xs hover:bg-gray-100"
            style={{ color: 'var(--text-secondary)' }}
          >
            ↻ 감사 새로고침
          </button>
        </div>
      </aside>

      {/* 포스트 테이블 */}
      <div className="flex-1 min-w-0">
        {/* 검색 바 */}
        <div className="mb-3 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: 'var(--text-secondary)' }} />
          <input
            type="text"
            placeholder="포스트 검색 (제목, 내용, 요약)..."
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border text-sm"
            style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
          />
        </div>

        {/* 벌크 액션 바 */}
        {selected.size > 0 && (
          <div className="flex items-center gap-2 mb-3 px-4 py-2.5 rounded-xl
            bg-primary-50 border border-primary-200">
            <span className="text-sm font-semibold text-primary-700">{selected.size}개 선택</span>
            <div className="flex gap-2 ml-auto">
              <button onClick={() => handleBulkStatus('published')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-600 text-white text-xs font-medium hover:bg-green-700">
                <CheckCircle size={12} /> 발행
              </button>
              <button onClick={() => handleBulkStatus('archived')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium hover:bg-white transition-colors"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>
                <Archive size={12} /> 보관
              </button>
              <button onClick={handleBulkDelete}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600 text-white text-xs font-medium hover:bg-red-700">
                <Trash2 size={12} /> 삭제
              </button>
            </div>
          </div>
        )}

        {/* 테이블 */}
        <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
                <th className="w-8 px-3 py-2 text-left">
                  <input
                    type="checkbox"
                    checked={selected.size === visiblePosts.length && visiblePosts.length > 0}
                    onChange={toggleAll}
                    className="rounded"
                  />
                </th>
                <th className="px-3 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>제목</th>
                <th className="px-3 py-2 text-left font-medium hidden md:table-cell" style={{ color: 'var(--text-secondary)' }}>카테고리</th>
                <th className="px-3 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>이슈</th>
                <th className="px-3 py-2 text-left font-medium hidden lg:table-cell" style={{ color: 'var(--text-secondary)' }}>조회</th>
                <th className="px-3 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>상태</th>
                <th className="px-3 py-2 text-right font-medium" style={{ color: 'var(--text-secondary)' }}>액션</th>
              </tr>
            </thead>
            <tbody>
              {visiblePosts.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
                    포스트가 없습니다.
                  </td>
                </tr>
              )}
              {visiblePosts.map(post => {
                const issues = auditMap[post.slug] || []
                const isSelected = selected.has(post.slug)
                return (
                  <tr
                    key={post.id}
                    className="border-t transition-colors hover:bg-gray-50"
                    style={{ borderColor: 'var(--border)', background: isSelected ? 'var(--bg-secondary)' : undefined }}
                  >
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelect(post.slug)}
                        className="rounded"
                      />
                    </td>
                    <td className="px-3 py-2 max-w-xs">
                      <span className="font-medium truncate block" style={{ color: 'var(--text)' }}>{post.title}</span>
                      <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {new Date(post.created_at).toLocaleDateString('ko-KR')}
                        {post.post_type !== 'article' && (
                          <span className="ml-1.5 px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">{post.post_type}</span>
                        )}
                      </span>
                    </td>
                    <td className="px-3 py-2 hidden md:table-cell">
                      {post.category ? (
                        <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                          style={{
                            background: `${post.category.color || '#6366f1'}15`,
                            color: post.category.color || '#6366f1',
                          }}>
                          {post.category.name}
                        </span>
                      ) : <span style={{ color: 'var(--text-secondary)' }}>-</span>}
                    </td>
                    <td className="px-3 py-2">
                      {issues.length > 0 ? (
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold text-red-600">{issues.length}</span>
                          <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium
                            ${ISSUE_COLORS[issues[0]] || 'bg-gray-100 text-gray-600'}`}>
                            {issues[0]}
                          </span>
                          {issues.length > 1 &&
                            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                              +{issues.length - 1}
                            </span>
                          }
                        </div>
                      ) : <span style={{ color: 'var(--border)' }}>-</span>}
                    </td>
                    <td className="px-3 py-2 hidden lg:table-cell">
                      <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {post.view_count || 0}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span className="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full"
                        style={{
                          background: `${STATUS_DOT[post.status] || '#94a3b8'}15`,
                          color: STATUS_DOT[post.status] || '#94a3b8',
                        }}>
                        <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'currentColor' }} />
                        {post.status}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-0.5 justify-end">
                        <Link to={`/post/${post.slug}`} target="_blank" title="보기"
                          className="p-1.5 rounded transition-colors hover:bg-gray-100"
                          style={{ color: 'var(--text-secondary)' }}>
                          <Eye size={14} />
                        </Link>
                        <Link to={`/editor/${post.slug}`} title="편집"
                          className="p-1.5 rounded transition-colors hover:bg-blue-50 hover:text-blue-600"
                          style={{ color: 'var(--text-secondary)' }}>
                          <Pencil size={14} />
                        </Link>
                        <button onClick={() => handleDelete(post.slug)} title="삭제"
                          className="p-1.5 rounded transition-colors hover:bg-red-50 hover:text-red-600"
                          style={{ color: 'var(--text-secondary)' }}>
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              {visiblePosts.length}개 표시 / 전체 {totalPosts}개
            </p>
            {setPageSize && (
              <select
                value={pageSize}
                onChange={e => setPageSize(Number(e.target.value))}
                className="text-xs px-2 py-1 rounded border"
                style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text-secondary)' }}
              >
                {[10, 25, 50].map(n => (
                  <option key={n} value={n}>{n}개씩</option>
                ))}
              </select>
            )}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded border text-xs transition-colors disabled:opacity-40"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                <ChevronLeft size={14} />
              </button>
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 rounded border text-xs transition-colors disabled:opacity-40"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                <ChevronRight size={14} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
