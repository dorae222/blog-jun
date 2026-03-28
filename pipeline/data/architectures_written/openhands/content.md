# OpenHands: 오픈소스 AI 소프트웨어 엔지니어

**UIUC** · **2024-07-23** · **Code Agent** · **MIT**

## 개요

OpenHands(구 OpenDevin)는 AI 소프트웨어 엔지니어가 인간 개발자와 동일한 방식으로 코드를 작성하고, 명령을 실행하고, 웹을 탐색하고, API를 호출할 수 있는 오픈소스 AI 에이전트 플랫폼이다. Wang et al.(UIUC, University of Illinois Urbana-Champaign, 2024)이 논문 "OpenDevin: An Open Platform for AI Software Developers as Generalist Agents"에서 발표한 이 플랫폼은, Devin 등 상용 SWE 에이전트에 대응하는 가장 강력한 오픈소스 대안으로 자리잡았다.

OpenHands의 설계 목표는 **"누구나 AI 소프트웨어 엔지니어를 사용하고 개선할 수 있는 오픈 플랫폼"**이다. 단일 에이전트부터 멀티 에이전트 파이프라인까지 다양한 아키텍처를 지원하며, 격리된 Docker 샌드박스 환경에서 안전한 코드 실행을 보장한다. SWE-bench Verified에서 Claude 3.5 Sonnet 기반으로 53% 이상의 이슈 해결률을 달성하는 등, 오픈소스 SWE 에이전트 중 최고 수준의 성능을 보이고 있다.

OpenHands의 학술적 기여는 **CodeAct 패러다임**의 제안에 있다. 기존 에이전트가 자연어 명령으로 도구를 호출하는 것과 달리, CodeAct는 에이전트의 모든 행동을 실행 가능한 Python 코드로 표현한다. 이를 통해 복잡한 로직을 정밀하게 제어하고, 실행 결과를 정확히 검증할 수 있다.

![OpenHands 아키텍처 - EventStream 기반 에이전트 런타임과 Docker 샌드박스 실행 환경](figures/architecture.svg)

*Figure 1: OpenHands 아키텍처 - CodeAct 패러다임으로 모든 에이전트 행동을 실행 가능한 Python 코드로 표현하고, 격리된 Docker 샌드박스에서 안전하게 실행하는 확장 가능한 에이전트 플랫폼이다.*

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

#### 이벤트 타입 분류

EventStream의 이벤트는 크게 **Action**과 **Observation** 두 범주로 나뉜다. Action은 에이전트가 환경에 가하는 행동이고, Observation은 환경이 에이전트에게 반환하는 결과다.

주요 Action 타입은 다음과 같다:

- **CmdRunAction**: 셸 명령 실행 (git, pip, pytest 등)
- **FileReadAction / FileEditAction**: 파일 읽기 및 수정
- **BrowseURLAction / BrowseInteractiveAction**: 웹 페이지 탐색 및 인터랙션
- **MessageAction**: 사용자에게 메시지 전달
- **AgentDelegateAction**: 다른 에이전트에게 작업 위임

각 Action에는 대응하는 Observation 타입이 존재한다. 예를 들어 `CmdRunAction`은 `CmdOutputObservation`을, `FileReadAction`은 `FileReadObservation`을 반환한다. 이 1:1 대응 구조 덕분에 에이전트는 자신의 행동이 어떤 결과를 낳았는지 항상 명확하게 파악할 수 있다.

#### 상태 관리와 이벤트 처리 흐름

에이전트는 EventStream 전체를 **누적 컨텍스트**로 유지한다. 매 턴(turn)마다 지금까지의 모든 이벤트를 LLM에 프롬프트로 전달하고, LLM의 응답을 다음 Action으로 파싱한다. 이 과정에서 State 객체가 현재 진행 상태(iteration 수, 최근 에러, 완료 여부 등)를 추적한다.

EventStream은 **직렬화(serialization)**가 가능하여, 진행 중인 작업을 중단했다가 나중에 재개할 수 있다. 이는 긴 작업을 처리하거나 에이전트 실행을 디버깅할 때 유용하다. 또한 이벤트 스트림을 재생(replay)하여 에이전트의 의사결정 과정을 분석하거나 벤치마크 평가에 활용할 수 있다.

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

#### CodeAct vs 전통적 도구 호출: 구체적 비교

CodeAct 패러다임의 이점은 복잡한 작업에서 극명하게 드러난다. 예를 들어, "프로젝트 내 모든 deprecated API 호출을 찾아 새 API로 마이그레이션"하는 작업을 생각해보자.

전통적 도구 호출 방식에서는 각 파일을 하나씩 검색하고, 결과를 파싱하여 다시 도구를 호출하는 반복이 필요하다. N개의 파일에 M개의 변경이 필요하면 최소 2NM번의 도구 호출이 발생한다.

```python
# CodeAct 방식: 한 번의 코드 실행으로 일괄 처리
import os, re

api_mapping = {
    "old_connect(": "new_connect(",
    "deprecated_query(": "execute_query(",
    "legacy_close(": "close_connection(",
}

for root, dirs, files in os.walk("src/"):
    for fname in files:
        if fname.endswith(".py"):
            path = os.path.join(root, fname)
            with open(path) as f:
                content = f.read()
            original = content
            for old, new in api_mapping.items():
                content = content.replace(old, new)
            if content != original:
                with open(path, "w") as f:
                    f.write(content)
                print(f"Updated: {path}")
```

이처럼 CodeAct는 Python의 모든 표현력(루프, 조건문, 정규식, 표준 라이브러리)을 에이전트 행동에 직접 활용할 수 있어, 도구 호출 기반 에이전트 대비 복잡한 작업에서 **턴(turn) 수를 대폭 줄이고** 정밀도를 높인다. Wang et al.의 실험에서 CodeAct는 동일 작업에서 전통적 도구 호출 대비 평균 30% 적은 턴으로 문제를 해결했다.

### Docker 샌드박스

모든 코드 실행은 격리된 Docker 컨테이너에서 이루어진다. 필요한 의존성이 사전 설치된 이미지를 사용하며, 호스트 시스템과 격리되어 안전한 실행 환경을 제공한다.

#### 보안 모델

Docker 샌드박스는 다층 보안 모델을 구현한다:

- **네트워크 격리**: 컨테이너는 기본적으로 인터넷 접근이 허용되지만, 호스트 네트워크와는 분리되어 있다. 필요에 따라 네트워크 접근을 완전히 차단할 수도 있다.
- **파일 시스템 격리**: 호스트의 작업 디렉토리만 마운트되며, 호스트의 시스템 파일이나 다른 프로젝트에는 접근할 수 없다. 이를 통해 에이전트가 실수로 시스템을 손상시키는 것을 방지한다.
- **리소스 제한**: CPU, 메모리, 디스크 사용량에 상한을 설정하여 무한 루프나 메모리 누수로 인한 호스트 시스템 장애를 방지한다.
- **권한 제한**: 컨테이너 내부에서 root 접근이 필요한 명령도 호스트에 영향을 줄 수 없도록 설계되었다.

에이전트가 생성하는 코드는 본질적으로 신뢰할 수 없으므로, 이러한 격리 환경은 OpenHands의 안전한 운영에 필수적이다. 사용자는 `--sandbox-type` 옵션으로 로컬 Docker, 원격 Docker, 또는 E2B 클라우드 샌드박스를 선택할 수 있다.

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

### SWE-bench Verified 상세 분석

SWE-bench Verified는 500개의 실제 오픈소스 GitHub 이슈로 구성된 벤치마크로, 각 이슈에는 문제 설명, 관련 코드베이스, 그리고 검증용 테스트 케이스가 포함되어 있다. OpenHands의 53% 해결률의 의미를 다른 에이전트와 비교하면 다음과 같다:

| 에이전트 | SWE-bench Verified | 유형 |
|---------|-------------------|------|
| Claude Code | 72.0%+ | 상용 |
| Devin | 55.0% | 상용 |
| **OpenHands** | **53.0%** | **오픈소스** |
| SWE-agent | 33.0% | 오픈소스 |
| Aider | 26.0% | 오픈소스 |

OpenHands가 특히 강점을 보이는 영역은 **다수 파일 수정이 필요한 이슈**와 **테스트 작성이 필요한 이슈**다. CodeAct 패러다임의 특성상, Python 코드로 여러 파일을 일괄 탐색하고 수정하는 작업이 자연스럽게 처리되기 때문이다. 반면 단순한 한 줄 수정 이슈에서는 다른 에이전트와 큰 차이를 보이지 않는다.

성능 차이의 핵심 요인은 **모델 선택**이다. GPT-4o 기반 38%에서 Claude 3.5 Sonnet 기반 53%로, 동일 에이전트 프레임워크에서도 모델에 따라 15%p 이상 차이가 발생한다. 이는 에이전트 아키텍처뿐 아니라 기반 LLM의 코딩 능력이 최종 성능에 결정적이라는 점을 보여준다.

## 구현

**GitHub 이슈 자동 해결**: GitHub Actions와 연동하여, 새로운 이슈가 등록되면 OpenHands가 자동으로 분석하고 PR을 생성하는 워크플로를 구축할 수 있다. OpenHands 팀은 공식 GitHub Action(`openhands-resolver`)을 제공하여, `.github/workflows/` 설정만으로 이슈 라벨 기반 자동 해결 파이프라인을 구축할 수 있다.

**코드 리뷰 자동화**: PR의 코드 변경 사항을 분석하고, 잠재적 버그나 개선 사항을 코멘트로 작성하는 자동 리뷰어로 활용한다.

**레거시 코드 현대화**: 오래된 코드베이스의 프레임워크 마이그레이션, API 업데이트, 보안 패치 적용 등을 자동화한다. 예를 들어 Django 3.x에서 5.x로의 마이그레이션, Python 2에서 3으로의 전환 등에서 CodeAct의 일괄 처리 능력이 유용하다.

**테스트 자동 생성**: 기존 코드베이스에 대한 단위 테스트를 자동으로 생성한다. 에이전트가 소스 코드를 분석하고, 경계 조건과 예외 처리를 포함한 테스트 코드를 작성한 뒤, 실행하여 통과 여부를 검증한다.

**문서화 자동화**: 코드 변경 사항에 맞춰 README, API 문서, 인라인 주석을 자동 업데이트한다. BrowsingAgent를 활용하여 관련 공식 문서를 참고하면서 정확한 문서를 생성할 수 있다.

## 한계 및 과제

오픈소스 SWE 에이전트의 선두주자임에도 불구하고, OpenHands는 몇 가지 구조적 한계를 안고 있다.

**컨텍스트 윈도우 제한**: EventStream에 누적되는 이벤트가 LLM의 컨텍스트 윈도우를 초과하면 초기 이벤트를 잘라내야(truncate) 한다. 이로 인해 대규모 코드베이스에서 장시간 작업 시 에이전트가 이전 작업 맥락을 잃어버리는 문제가 발생한다. 특히 수십 개 파일을 수정하는 복잡한 리팩토링에서 이 한계가 두드러진다.

**높은 API 비용**: CodeAct 패러다임은 매 턴마다 전체 EventStream을 LLM에 전달하므로, 입력 토큰 소비가 매우 크다. 복잡한 이슈 하나를 해결하는 데 수십 턴이 소요되며, 이는 수만~수십만 토큰의 API 비용으로 이어진다. Claude 3.5 Sonnet 기준으로 복잡한 이슈 하나에 $1~5 수준의 비용이 발생할 수 있다.

**복잡한 리팩토링의 신뢰성**: 단일 파일 버그 수정에서는 높은 성공률을 보이지만, 아키텍처 수준의 대규모 리팩토링(모듈 분리, 디자인 패턴 변경 등)에서는 성공률이 크게 떨어진다. 에이전트가 전체 시스템의 의존성 그래프를 완벽하게 파악하기 어렵기 때문이다.

**셀프 호스팅 복잡성**: Docker-in-Docker 또는 원격 Docker 연결이 필요하여, 초기 설정이 다른 에이전트 도구(예: Aider) 대비 복잡하다. 기업 환경에서는 보안 정책으로 인해 Docker 소켓 공유가 제한되는 경우가 많아 추가 설정이 필요하다.

## 관련 모델

OpenHands는 Devin의 비전을 오픈소스로 구현하려는 시도로 시작되었다(초기명: OpenDevin). SWE-agent의 ACI 설계에서 영감을 받되, CodeAct라는 독자적 패러다임과 웹 UI를 통해 차별화했다. 학계-산업계 협업 모델로서 SWE 에이전트 연구의 표준 플랫폼으로 자리잡고 있다.

## 참고 자료

- Wang et al., "OpenDevin: An Open Platform for AI Software Developers as Generalist Agents", arXiv:2407.16741, 2024
- [OpenHands GitHub Repository](https://github.com/All-Hands-AI/OpenHands)

## 관련 문서

- [[swe-agent|SWE-agent]] - 영감
