import { useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, AlertTriangle, XCircle, Wand2 } from 'lucide-react'
import useFocusTrap from '../../hooks/useFocusTrap'
import { SLUG_RE, slugify } from '../../utils/noteText'
import TagPicker from './TagPicker'

/** 본문 첫 문단(제목·이미지·코드·표 제외)을 요약 후보로 뽑는다. */
export function firstParagraph(md, max = 200) {
  const blocks = String(md || '').replace(/```[\s\S]*?```/g, '').split(/\n\s*\n/)
  for (const b of blocks) {
    const t = b.trim()
    if (!t || /^(#|!\[|\||<|>|---|\$\$)/.test(t)) continue
    const plain = t
      .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
      .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
      .replace(/[*_`~]/g, '')
      .replace(/\s+/g, ' ')
      .trim()
    if (plain.length >= 10) return plain.length > max ? `${plain.slice(0, max - 1)}…` : plain
  }
  return ''
}

/**
 * 발행 전 점검. 필수(제목·본문·카테고리·slug 형식)가 하나라도 빠지면 발행 버튼을 막고,
 * 권장(요약·표지·본문 길이)은 경고만 한다. 요약과 slug는 여기서 바로 고칠 수 있다.
 */
export default function PublishChecklist({
  open, onClose, onConfirm, form, onChange, categories, allTags, onTagCreated, coverUrl, isNew, isPublished, busy,
}) {
  const boxRef = useRef(null)
  const firstRef = useRef(null)
  useFocusTrap(boxRef, open, onClose)
  useEffect(() => { if (open) setTimeout(() => firstRef.current?.focus(), 30) }, [open])

  const catName = (() => {
    for (const c of categories || []) {
      if (String(c.id) === String(form.category)) return c.name
      const k = c.children?.find((x) => String(x.id) === String(form.category))
      if (k) return `${c.name} › ${k.name}`
    }
    return ''
  })()

  const len = form.content.trim().length
  const slugOk = SLUG_RE.test(form.slug || '')
  const items = [
    { key: 'title', label: '제목', level: form.title.trim() ? 'ok' : 'error', hint: form.title.trim() || '제목이 비어 있어요' },
    { key: 'content', label: '본문', level: len === 0 ? 'error' : len < 300 ? 'warn' : 'ok', hint: len === 0 ? '본문이 비어 있어요' : `${len.toLocaleString()}자${len < 300 ? ' · 짧은 편이에요' : ''}` },
    { key: 'category', label: '카테고리', level: form.category ? 'ok' : 'error', hint: catName || '아래에서 소분류를 골라 주세요' },
    { key: 'slug', label: '주소(slug)', level: slugOk ? 'ok' : 'error', hint: slugOk ? `/post/${form.slug}` : '영문 소문자·숫자·하이픈만 쓸 수 있어요' },
    { key: 'summary', label: '요약', level: form.summary.trim() ? 'ok' : 'warn', hint: form.summary.trim() ? `${form.summary.trim().length}자` : '목록·검색·공유 미리보기에 쓰여요' },
    { key: 'cover', label: '표지', level: coverUrl ? 'ok' : 'warn', hint: coverUrl ? '있음' : (isNew ? '한 번 저장한 뒤 상단에서 올릴 수 있어요' : '없음 · 상단 "표지 올리기"') },
  ]
  const blocked = items.some((i) => i.level === 'error')
  const Icon = { ok: CheckCircle2, warn: AlertTriangle, error: XCircle }
  const color = { ok: '#10b981', warn: '#f59e0b', error: '#ef4444' }

  return (
    <AnimatePresence>
      {open && (
        <motion.div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <div className="absolute inset-0 bg-black/40" onClick={onClose} />
          <motion.div
            ref={boxRef} role="dialog" aria-modal="true" aria-labelledby="publish-check-title"
            className="relative w-full sm:max-w-lg max-h-[90dvh] overflow-y-auto rounded-t-2xl sm:rounded-2xl border shadow-2xl p-5"
            style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
            initial={{ y: 20 }} animate={{ y: 0 }} exit={{ y: 20 }} transition={{ duration: 0.15 }}
          >
            <h2 id="publish-check-title" className="text-base font-semibold mb-1" style={{ color: 'var(--text)' }}>
              {isPublished ? '변경 내용 반영 전 점검' : '발행 전 점검'}
            </h2>
            <p className="text-xs mb-4" style={{ color: 'var(--text-secondary)' }}>
              빨간 항목을 채워야 {isPublished ? '반영' : '발행'}할 수 있어요. 노란 항목은 권장 사항이에요.
            </p>

            <ul className="space-y-2 mb-4">
              {items.map((it) => {
                const I = Icon[it.level]
                return (
                  <li key={it.key} className="flex items-start gap-2 text-sm">
                    <I size={16} className="mt-0.5 shrink-0" style={{ color: color[it.level] }} aria-hidden />
                    <span className="w-20 shrink-0 font-medium" style={{ color: 'var(--text)' }}>{it.label}</span>
                    <span className="min-w-0 break-all" style={{ color: 'var(--text-secondary)' }}>{it.hint}</span>
                  </li>
                )
              })}
            </ul>

            {!form.category && (
              <>
                <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }} htmlFor="pc-category">카테고리</label>
                <select id="pc-category" value={form.category} onChange={(e) => onChange({ category: e.target.value })}
                  className="w-full mb-3 text-sm px-3 py-2 rounded-lg border"
                  style={{ borderColor: '#ef4444', background: 'var(--bg)', color: 'var(--text)' }}>
                  <option value="">소분류 고르기</option>
                  {(categories || []).flatMap((c) => (c.children?.length
                    ? [<optgroup key={c.id} label={c.name}>{c.children.map((k) => <option key={k.id} value={k.id}>{k.name}</option>)}</optgroup>]
                    : [<option key={c.id} value={c.id}>{c.name}</option>]))}
                </select>
              </>
            )}

            <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }} htmlFor="pc-slug">주소(slug)</label>
            <div className="flex gap-2 mb-1">
              <input id="pc-slug" ref={firstRef} value={form.slug}
                onChange={(e) => onChange({ slug: e.target.value.trim() }, { slugTouched: true })}
                className="flex-1 min-w-0 text-sm px-3 py-2 rounded-lg border font-mono"
                style={{ borderColor: slugOk ? 'var(--border)' : '#ef4444', background: 'var(--bg)', color: 'var(--text)' }} />
              <button type="button" onClick={() => onChange({ slug: slugify(form.slug) || slugify(form.title) }, { slugTouched: true })}
                className="text-xs px-2 rounded-lg border" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                정리
              </button>
            </div>
            {isPublished && (
              <p className="text-[11px] mb-3" style={{ color: '#b45309' }}>발행된 글의 주소를 바꾸면 기존 링크가 깨져요.</p>
            )}

            <span className="block text-xs font-medium mt-3 mb-1" style={{ color: 'var(--text-secondary)' }}>태그 (권장)</span>
            <TagPicker value={form.tags} onChange={(tags) => onChange({ tags })} allTags={allTags} onTagCreated={onTagCreated} />

            <div className="flex items-center justify-between mt-3 mb-1">
              <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }} htmlFor="pc-summary">요약</label>
              <button type="button"
                onClick={() => onChange({ summary: firstParagraph(form.content) })}
                className="inline-flex items-center gap-1 text-[11px] text-primary-600 hover:underline">
                <Wand2 size={11} /> 첫 문단으로 채우기
              </button>
            </div>
            <textarea id="pc-summary" rows={3} maxLength={500} value={form.summary}
              onChange={(e) => onChange({ summary: e.target.value })}
              placeholder="한두 문장으로 이 글을 소개해 주세요"
              className="w-full text-sm px-3 py-2 rounded-lg border resize-none"
              style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }} />

            <div className="flex justify-end gap-2 mt-4">
              <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                계속 쓰기
              </button>
              <button onClick={onConfirm} disabled={blocked || busy}
                className="px-4 py-2 text-sm font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed">
                {busy ? '저장 중…' : isPublished ? '반영하기' : '발행하기'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
