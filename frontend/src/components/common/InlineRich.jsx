import { Fragment, useMemo } from 'react'
import katex from 'katex'
import { splitInline } from '../../utils/inlineText'

/**
 * 짧은 한 줄 글(요약 카드, 확인 질문)에 섞인 `$수식$`과 `코드`만 그려 주는 컴포넌트.
 * 본문용 MarkdownRenderer 는 문단·링크 카드 같은 블록 처리가 붙어 있어 여기에는 무겁다.
 * 수식이 아닌 글자는 React 가 그대로 이스케이프한다(KaTeX 결과만 HTML 로 넣는다).
 */
export default function InlineRich({ text }) {
  const parts = useMemo(() => splitInline(text).map((p) => {
    if (p.type !== 'math') return p
    try {
      return { ...p, html: katex.renderToString(p.value, { throwOnError: false, output: 'html' }) }
    } catch {
      return { type: 'text', value: `$${p.value}$` }
    }
  }), [text])

  return parts.map((p, i) => {
    if (p.type === 'math') return <span key={i} dangerouslySetInnerHTML={{ __html: p.html }} />
    if (p.type === 'code') {
      return (
        <code key={i} className="rounded px-1 py-0.5 text-[0.9em]" style={{ background: 'var(--code-bg)' }}>{p.value}</code>
      )
    }
    return <Fragment key={i}>{p.value}</Fragment>
  })
}
