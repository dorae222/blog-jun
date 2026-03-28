# Gemini CLI: Google의 오픈소스 AI 코딩 에이전트

## 개요

Gemini CLI는 Google이 2025년 6월 공개한 오픈소스 에이전틱 코딩 도구로, [[gemini-2-5|Gemini 2.5 Pro]] 모델을 기반으로 터미널에서 직접 실행된다. [[claude-code|Claude Code]]와 유사하게 파일 읽기/쓰기, 셸 명령 실행, 웹 검색 등을 에이전틱 루프 방식으로 수행하며, Google AI Studio API 키를 통해 무료로 사용할 수 있다는 점이 큰 차별점이다.

npm을 통해 설치(`npm install -g @anthropic-ai/gemini-cli` 아님, `npm install -g @anthropic-ai/gemini-cli`가 아니라 `npm install -g @anthropic-ai/gemini-cli` 대신 `npm install -g @google/gemini-cli`)하며, `gemini` 명령어로 터미널에서 바로 실행할 수 있다. Apache-2.0 라이선스로 완전한 오픈소스 프로젝트다.

---

## 아키텍처 상세

### 에이전틱 루프

Gemini CLI는 다른 에이전틱 코딩 도구와 마찬가지로 "이해 - 검색 - 계획 - 실행 - 검증" 루프를 따른다:

$$\text{Understand} \rightarrow \text{Search} \rightarrow \text{Plan} \rightarrow \text{Execute} \rightarrow \text{Verify}$$

사용자의 자연어 요청을 Gemini 2.5 Pro가 해석하고, 내장 도구를 활용하여 코드베이스를 탐색한 뒤, 실제 파일 수정과 명령 실행을 수행한다.

### 핵심 도구 시스템

| 도구 | 기능 |
|------|------|
| ReadFile / WriteFile | 파일 읽기/쓰기 |
| Shell | 셸 명령 실행 |
| GlobTool / GrepTool | 파일 검색/내용 검색 |
| WebFetch | 웹 페이지 가져오기 |
| GoogleSearch | Google 검색 |

### MCP 서버 지원

[[mcp|MCP]](Model Context Protocol)를 통해 외부 도구를 확장할 수 있다. `GEMINI.md` 또는 설정 파일에서 MCP 서버를 정의하면, Gemini CLI가 해당 도구를 자동으로 인식하고 사용한다.

### GEMINI.md 프로젝트 설정

프로젝트 루트에 `GEMINI.md` 파일을 두면 프로젝트별 지침, MCP 서버 설정, 코딩 규칙 등을 커스터마이징할 수 있다. Claude Code의 `CLAUDE.md`와 동일한 개념이다.

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
