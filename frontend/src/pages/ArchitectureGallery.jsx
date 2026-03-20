import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { GitBranch, Grid3x3 } from 'lucide-react'
import ArchitectureCard from '../components/architecture/ArchitectureCard'
import { getArchitectures, getArchitectureConcepts } from '../api/posts'

const CATEGORY_TABS = [
  { value: '', label: 'All' },
  { value: 'llm', label: 'LLM' },
  { value: 'ssm', label: 'SSM' },
  { value: 'diffusion', label: 'Diffusion' },
  { value: 'vision', label: 'Vision' },
  { value: 'multimodal', label: 'Multimodal' },
  { value: 'agent', label: 'Agent' },
]

const DECODER_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'dense', label: 'Dense' },
  { value: 'sparse_moe', label: 'MoE' },
  { value: 'sparse_hybrid', label: 'Hybrid' },
  { value: 'ssm', label: 'SSM' },
  { value: 'diffusion_unet', label: 'U-Net' },
  { value: 'diffusion_dit', label: 'DiT' },
  { value: 'vision_encoder', label: 'Vision Enc' },
  { value: 'multimodal', label: 'Multimodal' },
  { value: 'technique', label: 'Technique' },
]

export default function ArchitectureGallery() {
  const navigate = useNavigate()
  const [entries, setEntries] = useState([])
  const [concepts, setConcepts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterCategory, setFilterCategory] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterConcept, setFilterConcept] = useState('')

  useEffect(() => {
    getArchitectureConcepts()
      .then((r) => setConcepts(r.data.results || r.data || []))
      .catch(console.error)
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = {}
    if (filterCategory) params.architecture_category = filterCategory
    if (filterType) params.decoder_type = filterType
    if (filterConcept) params.concept = filterConcept
    getArchitectures(params)
      .then((r) => setEntries(r.data.results || r.data || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [filterCategory, filterType, filterConcept])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-7xl mx-auto px-4 py-12"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-3xl font-bold" style={{ color: 'var(--text)' }}>
          Architecture Gallery
        </h1>
        <button
          onClick={() => navigate('/architectures/tree')}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm hover:bg-gray-50 transition-colors"
          style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
        >
          <GitBranch size={16} /> 트리 보기
        </button>
      </div>
      <p className="text-sm mb-8" style={{ color: 'var(--text-secondary)' }}>
        AI 아키텍처 비교 갤러리 — LLM, SSM, Diffusion, Vision, Multimodal, Agent
      </p>

      {/* Category Tabs */}
      <div className="flex flex-wrap gap-4 mb-6">
        {/* 데스크톱 탭 */}
        <div className="hidden md:flex gap-1 p-1 rounded-xl" style={{ background: 'var(--bg-secondary)' }}>
          {CATEGORY_TABS.map((t) => (
            <button
              key={t.value}
              onClick={() => setFilterCategory(t.value)}
              className={`text-sm px-4 py-1.5 rounded-lg font-medium transition-all ${
                filterCategory === t.value
                  ? 'bg-white shadow-sm text-primary-600'
                  : 'hover:bg-white/50'
              }`}
              style={filterCategory !== t.value ? { color: 'var(--text-secondary)' } : {}}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* 모바일 드롭다운 */}
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="md:hidden text-sm px-3 py-1.5 rounded-lg border"
          style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
        >
          {CATEGORY_TABS.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
      </div>

      {/* Sub-filters: decoder_type + concepts */}
      <div className="flex flex-wrap gap-4 mb-8">
        <div className="flex flex-wrap gap-1.5">
          {DECODER_TYPES.filter(t => {
            if (!filterCategory) return ['', 'dense', 'sparse_moe', 'sparse_hybrid'].includes(t.value)
            return true
          }).map((t) => (
            <button
              key={t.value}
              onClick={() => setFilterType(t.value)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                filterType === t.value
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'hover:border-primary-400'
              }`}
              style={
                filterType !== t.value
                  ? { borderColor: 'var(--border)', color: 'var(--text-secondary)' }
                  : {}
              }
            >
              {t.label}
            </button>
          ))}
        </div>

        {concepts.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => setFilterConcept('')}
              className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                !filterConcept
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'hover:border-primary-400'
              }`}
              style={
                filterConcept
                  ? { borderColor: 'var(--border)', color: 'var(--text-secondary)' }
                  : {}
              }
            >
              All Concepts
            </button>
            {concepts.map((c) => (
              <button
                key={c.slug}
                onClick={() => setFilterConcept(c.slug)}
                className="text-xs px-2.5 py-1 rounded-full border transition-colors"
                style={
                  filterConcept === c.slug
                    ? { backgroundColor: c.color + '20', color: c.color, borderColor: c.color }
                    : { borderColor: 'var(--border)', color: 'var(--text-secondary)' }
                }
              >
                {c.abbreviation || c.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="rounded-2xl animate-pulse"
              style={{ background: 'var(--bg-secondary)', height: '320px' }}
            />
          ))}
        </div>
      ) : entries.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24">
          <p className="text-lg" style={{ color: 'var(--text-secondary)' }}>
            조건에 맞는 아키텍처가 없습니다.
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
          {entries.map((entry) => (
            <ArchitectureCard key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </motion.div>
  )
}
