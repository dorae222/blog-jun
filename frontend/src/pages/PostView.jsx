import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, List, X, ChevronRight } from 'lucide-react'
import { getCategoryIcon } from '../utils/categoryIcons'
import MarkdownRenderer from '../components/blog/MarkdownRenderer'
import PaperSummaryBox from '../components/blog/PaperSummaryBox'
import PDFViewer from '../components/blog/PDFViewer'
import ReadingProgress from '../components/blog/ReadingProgress'
import TableOfContents from '../components/blog/TableOfContents'
import TagChip from '../components/common/TagChip'
import ArchitectureLineageCard from '../components/blog/ArchitectureLineageCard'
import PostLinksSection from '../components/blog/PostLinksSection'
import { getPost } from '../api/posts'
import { CATEGORY_ROUTE_MAP } from '../data/categories'

export default function PostView() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tocOpen, setTocOpen] = useState(false)

  // TOC 드로어 열릴 때 배경 스크롤 잠금
  useEffect(() => {
    document.body.style.overflow = tocOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [tocOpen])

  useEffect(() => {
    setLoading(true)
    getPost(slug)
      .then((r) => setPost(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="space-y-4">
          <div className="h-8 rounded w-3/4 skeleton" />
          <div className="h-4 rounded w-1/2 skeleton" />
          <div className="h-96 rounded skeleton" />
        </div>
      </div>
    )
  }

  if (!post) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <h2 className="text-2xl font-bold mb-4">Post not found</h2>
        <Link to="/" className="text-primary-600 hover:underline">Back to Home</Link>
      </div>
    )
  }

  const catRouteKey = CATEGORY_ROUTE_MAP[post.category?.parent?.slug] || CATEGORY_ROUTE_MAP[post.category?.slug] || ''

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      <ReadingProgress />

      <div className="max-w-7xl mx-auto px-3 sm:px-4 py-6 sm:py-12 flex gap-8">
        <article className="flex-1 max-w-4xl">
          {/* 모바일 목차 버튼 (xl 미만에서만 표시) */}
          <div className="xl:hidden mb-4">
            <button
              onClick={() => setTocOpen(true)}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
            >
              <List size={16} /> 목차
            </button>
          </div>

          {/* Breadcrumb */}
          <nav className="flex items-center gap-1 text-xs mb-4 flex-wrap" style={{ color: 'var(--text-secondary)' }}>
            <Link to="/" className="hover:text-primary-600 transition-colors">Home</Link>
            <ChevronRight size={12} />
            <Link to="/posts" className="hover:text-primary-600 transition-colors">Posts</Link>
            {post.category && (
              <>
                <ChevronRight size={12} />
                <Link to={`/posts/${catRouteKey}`} className="hover:text-primary-600 transition-colors">
                  {post.category.name}
                </Link>
              </>
            )}
            <ChevronRight size={12} />
            <span className="truncate max-w-[200px]" style={{ color: 'var(--text)' }}>{post.title}</span>
          </nav>

          {/* Header */}
          <header className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              {post.category && (
                <Link
                  to={`/posts/${catRouteKey}`}
                  className="text-sm font-medium px-3 py-1 rounded-full"
                  style={{
                    backgroundColor: post.category.color + '12',
                    color: post.category.color,
                  }}
                >
                  <span className="inline-flex items-center gap-1">
                    {getCategoryIcon(post.category.slug, 14)}
                    {post.category.name}
                  </span>
                </Link>
              )}
              {post.series && (
                <Link
                  to={`/posts`}
                  className="text-sm font-medium text-primary-600 hover:underline"
                >
                  <BookOpen size={14} className="inline mr-1" /> {post.series.name}
                </Link>
              )}
            </div>

            <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-4" style={{ color: 'var(--text)' }}>
              {post.title}
            </h1>

            <div className="flex flex-wrap items-center gap-2 md:gap-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
              <span>
                {post.published_at
                  ? new Date(post.published_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
                  : new Date(post.created_at).toLocaleDateString('ko-KR')}
              </span>
              <span>{post.reading_time} min read</span>
              <span>{post.view_count} views</span>
            </div>
          </header>

          {/* Paper Summary / Architecture Info */}
          {(post.post_type === 'paper_review' || post.architecture_entries?.length > 0) && (
            <PaperSummaryBox post={post} />
          )}

          {/* Content */}
          <MarkdownRenderer content={post.content} postLinks={post.outgoing_links || []} />

          {/* PDF 첨부 뷰어 */}
          {post.pdf_file && (
            <PDFViewer
              url={post.pdf_file}
              title={post.title + ' — 첨부 PDF'}
            />
          )}

          {/* Tags */}
          {post.tags?.length > 0 && (
            <div className="mt-8 pt-8 border-t" style={{ borderColor: 'var(--border)' }}>
              <div className="flex flex-wrap gap-2">
                {post.tags.map((tag) => (
                  <TagChip key={tag.id} tag={tag} size="md" />
                ))}
              </div>
            </div>
          )}

          {/* Related: Architecture Lineage + Post Links */}
          {(post.architecture_entries?.length > 0 || post.outgoing_links?.length > 0 || post.incoming_links?.length > 0) && (
            <div className="mt-8 pt-8 border-t" style={{ borderColor: 'var(--border)' }}>
              <ArchitectureLineageCard entries={post.architecture_entries} />
              <PostLinksSection
                outgoingLinks={post.outgoing_links}
                incomingLinks={post.incoming_links}
              />
            </div>
          )}

          {/* Series Navigation */}
          {post.adjacent_posts && (post.adjacent_posts.prev || post.adjacent_posts.next) && (
            <nav className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
              {post.adjacent_posts.prev && (
                <Link
                  to={`/post/${post.adjacent_posts.prev.slug}`}
                  className="p-4 rounded-xl border hover:shadow-md transition-all text-left"
                  style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                >
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>← Previous</span>
                  <p className="text-sm font-medium mt-1" style={{ color: 'var(--text)' }}>{post.adjacent_posts.prev.title}</p>
                </Link>
              )}
              {post.adjacent_posts.next && (
                <Link
                  to={`/post/${post.adjacent_posts.next.slug}`}
                  className="p-4 rounded-xl border hover:shadow-md transition-all text-right md:col-start-2"
                  style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                >
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Next →</span>
                  <p className="text-sm font-medium mt-1" style={{ color: 'var(--text)' }}>{post.adjacent_posts.next.title}</p>
                </Link>
              )}
            </nav>
          )}

          {/* Related Posts (비시리즈 포스트용) */}
          {post.related_posts?.length > 0 && (
            <div className="mt-8">
              <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
                Related Posts
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {post.related_posts.map(rp => (
                  <Link
                    key={rp.id}
                    to={`/post/${rp.slug}`}
                    className="p-4 rounded-xl border hover:shadow-md transition-all"
                    style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                  >
                    <p className="text-sm font-medium line-clamp-2" style={{ color: 'var(--text)' }}>
                      {rp.title}
                    </p>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </article>

        {/* Sidebar TOC (데스크탑) */}
        <aside className="hidden xl:block w-64 shrink-0">
          <TableOfContents content={post.content} />
        </aside>
      </div>

      {/* 모바일 TOC 슬라이드 드로어 */}
      <AnimatePresence>
        {tocOpen && (
          <>
            {/* 오버레이 */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 z-40 xl:hidden"
              onClick={() => setTocOpen(false)}
            />
            {/* 드로어 패널 */}
            <motion.div
              initial={{ x: 256 }}
              animate={{ x: 0 }}
              exit={{ x: 256 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed top-0 right-0 h-full w-64 z-50 xl:hidden overflow-y-auto"
              style={{ background: 'var(--card-bg)', borderLeft: '1px solid var(--border)' }}
            >
              <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
                <span className="font-semibold text-sm" style={{ color: 'var(--text)' }}>목차</span>
                <button onClick={() => setTocOpen(false)} style={{ color: 'var(--text-secondary)' }}>
                  <X size={18} />
                </button>
              </div>
              <div className="px-4 py-3">
                <TableOfContents content={post.content} />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
