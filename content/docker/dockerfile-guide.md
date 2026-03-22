---
title: "Dockerfile 작성 가이드: 지시어부터 최적화까지"
slug: "dockerfile-guide"
category: cloud
tags: ["docker", "dockerfile", "multi-stage-build"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# Dockerfile 작성 가이드: 지시어부터 최적화까지

## 1. Dockerfile이란?

Dockerfile은 Docker 이미지를 자동으로 빌드하기 위한 텍스트 파일이다. 베이스 이미지 선택부터 애플리케이션 설치, 설정, 실행 명령까지 모든 과정을 코드로 정의한다.

```bash
# Dockerfile로 이미지 빌드
docker build -t my-app:v1.0 .
docker build -t my-app:v1.0 -f Dockerfile.prod .  # 특정 파일 지정
```

## 2. Dockerfile 지시어 총정리

### 2.1 FROM — 베이스 이미지 지정

모든 Dockerfile은 반드시 `FROM`으로 시작한다. 빌드의 기반이 되는 베이스 이미지를 지정한다.

```dockerfile
# 기본 사용법
FROM python:3.12-slim

# 특정 플랫폼 지정
FROM --platform=linux/amd64 node:20-alpine

# 빌드 인자 활용
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

# scratch: 완전히 빈 이미지 (Go 바이너리 등에 사용)
FROM scratch
```

### 2.2 RUN — 빌드 시 명령어 실행

이미지 빌드 과정에서 명령어를 실행한다. 각 RUN은 새로운 레이어를 생성한다.

```dockerfile
# Shell form
RUN apt-get update && apt-get install -y curl

# Exec form
RUN ["pip", "install", "--no-cache-dir", "-r", "requirements.txt"]

# 여러 명령어를 하나의 RUN으로 결합하여 레이어 최소화
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        git && \
    rm -rf /var/lib/apt/lists/*
```

### 2.3 COPY — 파일 복사

호스트의 파일이나 디렉토리를 이미지로 복사한다.

```dockerfile
# 단일 파일 복사
COPY requirements.txt /app/

# 디렉토리 전체 복사
COPY src/ /app/src/

# 파일 소유자 변경과 함께 복사
COPY --chown=appuser:appgroup . /app/

# 멀티스테이지 빌드에서 다른 스테이지의 결과물 복사
COPY --from=builder /app/dist /usr/share/nginx/html
```

### 2.4 ADD — 파일 추가 (확장 기능)

COPY와 유사하지만 추가 기능이 있다. 원격 URL 다운로드와 tar 파일 자동 압축 해제를 지원한다.

```dockerfile
# tar 파일 자동 압축 해제
ADD app.tar.gz /app/

# 원격 URL에서 다운로드 (권장하지 않음 — curl + RUN 조합 선호)
ADD https://example.com/file.txt /app/
```

> **권장 사항**: 단순 파일 복사에는 항상 `COPY`를 사용하라. `ADD`는 tar 자동 해제가 필요한 경우에만 사용한다.

### 2.5 WORKDIR — 작업 디렉토리 설정

이후 명령어들의 작업 디렉토리를 설정한다. 디렉토리가 없으면 자동 생성된다.

```dockerfile
WORKDIR /app

# 여러 번 사용 가능 (상대 경로도 가능)
WORKDIR /app
WORKDIR src    # 결과: /app/src
```

### 2.6 ENV — 환경 변수 설정

빌드 시점과 런타임 모두에서 사용되는 환경 변수를 설정한다.

```dockerfile
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app \
    APP_PORT=8000
```

### 2.7 ARG — 빌드 인자

빌드 시점에만 사용되는 변수를 정의한다. `--build-arg`로 값을 전달할 수 있다.

```dockerfile
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ARG BUILD_ENV=production
RUN echo "Building for ${BUILD_ENV}"
```

```bash
# 빌드 시 인자 전달
docker build --build-arg PYTHON_VERSION=3.11 --build-arg BUILD_ENV=staging .
```

> **주의**: `ARG`는 `FROM` 이후에 다시 선언해야 한다. `FROM` 이전에 선언한 ARG는 FROM 이후에는 사용할 수 없다.

### 2.8 EXPOSE — 포트 선언

컨테이너가 사용할 포트를 문서화한다. 실제 포트를 열지는 않으며, 사용자에게 정보를 제공하는 역할이다.

```dockerfile
EXPOSE 8000
EXPOSE 8000/tcp 8001/udp
```

### 2.9 CMD — 기본 실행 명령

컨테이너 시작 시 실행할 기본 명령을 정의한다. `docker run` 시 인자로 덮어쓸 수 있다.

```dockerfile
# Exec form (권장)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Shell form
CMD python manage.py runserver 0.0.0.0:8000
```

### 2.10 ENTRYPOINT — 실행 진입점

컨테이너의 진입점을 설정한다. CMD와 달리 `docker run` 인자로 쉽게 덮어쓸 수 없다.

```dockerfile
# ENTRYPOINT + CMD 조합 (권장 패턴)
ENTRYPOINT ["python", "manage.py"]
CMD ["runserver", "0.0.0.0:8000"]
```

```bash
# CMD 부분만 덮어쓰기 가능
docker run my-app migrate           # python manage.py migrate 실행
docker run my-app collectstatic     # python manage.py collectstatic 실행
```

**CMD vs ENTRYPOINT 비교표:**

| 항목 | CMD | ENTRYPOINT |
|------|-----|-----------|
| **역할** | 기본 실행 명령/인자 | 고정 실행 진입점 |
| **덮어쓰기** | `docker run` 인자로 쉽게 대체 | `--entrypoint` 플래그 필요 |
| **조합 시** | ENTRYPOINT의 기본 인자 역할 | CMD의 인자를 받음 |
| **사용 시점** | 유연한 기본 명령이 필요할 때 | 실행할 바이너리가 고정일 때 |

### 2.11 LABEL — 메타데이터

이미지에 메타데이터를 추가한다.

```dockerfile
LABEL maintainer="your-name"
LABEL version="1.0"
LABEL description="My Application Server"
```

### 2.12 USER — 실행 사용자

이후 명령어를 실행할 사용자를 설정한다. 보안을 위해 root가 아닌 사용자로 전환하는 것이 좋다.

```dockerfile
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

USER appuser
```

### 2.13 HEALTHCHECK — 헬스체크

컨테이너의 상태를 주기적으로 확인하는 명령을 정의한다.

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1
```

## 3. 멀티스테이지 빌드 (Multi-stage Build)

멀티스테이지 빌드는 빌드 도구와 최종 실행 환경을 분리하여 이미지 크기를 획기적으로 줄이는 기법이다.

### Builder → Runner 패턴

```dockerfile
# ===== Stage 1: Builder =====
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# ===== Stage 2: Runner =====
FROM nginx:alpine AS runner

# Builder 스테이지에서 빌드 결과물만 복사
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Python 예시 (Django)

```dockerfile
# ===== Stage 1: Builder =====
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ===== Stage 2: Runner =====
FROM python:3.12-slim AS runner

# 빌드 스테이지에서 설치된 패키지만 복사
COPY --from=builder /install /usr/local

WORKDIR /app
COPY . .

RUN addgroup --system django && \
    adduser --system --ingroup django django
USER django

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Go 예시 (극단적 경량화)

```dockerfile
FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server .

# scratch: 완전히 빈 이미지 (최종 크기 수 MB)
FROM scratch
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

## 4. 캐시 최적화 전략

Docker는 레이어 단위로 캐시를 관리한다. 한 레이어가 변경되면 그 이후 레이어는 모두 다시 빌드된다. 따라서 **변경 빈도가 낮은 레이어를 위에, 높은 레이어를 아래에** 배치해야 한다.

### 나쁜 예시 (캐시 비효율)

```dockerfile
FROM python:3.12-slim
WORKDIR /app

# 코드 변경 시 pip install부터 다시 실행됨
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
```

### 좋은 예시 (캐시 최적화)

```dockerfile
FROM python:3.12-slim
WORKDIR /app

# 의존성 파일만 먼저 복사 → 코드 변경 시에도 캐시 재사용
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 자주 변경되는 코드는 나중에 복사
COPY . .

CMD ["python", "app.py"]
```

## 5. .dockerignore 작성법

빌드 컨텍스트에서 불필요한 파일을 제외하여 빌드 속도와 이미지 크기를 최적화한다.

```dockerignore
# 버전 관리
.git
.gitignore

# 의존성 디렉토리
node_modules
__pycache__
*.pyc
.venv

# 빌드 결과물
dist
build

# IDE/에디터
.vscode
.idea
*.swp

# 환경 변수 및 시크릿
.env
.env.*
*.pem
*.key

# Docker 관련
Dockerfile*
docker-compose*.yml
.dockerignore

# 문서
README.md
docs/
```

## 6. 안티패턴 모음

### 안티패턴 1: latest 태그 사용

```dockerfile
# 나쁜 예: 재현성 없음
FROM python:latest

# 좋은 예: 정확한 버전 명시
FROM python:3.12.3-slim-bookworm
```

### 안티패턴 2: 불필요한 패키지 설치

```dockerfile
# 나쁜 예: 추천 패키지까지 모두 설치
RUN apt-get update && apt-get install -y python3

# 좋은 예: 최소한의 패키지만 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 && \
    rm -rf /var/lib/apt/lists/*
```

### 안티패턴 3: 시크릿을 이미지에 포함

```dockerfile
# 절대 금지: 이미지 레이어에 시크릿 영구 저장
COPY credentials.json /app/
ENV DB_PASSWORD=super-secret

# 올바른 방법: 런타임에 주입
# docker run -e DB_PASSWORD=**** my-app
# 또는 Docker BuildKit secret 사용
RUN --mount=type=secret,id=db_pass cat /run/secrets/db_pass
```

### 안티패턴 4: root로 실행

```dockerfile
# 나쁜 예: root로 실행 (보안 위험)
CMD ["python", "app.py"]

# 좋은 예: 비특권 사용자로 실행
RUN adduser --system --no-create-home appuser
USER appuser
CMD ["python", "app.py"]
```

### 안티패턴 5: RUN 남용으로 레이어 비대화

```dockerfile
# 나쁜 예: 레이어가 3개 생성, 삭제해도 이전 레이어에 남음
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# 좋은 예: 하나의 레이어에서 설치와 정리를 함께 수행
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
```

## 정리

효율적인 Dockerfile 작성의 핵심 원칙:

1. **정확한 버전의 slim/alpine 베이스 이미지** 사용
2. **멀티스테이지 빌드**로 빌드 도구와 런타임 분리
3. **레이어 순서 최적화**로 캐시 효율 극대화
4. **비특권 사용자**로 실행하여 보안 강화
5. **.dockerignore**로 불필요한 파일 제외
6. **시크릿은 절대 이미지에 포함하지 않기**

다음 글에서는 여러 컨테이너를 함께 관리하는 **Docker Compose 실전**을 다룬다.
