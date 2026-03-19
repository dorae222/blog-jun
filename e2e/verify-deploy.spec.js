import { test, expect } from '@playwright/test'

const SCREENSHOT_DIR = './e2e/screenshots'

// --- 4-1. 기존 페이지 검증 ---

test('홈 페이지 렌더링', async ({ page }) => {
  await page.goto('/')
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: `${SCREENSHOT_DIR}/verify-home.png`, fullPage: true })
  await expect(page).toHaveTitle(/blog/i)
})

test('Posts(검색) 페이지 렌더링', async ({ page }) => {
  await page.goto('/search')
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: `${SCREENSHOT_DIR}/verify-search.png`, fullPage: true })
  // 포스트 목록 또는 검색 UI 존재
  const body = page.locator('body')
  await expect(body).toBeVisible()
})

test('포스트 상세 페이지 렌더링', async ({ page }) => {
  // 검색 페이지에서 첫 번째 포스트 링크 가져오기
  await page.goto('/search')
  await page.waitForLoadState('networkidle')
  const firstPost = page.locator('a[href^="/post/"]').first()
  if (await firstPost.isVisible()) {
    const href = await firstPost.getAttribute('href')
    await page.goto(href)
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: `${SCREENSHOT_DIR}/verify-post.png`, fullPage: true })
  }
})

test('About 페이지 렌더링', async ({ page }) => {
  await page.goto('/about')
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: `${SCREENSHOT_DIR}/verify-about.png`, fullPage: true })
  const body = page.locator('body')
  await expect(body).toBeVisible()
})

// --- 4-2. 신규 페이지 검증 ---

test('Architecture 페이지 렌더링', async ({ page }) => {
  await page.goto('/architecture')
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: `${SCREENSHOT_DIR}/verify-architecture.png`, fullPage: true })

  // 필터 버튼 존재 확인 (All, Dense, MoE, Hybrid)
  const filterButtons = page.locator('button')
  const allButton = filterButtons.filter({ hasText: /All/i })
  await expect(allButton.first()).toBeVisible()
})

test('Papers 페이지 렌더링', async ({ page }) => {
  await page.goto('/papers')
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: `${SCREENSHOT_DIR}/verify-papers.png`, fullPage: true })

  // 페이지가 정상 렌더링되었는지 확인
  const body = page.locator('body')
  await expect(body).toBeVisible()
})

// --- 4-3. Header 네비게이션 검증 ---

test('Header에 5개 네비게이션 링크 존재', async ({ page }) => {
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  const nav = page.locator('header, nav')
  const expectedLinks = ['Home', 'Posts', 'Architecture', 'Papers', 'About']

  for (const linkText of expectedLinks) {
    const link = nav.locator(`a`).filter({ hasText: new RegExp(linkText, 'i') })
    await expect(link.first()).toBeVisible({ timeout: 5000 })
  }
})

test('Header 링크 클릭 시 올바른 페이지 이동', async ({ page }) => {
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  const routes = [
    { text: 'Architecture', path: '/architecture' },
    { text: 'Papers', path: '/papers' },
  ]

  for (const { text, path } of routes) {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    const link = page.locator('header a, nav a').filter({ hasText: new RegExp(text, 'i') }).first()
    await link.click()
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain(path)
  }
})

// --- 4-4. 다기종 뷰포트 캡처 ---

const DEVICES = [
  { name: 'iphone-15-pro',       width: 393,  height: 852  },
  { name: 'samsung-galaxy-s24',  width: 360,  height: 780  },
  { name: 'ipad-air-landscape',  width: 1180, height: 820  },
  { name: 'macbook-pro-14',      width: 1512, height: 982  },
]

const PAGES = [
  { name: 'home',   path: '/' },
  { name: 'search', path: '/search' },
  { name: 'about',  path: '/about' },
]

for (const device of DEVICES) {
  for (const pg of PAGES) {
    test(`[${device.name}] ${pg.name} 페이지 캡처`, async ({ browser }) => {
      const context = await browser.newContext({
        viewport: { width: device.width, height: device.height },
      })
      const page = await context.newPage()
      await page.goto(pg.path)
      await page.waitForLoadState('networkidle')

      await page.screenshot({
        path: `${SCREENSHOT_DIR}/${device.name}/${pg.name}.png`,
        fullPage: true,
      })

      // 헤더 로고 표시 확인
      const logo = page.locator('header a').filter({ hasText: /HJ/i }).first()
      await expect(logo).toBeVisible()

      // 모바일(너비 < 768)에서 햄버거 버튼 확인
      if (device.width < 768) {
        const hamburger = page.locator('header button[aria-label="메뉴 열기"]')
        await expect(hamburger).toBeVisible()
      }

      await context.close()
    })
  }
}

// 포스트 상세 다기종 캡처
for (const device of DEVICES) {
  test(`[${device.name}] post 상세 캡처`, async ({ browser }) => {
    const context = await browser.newContext({
      viewport: { width: device.width, height: device.height },
    })
    const page = await context.newPage()
    await page.goto('/search')
    await page.waitForLoadState('networkidle')
    const firstPost = page.locator('a[href^="/post/"]').first()
    if (await firstPost.isVisible()) {
      const href = await firstPost.getAttribute('href')
      await page.goto(href)
      await page.waitForLoadState('networkidle')
      await page.screenshot({
        path: `${SCREENSHOT_DIR}/${device.name}/post.png`,
        fullPage: true,
      })
    }
    await context.close()
  })
}

// --- 4-5. Posts 드롭다운 검증 (데스크탑) ---

test('데스크탑 Posts 드롭다운 hover 동작', async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 1512, height: 982 },
  })
  const page = await context.newPage()
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  // Posts 버튼에 hover
  const postsBtn = page.locator('header button').filter({ hasText: /Posts/i })
  await postsBtn.hover()
  await page.waitForTimeout(300)

  // 드롭다운 메뉴 항목 확인
  const dropdown = page.locator('header').getByText('All Posts')
  await expect(dropdown).toBeVisible({ timeout: 3000 })

  await context.close()
})

// --- 4-6. 모바일 Posts 아코디언 검증 ---

test('모바일 햄버거 → Posts 아코디언 동작', async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 393, height: 852 },
  })
  const page = await context.newPage()
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  // 햄버거 메뉴 클릭
  const hamburger = page.locator('header button[aria-label="메뉴 열기"]')
  await expect(hamburger).toBeVisible()
  await hamburger.click()
  await page.waitForTimeout(300)

  // Posts 아코디언 버튼 클릭
  const postsAccordion = page.locator('nav button').filter({ hasText: /Posts/i })
  await postsAccordion.click()
  await page.waitForTimeout(300)

  // 하위 메뉴 확인
  const allPosts = page.locator('nav').getByText('All Posts')
  await expect(allPosts).toBeVisible({ timeout: 3000 })

  await context.close()
})
