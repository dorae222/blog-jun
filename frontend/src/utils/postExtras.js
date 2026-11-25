// 요약 카드(summary_card)·확인 질문(quiz)의 편집기 폼 ↔ 서버 형식 변환. 순수 함수(npm test).

export const LEVELS = ['입문', '중급', '심화']
export const LEARN_SLOTS = 3
export const QUIZ_SLOTS = 3
export const MAX_PREREQ = 5

export function emptyCard() {
  return { one_line: '', learn: Array(LEARN_SLOTS).fill(''), prereq: [], level: '', read_min: '' }
}

export function emptyQuiz() {
  return Array.from({ length: QUIZ_SLOTS }, () => ({ q: '', a: '', where: '' }))
}

/** 서버 값(null 가능) → 폼. 칸 수를 고정해 입력란이 늘 같은 자리에 있게 한다. */
export function cardToForm(card) {
  const base = emptyCard()
  if (!card || typeof card !== 'object') return base
  const learn = Array.isArray(card.learn) ? card.learn.filter((s) => typeof s === 'string') : []
  return {
    one_line: card.one_line || '',
    learn: [...learn, ...base.learn].slice(0, Math.max(LEARN_SLOTS, learn.length)),
    prereq: Array.isArray(card.prereq)
      ? card.prereq.map((p) => ({ title: p?.title || '', slug: p?.slug || '' }))
      : [],
    level: card.level || '',
    read_min: card.read_min ? String(card.read_min) : '',
  }
}

export function quizToForm(quiz) {
  const rows = Array.isArray(quiz)
    ? quiz.map((r) => ({ q: r?.q || '', a: r?.a || '', where: r?.where || '' }))
    : []
  return [...rows, ...emptyQuiz()].slice(0, Math.max(QUIZ_SLOTS, rows.length))
}

/** 글 주소를 붙여 넣어도 slug 만 남긴다. */
export function parseSlugInput(value) {
  let v = (value || '').trim()
  const m = /\/post\/([^/?#]+)/.exec(v)
  if (m) v = m[1]
  try { v = decodeURIComponent(v) } catch { /* 그대로 둔다 */ }
  return v.replace(/^\/+|\/+$/g, '')
}

/**
 * 폼 → 서버 값.
 *   state 'empty'      전부 비었다 → value null (서버에서 지운다)
 *   state 'ok'         보낼 수 있다
 *   state 'incomplete' 쓰는 중이다 → 보내지 않는다(자동 저장이 400 으로 막히지 않게). reason 에 이유.
 */
export function cardPayload(form) {
  const f = form || emptyCard()
  const one = (f.one_line || '').trim()
  const learn = (f.learn || []).map((s) => (s || '').trim()).filter(Boolean)
  const prereq = (f.prereq || [])
    .map((p) => ({ title: (p.title || '').trim(), slug: parseSlugInput(p.slug) }))
    .filter((p) => p.slug || p.title)
  const readRaw = String(f.read_min ?? '').trim()
  const level = f.level || ''
  if (!one && !learn.length && !prereq.length && !level && !readRaw) return { state: 'empty', value: null }
  if (!one) return { state: 'incomplete', reason: '한 줄 결론을 채워 주세요.' }
  if (!learn.length) return { state: 'incomplete', reason: '"알게 되는 것"을 하나 이상 채워 주세요.' }
  if (prereq.some((p) => !p.slug)) return { state: 'incomplete', reason: '선수 지식에는 글 slug 가 필요해요.' }
  let read = null
  if (readRaw) {
    read = Number(readRaw)
    if (!Number.isInteger(read) || read < 1 || read > 300) {
      return { state: 'incomplete', reason: '읽는 시간은 1~300 사이 숫자(분)로 적어 주세요.' }
    }
  }
  return {
    state: 'ok',
    value: { one_line: one, learn: learn.slice(0, LEARN_SLOTS), prereq, level: level || null, read_min: read },
  }
}

export function quizPayload(rows) {
  const cleaned = (rows || []).map((r) => ({
    q: (r.q || '').trim(), a: (r.a || '').trim(), where: (r.where || '').trim(),
  }))
  const used = cleaned.filter((r) => r.q || r.a || r.where)
  if (!used.length) return { state: 'empty', value: null }
  if (used.some((r) => !r.q || !r.a)) {
    return { state: 'incomplete', reason: '질문과 답을 둘 다 채워야 저장돼요.' }
  }
  return { state: 'ok', value: used }
}
