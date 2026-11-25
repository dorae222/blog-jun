import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Copy, Plus, Trash2, Upload, X } from 'lucide-react'
import ConfirmDialog from '../common/ConfirmDialog'
import { deleteAttachment, getAttachments, updateAttachment, uploadAttachment } from '../../api/posts'
import { ATTACHMENT_ACCEPT, ATTACHMENT_KINDS, ATTACHMENT_MAX_BYTES, KIND_LABEL, formatBytes, kindFromName } from '../../utils/attachments'
import { LEVELS, MAX_PREREQ, cardPayload, parseSlugInput, quizPayload } from '../../utils/postExtras'

const inputCls = 'w-full rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary-500/40'
const inputStyle = { borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }
const labelCls = 'mb-1 block text-xs font-medium'
const labelStyle = { color: 'var(--text-secondary)' }
const btnCls = 'tap-target inline-flex items-center justify-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm hover:bg-black/5 disabled:opacity-50'
const btnStyle = { borderColor: 'var(--border)', color: 'var(--text)' }

function describe(err) {
  const d = err?.response?.data
  if (err?.response?.status === 413) return '파일이 너무 커요(20MB 이하).'
  if (!d) return err?.response ? `HTTP ${err.response.status}` : '네트워크 오류'
  if (d.detail) return String(d.detail)
  const first = Object.values(d)[0]
  return Array.isArray(first) ? first.join(' ') : String(first ?? '알 수 없는 오류')
}

function Section({ title, hint, children }) {
  return (
    <section className="border-t px-4 py-5 sm:px-6 first:border-t-0" style={{ borderColor: 'var(--border)' }}>
      <p className="m-0 text-sm font-semibold" style={{ color: 'var(--text)' }}>{title}</p>
      {hint && <p className="m-0 mt-0.5 mb-3 text-xs" style={{ color: 'var(--text-secondary)' }}>{hint}</p>}
      {children}
    </section>
  )
}

/** 요약 카드 폼: 한 줄 결론, 알게 되는 것 3가지, 난이도, 읽는 시간, 선수 지식 */
function CardForm({ card, onChange }) {
  const set = (patch) => onChange({ ...card, ...patch })
  const setLearn = (i, v) => set({ learn: card.learn.map((x, j) => (j === i ? v : x)) })
  const setPrereq = (i, patch) => set({ prereq: card.prereq.map((x, j) => (j === i ? { ...x, ...patch } : x)) })
  const state = cardPayload(card)

  return (
    <div className="space-y-3">
      <div>
        <label className={labelCls} style={labelStyle} htmlFor="sc-one">한 줄 결론</label>
        <textarea id="sc-one" rows={2} maxLength={200} value={card.one_line}
          onChange={(e) => set({ one_line: e.target.value })}
          placeholder="이 글을 한 문장으로 줄이면" className={inputCls} style={inputStyle} />
      </div>
      <fieldset className="m-0 border-0 p-0">
        <legend className={labelCls} style={labelStyle}>이 글로 알게 되는 것 (최대 3가지)</legend>
        <div className="space-y-2">
          {card.learn.map((v, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="w-4 shrink-0 text-xs tabular-nums" style={labelStyle} aria-hidden="true">{i + 1}.</span>
              <input value={v} maxLength={200} onChange={(e) => setLearn(i, e.target.value)}
                aria-label={`알게 되는 것 ${i + 1}`} className={inputCls} style={inputStyle} />
            </div>
          ))}
        </div>
      </fieldset>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={labelCls} style={labelStyle} htmlFor="sc-level">난이도</label>
          <select id="sc-level" value={card.level} onChange={(e) => set({ level: e.target.value })} className={inputCls} style={inputStyle}>
            <option value="">고르지 않음</option>
            {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <div>
          <label className={labelCls} style={labelStyle} htmlFor="sc-read">읽는 시간(분)</label>
          <input id="sc-read" type="number" inputMode="numeric" min="1" max="300" value={card.read_min}
            onChange={(e) => set({ read_min: e.target.value })} className={inputCls} style={inputStyle} />
        </div>
      </div>
      <fieldset className="m-0 border-0 p-0">
        <legend className={labelCls} style={labelStyle}>먼저 알면 좋은 글 (공개된 글의 slug 또는 주소)</legend>
        <div className="space-y-2">
          {card.prereq.map((p, i) => (
            <div key={i} className="flex flex-wrap items-center gap-2 sm:flex-nowrap">
              <input value={p.slug} onChange={(e) => setPrereq(i, { slug: e.target.value })}
                onBlur={(e) => setPrereq(i, { slug: parseSlugInput(e.target.value) })}
                placeholder="slug 또는 /post/… 주소" aria-label={`선수 글 ${i + 1} slug`}
                className={`${inputCls} sm:flex-1`} style={inputStyle} />
              <input value={p.title} maxLength={300} onChange={(e) => setPrereq(i, { title: e.target.value })}
                placeholder="표시 이름(비우면 글 제목)" aria-label={`선수 글 ${i + 1} 표시 이름`}
                className={`${inputCls} flex-1`} style={inputStyle} />
              <button type="button" onClick={() => set({ prereq: card.prereq.filter((_, j) => j !== i) })}
                className={`${btnCls} shrink-0`} style={btnStyle} aria-label={`선수 글 ${i + 1} 빼기`}>
                <Trash2 size={15} />
              </button>
            </div>
          ))}
          {card.prereq.length < MAX_PREREQ && (
            <button type="button" onClick={() => set({ prereq: [...card.prereq, { title: '', slug: '' }] })} className={btnCls} style={btnStyle}>
              <Plus size={15} /> 글 추가
            </button>
          )}
        </div>
      </fieldset>
      {state.state === 'incomplete' && (
        <p className="m-0 text-xs" style={{ color: '#b45309' }} role="status">아직 저장되지 않아요 · {state.reason}</p>
      )}
    </div>
  )
}

/** 확인 질문 폼: 질문 / 답 / 어디에 나오나 3쌍 */
function QuizForm({ quiz, onChange }) {
  const setRow = (i, patch) => onChange(quiz.map((r, j) => (j === i ? { ...r, ...patch } : r)))
  const state = quizPayload(quiz)
  return (
    <div className="space-y-4">
      {quiz.map((r, i) => (
        <fieldset key={i} className="m-0 space-y-2 rounded-lg border p-3" style={{ borderColor: 'var(--border)' }}>
          <legend className="px-1 text-xs font-medium" style={labelStyle}>질문 {i + 1}</legend>
          <input value={r.q} maxLength={300} onChange={(e) => setRow(i, { q: e.target.value })}
            placeholder="질문" aria-label={`질문 ${i + 1}`} className={inputCls} style={inputStyle} />
          <textarea rows={2} value={r.a} maxLength={1500} onChange={(e) => setRow(i, { a: e.target.value })}
            placeholder="답" aria-label={`질문 ${i + 1}의 답`} className={inputCls} style={inputStyle} />
          <input value={r.where} maxLength={200} onChange={(e) => setRow(i, { where: e.target.value })}
            placeholder="어디에 나오나 (소제목)" aria-label={`질문 ${i + 1}의 답이 나오는 소제목`} className={inputCls} style={inputStyle} />
        </fieldset>
      ))}
      {state.state === 'incomplete' && (
        <p className="m-0 text-xs" style={{ color: '#b45309' }} role="status">아직 저장되지 않아요 · {state.reason}</p>
      )}
    </div>
  )
}

/** 첨부 파일: 올리기 · 설명 수정 · 지우기. 글이 서버에 저장돼 주소(slug)가 있어야 쓸 수 있다. */
function AttachmentManager({ slug }) {
  const fileRef = useRef(null)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(null)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [newDesc, setNewDesc] = useState('')

  const load = useCallback(() => {
    if (!slug) return
    setLoading(true)
    getAttachments(slug)
      .then((r) => setItems(r.data || []))
      .catch(() => toast.error('첨부 목록을 불러오지 못했어요'))
      .finally(() => setLoading(false))
  }, [slug])
  useEffect(() => { load() }, [load])

  if (!slug) {
    return <p className="m-0 text-sm" style={labelStyle}>글을 한 번 저장하면 파일을 올릴 수 있어요.</p>
  }

  async function pick(e) {
    const file = e.target.files?.[0]
    if (fileRef.current) fileRef.current.value = ''
    if (!file) return
    if (!kindFromName(file.name)) { toast.error(`올릴 수 있는 형식: ${ATTACHMENT_KINDS.join(', ')}`); return }
    if (file.size > ATTACHMENT_MAX_BYTES) { toast.error('파일이 너무 커요(20MB 이하).'); return }
    const fd = new FormData()
    fd.append('file', file)
    if (newDesc.trim()) fd.append('description', newDesc.trim())
    setProgress(0)
    try {
      const { data } = await uploadAttachment(slug, fd, (ev) => {
        if (ev.total) setProgress(Math.round((ev.loaded / ev.total) * 100))
      })
      setItems((prev) => (prev.some((x) => x.id === data.id) ? prev.map((x) => (x.id === data.id ? data : x)) : [...prev, data]))
      setNewDesc('')
      toast.success('파일을 올렸어요')
    } catch (err) {
      toast.error(`올리기 실패 · ${describe(err)}`)
    } finally {
      setProgress(null)
    }
  }

  async function saveDesc(item, value) {
    const description = value.trim()
    if (description === (item.description || '')) return
    try {
      const { data } = await updateAttachment(slug, item.id, { description })
      setItems((prev) => prev.map((x) => (x.id === item.id ? data : x)))
      toast.success('설명을 고쳤어요')
    } catch (err) {
      toast.error(`설명 수정 실패 · ${describe(err)}`)
    }
  }

  async function remove() {
    const item = pendingDelete
    setPendingDelete(null)
    if (!item) return
    try {
      await deleteAttachment(slug, item.id)
      setItems((prev) => prev.filter((x) => x.id !== item.id))
      toast.success('파일을 지웠어요')
    } catch (err) {
      toast.error(`지우기 실패 · ${describe(err)}`)
    }
  }

  async function copyLink(item) {
    const md = `[${item.filename}](${item.url})`
    try {
      await navigator.clipboard.writeText(md)
      toast.success('본문에 붙일 링크를 복사했어요')
    } catch {
      toast(md)
    }
  }

  return (
    <div className="space-y-3">
      {loading && <p className="m-0 text-sm" style={labelStyle}>불러오는 중…</p>}
      {!loading && items.length === 0 && <p className="m-0 text-sm" style={labelStyle}>아직 올린 파일이 없어요.</p>}
      <ul className="m-0 list-none space-y-2 p-0">
        {items.map((item) => (
          <li key={item.id} className="rounded-lg border p-3" style={{ borderColor: 'var(--border)' }}>
            <div className="flex flex-wrap items-center gap-2">
              <p className="m-0 min-w-0 flex-1 basis-40 break-all text-sm font-medium" style={{ color: 'var(--text)' }}>
                {item.filename}
                <span className="ml-2 text-xs font-normal" style={labelStyle}>
                  {KIND_LABEL[item.kind] || item.kind} · {formatBytes(item.size_bytes)}
                </span>
              </p>
              <button type="button" onClick={() => copyLink(item)} className={btnCls} style={btnStyle} aria-label={`${item.filename} 본문 링크 복사`}>
                <Copy size={15} /> <span className="hidden sm:inline">링크 복사</span>
              </button>
              <button type="button" onClick={() => setPendingDelete(item)} className={btnCls} style={{ ...btnStyle, color: '#dc2626' }} aria-label={`${item.filename} 지우기`}>
                <Trash2 size={15} /> <span className="hidden sm:inline">지우기</span>
              </button>
            </div>
            <input defaultValue={item.description || ''} key={`${item.id}:${item.description || ''}`} maxLength={300}
              onBlur={(e) => saveDesc(item, e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur() }}
              placeholder="짧은 설명 (입력 후 Enter 또는 칸 밖을 누르면 저장)" aria-label={`${item.filename} 설명`}
              className={`${inputCls} mt-2`} style={inputStyle} />
          </li>
        ))}
      </ul>

      <div className="rounded-lg border border-dashed p-3" style={{ borderColor: 'var(--border)' }}>
        <input ref={fileRef} type="file" accept={ATTACHMENT_ACCEPT} hidden onChange={pick} />
        <input value={newDesc} maxLength={300} onChange={(e) => setNewDesc(e.target.value)}
          placeholder="새 파일의 짧은 설명 (선택)" aria-label="새 파일 설명" className={inputCls} style={inputStyle} />
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <button type="button" onClick={() => fileRef.current?.click()} disabled={progress !== null} className={btnCls} style={btnStyle}>
            <Upload size={15} /> {progress !== null ? `올리는 중 ${progress}%` : '파일 올리기'}
          </button>
          <span className="text-xs" style={labelStyle}>{ATTACHMENT_KINDS.join(' · ')} · 20MB 이하 · 같은 이름은 덮어써요</span>
        </div>
      </div>
      <p className="m-0 text-xs" style={labelStyle}>
        올린 파일은 주소를 아는 사람이면 누구나 받을 수 있어요(초안 글의 파일도 마찬가지).
      </p>

      <ConfirmDialog
        isOpen={Boolean(pendingDelete)}
        title="파일을 지울까요?"
        message={`${pendingDelete?.filename || ''} 파일이 저장소에서도 지워져요. 본문에 넣은 링크는 직접 지워야 해요.`}
        confirmLabel="지우기"
        variant="danger"
        onConfirm={remove}
        onCancel={() => setPendingDelete(null)}
      />
    </div>
  )
}

/**
 * 편집기의 "요약·질문·첨부" 창. 모바일에서는 아래에서 올라오는 전체 폭 시트, 넓은 화면에서는 가운데 창.
 * 요약 카드와 질문은 글 폼(form)에 들어가 글과 함께 저장되고, 첨부는 올리는 즉시 서버에 반영된다.
 */
export default function PostExtrasPanel({ open, onClose, form, onChange, slug }) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 sm:items-center sm:p-4" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-labelledby="extras-title"
        className="flex max-h-[92dvh] w-full flex-col rounded-t-2xl sm:max-w-2xl sm:rounded-2xl"
        style={{ background: 'var(--card-bg)' }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 border-b px-4 py-3 sm:px-6" style={{ borderColor: 'var(--border)' }}>
          <p id="extras-title" className="m-0 flex-1 text-base font-bold" style={{ color: 'var(--text)' }}>요약 · 질문 · 첨부</p>
          <button type="button" onClick={onClose} className={btnCls} style={btnStyle} aria-label="닫기"><X size={16} /></button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
          <Section title="글 머리 요약 카드" hint="본문 위에 보여요. 전부 비우면 카드가 나오지 않아요.">
            <CardForm card={form.summary_card} onChange={(summary_card) => onChange({ summary_card })} />
          </Section>
          <Section title="글 끝 확인 질문" hint="본문 아래에 보여요. 답은 접혀 있다가 누르면 펼쳐져요.">
            <QuizForm quiz={form.quiz} onChange={(quiz) => onChange({ quiz })} />
          </Section>
          <Section title="첨부 파일(실습 파일)" hint="요약 카드와 본문 아래에 내려받기 목록으로 보여요.">
            <AttachmentManager slug={slug} />
          </Section>
        </div>
        <div className="flex items-center justify-end border-t px-4 py-3 sm:px-6" style={{ borderColor: 'var(--border)' }}>
          <span className="mr-auto text-xs" style={labelStyle}>요약·질문은 글을 저장할 때 함께 저장돼요.</span>
          <button type="button" onClick={onClose} className={`${btnCls} bg-primary-600 !text-white hover:bg-primary-700`} style={{ borderColor: 'transparent' }}>
            닫기
          </button>
        </div>
      </div>
    </div>
  )
}
