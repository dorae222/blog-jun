import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000'
const SCREENSHOT_DIR = './e2e/screenshots/ui-review'

const DEVICES = [
  { name: 'iPhone17', viewport: { width: 402, height: 874 }, isMobile: true },
  { name: 'iPhone17ProMax', viewport: { width: 440, height: 956 }, isMobile: true },
  { name: 'GalaxyS25Ultra', viewport: { width: 480, height: 1040 }, isMobile: true },
  { name: 'iPadAir-landscape', viewport: { width: 1180, height: 820 }, isMobile: false },
  { name: 'MacBookPro14', viewport: { width: 1512, height: 982 }, isMobile: false },
]

const PAGES = [
  { name: 'home', path: '/' },
  { name: 'posts', path: '/posts' },
  { name: 'posts-ai-card', path: '/posts/ai?view=card' },
  { name: 'posts-cloud', path: '/posts/cloud' },
  { name: 'about', path: '/about' },
]

async function waitForPage(page) {
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(500)
}

// 멀티 디바이스 x 멀티 페이지 스크린샷
for (const device of DEVICES) {
  test.describe(`${device.name} (${device.viewport.width}x${device.viewport.height})`, () => {
    test.use({ viewport: device.viewport })

    for (const pg of PAGES) {
      test(`${pg.name}`, async ({ page }) => {
        await page.goto(`${BASE_URL}${pg.path}`)
        await waitForPage(page)
        await page.screenshot({
          path: `${SCREENSHOT_DIR}/${device.name}-${pg.name}.png`,
          fullPage: true,
        })
        await expect(page.locator('body')).toBeVisible()
      })
    }

    // 포스트 상세 페이지 (동적 slug)
    test('post-detail', async ({ page }) => {
      await page.goto(`${BASE_URL}/posts`)
      await waitForPage(page)
      const firstPost = page.locator('a[href^="/post/"]').first()
      if (await firstPost.isVisible()) {
        const href = await firstPost.getAttribute('href')
        await page.goto(`${BASE_URL}${href}`)
        await waitForPage(page)
        await page.screenshot({
          path: `${SCREENSHOT_DIR}/${device.name}-post-detail.png`,
          fullPage: true,
        })
      }
    })
  })
}

// 인터랙션 테스트 (데스크탑)
test.describe('Interactions (Desktop)', () => {
  test.use({ viewport: { width: 1512, height: 982 } })

  test('category tab click', async ({ page }) => {
    await page.goto(`${BASE_URL}/posts`)
    await waitForPage(page)
    const aiTab = page.locator('a[href="/posts/ai"]').first()
    if (await aiTab.isVisible()) {
      await aiTab.click()
      await waitForPage(page)
      await page.screenshot({ path: `${SCREENSHOT_DIR}/interaction-ai-tab.png`, fullPage: true })
    }
  })

  test('view mode toggle', async ({ page }) => {
    await page.goto(`${BASE_URL}/posts/ai?view=card`)
    await waitForPage(page)
    const listBtn = page.locator('button[aria-label="목록형"]')
    if (await listBtn.isVisible()) {
      await listBtn.click()
      await waitForPage(page)
      await page.screenshot({ path: `${SCREENSHOT_DIR}/interaction-list-view.png`, fullPage: true })
    }
  })
})

// 인터랙션 테스트 (모바일)
test.describe('Interactions (Mobile)', () => {
  test.use({ viewport: { width: 402, height: 874 } })

  test('mobile menu', async ({ page }) => {
    await page.goto(`${BASE_URL}/`)
    await waitForPage(page)
    const hamburger = page.locator('button[aria-label="메뉴"]').first()
    if (await hamburger.isVisible()) {
      await hamburger.click()
      await page.waitForTimeout(300)
      await page.screenshot({ path: `${SCREENSHOT_DIR}/interaction-mobile-menu.png` })
    }
  })

  test('post detail TOC drawer', async ({ page }) => {
    await page.goto(`${BASE_URL}/posts`)
    await waitForPage(page)
    const firstPost = page.locator('a[href^="/post/"]').first()
    if (await firstPost.isVisible()) {
      const href = await firstPost.getAttribute('href')
      await page.goto(`${BASE_URL}${href}`)
      await waitForPage(page)
      const tocBtn = page.getByText('목차')
      if (await tocBtn.isVisible()) {
        await tocBtn.click()
        await page.waitForTimeout(300)
        await page.screenshot({ path: `${SCREENSHOT_DIR}/interaction-toc-drawer.png` })
      }
    }
  })
})
