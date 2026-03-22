---
title: "Goose: AI 에이전트 프레임워크"
slug: goose
category: agent
tags: ["Block", "Goose", "MCP Integration", "Open-Source Agent"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.181428+00:00"
architecture_entry: goose
---

# Goose: 오픈소스 에이전틱 코딩 어시스턴트

**Block** · **2025-01-01** · **Agentic Coding** · **Apache-2.0**

## 개요

Goose는 Square와 Cash App의 모회사인 Block이 공개한 오픈소스 에이전틱 코딩 어시스턴트로, 로컬 개발 환경에서 파일 읽기/쓰기, 명령 실행, 코드 수정 등을 자율적으로 수행한다. Claude Code, Cursor Agent 등 상용 도구와 달리 완전한 오픈소스(Apache-2.0 라이선스)로 제공되어 자체 호스팅과 커스터마이징이 자유로우며, MCP(Model Context Protocol)를 통한 도구 생태계 확장을 기본으로 지원한다.

Goose의 독특한 포지셔닝은 **"기업이 실전에서 검증한 오픈소스 코딩 에이전트"**라는 점이다. Block은 내부 개발 팀이 실제 업무에서 Goose를 사용하며 검증한 도구를 오픈소스로 공개했다. 이는 학술 연구에서 시작된 SWE-agent나 OpenHands와 달리, 프로덕션 환경의 요구사항(안정성, 보안, 확장성)이 반영된 설계를 보여준다.

에이전틱 코딩 도구 시장에서 Goose가 제공하는 핵심 가치는 **벤더 독립성(vendor independence)**이다. Claude Code는 Anthropic API에, Cursor는 자체 인프라에 종속되지만, Goose는 Claude, GPT-4o, Gemini, 로컬 Ollama 모델 등 어떤 LLM 프로바이더든 설정 파일 한 줄로 전환할 수 있다. 비용 최적화가 필요하면 저렴한 모델로, 프라이버시가 중요하면 로컬 모델로 즉시 전환 가능하다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

Goose의 아키텍처는 고성능 코어와 확장 가능한 플러그인 시스템의 조합으로 설계되었다.

### Rust 코어

핵심 에이전트 루프, LLM 통신, 파일 시스템 조작 등 성능이 중요한 부분은 Rust로 구현되었다. 이는 대규모 코드베이스 탐색이나 다수의 파일 처리 시 Python 기반 도구 대비 수 배 빠른 처리 속도를 보장한다.

### MCP 기반 익스텐션 시스템

Goose의 가장 강력한 특징은 MCP 서버를 익스텐션(extension)으로 연결하는 확장 메커니즘이다.

```yaml
# ~/.config/goose/config.yaml
provider: anthropic
model: claude-sonnet-4-20250514

extensions:
  github:
    type: mcp
    command: npx
    args: ["@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}

  postgres:
    type: mcp
    command: npx
    args: ["@modelcontextprotocol/server-postgres"]
    env:
      DATABASE_URL: ${DATABASE_URL}

  jira:
    type: mcp
    command: uvx
    args: ["mcp-server-jira"]
    env:
      JIRA_URL: ${JIRA_URL}
      JIRA_TOKEN: ${JIRA_TOKEN}

  slack:
    type: mcp
    command: npx
    args: ["@anthropic/mcp-server-slack"]
```

이 설정만으로 Goose는 GitHub 이슈 관리, PostgreSQL 쿼리 실행, Jira 티켓 조회, Slack 메시지 전송을 도구로 사용할 수 있다. MCP 서버 생태계가 성장할수록 Goose의 능력도 자동으로 확장된다.

### 멀티 LLM 지원

| 프로바이더 | 설정값 | 특징 |
|-----------|--------|------|
| Anthropic | `anthropic` | Claude 모델, 높은 코딩 성능 |
| OpenAI | `openai` | GPT-4o, 빠른 응답 |
| Google | `google` | Gemini, 긴 컨텍스트 |
| Ollama | `ollama` | 로컬 모델, 프라이버시 |
| Groq | `groq` | 초고속 추론 |

### 에이전틱 루프

Goose의 에이전트 루프는 ReAct 패턴을 따른다.

$$\text{Think} \rightarrow \text{Plan} \rightarrow \text{Act} \rightarrow \text{Observe} \rightarrow \text{Think} \rightarrow \cdots$$

1. 사용자의 자연어 지시를 파싱
2. 현재 디렉토리 컨텍스트 파악
3. 관련 파일 탐색 및 코드 이해
4. 계획 수립 및 단계별 실행
5. 변경 사항 적용 및 검증 (테스트 실행)
6. 결과 보고 및 다음 단계 결정

## 핵심 혁신

1. **MCP 네이티브 통합**: Goose는 MCP를 익스텐션 시스템의 기본 프로토콜로 채택한 첫 번째 주요 코딩 에이전트 중 하나다. 이를 통해 수백 개의 커뮤니티 MCP 서버를 즉시 활용할 수 있다.

2. **Rust + Python 하이브리드 아키텍처**: 성능이 중요한 코어는 Rust로, 확장성이 중요한 익스텐션은 Python으로 작성하여 성능과 확장성을 동시에 달성한다.

3. **프로바이더 독립적 설계**: 특정 LLM 벤더에 종속되지 않아, 비용 최적화(저렴한 모델 사용)나 프라이버시 요구사항(로컬 모델 사용)을 유연하게 대응할 수 있다.

4. **실전 검증 설계**: Block 내부에서 수천 명의 개발자가 실제 업무에 사용하며 검증된 도구로, 엣지 케이스 처리와 안정성이 학술 프로젝트 대비 높다.

## 벤치마크/성능

| 도구 | 오픈소스 | 코어 언어 | MCP | LLM 선택 | 라이선스 |
|------|---------|----------|-----|---------|---------|
| **Goose** | 네 | Rust+Python | 네이티브 | 다중 | Apache-2.0 |
| Claude Code | 아니오 | TypeScript | 네 | Claude만 | 상용 |
| Aider | 네 | Python | 아니오 | 다중 | Apache-2.0 |
| OpenHands | 네 | Python | 아니오 | 다중 | MIT |
| Cursor | 아니오 | TypeScript | 네 | 다중 | 상용 |

## 구현

**프라이버시 중심 개발**: Ollama로 로컬 모델(예: Codestral, DeepSeek-Coder)을 사용하면, 코드가 외부 서버로 전송되지 않아 보안이 중요한 금융, 의료, 군사 프로젝트에서도 에이전틱 코딩을 활용할 수 있다.

**DevOps 자동화**: MCP 익스텐션을 통해 Kubernetes, Docker, AWS 등과 연동하여, 인프라 관리 작업까지 자연어로 수행할 수 있다. "스테이징 환경에 이 브랜치를 배포해줘"와 같은 지시가 가능하다.

**팀 커스터마이징**: 오픈소스 특성을 활용하여 팀의 코딩 컨벤션, 빌드 시스템, 배포 프로세스에 맞춤화된 도구를 구축할 수 있다.

## 관련 모델

Goose는 SWE-agent의 에이전틱 코딩 접근법에서 영감을 받되, MCP 통합과 오픈소스 유연성에 차별점을 둔다. Claude Code와 직접 경쟁하면서도 벤더 독립성이라는 독자적 가치를 제공한다. Block의 지속적인 투자와 MCP 생태계의 급속한 성장에 힘입어, Goose는 벤더 독립적 에이전틱 코딩 도구의 대표로 자리잡고 있다.

## 참고 자료

- [Goose GitHub Repository](https://github.com/block/goose)
- [Goose Documentation](https://block.github.io/goose)

## 관련 문서

- [[swe-agent|SWE-agent]] — 영감
- [[mcp|Model Context Protocol]] — 사용 기법
