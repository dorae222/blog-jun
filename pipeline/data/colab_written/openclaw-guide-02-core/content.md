<!-- infographic-hero -->
![OpenClaw Core Features 핵심 요약](figures/infographic.svg)

*Figure: OpenClaw Core Features 한 장 요약 인포그래픽*

# OpenClaw 핵심 기능: 아키텍처와 도구 시스템

## 들어가며

:::info
이 글은 **OpenClaw Guide** 시리즈의 두 번째 글이다. 시리즈 전체 목차:
1. [[openclaw-guide-01-setup|메시징 기반 AI 에이전트]]
2. **핵심 기능: 아키텍처와 도구 시스템** (현재 글)
3. [[openclaw-guide-03-advanced|고급 활용: 커스터마이징과 확장]]
4. [[openclaw-guide-04-workflow|실전: 자체 호스팅 AI 에이전트 환경]]
:::

이전 글에서 OpenClaw를 설치하고 첫 대화를 나누었다. 이 글에서는 OpenClaw가 **어떻게 동작하는지** 내부 아키텍처를 분석한다. TypeScript 기반의 Gateway 구조, SQLite+sqlite-vec 벡터 저장소, MCP 도구 시스템, 캐릭터 시스템, 메시지 처리 파이프라인까지 핵심 구성요소를 하나씩 살펴본다.

---

## 아키텍처 상세

### 기술 스택

OpenClaw는 TypeScript와 Node.js 기반으로 구축되었다. 전체 기술 스택을 정리한다:

| 계층 | 기술 | 역할 |
|------|------|------|
| 런타임 | Node.js 20+ | 서버 실행 환경 |
| 언어 | TypeScript | 타입 안전한 코드베이스 |
| 데이터베이스 | SQLite | 대화 기록, 설정, 세션 |
| 벡터 검색 | sqlite-vec | 임베딩 기반 유사도 검색 |
| 전문 검색 | SQLite FTS5 | 키워드 기반 전문 검색 |
| 프로토콜 | MCP (Model Context Protocol) | 도구 통신 표준 |
| 패키지 관리 | npm | 의존성 관리 |

### Gateway 아키텍처

OpenClaw의 핵심은 **Gateway 서버**다. Gateway는 메시징 플랫폼과 LLM 사이의 중앙 코디네이터로, 다음 역할을 수행한다:

```text
┌─────────────────────────────────────────────────┐
│                 Gateway Server                   │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Telegram │  │ Discord  │  │ WhatsApp │  ... │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │              │              │            │
│       └──────────────┼──────────────┘            │
│                      ↓                           │
│            ┌─────────────────┐                   │
│            │ Message Router  │                   │
│            └────────┬────────┘                   │
│                     ↓                            │
│            ┌─────────────────┐                   │
│            │ Session Manager │                   │
│            └────────┬────────┘                   │
│                     ↓                            │
│            ┌─────────────────┐                   │
│            │  Agent Runner   │                   │
│            └────────┬────────┘                   │
│                     ↓                            │
│            ┌─────────────────┐                   │
│            │   LLM Client   │                   │
│            └─────────────────┘                   │
└─────────────────────────────────────────────────┘
```

각 구성요소의 역할:

- **Channel Adapter**: 각 메시징 플랫폼의 API를 통일된 내부 형식으로 변환한다. 메시지 수신, 첨부 파일 추출, 응답 전송을 담당한다.
- **Message Router**: 수신된 메시지를 적절한 에이전트로 라우팅한다. 멀티 에이전트 환경에서는 채널, 계정, 피어 정보를 기반으로 라우팅한다.
- **Session Manager**: 대화 세션의 생명주기를 관리한다. 세션별로 독립적인 "레인(Lane)"을 할당하여 상태 오염을 방지한다.
- **Agent Runner**: 컨텍스트를 조립하고 LLM에 프롬프트를 전달한다. 워크스페이스 파일(AGENTS.md, SOUL.md 등)을 시스템 프롬프트에 주입한다.
- **LLM Client**: 다양한 LLM 프로바이더와 통신한다. OpenAI 호환 API와 Anthropic Messages API를 모두 지원한다.

### 레인 기반 직렬 실행

OpenClaw는 세션 격리를 위해 **레인(Lane)** 개념을 사용한다. 각 세션은 독립적인 레인에서 실행되며, 같은 레인 내 작업은 직렬로 처리된다:

```typescript
// 개념적 구조 (실제 코드를 단순화한 형태)
interface Lane {
  sessionId: string;
  queue: Message[];
  isProcessing: boolean;
}

// 같은 세션의 메시지는 순서대로 처리
// 다른 세션의 메시지는 병렬 처리 가능
```

이 설계는 한 사용자의 대화가 다른 사용자의 대화에 영향을 주지 않도록 보장한다.

---

## 멀티 LLM 지원

### 지원 프로바이더

OpenClaw는 단일 LLM에 종속되지 않는다. 다양한 프로바이더를 동시에 설정하고, 용도에 따라 다른 모델을 사용할 수 있다:

| 프로바이더 | API 타입 | 주요 모델 |
|-----------|---------|----------|
| Anthropic | anthropic-messages | Claude Opus 4.6, Sonnet 4.5, Haiku 4.5 |
| OpenAI | openai-completions | GPT-4.1, GPT-4.1-mini, GPT-4.1-nano |
| Google | openai-completions | Gemini 2.5 Pro, Gemini 2.5 Flash |
| Ollama | openai-completions | Llama 3.3, Qwen 3.5, Mistral |
| LM Studio | openai-completions | 로컬 모델 |
| Groq | openai-completions | 고속 추론 특화 |

### 모델 라우팅

용도별로 다른 모델을 지정하여 비용과 성능을 최적화할 수 있다:

```json
{
  "models": {
    "default": "anthropic/claude-sonnet-4.5",
    "routing": {
      "reasoning": "anthropic/claude-opus-4.6",
      "light": "anthropic/claude-haiku-4.5",
      "routine": "ollama/llama3.3",
      "code": "openai/gpt-4.1"
    }
  }
}
```

:::tip
**비용 최적화의 핵심은 모델 라우팅**이다. 복잡한 분석에는 Opus급 모델을, 단순 Q&A에는 Haiku나 로컬 모델을 사용하면 월 API 비용을 80% 이상 절감할 수 있다.
:::

### 커스텀 프로바이더 추가

OpenAI 호환 API를 제공하는 서비스라면 어떤 것이든 프로바이더로 추가할 수 있다:

```json
{
  "models": {
    "providers": {
      "my-custom": {
        "baseUrl": "https://my-llm-api.example.com/v1",
        "apiKey": "$MY_CUSTOM_API_KEY",
        "api": "openai-completions",
        "models": [
          {
            "id": "my-model-v1",
            "name": "My Custom Model v1",
            "reasoning": false,
            "inputTypes": ["text"],
            "contextWindow": 32000,
            "maxTokens": 4096,
            "costs": {
              "input": 0.5,
              "output": 1.5
            }
          }
        ]
      }
    }
  }
}
```

`costs` 필드는 백만 토큰당 달러 단위로, OpenClaw의 비용 추적 기능에 활용된다.

### 모델 변경

CLI로 기본 모델을 변경할 수 있다:

```bash
# 현재 모델 확인
openclaw config get models.default

# 모델 변경
openclaw config set models.default "openai/gpt-4.1"

# 변경 확인 (Gateway가 자동 핫 리로드)
openclaw doctor
```

---

## MCP 기반 도구 시스템

### MCP란 무엇인가

**MCP(Model Context Protocol)**는 AI 에이전트가 외부 도구와 통신하기 위한 표준 프로토콜이다. OpenClaw는 `@modelcontextprotocol/sdk`를 내장하여 MCP 서버와 네이티브로 연동된다.

MCP의 핵심 개념:

| 개념 | 설명 |
|------|------|
| MCP Server | 도구를 제공하는 프로세스 (예: Notion MCP, GitHub MCP) |
| MCP Client | 도구를 호출하는 측 (OpenClaw Agent Runner) |
| Tool | 서버가 제공하는 개별 기능 (예: create_page, search_issues) |
| Resource | 서버가 제공하는 데이터 소스 |
| Prompt | 서버가 제공하는 프롬프트 템플릿 |

### MCP 서버 설정

`openclaw.json`에서 MCP 서버를 설정한다:

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "mcp": {
          "servers": [
            {
              "name": "notion",
              "command": "npx",
              "args": ["-y", "@notionhq/mcp"],
              "env": {
                "NOTION_API_KEY": "$NOTION_API_KEY"
              }
            },
            {
              "name": "github",
              "command": "npx",
              "args": ["-y", "@anthropic/mcp-github"],
              "env": {
                "GITHUB_TOKEN": "$GITHUB_TOKEN"
              }
            },
            {
              "name": "filesystem",
              "command": "npx",
              "args": ["-y", "@anthropic/mcp-fs", "/home/user/documents"]
            }
          ]
        }
      }
    ]
  }
}
```

### MCP 연결 흐름

OpenClaw가 시작되면(또는 새 MCP 서버가 설정에 추가되면) 다음 과정을 거친다:

1. **프로세스 생성**: MCP 서버 프로세스를 스폰한다
2. **핸드셰이크**: 서버와 capability negotiation을 수행한다
3. **도구 등록**: 서버가 제공하는 도구 목록(파라미터 스키마 포함)을 수신한다
4. **대화 중 호출**: AI가 도구 사용을 결정하면 MCP 프로토콜로 요청을 전송한다
5. **결과 반환**: 도구 실행 결과가 AI에게 전달되어 응답에 반영된다

```text
사용자: "Notion에서 이번 주 회의록 찾아줘"
    ↓
Agent Runner → LLM: "사용 가능한 도구: notion.search_pages, ..."
    ↓
LLM 응답: tool_call(notion.search_pages, {query: "회의록", date: "this_week"})
    ↓
Agent Runner → MCP Server (Notion): search_pages 실행
    ↓
MCP Server → Agent Runner: 검색 결과 반환
    ↓
Agent Runner → LLM: 결과를 포함한 후속 프롬프트
    ↓
LLM → 사용자: "이번 주 회의록 3건을 찾았습니다: ..."
```

### 주요 MCP 서버

커뮤니티에서 제공하는 주요 MCP 서버:

| MCP 서버 | 기능 |
|----------|------|
| `@notionhq/mcp` | Notion 페이지/데이터베이스 관리 |
| `@anthropic/mcp-github` | GitHub 이슈/PR/레포 관리 |
| `@anthropic/mcp-fs` | 파일 시스템 읽기/쓰기 |
| `@anthropic/mcp-google` | Google Calendar/Drive/Gmail |
| `@anthropic/mcp-slack` | Slack 메시지/채널 관리 |
| `@anthropic/mcp-browser` | 웹 브라우징/스크래핑 |
| `homeassistant-mcp` | 스마트홈 기기 제어 |

1,000개 이상의 커뮤니티 MCP 서버가 있어 거의 모든 서비스와 연동할 수 있다.

---

## 벡터 저장소와 메모리

### RAG-lite 아키텍처

OpenClaw의 메모리 시스템은 전통적인 RAG와 다르게 **파일 우선(file-first)** 접근을 취한다. 마크다운 파일이 진실의 원천(source of truth)이고, 벡터 인덱스는 검색 효율을 위한 보조 구조다.

```text
워크스페이스 마크다운 파일
    ↓
청킹 (Markdown 구조 기반)
    ↓
임베딩 생성
    ↓
SQLite + sqlite-vec에 저장
    ↓
대화 시 하이브리드 검색으로 관련 컨텍스트 조회
```

### SQLite + sqlite-vec

OpenClaw는 외부 벡터 데이터베이스 대신 **SQLite의 sqlite-vec 확장**을 사용한다. 단일 `.db` 파일로 모든 데이터를 관리하는 것이 local-first 철학에 부합한다.

```sql
-- sqlite-vec가 제공하는 가상 테이블 (개념적 구조)
CREATE VIRTUAL TABLE vec_embeddings USING vec0(
  id INTEGER PRIMARY KEY,
  embedding FLOAT[1536]  -- OpenAI text-embedding-3-small 기준
);

-- 벡터 검색 쿼리
SELECT id, distance
FROM vec_embeddings
WHERE embedding MATCH ?
ORDER BY distance
LIMIT 10;
```

:::info
sqlite-vec 확장이 사용 가능하면 OpenClaw는 임베딩을 SQLite 가상 테이블(`vec0`)에 저장하고, 데이터베이스 내에서 벡터 거리 쿼리를 수행한다. 모든 임베딩을 JavaScript 메모리에 로드하지 않아도 되므로 검색이 빠르다.
:::

### 하이브리드 검색

OpenClaw는 벡터 유사도만 사용하지 않는다. **가중 점수 퓨전(weighted score fusion)**으로 두 가지 검색 방법을 결합한다:

| 검색 방법 | 기본 가중치 | 기술 | 강점 |
|-----------|-----------|------|------|
| 벡터 검색 | 70% | cosine similarity (sqlite-vec) | 의미적 유사도 |
| 키워드 검색 | 30% | BM25 (SQLite FTS5) | 정확한 용어 매칭 |

이 하이브리드 접근의 장점:

- "TypeScript" 같은 고유명사는 FTS5가 정확히 매칭한다
- "JavaScript와 비슷한 언어" 같은 의미 기반 질문은 벡터 검색이 처리한다
- 두 결과를 가중 합산하여 더 정확한 검색 결과를 제공한다

### 메모리 설정

메모리 시스템의 동작을 `openclaw.json`에서 세밀하게 조정할 수 있다:

```json
{
  "memory": {
    "enabled": true,
    "embeddingModel": "openai/text-embedding-3-small",
    "chunkSize": 512,
    "chunkOverlap": 50,
    "searchWeights": {
      "vector": 0.7,
      "keyword": 0.3
    },
    "maxResults": 10,
    "minRelevanceScore": 0.3,
    "autoIndex": true,
    "indexPaths": [
      "workspace/**/*.md",
      "workspace/notes/**"
    ]
  }
}
```

:::tip
`autoIndex`를 켜면 워크스페이스의 마크다운 파일이 변경될 때 자동으로 재인덱싱된다. 대규모 워크스페이스에서는 `indexPaths`로 인덱싱 범위를 제한하는 것이 좋다.
:::

### 메모리 관리 명령어

```bash
# 메모리 인덱스 상태 확인
openclaw memory status

# 수동 인덱싱 실행
openclaw memory reindex

# 메모리 검색 테스트
openclaw memory search "프로젝트 배포 절차"

# 메모리 초기화
openclaw memory clear
```

```output
Memory Status:
  Documents indexed: 47
  Chunks: 312
  Embedding model: openai/text-embedding-3-small
  Database size: 15.2 MB
  Last indexed: 2026-03-28 14:30:00 KST
```

---

## 캐릭터 시스템

### 개요

OpenClaw의 캐릭터 시스템은 AI 에이전트에게 **일관된 성격과 행동 규칙**을 부여한다. 단순한 시스템 프롬프트를 넘어, 여러 마크다운 파일로 구성된 다층적 페르소나를 정의할 수 있다.

### 핵심 파일 구조

| 파일 | 역할 | 주입 위치 |
|------|------|----------|
| `SOUL.md` | 깊은 행동 특성, 장기 목표, 철학 | 시스템 프롬프트 (코어) |
| `IDENTITY.md` | 이름, 이모지, 말투, 외형적 특성 | 시스템 프롬프트 (표면) |
| `USER.md` | 사용자 정보, 선호도, 스타일 | 시스템 프롬프트 (컨텍스트) |
| `AGENTS.md` | 동작 규칙, 경계선, 도구 사용 지침 | 시스템 프롬프트 (규칙) |
| `HEARTBEAT.md` | 주기적으로 수행할 모니터링 작업 | Heartbeat 루틴 |

이 파일들은 워크스페이스에 위치하며, **자동으로 시스템 프롬프트에 주입**되어 에이전트에게 지속적인 컨텍스트를 제공한다.

### SOUL.md 작성 예시

```markdown
# Soul

## Core Philosophy
나는 사용자의 시간을 가장 소중하게 여기는 AI 어시스턴트다.
불필요한 말을 줄이고 실행 가능한 결과를 제공한다.

## Communication Style
- 한국어로 대화한다
- 기술적 용어는 영어 원문을 병기한다
- 리스트와 표를 적극 활용한다
- 확실하지 않은 정보는 반드시 "확인이 필요합니다"라고 명시한다

## Long-term Goals
- 사용자의 업무 패턴을 학습하여 점점 더 효율적으로 돕는다
- 반복적인 작업을 자동화하여 사용자의 시간을 절약한다
```

### IDENTITY.md 작성 예시

```markdown
# Identity

## Basics
- Name: 클로
- Emoji: 🦞
- Catchphrase: "도와드릴게요!"
- Vibe: 따뜻하고 전문적인 비서

## Visual
- Avatar: avatars/claw-assistant.png

## Mannerisms
- 인사할 때 이모지를 사용한다
- 작업 완료 시 체크 마크(✓)를 붙인다
- 에러 발생 시 원인을 먼저 설명하고 해결책을 제시한다
```

### openclaw.json의 identity 설정

워크스페이스 파일 외에 `openclaw.json`에서도 기본 정체성을 설정할 수 있다:

```json
{
  "identity": {
    "name": "클로",
    "theme": "helpful professional assistant",
    "emoji": "🦞",
    "avatar": "avatars/claw-assistant.png"
  }
}
```

---

## 메시지 처리 파이프라인

### 6단계 처리 흐름

OpenClaw의 메시지 처리는 6개 주요 단계를 거친다:

**1단계: 채널 수신 (Channel Ingress)**

메시징 플랫폼의 Channel Adapter가 메시지를 수신한다. 각 플랫폼의 고유 형식(Telegram의 Update, Discord의 Message 등)을 통일된 내부 형식으로 변환한다.

```typescript
// 내부 메시지 형식 (개념적 구조)
interface NormalizedMessage {
  channelType: 'telegram' | 'discord' | 'whatsapp' | ...;
  accountId: string;
  peerId: string;
  content: string;
  attachments: Attachment[];
  timestamp: Date;
  metadata: Record<string, unknown>;
}
```

**2단계: 정규화 및 중복 제거 (Normalization)**

동일 메시지의 중복 수신을 필터링하고, 첨부 파일을 추출한다.

**3단계: 접근 제어 (Access Control)**

`allowFrom`, `allowGuilds`, `allowChannels` 설정에 따라 허용된 사용자/채널인지 확인한다.

**4단계: 세션 라우팅 (Session Resolution)**

메시지를 적절한 에이전트와 세션에 라우팅한다. 멀티 에이전트 환경에서는 바인딩 규칙에 따라 결정된다.

**5단계: 에이전트 처리 (Agent Processing)**

Agent Runner가 컨텍스트를 조립하고 LLM에 전달한다:

```text
시스템 프롬프트 조립:
  ├── SOUL.md 내용
  ├── IDENTITY.md 내용
  ├── USER.md 내용
  ├── AGENTS.md 규칙
  ├── 사용 가능한 도구 목록
  ├── 관련 메모리 (RAG 검색 결과)
  └── 대화 히스토리
```

**6단계: 응답 전달 (Reply Delivery)**

LLM의 응답을 원래 채널로 스트리밍한다. 도구 호출이 포함된 경우 Agentic Loop가 실행된다.

### Agentic Loop 상세

Agentic Loop는 OpenClaw의 핵심 메커니즘이다. LLM이 도구 호출을 제안하면 실행하고, 결과를 다시 LLM에 전달하는 과정을 반복한다:

```text
Agent Runner → LLM: 사용자 메시지 + 컨텍스트 + 도구 목록
    ↓
LLM 응답: "도구 X를 호출하겠습니다" (tool_call)
    ↓
Agent Runner: 도구 X 실행 → 결과 획득
    ↓
Agent Runner → LLM: 도구 결과 + 이전 컨텍스트
    ↓
LLM 응답: "추가로 도구 Y를 호출하겠습니다" (tool_call)
    ↓
Agent Runner: 도구 Y 실행 → 결과 획득
    ↓
Agent Runner → LLM: 모든 도구 결과 + 컨텍스트
    ↓
LLM 응답: "최종 결과입니다: ..." (텍스트 응답)
    ↓
사용자에게 전달
```

이 루프에는 안전장치가 있다:

| 제한 | 기본값 | 설명 |
|------|--------|------|
| 최대 반복 횟수 | 10 | 무한 루프 방지 |
| 턴당 최대 토큰 | 모델별 상이 | 비용 제한 |
| 타임아웃 | 300초 | 장기 실행 방지 |
| 도구 실행 타임아웃 | 60초 | 개별 도구 타임아웃 |

---

## Skills 시스템

### Skills란 무엇인가

Skills는 OpenClaw에게 **특정 도구 조합을 사용하는 방법**을 가르치는 지침서다. SDK나 컴파일이 필요 없이, `SKILL.md` 마크다운 파일 하나로 정의된다.

:::info
**MCP 서버와 Skills의 관계**: MCP 서버가 개별 도구(Tool)를 제공한다면, Skills는 그 도구들을 **조합하여 특정 작업을 수행하는 방법**을 에이전트에게 가르친다. 예를 들어 `gmail` MCP 서버가 이메일 검색/전송 도구를 제공하고, `inbox-cleanup` Skill은 "매일 아침 받은 편지함에서 뉴스레터를 분류하고 중요 메일만 요약하는 방법"을 가르친다.
:::

### Skill 구조

Skill은 `SKILL.md` 파일이 있는 디렉토리다:

```text
skills/
└── my-custom-skill/
    ├── SKILL.md          # 필수: Skill 정의 (YAML frontmatter + 지침)
    ├── templates/        # 선택: 템플릿 파일
    └── examples/         # 선택: 예시 파일
```

`SKILL.md`의 구조:

```markdown
---
name: daily-briefing
version: 1.0.0
description: "매일 아침 일일 브리핑을 생성합니다"
author: "your-name"
tags: ["productivity", "email", "calendar"]
tools: ["gmail", "google-calendar", "web-search"]
---

# Daily Briefing Skill

## 목적
매일 아침 사용자에게 중요한 이메일, 오늘 일정, 주요 뉴스를 요약한 브리핑을 제공한다.

## 절차
1. Gmail에서 최근 12시간 내 수신된 중요 이메일을 검색한다
2. Google Calendar에서 오늘과 내일의 일정을 조회한다
3. 중요도 순으로 정리하여 사용자에게 전달한다

## 응답 형식
```
🌅 오늘의 브리핑 (YYYY-MM-DD)

📧 중요 이메일 (N건)
- [발신자] 제목 - 요약

📅 오늘 일정 (N건)
- HH:MM 일정명

📌 내일 주요 일정
- HH:MM 일정명
```

## 주의사항
- 스팸이나 프로모션 메일은 제외한다
- 사용자의 타임존(KST)을 기준으로 한다
```

### Skills 관리

```bash
# Skills 레지스트리에서 검색
openclaw skills search "obsidian"

# Skill 설치
openclaw skills install obsidian

# 설치된 Skills 목록
openclaw skills list

# Skill 상세 정보
openclaw skills info obsidian

# Skill 제거
openclaw skills remove obsidian
```

### 주요 커뮤니티 Skills

5,400개 이상의 커뮤니티 Skills 중 인기 있는 것들:

| Skill | 설명 |
|-------|------|
| `google-calendar` | Google 캘린더 일정 관리 |
| `gmail` | Gmail 읽기/검색/전송 |
| `obsidian` | Obsidian 노트 정리 |
| `github` | GitHub 레포/이슈/PR 관리 |
| `slack` | Slack 메시지/채널 관리 |
| `spotify` | Spotify 음악 제어 |
| `file-manager` | 파일 시스템 조작 |
| `web-search` | 웹 검색 및 브라우징 |
| `shell-exec` | 셸 명령 실행 |
| `home-assistant` | 스마트홈 기기 제어 |

---

## 플러그인 아키텍처

### Skills vs 플러그인

Skills가 "지침서"라면, 플러그인은 OpenClaw의 **런타임 기능을 확장**하는 코드 모듈이다:

| 구분 | Skills | 플러그인 |
|------|--------|---------|
| 형태 | 마크다운 파일 (SKILL.md) | TypeScript/JavaScript 코드 |
| 역할 | 도구 사용법을 가르침 | 새로운 기능/동작을 추가 |
| 설치 | `openclaw skills install` | `openclaw plugin install` |
| 예시 | "이메일 정리하는 법" | "새로운 채널 어댑터", "커스텀 인증" |

### 플러그인 구조

```text
my-plugin/
├── openclaw.plugin.json    # 플러그인 매니페스트
├── src/
│   └── index.ts            # 메인 진입점
├── skills/                 # 플러그인 전용 Skills (선택)
│   └── my-skill/
│       └── SKILL.md
└── package.json
```

`openclaw.plugin.json` 예시:

```json
{
  "name": "my-custom-plugin",
  "version": "1.0.0",
  "description": "Custom functionality for OpenClaw",
  "main": "src/index.ts",
  "skills": ["skills/my-skill"],
  "hooks": {
    "onMessage": true,
    "onToolCall": true,
    "onResponse": true
  }
}
```

### 훅 시스템

플러그인은 **훅(Hook)**을 통해 메시지 처리 파이프라인의 다양한 지점에 개입할 수 있다:

| 훅 | 실행 시점 | 용도 |
|----|----------|------|
| `onMessage` | 메시지 수신 직후 | 전처리, 필터링, 로깅 |
| `onContext` | 컨텍스트 조립 시 | 추가 컨텍스트 주입 |
| `onToolCall` | 도구 호출 전 | 권한 확인, 감사 로그 |
| `onResponse` | LLM 응답 후 | 후처리, 번역, 포맷팅 |
| `onError` | 에러 발생 시 | 에러 핸들링, 알림 |

---

## Heartbeat과 Cron

### Heartbeat

Heartbeat는 **30분마다** 자동으로 실행되는 배치 모니터링 메커니즘이다. `HEARTBEAT.md`에 정의된 작업을 일괄 처리한다:

```markdown
# Heartbeat Tasks

- [ ] 새 이메일 확인하고 중요한 것만 알림
- [ ] Google Calendar에서 다가오는 일정 확인
- [ ] GitHub 레포에서 새 이슈/PR 확인
- [ ] 서버 상태 모니터링
```

:::tip
HEARTBEAT.md는 토큰 오버헤드를 최소화하기 위해 짧게 유지하는 것이 좋다. 복잡한 작업은 Cron으로 분리한다.
:::

### Cron

Cron은 정확한 일정에 따라 실행되는 예약 작업이다:

```bash
# Cron 작업 추가
openclaw cron add "daily-report" --schedule "0 9 * * *" --prompt "오늘의 일일 리포트를 생성해줘"

# Cron 작업 목록
openclaw cron list

# Cron 작업 삭제
openclaw cron remove "daily-report"
```

### Heartbeat vs Cron 선택 기준

| 질문 | 답변 | 사용할 것 |
|------|------|----------|
| 다른 주기적 체크와 묶을 수 있나? | YES | Heartbeat |
| 정확한 시간에 실행해야 하나? | YES | Cron |
| 하루 1회 이하? | YES | Cron |
| 실시간 모니터링? | YES | Heartbeat |

비용 최적화 팁: Cron 작업에 `isolatedSession: true`를 설정하면 전체 대화 히스토리(약 100K 토큰)를 보내지 않고 2-5K 토큰만으로 실행할 수 있다.

---

## 설정 핫 리로드

OpenClaw Gateway는 `openclaw.json` 파일의 변경을 감지하여 대부분의 설정을 **재시작 없이 반영**한다:

| 설정 | 핫 리로드 | 비고 |
|------|----------|------|
| 모델 변경 | 가능 | 다음 요청부터 적용 |
| 채널 추가/제거 | 가능 | 자동 연결/해제 |
| MCP 서버 추가 | 가능 | 프로세스 자동 스폰 |
| Skills 설치/제거 | 가능 | 즉시 반영 |
| 포트 변경 | 불가 | Gateway 재시작 필요 |
| 환경변수 변경 | 불가 | Gateway 재시작 필요 |

---

## 정리

이 글에서 다룬 핵심 구성요소를 정리한다:

- **Gateway 아키텍처**: TypeScript+Node.js 기반, Channel Adapter - Message Router - Session Manager - Agent Runner - LLM Client로 구성
- **멀티 LLM**: Anthropic, OpenAI, Google, Ollama 등 다양한 프로바이더를 동시에 사용하고 모델 라우팅으로 비용 최적화
- **MCP 도구 시스템**: @modelcontextprotocol/sdk 기반으로 1,000+ 외부 서비스와 네이티브 연동
- **벡터 저장소**: SQLite+sqlite-vec+FTS5 하이브리드 검색으로 local-first 메모리 구현
- **캐릭터 시스템**: SOUL.md, IDENTITY.md, USER.md, AGENTS.md로 다층적 페르소나 정의
- **Skills/플러그인**: 마크다운 기반 Skills(지침서)와 코드 기반 플러그인(런타임 확장)
- **Heartbeat/Cron**: 자동 모니터링과 예약 작업으로 프로액티브 에이전트 구현

다음 글 [[openclaw-guide-03-advanced|OpenClaw 고급 활용]]에서는 커스터마이징과 확장 기능을 다룬다.