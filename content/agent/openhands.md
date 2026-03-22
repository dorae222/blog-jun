---
title: "OpenHands: AI 에이전트 프레임워크"
slug: openhands
category: agent
tags: ["Code Agent", "OpenHands", "Open-Source Agent", "UIUC"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.292673+00:00"
architecture_entry: openhands
---

# OpenHands: 오픈소스 AI 소프트웨어 엔지니어

**UIUC** · **2024-07-23** · **Code Agent** · **MIT**

## 개요

OpenHands(구 OpenDevin)는 AI 소프트웨어 엔지니어가 인간 개발자와 동일한 방식으로 코드를 작성하고, 명령을 실행하고, 웹을 탐색하고, API를 호출할 수 있는 오픈소스 AI 에이전트 플랫폼이다. Wang et al.(UIUC, University of Illinois Urbana-Champaign, 2024)이 논문 "OpenDevin: An Open Platform for AI Software Developers as Generalist Agents"에서 발표한 이 플랫폼은, Devin 등 상용 SWE 에이전트에 대응하는 가장 강력한 오픈소스 대안으로 자리잡았다.

OpenHands의 설계 목표는 **"누구나 AI 소프트웨어 엔지니어를 사용하고 개선할 수 있는 오픈 플랫폼"**이다. 단일 에이전트부터 멀티 에이전트 파이프라인까지 다양한 아키텍처를 지원하며, 격리된 Docker 샌드박스 환경에서 안전한 코드 실행을 보장한다. SWE-bench Verified에서 Claude 3.5 Sonnet 기반으로 53% 이상의 이슈 해결률을 달성하는 등, 오픈소스 SWE 에이전트 중 최고 수준의 성능을 보이고 있다.

OpenHands의 학술적 기여는 **CodeAct 패러다임**의 제안에 있다. 기존 에이전트가 자연어 명령으로 도구를 호출하는 것과 달리, CodeAct는 에이전트의 모든 행동을 실행 가능한 Python 코드로 표현한다. 이를 통해 복잡한 로직을 정밀하게 제어하고, 실행 결과를 정확히 검증할 수 있다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

OpenHands의 아키텍처는 확장 가능한 에이전트 런타임을 중심으로 설계되었다.

### EventStream 아키텍처

OpenHands의 핵심 설계 패턴으로, 모든 에이전트 행동(Action)과 환경 관찰(Observation)을 구조화된 이벤트로 관리한다.

```
EventStream
+-- Action: CmdRunAction("git diff HEAD~1")
|   +-- Observation: CmdOutputObservation("diff --git a/...")
+-- Action: FileReadAction("/src/main.py")
|   +-- Observation: FileReadObservation("import os...")
+-- Action: FileEditAction("/src/main.py", changes=[...])
|   +-- Observation: FileEditObservation(success=True)
+-- Action: BrowseURLAction("https://docs.python.org/...")
|   +-- Observation: BrowseObservation(content="...")
+-- Action: MessageAction("수정 완료. 테스트를 실행합니다.")
```

이 이벤트 기반 설계는 에이전트 행동의 재현성(reproducibility)과 디버깅 용이성을 보장한다. 모든 이벤트는 시간 순서대로 기록되어, 작업 과정을 완벽하게 추적할 수 있다.

### 에이전트 구현체

| 에이전트 | 접근 방식 | 핵심 기능 |
|---------|----------|----------|
| CodeActAgent | 코드 기반 행동 | Python 코드로 모든 작업 수행 |
| BrowsingAgent | 웹 브라우징 | 정보 수집, 문서 검색 |
| DelegatorAgent | 오케스트레이션 | 서브에이전트에 작업 위임 |
| MicroAgent | 특화 서브에이전트 | 특정 작업에 최적화 |

### CodeAct 패러다임

CodeAct의 핵심 아이디어는 에이전트 행동을 자연어가 아닌 실행 가능한 코드로 표현하는 것이다.

```python
# 기존 에이전트: 자연어 도구 호출
# Action: search_file("config.py", "database")
# Action: edit_file("config.py", line=15, content="...")

# CodeAct: Python 코드로 행동 표현
import subprocess

# 관련 파일 찾기
result = subprocess.run(["grep", "-rn", "database", "src/"], capture_output=True)
print(result.stdout.decode())

# 파일 수정
with open("src/config.py") as f:
    content = f.read()
content = content.replace("sqlite:///db.sqlite3", "postgresql://...")
with open("src/config.py", "w") as f:
    f.write(content)
```

코드로 행동을 표현하면 복잡한 조건 분기, 반복문, 예외 처리를 자연스럽게 활용할 수 있어, 자연어 도구 호출보다 정밀한 제어가 가능하다.

### Docker 샌드박스

모든 코드 실행은 격리된 Docker 컨테이너에서 이루어진다. 필요한 의존성이 사전 설치된 이미지를 사용하며, 호스트 시스템과 격리되어 안전한 실행 환경을 제공한다.

### 웹 UI

브라우저 기반 인터페이스를 제공하여, 터미널에 익숙하지 않은 사용자도 에이전트와 상호작용할 수 있다. 코드 에디터, 터미널, 브라우저 뷰를 통합 제공한다.

## 핵심 혁신

1. **CodeAct 패러다임**: 에이전트의 행동을 실행 가능한 코드로 표현하여, 복잡한 로직을 정밀하게 제어하고 실행 결과를 정확히 검증할 수 있다.

2. **확장 가능한 에이전트 프레임워크**: 새로운 에이전트 아키텍처를 쉽게 추가할 수 있는 플러그인 구조. 연구자들이 다양한 에이전트 전략을 실험하고 비교할 수 있는 플랫폼을 제공한다.

3. **EventStream 기반 투명성**: 모든 에이전트 행동과 관찰이 구조화된 이벤트로 기록되어, 작업 과정의 재현과 디버깅이 용이하다.

4. **Human-in-the-Loop 모드**: 에이전트가 작업 중 사용자의 확인을 요청하거나, 사용자가 중간에 개입하여 방향을 수정할 수 있다.

## 벤치마크/성능

| 벤치마크 | 모델 | 해결률 |
|---------|------|--------|
| SWE-bench Verified | Claude 3.5 Sonnet | **53.0%** |
| SWE-bench Verified | GPT-4o | 38.0% |
| SWE-bench Lite | Claude 3.5 Sonnet | 28.3% |
| HumanEval | Claude 3.5 Sonnet | 91.0%+ |

OpenHands는 오픈소스 SWE 에이전트 중 SWE-bench에서 최고 수준의 성능을 지속적으로 달성하고 있다. 특히 Claude Code(72%+)를 제외하면 가장 높은 해결률을 보인다.

## 구현

**GitHub 이슈 자동 해결**: GitHub Actions와 연동하여, 새로운 이슈가 등록되면 OpenHands가 자동으로 분석하고 PR을 생성하는 워크플로를 구축할 수 있다.

**코드 리뷰 자동화**: PR의 코드 변경 사항을 분석하고, 잠재적 버그나 개선 사항을 코멘트로 작성하는 자동 리뷰어로 활용한다.

**레거시 코드 현대화**: 오래된 코드베이스의 프레임워크 마이그레이션, API 업데이트, 보안 패치 적용 등을 자동화한다.

## 관련 모델

OpenHands는 Devin의 비전을 오픈소스로 구현하려는 시도로 시작되었다(초기명: OpenDevin). SWE-agent의 ACI 설계에서 영감을 받되, CodeAct라는 독자적 패러다임과 웹 UI를 통해 차별화했다. 학계-산업계 협업 모델로서 SWE 에이전트 연구의 표준 플랫폼으로 자리잡고 있다.

## 참고 자료

- Wang et al., "OpenDevin: An Open Platform for AI Software Developers as Generalist Agents", arXiv:2407.16741, 2024
- [OpenHands GitHub Repository](https://github.com/All-Hands-AI/OpenHands)

## 관련 문서

- [[swe-agent|SWE-agent]] — 영감
