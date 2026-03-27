---
paths:
  - "frontend/src/**/*.{jsx,js,css}"
---
# React Frontend Rules

- React 19 + Vite + Tailwind CSS v4 사용
- Framer Motion으로 애니메이션
- 컴포넌트 400줄 초과 시 분할 검토
- highlight.js 등 외부 CSS는 index.css의 @import로 추가 (Tailwind v4 + Vite 환경 제약)
- API 호출은 api.js의 기존 함수 사용
- 이미지 lazy loading 적용

## 카드/Callout 디자인 규칙
- border-left 좌측 액센트 사용 금지 — AI 생성 느낌을 줌
- 타입 구분: 배경색 틴트(6% opacity) + 컬러 아이콘/타이틀 조합 (VitePress 스타일)
- 대시보드 stat 카드: border-top 상단 액센트 사용
- 색상: `frontend/src/data/cardColors.js`의 CARD_COLORS 사용 — 직접 하드코딩 금지
- 새 색상 추가: cardColors.js에 추가 (hex, rgb, label 필수)
- 용도별 매핑 추가: 새 카테고리/상태/타입이 생기면 해당 MAP 상수에 추가
- 헬퍼 함수:
  - `getCardStyle(colorKey, { topAccent })` — 카드 컨테이너
  - `getBadgeStyle(colorKey)` — 배지/pill (bg + text color)
  - `getTitleColor(colorKey)` — 아이콘/타이틀
  - `getStatusColor(status)` — 상태 도트
- 용도별 MAP 상수: CALLOUT_MAP, STAT_MAP, POST_TYPE_MAP, STATUS_MAP, DOMAIN_MAP, AUDIT_ISSUE_MAP, COVERAGE_MAP
