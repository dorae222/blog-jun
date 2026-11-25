// 외부 의존성 없이 node 내장 테스트 러너로 돌린다: npm test
import test from 'node:test'
import assert from 'node:assert/strict'
import { createSSEParser } from '../src/utils/sse.js'
import {
  parseQuickNote, noteTitleFrom, slugify, autoSlug, slugSuffix, SLUG_RE, timeAgo, isSafeSlug, isTypingTarget,
} from '../src/utils/noteText.js'

test('SSE: 조각난 청크를 이벤트 단위로 합친다', () => {
  const got = []
  const p = createSSEParser((e) => got.push(e))
  p.push('data: {"type":"sou')
  p.push('rces","sources":[{"title":"A","slug":"a"}]}\n\ndata: {"type":"token","content":"안"}\n')
  p.push('\ndata: {"type":"token","content":"녕"}\r')
  p.push('\n\r\n: keepalive\n\n')
  p.push('data: {"type":"done","message_id":"x"}')
  p.end()
  assert.deepEqual(got.map((e) => e.type), ['sources', 'token', 'token', 'done'])
  assert.equal(got[1].content + got[2].content, '안녕')
})

test('SSE: JSON이 아니면 token으로 취급', () => {
  const got = []
  const p = createSSEParser((e) => got.push(e))
  p.push('data: hello\n\n')
  assert.deepEqual(got, [{ type: 'token', content: 'hello' }])
})

test('빠른 메모: #태그 추출', () => {
  assert.deepEqual(parseQuickNote('회의 정리 #Work #k8s #work'), { text: '회의 정리', tags: ['work', 'k8s'] })
  assert.deepEqual(parseQuickNote('#아이디어 블로그 글감'), { text: '블로그 글감', tags: ['아이디어'] })
  assert.deepEqual(parseQuickNote('see https://a.com/page#sec'), { text: 'see https://a.com/page#sec', tags: [] })
  assert.deepEqual(parseQuickNote('끝에 점 #todo.'), { text: '끝에 점', tags: ['todo'] })
})

test('메모 제목', () => {
  assert.equal(noteTitleFrom(''), '제목 없는 메모')
  assert.equal(noteTitleFrom('\n# 제목\n본문'), '제목')
  assert.equal(noteTitleFrom('가'.repeat(100), 10).length, 10)
})

test('slugify / autoSlug', () => {
  assert.equal(slugify('  Hello, World! 쿠버네티스 '), 'hello-world')
  assert.equal(slugify('---'), '')
  assert.equal(slugify('Café Déjà'), 'cafe-deja')
  assert.equal(autoSlug('vLLM vs TGI serving', '20260101-0900'), 'vllm-vs-tgi-serving')
  assert.equal(autoSlug('LLM 서빙 정리', '20260101-0900'), 'llm-20260101-0900')
  assert.equal(autoSlug('쿠버네티스 입문', '20260101-0900'), 'post-20260101-0900')
  assert.ok(SLUG_RE.test(autoSlug('한글만', slugSuffix(new Date(2026, 0, 2, 3, 4)))))
  assert.equal(slugSuffix(new Date(2026, 0, 2, 3, 4)), '20260102-0304')
  assert.ok(!SLUG_RE.test('쿠버네티스'))
})

test('timeAgo', () => {
  const now = Date.UTC(2026, 0, 1, 12)
  assert.equal(timeAgo(now - 2000, now), '방금')
  assert.equal(timeAgo(now - 30000, now), '30초 전')
  assert.equal(timeAgo(now - 5 * 60000, now), '5분 전')
  assert.equal(timeAgo(null, now), '')
})

test('isSafeSlug', () => {
  assert.ok(isSafeSlug('llm-serving'))
  assert.ok(isSafeSlug('쿠버네티스-입문'))
  assert.ok(!isSafeSlug('../admin'))
  assert.ok(!isSafeSlug('a/b'))
  assert.ok(!isSafeSlug(''))
  assert.ok(!isSafeSlug(undefined))
})

test('isTypingTarget', () => {
  assert.ok(isTypingTarget({ tagName: 'input' }))
  assert.ok(isTypingTarget({ tagName: 'DIV', isContentEditable: true }))
  assert.ok(!isTypingTarget({ tagName: 'BUTTON' }))
  assert.ok(!isTypingTarget(null))
})

test("챗봇 피드백 본문: 의견은 다듬어 300자까지, 비면 넣지 않는다", async () => {
  const { feedbackPayload, FEEDBACK_COMMENT_MAX } = await import("../src/utils/feedback.js")
  const base = { messageId: "a".repeat(32), feedbackToken: "t".repeat(32) }
  assert.deepEqual(feedbackPayload({ ...base, value: "up" }), { message_id: base.messageId, feedback_token: base.feedbackToken, value: "up" })
  assert.equal("comment" in feedbackPayload({ ...base, value: "down", comment: "   " }), false)
  assert.equal(feedbackPayload({ ...base, value: "down", comment: "  출처가 달라요 " }).comment, "출처가 달라요")
  assert.equal(feedbackPayload({ ...base, value: "down", comment: "가".repeat(500) }).comment.length, FEEDBACK_COMMENT_MAX)
})
