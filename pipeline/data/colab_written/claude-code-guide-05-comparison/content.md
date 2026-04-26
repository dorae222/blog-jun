<!-- infographic-hero -->
![AI Coding Agent Comparison 핵심 요약](figures/infographic.svg)

*Figure: AI Coding Agent Comparison 한 장 요약 인포그래픽*

# AI 코딩 에이전트 비교: Claude Code vs Gemini CLI vs Codex CLI

:::info
이 글은 **Claude Code Guide** 시리즈의 마지막 글로, 주요 AI 코딩 에이전트를 비교 분석한다. 시리즈 전체 목차는 다음과 같다:
1. [[claude-code-guide-01-setup|설치와 기본 사용법]]
2. [[claude-code-guide-02-core|핵심 기능: 도구 시스템과 에이전틱 루프]]
3. [[claude-code-guide-03-advanced|고급 활용: MCP 서버와 서브에이전트]]
4. [[claude-code-guide-04-workflow|실전: 프로젝트 관리와 워크플로우]]
5. **AI 코딩 에이전트 비교** (현재 글)
:::

2025년은 AI 코딩 에이전트의 원년이라 할 수 있다. Anthropic의 Claude Code를 시작으로 OpenAI의 Codex CLI, Google의 Gemini CLI까지 빅테크 3사가 모두 터미널 기반 코딩 에이전트를 출시했다. 이 세 도구는 근본적으로 같은 문제를 해결하지만, 아키텍처 철학, 보안 모델, 확장 방식에서 뚜렷한 차이를 보인다.

이 글에서는 Claude Code, Gemini CLI, Codex CLI를 체계적으로 비교 분석하여 프로젝트와 상황에 맞는 도구를 선택하는 기준을 제시한다.

---

## 비교 대상 소개

### Claude Code (Anthropic)

2025년 2월에 출시된 Claude Code는 터미널 기반 에이전틱 코딩 도구의 선두주자다. Node.js(TypeScript)로 구현되었으며, Anthropic의 Claude 모델 패밀리(Opus, Sonnet, Haiku)를 사용한다. 바이너리 배포 방식으로, 소스 코드는 공개되지 않는다. 코드베이스 전체를 이해하고, 파일 읽기/쓰기, 셸 명령 실행, Git 조작, 웹 검색까지 에이전틱 방식으로 수행하는 것이 핵심 특징이다.

### Gemini CLI (Google)

2025년 6월에 출시된 Gemini CLI는 Google이 내놓은 오픈소스 코딩 에이전트다. Node.js(TypeScript)로 작성되었으며, Apache-2.0 라이선스로 GitHub에 전체 소스가 공개되어 있다. Gemini 2.5 Pro와 Flash 모델을 사용하며, Google AI Studio API를 통해 하루 1,000회 무료 요청이 가능한 넉넉한 무료 티어가 특징이다.

### Codex CLI (OpenAI)

2025년 4월에 출시된 Codex CLI는 OpenAI의 터미널 코딩 에이전트다. 초기에는 TypeScript로 작성되었으나 이후 Rust로 완전히 재작성되어 뛰어난 성능을 보인다. Apache-2.0 오픈소스이며, codex-mini-latest를 기본 모델로 사용한다. 플랫폼 네이티브 샌드박스를 적용한 가장 엄격한 보안 모델이 특징이다.

| 항목 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 출시 | 2025년 2월 | 2025년 6월 | 2025년 4월 |
| 개발사 | Anthropic | Google | OpenAI |
| GitHub 저장소 | 비공개 (바이너리 배포) | google-gemini/gemini-cli | openai/codex |
| 라이선스 | 프로프리에터리 | Apache-2.0 | Apache-2.0 |
| 설치 | `npm i -g @anthropic-ai/claude-code` | `npm i -g @anthropic-ai/gemini-cli` | `cargo install codex-cli` |

---

## 아키텍처 비교

세 도구의 기술 스택과 아키텍처를 비교하면 각각의 설계 철학이 드러난다.

| 항목 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 구현 언어 | Node.js (TypeScript) | Node.js (TypeScript) | Rust |
| 오픈소스 | No (바이너리 배포) | Yes (Apache-2.0) | Yes (Apache-2.0) |
| 기본 모델 | Claude Sonnet 4 | Gemini 2.5 Pro | codex-mini-latest |
| 사용 가능 모델 | Opus 4, Sonnet 4, Haiku 3.5 | Gemini 2.5 Pro, 2.5 Flash | codex-mini-latest, o4-mini, GPT-4.1 |
| 멀티모델 | Anthropic 전용 | Google 전용 | OpenAI 전용 |
| 컨텍스트 윈도우 | 200K 토큰 | 1M+ 토큰 | 200K 토큰 |
| 멀티모달 입력 | 이미지 | 이미지 | 이미지 |
| 바이너리 크기 | ~50MB (npm) | ~30MB (npm) | ~10MB (Rust 바이너리) |

:::tip
Codex CLI의 Rust 구현은 콜드 스타트 시간과 메모리 사용량에서 뚜렷한 장점이 있다. Node.js 기반 도구가 시작에 1-2초 걸리는 반면, Codex CLI는 거의 즉시 시작된다.
:::

### 에이전틱 루프 구조

세 도구 모두 "사용자 입력 - 모델 추론 - 도구 호출 - 결과 반영 - 다음 추론"의 에이전틱 루프를 따르지만, 세부 구현에 차이가 있다.

**Claude Code**는 가장 정교한 에이전틱 루프를 갖추고 있다. 서브에이전트(Agent 도구)를 통해 병렬 탐색이 가능하고, 컨텍스트 압축을 자동으로 수행하며, 도구 호출 전후에 Hooks를 삽입할 수 있다.

**Gemini CLI**는 Google의 강점인 대규모 컨텍스트를 활용한다. 1M 토큰 이상의 컨텍스트 윈도우 덕분에 대규모 코드베이스도 한 번에 처리할 수 있으며, Extensions 시스템으로 도구를 확장할 수 있다.

**Codex CLI**는 최소주의 접근을 취한다. 핵심 도구 6개로 대부분의 작업을 처리하며, Rust의 성능 덕분에 빠른 응답이 가능하다. 대신 서브에이전트나 고급 확장 기능은 제한적이다.

---

## 도구 시스템 비교

AI 코딩 에이전트의 실질적인 능력은 사용할 수 있는 도구에 의해 결정된다. 세 도구의 빌트인 도구 시스템을 비교한다.

### 빌트인 도구 수

| 도구 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 빌트인 도구 수 | 10+ | 12 | 6 |
| 접근 방식 | 풍부한 전용 도구 | 균형잡힌 도구 + Extensions | 최소 핵심 도구 |

### 기능별 도구 매핑

각 도구가 어떤 기능에 대응하는지 매핑한 테이블이다.

| 기능 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 파일 읽기 | Read | ReadFile | read_file |
| 파일 쓰기 | Write | WriteFile | write_file |
| 파일 편집 | Edit (정밀 교체) | EditFile (diff 기반) | apply_diff |
| 셸 실행 | Bash | RunCommand | shell |
| 파일 검색 | Glob (패턴 매칭) | ListDirectory + SearchFiles | list_dir (제한적) |
| 텍스트 검색 | Grep (ripgrep 기반) | SearchFiles (ripgrep) | shell + grep |
| 웹 검색 | WebSearch | WebSearch (Google Search) | 미지원 |
| 웹 페이지 | WebFetch | WebFetch | 미지원 |
| 서브에이전트 | Agent (병렬 탐색) | 미지원 | 미지원 |
| 이미지 분석 | Read (이미지 경로) | ReadFile (이미지) | read_file (이미지) |
| 노트북 편집 | NotebookEdit | 미지원 | 미지원 |
| 메모리/컨텍스트 | CLAUDE.md 자동 로드 | .gemini/context.md | codex.md |

### 도구 철학의 차이

**Claude Code**는 "모든 작업에 최적의 도구"를 지향한다. 파일 검색에 Glob(패턴 매칭)과 Grep(내용 검색)을 분리하고, Edit은 정확한 문자열 교체 방식으로 정밀한 수정을 지원한다. 서브에이전트(Agent)는 독립적인 탐색 태스크를 병렬로 처리할 수 있는 고유한 기능이다.

**Gemini CLI**는 "실용적인 완성도"를 추구한다. 12개의 빌트인 도구가 대부분의 시나리오를 커버하며, Extensions를 통해 제3자 도구를 추가할 수 있다. Google Search 기반의 WebSearch가 강점이다.

**Codex CLI**는 "단순함이 최고"라는 철학이다. 6개 핵심 도구만으로 동작하며, 복잡한 작업은 shell 도구를 통해 기존 CLI 도구를 호출하는 방식으로 해결한다. 웹 검색 같은 기능은 아예 제공하지 않는다.

:::info
Claude Code의 Agent(서브에이전트) 도구는 다른 두 도구에 없는 고유한 기능이다. 대규모 코드베이스에서 여러 파일을 동시에 탐색하거나, 복잡한 리팩토링에서 영향 범위를 파악할 때 특히 유용하다.
:::

---

## 보안/샌드박스 모델

AI 코딩 에이전트가 파일 시스템과 셸에 접근할 수 있기 때문에, 보안 모델은 선택에서 매우 중요한 요소다.

### Claude Code의 보안 모델

Claude Code는 **권한 기반 3단계 승인 시스템**을 사용한다.

| 단계 | 설명 | 예시 |
|------|------|------|
| 자동 허용 | allowlist에 등록된 도구/명령 | 파일 읽기, Glob, Grep |
| 확인 필요 | 승인 프롬프트 표시 | 파일 쓰기, 셸 명령 |
| 차단 | denylist에 등록된 명령 | `rm -rf`, `git push --force` |

설정 파일(`settings.json`)에서 글로브 패턴으로 파일 범위를 제한할 수 있다:

```json
{
  "permissions": {
    "allow": ["Read", "Glob", "Grep", "Bash(git status)"],
    "deny": ["Bash(rm -rf *)"]
  }
}
```

**Yolo 모드**를 활성화하면 모든 도구 호출이 자동 승인되어 완전 자동화가 가능하다. CI/CD 파이프라인에서 유용하지만, 신뢰할 수 있는 환경에서만 사용해야 한다.

### Gemini CLI의 보안 모델

Gemini CLI는 **컨테이너 기반 샌드박스 프로필**을 제공한다.

| 프로필 | 격리 수준 | 파일 접근 | 네트워크 | 사용 사례 |
|--------|----------|----------|---------|----------|
| none | 없음 | 전체 | 전체 | 개발/디버깅 |
| docker | 중간 | 작업 디렉토리 | 허용 | 일반 개발 |
| snappy | 높음 | 작업 디렉토리 | 제한 | 보안 민감 작업 |
| firecracker | 최고 | 마운트된 경로만 | 차단 | 프로덕션/CI |

Gemini CLI도 allowlist와 yolo 모드를 지원하며, 설정 파일(`~/.gemini/settings.json`)에서 세부 권한을 관리할 수 있다. 오픈소스이므로 샌드박스 코드를 직접 검증할 수 있다는 것이 장점이다.

### Codex CLI의 보안 모델

Codex CLI는 **플랫폼 네이티브 샌드박스**를 사용하여 가장 엄격한 기본 보안을 제공한다.

| 플랫폼 | 샌드박스 기술 | 특징 |
|--------|-------------|------|
| macOS | Seatbelt (sandbox-exec) | 커널 레벨 프로세스 격리 |
| Linux | Bubblewrap + Landlock | 네임스페이스 격리 + 파일 접근 제한 |

세 가지 실행 모드가 있다:

| 모드 | 파일 읽기 | 파일 쓰기 | 네트워크 | 자동 실행 |
|------|----------|----------|---------|----------|
| suggest | O | X | X | X (제안만) |
| auto-edit | O | O | X | 파일 수정만 |
| full-auto | O | O | O | O |

기본 모드는 `suggest`로, 코드를 제안만 하고 직접 수정하지 않는다. 이는 세 도구 중 가장 보수적인 기본 설정이다.

:::warning
`full-auto` 모드는 네트워크 접근까지 허용하므로, 신뢰할 수 없는 코드베이스에서는 사용을 피해야 한다. 특히 `package.json`의 postinstall 스크립트 등을 통한 공급망 공격에 주의가 필요하다.
:::

### 보안 모델 요약 비교

| 항목 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 기본 보안 수준 | 중간 (확인 프롬프트) | 중간 (프로필 선택) | 높음 (suggest 모드) |
| 샌드박스 방식 | 권한 목록 기반 | 컨테이너 기반 | 플랫폼 네이티브 |
| 커널 레벨 격리 | X | Docker/Firecracker | Seatbelt/Bubblewrap |
| 네트워크 차단 | X (denylist로 부분 제한) | 프로필에 따라 | suggest/auto-edit 모드 |
| 오픈소스 검증 | X | O | O |
| 완전 자동화 | Yolo 모드 | Yolo 모드 | full-auto 모드 |

---

## 확장성 비교

프로젝트에 맞게 도구를 커스터마이징하는 확장성은 장기적인 생산성에 큰 영향을 미친다.

### 확장 메커니즘 비교

| 확장 방식 | Claude Code | Gemini CLI | Codex CLI |
|----------|------------|------------|-----------|
| MCP 서버 | O (풍부한 생태계) | O (지원) | X (미지원) |
| Hooks | O (PreToolCall, PostToolCall, 알림 등) | O (PreToolCall, PostToolCall) | X |
| 커스텀 슬래시 명령 | O (`.claude/commands/`) | X | X |
| 서브에이전트 | O (Agent 도구) | X | X |
| Extensions | X | O (빌트인 + 제3자) | X |
| 오픈소스 포크 | X (프로프리에터리) | O (Apache-2.0) | O (Apache-2.0) |
| 프로젝트 설정 | CLAUDE.md | .gemini/context.md | codex.md |

### MCP (Model Context Protocol)

MCP는 AI 모델이 외부 도구/데이터 소스에 접근하는 표준 프로토콜이다. Claude Code와 Gemini CLI 모두 MCP를 지원하지만, 생태계 성숙도에 차이가 있다.

**Claude Code**는 MCP의 원조라 할 수 있다. Anthropic이 MCP 표준을 주도했으며, 가장 넓은 서버 생태계를 가지고 있다. GitHub, Slack, 데이터베이스, 모니터링 도구 등 수백 개의 MCP 서버가 존재한다.

**Gemini CLI**도 MCP를 지원하며, 기존 MCP 서버를 그대로 사용할 수 있다. 하지만 자체 Extensions 시스템도 제공하여, MCP가 아닌 독자적인 확장도 가능하다.

**Codex CLI**는 현재 MCP를 지원하지 않는다. Rust 기반 아키텍처의 확장은 소스 코드를 직접 수정하는 방식으로 이루어진다.

### Hooks 시스템

Claude Code와 Gemini CLI 모두 도구 호출 전후에 스크립트를 실행하는 Hooks를 지원한다.

```json
// Claude Code Hooks 예시
{
  "hooks": {
    "PreToolCall": [
      {
        "matcher": "Bash",
        "script": "echo 'Bash 명령 실행 전 로깅'"
      }
    ],
    "PostToolCall": [
      {
        "matcher": "Write",
        "script": "npx prettier --write $FILE_PATH"
      }
    ]
  }
}
```

Claude Code는 추가로 `Notification`, `Stop` 등 다양한 Hook 포인트를 제공하며, Gemini CLI는 `PreToolCall`과 `PostToolCall`을 지원한다.

### 프로젝트 설정 파일

세 도구 모두 프로젝트별 컨텍스트 파일을 지원하지만, 구조와 기능에 차이가 있다.

| 항목 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 파일명 | CLAUDE.md | .gemini/context.md | codex.md |
| 위치 | 프로젝트 루트 | .gemini/ 디렉토리 | 프로젝트 루트 |
| 글로벌 설정 | ~/.claude/CLAUDE.md | ~/.gemini/context.md | ~/.codex/codex.md |
| 자동 로드 | O | O | O |
| 하위 디렉토리 | O (경로별 CLAUDE.md) | O | X |
| 동적 포함 | O (서브에이전트가 참조) | X | X |

:::tip
세 도구를 함께 사용하는 프로젝트라면, 각 설정 파일에 공통 규칙을 작성하되, 도구별 특화 설정을 추가하는 방식이 효율적이다. 예를 들어, 코딩 컨벤션은 공통으로, MCP 서버 설정은 Claude Code에만 넣는 식이다.
:::

---

## 성능 및 비용

### 응답 속도

체감 응답 속도는 모델, 작업 복잡도, 네트워크 상태에 따라 크게 달라지지만, 일반적인 경향은 다음과 같다.

| 시나리오 | Claude Code | Gemini CLI | Codex CLI |
|---------|------------|------------|-----------|
| 단순 파일 읽기/편집 | 보통 (2-5초) | 보통 (2-5초) | 빠름 (1-3초) |
| 복잡한 멀티스텝 추론 | 빠름 (Opus 강력) | 보통 | 보통 (o4-mini) |
| 대규모 코드베이스 분석 | 보통 (서브에이전트 병렬) | 빠름 (1M 컨텍스트) | 느림 (컨텍스트 제한) |
| 콜드 스타트 | 1-2초 | 1-2초 | <1초 |

Codex CLI는 Rust 바이너리라서 시작 시간이 가장 빠르고, Gemini CLI는 대규모 컨텍스트 윈도우로 대형 코드베이스 분석에서 강점이 있다. Claude Code는 Opus 모델의 추론 능력이 복잡한 태스크에서 두드러진다.

### 가격 모델

| 항목 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 과금 방식 | API 토큰 / 구독 | API 토큰 / 무료 티어 | API 토큰 / 구독 |
| 무료 티어 | X | O (1,000 req/day) | X |
| 구독 플랜 | Max ($100/월, $200/월) | API 키 기반 | Pro ($20/월), Pro+ ($200/월) |
| API 입력 가격 | $3/M (Sonnet), $15/M (Opus) | $1.25/M (Flash), $1.25-10/M (Pro) | $0.15/M (codex-mini), $1.1/M (o4-mini) |
| API 출력 가격 | $15/M (Sonnet), $75/M (Opus) | $10/M (Flash), $10/M (Pro) | $0.6/M (codex-mini), $4.4/M (o4-mini) |
| 구독 내 사용 | Max 구독 시 무제한 | 해당 없음 | Pro/Pro+ 구독 시 포함 |

:::info
**비용 최적화 전략**: 일상적인 코딩 작업에는 Gemini CLI의 무료 티어를 활용하고, 복잡한 아키텍처 설계나 대규모 리팩토링에는 Claude Code(Opus)를 사용하는 조합이 비용 대비 효율적이다.
:::

### 토큰 효율성

동일한 작업을 수행할 때 소비하는 토큰 양도 중요한 비용 요소다.

| 요소 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 시스템 프롬프트 | 큼 (도구 정의 포함) | 중간 | 작음 (최소 도구) |
| 도구 호출 오버헤드 | 중간 | 중간 | 낮음 |
| 컨텍스트 압축 | O (자동) | O (1M 윈도우로 덜 필요) | X (제한적) |
| 캐싱 | O (프롬프트 캐싱) | O | O |

Claude Code는 Extended Thinking과 프롬프트 캐싱을 통해 토큰 효율성을 높이고, Gemini CLI는 넓은 컨텍스트 윈도우로 잦은 재로딩을 줄인다. Codex CLI는 최소 도구 세트로 시스템 프롬프트 오버헤드가 가장 적다.

---

## 개발자 경험 비교

### IDE 통합

| 통합 방식 | Claude Code | Gemini CLI | Codex CLI |
|----------|------------|------------|-----------|
| VS Code 확장 | O (공식) | O (Gemini Code Assist) | X (별도 확장 없음) |
| JetBrains 통합 | O (터미널) | O (Gemini 플러그인) | X |
| 터미널 기본 | O | O | O |
| 데스크톱 앱 | X | X | X |
| 웹 앱 | O (Claude.ai 연동) | O (AI Studio) | O (ChatGPT 연동) |
| GitHub 통합 | O (claude-bot PR 리뷰) | X | O (codex-bot) |

### 대화 이어가기/히스토리

| 기능 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 세션 지속 | O (`--continue`, `--resume`) | O (세션 히스토리) | O (`--continue`) |
| 히스토리 검색 | O | 제한적 | 제한적 |
| 세션 내보내기 | O (JSON) | O | X |
| 멀티 세션 | O (여러 터미널) | O | O |

### 컨텍스트 관리

| 기능 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 자동 컨텍스트 수집 | O (git, 디렉토리 구조) | O (프로젝트 분석) | O (제한적) |
| 컨텍스트 압축 | O (자동, 수동 `/compact`) | O (대용량 윈도우) | 제한적 |
| 이미지 입력 | O (드래그 앤 드롭) | O | O |
| URL 참조 | O (WebFetch) | O (WebFetch) | X |
| 파일 참조 | O (경로 자동 감지) | O | O |

### 학습 곡선

| 항목 | Claude Code | Gemini CLI | Codex CLI |
|------|------------|------------|-----------|
| 초기 설정 난이도 | 낮음 | 낮음 | 중간 (Rust 툴체인) |
| 기본 사용법 | 쉬움 | 쉬움 | 쉬움 |
| 고급 기능 마스터 | 높음 (MCP, Hooks, 서브에이전트) | 중간 (Extensions) | 낮음 (기능이 적음) |
| 문서화 수준 | 우수 | 양호 | 양호 |
| 커뮤니티 | 대규모 | 성장 중 | 중간 |

---

## 실전 시나리오별 비교

실제 개발 작업에서 각 도구가 어떤 성능을 보이는지 시나리오별로 비교한다.

### 시나리오 1: 대규모 리팩토링

100개 이상의 파일에 걸친 리팩토링 작업이다.

| 평가 항목 | Claude Code | Gemini CLI | Codex CLI |
|----------|------------|------------|-----------|
| 코드 이해 | 우수 (서브에이전트 병렬 탐색) | 우수 (1M 컨텍스트) | 보통 |
| 수정 정확도 | 우수 (Edit 도구 정밀) | 양호 | 양호 |
| 일관성 유지 | 우수 (CLAUDE.md 규칙) | 양호 | 보통 |
| 속도 | 보통 | 빠름 | 보통 |

### 시나리오 2: 버그 수정

에러 로그를 분석하고 원인을 찾아 수정하는 작업이다.

| 평가 항목 | Claude Code | Gemini CLI | Codex CLI |
|----------|------------|------------|-----------|
| 로그 분석 | 우수 | 양호 | 양호 |
| 원인 추적 | 우수 (Grep + Agent) | 양호 (SearchFiles) | 보통 (shell 조합) |
| 수정 제안 | 우수 | 양호 | 양호 |
| 테스트 실행 | 우수 (Bash) | 양호 (RunCommand) | 양호 (shell) |

### 시나리오 3: 새 기능 구현

설계부터 구현, 테스트까지 전체 과정이다.

| 평가 항목 | Claude Code | Gemini CLI | Codex CLI |
|----------|------------|------------|-----------|
| 설계 논의 | 우수 (Opus 추론) | 양호 | 보통 |
| 보일러플레이트 생성 | 우수 | 우수 | 양호 |
| 멀티파일 생성 | 우수 | 양호 | 보통 |
| 테스트 작성 | 우수 | 양호 | 양호 |

---

## 선택 가이드

### Claude Code를 선택해야 할 때

- **복잡한 멀티스텝 작업**: 서브에이전트를 활용한 병렬 탐색과 정교한 에이전틱 루프가 필요할 때
- **최고 수준의 추론 능력**: Claude Opus의 추론 능력은 아키텍처 설계, 복잡한 버그 추적에서 두드러진다
- **MCP 생태계 활용**: GitHub, Slack, DB 등 다양한 외부 도구와 연동이 필요할 때
- **프로젝트 규칙 관리**: CLAUDE.md를 통한 체계적인 프로젝트 컨텍스트 관리가 중요할 때
- **CI/CD 통합**: GitHub Actions, 자동 PR 리뷰 등 워크플로우 자동화가 필요할 때

### Gemini CLI를 선택해야 할 때

- **Google 생태계 연동**: Google Cloud, Firebase, Android 등 Google 서비스와 통합이 필요할 때
- **무료 티어 활용**: 하루 1,000회 무료 요청으로 비용 없이 시작하고 싶을 때
- **대규모 코드베이스**: 1M+ 토큰 컨텍스트로 대형 모노레포를 한 번에 분석해야 할 때
- **오픈소스 선호**: 소스 코드를 검증하거나 커스터마이징하고 싶을 때
- **Extensions**: Google 고유의 확장 시스템을 활용하고 싶을 때

### Codex CLI를 선택해야 할 때

- **최대 보안 요구**: 플랫폼 네이티브 샌드박스로 가장 엄격한 격리가 필요할 때
- **Rust 성능**: 콜드 스타트 시간과 메모리 사용량이 중요한 CI/CD 환경
- **OpenAI 생태계**: GPT-4.1, o4-mini 등 OpenAI 모델을 이미 사용하고 있을 때
- **최소주의 선호**: 복잡한 설정 없이 핵심 기능만 빠르게 사용하고 싶을 때
- **오픈소스 기여**: Rust 코드베이스에 직접 기여하고 싶을 때

### 의사결정 플로차트

다음 질문에 순서대로 답하면 적합한 도구를 빠르게 찾을 수 있다:

1. **무료로 시작하고 싶은가?** - Yes이면 **Gemini CLI**
2. **보안이 최우선인가?** - Yes이면 **Codex CLI**
3. **복잡한 멀티스텝 작업이 주인가?** - Yes이면 **Claude Code**
4. **Google Cloud/Firebase를 사용하는가?** - Yes이면 **Gemini CLI**
5. **OpenAI API를 이미 사용하는가?** - Yes이면 **Codex CLI**
6. **MCP 서버 연동이 필요한가?** - Yes이면 **Claude Code** 또는 **Gemini CLI**

:::tip
하나의 도구만 사용해야 한다는 법은 없다. 실제로 많은 개발자들이 일상 작업에는 Gemini CLI(무료 티어), 복잡한 설계 작업에는 Claude Code(Opus), 보안 민감한 작업에는 Codex CLI를 조합해서 사용한다.
:::

---

## 오픈소스 대안

빅테크 3사 외에도 주목할 만한 오픈소스 AI 코딩 에이전트들이 있다.

### 주요 오픈소스 도구

| 도구 | 언어 | 특징 | 모델 지원 | GitHub Stars |
|------|------|------|----------|-------------|
| Crush (구 OpenCode) | Go + Bubble Tea | TUI 인터페이스, LSP 통합 | 75+ 모델 (OpenAI, Anthropic, Ollama 등) | 10K+ |
| Aider | Python | 다중 모델, Git 통합 | OpenAI, Anthropic, Ollama 등 | 25K+ |
| Continue | TypeScript | VS Code/JetBrains 확장 | 다중 모델 | 20K+ |
| OpenClaw | TypeScript | 메시징 기반 범용 에이전트 | 다중 모델 | 1K+ |

### Crush (구 OpenCode)

Go와 Bubble Tea TUI 프레임워크로 구현된 터미널 코딩 에이전트다. 가장 큰 강점은 **75개 이상의 모델 지원**으로, OpenAI, Anthropic, Google, Ollama, OpenRouter 등 거의 모든 LLM 제공자를 지원한다. LSP(Language Server Protocol) 통합으로 IDE 수준의 코드 인텔리전스를 터미널에서 제공하며, 로컬 모델을 사용하면 완전히 오프라인으로 동작할 수 있다.

### Aider

Python으로 구현된 선구적인 AI 코딩 도구로, Claude Code 이전부터 터미널 기반 AI 코딩을 개척했다. Git과의 깊은 통합이 특징으로, 모든 AI 수정 사항을 자동으로 커밋하고 변경 이력을 관리한다. 다중 모델을 지원하며, 벤치마크 리더보드를 통해 모델별 코딩 성능을 투명하게 공개한다.

### Continue

VS Code와 JetBrains IDE에서 동작하는 오픈소스 AI 코딩 확장이다. 터미널 기반이 아닌 IDE 네이티브 경험을 제공하며, 자동완성, 인라인 편집, 채팅 등 다양한 인터페이스를 지원한다. 다중 모델을 지원하고, 로컬 모델(Ollama)과도 연동할 수 있다.

### OpenClaw

메시징 기반의 범용 AI 에이전트로, WhatsApp, Telegram, Slack 등 다양한 메시징 플랫폼에서 코딩 에이전트를 실행할 수 있다. 터미널이 아닌 메시징 앱에서 코드 작업을 지시할 수 있어, 모바일 환경에서의 원격 개발에 유용하다.

### 오픈소스 대안을 고려해야 할 때

| 조건 | 추천 도구 |
|------|----------|
| 로컬 모델(Ollama)로 오프라인 작업 | Crush, Aider, Continue |
| 75+ 다양한 모델을 자유롭게 전환 | Crush |
| IDE 통합이 필수 | Continue |
| Git 워크플로우 자동화 | Aider |
| 모바일/메시징 기반 원격 개발 | OpenClaw |
| 벤더 종속 없이 사용 | Crush, Aider |

---

## 향후 전망

AI 코딩 에이전트 시장은 2025년에 폭발적으로 성장했으며, 2026년에는 다음과 같은 트렌드가 예상된다.

**멀티모델 지원 확대**: 현재 각 도구가 자사 모델만 지원하지만, 오픈소스 진영을 중심으로 멀티모델 지원이 표준이 되어가고 있다. 빅테크 도구들도 점차 다른 모델을 지원할 가능성이 있다.

**MCP 표준화 가속**: MCP가 AI 도구 연동의 사실상 표준으로 자리잡으면서, Codex CLI도 MCP 지원을 추가할 것으로 예상된다. MCP 생태계의 도구 수는 계속 증가하고 있다.

**보안 강화**: 코딩 에이전트가 프로덕션 환경에서 사용되면서, 샌드박스와 권한 관리가 더욱 정교해질 것이다. Codex CLI의 플랫폼 네이티브 샌드박스 접근이 업계 표준이 될 수 있다.

**팀 협업 기능**: 개인 도구에서 팀 도구로 진화하면서, 공유 설정, 팀별 권한, 코드 리뷰 통합 등 협업 기능이 강화될 것이다.

---

## 정리

세 도구를 한 문장으로 요약하면 다음과 같다:

- **Claude Code**: 가장 강력한 추론과 가장 풍부한 확장 생태계
- **Gemini CLI**: 가장 넓은 컨텍스트와 가장 관대한 무료 티어
- **Codex CLI**: 가장 엄격한 보안과 가장 빠른 성능

| 최종 비교 | Claude Code | Gemini CLI | Codex CLI |
|----------|------------|------------|-----------|
| 추론 능력 | ★★★★★ | ★★★★ | ★★★★ |
| 도구 풍부함 | ★★★★★ | ★★★★ | ★★★ |
| 보안 | ★★★★ | ★★★★ | ★★★★★ |
| 성능/속도 | ★★★★ | ★★★★ | ★★★★★ |
| 비용 효율 | ★★★ | ★★★★★ | ★★★★ |
| 확장성 | ★★★★★ | ★★★★ | ★★★ |
| 오픈소스 | ★★ | ★★★★★ | ★★★★★ |
| 학습 곡선 | ★★★ | ★★★★ | ★★★★★ |

이것으로 **Claude Code Guide** 시리즈를 마친다. 설치부터 핵심 기능, 고급 활용, 실전 워크플로우, 그리고 다른 도구와의 비교까지 다루었다. AI 코딩 에이전트는 빠르게 발전하고 있으며, 각 도구의 강점을 이해하고 프로젝트에 맞게 선택하는 것이 중요하다.

가장 좋은 전략은 하나의 도구에 올인하는 것이 아니라, 상황에 맞게 여러 도구를 조합하는 것이다. 무료 티어로 시작하고, 필요에 따라 유료 도구를 추가하며, 프로젝트의 보안 요구사항에 맞는 샌드박스 모델을 선택하자. AI 코딩 에이전트는 더 이상 선택이 아닌 필수가 되어가고 있으며, 이 시리즈가 도구 선택과 활용에 도움이 되었기를 바란다.
