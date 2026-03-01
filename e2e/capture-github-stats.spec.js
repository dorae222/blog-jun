import { test } from '@playwright/test'

test('GitHub Stats 섹션 캡처', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('https://blog.dorae222.com', { waitUntil: 'networkidle' })

  // GitHub API 응답 대기
  await page.waitForTimeout(3000)

  // 전체 페이지 스크롤 → whileInView 트리거
  const pageHeight = await page.evaluate(() => document.body.scrollHeight)
  for (let y = 0; y <= pageHeight; y += 350) {
    await page.evaluate((s) => window.scrollTo(0, s), y)
    await page.waitForTimeout(60)
  }

  // 애니메이션 완료 대기
  await page.waitForTimeout(2500)

  // GitHub 섹션으로 스크롤
  await page.evaluate(() => {
    for (const el of document.querySelectorAll('h2')) {
      if (el.textContent.includes('GitHub')) {
        el.scrollIntoView({ behavior: 'instant', block: 'start' })
        break
      }
    }
  })
  await page.waitForTimeout(800)

  await page.screenshot({ path: 'e2e/screenshots/github-stats-new.png', fullPage: true })
})
