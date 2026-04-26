<!-- infographic-hero -->
![OpenCode Workflow Design 핵심 요약](figures/infographic.svg)

*Figure: OpenCode Workflow Design 한 장 요약 인포그래픽*

# OpenCode 실전: 팀 개발 환경 구축

:::info
이 글은 **OpenCode Guide** 시리즈의 마지막 글이다. 시리즈 전체 목차:
1. [[opencode-guide-01-setup|경량 터미널 AI 코딩 도구]]
2. [[opencode-guide-02-core|핵심 기능: 멀티 모델 지원과 TUI]]
3. [[opencode-guide-03-advanced|고급 활용: LSP 통합과 커스텀 설정]]
4. **실전: 팀 개발 환경 구축** (현재 글)
:::

지금까지 OpenCode의 설치, 핵심 기능, 고급 설정을 다뤘다. 이번 마지막 글에서는 OpenCode를 팀 환경에서 실전 활용하는 전략을 다룬다. 멀티 모델 전략으로 비용을 최적화하고, Crush로의 마이그레이션을 준비하며, 다른 AI 코딩 도구와의 역할 분담까지 실무적인 관점에서 정리한다.

---

## 팀 개발 환경에서의 OpenCode 활용

### 왜 팀 환경에서 OpenCode인가

팀에서 AI 코딩 도구를 도입할 때 가장 큰 고민은 **벤더 종속**과 **비용**이다. Claude Code는 Anthropic에, GitHub Copilot은 Microsoft에 종속된다. OpenCode는 오픈소스이며 프로바이더 독립적이므로 다음과 같은 이점을 제공한다.

| 고려사항 | 벤더 종속 도구 | OpenCode |
|----------|-------------|----------|
| 프로바이더 선택 | 하나로 고정 | 75+ 프로바이더 자유 선택 |
| 비용 | 구독료 + API 비용 | API 비용만 (또는 Ollama로 무료) |
| 커스터마이징 | 제한적 | 에이전트, 플러그인, MCP로 무한 확장 |
| 데이터 프라이버시 | 외부 전송 | 로컬 모델 사용 가능 |
| 팀 규칙 관리 | 도구별 설정 | AGENTS.md로 통일 |
| 라이선스 | 상용 | MIT (완전 자유) |

### 팀 설정 표준화

팀 전체가 일관된 OpenCode 경험을 갖도록 표준 설정을 구축하자.

#### 프로젝트 공통 설정

프로젝트 루트에 `opencode.json`을 Git으로 관리한다.

```json
{
  "model": "anthropic/claude-sonnet-4-20250514",
  "small_model": "openai/gpt-4.1-mini",

  "enabled_providers": ["openai", "anthropic", "google", "ollama"],

  "tools": {
    "bash": { "permission": "ask" },
    "write": { "permission": "ask" },
    "edit": { "permission": "allow" },
    "read": { "permission": "allow" }
  },

  "compaction": {
    "reserved": 25000
  }
}
```

#### 팀 AGENTS.md 관리

AGENTS.md를 Git으로 버전 관리하면, 팀 전체가 동일한 코딩 표준과 AI 지시사항을 공유할 수 있다.

```markdown
# Team Coding Standards - AGENTS.md

## Language & Framework
- TypeScript 5.x strict mode
- React 19 with Server Components
- PostgreSQL 16 with Drizzle ORM

## Conventions
- Function naming: camelCase
- Component naming: PascalCase
- File naming: kebab-case.ts
- Max function length: 50 lines
- All public functions must have JSDoc

## Error Handling
- Use Result type pattern (no thrown errors in business logic)
- HTTP errors: use standardized ApiError class
- Log errors with structured logging (pino)

## Testing
- Unit tests: Vitest
- E2E tests: Playwright
- Minimum coverage: 80%
- Test file naming: *.test.ts

## Git
- Conventional commits (feat:, fix:, chore:, etc.)
- PR title format: [TYPE] Brief description
- Squash merge to main
```

#### 원격 지시사항으로 팀 규칙 공유

팀 규칙을 중앙에서 관리하고 모든 프로젝트에 적용할 수 있다.

```json
{
  "instructions": [
    "https://raw.githubusercontent.com/team/standards/main/AGENTS.md"
  ]
}
```

이 방식의 장점은 규칙을 한 곳에서 업데이트하면 모든 프로젝트에 즉시 반영된다는 것이다. 5초 타임아웃이 있으므로 네트워크가 불안정한 환경에서는 로컬 복사본도 함께 유지하는 것이 좋다.

---

## 멀티 모델 전략

### 작업별 최적 모델 선택

모든 작업에 최고 성능 모델을 사용할 필요는 없다. 작업의 복잡도에 따라 적절한 모델을 선택하면 비용을 크게 절감할 수 있다.

| 작업 유형 | 권장 모델 | 이유 |
|-----------|----------|------|
| 복잡한 아키텍처 설계 | Claude Opus 4, GPT-4.1 | 최고 수준의 추론 능력 필요 |
| 멀티 파일 리팩토링 | Claude Sonnet 4, GPT-4.1 | 넓은 컨텍스트 이해 필요 |
| 일반 코드 작성 | Claude Sonnet 4, GPT-4.1-mini | 균형 잡힌 성능 |
| 단순 코드 수정 | GPT-4.1-mini, Gemini Flash | 빠르고 저렴 |
| 코드 설명/질문 | GPT-4.1-nano, Ollama 로컬 | 최소 비용 |
| 디버깅/추론 | o4-mini | 추론 특화 |
| 대규모 코드베이스 분석 | Gemini 2.5 Pro | 긴 컨텍스트 윈도우 |

### model과 small_model 활용

OpenCode의 `model`과 `small_model` 설정을 활용하면 자동으로 작업 복잡도에 따라 모델을 분배할 수 있다.

```json
{
  "model": "anthropic/claude-sonnet-4-20250514",
  "small_model": "openai/gpt-4.1-nano"
}
```

- `model` - 메인 코딩 작업에 사용되는 주 모델
- `small_model` - 자동 압축, 서브태스크 등 보조 작업에 사용

### 에이전트별 모델 분리

커스텀 에이전트를 만들 때 각 에이전트에 최적의 모델을 지정할 수 있다.

```markdown
<!-- .opencode/agents/planner.md -->
---
id: planner
name: "Strategic Planner"
model: "anthropic/claude-opus-4-20250514"
temperature: 0.3
tools:
  - read
  - glob
  - grep
---

You are a senior architect. Analyze the codebase and create detailed plans.
```

```markdown
<!-- .opencode/agents/implementer.md -->
---
id: implementer
name: "Fast Implementer"
model: "openai/gpt-4.1-mini"
temperature: 0.1
tools:
  - read
  - write
  - edit
  - bash
  - diagnostics
---

You are a fast, efficient coder. Follow the plan exactly.
```

```markdown
<!-- .opencode/agents/reviewer.md -->
---
id: reviewer
name: "Code Reviewer"
model: "openai/o4-mini"
temperature: 0.1
tools:
  - read
  - grep
  - diagnostics
  - hover
---

You are a code reviewer specializing in bug detection.
```

이렇게 하면 분석은 고성능 모델로, 구현은 빠른 모델로, 리뷰는 추론 특화 모델로 처리하는 효율적인 파이프라인이 만들어진다.

---

## 비용 최적화

### 클라우드 vs 로컬 모델 비용 비교

월 100만 토큰 기준으로 대략적인 비용을 비교해보자.

| 프로바이더/모델 | 입력 비용 (/1M tokens) | 출력 비용 (/1M tokens) | 월 추정 비용 |
|----------------|----------------------|----------------------|-------------|
| Claude Opus 4 | $15.00 | $75.00 | ~$45 |
| Claude Sonnet 4 | $3.00 | $15.00 | ~$9 |
| GPT-4.1 | $2.00 | $8.00 | ~$5 |
| GPT-4.1-mini | $0.40 | $1.60 | ~$1 |
| GPT-4.1-nano | $0.10 | $0.40 | ~$0.25 |
| Gemini 2.5 Flash | $0.15 | $0.60 | ~$0.38 |
| Ollama (로컬) | 무료 | 무료 | 전기 요금만 |

:::tip
개인 개발자라면 일상적인 작업은 GPT-4.1-mini나 로컬 모델로 처리하고, 복잡한 작업에만 Sonnet/Opus를 사용하면 월 비용을 $10 이하로 유지할 수 있다.
:::

### Ollama 로컬 모델 최적화

코딩에 적합한 로컬 모델과 하드웨어 요구사항은 다음과 같다.

| 모델 | 크기 | VRAM 요구 | 코딩 성능 |
|------|------|-----------|-----------|
| Qwen 2.5 Coder 32B | 32B | 24GB+ | 매우 좋음 |
| DeepSeek Coder V2 16B | 16B | 12GB+ | 좋음 |
| CodeLlama 34B | 34B | 24GB+ | 좋음 |
| Qwen 2.5 Coder 7B | 7B | 8GB+ | 보통 |
| CodeLlama 7B | 7B | 8GB+ | 기본적 |

```bash
# GPU가 충분하다면 큰 모델을
ollama pull qwen2.5-coder:32b

# GPU가 제한적이라면 작은 모델을
ollama pull qwen2.5-coder:7b

# 양자화 버전으로 VRAM 절약
ollama pull qwen2.5-coder:32b-q4_K_M
```

### 하이브리드 전략: 로컬 + 클라우드

가장 비용 효율적인 전략은 로컬 모델과 클라우드 모델을 혼합하는 것이다.

```json
{
  "model": "anthropic/claude-sonnet-4-20250514",
  "small_model": "ollama/qwen2.5-coder:7b",

  "provider": {
    "anthropic": {
      "apiKey": "{env:ANTHROPIC_API_KEY}"
    },
    "ollama": {}
  }
}
```

이 설정에서 메인 코딩 작업은 Claude Sonnet이 처리하고, 자동 압축이나 간단한 서브태스크는 로컬 모델이 무료로 처리한다.

### 작업 흐름별 모델 전환 전략

일일 개발 워크플로우에서 모델을 전환하는 실전 전략을 소개한다.

```text
[오전: 설계 및 분석 세션]
/model anthropic/claude-opus-4-20250514
- 아키텍처 분석
- 리팩토링 계획 수립
- 복잡한 알고리즘 설계

[오후: 구현 세션]
/model openai/gpt-4.1-mini
- 계획에 따른 코드 구현
- 테스트 작성
- 간단한 버그 수정

[저녁: 리뷰 세션]
/model openai/o4-mini
- 코드 리뷰
- 엣지 케이스 분석
- 보안 점검
```

---

## Crush로의 마이그레이션 가이드

### Crush 소개

Crush는 OpenCode의 원저자 Kujtim Hoxha가 Charm 팀에 합류한 후 개발한 프로젝트다. OpenCode와 같은 뿌리에서 출발했지만, Charm 생태계와 더 긴밀히 통합되어 있다.

```bash
# Crush 설치
brew install charmbracelet/tap/crush

# 또는 go install
go install github.com/charmbracelet/crush@latest
```

### OpenCode vs Crush 비교

| 항목 | OpenCode | Crush |
|------|----------|-------|
| 관리 주체 | Anomaly (SST 출신) | Charm + 원저자 |
| 저장소 | `anomalyco/opencode` | `charmbracelet/crush` |
| TUI 프레임워크 | Bubble Tea | Bubble Tea (더 깊은 통합) |
| 생태계 | 독자 플러그인 생태계 | Charm 생태계 (Soft Serve, Glow 등) |
| 모델 지원 | 75+ | 다양한 모델 (OpenAI, Anthropic 등) |
| LSP 지원 | O | O |
| 세션 관리 | SQLite | 세션 히스토리 유지 |
| 플랫폼 | macOS, Linux, Windows | macOS, Linux, Windows, Android, FreeBSD 등 |
| 커뮤니티 규모 | 매우 큼 (95K+ stars) | 성장 중 |
| 라이선스 | MIT | MIT |

### 차이점과 개선사항

Crush가 OpenCode 대비 차별화하는 주요 포인트는 다음과 같다.

1. **Charm 생태계 통합** - Charm의 다른 도구들(Soft Serve Git 서버, Glow 마크다운 뷰어 등)과 자연스럽게 연동
2. **폭넓은 플랫폼 지원** - Android, FreeBSD, OpenBSD, NetBSD까지 지원하여 거의 모든 플랫폼에서 실행 가능
3. **세션 중 모델 전환** - 컨텍스트를 유지하면서 모델 전환이 가능 (OpenCode도 지원)
4. **UI/UX 세련됨** - Charm 팀의 TUI 전문성이 반영된 더 세련된 인터페이스

### 마이그레이션 체크리스트

OpenCode에서 Crush로 전환할 때 확인할 사항은 다음과 같다.

```text
1. [ ] Crush 설치 확인
2. [ ] API 키 환경 변수 확인 (동일하게 사용 가능)
3. [ ] 설정 파일 형식 확인 및 변환
4. [ ] AGENTS.md 호환성 확인
5. [ ] 커스텀 에이전트 마이그레이션
6. [ ] MCP 서버 설정 이전
7. [ ] 팀원 교육 및 전환 일정 수립
```

:::info
OpenCode와 Crush를 동시에 사용하는 것도 가능하다. 두 도구 모두 MIT 라이선스이며, 같은 API 키와 모델을 공유할 수 있다. 급하게 전환할 필요 없이 점진적으로 이동하는 것을 권장한다.
:::

### 설정 마이그레이션

대부분의 설정은 유사한 구조를 사용하므로 큰 수정 없이 이전할 수 있다.

```bash
# OpenCode 설정 백업
cp -r ~/.config/opencode ~/.config/opencode-backup

# Crush 설정 디렉토리 확인
ls ~/.config/crush/
```

API 키 환경 변수는 동일하게 사용할 수 있다. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` 등 표준 환경 변수를 그대로 인식한다.

---

## 다른 도구와의 비교 및 사용 분담

### AI 코딩 도구 생태계

2026년 현재 주요 AI 코딩 도구의 포지셔닝은 다음과 같다.

| 도구 | 유형 | 가격 | 모델 | 강점 |
|------|------|------|------|------|
| **OpenCode** | 터미널 에이전트 | 무료 (+ API) | 75+ | 프로바이더 독립, 오픈소스 |
| **Claude Code** | 터미널 에이전트 | $20/월 + API | Claude만 | 최고 수준의 코드 이해력 |
| **Cursor** | IDE | $20/월 | 멀티 | 가장 낮은 진입 장벽, 시각적 |
| **GitHub Copilot** | IDE 플러그인 | $10-19/월 | OpenAI | GitHub 통합, 자동 완성 |
| **Windsurf** | IDE | $10-15/월 | 멀티 | Cascade 에이전트 |
| **Codex** | 터미널 에이전트 | API 비용 | OpenAI | OpenAI 공식 도구 |
| **Crush** | 터미널 에이전트 | 무료 (+ API) | 멀티 | Charm 생태계, 세련된 TUI |

### 도구 조합 전략

하나의 도구만 사용하기보다, 상황에 맞게 여러 도구를 조합하는 것이 효과적이다.

#### 전략 1: OpenCode + Cursor

```text
[Cursor] - 일상적인 코드 편집, 자동 완성, 시각적 diff 확인
[OpenCode] - 복잡한 리팩토링, 터미널 작업, CI/CD 통합
```

Cursor의 시각적 편집과 OpenCode의 터미널 자유도를 결합하는 전략이다. GUI가 필요한 작업은 Cursor에서, 스크립팅이나 자동화가 필요한 작업은 OpenCode에서 처리한다.

#### 전략 2: OpenCode + Claude Code

```text
[Claude Code] - 복잡한 추론이 필요한 고난도 작업 (Claude Opus)
[OpenCode] - 일상 작업 (Ollama 로컬 모델로 비용 절감)
```

Claude Code의 강점인 깊은 추론 능력과 OpenCode의 비용 효율성을 조합한다.

#### 전략 3: OpenCode 단독 (풀 오픈소스)

```text
[OpenCode + Ollama] - 모든 작업을 로컬에서 무료로 수행
[OpenCode + Cloud API] - 복잡한 작업에만 클라우드 API 사용
```

비용 최소화와 데이터 프라이버시가 최우선인 경우의 전략이다.

### 벤치마크 관점

SWE-bench Verified 기준으로 도구별 성능을 비교하면 다음과 같다.

| 도구 | SWE-bench 점수 | 컨텍스트 윈도우 |
|------|---------------|---------------|
| Claude Code (Opus 4) | ~80.8% | 1M tokens |
| OpenCode (Claude Sonnet 4) | ~70%+ | 모델별 상이 |
| Cursor (GPT-4.1) | ~65%+ | 모델별 상이 |
| OpenCode (Ollama 로컬) | ~40-50% | 모델별 상이 |

:::warning
벤치마크 점수는 참고용이다. 실제 개발에서는 프로젝트 특성, 프롬프트 품질, 컨텍스트 관리에 따라 결과가 크게 달라진다. 높은 벤치마크 점수가 반드시 더 나은 개발 경험을 의미하지는 않는다.
:::

---

## 실전 시나리오

### 시나리오 1: 신규 API 서버 개발

```bash
# 프로젝트 초기화
mkdir my-api && cd my-api
go mod init my-api
opencode
```

```text
# OpenCode에서:

1. Plan 에이전트로 아키텍처 설계
/agent plan
REST API 서버를 설계해줘.
- Clean Architecture 패턴
- PostgreSQL 데이터베이스
- JWT 인증
- 사용자 CRUD + 게시글 CRUD
설계 결과를 .opencode/plans/architecture.md에 작성해줘

2. Build 에이전트로 구현
/agent build
.opencode/plans/architecture.md의 설계대로 구현해줘.
먼저 프로젝트 구조와 도메인 모델부터 시작해줘.

3. 테스트 작성
각 핸들러에 대한 유닛 테스트를 작성해줘.
테스트 커버리지 80% 이상을 목표로 해줘.

4. 문서 생성
/docs  (커스텀 에이전트)
API 문서를 OpenAPI 3.0 형식으로 생성해줘.
```

### 시나리오 2: 레거시 코드 리팩토링

```text
# Plan 모드로 분석
/agent plan
이 프로젝트의 코드 품질 문제를 분석해줘.
- 중복 코드
- 긴 함수
- 복잡한 조건문
- 미사용 코드
우선순위별로 정리하고 리팩토링 계획을 세워줘.

# Build 모드로 실행
/agent build
Plan의 분석 결과를 바탕으로 우선순위 1번부터 리팩토링을 시작해줘.
각 변경 후 테스트가 통과하는지 확인해줘.
!go test ./...
```

### 시나리오 3: 다국어 프로젝트에서 LSP 활용

```text
# TypeScript + Go 혼합 프로젝트
@frontend/src/api.ts 와 @backend/handler.go 사이의
API 인터페이스가 일치하는지 확인해줘.
타입 불일치가 있으면 수정해줘.
```

OpenCode의 LSP 통합은 TypeScript와 Go 모두에서 동작하므로, 프론트엔드와 백엔드의 타입 일관성을 AI가 직접 확인할 수 있다.

### 시나리오 4: CI/CD 파이프라인에서 활용

```bash
#!/bin/bash
# ci-review.sh - PR 자동 리뷰 스크립트

# 변경된 파일 목록
CHANGED_FILES=$(git diff --name-only origin/main...HEAD)

# OpenCode CLI 모드로 리뷰
opencode -m "다음 파일들의 변경사항을 리뷰해줘: $CHANGED_FILES
코드 품질, 버그 가능성, 테스트 커버리지를 확인하고
리뷰 결과를 JSON 형식으로 출력해줘."
```

### 시나리오 5: 커스텀 명령으로 반복 작업 자동화

```markdown
<!-- .opencode/commands/pr-summary.md -->
---
description: "PR용 변경사항 요약 생성"
model: "openai/gpt-4.1-mini"
subtask: true
---

!git diff origin/main...HEAD

위 diff를 분석하여 PR 설명을 작성해줘.
다음 형식을 따라줘:

## Summary
- 주요 변경사항 3줄 요약

## Changes
- 파일별 변경 내용 상세

## Testing
- 테스트 방법 및 확인 사항
```

이 명령은 `/pr-summary`로 실행할 수 있다.

---

## 오픈소스 기여 가이드

### 기여 시작하기

OpenCode는 MIT 라이선스 오픈소스 프로젝트다. 기여는 언제나 환영받는다.

```bash
# 저장소 포크 및 클론
git clone https://github.com/YOUR_USERNAME/opencode.git
cd opencode

# Go 의존성 설치
go mod download

# 빌드 확인
go build ./...

# 테스트 실행
go test ./...
```

### 기여 가능한 영역

| 영역 | 난이도 | 설명 |
|------|--------|------|
| 문서 개선 | 낮음 | 오타 수정, 번역, 예시 추가 |
| 버그 수정 | 중간 | Issue에서 `good first issue` 라벨 확인 |
| 새 LSP 서버 추가 | 중간 | 새 언어의 LSP 서버 통합 |
| 테마 기여 | 낮음 | 커스텀 테마 PR |
| 플러그인 개발 | 중간-높음 | 커뮤니티 플러그인 |
| 새 프로바이더 지원 | 높음 | AI 프로바이더 통합 |
| 코어 기능 개선 | 높음 | TUI, 에이전트 시스템 |

### 이슈 리포팅

```markdown
# 이슈 템플릿 예시

## Description
[문제 설명]

## Steps to Reproduce
1. opencode 실행
2. /model 명령으로 모델 변경
3. [구체적인 재현 단계]

## Expected Behavior
[기대한 동작]

## Actual Behavior
[실제 발생한 동작]

## Environment
- OS: macOS 15.3
- OpenCode version: x.y.z
- Go version: 1.23.x
- Terminal: iTerm2
```

### 개발 환경 설정

```bash
# 개발 모드 실행
go run . --debug

# 특정 패키지 테스트
go test ./internal/tui/...
go test ./internal/lsp/...

# 린팅
golangci-lint run

# 빌드
go build -o opencode .
```

---

## 보안 고려사항

### API 키 관리

팀 환경에서 API 키 관리는 특히 중요하다.

```bash
# 방법 1: 환경 변수 (.env 파일은 .gitignore에 추가)
echo "OPENAI_API_KEY=sk-..." > .env
echo ".env" >> .gitignore

# 방법 2: 시크릿 매니저 연동
export OPENAI_API_KEY=$(vault read -field=key secret/openai)

# 방법 3: opencode auth (개인 인증)
opencode auth login
```

:::warning
API 키를 `opencode.json`에 직접 하드코딩하지 말자. 반드시 `{env:VARIABLE}` 참조 또는 시크릿 매니저를 사용해야 한다. Git에 API 키가 커밋되면 즉시 키를 회전(rotate)하자.
:::

### 코드 프라이버시

| 관심사 | 클라우드 API | 로컬 모델 (Ollama) |
|--------|------------|-------------------|
| 코드 전송 | API 서버로 전송됨 | 로컬에서 처리 |
| 데이터 보존 | 프로바이더 정책에 따름 | 없음 |
| 규정 준수 | 확인 필요 | 완전 통제 |
| 감사 추적 | 제한적 | 완전한 로컬 로그 |

민감한 코드를 다룰 때는 Ollama 로컬 모델 사용을 고려하자.

### 도구 권한 보안

```json
{
  "tools": {
    "bash": {
      "permission": "ask"
    },
    "write": {
      "permission": "ask"
    }
  }
}
```

프로덕션 코드나 인프라 관련 작업에서는 `bash`와 `write` 도구를 반드시 `"ask"` 모드로 설정하여, AI가 실행하기 전에 항상 확인 과정을 거치도록 하자.

---

## 트러블슈팅 종합

### 자주 발생하는 문제와 해결 방법

#### 모델 응답이 느린 경우

```bash
# 네트워크 확인
curl -s https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | head -c 100

# 작은 모델로 전환
/model openai/gpt-4.1-nano
```

#### 컨텍스트 윈도우 초과

```text
# 수동 압축
/compact

# 새 세션 시작
/session new

# compaction 설정 조정
# opencode.json에서 reserved 값 증가
```

#### LSP 관련 오류

```bash
# LSP 서버 재시작
# OpenCode를 종료하고 재시작하면 LSP 서버도 재시작됨

# 특정 LSP 서버 설치 확인
npm list -g typescript-language-server
pip show pyright
which gopls
```

#### 플러그인 로드 실패

```bash
# 플러그인 디렉토리 확인
ls -la .opencode/plugins/

# 디버그 모드로 상세 에러 확인
opencode --debug 2>&1 | grep "plugin"
```

---

## 정리

이 시리즈에서 다룬 OpenCode의 핵심 내용을 종합적으로 정리한다.

### 시리즈 요약

| 글 | 핵심 내용 |
|----|-----------|
| 1편: 시작하기 | 설치, 초기 설정, 멀티 프로바이더 구성, 기본 사용법 |
| 2편: 핵심 기능 | Bubble Tea TUI, 75+ 모델 상세, 도구 시스템, 세션 관리 |
| 3편: 고급 활용 | LSP 통합, 커스텀 설정, MCP 서버, 플러그인, 디버깅 |
| 4편: 실전 (이 글) | 팀 환경 구축, 멀티 모델 전략, 비용 최적화, 마이그레이션 |

### OpenCode가 적합한 경우

- 특정 벤더에 종속되고 싶지 않은 팀
- 여러 AI 모델을 자유롭게 실험하고 싶은 개발자
- 로컬 모델로 비용을 최소화하면서 AI 코딩을 도입하려는 조직
- 데이터 프라이버시가 중요한 프로젝트
- 터미널 중심 워크플로우를 선호하는 개발자
- 오픈소스 도구를 커스터마이징하여 사용하고 싶은 팀

### OpenCode가 부적합한 경우

- GUI 기반 편집을 선호하는 경우 (Cursor가 더 적합)
- 최고 수준의 코드 추론이 항상 필요한 경우 (Claude Code가 더 적합)
- 설정이나 커스터마이징에 시간을 쓰고 싶지 않은 경우

### 앞으로의 전망

OpenCode는 `anomalyco/opencode`에서 활발히 개발이 이루어지고 있다. 95K 이상의 GitHub 스타와 500명 이상의 기여자가 참여하는 대규모 오픈소스 프로젝트로서, AI 코딩 도구의 민주화를 이끌고 있다.

Crush 역시 Charm 팀의 TUI 전문성을 바탕으로 독자적인 발전을 이어가고 있다. 두 프로젝트의 경쟁과 협력이 오픈소스 AI 코딩 생태계 전체를 풍요롭게 만들고 있다.

이것으로 **OpenCode Guide** 시리즈를 마친다. OpenCode는 아카이브되었지만, 그 정신은 Crush로 이어지고 있으며, 오픈소스 AI 코딩 도구의 중요한 이정표로 남아 있다.
