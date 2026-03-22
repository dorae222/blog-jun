---
title: "Docker Compose 실전: 멀티 컨테이너 오케스트레이션"
slug: "docker-compose-practice"
category: cloud
tags: ["docker", "docker-compose", "orchestration"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# Docker Compose 실전: 멀티 컨테이너 오케스트레이션

## 1. Docker Compose란?

Docker Compose는 여러 컨테이너로 구성된 애플리케이션을 YAML 파일 하나로 정의하고 관리하는 도구이다. `docker compose up` 한 줄로 전체 스택을 구동할 수 있으며, 개발 환경과 CI/CD 파이프라인에서 핵심적으로 활용된다.

```bash
# 기본 명령어
docker compose up -d          # 백그라운드 실행
docker compose down            # 컨테이너·네트워크 정리
docker compose ps              # 실행 중인 서비스 확인
docker compose logs -f web     # 특정 서비스 로그 추적
docker compose exec web bash   # 실행 중인 컨테이너에 접속
```

## 2. docker-compose.yml 구조

docker-compose.yml은 크게 4가지 최상위 키로 구성된다.

```yaml
# docker-compose.yml 기본 구조
services:       # 컨테이너(서비스) 정의
  web:
    image: nginx:latest
  db:
    image: postgres:16

networks:       # 네트워크 정의
  backend:
    driver: bridge

volumes:        # 볼륨 정의
  db-data:
    driver: local

configs:        # 설정 파일 (Swarm 모드)
secrets:        # 시크릿 관리 (Swarm 모드)
```

> **참고**: Compose V2에서는 `version` 키가 더 이상 필수가 아니다. Docker Compose는 자동으로 최신 스펙을 적용한다.

## 3. 서비스 정의 상세

### 3.1 image vs build

```yaml
services:
  # 기존 이미지 사용
  nginx:
    image: nginx:1.25-alpine

  # Dockerfile로 빌드
  web:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
      args:
        PYTHON_VERSION: "3.12"
    image: my-app:latest    # 빌드 결과에 태그 부여
```

### 3.2 ports — 포트 매핑

```yaml
services:
  web:
    ports:
      - "8000:8000"         # HOST:CONTAINER
      - "127.0.0.1:8080:80" # 특정 인터페이스 바인딩
      - "3000-3005:3000-3005" # 포트 범위
```

### 3.3 environment / env_file — 환경 변수

```yaml
services:
  web:
    # 직접 정의
    environment:
      - DEBUG=false
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb

    # 파일에서 로드
    env_file:
      - .env
      - .env.production
```

### 3.4 volumes — 볼륨 마운트

```yaml
services:
  web:
    volumes:
      - ./src:/app/src              # Bind mount (개발용)
      - static-files:/app/static    # Named volume
      - /app/node_modules           # Anonymous volume (보호용)

  db:
    volumes:
      - db-data:/var/lib/postgresql/data  # DB 데이터 영속성

volumes:
  static-files:
  db-data:
```

### 3.5 restart — 재시작 정책

```yaml
services:
  web:
    restart: unless-stopped   # 수동 중지 외에는 항상 재시작

# 옵션: no / always / on-failure / unless-stopped
```

### 3.6 command / entrypoint — 실행 명령 오버라이드

```yaml
services:
  web:
    image: python:3.12-slim
    entrypoint: ["python", "manage.py"]
    command: ["runserver", "0.0.0.0:8000"]

  worker:
    image: python:3.12-slim
    command: celery -A config worker --loglevel=info
```

## 4. depends_on과 서비스 의존성

### 기본 의존성 (시작 순서만 보장)

```yaml
services:
  web:
    depends_on:
      - db
      - redis
  db:
    image: postgres:16-alpine
  redis:
    image: redis:7-alpine
```

> **주의**: 기본 `depends_on`은 컨테이너 **시작 순서**만 보장할 뿐, 서비스가 **준비 완료**되었는지는 보장하지 않는다.

### 조건부 의존성 (healthcheck 기반)

```yaml
services:
  web:
    depends_on:
      db:
        condition: service_healthy    # DB가 healthy일 때만 시작
      redis:
        condition: service_started

  db:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s
```

## 5. Healthcheck 설정

헬스체크를 통해 서비스의 실제 가용 상태를 확인할 수 있다.

```yaml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s       # 체크 간격
      timeout: 5s          # 타임아웃
      retries: 3           # 실패 허용 횟수
      start_period: 30s    # 초기 대기 시간 (이 기간 중 실패는 무시)

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
```

**컨테이너 상태 흐름**: `starting` → `healthy` / `unhealthy`

## 6. 환경 변수 관리

### .env 파일

프로젝트 루트에 `.env` 파일을 생성하면 Compose 파일 내에서 변수 치환이 가능하다.

```bash
# .env (프로젝트 루트)
POSTGRES_VERSION=16
APP_PORT=8000
DB_NAME=myapp
DB_USER=your-db-user
DB_PASSWORD=your-db-password
```

```yaml
# docker-compose.yml 에서 변수 참조
services:
  db:
    image: postgres:${POSTGRES_VERSION}-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  web:
    ports:
      - "${APP_PORT}:8000"
```

### environment vs env_file 비교

| 항목 | environment | env_file |
|------|-------------|----------|
| **정의 위치** | docker-compose.yml 내부 | 별도 파일 |
| **우선 순위** | 높음 (env_file 덮어씀) | 낮음 |
| **변수 치환** | 지원 (`${VAR}`) | 미지원 |
| **용도** | 소수의 핵심 설정 | 다수의 환경 변수 관리 |
| **Git 관리** | 가능 (시크릿 주의) | .gitignore에 추가 권장 |

## 7. Override 파일

Compose는 여러 파일을 병합하여 환경별 설정을 관리할 수 있다.

```bash
# 기본 동작: docker-compose.yml + docker-compose.override.yml 자동 병합
docker compose up -d

# 명시적으로 파일 지정
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

```yaml
# docker-compose.yml (기본)
services:
  web:
    build: ./backend
    ports:
      - "8000:8000"

# docker-compose.override.yml (개발 환경 — 자동 병합)
services:
  web:
    volumes:
      - ./backend:/app          # 코드 핫 리로드
    environment:
      - DEBUG=true
    command: python manage.py runserver 0.0.0.0:8000

# docker-compose.prod.yml (운영 환경 — 명시적 지정)
services:
  web:
    restart: always
    environment:
      - DEBUG=false
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## 8. 실전 예시: Django + PostgreSQL + Redis 3-Tier 구성

```yaml
services:
  # ===== 웹 서버 =====
  web:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_URL=postgresql://your-db-user:your-db-password@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=your-secret-key-here
    volumes:
      - static-files:/app/static
      - media-files:/app/media
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
    networks:
      - backend
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M

  # ===== 데이터베이스 =====
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: your-db-user
      POSTGRES_PASSWORD: your-db-password
    volumes:
      - db-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d  # 초기화 SQL
    ports:
      - "127.0.0.1:5432:5432"    # 로컬에서만 접근 가능
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U your-db-user -d appdb"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s
    restart: unless-stopped
    networks:
      - backend

  # ===== 캐시 서버 =====
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    restart: unless-stopped
    networks:
      - backend

  # ===== 비동기 워커 =====
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A config worker --loglevel=info --concurrency=2
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_URL=postgresql://your-db-user:your-db-password@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      web:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 256M

  # ===== 리버스 프록시 =====
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - static-files:/usr/share/nginx/static:ro
      - media-files:/usr/share/nginx/media:ro
    depends_on:
      web:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend

networks:
  backend:
    driver: bridge

volumes:
  db-data:
  redis-data:
  static-files:
  media-files:
```

## 9. 유용한 Compose 명령어

```bash
# 서비스 빌드만 수행
docker compose build --no-cache web

# 특정 서비스만 실행
docker compose up -d db redis

# 서비스 스케일링
docker compose up -d --scale celery-worker=3

# 볼륨까지 완전 삭제
docker compose down -v

# 서비스 재시작
docker compose restart web

# 설정 유효성 검증
docker compose config

# 이미지 업데이트 후 재배포
docker compose pull && docker compose up -d
```

## 10. 운영 팁

### 로그 관리

```yaml
services:
  web:
    logging:
      driver: json-file
      options:
        max-size: "10m"     # 로그 파일 최대 크기
        max-file: "3"       # 로그 파일 최대 개수
```

### 리소스 제한

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 128M
```

### 프로파일 (선택적 서비스)

```yaml
services:
  web:
    # 항상 실행

  debug-tools:
    image: busybox
    profiles:
      - debug     # debug 프로파일 활성화 시에만 실행

  monitoring:
    image: grafana/grafana
    profiles:
      - monitoring
```

```bash
# 특정 프로파일 활성화
docker compose --profile debug --profile monitoring up -d
```

## 정리

Docker Compose는 멀티 컨테이너 애플리케이션의 정의, 실행, 관리를 YAML 하나로 통합한다. 핵심 포인트:

1. **depends_on + healthcheck** 조합으로 안전한 서비스 기동 순서 보장
2. **override 파일**로 개발/운영 환경 분리
3. **.env 파일**로 환경 변수 중앙 관리
4. **리소스 제한과 로그 관리**로 운영 안정성 확보
5. **프로파일**로 선택적 서비스 관리

다음 글에서는 **Docker 네트워크**의 동작 원리와 컨테이너 간 통신 방법을 다룬다.
