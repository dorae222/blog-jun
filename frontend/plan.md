# Frontend 개선 계획

## 완료된 작업

### D-1. nginx.conf 보안 헤더
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin
- Content-Security-Policy (self + fonts + images + API)
- Strict-Transport-Security (HSTS 1년)
- Permissions-Policy (카메라/마이크/위치 차단)

### D-2. 정적 에셋 캐싱 + gzip 강화
- Vite 해시 파일 365일 캐시 + immutable
- gzip_comp_level 6
- gzip_vary on
- SSE chatbot 전용 location 블록 (proxy_buffering off)
- nginx health check endpoint (/nginx-health)

### D-3. Dockerfile 최적화
- npm ci (deterministic install)
- non-root nginx user
- HEALTHCHECK 내장

## 검증 방법
```bash
curl -I https://blog.dorae222.com/
# X-Frame-Options, CSP, HSTS 헤더 확인
```
