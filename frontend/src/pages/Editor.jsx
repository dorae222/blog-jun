import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import MarkdownRenderer from '../components/blog/MarkdownRenderer'
import useAuth from '../hooks/useAuth'
import { getPost, createPost, updatePost, getCategories, getTags, getSeries, getTemplates, uploadImage } from '../api/posts'

export default function Editor() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [viewMode, setViewMode] = useState('split') // split, edit, preview
  const [showTemplates, setShowTemplates] = useState(false)
  const [templates, setTemplates] = useState([])
  const [categories, setCategories] = useState([])
  const [allTags, setAllTags] = useState([])
  const [allSeries, setAllSeries] = useState([])
  const textareaRef = useRef(null)

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
  })

  useEffect(() => {
    if (!user) { navigate('/login'); return }
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
        })
      })
    }
  }, [slug, user, navigate])

  // Auto-save every 30 seconds
  const autoSaveRef = useRef(null)
  useEffect(() => {
    if (!form.title || !form.content) return
    autoSaveRef.current = setInterval(() => {
      handleSave(true)
    }, 30000)
    return () => clearInterval(autoSaveRef.current)
  }, [form])

  const handleSave = useCallback(async (silent = false) => {
    try {
      const data = { ...form }
      if (!data.category) delete data.category
      if (!data.series) delete data.series

      if (slug) {
        await updatePost(slug, data)
        if (!silent) toast.success('Saved!')
      } else {
        const r = await createPost(data)
        if (!silent) toast.success('Created!')
        navigate(`/editor/${r.data.slug}`, { replace: true })
      }
    } catch (err) {
      toast.error('Save failed')
    }
  }, [form, slug, navigate])

  const handlePublish = async () => {
    setForm(prev => ({ ...prev, status: 'published' }))
    setTimeout(() => handleSave(), 0)
  }

  const handleImageDrop = async (e) => {
    e.preventDefault()
    const file = e.dataTransfer?.files?.[0] || e.target?.files?.[0]
    if (!file || !file.type.startsWith('image/')) return

    const formData = new FormData()
    formData.append('image', file)
    try {
      const { data } = await uploadImage(formData)
      const md = `![${file.name}](${data.image})`
      const textarea = textareaRef.current
      const start = textarea.selectionStart
      setForm(prev => ({
        ...prev,
        content: prev.content.slice(0, start) + md + prev.content.slice(start),
      }))
      toast.success('Image uploaded!')
    } catch {
      toast.error('Upload failed')
    }
  }

  const applyTemplate = (tmpl) => {
    setForm(prev => ({
      ...prev,
      content: tmpl.content_template,
      post_type: tmpl.post_type,
    }))
    setShowTemplates(false)
  }

  if (!user) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-[calc(100vh-4rem)] flex flex-col"
    >
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b" style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
        <input
          value={form.title}
          onChange={e => setForm(prev => ({ ...prev, title: e.target.value, slug: e.target.value.toLowerCase().replace(/[^a-z0-9가-힣]+/g, '-') }))}
          placeholder="Post title..."
          className="flex-1 text-lg font-semibold bg-transparent outline-none"
          style={{ color: 'var(--text)' }}
        />

        <select
          value={form.post_type}
          onChange={e => setForm(prev => ({ ...prev, post_type: e.target.value }))}
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
          onChange={e => setForm(prev => ({ ...prev, category: e.target.value }))}
          className="text-sm px-2 py-1 rounded border"
          style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
        >
          <option value="">Category</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>

        <select
          value={form.series}
          onChange={e => setForm(prev => ({ ...prev, series: e.target.value }))}
          className="text-sm px-2 py-1 rounded border"
          style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
        >
          <option value="">Series</option>
          {allSeries.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>

        <div className="flex rounded-lg border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
          {['edit', 'split', 'preview'].map(m => (
            <button
              key={m}
              onClick={() => setViewMode(m)}
              className={`px-3 py-1 text-xs ${viewMode === m ? 'bg-primary-600 text-white' : ''}`}
            >
              {m}
            </button>
          ))}
        </div>

        <button
          onClick={() => setShowTemplates(true)}
          className="text-sm px-3 py-1 rounded border hover:bg-gray-50"
          style={{ borderColor: 'var(--border)' }}
        >
          Templates
        </button>

        <button onClick={() => handleSave()} className="text-sm px-4 py-1.5 rounded bg-gray-200 hover:bg-gray-300">
          Save
        </button>

        <button onClick={handlePublish} className="text-sm px-4 py-1.5 rounded bg-primary-600 text-white hover:bg-primary-700">
          Publish
        </button>
      </div>

      {/* Editor Area */}
      <div className="flex-1 flex overflow-hidden">
        {viewMode !== 'preview' && (
          <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} flex flex-col border-r`} style={{ borderColor: 'var(--border)' }}>
            <textarea
              ref={textareaRef}
              value={form.content}
              onChange={e => setForm(prev => ({ ...prev, content: e.target.value }))}
              onDrop={handleImageDrop}
              onDragOver={e => e.preventDefault()}
              className="flex-1 p-6 resize-none outline-none font-mono text-sm"
              style={{ background: 'var(--bg)', color: 'var(--text)' }}
              placeholder="Write your markdown here..."
            />
          </div>
        )}
        {viewMode !== 'edit' && (
          <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} overflow-y-auto p-6`}>
            <MarkdownRenderer content={form.content} />
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
    </motion.div>
  )
}
