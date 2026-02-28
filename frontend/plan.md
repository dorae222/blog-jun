# Frontend 개선 계획

> **마지막 업데이트**: 2026-03-01
> **담당**: @dorae222
> **관련 문서**: [CLAUDE.md](../CLAUDE.md)

## 개요
React 19 + Vite + Tailwind CSS v4 프론트엔드. nginx 보안/성능 최적화 완료, UI 디자인 개선 예정.

## 완료
### D-1. nginx.conf 보안 헤더 ✅
- **완료일**: 2025-02-28
- **내용**:
  - X-Frame-Options: SAMEORIGIN
  - X-Content-Type-Options: nosniff
  - Referrer-Policy: strict-origin-when-cross-origin
  - Content-Security-Policy (self + fonts + images + API)
  - Strict-Transport-Security (HSTS 1년)
  - Permissions-Policy (카메라/마이크/위치 차단)

### D-2. 정적 에셋 캐싱 + gzip 강화 ✅
- **완료일**: 2025-02-28
- **내용**:
  - Vite 해시 파일 365일 캐시 + immutable
  - gzip_comp_level 6
  - gzip_vary on
  - SSE chatbot 전용 location 블록 (proxy_buffering off)
  - nginx health check endpoint (/nginx-health)

### D-3. Dockerfile 최적화 ✅
- **완료일**: 2025-02-28
- **내용**:
  - npm ci (deterministic install)
  - non-root nginx user
  - HEALTHCHECK 내장

## 향후 계획
### D-4. UI 디자인 수정
- **우선순위**: P1 (중요)
- **예상 규모**: Medium
- **내용**: 콘텐츠 임포트 후 전체 UI/UX 검토 및 개선
- **선행 조건**: 파이프라인 테스트 임포트 완료

### D-5. PostTemplate 콘텐츠 템플릿 개선
- **우선순위**: P1 (중요)
- **예상 규모**: Medium
- **내용**: 카테고리별 렌더링 최적화, 코드 블록/수식 표시 개선
- **선행 조건**: 테스트 콘텐츠 확인 후

## 검증
```bash
curl -I https://blog.dorae222.com/
# X-Frame-Options, CSP, HSTS 헤더 확인
```

## 체크리스트
- [x] nginx 보안 헤더
- [x] 정적 에셋 캐싱 + gzip
- [x] Dockerfile 최적화
- [ ] UI 디자인 수정
- [ ] 콘텐츠 템플릿 개선

## 참고사항
- CSP 정책은 외부 리소스 추가 시 업데이트 필요
- SSE chatbot proxy_buffering off 설정 필수
