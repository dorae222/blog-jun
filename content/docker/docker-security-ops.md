---
title: "Docker 보안 & 운영: 프로덕션을 위한 베스트 프랙티스"
slug: "docker-security-ops"
category: cloud
tags: ["docker", "security", "monitoring", "operations"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# Docker 보안 & 운영: 프로덕션을 위한 베스트 프랙티스

## 1. 이미지 보안

### 1.1 취약점 스캔

프로덕션에 배포하기 전에 반드시 이미지의 보안 취약점을 스캔해야 한다.

#### Docker Scout

Docker Desktop에 내장된 공식 취약점 분석 도구이다.

```bash
# 이미지 취약점 스캔
docker scout cves my-app:latest

# CVSS 점수 기반 필터링
docker scout cves --only-severity critical,high my-app:latest

# 베이스 이미지 추천
docker scout recommendations my-app:latest

# CI/CD 파이프라인에서 사용 (취약점 발견 시 실패)
docker scout cves --exit-code --only-severity critical my-app:latest
```

#### Trivy

Aqua Security에서 개발한 오픈소스 취약점 스캐너이다.

```bash
# 설치 (macOS)
brew install trivy

# 이미지 스캔
trivy image my-app:latest

# 심각도 필터링
trivy image --severity HIGH,CRITICAL my-app:latest

# JSON 출력 (CI/CD 연동용)
trivy image --format json --output result.json my-app:latest

# Dockerfile 스캔 (설정 오류 탐지)
trivy config ./Dockerfile

# SBOM (Software Bill of Materials) 생성
trivy image --format spdx-json --output sbom.json my-app:latest
```

#### 스캔 도구 비교

| 항목 | Docker Scout | Trivy | Grype |
|------|-------------|-------|-------|
| **개발사** | Docker | Aqua Security | Anchore |
| **가격** | 무료/유료 | 무료 (OSS) | 무료 (OSS) |
| **속도** | 빠름 | 매우 빠름 | 빠름 |
| **DB 업데이트** | 자동 | 자동 | 자동 |
| **CI/CD 통합** | Docker Hub | 범용 | 범용 |
| **IaC 스캔** | 미지원 | 지원 | 미지원 |

### 1.2 신뢰할 수 있는 베이스 이미지

```dockerfile
# 나쁜 예: 출처 불명의 이미지
FROM some-random-user/python:latest

# 좋은 예: Docker Official Image 사용
FROM python:3.12-slim-bookworm

# 더 좋은 예: 특정 다이제스트로 고정 (불변)
FROM python:3.12-slim-bookworm@sha256:abcdef1234567890...
```

**이미지 선택 기준:**

1. Docker Official Image 또는 Verified Publisher 이미지 우선
2. 정확한 버전 태그 사용 (`latest` 금지)
3. 가능하면 `-slim` 또는 `-alpine` 변형 사용
4. 중요한 환경에서는 다이제스트(`@sha256:...`)로 고정

## 2. Rootless 모드

기본적으로 Docker 데몬은 root 권한으로 실행된다. Rootless 모드는 데몬 자체를 일반 사용자 권한으로 실행하여 보안을 강화한다.

```bash
# Rootless Docker 설치
dockerd-rootless-setuptool.sh install

# 환경 변수 설정
export PATH=/home/your-user/bin:$PATH
export DOCKER_HOST=unix:///run/user/1000/docker.sock

# Rootless 모드 확인
docker info | grep "rootless"
# Security Options: rootless
```

**Rootless 모드의 장점:**

- Docker 데몬 취약점 공격 시에도 root 권한 획득 불가
- 커널 취약점을 통한 컨테이너 탈출 시에도 피해 최소화
- 멀티테넌트 환경에서 사용자별 격리

**제약 사항:**

- 1024 미만의 포트 바인딩 불가 (기본 설정)
- 일부 스토리지 드라이버 사용 제한
- AppArmor/SELinux 일부 기능 제한

## 3. 사용자 네임스페이스 (User Namespace Remapping)

컨테이너 내부의 root(UID 0)를 호스트의 비특권 사용자로 매핑한다.

```bash
# /etc/docker/daemon.json 설정
{
    "userns-remap": "default"
}

# 또는 특정 사용자로 매핑
{
    "userns-remap": "your-user:your-group"
}
```

```bash
# Docker 재시작 후 확인
sudo systemctl restart docker

# 컨테이너 내부 root가 호스트에서는 비특권 사용자로 동작
docker run --rm alpine id
# uid=0(root) gid=0(root)  ← 컨테이너 내부에서는 root

# 호스트에서 확인하면 실제로는 매핑된 UID로 실행됨
```

### Dockerfile에서 사용자 설정

```dockerfile
FROM python:3.12-slim

# 전용 사용자 생성
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --create-home appuser

WORKDIR /app
COPY --chown=appuser:appgroup . .

# 비특권 사용자로 전환
USER appuser

CMD ["python", "app.py"]
```

## 4. 리소스 제한

컨테이너의 리소스 사용을 제한하여 하나의 컨테이너가 호스트 전체를 점유하는 것을 방지한다.

### 메모리 제한

```bash
# 메모리 제한 (초과 시 OOM Kill)
docker run -d --memory=512m --memory-swap=1g my-app

# 메모리 예약 (소프트 리밋)
docker run -d --memory=512m --memory-reservation=256m my-app
```

### CPU 제한

```bash
# CPU 코어 수 제한
docker run -d --cpus=1.5 my-app

# CPU 공유 비율 (상대적 가중치, 기본값 1024)
docker run -d --cpu-shares=512 my-app

# 특정 CPU 코어에 바인딩
docker run -d --cpuset-cpus="0,1" my-app
```

### I/O 제한

```bash
# 블록 I/O 가중치 (100-1000)
docker run -d --blkio-weight=300 my-app

# 디바이스별 읽기/쓰기 속도 제한
docker run -d \
    --device-read-bps=/dev/sda:10mb \
    --device-write-bps=/dev/sda:10mb \
    my-app
```

### Docker Compose에서 리소스 제한

```yaml
services:
  web:
    image: my-app:latest
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 128M
    # OOM 설정
    oom_score_adj: 100    # OOM 우선 종료 대상 조정
```

## 5. Seccomp & AppArmor

### Seccomp (Secure Computing Mode)

허용되는 시스템 콜을 제한하여 공격 표면을 줄인다.

```bash
# 기본 Seccomp 프로파일 확인 (Docker 기본 적용)
docker run --rm --security-opt seccomp=unconfined alpine  # 비활성화 (비권장)

# 커스텀 Seccomp 프로파일 적용
docker run --rm --security-opt seccomp=./custom-seccomp.json my-app
```

```json
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": ["SCMP_ARCH_X86_64"],
    "syscalls": [
        {
            "names": ["read", "write", "exit", "exit_group", "open", "close",
                       "stat", "fstat", "mmap", "mprotect", "munmap", "brk"],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
```

### AppArmor

파일시스템 접근, 네트워크 동작, 프로세스 실행 등을 프로파일 기반으로 제한한다.

```bash
# AppArmor 프로파일 로드
sudo apparmor_parser -r -W /etc/apparmor.d/docker-custom

# 프로파일 적용
docker run --rm --security-opt apparmor=docker-custom my-app

# AppArmor 상태 확인
sudo aa-status
```

### 추가 보안 옵션

```bash
# 읽기 전용 루트 파일시스템
docker run --read-only --tmpfs /tmp my-app

# 권한 상승(setuid/setgid) 방지
docker run --security-opt=no-new-privileges:true my-app

# 커널 캐퍼빌리티 제거
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE my-app

# 종합 보안 설정 예시
docker run -d \
    --read-only \
    --tmpfs /tmp:rw,noexec,size=64m \
    --security-opt=no-new-privileges:true \
    --cap-drop=ALL \
    --cap-add=NET_BIND_SERVICE \
    --memory=256m \
    --cpus=0.5 \
    --user 1000:1000 \
    my-app
```

## 6. 로깅 드라이버

Docker는 다양한 로깅 드라이버를 지원하여 컨테이너 로그를 중앙화할 수 있다.

| 드라이버 | 설명 | 용도 |
|---------|------|------|
| **json-file** | 기본값, JSON 형식으로 로컬 저장 | 개발/소규모 운영 |
| **local** | 최적화된 로컬 로깅 | 단일 호스트 운영 |
| **syslog** | Syslog 서버로 전송 | 기존 인프라 연동 |
| **journald** | systemd journal로 전송 | systemd 환경 |
| **fluentd** | Fluentd 수집기로 전송 | 대규모 로그 파이프라인 |
| **awslogs** | AWS CloudWatch Logs | AWS 환경 |
| **gcplogs** | Google Cloud Logging | GCP 환경 |
| **splunk** | Splunk HTTP Event Collector | Splunk 환경 |

### json-file 드라이버 (기본)

```bash
# 로그 크기 제한 설정
docker run -d \
    --log-driver json-file \
    --log-opt max-size=10m \
    --log-opt max-file=5 \
    my-app

# /etc/docker/daemon.json에서 전역 설정
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3",
        "compress": "true"
    }
}
```

### Fluentd 드라이버

```bash
# Fluentd로 로그 전송
docker run -d \
    --log-driver fluentd \
    --log-opt fluentd-address=10.0.0.x:24224 \
    --log-opt tag="docker.{{.Name}}" \
    my-app
```

### Docker Compose에서 로깅 설정

```yaml
services:
  web:
    image: my-app:latest
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
        tag: "{{.ImageName}}/{{.Name}}/{{.ID}}"
```

## 7. 모니터링

### docker stats

실행 중인 컨테이너의 리소스 사용량을 실시간으로 모니터링한다.

```bash
# 모든 컨테이너 실시간 모니터링
docker stats

# 특정 컨테이너만 조회
docker stats web db redis

# 스냅샷 모드 (일회성)
docker stats --no-stream

# 커스텀 포맷
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

### cAdvisor

Google에서 개발한 컨테이너 리소스 모니터링 도구이다. Prometheus와 연동하여 메트릭을 수집할 수 있다.

```yaml
# docker-compose.yml에 cAdvisor 추가
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports:
      - "127.0.0.1:8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    restart: unless-stopped
```

### Prometheus + Grafana 스택

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=your-grafana-password
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "127.0.0.1:9100:9100"
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

### Docker 데몬 메트릭 노출

```json
{
    "metrics-addr": "127.0.0.1:9323",
    "experimental": true
}
```

## 8. 이미지 경량화

### Alpine Linux 기반 이미지

```dockerfile
# 일반 이미지 → Alpine 이미지 변경
# python:3.12     ~1.0 GB
# python:3.12-slim ~150 MB
# python:3.12-alpine ~50 MB

FROM python:3.12-alpine

# Alpine은 musl libc를 사용하므로 일부 패키지 빌드에 추가 의존성 필요
RUN apk add --no-cache \
    gcc musl-dev libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### Distroless 이미지

Google에서 제공하는 최소한의 런타임 이미지이다. 셸, 패키지 매니저가 없어 공격 표면을 극도로 줄인다.

```dockerfile
# 멀티스테이지 빌드 + Distroless
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt
COPY . .

FROM gcr.io/distroless/python3-debian12
WORKDIR /app
COPY --from=builder /app /app
ENV PYTHONPATH=/app/deps
CMD ["app.py"]
```

### 이미지 크기 비교

| 베이스 이미지 | 대략적 크기 | 특징 |
|-------------|-----------|------|
| `ubuntu:22.04` | ~77 MB | 풀 OS, 편의성 높음 |
| `debian:bookworm-slim` | ~74 MB | Debian slim |
| `python:3.12` | ~1.0 GB | Python 풀 이미지 |
| `python:3.12-slim` | ~150 MB | 필수 패키지만 포함 |
| `python:3.12-alpine` | ~50 MB | Alpine 기반, musl libc |
| `gcr.io/distroless/python3` | ~52 MB | 셸 없음, 최소 런타임 |
| `scratch` | 0 B | 완전히 빈 이미지 |

### 이미지 분석 도구

```bash
# dive: 이미지 레이어별 크기 분석
dive my-app:latest

# docker history: 레이어 히스토리 확인
docker history my-app:latest

# 이미지 크기 확인
docker images my-app --format "{{.Repository}}:{{.Tag}} {{.Size}}"
```

## 9. 컨테이너 라이프사이클 관리

### 컨테이너 상태 흐름

```
Created → Running → Paused → Running → Stopped → Removed
   │         │                  │          │
   │         └──── Restart ─────┘          │
   │                                       │
   └───────────── Removed ─────────────────┘
```

### 라이프사이클 명령어

```bash
# 생성 → 시작 → 정지 → 삭제
docker create --name my-app my-image:latest   # Created
docker start my-app                            # Running
docker pause my-app                            # Paused
docker unpause my-app                          # Running
docker stop my-app                             # Stopped (SIGTERM → SIGKILL)
docker kill my-app                             # Stopped (즉시 SIGKILL)
docker rm my-app                               # Removed

# Graceful shutdown 타임아웃 설정
docker stop --time=30 my-app    # 30초 대기 후 SIGKILL
```

### 재시작 정책

```bash
# 재시작 정책 설정
docker run -d --restart=unless-stopped my-app

# 정책 변경 (실행 중인 컨테이너)
docker update --restart=always my-app
```

| 정책 | 설명 |
|------|------|
| `no` | 재시작하지 않음 (기본값) |
| `on-failure[:N]` | 비정상 종료(exit code != 0) 시 재시작, N회 제한 가능 |
| `always` | 항상 재시작 (수동 중지 포함) |
| `unless-stopped` | 수동 중지 외에는 항상 재시작 |

### 시스템 정리

```bash
# 중지된 컨테이너 정리
docker container prune

# 미사용 이미지 정리
docker image prune          # dangling 이미지만
docker image prune -a       # 사용하지 않는 모든 이미지

# 미사용 볼륨 정리
docker volume prune

# 미사용 네트워크 정리
docker network prune

# 전체 정리 (주의!)
docker system prune -a --volumes

# 디스크 사용량 확인
docker system df
docker system df -v    # 상세 정보
```

## 10. 운영 체크리스트

프로덕션 Docker 환경을 위한 핵심 체크리스트:

### 이미지 보안
- [ ] 공식/검증된 베이스 이미지 사용
- [ ] 정확한 버전 태그 또는 다이제스트 고정
- [ ] 이미지 취약점 스캔 (CI/CD 파이프라인에 통합)
- [ ] `.dockerignore`로 불필요한 파일 제외
- [ ] 시크릿을 이미지에 포함하지 않음

### 런타임 보안
- [ ] 비특권 사용자(`USER`)로 실행
- [ ] 읽기 전용 루트 파일시스템(`--read-only`)
- [ ] `no-new-privileges` 보안 옵션 적용
- [ ] 필요한 캐퍼빌리티만 추가(`--cap-drop=ALL` + 필요한 것만 `--cap-add`)
- [ ] 리소스 제한(메모리, CPU) 설정

### 운영 안정성
- [ ] 헬스체크 설정
- [ ] 적절한 재시작 정책 (`unless-stopped` 또는 `on-failure`)
- [ ] 로그 로테이션 설정 (`max-size`, `max-file`)
- [ ] 모니터링 도구 연동 (Prometheus, cAdvisor 등)
- [ ] 정기적 백업 및 복원 테스트

### 네트워크
- [ ] 사용자 정의 bridge 네트워크 사용
- [ ] 불필요한 포트 노출 금지
- [ ] 데이터 계층은 `internal` 네트워크로 격리
- [ ] 포트 바인딩 시 인터페이스 명시 (`127.0.0.1:...`)

## 정리

Docker 보안과 운영은 이미지 빌드부터 런타임 실행, 모니터링까지 전 과정에 걸쳐 있다. 핵심 원칙:

1. **최소 권한 원칙**: 비특권 사용자, 최소 캐퍼빌리티, 읽기 전용 파일시스템
2. **공격 표면 최소화**: slim/distroless 이미지, 불필요한 도구 제거
3. **지속적 스캔**: CI/CD 파이프라인에 취약점 스캔 통합
4. **리소스 격리**: 메모리/CPU 제한으로 한 컨테이너의 영향 범위 제한
5. **관측성 확보**: 로그 중앙화, 메트릭 모니터링, 헬스체크

이 Docker 시리즈에서 다룬 내용을 기반으로, 안전하고 효율적인 컨테이너 환경을 구축할 수 있을 것이다.
