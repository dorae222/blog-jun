---
title: "Docker 개요: 컨테이너 기술의 핵심 이해"
slug: "docker-overview"
category: cloud
tags: ["docker", "container", "virtualization"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# Docker 개요: 컨테이너 기술의 핵심 이해

## 1. 컨테이너 기술이란?

컨테이너(Container)는 애플리케이션과 그 실행에 필요한 모든 의존성(라이브러리, 바이너리, 설정 파일 등)을 하나의 격리된 단위로 패키징하는 기술이다. 컨테이너는 호스트 OS의 커널을 공유하면서도 프로세스, 네트워크, 파일시스템을 격리하여 마치 독립적인 환경처럼 동작한다.

컨테이너 기술의 근간은 리눅스 커널의 두 가지 핵심 기능에 있다:

- **Namespaces**: 프로세스, 네트워크, 마운트, 사용자 등을 격리하는 커널 기능
- **Cgroups (Control Groups)**: CPU, 메모리, 디스크 I/O 등 리소스 사용량을 제한하고 격리하는 기능

```
┌─────────────────────────────────────────────┐
│              Host OS Kernel                  │
├──────────┬──────────┬──────────┬────────────┤
│ Container│ Container│ Container│            │
│    A     │    B     │    C     │   ...      │
│ ┌──────┐ │ ┌──────┐ │ ┌──────┐ │            │
│ │App   │ │ │App   │ │ │App   │ │            │
│ │Libs  │ │ │Libs  │ │ │Libs  │ │            │
│ │Config│ │ │Config│ │ │Config│ │            │
│ └──────┘ │ └──────┘ │ └──────┘ │            │
└──────────┴──────────┴──────────┴────────────┘
```

## 2. VM vs 컨테이너 비교

가상 머신(VM)과 컨테이너는 모두 격리된 환경을 제공하지만, 근본적인 아키텍처 차이가 존재한다.

| 항목 | 가상 머신 (VM) | 컨테이너 (Container) |
|------|---------------|---------------------|
| **가상화 수준** | 하드웨어 수준 (Hypervisor) | OS 수준 (커널 공유) |
| **Guest OS** | 각 VM마다 별도 OS 필요 | 호스트 OS 커널 공유 |
| **부팅 시간** | 수십 초 ~ 수 분 | 수 밀리초 ~ 수 초 |
| **이미지 크기** | 수 GB ~ 수십 GB | 수 MB ~ 수백 MB |
| **메모리 사용량** | 높음 (OS별 오버헤드) | 낮음 (커널 공유) |
| **성능** | 하이퍼바이저 오버헤드 존재 | 네이티브에 가까운 성능 |
| **격리 수준** | 강력 (하드웨어 수준 격리) | 상대적으로 약함 (커널 공유) |
| **이식성** | 하이퍼바이저 의존적 | 높음 (Docker 런타임만 있으면 됨) |
| **밀도** | 호스트당 수십 개 | 호스트당 수백 ~ 수천 개 |
| **대표 기술** | VMware, VirtualBox, KVM | Docker, containerd, Podman |

> **핵심 차이**: VM은 하이퍼바이저 위에 전체 OS를 올리는 반면, 컨테이너는 호스트 커널을 직접 공유하여 훨씬 경량하게 동작한다.

## 3. Docker 아키텍처

Docker는 클라이언트-서버 아키텍처로 구성되며, 세 가지 핵심 컴포넌트로 이루어져 있다.

### 3.1 Docker Client

사용자가 직접 상호작용하는 CLI 도구이다. `docker run`, `docker build` 등의 명령어를 Docker Daemon에 REST API로 전달한다.

```bash
# Docker Client가 Daemon에 명령을 전달하는 구조
docker run -d --name my-app nginx:latest
```

### 3.2 Docker Daemon (dockerd)

Docker의 핵심 엔진으로, 이미지 빌드, 컨테이너 실행, 네트워크/볼륨 관리 등을 담당한다. 호스트에서 백그라운드 프로세스로 실행되며, Docker Client의 API 요청을 수신하고 처리한다.

```
┌─────────────┐     REST API      ┌──────────────────┐
│ Docker CLI  │ ───────────────▶  │  Docker Daemon   │
│  (Client)   │                   │    (dockerd)     │
└─────────────┘                   │                  │
                                  │ ┌──────────────┐ │
                                  │ │ containerd   │ │
                                  │ │  ┌────────┐  │ │
                                  │ │  │  runc  │  │ │
                                  │ │  └────────┘  │ │
                                  │ └──────────────┘ │
                                  └──────────────────┘
```

- **containerd**: 컨테이너 라이프사이클(생성, 시작, 중지, 삭제)을 관리하는 고수준 런타임
- **runc**: OCI 표준을 구현한 저수준 컨테이너 런타임으로, 실제로 컨테이너를 생성하고 실행

### 3.3 Docker Registry

Docker 이미지를 저장하고 배포하는 저장소이다. Docker Hub가 기본 공개 레지스트리이며, 프라이빗 레지스트리를 직접 구축할 수도 있다.

```bash
# Docker Hub에서 이미지 풀
docker pull nginx:latest

# 프라이빗 레지스트리 사용 예시
docker pull registry.example.com/my-app:v1.0
```

## 4. Docker 이미지와 컨테이너의 관계

### 4.1 이미지(Image)

이미지는 컨테이너를 실행하기 위한 **읽기 전용 템플릿**이다. 애플리케이션 코드, 런타임, 라이브러리, 환경 변수, 설정 파일 등을 포함한다.

### 4.2 컨테이너(Container)

컨테이너는 이미지의 **실행 가능한 인스턴스**이다. 이미지 위에 읽기-쓰기 가능한 레이어를 추가하여 생성된다.

```bash
# 이미지 → 컨테이너 관계
docker run -d --name web nginx:latest   # 이미지로부터 컨테이너 생성·실행
docker run -d --name web2 nginx:latest  # 동일 이미지에서 여러 컨테이너 생성 가능
```

### 4.3 레이어(Layer) 구조

Docker 이미지는 여러 개의 읽기 전용 레이어로 구성된다. 각 Dockerfile 명령어가 하나의 레이어를 생성하며, 레이어는 캐싱되어 빌드 효율성을 높인다.

```
┌────────────────────────────┐
│   쓰기 가능한 컨테이너 레이어  │  ← 컨테이너 실행 시 추가
├────────────────────────────┤
│   Layer 4: CMD, EXPOSE     │  ← 읽기 전용
├────────────────────────────┤
│   Layer 3: COPY app.py     │  ← 읽기 전용
├────────────────────────────┤
│   Layer 2: RUN pip install │  ← 읽기 전용
├────────────────────────────┤
│   Layer 1: FROM python:3.12│  ← 베이스 이미지 (읽기 전용)
└────────────────────────────┘
```

## 5. Union File System (UnionFS)

Docker의 레이어 구조를 가능하게 하는 핵심 기술이 **Union File System**이다. UnionFS는 여러 파일시스템(레이어)을 하나의 통합된 뷰로 합쳐서 보여주는 기술이다.

### 동작 원리

- **읽기 작업**: 최상위 레이어부터 하위 레이어까지 순차적으로 탐색하여 파일을 찾는다.
- **쓰기 작업 (Copy-on-Write)**: 읽기 전용 레이어의 파일을 수정하면, 해당 파일을 쓰기 가능한 최상위 레이어에 복사한 후 수정한다.
- **삭제 작업**: 하위 레이어의 파일을 삭제할 때는 whiteout 파일을 생성하여 해당 파일을 숨긴다.

Docker는 현재 주로 **overlay2** 스토리지 드라이버를 사용한다:

```bash
# 현재 사용 중인 스토리지 드라이버 확인
docker info | grep "Storage Driver"
# 출력 예: Storage Driver: overlay2
```

### Copy-on-Write (CoW) 전략의 장점

1. **디스크 절약**: 동일 베이스 이미지를 공유하는 컨테이너들은 베이스 레이어를 재사용
2. **빠른 시작**: 이미지를 복사할 필요 없이 새 쓰기 레이어만 추가하면 됨
3. **효율적 빌드**: 변경되지 않은 레이어는 캐시에서 재사용

## 6. Docker의 핵심 장점

### 6.1 이식성 (Portability)

"내 머신에서는 되는데..."라는 문제를 해결한다. 컨테이너는 실행 환경을 통째로 패키징하므로, 개발·테스트·운영 환경 간 일관성을 보장한다.

```bash
# 로컬에서 빌드한 이미지를 어디서든 실행 가능
docker build -t my-app:v1.0 .
docker save my-app:v1.0 | gzip > my-app.tar.gz

# 다른 서버에서 로드 후 실행
docker load < my-app.tar.gz
docker run -d my-app:v1.0
```

### 6.2 경량성 (Lightweight)

VM 대비 극도로 가벼운 리소스 사용량으로, 동일 하드웨어에서 훨씬 높은 밀도로 워크로드를 실행할 수 있다.

```bash
# 실행 중인 컨테이너의 리소스 사용량 확인
docker stats --no-stream
# CONTAINER ID   NAME     CPU %   MEM USAGE / LIMIT     MEM %
# a1b2c3d4e5f6   nginx    0.00%   3.5MiB / 7.77GiB      0.04%
```

### 6.3 격리성 (Isolation)

각 컨테이너는 독립적인 프로세스, 네트워크, 파일시스템 네임스페이스를 갖는다. 하나의 컨테이너에서 발생한 문제가 다른 컨테이너나 호스트에 영향을 미치지 않는다.

```bash
# 각 컨테이너는 격리된 네임스페이스에서 실행
docker run --rm alpine cat /etc/hostname    # 컨테이너별 고유 hostname
docker run --rm alpine ps aux               # 컨테이너 내부의 프로세스만 보임
```

### 6.4 재현성 (Reproducibility)

Dockerfile과 docker-compose.yml을 버전 관리하면 인프라를 코드로 관리(IaC)할 수 있다. 언제든 동일한 환경을 재현할 수 있다.

### 6.5 빠른 배포와 스케일링

컨테이너의 빠른 시작 시간은 CI/CD 파이프라인과 오토스케일링에 이상적이다.

```bash
# Docker Compose로 간편한 스케일링
docker compose up -d --scale web=3
```

## 정리

Docker는 컨테이너 기술을 대중화시킨 플랫폼으로, 경량화된 가상화, 이식성, 빠른 배포를 가능하게 한다. 리눅스 커널의 Namespace와 Cgroup을 활용한 격리 환경 위에 Union File System의 레이어 구조와 Copy-on-Write 전략을 결합하여, 효율적이고 재현 가능한 애플리케이션 실행 환경을 제공한다.

다음 글에서는 Docker 이미지를 직접 만드는 **Dockerfile 작성 가이드**를 다룬다.
