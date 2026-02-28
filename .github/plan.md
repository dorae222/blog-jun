# CI/CD 개선 계획

> **마지막 업데이트**: 2026-03-01
> **담당**: @dorae222
> **관련 문서**: [CLAUDE.md](../CLAUDE.md)

## 개요
GitHub Actions CI/CD 파이프라인. PR 체크(ci.yml) + main 배포(deploy.yml) 자동화 완료.

## 완료
### E-1. deploy.yml 개선 ✅
- **완료일**: 2025-02-28
- **내용**:
  - 이미지 태그: latest + ${{ github.sha }} (롤백 지원)
  - DB 준비 대기 후 마이그레이션 (서비스 시작 전)
  - Health check 10회 재시도 (5초 간격)
  - Docker build cache (type=gha) 유지

## 향후 계획
### E-2. ci.yml 테스트 강화
- **우선순위**: P2 (개선)
- **예상 규모**: Small
- **내용**: pytest 커버리지 리포트, lint 체크 추가
- **선행 조건**: 콘텐츠 임포트 후 안정화

## 롤백 방법
```bash
# 특정 커밋의 이미지로 롤백
IMAGE_TAG=<commit-sha> docker compose -f docker-compose.prod.yml up -d
```

## 체크리스트
- [x] deploy.yml 자동 배포
- [x] 이미지 태그 롤백 지원
- [x] Health check 재시도
- [ ] 테스트 커버리지 리포트

## 참고사항
- ProxyJump 경유 SSH 배포 (MacBook → hj-remote → blog-server)
- Docker build cache type=gha로 빌드 시간 단축
