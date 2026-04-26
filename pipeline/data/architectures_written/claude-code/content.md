<!-- infographic-hero -->
![Claude Code 핵심 요약](figures/infographic.svg)

*Figure: Claude Code 한 장 요약 인포그래픽*

# Claude Code: 에이전틱 소프트웨어 엔지니어링의 새로운 기준

**Anthropic** · **2025-02-24** · **Agentic Coding** · **상용**

## 개요

Claude Code는 Anthropic이 2025년 2월 공개한 에이전틱 코딩 CLI 도구로, Claude 모델을 기반으로 터미널에서 직접 실행되는 AI 소프트웨어 엔지니어링 보조도구다. 기존 GitHub Copilot 같은 자동완성(autocomplete) 도구와 근본적으로 다르게, Claude Code는 코드베이스 전체를 이해하고 파일 읽기/쓰기/생성, 명령 실행, Git 조작, 웹 검색까지 에이전틱(agentic) 방식으로 수행한다.

Claude Code의 설계 철학은 **"개발자의 워크플로에 자연스럽게 통합되는 AI 팀원"**이다. IDE에 종속되지 않고 터미널에서 동작하여, 기존 개발 환경(VS Code, JetBrains, Vim 등)을 변경하지 않으면서도 복잡한 리팩토링, 버그 수정, 새 기능 구현을 엔드투엔드로 처리한다. SWE-bench Verified에서 72% 이상의 이슈 해결률을 기록하며, 현존하는 코딩 에이전트 중 최고 수준의 성능을 보인다.

에이전틱 코딩의 핵심 가치는 **"의도 수준의 지시(intent-level instruction)"**에 있다. 개발자가 "이 API를 GraphQL로 마이그레이션해줘"라고 말하면, Claude Code는 스스로 관련 파일을 탐색하고, 변경 계획을 수립하며, 코드를 수정하고, 테스트를 실행하여 결과를 보고한다. 이 전 과정에서 개발자는 코드 한 줄도 직접 작성하지 않으면서도, 원하는 결과를 정확히 얻을 수 있다.

![Claude Code 에이전틱 코딩 아키텍처 - Understand-Search-Plan-Edit-Verify-Report 루프와 도구 사용 구조](figures/architecture.svg)

*Figure 1: Claude Code 아키텍처 - 사용자의 자연어 지시를 받아 코드베이스 탐색, 계획 수립, 파일 편집, 테스트 실행, 결과 보고의 에이전틱 루프를 반복하는 CLI 기반 AI 소프트웨어 엔지니어링 도구이다.*

## 아키텍처 상세

Claude Code의 아키텍처는 **"에이전틱 루프 + 안전한 도구 사용"**을 핵심 원칙으로 설계되었다.

### 에이전틱 루프

사용자의 자연어 지시를 받으면 Claude Code는 다음 사이클을 반복한다.

$$\text{Understand} \rightarrow \text{Search} \rightarrow \text{Plan} \rightarrow \text{Edit} \rightarrow \text{Verify} \rightarrow \text{Report}$$

1. **지시 이해 및 계획 수립**: 사용자의 요청을 분석하고 작업 전략을 결정
2. **코드베이스 탐색**: Glob, Grep, Read 도구로 관련 코드를 정확히 탐색
3. **코드 수정**: Edit, Write 도구로 정밀하게 코드를 변경
4. **변경 검증**: Bash로 테스트 실행, 린트 체크, 빌드 확인
5. **결과 보고 및 추가 작업 여부 판단**

### 도구 시스템

| 도구 | 기능 | 카테고리 |
|------|------|----------|
| `Read` | 파일 내용 읽기 (이미지, PDF 포함) | 읽기 |
| `Glob` | 패턴 기반 파일 검색 | 읽기 |
| `Grep` | 코드 내 정규식 패턴 검색 | 읽기 |
| `Edit` | 정밀한 문자열 교체 기반 파일 수정 | 쓰기 |
| `Write` | 새 파일 생성 또는 전체 덮어쓰기 | 쓰기 |
| `Bash` | 셸 명령 실행 (빌드, 테스트, Git 등) | 실행 |
| `WebFetch` | 웹 페이지 내용 가져오기 | 외부 |
| `Task` | 서브에이전트 생성 및 병렬 실행 | 에이전트 |

### 신뢰 레벨 시스템

도구 사용의 안전성을 보장하기 위해 3단계 권한 체계를 갖는다.

```
레벨 1 (자동 허용)  : Read, Glob, Grep - 읽기 전용
레벨 2 (설정 가능)  : Edit, Write, Bash - 일반 쓰기
레벨 3 (항상 확인)  : rm, curl, 외부 API - 위험 작업
```

이 체계를 통해 일상적인 코드 탐색은 빠르게 자동 실행하면서도, 파일 삭제나 외부 통신 같은 위험 작업은 반드시 사용자 확인을 거친다.

### 프로젝트 메모리 (CLAUDE.md)

프로젝트 루트에 `CLAUDE.md` 파일을 두어, 프로젝트 구조, 코딩 컨벤션, 빌드/배포 방법 등의 컨텍스트를 세션 간에 유지한다. 이를 통해 새 세션에서도 프로젝트를 빠르게 파악하고 일관된 코딩 스타일을 유지한다. `CLAUDE.md`는 세 수준에서 관리된다.
- 프로젝트 레벨: 리포지토리 루트의 `CLAUDE.md`
- 사용자 레벨: `~/.claude/CLAUDE.md`
- 디렉토리 레벨: 하위 디렉토리의 `CLAUDE.md`

### MCP 확장

Model Context Protocol을 통해 외부 도구를 무한히 확장할 수 있다. GitHub, Slack, 데이터베이스, Jira, Notion 등의 MCP 서버를 연결하여 Claude Code의 작업 범위를 넓힌다.

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"]
    },
    "postgres": {
      "command": "npx", 
      "args": ["@modelcontextprotocol/server-postgres"]
    }
  }
}
```

## 핵심 혁신

1. **코드베이스 전체 이해**: 단순 파일 단위가 아닌 프로젝트 전체를 탐색하고 이해하는 능력. Glob/Grep 기반 효율적 검색으로 수만 개 파일의 대규모 코드베이스에서도 관련 코드를 정확히 찾아낸다.

2. **서브에이전트 병렬 실행**: Task 도구를 통해 독립적인 서브에이전트를 생성하여 병렬 작업을 수행할 수 있다. 대규모 리팩토링이나 다중 파일 분석 시 효율적이다.

3. **자연스러운 Git 통합**: 커밋 메시지 작성, PR 생성, 코드 리뷰, 브랜치 관리 등 Git 워크플로를 자연어로 수행할 수 있다. `gh` CLI와의 통합으로 GitHub 작업도 원활하다.

4. **적응형 컨텍스트 관리**: 긴 세션에서도 컨텍스트 윈도우를 효율적으로 관리하며, 필요한 정보를 선택적으로 로드/언로드하여 대규모 프로젝트에서도 안정적으로 동작한다.

## 벤치마크/성능

| 벤치마크 | Claude Code (Opus 4) | OpenHands | SWE-agent | Devin |
|---------|---------------------|-----------|-----------|-------|
| SWE-bench Verified | **72%+** | 53% | 23% | 13.86% |
| Terminal Bench | **43.2%** | - | - | - |
| 다중 파일 수정 | 최상위 | 상위 | 중간 | 중간 |

Claude Code는 SWE-bench Verified에서 72% 이상의 해결률을 기록하여, 실제 GitHub 이슈를 자율적으로 해결하는 능력에서 타 도구를 크게 앞선다.

## 구현

**대규모 리팩토링**: "이 프로젝트의 모든 REST API를 GraphQL로 마이그레이션해줘"와 같은 복잡한 요청을 자율적으로 수행한다. 관련 파일을 탐색하고, 변경하고, 테스트하는 전 과정을 처리한다.

**버그 수정 자동화**: CI/CD 파이프라인에서 실패한 테스트의 로그를 분석하고, 원인을 진단하며, 수정 코드를 작성하고 PR을 생성하는 워크플로를 자동화할 수 있다.

**코드 리뷰 보조**: PR의 변경 사항을 분석하여 잠재적 버그, 성능 이슈, 보안 취약점을 식별하고 개선 제안을 작성한다. GitHub Actions와 연동하여 자동 리뷰를 수행할 수 있다.

## 관련 모델

Claude Code는 Claude Opus 4 시리즈를 기반으로 동작하며, MCP를 통해 도구 생태계를 확장한다. SWE-agent의 ACI 설계 철학에서 영감을 받되, CLI 기반의 실무 최적화에 집중했다. Cursor, Goose, Windsurf 등 경쟁 도구와 함께 에이전틱 코딩 시장을 형성하고 있다.

## 참고 자료

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Anthropic Blog: Introducing Claude Code](https://www.anthropic.com/claude-code)

## 관련 문서

- [[claude-4|Claude Opus 4]] - 발전 기반
- [[mcp|Model Context Protocol]] - 사용 기법
