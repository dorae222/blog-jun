<!-- infographic-hero -->
![OpenCode Advanced Usage 핵심 요약](figures/infographic.svg)

*Figure: OpenCode Advanced Usage 한 장 요약 인포그래픽*

# OpenCode 고급 활용: LSP 통합과 커스텀 설정

:::info
이 글은 **OpenCode Guide** 시리즈의 세 번째 글이다. 시리즈 전체 목차:
1. [[opencode-guide-01-setup|경량 터미널 AI 코딩 도구]]
2. [[opencode-guide-02-core|핵심 기능: 멀티 모델 지원과 TUI]]
3. **고급 활용: LSP 통합과 커스텀 설정** (현재 글)
4. [[opencode-guide-04-workflow|실전: 팀 개발 환경 구축]]
:::

앞선 글에서 OpenCode의 핵심 기능인 멀티 모델 지원, 도구 시스템, 세션 관리를 살펴보았다. 이번 글에서는 OpenCode를 전문 개발 도구로 활용하기 위한 고급 기능을 다룬다. LSP 통합으로 AI에게 코드 인텔리전스를 제공하고, 커스텀 설정으로 워크플로우를 최적화하는 방법을 상세히 알아본다.

---

## LSP (Language Server Protocol) 통합 심층

### LSP란 무엇인가

Language Server Protocol(LSP)은 Microsoft가 설계한 프로토콜로, IDE와 언어 서버 사이의 통신을 표준화한다. TypeScript의 타입 검사, Python의 린팅, Go의 코드 네비게이션 등 언어별 코드 인텔리전스를 하나의 프로토콜로 제공한다.

OpenCode가 LSP를 통합한다는 것은, AI 모델이 단순히 텍스트를 보는 것이 아니라 **코드의 구조와 의미를 이해하는 도구**를 사용할 수 있다는 뜻이다.

### OpenCode LSP의 동작 원리

```text
파일 열기/수정
    ↓
파일 확장자 감지 (.ts, .py, .go 등)
    ↓
해당 언어의 LSP 서버 자동 시작
    ↓
LSP 서버가 코드 분석
    ↓
진단 정보, 타입 정보, 심볼 등을 AI 에이전트에게 제공
    ↓
AI가 이 정보를 활용하여 더 정확한 코드 작성/수정
```

핵심은 **자동화**다. `.ts` 파일을 열면 TypeScript 서버가 시작되고, `.py` 파일을 열면 Pyright가 초기화된다. 개발자가 별도로 설정할 필요 없이, 30개 이상의 언어 서버가 내장되어 있다.

### 지원 언어 및 LSP 서버

| 언어 | LSP 서버 | 파일 확장자 | 자동 설치 |
|------|----------|-------------|-----------|
| TypeScript/JavaScript | typescript-language-server | `.ts`, `.tsx`, `.js`, `.jsx` | O |
| Python | Pyright | `.py` | O |
| Go | gopls | `.go` | O |
| Rust | rust-analyzer | `.rs` | O |
| C/C++ | clangd | `.c`, `.cpp`, `.h` | O |
| Java | jdtls | `.java` | O |
| Kotlin | kotlin-language-server | `.kt` | O |
| Ruby | Solargraph | `.rb` | O |
| PHP | Intelephense | `.php` | O |
| C# | OmniSharp | `.cs` | O |
| Vue | Volar | `.vue` | O |
| Svelte | svelte-language-server | `.svelte` | O |
| Astro | astro-language-server | `.astro` | O |
| Lua | lua-language-server | `.lua` | O |
| Zig | zls | `.zig` | O |
| Elixir | ElixirLS | `.ex`, `.exs` | O |
| Haskell | HLS | `.hs` | O |
| OCaml | ocamllsp | `.ml` | O |
| Nix | nil | `.nix` | O |
| Gleam | gleam lsp | `.gleam` | O |
| Clojure | clojure-lsp | `.clj` | O |

:::tip
`OPENCODE_DISABLE_LSP_DOWNLOAD` 환경 변수를 설정하면 자동 LSP 다운로드를 비활성화할 수 있다. 이미 시스템에 설치된 LSP 서버만 사용하고 싶을 때 유용하다.
:::

### LSP 도구: diagnostics

`diagnostics` 도구는 LSP 서버가 제공하는 진단 정보(에러, 경고, 힌트)를 AI에게 전달한다.

```text
[diagnostics 도구 동작]
AI → diagnostics(file_path: "src/main.ts")
    ↓
LSP 서버에 진단 요청
    ↓
결과 반환:
  - Error: Type 'string' is not assignable to type 'number' (line 42)
  - Warning: 'result' is declared but never used (line 15)
    ↓
AI가 에러를 이해하고 수정 코드 생성
```

파일 경로를 생략하면 현재 LSP 세션이 있는 모든 파일의 진단 정보를 반환한다. AI가 파일을 수정한 후에도 자동으로 진단이 실행되므로, 수정으로 인해 발생한 새 에러를 즉시 감지할 수 있다.

### LSP 도구: hover

`hover` 도구는 특정 코드 위치의 타입 정보와 문서를 조회한다.

```text
[hover 도구 동작]
AI → hover(file_path: "src/utils.ts", line: 10, character: 15)
    ↓
LSP 서버에 hover 요청
    ↓
결과:
  function parseConfig(path: string): Config
  "Parse a TOML configuration file and return a typed Config object."
```

이를 통해 AI는 함수의 시그니처, 타입 정보, JSDoc 주석 등을 정확히 파악하고, 올바른 타입의 코드를 생성할 수 있다.

### LSP와 AI의 피드백 루프

OpenCode의 가장 강력한 패턴은 LSP와 AI의 **피드백 루프**다.

```text
AI가 코드 작성 (write/edit)
    ↓
LSP가 즉시 코드 분석
    ↓
진단 정보 생성 (에러, 타입 불일치 등)
    ↓
AI가 진단 정보를 확인 (diagnostics)
    ↓
에러가 있으면 추가 수정
    ↓
다시 LSP 분석 ... (에러 없을 때까지 반복)
```

write 도구는 파일 작성 후 자동으로 해당 파일과 영향을 받는 파일(최대 5개)의 LSP 진단을 수집한다. 이 자동 진단 덕분에, AI가 생성한 코드에 타입 에러나 구문 오류가 있으면 즉시 발견하고 수정할 수 있다.

### 코드 네비게이션

LSP를 통해 AI는 코드 베이스를 지능적으로 탐색할 수 있다.

- **Go to Definition** - 함수나 타입의 정의 위치로 이동
- **Find References** - 특정 심볼이 사용되는 모든 위치 검색
- **Call Hierarchy** - 함수 호출 관계 분석

이 기능들은 대규모 코드베이스에서 AI가 "이 함수가 어디서 호출되는지", "이 타입을 변경하면 어디에 영향을 주는지" 등을 정확히 파악하는 데 활용된다.

---

## 커스텀 프로바이더 설정

### OpenAI 호환 서버 연결

자체 호스팅하는 LLM 서버가 OpenAI API와 호환된다면, 커스텀 프로바이더로 설정할 수 있다.

```json
{
  "provider": {
    "custom": {
      "apiKey": "{env:CUSTOM_API_KEY}",
      "baseURL": "http://localhost:8080/v1"
    }
  },
  "model": "custom/my-model"
}
```

또는 `LOCAL_ENDPOINT` 환경 변수를 사용한다.

```bash
export LOCAL_ENDPOINT="http://my-server:8080/v1"
```

### vLLM 서버 연결 예시

```bash
# vLLM 서버 시작
python -m vllm.entrypoints.openai.api_server \
  --model codellama/CodeLlama-34b-Instruct-hf \
  --port 8080

# OpenCode에서 사용
export LOCAL_ENDPOINT="http://localhost:8080/v1"
opencode
```

### LiteLLM 프록시 연결

LiteLLM을 프록시로 사용하면 여러 프로바이더를 통합 관리할 수 있다.

```yaml
# litellm_config.yaml
model_list:
  - model_name: "fast-model"
    litellm_params:
      model: "gpt-4.1-mini"
      api_key: "sk-..."
  - model_name: "smart-model"
    litellm_params:
      model: "claude-sonnet-4-20250514"
      api_key: "sk-ant-..."
```

```bash
# LiteLLM 프록시 시작
litellm --config litellm_config.yaml --port 4000
```

```json
{
  "provider": {
    "litellm": {
      "baseURL": "http://localhost:4000/v1",
      "apiKey": "{env:LITELLM_API_KEY}"
    }
  },
  "model": "litellm/fast-model"
}
```

---

## config 고급 설정

### 설정 파일 전체 구조

OpenCode의 설정은 JSON 형식이며, 다음과 같은 계층 구조를 가진다.

```json
{
  "model": "anthropic/claude-sonnet-4-20250514",
  "small_model": "openai/gpt-4.1-mini",
  "enabled_providers": ["openai", "anthropic", "ollama"],

  "provider": {
    "openai": { "apiKey": "{env:OPENAI_API_KEY}" },
    "anthropic": { "apiKey": "{env:ANTHROPIC_API_KEY}" },
    "ollama": {}
  },

  "compaction": {
    "reserved": 20000
  },

  "tools": {
    "bash": { "permission": "ask" },
    "write": { "permission": "ask" },
    "edit": { "permission": "allow" },
    "read": { "permission": "allow" }
  },

  "keybinds": {
    "command_list": "ctrl+k",
    "new_session": "ctrl+x n"
  },

  "mcp": {},

  "instructions": []
}
```

### 설정 병합 규칙

OpenCode의 설정은 여러 소스에서 로드되며 **병합(merge)**된다. 교체(replace)가 아니라 병합이므로, 프로젝트 설정에서 특정 키만 오버라이드할 수 있다.

```text
글로벌 설정 (~/.config/opencode/opencode.json)
  + 프로젝트 설정 (./opencode.json)
  = 최종 설정 (충돌 시 프로젝트 설정 우선)
```

예를 들어, 글로벌에서 OpenAI와 Anthropic 프로바이더를 설정하고, 특정 프로젝트에서는 모델만 변경하면 된다.

```json
// 프로젝트별 opencode.json - 모델만 오버라이드
{
  "model": "openai/gpt-4.1",
  "small_model": "openai/gpt-4.1-nano"
}
```

### 도구 권한 세분화

도구별로 세밀하게 권한을 설정할 수 있다.

```json
{
  "tools": {
    "bash": {
      "permission": "ask",
      "description": "셸 명령 실행 시 항상 확인"
    },
    "write": {
      "permission": "ask",
      "description": "새 파일 생성 시 확인"
    },
    "edit": {
      "permission": "allow",
      "description": "기존 파일 편집은 자동 허용"
    },
    "read": {
      "permission": "allow",
      "description": "파일 읽기는 항상 허용"
    },
    "glob": {
      "permission": "allow"
    },
    "grep": {
      "permission": "allow"
    }
  }
}
```

:::warning
보안이 중요한 프로젝트에서는 `bash` 도구의 권한을 `"ask"`로 설정하는 것을 권장한다. `"allow"`로 설정하면 AI가 확인 없이 셸 명령을 실행할 수 있어 위험할 수 있다.
:::

---

## 테마 커스터마이징

### 내장 테마 사용

OpenCode는 30개 이상의 내장 테마를 제공한다. 라이트/다크 모드를 자동으로 감지하여 적용한다.

```text
# TUI에서 테마 변경
/theme
```

또는 설정 파일에서 지정한다.

```json
// tui.json 또는 tui.jsonc
{
  "theme": "catppuccin"
}
```

주요 내장 테마 목록은 다음과 같다.

| 테마 | 스타일 | 특징 |
|------|--------|------|
| `opencode` | 기본 | OpenCode 공식 테마 |
| `catppuccin` | 다크/라이트 | 부드러운 파스텔 색상 |
| `dracula` | 다크 | 인기 있는 다크 테마 |
| `gruvbox` | 다크/라이트 | 레트로 느낌 |
| `tokyo-night` | 다크 | 모던한 나이트 테마 |
| `nord` | 다크/라이트 | 북유럽 색감 |
| `solarized` | 다크/라이트 | 클래식 테마 |
| `one-dark` | 다크 | Atom One Dark 스타일 |

### 커스텀 테마 생성

자신만의 테마를 만들려면 테마 디렉토리에 JSON 파일을 생성한다.

```bash
# 테마 디렉토리 생성
mkdir -p ~/.config/opencode/themes
```

```json
// ~/.config/opencode/themes/my-theme.json
{
  "name": "my-theme",
  "variant": {
    "dark": {
      "primary": "#61AFEF",
      "secondary": "#98C379",
      "accent": "#C678DD",
      "background": "#282C34",
      "foreground": "#ABB2BF",
      "error": "#E06C75",
      "warning": "#E5C07B",
      "success": "#98C379",
      "info": "#61AFEF"
    },
    "light": {
      "primary": "#4078F2",
      "secondary": "#50A14F",
      "accent": "#A626A4",
      "background": "#FAFAFA",
      "foreground": "#383A42",
      "error": "#E45649",
      "warning": "#C18401",
      "success": "#50A14F",
      "info": "#4078F2"
    }
  },
  "defs": {
    "myCustomColor": "#FF5733"
  }
}
```

`defs` 섹션에서 재사용 가능한 색상을 정의할 수 있다. 특수 값 `"none"`을 사용하면 터미널의 기본 색상을 상속받는다.

### 터미널 요구사항

테마가 올바르게 표시되려면 터미널이 **트루컬러(24-bit color)**를 지원해야 한다.

| 터미널 | 트루컬러 지원 |
|--------|-------------|
| iTerm2 (macOS) | O |
| WezTerm | O |
| Alacritty | O |
| Kitty | O |
| Windows Terminal | O |
| macOS Terminal.app | X (256색 제한) |
| 오래된 xterm | X |

---

## SQLite 세션 데이터 활용

### 세션 데이터 구조

OpenCode의 세션은 SQLite에 저장된다. 이 데이터베이스를 직접 조회하면 유용한 인사이트를 얻을 수 있다.

```bash
# SQLite 데이터베이스 위치
ls ~/.local/share/opencode/
```

```bash
# SQLite로 직접 조회
sqlite3 ~/.local/share/opencode/sessions.db
```

```sql
-- 세션 목록 조회
SELECT id, created_at, project_path FROM sessions
ORDER BY created_at DESC LIMIT 10;

-- 특정 세션의 메시지 수 확인
SELECT session_id, COUNT(*) as msg_count
FROM messages
GROUP BY session_id
ORDER BY msg_count DESC;
```

### 세션 데이터 백업

중요한 작업 세션은 백업해두는 것이 좋다.

```bash
# 세션 데이터 백업
cp ~/.local/share/opencode/sessions.db \
   ~/backups/opencode-sessions-$(date +%Y%m%d).db
```

### 세션 정리

오래된 세션이 쌓이면 데이터베이스 크기가 커질 수 있다. 주기적으로 정리하자.

```bash
# 데이터베이스 크기 확인
du -h ~/.local/share/opencode/sessions.db

# SQLite VACUUM으로 공간 회수
sqlite3 ~/.local/share/opencode/sessions.db "VACUUM;"
```

:::warning
세션 데이터베이스를 직접 수정할 때는 반드시 백업을 먼저 수행하자. OpenCode가 실행 중인 상태에서 DB를 수정하면 데이터 손상이 발생할 수 있다.
:::

---

## MCP 서버 연동

### MCP (Model Context Protocol)란

Model Context Protocol(MCP)은 AI 모델에게 외부 도구와 데이터 소스에 대한 접근 권한을 제공하는 프로토콜이다. OpenCode는 MCP를 지원하여 내장 도구 외에 외부 도구를 추가할 수 있다.

### 로컬 MCP 서버 설정

```json
{
  "mcp": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/workspace"],
      "enabled": true
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "{env:GITHUB_TOKEN}"
      },
      "enabled": true
    }
  }
}
```

### 리모트 MCP 서버 설정

원격 MCP 서버도 연결할 수 있다. OpenCode는 원격 MCP 서버의 OAuth 인증을 자동으로 처리한다.

```json
{
  "mcp": {
    "remote-tool": {
      "type": "remote",
      "url": "https://mcp-server.example.com",
      "headers": {
        "Authorization": "Bearer {env:MCP_TOKEN}"
      },
      "enabled": true
    }
  }
}
```

인증 토큰은 `~/.local/share/opencode/mcp-auth.json`에 안전하게 저장된다.

### MCP 서버 관리

```json
{
  "mcp": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "enabled": false
    }
  }
}
```

`enabled: false`로 설정하면 설정을 삭제하지 않고도 일시적으로 비활성화할 수 있다.

### 컨텍스트 주의사항

:::warning
MCP 서버를 사용하면 컨텍스트 윈도우가 빠르게 소진될 수 있다. 각 MCP 도구가 컨텍스트에 추가되므로, 많은 도구를 가진 MCP 서버를 여러 개 연결하면 실질적으로 사용 가능한 컨텍스트가 줄어든다. 필요한 MCP 서버만 선택적으로 활성화하자.
:::

### 실용적인 MCP 서버 조합 예시

| MCP 서버 | 용도 | 추천 상황 |
|----------|------|-----------|
| `server-github` | GitHub 이슈, PR 관리 | GitHub 기반 프로젝트 |
| `server-filesystem` | 확장된 파일 시스템 접근 | 외부 디렉토리 참조 필요 시 |
| `server-postgres` | PostgreSQL 직접 쿼리 | DB 스키마 설계/디버깅 |
| `server-slack` | Slack 메시지 조회 | 팀 커뮤니케이션 참조 |
| `server-memory` | 장기 메모리 저장 | 세션 간 컨텍스트 유지 |

---

## AGENTS.md와 Rules 시스템

### AGENTS.md

AGENTS.md는 프로젝트별 AI 지시사항 파일이다. Cursor의 `.cursorrules`와 유사한 역할을 한다.

```bash
# 자동 생성
opencode
/init
```

`/init` 명령은 프로젝트를 스캔하고, 프로젝트 구조와 기술 스택을 이해하여 적절한 AGENTS.md를 자동 생성한다.

### AGENTS.md 예시

```markdown
# Project Instructions

## Tech Stack
- Go 1.23
- PostgreSQL 16
- Docker

## Coding Standards
- All functions must have doc comments
- Error handling: wrap errors with fmt.Errorf("context: %w", err)
- Test coverage must be maintained above 80%

## Architecture
- Clean Architecture (handler -> service -> repository)
- Domain models in /internal/domain
- HTTP handlers in /internal/handler
- Business logic in /internal/service

## File Structure
- /cmd - Application entry points
- /internal - Private application code
- /pkg - Public library code
- /migrations - Database migrations
```

### 다중 지시사항 파일

OpenCode는 여러 위치에서 지시사항을 로드한다. 첫 번째로 매칭되는 파일이 사용된다.

```text
우선순위:
1. AGENTS.md (최우선)
2. CLAUDE.md (호환)
3. opencode.json의 instructions 배열
4. 글로벌 ~/.config/opencode/opencode.json의 instructions
```

### 원격 지시사항

URL에서 지시사항을 로드할 수도 있다. 팀 전체가 동일한 규칙을 공유할 때 유용하다.

```json
{
  "instructions": [
    "https://team-rules.example.com/coding-standards.md"
  ]
}
```

원격 지시사항은 5초 타임아웃으로 가져오며, AGENTS.md 파일과 결합된다.

---

## 커스텀 에이전트 생성

### 에이전트 설정 파일

`.opencode/agents/` 디렉토리에 마크다운 파일로 커스텀 에이전트를 정의한다.

```markdown
---
id: reviewer
name: "Code Reviewer"
model: "anthropic/claude-sonnet-4-20250514"
temperature: 0.2
color: "#FF5733"
tools:
  - read
  - glob
  - grep
  - diagnostics
  - hover
---

You are a code reviewer. Analyze code for:
1. Bugs and potential issues
2. Performance problems
3. Security vulnerabilities
4. Code style inconsistencies

Do NOT modify any files. Only provide analysis and recommendations.
Write your review to .opencode/plans/review.md.
```

### 에이전트 설정 옵션 상세

| 옵션 | 타입 | 설명 |
|------|------|------|
| `id` | string | 에이전트 고유 식별자 |
| `name` | string | 표시 이름 |
| `model` | string | 사용할 모델 (에이전트별 오버라이드) |
| `temperature` | number | 창의성 수준 (0.0 - 2.0) |
| `color` | string | UI 표시 색상 (hex 또는 테마 색상) |
| `tools` | list | 접근 가능한 도구 목록 |

### 실용적인 커스텀 에이전트 예시

#### Debug 에이전트

```markdown
---
id: debugger
name: "Debugger"
model: "openai/o4-mini"
temperature: 0.1
color: "error"
tools:
  - read
  - bash
  - diagnostics
  - grep
  - glob
---

You are a debugging specialist. When given an error or bug report:
1. Reproduce the issue if possible
2. Trace the root cause through the code
3. Suggest a minimal fix
4. Verify the fix resolves the issue

Use bash for running tests and checking logs.
```

#### Docs 에이전트

```markdown
---
id: docs
name: "Documentation Writer"
model: "anthropic/claude-sonnet-4-20250514"
temperature: 0.3
color: "info"
tools:
  - read
  - write
  - glob
  - grep
---

You are a documentation specialist. Write clear, concise documentation.
Follow the project's existing documentation style.
Include code examples for all public APIs.
```

---

## 플러그인 시스템

### 플러그인 기본 구조

플러그인은 `.opencode/plugins/` (프로젝트) 또는 `~/.config/opencode/plugins/` (글로벌) 디렉토리에 배치한다. TypeScript로 작성한다.

```text
.opencode/
  plugins/
    my-plugin.ts
```

### 플러그인 예시: 커스텀 도구

```typescript
// .opencode/plugins/git-summary.ts
import { definePlugin } from "opencode/plugin";

export default definePlugin({
  name: "git-summary",
  tools: {
    gitSummary: {
      description: "Get a summary of recent git activity",
      parameters: {
        days: {
          type: "number",
          description: "Number of days to look back",
          default: 7
        }
      },
      async execute({ days }) {
        const { stdout } = await exec(
          `git log --oneline --since="${days} days ago"`
        );
        return stdout;
      }
    }
  }
});
```

### 플러그인 훅

플러그인은 OpenCode의 이벤트에 훅을 걸 수 있다.

| 훅 | 시점 | 용도 |
|----|------|------|
| `session.compacting` | 세션 압축 직전 | 도메인 특화 컨텍스트 주입 |
| `message.before` | 메시지 전송 전 | 메시지 전처리 |
| `message.after` | 응답 수신 후 | 응답 후처리, 로깅 |
| `tool.before` | 도구 실행 전 | 권한 검사, 로깅 |
| `tool.after` | 도구 실행 후 | 결과 가공 |

```typescript
// .opencode/plugins/logger.ts
import { definePlugin } from "opencode/plugin";

export default definePlugin({
  name: "logger",
  hooks: {
    "tool.after": async (event) => {
      console.log(`Tool ${event.tool} executed in ${event.duration}ms`);
    }
  }
});
```

### npm 플러그인

npm 패키지로 배포된 플러그인도 사용할 수 있다.

```json
{
  "plugins": [
    "oh-my-opencode",
    "@team/opencode-rules"
  ]
}
```

---

## 디버깅과 로깅

### 디버그 모드 실행

문제가 발생하면 디버그 모드로 상세 정보를 확인할 수 있다.

```bash
# 디버그 모드
opencode --debug

# 단축 옵션
opencode -d

# 로그 레벨 지정
opencode --log-level DEBUG
```

### 환경 변수 디버깅

| 환경 변수 | 설명 |
|-----------|------|
| `DEBUG=opencode:*` | 전체 디버그 로깅 활성화 |
| `OPENCODE_DISABLE_LSP_DOWNLOAD` | LSP 자동 다운로드 비활성화 |
| `OPENCODE_PORT` | 데스크톱 앱 로컬 서버 포트 지정 |
| `LOCAL_ENDPOINT` | 커스텀 LLM 엔드포인트 |

### 일반적인 문제와 해결

#### LSP 서버가 시작되지 않는 경우

```bash
# LSP 서버 상태 확인
opencode --debug 2>&1 | grep "lsp"

# 특정 언어 서버 수동 확인
which typescript-language-server
which pyright
which gopls
```

#### API 인증 실패

```bash
# 환경 변수 확인
env | grep -E "(OPENAI|ANTHROPIC|GOOGLE)_API_KEY"

# 인증 파일 확인
cat ~/.local/share/opencode/auth.json
```

#### 메모리 사용량 이슈

```bash
# OpenCode 프로세스 메모리 확인
ps aux | grep opencode

# SQLite 데이터베이스 크기 확인
du -h ~/.local/share/opencode/sessions.db
```

### 로그 파일 위치

| 환경 | 위치 |
|------|------|
| CLI/TUI | stdout 또는 `~/.local/share/opencode/logs/` |
| 데스크톱 앱 | 앱 로그 디렉토리 |
| VS Code 확장 | VS Code 출력 패널 |

---

## Skills 시스템

### Skills란

Skills는 에이전트가 필요할 때 동적으로 로드하는 재사용 가능한 행동 패턴이다. 에이전트와 달리 항상 활성화되어 있지 않으며, 작업이 매칭될 때만 로드된다.

### Skills 정의

```markdown
<!-- .opencode/skills/code-review/SKILL.md -->
---
name: "Code Review"
description: "Perform thorough code review"
---

When performing a code review:

1. Check for common patterns:
   - Error handling completeness
   - Input validation
   - SQL injection vulnerabilities
   - Race conditions

2. Verify test coverage

3. Check documentation completeness

4. Output format:
   - Summary of findings
   - Priority: Critical / High / Medium / Low
   - Suggested fixes with code examples
```

AI 에이전트는 `skill` 도구를 통해 작업에 적합한 스킬을 자동으로 로드한다.

---

## 정리

이 글에서 다룬 고급 기능을 정리한다.

- **LSP 통합**: 30개 이상의 언어 서버를 자동으로 관리하며, AI에게 진단 정보와 타입 정보를 제공하여 코드 품질을 높인다
- **커스텀 프로바이더**: OpenAI 호환 API 서버, vLLM, LiteLLM 등 자체 호스팅 모델을 연결할 수 있다
- **고급 설정**: 설정 병합 규칙을 이해하고, 도구 권한을 세밀하게 제어할 수 있다
- **테마 커스터마이징**: 30개 이상의 내장 테마와 JSON 기반 커스텀 테마를 지원한다
- **MCP 서버**: 외부 도구와 데이터 소스를 MCP 프로토콜로 연결하여 기능을 확장한다
- **AGENTS.md**: 프로젝트별 AI 지시사항으로 일관된 코딩 표준을 유지한다
- **커스텀 에이전트**: 용도별 에이전트를 마크다운 파일로 손쉽게 생성할 수 있다
- **플러그인**: 훅과 커스텀 도구로 OpenCode를 무한히 확장할 수 있다
- **디버깅**: `--debug` 플래그와 환경 변수로 문제를 진단한다

다음 글 [[opencode-guide-04-workflow|OpenCode 실전]]에서는 팀 개발 환경 구축 전략을 다룬다.
