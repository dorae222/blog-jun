import { Link } from 'react-router-dom'
import AttachmentList from './AttachmentList'
import InlineRich from '../common/InlineRich'

/**
 * 글 머리 요약 카드. summary_card 가 없는 글에서는 아무것도 그리지 않는다.
 * 제목 태그(h1~h3)는 쓰지 않는다 — 목차가 article 안의 제목 태그를 모아 만들기 때문이다.
 */
export default function SummaryCard({ card, attachments = [] }) {
  if (!card?.one_line) return null
  const learn = (card.learn || []).filter(Boolean)
  const prereq = (card.prereq || []).filter((p) => p?.slug)
  const label = 'm-0 mb-1.5 text-xs font-semibold tracking-wide'
  const labelStyle = { color: 'var(--text-secondary)' }

  return (
    <aside
      className="not-prose mb-8 rounded-xl border p-5 sm:p-6"
      style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
      aria-label="이 글 요약"
    >
      <p className={label} style={labelStyle}>한 줄 요약</p>
      <p className="m-0 text-lg sm:text-xl font-semibold leading-snug break-words" style={{ color: 'var(--text)' }}>
        <InlineRich text={card.one_line} />
      </p>

      {/* 읽는 시간은 보여 주지 않는다(글 머리에 이미 있고, 요약 카드에는 군더더기다). */}
      {card.level && (
        <p className="m-0 mt-3 text-sm" style={{ color: 'var(--text-secondary)' }}>
          <span>난이도 <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{card.level}</strong></span>
        </p>
      )}

      {learn.length > 0 && (
        <div className="mt-5 border-t pt-4" style={{ borderColor: 'var(--border)' }}>
          <p className={label} style={labelStyle}>이 글에서 다루는 것</p>
          <ol className="m-0 list-none p-0 space-y-1.5">
            {learn.map((item, i) => (
              <li key={i} className="flex gap-2.5 text-[0.95rem] leading-relaxed" style={{ color: 'var(--text)' }}>
                <span className="shrink-0 tabular-nums" style={{ color: 'var(--text-secondary)' }} aria-hidden="true">{i + 1}.</span>
                <span className="min-w-0 break-words"><InlineRich text={item} /></span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {prereq.length > 0 && (
        <div className="mt-4 border-t pt-4" style={{ borderColor: 'var(--border)' }}>
          <p className={label} style={labelStyle}>먼저 읽으면 좋은 글</p>
          <ul className="m-0 list-none p-0 flex flex-col gap-1">
            {prereq.map((p) => (
              <li key={p.slug}>
                <Link to={`/post/${p.slug}`} className="tap-target inline-flex items-center text-[0.95rem] text-primary-600 hover:underline break-words">
                  {p.title || p.slug}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {attachments.length > 0 && (
        <div className="mt-4 border-t pt-4" style={{ borderColor: 'var(--border)' }}>
          <p className={label} style={labelStyle}>실습 파일</p>
          <AttachmentList items={attachments} compact />
        </div>
      )}
    </aside>
  )
}
