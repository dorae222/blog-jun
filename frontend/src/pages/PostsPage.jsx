import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { LayoutGrid, List, ChevronLeft, ChevronRight } from 'lucide-react'

import CategoryTabs from '../components/blog/CategoryTabs'
import LeftSidebar from '../components/blog/LeftSidebar'
import FeedCard from '../components/blog/FeedCard'
import BulletinListView from '../components/blog/BulletinListView'
import { getFeed } from '../api/posts'

// 탭별 기본 뷰 모드
const DEFAULT_VIEW = { ai: 'card', cloud: 'list', data: 'list' }

export default function PostsPage() {
  const { category, sub } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()

  const sort = searchParams.get('sort') || 'newest'
  const viewParam = searchParams.get('view')
  const page = parseInt(searchParams.get('page') || '1', 10)
  const q = searchParams.get('q') || ''

  // 뷰 모드: URL 파라미터 > 탭 기본값
  const viewMode = viewParam || DEFAULT_VIEW[category] || 'list'

  const [items, setItems] = useState([])
  const [pinnedItems, setPinnedItems] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [counts, setCounts] = useState(null)
  const [loading, setLoading] = useState(true)

  // 무한스크롤용
  const [infiniteItems, setInfiniteItems] = useState([])
  const [infinitePage, setInfinitePage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const observerRef = useRef(null)

  const PAGE_SIZE = 20

  const fetchFeed = useCallback(async (pageNum = 1, append = false) => {
    if (append) setLoadingMore(true)
    else setLoading(true)

    try {
      const params = { page: pageNum, page_size: PAGE_SIZE, sort }
      if (category) params.category = category
      if (sub) params.sub = sub
      if (q) params.q = q
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
    } catch (e) {
      console.error('Feed fetch error:', e)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [category, sub, sort, q, viewMode, counts])

  // 카테고리/서브/정렬/검색 변경 시 리셋
  useEffect(() => {
    setInfinitePage(1)
    setInfiniteItems([])
    setHasMore(true)
    fetchFeed(viewMode === 'card' ? 1 : page)
  }, [category, sub, sort, q, page, viewMode])

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

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="max-w-7xl mx-auto px-4 py-6"
    >
      <div className="flex gap-6">
        <LeftSidebar category={category} sub={sub} counts={counts} />

        <div className="flex-1 min-w-0">
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
                  className="p-1.5 transition-colors"
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
                  className="p-1.5 transition-colors"
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

          {/* 검색 중 표시 */}
          {q && (
            <div className="mb-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
              &quot;{q}&quot; 검색 결과
            </div>
          )}

          {/* 콘텐츠 영역 */}
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 rounded-xl animate-pulse"
                  style={{ background: 'var(--bg-secondary)' }} />
              ))}
            </div>
          ) : viewMode === 'card' ? (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                {infiniteItems.map((item) => (
                  <FeedCard key={item.slug} item={item} />
                ))}
              </div>
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
                  {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => {
                    // 페이지 번호 계산 (현재 페이지 중심)
                    let start = Math.max(1, page - 4)
                    let end = Math.min(totalPages, start + 9)
                    start = Math.max(1, end - 9)
                    const p = start + i
                    if (p > totalPages) return null
                    return (
                      <button
                        key={p}
                        onClick={() => goToPage(p)}
                        className="w-8 h-8 text-xs rounded-lg border transition-colors"
                        style={{
                          borderColor: p === page ? 'var(--text)' : 'var(--border)',
                          background: p === page ? 'var(--text)' : 'transparent',
                          color: p === page ? '#fff' : 'var(--text-secondary)',
                        }}
                      >
                        {p}
                      </button>
                    )
                  })}
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
  )
}
