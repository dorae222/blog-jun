<!-- infographic-hero -->
![Gemini CLI 핵심 요약](figures/infographic.svg)

*Figure: Gemini CLI 한 장 요약 인포그래픽*

# Gemini CLI: Google의 오픈소스 AI 코딩 에이전트

## 개요

Gemini CLI는 Google이 2025년 6월 공개한 오픈소스 에이전틱 코딩 도구로, [[gemini-2-5|Gemini 2.5 Pro]] 모델을 기반으로 터미널에서 직접 실행된다. [[claude-code|Claude Code]]와 유사하게 파일 읽기/쓰기, 셸 명령 실행, 웹 검색 등을 에이전틱 루프 방식으로 수행하며, Google AI Studio API 키를 통해 무료로 사용할 수 있다는 점이 큰 차별점이다.

`npx @google/gemini-cli` 또는 npm/Homebrew로 설치하며, `gemini` 명령어로 터미널에서 바로 실행할 수 있다. Apache-2.0 라이선스로 완전한 오픈소스 프로젝트이며, TypeScript 모노레포(Ink 6 + React 19 기반 TUI + 독립 core 라이브러리)로 구성된다. 2026년 3월 기준 99K+ GitHub stars, v0.35.3.

---

## 아키텍처 상세

### 에이전틱 루프

Gemini CLI는 다른 에이전틱 코딩 도구와 마찬가지로 "이해 - 검색 - 계획 - 실행 - 검증" 루프를 따른다:

$$\text{Understand} \rightarrow \text{Search} \rightarrow \text{Plan} \rightarrow \text{Execute} \rightarrow \text{Verify}$$

사용자의 자연어 요청을 Gemini 2.5 Pro가 해석하고, 내장 도구를 활용하여 코드베이스를 탐색한 뒤, 실제 파일 수정과 명령 실행을 수행한다.

### 내장 도구 (12종)

| 도구 | 기능 |
|------|------|
| ReadFile / ReadManyFiles | 파일 읽기 |
| WriteFile / Edit (replace) | 파일 쓰기/수정 |
| Shell | 셸 명령 실행 |
| Glob / SearchText | 파일 검색/내용 검색 |
| ReadFolder | 디렉토리 탐색 |
| WebFetch | 웹 페이지 가져오기 |
| GoogleSearch | Google 검색 그라운딩 |
| CodebaseInvestigator | 코드베이스 탐색 에이전트 |
| SaveMemory / WriteTodos | 메모리 저장/작업 관리 |

### MCP 서버 + Hooks

[[mcp|MCP]](Model Context Protocol)를 통해 외부 도구를 확장할 수 있다. settings.json의 `mcpServers`에서 정의하며, `/mcp` 명령으로 서버 상태를 확인할 수 있다.

**Hooks 시스템**: 에이전틱 루프의 주요 지점에서 동작을 가로채고 수정할 수 있다. 컨텍스트 주입, 보안 정책 적용, 응답 검열 등에 활용한다.

### GEMINI.md 계층적 컨텍스트

`GEMINI.md` 파일은 계층적으로 로드된다:

1. `~/.gemini/GEMINI.md` (사용자 수준)
2. 프로젝트 루트 `GEMINI.md`
3. 현재 디렉토리 `GEMINI.md`

Claude Code의 `CLAUDE.md`와 동일한 개념이며, `/init` 명령으로 자동 생성할 수 있다.

### 샌드박스 프로필

| 프로필 | 설명 |
|--------|------|
| permissive-open (기본) | 프로젝트 폴더 내 쓰기 제한 |
| restrictive-open | 기본적으로 작업 거부 |
| strict-open | 읽기/쓰기 모두 작업 디렉토리로 제한 |
| strict-proxied | strict + 네트워크 프록시 경유 |

---

## 핵심 혁신

1. **무료 접근성**: Google AI Studio API 키로 월 1,000회 무료 요청 제공 (Rate Tier 1). 유료 전환 없이 상당한 수준의 에이전틱 코딩 경험 가능
2. **1M 토큰 컨텍스트**: Gemini 2.5 Pro의 100만 토큰 컨텍스트 윈도우를 활용하여 대규모 코드베이스 전체를 한 번에 이해
3. **Google 생태계 통합**: Google Search 네이티브 지원, Vertex AI 연동을 통한 엔터프라이즈 확장
4. **멀티모달 입력**: 텍스트뿐 아니라 이미지, 스크린샷 등 멀티모달 입력을 직접 처리
5. **완전 오픈소스**: Apache-2.0 라이선스로 소스 코드 전체 공개, 커뮤니티 기여 활발

---

## Claude Code와의 비교

| 특성 | Gemini CLI | [[claude-code|Claude Code]] |
|------|-----------|-------------|
| 개발사 | Google | Anthropic |
| 기반 모델 | Gemini 2.5 Pro | Claude 4 시리즈 |
| 컨텍스트 | 1M+ 토큰 | 200K+ 토큰 |
| 가격 | 무료 (월 1,000회) | API 사용량 기반 |
| 라이선스 | Apache-2.0 (오픈소스) | 프로프라이어터리 |
| MCP 지원 | 지원 | 지원 |
| 프로젝트 설정 | GEMINI.md | CLAUDE.md |

---

## 관련 문서

- [[gemini-2-5|Gemini 2.5 Pro]] - 기반 모델
- [[claude-code|Claude Code]] - 경쟁 에이전틱 코딩 도구
- [[mcp|MCP]] - 도구 확장 프로토콜
- [[codex-cli|Codex CLI]] - OpenAI의 에이전틱 코딩 도구
