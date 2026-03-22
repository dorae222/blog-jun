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
