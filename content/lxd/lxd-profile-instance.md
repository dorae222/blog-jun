---
title: "LXD 프로파일로 인스턴스 생성"
slug: "lxd-profile-instance"
category: cloud
tags: ["lxd", "profile", "docker-in-lxd", "container"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# LXD 프로파일로 인스턴스 생성

## 들어가며

LXD 프로파일은 인스턴스 설정의 **템플릿**이다. CPU, 메모리, 디스크, 네트워크 설정을 프로파일로 정의해두면 동일한 스펙의 인스턴스를 반복적으로 생성할 수 있다. 특히 Docker-in-LXD 패턴에서는 보안 설정이 핵심인데, 프로파일을 통해 이를 표준화할 수 있다.

## 프로파일 개념

### 프로파일이란?

프로파일은 인스턴스에 적용할 **설정 묶음**이다. 인스턴스 생성 시 하나 이상의 프로파일을 지정할 수 있으며, 여러 프로파일이 적용될 경우 나중에 지정된 프로파일이 우선한다.

```bash
# 프로파일 목록 확인
lxc profile list

# 기본 프로파일 확인
lxc profile show default
```

### 프로파일 계층 구조

```
┌──────────────────────────────────────────┐
│ 인스턴스 직접 설정 (최우선)                │
├──────────────────────────────────────────┤
│ 프로파일 C (마지막 적용 = 높은 우선순위)    │
├──────────────────────────────────────────┤
│ 프로파일 B                                │
├──────────────────────────────────────────┤
│ 프로파일 A (처음 적용 = 낮은 우선순위)      │
├──────────────────────────────────────────┤
│ default 프로파일 (기본 적용)               │
└──────────────────────────────────────────┘
```

이 계층 구조를 활용하면 **기본 설정 + 역할별 설정**을 조합할 수 있다.

```bash
# 여러 프로파일을 적용하여 인스턴스 생성
lxc launch ubuntu:24.04 my-container \
  --profile default \
  --profile docker-ready \
  --profile high-memory
```

## 프로파일 YAML 구조

프로파일 YAML은 크게 `config`(시스템 설정)와 `devices`(디바이스 설정) 두 영역으로 나뉜다.

```yaml
# 프로파일 기본 구조
config:
  # 리소스 제한, 보안 설정 등
  limits.cpu: "4"
  limits.memory: 8GB

description: "프로파일 설명"

devices:
  # 디스크, 네트워크 등 디바이스 정의
  root:
    path: /
    pool: default
    size: 50GiB
    type: disk
  eth0:
    name: eth0
    network: lxdbr0
    type: nic
```

## 리소스 제한 설정

### CPU 제한

```yaml
config:
  # 고정 CPU 코어 수
  limits.cpu: "4"

  # 특정 코어 지정 (0, 1, 2, 3번 코어)
  limits.cpu: "0-3"

  # CPU 사용 비율 (밀리초 단위)
  limits.cpu.allowance: 50%

  # CFS 스케줄러 기반 제한
  limits.cpu.allowance: 100ms/200ms
```

| 설정 | 효과 |
|------|------|
| `limits.cpu: "4"` | 4개 코어 사용 (자동 할당) |
| `limits.cpu: "0,2"` | 0번, 2번 코어만 사용 |
| `limits.cpu: "0-3"` | 0~3번 코어 사용 |
| `limits.cpu.allowance: 50%` | 전체 CPU의 50%만 사용 |

### 메모리 제한

```yaml
config:
  # 고정 메모리 제한
  limits.memory: 8GB

  # 스왑 사용 금지
  limits.memory.swap: "false"

  # 메모리 OOM 우선순위 (0~1000, 낮을수록 우선 kill)
  limits.memory.swap.priority: "0"
```

### CPU와 메모리를 확인하는 방법

```bash
# 인스턴스 내부에서 확인
lxc exec my-container -- nproc
lxc exec my-container -- free -h

# 호스트에서 인스턴스 리소스 사용량 확인
lxc info my-container
```

## 디스크 설정

### root 디바이스

모든 인스턴스에는 루트 디스크가 필요하다.

```yaml
devices:
  root:
    type: disk
    path: /
    pool: default
    size: 50GiB
```

### 추가 디스크 마운트

호스트의 디렉토리를 컨테이너에 마운트할 수 있다.

```yaml
devices:
  shared-data:
    type: disk
    source: /opt/shared-data
    path: /mnt/shared
    readonly: "false"
```

### 디스크 I/O 제한

```yaml
devices:
  root:
    type: disk
    path: /
    pool: default
    size: 50GiB
    limits.read: 100MB
    limits.write: 50MB
```

## 네트워크 디바이스

### 브릿지 연결 (기본)

```yaml
devices:
  eth0:
    type: nic
    name: eth0
    network: lxdbr0
```

### 고정 IP 할당

DHCP가 아닌 고정 IP를 할당하면 서비스 운영이 안정적이다.

```yaml
devices:
  eth0:
    type: nic
    name: eth0
    network: lxdbr0
    ipv4.address: 10.0.0.10
```

컨테이너 안에서는 별도의 네트워크 설정이 필요 없다. LXD의 DHCP 서버가 해당 MAC에 고정 IP를 할당한다.

### 여러 네트워크 인터페이스

```yaml
devices:
  eth0:
    type: nic
    name: eth0
    network: lxdbr0
    ipv4.address: 10.0.0.10
  eth1:
    type: nic
    name: eth1
    nictype: macvlan
    parent: enp0s3
```

## Docker-in-LXD 보안 설정

LXD 컨테이너 안에서 Docker를 실행하려면 특별한 보안 설정이 필요하다. 이것이 프로파일에서 가장 중요한 부분이다.

### 필수 설정

```yaml
config:
  # Docker가 내부 컨테이너를 만들 수 있도록 중첩 허용
  security.nesting: "true"

  # overlay2 스토리지 드라이버에 필요한 syscall 허용
  security.syscalls.intercept.mknod: "true"
  security.syscalls.intercept.setxattr: "true"
```

### 각 설정의 의미

| 설정 | 목적 | 없으면? |
|------|------|---------|
| `security.nesting` | 컨테이너 안에서 또 다른 컨테이너(Docker) 생성 허용 | Docker 데몬 시작 실패 |
| `security.syscalls.intercept.mknod` | 디바이스 노드 생성 시스템콜 허용 | overlay2 마운트 실패 |
| `security.syscalls.intercept.setxattr` | 확장 속성 설정 시스템콜 허용 | overlay2 마운트 실패 |

### security.nesting의 동작 원리

`security.nesting: true`로 설정하면 LXD는 다음을 수행한다:

1. 컨테이너 내부에서 사용 가능한 네임스페이스를 확장
2. AppArmor 프로파일을 완화하여 내부 마운트 허용
3. cgroup v2 위임을 활성화하여 내부 컨테이너 리소스 관리 허용

> 보안상 `security.nesting`은 Docker가 필요한 컨테이너에만 적용해야 한다. 모든 컨테이너에 일괄 적용하는 것은 권장하지 않는다.

## 실전 프로파일 예시

### 웹서버 프로파일 (Docker-in-LXD)

실제 웹 서비스를 운영하기 위한 프로파일이다.

```yaml
# web-server-profile.yaml
config:
  limits.cpu: "4"
  limits.memory: 8GB
  limits.memory.swap: "false"

  # Docker-in-LXD 필수 설정
  security.nesting: "true"
  security.syscalls.intercept.mknod: "true"
  security.syscalls.intercept.setxattr: "true"

  # 부팅 설정
  boot.autostart: "true"
  boot.autostart.priority: "10"

description: "Docker 기반 웹서버 프로파일 (4 vCPU, 8GB RAM, 50GB Disk)"

devices:
  root:
    type: disk
    path: /
    pool: default
    size: 50GiB
  eth0:
    type: nic
    name: eth0
    network: lxdbr0
    ipv4.address: 10.0.0.10
```

### 프로파일 적용

```bash
# 프로파일 생성
lxc profile create web-server

# YAML 파일로 프로파일 설정
lxc profile edit web-server < web-server-profile.yaml

# 또는 cat을 사용하여 직접 입력
cat web-server-profile.yaml | lxc profile edit web-server

# 프로파일 확인
lxc profile show web-server
```

### 인스턴스 생성 및 프로파일 적용

```bash
# 프로파일을 지정하여 인스턴스 생성
lxc launch ubuntu:24.04 my-web-server --profile default --profile web-server

# 생성된 인스턴스 확인
lxc list
# +---------------+---------+---------------------+------+------------+
# |     NAME      |  STATE  |        IPV4         | TYPE | SNAPSHOTS  |
# +---------------+---------+---------------------+------+------------+
# | my-web-server | RUNNING | 10.0.0.10 (eth0)    | CONT | 0          |
# +---------------+---------+---------------------+------+------------+

# 인스턴스 상세 정보 (적용된 프로파일, 리소스 확인)
lxc config show my-web-server
```

### 기존 인스턴스에 프로파일 추가/변경

```bash
# 프로파일 추가
lxc profile add my-web-server high-memory

# 프로파일 제거
lxc profile remove my-web-server high-memory

# 적용된 프로파일 목록 확인
lxc config show my-web-server | grep profiles -A 5
```

## 프로파일 관리 명령어 정리

```bash
# 프로파일 CRUD
lxc profile create <name>          # 생성
lxc profile show <name>            # 조회
lxc profile edit <name>            # 편집 (에디터 열림)
lxc profile delete <name>          # 삭제
lxc profile list                   # 목록
lxc profile copy <src> <dst>       # 복사
lxc profile rename <old> <new>     # 이름 변경

# 개별 설정 변경
lxc profile set <name> limits.cpu 8
lxc profile set <name> limits.memory 16GB
lxc profile unset <name> limits.cpu

# 디바이스 관리
lxc profile device add <name> <device-name> <type> key=value
lxc profile device remove <name> <device-name>
lxc profile device list <name>
```

## 프로파일 설계 패턴

### 계층적 프로파일 조합

역할별로 프로파일을 분리하면 유연한 조합이 가능하다.

```
default          : 기본 네트워크, 기본 디스크
├── docker-ready : security.nesting 등 Docker 설정
├── small        : 2 vCPU, 4GB RAM
├── medium       : 4 vCPU, 8GB RAM
├── large        : 8 vCPU, 16GB RAM
└── gpu          : GPU 패스스루 설정
```

```bash
# 중형 Docker 인스턴스
lxc launch ubuntu:24.04 app-server \
  --profile default --profile docker-ready --profile medium

# 대형 GPU 인스턴스
lxc launch ubuntu:24.04 ml-server \
  --profile default --profile docker-ready --profile large --profile gpu
```

이 패턴을 사용하면 새로운 스펙 조합이 필요할 때 프로파일만 추가하면 된다. 기존 프로파일을 수정할 필요가 없으므로 운영 안정성이 높아진다.

## 마무리

프로파일은 LXD 인프라 관리의 핵심이다. 특히 Docker-in-LXD를 위한 보안 설정(`security.nesting`, `security.syscalls.intercept.*`)은 프로파일로 표준화해두면 실수를 방지할 수 있다. 고정 IP, 리소스 제한, 자동 부팅 등의 운영 설정도 프로파일에 포함시켜 인스턴스 생성을 완전히 자동화할 수 있다.

다음 글에서는 생성된 인스턴스에 소프트웨어를 자동 설치하는 프로비저닝 자동화를 다룬다.

## 시리즈 안내

1. LXD 개요: 시스템 컨테이너의 세계
2. LXD 설치 및 초기 설정
3. **LXD 프로파일로 인스턴스 생성** (현재 글)
4. LXD 프로비저닝 자동화
5. LXD 네트워킹 & SSH ProxyJump
6. Cloudflare Tunnel로 LXD 컨테이너 외부 노출
7. LXD에서 Docker Compose 프로덕션 운영
