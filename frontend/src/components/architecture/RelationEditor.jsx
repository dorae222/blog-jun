import { useState, useEffect } from 'react'
import { Plus, Trash2, ArrowRight } from 'lucide-react'
import { getArchitectures, createArchitectureRelation, deleteArchitectureRelation } from '../../api/posts'

const RELATION_TYPES = [
  { value: 'evolved_from', label: '발전 (Evolved From)' },
  { value: 'inspired_by', label: '영향 (Inspired By)' },
  { value: 'variant_of', label: '변형 (Variant Of)' },
  { value: 'technique_used', label: '기법 적용 (Technique Used)' },
]

export default function RelationEditor({ slug, relations = [], onUpdate }) {
  const [allEntries, setAllEntries] = useState([])
  const [newRelation, setNewRelation] = useState({ to_slug: '', relation_type: 'evolved_from' })
  const [search, setSearch] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)

  useEffect(() => {
    getArchitectures({ page_size: 500 })
      .then(r => {
        const items = r.data.results || r.data || []
        setAllEntries(items.filter(e => e.slug !== slug))
      })
      .catch(() => {})
  }, [slug])

  const filtered = allEntries.filter(e =>
    e.name.toLowerCase().includes(search.toLowerCase()) ||
    e.slug.toLowerCase().includes(search.toLowerCase())
  ).slice(0, 10)

  const handleAdd = async () => {
    if (!newRelation.to_slug) return
    try {
      await createArchitectureRelation({
        from_slug: slug,
        to_slug: newRelation.to_slug,
        relation_type: newRelation.relation_type,
      })
      setNewRelation({ to_slug: '', relation_type: 'evolved_from' })
      setSearch('')
      if (onUpdate) onUpdate()
    } catch (err) {
      console.error('Failed to add relation:', err)
    }
  }

  const handleDelete = async (toSlug) => {
    try {
      await deleteArchitectureRelation({ from_slug: slug, to_slug: toSlug })
      if (onUpdate) onUpdate()
    } catch (err) {
      console.error('Failed to delete relation:', err)
    }
  }

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Relations</h4>

      {/* Existing relations */}
      {relations.length > 0 && (
        <div className="space-y-2">
          {relations.map((rel, i) => (
            <div
              key={i}
              className="flex items-center gap-2 text-sm p-2 rounded-lg"
              style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
            >
              <span className="font-medium" style={{ color: 'var(--text)' }}>{slug}</span>
              <ArrowRight size={12} />
              <span className="px-1.5 py-0.5 rounded text-xs" style={{ background: 'var(--border)' }}>
                {RELATION_TYPES.find(t => t.value === rel.relation_type)?.label || rel.relation_type}
              </span>
              <ArrowRight size={12} />
              <span className="font-medium" style={{ color: 'var(--text)' }}>
                {rel.to_slug || rel.to_name}
              </span>
              <button
                onClick={() => handleDelete(rel.to_slug)}
                className="ml-auto p-1 text-red-400 hover:text-red-600 transition-colors"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add new relation */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Target</label>
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setShowDropdown(true) }}
            onFocus={() => setShowDropdown(true)}
            placeholder="Search architecture..."
            className="w-full text-sm px-3 py-1.5 rounded border"
            style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
          />
          {showDropdown && search && filtered.length > 0 && (
            <div
              className="absolute z-10 top-full mt-1 w-full rounded-lg shadow-lg max-h-48 overflow-y-auto"
              style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}
            >
              {filtered.map(e => (
                <button
                  key={e.slug}
                  onClick={() => {
                    setNewRelation(prev => ({ ...prev, to_slug: e.slug }))
                    setSearch(e.name)
                    setShowDropdown(false)
                  }}
                  className="block w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  style={{ color: 'var(--text)' }}
                >
                  {e.name} <span style={{ color: 'var(--text-secondary)' }}>({e.slug})</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Type</label>
          <select
            value={newRelation.relation_type}
            onChange={e => setNewRelation(prev => ({ ...prev, relation_type: e.target.value }))}
            className="text-sm px-2 py-1.5 rounded border"
            style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
          >
            {RELATION_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <button
          onClick={handleAdd}
          disabled={!newRelation.to_slug}
          className="flex items-center gap-1 px-3 py-1.5 rounded text-sm bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          <Plus size={14} />
          Add
        </button>
      </div>
    </div>
  )
}
