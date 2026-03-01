import { useEffect, useState, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { LayoutGrid, List, ChevronDown, SlidersHorizontal, X } from 'lucide-react'
import PostCard from '../components/blog/PostCard'
import SearchBar from '../components/common/SearchBar'
import { searchPosts, getPosts, getCategories, getTags } from '../api/posts'
import { getCategoryIcon } from '../utils/categoryIcons'

const PAGE_SIZE = 10
const POST_TYPES = ['', 'article', 'tutorial', 'paper_review', 'til', 'project', 'activity_log']
const TYPE_LABELS = {
  '': 'All',
  article: 'Article',
  tutorial: 'Tutorial',
  paper_review: 'Paper Review',
  til: 'TIL',
  project: 'Project',
  activity_log: 'Activity Log',
}

// ── Sidebar: 컴포넌트 외부에 정의해 매 렌더링 시 remount 방지
function Sidebar({ paramCat, paramType, updateParams, categories, tags }) {
  return (
    <aside className="w-60 shrink-0 space-y-6">
      {/* 검색바 */}
      <SearchBar className="w-full" />

      {/* 카테고리 */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: 'var(--text-secondary)' }}>
          Category
        </p>
        <ul className="space-y-1">
          <li>
            <button
              onClick={() => updateParams({ category: '' })}
              className={`w-full text-left px-3 py-1.5 rounded-lg text-sm flex items-center gap-2 transition-colors ${
                !paramCat ? 'bg-primary-100 text-primary-700 font-medium' : 'hover:bg-gray-100'
              }`}
              style={paramCat ? { color: 'var(--text)' } : {}}
            >
              All
            </button>
          </li>
          {categories.map(cat => (
            <li key={cat.id}>
              <button
                onClick={() => updateParams({ category: cat.slug })}
                className={`w-full text-left px-3 py-1.5 rounded-lg text-sm flex items-center gap-2 transition-colors ${
                  paramCat === cat.slug ? 'bg-primary-100 text-primary-700 font-medium' : 'hover:bg-gray-100'
                }`}
                style={paramCat !== cat.slug ? { color: 'var(--text)' } : {}}
              >
                <span style={{ color: cat.color || 'var(--text-secondary)' }}>
                  {getCategoryIcon(cat.slug, 14)}
                </span>
                <span className="flex-1 truncate">{cat.name}</span>
                {cat.post_count > 0 && (
                  <span
                    className="text-xs px-1.5 py-0.5 rounded-full"
                    style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
                  >
                    {cat.post_count}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Post Type */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: 'var(--text-secondary)' }}>
          Post Type
        </p>
        <div className="flex flex-wrap gap-1.5">
          {POST_TYPES.map(type => (
            <button
              key={type || 'all'}
              onClick={() => updateParams({ type })}
              className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                paramType === type
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'hover:border-primary-400'
              }`}
              style={paramType !== type ? { borderColor: 'var(--border)', color: 'var(--text-secondary)' } : {}}
            >
              {TYPE_LABELS[type]}
            </button>
          ))}
        </div>
      </div>

      {/* 태그 클라우드 */}
      {tags.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: 'var(--text-secondary)' }}>
            Tags
          </p>
          <div className="flex flex-wrap gap-1.5">
            {tags.slice(0, 20).map(t => (
              <a
                key={t.id}
                href={`/search?q=${t.slug}`}
                className="transition-all hover:scale-105 hover:text-primary-600"
                style={{
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-secondary)',
                  fontSize: `${Math.max(0.65, Math.min(1.0, 0.65 + (t.post_count || 0) * 0.04))}rem`,
                  padding: '2px 8px',
                  borderRadius: '9999px',
                }}
              >
                #{t.name}
              </a>
            ))}
          </div>
        </div>
      )}
    </aside>
  )
}

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const q           = searchParams.get('q')        || ''
  const paramType   = searchParams.get('type')     || ''
  const paramCat    = searchParams.get('category') || ''
  const paramPage   = parseInt(searchParams.get('page') || '1', 10)
  const paramView   = searchParams.get('view')     || 'grid'
  const paramSort   = searchParams.get('sort')     || 'newest'

  const [posts, setPosts]             = useState([])
  const [total, setTotal]             = useState(0)
  const [categories, setCategories]   = useState([])
  const [tags, setTags]               = useState([])
  const [loading, setLoading]         = useState(false)
  const [mobileFilter, setMobileFilter] = useState(false)

  // URL 파라미터 업데이트 헬퍼 — 필터 변경 시 page 자동 초기화
  const updateParams = useCallback((updates) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      Object.entries(updates).forEach(([k, v]) => {
        if (v === '' || v === null || v === undefined) next.delete(k)
        else next.set(k, String(v))
      })
      if (!('page' in updates)) next.set('page', '1')
      return next
    })
  }, [setSearchParams])

  // 포스트 로드 — URL 파라미터 기반으로 단일 effect
  useEffect(() => {
    setLoading(true)
    if (q) {
      searchPosts(q)
        .then(r => {
          const list = Array.isArray(r.data) ? r.data : r.data.results || []
          setPosts(list)
          setTotal(r.data.count || list.length)
        })
        .finally(() => setLoading(false))
    } else {
      const params = { status: 'published', page: paramPage, page_size: PAGE_SIZE }
      if (paramType) params.post_type          = paramType
      if (paramCat)  params['category__slug']  = paramCat
      if (paramSort === 'popular') params.ordering = '-view_count'
      getPosts(params)
        .then(r => {
          setPosts(r.data.results || [])
          setTotal(r.data.count || 0)
        })
        .finally(() => setLoading(false))
    }
  }, [q, paramType, paramCat, paramPage, paramSort])

  // 카테고리·태그는 한 번만 로드
  useEffect(() => {
    getCategories().then(r => setCategories(r.data.results || r.data || []))
    getTags().then(r => setTags(r.data.results || r.data || []))
  }, [])

  const totalPages = Math.ceil(total / PAGE_SIZE)

  const sidebarProps = { paramCat, paramType, updateParams, categories, tags }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-7xl mx-auto px-4 py-12"
    >
      <div className="flex gap-8">
        {/* 데스크탑 사이드바 */}
        <div className="hidden lg:block">
          <Sidebar {...sidebarProps} />
        </div>

        {/* 모바일 필터 시트 */}
        <AnimatePresence>
          {mobileFilter && (
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'tween', duration: 0.25 }}
              className="fixed inset-0 z-50 flex lg:hidden"
            >
              <div
                className="w-72 h-full overflow-y-auto p-6 shadow-xl"
                style={{ background: 'var(--bg)' }}
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="font-semibold" style={{ color: 'var(--text)' }}>Filters</span>
                  <button onClick={() => setMobileFilter(false)}>
                    <X size={20} style={{ color: 'var(--text-secondary)' }} />
                  </button>
                </div>
                <Sidebar {...sidebarProps} />
              </div>
              <div className="flex-1 bg-black/40" onClick={() => setMobileFilter(false)} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* 메인 영역 */}
        <div className="flex-1 min-w-0">
          {/* 상단 바 */}
          <div className="flex items-center justify-between mb-6 gap-3 flex-wrap">
            <div className="flex items-center gap-3">
              <button
                className="lg:hidden flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
                onClick={() => setMobileFilter(true)}
              >
                <SlidersHorizontal size={14} />
                Filters
              </button>
              <h1 className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                {q ? `"${q}" 검색 결과` : 'Posts'}
              </h1>
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {total.toLocaleString()}개
              </span>
            </div>

            <div className="flex items-center gap-2">
              {/* 정렬 */}
              <div className="relative">
                <select
                  value={paramSort}
                  onChange={e => updateParams({ sort: e.target.value })}
                  className="appearance-none pl-3 pr-8 py-1.5 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
                >
                  <option value="newest">최신순</option>
                  <option value="popular">인기순</option>
                </select>
                <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--text-secondary)' }} />
              </div>

              {/* Grid/List 토글 */}
              <div className="flex rounded-lg border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
                <button
                  onClick={() => updateParams({ view: 'grid' })}
                  className="px-2.5 py-1.5 transition-colors"
                  style={{
                    background: paramView === 'grid' ? 'var(--bg-secondary)' : 'var(--card-bg)',
                    color: paramView === 'grid' ? 'var(--text)' : 'var(--text-secondary)',
                  }}
                >
                  <LayoutGrid size={16} />
                </button>
                <button
                  onClick={() => updateParams({ view: 'list' })}
                  className="px-2.5 py-1.5 transition-colors border-l"
                  style={{
                    borderColor: 'var(--border)',
                    background: paramView === 'list' ? 'var(--bg-secondary)' : 'var(--card-bg)',
                    color: paramView === 'list' ? 'var(--text)' : 'var(--text-secondary)',
                  }}
                >
                  <List size={16} />
                </button>
              </div>
            </div>
          </div>

          {/* 활성 필터 칩 */}
          {(paramCat || paramType || q) && (
            <div className="flex flex-wrap gap-2 mb-4">
              {q && (
                <span className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-primary-100 text-primary-700">
                  검색: {q}
                  <a href="/search" className="hover:opacity-70"><X size={12} /></a>
                </span>
              )}
              {paramCat && (
                <button
                  onClick={() => updateParams({ category: '' })}
                  className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-primary-100 text-primary-700"
                >
                  {paramCat} <X size={12} />
                </button>
              )}
              {paramType && (
                <button
                  onClick={() => updateParams({ type: '' })}
                  className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-primary-100 text-primary-700"
                >
                  {TYPE_LABELS[paramType]} <X size={12} />
                </button>
              )}
            </div>
          )}

          {/* 포스트 목록 */}
          {loading ? (
            <div className={paramView === 'list' ? 'space-y-3' : 'grid md:grid-cols-2 xl:grid-cols-3 gap-6'}>
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="rounded-2xl animate-pulse"
                  style={{ background: 'var(--bg-secondary)', height: paramView === 'list' ? '80px' : '200px' }}
                />
              ))}
            </div>
          ) : posts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 gap-4">
              <p className="text-lg" style={{ color: 'var(--text-secondary)' }}>검색 결과가 없습니다.</p>
              <button
                onClick={() => setSearchParams({})}
                className="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm hover:bg-primary-700 transition-colors"
              >
                필터 초기화
              </button>
            </div>
          ) : paramView === 'list' ? (
            <div className="space-y-3">
              {posts.map(post => (
                <PostCard key={post.id} post={post} variant="list" />
              ))}
            </div>
          ) : (
            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
              {posts.map(post => (
                <PostCard key={post.id} post={post} />
              ))}
            </div>
          )}

          {/* 페이지네이션 */}
          {!loading && totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 mt-10">
              <button
                onClick={() => updateParams({ page: paramPage - 1 })}
                disabled={paramPage === 1}
                className="px-4 py-2 rounded-lg border text-sm transition-colors disabled:opacity-40"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                Prev
              </button>
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {paramPage} / {totalPages} 페이지
              </span>
              <button
                onClick={() => updateParams({ page: paramPage + 1 })}
                disabled={paramPage === totalPages}
                className="px-4 py-2 rounded-lg border text-sm transition-colors disabled:opacity-40"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
