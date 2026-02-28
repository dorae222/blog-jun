# Backend 개선 계획

> **마지막 업데이트**: 2026-03-01
> **담당**: @dorae222
> **관련 문서**: [CLAUDE.md](../CLAUDE.md)

## 개요
Django 5 + DRF 백엔드의 프로덕션 최적화. Docker 보안, 성능, 운영 안정성 강화 완료.

## 완료
### C-1. docker-compose.prod.yml 강화 ✅
- **완료일**: 2025-02-28
- **내용**:
  - 모든 서비스에 healthcheck 추가
  - depends_on condition (service_healthy) 적용
  - deploy.resources.limits 설정
  - IMAGE_TAG 변수 지원 (롤백용)
  - vLLM 환경변수 준비 (LLM_BASE_URL, LLM_MODEL)

### C-2. gunicorn.conf.py 생성 ✅
- **완료일**: 2025-02-28
- **내용**:
  - workers=5, gthread, threads=2
  - max_requests=1000 (메모리 누수 방지)
  - preload_app=True (메모리 절약)
  - 로그 파일 설정

### C-3. prod.py 보안 강화 ✅
- **완료일**: 2025-02-28
- **내용**:
  - 필수 환경변수 검증 (fail fast)
  - CONN_MAX_AGE=600 (커넥션 풀링)
  - SESSION/CSRF 쿠키 보안 (HttpOnly, SameSite)
  - DRF Throttling (anon 100/h, user 1000/h, chatbot_anon 5/h)
  - RotatingFileHandler + JSON 포맷 로깅
  - vLLM 연결 환경변수 준비

### C-5. backup.sh 생성 ✅
- **완료일**: 2025-02-28
- **내용**:
  - pg_dump + gzip 백업
  - 30일 보존 정책
  - Docker Compose 환경 지원

### C-6. Dockerfile 보안 강화 ✅
- **완료일**: 2025-02-28
- **내용**:
  - Multi-stage build (builder → production)
  - non-root user (appuser)
  - PYTHONOPTIMIZE=2
  - HEALTHCHECK 내장
  - gunicorn.conf.py 사용

### C-7. 쿼리 최적화 + 캐싱 ✅
- **완료일**: 2025-02-28
- **내용**:
  - post_list: 5분 캐시
  - search: 1분 캐시
  - dashboard_stats: 10분 캐시
  - public_stats: 5분 캐시

## 향후 계획
### C-8. 챗봇 vLLM 연동
- **우선순위**: P1 (중요)
- **예상 규모**: Large
- **내용**: Admin/Visitor 분리, vLLM 엔드포인트 연동
- **선행 조건**: lxd/llm-server 구축 완료

### C-9. pgvector 임베딩 마이그레이션
- **우선순위**: P2 (개선)
- **예상 규모**: Medium
- **내용**: Post 모델에 embedding 필드 추가, RAG 검색 품질 개선
- **선행 조건**: 콘텐츠 임포트 완료

## 체크리스트
- [x] Docker 보안 (non-root, healthcheck)
- [x] 프로덕션 설정 (gunicorn, prod.py)
- [x] 백업 스크립트
- [x] 쿼리 최적화 + 캐싱
- [ ] vLLM 챗봇 연동
- [ ] pgvector 임베딩

## 참고사항
- C-4는 사용하지 않음 (번호 건너뜀)
- Throttling 설정은 초기값이므로 트래픽 패턴 보고 조정 필요
