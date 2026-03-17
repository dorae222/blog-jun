# Server Guide

## SSH 접속

### 접속 구조
```
MacBook → hj-remote (Jump Host) → blog-server (LXD Container)
```

### ~/.ssh/config 설정
```ssh
Host hj-remote
    HostName <hj-remote-ip>
    User <username>
    IdentityFile ~/.ssh/id_rsa

Host blog-server
    HostName 10.10.10.30
    User ubuntu
    ProxyJump hj-remote
```

### 접속 명령어
```bash
# blog-server 직접 접속
ssh blog-server

# 또는 수동 ProxyJump
ssh -J hj-remote ubuntu@10.10.10.30
```

## LXD 컨테이너 정보

| 항목 | 값 |
|------|------|
| 컨테이너명 | blog-server |
| 내부 IP | 10.10.10.30 |
| OS | Ubuntu |
| 프로젝트 경로 | /opt/blog-jun/ |

## 서버 내 디렉토리 구조

```
/opt/blog-jun/
├── backend/          # Django DRF API
├── frontend/         # React SPA (Nginx 서빙)
├── docker-compose.prod.yml
├── deploy.sh
├── .env              # 환경변수 (git 미추적)
└── Makefile
```

## Docker Compose 서비스 구성

| 서비스 | 이미지 | 포트 | 역할 |
|--------|--------|------|------|
| db | pgvector/pgvector:pg16 | 5432 (내부) | PostgreSQL + pgvector |
| redis | redis:7-alpine | 6379 (내부) | 캐시 + 세션 |
| backend | ./backend (빌드) | 8000 (내부) | Django + Gunicorn |
| frontend | ./frontend (빌드) | 80 | Nginx + React SPA |

외부 접근은 **Cloudflare Tunnel**(`blog-jun`, ID: `079ef309`)을 통해 `https://blog.dorae222.com`으로 라우팅된다.

## 유용한 관리 명령어

```bash
# 서버 접속 후
cd /opt/blog-jun

# 서비스 상태 확인
docker compose -f docker-compose.prod.yml ps

# 로그 확인
docker compose -f docker-compose.prod.yml logs -f backend    # 백엔드 로그
docker compose -f docker-compose.prod.yml logs -f frontend   # 프론트엔드 로그
docker compose -f docker-compose.prod.yml logs --tail=50      # 최근 50줄

# 서비스 재시작
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend

# DB 접속
docker compose -f docker-compose.prod.yml exec db psql -U blog_user -d blog_jun

# Django 쉘
docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# 마이그레이션
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 이미지 정리
docker image prune -f
```

## 배포 플로우

### 자동 배포 (MacBook에서 실행)
```bash
# 프로젝트 루트에서
./deploy.sh
```

**deploy.sh 동작 순서:**
1. SSH로 서버 접속 (ProxyJump 경유)
2. `git pull origin main`
3. `docker compose build --no-cache`
4. DB/Redis 기동 → 마이그레이션
5. 전체 서비스 재시작
6. 헬스체크 (https://blog.dorae222.com)

### 수동 배포 (서버에서 직접)
```bash
ssh blog-server
cd /opt/blog-jun
git pull origin main
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

## Git 동기화 경로

| 위치 | 경로 | 용도 |
|------|------|------|
| MacBook | ~/Documents/Obsidian/blog-jun/ | 개발 + 파이프라인 |
| hj-remote | ~/lxd-servers/blog-jun/ | 인프라 관리 |
| blog-server | /opt/blog-jun/ | 프로덕션 |
