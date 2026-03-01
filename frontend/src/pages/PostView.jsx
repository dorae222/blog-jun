import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BookOpen } from 'lucide-react'
import { getCategoryIcon } from '../utils/categoryIcons'
import MarkdownRenderer from '../components/blog/MarkdownRenderer'
import PDFViewer from '../components/blog/PDFViewer'
import ReadingProgress from '../components/blog/ReadingProgress'
import TableOfContents from '../components/blog/TableOfContents'
import TagChip from '../components/common/TagChip'
import { getPost } from '../api/posts'

export default function PostView() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getPost(slug)
      .then((r) => setPost(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 rounded w-3/4" style={{ background: 'var(--bg-secondary)' }} />
          <div className="h-4 rounded w-1/2" style={{ background: 'var(--bg-secondary)' }} />
          <div className="h-96 rounded" style={{ background: 'var(--bg-secondary)' }} />
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <ReadingProgress />

      <div className="max-w-7xl mx-auto px-4 py-12 flex gap-8">
        <article className="flex-1 max-w-4xl">
          {/* Header */}
          <header className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              {post.category && (
                <Link
                  to={`/category/${post.category.slug}`}
                  className="text-sm font-medium px-3 py-1 rounded-full"
                  style={{
                    backgroundColor: post.category.color + '20',
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
                  to={`/series/${post.series.slug}`}
                  className="text-sm font-medium text-primary-600 hover:underline"
                >
                  <BookOpen size={14} className="inline mr-1" /> {post.series.name}
                </Link>
              )}
            </div>

            <h1 className="text-4xl font-bold mb-4" style={{ color: 'var(--text)' }}>
              {post.title}
            </h1>

            <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
              <span>
                {post.published_at
                  ? new Date(post.published_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
                  : new Date(post.created_at).toLocaleDateString('ko-KR')}
              </span>
              <span>{post.reading_time} min read</span>
              <span>{post.view_count} views</span>
            </div>
          </header>

          {/* Content */}
          <MarkdownRenderer content={post.content} />

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

          {/* Series Navigation */}
          {post.adjacent_posts && (post.adjacent_posts.prev || post.adjacent_posts.next) && (
            <nav className="mt-8 grid grid-cols-2 gap-4">
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
                  className="p-4 rounded-xl border hover:shadow-md transition-all text-right col-start-2"
                  style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                >
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Next →</span>
                  <p className="text-sm font-medium mt-1" style={{ color: 'var(--text)' }}>{post.adjacent_posts.next.title}</p>
                </Link>
              )}
            </nav>
          )}
        </article>

        {/* Sidebar TOC */}
        <aside className="hidden xl:block w-64 shrink-0">
          <TableOfContents content={post.content} />
        </aside>
      </div>
    </motion.div>
  )
}
