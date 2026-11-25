// 요약 카드·확인 질문의 한 줄 글에서 수식과 코드를 가려내는 규칙: npm test
import test from 'node:test'
import assert from 'node:assert/strict'
import { splitInline } from '../src/utils/inlineText.js'
import { headingKey } from '../src/utils/headingText.js'

test('수식과 코드를 글자와 나눈다', () => {
  assert.deepEqual(splitInline('$\\sqrt{d_k}$로 나누고 `softmax`를 취한다'), [
    { type: 'math', value: '\\sqrt{d_k}' },
    { type: 'text', value: '로 나누고 ' },
    { type: 'code', value: 'softmax' },
    { type: 'text', value: '를 취한다' },
  ])
})

test('수식이 없으면 글자 하나로 둔다', () => {
  assert.deepEqual(splitInline('토큰 3개'), [{ type: 'text', value: '토큰 3개' }])
  assert.deepEqual(splitInline(''), [])
  assert.deepEqual(splitInline(null), [])
})

test('금액처럼 공백이 붙은 달러는 수식으로 보지 않는다', () => {
  assert.deepEqual(splitInline('요금은 $5 에서 $10 사이'), [{ type: 'text', value: '요금은 $5 에서 $10 사이' }])
})

test('소제목 비교는 공백과 달러 차이를 무시한다', () => {
  assert.equal(headingKey('예제: 토큰 3개, $d_k = 2$'), headingKey('예제: 토큰 3개, d_k = 2'))
  assert.notEqual(headingKey('점수와 스케일'), headingKey('점수'))
})
