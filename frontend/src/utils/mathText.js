/**
 * `key_detail`에는 LaTeX 수식이 섞여 있다. KaTeX로 조판하는 자리에서는 그대로 넘기면
 * 되지만, d3가 innerHTML로 그리는 툴팁처럼 React 컴포넌트를 쓸 수 없는 자리도 있다.
 * 그런 자리에 원문을 그대로 넣으면 달러와 백슬래시가 날것으로 보인다.
 *
 * 여기서는 두 가지를 담당한다.
 *   1. `mathToPlainText` - 수식 구간을 읽을 수 있는 평문으로 바꾼다
 *   2. `escapeAngleBracketsOutsideMath` - 마크다운으로 그릴 때 본문에 그냥 적힌
 *      홑화살괄호가 HTML 태그로 먹혀 사라지는 것을 막는다
 */

// 툴팁은 읽히기만 하면 된다. 조판 대신 유니코드 한 글자로 갈음한다.
const GREEK = {
  alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', epsilon: 'ε', varepsilon: 'ε',
  zeta: 'ζ', eta: 'η', theta: 'θ', vartheta: 'θ', iota: 'ι', kappa: 'κ',
  lambda: 'λ', mu: 'μ', nu: 'ν', xi: 'ξ', pi: 'π', rho: 'ρ', sigma: 'σ',
  tau: 'τ', upsilon: 'υ', phi: 'φ', varphi: 'φ', chi: 'χ', psi: 'ψ', omega: 'ω',
  Gamma: 'Γ', Delta: 'Δ', Theta: 'Θ', Lambda: 'Λ', Xi: 'Ξ', Pi: 'Π',
  Sigma: 'Σ', Upsilon: 'Υ', Phi: 'Φ', Psi: 'Ψ', Omega: 'Ω',
}

const SYMBOLS = {
  times: '×', cdot: '·', cdots: '···', ldots: '...', dots: '...',
  pm: '±', mp: '∓', leq: '≤', le: '≤', geq: '≥', ge: '≥', neq: '≠', ne: '≠',
  approx: '≈', equiv: '≡', sim: '~', simeq: '≃', propto: '∝', triangleq: '≜',
  ll: '≪', gg: '≫', to: '→', rightarrow: '→', Rightarrow: '⇒', mapsto: '↦',
  leftarrow: '←', Leftarrow: '⇐', leftrightarrow: '↔',
  infty: '∞', partial: '∂', nabla: '∇', sum: '∑', prod: '∏', int: '∫',
  in: '∈', notin: '∉', subset: '⊂', subseteq: '⊆', cup: '∪', cap: '∩',
  emptyset: '∅', varnothing: '∅', forall: '∀', exists: '∃',
  otimes: '⊗', oplus: '⊕', odot: '⊙', circ: '∘', star: '⋆', ast: '*',
  langle: '⟨', rangle: '⟩', lVert: '‖', rVert: '‖', Vert: '‖', vert: '|',
  perp: '⊥', angle: '∠', deg: '°',
}

// 위아래 표시는 결합 문자로 붙인다. 한 글자짜리가 아니면 표시를 버리고 알맹이만 남긴다
const ACCENTS = {
  bar: '\u0304', overline: '\u0304', hat: '\u0302', widehat: '\u0302',
  tilde: '\u0303', widetilde: '\u0303', vec: '\u20D7', dot: '\u0307',
}

// 안쪽 중괄호부터 풀어야 하므로 더 이상 바뀌지 않을 때까지 돌린다.
// 중첩이 아무리 깊어도 몇 겹이면 끝나고, 안 끝나면 그냥 원문에 가깝게 둔다.
function replaceUntilStable(input, pattern, replacer) {
  let out = input
  for (let i = 0; i < 8; i += 1) {
    const next = out.replace(pattern, replacer)
    if (next === out) break
    out = next
  }
  return out
}

// 분수와 제곱근의 알맹이. 짧으면 괄호가 오히려 방해가 된다
function group(inner) {
  const t = inner.trim()
  return t.length > 2 || /[\s+\-*/]/.test(t) ? `(${t})` : t
}

function convertMathBody(body) {
  let s = body

  // 괄호 크기 지시자는 괄호만 남긴다
  s = s.replace(/\\(?:left|right|bigg?|Bigg?)\s*/g, '')

  // 글꼴 지정 매크로는 껍데기만 벗긴다
  s = replaceUntilStable(
    s,
    /\\(?:mathbf|mathrm|mathcal|mathbb|mathit|mathsf|mathtt|boldsymbol|bm|operatorname|text(?:bf|it|rm|sf|tt)?)\s*\{([^{}]*)\}/g,
    (_, inner) => inner,
  )

  // 그리스 문자와 기호. 모르는 매크로는 이 단계에서 손대지 않고 그대로 둔다
  s = s.replace(/\\([a-zA-Z]+)/g, (whole, name) => GREEK[name] ?? SYMBOLS[name] ?? whole)

  // 아래첨자와 위첨자의 중괄호를 먼저 푼다. x_{1:T} -> x_1:T
  // 이걸 뒤로 미루면 \sqrt{\bar{\alpha}_{t-1}} 처럼 중괄호가 겹친 인자를
  // \sqrt 규칙이 못 잡아 매크로 이름이 그대로 남는다
  s = replaceUntilStable(s, /([_^])\s*\{([^{}]*)\}/g, (_, mark, inner) => mark + inner)

  // 위아래 표시는 그리스 문자로 바뀐 뒤에 붙여야 한 글자로 잡힌다
  s = replaceUntilStable(
    s,
    /\\(bar|overline|hat|widehat|tilde|widetilde|vec|dot)\s*\{([^{}]*)\}/g,
    (_, kind, inner) => (Array.from(inner).length === 1 ? inner + ACCENTS[kind] : inner),
  )

  // 분수와 제곱근은 서로 안에 들어갈 수 있어 한 판에 놓고 안쪽부터 푼다
  s = replaceUntilStable(
    s,
    /\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}|\\sqrt\s*\{([^{}]*)\}/g,
    (_, num, den, root) => (root === undefined ? `${group(num)}/${group(den)}` : `√${group(root)}`),
  )

  // 글자가 아닌 이스케이프. 두 겹 백슬래시(줄바꿈)를 먼저 처리해야 한 겹 규칙이 반쪽을 물지 않는다
  s = s.replace(/\\\|/g, '‖')
    .replace(/\\\\/g, ' ')
    .replace(/\\([{}%&#_$~^])/g, '$1')

  // 간격 명령은 공백 한 칸으로 접는다
  s = s.replace(/\\(?:quad|qquad|[,;:! ])/g, ' ')

  // 남은 매크로는 이름만 남긴다. \log, \min, \exp 처럼 이름 자체가 뜻인 것들이다
  s = s.replace(/\\([a-zA-Z]+)/g, '$1')

  return s.replace(/[{}]/g, '').replace(/\s+/g, ' ').trim()
}

// `$...$`와 `$$...$$` 구간을 통째로 떼어내는 자리표. split의 캡처 덕에 홀수 칸이 수식이 된다
const MATH_SPAN = /(\$\$[\s\S]+?\$\$|\$[^$]+?\$)/

// 마크다운 이스케이프(`4\~8` 같은)는 평문에서는 백슬래시가 그대로 보인다.
// CommonMark가 이스케이프를 허용하는 ASCII 구두점만 되돌린다.
function unescapeMarkdown(text) {
  return text.replace(/\\([!-/:-@[-`{-~])/g, '$1')
}

/**
 * `$...$`와 `$$...$$` 구간을 읽을 수 있는 평문으로 바꾼다.
 */
export function mathToPlainText(raw) {
  if (!raw) return ''
  return raw
    .split(MATH_SPAN)
    .map((part, i) => (i % 2 === 1
      ? convertMathBody(part.replace(/^\$\$?|\$\$?$/g, ''))
      : unescapeMarkdown(part)))
    .join('')
    // 짝이 맞지 않는 달러가 남아도 화면으로는 내보내지 않는다
    .replace(/\$/g, '')
    .replace(/[ \t]{2,}/g, ' ')
}

const HTML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }

/**
 * innerHTML로 그리는 자리에 넣기 전에 통과시킨다.
 */
export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => HTML_ESCAPES[ch])
}

/**
 * 마크다운으로 그리는 자리용. 본문에 그냥 적힌 `<instruction>` 같은 토막이
 * rehype-raw를 거치면서 HTML 태그로 먹혀 화면에서 사라지는 것을 막는다.
 * 수식 구간은 건드리지 않는다. remark-math가 원문 그대로 KaTeX에 넘기므로
 * 여기서 바꾸면 수식 안에 실체 참조가 그대로 찍힌다.
 */
export function escapeAngleBracketsOutsideMath(raw) {
  if (!raw) return ''
  return raw
    .split(MATH_SPAN)
    .map((part, i) => (i % 2 === 1 ? part : part.replace(/</g, '&lt;')))
    .join('')
}
