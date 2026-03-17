import { useState, useMemo, Component } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeSlug from 'rehype-slug'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'

// Obsidian 위키 링크 등 비표준 마크다운을 표준으로 변환
function preprocessContent(raw) {
  if (!raw) return ''
  return raw
    // [[[Title|Display]]] → Display
    .replace(/\[\[\[([^\]]*?)\|([^\]]*?)\]\]\]/g, '$2')
    // [[[Title]]] → Title
    .replace(/\[\[\[([^\]]*?)\]\]\]/g, '$1')
    // [[Title|Display]] → Display
    .replace(/\[\[([^\]]*?)\|([^\]]*?)\]\]/g, '$2')
    // [[Title]] → Title
    .replace(/\[\[([^\]]*?)\]\]/g, '$1')
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

// rehypeHighlight가 생성한 highlight 트리에서 plain text 재귀 추출 (복사용)
function extractPlainText(children) {
  if (typeof children === 'string') return children
  if (Array.isArray(children)) return children.map(extractPlainText).join('')
  if (children?.props?.children) return extractPlainText(children.props.children)
  return ''
}

// 코드블록(block code) 전담 — pre 컴포넌트로 사용
function PreBlock({ children }) {
  const [copied, setCopied] = useState(false)

  // children은 rehypeHighlight가 처리한 <code className="language-xxx hljs">...</code>
  const codeProps = children?.props ?? {}
  const lang = /language-(\w+)/.exec(codeProps.className || '')?.[1] || ''
  const plainText = extractPlainText(codeProps.children).trim()

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

// inline code 전담 — code 컴포넌트로 사용 (className 없는 <code> 요소)
function InlineCode({ children, className, node, ...props }) {
  // className이 있으면 rehypeHighlight가 처리한 코드블록 내 code → PreBlock이 이미 담당
  // 여기서는 inline code만 처리
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

  // 깨진 이미지(Pasted image 등 404)는 렌더링하지 않음
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

export default function MarkdownRenderer({ content }) {
  const processed = useMemo(() => preprocessContent(content), [content])

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
        >
          {processed}
        </ReactMarkdown>
      </div>
    </ErrorBoundary>
  )
}
