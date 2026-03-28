# OpenClaw: 로컬 퍼스트 범용 AI 에이전트

## 개요

OpenClaw(구 Clawdbot → Moltbot → OpenClaw)는 Peter Steinberger가 2025년 11월 공개한 오픈소스 로컬 퍼스트 AI 에이전트다. 터미널 기반 코딩 도구인 [[claude-code|Claude Code]]나 [[gemini-cli|Gemini CLI]]와 달리, OpenClaw는 **메시징 앱**을 통해 접근하는 **범용 AI 어시스턴트**라는 점이 근본적으로 다르다.

WhatsApp, Telegram, Discord, Slack, iMessage, Signal 등 20개 이상의 메시징 플랫폼을 LLM에 연결하여, 일상적인 메시지 인터페이스로 파일 관리, 셸 명령, 웹 브라우징, 멀티스텝 워크플로우를 자율적으로 수행한다. 2026년 초 GitHub 339K+ stars를 달성하며 역대 가장 빠른 성장을 기록했다.

---

## 역사

| 시점 | 이벤트 |
|------|--------|
| 2025.11 | Peter Steinberger가 "Clawdbot"으로 최초 공개 |
| 2026.01.27 | Anthropic 상표권 이슈로 "Moltbot"으로 개명 |
| 2026.01.30 | "OpenClaw"로 최종 개명 |
| 2026.02.14 | Steinberger의 OpenAI 합류 발표, 독립 오픈소스 재단으로 이관 |

---

## 아키텍처 상세

### 로컬 퍼스트 제어 평면

OpenClaw의 핵심 설계 원칙은 **로컬 퍼스트**다. 모든 데이터와 실행이 사용자의 디바이스에서 이루어지며, 외부 서버를 거치지 않는다:

- **제어 평면**: 사용자 디바이스에서 실행
- **데이터 저장**: SQLite + sqlite-vec (로컬 벡터 검색)
- **메시징 브릿지**: 각 플랫폼 API에 직접 연결

### 멀티 플랫폼 메시징 통합

| 카테고리 | 플랫폼 |
|---------|--------|
| 모바일 메신저 | WhatsApp, Telegram, Signal, iMessage |
| 팀 협업 | Slack, Discord, Microsoft Teams, Matrix |
| 기타 | Email, SMS, 음성 (macOS/iOS/Android) |

### LLM 백엔드 지원

Claude, GPT, DeepSeek 등 주요 LLM 프로바이더를 모두 지원하며, 대화 중 모델을 전환할 수 있다.

### 기술 스택

- **런타임**: TypeScript + Node.js (pnpm 모노레포)
- **웹 게이트웨이**: Hono
- **제어 패널 UI**: Lit
- **저장소**: SQLite + sqlite-vec
- **컴패니언 앱**: iOS, Android

---

## 핵심 혁신

1. **메시징 네이티브**: 터미널이 아닌 일상 메시징 앱에서 AI 에이전트에 접근 - 비개발자도 사용 가능
2. **로컬 퍼스트**: 모든 데이터와 실행이 사용자 디바이스에서 이루어짐 - 프라이버시 보장
3. **음성 인터랙션**: macOS/iOS 웨이크 워드, Android 상시 음성 지원
4. **Canvas/A2UI**: 에이전트 기반 시각 워크스페이스
5. **ClawHub 스킬 레지스트리**: 커뮤니티 기반 스킬 확장 시스템

---

## 코딩 도구와의 비교

OpenClaw는 코딩 도구가 아닌 범용 AI 에이전트라는 점에서 근본적으로 다르다:

| 특성 | OpenClaw | [[claude-code|Claude Code]] / [[gemini-cli|Gemini CLI]] |
|------|----------|-----------------------------------|
| 인터페이스 | 메시징 앱 (WhatsApp 등) | 터미널 CLI |
| 대상 사용자 | 일반 사용자 + 개발자 | 개발자 |
| 핵심 기능 | 범용 작업 자동화 | 코드 생성/편집/실행 |
| 데이터 위치 | 로컬 디바이스 | API 전송 |
| 라이선스 | MIT | Apache-2.0 / 프로프라이어터리 |

---

## 관련 문서

- [[claude-code|Claude Code]] - Anthropic의 에이전틱 코딩 도구
- [[mcp|MCP]] - 도구 확장 프로토콜
- [[a2a|A2A]] - Agent-to-Agent 프로토콜
