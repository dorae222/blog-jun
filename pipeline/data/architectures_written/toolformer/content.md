# Toolformer: 언어 모델의 자기지도 도구 학습

**Meta AI** · **2023-02-09** · **Tool Learning** · **오픈**

## 개요

Toolformer는 언어 모델이 어떤 API를 언제 호출하고 어떤 인수를 전달할지를 자기지도(self-supervised) 방식으로 스스로 학습하는 기법이다. Meta AI의 Schick et al.이 2023년 논문 "Toolformer: Language Models Can Teach Themselves to Use Tools"에서 발표한 이 방법은, 인간의 레이블링 없이도 모델이 계산기, 검색 엔진, 번역기, 위키피디아 API, 달력 등 다양한 외부 도구를 텍스트 생성 흐름 안에 자연스럽게 삽입하도록 파인튜닝한다.

Toolformer의 혁신적 기여는 **도구 사용 능력을 모델 가중치에 직접 내재화**한다는 점이다. ReAct 같은 프롬프트 기반 도구 사용은 런타임에 few-shot 예시로 도구 사용법을 안내하지만, Toolformer는 모델이 "어떤 위치에서 어떤 도구를 호출하면 유용한가"를 학습 단계에서 체화한다. 이는 추론 시 추가 프롬프트 오버헤드 없이 자연스러운 도구 통합을 가능하게 한다.

이 접근의 핵심 아이디어는 **"도구 호출이 텍스트 예측을 개선하는가?"**라는 질문으로 요약된다. Toolformer는 텍스트의 각 위치에 다양한 API 호출을 삽입해 보고, 해당 호출이 후속 토큰 예측의 perplexity를 $\tau$ 이상 감소시키면 "유용한" 호출로 판정하여 학습 데이터에 포함한다. 이 자기지도 필터링 메커니즘은 인간 어노테이션 없이도 대규모 학습 데이터를 자동 생성할 수 있게 하며, 도구 사용 학습의 스케일러빌리티를 획기적으로 높인다. 특히 6.7B 크기의 Toolformer가 66B 크기의 OPT보다 뛰어난 성능을 보여, **도구 사용이 모델 크기의 한계를 보완할 수 있음**을 입증했다.

![Toolformer 아키텍처 — 자기지도 API 호출 학습과 perplexity 기반 필터링을 통한 도구 사용 내재화 구조](figures/architecture.svg)

*Figure 1: Toolformer 아키텍처 — 텍스트의 각 위치에 API 호출 후보를 샘플링하고, perplexity 감소 기준으로 유용한 호출만 필터링하여 모델 가중치에 도구 사용 능력을 자기지도 방식으로 내재화한다.*

다음은 Toolformer가 실제로 다양한 API를 자율적으로 호출하는 예시이다. QA, Calculator, MT, WikiSearch 등 각 상황에 적합한 도구를 선택하여 텍스트 생성에 자연스럽게 통합하는 모습을 보여준다.

![Toolformer의 다양한 API 호출 예시 — QA, Calculator, MT, WikiSearch](figures/fig_1.png)
*Figure 1: Toolformer 예측 예시 — 모델이 자율적으로 QA(질의응답), Calculator(계산기), MT(번역기), WikiSearch(위키피디아 검색) 등 다양한 API를 호출하여 텍스트 완성에 필요한 정보를 획득한다. (Source: Schick et al., 2023)*

## 아키텍처 상세

Toolformer의 학습 파이프라인은 세 단계로 구성된다.

### 1단계: API 호출 후보 샘플링

기존 텍스트 데이터(CCNet 코퍼스)에서 각 위치에 잠재적 API 호출을 삽입할 수 있는지를 GPT-3(few-shot 프롬프팅)으로 판단한다. 각 API에 대해 몇 개의 예시를 제공하면, GPT-3가 적절한 위치와 인수를 자동으로 제안한다.

```
원본: "The 2022 World Cup was held in Qatar."

후보 삽입:
  위치 1: "The 2022 World Cup [WikiSearch("2022 FIFA
          World Cup") → ...] was held in Qatar."
  위치 2: "The 2022 World Cup was held in
          [QA("Where was 2022 World Cup?") → Qatar]
          Qatar."
```

지원하는 API 유형은 다음과 같다.

| API | 기능 | 호출 형식 | 사용 예시 |
|-----|------|---------|----------|
| Calculator | 수학 연산 | `[Calculator(12*5) → 60]` | 수치 계산이 필요한 문맥 |
| QA | 질의응답 | `[QA("capital?") → Paris]` | 사실 확인이 필요한 문맥 |
| WikiSearch | 위키피디아 검색 | `[WikiSearch("topic") → ...]` | 배경 지식이 필요한 문맥 |
| MT | 기계 번역 | `[MT("text", "en") → ...]` | 다국어 처리 문맥 |
| Calendar | 날짜/시간 | `[Calendar() → 2023-02-09]` | 시간 관련 질의 |

### 2단계: 유용성 기반 필터링

아래 그림은 Toolformer의 핵심 학습 파이프라인을 QA 도구를 예시로 설명한다. 입력 텍스트에서 API 호출 후보를 샘플링하고, 실행 결과를 기반으로 유용성을 필터링한 후, 선택된 API 호출을 원본 텍스트에 삽입하는 전체 과정을 보여준다.

![Toolformer 학습 파이프라인 — API 호출 후보 샘플링, 실행, 필터링 과정](figures/fig_2.png)
*Figure 2: Toolformer 학습 파이프라인 — 입력 텍스트에서 API 호출 위치와 후보를 샘플링한 후, API를 실행하고 perplexity 감소 기준으로 유용한 호출만 필터링하여 최종 학습 데이터를 생성한다. (Source: Schick et al., 2023)*

이 단계가 Toolformer의 핵심 기여다. 각 API 호출 후보에 대해, 해당 호출이 텍스트 예측을 실제로 개선하는지를 perplexity 기반으로 측정한다.

두 가지 loss를 비교한다:

$$L_+(x_i) = -\log P(x_{i+1:n} | x_{1:i}, [\text{API}(\text{input}) \rightarrow \text{output}])$$
$$L_-(x_i) = -\min\left(\log P(x_{i+1:n} | x_{1:i}), \; \log P(x_{i+1:n} | x_{1:i}, [\text{API}(\text{input}) \rightarrow \varepsilon])\right)$$

$L_+$는 API 호출 결과를 포함했을 때의 loss이고, $L_-$는 API 호출이 없거나 빈 결과인 경우의 loss다. 필터링 조건은:

$$L_-(x_i) - L_+(x_i) \geq \tau$$

즉, API 호출 결과를 알 때의 loss가 모를 때보다 임계값 $\tau$ 이상 낮으면, 해당 API 호출은 "유용한" 것으로 판정하여 학습 데이터에 포함한다. 이 필터링은 불필요한 API 호출(예: "The cat sat on the mat"에서의 WikiSearch)을 자연스럽게 제거한다.

### 3단계: 파인튜닝

API 호출 마커가 삽입된 데이터로 GPT-J 6.7B를 표준 언어 모델링 목적함수로 파인튜닝한다. 모델은 텍스트 생성 중 자연스럽게 `[API_CALL(...)]` 형태의 특수 토큰 시퀀스를 생성하는 법을 학습한다.

```
학습 데이터 예시:
"The population of Tokyo is [QA("population of
 Tokyo") → 13.96 million] approximately 14 million."

추론 시:
Input: "What is 317 times 52?"
Output: "317 times 52 is [Calculator(317 * 52)
        → 16484] 16,484."
         ↑ 모델이 자동으로 API 호출 토큰 생성
```

### 추론 시 실행 메커니즘

추론 시 모델이 API 호출 시작 토큰 `[`를 생성하면, 디코딩 엔진이 이를 가로채어 다음 과정을 수행한다:

1. API 이름과 인수를 파싱
2. 해당 API를 실제로 호출
3. 결과를 `→ result]` 형태로 컨텍스트에 삽입
4. 삽입된 결과를 포함하여 텍스트 생성 계속

이 과정은 모델의 토큰 생성과 외부 API 호출을 매끄럽게 인터리빙(interleaving)하여, 사용자에게는 도구 사용이 자연스러운 텍스트의 일부로 나타난다.

## 핵심 혁신

1. **자기지도 학습 데이터 생성**: 인간의 어노테이션 없이, 모델 자체가 "어디에 API 호출이 유용한가"를 판단하여 학습 데이터를 자동 생성한다. 이는 도구 사용 학습의 스케일러빌리티를 획기적으로 높인다.

2. **유용성 기반 필터링**: API 호출의 유용성을 perplexity 감소라는 객관적 기준으로 측정한다. "도움이 되는" 호출만 학습하므로, 불필요한 API 호출을 자연스럽게 억제한다. 이 메커니즘은 "언제 도구를 사용하지 말아야 하는가"도 암묵적으로 학습한다.

3. **도구 내재화(Tool Internalization)**: 런타임 프롬프트가 아닌 모델 가중치에 도구 사용 능력을 내재화함으로써, 추가 프롬프트 오버헤드 없이 자연스러운 도구 통합이 가능하다. 컨텍스트 윈도우를 도구 사용 지시에 낭비할 필요가 없다.

4. **소형 모델의 능력 확장**: 6.7B 모델이 도구를 활용하여 66B 모델을 능가하는 결과는, 도구 사용이 모델 스케일링의 대안이 될 수 있음을 시사한다. 이는 효율적 AI 배포에 중요한 함의를 갖는다.

다음 그래프는 모델 크기에 따른 API 호출의 효과를 보여준다. 소형 모델에서는 API 호출이 도움이 되지 않지만, 충분히 큰 모델에서는 API 호출을 통한 성능 향상이 두드러진다.

![모델 크기별 API 호출 유무에 따른 LAMA, Math, QA 벤치마크 성능 비교](figures/fig_4.png)
*Figure 3: 모델 크기와 도구 사용의 관계 — GPT-2(다양한 크기)와 GPT-J에서 API 호출 유무에 따른 LAMA, Math, QA 성능. 큰 모델일수록 API 호출의 효과가 커지며, API 호출 여부에 따른 성능 격차가 유지된다. (Source: Schick et al., 2023)*

## 벤치마크/성능

| 작업 | GPT-J 6.7B (기본) | Toolformer 6.7B | OPT 66B | GPT-3 175B |
|-----|-------------------|-----------------|---------|-----------|
| 수학 (ASDiv) | 22.1% | **40.3%** | 29.1% | 42.2% |
| QA (WebQS) | 6.8% | **11.2%** | 10.7% | 12.3% |
| 시간 질의 (TempQA) | 9.4% | **29.7%** | 14.0% | 22.4% |
| 번역 (MLQA) | 25.4% | **32.9%** | 28.7% | 25.3% |
| 언어 모델링 (WikiText) | 15.5 PPL | **14.8 PPL** | - | - |

6.7B Toolformer가 66B OPT를 모든 태스크에서 상회하며, 일부 태스크(시간 질의)에서는 175B GPT-3까지 능가한다. 특히 시간 질의에서 9.4% $\rightarrow$ 29.7%의 3배 이상 향상은 Calendar API의 효과를 극적으로 보여준다. 언어 모델링 자체의 perplexity도 개선되어, 도구 사용 학습이 모델의 기본 언어 능력을 손상시키지 않음을 확인했다.

다음은 QA 도구에 대한 API 호출 생성을 위해 사용되는 프롬프트 예시이다. 이 few-shot 프롬프트를 통해 GPT-3가 텍스트에서 적절한 위치에 API 호출을 삽입하는 법을 학습한다.

![QA 도구용 few-shot 프롬프트 예시 — API 호출 위치와 형식을 안내하는 프롬프트](figures/fig_3.png)
*Figure 4: QA API 호출 생성 프롬프트 — few-shot 예시를 통해 GPT-3에게 텍스트 내 적절한 위치에 QA API 호출을 삽입하는 방법을 안내한다. 입력-출력 쌍으로 호출 패턴을 학습시킨다. (Source: Schick et al., 2023)*

## 학습

GPT-J 6.7B를 기반으로 파인튜닝한다. 학습 데이터는 CCNet 코퍼스에서 자동 생성되며, API 호출 후보 샘플링에 GPT-3(few-shot)을 사용한다. 필터링 임계값 $\tau$는 실험적으로 결정하며, 일반적으로 $\tau = 1.0$ 전후가 적절하다. 학습은 표준 언어 모델링 목적함수(cross-entropy loss)를 사용하며, API 호출 마커를 포함한 텍스트를 일반 텍스트처럼 학습한다. 전체 파이프라인은 (1) GPT-3로 후보 샘플링 $\rightarrow$ (2) API 실행 및 필터링 $\rightarrow$ (3) GPT-J 파인튜닝의 3단계로 구성되며, 한 번 파이프라인을 구축하면 다양한 API에 반복 적용할 수 있다.

## 관련 모델

Toolformer는 ReAct의 프롬프트 기반 도구 사용에서 영감을 받되, 도구 사용 능력을 가중치에 내재화하는 근본적으로 다른 접근을 취한다. 이후 GPT-4의 Function Calling, Gemini의 도구 사용, Claude의 tool use 등 주요 상용 모델의 도구 통합 방식에 개념적 영향을 미쳤다. 특히 "모델이 스스로 언제 도구를 사용할지 판단한다"는 아이디어는 현대 LLM의 도구 사용 패러다임의 근간이 되었다.

## 참고 자료

- Schick et al., "Toolformer: Language Models Can Teach Themselves to Use Tools", NeurIPS 2023, arXiv:2302.04761

## 관련 문서

- [[react|ReAct]] — 영감
