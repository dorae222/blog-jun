import { useEffect, useMemo, useState } from 'react'
import { useReducedMotion } from 'framer-motion'
import { CARD_COLORS } from '../../data/cardColors'

const MONO = 'ui-monospace, SFMono-Regular, Menlo, "Liberation Mono", monospace'

// 토큰 타입 → 색상 (카드 팔레트만 사용, 하드코딩 hex 없음)
const TOKEN_COLOR = {
  kw:  CARD_COLORS.purple.hex,   // keyword
  cls: CARD_COLORS.blue.hex,     // type / class
  fn:  CARD_COLORS.cyan.hex,     // function name
  str: CARD_COLORS.emerald.hex,  // string
  com: CARD_COLORS.slate.hex,    // comment
  num: CARD_COLORS.orange.hex,   // number
  op:  'var(--text-secondary)',  // operator / punctuation
}
const colorOf = (type) => (type ? TOKEN_COLOR[type] : 'var(--text)')

// 본인 소개를 "코드로" 표현한 스니펫. 각 줄 = [텍스트, 토큰타입|null] 배열
const CODE_LINES = [
  [['# whoami.py', 'com']],
  [],
  [['class ', 'kw'], ['HyeongJun', 'cls'], [':', null]],
  [['    role     ', null], ['=', 'op'], [' ', null], ['"AIOps Engineer"', 'str']],
  [['    based_in ', null], ['=', 'op'], [' ', null], ['"Seoul, South Korea"', 'str']],
  [['    stack    ', null], ['=', 'op'], [' [', null], ['"Python"', 'str'], [', ', null], ['"PyTorch"', 'str'], [', ', null], ['"Kubernetes"', 'str'], [']', null]],
  [],
  [['    def ', 'kw'], ['what_i_do', 'fn'], ['(self):', null]],
  [['        ', null], ['# 설계 → 배포 → 운영까지 직접 잇는다', 'com']],
  [['        return ', 'kw'], ['ship', 'fn'], ['(self.stack, to', null], ['=', 'op'], ['"production"', 'str'], [')', null]],
  [],
  [['HyeongJun', 'cls'], ['().', null], ['what_i_do', 'fn'], ['()', null]],
]

const TRAFFIC = [CARD_COLORS.red.hex, CARD_COLORS.amber.hex, CARD_COLORS.emerald.hex]

export default function CodeEditorHero() {
  const reduce = useReducedMotion()

  // 줄별 글자 수 + 줄 시작 누적 인덱스(줄바꿈 1글자 포함) 사전 계산
  const { lineLens, starts, total } = useMemo(() => {
    const lens = CODE_LINES.map((line) => line.reduce((n, t) => n + t[0].length, 0))
    const st = []
    let acc = 0
    for (let i = 0; i < lens.length; i++) {
      st.push(acc)
      acc += lens[i] + 1
    }
    return { lineLens: lens, starts: st, total: acc }
  }, [])

  const [shown, setShown] = useState(reduce ? total : 0)

  useEffect(() => {
    if (reduce) {
      setShown(total)
      return
    }
    setShown(0)
    const STEP = 2 // 틱당 글자 수
    const INTERVAL = 22 // ms — ~90자/초, 차분하게
    const id = setInterval(() => {
      setShown((prev) => {
        const next = prev + STEP
        if (next >= total) {
          clearInterval(id)
          return total
        }
        return next
      })
    }, INTERVAL)
    return () => clearInterval(id)
  }, [reduce, total])

  const done = shown >= total
  const lastLine = CODE_LINES.length - 1

  return (
    <div
      className="w-full rounded-xl overflow-hidden"
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--border)',
        boxShadow: '0 20px 50px -24px rgba(15,23,42,0.28), 0 6px 16px -12px rgba(15,23,42,0.14)',
      }}
    >
      {/* 타이틀 바 — macOS 스타일 신호등 + 파일 탭 */}
      <div
        className="flex items-center gap-3 px-4 h-11 select-none"
        style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-secondary)' }}
      >
        <div className="flex items-center gap-2">
          {TRAFFIC.map((c) => (
            <span key={c} className="w-3 h-3 rounded-full" style={{ background: c, opacity: 0.85 }} />
          ))}
        </div>
        <div
          className="ml-2 inline-flex items-center gap-2 px-3 py-1 rounded-t-md text-xs font-medium"
          style={{ background: 'var(--card-bg)', color: 'var(--text)', border: '1px solid var(--border)', borderBottom: 'none', marginBottom: '-1px' }}
        >
          <span className="w-2 h-2 rounded-full" style={{ background: CARD_COLORS.blue.hex }} />
          whoami.py
        </div>
        <span className="ml-auto text-[11px] font-medium tracking-wide" style={{ color: 'var(--text-secondary)' }}>
          Python
        </span>
      </div>

      {/* 코드 본문 */}
      <div className="overflow-x-auto">
        <div
          className="py-4 pr-5 text-xs sm:text-[13px]"
          style={{ fontFamily: MONO, lineHeight: 1.65 }}
        >
          {CODE_LINES.map((line, i) => {
            const visibleOnLine = shown - starts[i] // 이 줄에서 보여줄 글자 수
            const active = shown >= starts[i] && shown <= starts[i] + lineLens[i]
            const showCaret = !reduce && (active || (done && i === lastLine))
            let used = 0

            return (
              <div key={i} className="flex whitespace-pre" style={{ minHeight: '1.65em' }}>
                <span
                  className="inline-block text-right select-none pr-4 pl-4"
                  style={{ width: '3.25rem', color: 'var(--text-secondary)', opacity: 0.5 }}
                >
                  {i + 1}
                </span>
                <code className="whitespace-pre">
                  {line.map((tok, j) => {
                    const [text, type] = tok
                    const start = used
                    used += text.length
                    if (visibleOnLine <= start) return null
                    return (
                      <span key={j} style={{ color: colorOf(type) }}>
                        {text.slice(0, Math.max(0, visibleOnLine - start))}
                      </span>
                    )
                  })}
                  {showCaret && (
                    <span
                      className="code-caret inline-block align-middle"
                      style={{ width: '2px', height: '1.05em', marginLeft: '1px', borderRadius: '1px', background: 'var(--color-primary-500)' }}
                    />
                  )}
                </code>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
