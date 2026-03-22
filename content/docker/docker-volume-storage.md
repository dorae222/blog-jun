---
title: "Docker 볼륨 & 스토리지: 데이터 영속성 완전 가이드"
slug: "docker-volume-storage"
category: cloud
tags: ["docker", "volume", "storage", "persistence"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# Docker 볼륨 & 스토리지: 데이터 영속성 완전 가이드

## 1. 왜 볼륨이 필요한가?

Docker 컨테이너는 기본적으로 **일시적(ephemeral)**이다. 컨테이너가 삭제되면 내부에 저장된 모든 데이터도 함께 사라진다. 데이터베이스, 업로드 파일, 로그 등 영속성이 필요한 데이터를 보존하려면 Docker의 스토리지 메커니즘을 이해해야 한다.

```bash
# 컨테이너 내부의 데이터는 컨테이너와 함께 사라짐
docker run --name temp-db postgres:16-alpine
docker rm temp-db    # DB 데이터 영구 손실!
```

## 2. Docker 스토리지 드라이버 개요

Docker는 이미지 레이어와 컨테이너의 쓰기 가능 레이어를 관리하기 위해 **스토리지 드라이버**를 사용한다.

| 스토리지 드라이버 | 설명 | 지원 OS |
|------------------|------|---------|
| **overlay2** | 현재 기본 권장 드라이버, 안정적이고 성능 우수 | Linux (대부분) |
| **fuse-overlayfs** | Rootless Docker에서 사용 | Linux |
| **btrfs** | Btrfs 파일시스템 네이티브 지원 | Linux (Btrfs) |
| **zfs** | ZFS 파일시스템 네이티브 지원 | Linux (ZFS) |
| **vfs** | 레이어 공유 없음 (테스트용) | 모든 OS |

```bash
# 현재 스토리지 드라이버 확인
docker info | grep "Storage Driver"
# Storage Driver: overlay2
```

> **참고**: 대부분의 환경에서는 기본 `overlay2`를 사용하면 된다. 특별한 이유가 없는 한 변경할 필요가 없다.

## 3. 3가지 마운트 타입 비교

Docker는 컨테이너에 데이터를 제공하는 세 가지 마운트 방식을 제공한다.

```
┌────────────────────────────────────────────────────┐
│                   Docker Host                       │
│                                                    │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐   │
│  │  Volume   │   │Bind Mount│   │   tmpfs      │   │
│  │          │   │          │   │  (RAM)       │   │
│  │ /var/lib/│   │ /home/   │   │              │   │
│  │ docker/  │   │ user/    │   │ 메모리에만    │   │
│  │ volumes/ │   │ project/ │   │ 존재         │   │
│  └────┬─────┘   └────┬─────┘   └──────┬───────┘   │
│       │              │                │            │
│  ┌────▼──────────────▼────────────────▼───────┐    │
│  │              Container                      │    │
│  │  /data         /app           /tmp/secret   │    │
│  └────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────┘
```

| 항목 | Volume | Bind Mount | tmpfs |
|------|--------|-----------|-------|
| **저장 위치** | Docker 관리 영역 (`/var/lib/docker/volumes/`) | 호스트 임의 경로 | 메모리 (RAM) |
| **Docker 관리** | Docker가 관리 (생성/삭제) | 사용자가 직접 관리 | 자동 (컨테이너 종료 시 삭제) |
| **이식성** | 높음 (Docker가 관리) | 낮음 (호스트 경로 의존) | 해당 없음 |
| **성능** | 좋음 | 좋음 (네이티브 수준) | 매우 빠름 (RAM) |
| **공유** | 여러 컨테이너 간 공유 가능 | 호스트와 컨테이너 간 공유 | 공유 불가 |
| **백업** | Docker 명령으로 쉽게 백업 | 일반 파일 도구로 백업 | 불가 (휘발성) |
| **적합 용도** | DB 데이터, 영속 데이터 | 소스 코드 마운트 (개발) | 시크릿, 임시 데이터 |

## 4. Volume (볼륨)

Docker가 관리하는 가장 권장되는 데이터 영속화 방법이다.

### Named Volume vs Anonymous Volume

```bash
# Named Volume: 이름을 지정하여 생성
docker run -d --name db \
    -v db-data:/var/lib/postgresql/data \
    postgres:16-alpine

# Anonymous Volume: 이름 없이 자동 생성 (해시값으로 식별)
docker run -d --name db \
    -v /var/lib/postgresql/data \
    postgres:16-alpine
```

| 구분 | Named Volume | Anonymous Volume |
|------|-------------|-----------------|
| **식별** | 사람이 읽을 수 있는 이름 | 자동 생성된 해시 |
| **재사용** | 이름으로 쉽게 재사용 | 컨테이너 삭제 후 접근 어려움 |
| **정리** | 명시적 삭제 필요 | `docker volume prune`으로 일괄 정리 |
| **사용 시나리오** | DB 데이터, 공유 데이터 | node_modules 보호 등 |

## 5. Bind Mount (바인드 마운트)

호스트의 특정 디렉토리를 컨테이너에 직접 마운트한다.

```bash
# -v 플래그 사용
docker run -d --name web \
    -v /home/your-user/project/src:/app/src \
    my-app:latest

# --mount 플래그 사용 (더 명시적)
docker run -d --name web \
    --mount type=bind,source=/home/your-user/project/src,target=/app/src \
    my-app:latest

# 읽기 전용 마운트
docker run -d --name web \
    -v /home/your-user/config/nginx.conf:/etc/nginx/nginx.conf:ro \
    nginx:latest
```

**Bind Mount의 활용:**

- **개발 환경**: 소스 코드를 마운트하여 코드 변경 시 실시간 반영 (hot reload)
- **설정 파일**: 호스트의 설정 파일을 컨테이너에 주입
- **로그 수집**: 컨테이너 로그를 호스트에서 직접 접근

> **주의**: Bind Mount는 호스트 파일시스템에 직접 접근하므로, 컨테이너가 호스트의 중요한 파일을 수정하거나 삭제할 수 있다. `ro`(읽기 전용) 옵션을 적극 활용하라.

## 6. tmpfs Mount

메모리에 데이터를 저장하는 임시 마운트이다. 컨테이너가 중지되면 데이터가 사라진다.

```bash
# tmpfs 마운트
docker run -d --name secure-app \
    --tmpfs /tmp:rw,noexec,size=64m \
    my-app:latest

# --mount 플래그 사용
docker run -d --name secure-app \
    --mount type=tmpfs,destination=/run/secrets,tmpfs-size=10m \
    my-app:latest
```

**사용 사례:**

- 시크릿 키, 토큰 등 민감한 데이터의 임시 저장
- 디스크에 저장하면 안 되는 중간 처리 데이터
- 고속 I/O가 필요한 캐시 데이터

## 7. 볼륨 생성·조회·삭제 명령어

```bash
# 볼륨 생성
docker volume create my-data

# 옵션을 지정한 볼륨 생성
docker volume create --driver local \
    --opt type=nfs \
    --opt o=addr=10.0.0.x,rw \
    --opt device=:/path/to/share \
    nfs-data

# 볼륨 목록 조회
docker volume ls

# 볼륨 상세 정보
docker volume inspect my-data
# 출력 예:
# [
#     {
#         "CreatedAt": "2026-03-22T00:00:00+09:00",
#         "Driver": "local",
#         "Labels": {},
#         "Mountpoint": "/var/lib/docker/volumes/my-data/_data",
#         "Name": "my-data",
#         "Options": {},
#         "Scope": "local"
#     }
# ]

# 특정 볼륨 삭제
docker volume rm my-data

# 사용하지 않는 볼륨 일괄 정리 (주의!)
docker volume prune
docker volume prune --filter "label!=keep"  # 필터 적용
```

## 8. Docker Compose에서 볼륨 설정

```yaml
services:
  db:
    image: postgres:16-alpine
    volumes:
      # Named Volume — DB 데이터 영속성
      - db-data:/var/lib/postgresql/data

  web:
    build: .
    volumes:
      # Bind Mount — 개발 시 소스 코드 동기화
      - ./src:/app/src
      # Named Volume — 정적 파일
      - static-files:/app/static
      # Anonymous Volume — node_modules 보호
      - /app/node_modules
      # 읽기 전용 설정 파일
      - ./config/app.conf:/app/config/app.conf:ro

  cache:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    tmpfs:
      - /tmp:size=32m

# 최상위 volumes 선언
volumes:
  db-data:
    driver: local
  static-files:
  redis-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/fast-storage/redis
```

### 볼륨 드라이버 옵션

```yaml
volumes:
  # NFS 볼륨
  nfs-data:
    driver: local
    driver_opts:
      type: nfs
      o: "addr=10.0.0.x,nolock,soft,rw"
      device: ":/export/data"

  # 특정 경로에 바인딩
  host-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/app
```

## 9. 데이터 백업·복원

### 볼륨 백업

```bash
# 방법 1: 임시 컨테이너로 볼륨 데이터 tar 백업
docker run --rm \
    -v db-data:/source:ro \
    -v $(pwd)/backup:/backup \
    alpine tar czf /backup/db-data-backup.tar.gz -C /source .

# 방법 2: docker cp 활용 (실행 중인 컨테이너에서)
docker cp db:/var/lib/postgresql/data ./db-backup/
```

### 볼륨 복원

```bash
# 새 볼륨에 백업 복원
docker volume create db-data-restored

docker run --rm \
    -v db-data-restored:/target \
    -v $(pwd)/backup:/backup:ro \
    alpine tar xzf /backup/db-data-backup.tar.gz -C /target
```

### PostgreSQL 특화 백업

```bash
# pg_dump를 활용한 논리적 백업
docker exec db pg_dump -U your-db-user your-db-name > backup.sql

# 복원
docker exec -i db psql -U your-db-user your-db-name < backup.sql

# 자동 백업 스크립트용 컨테이너
docker run --rm \
    --network my-network \
    -v $(pwd)/backups:/backups \
    postgres:16-alpine \
    pg_dump -h db -U your-db-user your-db-name -f /backups/backup-$(date +%Y%m%d).sql
```

## 10. 볼륨 플러그인

Docker의 플러그인 시스템을 통해 다양한 스토리지 백엔드를 볼륨 드라이버로 사용할 수 있다.

| 플러그인 | 설명 | 용도 |
|---------|------|------|
| **local** | 기본 로컬 스토리지 | 단일 호스트 |
| **REX-Ray** | 클라우드 스토리지 연동 (AWS EBS, GCE PD 등) | 클라우드 환경 |
| **NetApp Trident** | NetApp 스토리지 연동 | 엔터프라이즈 |
| **Portworx** | 분산 스토리지 | Kubernetes/Swarm |
| **GlusterFS** | 분산 파일시스템 | 멀티호스트 공유 스토리지 |

```bash
# 플러그인 설치 예시
docker plugin install rexray/ebs

# 플러그인 볼륨 사용
docker volume create --driver rexray/ebs \
    --opt size=50 \
    my-ebs-volume
```

## 11. 실전: DB 데이터 영속성 패턴

### 패턴 1: 기본 볼륨 패턴

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: your-db-user
      POSTGRES_PASSWORD: your-db-password
    volumes:
      - db-data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  db-data:
```

### 패턴 2: 초기화 스크립트 + 볼륨

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: your-db-user
      POSTGRES_PASSWORD: your-db-password
    volumes:
      - db-data:/var/lib/postgresql/data
      # /docker-entrypoint-initdb.d/의 .sql, .sh 파일이 최초 실행 시 자동 실행
      - ./init-scripts:/docker-entrypoint-initdb.d:ro

volumes:
  db-data:
```

### 패턴 3: 자동 백업 패턴

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: your-db-user
      POSTGRES_PASSWORD: your-db-password
    volumes:
      - db-data:/var/lib/postgresql/data

  db-backup:
    image: postgres:16-alpine
    environment:
      PGHOST: db
      PGUSER: your-db-user
      PGPASSWORD: your-db-password
      PGDATABASE: myapp
    volumes:
      - ./backups:/backups
    entrypoint: >
      sh -c "while true; do
        pg_dump -f /backups/backup-$$(date +%Y%m%d-%H%M%S).sql;
        find /backups -name '*.sql' -mtime +7 -delete;
        sleep 86400;
      done"
    depends_on:
      db:
        condition: service_healthy

volumes:
  db-data:
```

### 패턴 4: 개발/운영 환경 분리

```yaml
# docker-compose.yml (공통)
services:
  db:
    image: postgres:16-alpine
    volumes:
      - db-data:/var/lib/postgresql/data

# docker-compose.override.yml (개발 — 자동 적용)
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"    # 로컬 접근 허용
    volumes:
      - ./seed-data:/docker-entrypoint-initdb.d:ro  # 시드 데이터

# docker-compose.prod.yml (운영)
services:
  db:
    deploy:
      resources:
        limits:
          memory: 2G
```

## 정리

Docker 스토리지 관리의 핵심 원칙:

1. **영속 데이터는 반드시 Named Volume을 사용**하라 — Anonymous Volume은 관리가 어렵다
2. **개발 환경에서만 Bind Mount**를 사용하라 — 운영에서는 Volume이 더 안전하다
3. **민감한 데이터는 tmpfs**에 저장하라 — 디스크에 남지 않는다
4. **정기적으로 백업**하라 — `docker volume prune`으로 실수로 삭제할 수 있다
5. **읽기 전용 마운트**를 적극 활용하라 — 불필요한 쓰기 권한을 최소화

다음 글에서는 **Docker 보안과 운영** 베스트 프랙티스를 다룬다.
