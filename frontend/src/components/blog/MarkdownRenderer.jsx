import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'

function CodeBlock({ children, className, ...props }) {
  const [copied, setCopied] = useState(false)
  const match = /language-(\w+)/.exec(className || '')
  const lang = match?.[1] || ''
  const code = String(children).replace(/\n$/, '')

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (!match) {
    return (
      <code className="px-1.5 py-0.5 rounded text-sm" style={{ background: 'var(--code-bg)' }} {...props}>
        {children}
      </code>
    )
  }

  return (
    <div className="relative group rounded-xl overflow-hidden my-4" style={{ background: 'var(--code-bg)' }}>
      <div className="flex items-center justify-between px-4 py-2 border-b text-xs" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
        <span className="font-mono">{lang}</span>
        <button
          onClick={handleCopy}
          className="opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 rounded hover:bg-gray-200"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-sm">
        <code className={className} {...props}>{children}</code>
      </pre>
    </div>
  )
}

function ImageWithZoom({ src, alt }) {
  const [zoomed, setZoomed] = useState(false)

  return (
    <>
      <img
        src={src}
        alt={alt || ''}
        loading="lazy"
        onClick={() => setZoomed(true)}
        className="rounded-lg cursor-zoom-in max-w-full mx-auto hover:shadow-lg transition-shadow"
      />
      {zoomed && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center cursor-zoom-out p-8"
          onClick={() => setZoomed(false)}
        >
          <img
            src={src}
            alt={alt || ''}
            className="max-w-full max-h-full object-contain rounded-lg"
          />
        </div>
      )}
    </>
  )
}

export default function MarkdownRenderer({ content }) {
  return (
    <div className="prose prose-lg max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkMath, remarkGfm]}
        rehypePlugins={[rehypeKatex, rehypeHighlight]}
        components={{
          code: CodeBlock,
          img: ({ src, alt }) => <ImageWithZoom src={src} alt={alt} />,
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full text-sm">{children}</table>
            </div>
          ),
        }}
      />
    </div>
  )
}
