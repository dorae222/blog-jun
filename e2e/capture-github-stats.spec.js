import { test } from '@playwright/test'

test('GitHub Stats 섹션 클로즈업 캡처', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('https://blog.dorae222.com', { waitUntil: 'networkidle' })

  // GitHub API 대기
  await page.waitForTimeout(3500)

  // 전체 페이지 스크롤 → whileInView 트리거
  const pageHeight = await page.evaluate(() => document.body.scrollHeight)
  for (let y = 0; y <= pageHeight; y += 350) {
    await page.evaluate((s) => window.scrollTo(0, s), y)
    await page.waitForTimeout(55)
  }
  await page.waitForTimeout(2000)

  // GitHub Activity 섹션으로 이동
  await page.evaluate(() => {
    for (const el of document.querySelectorAll('h2')) {
      if (el.textContent.includes('GitHub')) {
        el.scrollIntoView({ behavior: 'instant', block: 'start' })
        break
      }
    }
  })
  await page.waitForTimeout(1200)

  // 섹션 element 클로즈업 캡처
  const section = await page.$('section.section-gradient-blue, section:has(h2)')
  // h2 GitHub이 있는 섹션 찾기
  const githubSection = await page.evaluateHandle(() => {
    for (const s of document.querySelectorAll('section')) {
      if (s.textContent.includes('GitHub Activity')) return s
    }
    return null
  })

  if (githubSection) {
    await githubSection.asElement()?.screenshot({ path: 'e2e/screenshots/github-section-closeup.png' })
  }

  // 뷰포트 캡처 (현재 보이는 화면)
  await page.screenshot({ path: 'e2e/screenshots/github-viewport.png' })
})
