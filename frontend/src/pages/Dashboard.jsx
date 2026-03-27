import { useEffect, useState, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import useAuth from '../hooks/useAuth'
import {
  getDashboardStats, getPosts, deletePost,
  bulkDeletePosts, bulkUpdateStatus,
  getAuditResults, getTags, mergeTags, cleanupTags,
  getArchitectures, deleteArchitecture,
} from '../api/posts'
import toast from 'react-hot-toast'
import {
  FileText, CheckCircle, Clock,
  LayoutGrid, Cloud, Brain, Database, Code2, FolderOpen, Terminal, BookOpen,
  Archive, Plus, Tags, Cpu,
  BarChart3, MessageCircle,
} from 'lucide-react'
import StatsBar from '../components/dashboard/StatsBar'
import PostsTab from '../components/dashboard/PostsTab'
import ArchitecturesTab from '../components/dashboard/ArchitecturesTab'
import TagsTab from '../components/dashboard/TagsTab'
import CommentsTab from '../components/dashboard/CommentsTab'
import OverviewTab from '../components/dashboard/OverviewTab'

const DEFAULT_PAGE_SIZE = 10

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

const POST_TYPES = [
  { value: '',              label: '전체 타입' },
  { value: 'article',       label: 'Article' },
  { value: 'paper_review',  label: 'Paper Review' },
  { value: 'tutorial',      label: 'Tutorial' },
  { value: 'til',           label: 'TIL' },
  { value: 'project',       label: 'Project' },
  { value: 'activity_log',  label: 'Activity Log' },
]

const ARCH_CATEGORIES = [
  { value: '',           label: '전체' },
  { value: 'llm',        label: 'LLM' },
  { value: 'ssm',        label: 'SSM' },
  { value: 'diffusion',  label: 'Diffusion' },
  { value: 'multimodal', label: 'Multimodal' },
  { value: 'agent',      label: 'Agent' },
  { value: 'technique',  label: 'Technique' },
  { value: 'vision',     label: 'Vision' },
]

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()

  // 탭: posts | architectures | tags | overview
  const [tab, setTab] = useState('posts')

  // 포스트 목록 상태
  const [stats, setStats] = useState(null)
  const [posts, setPosts] = useState([])
  const [totalPosts, setTotalPosts] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [statusFilter, setStatusFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [postTypeFilter, setPostTypeFilter] = useState('')
  const [noImageFilter, setNoImageFilter] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
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

  // 아키텍처 탭
  const [archEntries, setArchEntries] = useState([])
  const [archCatFilter, setArchCatFilter] = useState('')

  // 데이터 로드
  const loadPosts = useCallback((statusF = statusFilter, catF = categoryFilter, pageNum = page, typeF = postTypeFilter, noImg = noImageFilter, search = searchQuery) => {
    const params = { page_size: pageSize, page: pageNum }
    if (statusF) params.status = statusF
    if (catF)    params['category__slug'] = catF
    if (typeF)   params.post_type = typeF
    if (noImg)   params.has_cover = 'false'
    if (search)  params.search = search
    getPosts(params).then(r => {
      const list = r.data.results || r.data || []
      setPosts(list)
      setTotalPosts(r.data.count || 0)
      setSelected(new Set())
    }).catch(() => toast.error('포스트 로드 실패'))
  }, [statusFilter, categoryFilter, page, pageSize, postTypeFilter, noImageFilter, searchQuery])

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

  const loadArchitectures = useCallback((catF = archCatFilter) => {
    const params = {}
    if (catF) params.architecture_category = catF
    getArchitectures(params).then(r => setArchEntries(r.data.results || r.data || [])).catch(() => {})
  }, [archCatFilter])

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    getDashboardStats().then(r => setStats(r.data)).catch(() => {})
    loadAudit()
  }, [user, navigate])

  useEffect(() => {
    if (tab === 'tags') loadTags()
    if (tab === 'architectures') loadArchitectures()
  }, [tab])

  useEffect(() => {
    loadPosts(statusFilter, categoryFilter, page, postTypeFilter, noImageFilter, searchQuery)
  }, [statusFilter, categoryFilter, page, pageSize, postTypeFilter, noImageFilter, searchQuery])

  useEffect(() => {
    loadArchitectures(archCatFilter)
  }, [archCatFilter])

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

  // 검색 디바운스
  const [searchInput, setSearchInput] = useState('')
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(searchInput)
      setPage(1)
    }, 400)
    return () => clearTimeout(timer)
  }, [searchInput])

  const missingImageCount = stats?.image_coverage?.missing_image ?? 0
  const totalPages = Math.ceil(totalPosts / pageSize)

  if (!user) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
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
      <StatsBar
        stats={stats}
        auditTotalIssues={auditSummary.total_issues}
        missingImageCount={missingImageCount}
      />

      {/* 탭 (세그먼트 컨트롤) */}
      <div className="flex gap-1 mb-6 p-1 rounded-xl w-fit"
        style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
        {[
          { id: 'posts', label: '포스트', Icon: FileText },
          { id: 'architectures', label: 'Architectures', Icon: Cpu },
          { id: 'tags',  label: '태그 관리', Icon: Tags },
          { id: 'comments', label: '댓글 관리', Icon: MessageCircle },
          { id: 'overview', label: '콘텐츠 현황', Icon: BarChart3 },
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
        <PostsTab
          categoryFilter={categoryFilter} setCategoryFilter={setCategoryFilter}
          statusFilter={statusFilter} setStatusFilter={setStatusFilter}
          postTypeFilter={postTypeFilter} setPostTypeFilter={setPostTypeFilter}
          noImageFilter={noImageFilter} setNoImageFilter={setNoImageFilter}
          auditFilter={auditFilter} setAuditFilter={setAuditFilter}
          searchInput={searchInput} setSearchInput={setSearchInput}
          setPage={setPage}
          visiblePosts={visiblePosts} totalPosts={totalPosts}
          page={page} totalPages={totalPages}
          pageSize={pageSize} setPageSize={(size) => { setPageSize(size); setPage(1) }}
          auditMap={auditMap} selected={selected}
          toggleSelect={toggleSelect} toggleAll={toggleAll}
          handleDelete={handleDelete} handleBulkDelete={handleBulkDelete}
          handleBulkStatus={handleBulkStatus} loadAudit={loadAudit}
          CATEGORIES={CATEGORIES} STATUS_META={STATUS_META}
          POST_TYPES={POST_TYPES} CAT_ICONS={CAT_ICONS}
        />
      )}

      {/* ─── Architectures 탭 ─── */}
      {tab === 'architectures' && (
        <ArchitecturesTab
          archEntries={archEntries}
          archCatFilter={archCatFilter} setArchCatFilter={setArchCatFilter}
          loadArchitectures={loadArchitectures}
          deleteArchitecture={deleteArchitecture}
          ARCH_CATEGORIES={ARCH_CATEGORIES}
        />
      )}

      {/* ─── 태그 탭 ─── */}
      {tab === 'tags' && (
        <TagsTab
          tags={tags}
          mergeSrc={mergeSrc} setMergeSrc={setMergeSrc}
          mergeDst={mergeDst} setMergeDst={setMergeDst}
          handleMerge={handleMerge} handleCleanup={handleCleanup}
        />
      )}

      {/* ─── 댓글 관리 탭 ─── */}
      {tab === 'comments' && <CommentsTab />}

      {/* ─── 콘텐츠 현황 탭 ─── */}
      {tab === 'overview' && (
        <OverviewTab
          stats={stats}
          onShowMissingImages={() => { setTab('posts'); setNoImageFilter(true); setPage(1) }}
        />
      )}
    </motion.div>
  )
}
