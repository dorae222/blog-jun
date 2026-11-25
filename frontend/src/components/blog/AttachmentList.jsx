import { Download, File, FileArchive, FileCode, FileSpreadsheet, FileText } from 'lucide-react'
import { KIND_LABEL, formatBytes } from '../../utils/attachments'

const ICONS = {
  xlsx: FileSpreadsheet,
  csv: FileSpreadsheet,
  ipynb: FileCode,
  py: FileCode,
  pdf: FileText,
  zip: FileArchive,
}

/**
 * 글 첨부 파일(실습 파일) 목록. 본문 위 요약 카드, 본문 아래, 본문 속 첨부 링크가 모두 이 컴포넌트를 쓴다.
 * 파일이 없으면 아무것도 그리지 않는다.
 *   compact: 요약 카드 안처럼 테두리 상자 안에 들어갈 때(자체 테두리·제목 없음)
 */
export default function AttachmentList({ items, title = '실습 파일', compact = false, className = '' }) {
  if (!items?.length) return null

  const rows = (
    <ul className="m-0 list-none p-0">
      {items.map((a, i) => {
        const Icon = ICONS[a.kind] || File
        const meta = [KIND_LABEL[a.kind] || (a.kind || '').toUpperCase(), formatBytes(a.size_bytes)].filter(Boolean).join(' · ')
        return (
          <li
            key={a.id ?? a.url}
            className={`flex items-center gap-3 ${compact ? 'py-2' : 'px-4 py-3'} ${i > 0 ? 'border-t' : ''}`}
            style={{ borderColor: 'var(--border)' }}
          >
            <Icon size={20} className="shrink-0" style={{ color: 'var(--text-secondary)' }} aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="m-0 text-sm font-medium break-all" style={{ color: 'var(--text)' }}>{a.filename}</p>
              {(meta || a.description) && (
                <p className="m-0 mt-0.5 text-xs break-words" style={{ color: 'var(--text-secondary)' }}>
                  {meta}{meta && a.description ? ' · ' : ''}{a.description}
                </p>
              )}
            </div>
            {/* 같은 탭에서 바로 내려받는다(새 탭을 열지 않는다) */}
            <a
              href={a.url}
              download={a.filename}
              className="tap-target shrink-0 inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium no-underline hover:bg-black/5"
              style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              aria-label={`${a.filename} 내려받기`}
            >
              <Download size={15} aria-hidden="true" />
              <span className="hidden sm:inline">내려받기</span>
            </a>
          </li>
        )
      })}
    </ul>
  )

  if (compact) return <div className={className}>{rows}</div>

  return (
    <section className={`not-prose my-6 ${className}`} aria-label={title || '첨부 파일'}>
      {title && (
        <p className="m-0 mb-2 text-sm font-semibold" style={{ color: 'var(--text)' }}>{title}</p>
      )}
      <div className="rounded-xl border" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
        {rows}
      </div>
    </section>
  )
}
