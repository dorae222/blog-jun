# SEO 관리 규칙

## 현재 SEO 인프라 (2026-03-27 적용)

| 요소 | 위치 | 설명 |
|------|------|------|
| sitemap.xml | `backend/blog/sitemaps.py` → `/sitemap.xml` | 발행된 포스트 전체 XML |
| robots.txt | `backend/blog/sitemaps.py` → `/robots.txt` | 크롤링 허용 범위 |
| 동적 meta tags | `frontend/src/pages/PostView.jsx` | 포스트별 title/description/OG/canonical |
| JSON-LD | `frontend/src/pages/PostView.jsx` | Article 스키마 |
| 카테고리 title | `frontend/src/pages/PostsPage.jsx` | 카테고리별 동적 title |
| GA4 | `frontend/index.html` | G-T0Q3NR8HJJ |

---

## 업데이트 시나리오별 대응

### 포스트 추가/수정
- **별도 작업 없음** — `sitemap.xml`은 DB에서 실시간 생성, `PostView` Helmet은 API 데이터 기반
- 배포만 하면 자동 반영

### 새 카테고리/서브카테고리 추가
- `frontend/src/data/categories.js`의 `CATEGORY_TREE`에 항목 추가
- `PostsPage.jsx`의 `pageTitle`은 `CATEGORY_TREE` 기반이라 자동 반영

### 도메인 변경
수정 필요한 파일:
1. `backend/config/settings/base.py` — `SITE_URL` 환경변수 (`.env.prod`)
2. `frontend/index.html` — fallback `og:url`
3. `frontend/src/pages/PostView.jsx` — `canonicalUrl` 하드코딩 부분

> 이상적으로는 `PostView.jsx`의 `https://blog.dorae222.com`도 env 기반으로 관리해야 함
> 현재는 하드코딩이므로 도메인 변경 시 반드시 수정 필요

### GA4 Measurement ID 변경
1. `frontend/index.html` — `gtag('config', 'G-XXXXXXXX')` 업데이트
2. `nginx.conf`의 CSP `script-src`에 새 도메인이 다르면 업데이트

---

## 신규 페이지 추가 시 SEO 체크리스트

새 페이지(`frontend/src/pages/`)를 만들 때:
- [ ] `import { Helmet } from 'react-helmet-async'` 추가
- [ ] `<Helmet><title>{페이지명} | HJ Tech Blog</title></Helmet>` 추가
- [ ] 콘텐츠 페이지라면 `description` meta도 추가

---

## 정기 점검 (월 1회 권장)

1. **Google Search Console** → 색인 현황, 크롤링 오류 확인
2. **sitemap.xml** 제출 상태 확인 (최초 1회 제출 후 자동)
3. 포스트 수 대비 색인된 URL 수 확인
4. Core Web Vitals 점수 확인

---

## 추가 개선 가능 항목 (미적용)

| 항목 | 효과 | 난이도 |
|------|------|--------|
| RSS/Atom XML 피드 | 피드 구독자 유입 | 낮음 |
| 홈/About 페이지 Helmet | 추가 페이지 색인 | 낮음 |
| og:image 자동 생성 | SNS 공유 품질 | 중간 |
| PostView.jsx 도메인 env화 | 도메인 변경 대응 | 낮음 |
