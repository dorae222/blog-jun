# Claude Code 고급 활용: MCP 서버와 서브에이전트

## 들어가며

:::info
이 글은 **Claude Code Guide** 시리즈의 세 번째 글로, MCP 서버와 서브에이전트 등 고급 기능을 다룬다. 시리즈 전체 목차는 다음과 같다:
1. [[claude-code-guide-01-setup|설치와 기본 사용법]]
2. [[claude-code-guide-02-core|핵심 기능: 도구 시스템과 에이전틱 루프]]
3. **고급 활용: MCP 서버와 서브에이전트** (현재 글)
4. [[claude-code-guide-04-workflow|실전: 프로젝트 관리와 워크플로우]]
5. [[claude-code-guide-05-comparison|AI 코딩 에이전트 비교]]
:::

이전 글에서 Claude Code의 도구 시스템과 에이전틱 루프를 살펴보았다. 이번 글에서는 한 단계 더 나아가, **MCP 서버로 도구를 확장**하고, **서브에이전트로 작업을 병렬화**하며, **Hooks로 자동화 파이프라인을 구축**하는 고급 기능을 다룬다.

기본 도구만으로도 대부분의 코딩 작업을 수행할 수 있지만, MCP 서버를 연동하면 GitHub PR 관리, Slack 알림, 데이터베이스 쿼리 같은 외부 서비스와의 통합이 가능해진다. 서브에이전트를 활용하면 코드 리뷰, 테스트 작성, 문서 업데이트를 동시에 처리할 수 있다. 이 고급 기능들을 조합하면 Claude Code는 단순한 코딩 도구를 넘어, **개발 워크플로우 전체를 오케스트레이션하는 플랫폼**이 된다.

---

## 1. MCP (Model Context Protocol) 서버 연동

### MCP란?

**MCP(Model Context Protocol)**는 Claude Code의 도구를 확장하는 표준 프로토콜이다. Claude Code에 내장된 도구(Read, Edit, Bash 등)는 로컬 파일시스템과 셸에 한정되지만, MCP 서버를 연동하면 **외부 서비스와의 통합**이 가능해진다.

MCP 서버는 JSON-RPC 기반의 경량 프로세스로, Claude Code가 필요할 때 자동으로 시작하고 도구 목록을 노출한다. Claude Code는 이 도구들을 내장 도구와 동일하게 사용할 수 있다.

```text
Claude Code ← JSON-RPC → MCP 서버 ← API → 외부 서비스
                                          (GitHub, Slack, DB...)
```

### 설정 방법

MCP 서버는 `.claude/settings.json` 파일에서 `mcpServers` 섹션에 설정한다.

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

각 필드의 의미는 다음과 같다:

| 필드 | 설명 |
|------|------|
| `command` | MCP 서버를 실행할 명령어 |
| `args` | 명령어에 전달할 인자 배열 |
| `env` | 환경변수 (API 토큰 등) |

MCP 서버가 정상적으로 설정되면, Claude Code 시작 시 자동으로 해당 프로세스를 기동하고 사용 가능한 도구 목록을 로드한다.

### 스코프: Project vs User 레벨

MCP 서버 설정은 두 가지 스코프에서 관리할 수 있다:

| 스코프 | 설정 위치 | 적용 범위 |
|--------|-----------|-----------|
| **Project** | `프로젝트/.claude/settings.json` | 해당 프로젝트에서만 |
| **User** | `~/.claude/settings.json` | 모든 프로젝트 |

프로젝트별로 다른 MCP 서버가 필요한 경우 Project 레벨을 사용하고, 모든 프로젝트에서 공통으로 사용할 서버는 User 레벨에 설정한다.

```json
// ~/.claude/settings.json (User 레벨 - 전역)
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-..."
      }
    }
  }
}
```

```json
// 프로젝트/.claude/settings.json (Project 레벨)
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/mydb"
      }
    }
  }
}
```

:::tip
보안상 민감한 토큰(GITHUB_TOKEN, SLACK_BOT_TOKEN 등)은 User 레벨에 설정하고, `.gitignore`에 `~/.claude/settings.json`이 포함되어 있는지 확인한다. Project 레벨 설정 파일이 Git에 커밋되면 토큰이 노출될 수 있다.
:::

### 대표적인 MCP 서버

MCP 생태계에는 다양한 공식/커뮤니티 서버가 존재한다. 대표적인 서버들을 정리하면 다음과 같다:

| MCP 서버 | 패키지 | 주요 기능 |
|----------|--------|-----------|
| **GitHub** | `@modelcontextprotocol/server-github` | PR 생성/리뷰, Issue 관리, 코드 검색 |
| **Slack** | `@modelcontextprotocol/server-slack` | 채널 메시지 읽기/보내기, 스레드 관리 |
| **Google Drive** | `@modelcontextprotocol/server-gdrive` | 문서/스프레드시트 접근, 파일 검색 |
| **PostgreSQL** | `@modelcontextprotocol/server-postgres` | SQL 쿼리 실행, 스키마 탐색 |
| **SQLite** | `@modelcontextprotocol/server-sqlite` | 로컬 SQLite DB 쿼리 |
| **Puppeteer** | `@modelcontextprotocol/server-puppeteer` | 브라우저 자동화, 스크린샷, 페이지 탐색 |
| **Sentry** | `@modelcontextprotocol/server-sentry` | 에러 이벤트 조회, 이슈 분석 |
| **Filesystem** | `@modelcontextprotocol/server-filesystem` | 샌드박스 외부 파일 접근 |

여러 MCP 서버를 동시에 설정할 수 있으며, Claude Code는 작업 맥락에 따라 적절한 MCP 도구를 자동으로 선택한다.

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_..." }
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": { "SLACK_BOT_TOKEN": "xoxb-..." }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": { "DATABASE_URL": "postgresql://..." }
    }
  }
}
```

### MCP 리소스 접근

MCP 서버는 도구(Tools) 외에 **리소스(Resources)**도 노출할 수 있다. 리소스는 읽기 전용 데이터로, Claude Code에서 `ReadMcpResource` 도구를 통해 접근한다.

예를 들어, PostgreSQL MCP 서버가 테이블 스키마를 리소스로 노출하면:

```text
> 데이터베이스의 users 테이블 스키마를 확인해줘
```

Claude Code는 `mcp__postgres__ReadResource`를 호출하여 스키마 정보를 가져온다. 이를 통해 직접 쿼리를 실행하지 않고도 데이터베이스 구조를 파악할 수 있다.

### 실전 예시: GitHub MCP로 PR 리뷰 자동화

GitHub MCP 서버를 연동하면 Claude Code에서 직접 PR을 관리할 수 있다. 다음은 PR 리뷰를 자동화하는 실전 워크플로우다.

**1단계: GitHub MCP 설정**

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

**2단계: PR 목록 확인 및 리뷰**

```text
> 현재 열린 PR 목록을 보여줘
```

Claude Code가 GitHub MCP 도구를 사용하여 PR 목록을 조회한다.

```text
> PR #42의 변경 사항을 리뷰하고, 코드 품질 이슈가 있으면 리뷰 코멘트를 남겨줘
```

Claude Code는:
1. GitHub MCP로 PR #42의 diff를 가져옴
2. 변경된 파일들을 분석
3. 코드 품질 이슈 탐지 (타입 오류, 보안 취약점, 성능 문제 등)
4. GitHub MCP로 라인별 리뷰 코멘트 작성

:::info
GitHub MCP 없이도 Claude Code에 내장된 `gh` CLI 도구로 PR을 관리할 수 있다. MCP의 장점은 Claude Code가 도구를 자동으로 인식하고, 별도의 CLI 명령어 없이 자연어로 조작할 수 있다는 점이다.
:::

---

## 2. 서브에이전트 (Agent Tool)

### 서브에이전트란?

서브에이전트는 **메인 대화에서 독립적인 작업을 위임하는 하위 에이전트**다. 메인 Claude Code 세션은 대화의 흐름을 유지하면서, 복잡한 하위 작업을 서브에이전트에 맡길 수 있다.

서브에이전트는 독자적인 컨텍스트 윈도우를 가지며, 메인 세션과 별도로 도구를 실행한다. 이를 통해 메인 컨텍스트 윈도우를 깔끔하게 유지하면서 동시에 여러 작업을 처리할 수 있다.

```text
메인 세션
├── 서브에이전트 A: 코드 리뷰 (포그라운드)
├── 서브에이전트 B: 테스트 작성 (백그라운드)
└── 서브에이전트 C: 문서 업데이트 (백그라운드)
```

### 사용 가능한 에이전트 타입

Claude Code에서 사용할 수 있는 서브에이전트 타입은 다음과 같다:

| 에이전트 타입 | 용도 | 도구 접근 |
|--------------|------|-----------|
| `general-purpose` | 범용 작업 수행 | 모든 도구 사용 가능 |
| `Explore` | 코드베이스 탐색 전문 | Read, Grep, Glob 등 탐색 도구 |
| `Plan` | 아키텍처 설계/계획 수립 | 탐색 도구 + 분석 기능 |
| `claude-code-guide` | Claude Code 관련 질문 응답 | 내장 지식 |

**Explore 에이전트**는 탐색 깊이를 조절할 수 있다:
- `quick` - 빠른 탐색 (파일 구조 파악 수준)
- `medium` - 중간 수준 (주요 파일 내용 확인)
- `very thorough` - 심층 탐색 (관련 코드 전체 분석)

```text
> 이 프로젝트의 인증 시스템을 very thorough 수준으로 분석해줘
```

### 포그라운드 vs 백그라운드 실행

서브에이전트는 두 가지 실행 모드를 지원한다:

**포그라운드 (동기 실행)**: 서브에이전트의 결과가 메인 작업에 필요할 때 사용한다. 메인 세션은 서브에이전트가 완료될 때까지 대기한다.

```text
> API 엔드포인트 목록을 조사하고, 그 결과를 바탕으로 테스트 계획을 세워줘
```

이 경우 Claude Code는 먼저 Explore 서브에이전트를 포그라운드로 실행하여 API 목록을 파악한 뒤, 그 결과를 기반으로 테스트 계획을 수립한다.

**백그라운드 (비동기 실행)**: 메인 작업과 독립적인 작업을 병렬로 처리할 때 사용한다. 서브에이전트가 완료되면 알림이 표시된다.

```text
> 백그라운드에서 전체 테스트를 실행하면서, 나는 새 기능 코드를 리뷰할게
```

백그라운드 서브에이전트는 메인 세션을 차단하지 않으므로, 사용자는 다른 대화를 이어갈 수 있다.

| 실행 모드 | 결과 반환 | 메인 세션 차단 | 사용 시점 |
|-----------|-----------|---------------|-----------|
| 포그라운드 | 즉시 | O | 결과가 다음 작업에 필요할 때 |
| 백그라운드 | 완료 시 알림 | X | 독립적인 병렬 작업 |

### Worktree 격리

서브에이전트는 `isolation: "worktree"` 옵션으로 **별도의 Git worktree에서 작업**할 수 있다. 이는 메인 작업 디렉토리를 건드리지 않고 독립적으로 코드를 수정해야 할 때 유용하다.

```text
메인 worktree: /project (현재 작업 중)
서브에이전트 worktree: /project-worktree-abc123 (격리된 복사본)
```

worktree 격리의 장점:
- 메인 작업 디렉토리의 변경 사항과 충돌하지 않음
- 서브에이전트가 실험적인 코드 변경을 안전하게 시도 가능
- 실패 시 worktree를 삭제하면 원본에 영향 없음
- 결과가 만족스러우면 Git merge로 통합

:::warning
worktree 격리는 Git 리포지토리에서만 작동한다. Git이 초기화되지 않은 디렉토리에서는 사용할 수 없다. 또한 worktree에서 작업하는 서브에이전트는 메인 브랜치의 최신 변경 사항을 자동으로 반영하지 않으므로, 장시간 격리된 작업 후에는 merge conflict에 주의해야 한다.
:::

### 병렬 서브에이전트

여러 서브에이전트를 동시에 실행하면 작업 시간을 크게 단축할 수 있다. Claude Code는 독립적인 작업을 자동으로 병렬화하거나, 사용자가 명시적으로 병렬 실행을 요청할 수 있다.

```text
> 다음 세 가지 작업을 병렬로 수행해줘:
> 1. backend/views.py의 코드 품질 리뷰
> 2. 누락된 단위 테스트 작성
> 3. API 문서 업데이트
```

Claude Code는 세 개의 서브에이전트를 동시에 시작한다:

```text
[서브에이전트 A] 코드 리뷰 진행 중...
[서브에이전트 B] 테스트 작성 중...
[서브에이전트 C] 문서 업데이트 중...
```

세 에이전트가 모두 완료되면 각각의 결과를 종합하여 보고한다.

### 실전 예시: 3개 서브에이전트로 코드 리뷰, 테스트, 문서 병렬 수행

실제 프로젝트에서 새 기능을 구현한 후 품질 검증을 병렬로 수행하는 시나리오를 살펴보자.

```text
> 방금 구현한 사용자 인증 모듈에 대해 다음을 병렬로 수행해줘:
> 1. 보안 관점에서 코드 리뷰 (SQL 인젝션, XSS, CSRF 등)
> 2. pytest 기반 단위 테스트 작성 (정상/비정상 케이스)
> 3. API 문서(README의 API 섹션) 업데이트
```

Claude Code의 실행 흐름:

1. **서브에이전트 A (코드 리뷰)**: `Explore` 타입으로 인증 관련 코드를 탐색하고, 보안 취약점을 분석하여 리포트 생성
2. **서브에이전트 B (테스트 작성)**: `general-purpose` 타입으로 테스트 파일 생성, 정상 로그인/로그아웃, 잘못된 비밀번호, 토큰 만료 등 케이스 작성
3. **서브에이전트 C (문서 업데이트)**: `general-purpose` 타입으로 기존 README를 읽고, API 엔드포인트 문서를 업데이트

세 작업은 동시에 진행되며, 약 2-3분 내에 모든 결과가 반환된다. 순차 실행이었다면 6-9분이 걸렸을 작업이다.

:::tip
서브에이전트를 효과적으로 활용하는 핵심 원칙: **하나의 서브에이전트에는 하나의 작업만 할당**한다. 여러 작업을 하나의 서브에이전트에 맡기면 컨텍스트가 혼잡해지고 품질이 떨어진다.
:::

---

## 3. Hooks 시스템

### Hooks란?

Hooks는 **특정 이벤트에 자동으로 실행되는 셸 명령**이다. Claude Code가 도구를 실행하기 전/후, 응답을 완료할 때 등 특정 시점에 사용자가 정의한 스크립트를 자동으로 트리거한다.

Hooks를 활용하면 다음과 같은 자동화가 가능하다:
- 파일 수정 후 자동 린트
- 민감 파일 수정 시도 차단
- 작업 완료 시 Slack 알림 전송
- 서브에이전트 완료 시 결과 로깅

### 설정 위치

Hooks는 `.claude/settings.json`의 `hooks` 섹션에 정의한다:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/pre-edit-check.sh $TOOL_INPUT"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npx eslint --fix $FILEPATH"
          }
        ]
      }
    ]
  }
}
```

### 이벤트 타입

Claude Code에서 지원하는 Hook 이벤트는 다음과 같다:

| 이벤트 | 발생 시점 | 주요 용도 |
|--------|-----------|-----------|
| `PreToolUse` | 도구 실행 **전** | 검증, 차단, 입력 변환 |
| `PostToolUse` | 도구 실행 **후** | 후처리, 린트, 포맷팅 |
| `Notification` | 알림 발생 시 | 외부 알림 전송 |
| `Stop` | 응답 완료 시 | 결과 로깅, 알림 |
| `SubagentStop` | 서브에이전트 완료 시 | 결과 수집, 후속 작업 |

**matcher** 필드로 특정 도구에만 Hook을 적용할 수 있다. 예를 들어 `"matcher": "Edit"`은 Edit 도구가 호출될 때만 해당 Hook이 실행된다. matcher를 생략하면 모든 도구에 적용된다.

### Hook 응답 형식

`PreToolUse` Hook은 JSON 형식의 stdout을 반환하여 도구 실행을 제어할 수 있다:

```json
{
  "decision": "block",
  "reason": ".env 파일 수정은 허용되지 않습니다."
}
```

| decision 값 | 동작 |
|-------------|------|
| `"approve"` | 도구 실행을 허용 |
| `"block"` | 도구 실행을 차단 (reason이 Claude에게 전달됨) |
| `"ask"` | 사용자에게 확인 요청 |
| (없음) | 기본 동작 (사용자 권한 설정에 따름) |

`PostToolUse` Hook은 실행 결과만 반환하면 되며, 별도의 decision 필드는 필요 없다.

### 실전 예시 1: Edit 후 ESLint 자동 실행

파일을 수정할 때마다 ESLint를 자동으로 실행하여 코드 스타일을 유지하는 설정이다:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npx eslint --fix \"$FILEPATH\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

Claude Code가 Edit 도구로 파일을 수정할 때마다, 자동으로 ESLint가 해당 파일을 검사하고 자동 수정 가능한 문제를 수정한다.

### 실전 예시 2: 민감 파일 수정 차단

`.env`, `credentials.json` 같은 민감 파일의 수정을 차단하는 Hook이다:

먼저 Hook 스크립트를 작성한다:

```bash
#!/bin/bash
# .claude/hooks/block-sensitive.sh

FILEPATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // empty')

SENSITIVE_PATTERNS=(
  ".env"
  "credentials"
  "secrets"
  ".pem"
  ".key"
)

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
  if [[ "$FILEPATH" == *"$pattern"* ]]; then
    echo "{\"decision\": \"block\", \"reason\": \"민감 파일 수정 차단: $FILEPATH\"}"
    exit 0
  fi
done
```

설정 파일에 등록:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/block-sensitive.sh"
          }
        ]
      }
    ]
  }
}
```

이제 Claude Code가 `.env` 파일을 수정하려고 하면 Hook이 차단하고 이유를 Claude에게 전달한다. Claude는 이 피드백을 받고 다른 방법을 시도한다.

### 실전 예시 3: 작업 완료 시 Slack 알림

장시간 작업이 완료되면 Slack으로 알림을 보내는 설정이다:

```bash
#!/bin/bash
# .claude/hooks/notify-slack.sh

curl -X POST "$SLACK_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Claude Code 작업 완료: $(pwd)\"}"
```

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/notify-slack.sh"
          }
        ]
      }
    ]
  }
}
```

:::tip
Hooks는 **파이프라인의 관문** 역할을 한다. PreToolUse로 위험한 작업을 사전 차단하고, PostToolUse로 품질을 자동 검증하며, Stop/Notification으로 결과를 알리는 3단계 자동화를 구축하면 안전하고 효율적인 개발 환경을 만들 수 있다.
:::

---

## 4. 메모리 시스템

### 메모리란?

Claude Code의 메모리 시스템은 **세션 간 정보를 유지**하는 기능이다. 일반적인 AI 채팅은 세션이 끝나면 모든 맥락을 잃지만, Claude Code는 메모리를 통해 프로젝트별 지식, 사용자 선호, 피드백을 지속적으로 축적한다.

### 메모리 저장 위치

메모리는 다음 경로에 자동으로 저장된다:

```text
~/.claude/
├── projects/
│   └── {project-path-hash}/
│       └── memory/
│           ├── MEMORY.md          ← 인덱스 파일
│           ├── project_*.md       ← 프로젝트 정보
│           ├── feedback_*.md      ← 사용자 피드백
│           └── user_*.md          ← 사용자 선호
└── CLAUDE.md                      ← 전역 사용자 설정
```

**MEMORY.md**는 인덱스 파일로, 모든 메모리 파일의 요약과 링크를 포함한다. Claude Code는 세션 시작 시 이 파일을 먼저 읽어 이전 대화의 맥락을 파악한다.

### 메모리 타입

| 타입 | 접두사 | 용도 | 예시 |
|------|--------|------|------|
| **project** | `project_` | 프로젝트 구조, 설정 | 배포 절차, 테스트 명령어 |
| **feedback** | `feedback_` | 사용자 피드백, 교정 | "한국어 주석 사용", "em dash 금지" |
| **user** | `user_` | 사용자 개인 선호 | 코딩 스타일, 선호 도구 |
| **reference** | `reference_` | 참조 정보 | API 문서, 외부 링크 |

### 프론트매터 형식

각 메모리 파일은 YAML 프론트매터로 메타데이터를 관리한다:

```markdown
---
type: feedback
created: 2026-03-15
tags: [coding-style, convention]
---

# 코딩 스타일 피드백

- 한국어 주석 사용
- em dash(-) 대신 하이픈(-) 사용
- 컴포넌트 400줄 초과 시 분할
```

### 메모리 관리 명령

메모리는 자연어로 관리할 수 있다:

**저장하기:**
```text
> "이 프로젝트에서는 항상 pytest를 사용한다는 걸 기억해줘"
```

Claude Code는 이 정보를 메모리 파일로 저장한다.

**삭제하기:**
```text
> "pytest 관련 메모리를 잊어줘"
```

해당 메모리를 찾아 삭제하거나 비활성화한다.

**확인하기:**
```text
> "이 프로젝트에 대해 어떤 것들을 기억하고 있어?"
```

현재 메모리에 저장된 정보를 요약하여 보여준다.

:::info
메모리는 Claude Code의 핵심 차별점 중 하나다. 프로젝트에 합류한 지 얼마 안 된 개발자처럼 매번 처음부터 설명할 필요 없이, 축적된 메모리를 통해 프로젝트의 맥락을 빠르게 파악한다. 특히 팀 프로젝트에서 각 개발자의 커밋 패턴, 코드 스타일, 우선순위를 학습하면 점점 더 정확한 도움을 줄 수 있다.
:::

---

## 5. 커스텀 슬래시 명령

### 커스텀 명령이란?

Claude Code에서 `/help`, `/commit` 같은 내장 명령 외에, **프로젝트별 커스텀 슬래시 명령**을 정의할 수 있다. 반복적인 워크플로우를 단일 명령으로 캡슐화하여 팀 전체가 일관된 방식으로 작업할 수 있다.

### 정의 방법

`.claude/commands/` 디렉토리에 Markdown 파일로 정의한다. 파일명이 곧 명령어 이름이 된다.

```text
.claude/
└── commands/
    ├── review.md        → /project:review
    ├── deploy.md        → /project:deploy
    └── test-plan.md     → /project:test-plan
```

### 명령 파일 작성

각 Markdown 파일에는 Claude Code에게 전달할 지침을 작성한다. `$ARGUMENTS` 변수로 사용자 인자를 받을 수 있다.

**`.claude/commands/review.md`**:

```markdown
다음 파일에 대한 코드 리뷰를 수행해줘: $ARGUMENTS

리뷰 기준:
1. 보안 취약점 (SQL 인젝션, XSS, CSRF)
2. 성능 이슈 (N+1 쿼리, 불필요한 반복)
3. 에러 처리 누락
4. 코딩 컨벤션 위반
5. 테스트 가능성

각 이슈를 심각도(높음/중간/낮음)와 함께 정리하고,
수정 코드를 제안해줘.
```

사용법:

```text
> /project:review backend/blog/views.py
```

`$ARGUMENTS`가 `backend/blog/views.py`로 치환되어 Claude Code가 해당 파일을 리뷰한다.

**`.claude/commands/deploy.md`**:

```markdown
배포 전 체크리스트를 수행해줘:

1. 마이그레이션 파일 확인: 커밋되지 않은 마이그레이션이 있는지 확인
2. 테스트 실행: `python manage.py test` 전체 통과 확인
3. 린트 검사: `flake8` 통과 확인
4. 환경변수 확인: .env.prod에 새로 추가된 변수가 있는지 확인
5. Docker 빌드: `docker compose -f docker-compose.prod.yml build` 성공 확인

모든 항목이 통과하면 "배포 준비 완료"로 보고하고,
실패 항목이 있으면 해결 방법과 함께 보고해줘.
```

사용법:

```text
> /project:deploy
```

### 실전 예시: 코드 리뷰 커스텀 명령 만들기

팀에서 일관된 코드 리뷰를 위해 커스텀 명령을 설계하는 전체 과정을 살펴보자.

**1단계: 리뷰 명령 정의**

```bash
mkdir -p .claude/commands
```

**`.claude/commands/full-review.md`**:

```markdown
$ARGUMENTS에 대한 종합 리뷰를 수행해줘.

## 서브에이전트를 활용한 병렬 리뷰

다음 3개의 서브에이전트를 병렬로 실행해줘:

### 에이전트 1: 보안 리뷰
- SQL 인젝션, XSS, CSRF 취약점
- 인증/인가 누락
- 민감 데이터 노출

### 에이전트 2: 성능 리뷰
- N+1 쿼리 패턴
- 불필요한 데이터 로딩
- 캐싱 가능 여부

### 에이전트 3: 코드 품질 리뷰
- 함수 길이 및 복잡도
- 네이밍 컨벤션
- 중복 코드
- 에러 처리

## 결과 통합
모든 에이전트의 결과를 종합하여 다음 형식으로 보고해줘:

| 카테고리 | 심각도 | 파일:라인 | 이슈 | 제안 |
```

**2단계: 사용**

```text
> /project:full-review backend/blog/
```

이 한 줄의 명령으로 3개의 서브에이전트가 병렬로 실행되어 종합적인 코드 리뷰가 수행된다. 팀원 누구나 동일한 명령으로 일관된 품질의 리뷰를 받을 수 있다.

:::tip
커스텀 명령은 **팀의 개발 문화를 코드화**하는 도구다. 리뷰 기준, 배포 절차, 테스트 전략 등 암묵적인 팀 규칙을 명시적인 명령으로 만들면, 신규 팀원도 즉시 팀의 워크플로우를 따를 수 있다.
:::

---

## 6. 고급 CLI 옵션

### 도구 제어

Claude Code의 CLI에서 사용 가능한 도구를 세밀하게 제어할 수 있다.

**`--allowedTools` - 허용 도구 제한**

특정 도구만 사용하도록 제한한다. 읽기 전용 분석 작업에 유용하다:

```bash
# 탐색 도구만 허용 (파일 수정 불가)
claude --allowedTools "Read,Grep,Glob" -p "이 프로젝트의 아키텍처를 분석해줘"
```

**`--disallowedTools` - 특정 도구 차단**

특정 도구만 차단하고 나머지는 모두 허용한다:

```bash
# Bash 실행만 차단
claude --disallowedTools "Bash" -p "코드를 수정해줘"
```

### 작업 디렉토리 확장

**`--add-dir` - 추가 작업 디렉토리**

현재 디렉토리 외에 추가 디렉토리를 Claude Code의 작업 범위에 포함한다:

```bash
# 프론트엔드와 백엔드를 동시에 작업
claude --add-dir /path/to/frontend --add-dir /path/to/backend
```

```bash
# 공유 라이브러리 참조
claude --add-dir /path/to/shared-lib
```

여러 리포지토리에 걸친 작업이나, 모노레포 내 특정 패키지만 선택적으로 포함할 때 유용하다.

### 시스템 프롬프트 제어

**`--system-prompt` - 시스템 프롬프트 오버라이드**

기본 시스템 프롬프트를 완전히 교체한다. 특수한 역할을 부여할 때 사용한다:

```bash
claude --system-prompt "당신은 보안 전문가입니다. 모든 코드를 보안 관점에서만 분석하세요." \
  -p "views.py를 분석해줘"
```

**`--append-system-prompt` - 시스템 프롬프트 추가**

기본 프롬프트를 유지하면서 추가 지시를 덧붙인다:

```bash
claude --append-system-prompt "모든 응답을 한국어로 작성하고, 코드 주석도 한국어로 작성하세요." \
  -p "새로운 API 엔드포인트를 추가해줘"
```

### 출력 제어

**`--max-tokens` - 최대 토큰 제한**

응답의 최대 토큰 수를 제한한다:

```bash
claude --max-tokens 4096 -p "이 함수를 설명해줘"
```

**`--output-format` - 프로그래매틱 출력**

Claude Code의 출력을 프로그램에서 파싱할 수 있는 형식으로 변환한다:

```bash
# JSON 형식 출력
claude --output-format json -p "프로젝트 구조를 JSON으로 정리해줘"
```

```bash
# 스트리밍 JSON (줄 단위 JSON 이벤트)
claude --output-format stream-json -p "이 파일을 리팩토링해줘"
```

| 형식 | 설명 | 용도 |
|------|------|------|
| `text` (기본) | 일반 텍스트 | 터미널 대화 |
| `json` | 전체 응답을 JSON으로 | 스크립트 통합 |
| `stream-json` | 줄 단위 JSON 스트림 | 실시간 처리, CI/CD 파이프라인 |

### 실전 예시: CI/CD 파이프라인 통합

CLI 옵션을 조합하면 Claude Code를 CI/CD 파이프라인에 통합할 수 있다:

```bash
#!/bin/bash
# ci-review.sh - PR 자동 리뷰 스크립트

CHANGED_FILES=$(git diff --name-only origin/main...HEAD)

claude \
  --allowedTools "Read,Grep,Glob" \
  --output-format json \
  --max-tokens 8192 \
  --append-system-prompt "보안 취약점과 성능 이슈에 집중하여 리뷰하세요." \
  -p "다음 변경된 파일들을 리뷰해줘: $CHANGED_FILES"
```

```bash
# GitHub Actions에서 사용
- name: AI Code Review
  run: |
    RESULT=$(bash ci-review.sh)
    echo "$RESULT" | jq -r '.result' > review-comment.md
    gh pr comment ${{ github.event.pull_request.number }} --body-file review-comment.md
```

:::warning
CI/CD에서 Claude Code를 사용할 때는 반드시 `--allowedTools`로 도구를 제한하고, `--max-tokens`로 비용을 통제해야 한다. 무제한 도구 접근과 토큰 사용은 예상치 못한 비용 폭증이나 보안 사고로 이어질 수 있다.
:::

---

## 고급 기능 조합: 통합 시나리오

지금까지 다룬 MCP, 서브에이전트, Hooks, 메모리, 커스텀 명령, CLI 옵션을 조합한 통합 시나리오를 살펴보자.

### 시나리오: 자동화된 PR 파이프라인

PR이 생성되면 자동으로 리뷰하고, 이슈를 보고하며, 완료 시 Slack 알림을 보내는 파이프라인이다.

**설정:**

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_..." }
    }
  },
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/notify-slack.sh"
          }
        ]
      }
    ]
  }
}
```

**커스텀 명령 (`.claude/commands/pr-pipeline.md`):**

```markdown
PR #$ARGUMENTS에 대한 전체 파이프라인을 수행해줘:

1. GitHub MCP로 PR diff를 가져와
2. 3개 서브에이전트를 병렬 실행:
   - 보안 리뷰
   - 성능 리뷰
   - 코드 스타일 리뷰
3. 결과를 종합하여 GitHub PR 코멘트로 게시
4. 심각도 높은 이슈가 있으면 GitHub Label "needs-fix" 추가
```

**실행:**

```text
> /project:pr-pipeline 42
```

이 한 줄로 MCP(GitHub 연동), 서브에이전트(병렬 리뷰), Hooks(Slack 알림)가 모두 연동되어 동작한다.

---

## 정리

| 기능 | 핵심 개념 | 설정 위치 |
|------|-----------|-----------|
| **MCP 서버** | 외부 서비스 도구 확장 | `.claude/settings.json`의 `mcpServers` |
| **서브에이전트** | 독립 작업 위임/병렬화 | 대화 중 자연어로 요청 |
| **Hooks** | 이벤트 기반 자동화 | `.claude/settings.json`의 `hooks` |
| **메모리** | 세션 간 정보 유지 | `~/.claude/projects/{path}/memory/` |
| **커스텀 명령** | 워크플로우 캡슐화 | `.claude/commands/*.md` |
| **CLI 옵션** | 실행 환경 세밀 제어 | 명령줄 플래그 |

이 고급 기능들은 단독으로도 강력하지만, 조합하면 시너지가 극대화된다. MCP로 외부 서비스를 연결하고, 서브에이전트로 작업을 병렬화하며, Hooks로 품질 관문을 설치하고, 메모리로 맥락을 유지하며, 커스텀 명령으로 이 모든 것을 한 줄의 명령으로 실행한다.

다음 글 [[claude-code-guide-04-workflow|Claude Code 실전]]에서는 프로젝트 관리와 워크플로우 설계를 다룬다.
