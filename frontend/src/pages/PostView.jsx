import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, List, X, ChevronRight } from 'lucide-react'
import { getCategoryIcon } from '../utils/categoryIcons'
import MarkdownRenderer from '../components/blog/MarkdownRenderer'
import useAuth from '../hooks/useAuth'
import PaperSummaryBox from '../components/blog/PaperSummaryBox'
import PDFViewer from '../components/blog/PDFViewer'
import TableOfContents from '../components/blog/TableOfContents'
import TagChip from '../components/common/TagChip'
import ArchitectureLineageCard from '../components/blog/ArchitectureLineageCard'
import PostLinksSection from '../components/blog/PostLinksSection'
import CommentSection from '../components/blog/CommentSection'
import RelatedSeries from '../components/blog/RelatedSeries'
import SummaryCard from '../components/blog/SummaryCard'
import AttachmentList from '../components/blog/AttachmentList'
import PostQuiz from '../components/blog/PostQuiz'
import { getPost } from '../api/posts'
import { CATEGORY_ROUTE_MAP } from '../data/categories'
import { ogImageUrl } from '../utils/ogImage'

// 본문 첫 H1이 포스트 제목과 동일하면 제거 - 페이지 헤더 제목과 중복(제목 2번) 방지.
// 히어로 이미지/캡션 등 H1 이전 라인은 유지하고, 첫 번째 H1만 검사한다.
// 본문 맨 앞의 H1 을 걷는다. 이 화면은 위에서 `post.title` 을 이미 제목으로 그리므로
// 본문 H1 은 언제나 **두 번째 제목**이 된다.
//
// 전에는 H1 글자가 제목과 **똑같을 때만** 걷었다. 그래서 둘이 갈라진 글에서 제목이
// 두 번 떴다. 876편 가운데 187편이 그 상태였다. 예를 들어 `glide` 는 제목이
// `GLIDE - CLIP Guidance 대 Classifier-Free Guidance` 인데 본문 H1 은
// `GLIDE: 텍스트 가이드 확산 이미지 생성` 이라 둘 다 화면에 떴다.
//
// 글자를 비교하지 않고 **자리**로 가른다. 첫 `##` 보다 앞에 오는 `#` 하나만 제목 자리다.
// 그 뒤의 `#` 은 본문이 쓰는 절이므로 건드리지 않는다.
function stripLeadingTitleHeading(content) {
  if (!content) return content
  const lines = content.split('\n')
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (/^##\s/.test(line)) break          // 절이 먼저 나왔다. 제목 자리가 아니다
    if (/^```/.test(line)) break            // 코드 펜스 안은 보지 않는다
    if (!/^#\s+\S/.test(line)) continue
    lines.splice(i, lines[i + 1] !== undefined && lines[i + 1].trim() === '' ? 2 : 1)
    break
  }
  return lines.join('\n')
}

export default function PostView() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tocOpen, setTocOpen] = useState(false)
  const { user, loading: authLoading } = useAuth()

  // TOC 드로어 열릴 때 배경 스크롤 잠금
  useEffect(() => {
    document.body.style.overflow = tocOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [tocOpen])

  useEffect(() => {
    setLoading(true)
    getPost(slug)
      .then((r) => setPost(r.data))
      .catch(() => setPost(null))
      .finally(() => setLoading(false))
    // 로그인 상태가 바뀌면 다시 받는다(비공개 초안은 로그인해야 보인다)
  }, [slug, user?.id])

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
        <h2 className="text-2xl font-bold mb-3">글을 찾을 수 없습니다</h2>
        {!authLoading && !user ? (
          <>
            <p className="mb-5 text-sm" style={{ color: 'var(--text-secondary)' }}>
              주소가 바뀌었거나, 아직 공개하지 않은 글일 수 있습니다. 비공개 글은 로그인해야 보입니다.
            </p>
            <Link to={`/login?next=${encodeURIComponent(`/post/${slug}`)}`}
              className="inline-block px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700">로그인하고 다시 열기</Link>
            <div className="mt-4"><Link to="/" className="text-sm text-primary-600 hover:underline">홈으로</Link></div>
          </>
        ) : (
          <Link to="/" className="text-primary-600 hover:underline">홈으로</Link>
        )}
      </div>
    )
  }

  const catRouteKey = CATEGORY_ROUTE_MAP[post.category?.parent?.slug] || CATEGORY_ROUTE_MAP[post.category?.slug] || ''
  // 제목 중복 제거된 본문 (렌더러 + TOC 공통 사용)
  const bodyContent = stripLeadingTitleHeading(post.content)

  const canonicalUrl = `https://blog.dorae222.com/post/${post.slug}`
  // 카드에 보이는 표지는 움직이는 SVG지만 링크 미리보기용 그림은 PNG로 준다.
  // 이유와 변환 규칙은 utils/ogImage.js 주석에 적어 뒀다.
  const ogImage = ogImageUrl(post.cover_image_url)
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: post.title,
    description: post.summary || post.title,
    datePublished: post.published_at || post.created_at,
    dateModified: post.updated_at || post.published_at || post.created_at,
    author: { '@type': 'Person', name: 'HyeongJun' },
    publisher: { '@type': 'Organization', name: 'HJ Tech Blog' },
    ...(ogImage ? { image: ogImage } : {}),
  }

  return (
    <>
    <Helmet>
      <title>{post.title} | HJ Tech Blog</title>
      <meta name="description" content={post.summary || post.title} />
      <meta property="og:title" content={post.title} />
      <meta property="og:description" content={post.summary || post.title} />
      <meta property="og:type" content="article" />
      <meta property="og:url" content={canonicalUrl} />
      {ogImage && <meta property="og:image" content={ogImage} />}
      <link rel="canonical" href={canonicalUrl} />
      <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
    </Helmet>
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >

      {/* overflow-x는 clip으로 - hidden이면 자식 TOC의 position:sticky가 동작하지 않는다 */}
      <div className="w-full max-w-7xl mx-auto px-3 sm:px-4 py-6 sm:py-12 flex gap-8" style={{ overflowX: 'clip' }}>
        <article className="w-full min-w-0 flex-1 max-w-4xl overflow-hidden">
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
          <nav className="min-w-0 flex items-center gap-1 text-xs mb-4 flex-wrap" style={{ color: 'var(--text-secondary)' }}>
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
            <span className="min-w-0 truncate max-w-[200px]" style={{ color: 'var(--text)' }}>{post.title}</span>
          </nav>

          {/* Header */}
          <header className="mb-8 min-w-0">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5 mb-4">
              {post.category && (
                <Link
                  to={`/posts/${catRouteKey}`}
                  className="shrink-0 whitespace-nowrap text-sm font-medium px-3 py-1 rounded-full"
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
                  to={`/series?s=${post.series.slug}`}
                  className="text-sm font-medium text-primary-600 hover:underline"
                >
                  <BookOpen size={14} className="inline mr-1" /> {post.series.name}
                </Link>
              )}
            </div>

            <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-4 break-words" style={{ color: 'var(--text)' }}>
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

          {/* 글 머리 요약 카드 - summary_card 가 있는 글에만 나온다 */}
          <SummaryCard card={post.summary_card} attachments={post.attachments || []} />

          {/* Content */}
          <MarkdownRenderer content={bodyContent} postLinks={post.outgoing_links || []} attachments={post.attachments || []} />

          {/* 실습 파일 · 확인 질문 - 데이터가 있는 글에만 나온다 */}
          <AttachmentList items={post.attachments} className="mt-10" />
          <PostQuiz quiz={post.quiz} />

          {/* PDF 첨부 뷰어 */}
          {post.pdf_file && (
            <PDFViewer
              url={post.pdf_file}
              title={post.title + ' - 첨부 PDF'}
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

          {/* 이어서 읽기 - 흩어져 있던 연결(시리즈·계보·관련 글)을 한 자리에 모은다.
              정확도가 높은 순으로 쌓는다: 사람이 묶은 시리즈 > 검증한 계보 > 링크·태그 */}
          {(post.adjacent_posts?.prev || post.adjacent_posts?.next ||
            post.architecture_entries?.length > 0 ||
            post.outgoing_links?.length > 0 || post.incoming_links?.length > 0) && (
            <section className="mt-10 pt-8 border-t" style={{ borderColor: 'var(--border)' }}>
              <h2 className="text-lg font-bold mb-4" style={{ color: 'var(--text)' }}>
                이어서 읽기
              </h2>

              {/* 1. 같은 시리즈의 앞뒤 편 */}
              {(post.adjacent_posts?.prev || post.adjacent_posts?.next) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
                  {['prev', 'next'].map((dir) => {
                    const item = post.adjacent_posts?.[dir]
                    if (!item) return <div key={dir} className="hidden md:block" />
                    return (
                      <Link
                        key={dir}
                        to={`/post/${item.slug}`}
                        className="group p-4 rounded-xl border transition-shadow hover:shadow-md"
                        style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                      >
                        <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                          {dir === 'prev' ? '이전 편' : '다음 편'}
                          {post.series?.name ? ` · ${post.series.name}` : ''}
                        </span>
                        <p className="text-sm font-semibold mt-1 line-clamp-2 group-hover:text-primary-600 transition-colors"
                          style={{ color: 'var(--text)' }}>
                          {item.title}
                        </p>
                      </Link>
                    )
                  })}
                </div>
              )}

              {/* 2. 검증한 아키텍처 계보 */}
              <ArchitectureLineageCard entries={post.architecture_entries} />

              {/* 3. 본문에서 오간 링크 */}
              <PostLinksSection
                outgoingLinks={post.outgoing_links}
                incomingLinks={post.incoming_links}
              />
            </section>
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

          {/* 관련 시리즈 - 한 편을 다 읽은 독자가 다음으로 갈 곳은 낱개 글보다 묶음이다 */}
          {/* 카테고리 대분류는 포스트 쪽에 없다. 시리즈에 딸려 오는 값을 쓰고,
              시리즈가 없는 글은 소분류 이름으로만 맞춘다. */}
          <RelatedSeries
            series={post.series}
            categoryName={post.category?.name}
            categoryGroup={post.series?.category_group}
          />

          {/* 댓글 */}
          <CommentSection postSlug={slug} />
        </article>

        {/* Sidebar TOC (데스크탑) */}
        <aside className="hidden xl:block w-64 shrink-0">
          <TableOfContents content={bodyContent} />
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
                <TableOfContents content={bodyContent} onNavigate={() => setTocOpen(false)} />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
    </>
  )
}
