import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import useAuth from '../hooks/useAuth'
import NotionEditor from '../components/editor/NotionEditor'
import {
  getArchitecture, createArchitecture, updateArchitecture,
  getArchitectureConcepts, uploadArchitectureFigure,
} from '../api/posts'
import { Save, CheckCircle, Upload } from 'lucide-react'

const DECODER_TYPES = [
  'dense', 'sparse_moe', 'sparse_hybrid', 'ssm', 'hybrid_ssm',
  'diffusion_unet', 'diffusion_dit', 'vision_encoder', 'multimodal', 'technique',
]

const CATEGORIES = ['llm', 'ssm', 'diffusion', 'vision', 'multimodal', 'agent', 'technique']

const BRANCHES = [
  '', 'encoder_only', 'encoder_decoder', 'decoder_only',
  'ssm', 'diffusion', 'vision', 'multimodal', 'agent',
]

const INITIAL_FORM = {
  name: '', slug: '', organization: '', release_date: '',
  decoder_type: 'dense', param_scale: '', context_length: '',
  attention_type: '', normalization: '', activation: '', position_encoding: '',
  vocab_size: '', hidden_dim: '', num_layers: '', num_heads: '',
  num_experts: '', active_experts: '',
  description: '', key_detail: '', training_detail: '',
  paper_url: '', code_url: '', license_type: '',
  architecture_category: 'llm', branch_type: '', is_open_source: true,
  concepts: [],
}

export default function ArchitectureEditor() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [form, setForm] = useState(INITIAL_FORM)
  const [saveStatus, setSaveStatus] = useState('saved') // saved | saving | changed
  const [allConcepts, setAllConcepts] = useState([])
  const [activeTab, setActiveTab] = useState('description')
  const autoSaveRef = useRef(null)

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    getArchitectureConcepts()
      .then(r => setAllConcepts(r.data.results || r.data || []))
      .catch(() => {})
    if (slug) {
      getArchitecture(slug).then(r => {
        const e = r.data
        setForm({
          name: e.name, slug: e.slug, organization: e.organization,
          release_date: e.release_date || '',
          decoder_type: e.decoder_type, param_scale: e.param_scale || '',
          context_length: e.context_length || '',
          attention_type: e.attention_type || '', normalization: e.normalization || '',
          activation: e.activation || '', position_encoding: e.position_encoding || '',
          vocab_size: e.vocab_size || '', hidden_dim: e.hidden_dim || '',
          num_layers: e.num_layers || '', num_heads: e.num_heads || '',
          num_experts: e.num_experts || '', active_experts: e.active_experts || '',
          description: e.description || '', key_detail: e.key_detail || '',
          training_detail: e.training_detail || '',
          paper_url: e.paper_url || '', code_url: e.code_url || '',
          license_type: e.license_type || '',
          architecture_category: e.architecture_category || 'llm',
          branch_type: e.branch_type || '', is_open_source: e.is_open_source ?? true,
          concepts: e.concepts?.map(c => c.slug) || [],
        })
      })
    }
  }, [slug, user, navigate])

  // Auto-save (30s debounce)
  useEffect(() => {
    if (!form.name) return
    clearInterval(autoSaveRef.current)
    autoSaveRef.current = setInterval(() => {
      if (saveStatus === 'changed') handleSave(true)
    }, 30000)
    return () => clearInterval(autoSaveRef.current)
  }, [form, saveStatus])

  const updateField = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }))
    setSaveStatus('changed')
  }

  const handleSave = useCallback(async (silent = false) => {
    setSaveStatus('saving')
    try {
      const data = { ...form }
      if (slug) {
        await updateArchitecture(slug, data)
        if (!silent) toast.success('저장 완료')
      } else {
        if (!data.slug) data.slug = data.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')
        const r = await createArchitecture(data)
        if (!silent) toast.success('생성 완료')
        navigate(`/architectures/${r.data.slug}/edit`, { replace: true })
      }
      setSaveStatus('saved')
    } catch (err) {
      setSaveStatus('changed')
      toast.error('저장 실패')
    }
  }, [form, slug, navigate])

  // Ctrl+S
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault()
        handleSave()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handleSave])

  // Figure upload
  const handleFigureUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file || !slug) return
    const fd = new FormData()
    fd.append('figure', file)
    try {
      await uploadArchitectureFigure(slug, fd)
      toast.success('Figure 업로드 완료')
    } catch {
      toast.error('Figure 업로드 실패')
    }
  }

  if (!user) return null

  const SAVE_INDICATOR = {
    saved: { text: '저장됨', icon: CheckCircle, color: '#10b981' },
    saving: { text: '저장 중...', icon: Save, color: '#f59e0b' },
    changed: { text: '변경사항 있음', icon: Save, color: '#6366f1' },
  }
  const si = SAVE_INDICATOR[saveStatus]

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-6xl mx-auto px-4 py-8"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
          {slug ? `Edit: ${form.name}` : 'New Architecture'}
        </h1>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs" style={{ color: si.color }}>
            <si.icon size={14} /> {si.text}
          </span>
          <button
            onClick={() => handleSave()}
            className="px-4 py-1.5 rounded-lg bg-primary-600 text-white text-sm hover:bg-primary-700"
          >
            저장
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* 좌측: 기본 정보 + 스펙 */}
        <div className="space-y-4">
          <div className="p-4 rounded-xl border space-y-3" style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>기본 정보</h3>
            <Input label="Name" value={form.name} onChange={v => updateField('name', v)} />
            <Input label="Slug" value={form.slug} onChange={v => updateField('slug', v)} />
            <Input label="Organization" value={form.organization} onChange={v => updateField('organization', v)} />
            <Input label="Release Date" value={form.release_date} onChange={v => updateField('release_date', v)} type="date" />
            <Input label="Paper URL" value={form.paper_url} onChange={v => updateField('paper_url', v)} />
            <Input label="Code URL" value={form.code_url} onChange={v => updateField('code_url', v)} />
            <Input label="License" value={form.license_type} onChange={v => updateField('license_type', v)} />
          </div>

          <div className="p-4 rounded-xl border space-y-3" style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>분류</h3>
            <Select label="Category" value={form.architecture_category} onChange={v => updateField('architecture_category', v)} options={CATEGORIES} />
            <Select label="Decoder Type" value={form.decoder_type} onChange={v => updateField('decoder_type', v)} options={DECODER_TYPES} />
            <Select label="Branch" value={form.branch_type} onChange={v => updateField('branch_type', v)} options={BRANCHES} />
            <label className="flex items-center gap-2 text-sm" style={{ color: 'var(--text)' }}>
              <input type="checkbox" checked={form.is_open_source} onChange={e => updateField('is_open_source', e.target.checked)} />
              Open Source
            </label>
          </div>

          <div className="p-4 rounded-xl border space-y-3" style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>스펙</h3>
            <Input label="Parameters" value={form.param_scale} onChange={v => updateField('param_scale', v)} />
            <Input label="Context Length" value={form.context_length} onChange={v => updateField('context_length', v)} />
            <Input label="Attention" value={form.attention_type} onChange={v => updateField('attention_type', v)} />
            <Input label="Normalization" value={form.normalization} onChange={v => updateField('normalization', v)} />
            <Input label="Activation" value={form.activation} onChange={v => updateField('activation', v)} />
            <Input label="Position Encoding" value={form.position_encoding} onChange={v => updateField('position_encoding', v)} />
            <Input label="Hidden Dim" value={form.hidden_dim} onChange={v => updateField('hidden_dim', v)} />
            <Input label="Layers" value={form.num_layers} onChange={v => updateField('num_layers', v)} />
            <Input label="Heads" value={form.num_heads} onChange={v => updateField('num_heads', v)} />
            <Input label="Vocab Size" value={form.vocab_size} onChange={v => updateField('vocab_size', v)} />
            <Input label="Experts" value={form.num_experts} onChange={v => updateField('num_experts', v)} />
            <Input label="Active Experts" value={form.active_experts} onChange={v => updateField('active_experts', v)} />
          </div>

          {slug && (
            <div className="p-4 rounded-xl border" style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
              <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text)' }}>Figure</h3>
              <label className="flex items-center gap-2 px-4 py-2 rounded-lg border cursor-pointer hover:bg-gray-50 transition-colors text-sm"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                <Upload size={14} /> Figure 업로드
                <input type="file" accept="image/*" onChange={handleFigureUpload} className="hidden" />
              </label>
            </div>
          )}
        </div>

        {/* 우측: 콘텐츠 에디터 */}
        <div className="lg:col-span-2 space-y-4">
          {/* 탭 */}
          <div className="flex gap-1 p-1 rounded-xl" style={{ background: 'var(--bg-secondary)' }}>
            {['description', 'key_detail', 'training_detail'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab ? 'bg-white shadow-sm text-primary-600' : 'hover:bg-white/50'
                }`}
                style={activeTab !== tab ? { color: 'var(--text-secondary)' } : {}}
              >
                {tab === 'description' ? 'Overview' : tab === 'key_detail' ? '핵심 아키텍처' : '학습 상세'}
              </button>
            ))}
          </div>

          {/* 에디터 영역 */}
          <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
            <div className="min-h-[500px]">
              <NotionEditor
                content={form[activeTab]}
                onChange={(md) => updateField(activeTab, md)}
              />
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// Helper components
function Input({ label, value, onChange, type = 'text' }) {
  return (
    <div>
      <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full text-sm px-2.5 py-1.5 rounded-lg border outline-none focus:border-primary-400"
        style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
      />
    </div>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full text-sm px-2.5 py-1.5 rounded-lg border outline-none"
        style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
      >
        {options.map(o => <option key={o} value={o}>{o || '(none)'}</option>)}
      </select>
    </div>
  )
}
