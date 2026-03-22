---
title: "LXD 설치 및 초기 설정"
slug: "lxd-install-setup"
category: cloud
tags: ["lxd", "installation", "zfs", "storage", "networking"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# LXD 설치 및 초기 설정

## 들어가며

LXD를 실제로 사용하려면 설치 후 초기 설정(init)을 거쳐야 한다. 이 과정에서 **스토리지 백엔드**, **네트워크 브릿지**, **보안 설정** 등 인프라의 기반이 결정된다. 이 글에서는 snap을 통한 설치부터 대화형 설정, 그리고 자동화를 위한 preseed 방식까지 다룬다.

## LXD 설치

### snap을 통한 설치 (권장)

Ubuntu에서 LXD는 snap 패키지로 배포된다. 커널 모듈과의 호환성 관리가 자동으로 이루어지므로 snap 설치를 권장한다.

```bash
# snap 설치 (Ubuntu 서버에는 보통 이미 설치되어 있음)
sudo snap install lxd

# 안정 채널 고정 (선택)
sudo snap install lxd --channel=5.21/stable

# 설치 확인
lxd --version

# 현재 사용자를 lxd 그룹에 추가 (sudo 없이 사용하기 위해)
sudo usermod -aG lxd $USER

# 그룹 변경 적용 (재로그인 또는)
newgrp lxd
```

### 버전 채널 선택

| 채널 | 설명 | 용도 |
|------|------|------|
| `5.21/stable` | LTS 기반 안정 버전 | 프로덕션 |
| `latest/stable` | 최신 안정 버전 | 새 기능 활용 |
| `latest/candidate` | 릴리즈 후보 | 테스트 |
| `latest/edge` | 개발 빌드 | 개발/디버깅 |

프로덕션 환경에서는 LTS 채널을 사용하는 것이 안전하다.

## lxd init: 대화형 초기 설정

설치 후 `lxd init` 명령으로 초기 설정을 진행한다. 각 항목이 인프라에 미치는 영향을 이해하는 것이 중요하다.

```bash
sudo lxd init
```

### 대화형 설정 항목 상세

```
Would you like to use LXD clustering? (yes/no) [default=no]: no
```
단일 서버 운영이면 `no`를 선택한다. 클러스터링은 여러 물리 서버를 하나의 LXD 풀로 묶을 때 사용한다.

```
Do you want to configure a new storage pool? (yes/no) [default=yes]: yes
Name of the new storage pool [default=default]:
Name of the storage backend to use (dir, btrfs, zfs, ...) [default=zfs]: zfs
Create a new ZFS pool? (yes/no) [default=yes]: yes
Would you like to use an existing block device? (yes/no) [default=no]: no
Size in GiB of the new loop device (1GiB minimum) [default=30GiB]: 100
```

```
Would you like to connect to a MAAS server? (yes/no) [default=no]: no
```

```
Would you like to create a new local network bridge? (yes/no) [default=yes]: yes
What should the new bridge be called? [default=lxdbr0]:
What IPv4 address should be used? (CIDR subnet notation, "auto" or "none") [default=auto]: 10.0.0.1/24
What IPv6 address should be used? (CIDR subnet notation, "auto" or "none") [default=auto]: none
```
IPv6을 사용하지 않는다면 `none`으로 설정해 불필요한 복잡도를 줄인다.

```
Would you like the LXD server to be available over the network? (yes/no) [default=no]: yes
Address to bind LXD to (not including port) [default=all]:
Port to bind LXD to [default=8443]:
Trust password for new clients:
```
리모트 관리가 필요하면 네트워크 노출을 활성화한다. Trust password는 다른 호스트에서 `lxc remote add` 시 사용된다.

```
Would you like stale cached images to be updated automatically? (yes/no) [default=yes]: yes
Would you like a YAML "lxd init" preseed to be printed? (yes/no) [default=no]: yes
```
마지막에 preseed YAML을 출력하면 동일 설정을 다른 서버에 재현할 수 있다.

## 스토리지 백엔드 선택

스토리지 백엔드는 LXD 성능과 기능에 직접적인 영향을 미친다.

### 비교표

| 기능 | dir | ZFS | Btrfs | LVM | Ceph |
|------|-----|-----|-------|-----|------|
| **설치 난이도** | 매우 쉬움 | 쉬움 | 쉬움 | 보통 | 어려움 |
| **스냅샷** | 느림 (복사) | 빠름 (COW) | 빠름 (COW) | 빠름 | 빠름 |
| **압축** | 불가 | 지원 | 지원 | 불가 | 불가 |
| **중복 제거** | 불가 | 지원 | 불가 | 불가 | 불가 |
| **성능** | 보통 | 우수 | 우수 | 우수 | 우수 |
| **안정성** | 높음 | 매우 높음 | 높음 | 높음 | 매우 높음 |
| **클러스터** | 불가 | 불가 | 불가 | 불가 | 지원 |

### ZFS (권장)

ZFS는 LXD의 가장 인기 있는 스토리지 백엔드다. COW 스냅샷, 투명 압축, 중복 제거를 모두 지원한다.

```bash
# ZFS 풀 상태 확인
sudo zpool status

# ZFS 풀 용량 확인
sudo zpool list

# 압축 설정 확인
sudo zfs get compression default

# 수동으로 ZFS 풀 생성 (블록 디바이스 사용)
sudo zpool create lxd-pool /dev/sdb
lxc storage create my-pool zfs source=lxd-pool
```

### ZFS 스냅샷 활용

```bash
# 컨테이너 스냅샷 생성 (ZFS COW로 즉각적)
lxc snapshot my-container backup-20260322

# 스냅샷 목록 확인
lxc info my-container | grep -A 20 Snapshots

# 스냅샷에서 새 컨테이너 생성
lxc copy my-container/backup-20260322 restored-container

# 스냅샷으로 복원
lxc restore my-container backup-20260322
```

### Btrfs

Btrfs는 ZFS보다 설정이 간단하고 리눅스 커널에 내장되어 있다.

```bash
# Btrfs 스토리지 풀 생성
lxc storage create my-btrfs-pool btrfs size=100GiB

# Btrfs 서브볼륨 확인
sudo btrfs subvolume list /var/snap/lxd/common/lxd/storage-pools/my-btrfs-pool
```

### dir (테스트용)

가장 단순한 백엔드로, 일반 디렉토리를 사용한다. 스냅샷이 전체 복사로 이루어지므로 프로덕션에는 적합하지 않다.

```bash
lxc storage create simple-pool dir
```

## 네트워크 설정: lxdbr0

### 브릿지 네트워크 상세

`lxdbr0`는 LXD가 관리하는 Linux 브릿지다. NAT, DHCP, DNS를 자체적으로 제공한다.

```bash
# 네트워크 상태 확인
lxc network show lxdbr0
```

출력 예시:

```yaml
config:
  dns.domain: lxd
  dns.mode: managed
  ipv4.address: 10.0.0.1/24
  ipv4.dhcp: "true"
  ipv4.dhcp.ranges: 10.0.0.2-10.0.0.254
  ipv4.nat: "true"
  ipv6.address: none
description: ""
name: lxdbr0
type: bridge
managed: true
status: Created
```

### 주요 네트워크 설정 항목

```bash
# DHCP 범위 조정
lxc network set lxdbr0 ipv4.dhcp.ranges 10.0.0.100-10.0.0.200

# DNS 도메인 변경
lxc network set lxdbr0 dns.domain my-lab

# MTU 설정
lxc network set lxdbr0 bridge.mtu 9000

# NAT 상태 확인
lxc network get lxdbr0 ipv4.nat
```

### NAT와 iptables

LXD는 lxdbr0에 대해 자동으로 iptables NAT 규칙을 설정한다.

```bash
# LXD가 추가한 iptables 규칙 확인
sudo iptables -t nat -L -n | grep 10.0.0
# MASQUERADE  all  -- 10.0.0.0/24  !10.0.0.0/24
```

이를 통해 컨테이너에서 외부 인터넷 접속이 가능해진다.

## Preseed를 이용한 자동 설정

동일한 설정을 여러 서버에 반복 적용하거나 IaC(Infrastructure as Code) 관리를 하려면 preseed YAML을 사용한다.

```yaml
# preseed.yaml
config:
  core.https_address: '[::]:8443'
  core.trust_password: your-secure-password
networks:
- config:
    ipv4.address: 10.0.0.1/24
    ipv4.nat: "true"
    ipv6.address: none
  description: ""
  name: lxdbr0
  type: bridge
  project: default
storage_pools:
- config:
    size: 100GiB
  description: ""
  name: default
  driver: zfs
profiles:
- config: {}
  description: Default LXD profile
  devices:
    eth0:
      name: eth0
      network: lxdbr0
      type: nic
    root:
      path: /
      pool: default
      size: 50GiB
      type: disk
  name: default
projects: []
cluster: null
```

적용 방법:

```bash
# preseed 파일로 자동 초기화
cat preseed.yaml | sudo lxd init --preseed

# 또는 파이프로
sudo lxd init --preseed < preseed.yaml
```

## 리모트 서버 관리

LXD는 리모트 서버를 등록하여 로컬에서 원격 인스턴스를 관리할 수 있다.

```bash
# 리모트 서버 추가
lxc remote add my-lxd-host https://my-lxd-host:8443

# 리모트 서버 목록
lxc remote list

# 리모트 서버의 인스턴스 조회
lxc list my-lxd-host:

# 리모트 서버에 인스턴스 생성
lxc launch ubuntu:24.04 my-lxd-host:test-container

# 서버 간 인스턴스 복사
lxc copy my-lxd-host:my-container local:my-container-copy
```

## 이미지 서버

LXD는 여러 공식 이미지 서버를 제공한다.

```bash
# 기본 이미지 서버 목록
lxc remote list

# ubuntu: 공식 Ubuntu 이미지
# images: 다양한 배포판 이미지 (community)

# Ubuntu 이미지 검색
lxc image list ubuntu: 24.04 architecture=amd64

# 다른 배포판 이미지 검색
lxc image list images: debian/12
lxc image list images: rocky/9
lxc image list images: alpine/3.19

# 이미지 다운로드 (캐시)
lxc image copy ubuntu:24.04 local: --alias ubuntu-2404

# 로컬 이미지 목록
lxc image list local:
```

## 설치 후 검증

모든 설정이 완료되면 다음 항목을 확인한다.

```bash
# LXD 상태 확인
lxc info

# 스토리지 풀 확인
lxc storage list
lxc storage info default

# 네트워크 확인
lxc network list
lxc network info lxdbr0

# 프로파일 확인
lxc profile list
lxc profile show default

# 테스트 컨테이너 생성·삭제
lxc launch ubuntu:24.04 test-container
lxc exec test-container -- cat /etc/os-release
lxc exec test-container -- ping -c 2 8.8.8.8
lxc delete test-container --force
```

모든 검증이 통과하면 LXD를 사용할 준비가 된 것이다.

## 마무리

LXD 초기 설정에서 가장 중요한 결정은 **스토리지 백엔드**와 **네트워크 구성**이다. ZFS를 선택하면 스냅샷, 압축, 중복 제거의 이점을 누릴 수 있고, lxdbr0 브릿지의 NAT/DHCP 설정으로 별도의 네트워크 장비 없이도 격리된 네트워크를 구성할 수 있다.

다음 글에서는 LXD 프로파일을 활용해 표준화된 인스턴스를 생성하는 방법을 다룬다.

## 시리즈 안내

1. LXD 개요: 시스템 컨테이너의 세계
2. **LXD 설치 및 초기 설정** (현재 글)
3. LXD 프로파일로 인스턴스 생성
4. LXD 프로비저닝 자동화
5. LXD 네트워킹 & SSH ProxyJump
6. Cloudflare Tunnel로 LXD 컨테이너 외부 노출
7. LXD에서 Docker Compose 프로덕션 운영
