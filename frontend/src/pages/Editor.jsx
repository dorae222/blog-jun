import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { Eye, Code, Columns, List, Check, Circle, Link2 } from 'lucide-react'
import PostLinkModal from '../components/editor/PostLinkModal'
import NotionEditor from '../components/editor/NotionEditor'
import SplitEditor from '../components/editor/SplitEditor'
import MarkdownEditor from '../components/editor/MarkdownEditor'
import useAuth from '../hooks/useAuth'
import { getPost, createPost, updatePost, getCategories, getTags, getSeries, getTemplates, uploadImage } from '../api/posts'

export default function Editor() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [showTemplates, setShowTemplates] = useState(false)
  const [showLinkModal, setShowLinkModal] = useState(false)
  const [templates, setTemplates] = useState([])
  const [categories, setCategories] = useState([])
  const [allTags, setAllTags] = useState([])
  const [allSeries, setAllSeries] = useState([])
  const [viewMode, setViewMode] = useState('wysiwyg') // wysiwyg | split | source
  const [showToc, setShowToc] = useState(false)
  const [headings, setHeadings] = useState([])
  const [errors, setErrors] = useState({})

  const [form, setForm] = useState({
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
    arxiv_url: '',
    venue: '',
    paper_year: null,
    paper_authors: '',
  })

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    if (!user.is_staff) { navigate('/'); return }
    getCategories().then(r => setCategories(r.data.results || r.data || []))
    getTags().then(r => setAllTags(r.data.results || r.data || []))
    getSeries().then(r => setAllSeries(r.data.results || r.data || []))
    getTemplates().then(r => setTemplates(r.data.results || r.data || [])).catch(() => {})
    if (slug) {
      getPost(slug).then(r => {
        const p = r.data
        setForm({
          title: p.title,
          slug: p.slug,
          content: p.content,
          summary: p.summary || '',
          category: p.category?.id || '',
          tags: p.tags?.map(t => t.id) || [],
          series: p.series?.id || '',
          series_order: p.series_order || 0,
          post_type: p.post_type,
          status: p.status,
          arxiv_url: p.arxiv_url || '',
          venue: p.venue || '',
          paper_year: p.paper_year || null,
          paper_authors: p.paper_authors || '',
        })
      })
    }
  }, [slug, user, navigate])

  const [saveStatus, setSaveStatus] = useState('saved')

  const autoSaveRef = useRef(null)
  useEffect(() => {
    if (!form.title || !form.content) return
    autoSaveRef.current = setInterval(() => {
      if (saveStatus === 'changed') handleSave(true)
    }, 30000)
    return () => clearInterval(autoSaveRef.current)
  }, [form, saveStatus])

  const updateForm = (updates) => {
    setForm(prev => ({ ...prev, ...updates }))
    setSaveStatus('changed')
    // Clear validation errors for changed fields
    setErrors(prev => {
      const next = { ...prev }
      Object.keys(updates).forEach(key => delete next[key])
      return next
    })
  }

  // 콘텐츠 변경 시 헤딩 추출 (TOC용)
  const handleContentChange = useCallback((markdown) => {
    updateForm({ content: markdown })
    // 헤딩 추출
    const matches = [...(markdown || '').matchAll(/^(#{1,3})\s+(.+)$/gm)]
    setHeadings(matches.map((m, i) => ({
      level: m[1].length,
      text: m[2].replace(/[*_`]/g, ''),
      id: `heading-${i}`,
    })))
  }, [])

  const validateForm = () => {
    const errs = {}
    if (!form.title.trim()) errs.title = '제목을 입력하세요'
    if (!form.content.trim()) errs.content = '내용을 입력하세요'
    if (!form.category) errs.category = '카테고리를 선택하세요'
    return errs
  }

  const handleSave = useCallback(async (silent = false, overrides = {}) => {
    if (!silent) {
      const validationErrors = validateForm()
      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors)
        toast.error('필수 항목을 확인하세요')
        return
      }
    }
    setSaveStatus('saving')
    try {
      const data = { ...form, ...overrides }
      if (!data.category) delete data.category
      if (!data.series) delete data.series

      if (slug) {
        await updatePost(slug, data)
        if (!silent) toast.success('저장됨')
      } else {
        const r = await createPost(data)
        if (!silent) toast.success('생성됨')
        navigate(`/editor/${r.data.slug}`, { replace: true })
      }
      setSaveStatus('saved')
    } catch (err) {
      setSaveStatus('changed')
      toast.error('저장 실패')
    }
  }, [form, slug, navigate])

  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault()
        handleSave()
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setShowLinkModal(true)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handleSave])

  useEffect(() => {
    const handler = (e) => { if (saveStatus === 'changed') { e.preventDefault(); e.returnValue = '' } }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [saveStatus])

  const handlePublish = () => handleSave(false, { status: 'published' })

  const handleImageUpload = useCallback(async (file) => {
    const formData = new FormData()
    formData.append('image', file)
    const { data } = await uploadImage(formData)
    return data.image
  }, [])

  const applyTemplate = (tmpl) => {
    setForm(prev => ({
      ...prev,
      content: tmpl.content_template,
      post_type: tmpl.post_type,
    }))
    setShowTemplates(false)
  }

  const handleInsertLink = useCallback((linkText) => {
    updateForm({ content: form.content + '\n' + linkText })
  }, [form.content])

  if (!user || !user.is_staff) return null

  const VIEW_MODES = [
    { id: 'wysiwyg', icon: Eye, label: 'WYSIWYG' },
    { id: 'split', icon: Columns, label: 'Split' },
    { id: 'source', icon: Code, label: 'Source' },
  ]

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-[calc(100vh-4rem)] flex flex-col"
    >
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b overflow-x-auto" style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
        <input
          value={form.title}
          onChange={e => updateForm({ title: e.target.value, slug: e.target.value.toLowerCase().replace(/[^a-z0-9가-힣]+/g, '-') })}
          placeholder="Post title..."
          className="flex-1 min-w-0 text-lg font-semibold bg-transparent outline-none"
          style={{ color: 'var(--text)', borderBottom: errors.title ? '2px solid #ef4444' : undefined }}
        />

        <select
          value={form.post_type}
          onChange={e => updateForm({ post_type: e.target.value })}
          className="text-sm px-2 py-1 rounded border"
          style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
        >
          <option value="article">Article</option>
          <option value="paper_review">Paper Review</option>
          <option value="tutorial">Tutorial</option>
          <option value="til">TIL</option>
          <option value="project">Project</option>
          <option value="activity_log">Activity Log</option>
        </select>

        <select
          value={form.category}
          onChange={e => updateForm({ category: e.target.value })}
          className="text-sm px-2 py-1 rounded border"
          style={{ borderColor: errors.category ? '#ef4444' : 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
        >
          <option value="">Category</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>

        <select
          value={form.series}
          onChange={e => updateForm({ series: e.target.value })}
          className="text-sm px-2 py-1 rounded border"
          style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
        >
          <option value="">Series</option>
          {allSeries.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>

        {/* Paper Review 메타데이터 (post_type 선택 시 표시) */}
        {form.post_type === 'paper_review' && (
          <>
            <input
              value={form.arxiv_url}
              onChange={e => updateForm({ arxiv_url: e.target.value })}
              placeholder="arXiv URL"
              className="text-sm px-2 py-1 rounded border w-40"
              style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
            />
            <input
              value={form.venue}
              onChange={e => updateForm({ venue: e.target.value })}
              placeholder="학회 (NeurIPS, ICML...)"
              className="text-sm px-2 py-1 rounded border w-32"
              style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
            />
            <input
              type="number"
              value={form.paper_year || ''}
              onChange={e => updateForm({ paper_year: e.target.value ? parseInt(e.target.value) : null })}
              placeholder="연도"
              className="text-sm px-2 py-1 rounded border w-20"
              style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
            />
          </>
        )}

        {/* View Mode Toggle */}
        <div className="flex items-center rounded border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
          {VIEW_MODES.map(mode => (
            <button
              key={mode.id}
              onClick={() => setViewMode(mode.id)}
              className="px-2 py-1 text-xs flex items-center gap-1 transition-colors"
              style={{
                background: viewMode === mode.id ? 'var(--bg)' : 'transparent',
                color: viewMode === mode.id ? 'var(--text)' : 'var(--text-secondary)',
                fontWeight: viewMode === mode.id ? 600 : 400,
              }}
              title={mode.label}
            >
              <mode.icon size={14} />
            </button>
          ))}
        </div>

        {/* TOC Toggle */}
        <button
          onClick={() => setShowToc(prev => !prev)}
          className="px-2 py-1 rounded border text-xs"
          style={{
            borderColor: 'var(--border)',
            background: showToc ? 'var(--bg)' : 'transparent',
            color: showToc ? 'var(--text)' : 'var(--text-secondary)',
          }}
          title="Table of Contents"
        >
          <List size={14} />
        </button>

        <button
          onClick={() => setShowLinkModal(true)}
          className="text-sm px-3 py-1 rounded border hover:bg-gray-50"
          style={{ borderColor: 'var(--border)' }}
          title="Insert post link (Ctrl+K)"
        >
          <Link2 size={14} />
        </button>

        <button
          onClick={() => setShowTemplates(true)}
          className="text-sm px-3 py-1 rounded border hover:bg-gray-50"
          style={{ borderColor: 'var(--border)' }}
        >
          Templates
        </button>

        <span className="text-xs shrink-0" style={{ color: 'var(--text-secondary)' }}>
          {(() => {
            const chars = form.content.trim().length
            return `${chars}자 · ${Math.max(1, Math.ceil(chars / 500))}분`
          })()}
        </span>

        <span className="inline-flex items-center gap-1 text-xs px-2 shrink-0" style={{
          color: saveStatus === 'saved' ? '#10b981' : saveStatus === 'saving' ? '#f59e0b' : '#6366f1'
        }}>
          {saveStatus === 'saved' ? <><Check size={12} /> 저장됨</> : saveStatus === 'saving' ? '저장 중...' : <><Circle size={8} className="fill-current" /> 변경사항</>}
        </span>

        <button
          onClick={() => handleSave()}
          disabled={saveStatus === 'saving'}
          className="text-sm px-4 py-1.5 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saveStatus === 'saving' ? '저장 중...' : 'Save'}
        </button>

        <button
          onClick={handlePublish}
          disabled={saveStatus === 'saving'}
          className="text-sm px-4 py-1.5 rounded bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saveStatus === 'saving' ? '저장 중...' : 'Publish'}
        </button>
      </div>

      {/* Editor Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* TOC Sidebar */}
        {showToc && headings.length > 0 && (
          <div
            className="w-56 border-r overflow-y-auto py-4 px-3 shrink-0"
            style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}
          >
            <div className="text-xs font-semibold uppercase mb-3" style={{ color: 'var(--text-secondary)' }}>
              Contents
            </div>
            {headings.map((h, i) => (
              <div
                key={i}
                className="text-sm py-1 cursor-pointer hover:opacity-80 truncate"
                style={{
                  paddingLeft: `${(h.level - 1) * 0.75}rem`,
                  color: 'var(--text-secondary)',
                  fontSize: h.level === 1 ? '0.875rem' : '0.8125rem',
                  fontWeight: h.level === 1 ? 600 : 400,
                }}
              >
                {h.text}
              </div>
            ))}
          </div>
        )}

        {/* Main Editor */}
        {viewMode === 'wysiwyg' && (
          <NotionEditor
            content={form.content}
            onChange={handleContentChange}
            onImageUpload={handleImageUpload}
          />
        )}
        {viewMode === 'split' && (
          <SplitEditor
            content={form.content}
            onChange={handleContentChange}
          />
        )}
        {viewMode === 'source' && (
          <div className="flex-1 overflow-hidden">
            <MarkdownEditor
              value={form.content}
              onChange={(val) => handleContentChange(val)}
            />
          </div>
        )}
      </div>

      {/* Template Modal */}
      {showTemplates && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setShowTemplates(false)}>
          <div
            className="w-full max-w-lg rounded-2xl p-6 max-h-[80vh] overflow-y-auto"
            style={{ background: 'var(--card-bg)' }}
            onClick={e => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold mb-4" style={{ color: 'var(--text)' }}>Choose Template</h3>
            <div className="space-y-3">
              {templates.map(t => (
                <button
                  key={t.id}
                  onClick={() => applyTemplate(t)}
                  className="w-full text-left p-4 rounded-xl border hover:shadow-md transition-all"
                  style={{ borderColor: 'var(--border)' }}
                >
                  <h4 className="font-semibold" style={{ color: 'var(--text)' }}>{t.name}</h4>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{t.description}</p>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Post Link Modal */}
      <PostLinkModal isOpen={showLinkModal} onClose={() => setShowLinkModal(false)} onInsert={handleInsertLink} />
    </motion.div>
  )
}
