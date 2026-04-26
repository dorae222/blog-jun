<!-- infographic-hero -->
![ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems 핵심 요약](figures/infographic.svg)

*Figure: ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems 한 장 요약 인포그래픽*

## 개요

검색 증강 생성(Retrieval-Augmented Generation, [[RAG]]) 시스템은 외부 지식 베이스에서 관련 문서를 검색하여 대규모 언어 모델([[LLM]])의 응답 품질을 높이는 기법으로, 산업계와 학계에서 가장 활발하게 활용되는 [[LLM]] 활용 패러다임이다. 그러나 RAG 시스템의 성능을 정확하고 신뢰성 있게 평가하는 것은 그 자체로 어려운 문제다. RAG 파이프라인은 검색(retrieval)과 생성(generation)이라는 서로 다른 두 단계로 구성되며, 각 단계가 최종 응답 품질에 독립적으로 기여하기 때문에 단일 지표만으로는 시스템의 강점과 약점을 파악하기 어렵다.

ARES(Automated RAG Evaluation System)는 이러한 평가의 어려움을 해결하기 위해 제안된 자동화 평가 프레임워크로, **NAACL 2024**에 발표되었다. ARES의 핵심 접근 방식은 세 가지 단계로 구성된다. 첫째, 대상 도메인의 코퍼스를 기반으로 합성 학습 데이터를 자동 생성한다. 둘째, 이 합성 데이터를 활용하여 경량 LLM 기반 판별자(judge)를 파인튜닝한다. 셋째, 소수의 인간 레이블과 다수의 판별자 예측을 결합하는 예측 기반 추론(Prediction-Powered Inference, PPI)을 적용하여 통계적으로 유효한 신뢰구간을 추정한다.

본 논문의 핵심 기여는 다음과 같다:

1. RAG 시스템의 품질을 **Context Relevance, Answer Faithfulness, Answer Relevance** 세 가지 독립적인 축으로 분리하여 측정하는 체계적 평가 프레임워크를 제안한다.
2. 합성 학습 데이터 생성과 경량 모델 파인튜닝을 결합하여, GPT-3.5 직접 호출 대비 비용을 크게 절감하면서도 동등하거나 우수한 평가 정확도를 달성한다.
3. PPI를 RAG 평가에 최초로 적용하여, 약 150개의 인간 레이블만으로도 통계적으로 신뢰 가능한 평가 결과를 도출할 수 있음을 보인다.
4. KILT, SuperGLUE 벤치마크의 총 6개 데이터셋에서 RAGAS 대비 Context Relevance 정확도를 평균 59.9%p, Answer Relevance 정확도를 평균 14.4%p 향상시킨다.

## 배경 및 문제

### RAG 시스템 평가의 현재 상황

RAG 시스템은 지식 집약적(knowledge-intensive) 태스크에서 LLM의 성능을 향상시키는 대표적인 방법론이다. 사용자의 질문이 주어지면, 검색 모듈이 외부 코퍼스에서 관련 문서(passage)를 검색하고, 생성 모듈이 검색된 문서를 참조하여 응답을 생성한다. 이 과정에서 검색의 정확도, 생성의 충실성, 응답의 적절성 등 여러 차원의 품질이 복합적으로 작용한다.

기존의 RAG 평가 방식에는 크게 세 가지 접근이 존재한다.

**인간 평가(Human Evaluation)**: 전문 평가자가 RAG 시스템의 출력을 직접 검토하는 방식으로, 가장 정확한 평가를 제공한다. 그러나 수천 개의 응답을 일일이 검토하는 것은 비용과 시간 측면에서 비현실적이며, 평가자 간 일치도(inter-annotator agreement) 문제도 존재한다. 대규모 RAG 시스템의 반복적 평가에는 적합하지 않다.

**자동 지표 기반 평가(Automatic Metrics)**: BLEU, ROUGE, BERTScore 등 참조 답변과의 유사도를 측정하는 자동 지표가 널리 사용된다. 그러나 이러한 지표들은 표면적 유사성에 의존하므로, 의미적으로 올바르지만 표현이 다른 응답을 저평가하거나, 유창하지만 사실적으로 부정확한 응답을 과대평가하는 문제가 있다. 특히 RAG 시스템에서 중요한 충실성(faithfulness) 평가에는 근본적으로 부적합하다.

**LLM 직접 호출 평가(LLM-as-Judge)**: GPT-4 등 강력한 LLM을 프롬프팅하여 응답 품질을 직접 판단하게 하는 방식이다. 비교적 높은 정확도를 보이지만, 다수의 편향이 보고되었다. 긴 응답을 선호하는 경향(verbosity bias), 특정 위치의 응답을 선호하는 경향(position bias), 자기 생성 응답을 높게 평가하는 경향(self-enhancement bias) 등이 대표적이다. API 호출 비용이 높고, 모델 버전 변경에 따른 재현성 문제도 있다. RAGAS와 같은 프레임워크가 이 범주에 해당하며, 도메인 적응 없이 수작업 프롬프트에 의존하는 한계가 있다.

### ARES가 해결하려는 핵심 문제

ARES는 위 세 가지 접근 방식의 한계를 극복하기 위해, 다음과 같은 핵심 질문에 답한다:

> "소수의 인간 레이블만으로 대규모 RAG 시스템의 성능을 통계적으로 신뢰할 수 있게 평가할 수 있는가?"

이 질문에 긍정적으로 답하기 위해, ARES는 합성 데이터 기반 판별자 학습과 PPI라는 통계적 프레임워크를 결합한다. 인간 평가의 정확성, 자동 평가의 확장성, 그리고 통계적 추론의 신뢰성을 동시에 달성하는 것이 목표다.

## 핵심 아이디어

ARES의 핵심 아이디어는 "자동화된 RAG 평가"를 세 가지 기술적 혁신을 통해 구현하는 것이다.

### 3축 평가 체계

![ARES 프레임워크의 3축 평가 체계와 파이프라인 구조 개요](figures/architecture.png)
*ARES 프레임워크의 전체 아키텍처. 상단은 Context Relevance, Answer Faithfulness, Answer Relevance 세 가지 평가 축과 각각의 판단 기준을 보여주며, 하단은 LLM Judge(합성 레이블 생성) -> Classifier(경량 분류기 학습) -> PPI(신뢰구간 추론)로 이어지는 3단계 파이프라인 구조를 나타낸다.*

RAG 시스템의 품질을 단일 점수로 표현하면 시스템의 병목 지점을 파악하기 어렵다. ARES는 RAG 파이프라인의 각 구성 요소를 독립적으로 평가하기 위해 세 가지 축을 정의한다.

- **Context Relevance (CR)**: 검색된 문서가 질문에 관련이 있는가? 이 지표는 검색 모듈의 성능을 직접 반영한다.
- **Answer Faithfulness (AF)**: 생성된 응답이 검색된 문서에 충실한가? [[Hallucination]] 탐지와 직결되는 지표다.
- **Answer Relevance (AR)**: 생성된 응답이 사용자의 질문에 적절히 답하는가? 최종 사용자 경험을 반영하는 지표다.

이 세 축의 조합으로 RAG 시스템의 문제를 정확히 진단할 수 있다. 예를 들어, CR이 높지만 AF가 낮다면 검색은 잘 되지만 생성 모델이 환각(hallucination)을 일으키고 있다는 의미이며, CR이 낮다면 검색 모듈의 개선이 우선적으로 필요하다는 신호다.

### 합성 데이터를 활용한 판별자 사전학습

인간 레이블 없이도 판별자를 초기 학습시키기 위해, LLM을 활용한 합성 데이터 생성 파이프라인을 구축한다. 대상 도메인의 문서 코퍼스에서 패시지를 추출한 후, **FLAN-T5 XXL**을 이용하여 질문-컨텍스트-응답 트리플을 자동 생성한다. 생성된 합성 질문은 FAISS IndexFlatL2 인덱스와 OpenAI text-embedding-ada-002 임베딩을 활용한 필터링 과정을 거친다. 양성(positive) 예시뿐만 아니라 음성(negative) 예시도 약한 음성(weak negative)과 강한 음성(strong negative) 두 가지 전략으로 생성하여 판별자의 변별력을 강화한다.

### PPI를 통한 통계적 신뢰구간 추정

파인튜닝된 판별자의 예측만으로는 체계적 편향이 존재할 수 있다. PPI는 소수의 인간 레이블을 "보정 데이터"로 활용하여 판별자의 예측 오차를 학습하는 **보정 함수(rectifier function)**를 구성하고, 동시에 통계적으로 유효한 신뢰구간을 제공한다. 약 150개의 인간 레이블과 대규모 비표기 데이터를 결합하여 95% 신뢰수준의 평가 결과를 도출한다.

## 방법론

### 전체 파이프라인 개요

![ARES의 3단계 자동화 RAG 평가 파이프라인 흐름도](figures/fig_1.png)
*ARES의 3단계 평가 파이프라인. Step 1에서 도메인 내 패시지로부터 합성 질문-응답 쌍을 생성하고, Step 2에서 합성 데이터와 대조 학습 프레임워크로 LLM 판별자를 파인튜닝하며, Step 3에서 파인튜닝된 판별자와 PPI 및 인간 레이블을 결합하여 RAG 시스템의 순위를 신뢰구간과 함께 산출한다.*

ARES의 전체 파이프라인은 세 가지 입력을 필요로 한다: (1) 도메인 내 패시지 집합, (2) 150개 이상의 인간 어노테이션으로 구성된 검증 세트, (3) 합성 데이터 생성용 5개의 few-shot 예시 쌍이다. 이 입력들을 기반으로 합성 데이터 생성, 판별자 파인튜닝, PPI 기반 평가라는 세 단계를 순차적으로 수행한다.

### 평가 지표의 수학적 정의

각 평가 지표는 이진 분류 함수로 정의된다. 질문 $q$, 검색된 문서(컨텍스트) $d$, 생성된 응답 $a$에 대해 다음과 같이 정의한다.

**Context Relevance (문맥 관련성)**

$$\text{CR}(q, d) = \mathbb{1}[d \text{ is relevant to answering } q]$$

검색된 문서가 사용자 질문에 답하는 데 유용한 정보를 포함하고 있는지를 판단한다. 이 지표가 낮으면 검색 모듈(retriever)의 개선이 필요하다.

**Answer Faithfulness (응답 충실성)**

$$\text{AF}(a, d) = \mathbb{1}[\text{all claims in } a \text{ are supported by } d]$$

생성된 응답의 모든 주장(claim)이 제공된 컨텍스트 문서에 의해 뒷받침되는지를 판단한다. 모델이 컨텍스트에 없는 내용을 지어내거나, 컨텍스트와 모순되는 응답을 생성하면 이 점수가 0이 된다. [[Hallucination]] 문제와 직결되는 가장 중요한 평가 축 중 하나다.

**Answer Relevance (응답 관련성)**

$$\text{AR}(a, q) = \mathbb{1}[a \text{ correctly answers } q]$$

생성된 응답이 사용자의 원래 질문에 대해 올바르고 적절한 답변을 제공하는지를 판단한다.

### 1단계: 합성 데이터 생성

대상 도메인의 문서 코퍼스 $\mathcal{D} = \{d_1, d_2, \ldots, d_M\}$에서 패시지를 샘플링한다. 각 패시지 $d_i$에 대해 **FLAN-T5 XXL**을 few-shot 프롬프팅하여 합성 질문 $q_i$를 생성한다. 프롬프트에는 5개의 도메인 내 (문서, 질문) 예시를 포함하여, 생성되는 질문이 해당 도메인의 스타일과 난이도에 맞도록 유도한다.

**질문 생성 프롬프트 구조:**
```
Example #1: Document: [passage_1] → Query: [query_1]
Example #2: Document: [passage_2] → Query: [query_2]
Example #3: Document: [passage_3] → Query: [query_3]
Example #4: Document: [target_passage] → Query: [모델이 생성]
```

**답변 생성 프롬프트 구조:**
```
Example #1: Query: [q_1] Document: [d_1] → Answer: [a_1]
Example #2: Query: [q_2] Document: [d_2] → Answer: [a_2]
Example #3: Query: [q_3] Document: [d_3] → Answer: [a_3]
Example #4: Query: [synthetic_q] Document: [passage] → Answer: [모델이 생성]
```

**합성 질문 품질 필터링**: 생성된 질문의 품질을 보장하기 위해, 각 합성 질문에 대해 원본 패시지가 검색 상위에 복원되는지를 검증한다. OpenAI의 text-embedding-ada-002 임베딩으로 FAISS IndexFlatL2 인덱스를 구축하고, 합성 질문으로 검색했을 때 원본 패시지가 상위 $k$개에 포함되지 않으면 해당 질문을 폐기한다. 이 필터링 과정은 합성 질문이 원본 패시지의 핵심 내용을 적절히 반영하는지를 간접적으로 검증하는 역할을 한다.

**양성/음성 예시 구성 전략:**

양성 예시:
- CR 양성: $(q_i, d_i)$ 쌍에서 $d_i$가 $q_i$에 관련 있는 경우
- AF 양성: 컨텍스트에 기반한 정확한 응답 $a_i$를 LLM이 생성
- AR 양성: 질문에 적절히 답하는 응답 $a_i$

음성 예시 (두 가지 난이도):
- **약한 음성(Weak Negatives)**: 무관한 패시지 $d_j$ ($j \neq i$)를 랜덤 샘플링하여 $(q_i, d_j)$ 구성, 또는 다른 패시지의 응답을 가져와 대체
- **강한 음성(Strong Negatives)**: BM25 검색으로 동일 문서 내의 유사하지만 답변에 도움되지 않는 패시지를 추출하거나, LLM으로 컨텍스트와 모순되는 응답을 의도적으로 생성

강한 음성 예시의 포함은 판별자의 변별력 향상에 핵심적이다. 단순히 무관한 패시지만 음성으로 사용하면, 판별자가 주제 유사성만으로 판단하게 되어 실제 RAG 시스템에서 발생하는 미묘한 오류를 탐지하지 못한다. 예를 들어, 질문과 같은 주제를 다루지만 실제로 답을 포함하지 않는 패시지를 "관련 있음"으로 잘못 분류하는 문제가 발생할 수 있다.

### 2단계: LLM 판별자 파인튜닝

**DeBERTa-v3-Large**(약 400M 파라미터) 인코더 모델에 이진 분류 헤드를 추가하여 각 지표에 대한 판별자를 개별적으로 학습한다. 입력은 질문, 컨텍스트, 응답의 연결(concatenation)이며, 출력은 해당 지표에 대한 이진 확률이다.

학습 목적 함수는 대조 학습(contrastive learning) 프레임워크에 기반한 이진 교차 엔트로피(Binary Cross-Entropy) 손실이다:

$$\mathcal{L}_{\text{BCE}} = -\frac{1}{N}\sum_{i=1}^{N}\left[y_i \log \hat{y}_i + (1-y_i)\log(1-\hat{y}_i)\right]$$

여기서 $y_i \in \{0, 1\}$는 합성 레이블, $\hat{y}_i$는 모델의 예측 확률이다. 세 가지 지표(CR, AF, AR)에 대해 각각 독립적인 판별자를 학습하므로 총 **세 개의 분류기**가 생성된다. 학습 시 인간 검증 세트(150개 이상)를 기반으로 early stopping을 적용하여, 3 에포크 동안 검증 손실이 개선되지 않으면 학습을 종료한다.

경량 모델을 사용하는 이유는 두 가지다. 첫째, GPT-3.5/4 대비 추론 비용이 수십~수백 배 저렴하다. 둘째, 도메인 특화 파인튜닝을 통해 범용 LLM보다 해당 도메인에서 더 높은 판별 정확도를 달성할 수 있다. 이는 "작지만 특화된 모델이 크지만 범용적인 모델을 이길 수 있다"는 최근 연구 트렌드와 맥을 같이 한다. 실험 결과, 파인튜닝된 DeBERTa 판별자는 few-shot GPT-3.5보다 Kendall's tau 기준 평균 0.06 더 높은 순위 상관관계를 보였다.

### 3단계: PPI 기반 신뢰구간 추정

PPI(Prediction-Powered Inference)는 Angelopoulos et al. (2023)이 제안한 통계적 프레임워크로, 기계 학습 모델의 예측과 소수의 인간 레이블을 결합하여 통계적으로 유효한 추론을 수행한다. ARES는 이 프레임워크를 RAG 평가에 최초로 적용한다.

비표기 데이터셋 $\mathcal{U} = \{x_1, \ldots, x_N\}$에 대한 판별자 예측 $\{f(x_1), \ldots, f(x_N)\}$과, 소규모 표기 데이터셋 $\mathcal{L} = \{(x_1', y_1'), \ldots, (x_n', y_n')\}$이 주어졌을 때, PPI는 다음과 같이 동작한다:

**1) 보정 함수(Rectifier Function) 학습**: 표기 데이터에서 판별자의 예측 오차 패턴을 학습한다. 이를 통해 판별자가 체계적으로 과대/과소평가하는 방향과 크기를 파악한다.

**2) PPI 추정량 계산**:

$$\hat{\mu}^{\text{PPI}} = \underbrace{\frac{1}{N}\sum_{i=1}^{N}f(x_i)}_{\text{모델 예측 평균}} + \underbrace{\frac{1}{n}\sum_{j=1}^{n}\left(y_j' - f(x_j')\right)}_{\text{편향 보정 항}}$$

여기서 첫 번째 항은 전체 비표기 데이터에 대한 모델 예측의 평균이고, 두 번째 항은 표기 데이터에서 관찰된 모델의 체계적 편향을 보정한다. 직관적으로, 모델이 체계적으로 과대평가하고 있다면 두 번째 항이 음수가 되어 보정 역할을 한다.

**3) 분산 추정 및 신뢰구간 구성**:

$$\hat{\sigma}^{2}_{\text{PPI}} = \frac{\hat{\sigma}^{2}_{f}}{N} + \frac{\hat{\sigma}^{2}_{\Delta}}{n}$$

여기서 $\hat{\sigma}^{2}_{f}$는 모델 예측 $f(x_i)$의 분산, $\hat{\sigma}^{2}_{\Delta}$는 편향 보정 항 $y_j' - f(x_j')$의 분산이다. 이를 통해 $1 - \alpha$ 신뢰구간을 다음과 같이 구성한다:

$$\text{CI}_{1-\alpha} = \left[\hat{\mu}^{\text{PPI}} - z_{1-\alpha/2} \cdot \hat{\sigma}_{\text{PPI}},\ \hat{\mu}^{\text{PPI}} + z_{1-\alpha/2} \cdot \hat{\sigma}_{\text{PPI}}\right]$$

여기서 $z_{1-\alpha/2}$는 표준 정규 분포의 $1-\alpha/2$ 분위수이다 (95% 신뢰구간의 경우 $z_{0.975} \approx 1.96$).

PPI의 핵심적 이점은 $n$이 상대적으로 작더라도 (예: 150개), $N$이 충분히 크면 좁은 신뢰구간을 얻을 수 있다는 점이다. 이는 두 분산 항의 구조에서 기인한다. $\hat{\sigma}^{2}_{f}/N$ 항은 대규모 비표기 데이터 덕분에 매우 작아지고, 전체 분산은 주로 $\hat{\sigma}^{2}_{\Delta}/n$ 항에 의해 결정된다. 판별자의 품질이 높아 $\hat{\sigma}^{2}_{\Delta}$가 작으면, 소수의 $n$으로도 충분히 좁은 신뢰구간을 얻을 수 있다.

### ARES 전체 파이프라인 요약

```
[입력]
  도메인 코퍼스 + 5개 few-shot 예시 + 150개 이상 인간 레이블
      |
      v
[1단계] 합성 데이터 생성
  - FLAN-T5 XXL로 (질문, 컨텍스트, 응답) 트리플 생성
  - FAISS 기반 질문 품질 필터링
  - 약한/강한 음성 예시 구성
      |
      v
[2단계] 판별자 파인튜닝
  - DeBERTa-v3-Large 기반 이진 분류기
  - CR, AF, AR 각각 독립 학습
  - Early stopping (검증 세트 기반)
      |
      v
[3단계] RAG 출력 스코어링 + PPI
  - 파인튜닝된 판별자로 대규모 평가
  - PPI 보정 함수로 편향 교정
  - 95% 신뢰구간 + 순위 중앙값 제공
      |
      v
[출력]
  CR / AF / AR 점수 + 신뢰구간 + 시스템 순위
```

## 실험 결과

### 실험 설정

ARES의 평가 성능을 검증하기 위해 다양한 벤치마크 데이터셋과 RAG 시스템 구성을 사용하였다.

**데이터셋**: KILT 벤치마크(Natural Questions, HotpotQA, WoW, FEVER)와 SuperGLUE 기반 데이터셋(MultiRC, ReCoRD)을 포함한 총 **6개 도메인**에서 실험을 수행한다. 이들 데이터셋은 단답형 QA부터 대화형 응답, 사실 검증까지 다양한 유형의 태스크를 포함하여, ARES의 범용성을 검증하기에 적합하다.

**RAG 시스템 구성**: 다양한 검색-생성 조합으로 모의(mock) RAG 시스템을 구성하여, ARES가 이들의 상대적 성능 순위를 얼마나 정확히 예측하는지를 평가한다. 검색 모듈은 BM25, Contriever 등을 사용하고, 생성 모듈은 FLAN-T5, GPT-3.5 등을 활용하여 다양한 성능 수준의 RAG 시스템을 구성한다.

**비교 기준선**: RAGAS(휴리스틱 프롬프팅 기반), few-shot GPT-3.5 judge(PPI 보강 포함)를 주요 비교 대상으로 사용한다.

### 순위 예측 정확도 비교 (Kendall's Tau)

ARES의 핵심 평가 지표는 **Kendall's tau** 순위 상관관계와 **정확도(accuracy)**다. Kendall's tau는 평가 프레임워크가 예측한 RAG 시스템 순위가 실제 인간 평가 순위와 얼마나 일치하는지를 측정하며, -1(완전 역순)부터 1(완전 일치)까지의 범위를 갖는다.

| 평가 방법 | CR Kendall $\tau$ | AR Kendall $\tau$ | CR 정확도 (%) | AR 정확도 (%) |
|---|---|---|---|---|
| RAGAS | 0.72--0.94 | 0.44--0.94 | 15.0--36.4 | 69.2--77.8 |
| GPT-3.5 (few-shot) | 0.67--0.94 | 0.78--0.94 | 60.4--84.3 | 59.6--85.2 |
| **ARES (DeBERTa)** | **0.83--1.0** | **0.78--1.0** | **79.3--92.3** | **78.5--97.2** |

ARES의 핵심 실험 결과를 정리하면:

- **Context Relevance**: ARES는 RAGAS 대비 Kendall's tau 평균 0.065 향상, 정확도 평균 **59.9%p** 향상을 달성한다. RAGAS의 Context Relevance 정확도가 15~36%에 불과한 반면, ARES는 79~92%를 기록하여 압도적인 차이를 보인다. RAGAS가 CR 평가에서 크게 실패하는 이유는 도메인 적응 없는 범용 프롬프트만으로는 "관련성"의 기준이 도메인마다 상이한 문제를 포착하지 못하기 때문이다.
- **Answer Relevance**: ARES는 RAGAS 대비 Kendall's tau 평균 0.132 향상, 정확도 평균 **14.4%p** 향상을 달성한다. AR에서의 차이가 CR보다 작은 것은, 응답의 적절성 판단이 문맥 관련성보다 상대적으로 도메인 독립적이기 때문으로 해석된다.
- **GPT-3.5 대비**: 파인튜닝된 DeBERTa 판별자가 few-shot GPT-3.5보다 Kendall's tau 기준 평균 0.06 더 높은 순위 상관관계를 보이며, 추론 비용은 수십 배 저렴하다.

### PPI 어노테이션 민감도 분석

인간 레이블 수에 따른 PPI의 순위 예측 성능 변화를 분석한다. 이 실험은 실무 적용 시 필요한 어노테이션 비용을 가늠하는 데 핵심적이다.

| 인간 레이블 수 ($n$) | Kendall's $\tau$ 범위 | 95% CI 폭 (pp) |
|---|---|---|
| 25 | 0.44--0.89 | -- |
| 50 | 0.44--0.94 | -- |
| 100 | 0.44--1.0 | -- |
| **150** | **0.72--1.0** | **6.5--11.9** |
| 200 | 0.83--1.0 | -- |
| 300 | 0.83--1.0 | -- |
| 400 | 0.89--1.0 | -- |

이 결과에서 핵심적인 관찰은 다음과 같다:

1. **최소 150개의 인간 레이블**이 안정적인 성능을 위해 필요하다. 100개 이하에서는 Kendall's tau 하한이 0.44까지 떨어질 수 있어 불안정하다. 150개를 기점으로 하한이 0.72로 급격히 상승하는데, 이는 PPI의 편향 보정 항 $\hat{\sigma}^{2}_{\Delta}/n$의 분산이 충분히 줄어드는 임계점에 해당한다.
2. 150개에서 300개로 늘리면 하한이 0.72에서 0.83으로 안정화되지만, 추가적인 개선 폭은 점차 감소한다. 이는 수확 체감(diminishing returns)의 전형적 패턴이다.
3. 95% 신뢰구간의 폭은 6.5~11.9 percentage point 수준으로, RAG 시스템 간 유의미한 성능 차이를 판별하기에 충분한 정밀도를 제공한다.
4. 이는 전체 평가 세트(수천 개)를 인간이 평가하는 것 대비 **약 20배 이상의 비용 절감**을 의미한다.

### 교차 도메인 일반화 분석

ARES의 판별자가 학습 도메인과 다른 도메인에서도 유효하게 작동하는지를 검증한다. 이 실험은 ARES의 실용성을 판단하는 데 중요한데, 매번 새 도메인마다 합성 데이터를 생성하고 판별자를 재학습해야 한다면 활용 비용이 크게 증가하기 때문이다.

| 도메인 이동 유형 | Kendall's $\tau$ 범위 | 일반화 여부 |
|---|---|---|
| 질문 유형 변경 (동일 문서) | 0.78--1.0 | 성공 |
| 문서 유형 변경 (동일 질문) | 0.78--1.0 | 성공 |
| 질문 + 문서 동시 변경 | 0.78--1.0 | 성공 |
| 언어 변경 (XGLUE) | ~0.33 | **실패** |
| 텍스트 -> 코드 (CodeSearchNet) | ~0.28 | **실패** |
| 텍스트 -> 추출형 (T-Rex) | ~0.38 | **실패** |

파인튜닝된 판별자는 동일 모달리티 내의 도메인 이동에는 강건하게 대응하지만, **언어 변경, 텍스트->코드 전환, 추출형 태스크 전환**과 같은 근본적인 도메인 변화에서는 성능이 급격히 하락한다. 특히 텍스트->코드 전환에서 Kendall's tau가 0.28까지 떨어지는 것은 사실상 랜덤 수준에 가까운 성능이다. 이는 DeBERTa 판별자가 자연어 텍스트의 구문적/의미적 패턴에 강하게 의존하며, 코드와 같은 구조적으로 상이한 입력에 대해서는 학습된 표현이 전이되지 않음을 의미한다.

### GPT-4 레이블 대체 실험

인간 레이블 대신 GPT-4가 생성한 레이블을 PPI 보정에 사용할 수 있는지를 검증한 결과, Kendall's tau가 0.05~0.30 감소하는 것으로 나타났다. 500개의 GPT-4 레이블을 사용하면 150개의 인간 레이블보다 일부 개선되는 추세를 보이지만, 동일 수량의 인간 레이블을 대체하지는 못한다.

이 결과는 흥미로운 시사점을 제공한다. PPI 보정에서 인간 어노테이션의 역할은 단순한 레이블링이 아니라, 모델의 체계적 편향을 정확히 포착하는 "교정 기준"이다. GPT-4도 LLM인 이상 판별자와 유사한 편향 패턴을 공유할 수 있으며, 이 경우 편향 보정이 불완전해진다. 즉, 보정 데이터의 가치는 양(quantity)이 아니라 판별자와의 "독립성(independence)"에서 비롯된다.

## 의의 및 한계

### 학술적 의의

**평가 방법론의 패러다임 전환**: ARES는 RAG 평가에서 "정확하지만 비싼 인간 평가" 또는 "저렴하지만 편향된 자동 평가"라는 이분법을 넘어, 두 가지의 장점을 결합한 새로운 패러다임을 제시한다. PPI를 통해 소량의 인간 레이블이 대규모 자동 평가의 신뢰성을 보증하는 구조는, RAG 평가뿐만 아니라 NLG(자연어 생성) 평가 전반에 적용 가능한 방법론적 기여다.

**통계적 엄밀성의 도입**: 기존 LLM-as-Judge 방식은 단일 점수를 제공할 뿐, 그 점수의 신뢰도에 대한 정보를 제공하지 않는다. ARES는 95% 신뢰구간을 함께 보고함으로써 평가 결과의 불확실성을 정량화한다. 6.5~11.9pp 폭의 신뢰구간은 A/B 테스트나 시스템 비교에서 통계적으로 유의미한 차이를 판단하는 데 충분히 실용적이다.

**재현성과 비용 효율성**: GPT-4 API의 버전 변경이나 프롬프트 민감성으로 인한 재현성 문제를 파인튜닝된 로컬 모델로 해결한다. DeBERTa-v3-Large는 단일 GPU에서도 빠르게 추론할 수 있어, 대규모 평가의 비용을 GPT-3.5/4 대비 수십~수백 배 절감한다.

### 실무적 활용 가능성

ARES는 실무에서 다음과 같은 시나리오에 적용될 수 있다:

- **RAG 파이프라인 CI/CD**: RAG 시스템의 구성 요소(검색 모듈, 생성 모델, 프롬프트 등)를 변경할 때마다 ARES를 실행하여 성능 변화를 자동으로 모니터링한다. 신뢰구간이 제공되므로 "이 변경이 통계적으로 유의미한 개선인가?"라는 질문에 답할 수 있다.
- **도메인 특화 RAG 최적화**: 의료, 법률, 금융 등 특수 도메인에서 도메인 전문가가 소수의 레이블만 제공하면 해당 도메인에 최적화된 평가가 가능하다.
- **검색-생성 모듈 선택**: 다양한 검색 모듈과 생성 모델의 조합을 체계적으로 비교하여 최적 구성을 도출한다. 3축 평가를 통해 "검색은 우수하지만 생성이 부족한 조합"과 같은 세분화된 진단이 가능하다.

### 한계

**합성 데이터 품질 의존성**: 합성 데이터 생성에 사용된 FLAN-T5 XXL의 편향이 판별자에 전이될 수 있다. 특히 강한 음성 예시가 실제 RAG 시스템에서 발생하는 오류 패턴과 다를 경우, 판별자의 변별력이 저하된다. 의료 분야에서의 미묘한 사실 오류나, 법률 분야에서의 맥락 의존적 해석 차이 같은 도메인 특화 오류 패턴은 합성적으로 재현하기 어렵다.

**교차 도메인 일반화 실패**: 실험에서 명확히 드러난 것처럼, 언어 변경(Kendall's tau ~0.33), 텍스트->코드 전환(~0.28), 추출형 태스크(~0.38)에서 판별자 성능이 급격히 하락한다. 새로운 모달리티나 언어에 대해서는 합성 데이터와 판별자를 처음부터 다시 구축해야 하며, 이는 "자동화"라는 ARES의 핵심 가치를 다소 훼손한다.

**이진 분류의 한계**: 현재 프레임워크는 각 지표를 이진(관련/비관련, 충실/불충실)으로 판단한다. 그러나 실제로는 부분적 관련성이나 부분적 충실성과 같은 연속적 스펙트럼이 존재한다. 응답이 대부분 충실하지만 하나의 사소한 사실 오류를 포함하는 경우, 이를 완전히 "불충실"로 분류하는 것은 정보 손실을 초래한다. Likert 스케일 등 다단계 평가로의 확장이 향후 연구 방향이 될 수 있다.

**Answer Faithfulness 평가의 부재**: 저자들 스스로 인정한 것처럼, KILT 및 SuperGLUE 데이터셋에서는 인간이 어노테이션한 hallucinated answer가 없어 Answer Faithfulness 평가를 수행하지 못했다. 이는 ARES가 가장 중요하게 내세우는 3축 평가 중 하나에 대한 실증적 검증이 불완전함을 의미하며, 논문의 가장 아쉬운 지점이다. AF 평가가 CR, AR과 동일한 수준의 성능을 보이는지는 HaluEval 등 hallucination 전용 벤치마크에서의 추가 검증이 필요하다.

**모의 RAG 시스템의 한계**: 실험에서 사용된 RAG 시스템은 실제 프로덕션 시스템이 아닌, 다양한 검색-생성 모듈을 인위적으로 조합한 모의 시스템이다. 프로덕션 RAG 시스템에서 발생하는 복잡한 오류 패턴(멀티홉 검색 실패, 긴 문서의 정보 누락, 실시간 지식 업데이트 불일치 등)에 대한 ARES의 대응력은 별도 검증이 필요하다.

**PPI의 i.i.d. 가정**: PPI는 표기 데이터와 비표기 데이터가 동일한 분포에서 추출되었다는 가정에 기반한다. 인간 레이블이 특정 유형의 질문(예: 쉬운 질문 위주)에 편향되어 있으면 신뢰구간의 커버리지가 보장되지 않을 수 있다. 실무에서는 계층화 샘플링(stratified sampling) 등의 보완이 필요하다.

## 관련 연구 비교

ARES 이후로도 RAG 평가 분야는 빠르게 발전하고 있다. [[RAGAS]], [[TruLens]], [[DeepEval]] 등의 프레임워크가 유사한 다축 평가를 제공하지만, ARES는 PPI를 통한 통계적 신뢰구간 제공이라는 차별점을 가진다.

| 프레임워크 | 평가 방식 | 통계적 보증 | 도메인 적응 | 비용 |
|---|---|---|---|---|
| RAGAS | 휴리스틱 프롬프팅 | 없음 | 없음 (수작업 프롬프트) | 높음 |
| TruLens | LLM 직접 호출 | 없음 | 제한적 | 높음 |
| ARES | 파인튜닝 판별자 + PPI | 95% CI 제공 | 합성 데이터 기반 | 낮음 |
| 인간 평가 | 전문가 검토 | 가능 (충분한 표본 시) | 자연스러움 | 매우 높음 |

ARES는 자동화된 평가의 저비용과 통계적 추론의 엄밀성을 동시에 달성한 프레임워크로서, 특히 PPI 기반 신뢰구간 추정이라는 방법론적 혁신이 후속 연구에 의미 있는 방향성을 제시한다. 다만 RAGAS가 2024~2025년 사이 커뮤니티에서 더 광범위하게 채택된 점은 주목할 만하다. RAGAS는 설치 즉시 사용 가능한 반면, ARES는 합성 데이터 생성과 판별자 파인튜닝이라는 초기 셋업 비용이 존재하기 때문이다. 이는 "더 나은 방법론"과 "더 실용적인 도구" 사이의 트레이드오프를 보여준다.

## 코드 예제

### ARES 라이브러리 기본 사용법

ARES는 Python 라이브러리로 제공되며, 몇 줄의 코드만으로 RAG 시스템을 평가할 수 있다.

```python
from ares import ARES

# ARES 평가 설정
ares_config = {
    # 평가 대상 RAG 시스템의 출력
    "rag_output_file": "rag_outputs.tsv",
    # 소수의 인간 레이블 (PPI 보정용, 최소 150개 권장)
    "human_label_file": "human_annotations.tsv",
    # 판별자 모델 경로
    "judge_model": "ares-judge-deberta-v3-large",
    # 평가할 지표 선택
    "metrics": ["context_relevance", "answer_faithfulness", "answer_relevance"],
    # 신뢰구간 수준
    "confidence_level": 0.95,
}

# ARES 인스턴스 생성 및 평가 실행
ares = ARES(config=ares_config)
results = ares.evaluate()

# 결과 출력: 각 지표별 점수 + 95% 신뢰구간
for metric, result in results.items():
    print(f"{metric}:")
    print(f"  Score: {result['score']:.4f}")
    print(f"  95% CI: [{result['ci_lower']:.4f}, {result['ci_upper']:.4f}]")
```

### PPI 신뢰구간 직접 계산

PPI의 핵심 로직을 NumPy로 직접 구현하면 다음과 같다.

```python
import numpy as np
from scipy import stats

def compute_ppi_confidence_interval(
    model_predictions: np.ndarray,   # f(x_i), 전체 비표기 데이터 예측
    labeled_predictions: np.ndarray, # f(x_j'), 표기 데이터에 대한 모델 예측
    human_labels: np.ndarray,        # y_j', 인간 레이블
    alpha: float = 0.05,             # 유의 수준
) -> dict:
    """
    Prediction-Powered Inference로 신뢰구간을 계산한다.

    PPI 추정량: mu_ppi = mean(f(x_i)) + mean(y_j' - f(x_j'))
    - 첫째 항: 대규모 비표기 데이터에 대한 모델 예측 평균
    - 둘째 항: 소규모 표기 데이터에서 관찰된 편향 보정
    """
    N = len(model_predictions)
    n = len(human_labels)

    # PPI 추정량 계산
    model_mean = np.mean(model_predictions)
    bias_correction = np.mean(human_labels - labeled_predictions)
    mu_ppi = model_mean + bias_correction

    # 분산 추정
    sigma_f_sq = np.var(model_predictions, ddof=1) / N
    delta = human_labels - labeled_predictions
    sigma_delta_sq = np.var(delta, ddof=1) / n
    sigma_ppi = np.sqrt(sigma_f_sq + sigma_delta_sq)

    # 신뢰구간 구성
    z = stats.norm.ppf(1 - alpha / 2)
    ci_lower = mu_ppi - z * sigma_ppi
    ci_upper = mu_ppi + z * sigma_ppi

    return {
        "score": mu_ppi,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "bias_correction": bias_correction,
        "ci_width": ci_upper - ci_lower,
    }

# 사용 예시: 150개 인간 레이블 + 5000개 모델 예측
np.random.seed(42)
model_preds = np.random.beta(8, 2, size=5000)  # 대규모 비표기 데이터 예측
human_preds = model_preds[:150]                  # 표기 데이터에 대한 모델 예측
human_labels = (np.random.rand(150) < 0.82).astype(float)  # 인간 레이블

result = compute_ppi_confidence_interval(
    model_predictions=model_preds,
    labeled_predictions=human_preds,
    human_labels=human_labels,
    alpha=0.05,
)

print(f"PPI Score: {result['score']:.4f}")
print(f"95% CI: [{result['ci_lower']:.4f}, {result['ci_upper']:.4f}]")
print(f"CI Width: {result['ci_width']:.4f}")
print(f"Bias Correction: {result['bias_correction']:.4f}")
```