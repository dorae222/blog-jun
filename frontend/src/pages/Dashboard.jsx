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
import {
  FileText, CheckCircle, Clock, Eye, AlertTriangle, Pencil, Trash2,
  LayoutGrid, Cloud, Brain, Database, Code2, FolderOpen, Terminal, BookOpen,
  Archive, Plus, Tags, ChevronLeft, ChevronRight,
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

const PAGE_SIZE = 10

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

const CAT_ICONS = {
  '':           LayoutGrid,
  'cloud':      Cloud,
  'ai-ml':      Brain,
  'data':       Database,
  'dev':        Code2,
  'foundation': BookOpen,
  'project':    FolderOpen,
  'program':    Terminal,
}

const STATUS_META = [
  { value: '',          label: '전체',     Icon: LayoutGrid,  dot: null      },
  { value: 'published', label: 'Published', Icon: CheckCircle, dot: '#10b981' },
  { value: 'draft',     label: 'Draft',     Icon: Clock,       dot: '#f59e0b' },
  { value: 'archived',  label: 'Archived',  Icon: Archive,     dot: '#94a3b8' },
]

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()

  // 탭: posts | tags
  const [tab, setTab] = useState('posts')

  // 포스트 목록 상태
  const [stats, setStats] = useState(null)
  const [posts, setPosts] = useState([])
  const [totalPosts, setTotalPosts] = useState(0)
  const [page, setPage] = useState(1)
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
  const loadPosts = useCallback((statusF = statusFilter, catF = categoryFilter, pageNum = page) => {
    const params = { page_size: PAGE_SIZE, page: pageNum }
    if (statusF) params.status = statusF
    if (catF)    params['category__slug'] = catF
    getPosts(params).then(r => {
      const list = r.data.results || r.data || []
      setPosts(list)
      setTotalPosts(r.data.count || 0)
      setSelected(new Set())
    }).catch(() => toast.error('포스트 로드 실패'))
  }, [statusFilter, categoryFilter, page])

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
    loadAudit()
  }, [user, navigate])

  useEffect(() => {
    if (tab === 'tags') loadTags()
  }, [tab])

  useEffect(() => {
    loadPosts(statusFilter, categoryFilter, page)
  }, [statusFilter, categoryFilter, page])

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

  // Stats Bar 정의 (auditSummary 클로저 접근)
  const STAT_DEFS = [
    { label: '총 포스트', icon: FileText,      accent: '#3b82f6', fn: s => s.total_posts  },
    { label: '발행',       icon: CheckCircle,   accent: '#10b981', fn: s => s.published   },
    { label: '초안',       icon: Clock,         accent: '#f59e0b', fn: s => s.drafts      },
    { label: '총 조회수',  icon: Eye,           accent: '#8b5cf6', fn: s => s.total_views },
    { label: '감사 이슈',  icon: AlertTriangle, accent: '#ef4444', fn: () => auditSummary.total_issues },
  ]

  const totalPages = Math.ceil(totalPosts / PAGE_SIZE)

  if (!user) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-7xl mx-auto px-4 py-10"
    >
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Dashboard</h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>
            포스트 관리 및 블로그 현황
          </p>
        </div>
        <Link to="/editor"
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 text-white
            hover:bg-primary-700 text-sm font-medium transition-colors">
          <Plus size={15} /> 새 포스트
        </Link>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          {STAT_DEFS.map(({ label, icon: Icon, accent, fn }) => (
            <div key={label} className="relative p-4 rounded-xl overflow-hidden"
              style={{ background: 'var(--card-bg)', border: '1px solid var(--border)',
                       borderLeft: `4px solid ${accent}` }}>
              <Icon size={32} className="absolute right-3 top-3"
                style={{ color: accent, opacity: 0.12 }} />
              <p className="text-2xl font-bold" style={{ color: accent }}>
                {(fn(stats) ?? 0).toLocaleString()}
              </p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* 탭 (세그먼트 컨트롤) */}
      <div className="flex gap-1 mb-6 p-1 rounded-xl w-fit"
        style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
        {[
          { id: 'posts', label: '포스트', Icon: FileText },
          { id: 'tags',  label: '태그 관리', Icon: Tags },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              tab === t.id
                ? 'bg-white shadow-sm text-primary-600'
                : 'hover:bg-white/50'
            }`}
            style={tab !== t.id ? { color: 'var(--text-secondary)' } : {}}>
            <t.Icon size={14} /> {t.label}
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
                        <td className="px-3 py-2 hidden md:table-cell">
                          {post.category ? (
                            <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                              style={{
                                background: `${post.category.color || '#6366f1'}15`,
                                color: post.category.color || '#6366f1',
                              }}>
                              {post.category.name}
                            </span>
                          ) : <span style={{ color: 'var(--text-secondary)' }}>—</span>}
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
                          ) : <span style={{ color: 'var(--border)' }}>—</span>}
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
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                {visiblePosts.length}개 표시 / 전체 {totalPosts}개
              </p>
              {totalPages > 1 && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-1.5 rounded border text-xs transition-colors disabled:opacity-40"
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
                    className="p-1.5 rounded border text-xs transition-colors disabled:opacity-40"
                    style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
                  >
                    <ChevronRight size={14} />
                  </button>
                </div>
              )}
            </div>
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
                  <tr key={tag.slug} className="border-t"
                    style={{ borderColor: 'var(--border)', opacity: tag.post_count === 0 ? 0.45 : 1 }}>
                    <td className="px-4 py-2">
                      <span className="inline-flex items-center gap-1.5 text-sm font-medium"
                        style={{ color: 'var(--text)' }}>
                        <span className="w-2 h-2 rounded-full flex-shrink-0"
                          style={{ background: `hsl(${(tag.name.charCodeAt(0) * 37) % 360},55%,60%)` }} />
                        {tag.name}
                      </span>
                    </td>
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
