# OpenClaw 시작하기: 메시징 기반 AI 에이전트

## 들어가며

:::info
이 글은 **OpenClaw Guide** 시리즈의 첫 번째 글이다. 시리즈 전체 목차:
1. **메시징 기반 AI 에이전트** (현재 글)
2. [[openclaw-guide-02-core|핵심 기능: 아키텍처와 도구 시스템]]
3. [[openclaw-guide-03-advanced|고급 활용: 커스터마이징과 확장]]
4. [[openclaw-guide-04-workflow|실전: 자체 호스팅 AI 에이전트 환경]]
:::

OpenClaw는 메시징 기반의 범용 AI 에이전트 플랫폼이다. 터미널이 아닌 **WhatsApp, Telegram, Discord, Slack** 같은 일상적인 메시징 앱에서 AI와 대화하며, 파일 관리, 이메일 정리, 캘린더 관리, 웹 검색까지 자동화할 수 있다. 2025년 11월 첫 공개 이후 폭발적으로 성장해 GitHub에서 **337K+ 스타**를 기록하며 역대 가장 빠르게 성장한 오픈소스 프로젝트 중 하나가 되었다.

이 글에서는 OpenClaw의 개념을 이해하고, 설치부터 메시징 플랫폼 연동, 첫 대화까지의 전 과정을 단계별로 안내한다.

---

## OpenClaw란 무엇인가

### 메시징 기반 범용 AI 에이전트

OpenClaw는 **자체 호스팅(self-hosted) AI 개인 비서**다. 핵심 아이디어는 단순하다 - LLM(대규모 언어 모델)을 두뇌로 삼고, 메시징 앱을 인터페이스로 사용하며, 다양한 도구(Skills)를 통해 실제 작업을 수행하는 것이다.

| 특성 | 설명 |
|------|------|
| 라이선스 | MIT (완전 무료, 오픈소스) |
| 언어 | TypeScript + Node.js |
| 저장소 | SQLite + sqlite-vec (벡터 검색) |
| LLM 지원 | OpenAI, Anthropic, Google, Ollama 등 |
| 메시징 | 25+ 플랫폼 지원 |
| GitHub | 337K+ 스타 (2026년 3월 기준) |

:::tip
OpenClaw는 Claude Code나 GitHub Copilot 같은 **코딩 전용 도구가 아니다**. 메시징 앱을 통해 일상적인 업무 전반을 자동화하는 **범용 AI 에이전트**다. 코딩 에이전트와의 차이는 시리즈 마지막 글에서 상세히 비교한다.
:::

### 지원 플랫폼

OpenClaw가 연동 가능한 메시징 플랫폼은 다음과 같다:

| 카테고리 | 플랫폼 |
|----------|--------|
| 주요 메신저 | WhatsApp, Telegram, Signal, iMessage |
| 업무용 | Slack, Microsoft Teams, Google Chat, Mattermost |
| 커뮤니티 | Discord, IRC, Matrix, Twitch |
| 아시아권 | LINE, WeChat, Zalo, Feishu |
| 기타 | Nostr, Synology Chat, Nextcloud Talk, BlueBubbles, Tlon |

각 플랫폼은 **채널(Channel)**이라는 개념으로 관리되며, 하나의 OpenClaw 인스턴스에서 여러 채널을 동시에 운영할 수 있다.

### 코딩 에이전트와의 차이

OpenClaw를 처음 접하면 Claude Code 같은 코딩 에이전트와 혼동할 수 있다. 핵심 차이를 정리한다:

| 비교 항목 | OpenClaw | Claude Code |
|-----------|----------|-------------|
| 주요 인터페이스 | 메시징 앱 (WhatsApp, Telegram 등) | 터미널 CLI |
| 주요 용도 | 범용 업무 자동화 | 코드 작성/리팩토링 |
| 작동 방식 | Gateway 서버 + 메시징 브릿지 | 프로세스 기반 CLI |
| LLM | 다중 프로바이더 지원 | Anthropic Claude 전용 |
| 데이터 저장 | SQLite (local-first) | 세션 기반 (임시) |
| 비용 | 소프트웨어 무료, API 비용만 | 구독 또는 API 비용 |

---

## 사전 요구사항

### 시스템 요구사항

OpenClaw를 설치하려면 다음이 필요하다:

- **Node.js 20+** (npm 포함)
- **운영체제**: macOS, Linux, Windows (WSL2 권장)
- **RAM**: 최소 2GB (4GB 권장)
- **디스크**: 10GB+ (Docker 이미지, 애플리케이션 데이터, 로그)

Node.js 설치 여부를 확인한다:

```bash
node --version
# v20.x.x 이상

npm --version
# 10.x.x 이상
```

### LLM API 키

OpenClaw 자체는 무료지만, AI 모델 사용을 위한 API 키가 필요하다. 지원하는 주요 프로바이더:

| 프로바이더 | 환경변수 | 비고 |
|-----------|---------|------|
| Anthropic | `ANTHROPIC_API_KEY` | Claude 모델 |
| OpenAI | `OPENAI_API_KEY` | GPT 모델 |
| Google | `GOOGLE_API_KEY` | Gemini 모델 |
| Ollama | (로컬) | 무료, 로컬 실행 |

:::tip
처음 시작한다면 **Anthropic Claude** 또는 **OpenAI GPT** 중 하나의 API 키를 준비하면 된다. 로컬 LLM(Ollama)을 사용하면 API 비용 없이 운영할 수도 있다.
:::

### 메시징 플랫폼 API 키

연동할 메시징 플랫폼의 봇 토큰이 필요하다:

- **Telegram**: BotFather에서 봇 생성 후 토큰 발급
- **Discord**: Discord Developer Portal에서 봇 생성
- **Slack**: Slack API에서 앱 생성 후 Bot Token 발급
- **WhatsApp**: Meta Business API 설정 (가장 복잡)

---

## 설치 방법

### 방법 1: 원라이너 설치 (권장)

가장 간단한 설치 방법이다. Node.js가 없어도 자동으로 설치해준다:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

설치가 완료되면 온보딩 마법사가 자동으로 시작된다:

```bash
openclaw onboard
```

온보딩 과정에서 다음을 설정한다:
1. LLM 프로바이더 선택
2. API 키 입력
3. Gateway 데몬 설정

```output
🦞 Welcome to OpenClaw!

? Choose your AI provider:
  ❯ Anthropic (Claude)
    OpenAI (GPT)
    Google (Gemini)
    Ollama (Local)
    Custom Provider

? Enter your Anthropic API key: sk-ant-***

✓ API key validated
✓ Gateway configured
✓ Daemon installed

OpenClaw is ready! Send a message to start.
```

### 방법 2: Git Clone

소스 코드에서 직접 빌드하는 방법이다:

```bash
# 저장소 클론
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# 의존성 설치
npm install

# 환경변수 설정
cp .env.example .env

# 빌드 및 실행
npm run build
npm start
```

### 방법 3: Docker (프로덕션 권장)

Docker를 사용한 설치는 프로덕션 환경에서 권장된다:

```bash
# 저장소 클론
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# 환경변수 설정
cp .env.example .env

# Docker Compose로 실행
docker compose up -d
```

`docker-compose.yml` 기본 구조:

```yaml
version: '3.8'
services:
  openclaw:
    image: openclaw/openclaw:latest
    container_name: openclaw
    restart: unless-stopped
    volumes:
      - ./data:/home/node/.openclaw
      - ./workspace:/home/node/.openclaw/workspace
    env_file:
      - .env
    ports:
      - "3000:3000"
    user: "1000:1000"
```

:::warning
Docker 환경에서는 반드시 `user: "1000:1000"`을 설정하여 root가 아닌 사용자로 실행해야 한다. 또한 볼륨 마운트는 OpenClaw가 실제로 필요한 디렉토리만 노출하자.
:::

---

## 초기 설정

### .env 파일 구성

OpenClaw의 환경변수는 `~/.openclaw/.env`에 저장된다. 주요 설정 항목:

```bash
# LLM Provider
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# Telegram (선택)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Discord (선택)
DISCORD_BOT_TOKEN=your-discord-bot-token

# Slack (선택)
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# WhatsApp (선택)
WHATSAPP_AUTH_TOKEN=your-whatsapp-token

# Gateway 설정
OPENCLAW_PORT=3000
OPENCLAW_LOG_LEVEL=info
```

환경변수의 우선순위는 다음과 같다:

1. 프로세스 환경변수 (`export`)
2. 현재 디렉토리의 `.env`
3. 글로벌 `~/.openclaw/.env`
4. `openclaw.json`의 `env` 블록

### LLM 프로바이더 설정

`~/.openclaw/openclaw.json`에서 모델을 상세 설정할 수 있다:

```json
{
  "models": {
    "default": "anthropic/claude-sonnet-4.5",
    "providers": {
      "anthropic": {
        "apiKey": "$ANTHROPIC_API_KEY",
        "models": [
          {
            "id": "claude-sonnet-4.5",
            "name": "Claude Sonnet 4.5",
            "contextWindow": 200000,
            "maxTokens": 8192
          },
          {
            "id": "claude-haiku-4.5",
            "name": "Claude Haiku 4.5",
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      },
      "openai": {
        "apiKey": "$OPENAI_API_KEY",
        "models": [
          {
            "id": "gpt-4.1",
            "name": "GPT-4.1",
            "contextWindow": 128000,
            "maxTokens": 16384
          }
        ]
      }
    }
  }
}
```

:::tip
모델 참조는 `프로바이더/모델명` 형식을 사용한다. 예: `anthropic/claude-sonnet-4.5`, `openai/gpt-4.1`, `ollama/llama3.3`. API 키는 `$ENV_VAR` 형식으로 환경변수를 참조할 수 있어 보안에 유리하다.
:::

### 로컬 LLM 설정 (Ollama)

API 비용 없이 로컬에서 LLM을 실행하려면 Ollama를 사용한다:

```bash
# Ollama 설치 (macOS)
brew install ollama

# 모델 다운로드
ollama pull llama3.3
ollama pull qwen3.5

# Ollama 서버 시작
ollama serve
```

`openclaw.json`에 Ollama 프로바이더를 추가한다:

```json
{
  "models": {
    "default": "ollama/llama3.3",
    "providers": {
      "ollama": {
        "baseUrl": "http://localhost:11434",
        "api": "openai-completions",
        "models": [
          {
            "id": "llama3.3",
            "name": "Llama 3.3 8B",
            "contextWindow": 131072,
            "maxTokens": 4096
          }
        ]
      }
    }
  }
}
```

### 설정 검증

설정이 올바른지 진단 명령으로 확인한다:

```bash
openclaw doctor
```

```output
OpenClaw Doctor v1.x.x

✓ Configuration file    ~/.openclaw/openclaw.json
✓ Environment file      ~/.openclaw/.env
✓ Anthropic API         Connected (claude-sonnet-4.5)
✓ Telegram Bot          Connected (@YourBot)
✗ Discord Bot           Not configured
✗ WhatsApp              Not configured
✓ SQLite database       ~/.openclaw/data/openclaw.db
✓ Workspace             ~/.openclaw/workspace

Status: Ready (2/4 channels active)
```

---

## 메시징 플랫폼 연동

### Telegram 연동 (가장 간단)

Telegram은 공식 Bot API를 사용하므로 설정이 가장 간단하고 응답 속도도 빠르다.

**1단계: BotFather에서 봇 생성**

Telegram에서 `@BotFather`를 검색하여 대화를 시작한다:

```
/newbot
```

봇 이름과 사용자명을 설정하면 토큰이 발급된다:

```output
Done! Congratulations on your new bot.
Use this token to access the HTTP API:
7654321098:AAF-your-bot-token-here
```

**2단계: 환경변수 설정**

발급받은 토큰을 `.env`에 추가한다:

```bash
TELEGRAM_BOT_TOKEN=7654321098:AAF-your-bot-token-here
```

**3단계: 채널 설정**

`openclaw.json`에 Telegram 채널을 추가한다:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "$TELEGRAM_BOT_TOKEN",
      "allowFrom": ["your_telegram_username"],
      "polling": true
    }
  }
}
```

:::warning
`allowFrom`을 반드시 설정하여 허용된 사용자만 봇과 대화할 수 있도록 해야 한다. 비워두면 누구나 봇에게 메시지를 보낼 수 있어 API 비용이 급증할 수 있다.
:::

**4단계: Gateway 재시작 및 테스트**

```bash
openclaw gateway restart
```

Telegram에서 봇에게 메시지를 보내면 AI가 응답한다.

### WhatsApp 연동

WhatsApp은 Meta의 API 요구사항이 엄격해 설정이 가장 복잡하다.

**1단계: 전용 번호 준비**

:::warning
개인 번호를 OpenClaw WhatsApp 자동화에 절대 사용하지 말 것. 전용 비즈니스 번호를 사용해야 의도치 않은 메시지 전송과 계정 차단을 방지할 수 있다.
:::

**2단계: WhatsApp Business API 설정**

Meta Developer Portal에서 WhatsApp Business API를 설정한다:

1. [developers.facebook.com](https://developers.facebook.com)에서 앱 생성
2. WhatsApp 제품 추가
3. 비즈니스 전화번호 등록
4. 영구 토큰 생성

**3단계: 환경변수 및 채널 설정**

```bash
WHATSAPP_AUTH_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
```

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "authToken": "$WHATSAPP_AUTH_TOKEN",
      "phoneNumberId": "$WHATSAPP_PHONE_NUMBER_ID",
      "allowFrom": ["+821012345678"],
      "webhookVerifyToken": "your-verify-token"
    }
  }
}
```

### Discord 연동

**1단계: Discord Developer Portal에서 봇 생성**

1. [discord.com/developers](https://discord.com/developers/applications)에서 새 애플리케이션 생성
2. Bot 섹션에서 토큰 생성
3. OAuth2 URL Generator에서 `bot` 스코프와 필요한 권한 선택
4. 생성된 URL로 서버에 봇 초대

**2단계: 설정**

```bash
DISCORD_BOT_TOKEN=your-discord-bot-token
```

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "botToken": "$DISCORD_BOT_TOKEN",
      "allowGuilds": ["your-server-id"],
      "allowChannels": ["channel-id-1", "channel-id-2"]
    }
  }
}
```

---

## 첫 대화

Gateway가 실행되고 메시징 플랫폼이 연동되면, 봇에게 메시지를 보내 첫 대화를 시작한다.

### 기본 대화

Telegram이나 다른 연동된 플랫폼에서 봇에게 메시지를 보낸다:

```
사용자: 안녕, 너는 누구야?
봇: 안녕하세요! 저는 OpenClaw 기반의 AI 어시스턴트입니다.
    다양한 작업을 도와드릴 수 있어요 - 정보 검색, 일정 관리,
    파일 정리, 이메일 처리 등 무엇이든 말씀해주세요.
```

### 실용적인 활용 예시

OpenClaw는 단순 채팅을 넘어 실제 작업을 수행한다:

```
사용자: 내일 오후 3시에 팀 미팅 일정 잡아줘
봇: Google Calendar에 내일 오후 3시 팀 미팅을 등록했습니다.
    참석자를 추가할까요?

사용자: 오늘 받은 이메일 중 중요한 것만 요약해줘
봇: 오늘 수신된 이메일 23통 중 중요 메일 3통을 정리했습니다:
    1. [프로젝트A] 배포 승인 요청 - 김팀장
    2. [인사] 연차 승인 완료 - HR
    3. [긴급] 서버 모니터링 알림 - DevOps

사용자: ~/Documents/report.md 파일 내용 요약해줘
봇: report.md 파일을 확인했습니다. 요약:
    Q1 매출 목표 달성률 95%, 신규 고객 15% 증가...
```

### Skills 설치

OpenClaw의 기능을 확장하려면 **Skills**를 설치한다. Skills는 AI에게 특정 도구 사용법을 가르치는 지침서다:

```bash
# 사용 가능한 Skills 검색
openclaw skills search "google calendar"

# Skill 설치
openclaw skills install google-calendar

# 설치된 Skills 확인
openclaw skills list
```

```output
Installed Skills:
  ├── google-calendar    v2.1.0  Calendar management
  ├── gmail              v1.8.0  Email automation
  ├── file-manager       v3.0.1  File system operations
  └── web-search         v1.5.0  Web browsing and search
```

5,400개 이상의 커뮤니티 Skills가 등록되어 있으며, 직접 만들 수도 있다.

---

## Local-First 아키텍처 개요

### 왜 Local-First인가

OpenClaw의 핵심 설계 철학은 **local-first**다. 모든 데이터가 사용자의 머신에 저장되고, 외부 서버에 의존하지 않는다:

| 구성요소 | 저장 위치 | 설명 |
|----------|----------|------|
| 설정 | `~/.openclaw/openclaw.json` | 에이전트 설정, 채널 구성 |
| 환경변수 | `~/.openclaw/.env` | API 키, 토큰 |
| 데이터베이스 | `~/.openclaw/data/openclaw.db` | SQLite (대화 기록, 벡터 인덱스) |
| 워크스페이스 | `~/.openclaw/workspace/` | 에이전트 컨텍스트 파일 |
| 세션 | `~/.openclaw/sessions/` | 대화 세션 상태 |
| 로그 | `/tmp/openclaw/` | 롤링 로그 파일 |

### 아키텍처 흐름

OpenClaw의 메시지 처리 흐름을 간략히 정리한다:

```
메시징 앱 (Telegram/WhatsApp/...)
    ↓
Channel Adapter (메시지 정규화)
    ↓
Gateway Server (중앙 코디네이터)
    ↓
Session Router → Lane Queue
    ↓
Agent Runner (컨텍스트 조립)
    ↓
LLM API (Claude/GPT/Ollama)
    ↓
Agentic Loop (도구 호출 → 결과 → 반복)
    ↓
응답 스트리밍 → 메시징 앱
```

핵심은 **Agentic Loop**다. LLM이 도구 호출을 제안하면 시스템이 실행하고, 결과를 LLM에 다시 전달하는 과정을 해결될 때까지 반복한다. 이것이 OpenClaw를 단순 챗봇이 아닌 "에이전트"로 만드는 핵심 메커니즘이다.

### 디렉토리 구조

OpenClaw 설치 후 기본 디렉토리 구조:

```
~/.openclaw/
├── openclaw.json          # 메인 설정 파일
├── .env                   # 환경변수 (API 키, 토큰)
├── data/
│   └── openclaw.db        # SQLite 데이터베이스
├── workspace/
│   ├── AGENTS.md          # 에이전트 동작 규칙
│   ├── SOUL.md            # 에이전트 페르소나
│   ├── USER.md            # 사용자 정보/선호도
│   ├── HEARTBEAT.md       # 주기적 작업 목록
│   └── IDENTITY.md        # 에이전트 정체성
├── skills/                # 설치된 Skills
├── sessions/              # 대화 세션
└── agents/                # 멀티 에이전트 설정
    └── <agentId>/
        └── sessions/
```

### Gateway 데몬

OpenClaw Gateway는 백그라운드 데몬으로 실행되어 메시징 플랫폼의 메시지를 24시간 수신한다:

```bash
# Gateway 시작
openclaw gateway start

# Gateway 상태 확인
openclaw gateway status

# Gateway 중지
openclaw gateway stop

# Gateway 로그 확인
openclaw gateway logs --follow
```

```output
OpenClaw Gateway v1.x.x
Status: Running
Uptime: 2h 15m
Channels:
  telegram  ✓ active  (@MyAssistantBot)
  discord   ✓ active  (MyAssistant#1234)
  whatsapp  ✗ disabled
Sessions: 3 active
Memory: 245 MB
```

Gateway는 `openclaw.json` 파일의 변경을 감지하여 대부분의 설정을 **핫 리로드**한다. 채널 추가나 모델 변경 시 재시작 없이 반영된다.

---

## 워크스페이스 파일 이해하기

OpenClaw의 동작을 결정하는 핵심 워크스페이스 파일들을 간략히 소개한다. 각 파일의 심층 활용법은 이후 시리즈에서 다룬다.

### AGENTS.md

에이전트의 동작 규칙과 지침을 정의한다:

```markdown
# Agent Guidelines

## Communication
- Always respond in Korean
- Keep responses concise but helpful
- Use bullet points for lists

## Boundaries
- Never share API keys or credentials
- Ask for confirmation before file modifications
- Do not access files outside the workspace
```

### SOUL.md

에이전트의 성격과 행동 특성을 정의한다:

```markdown
# Soul

You are a helpful and proactive personal assistant.
You have a warm, professional tone.
You prefer structured responses with clear action items.
When uncertain, you ask clarifying questions rather than guessing.
```

### USER.md

사용자에 대한 정보를 저장하여 개인화된 응답을 제공한다:

```markdown
# User Profile

- Name: 현정
- Language: Korean (primary), English (technical terms OK)
- Timezone: Asia/Seoul (KST, UTC+9)
- Preferences: Concise answers, Markdown formatting
```

---

## 문제 해결

### 자주 발생하는 문제

**Gateway가 시작되지 않을 때:**

```bash
# 포트 충돌 확인
lsof -i :3000

# 로그 확인
cat /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | tail -50

# 설정 검증
openclaw doctor
```

**Telegram 봇이 응답하지 않을 때:**

```bash
# 봇 토큰 유효성 확인
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Gateway 로그에서 Telegram 관련 에러 확인
openclaw gateway logs | grep telegram
```

**LLM API 오류:**

```bash
# API 키 유효성 확인
openclaw doctor

# 다른 모델로 전환 테스트
openclaw config set models.default "openai/gpt-4.1-mini"
```

:::tip
`openclaw doctor` 명령은 설정 파일 문법, 프로바이더 연결, 모델 가용성, 인증 상태를 종합적으로 진단한다. 문제가 생기면 가장 먼저 실행하자.
:::

### 유용한 CLI 명령어

| 명령어 | 설명 |
|--------|------|
| `openclaw onboard` | 초기 설정 마법사 |
| `openclaw doctor` | 설정 진단 |
| `openclaw gateway start/stop/restart` | Gateway 관리 |
| `openclaw gateway logs` | 로그 확인 |
| `openclaw skills search <query>` | Skills 검색 |
| `openclaw skills install <name>` | Skills 설치 |
| `openclaw config set <key> <value>` | 설정 변경 |
| `openclaw agents list` | 에이전트 목록 |

---

## 정리

이 글에서 다룬 내용을 정리한다:

- **OpenClaw**는 메시징 기반의 local-first AI 에이전트 플랫폼이다
- **25+ 메시징 플랫폼**을 지원하며, Telegram이 설정이 가장 간단하다
- 설치는 **원라이너, Git Clone, Docker** 세 가지 방법을 지원한다
- **openclaw.json**과 **.env**로 LLM 프로바이더와 채널을 설정한다
- 워크스페이스 파일(**AGENTS.md, SOUL.md, USER.md**)로 에이전트 동작을 제어한다
- **local-first 아키텍처**로 모든 데이터가 사용자 머신에 저장된다

다음 글 [[openclaw-guide-02-core|OpenClaw 핵심 기능]]에서는 아키텍처와 도구 시스템을 상세히 분석한다.