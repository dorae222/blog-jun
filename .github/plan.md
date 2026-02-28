# CI/CD 개선 계획

## 완료된 작업

### E-1. deploy.yml 개선
- 이미지 태그: latest + ${{ github.sha }} (롤백 지원)
- DB 준비 대기 후 마이그레이션 (서비스 시작 전)
- Health check 10회 재시도 (5초 간격)
- Docker build cache (type=gha) 유지

## 롤백 방법
```bash
# 특정 커밋의 이미지로 롤백
IMAGE_TAG=<commit-sha> docker compose -f docker-compose.prod.yml up -d
```
