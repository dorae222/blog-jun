# OpenClaw 실전: 자체 호스팅 AI 에이전트 환경

## 들어가며

:::info
이 글은 **OpenClaw Guide** 시리즈의 마지막 글이다. 시리즈 전체 목차:
1. [[openclaw-guide-01-setup|메시징 기반 AI 에이전트]]
2. [[openclaw-guide-02-core|핵심 기능: 아키텍처와 도구 시스템]]
3. [[openclaw-guide-03-advanced|고급 활용: 커스터마이징과 확장]]
4. **실전: 자체 호스팅 AI 에이전트 환경** (현재 글)
:::

이전 글들에서 OpenClaw의 설치, 아키텍처, 고급 커스터마이징을 다루었다. 이 마지막 글에서는 **프로덕션 환경에서 OpenClaw를 안정적으로 운영**하는 방법을 다룬다. Docker Compose 배포, SSL/리버스 프록시 설정, 팀 통합, 모니터링, 백업, 비용 최적화, 실전 시나리오까지 자체 호스팅 AI 에이전트 환경의 전 과정을 안내한다.

---

## Docker Compose로 배포

### 프로덕션용 Docker Compose

개발 환경과 프로덕션 환경의 Docker Compose 설정은 다르다. 프로덕션에 적합한 설정을 구성한다:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  openclaw:
    image: openclaw/openclaw:latest
    container_name: openclaw-gateway
    restart: unless-stopped
    user: "1000:1000"
    env_file:
      - .env.prod
    volumes:
      - openclaw-config:/home/node/.openclaw
      - openclaw-workspace:/home/node/.openclaw/workspace
      - openclaw-data:/home/node/.openclaw/data
    ports:
      - "127.0.0.1:3000:3000"  # localhost만 노출 (리버스 프록시 경유)
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"

volumes:
  openclaw-config:
    driver: local
  openclaw-workspace:
    driver: local
  openclaw-data:
    driver: local
```

### .env.prod 파일

프로덕션 환경변수를 별도 파일로 관리한다:

```bash
# .env.prod

# LLM Providers
ANTHROPIC_API_KEY=sk-ant-prod-key-here
OPENAI_API_KEY=sk-prod-key-here

# Messaging Channels
TELEGRAM_BOT_TOKEN=prod-telegram-token
DISCORD_BOT_TOKEN=prod-discord-token
SLACK_BOT_TOKEN=xoxb-prod-slack-token

# Gateway Settings
OPENCLAW_PORT=3000
OPENCLAW_LOG_LEVEL=warn
NODE_ENV=production

# Security
OPENCLAW_SECRET_KEY=your-random-secret-key-here
```

### 배포 실행

```bash
# 이미지 최신 버전 풀
docker compose -f docker-compose.prod.yml pull

# 백그라운드로 실행
docker compose -f docker-compose.prod.yml up -d

# 상태 확인
docker compose -f docker-compose.prod.yml ps

# 로그 확인
docker compose -f docker-compose.prod.yml logs -f openclaw
```

```output
NAME                STATUS          PORTS
openclaw-gateway    Up 2 minutes    127.0.0.1:3000->3000/tcp
```

### 업데이트 절차

```bash
# 1. 백업 (필수!)
./backup.sh

# 2. 최신 이미지 풀
docker compose -f docker-compose.prod.yml pull

# 3. 컨테이너 교체 (다운타임 최소화)
docker compose -f docker-compose.prod.yml up -d --force-recreate

# 4. 상태 확인
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=50 openclaw
```

:::warning
업데이트 전에 반드시 백업을 수행해야 한다. Docker 볼륨의 `openclaw-config`와 `openclaw-data`에 설정, 대화 기록, 메모리 인덱스가 모두 저장되어 있다.
:::

---

## 프로덕션 설정

### SSL 인증서와 도메인

프로덕션 환경에서는 HTTPS가 필수다. Let's Encrypt를 사용한 자동 SSL 설정:

```yaml
# docker-compose.prod.yml에 추가
services:
  nginx:
    image: nginx:alpine
    container_name: openclaw-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - certbot-webroot:/var/www/certbot:ro
    depends_on:
      - openclaw

  certbot:
    image: certbot/certbot
    container_name: openclaw-certbot
    volumes:
      - ./nginx/ssl:/etc/letsencrypt
      - certbot-webroot:/var/www/certbot

volumes:
  certbot-webroot:
    driver: local
```

### Nginx 리버스 프록시

```
# nginx/conf.d/openclaw.conf

upstream openclaw_backend {
    server openclaw:3000;
}

server {
    listen 80;
    server_name agent.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name agent.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/live/agent.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/agent.yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # WebSocket support (메시징 채널용)
    location /ws/ {
        proxy_pass http://openclaw_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Webhook endpoints (WhatsApp, Slack 등)
    location /webhook/ {
        proxy_pass http://openclaw_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://openclaw_backend;
    }

    # Control UI (관리자만 접근)
    location / {
        proxy_pass http://openclaw_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # IP 제한 (관리자만)
        allow 10.0.0.0/8;
        allow 192.168.0.0/16;
        deny all;
    }
}
```

### SSL 인증서 발급

```bash
# 초기 인증서 발급
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d agent.yourdomain.com \
  --agree-tos \
  --email admin@yourdomain.com

# 자동 갱신 (crontab에 추가)
# 0 3 * * 0 docker compose -f docker-compose.prod.yml run --rm certbot renew && docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Cloudflare Tunnel 대안

SSL 인증서 관리 없이 더 간단하게 외부 접근을 설정하려면 Cloudflare Tunnel을 사용할 수 있다:

```yaml
# docker-compose.prod.yml에 추가
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: openclaw-tunnel
    restart: unless-stopped
    command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    depends_on:
      - openclaw
```

```bash
# Cloudflare Tunnel 생성
cloudflared tunnel create openclaw-agent

# 도메인 라우팅 설정
cloudflared tunnel route dns openclaw-agent agent.yourdomain.com
```

:::tip
Cloudflare Tunnel을 사용하면 서버의 포트를 외부에 노출할 필요가 없다. SSL도 자동 처리되므로 인증서 관리가 불필요하다. 소규모 배포에 특히 유리하다.
:::

---

## 팀 메시징 채널에 AI 에이전트 통합

### Slack 팀 통합

팀 Slack 워크스페이스에 OpenClaw 에이전트를 통합하는 시나리오:

**1단계: Slack 앱 설정**

Slack API에서 새 앱을 만들고 필요한 스코프를 설정한다:

```json
{
  "scopes": {
    "bot": [
      "channels:history",
      "channels:read",
      "chat:write",
      "files:read",
      "groups:history",
      "groups:read",
      "im:history",
      "im:read",
      "im:write",
      "reactions:read",
      "reactions:write",
      "users:read"
    ]
  }
}
```

**2단계: 채널별 에이전트 배치**

```json
{
  "agents": {
    "list": [
      {
        "id": "slack-general",
        "name": "팀 어시스턴트",
        "model": "anthropic/claude-sonnet-4.5",
        "workspace": "~/.openclaw/agents/slack-general/workspace"
      },
      {
        "id": "slack-devops",
        "name": "DevOps 봇",
        "model": "openai/gpt-4.1",
        "workspace": "~/.openclaw/agents/slack-devops/workspace"
      }
    ],
    "bindings": [
      {
        "agentId": "slack-general",
        "channel": "slack",
        "channelId": "C0GENERAL01"
      },
      {
        "agentId": "slack-devops",
        "channel": "slack",
        "channelId": "C0DEVOPS01"
      }
    ]
  }
}
```

**3단계: 팀 지식 베이스 구성**

팀 에이전트의 워크스페이스에 팀 지식을 추가한다:

```bash
# 팀 문서를 워크스페이스에 복사
cp -r /path/to/team-docs/* ~/.openclaw/agents/slack-general/workspace/docs/

# 인덱싱 실행
openclaw memory reindex --agent slack-general
```

팀 에이전트의 `AGENTS.md`:

```markdown
# Team Assistant Rules

## 응답 규칙
- 팀 내부 정보만 참조한다
- 외부 검색은 팀원이 명시적으로 요청한 경우만 수행한다
- 코드 리뷰 요청은 #dev-review 채널로 안내한다

## 사용 가능한 도구
- Notion 검색 (팀 위키)
- Google Calendar (팀 일정)
- GitHub (레포 조회, PR 상태)

## 제한
- 파일 시스템 접근 불가
- 셸 명령 실행 불가
- 외부 이메일 전송 불가
```

### Discord 커뮤니티 통합

Discord 서버에 OpenClaw를 통합하여 커뮤니티 지원 봇으로 활용하는 구성:

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "botToken": "$DISCORD_BOT_TOKEN",
      "allowGuilds": ["your-server-id"],
      "channelMapping": {
        "general-help": {
          "channelId": "CH_GENERAL_HELP",
          "agentId": "community-support",
          "responseMode": "thread"
        },
        "tech-support": {
          "channelId": "CH_TECH_SUPPORT",
          "agentId": "tech-support",
          "responseMode": "thread"
        }
      }
    }
  }
}
```

`responseMode: "thread"`로 설정하면 봇이 답변을 스레드로 생성하여 채널이 깔끔하게 유지된다.

---

## 모니터링과 로깅

### 로그 시스템

OpenClaw Gateway는 JSON Lines 형식으로 구조화된 로그를 기록한다:

```bash
# 기본 로그 위치
/tmp/openclaw/openclaw-YYYY-MM-DD.log

# Docker 환경에서 로그 확인
docker compose -f docker-compose.prod.yml logs -f openclaw

# 최근 에러만 필터링
docker compose -f docker-compose.prod.yml logs openclaw | grep '"level":"error"'
```

로그 파일은 자동으로 로테이션된다:
- 파일 크기 제한: 100MB
- 보관 개수: 최대 10개

### 로그 설정

```json
{
  "logging": {
    "level": "warn",
    "format": "json",
    "outputs": [
      {
        "type": "file",
        "path": "/tmp/openclaw/openclaw.log",
        "maxSize": "100MB",
        "maxFiles": 10
      },
      {
        "type": "console",
        "level": "error"
      }
    ],
    "diagnostics": {
      "enabled": true,
      "modelRuns": true,
      "messageFlow": true
    }
  }
}
```

### 헬스 체크

OpenClaw는 `/health` 엔드포인트를 제공한다:

```bash
curl http://localhost:3000/health
```

```json
{
  "status": "healthy",
  "uptime": 86400,
  "version": "1.x.x",
  "channels": {
    "telegram": "connected",
    "discord": "connected",
    "slack": "connected"
  },
  "agents": {
    "active": 3,
    "sessions": 12
  },
  "memory": {
    "rss": "256MB",
    "heap": "128MB"
  }
}
```

### Prometheus 메트릭

OpenClaw는 Prometheus 메트릭을 내보낼 수 있다:

```json
{
  "monitoring": {
    "prometheus": {
      "enabled": true,
      "port": 9090,
      "path": "/metrics"
    }
  }
}
```

주요 메트릭:

| 메트릭 | 타입 | 설명 |
|--------|------|------|
| `openclaw_messages_total` | counter | 처리된 메시지 총 수 |
| `openclaw_llm_requests_total` | counter | LLM API 호출 수 |
| `openclaw_llm_tokens_total` | counter | 사용된 토큰 수 (입력/출력) |
| `openclaw_llm_cost_usd` | counter | 누적 API 비용 (USD) |
| `openclaw_tool_calls_total` | counter | 도구 호출 수 |
| `openclaw_response_latency_seconds` | histogram | 응답 지연 시간 |
| `openclaw_active_sessions` | gauge | 활성 세션 수 |
| `openclaw_queue_depth` | gauge | 대기 중인 메시지 수 |

### 대시보드 구성

커뮤니티에서 제공하는 모니터링 대시보드를 활용할 수 있다:

```bash
# openclaw-dashboard 설치
git clone https://github.com/tugcantopaloglu/openclaw-dashboard.git
cd openclaw-dashboard

# Docker로 실행
docker compose up -d
```

대시보드는 실시간 메시지 피드, 비용 추적, 메모리 브라우저, 에이전트 상태를 제공한다.

### 알림 설정

특정 조건에서 알림을 보내도록 설정한다:

```json
{
  "monitoring": {
    "alerts": {
      "costThreshold": {
        "daily": 10.0,
        "monthly": 200.0,
        "notify": "telegram"
      },
      "errorRate": {
        "threshold": 0.05,
        "window": "5m",
        "notify": "slack"
      },
      "queueDepth": {
        "threshold": 50,
        "notify": "discord"
      }
    }
  }
}
```

---

## 백업과 데이터 관리

### 백업 대상

OpenClaw의 모든 상태는 `~/.openclaw/`에 저장된다:

| 디렉토리/파일 | 내용 | 중요도 |
|-------------|------|--------|
| `openclaw.json` | 에이전트/채널/모델 설정 | 필수 |
| `.env` | API 키, 토큰 | 필수 (암호화) |
| `data/openclaw.db` | 대화 기록, 벡터 인덱스 | 높음 |
| `workspace/` | SOUL.md, AGENTS.md 등 | 높음 |
| `agents/` | 멀티 에이전트 워크스페이스 | 높음 |
| `sessions/` | 활성 세션 상태 | 중간 |
| `skills/` | 설치된 Skills | 낮음 (재설치 가능) |

### 백업 스크립트

```bash
#!/bin/bash
# backup.sh - OpenClaw 백업 스크립트

BACKUP_DIR="/backup/openclaw"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/openclaw_backup_${TIMESTAMP}.tar.gz.enc"

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

# Docker 볼륨 데이터 백업 (암호화)
docker compose -f docker-compose.prod.yml exec openclaw \
  tar czf - /home/node/.openclaw | \
  openssl enc -aes-256-cbc -salt -pbkdf2 \
    -pass file:/backup/openclaw/.backup_password \
    -out "$BACKUP_FILE"

# 30일 이상 된 백업 정리
find "$BACKUP_DIR" -name "openclaw_backup_*.tar.gz.enc" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
echo "Size: $(du -h "$BACKUP_FILE" | cut -f1)"
```

### 자동 백업 (crontab)

```bash
# crontab -e
# 매일 새벽 3시 백업
0 3 * * * /opt/openclaw/backup.sh >> /var/log/openclaw-backup.log 2>&1

# 매주 일요일 SSL 인증서 갱신
0 4 * * 0 docker compose -f /opt/openclaw/docker-compose.prod.yml run --rm certbot renew
```

:::warning
백업 파일에는 API 키와 OAuth 토큰이 포함되므로 **반드시 암호화**해야 한다. 암호화되지 않은 백업을 클라우드 스토리지에 업로드하면 안 된다.
:::

### 복원 절차

```bash
# 1. 백업 파일 복호화
openssl enc -aes-256-cbc -d -salt -pbkdf2 \
  -pass file:/backup/openclaw/.backup_password \
  -in openclaw_backup_20260328_030000.tar.gz.enc | \
  tar xzf - -C /tmp/openclaw-restore/

# 2. 기존 데이터 백업 (안전장치)
docker compose -f docker-compose.prod.yml stop
docker volume create openclaw-config-old
# ... (기존 볼륨 이름 변경)

# 3. 복원 데이터로 교체
docker compose -f docker-compose.prod.yml up -d

# 4. 상태 확인
docker compose -f docker-compose.prod.yml exec openclaw openclaw doctor
```

### 데이터 정리

시간이 지나면 대화 기록과 세션 데이터가 누적된다. 주기적으로 정리한다:

```bash
# 90일 이상 된 세션 정리
openclaw sessions prune --older-than 90d

# 메모리 인덱스 최적화
openclaw memory optimize

# 데이터베이스 VACUUM
openclaw db vacuum
```

---

## 비용 최적화

### 비용 구조

OpenClaw 운영 비용은 크게 세 가지로 나뉜다:

| 항목 | 예상 비용 | 최적화 방법 |
|------|----------|------------|
| 서버 (VPS) | $5-15/월 | 가벼운 VPS, ARM 인스턴스 |
| LLM API | $10-200+/월 | 모델 라우팅, 로컬 LLM |
| 메시징 API | 대부분 무료 | Telegram/Discord 무료 |

### 모델 라우팅으로 비용 절감

가장 효과적인 비용 최적화는 **작업 유형별 모델 분리**다:

```json
{
  "models": {
    "routing": {
      "reasoning": {
        "model": "anthropic/claude-sonnet-4.5",
        "description": "복잡한 분석, 코드 생성, 다단계 계획"
      },
      "light": {
        "model": "anthropic/claude-haiku-4.5",
        "description": "단순 Q&A, 포맷팅, 요약"
      },
      "routine": {
        "model": "ollama/llama3.3",
        "description": "스케줄링, 리마인더, 단순 조회"
      }
    }
  }
}
```

비용 비교 (백만 토큰당):

| 모델 | 입력 비용 | 출력 비용 | 적합한 작업 |
|------|----------|----------|------------|
| Claude Opus 4.6 | $15 | $75 | 복잡한 추론 (제한적 사용) |
| Claude Sonnet 4.5 | $3 | $15 | 일반 작업 (기본) |
| Claude Haiku 4.5 | $0.25 | $1.25 | 단순 작업 (대부분) |
| GPT-4.1-mini | $0.40 | $1.60 | 단순 작업 대안 |
| GPT-4.1-nano | $0.10 | $0.40 | 최소 비용 작업 |
| Ollama (로컬) | $0 | $0 | 루틴 작업 (전기료만) |

### 로컬 LLM으로 전환

API 비용을 완전히 제거하려면 로컬 LLM을 사용한다:

```bash
# Ollama 설치 및 모델 다운로드
ollama pull qwen3.5:14b    # 14B 파라미터 (16GB RAM 필요)
ollama pull llama3.3:8b    # 8B 파라미터 (8GB RAM 충분)
```

하드웨어별 적합한 모델:

| 하드웨어 | RAM | 추천 모델 | 성능 |
|----------|-----|----------|------|
| Mac mini M4 | 16GB | 7B-14B 모델 | ~30 tokens/sec |
| Mac mini M4 Pro | 48GB | 70B 모델 | ~15 tokens/sec |
| Linux + RTX 4090 | 24GB VRAM | 70B 모델 (양자화) | ~40 tokens/sec |
| Linux + 32GB RAM | 32GB | 7B-13B 모델 | ~10 tokens/sec |

:::tip
**하이브리드 전략이 가장 현실적**이다. Heartbeat, 단순 응답, 리마인더 같은 루틴 작업은 로컬 모델로 처리하고, 복잡한 분석이나 긴 대화는 클라우드 API를 사용한다. 이렇게 하면 월 $15-25 수준으로 운영할 수 있다.
:::

### Heartbeat 비용 최적화

Heartbeat는 30분마다 실행되므로 비용이 누적될 수 있다. 최적화 설정:

```json
{
  "heartbeat": {
    "interval": 1800,
    "isolatedSession": true,
    "lightContext": true,
    "model": "ollama/llama3.3"
  }
}
```

- `isolatedSession: true`: 전체 대화 히스토리(~100K 토큰) 대신 2-5K 토큰만 사용
- `lightContext: true`: HEARTBEAT.md만 컨텍스트에 포함
- 로컬 모델 사용: API 비용 0

### 비용 추적

```bash
# 일일 비용 확인
openclaw costs today

# 월별 비용 확인
openclaw costs month

# 에이전트별 비용 확인
openclaw costs --by-agent
```

```output
Cost Report (2026-03-28)

Today:
  Total: $1.23
  By model:
    claude-sonnet-4.5:  $0.85 (42 requests, 125K tokens)
    claude-haiku-4.5:   $0.32 (128 requests, 380K tokens)
    ollama/llama3.3:    $0.00 (256 requests, local)
    gpt-4.1-mini:       $0.06 (15 requests, 45K tokens)

Month to date: $28.50
  Budget remaining: $71.50 / $100.00
```

---

## 실전 시나리오

### 시나리오 1: 고객 지원 봇

Telegram이나 WhatsApp으로 고객 문의를 자동 처리하는 봇:

```json
{
  "agents": {
    "list": [
      {
        "id": "customer-support",
        "name": "고객지원 봇",
        "model": "anthropic/claude-haiku-4.5",
        "workspace": "~/.openclaw/agents/support/workspace",
        "mcp": {
          "servers": [
            { "name": "notion", "command": "npx", "args": ["-y", "@notionhq/mcp"] }
          ]
        },
        "tools": {
          "allow": ["notion.search_pages", "notion.read_page"],
          "deny": ["shell.*", "filesystem.*"]
        }
      }
    ]
  }
}
```

`AGENTS.md`:

```markdown
# Customer Support Agent

## 역할
당신은 [회사명]의 고객지원 봇입니다.

## 응답 규칙
1. 항상 친절하고 공손하게 응답합니다
2. FAQ 문서를 먼저 검색하여 정확한 정보를 제공합니다
3. FAQ에 없는 질문은 "담당자에게 전달하겠습니다"로 응답합니다
4. 환불/취소 관련 요청은 직접 처리하지 않고 안내만 합니다
5. 개인정보를 요청하거나 저장하지 않습니다

## 에스컬레이션
- "담당자 연결" 요청 시: 운영팀 채널로 알림 전달
- 3회 이상 같은 질문 반복 시: 자동 에스컬레이션
```

### 시나리오 2: 팀 어시스턴트

Slack에서 팀의 일상 업무를 지원하는 어시스턴트:

`HEARTBEAT.md`:

```markdown
# Team Assistant Heartbeat

- [ ] #general 채널에서 아직 답변이 없는 질문이 있는지 확인
- [ ] Google Calendar에서 다음 1시간 내 미팅이 있으면 #general에 리마인더
- [ ] GitHub에서 리뷰 대기 중인 PR이 24시간 이상이면 담당자에게 DM
```

Cron 작업 설정:

```bash
# 매일 오전 9시 일일 브리핑
openclaw cron add "daily-briefing" \
  --schedule "0 9 * * 1-5" \
  --agent "team-assistant" \
  --channel "slack:C0GENERAL01" \
  --prompt "오늘의 팀 브리핑을 생성해줘: 오늘 일정, 대기 중인 PR, 중요 알림"

# 매주 금요일 오후 5시 주간 리포트
openclaw cron add "weekly-report" \
  --schedule "0 17 * * 5" \
  --agent "team-assistant" \
  --channel "slack:C0GENERAL01" \
  --prompt "이번 주 팀 활동 요약 리포트를 생성해줘"
```

### 시나리오 3: 지식 관리 에이전트

Obsidian 노트나 Notion 위키를 기반으로 지식을 관리하고 검색하는 에이전트:

```json
{
  "agents": {
    "list": [
      {
        "id": "knowledge",
        "name": "지식 관리자",
        "model": "anthropic/claude-sonnet-4.5",
        "memory": {
          "enabled": true,
          "sources": [
            {
              "type": "directory",
              "path": "/path/to/obsidian-vault/**/*.md",
              "autoSync": true
            }
          ],
          "embeddingModel": "openai/text-embedding-3-small",
          "searchWeights": {
            "vector": 0.6,
            "keyword": 0.4
          }
        }
      }
    ]
  }
}
```

사용 예시:

```
사용자: Kubernetes의 Pod 스케줄링에 대해 정리한 노트가 있었는데, 핵심 내용이 뭐였지?
봇: 작년 11월에 작성한 "K8s Scheduling Deep Dive" 노트를 찾았습니다.

    핵심 내용:
    1. 스케줄러의 3단계: 필터링 → 스코어링 → 바인딩
    2. nodeSelector vs nodeAffinity 차이점
    3. Taint/Toleration으로 특수 노드 관리
    4. PriorityClass로 Pod 우선순위 제어

    원본 노트: [[k8s-scheduling-deep-dive]]
    관련 노트: [[k8s-resource-management]], [[k8s-autoscaling]]
```

---

## 다른 도구와의 비교

### OpenClaw의 위치

AI 에이전트 생태계에서 OpenClaw가 어디에 위치하는지 정리한다:

| 도구 | 인터페이스 | 주요 용도 | 모델 | 비용 |
|------|-----------|----------|------|------|
| **OpenClaw** | 메시징 앱 | 범용 업무 자동화 | 멀티 프로바이더 | 무료 (API만) |
| Claude Code | 터미널 | 코딩 에이전트 | Anthropic 전용 | $20-200/월 |
| Gemini CLI | 터미널 | 코딩 에이전트 | Google 전용 | 무료-유료 |
| OpenCode | 터미널 | 코딩 에이전트 | 멀티 프로바이더 | 무료 (API만) |
| Codex CLI | 터미널 | 코딩 에이전트 | OpenAI 전용 | API 비용 |

### Claude Code와의 핵심 차이

가장 자주 비교되는 Claude Code와의 차이를 상세히 정리한다:

| 비교 항목 | OpenClaw | Claude Code |
|-----------|----------|-------------|
| **설계 목적** | 메시징 기반 범용 비서 | 터미널 기반 코딩 에이전트 |
| **인터페이스** | WhatsApp, Telegram, Discord 등 | 터미널 CLI, VS Code, JetBrains |
| **데이터 주권** | 완전한 local-first (자체 서버) | Anthropic 서버 경유 |
| **모델 유연성** | Claude, GPT, Gemini, Ollama 등 | Anthropic Claude만 |
| **도구 생태계** | 5,400+ Skills, 1,000+ MCP 서버 | 코드베이스 중심 도구 |
| **작동 시간** | 24시간 데몬 (항상 대기) | 사용자 세션 동안만 |
| **사용 사례** | 이메일, 캘린더, 파일, 스마트홈 | 코드 작성, 리팩토링, 디버깅 |
| **팀 지원** | 멀티 에이전트, 채널별 분리 | 개인 사용 중심 |
| **비용** | 소프트웨어 무료 + API 비용 | 구독 $20-200/월 |

:::info
**OpenClaw와 코딩 에이전트는 대체재가 아니라 보완재**다. 프로덕션 환경에서 최대 가치를 추출하는 팀은 두 도구를 동시에 사용한다 - OpenClaw는 메시징 기반 업무 자동화에, Claude Code는 개발 워크플로우에 각각 특화된다.
:::

### 언제 OpenClaw를 선택하는가

OpenClaw가 적합한 경우:

- 메시징 앱에서 AI를 사용하고 싶을 때
- 24시간 항상 대기하는 AI 비서가 필요할 때
- 이메일, 캘린더, 파일 관리 등 범용 업무를 자동화할 때
- 팀 채널에 AI를 통합하고 싶을 때
- 데이터 주권이 중요할 때 (local-first)
- 특정 LLM에 종속되고 싶지 않을 때
- 예산을 완전히 통제하고 싶을 때

OpenClaw가 부적합한 경우:

- 코딩 전용 에이전트가 필요할 때 (Claude Code가 더 적합)
- 대규모 코드베이스를 이해하는 AI가 필요할 때
- 서버 관리에 익숙하지 않을 때 (자체 호스팅 필요)

---

## 운영 체크리스트

### 일일

- [ ] 헬스 체크 엔드포인트 정상 확인
- [ ] 일일 API 비용 확인
- [ ] 에러 로그 확인

### 주간

- [ ] 백업 무결성 확인
- [ ] 디스크 사용량 확인
- [ ] 오래된 세션 정리
- [ ] 채널 연결 상태 확인

### 월간

- [ ] OpenClaw 버전 업데이트 확인
- [ ] SSL 인증서 만료일 확인
- [ ] 월간 비용 리뷰 및 모델 라우팅 최적화
- [ ] 보안 패치 적용
- [ ] 메모리 인덱스 최적화 (`openclaw memory optimize`)
- [ ] 백업 복원 테스트 (분기 1회)

### 자동화 가능 항목

```bash
#!/bin/bash
# daily-maintenance.sh

# 헬스 체크
HEALTH=$(curl -sf http://localhost:3000/health)
if [ $? -ne 0 ]; then
  echo "ALERT: OpenClaw health check failed" | \
    curl -X POST "https://hooks.slack.com/services/XXX" \
    -H 'Content-Type: application/json' \
    -d '{"text":"OpenClaw health check failed!"}'
fi

# 비용 확인
DAILY_COST=$(echo $HEALTH | jq -r '.costs.today')
if (( $(echo "$DAILY_COST > 10.0" | bc -l) )); then
  echo "ALERT: Daily cost exceeded $10: $DAILY_COST"
fi

# 디스크 사용량 확인
DISK_USAGE=$(df -h /var/lib/docker | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 80 ]; then
  echo "ALERT: Disk usage at ${DISK_USAGE}%"
  # 오래된 로그 정리
  docker compose -f docker-compose.prod.yml exec openclaw \
    find /tmp/openclaw -name "*.log" -mtime +7 -delete
fi
```

```bash
# crontab에 추가
0 8 * * * /opt/openclaw/daily-maintenance.sh >> /var/log/openclaw-maintenance.log 2>&1
```

---

## 정리

이 글에서 다룬 프로덕션 운영 내용을 정리한다:

- **Docker Compose 배포**: 프로덕션용 설정, 리소스 제한, 헬스 체크, 자동 재시작
- **SSL/리버스 프록시**: Nginx + Let's Encrypt 또는 Cloudflare Tunnel로 안전한 외부 접근
- **팀 통합**: Slack/Discord 채널별 에이전트 배치, 팀 지식 베이스 연동
- **모니터링**: JSON Lines 로그, Prometheus 메트릭, 대시보드, 알림 설정
- **백업**: 암호화된 자동 백업, 복원 절차, 데이터 정리
- **비용 최적화**: 모델 라우팅(Opus/Sonnet/Haiku/로컬 분리)으로 80%+ 절감, 하이브리드 전략
- **실전 시나리오**: 고객 지원 봇, 팀 어시스턴트, 지식 관리 에이전트
- **도구 비교**: OpenClaw는 메시징 기반 범용 에이전트, Claude Code 등 코딩 도구와 보완적

이것으로 **OpenClaw Guide** 시리즈를 마친다. OpenClaw는 메시징 기반의 local-first AI 에이전트로, 코딩 전용 도구와는 다른 영역에서 강력한 가치를 제공한다.