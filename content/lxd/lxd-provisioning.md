---
title: "LXD 프로비저닝 자동화"
slug: "lxd-provisioning"
category: cloud
tags: ["lxd", "provisioning", "cloud-init", "docker", "automation"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# LXD 프로비저닝 자동화

## 들어가며

LXD 인스턴스를 생성한 후에는 Docker, SSH, Git 등의 소프트웨어를 설치하고 설정해야 한다. 이 과정을 매번 수동으로 하면 시간이 들고 실수가 발생한다. 이 글에서는 **셸 스크립트**와 **cloud-init**을 활용하여 프로비저닝을 자동화하는 방법을 다룬다.

## 프로비저닝이란?

프로비저닝(Provisioning)은 인프라 리소스를 사용 가능한 상태로 만드는 과정이다. LXD 컨텍스트에서는 다음을 의미한다:

1. **패키지 설치**: Docker, Git, Node.js, cloudflared 등
2. **서비스 설정**: SSH 보안 설정, Docker 데몬 설정
3. **사용자 설정**: SSH 키 등록, 권한 부여
4. **환경 준비**: 디렉토리 구조, 환경 변수

```
인스턴스 생성 → 프로비저닝 → 서비스 배포 → 운영
   (LXD)      (이 글의 범위)   (Docker Compose)
```

## 프로비저닝 방식 비교

| 방식 | 장점 | 단점 | 적합한 상황 |
|------|------|------|------------|
| 수동 (lxc exec) | 즉시 실행, 유연함 | 재현 불가, 실수 위험 | 1회성 테스트 |
| 셸 스크립트 | 간단, 디버깅 쉬움 | 상태 관리 없음 | 소규모 인프라 |
| cloud-init | 인스턴스 생성과 동시 실행 | 디버깅 어려움 | 자동화된 배포 |
| Ansible | 멱등성, 상태 관리 | 학습 곡선, 복잡도 | 대규모 인프라 |

이 글에서는 가장 실용적인 **셸 스크립트 방식**을 중심으로 설명하고, cloud-init 방식도 함께 다룬다.

## 셸 스크립트 프로비저닝

### 전체 구조

프로비저닝 스크립트를 기능별로 분리하면 유지보수가 편하다.

```
provision/
├── provision.sh          # 메인 스크립트 (엔트리포인트)
├── install-docker.sh     # Docker CE 설치
├── setup-ssh.sh          # SSH 보안 설정
├── install-tools.sh      # 추가 도구 설치
└── authorized_keys       # SSH 공개키
```

### 메인 프로비저닝 스크립트

```bash
#!/bin/bash
# provision.sh - LXD 컨테이너 프로비저닝 메인 스크립트
set -euo pipefail

CONTAINER_NAME="${1:?Usage: $0 <container-name>}"

echo "=== 프로비저닝 시작: ${CONTAINER_NAME} ==="

# 컨테이너가 실행 중인지 확인
if ! lxc info "${CONTAINER_NAME}" | grep -q "Status: RUNNING"; then
    echo "Error: 컨테이너가 실행 중이 아닙니다."
    exit 1
fi

# 네트워크가 준비될 때까지 대기
echo "[1/5] 네트워크 준비 대기 중..."
for i in $(seq 1 30); do
    if lxc exec "${CONTAINER_NAME}" -- ping -c 1 -W 1 8.8.8.8 &>/dev/null; then
        echo "  네트워크 준비 완료"
        break
    fi
    sleep 1
done

# apt 업데이트
echo "[2/5] 패키지 목록 업데이트 중..."
lxc exec "${CONTAINER_NAME}" -- apt-get update -qq

# Docker CE 설치
echo "[3/5] Docker CE 설치 중..."
lxc file push install-docker.sh "${CONTAINER_NAME}/tmp/install-docker.sh"
lxc exec "${CONTAINER_NAME}" -- bash /tmp/install-docker.sh

# SSH 설정
echo "[4/5] SSH 설정 중..."
lxc file push authorized_keys "${CONTAINER_NAME}/tmp/authorized_keys"
lxc file push setup-ssh.sh "${CONTAINER_NAME}/tmp/setup-ssh.sh"
lxc exec "${CONTAINER_NAME}" -- bash /tmp/setup-ssh.sh

# 추가 도구 설치
echo "[5/5] 추가 도구 설치 중..."
lxc file push install-tools.sh "${CONTAINER_NAME}/tmp/install-tools.sh"
lxc exec "${CONTAINER_NAME}" -- bash /tmp/install-tools.sh

# 정리
lxc exec "${CONTAINER_NAME}" -- rm -rf /tmp/*.sh /tmp/authorized_keys

echo "=== 프로비저닝 완료: ${CONTAINER_NAME} ==="
```

### Docker CE 설치 스크립트

Docker의 공식 설치 절차를 스크립트로 자동화한다.

```bash
#!/bin/bash
# install-docker.sh - Docker CE 설치
set -euo pipefail

# 이미 설치되어 있으면 건너뛰기 (멱등성)
if command -v docker &>/dev/null; then
    echo "Docker가 이미 설치되어 있습니다: $(docker --version)"
    exit 0
fi

echo "Docker CE 설치를 시작합니다..."

# 기존 패키지 제거 (충돌 방지)
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
    apt-get remove -y "$pkg" 2>/dev/null || true
done

# Docker 공식 GPG 키 추가
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Docker apt 리포지토리 추가
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
apt-get update -qq
apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# Docker 서비스 시작 및 자동 실행 등록
systemctl enable docker
systemctl start docker

# 설치 확인
docker --version
docker compose version

echo "Docker CE 설치 완료"
```

### SSH 보안 설정 스크립트

SSH 접속을 공개키 인증으로만 허용하고 패스워드 인증을 비활성화한다.

```bash
#!/bin/bash
# setup-ssh.sh - SSH 보안 설정
set -euo pipefail

# openssh-server 설치 (없을 경우)
if ! command -v sshd &>/dev/null; then
    apt-get install -y openssh-server
fi

# root 사용자 SSH 키 설정
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# 공개키 추가 (기존 키 유지)
if [ -f /tmp/authorized_keys ]; then
    cat /tmp/authorized_keys >> /root/.ssh/authorized_keys
    # 중복 제거
    sort -u /root/.ssh/authorized_keys -o /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
fi

# SSH 설정 변경 - 패스워드 인증 비활성화
SSHD_CONFIG="/etc/ssh/sshd_config"

# 백업
cp "${SSHD_CONFIG}" "${SSHD_CONFIG}.bak"

# 설정 적용
sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' "${SSHD_CONFIG}"
sed -i 's/^#\?PubkeyAuthentication .*/PubkeyAuthentication yes/' "${SSHD_CONFIG}"
sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin prohibit-password/' "${SSHD_CONFIG}"
sed -i 's/^#\?ChallengeResponseAuthentication .*/ChallengeResponseAuthentication no/' "${SSHD_CONFIG}"

# SSH 서비스 재시작
systemctl enable ssh
systemctl restart ssh

echo "SSH 보안 설정 완료"
echo "  - 패스워드 인증: 비활성화"
echo "  - 공개키 인증: 활성화"
echo "  - Root 로그인: 키 인증만 허용"
```

### 추가 도구 설치 스크립트

```bash
#!/bin/bash
# install-tools.sh - 추가 개발 도구 설치
set -euo pipefail

echo "추가 도구 설치를 시작합니다..."

# Git 설치
if ! command -v git &>/dev/null; then
    apt-get install -y git
    echo "Git 설치 완료: $(git --version)"
fi

# Node.js 설치 (NodeSource 리포지토리)
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y nodejs
    echo "Node.js 설치 완료: $(node --version)"
fi

# cloudflared 설치 (Cloudflare Tunnel 클라이언트)
if ! command -v cloudflared &>/dev/null; then
    curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | \
        tee /usr/share/keyrings/cloudflare-main.gpg > /dev/null
    echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] \
        https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | \
        tee /etc/apt/sources.list.d/cloudflared.list > /dev/null
    apt-get update -qq
    apt-get install -y cloudflared
    echo "cloudflared 설치 완료: $(cloudflared --version)"
fi

# 유용한 유틸리티
apt-get install -y \
    htop \
    curl \
    wget \
    jq \
    vim \
    unzip \
    net-tools

# apt 캐시 정리 (이미지 크기 절약)
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "추가 도구 설치 완료"
```

## lxc file push와 lxc exec

LXD는 호스트와 컨테이너 간 파일 전송과 명령 실행을 위한 내장 도구를 제공한다.

### lxc file push (파일 전송)

```bash
# 단일 파일 전송
lxc file push local-file.txt my-container/tmp/local-file.txt

# 디렉토리 전체 전송 (재귀)
lxc file push -r ./config-dir my-container/opt/

# 권한 설정과 함께 전송
lxc file push --mode 0600 secrets.conf my-container/etc/app/secrets.conf

# 컨테이너에서 파일 가져오기
lxc file pull my-container/var/log/syslog ./syslog-backup
```

### lxc exec (명령 실행)

```bash
# 단일 명령 실행
lxc exec my-container -- apt-get update

# 인터랙티브 셸
lxc exec my-container -- bash

# 환경 변수 설정
lxc exec my-container --env MY_VAR=hello -- printenv MY_VAR

# 특정 사용자로 실행
lxc exec my-container -- su - ubuntu -c "whoami"

# 스크립트 실행 (push 후)
lxc file push script.sh my-container/tmp/script.sh
lxc exec my-container -- chmod +x /tmp/script.sh
lxc exec my-container -- /tmp/script.sh
```

## cloud-init을 이용한 프로비저닝

cloud-init은 인스턴스 최초 부팅 시 자동으로 실행되는 초기화 시스템이다. LXD 프로파일에 cloud-init 설정을 포함시킬 수 있다.

### cloud-init 프로파일 예시

```yaml
config:
  cloud-init.user-data: |
    #cloud-config
    package_update: true
    package_upgrade: true

    packages:
      - git
      - curl
      - htop
      - vim
      - openssh-server

    users:
      - name: admin
        sudo: ALL=(ALL) NOPASSWD:ALL
        shell: /bin/bash
        ssh_authorized_keys:
          - ssh-ed25519 AAAA... your-key-comment

    write_files:
      - path: /etc/ssh/sshd_config.d/99-hardening.conf
        content: |
          PasswordAuthentication no
          PubkeyAuthentication yes
          PermitRootLogin prohibit-password

    runcmd:
      - systemctl restart ssh
      - echo "cloud-init 프로비저닝 완료" >> /var/log/provision.log

  cloud-init.network-config: |
    version: 2
    ethernets:
      eth0:
        dhcp4: true
```

### cloud-init 적용

```bash
# cloud-init 프로파일 적용하여 인스턴스 생성
lxc launch ubuntu:24.04 my-container --profile default --profile cloud-init-profile

# cloud-init 진행 상태 확인
lxc exec my-container -- cloud-init status --wait

# cloud-init 로그 확인
lxc exec my-container -- cat /var/log/cloud-init-output.log
```

### cloud-init vs 셸 스크립트

| 항목 | cloud-init | 셸 스크립트 |
|------|-----------|------------|
| 실행 시점 | 최초 부팅 시 자동 | 수동 실행 |
| 디버깅 | 로그 확인 필요 | 실시간 출력 |
| 복잡한 로직 | 제한적 | 자유로움 |
| Docker 설치 | runcmd로 가능하나 복잡 | 명확하고 관리 쉬움 |
| 재실행 | 어려움 (초기화 1회) | 쉬움 |

개인적으로는 기본 패키지와 사용자 설정은 cloud-init으로, Docker 같은 복잡한 설치는 셸 스크립트로 하는 하이브리드 접근을 선호한다.

## 멱등성 스크립트 작성 팁

프로비저닝 스크립트는 **여러 번 실행해도 동일한 결과**를 보장해야 한다.

### 패턴 1: 설치 전 확인

```bash
# 이미 설치되어 있으면 건너뛰기
if command -v docker &>/dev/null; then
    echo "이미 설치됨. 건너뜁니다."
    exit 0
fi
```

### 패턴 2: 파일 존재 확인

```bash
# 설정 파일이 이미 수정되었으면 건너뛰기
if grep -q "PasswordAuthentication no" /etc/ssh/sshd_config; then
    echo "SSH 설정이 이미 적용되어 있습니다."
else
    sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
fi
```

### 패턴 3: apt 리포지토리 중복 방지

```bash
# 리포지토리가 이미 추가되어 있으면 건너뛰기
if [ ! -f /etc/apt/sources.list.d/docker.list ]; then
    # Docker 리포지토리 추가
    echo "deb [arch=...] https://download.docker.com/linux/ubuntu ..." | \
        tee /etc/apt/sources.list.d/docker.list
fi
```

### 패턴 4: 마커 파일 사용

```bash
MARKER="/var/log/.provision-complete"

if [ -f "${MARKER}" ]; then
    echo "프로비저닝이 이미 완료되었습니다."
    exit 0
fi

# ... 프로비저닝 작업 수행 ...

# 완료 마커 생성
date > "${MARKER}"
echo "프로비저닝 완료"
```

## 전체 워크플로우 실행

프로파일과 프로비저닝을 결합한 전체 워크플로우다.

```bash
#!/bin/bash
# create-web-server.sh - 웹서버 인스턴스 생성 + 프로비저닝
set -euo pipefail

CONTAINER_NAME="${1:?Usage: $0 <container-name>}"

echo "=== 웹서버 인스턴스 생성 ==="

# 1. 프로파일 적용하여 인스턴스 생성
lxc launch ubuntu:24.04 "${CONTAINER_NAME}" \
    --profile default \
    --profile web-server

# 2. 인스턴스가 완전히 부팅될 때까지 대기
echo "부팅 대기 중..."
sleep 5

# 3. 프로비저닝 실행
bash provision.sh "${CONTAINER_NAME}"

# 4. 결과 확인
echo ""
echo "=== 인스턴스 정보 ==="
lxc list "${CONTAINER_NAME}" -c ns4tS
echo ""
echo "=== Docker 상태 ==="
lxc exec "${CONTAINER_NAME}" -- docker --version
lxc exec "${CONTAINER_NAME}" -- docker compose version
echo ""
echo "=== SSH 접속 테스트 ==="
CONTAINER_IP=$(lxc list "${CONTAINER_NAME}" -f csv -c 4 | cut -d' ' -f1)
echo "SSH 접속: ssh root@${CONTAINER_IP}"
```

실행:

```bash
chmod +x create-web-server.sh
./create-web-server.sh my-web-server
```

## 마무리

프로비저닝 자동화의 핵심은 **재현 가능성**과 **멱등성**이다. 스크립트로 관리하면 새 인스턴스를 생성할 때마다 동일한 환경이 보장되고, 설정 변경 이력도 Git으로 추적할 수 있다.

셸 스크립트가 단순하면서도 강력한 이유는 Docker CE 설치 같은 복잡한 절차를 그대로 옮겨올 수 있기 때문이다. cloud-init은 기본 설정에, 셸 스크립트는 복잡한 설치에 활용하는 하이브리드 접근이 현실적으로 가장 효과적이다.

다음 글에서는 LXD 네트워킹의 세부 사항과 SSH ProxyJump를 통한 안전한 접속 방법을 다룬다.

## 시리즈 안내

1. LXD 개요: 시스템 컨테이너의 세계
2. LXD 설치 및 초기 설정
3. LXD 프로파일로 인스턴스 생성
4. **LXD 프로비저닝 자동화** (현재 글)
5. LXD 네트워킹 & SSH ProxyJump
6. Cloudflare Tunnel로 LXD 컨테이너 외부 노출
7. LXD에서 Docker Compose 프로덕션 운영
