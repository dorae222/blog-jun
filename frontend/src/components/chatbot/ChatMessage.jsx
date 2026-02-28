import { Link } from 'react-router-dom'

export default function ChatMessage({ role, content, sources = [] }) {
  const isUser = role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className="max-w-[80%]">
        <div
          className={`px-3 py-2 rounded-xl text-sm ${
            isUser ? 'bg-primary-600 text-white' : ''
          }`}
          style={!isUser ? { background: 'var(--bg-secondary)' } : {}}
        >
          {content}
        </div>
        {sources?.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {sources.map((s, i) => (
              <Link
                key={i}
                to={`/post/${s.slug}`}
                className="text-xs text-primary-600 hover:underline"
              >
                {s.title}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
