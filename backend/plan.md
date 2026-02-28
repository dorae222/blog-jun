# Backend 개선 계획

## 완료된 작업

### C-1. docker-compose.prod.yml 강화
- 모든 서비스에 healthcheck 추가
- depends_on condition (service_healthy) 적용
- deploy.resources.limits 설정
- IMAGE_TAG 변수 지원 (롤백용)
- vLLM 환경변수 준비 (LLM_BASE_URL, LLM_MODEL)

### C-2. gunicorn.conf.py 생성
- workers=5, gthread, threads=2
- max_requests=1000 (메모리 누수 방지)
- preload_app=True (메모리 절약)
- 로그 파일 설정

### C-3. prod.py 보안 강화
- 필수 환경변수 검증 (fail fast)
- CONN_MAX_AGE=600 (커넥션 풀링)
- SESSION/CSRF 쿠키 보안 (HttpOnly, SameSite)
- DRF Throttling (anon 100/h, user 1000/h, chatbot_anon 5/h)
- RotatingFileHandler + JSON 포맷 로깅
- vLLM 연결 환경변수 준비

### C-5. backup.sh 생성
- pg_dump + gzip 백업
- 30일 보존 정책
- Docker Compose 환경 지원

### C-6. Dockerfile 보안 강화
- Multi-stage build (builder → production)
- non-root user (appuser)
- PYTHONOPTIMIZE=2
- HEALTHCHECK 내장
- gunicorn.conf.py 사용

### C-7. 쿼리 최적화 + 캐싱
- post_list: 5분 캐시
- search: 1분 캐시
- dashboard_stats: 10분 캐시
- public_stats: 5분 캐시

## 추후 작업 (별도 개발 사이클)
- 챗봇 vLLM 연동 (Admin/Visitor 분리)
- pgvector 임베딩 마이그레이션
