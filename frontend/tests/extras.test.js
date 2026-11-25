// 첨부 파일 링크 판별과 요약 카드·질문 폼 변환: npm test
import test from 'node:test'
import assert from 'node:assert/strict'
import {
  attachmentPath, attachmentFromLink, filenameFromPath, formatBytes, kindFromName,
} from '../src/utils/attachments.js'
import {
  cardPayload, cardToForm, emptyCard, emptyQuiz, parseSlugInput, quizPayload, quizToForm,
} from '../src/utils/postExtras.js'

test('첨부 링크: /media/.../files/... 만 첨부로 본다', () => {
  assert.equal(attachmentPath('/media/posts/a/files/x.xlsx'), '/media/posts/a/files/x.xlsx')
  assert.equal(attachmentPath('https://blog.dorae222.com/media/posts/a/files/x.xlsx?v=1'), '/media/posts/a/files/x.xlsx')
  assert.equal(attachmentPath('/media/posts/a/files/%EC%8B%A4%EC%8A%B5.csv#top'), '/media/posts/a/files/%EC%8B%A4%EC%8A%B5.csv')
  assert.equal(attachmentPath('https://dev.local/media/posts/a/files/x.py', 'dev.local'), '/media/posts/a/files/x.py')
  for (const href of [
    '/media/posts/a/overview.svg', '/media/files/x.xlsx', '/post/a', 'https://example.com/media/posts/a/files/x.xlsx',
    'https://github.com/a/b', '/media/posts/a/files/', '/media/posts/../files/x.zip', 'javascript:alert(1)', '', null, undefined,
    'mailto:a@b.c', '/media/posts/a/files/sub/x.zip/..',
  ]) assert.equal(attachmentPath(href), null, String(href))
})

test('첨부 링크: 파일명과 항목 만들기', () => {
  assert.equal(filenameFromPath('/media/posts/a/files/%EC%8B%A4%EC%8A%B5_1.csv'), '실습_1.csv')
  assert.equal(filenameFromPath('/media/posts/a/files/%E0%A4%A.csv'), '%E0%A4%A.csv')
  const known = [{ id: 7, filename: 'x.xlsx', url: '/media/posts/a/files/x.xlsx', size_bytes: 10, kind: 'xlsx', description: 'd' }]
  assert.equal(attachmentFromLink('/media/posts/a/files/x.xlsx', '받기', known).id, 7)
  const made = attachmentFromLink('/media/posts/a/files/y.py', '예제 코드', known)
  assert.deepEqual(made, { id: '/media/posts/a/files/y.py', filename: 'y.py', url: '/media/posts/a/files/y.py', size_bytes: null, kind: 'py', description: '예제 코드' })
  assert.equal(attachmentFromLink('/media/posts/a/files/y.py', 'y.py').description, '')
})

test('첨부: 크기와 종류 표기', () => {
  assert.equal(formatBytes(0), '0 B')
  assert.equal(formatBytes(1536), '1.5 KB')
  assert.equal(formatBytes(20 * 1024), '20 KB')
  assert.equal(formatBytes(5 * 1024 * 1024), '5.0 MB')
  assert.equal(formatBytes(null), '')
  assert.equal(kindFromName('A.XLSX'), 'xlsx')
  assert.equal(kindFromName('a.exe'), '')
  assert.equal(kindFromName('noext'), '')
})

test('요약 카드: 빈 폼은 null, 쓰는 중이면 보내지 않는다', () => {
  assert.deepEqual(cardPayload(emptyCard()), { state: 'empty', value: null })
  assert.equal(cardPayload({ ...emptyCard(), learn: ['a', '', ''] }).state, 'incomplete')
  assert.equal(cardPayload({ ...emptyCard(), one_line: 'x' }).state, 'incomplete')
  assert.equal(cardPayload({ ...emptyCard(), one_line: 'x', learn: ['a'], read_min: 'abc' }).state, 'incomplete')
  assert.equal(cardPayload({ ...emptyCard(), one_line: 'x', learn: ['a'], prereq: [{ title: 't', slug: '' }] }).state, 'incomplete')
  const ok = cardPayload({
    one_line: ' 결론 ', learn: ['하나', ' ', '둘'], level: '입문', read_min: '12',
    prereq: [{ title: '', slug: 'https://blog.dorae222.com/post/vector-db' }, { title: '', slug: '' }],
  })
  assert.deepEqual(ok, {
    state: 'ok',
    value: { one_line: '결론', learn: ['하나', '둘'], prereq: [{ title: '', slug: 'vector-db' }], level: '입문', read_min: 12 },
  })
  assert.equal(cardPayload({ ...emptyCard(), one_line: 'x', learn: ['a'] }).value.level, null)
})

test('요약 카드·질문: 서버 값 ↔ 폼 왕복', () => {
  const server = { one_line: '결론', learn: ['a', 'b'], prereq: [{ title: 'T', slug: 's' }], level: '심화', read_min: 7 }
  const form = cardToForm(server)
  assert.deepEqual(form.learn, ['a', 'b', ''])
  assert.equal(form.read_min, '7')
  assert.deepEqual(cardPayload(form).value, server)
  assert.deepEqual(cardToForm(null), emptyCard())
  const quiz = [{ q: 'q1', a: 'a1', where: 'w' }]
  assert.equal(quizToForm(quiz).length, 3)
  assert.deepEqual(quizPayload(quizToForm(quiz)).value, quiz)
  assert.deepEqual(quizPayload(emptyQuiz()), { state: 'empty', value: null })
  assert.equal(quizPayload([{ q: 'q', a: '', where: '' }]).state, 'incomplete')
  assert.deepEqual(quizToForm(undefined), emptyQuiz())
})

test('선수 글: 주소를 붙여 넣어도 slug 만 남긴다', () => {
  assert.equal(parseSlugInput('https://blog.dorae222.com/post/rag-intro?x=1'), 'rag-intro')
  assert.equal(parseSlugInput('/post/rag-intro/'), 'rag-intro')
  assert.equal(parseSlugInput('  rag-intro '), 'rag-intro')
  assert.equal(parseSlugInput('/post/%ED%95%9C%EA%B8%80'), '한글')
  assert.equal(parseSlugInput(''), '')
})
