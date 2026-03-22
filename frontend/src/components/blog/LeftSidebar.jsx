import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ChevronRight, ChevronDown, Flame, TagIcon, Eye } from 'lucide-react'
import { getPopularPosts, getTags } from '../../api/posts'

const CATEGORY_TREE = [
  {
    key: 'ai', label: 'AI', color: '#FF6F00',
    subs: [
      { key: 'llm', label: 'LLM' },
      { key: 'ssm', label: 'SSM' },
      { key: 'diffusion', label: 'Diffusion' },
      { key: 'vision', label: 'Vision' },
      { key: 'multimodal', label: 'Multimodal' },
      { key: 'agent', label: 'Agent' },
      { key: 'technique', label: 'Technique' },
    ],
  },
  {
    key: 'cloud', label: 'Cloud', color: '#FF9900',
    subs: [
      { key: 'aws', label: 'AWS' },
      { key: 'docker', label: 'Docker' },
      { key: 'lxd', label: 'LXD' },
      { key: 'devops', label: 'DevOps' },
    ],
  },
  {
    key: 'data', label: 'Data Engineering', color: '#336791',
    subs: [
      { key: 'hadoop', label: 'Hadoop' },
      { key: 'spark', label: 'Spark' },
      { key: 'database', label: 'Database' },
      { key: 'pipeline', label: 'Pipeline' },
    ],
  },
]

export default function LeftSidebar({ category, sub, counts }) {
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState(category || null)
  const [popular, setPopular] = useState([])
  const [tags, setTags] = useState([])

  useEffect(() => {
    getPopularPosts(5).then((r) => setPopular(r.data || [])).catch(() => {})
    getTags().then((r) => {
      const list = r.data?.results || r.data || []
      setTags(list.sort((a, b) => (b.post_count || 0) - (a.post_count || 0)).slice(0, 15))
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (category) setExpanded(category)
  }, [category])

  return (
    <aside className="hidden lg:block w-56 shrink-0 sticky top-20 self-start space-y-6 pr-4">
      {/* 카테고리 트리 */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider mb-3"
          style={{ color: 'var(--text-secondary)' }}>
          카테고리
        </h3>
        <nav className="space-y-0.5">
          {CATEGORY_TREE.map((cat) => {
            const isExpanded = expanded === cat.key
            const catCount = counts?.[cat.key]?.count || 0
            return (
              <div key={cat.key}>
                <button
                  onClick={() => {
                    setExpanded(isExpanded ? null : cat.key)
                    navigate(`/posts/${cat.key}`)
                  }}
                  className="flex items-center gap-1.5 w-full px-2 py-1.5 text-sm rounded-lg transition-colors hover:bg-gray-50"
                  style={{
                    color: category === cat.key ? cat.color : 'var(--text)',
                    fontWeight: category === cat.key ? 600 : 400,
                  }}
                >
                  {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  <span className="flex-1 text-left">{cat.label}</span>
                  <span className="text-[11px] opacity-50">{catCount}</span>
                </button>
                {isExpanded && (
                  <div className="ml-5 space-y-0.5 mt-0.5">
                    {cat.subs.map((s) => {
                      const subCount = counts?.[cat.key]?.subs?.[s.key] || 0
                      const isActive = category === cat.key && sub === s.key
                      return (
                        <button
                          key={s.key}
                          onClick={() => navigate(`/posts/${cat.key}/${s.key}`)}
                          className="flex items-center gap-1 w-full px-2 py-1 text-xs rounded-lg transition-colors hover:bg-gray-50"
                          style={{
                            color: isActive ? cat.color : 'var(--text-secondary)',
                            fontWeight: isActive ? 600 : 400,
                          }}
                        >
                          <span className="w-1 h-1 rounded-full shrink-0"
                            style={{ background: isActive ? cat.color : 'var(--border)' }} />
                          <span className="flex-1 text-left">{s.label}</span>
                          <span className="text-[10px] opacity-50">{subCount}</span>
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </nav>
      </div>

      {/* 인기글 */}
      {popular.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5"
            style={{ color: 'var(--text-secondary)' }}>
            <Flame size={12} /> 인기글
          </h3>
          <div className="space-y-1.5">
            {popular.map((post, i) => (
              <Link
                key={post.slug}
                to={`/post/${post.slug}`}
                className="flex items-start gap-2 px-2 py-1.5 rounded-lg text-xs transition-colors hover:bg-gray-50"
              >
                <span className="text-primary-600/40 font-bold mt-px">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="line-clamp-2 leading-snug" style={{ color: 'var(--text)' }}>{post.title}</p>
                  <span className="flex items-center gap-0.5 mt-0.5"
                    style={{ color: 'var(--text-secondary)' }}>
                    <Eye size={9} /> {post.view_count}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* 태그 클라우드 */}
      {tags.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5"
            style={{ color: 'var(--text-secondary)' }}>
            <TagIcon size={12} /> 태그
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <Link
                key={tag.id}
                to={`/posts?q=${tag.name}`}
                className="text-[11px] px-2 py-0.5 rounded-full border transition-colors hover:bg-gray-50"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
              >
                {tag.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </aside>
  )
}
