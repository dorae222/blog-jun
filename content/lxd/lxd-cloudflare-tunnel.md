---
title: "Cloudflare Tunnel로 LXD 컨테이너 외부 노출"
slug: "lxd-cloudflare-tunnel"
category: cloud
tags: ["lxd", "cloudflare", "tunnel", "zero-trust", "networking"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# Cloudflare Tunnel로 LXD 컨테이너 외부 노출

## 들어가며

LXD 컨테이너에서 웹 서비스를 운영할 때 가장 큰 과제는 **외부 접속**이다. 컨테이너는 내부 네트워크(10.0.0.x)에 위치하므로, 외부에서 직접 접속이 불가능하다. 전통적으로는 포트 포워딩과 공유기 설정으로 해결했지만, **Cloudflare Tunnel**을 사용하면 포트를 열지 않고도 안전하게 서비스를 노출할 수 있다.

## Cloudflare Tunnel이란?

Cloudflare Tunnel(구 Argo Tunnel)은 서버에서 Cloudflare 에지 네트워크로 **아웃바운드 연결**을 생성하는 기술이다. 인바운드 포트를 열 필요가 없으므로 보안이 크게 향상된다.

### 동작 원리

```
┌──────────┐         ┌────────────────┐         ┌──────────────────────┐
│ 사용자    │  HTTPS  │ Cloudflare Edge│  Tunnel  │ LXD Container        │
│ 브라우저  │ ──────→ │ (CDN + WAF)    │ ←────── │ cloudflared daemon    │
│          │         │                │ 아웃바운드│ → localhost:8000     │
└──────────┘         └────────────────┘         └──────────────────────┘

① 사용자가 app.example.com으로 접속
② Cloudflare 에지가 요청 수신
③ cloudflared가 Cloudflare 에지로 아웃바운드 터널 유지
④ 터널을 통해 요청이 컨테이너 내부 서비스로 전달
⑤ 응답이 역방향으로 전달
```

### 포트 포워딩 대신 Tunnel을 사용하는 이유

| 항목 | 포트 포워딩 | Cloudflare Tunnel |
|------|-----------|-------------------|
| **인바운드 포트** | 열어야 함 (80, 443 등) | 불필요 (아웃바운드만) |
| **공인 IP** | 필요 | 불필요 |
| **SSL 인증서** | 직접 관리 (Let's Encrypt 등) | Cloudflare 자동 관리 |
| **DDoS 보호** | 없음 | Cloudflare 기본 제공 |
| **WAF** | 별도 구축 필요 | Cloudflare 기본 제공 |
| **CDN** | 별도 구축 필요 | Cloudflare 기본 제공 |
| **설정 복잡도** | 공유기 + 방화벽 + DNS | cloudflared 하나로 통합 |
| **CGNAT 환경** | 불가능 | 가능 |

특히 홈서버나 사내 네트워크처럼 **공인 IP가 없거나 포트 포워딩이 어려운 환경**에서 Tunnel은 유일한 해법이 되기도 한다.

## 사전 준비

### 필요 조건

1. Cloudflare 계정
2. Cloudflare에 등록된 도메인 (DNS 관리가 Cloudflare에 있어야 함)
3. LXD 컨테이너에 cloudflared 설치 (프로비저닝 글 참조)

### cloudflared 설치

컨테이너에 cloudflared가 설치되어 있지 않다면:

```bash
# LXD 컨테이너 내부에서 실행
# Cloudflare GPG 키 추가
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | \
    tee /usr/share/keyrings/cloudflare-main.gpg > /dev/null

# apt 리포지토리 추가
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] \
    https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | \
    tee /etc/apt/sources.list.d/cloudflared.list > /dev/null

# 설치
apt-get update && apt-get install -y cloudflared

# 설치 확인
cloudflared --version
```

## Tunnel 생성 및 인증

### 1단계: Cloudflare 로그인

```bash
cloudflared tunnel login
```

이 명령을 실행하면 브라우저 인증 URL이 출력된다. URL을 열고 도메인을 선택하면 인증서가 다운로드된다.

```
Please open the following URL and log in with your Cloudflare account:
https://dash.cloudflare.com/argotunnel?...

You have successfully logged in.
If you wish to copy your credentials to a server, they have been saved to:
/root/.cloudflared/cert.pem
```

> 헤드리스(GUI 없는) 환경에서는 URL을 복사하여 다른 컴퓨터의 브라우저에서 인증할 수 있다.

### 2단계: Tunnel 생성

```bash
cloudflared tunnel create my-app-tunnel
```

출력:

```
Tunnel credentials written to /root/.cloudflared/your-tunnel-id.json
Created tunnel my-app-tunnel with id your-tunnel-id
```

여기서 생성된 **tunnel ID**와 **credentials 파일**이 이후 설정에 사용된다.

### 3단계: Tunnel 목록 확인

```bash
cloudflared tunnel list

# +--------------------------------------+----------------+-----+----------+
# |                  ID                  |      NAME      | ... | CONN     |
# +--------------------------------------+----------------+-----+----------+
# | your-tunnel-id                       | my-app-tunnel  | ... | 0 conn   |
# +--------------------------------------+----------------+-----+----------+
```

## config.yml 설정

### 기본 구조

Tunnel의 라우팅 규칙을 정의하는 설정 파일이다.

```yaml
# /root/.cloudflared/config.yml

tunnel: your-tunnel-id
credentials-file: /root/.cloudflared/your-tunnel-id.json

ingress:
  # 메인 웹 서비스 (예: React 프론트엔드)
  - hostname: app.example.com
    service: http://localhost:80

  # API 서비스 (예: Django 백엔드)
  - hostname: api.example.com
    service: http://localhost:8000

  # 반드시 마지막에 catch-all 규칙 필요
  - service: http_status:404
```

### ingress 규칙 상세

ingress 규칙은 위에서부터 순서대로 매칭된다. **반드시 마지막에 catch-all 규칙**이 있어야 한다.

```yaml
ingress:
  # 호스트명 매칭
  - hostname: app.example.com
    service: http://localhost:80

  # 경로 매칭
  - hostname: app.example.com
    path: /api/*
    service: http://localhost:8000

  # WebSocket 서비스
  - hostname: ws.example.com
    service: ws://localhost:8080

  # SSH 접속 (브라우저 기반)
  - hostname: ssh.example.com
    service: ssh://localhost:22

  # catch-all (필수)
  - service: http_status:404
```

### 서비스별 추가 옵션

```yaml
ingress:
  - hostname: app.example.com
    service: http://localhost:80
    originRequest:
      # HTTP/2 사용
      http2Origin: true
      # 연결 타임아웃
      connectTimeout: 30s
      # TLS 검증 비활성화 (자체 서명 인증서 사용 시)
      noTLSVerify: true
      # Keep-Alive
      keepAliveTimeout: 90s

  - service: http_status:404
```

### 설정 검증

```bash
# config.yml 문법 검증
cloudflared tunnel ingress validate

# 특정 URL이 어떤 규칙에 매칭되는지 테스트
cloudflared tunnel ingress rule https://app.example.com/
# Using rules from /root/.cloudflared/config.yml
# Matched rule #0: hostname=app.example.com service=http://localhost:80
```

## DNS 레코드 설정

Tunnel을 도메인에 연결하려면 CNAME DNS 레코드가 필요하다.

### 자동 설정 (권장)

```bash
# cloudflared가 자동으로 DNS 레코드를 생성
cloudflared tunnel route dns my-app-tunnel app.example.com

# 여러 도메인 등록
cloudflared tunnel route dns my-app-tunnel api.example.com
```

### 수동 설정

Cloudflare 대시보드에서 직접 설정할 수도 있다.

```
Type:    CNAME
Name:    app
Target:  your-tunnel-id.cfargotunnel.com
Proxied: Yes (주황색 구름)
```

> 주의: 반드시 **Proxied (프록시됨)**이 활성화되어야 한다. DNS Only로 설정하면 Tunnel이 동작하지 않는다.

## Tunnel 실행

### 포그라운드 실행 (테스트용)

```bash
cloudflared tunnel run my-app-tunnel
```

출력:

```
INF Starting tunnel  tunnelID=your-tunnel-id
INF Version 2024.x.x
INF ICMP proxy will use 10.0.0.10 as source for ICMP packets
INF Starting metrics server on 127.0.0.1:38927/metrics
INF Connection established  connIndex=0 event=connected ...
INF Connection established  connIndex=1 event=connected ...
INF Connection established  connIndex=2 event=connected ...
INF Connection established  connIndex=3 event=connected ...
```

4개의 커넥션이 모두 established되면 정상 동작 중이다.

### systemd 서비스 등록 (프로덕션)

Tunnel을 시스템 서비스로 등록하면 부팅 시 자동 시작되고, 장애 시 자동 재시작된다.

```bash
# systemd 서비스 설치 (자동으로 서비스 파일 생성)
cloudflared service install
```

이 명령은 다음을 수행한다:
1. `/etc/systemd/system/cloudflared.service` 파일 생성
2. config.yml과 credentials를 `/etc/cloudflared/`로 복사
3. 서비스 활성화 및 시작

```bash
# 서비스 상태 확인
systemctl status cloudflared

# 서비스 로그 확인
journalctl -u cloudflared --no-pager -n 50

# 서비스 재시작
systemctl restart cloudflared

# 서비스 중지
systemctl stop cloudflared
```

### 수동으로 systemd 서비스 파일 작성

자동 설치가 동작하지 않을 경우 직접 작성할 수 있다.

```ini
# /etc/systemd/system/cloudflared.service
[Unit]
Description=Cloudflare Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
ExecStart=/usr/bin/cloudflared tunnel --config /etc/cloudflared/config.yml run
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

## 상태 확인

### Tunnel 연결 상태

```bash
# cloudflared 명령으로 확인
cloudflared tunnel info my-app-tunnel

# Cloudflare 대시보드에서도 확인 가능
# Zero Trust → Networks → Tunnels
```

### 서비스 접속 테스트

```bash
# 외부에서 접속 테스트
curl -I https://app.example.com
# HTTP/2 200
# cf-ray: ...
# server: cloudflare

# Tunnel 메트릭스 확인 (로컬)
curl http://127.0.0.1:38927/metrics
```

### 헬스체크 설정

config.yml에 헬스체크 엔드포인트를 설정하면 Cloudflare가 서비스 상태를 모니터링한다.

```yaml
ingress:
  - hostname: app.example.com
    service: http://localhost:80
    originRequest:
      # Cloudflare가 원본 서버 상태를 주기적으로 확인
      connectTimeout: 10s

  - service: http_status:404

# Tunnel 수준 헬스체크
warp-routing:
  enabled: false
```

## 다중 서비스 노출

하나의 Tunnel로 여러 서비스를 노출할 수 있다. 이것이 Tunnel의 큰 장점이다.

### 예시: 풀스택 애플리케이션

```yaml
# /root/.cloudflared/config.yml

tunnel: your-tunnel-id
credentials-file: /root/.cloudflared/your-tunnel-id.json

ingress:
  # React 프론트엔드 (Nginx)
  - hostname: app.example.com
    service: http://localhost:80

  # Django API (Gunicorn)
  - hostname: api.example.com
    service: http://localhost:8000

  # 관리자 페이지
  - hostname: admin.example.com
    service: http://localhost:8000
    originRequest:
      httpHostHeader: admin.example.com

  # catch-all
  - service: http_status:404
```

### 같은 도메인에서 경로로 분기

```yaml
ingress:
  # /api 경로는 백엔드로
  - hostname: app.example.com
    path: /api/.*
    service: http://localhost:8000

  # 나머지는 프론트엔드로
  - hostname: app.example.com
    service: http://localhost:80

  - service: http_status:404
```

## 트러블슈팅

### 문제 1: Tunnel이 연결되지 않음

```bash
# 원인 확인
cloudflared tunnel run my-app-tunnel 2>&1 | head -20

# 일반적인 원인:
# - credentials 파일 경로 오류
# - tunnel ID 불일치
# - 네트워크 아웃바운드 차단 (443 포트 필요)

# 해결: 설정 파일 경로 확인
ls -la /root/.cloudflared/
cat /root/.cloudflared/config.yml
```

### 문제 2: 502 Bad Gateway

```bash
# 원인: 로컬 서비스가 실행 중이지 않음
# 해결: 서비스 상태 확인
curl -I http://localhost:80
systemctl status nginx  # 또는 해당 서비스

# 원인: 포트 불일치
# 해결: config.yml의 포트와 실제 서비스 포트 비교
ss -tlnp | grep -E '80|8000'
```

### 문제 3: 도메인 접속 시 DNS 오류

```bash
# DNS 레코드 확인
dig app.example.com CNAME

# 예상 결과:
# app.example.com.  IN  CNAME  your-tunnel-id.cfargotunnel.com.

# DNS 레코드가 없으면 다시 설정
cloudflared tunnel route dns my-app-tunnel app.example.com
```

### 문제 4: WebSocket 연결 실패

```yaml
# config.yml에서 ws:// 프로토콜 사용
ingress:
  - hostname: ws.example.com
    service: ws://localhost:8080
  - service: http_status:404
```

### 로그 확인 방법

```bash
# systemd 로그
journalctl -u cloudflared -f

# 상세 로그 레벨
cloudflared tunnel --loglevel debug run my-app-tunnel

# Cloudflare 대시보드
# Zero Trust → Logs → Gateway
```

## 보안 강화 (Zero Trust)

Cloudflare Tunnel은 Zero Trust 네트워크의 일부다. 추가 보안 정책을 적용할 수 있다.

### Access Policy

Cloudflare Access를 사용하면 Tunnel에 인증 레이어를 추가할 수 있다.

```
Zero Trust → Access → Applications → Add an Application
- Application domain: admin.example.com
- Policy: Email이 @example.com인 사용자만 허용
```

이를 통해 관리자 페이지 등 민감한 서비스에 SSO 인증을 추가할 수 있다.

## 마무리

Cloudflare Tunnel은 LXD 컨테이너의 서비스를 외부에 노출하는 가장 안전하고 편리한 방법이다. 포트 포워딩 없이 아웃바운드 연결만으로 동작하므로 보안이 강화되고, SSL 인증서, CDN, DDoS 보호가 자동으로 제공된다.

하나의 Tunnel로 여러 서비스를 hostname이나 path 기반으로 라우팅할 수 있어, 풀스택 애플리케이션을 운영하기에도 적합하다.

다음 글에서는 LXD 컨테이너 안에서 Docker Compose로 프로덕션 스택을 운영하는 방법을 다룬다.

## 시리즈 안내

1. LXD 개요: 시스템 컨테이너의 세계
2. LXD 설치 및 초기 설정
3. LXD 프로파일로 인스턴스 생성
4. LXD 프로비저닝 자동화
5. LXD 네트워킹 & SSH ProxyJump
6. **Cloudflare Tunnel로 LXD 컨테이너 외부 노출** (현재 글)
7. LXD에서 Docker Compose 프로덕션 운영
