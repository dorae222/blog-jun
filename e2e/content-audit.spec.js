/**
 * content-audit.spec.js
 * 배포된 블로그 포스트 렌더링 품질 감사 스크립트
 *
 * 점검 항목:
 *  - render_error   : ErrorBoundary 오류 텍스트 감지
 *  - wiki_links     : [[...]] 미변환 위키링크 잔류
 *  - katex_error    : .katex-error 요소 존재
 *  - empty_content  : 본문 100자 미만
 *  - broken_images  : HTTP 404 이미지 응답 감지 (response intercept)
 *
 * 실행:
 *   npx playwright test e2e/content-audit.spec.js --reporter=line
 *
 * 출력:
 *   e2e/audit-results/content-audit.json
 *   e2e/audit-results/screenshots/*.png
 */

import { test } from '@playwright/test'
import fs from 'fs'
import path from 'path'

const BASE = 'https://blog.dorae222.com'
const API_BASE = `${BASE}/api`
const PAGE_SIZE = 50
const RESULTS_DIR = 'e2e/audit-results'
const SCREENSHOTS_DIR = `${RESULTS_DIR}/screenshots`
const REPORT_PATH = `${RESULTS_DIR}/content-audit.json`

// 전체 타임아웃: 포스트 수 × 평균 처리 시간 여유분
test.setTimeout(30 * 60 * 1000) // 30분

/** API로 전체 published 포스트 목록 수집 */
async function fetchAllPosts(request) {
  const posts = []
  let page = 1
  let hasMore = true

  while (hasMore) {
    const url = `${API_BASE}/posts/?status=published&page_size=${PAGE_SIZE}&page=${page}`
    const resp = await request.get(url)
    if (!resp.ok()) {
      console.error(`API 호출 실패: ${url} → ${resp.status()}`)
      break
    }
    const data = await resp.json()

    // DRF 페이지네이션: { count, next, results } 구조 가정
    const results = data.results ?? data
    posts.push(...results)

    hasMore = !!data.next
    page++
  }
  return posts
}

/** 단일 포스트 페이지 감사 */
async function auditPost(page, post) {
  const url = `${BASE}/post/${post.slug}`
  const issues = []
  const brokenImageUrls = []

  // 이미지 404 감지 (response intercept)
  page.on('response', resp => {
    if (
      resp.status() === 404 &&
      /\.(png|jpg|jpeg|gif|webp|svg)(\?|$)/i.test(resp.url())
    ) {
      brokenImageUrls.push(resp.url())
    }
  })

  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30_000 })
  } catch {
    issues.push({ type: 'load_timeout', detail: 'networkidle 타임아웃' })
    return { issues, brokenImageUrls }
  }

  // 1. render_error: ErrorBoundary 텍스트 감지
  const errorText = await page
    .locator('text=콘텐츠를 렌더링하는 중 오류가 발생했습니다')
    .count()
  if (errorText > 0) {
    issues.push({ type: 'render_error', detail: 'ErrorBoundary 활성화' })
  }

  // 2. wiki_links: article 안에 [[ 또는 ]] 잔류
  const articleText = await page
    .locator('article')
    .textContent()
    .catch(() => '')
  if (articleText.includes('[[') || articleText.includes(']]')) {
    // 샘플 추출 (최대 3개)
    const matches = [...articleText.matchAll(/\[\[([^\]]+)\]\]/g)]
      .slice(0, 3)
      .map(m => m[0])
    issues.push({
      type: 'wiki_links',
      detail: `미변환 위키링크 ${matches.length}건+`,
      samples: matches,
    })
  }

  // 3. katex_error: .katex-error 요소
  const katexErrors = await page.locator('.katex-error').count()
  if (katexErrors > 0) {
    issues.push({ type: 'katex_error', detail: `KaTeX 오류 ${katexErrors}개` })
  }

  // 4. empty_content: 본문 100자 미만
  const bodyLen = articleText.trim().length
  if (bodyLen < 100) {
    issues.push({
      type: 'empty_content',
      detail: `본문 ${bodyLen}자 (기준: 100자)`,
    })
  }

  // 5. broken_images: response intercept 결과 취합
  if (brokenImageUrls.length > 0) {
    issues.push({
      type: 'broken_images',
      detail: `404 이미지 ${brokenImageUrls.length}개`,
      urls: brokenImageUrls,
    })
  }

  return { issues, brokenImageUrls }
}

test('전체 포스트 렌더링 감사', async ({ page, request }) => {
  // 출력 디렉토리 생성
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true })

  // 1. 전체 포스트 목록 수집
  console.log('포스트 목록 수집 중...')
  const posts = await fetchAllPosts(request)
  console.log(`총 ${posts.length}개 포스트 발견`)

  if (posts.length === 0) {
    console.log('포스트가 없습니다. 감사를 건너뜁니다.')
    return
  }

  // 2. 결과 누적
  const report = {
    timestamp: new Date().toISOString(),
    base_url: BASE,
    total: posts.length,
    checked: 0,
    clean: 0,
    with_issues: 0,
    issue_breakdown: {
      render_error: 0,
      wiki_links: 0,
      katex_error: 0,
      empty_content: 0,
      broken_images: 0,
      load_timeout: 0,
    },
    posts_with_issues: [],
  }

  // 3. 포스트 순차 방문
  for (let i = 0; i < posts.length; i++) {
    const post = posts[i]
    const progress = `[${i + 1}/${posts.length}]`
    process.stdout.write(`\r${progress} 감사 중: ${post.slug.substring(0, 60)}`)

    const { issues } = await auditPost(page, post)
    report.checked++

    if (issues.length === 0) {
      report.clean++
    } else {
      report.with_issues++

      // issue_breakdown 집계
      for (const issue of issues) {
        if (issue.type in report.issue_breakdown) {
          report.issue_breakdown[issue.type]++
        }
      }

      // 스크린샷 저장
      const screenshotName = `${post.slug.replace(/[^a-z0-9-]/g, '_')}.png`
      const screenshotPath = path.join(SCREENSHOTS_DIR, screenshotName)
      await page
        .screenshot({ path: screenshotPath, fullPage: true })
        .catch(() => {})

      report.posts_with_issues.push({
        id: post.id,
        slug: post.slug,
        title: post.title,
        url: `${BASE}/post/${post.slug}`,
        issues,
        screenshot: screenshotPath,
      })
    }

    // 중간 저장 (50개마다)
    if ((i + 1) % 50 === 0) {
      fs.writeFileSync(REPORT_PATH, JSON.stringify(report, null, 2))
    }
  }

  // 4. 최종 리포트 저장
  fs.writeFileSync(REPORT_PATH, JSON.stringify(report, null, 2))

  // 5. 콘솔 요약
  console.log('\n\n=== 감사 완료 ===')
  console.log(`총 포스트: ${report.total}`)
  console.log(`정상:       ${report.clean}`)
  console.log(`문제 있음:  ${report.with_issues}`)
  console.log('이슈 분류:')
  for (const [type, count] of Object.entries(report.issue_breakdown)) {
    if (count > 0) console.log(`  ${type}: ${count}`)
  }
  console.log(`\n리포트 저장: ${REPORT_PATH}`)
  console.log(`스크린샷:   ${SCREENSHOTS_DIR}/`)
})
