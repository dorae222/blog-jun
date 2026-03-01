import { useEffect, useState, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import useAuth from '../hooks/useAuth'
import {
  getDashboardStats, getPosts, deletePost,
  bulkDeletePosts, bulkUpdateStatus,
  getAuditResults, getTags, mergeTags, cleanupTags,
} from '../api/posts'
import toast from 'react-hot-toast'

// 이슈 배지 색상
const ISSUE_COLORS = {
  HTML_TAG:     'bg-orange-100 text-orange-700',
  JUPYTER:      'bg-purple-100 text-purple-700',
  SHORT:        'bg-gray-100 text-gray-500',
  META_REMNANT: 'bg-yellow-100 text-yellow-700',
  ENCODING:     'bg-red-100 text-red-700',
}

const STATUS_COLORS = {
  published: 'bg-green-100 text-green-700',
  draft:     'bg-yellow-100 text-yellow-700',
  archived:  'bg-gray-100 text-gray-500',
}

// 사이드바 카테고리 목록
const CATEGORIES = [
  { label: '전체',       slug: '' },
  { label: 'Cloud',      slug: 'cloud' },
  { label: 'AI/ML',      slug: 'ai-ml' },
  { label: 'Data',       slug: 'data' },
  { label: 'DEV',        slug: 'dev' },
  { label: 'Foundation', slug: 'foundation' },
  { label: 'Project',    slug: 'project' },
  { label: 'Program',    slug: 'program' },
]

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()

  // 탭: posts | tags
  const [tab, setTab] = useState('posts')

  // 포스트 목록 상태
  const [stats, setStats] = useState(null)
  const [posts, setPosts] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [auditFilter, setAuditFilter] = useState(false)

  // 감사 결과
  const [auditMap, setAuditMap] = useState({}) // slug → issues[]
  const [auditSummary, setAuditSummary] = useState({ total_issues: 0 })

  // 벌크 선택
  const [selected, setSelected] = useState(new Set())

  // 태그 탭
  const [tags, setTags] = useState([])
  const [mergeSrc, setMergeSrc] = useState('')
  const [mergeDst, setMergeDst] = useState('')

  // 데이터 로드
  const loadPosts = useCallback((statusF = statusFilter, catF = categoryFilter) => {
    const params = {}
    if (statusF) params.status = statusF
    if (catF)    params['category__slug'] = catF
    params.page_size = 500
    getPosts(params).then(r => {
      const list = r.data.results || r.data || []
      setPosts(list)
      setSelected(new Set())
    }).catch(() => toast.error('포스트 로드 실패'))
  }, [statusFilter, categoryFilter])

  const loadAudit = useCallback(() => {
    getAuditResults().then(r => {
      const map = {}
      ;(r.data.results || []).forEach(item => { map[item.slug] = item.issues })
      setAuditMap(map)
      setAuditSummary({ total_issues: r.data.total_issues || 0 })
    }).catch(() => {})
  }, [])

  const loadTags = useCallback(() => {
    getTags().then(r => setTags(r.data.results || r.data || [])).catch(() => {})
  }, [])

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    getDashboardStats().then(r => setStats(r.data)).catch(() => {})
    loadPosts()
    loadAudit()
  }, [user, navigate])

  useEffect(() => {
    if (tab === 'tags') loadTags()
  }, [tab])

  useEffect(() => {
    loadPosts(statusFilter, categoryFilter)
  }, [statusFilter, categoryFilter])

  // 필터링된 포스트
  const visiblePosts = auditFilter
    ? posts.filter(p => auditMap[p.slug]?.length > 0)
    : posts

  // 체크박스
  const toggleSelect = (slug) => {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(slug) ? next.delete(slug) : next.add(slug)
      return next
    })
  }
  const toggleAll = () => {
    if (selected.size === visiblePosts.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(visiblePosts.map(p => p.slug)))
    }
  }

  // 단일 삭제
  const handleDelete = async (slug) => {
    if (!confirm('이 포스트를 삭제할까요?')) return
    try {
      await deletePost(slug)
      toast.success('삭제 완료')
      loadPosts()
    } catch {
      toast.error('삭제 실패')
    }
  }

  // 벌크 삭제
  const handleBulkDelete = async () => {
    if (!selected.size) return
    if (!confirm(`선택한 ${selected.size}개 포스트를 삭제할까요?`)) return
    try {
      const r = await bulkDeletePosts([...selected])
      toast.success(`${r.data.deleted}개 삭제 완료`)
      loadPosts()
    } catch {
      toast.error('벌크 삭제 실패')
    }
  }

  // 벌크 상태 변경
  const handleBulkStatus = async (newStatus) => {
    if (!selected.size) return
    try {
      const r = await bulkUpdateStatus([...selected], newStatus)
      toast.success(`${r.data.updated}개 → ${newStatus}`)
      loadPosts()
    } catch {
      toast.error('상태 변경 실패')
    }
  }

  // 태그 병합
  const handleMerge = async () => {
    if (!mergeSrc || !mergeDst) { toast.error('소스/대상 태그를 선택하세요'); return }
    if (!confirm(`"${mergeSrc}" → "${mergeDst}" 병합할까요?`)) return
    try {
      const r = await mergeTags(mergeSrc, mergeDst)
      toast.success(`병합 완료 (${r.data.posts_moved}개 포스트 이전)`)
      loadTags()
      setMergeSrc(''); setMergeDst('')
    } catch {
      toast.error('병합 실패')
    }
  }

  // 고아 태그 삭제
  const handleCleanup = async () => {
    if (!confirm('포스트 없는 태그를 모두 삭제할까요?')) return
    try {
      const r = await cleanupTags()
      toast.success(`${r.data.deleted_orphaned}개 고아 태그 삭제`)
      loadTags()
    } catch {
      toast.error('정리 실패')
    }
  }

  if (!user) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-7xl mx-auto px-4 py-10"
    >
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Dashboard</h1>
        <Link
          to="/editor"
          className="px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors text-sm"
        >
          + New Post
        </Link>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          {[
            { label: '총 포스트',  value: stats.total_posts,  color: 'text-blue-600' },
            { label: '발행',        value: stats.published,    color: 'text-green-600' },
            { label: '초안',        value: stats.drafts,       color: 'text-yellow-600' },
            { label: '총 조회수',   value: stats.total_views,  color: 'text-purple-600' },
            { label: '감사 이슈',   value: auditSummary.total_issues, color: 'text-red-600' },
          ].map(s => (
            <div key={s.label} className="p-3 rounded-xl border" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{s.label}</p>
              <p className={`text-xl font-bold ${s.color}`}>{s.value?.toLocaleString() ?? 0}</p>
            </div>
          ))}
        </div>
      )}

      {/* 탭 */}
      <div className="flex gap-2 mb-6 border-b" style={{ borderColor: 'var(--border)' }}>
        {['posts', 'tags'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? 'border-primary-600 text-primary-600' : 'border-transparent'
            }`}
            style={tab !== t ? { color: 'var(--text-secondary)' } : {}}
          >
            {t === 'posts' ? '포스트' : '태그 관리'}
          </button>
        ))}
      </div>

      {/* ─── 포스트 탭 ─── */}
      {tab === 'posts' && (
        <div className="flex gap-6">
          {/* 사이드바 */}
          <aside className="w-44 shrink-0">
            <p className="text-xs font-semibold mb-2 uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>카테고리</p>
            <ul className="space-y-1">
              {CATEGORIES.map(cat => (
                <li key={cat.slug}>
                  <button
                    onClick={() => setCategoryFilter(cat.slug)}
                    className={`w-full text-left px-3 py-1.5 rounded-lg text-sm transition-colors ${
                      categoryFilter === cat.slug
                        ? 'bg-primary-100 text-primary-700 font-medium'
                        : 'hover:bg-gray-100'
                    }`}
                    style={categoryFilter !== cat.slug ? { color: 'var(--text)' } : {}}
                  >
                    {cat.label}
                  </button>
                </li>
              ))}
            </ul>

            <div className="mt-6 space-y-2">
              <p className="text-xs font-semibold mb-2 uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>상태</p>
              {['', 'draft', 'published', 'archived'].map(f => (
                <button
                  key={f}
                  onClick={() => setStatusFilter(f)}
                  className={`w-full text-left px-3 py-1.5 rounded-lg text-sm transition-colors ${
                    statusFilter === f ? 'bg-primary-100 text-primary-700 font-medium' : 'hover:bg-gray-100'
                  }`}
                  style={statusFilter !== f ? { color: 'var(--text)' } : {}}
                >
                  {f || '전체'}
                </button>
              ))}
            </div>

            <div className="mt-6">
              <button
                onClick={() => setAuditFilter(v => !v)}
                className={`w-full text-left px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  auditFilter ? 'bg-red-100 text-red-700 font-medium' : 'hover:bg-gray-100'
                }`}
                style={!auditFilter ? { color: 'var(--text)' } : {}}
              >
                {auditFilter ? '⚠ 이슈 필터 ON' : '이슈 있는 것만'}
              </button>
              <button
                onClick={loadAudit}
                className="w-full text-left px-3 py-1.5 rounded-lg text-xs mt-1 hover:bg-gray-100"
                style={{ color: 'var(--text-secondary)' }}
              >
                ↻ 감사 새로고침
              </button>
            </div>
          </aside>

          {/* 포스트 테이블 */}
          <div className="flex-1 min-w-0">
            {/* 벌크 액션 바 */}
            {selected.size > 0 && (
              <div className="flex items-center gap-2 mb-3 p-3 rounded-lg bg-primary-50 border border-primary-200">
                <span className="text-sm font-medium text-primary-700">{selected.size}개 선택됨</span>
                <button
                  onClick={handleBulkDelete}
                  className="ml-auto px-3 py-1 rounded text-sm bg-red-600 text-white hover:bg-red-700"
                >
                  삭제
                </button>
                <button
                  onClick={() => handleBulkStatus('archived')}
                  className="px-3 py-1 rounded text-sm border hover:bg-gray-50"
                  style={{ borderColor: 'var(--border)' }}
                >
                  보관
                </button>
                <button
                  onClick={() => handleBulkStatus('published')}
                  className="px-3 py-1 rounded text-sm bg-green-600 text-white hover:bg-green-700"
                >
                  발행
                </button>
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
                    <th className="px-3 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>상태</th>
                    <th className="px-3 py-2 text-right font-medium" style={{ color: 'var(--text-secondary)' }}>액션</th>
                  </tr>
                </thead>
                <tbody>
                  {visiblePosts.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
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
                          </span>
                        </td>
                        <td className="px-3 py-2 hidden md:table-cell text-xs" style={{ color: 'var(--text-secondary)' }}>
                          {post.category?.name || '-'}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex flex-wrap gap-1">
                            {issues.map(iss => (
                              <span key={iss} className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${ISSUE_COLORS[iss] || 'bg-gray-100 text-gray-600'}`}>
                                {iss}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-3 py-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[post.status] || 'bg-gray-100 text-gray-600'}`}>
                            {post.status}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-1 justify-end">
                            <Link
                              to={`/post/${post.slug}`}
                              target="_blank"
                              className="px-2 py-1 text-xs rounded border hover:bg-gray-50"
                              style={{ borderColor: 'var(--border)' }}
                            >
                              보기
                            </Link>
                            <Link
                              to={`/editor/${post.slug}`}
                              className="px-2 py-1 text-xs rounded border hover:bg-gray-50"
                              style={{ borderColor: 'var(--border)' }}
                            >
                              편집
                            </Link>
                            <button
                              onClick={() => handleDelete(post.slug)}
                              className="px-2 py-1 text-xs rounded border text-red-600 hover:bg-red-50"
                              style={{ borderColor: 'var(--border)' }}
                            >
                              삭제
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <p className="mt-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
              {visiblePosts.length}개 표시 / 전체 {posts.length}개
            </p>
          </div>
        </div>
      )}

      {/* ─── 태그 탭 ─── */}
      {tab === 'tags' && (
        <div className="space-y-6">
          {/* 병합 */}
          <div className="p-4 rounded-xl border" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
            <h3 className="font-semibold mb-3" style={{ color: 'var(--text)' }}>태그 병합</h3>
            <div className="flex flex-wrap gap-3 items-end">
              <div>
                <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>소스 태그 (삭제됨)</label>
                <select
                  value={mergeSrc}
                  onChange={e => setMergeSrc(e.target.value)}
                  className="border rounded px-2 py-1 text-sm"
                  style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
                >
                  <option value="">선택</option>
                  {tags.map(t => <option key={t.slug} value={t.slug}>{t.name} ({t.post_count})</option>)}
                </select>
              </div>
              <span className="text-gray-400">→</span>
              <div>
                <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>대상 태그 (유지됨)</label>
                <select
                  value={mergeDst}
                  onChange={e => setMergeDst(e.target.value)}
                  className="border rounded px-2 py-1 text-sm"
                  style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
                >
                  <option value="">선택</option>
                  {tags.map(t => <option key={t.slug} value={t.slug}>{t.name} ({t.post_count})</option>)}
                </select>
              </div>
              <button
                onClick={handleMerge}
                className="px-4 py-1.5 rounded bg-primary-600 text-white text-sm hover:bg-primary-700"
              >
                병합
              </button>
            </div>
          </div>

          {/* 고아 태그 삭제 */}
          <div className="flex items-center gap-4">
            <button
              onClick={handleCleanup}
              className="px-4 py-2 rounded border text-sm text-red-600 hover:bg-red-50"
              style={{ borderColor: 'var(--border)' }}
            >
              고아 태그 일괄 삭제
            </button>
            <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              포스트 0개인 태그를 모두 제거합니다.
            </span>
          </div>

          {/* 태그 목록 */}
          <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
                  <th className="px-4 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>태그</th>
                  <th className="px-4 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>슬러그</th>
                  <th className="px-4 py-2 text-right font-medium" style={{ color: 'var(--text-secondary)' }}>포스트 수</th>
                </tr>
              </thead>
              <tbody>
                {tags.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
                      태그가 없습니다.
                    </td>
                  </tr>
                )}
                {tags.map(tag => (
                  <tr key={tag.slug} className="border-t" style={{ borderColor: 'var(--border)' }}>
                    <td className="px-4 py-2 font-medium" style={{ color: 'var(--text)' }}>{tag.name}</td>
                    <td className="px-4 py-2 text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{tag.slug}</td>
                    <td className="px-4 py-2 text-right" style={{ color: tag.post_count === 0 ? 'var(--text-secondary)' : 'var(--text)' }}>
                      {tag.post_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </motion.div>
  )
}
