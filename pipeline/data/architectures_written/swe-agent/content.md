# SWE-agent: Agent-Computer Interface 설계의 선구자

**Princeton** · **2024-04-02** · **Code Agent** · **MIT**

## 개요

SWE-agent는 LLM이 실제 GitHub 이슈를 자율적으로 해결하는 소프트웨어 엔지니어링 에이전트로, Agent-Computer Interface(ACI) 설계 철학을 중심으로 구축되었다. Yang et al.(Princeton, 2024)이 논문 "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering"에서 발표한 이 시스템은, LLM이 명령줄 환경에서 파일 탐색, 코드 편집, 테스트 실행을 효과적으로 수행할 수 있도록 최적화된 도구 인터페이스를 설계했다.

SWE-agent의 핵심 통찰은 **"도구의 인터페이스 설계가 에이전트 성능에 결정적 영향을 미친다"**는 것이다. 인간 개발자에게 최적화된 표준 bash 인터페이스는 LLM에게 최적이 아니다. LLM은 긴 터미널 출력 파싱, 정밀한 커서 조작, 복잡한 명령 옵션 조합에 취약하다. SWE-agent는 이 문제를 HCI(Human-Computer Interaction)의 원리를 ACI(Agent-Computer Interaction)로 전환하여 해결한다. LLM의 강점(자연어 이해, 코드 추론)을 극대화하고 약점(정밀한 문자열 조작, 긴 출력 관리)을 보완하는 전용 인터페이스를 설계함으로써, **동일한 모델로도 2~6배 높은 이슈 해결률**을 달성한다.

SWE-bench 벤치마크에서 GPT-4 기반으로 12.47%의 이슈 해결률을 달성한 SWE-agent는, 이전 RAG 기반 접근법(1.96%)을 6배 이상 상회하며 최초의 체계적 소프트웨어 엔지니어링 에이전트로 주목받았다. 더 중요한 것은 SWE-agent가 확립한 ACI 설계 원칙과 SWE-bench 벤치마크가 이후 소프트웨어 에이전트 분야 전체의 표준이 되었다는 점이다. Devin, OpenHands, Claude Code, Goose 등 모든 후속 SWE 에이전트가 SWE-bench를 기준으로 성능을 측정하며, ACI 설계 원칙을 참조한다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

SWE-agent의 아키텍처는 ACI(Agent-Computer Interface) 설계 원칙을 중심으로 구축되었다.

### ACI 설계 원칙

ACI 설계의 네 가지 핵심 원칙은 다음과 같다.

1. **정보 밀도 제어**: LLM에게 한 번에 보이는 정보량을 제한하여 정보 과부하(information overload)를 방지한다. `cat` 명령이 수천 줄을 출력하는 대신, `open` 명령이 100줄 윈도우로 표시한다.

2. **명확한 피드백**: 행동의 결과를 구조화된 형태로 즉시 피드백한다. 편집 성공/실패, 검색 결과 수, 현재 위치 등을 명시적으로 전달한다.

3. **오류 복구 지원**: 잘못된 편집 시 자동으로 원래 상태로 롤백하고, 구문 오류를 지적하며, 수정 재시도를 유도한다. 이는 에이전트가 실수로부터 회복할 수 있게 하는 핵심 메커니즘이다.

4. **조합 가능성(Composability)**: 도구들을 자유롭게 조합하여 복잡한 워크플로를 구성할 수 있도록 설계한다.

### 핵심 도구 세트

| 도구 | 기능 | bash 대비 장점 |
|------|------|---------------|
| `open [file] [line]` | 파일을 라인 번호와 함께 100줄 윈도우로 표시 | `cat`의 대량 출력 문제 해결 |
| `scroll_up` / `scroll_down` | 파일 뷰어를 위/아래로 스크롤 | 페이지네이션 자동 관리 |
| `search_file [pattern] [file]` | 파일 내 패턴 검색 | `grep`보다 LLM 친화적 출력 |
| `search_dir [pattern] [dir]` | 디렉토리 전체에서 패턴 검색 | 결과를 구조화하여 표시 |
| `edit [start:end]` | 특정 라인 범위를 새 내용으로 교체 | 전체 파일 재작성 불필요 |
| `create [file]` | 새 파일 생성 | 경로 자동 생성 |
| `submit` | 최종 패치 제출 | 변경 사항 요약 자동 생성 |

### ReAct 기반 실행 루프

SWE-agent는 ReAct 패턴을 SWE 도메인에 특화하여 적용한다. Thought에서 현재 상황을 분석하고, Action에서 ACI 도구를 실행하며, Observation에서 결과를 확인하는 사이클을 반복한다.

$$\pi_{\text{SWE}}(a_t | \text{issue}, o_{1:t}, a_{1:t-1}) = \text{LLM}(\text{thought}_t, \text{action}_t)$$

```
[SWE-agent 실행 흐름 예시]

GitHub 이슈: "KeyError 발생: config.yaml에서
              'timeout' 키가 누락된 경우"

Thought 1: 먼저 관련 코드 파일을 찾아야 한다.
          'KeyError'와 'timeout'을 검색하자.
Action 1: search_dir "KeyError" src/
Observation 1: Found in src/config_loader.py (line 45)

Thought 2: 해당 파일에서 KeyError가 발생하는
          코드를 확인한다.
Action 2: open src/config_loader.py 40
Observation 2:
  40| def load_config(path):
  41|     with open(path) as f:
  42|         config = yaml.safe_load(f)
  43|
  44|     # 문제 지점: 키가 없으면 KeyError 발생
  45|     timeout = config['timeout']
  46|     return Config(timeout=timeout)

Thought 3: config.get()을 사용해 기본값을 제공하면
          KeyError를 방지할 수 있다.
Action 3: edit 45:45
     timeout = config.get('timeout', 30)
end_of_edit
Observation 3: File updated successfully.
               [Lint passed: no syntax errors]

Thought 4: 수정이 올바른지 테스트를 실행한다.
Action 4: python -m pytest tests/test_config.py -v
Observation 4: 5 passed, 0 failed

Action 5: submit
```

### 에러 복구 메커니즘

편집 시 구문 오류가 발생하면, SWE-agent는 자동으로 원래 상태로 롤백하고 에러 메시지를 표시한다.

```
Action: edit 45:46
     timeout = config.get('timeout', 30
end_of_edit

Observation: ERROR: Syntax error detected!
  Line 45: SyntaxError: unexpected EOF while parsing
  Edit reverted. Please fix the syntax error
  and try again.
```

이 자동 롤백 메커니즘은 에이전트가 잘못된 편집으로 코드베이스를 오염시키는 것을 방지하며, Reflexion과 유사한 자기 수정 루프를 자연스럽게 형성한다.

## 핵심 혁신

1. **ACI 설계 철학**: "인간을 위한 인터페이스"와 "AI를 위한 인터페이스"는 다르다는 통찰을 체계화했다. HCI 원칙을 에이전트 도구 설계에 적용한 최초의 체계적 연구로, 이후 Claude Code의 Edit/Glob/Grep 도구, OpenHands의 CodeAct, Goose의 도구 시스템 등에 직접적 영향을 미쳤다.

2. **SWE-bench 벤치마크 확립**: 2,294개의 실제 GitHub 이슈-PR 쌍으로 구성된 SWE-bench는, 이후 소프트웨어 에이전트의 표준 벤치마크로 자리잡았다. SWE-bench Verified(500개 인간 검증 인스턴스), SWE-bench Lite(300개 경량 인스턴스) 등의 변형이 후속으로 등장하여 평가 생태계를 형성했다.

3. **검색-이해-수정 패턴**: 코드베이스를 탐색하는 도구(search, open)와 수정하는 도구(edit)를 명확히 분리하여, 에이전트가 "먼저 이해하고 나서 수정"하는 워크플로를 자연스럽게 따르도록 유도한다. 이 패턴은 인간 개발자의 실제 작업 흐름과 일치한다.

4. **에러 피드백 루프**: 편집 후 구문 오류가 발생하면 자동으로 롤백하고 에러 정보를 제공하여, 에이전트가 수정을 재시도할 수 있게 한다. 이는 Reflexion의 자기 반성 메커니즘을 도구 수준에서 구현한 것이다.

## 벤치마크/성능

| 시스템 | 모델 | SWE-bench (전체) | SWE-bench Lite | 접근 방식 |
|-------|------|-----------------|----------------|----------|
| SWE-agent | GPT-4 | **12.47%** | 18.0% | ACI 도구 |
| SWE-agent | Claude 3.5 | - | 23.0% | ACI 도구 |
| RAG baseline | GPT-4 | 1.96% | - | 검색+생성 |
| Shell-only | GPT-4 | 3.8% | - | 표준 bash |

초기 발표 시점에서 RAG 기반 접근법(1.96%)을 6배 이상 상회하는 12.47%를 달성했다. 특히 주목할 점은 동일한 GPT-4 모델에서 표준 bash 인터페이스(3.8%)와 ACI 인터페이스(12.47%)의 차이가 3배 이상이라는 것이다. 이는 **"모델을 바꾸지 않고 인터페이스만 변경해도 성능이 크게 향상될 수 있다"**는 ACI 설계의 핵심 주장을 실증한다.

## 구현

**GitHub Issue 자동 해결 봇**: SWE-agent를 GitHub Actions와 연동하여, 특정 라벨(예: "good-first-issue", "bug")이 붙은 이슈를 자동으로 분석하고 PR을 생성하는 봇을 구축할 수 있다. Docker 컨테이너 기반의 격리된 실행 환경에서 안전하게 동작한다.

**코드 마이그레이션 자동화**: API 변경, 라이브러리 업데이트, 프레임워크 마이그레이션 등으로 인한 대량의 코드 수정을 자동화할 수 있다. SWE-agent의 검색-이해-수정 패턴이 이런 반복적 수정 작업에 적합하다.

**ACI 연구 플랫폼**: SWE-agent의 오픈소스 구조(MIT 라이선스)를 활용하여, 새로운 ACI 도구와 인터페이스 설계를 실험하고 SWE-bench에서 성능을 비교하는 연구 플랫폼으로 활용된다.

## 관련 모델

SWE-agent는 ReAct의 Thought-Action-Observation 루프를 소프트웨어 엔지니어링 도메인에 특화하여 적용한 시스템이다. ACI 설계 철학은 이후 Claude Code의 도구 설계(Read/Edit/Glob/Grep), OpenHands의 CodeAct 패러다임, Goose의 확장 가능한 도구 시스템에 직접적 영향을 미쳤다. SWE-bench는 Devin, OpenHands, Claude Code 등 모든 SWE 에이전트의 표준 벤치마크로 채택되었다.

## 참고 자료

- Yang et al., "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering", arXiv:2405.15793, 2024
- [SWE-agent GitHub Repository](https://github.com/princeton-nlp/SWE-agent)
- [SWE-bench Benchmark](https://www.swebench.com)

## 관련 문서

- [[react|ReAct]] — 발전 기반
- [[devin|Devin]] — 영감을 줌
- [[goose|Goose]] — 영감을 줌
- [[openhands|OpenHands]] — 영감을 줌
