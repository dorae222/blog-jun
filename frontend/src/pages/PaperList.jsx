import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileText } from 'lucide-react'
import { getPosts } from '../api/posts'

export default function PaperList() {
  const [papers, setPapers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getPosts({ post_type: 'paper_review', status: 'published', page_size: 100 })
      .then((r) => setPapers(r.data.results || r.data || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-5xl mx-auto px-4 py-12"
    >
      <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text)' }}>
        Paper Reviews
      </h1>
      <p className="text-sm mb-8" style={{ color: 'var(--text-secondary)' }}>
        논문 리뷰 모음
      </p>

      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-24 rounded-xl animate-pulse"
              style={{ background: 'var(--bg-secondary)' }}
            />
          ))}
        </div>
      ) : papers.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24">
          <FileText size={48} style={{ color: 'var(--text-secondary)', opacity: 0.3 }} />
          <p className="text-lg mt-4" style={{ color: 'var(--text-secondary)' }}>
            아직 논문 리뷰가 없습니다.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {papers.map((paper) => (
            <Link
              key={paper.id}
              to={`/post/${paper.slug}`}
              className="block rounded-xl border p-5 hover:shadow-md transition-all"
              style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
            >
              <div className="flex items-start gap-4">
                <div className="shrink-0 mt-1">
                  <FileText size={20} className="text-primary-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-base mb-1" style={{ color: 'var(--text)' }}>
                    {paper.title}
                  </h3>
                  {paper.summary && (
                    <p className="text-sm line-clamp-2 mb-2" style={{ color: 'var(--text-secondary)' }}>
                      {paper.summary}
                    </p>
                  )}
                  <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--text-secondary)' }}>
                    {paper.category && (
                      <span
                        className="px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: paper.category.color + '20', color: paper.category.color }}
                      >
                        {paper.category.name}
                      </span>
                    )}
                    <span>
                      {paper.published_at
                        ? new Date(paper.published_at).toLocaleDateString('ko-KR')
                        : new Date(paper.created_at).toLocaleDateString('ko-KR')}
                    </span>
                    <span>{paper.reading_time} min</span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </motion.div>
  )
}
