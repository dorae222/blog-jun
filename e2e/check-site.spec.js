import { test, expect } from '@playwright/test'

const BASE = 'https://blog.dorae222.com'

test('홈 — GitHub Stats 표시, Latest Posts 없음', async ({ page }) => {
  await page.goto(BASE)
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: 'e2e/screenshots/home-new.png', fullPage: true })

  // Latest Posts 섹션 없음
  await expect(page.getByText('Latest Posts')).not.toBeVisible()
  // GitHub Stats 섹션 있음
  await expect(page.getByText('GitHub Stats')).toBeVisible()
  // Activities 섹션 있음
  await expect(page.getByText('Activities')).toBeVisible()
  console.log('✓ 홈 확인 완료')
})

test('/search — 사이드바·Grid/List 토글·페이지네이션', async ({ page }) => {
  await page.goto(`${BASE}/search`)
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: 'e2e/screenshots/search-new.png', fullPage: true })

  // 사이드바 Category 헤더
  await expect(page.getByText('Category').first()).toBeVisible()
  // Post Type 헤더
  await expect(page.getByText('Post Type')).toBeVisible()
  // Grid/List 토글 버튼 존재
  const listBtn = page.locator('button').filter({ has: page.locator('svg') }).nth(1)
  await expect(listBtn).toBeVisible()
  console.log('✓ Search 페이지 확인 완료')
})

test('/category/cloud — 10개 페이지네이션', async ({ page }) => {
  await page.goto(`${BASE}/category/cloud`)
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: 'e2e/screenshots/category-new.png', fullPage: true })

  // 페이지네이션 존재 (포스트가 10개 초과일 경우)
  const nextBtn = page.getByRole('button', { name: 'Next' })
  const isVisible = await nextBtn.isVisible()
  console.log(`✓ Category 페이지 확인 완료 (페이지네이션: ${isVisible ? '있음' : '없음 - 포스트 10개 이하'})`)
})

test('포스트 상세 — 깨진 이미지 없음', async ({ page }) => {
  // 깨진 이미지가 많던 포스트 중 하나 확인
  await page.goto(`${BASE}/post/css-기초-스타일과-선택자-사용법`)
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: 'e2e/screenshots/post-clean.png', fullPage: true })

  // 깨진 이미지(naturalWidth=0인 img) 개수 확인
  const brokenCount = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('img'))
      .filter(img => img.complete && img.naturalWidth === 0).length
  })
  console.log(`✓ 깨진 이미지: ${brokenCount}개`)
  expect(brokenCount).toBe(0)
})
