---
title: "LXD에서 Docker Compose 프로덕션 운영"
slug: "lxd-docker-compose-prod"
category: cloud
tags: ["lxd", "docker", "docker-compose", "production", "gpu"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# LXD에서 Docker Compose 프로덕션 운영

## 들어가며

이 시리즈의 마지막 글에서는 LXD 컨테이너 안에서 **Docker Compose로 프로덕션 스택을 운영**하는 방법을 다룬다. LXD가 서버 격리를, Docker가 애플리케이션 격리를 담당하는 Docker-in-LXD 패턴은 소규모 인프라에서 매우 효과적이다.

## LXD에서 Docker를 쓰는 이유

### 왜 Docker-in-LXD인가?

직접 Docker만 사용하면 되지 않을까? Docker-in-LXD가 추가적인 가치를 제공하는 상황이 있다.

| 시나리오 | Docker만 사용 | Docker-in-LXD |
|---------|-------------|---------------|
| 단일 서비스 | 충분 | 과도할 수 있음 |
| 서비스별 격리 | 네트워크로만 격리 | OS 수준 격리 |
| 다중 프로젝트 | Docker 네트워크 복잡 | 프로젝트별 컨테이너 |
| 리소스 관리 | cgroup 직접 설정 | LXD 프로파일로 간편 |
| 스냅샷/백업 | 볼륨별 관리 | OS 전체 스냅샷 |
| 마이그레이션 | 구성 파일 기반 | 라이브 마이그레이션 가능 |

Docker-in-LXD의 핵심 가치는 **프로젝트(서비스)별 완전한 격리**다. 하나의 물리 서버에서 여러 프로젝트를 운영할 때, 각 프로젝트가 독립된 OS 환경을 갖는다.

```
┌── 물리 서버 ──────────────────────────────────────────┐
│                                                       │
│  ┌── LXD: 블로그 서버 (10.0.0.10) ──────────────────┐ │
│  │  Docker Compose:                                  │ │
│  │  PostgreSQL + Redis + Django + React/Nginx        │ │
│  │  리소스: 4 vCPU, 8GB RAM                          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                       │
│  ┌── LXD: ML 서버 (10.0.0.20) ─────────────────────┐ │
│  │  Docker Compose:                                  │ │
│  │  Jupyter + MLflow + GPU 워크로드                   │ │
│  │  리소스: 8 vCPU, 32GB RAM, GPU                    │ │
│  └──────────────────────────────────────────────────┘ │
│                                                       │
│  ┌── LXD: 모니터링 (10.0.0.30) ────────────────────┐ │
│  │  Docker Compose:                                  │ │
│  │  Prometheus + Grafana + AlertManager              │ │
│  │  리소스: 2 vCPU, 4GB RAM                          │ │
│  └──────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

## security.nesting 상세

Docker-in-LXD의 핵심 설정인 `security.nesting`의 내부 동작을 이해해야 문제 발생 시 대응할 수 있다.

### 활성화되는 기능

`security.nesting: true`가 설정되면 다음이 변경된다:

```
1. AppArmor 프로파일 완화
   - 내부 마운트 작업 허용
   - overlay 파일시스템 마운트 허용

2. 네임스페이스 중첩
   - 컨테이너 내부에서 새로운 네임스페이스 생성 허용
   - PID, NET, MNT 등

3. cgroup v2 위임
   - 컨테이너 내부에서 cgroup 하위 트리 관리 허용
   - Docker의 리소스 제한 기능 동작
```

### overlay2 관련 추가 설정

```yaml
# overlay2 스토리지 드라이버에 필요
security.syscalls.intercept.mknod: "true"
security.syscalls.intercept.setxattr: "true"
```

이 설정이 없으면 Docker 이미지 빌드나 컨테이너 시작 시 다음과 같은 오류가 발생한다:

```
failed to register layer: error creating overlay mount ...
operation not permitted
```

### Docker 정상 동작 확인

```bash
# LXD 컨테이너 내부에서 확인
docker info | grep -E "Storage Driver|Cgroup"
# Storage Driver: overlay2
# Cgroup Driver: systemd
# Cgroup Version: 2

# 테스트 컨테이너 실행
docker run --rm hello-world
```

## Docker Compose 프로덕션 스택

### 전체 구조

실제 웹 서비스를 위한 Docker Compose 스택이다. PostgreSQL, Redis, Django/Gunicorn, React/Nginx로 구성된다.

```
project/
├── docker-compose.yml        # 서비스 정의
├── docker-compose.prod.yml   # 프로덕션 오버라이드
├── .env                      # 환경 변수
├── backend/
│   ├── Dockerfile
│   └── ...
└── frontend/
    ├── Dockerfile
    └── nginx.conf
```

### docker-compose.yml (베이스)

```yaml
# docker-compose.yml
services:
  db:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME:-myapp}
      POSTGRES_USER: ${DB_USER:-appuser}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD is required}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-appuser} -d ${DB_NAME:-myapp}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-appuser}:${DB_PASSWORD}@db:5432/${DB_NAME:-myapp}
      - REDIS_URL=redis://redis:6379/0
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - SECRET_KEY=${SECRET_KEY:?SECRET_KEY is required}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    name: myapp_postgres_data
  redis_data:
    name: myapp_redis_data
```

### docker-compose.prod.yml (프로덕션 오버라이드)

```yaml
# docker-compose.prod.yml
services:
  db:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          memory: 1G
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  backend:
    command: >
      gunicorn config.wsgi:application
      --bind 0.0.0.0:8000
      --workers 4
      --worker-class gthread
      --threads 2
      --timeout 120
      --access-logfile -
      --error-logfile -
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          memory: 512M
    logging:
      driver: json-file
      options:
        max-size: "20m"
        max-file: "5"

  frontend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

### 프로덕션 실행

```bash
# 프로덕션 설정으로 실행
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f --tail=50

# 특정 서비스 로그
docker compose logs -f backend
```

## 리소스 제한 전략

### LXD vs Docker 리소스 제한

리소스 제한은 두 레이어에서 설정할 수 있다.

```
┌── LXD 제한 (전체 컨테이너) ──────────────────┐
│  limits.cpu: 4                                │
│  limits.memory: 8GB                           │
│                                               │
│  ┌── Docker 제한 (개별 서비스) ─────────────┐ │
│  │  db:      CPU 1.0, RAM 2G               │ │
│  │  redis:   CPU 0.5, RAM 512M             │ │
│  │  backend: CPU 2.0, RAM 2G               │ │
│  │  frontend:CPU 0.5, RAM 256M             │ │
│  │  합계:    CPU 4.0, RAM ~4.75G           │ │
│  └─────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```

LXD 레벨에서 상한을 정하고, Docker 레벨에서 서비스별 배분을 하는 것이 권장 패턴이다.

### 리소스 모니터링

```bash
# Docker 서비스별 리소스 사용량
docker stats --no-stream

# 출력 예시:
# CONTAINER    CPU %   MEM USAGE / LIMIT   NET I/O
# backend      12.5%   450MiB / 2GiB       1.2MB / 800kB
# db           3.2%    1.1GiB / 2GiB       500kB / 200kB
# redis        0.5%    45MiB / 512MiB      100kB / 50kB
# frontend     0.1%    30MiB / 256MiB      2.5MB / 5MB

# LXD 컨테이너 전체 리소스 (호스트에서)
lxc info my-web-server | grep -A 10 Resources
```

## Healthcheck 패턴

### 의존성 기반 시작 순서

```yaml
services:
  backend:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

이렇게 하면 DB와 Redis가 healthy 상태가 된 후에야 backend가 시작된다.

### Healthcheck 설정 가이드

| 서비스 | 체크 방법 | interval | timeout | retries | start_period |
|--------|----------|----------|---------|---------|-------------|
| PostgreSQL | pg_isready | 10s | 5s | 5 | 30s |
| Redis | redis-cli ping | 10s | 5s | 5 | 10s |
| Django | curl /health/ | 30s | 10s | 3 | 40s |
| Nginx | curl / | 30s | 10s | 3 | 10s |

`start_period`는 서비스가 처음 시작될 때 healthcheck 실패를 무시하는 기간이다. 초기화가 오래 걸리는 서비스(DB 마이그레이션 등)에 충분한 시간을 부여한다.

## 볼륨 관리

### Named Volume (권장)

```yaml
volumes:
  postgres_data:
    name: myapp_postgres_data    # 명시적 이름
  redis_data:
    name: myapp_redis_data
```

```bash
# 볼륨 목록
docker volume ls

# 볼륨 상세 (저장 위치 확인)
docker volume inspect myapp_postgres_data

# 볼륨 백업
docker run --rm \
  -v myapp_postgres_data:/source:ro \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/postgres-backup.tar.gz -C /source .

# 볼륨 복원
docker run --rm \
  -v myapp_postgres_data:/target \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /target
```

### PostgreSQL 논리적 백업

```bash
# pg_dump로 백업
docker compose exec db pg_dump -U appuser myapp > backup.sql

# 복원
docker compose exec -T db psql -U appuser myapp < backup.sql
```

## 로그 관리

### JSON 파일 로그 드라이버 설정

```yaml
services:
  backend:
    logging:
      driver: json-file
      options:
        max-size: "20m"    # 파일당 최대 20MB
        max-file: "5"      # 최대 5개 파일 유지
```

이 설정이 없으면 로그가 무한히 쌓여 디스크를 가득 채울 수 있다.

### 로그 확인

```bash
# 실시간 로그 (최근 100줄부터)
docker compose logs -f --tail=100

# 특정 서비스의 특정 시간 이후 로그
docker compose logs --since="2026-03-22T00:00:00" backend

# 로그 파일 위치 확인
docker inspect --format='{{.LogPath}}' $(docker compose ps -q backend)
```

### 디스크 사용량 관리

```bash
# Docker 전체 디스크 사용량
docker system df

# 사용하지 않는 리소스 정리
docker system prune -f

# 오래된 이미지 정리
docker image prune -a --filter "until=168h"  # 7일 이상
```

## 자동 재시작

### restart 정책

```yaml
services:
  backend:
    restart: unless-stopped
```

| 정책 | 동작 |
|------|------|
| `no` | 재시작하지 않음 (기본값) |
| `always` | 항상 재시작 (수동 중지해도) |
| `unless-stopped` | 수동 중지하지 않는 한 재시작 |
| `on-failure` | 비정상 종료(exit code != 0) 시만 재시작 |

프로덕션에서는 `unless-stopped`를 권장한다. 서버 재부팅 시 Docker 데몬이 시작되면 컨테이너도 자동으로 시작된다.

### LXD + Docker 자동 시작 체인

```
서버 부팅
  → LXD 데몬 시작
    → boot.autostart가 설정된 LXD 컨테이너 시작
      → 컨테이너 내부 Docker 데몬 시작 (systemd)
        → restart: unless-stopped인 Docker 컨테이너 시작
```

LXD 프로파일에서 자동 시작 설정:

```yaml
config:
  boot.autostart: "true"
  boot.autostart.priority: "10"    # 낮은 번호가 먼저 시작
  boot.autostart.delay: "5"       # 시작 전 대기 시간 (초)
```

## GPU 패스스루

### GPU 패스스루란?

물리 서버의 GPU를 LXD 컨테이너에 직접 할당하는 기술이다. ML/AI 워크로드에서 컨테이너 격리를 유지하면서 GPU 가속을 사용할 수 있다.

### 기본 개념

```
┌── 물리 서버 ──────────────────────────────┐
│  GPU 0: RTX 3090 (PCI: 0000:01:00.0)     │
│  GPU 1: RTX 3090 (PCI: 0000:02:00.0)     │
│                                           │
│  ┌── LXD 컨테이너 (GPU 0 할당) ────────┐ │
│  │  nvidia-smi → GPU 0 사용 가능       │ │
│  │  Docker + NVIDIA Container Toolkit  │ │
│  └────────────────────────────────────┘ │
│                                           │
│  ┌── LXD 컨테이너 (GPU 1 할당) ────────┐ │
│  │  nvidia-smi → GPU 1 사용 가능       │ │
│  └────────────────────────────────────┘ │
└───────────────────────────────────────────┘
```

### LXD 프로파일에 GPU 추가

```yaml
# gpu-profile.yaml
config:
  security.nesting: "true"
  nvidia.runtime: "true"

devices:
  gpu0:
    type: gpu
    gputype: physical
    pci: "0000:01:00.0"    # lspci로 확인한 PCI 주소
```

또는 모든 GPU를 공유하는 방식:

```yaml
devices:
  gpu:
    type: gpu
    gputype: physical
```

### GPU 할당 확인

```bash
# LXD 컨테이너 내부에서
nvidia-smi

# Docker에서 GPU 사용 (NVIDIA Container Toolkit 필요)
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Tensor Parallelism 예시

복수 GPU를 활용한 대규모 모델 추론 구성이다.

```yaml
# docker-compose.gpu.yml
services:
  inference:
    image: my-ml-model:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2           # 2개 GPU 사용
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0,1
      - TENSOR_PARALLEL_SIZE=2
```

> GPU 패스스루는 호스트의 NVIDIA 드라이버 버전과 컨테이너의 CUDA 버전 호환성에 주의해야 한다. 호스트에 먼저 NVIDIA 드라이버를 설치하고, 컨테이너에는 NVIDIA Container Toolkit을 설치한다.

## 배포 자동화 패턴

### 수동 배포 스크립트

```bash
#!/bin/bash
# deploy.sh - 수동 배포 스크립트
set -euo pipefail

APP_DIR="/opt/app"
COMPOSE_FILE="${APP_DIR}/docker-compose.yml"
PROD_FILE="${APP_DIR}/docker-compose.prod.yml"

echo "=== 배포 시작 ==="

# 1. 소스 코드 업데이트
cd "${APP_DIR}"
git pull origin main

# 2. 이미지 빌드
echo "[1/4] 이미지 빌드 중..."
docker compose -f "${COMPOSE_FILE}" -f "${PROD_FILE}" build --no-cache

# 3. DB 마이그레이션 (backend 서비스로 실행)
echo "[2/4] DB 마이그레이션 실행 중..."
docker compose -f "${COMPOSE_FILE}" -f "${PROD_FILE}" run --rm backend \
    python manage.py migrate --noinput

# 4. 정적 파일 수집
echo "[3/4] 정적 파일 수집 중..."
docker compose -f "${COMPOSE_FILE}" -f "${PROD_FILE}" run --rm backend \
    python manage.py collectstatic --noinput

# 5. 서비스 재시작 (다운타임 최소화)
echo "[4/4] 서비스 재시작 중..."
docker compose -f "${COMPOSE_FILE}" -f "${PROD_FILE}" up -d

# 6. 헬스체크 대기
echo "헬스체크 대기 중..."
sleep 10
docker compose ps

# 7. 오래된 이미지 정리
docker image prune -f

echo "=== 배포 완료 ==="
```

### CI/CD 연동 패턴

GitHub Actions에서 SSH를 통해 LXD 컨테이너에 배포할 수 있다.

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USERNAME }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          proxy_host: ${{ secrets.JUMP_HOST }}
          proxy_username: ${{ secrets.JUMP_USERNAME }}
          proxy_key: ${{ secrets.JUMP_PRIVATE_KEY }}
          script: |
            cd /opt/app
            git pull origin main
            docker compose -f docker-compose.yml -f docker-compose.prod.yml build
            docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm backend python manage.py migrate --noinput
            docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
            docker image prune -f
```

이 워크플로우에서 `proxy_host`와 `proxy_key`는 SSH ProxyJump와 동일한 역할을 한다. GitHub Actions 러너가 Jump Host를 경유하여 LXD 컨테이너에 접속한다.

## 운영 체크리스트

프로덕션 배포 전 확인해야 할 항목이다.

### LXD 레이어

- [ ] `security.nesting: true` 설정
- [ ] `security.syscalls.intercept.mknod/setxattr` 설정
- [ ] 리소스 제한 (CPU, RAM) 설정
- [ ] 고정 IP 할당
- [ ] `boot.autostart` 설정
- [ ] ZFS 스냅샷 스케줄 설정

### Docker 레이어

- [ ] 모든 서비스에 `restart: unless-stopped`
- [ ] 모든 서비스에 `healthcheck` 설정
- [ ] 서비스별 `resource limits` 설정
- [ ] 로그 로테이션 (`max-size`, `max-file`) 설정
- [ ] Named volume 사용 (이름 명시)
- [ ] `.env` 파일에 비밀번호, API 키 분리

### 네트워크 레이어

- [ ] Cloudflare Tunnel 설정 및 systemd 등록
- [ ] SSL/TLS Cloudflare 자동 관리 확인
- [ ] DNS 레코드 설정 확인

### 백업

- [ ] LXD 스냅샷 자동화 (cron)
- [ ] PostgreSQL pg_dump 자동화
- [ ] 볼륨 백업 스크립트

## 마무리

Docker-in-LXD는 시스템 격리와 애플리케이션 컨테이너화를 결합한 실용적인 패턴이다. LXD 프로파일로 서버 환경을 표준화하고, 프로비저닝 스크립트로 소프트웨어를 자동 설치하고, Docker Compose로 애플리케이션 스택을 관리하고, Cloudflare Tunnel로 외부에 안전하게 노출하는 전체 파이프라인이 완성된다.

이 시리즈에서 다룬 내용을 정리하면:

1. **LXD 개요**: 시스템 컨테이너의 위치와 장점
2. **설치 및 설정**: ZFS, lxdbr0, preseed
3. **프로파일**: 리소스 제한, Docker-in-LXD 보안 설정
4. **프로비저닝**: Docker CE, SSH, 도구 자동 설치
5. **네트워킹**: 브릿지 NAT, SSH ProxyJump
6. **Cloudflare Tunnel**: 포트리스 외부 노출
7. **Docker Compose 운영**: 프로덕션 스택, GPU, 배포 자동화

이 아키텍처는 소규모~중규모 인프라에서 비용 효율적이고 관리가 간편한 운영 환경을 제공한다.

## 시리즈 안내

1. LXD 개요: 시스템 컨테이너의 세계
2. LXD 설치 및 초기 설정
3. LXD 프로파일로 인스턴스 생성
4. LXD 프로비저닝 자동화
5. LXD 네트워킹 & SSH ProxyJump
6. Cloudflare Tunnel로 LXD 컨테이너 외부 노출
7. **LXD에서 Docker Compose 프로덕션 운영** (현재 글)
