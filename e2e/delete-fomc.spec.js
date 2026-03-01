/**
 * FOMC 관련 포스트 일괄 삭제 스크립트
 * 실행: BLOG_USER=admin BLOG_PASS=비밀번호 npx playwright test e2e/delete-fomc.spec.js --reporter=list
 *
 * ⚠ 주의: 실제 데이터가 삭제됩니다
 */
import { test, expect } from '@playwright/test'

const BASE = 'https://blog.dorae222.com'
const BLOG_USER = process.env.BLOG_USER
const BLOG_PASS = process.env.BLOG_PASS

test('FOMC 포스트 일괄 삭제', async ({ page }) => {
  // ── 1. 로그인
  await page.goto(`${BASE}/login`)
  await page.waitForLoadState('networkidle')
  await page.fill('input[type="text"], input[name="username"]', BLOG_USER)
  await page.fill('input[type="password"]', BLOG_PASS)
  await page.click('button[type="submit"]')
  await page.waitForURL(`${BASE}/dashboard`, { timeout: 15_000 }).catch(() => {})

  // ── 2. 대시보드에서 API로 포스트 목록 수집 (page_size=500)
  const token = await page.evaluate(() => {
    return localStorage.getItem('access') || localStorage.getItem('token') || ''
  })

  const resp = await page.request.get(`${BASE}/api/posts/?page_size=500`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  const data = await resp.json()
  const allPosts = data.results || data

  // ── 3. FOMC 관련 포스트 필터
  const fomcPosts = allPosts.filter(p =>
    /fomc/i.test(p.title) || /fomc/i.test(p.slug)
  )
  console.log(`\nFOMC 포스트 발견: ${fomcPosts.length}개`)
  fomcPosts.forEach(p => console.log(` - [${p.status}] ${p.title} (${p.slug})`))

  if (fomcPosts.length === 0) {
    console.log('삭제할 FOMC 포스트 없음')
    return
  }

  // ── 4. bulk_delete API 호출
  const slugs = fomcPosts.map(p => p.slug)
  const deleteResp = await page.request.post(`${BASE}/api/posts/bulk_delete/`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    data: JSON.stringify({ slugs }),
  })

  const result = await deleteResp.json()
  console.log(`\n삭제 결과:`, result)
  expect(deleteResp.status()).toBe(200)
  expect(result.deleted).toBeGreaterThan(0)
  console.log(`✓ FOMC 포스트 ${result.deleted}개 삭제 완료`)

  // ── 5. 대시보드 스크린샷 (삭제 후)
  await page.goto(`${BASE}/dashboard`)
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: 'e2e/screenshots/dashboard-fomc-deleted.png', fullPage: true })
})
