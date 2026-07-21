import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Helmet } from 'react-helmet-async'
import { ChevronRight } from 'lucide-react'

import ExploreNav from '../components/explore/ExploreNav'
import { CATEGORY_TREE } from '../data/categories'

// 사람용 사이트맵 — 전 카테고리 → 서브카테고리를 계층적으로 한눈에
export default function SiteIndexPage() {
  return (
    <>
      <Helmet>
        <title>사이트맵 | HJ Tech Blog</title>
        <meta
          name="description"
          content="AI, Tool, ML, Cloud, Data Engineering 등 전체 카테고리와 서브카테고리를 한눈에 볼 수 있는 사이트맵입니다."
        />
        <meta property="og:title" content="사이트맵 | HJ Tech Blog" />
        <meta property="og:type" content="website" />
      </Helmet>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.25, ease: 'easeOut' }}
        className="max-w-7xl mx-auto px-4 py-6"
      >
        <ExploreNav />

        {/* 헤더 */}
        <div className="mt-6 mb-5">
          <h1 className="text-xl sm:text-2xl font-bold" style={{ color: 'var(--text)' }}>
            사이트맵
          </h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
            전체 카테고리와 서브카테고리를 한눈에 둘러보세요.
          </p>
        </div>

        {/* 카테고리 카드 그리드 */}
        <motion.div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
          initial="hidden"
          animate="visible"
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.05 } } }}
        >
          {CATEGORY_TREE.map((cat) => (
            <motion.section
              key={cat.key}
              variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
              className="rounded-2xl border p-5 flex flex-col"
              style={{ background: cat.color + '0F', borderColor: 'var(--border)' }}
            >
              {/* 카테고리 타이틀 (컬러) — 클릭 시 해당 카테고리 목록으로 */}
              <Link
                to={cat.path}
                className="group flex items-center gap-2 mb-1"
              >
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ background: cat.color }}
                />
                <h2 className="text-base font-semibold" style={{ color: cat.color }}>
                  {cat.label}
                </h2>
                <span className="text-xs ml-auto flex items-center gap-0.5" style={{ color: 'var(--text-secondary)' }}>
                  {cat.subs.length}
                  <ChevronRight size={13} className="transition-transform group-hover:translate-x-0.5" />
                </span>
              </Link>

              {cat.desc && (
                <p className="text-xs mb-3" style={{ color: 'var(--text-secondary)' }}>
                  {cat.desc}
                </p>
              )}

              {/* 서브카테고리 링크 */}
              <div className="flex flex-wrap gap-1.5">
                {cat.subs.map((sub) => (
                  <Link
                    key={sub.key}
                    to={`/posts/${cat.key}/${sub.key}`}
                    className="text-xs px-2.5 py-1 rounded-full border transition-colors hover:text-primary-600 hover:border-primary-400"
                    style={{
                      borderColor: 'var(--border)',
                      color: 'var(--text-secondary)',
                      background: 'var(--card-bg)',
                    }}
                  >
                    {sub.label}
                  </Link>
                ))}
              </div>
            </motion.section>
          ))}
        </motion.div>
      </motion.div>
    </>
  )
}
