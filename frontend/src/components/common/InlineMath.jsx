import { useMemo } from 'react'
import katex from 'katex'

// $...$ 인라인 수식을 KaTeX로 렌더링하는 경량 컴포넌트
// summary 등 짧은 텍스트에 사용 (full MarkdownRenderer 대신)
const INLINE_MATH_RE = /\$([^$]+)\$/g

export default function InlineMath({ text, className, style }) {
  const html = useMemo(() => {
    if (!text || !INLINE_MATH_RE.test(text)) return null
    INLINE_MATH_RE.lastIndex = 0

    return text.replace(INLINE_MATH_RE, (_, expr) => {
      try {
        return katex.renderToString(expr.trim(), {
          throwOnError: false,
          output: 'html',
        })
      } catch {
        return `$${expr}$`
      }
    })
  }, [text])

  if (!html) return <span className={className} style={style}>{text}</span>

  return (
    <span
      className={className}
      style={style}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
