# OpenCode: Go 네이티브 AI 코딩 TUI

## 개요

OpenCode는 Go로 작성된 오픈소스 터미널 기반 AI 코딩 도구로, [[claude-code|Claude Code]]에서 영감을 받아 개발되었다. 가장 큰 차별점은 **풍부한 TUI(Terminal User Interface)**와 **Go 네이티브 구현**으로, 빠른 실행 속도와 단일 바이너리 배포를 달성한 점이다.

Anthropic, OpenAI, Google, Groq, AWS Bedrock, Azure OpenAI 등 주요 LLM 프로바이더를 모두 지원하며, LSP(Language Server Protocol) 통합을 통해 코드 인텔리전스를 에이전트에게 직접 제공한다.

---

## 아키텍처 상세

### Go 네이티브 TUI

OpenCode는 Go의 Bubble Tea(TUI 프레임워크)를 사용하여 터미널 내에서 리치 인터페이스를 제공한다:

- **구문 강조**: 코드 블록에 syntax highlighting 적용
- **diff 뷰**: 파일 변경 사항을 시각적으로 표시
- **파일 트리**: 프로젝트 구조를 사이드 패널로 탐색
- **대화 이력**: 세션별 대화 관리 및 검색

### 멀티 프로바이더 지원

| 프로바이더 | 지원 모델 |
|-----------|----------|
| Anthropic | Claude 4 Opus/Sonnet, Claude 3.5 |
| OpenAI | GPT-4.1, o4-mini, o3 |
| Google | Gemini 2.5 Pro/Flash |
| Groq | LLaMA, Mixtral |
| AWS Bedrock | Claude, Titan |
| Azure OpenAI | GPT-4 시리즈 |
| Ollama | 로컬 모델 |

설정 파일(`opencode.json`)에서 프로바이더와 모델을 지정한다. 대화 중에도 `@model` 명령으로 모델을 전환할 수 있다.

### LSP 통합

OpenCode는 LSP 클라이언트를 내장하여 에이전트에게 코드 인텔리전스를 제공한다:

- **정의 이동**: 함수/클래스 정의 위치 확인
- **참조 찾기**: 심볼의 사용처 탐색
- **자동완성**: 코드 작성 시 제안
- **진단**: 문법 오류 및 경고 감지

이를 통해 에이전트가 코드베이스를 더 정확하게 이해하고 수정할 수 있다.

### 핵심 도구

| 도구 | 기능 |
|------|------|
| ReadFile / WriteFile | 파일 읽기/쓰기 |
| Bash | 셸 명령 실행 |
| Glob / Grep | 파일 및 내용 검색 |
| Fetch | URL 내용 가져오기 |
| Diagnostics | LSP 기반 코드 진단 |

---

## 핵심 혁신

1. **Go 네이티브**: 컴파일된 단일 바이너리, 빠른 시작 속도, 런타임 의존성 없음
2. **리치 TUI**: 터미널 내에서 구문 강조, diff 뷰, 파일 트리 등 풍부한 UI
3. **멀티 프로바이더**: 주요 LLM 프로바이더를 모두 지원, 대화 중 모델 전환 가능
4. **LSP 통합**: 코드 인텔리전스를 에이전트에 직접 제공하여 정확도 향상
5. **세션 관리**: 대화 이력 저장 및 검색, 이전 세션 재개 가능

---

## Claude Code와의 비교

| 특성 | OpenCode | [[claude-code|Claude Code]] |
|------|----------|-------------|
| 구현 언어 | Go | Node.js/TypeScript |
| UI | 리치 TUI (Bubble Tea) | 기본 터미널 |
| 모델 지원 | 멀티 프로바이더 | Claude 전용 |
| LSP 통합 | 내장 | 없음 (Glob/Grep 기반) |
| 배포 | 단일 바이너리 | npm 패키지 |
| 라이선스 | MIT | 프로프라이어터리 |

---

## 관련 문서

- [[claude-code|Claude Code]] - 영감을 준 에이전틱 코딩 도구
- [[openclaw|OpenClaw]] - 또 다른 오픈소스 에이전틱 코딩 CLI
- [[gemini-cli|Gemini CLI]] - Google의 에이전틱 코딩 도구
- [[codex-cli|Codex CLI]] - OpenAI의 에이전틱 코딩 도구
