import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import ArchitectureCard from '../components/architecture/ArchitectureCard'
import { getArchitectures, getArchitectureConcepts } from '../api/posts'

const DECODER_TYPES = [
  { value: '', label: 'All' },
  { value: 'dense', label: 'Dense' },
  { value: 'sparse_moe', label: 'MoE' },
  { value: 'sparse_hybrid', label: 'Hybrid' },
]

export default function ArchitectureGallery() {
  const [entries, setEntries] = useState([])
  const [concepts, setConcepts] = useState([])
  const [loading, setLoading] = useState(true)
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
    if (filterType) params.decoder_type = filterType
    if (filterConcept) params.concept = filterConcept
    getArchitectures(params)
      .then((r) => setEntries(r.data.results || r.data || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [filterType, filterConcept])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-7xl mx-auto px-4 py-12"
    >
      <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text)' }}>
        Architecture Gallery
      </h1>
      <p className="text-sm mb-8" style={{ color: 'var(--text-secondary)' }}>
        LLM 아키텍처 비교 갤러리
      </p>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-8">
        <div className="flex flex-wrap gap-1.5">
          {DECODER_TYPES.map((t) => (
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
