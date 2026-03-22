---
title: "Docker 네트워크: 컨테이너 통신의 모든 것"
slug: "docker-network"
category: cloud
tags: ["docker", "networking", "bridge"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# Docker 네트워크: 컨테이너 통신의 모든 것

## 1. Docker 네트워크 개요

Docker는 컨테이너 간 통신과 외부 네트워크 연결을 위한 자체 네트워킹 시스템을 제공한다. 컨테이너를 실행하면 Docker는 자동으로 네트워크 인터페이스를 생성하고, IP를 할당하며, 라우팅 규칙을 설정한다.

```bash
# 네트워크 기본 명령어
docker network ls                        # 네트워크 목록 조회
docker network inspect bridge            # 특정 네트워크 상세 정보
docker network create my-network         # 사용자 정의 네트워크 생성
docker network rm my-network             # 네트워크 삭제
docker network prune                     # 사용하지 않는 네트워크 정리
```

## 2. Docker 네트워크 드라이버 종류

Docker는 다양한 네트워크 드라이버를 제공하며, 각각 다른 사용 사례에 최적화되어 있다.

| 드라이버 | 설명 | 사용 사례 |
|----------|------|----------|
| **bridge** | 단일 호스트 내 컨테이너 간 통신 (기본값) | 일반적인 단일 호스트 배포 |
| **host** | 호스트 네트워크 스택 직접 사용 | 최대 네트워크 성능 필요 시 |
| **overlay** | 멀티 호스트 간 컨테이너 통신 | Docker Swarm, 클러스터 환경 |
| **macvlan** | 컨테이너에 물리적 MAC 주소 할당 | 레거시 앱, 물리 네트워크 직접 연결 |
| **none** | 네트워크 비활성화 | 완전한 네트워크 격리 필요 시 |
| **ipvlan** | L2/L3 수준 네트워크 연결 | macvlan 대안, 고급 네트워크 구성 |

## 3. Bridge 네트워크

### 3.1 기본 bridge 네트워크

Docker 설치 시 자동으로 생성되는 `bridge` 네트워크이다. 별도 네트워크를 지정하지 않으면 모든 컨테이너가 이 네트워크에 연결된다.

```bash
# 기본 bridge 네트워크에서 컨테이너 실행
docker run -d --name app1 nginx
docker run -d --name app2 nginx

# 네트워크 정보 확인
docker network inspect bridge
```

**기본 bridge의 한계점:**

- 컨테이너 이름으로 DNS 해석이 **되지 않는다** (IP로만 통신 가능)
- 모든 컨테이너가 같은 네트워크에 위치하여 격리 불가
- `--link` 옵션은 레거시 기능으로 사용 비권장

### 3.2 사용자 정의 bridge 네트워크

사용자 정의 bridge 네트워크는 기본 bridge의 한계를 해결한다.

```bash
# 사용자 정의 네트워크 생성
docker network create --driver bridge \
    --subnet 172.20.0.0/16 \
    --gateway 172.20.0.1 \
    my-app-network

# 네트워크에 컨테이너 연결
docker run -d --name web --network my-app-network nginx
docker run -d --name api --network my-app-network python:3.12-slim
```

**사용자 정의 bridge의 장점:**

| 기능 | 기본 bridge | 사용자 정의 bridge |
|------|------------|-------------------|
| **DNS 해석** | 불가 (IP만 사용) | 컨테이너 이름으로 DNS 자동 해석 |
| **네트워크 격리** | 모든 컨테이너 동일 네트워크 | 서비스별 네트워크 분리 가능 |
| **실행 중 연결/해제** | 불가 | `docker network connect/disconnect` |
| **서브넷 설정** | 자동 | 직접 지정 가능 |

```bash
# DNS 해석 테스트: 컨테이너 이름으로 통신
docker exec web curl http://api:8000/health/

# 실행 중인 컨테이너를 다른 네트워크에 연결
docker network connect another-network web
docker network disconnect my-app-network web
```

## 4. Host 네트워크

컨테이너가 호스트의 네트워크 스택을 직접 사용한다. 포트 매핑이 필요 없으며, 네트워크 오버헤드가 최소화된다.

```bash
# host 네트워크 사용
docker run -d --network host nginx
# nginx가 호스트의 80 포트에서 직접 수신
```

**특징:**

- 포트 매핑(`-p`) 불필요 — 컨테이너 포트 = 호스트 포트
- 네트워크 NAT 오버헤드 없음 → 최대 성능
- 포트 충돌 위험 존재
- Linux에서만 완전 지원 (macOS/Windows에서는 VM 경유)
- 네트워크 격리가 없으므로 보안상 주의 필요

## 5. Overlay 네트워크

여러 Docker 호스트에 걸친 컨테이너 간 통신을 가능하게 한다. Docker Swarm이나 외부 키-밸류 스토어가 필요하다.

```bash
# Swarm 모드 초기화
docker swarm init

# Overlay 네트워크 생성
docker network create --driver overlay \
    --attachable \
    my-overlay-network

# 다른 호스트의 컨테이너도 이 네트워크에 참여 가능
docker run -d --name web --network my-overlay-network nginx
```

**Overlay 네트워크의 핵심:**

- VXLAN 캡슐화를 사용하여 호스트 간 L2 터널링
- 기본적으로 AES 암호화 지원 (`--opt encrypted`)
- Docker Swarm 서비스 간 로드밸런싱 제공

## 6. Macvlan 네트워크

컨테이너에 고유한 MAC 주소를 할당하여 물리 네트워크에 직접 연결된 것처럼 보이게 한다.

```bash
# Macvlan 네트워크 생성
docker network create -d macvlan \
    --subnet=10.0.0.0/24 \
    --gateway=10.0.0.1 \
    -o parent=eth0 \
    my-macvlan

# 고정 IP로 컨테이너 실행
docker run -d --network my-macvlan \
    --ip 10.0.0.100 \
    --name legacy-app \
    my-legacy-image
```

**사용 사례:**

- DHCP 서버처럼 네트워크에서 고유한 MAC이 필요한 경우
- 레거시 애플리케이션이 물리 네트워크에 직접 연결되어야 하는 경우
- 네트워크 모니터링 도구 실행

## 7. 포트 매핑 상세

`-p` 또는 `--publish` 플래그로 호스트와 컨테이너 간 포트를 매핑한다.

```bash
# 기본 포트 매핑
docker run -d -p 8080:80 nginx        # 호스트 8080 → 컨테이너 80

# 특정 인터페이스 바인딩
docker run -d -p 127.0.0.1:8080:80 nginx   # localhost에서만 접근

# 랜덤 호스트 포트
docker run -d -p 80 nginx             # 호스트의 임의 포트 → 컨테이너 80
docker port <container-id>             # 할당된 포트 확인

# UDP 포트
docker run -d -p 5353:53/udp dns-server

# 여러 포트 매핑
docker run -d -p 80:80 -p 443:443 nginx
```

**포트 매핑 동작 원리:**

```
외부 요청 → 호스트:8080 → iptables/DNAT → docker-proxy → 컨테이너:80
```

Docker는 `iptables` 규칙과 `docker-proxy` 프로세스를 조합하여 포트 포워딩을 구현한다.

> **보안 주의**: `-p 8080:80`은 기본적으로 `0.0.0.0:8080`에 바인딩되어 **모든 인터페이스**에서 접근 가능하다. 외부 노출을 원하지 않으면 `127.0.0.1:8080:80`으로 명시적으로 제한하라.

## 8. Docker Compose에서의 네트워크

Docker Compose는 기본적으로 프로젝트별 네트워크를 자동 생성한다.

### 기본 네트워크 동작

```yaml
# docker-compose.yml
services:
  web:
    image: nginx
  api:
    image: python:3.12-slim
  db:
    image: postgres:16-alpine
```

위 설정에서 Compose는 `<프로젝트명>_default` 네트워크를 자동 생성하고, 모든 서비스를 해당 네트워크에 연결한다. 서비스 이름(`web`, `api`, `db`)이 DNS 호스트명으로 사용된다.

### 커스텀 네트워크로 격리

```yaml
services:
  # 프론트엔드 네트워크만 접근
  nginx:
    image: nginx:1.25-alpine
    networks:
      - frontend

  # 프론트엔드 + 백엔드 양쪽 모두 접근
  api:
    image: my-api:latest
    networks:
      - frontend
      - backend

  # 백엔드 네트워크만 접근 (외부 노출 없음)
  db:
    image: postgres:16-alpine
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true    # 외부 인터넷 접근 차단
```

이 구조에서 `nginx`는 `db`에 직접 접근할 수 없다. 반드시 `api`를 통해서만 통신할 수 있다.

### 외부 네트워크 참조

```yaml
services:
  web:
    networks:
      - existing-network

networks:
  existing-network:
    external: true          # 이미 존재하는 네트워크 사용
    name: my-shared-network  # 실제 네트워크 이름
```

## 9. 멀티호스트 네트워킹

단일 호스트를 넘어 여러 서버에서 컨테이너 간 통신이 필요한 경우의 선택지:

| 방법 | 설명 | 복잡도 |
|------|------|--------|
| **Docker Swarm + Overlay** | Docker 내장 클러스터링 | 낮음 |
| **Kubernetes** | 컨테이너 오케스트레이션 플랫폼 | 높음 |
| **WireGuard/VPN** | 호스트 간 VPN 터널 + bridge | 중간 |
| **Consul/etcd + Overlay** | 외부 KV 스토어 기반 | 중간 |

```bash
# Docker Swarm으로 멀티호스트 네트워킹
# Manager 노드
docker swarm init --advertise-addr 10.0.0.x

# Worker 노드 참가 (Manager에서 출력된 토큰 사용)
docker swarm join --token <join-token> 10.0.0.x:2377

# Overlay 네트워크 생성 → 모든 노드에서 사용 가능
docker network create --driver overlay --attachable multi-host-net
```

## 10. 네트워크 격리 전략

### 마이크로서비스 네트워크 설계 예시

```
┌─────────────────────────────────────────────────┐
│                 dmz-network                      │
│  ┌──────────┐                                   │
│  │  Nginx   │                                   │
│  │ (Proxy)  │                                   │
│  └────┬─────┘                                   │
├───────┼─────────────────────────────────────────┤
│       │         app-network                      │
│  ┌────▼─────┐  ┌──────────┐  ┌──────────┐      │
│  │  Web API │  │  Worker  │  │  Scheduler│      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
├───────┼──────────────┼─────────────┼────────────┤
│       │         data-network (internal)          │
│  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐      │
│  │ PostgreSQL│  │  Redis  │  │ RabbitMQ │      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
```

**원칙:**

1. **최소 권한 원칙**: 각 서비스는 필요한 네트워크에만 연결
2. **Internal 네트워크**: 데이터베이스 등은 `internal: true`로 외부 인터넷 접근 차단
3. **DMZ 분리**: 외부에 노출되는 프록시와 내부 서비스를 네트워크로 분리
4. **서비스 메시**: 복잡한 마이크로서비스에서는 Istio, Linkerd 등 서비스 메시 고려

## 11. 네트워크 트러블슈팅

```bash
# 컨테이너의 네트워크 설정 확인
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' my-container

# 컨테이너 내부에서 DNS 해석 확인
docker exec my-container nslookup api

# 컨테이너 간 연결 테스트
docker exec web curl -s http://api:8000/health/

# 네트워크 상세 정보 (연결된 컨테이너 목록 포함)
docker network inspect my-network

# iptables 규칙 확인 (Linux)
sudo iptables -t nat -L -n | grep DOCKER
```

## 정리

Docker 네트워크의 핵심 요점:

1. **항상 사용자 정의 bridge 네트워크를 사용**하라 (기본 bridge 사용 금지)
2. **서비스 이름**이 곧 DNS 호스트명이다 — IP 하드코딩 금지
3. **네트워크 분리**로 서비스 간 접근을 최소화하라
4. **internal 네트워크**로 데이터 계층의 외부 접근을 차단하라
5. 포트 매핑 시 **바인딩 주소를 명시**하여 의도치 않은 노출을 방지하라

다음 글에서는 **Docker 볼륨과 스토리지** 관리 방법을 다룬다.
