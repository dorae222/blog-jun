/**
 * 본문 소제목(h1~h4)에서 글자를 뽑는 도우미.
 * KaTeX 는 수식 하나를 MathML(TeX 원문 포함)과 HTML 로 두 번 넣는다. 그래서 textContent 를 그대로 읽으면
 * "dk=2d_k = 2dk=2" 처럼 글자가 겹친다. 목차와 "본문에서 다시 보기"가 이 겹친 글자를 쓰지 않게 한다.
 */

/** 목차에 그릴 HTML. 수식은 KaTeX 가 그린 모양 그대로 두고, 화면에 안 보이는 MathML 과 id, 링크는 뺀다. */
export function headingHtml(el) {
  const clone = el.cloneNode(true)
  for (const n of clone.querySelectorAll('.katex-mathml')) n.parentNode.removeChild(n)
  for (const n of clone.querySelectorAll('[id]')) n.removeAttribute('id')
  for (const a of clone.querySelectorAll('a')) {
    const span = document.createElement('span')
    span.innerHTML = a.innerHTML
    a.replaceWith(span)
  }
  return clone.innerHTML.trim()
}

/** 소제목의 원문에 가까운 글자. 수식은 TeX 원문으로 되돌린다. */
export function headingSource(el) {
  const clone = el.cloneNode(true)
  for (const k of clone.querySelectorAll('.katex')) {
    const tex = k.querySelector('annotation')?.textContent ?? ''
    k.replaceWith(document.createTextNode(tex))
  }
  return clone.textContent
}

/** 비교용으로 줄인 글자. 공백과 수식 구분자($)의 차이는 무시한다. */
export function headingKey(text) {
  return String(text ?? '').replace(/\$/g, '').replace(/\s+/g, '')
}
