# Codex CLI: OpenAI의 샌드박스 기반 AI 코딩 에이전트

## 개요

Codex CLI는 OpenAI가 2025년 4월 o3/o4-mini와 함께 공개한 오픈소스 에이전틱 코딩 도구다. 초기에는 TypeScript/Node.js(Ink 프레임워크)로 구현되었으나, 2025년 6월 성능과 보안을 위해 **Rust로 전면 리라이트**되었다. [[claude-code|Claude Code]]나 [[gemini-cli|Gemini CLI]]와 유사한 에이전틱 코딩 도구이지만, **플랫폼 네이티브 샌드박스** 실행을 핵심 차별점으로 삼는다.

Apache-2.0 라이선스의 완전 오픈소스 프로젝트로, npm/Homebrew/바이너리 다운로드로 설치하며 OpenAI API 키로 인증한다. 2026년 3월 기준 68K+ GitHub stars.

---

## 아키텍처 상세

### 플랫폼 네이티브 샌드박스

Codex CLI의 가장 큰 특징은 **OS 수준의 네이티브 샌드박스**를 사용한다는 점이다:

| 플랫폼 | 샌드박스 기술 |
|--------|-------------|
| macOS | Seatbelt (App Sandbox) |
| Linux | Bubblewrap + Landlock |
| Windows | Restricted Tokens |

### 샌드박스 모드

| 모드 | 파일 읽기 | 파일 쓰기 | 네트워크 |
|------|:---------:|:---------:|:--------:|
| read-only | 프로젝트만 | 불가 | 차단 |
| workspace-write (기본) | 전체 | 프로젝트만 | 차단 |
| danger-full-access | 전체 | 전체 | 허용 |

### 승인 정책

| 정책 | 동작 |
|------|------|
| untrusted | 안전한 읽기만 자동, 모든 변경 승인 필요 |
| on-request (기본) | 워크스페이스 내 편집 자동, 외부 접근 승인 |
| never | 모든 작업 자동 (--full-auto) |

### 핵심 도구

- **Shell**: 샌드박스 내 셸 명령 실행 (주요 도구)
- **파일 읽기/쓰기**: 코드베이스 탐색 및 수정
- **Web Search**: 기본 활성화된 웹 검색
- **MCP 서버**: 외부 도구 확장

---

## 핵심 혁신

1. **플랫폼 네이티브 샌드박스**: OS 수준 격리(Seatbelt/Bubblewrap/Landlock)로 보안 사고 원천 차단
2. **Rust 네이티브**: TypeScript에서 Rust로 전면 리라이트하여 빠른 시작 속도와 낮은 메모리 사용
3. **세밀한 보안 제어**: 3가지 샌드박스 모드 x 3가지 승인 정책 조합으로 정밀한 보안 수준 설정
4. **codex-mini-latest**: 코딩 특화 파인튜닝 모델(200K 컨텍스트, 100K 출력)
5. **오픈소스**: Apache-2.0 라이선스, OpenAI가 $1M API 크레딧 지원

---

## 기반 모델

| 모델 | 특성 | 용도 |
|------|------|------|
| codex-mini-latest | o4-mini 코딩 특화, 200K ctx | 기본 모델 |
| o4-mini | 추론 모델, 범용 | 대안 |
| GPT-5.x 시리즈 | 최신 플래그십 | --model로 전환 |

---

## Claude Code와의 비교

| 특성 | Codex CLI | [[claude-code|Claude Code]] |
|------|-----------|-------------|
| 개발사 | OpenAI | Anthropic |
| 기반 모델 | o4-mini | Claude 4 시리즈 |
| 구현 언어 | Rust | Node.js/TypeScript |
| 핵심 차별점 | 플랫폼 네이티브 샌드박스 | 에이전틱 루프 + 안전한 도구 사용 |
| 자율성 제어 | 샌드박스 모드 x 승인 정책 | 허용 목록 기반 |
| 라이선스 | Apache-2.0 | 프로프라이어터리 |
| MCP 지원 | 지원 | 지원 |

---

## 관련 문서

- [[claude-code|Claude Code]] - Anthropic의 에이전틱 코딩 도구
- [[gemini-cli|Gemini CLI]] - Google의 에이전틱 코딩 도구
- [[mcp|MCP]] - 도구 확장 프로토콜
