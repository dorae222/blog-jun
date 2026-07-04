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
      <code className="break-words rounded px-1.5 py-0.5 text-[0.92em]" style={{ background: 'var(--code-bg)' }} {...props}>
        {children}
      </code>
    )
  }

  return (
    <div className="relative group my-5 max-w-full overflow-hidden rounded-lg" style={{ background: 'var(--code-bg)' }}>
      <div className="flex items-center justify-between gap-3 border-b px-3 py-2 text-xs sm:px-4" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
        <span className="font-mono">{lang}</span>
        <button
          onClick={handleCopy}
          className="min-h-8 rounded px-2 py-1 transition-opacity sm:opacity-0 sm:group-hover:opacity-100 hover:bg-gray-200 dark:hover:bg-gray-700"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="max-w-full overflow-x-auto p-3 text-[0.82rem] leading-relaxed sm:p-4 sm:text-sm">
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
        className="mx-auto h-auto max-w-full cursor-zoom-in rounded-lg transition-shadow hover:shadow-lg"
      />
      {zoomed && (
        <div
          className="fixed inset-0 z-50 flex cursor-zoom-out items-center justify-center bg-black/80 p-3 sm:p-8"
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
    <div className="blog-prose prose max-w-none dark:prose-invert sm:prose-lg">
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
            <div className="my-5 max-w-full overflow-x-auto rounded-lg border" style={{ borderColor: 'var(--border)' }}>
              <table className="min-w-full text-sm">{children}</table>
            </div>
          ),
        }}
      />
    </div>
  )
}
