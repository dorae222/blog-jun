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

  // remark-math v6: multi-line display math에서 $$는 반드시 독립 행이어야 함.
  //
  // 들여쓰기를 보존한다. 목록 항목 안의 수식은 항목 들여쓰기를 이어받아야 그 항목에
  // 붙는데, 여기서 0열로 내리면 그 자리에서 목록이 끊긴다. 실제로 그랬다 -
  // `  $$` 줄이 아래 두 번째 치환에 걸려 `"  " + "\n$$"`로 벌어졌고, 공백만 남은 줄이
  // 빈 줄이 되면서 4항목 목록이 ul(3) + ul(1)로 쪼개졌다.
  processed = processed.replace(/^([ \t]*)\$\$(.+)$/gm, (match, indent, rest) => {
    if (rest.trimEnd().endsWith('$$')) return match
    return indent + '$$\n' + indent + rest
  })
  processed = processed.replace(/^([ \t]*)(.+)\$\$[ \t]*$/gm, (match, indent, content) => {
    // 이미 독립 행인 `$$`(들여쓴 것 포함)은 건드리지 않는다. 여는 쪽도 마찬가지다.
    if (!content.trim() || content.trimStart().startsWith('$$')) return match
    return indent + content + '\n' + indent + '$$'
  })

  // :::type ... ::: 콜아웃 블록 → HTML 변환 (SVG 아이콘)
  processed = processed.replace(
    // 주의: 닫는 ::: 뒤를 \s* 로 잡으면 뒤따르는 개행까지 먹어 </div> 바로 다음 줄에
    // 헤딩이 붙고, CommonMark HTML 블록 규칙 때문에 그 헤딩이 raw 텍스트로 삼켜진다.
    // 여는/닫는 마커 모두 같은 줄의 공백만 허용한다.
    /^:::(info|warning|tip|danger)[ \t]*\n([\s\S]*?)\n[ \t]*:::[ \t]*$/gm,
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
      return `<div class="callout callout-${type}" style="background:rgba(${c.rgb},0.06);border:1px solid rgba(${c.rgb},0.08);border-radius:12px;padding:1rem 1.25rem;margin:1rem 0">\n<div style="display:flex;align-items:center;gap:6px;font-weight:600;font-size:13px;color:${c.hex};margin-bottom:6px"><span style="display:inline-flex">${icon}</span><span>${c.label}</span></div>\n\n${content.trim()}\n\n</div>\n`
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

// 사이트 팔레트에 맞춘 mermaid 테마. 기본 테마는 회색 실선이라 본문에 섞이면 흐릿하다.
const MERMAID_THEME = {
  primaryColor: '#eef2ff',
  primaryTextColor: '#1e293b',
  primaryBorderColor: '#818cf8',
  lineColor: '#94a3b8',
  secondaryColor: '#f0fdfa',
  secondaryBorderColor: '#5eead4',
  tertiaryColor: '#fff7ed',
  tertiaryBorderColor: '#fdba74',
  fontFamily: 'Pretendard, -apple-system, BlinkMacSystemFont, sans-serif',
  fontSize: '14px',
  edgeLabelBackground: '#ffffff',
  clusterBkg: '#f8fafc',
  clusterBorder: '#cbd5e1',
}

/**
 * Mermaid 다이어그램.
 * 기본 렌더는 자기루프나 긴 엣지 라벨이 viewBox 밖으로 나가 잘린다.
 * 그려진 내용의 실제 bbox를 재서 viewBox를 다시 잡아 잘림을 없앤다.
 */
function MermaidDiagram({ code }) {
  const hostRef = useRef(null)
  const [svg, setSvg] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!code) return
    let alive = true
    import('mermaid').then(({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'loose',
        theme: 'base',
        themeVariables: MERMAID_THEME,
        flowchart: { curve: 'basis', padding: 18, htmlLabels: true, useMaxWidth: true },
        er: { useMaxWidth: true },
        sequence: { useMaxWidth: true, actorMargin: 60 },
      })
      const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`
      mermaid.render(id, code)
        .then(({ svg }) => { if (alive) { setSvg(svg); setError(null) } })
        .catch((err) => { if (alive) { setError(err.message); setSvg('') } })
    })
    return () => { alive = false }
  }, [code])

  // 그린 뒤 실제 내용 크기로 viewBox를 다시 잡고, 크기를 일정한 띠 안으로 모은다.
  //
  // 예전에는 width를 100%로 못 박았다. 그러면 크기가 내용이 아니라 방향에 끌려다닌다.
  // 가로 flowchart(LR)는 종횡비가 10:1까지 나와 본문 폭에서 높이가 79px짜리 띠가 되고,
  // 세로 flowchart(TD)는 반대로 1,500px까지 치솟는다. 같은 글 안에서도 들쭉날쭉했다.
  //
  // 그래서 높이를 기준으로 잡는다. 목표 높이에 맞춰 폭을 정하고, 폭이 본문을 넘으면
  // 그때만 폭에 맞춘다. 종횡비는 유지하고 가운데 정렬한다.
  // mermaid가 잡은 자연 크기를 존중하고 극단만 손본다.
  // 처음에는 목표 높이 320px에 전부 맞췄는데, 자연 크기가 224x677인 도해가
  // 106x320으로 줄어 글자가 안 읽혔다. 0.47배 축소였다.
  // 순서를 바꿨다. **폭이 먼저다.**
  //
  // 높이를 먼저 620px에 맞추다 보니, 세로로 긴 도해가 칼럼 폭에 닿기도 전에 줄어들어
  // 좁은 띠가 됐다. 실제로 여러 편을 재 보니 전부 높이 620에 딱 붙어 있었다.
  //   205x620 · 245x620 · 323x620 · 456x620 · 489x620
  // 칼럼 레이아웃에서 묶는 조건은 폭이다. 폭에 맞춘 뒤, 그래도 너무 길 때만 줄인다.
  // 긴 도해는 스크롤로 읽으면 된다. 억지로 줄이면 글자가 죽는다.
  // 폭에 맞췄더니 이 높이도 못 채우는 도해가 있다. 그때는 폭을 넘겨 키우고 스크롤을 준다.
  //
  // 왜 필요한가: `maxWidth: 100%`가 가로 스크롤을 원천 봉쇄하고 있었다. 그래서 종횡비가
  // 12:1, 17:1인 도해가 칼럼 폭 862px에 억지로 눌려 높이 53~148px짜리 띠가 됐다.
  // viewBox 172px 안의 14px 글자가 화면에서 6px이 된다. **아예 안 읽힌다.**
  // 실측으로 그런 도해가 63개였고, 최악은 862x3px(gantt, viewBox 폭 45,421)이었다.
  // 폭 안에 다 넣는 것보다 옆으로 미는 편이 낫다. 안 읽히는 글자는 감당할 수 없다.
  const LEGIBLE_H = 240
  // 다만 무한정 넓힐 수는 없다. 칼럼의 이 배수까지만 넘긴다. 그보다 넓은 도해는
  // 렌더러가 구할 수 없고 소스에서 방향을 돌려야 한다.
  const OVERFLOW_X = 2.5
  const MIN_H = 150      // 이보다 낮으면 글자가 안 읽힌다
  // 1100으로 되돌렸다. 900으로 낮춰 보니 세로로 긴 도해가 오히려 더 좁아졌다.
  // 좁아지면 글자가 죽는다. 스크롤은 감당할 수 있지만 안 읽히는 글자는 못 감당한다.
  //   같은 도해: MAX_H 620 -> 205x620, 900 -> 216x690, 1100 -> 353x1100
  const MAX_H = 1100
  // 세로로 긴 도해는 MAX_H에 걸려 폭이 176px까지 좁아졌다(실측 9개). 좁고 긴 것은
  // 높이를 더 허용하는 편이 낫다. 어차피 스크롤로 읽는다.
  const MAX_H_NARROW = 1500
  const NARROW = 0.45    // 칼럼 폭의 이 비율보다 좁으면 읽히도록 키운다

  // 실제로 재서 크기를 정하는 일은 함수로 빼 둔다. **한 번 적용으로는 안 남는다.**
  // 적용 직후 로그로 확인해 보면 `max-width: none; width: 2235px`까지 제대로 들어가는데,
  // 잠시 뒤 mermaid가 붙여 둔 원래 `max-width: 2876px`으로 되돌아가 있었다. 본문이 다시
  // 그려질 때 dangerouslySetInnerHTML이 SVG를 새로 써 넣기 때문이다(위키링크가 늦게
  // 도착하면 본문 문자열이 바뀐다). 그래서 childList를 지켜보다가 바뀌면 다시 적용한다.
  const applySize = () => {
    const host = hostRef.current
    if (!host) return
    const el = host.querySelector('svg')
    if (!el) return
    try {
      const box = el.getBBox()
      const pad = 12
      const vw = box.width + pad * 2
      const vh = box.height + pad * 2
      el.setAttribute('viewBox', `${box.x - pad} ${box.y - pad} ${vw} ${vh}`)
      el.setAttribute('preserveAspectRatio', 'xMidYMid meet')

      const maxW = host.clientWidth || 896
      const capH = vw / vh < 1 ? MAX_H_NARROW : MAX_H   // 좁고 긴 것은 더 허용한다
      let scale = 1
      if (vw > maxW) scale = maxW / vw                // 1. 폭이 칼럼을 넘으면 폭에 맞춘다
      if (vw * scale < maxW * NARROW) {               // 2. 너무 좁으면 읽히도록 키운다
        scale = Math.min((maxW * 0.7) / vw, capH / vh)
      }
      if (vh * scale < MIN_H) {                       // 3. 납작하면 키운다
        scale = Math.min(MIN_H / vh, maxW / vw)
      }
      if (vh * scale > capH) {                        // 4. 그래도 지나치게 길면 그때 줄인다
        scale = capH / vh
      }
      // 5. 폭에 맞춰 놓고도 글자가 죽을 만큼 납작하면, 칼럼을 넘겨 키우고 스크롤로 넘긴다
      const overflowing = vh * scale < LEGIBLE_H
      if (overflowing) {
        scale = Math.min(LEGIBLE_H / vh, (maxW * OVERFLOW_X) / vw)
      }
      const w = vw * scale
      const h = vh * scale
      el.style.width = `${Math.round(w)}px`
      el.style.height = `${Math.round(h)}px`
      // 넘길 때는 maxWidth를 걷어야 한다. 이게 남아 있으면 스크롤이 아예 안 생긴다
      el.style.maxWidth = overflowing ? 'none' : '100%'
      el.style.display = 'block'
      el.style.margin = overflowing ? '0' : '0 auto'  // 폭이 본문보다 좁을 때 가운데로
      el.removeAttribute('height')
      el.removeAttribute('width')
      // 옆으로 넘겼다는 사실은 figure의 data 속성으로 알린다. 힌트는 CSS가 켠다.
      // **여기서 setState를 부르면 안 된다.** 재렌더가 SVG를 다시 써서 크기가 날아간다.
      const fig = host.closest('figure')
      if (fig) fig.dataset.wide = overflowing && w > maxW + 4 ? '1' : '0'
    } catch {
      /* getBBox는 숨겨진 노드에서 던진다 - 그 경우 원본 그대로 둔다 */
    }
  }

  useEffect(() => {
    if (!svg || !hostRef.current) return
    const host = hostRef.current
    applySize()
    // SVG가 새로 써 넣어지면 다시 적용한다. 속성만 바꾸므로 스스로를 또 깨우지 않는다.
    const mo = new MutationObserver(() => applySize())
    mo.observe(host, { childList: true })
    // 창 폭이 바뀌면 기준이 되는 칼럼 폭도 바뀐다
    const ro = new ResizeObserver(() => applySize())
    ro.observe(host)
    return () => { mo.disconnect(); ro.disconnect() }
  }, [svg])

  if (error) {
    return (
      <div className="my-6 rounded-xl border px-4 py-3 text-sm"
        style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)', background: 'var(--bg-secondary)' }}>
        다이어그램을 그리지 못했습니다: {error}
      </div>
    )
  }
  if (!svg) {
    return <div className="my-6 h-24 rounded-xl skeleton" />
  }

  return (
    <figure className="my-6 rounded-xl border overflow-hidden"
      style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
      <div className="flex items-center gap-2 px-3 py-1.5 border-b text-[11px] font-medium tracking-wide"
        style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>
        <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: '#818cf8' }} />
        DIAGRAM
        {/* 옆으로 밀린다는 사실을 알려 준다. 모르면 잘린 그림으로 읽는다.
            보이고 감추는 것은 CSS가 figure[data-wide]로 정한다(위 주석 참고) */}
        <span className="ml-auto normal-case tracking-normal wide-hint">옆으로 넘겨 보세요</span>
      </div>
      <div
        ref={hostRef}
        className="px-4 py-5 overflow-x-auto diagram-scroll"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </figure>
  )
}

// 아주 긴 코드 창은 접는다. 코퍼스에 60줄이 넘는 블록이 120개 있고 최장이 191줄인데,
// 13.5px에 줄높이 1.75면 191줄이 화면에서 4,500px짜리 벽이 된다. 읽던 글의 맥락이 끊긴다.
const LONG_LINES = 44        // 이 줄 수를 넘으면 접는다
const VISIBLE_LINES = 30     // 접었을 때 보여 줄 줄 수
const COLLAPSED_H = Math.round(VISIBLE_LINES * 13.5 * 1.75) + 28   // 위아래 패딩까지

// 코드블록 전담 - pre 컴포넌트
function PreBlock({ children }) {
  const [copied, setCopied] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [scrollable, setScrollable] = useState(false)
  const preRef = useRef(null)

  const codeProps = children?.props ?? {}
  const lang = /language-(\w+)/.exec(codeProps.className || '')?.[1] || ''
  const plainText = extractPlainText(codeProps.children).trim()

  // 가로로 넘치는지 실제로 재서 판단한다. 글자 수로 어림하면 폰트·글꼴에 따라 어긋난다.
  // 코퍼스의 8%가 100자를 넘고 최장이 594자다. 표시가 없으면 잘린 줄을 전부라고 읽는다.
  useEffect(() => {
    const el = preRef.current
    if (!el) return
    const measure = () => setScrollable(el.scrollWidth - el.clientWidth > 4)
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [plainText, expanded])

  const handleCopy = () => {
    navigator.clipboard.writeText(plainText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Mermaid 코드블록 → 다이어그램 렌더링
  if (lang === 'mermaid') {
    return <MermaidDiagram code={plainText} />
  }

  // 실행 결과 - 어두운 터미널 판. 앞의 코드 창과 이어 붙여 한 창처럼 읽히게 한다.
  // 본문을 children이 아니라 plainText로 그린다: highlight.js가 <code>에 밝은 테마 색을
  // 강제해서 어두운 바탕 위에 어두운 글씨가 되어 안 보였다.
  // 이어 붙이는 모양(위 테두리 없음, 위쪽 각지게, 음수 마진)은 **앞에 코드 창이 정말
  // 있을 때만** 맞다. 예전에는 무조건 붙여서, 앞이 문단인 output 30개가 문단 위로 24px
  // 겹치고 위 테두리 없이 잘린 판처럼 보였다. 형제 선택자로 CSS에 넘긴다(.term-out-wrap).
  if (lang === 'output') {
    return (
      <div className="relative group not-prose my-6 max-w-full overflow-hidden term-out-wrap"
        style={{ background: 'var(--term-out)' }}>
        <div className="flex items-center justify-between px-4 py-1.5 text-[11px] font-mono tracking-wide"
          style={{ color: 'var(--term-dim)', borderBottom: '1px solid var(--term-line)' }}>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: '#3fb950' }} />
            OUTPUT
          </span>
          <button onClick={handleCopy} aria-label="실행 결과 복사"
            className="opacity-50 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity
              px-2 py-0.5 rounded hover:bg-white/10">
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
        <div className="term-out-body">
          {/* 글자 크기를 코드 창과 같게 못 박는다. 0.8em이 본문 16px을 물려받아 14.4px이
              되면서 코드(13.5px)보다 **더 컸다.** 실행 결과가 코드보다 도드라져 보였고,
              줄높이도 25.2px 대 23.6px로 어긋나 한 창처럼 읽히지 않았다. */}
          <pre className="term-output px-4 py-3.5 overflow-x-auto m-0 max-w-full"
            style={{
              fontSize: '13.5px', lineHeight: '1.75', color: '#cdd7e3',
              background: 'transparent', border: 'none', borderRadius: 0,
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
            }}>
            {plainText}
          </pre>
        </div>
      </div>
    )
  }

  // 매핑에 없는 언어는 칩에 소문자 원문이 그대로 나온다. 코퍼스를 세어 보니 그런 것이
  // 19종 800개였다(text 645, markdown 61, dockerfile 32, pig 27 ...). 표기가 들쭉날쭉해
  // 매핑된 것들과 나란히 놓이면 미완성으로 보인다. 실제로 쓰이는 것을 모두 채운다.
  const LANG_LABEL = {
    sql: 'SQL', bash: 'bash', sh: 'shell', zsh: 'zsh', python: 'Python', cypher: 'Cypher',
    js: 'JavaScript', javascript: 'JavaScript', ts: 'TypeScript', typescript: 'TypeScript',
    jsx: 'JSX', tsx: 'TSX', yaml: 'YAML', yml: 'YAML', json: 'JSON', json5: 'JSON5',
    hcl: 'HCL', go: 'Go', rust: 'Rust', java: 'Java', scala: 'Scala', c: 'C', cpp: 'C++',
    text: 'text', markdown: 'Markdown', md: 'Markdown', dockerfile: 'Dockerfile',
    dockerignore: '.dockerignore', gitignore: '.gitignore', pig: 'Pig Latin', toml: 'TOML',
    ini: 'INI', xml: 'XML', promql: 'PromQL', powershell: 'PowerShell', graphql: 'GraphQL',
    proto: 'Protobuf', diff: 'diff', hql: 'HiveQL', nginx: 'nginx', prolog: 'Prolog',
    css: 'CSS', html: 'HTML', r: 'R', csv: 'CSV', make: 'Makefile', makefile: 'Makefile',
  }

  const lineCount = plainText ? plainText.split('\n').length : 0
  const collapsible = lineCount > LONG_LINES && !expanded

  return (
    <div className="relative group not-prose my-6 max-w-full overflow-hidden code-window"
      style={{
        background: 'var(--term-bg)',
        border: '1px solid var(--term-line)',
        borderRadius: 14,
        boxShadow: '0 1px 2px rgba(15,23,42,0.06), 0 8px 24px -12px rgba(15,23,42,0.35)',
      }}>
      {/* 창 머리띠 - 신호등과 언어 칩으로 '입력'임을 알린다 */}
      <div className="flex items-center gap-3 px-3.5 py-2.5"
        style={{ background: 'var(--term-bar)', borderBottom: '1px solid var(--term-line)' }}>
        <span className="flex items-center gap-[7px] shrink-0">
          <span className="inline-block w-[11px] h-[11px] rounded-full" style={{ background: '#ff5f57' }} />
          <span className="inline-block w-[11px] h-[11px] rounded-full" style={{ background: '#febc2e' }} />
          <span className="inline-block w-[11px] h-[11px] rounded-full" style={{ background: '#28c840' }} />
        </span>
        <span className="px-2 py-[3px] rounded-md text-[11px] font-mono font-semibold tracking-wide"
          style={{ background: 'rgba(255,255,255,0.07)', color: '#c3cdda' }}>
          {LANG_LABEL[lang] || lang || 'text'}
        </span>
        {/* 줄 수를 적어 둔다. 접힌 창에서 얼마가 감춰졌는지 알 수 있어야 한다 */}
        {lineCount > LONG_LINES && (
          <span className="text-[11px] font-mono" style={{ color: 'var(--term-dim)' }}>
            {lineCount}줄
          </span>
        )}
        {/* 옆으로 밀린다는 표시. 없으면 잘린 코드를 전부라고 읽는다 */}
        {scrollable && (
          <span className="text-[11px] font-mono" style={{ color: 'var(--term-dim)' }}>
            옆으로 넘겨 보세요
          </span>
        )}
        {/* 늘 보이게 둔다. opacity-0이면 손가락으로 쓰는 화면에서는 있는 줄도 모른다 */}
        <button
          onClick={handleCopy}
          aria-label="코드 복사"
          className="ml-auto opacity-50 group-hover:opacity-100 focus-visible:opacity-100
            transition-opacity px-2 py-0.5 rounded text-[11px] font-mono hover:bg-white/10"
          style={{ color: 'var(--term-dim)' }}
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <div className="relative">
        <pre
          ref={preRef}
          className="px-4 py-3.5 overflow-x-auto text-[13.5px] leading-[1.75] m-0 rounded-none max-w-full"
          style={collapsible ? { maxHeight: COLLAPSED_H, overflowY: 'hidden' } : undefined}
        >
          {children}
        </pre>
        {collapsible && (
          <button
            onClick={() => setExpanded(true)}
            className="absolute inset-x-0 bottom-0 pt-14 pb-3 text-[12px] font-mono"
            style={{
              color: '#c3cdda',
              background: 'linear-gradient(to bottom, transparent, var(--term-bg) 62%)',
            }}
          >
            남은 {lineCount - VISIBLE_LINES}줄 펼치기
          </button>
        )}
      </div>
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
          rehypePlugins={[rehypeRaw, rehypeSlug, rehypeKatex,
            // detect:false - 언어를 안 적은 블록(ASCII 다이어그램 등)을 억지로
            // 감지해 칠하면 줄마다 흰 상자가 생긴다. 명시한 언어만 칠한다.
            [rehypeHighlight, { detect: false, ignoreMissing: true }]]}
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
