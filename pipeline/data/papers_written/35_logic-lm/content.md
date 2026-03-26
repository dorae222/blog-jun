## 개요

대규모 언어 모델(LLM)은 자연어 이해와 생성에서 놀라운 성능을 보여주지만, 엄밀한 논리적 추론(logical reasoning)에서는 여전히 근본적인 한계를 노출합니다. 확률적 패턴 매칭에 기반한 LLM은 연역적 추론에서 논리적 비약이나 오류를 빈번히 범하며, 추론 깊이가 깊어질수록 오류가 지수적으로 누적됩니다.

Pan et al.(2023)이 EMNLP 2023에서 발표한 **Logic-LM**은 이 문제를 **신경-기호 통합(neuro-symbolic integration)** 방식으로 해결합니다. 핵심 설계 원칙은 간명합니다: LLM은 자연어를 형식 논리 프로그램으로 변환하는 **번역기(translator)**에 집중하고, 실제 추론은 수학적으로 건전하고 완전한(sound and complete) **기호 추론기(symbolic solver)**에 위임합니다. 이 역할 분리를 통해 각 구성 요소가 자신의 강점에 특화된 역할을 수행합니다.

Logic-LM은 문제 형식화(Problem Formulation), 기호 추론(Symbolic Solving), 자기 수정(Self-Refinement), 결과 해석(Result Interpretation)의 네 단계로 구성됩니다. 1차 논리(FOL), Prolog, 제약 최적화, 명제 논리(SAT) 등 다양한 형식 체계를 지원하며, FOLIO, ProntoQA, ProofWriter, LogicalDeduction, AR-LSAT 5개 벤치마크에서 Chain-of-Thought(CoT) 프롬프팅 대비 일관된 성능 향상을 달성하였습니다.

---

## 배경 및 문제

### LLM의 논리적 추론 한계

현대 LLM은 방대한 텍스트 코퍼스에서 학습한 패턴으로 다음 토큰을 예측합니다. 이 방식은 자연어 처리에서 뛰어나지만, 논리적 추론의 관점에서는 세 가지 근본적 한계를 갖습니다.

**연역적 추론의 비결정성.** 삼단논법(syllogism)이나 전건 긍정법(modus ponens) 같은 기본 추론 규칙을 LLM이 항상 올바르게 적용하지는 않습니다. "모든 A는 B이다"와 "x는 A이다"에서 "x는 B이다"라는 결론은 논리적 필연이지만, LLM은 이를 확률적으로 추정할 뿐입니다.

$$\forall x. A(x) \to B(x), \quad A(c) \quad \vdash \quad B(c)$$

**추론 체인의 오류 누적.** 복잡한 과제에서는 여러 단계의 추론이 연쇄적으로 필요합니다. 각 단계의 정확률이 $p$이고 추론 깊이가 $d$이면, 전체 정확률은 $p^d$로 지수적 감소합니다.

$$P(\text{correct chain}) = p^d$$

**형식적 보장의 부재.** LLM의 출력은 어떤 논리적 정리(theorem)에 의해서도 보장되지 않습니다. 동일한 입력에 대해 다른 답변을 생성할 수 있으며, 이는 논리적 추론이 요구하는 결정론성(determinism)에 부합하지 않습니다.

### 기존 접근법의 한계

Chain-of-Thought(CoT) 프롬프팅은 LLM에게 단계별 추론 과정을 생성하도록 유도하여 추론 능력을 향상시킵니다. 그러나 CoT는 여전히 LLM 내부에서 추론이 이루어지므로, 확률적 오류의 근본적 한계를 극복하지 못합니다. Tree-of-Thoughts(ToT)는 탐색 공간을 넓히고, Self-Consistency는 다수결 투표를 활용하지만, 모두 확률적 추론에 의존한다는 본질적 제약을 공유합니다.

이러한 배경에서 Logic-LM은 근본적으로 다른 접근을 취합니다: LLM의 추론 능력 자체를 향상시키는 대신, **추론을 수학적으로 검증된 외부 시스템에 위임**합니다.

### 기호 추론기의 강점

기호 추론기는 수십 년간 연구된 형식 검증(formal verification) 분야의 성과물로, 다음과 같은 수학적 보장을 제공합니다:

- **건전성(Soundness)**: 도출된 결론은 항상 전제로부터 논리적으로 유효합니다.
- **완전성(Completeness)**: 전제로부터 도출 가능한 모든 결론을 찾아낼 수 있습니다.
- **결정론성(Determinism)**: 동일한 입력에 대해 항상 동일한 결과를 반환합니다.

Z3 SMT 솔버는 충족 가능성 모듈로 이론(Satisfiability Modulo Theories)에 기반하여 명제 논리, 1차 논리, 산술 등 다양한 이론의 결정 절차를 제공합니다. Prolog는 SLD 분해(SLD Resolution)에 기반한 논리 프로그래밍 언어로, 규칙 기반 연쇄 추론에 특화되어 있습니다.

---

## 핵심 아이디어

Logic-LM의 설계 원칙은 **"LLM은 번역하고, 기호 추론기는 추론한다"**는 역할 분리입니다. 신경-기호 AI(neuro-symbolic AI) 패러다임의 구체적 구현체로서, 두 시스템의 상호 보완적 강점을 결합합니다.

### LLM의 역할: 자연어에서 형식 논리로의 번역

LLM은 풍부한 언어 지식으로 자연어의 의미를 파악하고, 기호 추론기가 처리할 수 있는 형식 논리 프로그램으로 변환합니다. 문맥 이해, 의미 분석, 코드 생성 등 LLM의 핵심 역량이 활용됩니다.

$$f_{\text{LLM}}: \text{NL}(\text{premises}, \text{query}) \to \text{FormalProgram}(\phi, q)$$

### 기호 추론기의 역할: 결정론적 추론

기호 추론기는 형식 논리 프로그램을 입력받아 수학적으로 보장된 추론을 수행합니다.

$$f_{\text{solver}}: \text{FormalProgram}(\phi, q) \to \text{Result} \in \{\text{True}, \text{False}, \text{Unknown}\}$$

전체 시스템은 두 함수의 합성으로 표현됩니다:

$$\text{Logic-LM} = f_{\text{solver}} \circ f_{\text{LLM}}$$

이 합성에서 LLM이 올바르게 형식화를 수행하면, 기호 추론기의 건전성에 의해 최종 결과의 논리적 정확성이 보장됩니다. 따라서 전체 시스템의 성능 병목은 LLM의 추론 능력이 아니라 **형식화 품질**에 달려 있습니다.

---

## 방법론

### 전체 파이프라인 구조

![Logic-LM 세 모듈 구성도: 문제 형식화, 기호 추론, 결과 해석의 전체 파이프라인](figures/fig_2.png)
*Figure 2. Logic-LM의 세 모듈 구성. (1) Problem Formulator가 인컨텍스트 학습으로 자연어 문제를 기호 표현으로 변환하고, (2) Symbolic Reasoner가 논리 프로그래밍/FOL/제약 최적화/SAT 중 적절한 추론기로 논리 추론을 수행하며, (3) Result Interpreter가 기호 답변을 자연어로 해석한다. 세 가지 서로 다른 벤치마크 문제 유형에 대한 변환 예시가 함께 제시되어 있다. (Pan et al., 2023)*

Logic-LM의 전체 파이프라인은 네 단계로 구성됩니다:

$$\text{자연어 문제} \xrightarrow{\text{LLM (형식화)}} \text{형식 프로그램} \xrightarrow{\text{기호 추론기}} \text{형식 결과} \xrightarrow{\text{매핑}} \text{최종 답변}$$

기호 추론기 단계에서 오류가 발생하면, 자기 수정(Self-Refinement) 루프가 활성화되어 형식 프로그램을 반복적으로 개선합니다.

### 1단계: 문제 형식화 (Problem Formulation)

LLM은 퓨샷 프롬프팅(few-shot prompting)을 통해 자연어 문제를 형식 논리 표현으로 변환합니다. 프롬프트에는 변환 규칙과 예시가 포함되며, 문제 유형에 따라 적절한 형식 체계가 선택됩니다.

**지원하는 형식 체계:**

| 형식 체계 | 추론기 | 적용 문제 유형 | 벤치마크 |
|-----------|--------|----------------|----------|
| 1차 논리 (FOL) | Z3 SMT Solver | 연역적 추론, 충족 가능성 | FOLIO |
| Prolog | SWI-Prolog | 규칙 기반 연쇄 추론 | ProntoQA, ProofWriter |
| 제약 최적화 | Python (PuLP) | 제약 충족 문제 | LogicalDeduction |
| 명제 논리 | Z3 SAT | 논리 퍼즐, 법학 추론 | AR-LSAT |

![Logic-LM이 FOLIO 문제에 대해 생성한 기호 표현과 추론 결과 예시](figures/fig_5.png)
*Figure 5. FOLIO 벤치마크 문제에 대한 Logic-LM의 기호 변환 예시. 자연어 전제("Stranger Things is a popular Netflix show..." 등)를 FOL 술어와 규칙으로 정확히 변환하고, 질의에 대해 결정론적 추론 결과를 도출하는 과정을 보여준다. (Pan et al., 2023)*

**FOL 형식화 예시 (Z3):**

자연어 입력:
```
전제: 모든 개발자는 커피를 좋아한다.
        Alice는 개발자이다.
질의: Alice는 커피를 좋아하는가?
```

LLM이 생성하는 Z3 프로그램:
```python
from z3 import *

# 변수 및 함수 선언
x = Const('x', DeclareSort('Object'))
alice = Const('alice', DeclareSort('Object'))
developer = Function('developer', DeclareSort('Object'), BoolSort())
likes_coffee = Function('likes_coffee', DeclareSort('Object'), BoolSort())

# 전제 형식화
s = Solver()
s.add(ForAll([x], Implies(developer(x), likes_coffee(x))))  # 규칙
s.add(developer(alice))  # 사실

# 질의: alice가 커피를 좋아하지 않는다고 가정하면 모순인가?
s.add(Not(likes_coffee(alice)))
result = s.check()  # UNSAT -> 즉, alice는 커피를 좋아함
```

**Prolog 형식화 예시:**

```prolog
% 전제
developer(alice).
likes_coffee(X) :- developer(X).

% 질의
?- likes_coffee(alice).  % true
```

형식화 과정에서 LLM은 다음을 수행합니다:
- 자연어 전제에서 술어(predicate), 상수(constant), 변수(variable)를 식별
- 논리적 구조(전칭 양화, 존재 양화, 함의, 부정 등)를 형식 논리 연결사로 변환
- 질의를 추론기가 처리할 수 있는 형태(충족 가능성 검사, 쿼리 등)로 변환

### 2단계: 기호 추론 (Symbolic Solving)

형식 프로그램이 생성되면 해당 추론기를 실행하여 결정론적 추론을 수행합니다.

**Z3 SMT 솔버의 동작 원리:**

Z3는 주어진 논리식 $\phi$에 대해 충족 가능성(satisfiability)을 판별합니다:

$$\text{Z3}(\phi) \to \begin{cases} \text{SAT} & \text{if } \exists \mathcal{M}. \mathcal{M} \models \phi \\ \text{UNSAT} & \text{if } \forall \mathcal{M}. \mathcal{M} \not\models \phi \\ \text{UNKNOWN} & \text{otherwise} \end{cases}$$

Logic-LM에서는 "질의의 부정이 전제와 모순인가?"를 검사하는 반증법 방식을 사용합니다. $\phi \wedge \neg q$가 UNSAT이면 $q$는 $\phi$로부터 논리적으로 도출됩니다:

$$\phi \models q \iff \phi \wedge \neg q \text{ is UNSAT}$$

**Prolog의 동작 원리:**

Prolog는 SLD 분해에 기반한 후방 연쇄 추론(backward chaining)을 수행합니다. 질의가 주어지면 규칙을 역방향으로 적용하여 사실(fact)에 도달할 수 있는지 확인합니다.

### 3단계: 자기 수정 (Self-Refinement)

LLM이 생성한 형식 프로그램에 구문 오류나 실행 오류가 있을 수 있습니다. Logic-LM은 이를 자동으로 복구하는 자기 수정 메커니즘을 포함합니다.

자기 수정 프로세스:

1. 기호 추론기에서 오류가 발생하면, 오류 메시지를 캡처
2. LLM에게 원본 프로그램, 오류 메시지, 원본 자연어 문제를 함께 제공
3. LLM이 오류를 분석하고 수정된 형식 프로그램을 생성
4. 수정된 프로그램을 다시 추론기에서 실행
5. 이 과정을 최대 $k$번(논문에서는 $k=3$) 반복

![다양한 벤치마크에서 Logic-LM의 기호 변환 및 자기 수정 예시 4건](figures/fig_6.png)
*Figure 6. Logic-LM의 기호 변환 및 자기 수정 예시. 4개의 서로 다른 벤치마크(FOLIO, ProntoQA, LogicalDeduction, AR-LSAT) 문제에 대한 형식화 결과를 보여준다. 빨간색은 초기 형식화의 오류 구간과 원문 대응 위치, 초록색은 자기 수정을 통해 교정된 내용을 나타낸다. (Pan et al., 2023)*

자기 수정의 효과는 상당합니다. 수정 없이는 약 15~25%의 케이스에서 실행 오류가 발생하지만, 자기 수정 적용 시 오류율이 5% 이하로 감소합니다.

### 4단계: 결과 해석 (Result Interpretation)

기호 추론기의 출력을 원래 문제의 답변 형식에 맞게 매핑합니다:

| 추론기 출력 | 문제 유형 | 최종 답변 |
|-------------|-----------|----------|
| UNSAT | FOL 연역 | True (질의가 전제로부터 도출됨) |
| SAT | FOL 연역 | False 또는 Unknown |
| true | Prolog 쿼리 | True |
| false | Prolog 쿼리 | False |
| 최적값 | 제약 최적화 | 해당 값 또는 선택지 |

---

## 실험 결과

### 벤치마크 데이터셋

Logic-LM은 논리적 추론의 다양한 측면을 평가하는 5개 벤치마크에서 검증되었습니다:

| 벤치마크 | 문제 유형 | 추론 형식 | 규모 |
|----------|-----------|-----------|------|
| FOLIO | 1차 논리 추론 | FOL (Z3) | 204 |
| ProntoQA | 연쇄 연역 추론 | Prolog | 500 |
| ProofWriter | 다단계 연역 추론 | Prolog | 600 |
| LogicalDeduction | 제약 충족 | Python | 300 |
| AR-LSAT | 분석적 추론 (법학) | SAT (Z3) | 230 |

- **FOLIO**: Wikipedia 기반의 1차 논리 추론 데이터셋으로, 전제-가설 쌍에 대해 True/False/Unknown을 판별
- **ProntoQA**: 합성된 온톨로지 기반 연쇄 추론 데이터셋으로, 여러 단계의 is-a 관계를 추적
- **ProofWriter**: 규칙 기반 다단계 추론 데이터셋으로, 깊이 0~5까지의 추론 체인을 요구
- **LogicalDeduction**: BIG-Bench의 논리적 추론 과제로, 순서 관계 등의 제약을 만족하는 해를 탐색
- **AR-LSAT**: LSAT 법학 적성 시험의 분석적 추론 섹션에서 추출한 복잡한 제약 추론 문제

### GPT-4 기반 주요 결과

| 벤치마크 | Standard | CoT | Logic-LM | 향상 (vs CoT) |
|----------|----------|-----|----------|---------------|
| FOLIO | 68.6 | 70.3 | **79.8** | +9.5%p |
| ProntoQA | 79.5 | 82.1 | **97.0** | +14.9%p |
| ProofWriter | 56.7 | 65.0 | **79.9** | +14.9%p |
| LogicalDeduction | 60.3 | 67.6 | **81.3** | +13.7%p |
| AR-LSAT | 24.8 | 28.5 | **36.8** | +8.3%p |

모든 벤치마크에서 Logic-LM이 Standard 프롬프팅과 CoT 프롬프팅을 모두 상회합니다. 특히 ProntoQA에서는 97.0%의 정확도를 달성하여, 규칙이 명확한 연역 추론에서 기호 추론기의 효과가 극대화됨을 보여줍니다.

### 추론 깊이에 따른 성능 분석

![ProofWriter 데이터셋에서 추론 깊이별 Standard, CoT, Logic-LM 정확도 비교 그래프](figures/fig_3.png)
*Figure 3. ProofWriter 데이터셋에서 추론 깊이(reasoning depth)에 따른 모델별 정확도 변화. Standard와 CoT 프롬프팅은 추론 깊이가 증가할수록 급격히 성능이 하락하는 반면, Logic-LM은 깊이 5에서도 상대적으로 높은 정확도를 유지한다. 이는 기호 추론기가 추론 체인 길이와 무관하게 결정론적 추론을 수행하기 때문이다. (Pan et al., 2023)*

추론 깊이에 따른 성능 변화는 Logic-LM의 핵심 이점을 가장 극적으로 보여줍니다. Standard와 CoT 프롬프팅은 추론 깊이가 증가하면 정확도가 급격히 하락합니다. 이는 앞서 논의한 오류 누적 문제($p^d$)의 직접적 현상입니다. 반면 Logic-LM은 LLM이 형식화만 올바르게 수행하면, 기호 추론기가 깊이와 무관하게 정확한 추론을 보장하므로 성능 하락이 현저히 적습니다.

### GPT-3.5 기반 결과: 모델 크기 효율성

| 벤치마크 | CoT (GPT-3.5) | Logic-LM (GPT-3.5) | CoT (GPT-4) |
|----------|---------------|---------------------|-------------|
| FOLIO | 56.4 | 66.7 | 70.3 |
| ProntoQA | 65.8 | **85.4** | 82.1 |
| ProofWriter | 48.2 | **69.1** | 65.0 |
| LogicalDeduction | 39.7 | 56.0 | 67.6 |
| AR-LSAT | 19.1 | 25.2 | 28.5 |

주목할 점은, GPT-3.5 기반 Logic-LM이 ProntoQA(85.4 vs 82.1)와 ProofWriter(69.1 vs 65.0)에서 GPT-4 기반 CoT를 상회한다는 것입니다. 이는 기호 추론기의 결합이 더 작은 LLM의 추론 한계를 효과적으로 보완할 수 있음을 시사합니다. 즉, **형식화만 적절히 수행되면 추론의 품질은 LLM의 크기에 의존하지 않습니다**.

### 자기 수정의 효과 분석

| 벤치마크 | Logic-LM (수정 없음) | Logic-LM (수정 있음) | 오류율 감소 |
|----------|---------------------|---------------------|------------|
| FOLIO | 73.5 | 79.8 | 22% -> 6% |
| ProntoQA | 91.2 | 97.0 | 18% -> 4% |
| ProofWriter | 72.3 | 79.9 | 25% -> 7% |
| LogicalDeduction | 74.8 | 81.3 | 20% -> 5% |
| AR-LSAT | 31.7 | 36.8 | 23% -> 8% |

자기 수정 메커니즘은 모든 벤치마크에서 일관된 성능 향상을 가져왔습니다. 특히 형식화 난이도가 높은 ProofWriter(+7.6%p)와 ProntoQA(+5.8%p)에서 큰 효과를 보였으며, 이는 복잡한 문제일수록 초기 형식화에서 오류가 발생할 가능성이 높기 때문입니다. 3라운드 이후에는 추가 수정의 한계 효용이 급감하여 수렴합니다.

### 오류 분석

Logic-LM의 오류는 세 가지 범주로 분류됩니다:

1. **형식화 오류 (Formulation Error, ~45%)**: LLM이 자연어의 의미를 잘못 형식화한 경우. 양화사 범위 오류, "모든"/"어떤" 혼동, 부정의 범위(scope of negation) 오류 등이 대표적입니다.
2. **실행 오류 (Execution Error, ~20%)**: 구문 오류나 타입 오류로 추론기가 실행되지 않는 경우. 자기 수정으로 대부분 해결됩니다.
3. **매핑 오류 (Mapping Error, ~10%)**: 추론기 출력을 최종 답변으로 변환하는 과정에서 발생하는 오류.

형식화 오류가 전체 오류의 거의 절반을 차지한다는 점에서, Logic-LM의 성능 상한은 LLM의 형식 논리 번역 능력에 의해 결정됩니다.

---

## 의의 및 한계

### 학술적 의의

**신뢰할 수 있는 논리 추론의 실현.** Logic-LM은 LLM의 추론 결과에 형식적 보장을 부여하는 실용적 방법을 제시합니다. 기호 추론기의 건전성과 완전성에 의해, 형식화가 올바르다면 추론 결과도 반드시 올바릅니다. 의료, 법률, 금융 등 논리적 정확성이 요구되는 도메인에서의 LLM 활용 가능성을 높입니다.

**설명 가능한 AI 추론.** 기호 추론기는 추론 과정을 명시적인 논리식과 증명 단계로 표현합니다. 블랙박스인 LLM의 내부 추론과 달리, 결과에 대한 투명한 설명을 자동으로 생성합니다. 감사 가능성(auditability)이 요구되는 응용 분야에서 특히 중요합니다.

**역할 분리 원칙의 실증.** LLM과 기호 시스템의 강점을 분리하여 결합하는 것이 각각을 단독 사용하는 것보다 우수함을 실험적으로 증명하였습니다. 신경-기호 AI 연구의 구체적 설계 원칙으로 활용될 수 있습니다.

**모델 크기 효율성.** GPT-3.5 기반 Logic-LM이 일부 벤치마크에서 GPT-4 CoT를 상회한다는 발견은, 기호 추론기와의 결합이 더 작은 모델의 한계를 보완하여 비용 효율적인 시스템 설계를 가능하게 함을 보여줍니다.

### 한계점

**형식화 품질 의존성.** 전체 오류의 약 45%가 형식화 오류에서 기인합니다. 양화사의 범위 모호성("모든 학생이 어떤 과목을 좋아한다"), 암묵적 전제(세상 지식 의존), 비단조 논리(예외 허용 규칙) 등은 형식화가 본질적으로 어렵습니다.

**지원 추론 유형의 제한.** Logic-LM은 연역적 추론에 특화되어 있으며, 귀납적 추론(inductive reasoning), 유비 추론(analogical reasoning), 확률적 추론(probabilistic reasoning) 등은 지원하지 않습니다. 이러한 추론 유형은 베이지안 네트워크, 확률 프로그래밍 등 다른 형식 체계와의 결합이 필요합니다.

**상식 및 맥락 추론의 한계.** 기호 논리는 명시적으로 주어진 전제에만 의존합니다. "새는 날 수 있다", "물은 아래로 흐른다" 같은 암묵적 상식 지식을 필요로 하는 추론은 별도의 지식 기반 없이 처리할 수 없습니다.

**계산 비용 증가.** LLM 호출에 더해 기호 추론기 실행과 자기 수정 반복이 추가적인 지연 시간을 유발합니다. 특히 자기 수정이 최대 횟수까지 반복될 경우 응답 시간이 크게 증가합니다.

**오픈소스 LLM 호환성.** 논문의 주요 결과는 GPT-4/GPT-3.5 기반이며, 코드 생성 능력이 상대적으로 약한 오픈소스 LLM에서는 형식화 오류율이 크게 증가할 것으로 예상됩니다.

### 후속 연구

- **LINC (2023)**: FOL과 Prolog에 특화하여 Logic-LM의 아이디어를 확장
- **SatLM (2023)**: SAT 솔버와의 결합에 초점을 맞춘 연구
- **LEVER (2023)**: 코드 검증기를 활용한 자기 수정 메커니즘 제안
- **Tool-augmented LLM**: Logic-LM은 ReAct, Toolformer 등 도구 사용 LLM의 맥락에서, 외부 도구 결합을 통한 LLM 능력 확장의 중요한 사례

---

## 코드 예제

### Logic-LM 파이프라인 구현

다음은 Logic-LM의 핵심 파이프라인을 간소화하여 Python으로 구현한 예제입니다.

```python
from z3 import *
import openai

class LogicLM:
    """Logic-LM 신경-기호 추론 파이프라인"""

    def __init__(self, model: str = "gpt-4", max_refinements: int = 3):
        self.model = model
        self.max_refinements = max_refinements
        self.client = openai.OpenAI()

    def formulate(self, problem: str) -> str:
        """1단계: LLM을 사용하여 자연어를 형식 논리 프로그램으로 변환"""
        prompt = f"""다음 논리 추론 문제를 Z3 Python 코드로 변환하세요.
결과는 'result' 변수에 True/False/Unknown으로 저장하세요.

문제:
{problem}

Z3 Python 코드:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content

    def solve(self, program: str) -> dict:
        """2단계: 기호 추론기 실행"""
        namespace = {}
        try:
            exec(program, namespace)
            return {
                "success": True,
                "result": namespace.get("result", "Unknown")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def refine(self, problem: str, program: str, error: str) -> str:
        """3단계: 오류 발생 시 LLM을 통한 자기 수정"""
        prompt = f"""다음 Z3 프로그램에서 오류가 발생했습니다.

원본 문제: {problem}

프로그램:
{program}

오류 메시지: {error}

오류를 수정하여 올바른 Z3 Python 코드를 다시 생성하세요."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content

    def reason(self, problem: str) -> str:
        """전체 파이프라인 실행"""
        # 1단계: 형식화
        program = self.formulate(problem)

        # 2단계 + 3단계: 추론 및 자기 수정 루프
        for attempt in range(self.max_refinements + 1):
            result = self.solve(program)

            if result["success"]:
                return result["result"]

            if attempt < self.max_refinements:
                program = self.refine(
                    problem, program, result["error"]
                )

        # 모든 수정 시도 실패 시 LLM 단독 추론으로 폴백
        return self._fallback_reasoning(problem)

    def _fallback_reasoning(self, problem: str) -> str:
        """기호 추론 실패 시 CoT 폴백"""
        prompt = f"단계별로 추론하여 답하세요:\n{problem}"
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content


# 사용 예시
if __name__ == "__main__":
    logic_lm = LogicLM(model="gpt-4", max_refinements=3)

    problem = """
    전제:
    1. 모든 프로그래머는 논리적 사고를 할 수 있다.
    2. 논리적 사고를 할 수 있는 사람은 수학 문제를 풀 수 있다.
    3. Alice는 프로그래머이다.

    질의: Alice는 수학 문제를 풀 수 있는가?
    """

    answer = logic_lm.reason(problem)
    print(f"답변: {answer}")  # True
```

### Z3를 활용한 직접 추론 예제

다음은 기호 추론기의 동작을 직접 확인할 수 있는 Z3 예제입니다.

```python
from z3 import *

# 정렬(Sort) 선언
Person = DeclareSort('Person')

# 술어(Predicate) 선언
programmer = Function('programmer', Person, BoolSort())
logical_thinker = Function('logical_thinker', Person, BoolSort())
can_solve_math = Function('can_solve_math', Person, BoolSort())

# 상수(Constant) 선언
alice = Const('alice', Person)
x = Const('x', Person)

# 솔버 생성 및 전제 추가
s = Solver()

# 전제 1: 모든 프로그래머는 논리적 사고를 할 수 있다
s.add(ForAll([x], Implies(programmer(x), logical_thinker(x))))

# 전제 2: 논리적 사고를 할 수 있는 사람은 수학을 풀 수 있다
s.add(ForAll([x], Implies(logical_thinker(x), can_solve_math(x))))

# 전제 3: Alice는 프로그래머이다
s.add(programmer(alice))

# 질의: Alice가 수학을 풀 수 없다고 가정 -> 모순 검사
s.add(Not(can_solve_math(alice)))

if s.check() == unsat:
    print("결론: Alice는 수학 문제를 풀 수 있다 (True)")
    # 추론 체인: programmer(alice) -> logical_thinker(alice)
    #            -> can_solve_math(alice)
elif s.check() == sat:
    print("결론: 주어진 전제로부터 도출할 수 없다 (Unknown)")
```

이 코드는 Logic-LM에서 Z3 솔버가 수행하는 추론 과정을 명시적으로 보여줍니다. 질의의 부정을 전제에 추가하여 UNSAT이 되는지 확인하는 반증법(proof by contradiction) 방식이 핵심입니다.

---

## 관련 연구

| 접근법 | 추론 주체 | 형식적 보장 | 설명 가능성 | 범용성 |
|--------|-----------|-------------|-------------|--------|
| Standard Prompting | LLM | 없음 | 낮음 | 높음 |
| Chain-of-Thought | LLM | 없음 | 중간 | 높음 |
| Self-Consistency | LLM (앙상블) | 없음 | 중간 | 높음 |
| **Logic-LM** | **기호 추론기** | **있음** | **높음** | **중간** |
| PAL | Python 인터프리터 | 부분적 | 높음 | 중간 |
| Faithful CoT | LLM + 코드 | 부분적 | 높음 | 중간 |

Logic-LM은 형식적 보장과 설명 가능성 측면에서 다른 접근법보다 우수하지만, 범용성에서는 순수 LLM 기반 접근법보다 제한적입니다. 이는 지원 가능한 형식 체계의 범위에 의해 결정됩니다.

---

## 결론

Logic-LM은 LLM의 논리적 추론 한계를 극복하기 위한 실용적이고 효과적인 신경-기호 프레임워크입니다. "LLM은 번역하고, 기호 추론기는 추론한다"는 명확한 역할 분리를 통해 각 구성 요소의 강점을 극대화하였으며, 5개 벤치마크에서의 일관된 성능 향상이 이 접근법의 유효성을 입증합니다.

형식화 품질에 대한 의존성이라는 한계가 있지만, 자기 수정 메커니즘과 향후 더 강력한 코드 생성 LLM의 등장으로 점진적 완화가 기대됩니다. 특히 GPT-3.5+기호추론기가 GPT-4 단독 추론을 일부 상회한다는 결과는, 모델 크기 확장(scaling up)에만 의존하지 않고 외부 도구와의 결합을 통해 추론 품질을 높일 수 있음을 보여주는 중요한 시사점입니다. Logic-LM은 신뢰할 수 있는 AI 추론 시스템을 향한 중요한 이정표입니다.