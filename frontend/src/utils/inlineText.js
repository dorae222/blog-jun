// 짧은 한 줄 글에서 `$수식$`과 백틱 코드를 가려낸다(요약 카드, 확인 질문).
// 여는 $ 뒤와 닫는 $ 앞에 공백이 없어야 수식으로 본다("$5 와 $10" 같은 금액을 피한다).
const TOKEN_RE = /(\$(?!\s)[^$\n]+?(?<!\s)\$|`[^`\n]+`)/g

export function splitInline(text) {
  return String(text ?? '').split(TOKEN_RE).filter((part) => part !== '').map((part) => {
    if (part.length > 2 && part.startsWith('$') && part.endsWith('$')) return { type: 'math', value: part.slice(1, -1) }
    if (part.length > 2 && part.startsWith('`') && part.endsWith('`')) return { type: 'code', value: part.slice(1, -1) }
    return { type: 'text', value: part }
  })
}
