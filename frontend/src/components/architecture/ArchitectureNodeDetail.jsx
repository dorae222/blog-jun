import { useState, useRef, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  X, ExternalLink, FileX, Calendar, Building2,
  ArrowRight, ArrowLeft, Image as ImageIcon,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { CATEGORY_COLORS } from '../../data/architectureConstants'
import MarkdownRenderer from '../blog/MarkdownRenderer'
import { escapeAngleBracketsOutsideMath } from '../../utils/mathText'

export default function ArchitectureNodeDetail({
  node,
  edges,
  onClose,
  onNodeFocus,
  layout = 'bottom', // 'bottom' | 'side'
  hideRelations = false,
}) {
  const navigate = useNavigate()

  // 하단 시트는 화면의 절반만 차지해서 아래에 내용이 더 있는지 보이지 않는다.
  // 그래서 (a) 위에 드래그 핸들을 두어 시트임을 알리고
  //        (b) 스크롤 영역 아래에 페이드를 깔아 더 있다는 것을 표시한다.
  // 끝까지 내리면 페이드를 지운다. 안 지우면 다 봤는데도 더 있는 것처럼 보인다.
  //
  // **훅은 조건부 반환보다 위에 있어야 한다.** 아래 `if (!node) return null` 뒤에
  // 두었더니 node 가 null 인 판과 아닌 판의 훅 개수가 달라져 eslint 가 막았다.
  // 지금은 두 호출자가 `selectedNode &&` 로 감싸서 터지지 않았을 뿐이다.
  const scrollRef = useRef(null)
  const [hasMore, setHasMore] = useState(false)

  const syncScrollHint = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    // 1px 여유를 둔다. 배율이나 소수 픽셀 때문에 정확히 0이 안 되는 경우가 있다
    setHasMore(el.scrollHeight - el.scrollTop - el.clientHeight > 1)
  }, [])

  useEffect(() => {
    syncScrollHint()
    const el = scrollRef.current
    if (!el || typeof ResizeObserver === 'undefined') return
    // 표지를 펴거나 수식이 늦게 조판되면 높이가 바뀐다. 그때도 다시 잰다
    const ro = new ResizeObserver(syncScrollHint)
    ro.observe(el)
    return () => ro.disconnect()
  }, [syncScrollHint, node?.slug])

  if (!node) return null

  const color = CATEGORY_COLORS[node.architecture_category] || '#6B7280'

  // 부모/자식 - hideRelations 시 빈 배열 (좌측 패널에서 대신 표시)
  const parents = hideRelations ? [] : edges
    .filter(e => e.to_slug === node.slug)
    .map(e => ({ slug: e.from_slug, name: e.from_name, type: e.relation_type }))

  const children = hideRelations ? [] : edges
    .filter(e => e.from_slug === node.slug)
    .map(e => ({ slug: e.to_slug, name: e.to_name, type: e.relation_type }))

  const releaseYear = node.release_date?.slice(0, 4)

  const specs = [
    { label: 'Parameters', value: node.param_scale },
    { label: 'Context', value: node.context_length },
    { label: 'Decoder', value: node.decoder_type?.replace(/_/g, ' ') },
    { label: 'Branch', value: node.branch_type },
  ].filter(s => s.value)

  const isSide = layout === 'side'

  const motionProps = isSide
    ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } }
    : { initial: { y: '100%', opacity: 0 }, animate: { y: 0, opacity: 1 }, exit: { y: '100%', opacity: 0 } }

  // 하단 시트도 세로 flex로 세운다. 그래야 본문만 늘어나고 링크 줄은 바닥에 남는다
  const containerClass = isSide
    ? 'h-full overflow-hidden flex flex-col'
    : 'absolute bottom-0 left-0 right-0 z-30 rounded-t-2xl shadow-2xl overflow-hidden flex flex-col'

  const containerStyle = isSide
    ? { background: 'var(--card-bg)', borderRight: '1px solid var(--border)' }
    : { background: 'var(--card-bg)', border: '1px solid var(--border)', borderBottom: 'none', height: '58vh', maxHeight: '58vh' }

  // minHeight 0이 없으면 flex 항목이 내용 높이만큼 버텨 하단 줄을 밀어낸다.
  // overscrollBehavior는 본문 끝에서 바퀴질이 문서로 넘어가 페이지째 밀리는 것을 막는다
  const innerScrollStyle = { overflowY: 'auto', overscrollBehavior: 'contain' }

  const linkBase =
    'inline-flex items-center justify-center gap-1.5 text-[13px] font-semibold px-3 py-2 rounded-lg w-full'

  return (
    <motion.div
      {...motionProps}
      transition={{ type: 'spring', damping: 25, stiffness: 300 }}
      className={containerClass}
      style={containerStyle}
    >
      {/* 하단 시트임을 알리는 손잡이. 옆 패널에는 필요 없다 */}
      {!isSide && (
        <div className="shrink-0 flex justify-center pt-2 pb-0.5">
          <div
            className="h-1 w-9 rounded-full"
            style={{ background: 'var(--border)' }}
            aria-hidden="true"
          />
        </div>
      )}

      {/* 헤더 */}
      <div className={`flex items-start justify-between px-4 ${isSide ? 'pt-3' : 'pt-1'} pb-2 shrink-0`}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {/* 계열은 굵은 색 줄이 아니라 제목 옆 점으로 알린다.
                카드 위 색 줄은 시트가 잘려 보일 때 그 줄만 남아 어색하다 */}
            <span
              className="h-2 w-2 rounded-full shrink-0"
              style={{ background: color }}
              aria-hidden="true"
            />
            <h3 className={`${isSide ? 'text-[15px]' : 'text-base'} font-bold truncate`} style={{ color: 'var(--text)' }}>
              {node.name}
            </h3>
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full shrink-0"
              style={{ backgroundColor: color + '20', color }}
            >
              {(node.architecture_category || '').toUpperCase()}
            </span>
            {node.is_open_source && (
              <span
                className="text-xs px-2 py-0.5 rounded-full"
                style={{ backgroundColor: '#10B98120', color: '#10B981' }}
              >
                Open Source
              </span>
            )}
          </div>
          <div
            className="flex items-center gap-3 mt-1 text-xs"
            style={{ color: 'var(--text-secondary)' }}
          >
            {node.organization && (
              <span className="flex items-center gap-1">
                <Building2 size={13} /> {node.organization}
              </span>
            )}
            {releaseYear && (
              <span className="flex items-center gap-1">
                <Calendar size={13} /> {releaseYear}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-gray-100/10 transition-colors shrink-0 ml-2"
          style={{ color: 'var(--text-secondary)' }}
          aria-label="닫기"
        >
          <X size={18} />
        </button>
      </div>

      <div className="relative overflow-hidden" style={{ flex: 1, minHeight: 0 }}>
      <div ref={scrollRef} onScroll={syncScrollHint} className="absolute inset-0 px-4 pb-4" style={innerScrollStyle}>
        {/* 표지 썸네일.
            좁은 화면(하단 시트)에서는 기본으로 접는다. 세로가 가장 비싼 자원인데
            표지는 1792x1120 가로형이라 시트의 큰 몫을 먹고, 정작 먼저 읽어야 할
            설명이 스크롤 밖으로 밀린다. 보고 싶으면 눌러서 편다 */}
        {node.figure_url && (
          isSide ? (
            <div
              className="rounded-xl overflow-hidden mb-3 flex items-center justify-center"
              style={{ background: 'var(--bg)', maxHeight: '180px' }}
            >
              <img
                src={node.figure_url}
                alt={node.name}
                className="max-w-full max-h-[180px] object-contain p-2"
                loading="lazy"
              />
            </div>
          ) : (
            <details className="mb-3">
              <summary
                className="cursor-pointer text-xs px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5"
                style={{ background: 'var(--bg)', color: 'var(--text-secondary)' }}
              >
                <ImageIcon size={13} /> 표지 보기
              </summary>
              <div
                className="rounded-xl overflow-hidden mt-2 flex items-center justify-center"
                style={{ background: 'var(--bg)', maxHeight: '160px' }}
              >
                <img
                  src={node.figure_url}
                  alt={node.name}
                  className="max-w-full max-h-[160px] object-contain p-2"
                  loading="lazy"
                />
              </div>
            </details>
          )
        )}

        {/* Specs 그리드 */}
        {specs.length > 0 && (
          <div className={`grid ${isSide ? 'grid-cols-2' : 'grid-cols-2 sm:grid-cols-4'} gap-2 mb-3`}>
            {specs.map(s => (
              <div
                key={s.label}
                className="rounded-lg px-3 py-2 text-center"
                style={{ background: 'var(--bg)' }}
              >
                <div className="text-xs mb-0.5" style={{ color: 'var(--text-secondary)' }}>
                  {s.label}
                </div>
                <div className="text-[13px] font-semibold truncate" style={{ color: 'var(--text)' }}>
                  {s.value}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Key Detail (마크다운 + 수식 지원).
            긴 수식은 패널 폭을 넘으므로 본문 칸 안에서만 가로로 밀리게 막아 둔다.

            자손 전체에 font-size를 상속시키지 않는다. index.css가 같은 이유로
            `.prose .katex`의 font-size:inherit를 걷어냈다 - KaTeX는 첨자·분수 크기를
            em으로 계산하므로 자손까지 크기를 고정하면 위첨자가 본문만큼 부풀어 오른다.
            바깥 `.prose` 한 겹만 눌러 두면 충분하다. */}
        {node.key_detail && (
          <div
            className="text-[13px] leading-relaxed mb-3 break-words overflow-x-auto [&_p]:m-0 [&_.katex]:text-[0.85em] [&_.prose]:text-[13px] [&_.prose]:leading-relaxed [&_.prose]:max-w-none"
            style={{ color: 'var(--text-secondary)' }}
          >
            <MarkdownRenderer content={escapeAngleBracketsOutsideMath(node.key_detail)} />
          </div>
        )}

        {/* 관계 (부모/자식) */}
        {(parents.length > 0 || children.length > 0) && (
          <div className="mb-3 space-y-2">
            {parents.length > 0 && (
              <div>
                <div
                  className="text-xs font-semibold uppercase tracking-wider mb-1.5 flex items-center gap-1"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  <ArrowLeft size={12} /> Parent Models
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {parents.map((p, i) => (
                    <button
                      key={`${p.slug}-${i}`}
                      onClick={() => onNodeFocus?.(p.slug)}
                      className="text-xs px-2.5 py-1 rounded-lg hover:opacity-80 transition-opacity flex items-center gap-1"
                      style={{ background: 'var(--bg)', color: 'var(--text)' }}
                    >
                      {p.name}
                      <span style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>
                        ({p.type?.replace(/_/g, ' ')})
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            {children.length > 0 && (
              <div>
                <div
                  className="text-xs font-semibold uppercase tracking-wider mb-1.5 flex items-center gap-1"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  <ArrowRight size={12} /> Derived Models
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {children.map((c, i) => (
                    <button
                      key={`${c.slug}-${i}`}
                      onClick={() => onNodeFocus?.(c.slug)}
                      className="text-xs px-2.5 py-1 rounded-lg hover:opacity-80 transition-opacity flex items-center gap-1"
                      style={{ background: 'var(--bg)', color: 'var(--text)' }}
                    >
                      {c.name}
                      <span style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>
                        ({c.type?.replace(/_/g, ' ')})
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

      </div>

      {/* 아래에 내용이 더 있다는 표시. 끝까지 내리면 사라진다.
          pointer-events-none 이라 이 위로도 스크롤이 그대로 먹는다 */}
      {hasMore && (
        <div
          className="pointer-events-none absolute bottom-0 left-0 right-0 h-8"
          style={{ background: 'linear-gradient(to top, var(--card-bg), transparent)' }}
        />
      )}
      </div>

      {/* 링크는 그래프 하단 가운데(`NodeLinkBar`)에만 둔다.
          여기 한 벌 더 두었더니 같은 버튼이 화면에 둘이 되어 어느 쪽을 눌러야 할지
          알 수 없었다. 다만 좁은 화면에서는 그래프가 카드 목록으로 바뀌어
          가운데 바가 없으므로 그때만 이 자리에 그린다 */}
      {!isSide && (
        <div
          className="shrink-0 grid grid-cols-2 gap-2 px-4 py-3"
          style={{ borderTop: '1px solid var(--border)', background: 'var(--card-bg)' }}
        >
          {node.paper_url ? (
            <a
              href={node.paper_url}
              target="_blank"
              rel="noopener noreferrer"
              className={`${linkBase} transition-opacity hover:opacity-75`}
              style={{ border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
            >
              논문 원문 <ExternalLink size={14} />
            </a>
          ) : (
            <span
              className={`${linkBase} cursor-not-allowed select-none`}
              style={{ border: '1px dashed var(--border)', color: 'var(--text-secondary)', opacity: 0.7 }}
              aria-disabled="true"
            >
              <FileX size={14} /> 논문 없음
            </span>
          )}
          {node.related_post_slug ? (
            <button
              onClick={() => navigate(`/post/${node.related_post_slug}`)}
              className={`${linkBase} bg-primary-600 text-white transition-colors hover:bg-primary-700`}
            >
              컨텐츠 보러가기 <ArrowRight size={14} />
            </button>
          ) : (
            <span
              className={`${linkBase} cursor-not-allowed select-none`}
              style={{ border: '1px dashed var(--border)', color: 'var(--text-secondary)', opacity: 0.7 }}
              aria-disabled="true"
            >
              <FileX size={14} /> 컨텐츠 없음
            </span>
          )}
        </div>
      )}
    </motion.div>
  )
}
