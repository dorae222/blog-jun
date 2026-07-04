import React, { useState, useMemo, useEffect, useRef, Component } from 'react'

import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeSlug from 'rehype-slug'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'
import BookmarkEmbed from '../common/BookmarkEmbed'
import PostLinkTooltip from './PostLinkTooltip'
import { OptimizedImage } from '../../utils/mediaVariants'

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
      return `[${display}](/post/${slug || target})`
    })
    .replace(/\[\[\[([^\]]*?)\]\]\]/g, (_, title) => {
      const slug = linkMap[title.toLowerCase()]
      return `[${title}](/post/${slug || title})`
    })
    .replace(/\[\[([^\]]*?)\|([^\]]*?)\]\]/g, (_, target, display) => {
      const slug = linkMap[target.toLowerCase()]
      return `[${display}](/post/${slug || target})`
    })
    .replace(/\[\[([^\]]*?)\]\]/g, (_, title) => {
      const slug = linkMap[title.toLowerCase()]
      return `[${title}](/post/${slug || title})`
    })
    // closing ** 뒤에 한국어가 바로 오면 bold 파싱 실패 → 공백 삽입
    .replace(/([^\s*])\*\*([\uAC00-\uD7AF])/g, '$1** $2')

  // remark-math v6: multi-line display math에서 $$는 반드시 독립 행이어야 함
  processed = processed.replace(/^\$\$(.+)$/gm, (match, rest) => {
    if (rest.trimEnd().endsWith('$$')) return match
    return '$$\n' + rest
  })
  processed = processed.replace(/^(.+)\$\$\s*$/gm, (match, content) => {
    if (content.trimStart().startsWith('$$')) return match
    return content + '\n$$'
  })

  // :::type ... ::: 콜아웃 블록 → HTML 변환 (SVG 아이콘)
  processed = processed.replace(
    /^:::(info|warning|tip|danger)\s*\n([\s\S]*?)^:::\s*$/gm,
    (_, type, content) => {
      const svgIcons = {
        info: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        tip: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>',
        danger: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
      }
      const colors = {
        info:    { hex: '#3b82f6', rgb: '59,130,246',  label: 'Note' },
        warning: { hex: '#f59e0b', rgb: '245,158,11',  label: 'Warning' },
        tip:     { hex: '#10b981', rgb: '16,185,129',  label: 'Tip' },
        danger:  { hex: '#ef4444', rgb: '239,68,68',   label: 'Caution' },
      }
      const c = colors[type] || colors.info
      const icon = svgIcons[type] || svgIcons.info
      return `<div class="callout callout-${type}" style="background:rgba(${c.rgb},0.06);border:1px solid rgba(${c.rgb},0.08);border-radius:12px;padding:1rem 1.25rem;margin:1rem 0">\n<div style="display:flex;align-items:center;gap:6px;font-weight:600;font-size:13px;color:${c.hex};margin-bottom:6px"><span style="display:inline-flex">${icon}</span><span>${c.label}</span></div>\n\n${content.trim()}\n\n</div>`
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
      mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' })
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
      className="my-4 flex justify-center max-w-full overflow-x-auto"
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

  const handleCopy = () => {
    navigator.clipboard.writeText(plainText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Mermaid 코드블록 → 다이어그램 렌더링
  if (lang === 'mermaid') {
    return <MermaidDiagram code={plainText} />
  }

  // Output 블록 — 코드 실행 결과 표시용
  if (lang === 'output') {
    return (
      <div className="relative group rounded-lg overflow-hidden my-2 -mt-4 max-w-full" style={{
        background: 'var(--output-bg)',
        border: '1px solid var(--border)'
      }}>
        <div className="flex items-center justify-between px-4 py-1.5 text-xs"
          style={{ color: 'var(--text-secondary)', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
          <span className="font-mono opacity-60">Output</span>
          <button onClick={handleCopy}
            className="opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 rounded hover:bg-gray-200">
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        <pre className="px-4 pb-3 pt-1 overflow-x-auto m-0 rounded-none max-w-full"
          style={{ fontSize: '0.85em', lineHeight: '1.6' }}>
          {children}
        </pre>
      </div>
    )
  }

  return (
    <div className="relative group rounded-xl overflow-hidden my-6 max-w-full" style={{ background: 'var(--code-bg)' }}>
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
      <pre className="p-4 overflow-x-auto text-sm leading-relaxed m-0 rounded-none max-w-full">
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

  useEffect(() => {
    if (!zoomed) return
    const handleEsc = (e) => { if (e.key === 'Escape') setZoomed(false) }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [zoomed])

  if (broken) return null

  return (
    <>
      <OptimizedImage
        src={src}
        alt={alt || ''}
        loading="lazy"
        onClick={() => setZoomed(true)}
        onError={() => setBroken(true)}
        className="rounded-lg cursor-zoom-in max-w-full mx-auto hover:shadow-lg transition-shadow"
        style={{ maxHeight: '70vh' }}
        sizes="(max-width: 768px) 100vw, 896px"
      />
      {zoomed && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center cursor-zoom-out p-8"
          onClick={() => setZoomed(false)}
        >
          <img
            src={src}
            alt={alt || ''}
            className="object-contain rounded-lg"
            style={{ maxWidth: '90vw', maxHeight: '90vh' }}
          />
        </div>
      )}
    </>
  )
}

export default function MarkdownRenderer({ content, postLinks = [] }) {
  const processed = useMemo(() => preprocessContent(content, postLinks), [content, postLinks])

  return (
    <ErrorBoundary>
      <div className="prose max-w-none min-w-0 break-words sm:prose-lg">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeRaw, rehypeSlug, rehypeKatex, rehypeHighlight]}
          components={{
            pre: PreBlock,
            code: InlineCode,
            img: ({ src, alt }) => {
              // Figure N: 캡션 패턴 → <figure> + <figcaption> 렌더링
              const figMatch = alt?.match(/^Figure\s+(\d+):\s*(.+)$/)
              if (figMatch) {
                return (
                  <figure className="my-6 text-center">
                    <ImageWithZoom src={src} alt={alt} />
                    <figcaption className="mt-2 text-xs italic"
                      style={{ color: 'var(--text-secondary)' }}>
                      {alt}
                    </figcaption>
                  </figure>
                )
              }
              return <ImageWithZoom src={src} alt={alt} />
            },
            a: ({ href, children }) => {
              if (href?.startsWith('/post/')) {
                const slug = href.replace('/post/', '')
                const linkData = postLinks.find(l => l.slug === slug)
                return <PostLinkTooltip href={href} linkData={linkData}>{children}</PostLinkTooltip>
              }
              return (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline break-words">
                  {children}
                </a>
              )
            },
            p: ({ children }) => {
              const arr = React.Children.toArray(children)
              if (arr.length === 1 && arr[0]?.props?.href && !arr[0].props.href.startsWith('/')) {
                const text = extractPlainText(arr[0].props.children)
                if (text === arr[0].props.href || text.length < 100) {
                  return <BookmarkEmbed url={arr[0].props.href} />
                }
              }
              return <p>{children}</p>
            },
            table: ({ children }) => (
              <div className="relative overflow-x-auto my-4 max-w-full">
                <table className="min-w-full text-sm">{children}</table>
                <div className="absolute right-0 top-0 bottom-0 w-6 bg-gradient-to-l from-[var(--bg)] to-transparent pointer-events-none md:hidden" />
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
