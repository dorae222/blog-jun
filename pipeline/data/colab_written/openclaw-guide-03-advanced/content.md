# OpenClaw 고급 활용: 커스터마이징과 확장

## 들어가며

:::info
이 글은 **OpenClaw Guide** 시리즈의 세 번째 글이다. 시리즈 전체 목차:
1. [[openclaw-guide-01-setup|메시징 기반 AI 에이전트]]
2. [[openclaw-guide-02-core|핵심 기능: 아키텍처와 도구 시스템]]
3. **고급 활용: 커스터마이징과 확장** (현재 글)
4. [[openclaw-guide-04-workflow|실전: 자체 호스팅 AI 에이전트 환경]]
:::

이전 글에서 OpenClaw의 아키텍처와 도구 시스템을 분석했다. 이 글에서는 한 단계 더 나아가 **캐릭터 시스템 심층 설정, 커스텀 MCP 서버 개발, 플러그인 개발, 멀티 에이전트 구성, RAG 파이프라인 커스터마이징, 고급 LLM 설정, 보안 강화**까지 OpenClaw를 본격적으로 확장하는 방법을 다룬다.

---

## 캐릭터 시스템 심층

### 페르소나 설계 원칙

효과적인 AI 에이전트 페르소나를 설계하려면 세 가지 계층을 분리해야 한다:

| 계층 | 파일 | 변경 빈도 | 설명 |
|------|------|----------|------|
| 코어 | `SOUL.md` | 거의 없음 | 근본적인 가치관, 사고 방식, 장기 목표 |
| 표면 | `IDENTITY.md` | 드물게 | 이름, 말투, 이모지, 외형적 특성 |
| 컨텍스트 | `USER.md` | 자주 | 사용자 정보, 선호도, 최근 관심사 |
| 규칙 | `AGENTS.md` | 필요 시 | 도구 사용 규칙, 경계선, 권한 |

### SOUL.md 심층 작성

SOUL.md는 에이전트의 가장 깊은 행동 특성을 정의한다. 단순한 시스템 프롬프트를 넘어, 에이전트의 **의사결정 프레임워크**를 구성한다:

```markdown
# Soul

## Core Values
1. 정확성이 속도보다 중요하다 - 확실하지 않으면 반드시 확인한다
2. 사용자의 의도를 파악하는 것이 최우선이다
3. 최소 개입 원칙 - 요청받은 것만 수행하되, 명백한 위험이 있으면 경고한다

## Decision Framework
- 사용자가 파일 삭제를 요청하면: 삭제 전 확인을 구한다
- 외부 API 호출 시: 비용이 발생할 수 있으면 사전에 알린다
- 불확실한 정보: "~로 보입니다만, 확인이 필요합니다"로 표현한다

## Behavioral Patterns
- 복잡한 작업은 단계별로 분리하여 진행 상황을 보고한다
- 오류 발생 시 원인을 먼저 설명하고, 가능한 해결책을 제시한다
- 사용자가 같은 질문을 반복하면 이전 답변을 참조하여 더 상세하게 설명한다

## Anti-patterns (절대 하지 않을 것)
- 추측으로 중요한 결정을 내리지 않는다
- 사용자의 동의 없이 시스템 설정을 변경하지 않는다
- API 키나 비밀번호를 메시지에 포함하지 않는다

## Knowledge Domain
- 전문: 소프트웨어 개발, 클라우드 인프라, 데이터 분석
- 보통: 일반 업무, 문서 작성, 일정 관리
- 약함: 법률 자문, 의료 조언 (이 분야는 전문가 상담을 권장)
```

### 동적 페르소나 전환

OpenClaw의 훅 시스템을 활용하면 시간대나 조건에 따라 페르소나를 동적으로 전환할 수 있다:

```json
{
  "identity": {
    "name": "클로",
    "theme": "professional assistant",
    "schedules": {
      "weekday_work": {
        "hours": "09:00-18:00",
        "days": ["mon", "tue", "wed", "thu", "fri"],
        "soul": "workspace/souls/work-mode.md"
      },
      "evening": {
        "hours": "18:00-23:00",
        "soul": "workspace/souls/casual-mode.md"
      }
    }
  }
}
```

:::tip
SOUL.md의 내용을 시간대별로 전환하면 업무 시간에는 전문적이고 효율적인 어시스턴트로, 저녁에는 캐주얼한 대화 상대로 동작하게 할 수 있다. 이 전환은 메모리 내에서만 이루어지며 디스크의 파일은 수정되지 않는다.
:::

### 스타일 예시 첨부

페르소나에 실제 대화 예시를 첨부하여 말투를 더 정밀하게 제어할 수 있다:

```json
{
  "identity": {
    "name": "클로",
    "style_examples": [
      {
        "user": "오늘 미팅 일정 알려줘",
        "agent": "오늘 미팅 2건 있습니다:\n- 14:00 팀 스탠드업 (30분)\n- 16:00 클라이언트 리뷰 (1시간)\n\n다음 미팅까지 2시간 여유가 있네요."
      },
      {
        "user": "이 코드 뭐가 문제야?",
        "agent": "두 가지 문제를 발견했습니다:\n1. L15: null 체크 누락 - `user?.name` 으로 수정\n2. L23: async 함수에 await 누락\n\n수정 버전을 보내드릴까요?"
      }
    ]
  }
}
```

---

## 커스텀 MCP 서버 개발

### 왜 커스텀 MCP 서버가 필요한가

커뮤니티 MCP 서버가 1,000개 이상 있지만, 사내 시스템이나 커스텀 API에 연동하려면 직접 MCP 서버를 개발해야 한다. OpenClaw가 내부적으로 사용하는 `@modelcontextprotocol/sdk`를 동일하게 활용하므로 개발이 직관적이다.

### 기본 MCP 서버 구조

TypeScript로 커스텀 MCP 서버를 만드는 기본 구조:

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk
npm install typescript tsx -D
```

`tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*"]
}
```

### 예시: 사내 API 연동 MCP 서버

사내 프로젝트 관리 시스템에 연동하는 MCP 서버를 만들어보자:

```typescript
// src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "internal-project-manager",
  version: "1.0.0",
});

// 도구 1: 프로젝트 목록 조회
server.tool(
  "list_projects",
  "사내 프로젝트 목록을 조회합니다",
  {
    status: z.enum(["active", "completed", "all"]).optional()
      .describe("프로젝트 상태 필터"),
  },
  async ({ status }) => {
    const response = await fetch(
      `${process.env.INTERNAL_API_URL}/projects?status=${status || "active"}`,
      {
        headers: {
          Authorization: `Bearer ${process.env.INTERNAL_API_TOKEN}`,
        },
      }
    );
    const projects = await response.json();
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(projects, null, 2),
        },
      ],
    };
  }
);

// 도구 2: 이슈 생성
server.tool(
  "create_issue",
  "프로젝트에 새 이슈를 생성합니다",
  {
    projectId: z.string().describe("프로젝트 ID"),
    title: z.string().describe("이슈 제목"),
    description: z.string().describe("이슈 설명"),
    priority: z.enum(["low", "medium", "high", "critical"])
      .describe("우선순위"),
    assignee: z.string().optional().describe("담당자 이메일"),
  },
  async ({ projectId, title, description, priority, assignee }) => {
    const response = await fetch(
      `${process.env.INTERNAL_API_URL}/projects/${projectId}/issues`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${process.env.INTERNAL_API_TOKEN}`,
        },
        body: JSON.stringify({
          title,
          description,
          priority,
          assignee,
        }),
      }
    );
    const issue = await response.json();
    return {
      content: [
        {
          type: "text",
          text: `이슈가 생성되었습니다: #${issue.id} - ${issue.title}`,
        },
      ],
    };
  }
);

// 도구 3: 프로젝트 상태 대시보드
server.tool(
  "project_dashboard",
  "프로젝트의 전체 상태 대시보드를 조회합니다",
  {
    projectId: z.string().describe("프로젝트 ID"),
  },
  async ({ projectId }) => {
    const [project, issues, members] = await Promise.all([
      fetch(`${process.env.INTERNAL_API_URL}/projects/${projectId}`).then(r => r.json()),
      fetch(`${process.env.INTERNAL_API_URL}/projects/${projectId}/issues`).then(r => r.json()),
      fetch(`${process.env.INTERNAL_API_URL}/projects/${projectId}/members`).then(r => r.json()),
    ]);

    const dashboard = {
      project: project.name,
      status: project.status,
      progress: `${project.completedTasks}/${project.totalTasks}`,
      openIssues: issues.filter((i: any) => i.status === "open").length,
      members: members.length,
      deadline: project.deadline,
    };

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(dashboard, null, 2),
        },
      ],
    };
  }
);

// 서버 시작
const transport = new StdioServerTransport();
await server.connect(transport);
```

### OpenClaw에 커스텀 MCP 서버 등록

개발한 MCP 서버를 OpenClaw에 연결한다:

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "mcp": {
          "servers": [
            {
              "name": "internal-pm",
              "command": "npx",
              "args": ["tsx", "/path/to/my-mcp-server/src/index.ts"],
              "env": {
                "INTERNAL_API_URL": "https://pm.internal.company.com/api",
                "INTERNAL_API_TOKEN": "$INTERNAL_API_TOKEN"
              }
            }
          ]
        }
      }
    ]
  }
}
```

이제 메시징 앱에서 자연어로 사내 시스템을 조회하고 조작할 수 있다:

```text
사용자: 현재 진행 중인 프로젝트 목록 보여줘
봇: 현재 활성 프로젝트 3건입니다:
    1. 블로그 리팩토링 (진행률 75%)
    2. 모바일 앱 v2.0 (진행률 30%)
    3. 데이터 파이프라인 (진행률 90%)

사용자: 블로그 리팩토링에 "검색 기능 개선" 이슈 만들어줘. 우선순위 높음
봇: 이슈가 생성되었습니다: #142 - 검색 기능 개선 (우선순위: high)
    담당자를 지정할까요?
```

---

## 플러그인 개발

### 플러그인 개발 환경 설정

```bash
mkdir openclaw-plugin-myfeature && cd openclaw-plugin-myfeature
npm init -y
npm install @openclaw/plugin-sdk typescript -D
```

### 메시지 필터링 플러그인 예시

수신 메시지를 전처리하는 플러그인을 만들어보자. 예를 들어 특정 키워드가 포함된 메시지를 자동 분류하는 기능이다:

`openclaw.plugin.json`:

```json
{
  "name": "message-classifier",
  "version": "1.0.0",
  "description": "메시지를 키워드 기반으로 자동 분류하고 태그를 추가합니다",
  "main": "src/index.ts",
  "hooks": {
    "onMessage": true,
    "onResponse": true
  },
  "config": {
    "rules": {
      "type": "array",
      "description": "분류 규칙 목록"
    }
  }
}
```

`src/index.ts`:

```typescript
import { OpenClawPlugin, MessageHook, ResponseHook } from "@openclaw/plugin-sdk";

interface ClassificationRule {
  keywords: string[];
  tag: string;
  priority: "low" | "medium" | "high";
  autoReply?: string;
}

const defaultRules: ClassificationRule[] = [
  {
    keywords: ["긴급", "urgent", "ASAP"],
    tag: "urgent",
    priority: "high",
  },
  {
    keywords: ["보고서", "리포트", "report"],
    tag: "report",
    priority: "medium",
  },
  {
    keywords: ["회의", "미팅", "meeting"],
    tag: "meeting",
    priority: "medium",
  },
];

export default class MessageClassifier implements OpenClawPlugin {
  private rules: ClassificationRule[];

  constructor(config: { rules?: ClassificationRule[] }) {
    this.rules = config.rules || defaultRules;
  }

  onMessage: MessageHook = async (message, context) => {
    const content = message.content.toLowerCase();
    const matchedRules = this.rules.filter((rule) =>
      rule.keywords.some((kw) => content.includes(kw.toLowerCase()))
    );

    if (matchedRules.length > 0) {
      // 매칭된 태그를 메시지 메타데이터에 추가
      message.metadata = {
        ...message.metadata,
        tags: matchedRules.map((r) => r.tag),
        maxPriority: matchedRules.reduce(
          (max, r) =>
            r.priority === "high" ? "high" :
            r.priority === "medium" && max !== "high" ? "medium" : max,
          "low" as string
        ),
      };

      // 에이전트 컨텍스트에 분류 정보 추가
      context.appendSystemMessage(
        `[분류 정보] 이 메시지는 다음 태그로 분류되었습니다: ` +
        `${matchedRules.map((r) => r.tag).join(", ")}. ` +
        `최고 우선순위: ${message.metadata.maxPriority}`
      );
    }

    return message; // 수정된 메시지 반환
  };

  onResponse: ResponseHook = async (response, context) => {
    // 긴급 태그가 있는 메시지에 대한 응답에 알림 추가
    if (context.message.metadata?.maxPriority === "high") {
      response.content = `⚠️ [긴급]\n\n${response.content}`;
    }
    return response;
  };
}
```

### 플러그인 설치 및 활성화

```bash
# 로컬 플러그인 설치
openclaw plugin install ./openclaw-plugin-myfeature

# 또는 npm 레지스트리에서 설치
openclaw plugin install openclaw-plugin-message-classifier

# 활성 플러그인 확인
openclaw plugin list
```

`openclaw.json`에서 플러그인 설정:

```json
{
  "plugins": {
    "message-classifier": {
      "enabled": true,
      "config": {
        "rules": [
          {
            "keywords": ["장애", "서버다운", "에러"],
            "tag": "incident",
            "priority": "high"
          },
          {
            "keywords": ["배포", "릴리즈", "deploy"],
            "tag": "deployment",
            "priority": "medium"
          }
        ]
      }
    }
  }
}
```

---

## 멀티 에이전트 설정

### 멀티 에이전트 아키텍처

OpenClaw는 하나의 Gateway에서 **여러 독립적인 에이전트**를 실행할 수 있다. 각 에이전트는 자체적인 워크스페이스, 메모리, 세션, 도구 권한을 가진다.

```text
┌─────────────────────────────────────┐
│            Gateway Server            │
│                                      │
│  ┌─────────┐  ┌─────────┐          │
│  │ Agent A │  │ Agent B │  ...     │
│  │ (개인)  │  │ (업무)  │          │
│  ├─────────┤  ├─────────┤          │
│  │ Soul A  │  │ Soul B  │          │
│  │ Memory A│  │ Memory B│          │
│  │ Tools A │  │ Tools B │          │
│  └────┬────┘  └────┬────┘          │
│       │             │                │
│  Telegram      Discord/Slack        │
│  (개인)        (팀 채널)            │
└─────────────────────────────────────┘
```

### 멀티 에이전트 설정

`openclaw.json`에서 여러 에이전트를 정의한다:

```json
{
  "agents": {
    "list": [
      {
        "id": "personal",
        "name": "클로 (개인)",
        "workspace": "~/.openclaw/agents/personal/workspace",
        "model": "anthropic/claude-sonnet-4.5",
        "mcp": {
          "servers": [
            { "name": "gmail", "command": "npx", "args": ["-y", "@anthropic/mcp-google"] },
            { "name": "calendar", "command": "npx", "args": ["-y", "@anthropic/mcp-gcal"] }
          ]
        }
      },
      {
        "id": "devops",
        "name": "클로 (DevOps)",
        "workspace": "~/.openclaw/agents/devops/workspace",
        "model": "openai/gpt-4.1",
        "mcp": {
          "servers": [
            { "name": "github", "command": "npx", "args": ["-y", "@anthropic/mcp-github"] },
            { "name": "shell", "command": "npx", "args": ["-y", "@anthropic/mcp-shell"] }
          ]
        }
      },
      {
        "id": "support",
        "name": "클로 (고객지원)",
        "workspace": "~/.openclaw/agents/support/workspace",
        "model": "anthropic/claude-haiku-4.5",
        "mcp": {
          "servers": [
            { "name": "notion", "command": "npx", "args": ["-y", "@notionhq/mcp"] }
          ]
        }
      }
    ]
  }
}
```

### 바인딩 설정

바인딩은 수신 메시지를 어떤 에이전트로 라우팅할지 결정한다:

```json
{
  "agents": {
    "bindings": [
      {
        "agentId": "personal",
        "channel": "telegram",
        "accountId": "my-telegram-bot",
        "peer": "my_username"
      },
      {
        "agentId": "devops",
        "channel": "discord",
        "accountId": "devops-bot",
        "guildId": "123456789"
      },
      {
        "agentId": "support",
        "channel": "slack",
        "accountId": "support-bot",
        "channelId": "C0SUPPORT01"
      }
    ]
  }
}
```

```bash
# 바인딩 확인
openclaw agents list --bindings
```

```output
Agents:
  personal  → telegram/my-telegram-bot (peer: my_username)
  devops    → discord/devops-bot (guild: 123456789)
  support   → slack/support-bot (channel: C0SUPPORT01)
```

:::warning
멀티 에이전트 설정에서 가장 중요한 것은 **격리**다. 고객지원 채널의 데이터가 개인 에이전트로 유출되거나, 팀 봇이 셸 접근 권한을 갖지 않도록 워크스페이스와 도구 권한을 분리해야 한다.
:::

### 에이전트 간 통신

필요한 경우 에이전트 간 메시지를 전달할 수 있다. 예를 들어 고객지원 에이전트가 기술적 문제를 감지하면 DevOps 에이전트에게 알림을 보내는 구성:

```json
{
  "agents": {
    "routing": {
      "escalation": {
        "from": "support",
        "to": "devops",
        "triggers": ["서버 장애", "배포 실패", "API 오류"]
      }
    }
  }
}
```

---

## RAG 파이프라인 커스터마이징

### 임베딩 모델 변경

기본 임베딩 모델 외에 다른 모델을 사용할 수 있다:

```json
{
  "memory": {
    "embeddingModel": "openai/text-embedding-3-large",
    "embeddingDimensions": 3072
  }
}
```

로컬 임베딩 모델을 사용하면 API 비용을 절감할 수 있다:

```json
{
  "memory": {
    "embeddingModel": "ollama/nomic-embed-text",
    "embeddingDimensions": 768,
    "embeddingEndpoint": "http://localhost:11434"
  }
}
```

### 청킹 전략 조정

문서의 특성에 따라 청킹 전략을 조정한다:

```json
{
  "memory": {
    "chunking": {
      "strategy": "markdown",
      "chunkSize": 512,
      "chunkOverlap": 50,
      "respectHeaders": true,
      "minChunkSize": 100
    }
  }
}
```

| 전략 | 설명 | 적합한 문서 |
|------|------|------------|
| `markdown` | 마크다운 헤더 기반 분할 | 구조화된 문서, 기술 문서 |
| `paragraph` | 단락 기반 분할 | 자유 형식 텍스트, 에세이 |
| `fixed` | 고정 크기 분할 | 로그 파일, 코드 |
| `semantic` | 의미 단위 분할 | 대화 기록, Q&A |

### 검색 가중치 튜닝

하이브리드 검색의 가중치를 용도에 맞게 조정한다:

```json
{
  "memory": {
    "searchWeights": {
      "vector": 0.6,
      "keyword": 0.4
    },
    "reranking": {
      "enabled": true,
      "model": "cross-encoder",
      "topK": 20,
      "finalK": 5
    }
  }
}
```

:::tip
기술 문서가 많은 워크스페이스에서는 키워드 검색 가중치를 높이는 것이 좋다. "Kubernetes", "Docker", "nginx" 같은 고유명사는 벡터 유사도보다 정확한 키워드 매칭이 효과적이다.
:::

### 커스텀 인덱싱 파이프라인

특정 소스에서 자동으로 지식을 수집하여 인덱싱하는 파이프라인을 구성할 수 있다:

```json
{
  "memory": {
    "sources": [
      {
        "type": "directory",
        "path": "workspace/notes/**/*.md",
        "autoSync": true
      },
      {
        "type": "notion",
        "databaseId": "abc123",
        "syncInterval": "1h"
      },
      {
        "type": "confluence",
        "spaceKey": "TEAM",
        "syncInterval": "4h"
      }
    ]
  }
}
```

---

## 고급 LLM 설정

### 모델별 파라미터 튜닝

각 모델의 생성 파라미터를 세밀하게 조정할 수 있다:

```json
{
  "models": {
    "providers": {
      "anthropic": {
        "models": [
          {
            "id": "claude-sonnet-4.5",
            "parameters": {
              "temperature": 0.7,
              "maxTokens": 8192,
              "topP": 0.9,
              "stopSequences": []
            }
          }
        ]
      }
    }
  }
}
```

| 파라미터 | 범위 | 용도 |
|---------|------|------|
| `temperature` | 0.0 - 2.0 | 응답의 다양성 (0=결정적, 높을수록 창의적) |
| `maxTokens` | 1 - 모델 한계 | 응답 최대 길이 |
| `topP` | 0.0 - 1.0 | 핵 샘플링 (temperature와 함께 조정) |
| `stopSequences` | 문자열 배열 | 응답 중단 트리거 |

### 용도별 최적 설정

| 용도 | temperature | maxTokens | 추천 모델 |
|------|------------|-----------|----------|
| 정확한 정보 조회 | 0.0 - 0.3 | 2048 | Haiku, GPT-4.1-mini |
| 일반 대화 | 0.5 - 0.7 | 4096 | Sonnet, GPT-4.1 |
| 창의적 글쓰기 | 0.8 - 1.0 | 8192 | Opus, GPT-4.1 |
| 코드 생성 | 0.0 - 0.2 | 8192 | Sonnet, GPT-4.1 |
| 요약/분석 | 0.3 - 0.5 | 4096 | Sonnet, Gemini Pro |

### 컨텍스트 윈도우 관리

긴 대화에서 컨텍스트 윈도우를 효율적으로 관리하는 설정:

```json
{
  "session": {
    "maxHistoryTokens": 50000,
    "compactionStrategy": "summarize",
    "compactionThreshold": 0.8,
    "keepSystemPrompt": true,
    "keepRecentTurns": 10
  }
}
```

- `compactionThreshold`: 컨텍스트 윈도우의 80%가 차면 압축 실행
- `compactionStrategy`:
  - `"summarize"`: 이전 대화를 요약하여 압축
  - `"truncate"`: 오래된 대화를 삭제
  - `"sliding"`: 슬라이딩 윈도우 방식

### 폴백(Fallback) 설정

주 모델이 실패했을 때 자동으로 다른 모델로 전환하는 설정:

```json
{
  "models": {
    "default": "anthropic/claude-sonnet-4.5",
    "fallback": [
      "openai/gpt-4.1",
      "ollama/llama3.3"
    ],
    "retryPolicy": {
      "maxRetries": 3,
      "retryDelay": 1000,
      "exponentialBackoff": true
    }
  }
}
```

:::info
폴백 체인은 순서대로 시도된다. 클라우드 API의 rate limit에 걸렸을 때 로컬 모델로 자동 전환되도록 설정하면, 서비스 중단 없이 에이전트를 운영할 수 있다.
:::

---

## 보안 설정

### 접근 제어

메시징 채널별로 세밀한 접근 제어를 설정한다:

```json
{
  "channels": {
    "telegram": {
      "allowFrom": ["user1", "user2"],
      "denyFrom": ["spammer1"],
      "rateLimit": {
        "messagesPerMinute": 10,
        "messagesPerHour": 100
      }
    },
    "discord": {
      "allowGuilds": ["guild-id-1"],
      "allowChannels": ["channel-id-1"],
      "allowRoles": ["admin", "team-lead"]
    }
  }
}
```

### 도구 권한 관리

에이전트별로 사용 가능한 도구를 제한한다:

```json
{
  "agents": {
    "list": [
      {
        "id": "support",
        "tools": {
          "allow": ["notion.*", "gmail.read", "gmail.search"],
          "deny": ["shell.*", "filesystem.write", "gmail.send"]
        }
      }
    ]
  }
}
```

| 권한 패턴 | 설명 |
|-----------|------|
| `notion.*` | Notion의 모든 도구 허용 |
| `gmail.read` | Gmail 읽기만 허용 |
| `shell.*` | 셸 명령 전체 차단 (deny에 설정) |
| `filesystem.write` | 파일 쓰기 차단 |

### 비밀 관리

API 키와 토큰을 안전하게 관리하는 방법:

```bash
# .env 파일에 직접 저장 (기본)
ANTHROPIC_API_KEY=sk-ant-...

# SecretRef 시스템 (공유 환경 권장)
openclaw secrets set ANTHROPIC_API_KEY "sk-ant-..."
openclaw secrets set INTERNAL_API_TOKEN "token-..."
```

:::warning
`~/.openclaw/` 디렉토리에는 API 키와 OAuth 토큰이 평문으로 저장된다. 백업 시 반드시 암호화해야 하며, 공유 서버에서는 파일 권한을 `600`으로 설정해야 한다.
:::

```bash
# 파일 권한 설정
chmod 600 ~/.openclaw/.env
chmod 600 ~/.openclaw/openclaw.json
chmod -R 700 ~/.openclaw/
```

### 네트워크 보안

Docker 환경에서의 네트워크 격리:

```yaml
# docker-compose.yml
services:
  openclaw:
    networks:
      - openclaw-net
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    volumes:
      - openclaw-data:/home/node/.openclaw

networks:
  openclaw-net:
    driver: bridge
    internal: false  # 외부 API 접근 필요
```

### 감사 로그

모든 도구 호출과 외부 API 접근을 로깅한다:

```json
{
  "logging": {
    "level": "info",
    "audit": {
      "enabled": true,
      "logToolCalls": true,
      "logApiRequests": true,
      "logFileAccess": true,
      "outputPath": "~/.openclaw/logs/audit.jsonl"
    }
  }
}
```

감사 로그 예시:

```json
{
  "timestamp": "2026-03-28T10:30:00.000Z",
  "agentId": "support",
  "action": "tool_call",
  "tool": "notion.search_pages",
  "params": {"query": "회의록"},
  "result": "success",
  "duration": 450,
  "channel": "slack",
  "userId": "U0USER01"
}
```

---

## 정리

이 글에서 다룬 고급 활용 기법을 정리한다:

- **캐릭터 시스템 심층**: SOUL.md의 의사결정 프레임워크, 동적 페르소나 전환, 스타일 예시로 정밀한 에이전트 성격 제어
- **커스텀 MCP 서버**: @modelcontextprotocol/sdk로 사내 시스템 연동 MCP 서버 개발
- **플러그인 개발**: 훅 시스템을 활용한 메시지 전처리/후처리 플러그인
- **멀티 에이전트**: 독립적인 워크스페이스, 메모리, 권한을 가진 여러 에이전트를 하나의 Gateway에서 운영
- **RAG 커스터마이징**: 임베딩 모델 변경, 청킹 전략 조정, 하이브리드 검색 가중치 튜닝
- **고급 LLM 설정**: 모델별 파라미터 튜닝, 컨텍스트 관리, 폴백 체인
- **보안**: 접근 제어, 도구 권한 관리, 비밀 관리, 감사 로그

다음 글 [[openclaw-guide-04-workflow|OpenClaw 실전]]에서는 자체 호스팅 환경 구축을 다룬다.