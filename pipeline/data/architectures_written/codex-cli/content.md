# Codex CLI: OpenAI의 샌드박스 기반 AI 코딩 에이전트

## 개요

Codex CLI는 OpenAI가 2025년 4월 공개한 오픈소스 에이전틱 코딩 도구로, o4-mini 모델을 기반으로 터미널에서 코드 생성, 리팩토링, 디버깅을 수행한다. [[claude-code|Claude Code]]나 [[gemini-cli|Gemini CLI]]와 유사한 에이전틱 코딩 도구이지만, **네트워크 격리 샌드박스** 실행을 핵심 차별점으로 삼는다.

Apache-2.0 라이선스의 완전 오픈소스 프로젝트로, npm을 통해 설치(`npm install -g @openai/codex`)하며 OpenAI API 키로 인증한다.

---

## 아키텍처 상세

### 샌드박스 우선 설계

Codex CLI의 가장 큰 특징은 모든 코드 실행이 네트워크가 격리된 샌드박스에서 이루어진다는 점이다. 이는 악의적인 코드 실행이나 예기치 않은 외부 요청을 원천적으로 차단한다.

실행 흐름:

$$\text{사용자 요청} \rightarrow \text{모델 추론} \rightarrow \text{샌드박스 실행} \rightarrow \text{결과 검증} \rightarrow \text{사용자 승인} \rightarrow \text{적용}$$

### 자율성 수준

| 모드 | 설명 | 파일 수정 | 명령 실행 |
|------|------|:---------:|:---------:|
| suggest | 제안만, 실행 안 함 | 제안만 | 제안만 |
| auto-edit | 파일 자동 수정, 명령은 확인 | 자동 | 확인 필요 |
| full-auto | 모든 작업 자동 실행 | 자동 | 자동 |

### 핵심 도구

- **파일 읽기/쓰기**: 코드베이스 탐색 및 수정
- **셸 명령 실행**: 샌드박스 내에서 안전하게 실행
- **패치 적용**: diff 기반 정밀 코드 수정

---

## 핵심 혁신

1. **샌드박스 격리**: 네트워크 격리 환경에서 코드 실행, 보안 사고 원천 차단
2. **3단계 자율성**: suggest/auto-edit/full-auto로 사용자가 신뢰 수준을 세밀하게 제어
3. **멀티파일 편집**: 여러 파일에 걸친 리팩토링을 한 번의 요청으로 처리
4. **Git 통합**: 변경 사항을 Git diff로 명확하게 보여주고, 커밋까지 자동화
5. **오픈소스**: Apache-2.0 라이선스, 커뮤니티 기여 활발

---

## 기반 모델

Codex CLI는 기본적으로 **o4-mini** 모델을 사용한다. OpenAI의 추론(reasoning) 모델 계열로, 코딩 태스크에서 뛰어난 성능을 보인다. `--model` 플래그로 다른 OpenAI 모델(o3, gpt-4.1 등)로 전환할 수 있다.

---

## Claude Code와의 비교

| 특성 | Codex CLI | [[claude-code|Claude Code]] |
|------|-----------|-------------|
| 개발사 | OpenAI | Anthropic |
| 기반 모델 | o4-mini | Claude 4 시리즈 |
| 핵심 차별점 | 샌드박스 격리 실행 | 에이전틱 루프 + 안전한 도구 사용 |
| 자율성 제어 | 3단계 (suggest/auto-edit/full-auto) | 허용 목록 기반 |
| 라이선스 | Apache-2.0 | 프로프라이어터리 |
| MCP 지원 | 지원 | 지원 |

---

## 관련 문서

- [[claude-code|Claude Code]] - Anthropic의 에이전틱 코딩 도구
- [[gemini-cli|Gemini CLI]] - Google의 에이전틱 코딩 도구
- [[mcp|MCP]] - 도구 확장 프로토콜
