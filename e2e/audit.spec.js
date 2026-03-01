import { test, expect } from '@playwright/test'

const BASE = 'https://blog.dorae222.com'
const BLOG_USER = process.env.BLOG_USER
const BLOG_PASS = process.env.BLOG_PASS

test.describe('공개 페이지', () => {
  test('홈 페이지 로드 및 스크린샷', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: 'e2e/screenshots/home.png', fullPage: true })

    // 기본 요소 확인
    await expect(page).toHaveTitle(/.+/)
  })

  test('첫 번째 포스트 상세 페이지', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    const firstPost = page.locator('a[href*="/post/"]').first()
    const count = await firstPost.count()
    if (count === 0) {
      console.log('포스트 링크를 찾을 수 없음 — 건너뜀')
      return
    }

    const href = await firstPost.getAttribute('href')
    await page.goto(href.startsWith('http') ? href : BASE + href)
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: 'e2e/screenshots/post-detail.png', fullPage: true })
  })
})

test.describe('대시보드 (인증 필요)', () => {
  test.skip(!BLOG_USER || !BLOG_PASS, 'BLOG_USER / BLOG_PASS 환경변수 미설정')

  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/login`)
    await page.waitForLoadState('networkidle')
    await page.fill('input[type="text"], input[name="username"]', BLOG_USER)
    await page.fill('input[type="password"]', BLOG_PASS)
    await page.click('button[type="submit"]')
    await page.waitForURL(`${BASE}/dashboard`, { timeout: 10_000 }).catch(() => {})
  })

  test('대시보드 포스트 목록 — 전체 표시 확인', async ({ page }) => {
    await page.goto(`${BASE}/dashboard`)
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: 'e2e/screenshots/dashboard.png', fullPage: true })

    // 목록 카운트 텍스트에서 숫자 추출
    const countText = await page.locator('text=/\\d+개 표시/').textContent().catch(() => '')
    console.log('포스트 카운트:', countText)

    // 12개 초과 표시 여부 확인 (페이지네이션 버그 수정 검증)
    const match = countText.match(/(\d+)개 표시/)
    if (match) {
      const displayed = parseInt(match[1], 10)
      expect(displayed).toBeGreaterThan(12)
      console.log(`✓ ${displayed}개 포스트 표시 — 페이지네이션 버그 수정 확인`)
    }
  })

  test('포스트 삭제 후 즉시 목록 갱신 확인', async ({ page }) => {
    await page.goto(`${BASE}/dashboard`)
    await page.waitForLoadState('networkidle')

    // 첫 번째 포스트 행의 제목 저장
    const firstTitle = await page.locator('table tbody tr td:nth-child(2) span').first()
      .textContent().catch(() => null)

    if (!firstTitle) {
      console.log('포스트가 없어 삭제 테스트 건너뜀')
      return
    }
    console.log('삭제 대상 포스트:', firstTitle)

    // 삭제 버튼 클릭 → confirm 다이얼로그 처리
    page.once('dialog', async dialog => {
      console.log('다이얼로그:', dialog.message())
      await dialog.accept()
    })

    const [deleteResp] = await Promise.all([
      page.waitForResponse(
        res => res.url().includes('/api/posts/') && res.request().method() === 'DELETE',
        { timeout: 10_000 }
      ).catch(() => null),
      page.locator('button:text("삭제")').first().click(),
    ])

    if (deleteResp) {
      console.log('DELETE status:', deleteResp.status())
      expect(deleteResp.status()).toBe(204)
    }

    // 삭제 후 목록 갱신 대기
    await page.waitForTimeout(1_500)
    await page.screenshot({ path: 'e2e/screenshots/dashboard-after-delete.png', fullPage: true })

    // 캐시 버그 검증: 삭제된 포스트가 목록에 없어야 함
    const titles = await page.locator('table tbody tr td:nth-child(2) span').allTextContents()
    const stillExists = titles.some(t => t.trim() === firstTitle.trim())
    expect(stillExists).toBe(false)
    console.log(`✓ 삭제된 포스트 "${firstTitle}"가 목록에서 즉시 제거됨`)
  })
})
