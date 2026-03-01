# UI 점검 결과 (2026-03-01)

## 수정 완료된 버그

### Bug 1: 포스트 목록 최대 12개 제한
- **원인**: DRF 기본 `PageNumberPagination`이 클라이언트의 `?page_size` 파라미터를 무시
- **수정**: `blog/pagination.py` — `StandardPagination(page_size_query_param='page_size', max_page_size=1000)` 신규 추가
  `settings/base.py` — `DEFAULT_PAGINATION_CLASS`를 `blog.pagination.StandardPagination`으로 교체
- **결과**: 대시보드의 `?page_size=500` 요청이 정상 동작, 전체 포스트 반환

### Bug 2: 삭제 후 포스트가 5분간 잔존
- **원인**: `PostViewSet.list`에 `@cache_page(60 * 5)` 적용으로 DELETE 후에도 캐시된 목록 반환
- **수정**: `blog/views.py` — 인증 사용자는 캐시 bypass, 비인증 공개 목록만 5분 캐시 유지
- **결과**: 삭제 직후 `loadPosts()` 호출 시 DB에서 최신 목록 반환

---

## Playwright 점검 결과

### 공개 페이지 ✓ 통과

| 테스트 | 결과 | 비고 |
|--------|------|------|
| 홈 페이지 로드 | PASS | `e2e/screenshots/home.png` |
| 첫 번째 포스트 상세 | PASS | `e2e/screenshots/post-detail.png` |

### 대시보드 (인증 필요)

실행 방법:
```bash
BLOG_USER=admin BLOG_PASS=<비밀번호> npx playwright test e2e/audit.spec.js --grep "대시보드" --reporter=list
```

---

## FOMC 포스트 삭제

제목/슬러그에 "fomc"가 포함된 포스트를 `bulk_delete` API로 일괄 삭제.

실행 방법:
```bash
BLOG_USER=admin BLOG_PASS=<비밀번호> npx playwright test e2e/delete-fomc.spec.js --reporter=list
```

삭제 후 스크린샷: `e2e/screenshots/dashboard-fomc-deleted.png`

---

## 개선 제안 (다음 세션)

- [ ] 대시보드에 페이지네이션 UI (대용량 포스트 대비)
- [ ] 대시보드 검색창 추가 (현재 카테고리/상태 필터만 존재)
- [ ] 삭제 시 `confirm()` 대신 모달 다이얼로그 사용
- [ ] 감사(audit) 배지를 대시보드 카드에서도 표시
