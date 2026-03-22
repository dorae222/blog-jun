---
title: "LXD 네트워킹 & SSH ProxyJump"
slug: "lxd-networking-ssh"
category: cloud
tags: ["lxd", "networking", "ssh", "proxyjump", "bridge"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# LXD 네트워킹 & SSH ProxyJump

## 들어가며

LXD 컨테이너를 효과적으로 운영하려면 네트워크 구조를 이해해야 한다. 컨테이너는 호스트의 내부 네트워크에 위치하므로, 외부에서 접속하려면 **SSH ProxyJump** 같은 접속 체인이 필요하다. 이 글에서는 LXD 네트워크 모드, lxdbr0 브릿지의 동작 방식, 그리고 SSH 접속 설정을 상세히 다룬다.

## LXD 네트워크 모드

LXD는 여러 네트워크 모드를 지원한다. 용도에 따라 적절한 모드를 선택한다.

### 네트워크 모드 비교

| 모드 | 설명 | 컨테이너 IP | 호스트 네트워크와 관계 | 용도 |
|------|------|------------|---------------------|------|
| **bridge** | 가상 브릿지에 연결 | 별도 서브넷 | NAT로 분리 | 기본, 가장 일반적 |
| **macvlan** | 물리 NIC에 가상 MAC 부여 | 호스트와 같은 서브넷 | 직접 연결 | 외부 직접 접속 필요 시 |
| **sriov** | 물리 NIC 가상화 (SR-IOV) | 호스트와 같은 서브넷 | 하드웨어 분리 | 고성능 네트워크 |
| **ovn** | 오버레이 네트워크 | 가상 서브넷 | 소프트웨어 정의 | 대규모 클러스터 |

대부분의 경우 **bridge** 모드로 충분하다. 이 글에서는 bridge 모드를 중심으로 설명한다.

## lxdbr0 브릿지 상세

### 브릿지 네트워크 구조

```
┌─────────────────────────────────────────────────────┐
│ 물리 서버                                            │
│                                                     │
│  ┌─── 물리 NIC (enp0s3) ────┐                      │
│  │ 192.168.1.x (외부 접속)   │                      │
│  └───────────┬───────────────┘                      │
│              │                                      │
│  ┌───────────┴────── iptables NAT ──────────────┐   │
│  │                                               │   │
│  │  ┌─── lxdbr0 (10.0.0.1/24) ───┐             │   │
│  │  │  DHCP: 10.0.0.2~254        │             │   │
│  │  │  DNS:  lxdbr0 내장          │             │   │
│  │  │  NAT:  자동 MASQUERADE      │             │   │
│  │  └──┬──────────┬──────────┬───┘             │   │
│  │     │          │          │                  │   │
│  │  ┌──┴──┐  ┌───┴──┐  ┌───┴──┐              │   │
│  │  │ C-1 │  │ C-2  │  │ C-3  │              │   │
│  │  │.10  │  │.20   │  │.30   │              │   │
│  │  └─────┘  └──────┘  └──────┘              │   │
│  └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### lxdbr0의 핵심 기능

**1. NAT (Network Address Translation)**

컨테이너의 사설 IP(10.0.0.x)를 호스트의 공인 IP로 변환하여 인터넷 접속을 가능하게 한다.

```bash
# NAT 규칙 확인
sudo iptables -t nat -L POSTROUTING -n -v
# MASQUERADE  all  --  10.0.0.0/24  !10.0.0.0/24

# 컨테이너에서 외부 접속 테스트
lxc exec my-container -- curl -s ifconfig.me
# → 호스트의 공인 IP가 출력됨
```

**2. DHCP**

컨테이너에 자동으로 IP를 할당한다. 프로파일에서 고정 IP를 지정하면 해당 MAC에 고정 할당된다.

```bash
# DHCP 설정 확인
lxc network show lxdbr0 | grep dhcp

# DHCP 리스 확인 (dnsmasq)
lxc network list-leases lxdbr0
# +-------------------+-------------------+----------+------+
# |       NAME        |    MAC ADDRESS    | IP       | TYPE |
# +-------------------+-------------------+----------+------+
# | my-web-server     | 00:16:3e:xx:xx:xx | 10.0.0.10| DYNAMIC|
# +-------------------+-------------------+----------+------+
```

**3. DNS**

lxdbr0에 연결된 컨테이너들은 서로를 이름으로 찾을 수 있다.

```bash
# 컨테이너 간 DNS 해결
lxc exec container-a -- ping container-b.lxd
# PING container-b.lxd (10.0.0.20): 56 data bytes
```

## 고정 IP 할당

서비스를 운영할 때는 반드시 고정 IP를 사용해야 한다. 두 가지 방법이 있다.

### 방법 1: 프로파일에서 설정 (권장)

```yaml
devices:
  eth0:
    type: nic
    name: eth0
    network: lxdbr0
    ipv4.address: 10.0.0.10
```

### 방법 2: 인스턴스 개별 설정

```bash
# 인스턴스의 네트워크 디바이스에 직접 설정
lxc config device override my-container eth0 ipv4.address=10.0.0.10

# 설정 확인
lxc config device show my-container
```

### 고정 IP 적용 후 확인

```bash
# 컨테이너 재시작으로 새 IP 적용
lxc restart my-container

# IP 확인
lxc list my-container -c n4
# +----------------+-------------------+
# |      NAME      |       IPV4        |
# +----------------+-------------------+
# | my-container   | 10.0.0.10 (eth0)  |
# +----------------+-------------------+
```

## 다중 네트워크 인터페이스

하나의 컨테이너에 여러 네트워크를 연결할 수 있다. 관리 네트워크와 서비스 네트워크를 분리할 때 유용하다.

```bash
# 두 번째 브릿지 생성
lxc network create lxdbr1 ipv4.address=10.0.1.1/24 ipv4.nat=true ipv6.address=none

# 컨테이너에 두 번째 인터페이스 추가
lxc config device add my-container eth1 nic network=lxdbr1 ipv4.address=10.0.1.10

# 확인
lxc exec my-container -- ip addr show
```

## macvlan 모드

macvlan을 사용하면 컨테이너가 호스트와 동일한 네트워크에 직접 연결된다.

```bash
# macvlan 네트워크 생성
lxc network create my-macvlan \
    --type=macvlan \
    parent=enp0s3

# macvlan 프로파일 적용
lxc config device add my-container eth0 nic \
    nictype=macvlan \
    parent=enp0s3
```

> 주의: macvlan을 사용하면 **호스트와 컨테이너 간 통신이 불가능**하다. 외부에서 컨테이너에 직접 접속은 가능하지만, 같은 호스트에서의 접속은 추가 설정이 필요하다.

## SSH 접속 체인

### 접속 구조

LXD 컨테이너는 내부 네트워크(10.0.0.x)에 위치하므로, 외부에서 직접 SSH 접속이 불가능하다. **SSH ProxyJump**를 사용하면 중간 호스트를 경유하여 투명하게 접속할 수 있다.

```
┌──────────┐    SSH    ┌──────────────┐    SSH    ┌──────────────┐
│ 내 PC    │ ───────→  │ Jump Host    │ ───────→  │ LXD Container│
│ (외부)   │           │ (192.168.1.x)│           │ (10.0.0.10)  │
└──────────┘           └──────────────┘           └──────────────┘
                       공인 IP 또는               lxdbr0 내부 IP
                       VPN 접속 가능
```

### SSH ProxyJump 설정

`~/.ssh/config` 파일에 다음과 같이 설정한다.

```
# ~/.ssh/config

# Jump Host (중간 경유 서버)
Host my-jump-host
    HostName 192.168.1.x
    User your-username
    Port 22
    IdentityFile ~/.ssh/id_ed25519

# LXD 컨테이너 (Jump Host를 경유)
Host my-container
    HostName 10.0.0.10
    User root
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ProxyJump my-jump-host

# 같은 호스트의 다른 컨테이너
Host my-container-2
    HostName 10.0.0.20
    User root
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ProxyJump my-jump-host
```

### 접속 테스트

```bash
# 한 줄 명령으로 컨테이너 직접 접속
ssh my-container

# ProxyJump를 직접 지정 (config 파일 없이)
ssh -J your-username@192.168.1.x root@10.0.0.10

# 다단계 점프 (hop이 2개 이상)
ssh -J user1@host1,user2@host2 root@10.0.0.10
```

### SCP/SFTP도 ProxyJump 지원

```bash
# 파일 복사
scp ./deploy.tar.gz my-container:/opt/app/

# 디렉토리 복사
scp -r ./config/ my-container:/opt/app/config/

# sftp 접속
sftp my-container
```

### VS Code Remote SSH

VS Code의 Remote SSH 확장도 `~/.ssh/config`를 읽으므로, ProxyJump 설정이 그대로 적용된다.

1. Remote SSH 확장 설치
2. `Remote-SSH: Connect to Host` 실행
3. `my-container` 선택
4. Jump Host를 경유하여 자동 접속

## SSH 디버깅

SSH 접속에 문제가 있을 때의 디버깅 방법이다.

### 단계별 확인

```bash
# 1. Jump Host 접속 확인
ssh my-jump-host

# 2. Jump Host에서 컨테이너 접속 확인
ssh root@10.0.0.10

# 3. 상세 로그 확인 (-v, -vv, -vvv)
ssh -vvv my-container

# 4. 컨테이너 SSH 서비스 상태 확인
lxc exec my-container -- systemctl status ssh

# 5. 컨테이너 SSH 로그 확인
lxc exec my-container -- journalctl -u ssh --no-pager -n 20

# 6. 방화벽 확인
lxc exec my-container -- iptables -L -n
```

### 자주 발생하는 문제와 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| Connection refused | SSH 서비스 미실행 | `systemctl start ssh` |
| Permission denied | 키 불일치 또는 권한 | authorized_keys 확인, chmod 600 |
| Connection timed out | 네트워크 도달 불가 | IP, 라우팅, 방화벽 확인 |
| Host key verification failed | 호스트 키 변경 | `ssh-keygen -R <host>` |

### SSH 키 관리

```bash
# ED25519 키 생성 (권장)
ssh-keygen -t ed25519 -C "your-key-comment"

# 공개키 확인
cat ~/.ssh/id_ed25519.pub

# 컨테이너에 공개키 추가 (lxc를 통해)
lxc exec my-container -- mkdir -p /root/.ssh
lxc file push ~/.ssh/id_ed25519.pub my-container/root/.ssh/authorized_keys
lxc exec my-container -- chmod 600 /root/.ssh/authorized_keys
lxc exec my-container -- chmod 700 /root/.ssh
```

## proxy device: 포트 포워딩 대안

SSH ProxyJump 외에도, LXD의 **proxy device**를 사용하면 호스트의 포트를 컨테이너로 직접 포워딩할 수 있다.

```bash
# 호스트의 8080 포트를 컨테이너의 80 포트로 포워딩
lxc config device add my-container http-proxy proxy \
    listen=tcp:0.0.0.0:8080 \
    connect=tcp:127.0.0.1:80

# 호스트의 2222 포트를 컨테이너의 22 포트로 포워딩
lxc config device add my-container ssh-proxy proxy \
    listen=tcp:0.0.0.0:2222 \
    connect=tcp:127.0.0.1:22

# proxy device 확인
lxc config device show my-container

# 포트 포워딩을 통한 SSH 접속
ssh -p 2222 root@192.168.1.x
```

### proxy device vs ProxyJump 비교

| 항목 | proxy device | ProxyJump |
|------|-------------|-----------|
| 설정 위치 | LXD 서버 | 클라이언트 SSH config |
| 포트 충돌 | 호스트 포트 사용 (충돌 가능) | 없음 |
| 보안 | 호스트 포트 노출 | 경유만 (노출 없음) |
| 편의성 | 직접 접속 가능 | config 설정 필요 |
| 범용성 | SSH 외 서비스도 가능 | SSH 전용 |

일반적으로 **SSH 접속에는 ProxyJump**, **웹 서비스 테스트에는 proxy device**를 사용하는 것이 좋다. 프로덕션 웹 서비스 노출에는 다음 글에서 다룰 Cloudflare Tunnel을 권장한다.

## 네트워크 모니터링

```bash
# 모든 컨테이너의 IP 확인
lxc list -c ns4

# 특정 네트워크의 연결 상태
lxc network info lxdbr0

# 네트워크 사용량 확인
lxc info my-container | grep -A 5 "Network usage"

# 컨테이너 간 연결 테스트
lxc exec container-a -- ping -c 3 10.0.0.20
```

## 마무리

LXD 네트워킹의 핵심은 **lxdbr0 브릿지**와 **SSH ProxyJump**다. 브릿지 네트워크가 NAT, DHCP, DNS를 자동 관리해주므로 별도의 네트워크 인프라 없이도 격리된 환경을 구축할 수 있다. SSH ProxyJump를 설정하면 마치 직접 접속하는 것처럼 편리하게 컨테이너에 접근할 수 있다.

다음 글에서는 Cloudflare Tunnel을 사용하여 LXD 컨테이너의 서비스를 안전하게 외부에 노출하는 방법을 다룬다.

## 시리즈 안내

1. LXD 개요: 시스템 컨테이너의 세계
2. LXD 설치 및 초기 설정
3. LXD 프로파일로 인스턴스 생성
4. LXD 프로비저닝 자동화
5. **LXD 네트워킹 & SSH ProxyJump** (현재 글)
6. Cloudflare Tunnel로 LXD 컨테이너 외부 노출
7. LXD에서 Docker Compose 프로덕션 운영
