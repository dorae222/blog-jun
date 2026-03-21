import { useState, useMemo, useEffect, useRef, Component } from 'react'
import { Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeSlug from 'rehype-slug'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'

// Obsidian 위키 링크를 내부 링크 또는 텍스트로 변환
function preprocessContent(raw, postLinks = []) {
  if (!raw) return ''

  const linkMap = {}
  postLinks.forEach(link => {
    linkMap[link.link_text?.toLowerCase()] = link.slug
    linkMap[link.title?.toLowerCase()] = link.slug
  })

  let processed = raw
    .replace(/\[\[\[([^\]]*?)\|([^\]]*?)\]\]\]/g, (_, target, display) => {
      const slug = linkMap[target.toLowerCase()]
      return slug ? `[${display}](/post/${slug})` : display
    })
    .replace(/\[\[\[([^\]]*?)\]\]\]/g, (_, title) => {
      const slug = linkMap[title.toLowerCase()]
      return slug ? `[${title}](/post/${slug})` : title
    })
    .replace(/\[\[([^\]]*?)\|([^\]]*?)\]\]/g, (_, target, display) => {
      const slug = linkMap[target.toLowerCase()]
      return slug ? `[${display}](/post/${slug})` : display
    })
    .replace(/\[\[([^\]]*?)\]\]/g, (_, title) => {
      const slug = linkMap[title.toLowerCase()]
      return slug ? `[${title}](/post/${slug})` : title
    })
    .replace(/\)\*\*([\uAC00-\uD7AF])/g, ')** $1')

  // :::type ... ::: 콜아웃 블록 → HTML 변환
  processed = processed.replace(
    /^:::(info|warning|tip|danger)\s*\n([\s\S]*?)^:::\s*$/gm,
    (_, type, content) => {
      const colors = {
        info: { icon: 'ℹ️', border: '#3b82f6', bg: 'rgba(59,130,246,0.08)' },
        warning: { icon: '⚠️', border: '#f59e0b', bg: 'rgba(245,158,11,0.08)' },
        tip: { icon: '💡', border: '#10b981', bg: 'rgba(16,185,129,0.08)' },
        danger: { icon: '🚨', border: '#ef4444', bg: 'rgba(239,68,68,0.08)' },
      }
      const c = colors[type] || colors.info
      return `<div class="callout callout-${type}" style="border-left:4px solid ${c.border};background:${c.bg};border-radius:8px;padding:1rem 1rem 1rem 0.75rem;margin:1rem 0">\n<span style="margin-right:0.5rem">${c.icon}</span>\n\n${content.trim()}\n\n</div>`
    }
  )

  return processed
}

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 rounded-lg border border-red-200 bg-red-50 text-red-700 text-sm">
          콘텐츠를 렌더링하는 중 오류가 발생했습니다.
        </div>
      )
    }
    return this.props.children
  }
}

function extractPlainText(children) {
  if (typeof children === 'string') return children
  if (Array.isArray(children)) return children.map(extractPlainText).join('')
  if (children?.props?.children) return extractPlainText(children.props.children)
  return ''
}

// Mermaid 렌더링 컴포넌트
function MermaidDiagram({ code }) {
  const containerRef = useRef(null)
  const [svg, setSvg] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!code) return
    import('mermaid').then(({ default: mermaid }) => {
      mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' })
      const id = `mermaid-view-${Date.now()}`
      mermaid.render(id, code)
        .then(({ svg }) => { setSvg(svg); setError(null) })
        .catch(err => { setError(err.message); setSvg('') })
    })
  }, [code])

  if (error) {
    return <div className="text-red-500 text-sm p-2">Mermaid error: {error}</div>
  }
  if (!svg) {
    return <div className="text-gray-400 text-sm p-2">Loading diagram...</div>
  }

  return (
    <div
      ref={containerRef}
      className="my-4 flex justify-center"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}

// 코드블록 전담 — pre 컴포넌트
function PreBlock({ children }) {
  const [copied, setCopied] = useState(false)

  const codeProps = children?.props ?? {}
  const lang = /language-(\w+)/.exec(codeProps.className || '')?.[1] || ''
  const plainText = extractPlainText(codeProps.children).trim()

  // Mermaid 코드블록 → 다이어그램 렌더링
  if (lang === 'mermaid') {
    return <MermaidDiagram code={plainText} />
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(plainText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group rounded-xl overflow-hidden my-6" style={{ background: 'var(--code-bg)' }}>
      <div
        className="flex items-center justify-between px-4 py-2 border-b text-xs"
        style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
      >
        <span className="font-mono opacity-60">{lang || 'code'}</span>
        <button
          onClick={handleCopy}
          className="opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 rounded hover:bg-gray-200"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-sm leading-relaxed m-0 rounded-none">
        {children}
      </pre>
    </div>
  )
}

function InlineCode({ children, className, node, ...props }) {
  return (
    <code
      className={className}
      style={!className ? { background: 'var(--code-bg)', padding: '0.15em 0.4em', borderRadius: '4px', fontWeight: 400 } : undefined}
      {...props}
    >
      {children}
    </code>
  )
}

function ImageWithZoom({ src, alt }) {
  const [zoomed, setZoomed] = useState(false)
  const [broken, setBroken] = useState(false)

  if (broken) return null

  return (
    <>
      <img
        src={src}
        alt={alt || ''}
        loading="lazy"
        onClick={() => setZoomed(true)}
        onError={() => setBroken(true)}
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

function SmartLink({ href, children }) {
  if (href?.startsWith('/post/')) {
    return (
      <Link to={href} className="text-primary-600 hover:underline">
        {children}
      </Link>
    )
  }
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
      {children}
    </a>
  )
}

export default function MarkdownRenderer({ content, postLinks = [] }) {
  const processed = useMemo(() => preprocessContent(content, postLinks), [content, postLinks])

  return (
    <ErrorBoundary>
      <div className="prose prose-lg max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeRaw, rehypeSlug, rehypeKatex, rehypeHighlight]}
          components={{
            pre: PreBlock,
            code: InlineCode,
            img: ({ src, alt }) => <ImageWithZoom src={src} alt={alt} />,
            a: SmartLink,
            table: ({ children }) => (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full text-sm">{children}</table>
              </div>
            ),
          }}
        >
          {processed}
        </ReactMarkdown>
      </div>
    </ErrorBoundary>
  )
}
