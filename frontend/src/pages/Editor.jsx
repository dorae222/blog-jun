import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  Eye, Code, Columns, List, Check, Circle, Link2, BookOpen, SlidersHorizontal, AlertTriangle, RotateCcw, LoaderCircle, Tags, ListChecks,
} from 'lucide-react'
import PostLinkModal from '../components/editor/PostLinkModal'
import NotionEditor from '../components/editor/NotionEditor'
import SplitEditor from '../components/editor/SplitEditor'
import MarkdownEditor from '../components/editor/MarkdownEditor'
import PublishChecklist from '../components/editor/PublishChecklist'
import TagPicker from '../components/editor/TagPicker'
import PostExtrasPanel from '../components/editor/PostExtrasPanel'
import SummaryCard from '../components/blog/SummaryCard'
import PostQuiz from '../components/blog/PostQuiz'
import useLeaveGuard from '../hooks/useLeaveGuard'
import MarkdownRenderer from '../components/blog/MarkdownRenderer'
import ConfirmDialog from '../components/common/ConfirmDialog'
import client from '../api/client'
import { getPost, createPost, updatePost, getCategories, getSeries, getTemplates, getAllTags, uploadImage } from '../api/posts'
import { readDraft, writeDraft, clearDraft } from '../utils/editorDraft'
import { autoSlug, slugSuffix, timeAgo } from '../utils/noteText'
import { emptyCard, emptyQuiz, cardToForm, quizToForm, cardPayload, quizPayload } from '../utils/postExtras'

/**
 * 글 편집기.
 *
 * 저장은 두 겹이다.
 *  1) 로컬 임시저장: 입력이 멈추고 0.6초 뒤 localStorage에 쓴다. 탭이 죽어도 남는다.
 *  2) 서버 자동 저장: 초안(draft)일 때만, 입력이 멈추고 4초 뒤 PATCH(새 글이면 POST)한다.
 *     발행된 글은 자동으로 서버에 올리지 않는다. 쓰는 도중의 문장이 그대로 공개되면 안 되기 때문이다.
 *     발행된 글은 Cmd/Ctrl+S나 "반영" 버튼으로만 서버에 저장된다.
 * 다시 열었을 때 서버 내용과 다른 로컬 임시본이 있으면 복구할지 묻는다.
 */

const EMPTY_FORM = {
  title: '',
  slug: '',
  content: '',
  summary: '',
  category: '',
  tags: [],
  series: '',
  series_order: 0,
  post_type: 'article',
  status: 'draft',
  published_at: null,
  arxiv_url: '',
  venue: '',
  paper_year: null,
  paper_authors: '',
  // 글 머리 요약 카드 · 글 끝 확인 질문(폼 모양. 서버 형식으로는 toPayload 에서 바꾼다)
  summary_card: emptyCard(),
  quiz: emptyQuiz(),
}

const LOCAL_DEBOUNCE_MS = 600
const SERVER_DEBOUNCE_MS = 4000

function toForm(p) {
  return {
    title: p.title || '',
    slug: p.slug || '',
    content: p.content || '',
    summary: p.summary || '',
    category: p.category?.id || '',
    tags: p.tags?.map(t => t.id) || [],
    series: p.series?.id || '',
    series_order: p.series_order || 0,
    post_type: p.post_type || 'article',
    status: p.status || 'draft',
    published_at: p.published_at || null,
    arxiv_url: p.arxiv_url || '',
    venue: p.venue || '',
    paper_year: p.paper_year || null,
    paper_authors: p.paper_authors || '',
    summary_card: cardToForm(p.summary_card),
    quiz: quizToForm(p.quiz),
  }
}

/** DRF 형식 오류({field: [msg]} 또는 {detail})를 한 줄로. */
function describeError(err) {
  const d = err?.response?.data
  if (!d) return err?.response ? `HTTP ${err.response.status}` : '네트워크 오류'
  if (typeof d === 'string') return d.slice(0, 120)
  if (d.detail) return String(d.detail)
  const first = Object.entries(d)[0]
  if (first) {
    const [k, v] = first
    return `${k}: ${Array.isArray(v) ? v.join(' ') : String(v)}`
  }
  return '알 수 없는 오류'
}

/** 서버로 보낼 본문. 바뀌지 않은 slug는 보내지 않는다(예전 한글 slug 글도 수정할 수 있게). */
function toPayload(form, { isNew, originalSlug }) {
  const data = { ...form }
  if (!isNew && data.slug === originalSlug) delete data.slug
  if (!data.category) { if (isNew) delete data.category; else data.category = null }
  if (!data.series) { if (isNew) delete data.series; else data.series = null }
  if (!data.published_at) delete data.published_at
  if (!data.paper_year) data.paper_year = null
  // 요약 카드·질문: 다 비었으면 null(지움), 쓰는 중(필수 칸이 빔)이면 보내지 않아 서버 값을 그대로 둔다.
  // 쓰는 중인 값을 보내면 400 이 나서 본문 자동 저장까지 막힌다.
  const card = cardPayload(form.summary_card)
  if (card.state === 'incomplete') delete data.summary_card
  else data.summary_card = card.value
  const quiz = quizPayload(form.quiz)
  if (quiz.state === 'incomplete') delete data.quiz
  else data.quiz = quiz.value
  return data
}

function CoverPicker({ slug, url, onDone }) {
  const ref = useRef(null)
  const [busy, setBusy] = useState(false)

  if (!slug) return null

  async function pick(e) {
    const f = e.target.files?.[0]
    if (!f) return
    const fd = new FormData()
    fd.append('file', f)
    setBusy(true)
    try {
      const { data } = await client.post(`/posts/${slug}/cover/`, fd,
        { headers: { 'Content-Type': 'multipart/form-data' } })
      onDone(data.cover_image_url)
      toast.success('표지를 올렸습니다')
    } catch {
      toast.error('표지 업로드에 실패했습니다')
    } finally {
      setBusy(false)
      if (ref.current) ref.current.value = ''
    }
  }

  return (
    <span className="inline-flex items-center gap-2">
      <input ref={ref} type="file" accept="image/*" hidden onChange={pick} />
      {url && (
        <img src={url} alt="" className="h-7 w-11 object-cover rounded border"
          style={{ borderColor: 'var(--border)' }} />
      )}
      <button type="button" onClick={() => ref.current?.click()} disabled={busy}
        className="text-sm px-2 py-1 rounded border hover:bg-black/5 disabled:opacity-50"
        style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
        {busy ? '올리는 중' : (url ? '표지 변경' : '표지 올리기')}
      </button>
    </span>
  )
}

export default function Editor() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const isNew = !slug
  const draftKey = slug || 'new'

  const [coverUrl, setCoverUrl] = useState('')
  const [showTemplates, setShowTemplates] = useState(false)
  const [pendingTemplate, setPendingTemplate] = useState(null)
  const [showLinkModal, setShowLinkModal] = useState(false)
  const [showChecklist, setShowChecklist] = useState(false)
  const [showMeta, setShowMeta] = useState(false)
  const [showExtras, setShowExtras] = useState(false)
  const [templates, setTemplates] = useState([])
  const [categories, setCategories] = useState([])
  const [allTags, setAllTags] = useState([])
  const [showTagPicker, setShowTagPicker] = useState(false)
  const [pendingNav, setPendingNav] = useState(null)
  const tiptapRef = useRef(null)
  const mdRef = useRef(null)
  const areaRef = useRef(null)
  const [allSeries, setAllSeries] = useState([])
  const [viewMode, setViewMode] = useState('wysiwyg') // wysiwyg | split | source | preview
  const [showToc, setShowToc] = useState(false)
  const [headings, setHeadings] = useState([])
  const [errors, setErrors] = useState({})

  const [form, setForm] = useState(EMPTY_FORM)
  const [loaded, setLoaded] = useState(isNew)
  const [loadError, setLoadError] = useState(false)
  const [serverStatus, setServerStatus] = useState('draft') // 서버에 저장된 상태
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [lastSavedAt, setLastSavedAt] = useState(null)
  const [localSavedAt, setLocalSavedAt] = useState(null)
  const [recovery, setRecovery] = useState(null)
  const [slugTouched, setSlugTouched] = useState(!isNew)
  const [, setTick] = useState(0)

  const formRef = useRef(form)
  const dirtyRef = useRef(false)
  const savingRef = useRef(false)
  const originalSlugRef = useRef(slug || '')
  const skipLoadRef = useRef(null)
  const suffixRef = useRef(slugSuffix())
  const slugTouchedRef = useRef(slugTouched)
  useEffect(() => { slugTouchedRef.current = slugTouched }, [slugTouched])
  useEffect(() => { formRef.current = form }, [form])
  useEffect(() => { dirtyRef.current = dirty }, [dirty])

  // "저장됨 n초 전" 표시를 살아 있게
  useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 5000)
    return () => clearInterval(t)
  }, [])

  // 고를 거리(카테고리·시리즈·템플릿)는 한 번만
  useEffect(() => {
    getCategories().then(r => setCategories(r.data.results || r.data || [])).catch(() => {})
    getSeries().then(r => setAllSeries(r.data.results || r.data || [])).catch(() => {})
    getAllTags().then(r => setAllTags(r.data.results || r.data || [])).catch(() => {})
    getTemplates().then(r => setTemplates(r.data.results || r.data || [])).catch(() => {})
  }, [])

  // 목차: 코드 블록 안의 `# 주석`은 빼고, 소스 모드 이동용으로 글자 위치(offset)도 같이 든다.
  const extractHeadings = useCallback((markdown) => {
    const out = []
    let inFence = false
    let offset = 0
    for (const line of (markdown || '').split('\n')) {
      if (/^\s*(```|~~~)/.test(line)) inFence = !inFence
      else if (!inFence) {
        const m = /^(#{1,3})\s+(.+)$/.exec(line)
        if (m) out.push({ level: m[1].length, text: m[2].replace(/[*_`]/g, ''), offset })
      }
      offset += line.length + 1
    }
    setHeadings(out)
  }, [])

  // 글 불러오기. 방금 저장하면서 주소만 바뀐 경우(skipLoadRef)는 다시 불러오지 않는다.
  useEffect(() => {
    if (skipLoadRef.current && skipLoadRef.current === slug) {
      skipLoadRef.current = null
      return
    }
    setRecovery(null)
    setSaveError(null)
    setLoadError(false)
    setDirty(false)
    originalSlugRef.current = slug || ''
    if (!slug) {
      setForm(EMPTY_FORM)
      setCoverUrl('')
      setServerStatus('draft')
      setLastSavedAt(null)
      setSlugTouched(false)
      setLoaded(true)
      extractHeadings('')
      const d = readDraft('new')
      if (d && (d.form.title?.trim() || d.form.content?.trim())) setRecovery(d)
      return
    }
    let alive = true
    setLoaded(false)
    setSlugTouched(true)
    getPost(slug).then(r => {
      if (!alive) return
      const p = r.data
      const f = toForm(p)
      setForm(f)
      extractHeadings(f.content)
      setServerStatus(f.status)
      setCoverUrl(p.cover_image_url || '')
      setLastSavedAt(p.updated_at ? Date.parse(p.updated_at) : null)
      setLoaded(true)
      const d = readDraft(slug)
      if (d && (d.form.content !== f.content || d.form.title !== f.title)) setRecovery(d)
      else if (d) clearDraft(slug)
    }).catch(() => {
      if (!alive) return
      setLoadError(true)
      setLoaded(true)
    })
    return () => { alive = false }
  }, [slug, extractHeadings])

  const updateForm = useCallback((updates, opts = {}) => {
    if (opts.slugTouched) setSlugTouched(true)
    setForm(prev => ({ ...prev, ...updates }))
    setDirty(true)
    setSaveError(null)
    setErrors(prev => {
      const next = { ...prev }
      Object.keys(updates).forEach(key => delete next[key])
      return next
    })
  }, [])

  const handleTitle = (title) => {
    updateForm(slugTouched ? { title } : { title, slug: autoSlug(title, suffixRef.current) })
  }

  const handleContentChange = useCallback((markdown) => {
    if (markdown === formRef.current.content) return
    updateForm({ content: markdown })
    extractHeadings(markdown)
  }, [updateForm, extractHeadings])

  // ── 저장 ─────────────────────────────────────────────
  const save = useCallback(async ({ silent = false, overrides = {} } = {}) => {
    if (savingRef.current) return false
    const snapshot = formRef.current
    const cur = { ...snapshot, ...overrides }
    if (!cur.title.trim()) {
      if (!silent) { setErrors({ title: true }); toast.error('제목을 입력하세요') }
      return false
    }
    if (!cur.content.trim()) {
      if (!silent) toast.error('본문이 비어 있어요')
      return false
    }
    if (isNew && !cur.slug) cur.slug = autoSlug(cur.title, suffixRef.current)
    savingRef.current = true
    setSaving(true)
    try {
      const payload = toPayload(cur, { isNew, originalSlug: originalSlugRef.current })
      let r
      try {
        r = isNew ? await createPost(payload) : await updatePost(slug, payload)
      } catch (err) {
        // 새 글의 자동 slug가 이미 있는 글과 겹치면 꼬리를 붙여 한 번만 다시 시도한다.
        // (사용자가 직접 고친 slug는 건드리지 않고 오류로 알린다)
        if (!(isNew && !slugTouchedRef.current && err?.response?.status === 400 && err.response.data?.slug)) throw err
        payload.slug = `${cur.slug}-${Math.random().toString(36).slice(2, 5)}`
        r = await createPost(payload)
      }
      const savedSlug = r.data?.slug || payload.slug || cur.slug || slug
      const editedDuring = formRef.current !== snapshot
      // 서버가 다듬은 요약 카드(선수 글 제목 채움 등)를 폼에 되돌려 놓는다. 저장 중에 더 고쳤으면 건드리지 않는다.
      const normalized = !editedDuring && r.data && 'summary_card' in payload && r.data.summary_card !== undefined
        ? { summary_card: cardToForm(r.data.summary_card) }
        : {}
      setForm(prev => ({ ...prev, ...overrides, ...normalized, slug: savedSlug }))
      setServerStatus(cur.status)
      setLastSavedAt(Date.now())
      setSaveError(null)
      setDirty(editedDuring)
      setSlugTouched(true)
      if (!editedDuring) clearDraft(draftKey)
      if (isNew) clearDraft('new')
      originalSlugRef.current = savedSlug
      if (savedSlug !== slug) {
        // 주소가 생기거나 바뀌었다. 편집기를 다시 그리지 않고 주소창만 맞춘다.
        if (editedDuring) writeDraft(savedSlug, formRef.current)
        skipLoadRef.current = savedSlug
        navigate(`/editor/${encodeURIComponent(savedSlug)}`, { replace: true })
      }
      if (!silent) toast.success(cur.status === 'published' ? (overrides.status ? '발행했어요' : '반영했어요') : '저장했어요')
      return true
    } catch (err) {
      const msg = describeError(err)
      setSaveError(msg)
      if (!silent) toast.error(`저장 실패 · ${msg}`)
      return false
    } finally {
      savingRef.current = false
      setSaving(false)
    }
  }, [isNew, slug, draftKey, navigate])

  // 1) 로컬 임시저장
  useEffect(() => {
    if (!dirty) return
    const t = setTimeout(() => {
      const at = writeDraft(draftKey, formRef.current)
      if (at) setLocalSavedAt(at)
    }, LOCAL_DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [form, dirty, draftKey])

  // 2) 서버 자동 저장(초안만). 복구 안내가 떠 있는 동안은 서버를 덮어쓰지 않는다.
  const autoEligible = serverStatus === 'draft' && !recovery && loaded && !loadError
  useEffect(() => {
    if (!dirty || !autoEligible || saveError) return
    if (!form.title.trim() || !form.content.trim()) return
    const t = setTimeout(() => { save({ silent: true }) }, SERVER_DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [form, dirty, autoEligible, saveError, save])

  // 저장 실패 후에는 30초마다 한 번 다시 시도(네트워크 순단 대비)
  useEffect(() => {
    if (!saveError || !dirty || !autoEligible) return
    const t = setTimeout(() => { save({ silent: true }) }, 30000)
    return () => clearTimeout(t)
  }, [saveError, dirty, autoEligible, save])

  // 화면을 떠날 때: 로컬엔 반드시 남기고, 초안이면 서버에도 한 번 밀어 넣는다(실패해도 로컬이 있다).
  const leaveRef = useRef({})
  useEffect(() => { leaveRef.current = { draftKey, slug, autoEligible } }, [draftKey, slug, autoEligible])
  useEffect(() => () => {
    if (!dirtyRef.current) return
    const { draftKey: key, slug: s, autoEligible: ok } = leaveRef.current
    writeDraft(key, formRef.current)
    if (s && ok && formRef.current.title.trim() && formRef.current.content.trim()) {
      updatePost(s, toPayload(formRef.current, { isNew: false, originalSlug: originalSlugRef.current }))
        .then(() => clearDraft(key)).catch(() => {})
    }
  }, [])

  useEffect(() => {
    const handler = (e) => {
      if (!dirtyRef.current) return
      writeDraft(draftKey, formRef.current)
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [draftKey])

  const openChecklist = () => {
    const errs = {}
    if (!form.category) errs.category = true
    if (!form.title.trim()) errs.title = true
    setErrors(errs)
    setShowChecklist(true)
  }

  const confirmPublish = async () => {
    const overrides = serverStatus === 'published'
      ? {}
      : { status: 'published', published_at: form.published_at || new Date().toISOString() }
    const ok = await save({ overrides })
    if (ok) setShowChecklist(false)
  }

  // 단축키: Cmd/Ctrl+S 저장, Cmd/Ctrl+K 글 링크, Alt+P 미리보기 전환
  useEffect(() => {
    const handler = (e) => {
      const mod = e.metaKey || e.ctrlKey
      if (mod && e.key.toLowerCase() === 's') {
        e.preventDefault()
        save()
      } else if (mod && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setShowLinkModal(true)
      } else if (e.altKey && e.code === 'KeyP') {
        e.preventDefault()
        setViewMode(m => (m === 'preview' ? 'wysiwyg' : 'preview'))
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [save])

  const handleImageUpload = useCallback(async (file) => {
    const formData = new FormData()
    formData.append('image', file)
    const { data } = await uploadImage(formData)
    return data.image
  }, [])

  const applyTemplate = (tmpl) => {
    updateForm({ content: tmpl.content_template || '', post_type: tmpl.post_type || formRef.current.post_type })
    extractHeadings(tmpl.content_template || '')
    setShowTemplates(false)
    setPendingTemplate(null)
  }
  const pickTemplate = (tmpl) => {
    if (formRef.current.content.trim()) { setPendingTemplate(tmpl); setShowTemplates(false) }
    else applyTemplate(tmpl)
  }

  // 글 링크(Ctrl/Cmd+K)는 커서 자리에 넣는다. 커서를 알 수 없는 미리보기 모드에서만 끝에 붙인다.
  const handleInsertLink = useCallback((linkText) => {
    if (viewMode === 'wysiwyg' && tiptapRef.current && !tiptapRef.current.isDestroyed) {
      tiptapRef.current.chain().focus().insertContent(linkText).run()
      return
    }
    if ((viewMode === 'source' || viewMode === 'split') && mdRef.current) {
      mdRef.current.insertAtCursor(linkText)
      return
    }
    updateForm({ content: `${formRef.current.content}\n${linkText}` })
    toast('미리보기 모드라 본문 끝에 넣었어요')
  }, [updateForm, viewMode])

  // 목차 클릭 → 해당 헤딩으로. 소스 계열은 커서도 그 줄로 옮긴다.
  const scrollToHeading = (h, i) => {
    if (viewMode === 'source' || viewMode === 'split') mdRef.current?.scrollToOffset(h.offset)
    if (viewMode === 'source') return
    const root = areaRef.current?.querySelector(viewMode === 'wysiwyg' ? '.notion-editor-content' : '[data-toc-root]')
    const el = root?.querySelectorAll('h1, h2, h3')[i]
    el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  // 저장 안 된 변경이 있을 때 앱 안 링크(헤더 메뉴 등)로 나가려 하면 묻는다.
  useLeaveGuard(dirty || saving, setPendingNav)
  const leaveWithoutSave = () => {
    const to = pendingNav
    if (dirtyRef.current) writeDraft(draftKey, formRef.current)
    setPendingNav(null)
    navigate(to)
  }
  const saveAndLeave = async () => {
    const to = pendingNav
    const ok = await save()
    if (ok) { setPendingNav(null); navigate(to) }
  }

  const restoreDraft = () => {
    if (!recovery) return
    // 예전 임시저장본에는 요약 카드·질문 칸이 없다. 그때는 지금(서버) 값을 그대로 둔다.
    setForm(prev => ({ ...EMPTY_FORM, summary_card: prev.summary_card, quiz: prev.quiz, ...recovery.form }))
    extractHeadings(recovery.form.content)
    if (recovery.form.slug && isNew) setSlugTouched(Boolean(recovery.form.slug))
    setDirty(true)
    setRecovery(null)
    toast.success('임시저장본을 불러왔어요')
  }
  const discardDraft = () => {
    clearDraft(draftKey)
    setRecovery(null)
  }

  if (!loaded) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm" style={{ color: 'var(--text-secondary)' }}>
        Loading...
      </div>
    )
  }
  if (loadError) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-sm" style={{ color: 'var(--text-secondary)' }}>
        글을 불러오지 못했어요.
        <button onClick={() => navigate('/dashboard')} className="px-3 py-1.5 rounded-lg border" style={{ borderColor: 'var(--border)' }}>대시보드로</button>
      </div>
    )
  }

  const VIEW_MODES = [
    { id: 'wysiwyg', icon: Eye, label: 'WYSIWYG' },
    { id: 'split', icon: Columns, label: '나란히(소스+미리보기)' },
    { id: 'source', icon: Code, label: '마크다운 소스' },
    { id: 'preview', icon: BookOpen, label: '미리보기 (Alt+P)' },
  ]
  const isPublished = serverStatus === 'published'
  const fieldCls = 'min-w-[8rem] flex-1 md:flex-none text-sm px-2 py-1 rounded border'
  const fieldStyle = { borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }

  let statusNode
  if (saving) statusNode = <span style={{ color: '#f59e0b' }} className="inline-flex items-center gap-1"><LoaderCircle size={12} className="animate-spin" /> 저장 중</span>
  else if (saveError) statusNode = (
    <button onClick={() => save()} title={saveError} className="inline-flex items-center gap-1 text-red-500 hover:underline">
      <AlertTriangle size={12} /> 저장 실패 · 재시도
    </button>
  )
  else if (dirty) statusNode = (
    <span style={{ color: '#6366f1' }} className="inline-flex items-center gap-1"
      title={autoEligible ? '입력이 멈추면 서버에 자동 저장돼요' : '발행된 글은 자동으로 서버에 올리지 않아요. Cmd/Ctrl+S로 반영하세요.'}>
      <Circle size={8} className="fill-current" />
      {autoEligible ? '변경됨' : `로컬 임시저장${localSavedAt ? ` ${timeAgo(localSavedAt)}` : ''}`}
    </span>
  )
  else statusNode = (
    <span style={{ color: '#10b981' }} className="inline-flex items-center gap-1">
      <Check size={12} /> {lastSavedAt ? `저장됨 ${timeAgo(lastSavedAt)}` : (isNew ? '새 글' : '저장됨')}
    </span>
  )

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-[calc(100dvh-4rem)] flex flex-col overflow-hidden"
    >
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 md:gap-3 px-3 md:px-4 py-2 border-b" style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
        <input
          value={form.title}
          onChange={e => handleTitle(e.target.value)}
          placeholder="제목"
          aria-label="제목"
          className="basis-full min-w-0 text-base md:text-lg font-semibold bg-transparent outline-none"
          style={{ color: 'var(--text)', borderBottom: errors.title ? '2px solid #ef4444' : undefined }}
        />

        {/* 메타데이터: 모바일에서는 "설정"을 눌러야 펼친다 */}
        <div className={`${showMeta ? 'flex' : 'hidden'} md:contents basis-full flex-wrap items-center gap-2`}>
          <select value={form.post_type} onChange={e => updateForm({ post_type: e.target.value })} className={fieldCls} style={fieldStyle} aria-label="글 유형">
            <option value="article">Article</option>
            <option value="paper_review">Paper Review</option>
            <option value="tutorial">Tutorial</option>
            <option value="til">TIL</option>
            <option value="project">Project</option>
            <option value="activity_log">Activity Log</option>
          </select>

          <select value={form.category} onChange={e => updateForm({ category: e.target.value })} className={fieldCls}
            style={{ ...fieldStyle, borderColor: errors.category ? '#ef4444' : 'var(--border)' }} aria-label="카테고리">
            <option value="">Category</option>
            {/* 글은 소분류에만 붙인다. 대탭은 묶음일 뿐이라 고를 수 없게 막는다. */}
            {categories.flatMap(c => (c.children?.length
              ? [<option key={c.id} disabled>{`— ${c.name} —`}</option>,
                 ...c.children.map(k => <option key={k.id} value={k.id}>{`  ${k.name}`}</option>)]
              : [<option key={c.id} value={c.id}>{c.name}</option>]))}
          </select>

          <select value={form.series} onChange={e => updateForm({ series: e.target.value })} className={fieldCls} style={fieldStyle} aria-label="시리즈">
            <option value="">Series</option>
            {allSeries.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>

          {form.series && (
            <input type="number" min="0" value={form.series_order}
              onChange={e => updateForm({ series_order: Number(e.target.value) })}
              title="시리즈 안에서의 편 번호" aria-label="시리즈 편 번호"
              className="w-20 text-sm px-2 py-1 rounded border" style={fieldStyle} placeholder="편" />
          )}

          <CoverPicker slug={slug} url={coverUrl} onDone={setCoverUrl} />

          {form.post_type === 'paper_review' && (
            <>
              <input value={form.arxiv_url} onChange={e => updateForm({ arxiv_url: e.target.value })} placeholder="arXiv URL"
                className="text-sm px-2 py-1 rounded border w-full md:w-40" style={fieldStyle} />
              <input value={form.venue} onChange={e => updateForm({ venue: e.target.value })} placeholder="학회 (NeurIPS, ICML...)"
                className="text-sm px-2 py-1 rounded border flex-1 md:flex-none md:w-32" style={fieldStyle} />
              <input type="number" value={form.paper_year || ''}
                onChange={e => updateForm({ paper_year: e.target.value ? parseInt(e.target.value) : null })}
                placeholder="연도" className="text-sm px-2 py-1 rounded border w-24 md:w-20" style={fieldStyle} />
            </>
          )}

          <button onClick={() => setShowLinkModal(true)} className="shrink-0 text-sm px-3 py-1 rounded border hover:bg-gray-50"
            style={{ borderColor: 'var(--border)' }} title="글 링크 넣기 (Ctrl/Cmd+K)" aria-label="글 링크 넣기">
            <Link2 size={14} />
          </button>
          <button onClick={() => setShowTemplates(true)} className="shrink-0 text-sm px-3 py-1 rounded border hover:bg-gray-50"
            style={{ borderColor: 'var(--border)' }}>
            Templates
          </button>

          <button onClick={() => setShowExtras(true)}
            className="shrink-0 inline-flex items-center gap-1 text-sm px-3 py-1 rounded border hover:bg-gray-50"
            style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }} title="요약 카드 · 확인 질문 · 첨부 파일">
            <ListChecks size={14} /> 요약·질문·첨부
          </button>

          <div className="relative">
            <button onClick={() => setShowTagPicker(v => !v)} aria-expanded={showTagPicker}
              className="shrink-0 inline-flex items-center gap-1 text-sm px-3 py-1 rounded border hover:bg-gray-50"
              style={{ borderColor: 'var(--border)', color: form.tags.length ? 'var(--text)' : 'var(--text-secondary)' }}>
              <Tags size={14} /> 태그{form.tags.length ? ` ${form.tags.length}` : ''}
            </button>
            {showTagPicker && (
              <div className="absolute z-40 mt-1 left-0 w-[min(22rem,calc(100vw-2rem))] p-2 rounded-xl border shadow-lg"
                style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                onKeyDown={e => { if (e.key === 'Escape') setShowTagPicker(false) }}>
                <div className="flex items-center mb-1.5">
                  <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>태그 · 입력 후 Enter (없으면 새로 만듦)</span>
                  <button onClick={() => setShowTagPicker(false)} className="ml-auto text-xs px-2 py-0.5 rounded hover:bg-black/5" style={{ color: 'var(--text-secondary)' }}>닫기</button>
                </div>
                <TagPicker value={form.tags} onChange={tags => updateForm({ tags })} allTags={allTags}
                  onTagCreated={t => setAllTags(prev => [...prev, t])} />
              </div>
            )}
          </div>
        </div>

        <button onClick={() => setShowMeta(v => !v)} className="md:hidden shrink-0 inline-flex items-center gap-1 text-xs px-2 py-1 rounded border"
          style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }} aria-expanded={showMeta}>
          <SlidersHorizontal size={13} /> 설정
        </button>

        {/* View Mode Toggle */}
        <div className="flex shrink-0 items-center rounded border overflow-hidden" style={{ borderColor: 'var(--border)' }} role="group" aria-label="보기 방식">
          {VIEW_MODES.map(mode => (
            <button key={mode.id} onClick={() => setViewMode(mode.id)}
              className={`px-2 py-1 text-xs flex items-center gap-1 transition-colors ${mode.id === 'split' ? 'hidden md:flex' : ''}`}
              style={{
                background: viewMode === mode.id ? 'var(--bg)' : 'transparent',
                color: viewMode === mode.id ? 'var(--text)' : 'var(--text-secondary)',
                fontWeight: viewMode === mode.id ? 600 : 400,
              }}
              title={mode.label} aria-label={mode.label} aria-pressed={viewMode === mode.id}>
              <mode.icon size={14} />
            </button>
          ))}
        </div>

        <button onClick={() => setShowToc(prev => !prev)} className="hidden md:inline-flex shrink-0 px-2 py-1 rounded border text-xs"
          style={{ borderColor: 'var(--border)', background: showToc ? 'var(--bg)' : 'transparent', color: showToc ? 'var(--text)' : 'var(--text-secondary)' }}
          title="목차" aria-label="목차" aria-pressed={showToc}>
          <List size={14} />
        </button>

        <span className="hidden sm:inline text-xs shrink-0" style={{ color: 'var(--text-secondary)' }}>
          {(() => {
            const chars = form.content.trim().length
            return `${chars.toLocaleString()}자 · ${Math.max(1, Math.ceil(chars / 500))}분`
          })()}
        </span>

        <span className="ml-auto text-xs px-1 shrink-0" aria-live="polite">{statusNode}</span>

        <button onClick={() => save()} disabled={saving}
          className="shrink-0 text-sm px-3 md:px-4 py-1.5 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          title="저장 (Ctrl/Cmd+S)">
          {isPublished ? '업데이트' : '저장'}
        </button>

        <button onClick={openChecklist} disabled={saving}
          className="shrink-0 text-sm px-3 md:px-4 py-1.5 rounded bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed">
          {isPublished ? '점검 후 반영' : '발행'}
        </button>
      </div>

      {/* 복구 안내 */}
      {recovery && (
        <div className="flex flex-wrap items-center gap-2 px-4 py-2 text-sm border-b"
          style={{ background: '#fffbeb', borderColor: '#fde68a', color: '#92400e' }} role="status">
          <RotateCcw size={14} />
          <span>저장되지 않은 임시저장본이 있어요 ({timeAgo(recovery.savedAt)}, {(recovery.form.content || '').length.toLocaleString()}자).</span>
          <button onClick={restoreDraft} className="px-2 py-0.5 rounded bg-amber-600 text-white text-xs">복구</button>
          <button onClick={discardDraft} className="px-2 py-0.5 rounded border border-amber-400 text-xs">버리기</button>
        </div>
      )}
      {isPublished && dirty && !recovery && (
        <div className="px-4 py-1.5 text-xs border-b" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
          발행된 글이라 자동으로 서버에 올리지 않아요. 변경 내용은 이 브라우저에 임시저장돼 있어요. 반영하려면 Cmd/Ctrl+S.
        </div>
      )}

      {/* Editor Area */}
      <div ref={areaRef} className="flex-1 flex overflow-hidden">
        {showToc && headings.length > 0 && viewMode !== 'preview' && (
          <div className="hidden md:block w-56 border-r overflow-y-auto py-4 px-3 shrink-0"
            style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
            <div className="text-xs font-semibold uppercase mb-3" style={{ color: 'var(--text-secondary)' }}>Contents</div>
            {headings.map((h, i) => (
              <button key={i} type="button" onClick={() => scrollToHeading(h, i)}
                className="block w-full text-left text-sm py-1 truncate hover:text-primary-600"
                style={{
                  paddingLeft: `${(h.level - 1) * 0.75}rem`,
                  color: 'var(--text-secondary)',
                  fontSize: h.level === 1 ? '0.875rem' : '0.8125rem',
                  fontWeight: h.level === 1 ? 600 : 400,
                }}>
                {h.text}
              </button>
            ))}
          </div>
        )}

        {viewMode === 'wysiwyg' && (
          <NotionEditor content={form.content} onChange={handleContentChange} onImageUpload={handleImageUpload}
            onReady={ed => { tiptapRef.current = ed }} />
        )}
        {viewMode === 'split' && (
          <SplitEditor content={form.content} onChange={handleContentChange} onImageUpload={handleImageUpload} editorRef={mdRef} />
        )}
        {viewMode === 'source' && (
          <div className="flex-1 overflow-hidden">
            <MarkdownEditor ref={mdRef} value={form.content} onChange={handleContentChange} onImageUpload={handleImageUpload} />
          </div>
        )}
        {viewMode === 'preview' && (
          <div className="flex-1 overflow-y-auto">
            <article className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
              <h1 className="text-2xl sm:text-3xl font-bold mb-2" style={{ color: 'var(--text)' }}>{form.title || '제목 없음'}</h1>
              {form.summary && <p className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>{form.summary}</p>}
              <SummaryCard card={cardPayload(form.summary_card).value} />
              <div data-toc-root><MarkdownRenderer content={form.content} /></div>
              <PostQuiz quiz={quizPayload(form.quiz).value} />
            </article>
          </div>
        )}
      </div>

      {/* Template Modal */}
      {showTemplates && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setShowTemplates(false)}>
          <div className="w-full max-w-lg rounded-2xl p-6 max-h-[80vh] overflow-y-auto" style={{ background: 'var(--card-bg)' }}
            onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-4" style={{ color: 'var(--text)' }}>템플릿 고르기</h3>
            {templates.length === 0 && <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>등록된 템플릿이 없어요.</p>}
            <div className="space-y-3">
              {templates.map(t => (
                <button key={t.id} onClick={() => pickTemplate(t)}
                  className="w-full text-left p-4 rounded-xl border hover:shadow-md transition-all" style={{ borderColor: 'var(--border)' }}>
                  <h4 className="font-semibold" style={{ color: 'var(--text)' }}>{t.name}</h4>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{t.description}</p>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        isOpen={Boolean(pendingTemplate)}
        title="템플릿으로 바꿀까요?"
        message={`지금 쓴 본문(${form.content.trim().length.toLocaleString()}자)이 템플릿 내용으로 바뀌어요. 되돌릴 수 없어요.`}
        confirmLabel="바꾸기"
        variant="danger"
        onConfirm={() => applyTemplate(pendingTemplate)}
        onCancel={() => setPendingTemplate(null)}
      />

      <PublishChecklist
        open={showChecklist}
        onClose={() => setShowChecklist(false)}
        onConfirm={confirmPublish}
        form={form}
        onChange={updateForm}
        categories={categories}
        allTags={allTags}
        onTagCreated={t => setAllTags(prev => [...prev, t])}
        coverUrl={coverUrl}
        isNew={isNew}
        isPublished={isPublished}
        busy={saving}
      />

      {pendingNav && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={() => setPendingNav(null)} />
          <div role="alertdialog" aria-modal="true" aria-labelledby="leave-title"
            className="relative max-w-sm w-full rounded-2xl p-6 shadow-2xl border"
            style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
            onKeyDown={e => { if (e.key === 'Escape') setPendingNav(null) }}>
            <h3 id="leave-title" className="text-base font-semibold mb-2" style={{ color: 'var(--text)' }}>저장하지 않은 변경이 있어요</h3>
            <p className="text-sm mb-5" style={{ color: 'var(--text-secondary)' }}>
              {isPublished ? '발행된 글이라 서버에는 아직 반영되지 않았어요.' : '서버에 아직 저장되지 않았어요.'} 그냥 나가도 이 브라우저에 임시저장본이 남아요.
            </p>
            <div className="flex flex-wrap justify-end gap-2">
              <button autoFocus onClick={() => setPendingNav(null)} className="px-3 py-2 text-sm rounded-lg border"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>계속 쓰기</button>
              <button onClick={leaveWithoutSave} className="px-3 py-2 text-sm rounded-lg border"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>그냥 나가기</button>
              <button onClick={saveAndLeave} disabled={saving}
                className="px-3 py-2 text-sm font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50">
                {isPublished ? '반영하고 나가기' : '저장하고 나가기'}
              </button>
            </div>
          </div>
        </div>
      )}

      <PostExtrasPanel open={showExtras} onClose={() => setShowExtras(false)} form={form} onChange={updateForm} slug={slug} />

      <PostLinkModal isOpen={showLinkModal} onClose={() => setShowLinkModal(false)} onInsert={handleInsertLink} />
    </motion.div>
  )
}
