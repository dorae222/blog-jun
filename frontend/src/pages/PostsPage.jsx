import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { LayoutGrid, List, ChevronLeft, ChevronRight, SlidersHorizontal, X } from 'lucide-react'
import { Helmet } from 'react-helmet-async'

import ExploreNav from '../components/explore/ExploreNav'
import CategoryTabs from '../components/blog/CategoryTabs'
import LeftSidebar from '../components/blog/LeftSidebar'
import FeedCard from '../components/blog/FeedCard'
import BulletinListView from '../components/blog/BulletinListView'
import { getFeed } from '../api/posts'
import { CATEGORY_TREE } from '../data/categories'

// 탭별 기본 뷰 모드
const DEFAULT_VIEW = { ai: 'card', cloud: 'list', data: 'list' }

export default function PostsPage() {
  const { category, sub } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()

  const sort = searchParams.get('sort') || 'newest'
  const viewParam = searchParams.get('view')
  const page = parseInt(searchParams.get('page') || '1', 10)
  const q = searchParams.get('q') || ''
  const tag = searchParams.get('tag') || ''

  // 뷰 모드: URL 파라미터 > 탭 기본값
  const viewMode = viewParam || DEFAULT_VIEW[category] || 'list'

  const [items, setItems] = useState([])
  const [pinnedItems, setPinnedItems] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [counts, setCounts] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // 무한스크롤용
  const [infiniteItems, setInfiniteItems] = useState([])
  const [infinitePage, setInfinitePage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const observerRef = useRef(null)

  // Sidebar drawer body scroll lock
  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [sidebarOpen])

  const PAGE_SIZE = 20

  const fetchFeed = useCallback(async (pageNum = 1, append = false) => {
    if (append) setLoadingMore(true)
    else setLoading(true)

    try {
      const params = { page: pageNum, page_size: PAGE_SIZE, sort }
      if (category) params.category = category
      if (sub) params.sub = sub
      if (q) params.q = q
      if (tag) params.tag = tag
      // 첫 요청 시 카운트 포함
      if (!counts) params.include_counts = 'true'

      const res = await getFeed(params)
      const data = res.data
      const results = data.results || []
      const count = data.count || 0

      if (data.categories) setCounts(data.categories)

      if (viewMode === 'card') {
        // 무한스크롤 모드
        if (append) {
          setInfiniteItems((prev) => [...prev, ...results])
        } else {
          setInfiniteItems(results)
        }
        setHasMore(results.length >= PAGE_SIZE)
      } else {
        // 페이지네이션 모드: 고정글 분리
        const pinned = results.filter((r) => r.is_pinned)
        const normal = results.filter((r) => !r.is_pinned)
        setPinnedItems(pinned)
        setItems(normal)
      }

      setTotalCount(count)
      setTotalPages(Math.ceil(count / PAGE_SIZE))
    } catch {
      // Silently handled — loading state will clear
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [category, sub, sort, q, tag, viewMode, counts])

  // 카테고리/서브/정렬/검색 변경 시 리셋
  useEffect(() => {
    window.scrollTo(0, 0)
    setInfinitePage(1)
    setInfiniteItems([])
    setHasMore(true)
    fetchFeed(viewMode === 'card' ? 1 : page)
  }, [category, sub, sort, q, tag, page, viewMode])

  // 무한스크롤 observer
  useEffect(() => {
    if (viewMode !== 'card' || !hasMore || loadingMore) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) {
          const nextPage = infinitePage + 1
          setInfinitePage(nextPage)
          fetchFeed(nextPage, true)
        }
      },
      { rootMargin: '200px' }
    )

    if (observerRef.current) observer.observe(observerRef.current)
    return () => observer.disconnect()
  }, [viewMode, hasMore, loadingMore, infinitePage, fetchFeed])

  const setView = (v) => {
    const params = new URLSearchParams(searchParams)
    params.set('view', v)
    params.delete('page')
    setSearchParams(params)
  }

  const setSort = (s) => {
    const params = new URLSearchParams(searchParams)
    params.set('sort', s)
    params.delete('page')
    setSearchParams(params)
  }

  const goToPage = (p) => {
    const params = new URLSearchParams(searchParams)
    params.set('page', String(p))
    setSearchParams(params)
  }

  const catNode = CATEGORY_TREE.find((c) => c.key === category)
  const subNode = catNode?.subs?.find((s) => s.key === sub)
  const pageTitle = subNode
    ? `${catNode.label} / ${subNode.label} | HJ Tech Blog`
    : catNode
    ? `${catNode.label} | HJ Tech Blog`
    : '포스트 | HJ Tech Blog'

  return (
    <>
    <Helmet>
      <title>{pageTitle}</title>
      <meta name="description" content={catNode?.desc || 'AI, 클라우드, 데이터 엔지니어링 기술 블로그. 논문 리뷰, 튜토리얼, 프로젝트 기록을 공유합니다.'} />
      <meta property="og:title" content={pageTitle} />
      <meta property="og:type" content="website" />
    </Helmet>
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className="max-w-7xl mx-auto px-4 py-6"
    >
      <div className="mb-5">
        <ExploreNav />
      </div>

      <div className="flex gap-6">
        <LeftSidebar category={category} sub={sub} counts={counts} />

        <div className="flex-1 min-w-0">
          {/* 모바일 필터 버튼 */}
          <div className="lg:hidden mb-3">
            <button onClick={() => setSidebarOpen(true)}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border text-sm min-h-[44px]"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
              <SlidersHorizontal size={16} /> 필터
            </button>
          </div>

          {/* 모바일 사이드바 드로어 */}
          <AnimatePresence>
            {sidebarOpen && (
              <>
                <motion.div
                  className="fixed inset-0 bg-black/40 z-40 lg:hidden"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  onClick={() => setSidebarOpen(false)}
                />
                <motion.div
                  className="fixed top-0 left-0 h-full w-72 z-50 lg:hidden overflow-y-auto border-r"
                  style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}
                  initial={{ x: -288 }} animate={{ x: 0 }} exit={{ x: -288 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                >
                  <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'var(--border)' }}>
                    <span className="font-semibold text-sm" style={{ color: 'var(--text)' }}>카테고리</span>
                    <button onClick={() => setSidebarOpen(false)} className="p-1 rounded-lg hover:bg-gray-50">
                      <X size={18} style={{ color: 'var(--text-secondary)' }} />
                    </button>
                  </div>
                  <div className="p-4">
                    <LeftSidebar category={category} sub={sub} counts={counts} mobile onNavigate={() => setSidebarOpen(false)} />
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>

          {/* 탭 */}
          <CategoryTabs category={category} sub={sub} counts={counts} />

          {/* 툴바 */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-2">
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                className="text-xs px-2 py-1 rounded-lg border"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)', background: 'var(--card-bg)' }}
              >
                <option value="newest">최신순</option>
                <option value="popular">인기순</option>
              </select>
            </div>

            <div className="flex items-center gap-3">
              {/* 뷰 모드 토글 */}
              <div className="flex items-center border rounded-lg overflow-hidden"
                style={{ borderColor: 'var(--border)' }}>
                <button
                  onClick={() => setView('card')}
                  className="p-2 transition-colors"
                  style={{
                    background: viewMode === 'card' ? 'var(--text)' : 'transparent',
                    color: viewMode === 'card' ? '#fff' : 'var(--text-secondary)',
                  }}
                  aria-label="카드형"
                >
                  <LayoutGrid size={14} />
                </button>
                <button
                  onClick={() => setView('list')}
                  className="p-2 transition-colors"
                  style={{
                    background: viewMode === 'list' ? 'var(--text)' : 'transparent',
                    color: viewMode === 'list' ? '#fff' : 'var(--text-secondary)',
                  }}
                  aria-label="목록형"
                >
                  <List size={14} />
                </button>
              </div>

              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                {totalCount}건
              </span>
            </div>
          </div>

          {/* 검색/태그 필터 표시 */}
          {(q || tag) && (
            <div className="mb-4 flex items-center gap-2">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {q ? `"${q}" 검색 결과` : `#${tag} 태그`} — {totalCount}건
              </span>
              <button
                onClick={() => {
                  const params = new URLSearchParams(searchParams)
                  params.delete('q')
                  params.delete('tag')
                  setSearchParams(params)
                }}
                className="text-xs px-2 py-0.5 rounded-full border"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
              >
                초기화
              </button>
            </div>
          )}

          {/* 콘텐츠 영역 */}
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 rounded-xl skeleton" />
              ))}
            </div>
          ) : viewMode === 'card' ? (
            <>
              <motion.div
                className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4"
                initial="hidden"
                animate="visible"
                variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.04 } } }}
              >
                {infiniteItems.map((item) => (
                  <motion.div
                    key={item.slug}
                    variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
                  >
                    <FeedCard item={item} />
                  </motion.div>
                ))}
              </motion.div>
              {infiniteItems.length === 0 && (
                <div className="py-12 text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
                  게시글이 없습니다.
                </div>
              )}
              {/* 무한스크롤 sentinel */}
              {hasMore && (
                <div ref={observerRef} className="py-8 text-center">
                  {loadingMore && (
                    <div className="inline-block w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
                  )}
                </div>
              )}
            </>
          ) : (
            <>
              <BulletinListView
                items={items}
                totalCount={totalCount}
                pinnedItems={pinnedItems}
              />

              {/* 페이지네이션 */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-1 mt-6">
                  <button
                    onClick={() => goToPage(Math.max(1, page - 1))}
                    disabled={page <= 1}
                    className="p-2 rounded-lg border disabled:opacity-30 transition-colors hover:bg-gray-50"
                    style={{ borderColor: 'var(--border)' }}
                  >
                    <ChevronLeft size={16} />
                  </button>
                  {(() => {
                    const pages = new Set([1, totalPages])
                    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) pages.add(i)
                    const sorted = [...pages].sort((a, b) => a - b)
                    const result = []
                    let prev = 0
                    for (const p of sorted) {
                      if (p - prev > 1) result.push('...')
                      result.push(p)
                      prev = p
                    }
                    return result.map((p, i) =>
                      p === '...' ? (
                        <span key={`ellipsis-${i}`} className="px-1 text-xs" style={{ color: 'var(--text-secondary)' }}>...</span>
                      ) : (
                        <button
                          key={p}
                          onClick={() => goToPage(p)}
                          className="min-w-[44px] min-h-[44px] text-xs rounded-lg border transition-colors"
                          style={{
                            borderColor: p === page ? 'var(--text)' : 'var(--border)',
                            background: p === page ? 'var(--text)' : 'transparent',
                            color: p === page ? '#fff' : 'var(--text-secondary)',
                          }}
                        >
                          {p}
                        </button>
                      )
                    )
                  })()}
                  <button
                    onClick={() => goToPage(Math.min(totalPages, page + 1))}
                    disabled={page >= totalPages}
                    className="p-2 rounded-lg border disabled:opacity-30 transition-colors hover:bg-gray-50"
                    style={{ borderColor: 'var(--border)' }}
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </motion.div>
    </>
  )
}
