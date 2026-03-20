import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft, ExternalLink, Pencil, GitBranch, Lock, Unlock,
  Cpu, Layers, Calendar, Building2,
} from 'lucide-react'
import MarkdownRenderer from '../components/blog/MarkdownRenderer'
import useAuth from '../hooks/useAuth'
import { getArchitecture } from '../api/posts'

const TYPE_LABELS = {
  dense: 'Dense',
  sparse_moe: 'Sparse MoE',
  sparse_hybrid: 'Sparse Hybrid',
  ssm: 'State Space Model',
  hybrid_ssm: 'Hybrid SSM',
  diffusion_unet: 'Diffusion (U-Net)',
  diffusion_dit: 'Diffusion (DiT)',
  vision_encoder: 'Vision Encoder',
  multimodal: 'Multimodal',
  technique: 'Technique',
}

const CATEGORY_COLORS = {
  llm: '#8b5cf6',
  ssm: '#06b6d4',
  diffusion: '#f59e0b',
  vision: '#ec4899',
  multimodal: '#fb7185',
  agent: '#84cc16',
  technique: '#9ca3af',
}

export default function ArchitectureDetail() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [entry, setEntry] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getArchitecture(slug)
      .then((r) => setEntry(r.data))
      .catch(() => navigate('/architectures'))
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    )
  }

  if (!entry) return null

  const catColor = CATEGORY_COLORS[entry.architecture_category] || '#8b5cf6'
  const specs = [
    { label: 'Parameters', value: entry.param_scale },
    { label: 'Context', value: entry.context_length },
    { label: 'Attention', value: entry.attention_type },
    { label: 'Normalization', value: entry.normalization },
    { label: 'Activation', value: entry.activation },
    { label: 'Positional Encoding', value: entry.position_encoding },
    { label: 'Hidden Dim', value: entry.hidden_dim },
    { label: 'Layers', value: entry.num_layers },
    { label: 'Heads', value: entry.num_heads },
    { label: 'Vocab Size', value: entry.vocab_size },
    { label: 'Experts', value: entry.num_experts },
    { label: 'Active Experts', value: entry.active_experts },
  ].filter((s) => s.value)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="max-w-4xl mx-auto px-4 py-8"
    >
      {/* 뒤로가기 + 편집 */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigate('/architectures')}
          className="flex items-center gap-1.5 text-sm hover:text-primary-600 transition-colors"
          style={{ color: 'var(--text-secondary)' }}
        >
          <ArrowLeft size={16} /> Gallery
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/architectures/tree')}
            className="flex items-center gap-1.5 text-sm px-3 py-1 rounded-lg border hover:bg-gray-50 transition-colors"
            style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
          >
            <GitBranch size={14} /> 트리에서 보기
          </button>
          {user && (
            <Link
              to={`/architectures/${slug}/edit`}
              className="flex items-center gap-1.5 text-sm px-3 py-1 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors"
            >
              <Pencil size={14} /> 편집
            </Link>
          )}
        </div>
      </div>

      {/* Hero */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <span
            className="text-xs font-semibold px-2.5 py-1 rounded-full uppercase"
            style={{ background: `${catColor}20`, color: catColor }}
          >
            {entry.architecture_category}
          </span>
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
          >
            {TYPE_LABELS[entry.decoder_type] || entry.decoder_type}
          </span>
          {entry.is_open_source !== undefined && (
            <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
              {entry.is_open_source ? <Unlock size={12} className="text-green-500" /> : <Lock size={12} className="text-red-400" />}
              {entry.is_open_source ? 'Open Source' : 'Closed'}
            </span>
          )}
        </div>

        <h1 className="text-4xl font-bold mb-2" style={{ color: 'var(--text)' }}>
          {entry.name}
        </h1>

        <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
          <span className="flex items-center gap-1.5">
            <Building2 size={14} /> {entry.organization}
          </span>
          {entry.release_date && (
            <span className="flex items-center gap-1.5">
              <Calendar size={14} /> {entry.release_date}
            </span>
          )}
          {entry.license_type && (
            <span className="flex items-center gap-1.5">
              <Layers size={14} /> {entry.license_type}
            </span>
          )}
        </div>
      </div>

      {/* Paper bookmark */}
      {entry.paper_url && (
        <a
          href={entry.paper_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3 p-4 rounded-xl border mb-8 hover:shadow-md transition-shadow"
          style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
        >
          <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${catColor}15` }}>
            <ExternalLink size={18} style={{ color: catColor }} />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>
              {entry.paper_url.includes('arxiv') ? `arXiv: ${entry.paper_url.split('/').pop()}` : 'Paper / Technical Report'}
            </p>
            <p className="text-xs truncate" style={{ color: 'var(--text-secondary)' }}>
              {entry.paper_url}
            </p>
          </div>
        </a>
      )}

      {/* Figure */}
      {entry.figure_url && (
        <div className="mb-8 rounded-xl overflow-hidden border" style={{ borderColor: 'var(--border)' }}>
          <div className="p-6" style={{ background: 'var(--bg-secondary)' }}>
            <img
              src={entry.figure_url}
              alt={`${entry.name} architecture diagram`}
              className="w-full max-h-96 object-contain"
            />
          </div>
        </div>
      )}

      {/* Specs Grid */}
      {specs.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-8">
          {specs.map((s) => (
            <div
              key={s.label}
              className="p-3 rounded-xl"
              style={{ background: 'var(--bg-secondary)' }}
            >
              <p className="text-xs mb-0.5" style={{ color: 'var(--text-secondary)' }}>
                {s.label}
              </p>
              <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
                {s.value}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Concepts */}
      {entry.concepts?.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-8">
          {entry.concepts.map((c) => (
            <span
              key={c.id}
              className="text-sm px-3 py-1 rounded-full font-medium"
              style={{ backgroundColor: c.color + '20', color: c.color }}
            >
              {c.abbreviation || c.name}
            </span>
          ))}
        </div>
      )}

      {/* Description */}
      {entry.description && (
        <section className="mb-8">
          <h2
            className="text-xl font-bold mb-4 pb-2 border-b"
            style={{ color: 'var(--text)', borderColor: 'var(--border)' }}
          >
            Overview
          </h2>
          <MarkdownRenderer content={entry.description} />
        </section>
      )}

      {/* Key Detail */}
      {entry.key_detail && (
        <section className="mb-8">
          <h2
            className="text-xl font-bold mb-4 pb-2 border-b"
            style={{ color: 'var(--text)', borderColor: 'var(--border)' }}
          >
            핵심 아키텍처
          </h2>
          <MarkdownRenderer content={entry.key_detail} />
        </section>
      )}

      {/* Training Detail */}
      {entry.training_detail && (
        <section className="mb-8">
          <h2
            className="text-xl font-bold mb-4 pb-2 border-b"
            style={{ color: 'var(--text)', borderColor: 'var(--border)' }}
          >
            학습 상세
          </h2>
          <MarkdownRenderer content={entry.training_detail} />
        </section>
      )}

      {/* Relations */}
      {(entry.parent_relations?.length > 0 || entry.child_relations?.length > 0) && (
        <section className="mb-8">
          <h2
            className="text-xl font-bold mb-4 pb-2 border-b"
            style={{ color: 'var(--text)', borderColor: 'var(--border)' }}
          >
            관련 아키텍처
          </h2>
          <div className="space-y-2">
            {entry.parent_relations?.map((rel) => (
              <Link
                key={rel.id}
                to={`/architectures/${rel.from_slug}`}
                className="flex items-center gap-2 p-3 rounded-lg border hover:shadow-sm transition-shadow"
                style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
              >
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                  ← {rel.relation_type === 'evolved_from' ? '발전' : rel.relation_type === 'inspired_by' ? '영향' : rel.relation_type === 'technique_used' ? '기법' : '변형'}
                </span>
                <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                  {rel.from_name}
                </span>
                {rel.description && (
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                    — {rel.description}
                  </span>
                )}
              </Link>
            ))}
            {entry.child_relations?.map((rel) => (
              <Link
                key={rel.id}
                to={`/architectures/${rel.to_slug}`}
                className="flex items-center gap-2 p-3 rounded-lg border hover:shadow-sm transition-shadow"
                style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
              >
                <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                  → {rel.relation_type === 'evolved_from' ? '후속' : rel.relation_type === 'inspired_by' ? '영향줌' : rel.relation_type === 'technique_used' ? '적용됨' : '변형'}
                </span>
                <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                  {rel.to_name}
                </span>
                {rel.description && (
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                    — {rel.description}
                  </span>
                )}
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Code URL */}
      {entry.code_url && (
        <a
          href={entry.code_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm text-primary-600 hover:underline mb-8"
        >
          <ExternalLink size={14} /> 코드 보기
        </a>
      )}
    </motion.div>
  )
}
