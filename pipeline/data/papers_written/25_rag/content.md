## 개요

RAG(Retrieval-Augmented Generation)는 2020년 NeurIPS에서 Meta AI(당시 Facebook AI Research)의 Patrick Lewis, Ethan Perez, Aleksandra Piktus 등이 발표한 논문으로, **사전학습 언어 모델에 외부 문서 검색 기능을 결합**하는 범용 프레임워크를 제안한다. 기존 seq2seq 모델은 학습 시점에 파라미터 안에 지식을 고정적으로 저장하므로, 새로운 사실이나 롱테일 지식에 취약하다는 한계가 있었다. RAG는 이 문제를 비모수적(non-parametric) 메모리인 외부 문서 저장소와 결합함으로써 해결한다.

이 논문은 Semantic Scholar 기준 약 **10,000회 이상 인용**되었으며(995건의 고영향력 인용 포함), 현대 LLM 시대의 검색 증강 생성 패러다임을 확립한 기념비적 연구로 평가받는다. "RAG"라는 용어 자체가 이 논문에서 시작되어 현재는 AI 산업의 핵심 아키텍처 패턴이 되었다.

논문의 핵심 기여를 정리하면 다음과 같다:

1. 사전학습된 검색기(DPR)와 생성기(BART)를 하나의 확률적 모델로 통합하는 end-to-end 프레임워크 설계
2. 검색 문서를 잠재 변수로 취급하고 주변화하는 두 가지 변형(RAG-Sequence, RAG-Token) 제안
3. 오픈 도메인 QA, 자유 형식 생성, 팩트 검증 등 다양한 지식 집약적 태스크에서의 범용성 입증
4. 문서 저장소 교체만으로 지식을 업데이트할 수 있는 실용적 아키텍처 제시

## 배경 및 문제

### 파라미터 기억의 한계

사전학습 언어 모델(GPT, BERT, T5 등)은 대규모 텍스트 코퍼스를 학습하며 방대한 지식을 파라미터 안에 내재화한다. 하지만 이 **파라미터 기억(parametric memory)**은 다음과 같은 근본적인 문제를 지닌다:

1. **지식의 정적성**: 학습 이후 새로운 사실을 반영하려면 전체 모델을 재학습해야 한다. 2020년에 학습된 모델은 2021년의 사건을 알 수 없다. 이는 실시간 정보가 필요한 응용에서 치명적인 제약이 된다.
2. **불투명성**: 모델이 어떤 근거로 답변을 생성하는지 추적하기 어렵다. 내부 파라미터의 어떤 부분이 특정 사실을 인코딩하는지 알 수 없으므로, 답변의 신뢰성을 검증할 방법이 없다.
3. **롱테일 지식 취약**: 학습 데이터에 적게 등장하는 희귀한 사실에 대한 답변 정확도가 낮다. 이는 모델이 빈도 기반으로 지식을 저장하기 때문이며, Roberts et al.(2020)이 T5 모델로 보인 것처럼 모델 크기를 늘려도 롱테일 지식의 정확도 개선에는 한계가 있다.
4. **환각(hallucination)**: 정확한 사실 근거 없이 그럴듯한 내용을 생성하는 경향이 있다. 모델이 "모른다"고 답하지 못하고 자신감 있게 잘못된 정보를 생성한다. 이는 의료, 법률, 금융 등 사실 정확성이 중요한 도메인에서 심각한 위험 요인이 된다.
5. **확장성 문제**: 더 많은 지식을 저장하려면 모델 파라미터를 늘려야 하며, 이는 학습 비용과 추론 비용의 기하급수적 증가를 초래한다. GPT-3(175B)가 모든 세계 지식을 저장하기에는 여전히 부족하다.

### 기존 검색 기반 접근법

RAG 이전에도 검색과 NLP를 결합하려는 시도가 있었다:

- **DrQA** (Chen et al., 2017): TF-IDF 기반 문서 검색과 BERT 판독기를 조합한 오픈 도메인 QA 시스템. 그러나 희소 검색(sparse retrieval)의 한계로 의미적 유사도 포착이 어려웠다.
- **ORQA** (Lee et al., 2019): 역 클로즈(Inverse Cloze Task)로 검색기를 사전학습하여 밀집 검색의 가능성을 보였다. 하지만 검색기와 판독기의 공동 학습이 제한적이었다.
- **REALM** (Guu et al., 2020): 사전학습 단계에서 검색을 통합한 최초의 연구. 마스킹된 언어 모델링 목적 함수에서 검색된 문서를 조건으로 활용했다. 그러나 추출형 QA에만 적용 가능했다.
- **kNN-LM** (Khandelwal et al., 2020): 추론 시 학습 데이터의 가장 가까운 이웃을 참조하여 언어 모델의 예측을 보정하는 방법. 생성 과정에서 외부 지식을 활용하는 아이디어를 보였으나, 검색과 생성의 통합적 학습이 불가능했다.

이들의 공통적인 한계는 대부분 **추출형 QA(extractive QA)**에 특화되어 있었다는 점이다. 추출형 QA는 문서 내에서 답변 스팬(span)을 찾는 태스크이므로, 자유 형식 텍스트 생성이나 추론이 필요한 태스크에는 적용이 어려웠다.

RAG는 이러한 한계를 극복하기 위해 **파라미터 기억과 비모수적 외부 메모리를 결합**하는 범용 생성 프레임워크를 제안하며, 추출형 QA뿐 아니라 자유 형식 생성, 팩트 검증 등 다양한 태스크에 적용 가능하다는 점에서 패러다임의 전환을 이루었다.

## 핵심 아이디어

RAG의 핵심은 텍스트 생성(generation) 과정에서 외부 문서 검색 결과를 잠재 변수(latent variable)로 활용하는 것이다. 입력 질문 $x$에 대해 관련 문서 $z$를 검색한 뒤, 이를 컨텍스트로 사용하여 최종 답변 $y$를 생성한다. 이를 수식으로 표현하면:

$$p(y|x) = \sum_{z \in \text{top-k}(p(\cdot|x))} p_\eta(z|x) \cdot p_\theta(y|x, z)$$

여기서:
- $p_\eta(z|x)$: DPR(Dense Passage Retriever)이 질문 $x$에 대해 문서 $z$를 반환할 확률 (검색기)
- $p_\theta(y|x, z)$: BART 기반 생성 모델이 질문 $x$와 문서 $z$를 입력으로 답변 $y$를 생성할 확률 (생성기)
- top-k: 가장 관련성 높은 $k$개의 문서만 합산 (실험에서 $k=5$ 또는 $k=10$ 사용)

이 수식의 핵심은 **잠재 변수(latent variable)로서의 문서 $z$**이다. 문서 $z$는 모델이 직접 관찰하는 것이 아니라, 검색 확률에 의해 가중 합산된다. 이를 통해 여러 문서의 정보를 유연하게 조합할 수 있다. 이는 전통적인 잠재 변수 모델(VAE 등)과 유사한 구조이지만, 잠재 변수가 연속 벡터가 아닌 이산적인 문서라는 점이 다르다.

### RAG-Sequence vs RAG-Token

논문은 주변화(marginalization)를 수행하는 위치에 따라 두 가지 변형을 제안한다:

**RAG-Sequence**: 전체 답변 시퀀스에 동일한 문서를 사용한다. 하나의 문서가 전체 답변 생성을 안내하는 방식이다. 수식적으로, 문서에 대한 합산이 시퀀스 확률의 바깥에 위치한다:

$$p_{\text{RAG-Seq}}(y|x) \approx \sum_{z \in \text{top-k}} p_\eta(z|x) \prod_{i=1}^{N} p_\theta(y_i | x, z, y_{1:i-1})$$

즉, 각 문서 $z$에 대해 전체 시퀀스의 생성 확률 $\prod_{i} p_\theta(y_i|x,z,y_{1:i-1})$을 먼저 계산한 후, 검색 확률 $p_\eta(z|x)$로 가중 합산한다. 이는 "하나의 문서가 하나의 완전한 답변을 생성한다"는 직관에 부합한다.

**RAG-Token**: 각 토큰 생성 시마다 다른 문서를 조건으로 활용할 수 있다. 문서에 대한 합산이 각 토큰 확률의 안쪽에 위치한다:

$$p_{\text{RAG-Token}}(y|x) \approx \prod_{i=1}^{N} \sum_{z \in \text{top-k}} p_\eta(z|x) \cdot p_\theta(y_i | x, z, y_{1:i-1})$$

각 토큰 $y_i$를 생성할 때마다 모든 top-k 문서에 대한 가중 합산을 수행하므로, 토큰별로 가장 적합한 문서의 영향을 받을 수 있다. 예를 들어, "아인슈타인의 출생지와 사망년도는?"이라는 질문에서 출생지 토큰은 전기 문서를, 사망년도 토큰은 연표 문서를 주로 참조할 수 있다.

![RAG-Token 모델의 토큰별 문서 사후 확률 히트맵](figures/fig_4.png)
*Figure 2: Hemingway 입력에 대한 Jeopardy 생성 시 RAG-Token의 토큰별 문서 사후 확률 p(z_i|x, y_i, y_{-i}). "A Farewell to Arms" 생성 시 문서 1의 확률이, "The Sun Also Rises" 생성 시 문서 2의 확률이 높아지며, 토큰 수준 주변화가 서로 다른 문서의 정보를 세밀하게 조합하는 과정을 보여준다.*

이 히트맵은 RAG-Token의 핵심 메커니즘을 직관적으로 보여준다. 동일한 답변 시퀀스 내에서도 생성되는 토큰에 따라 참조하는 문서가 동적으로 전환된다. "A Farewell to Arms"라는 작품명을 생성할 때는 해당 작품을 언급하는 문서 1이 지배적이고, "The Sun Also Rises"를 생성할 때는 문서 2로 전환된다. 이는 RAG-Sequence에서는 불가능한 방식의 정보 조합이다.

두 변형의 차이를 정리하면:

| 특성 | RAG-Sequence | RAG-Token |
|------|-------------|----------|
| 주변화 위치 | 시퀀스 수준 (외부) | 토큰 수준 (내부) |
| 문서 일관성 | 높음 (단일 문서 기반) | 낮음 (토큰별 혼합) |
| 정보 조합 | 제한적 | 세밀함 |
| 적합한 태스크 | 단일 사실 QA | 복합적 질문, 생성 |
| 디코딩 복잡도 | 높음 (비표준 beam search) | 낮음 (표준 beam search) |

RAG-Sequence는 답변의 일관성이 중요한 단답형 QA에서 유리하고, RAG-Token은 여러 출처의 정보를 조합해야 하는 긴 텍스트 생성에서 강점을 보인다. 실험 결과 두 변형 간 성능 차이는 태스크 특성에 따라 달라지며, 어느 한 쪽이 일관되게 우월하지는 않았다.

## 방법론

### 구성 요소

![RAG 전체 아키텍처: DPR 검색기와 BART 생성기의 end-to-end 연결 구조](figures/fig_1.png)
*Figure 1: RAG의 end-to-end 아키텍처. 질문 x를 Query Encoder가 벡터로 인코딩하여 MIPS(Maximum Inner Product Search)로 문서 인덱스에서 top-k 패시지를 검색하고, Generator(BART)가 질문과 검색 문서를 입력으로 답변 y를 생성한다. 검색 문서 z는 잠재 변수로 취급되어 주변화된다.*

RAG는 두 개의 주요 컴포넌트로 구성된다:

**1. Retriever: DPR (Dense Passage Retriever)**

DPR은 Karpukhin et al.(2020)이 제안한 밀집 검색 모델로, RAG의 검색 모듈로 사용된다:

- 질문 인코더 $\text{BERT}_q(\cdot)$와 문서 인코더 $\text{BERT}_d(\cdot)$를 각각 BERT-base 모델로 구성한다. 두 인코더는 파라미터를 공유하지 않는 독립적인 모델이다.
- 질문과 문서를 각각 고정 차원($d=768$)의 밀집 벡터로 인코딩한 뒤, 내적(dot product)으로 유사도를 계산한다:

$$p_\eta(z|x) \propto \exp\left(\text{BERT}_q(x)^\top \text{BERT}_d(z)\right)$$

- Wikipedia 전체(2018년 12월 덤프)를 100 단어 단위의 청크로 분할한 약 **2,100만 개의 패시지**를 사전에 인코딩하여 FAISS 인덱스에 저장한다.
- FAISS(Facebook AI Similarity Search)의 HNSW(Hierarchical Navigable Small World) 알고리즘을 사용하여 밀리초 단위의 빠른 최근접 이웃(approximate nearest neighbor) 탐색을 수행한다. 이를 통해 2,100만 개 패시지에서 top-k 문서를 실시간으로 검색할 수 있다.

DPR의 핵심 장점은 **의미적 유사도(semantic similarity)**를 포착한다는 것이다. 전통적인 BM25 같은 희소 검색(sparse retrieval)은 키워드 매칭에 의존하므로, "미국의 초대 대통령은 누구인가?"와 "George Washington was inaugurated as the first president"를 연결하기 어렵다. 반면 DPR은 질문과 문서의 의미적 관계를 벡터 공간에서 직접 포착할 수 있다.

**2. Generator: BART**

BART(Lewis et al., 2020)는 Facebook AI가 개발한 denoising autoencoder 기반 seq2seq 모델이다:

- BART-large 모델(약 400M 파라미터, 12 인코더 레이어 + 12 디코더 레이어)을 사용한다.
- 입력 구성: 질문 $x$와 검색된 문서 $z$를 `[SEP]` 토큰으로 연결하여 인코더에 전달한다. 여러 문서가 검색된 경우 각 문서를 독립적으로 질문과 연결한다:

$$\text{input}_k = [x_1, \ldots, x_m, \text{[SEP]}, z_{k,1}, \ldots, z_{k,n}]$$

- BART는 사전학습 과정에서 텍스트 손상(corruption) 후 원문을 복원하는 방식으로 학습되었으므로, 불완전한 정보로부터 완전한 텍스트를 생성하는 능력이 뛰어나다. 이는 검색된 문서의 단편적 정보를 자연스러운 답변으로 통합하는 데 적합하다.
- Retriever(질문 인코더)와 Generator(BART)를 함께 end-to-end로 파인튜닝하되, 문서 인코더 $\text{BERT}_d$는 고정한다.

### 학습 방식

문서 인코더 $\text{BERT}_d(\cdot)$를 포함한 FAISS 인덱스는 학습 중 고정하고, 질문 인코더 $\text{BERT}_q(\cdot)$와 BART 파라미터 $\theta$만 역전파(backpropagation)로 업데이트한다. 이 설계 결정에는 실용적 이유가 있다: 문서 인코더를 업데이트할 경우 2,100만 패시지의 임베딩을 매 학습 스텝마다 재계산해야 하므로 계산 비용이 비현실적이다.

학습 목적 함수는 음의 주변 로그 우도(negative marginal log-likelihood)이다:

$$\mathcal{L}(\theta, \eta) = -\sum_{(x_j, y_j) \in \mathcal{D}} \log p(y_j | x_j) = -\sum_{(x_j, y_j)} \log \sum_{z \in \text{top-k}} p_\eta(z|x_j) \cdot p_\theta(y_j|x_j, z)$$

이 손실 함수에서 $p(y_j|x_j)$를 계산할 때 상위 $k$개 문서에 대한 주변화(marginalization)가 이루어진다. 역전파 시 검색 확률 $p_\eta(z|x)$에 대한 그래디언트가 질문 인코더로 전달되어, 검색기가 답변 생성에 더 유용한 문서를 찾도록 학습된다. 이 과정은 EM(Expectation-Maximization) 알고리즘과 유사한 구조를 가진다: E-step에서 현재 검색기로 문서 분포를 추정하고, M-step에서 그 분포 하에 생성 확률을 최대화하는 방향으로 파라미터를 갱신하는 것이다.

학습 하이퍼파라미터는 다음과 같다:
- 학습률: $1 \times 10^{-5}$ (Adam optimizer)
- 배치 크기: 태스크에 따라 다름
- top-k 문서 수: $k = 5$ 또는 $k = 10$
- 문서 최대 길이: 100 단어 (약 200 BPE 토큰)

주목할 점은 문서 인코더를 고정하면서도 질문 인코더만 학습하는 것으로 검색 품질이 충분히 개선된다는 것이다. 이는 질문 벡터가 이동하면 MIPS에서 다른 문서가 top-k에 진입하게 되므로, 검색기의 효과적인 학습이 가능하다. 이 비대칭적 학습 전략은 이후 많은 검색 증강 모델에서 채택되었다.

### 디코딩 전략

RAG-Sequence의 디코딩은 일반적인 beam search와 구조적으로 다르다. 각 문서 $z$마다 beam search를 독립적으로 수행한 후, 모든 문서의 결과를 합산하여 최종 시퀀스를 선택한다:

$$\text{score}(y) = \sum_{z \in \text{top-k}} p_\eta(z|x) \cdot p_\theta(y|x,z)$$

이 과정에서 "Thorough Decoding"과 "Fast Decoding" 두 가지 변형을 제안한다:

- **Thorough Decoding**: 모든 문서에서 생성된 모든 후보 시퀀스에 대해, 각 문서별 확률을 다시 forward pass로 계산하여 정확한 주변 확률을 구한다. 후보 시퀀스 $y$가 문서 $z$에서 beam에 포함되지 않았더라도, $p_\theta(y|x,z)$를 명시적으로 계산한다.
- **Fast Decoding**: 각 문서에서 나온 후보만 해당 문서의 확률로 평가하고, 다른 문서에서의 확률은 0으로 근사한다. 추가 forward pass가 필요 없어 계산 비용이 크게 줄어든다.

실험 결과 두 방법의 성능 차이는 미미했다. 이는 하나의 문서에서 높은 확률로 생성된 시퀀스가 다른 문서에서는 대체로 낮은 확률을 가지기 때문이다.

RAG-Token은 토큰별로 문서 확률을 합산하므로 표준 beam search를 그대로 사용할 수 있다. 이는 구현의 단순성 측면에서 RAG-Token의 실용적 장점이다.

## 실험 결과

논문은 네 가지 유형의 지식 집약적 태스크에서 RAG를 평가한다.

### 오픈 도메인 QA 벤치마크 (Exact Match)

추출형 QA 모델(DPR + span extraction)과 비교하여, RAG는 생성 방식임에도 동등하거나 우수한 성능을 보였다:

| 모델 | NQ | TriviaQA | WebQ | CuratedTREC |
|------|-----|---------|------|-------------|
| DPR (Extractive) | 41.5 | 57.9 | 41.1 | 42.9 |
| REALM | 40.4 | - | 40.7 | 46.8 |
| T5-11B (Closed-book) | 36.6 | 60.5 | 37.4 | - |
| T5-11B+SSM | 36.6 | 60.5 | 44.7 | - |
| RAG-Token | **44.5** | 56.8 | 45.2 | **68.0** |
| RAG-Sequence | **44.5** | 55.8 | **45.5** | 65.7 |

주목할 점은 다음과 같다:

- **CuratedTREC**에서 기존 SOTA 대비 **25%p 이상의 향상**을 보였다. 이는 RAG의 생성 능력이 답변 형식의 다양성을 요구하는 데이터셋에서 특히 유리함을 보여준다. 추출형 모델은 문서 내 정확한 스팬만 반환할 수 있지만, RAG는 자연스러운 형태로 답변을 재구성할 수 있다.
- **NaturalQuestions**에서는 추출형 DPR과 동일한 44.5 EM을 달성하면서도, 11B 파라미터의 T5 대비 훨씬 적은 파라미터(약 600M)로 우수한 성능을 보였다. 이는 외부 검색이 파라미터 증가 없이 지식 범위를 확장하는 효과적 수단임을 입증한다.
- RAG-Token과 RAG-Sequence 간의 성능 차이는 태스크에 따라 다르며, 어느 한 변형이 일관되게 우월하지는 않았다.

### Abstractive QA (MS-MARCO NLG)

MS-MARCO NLG 태스크에서는 질문에 대해 자유 형식의 자연어 답변을 생성해야 한다:

| 모델 | Bleu-1 | Rouge-L |
|------|--------|--------|
| BART (baseline) | 33.0 | 26.2 |
| RAG-Token | 44.1 | **35.3** |
| RAG-Sequence | **44.2** | 35.1 |

RAG는 검색 없는 BART 대비 Bleu-1에서 **11점 이상**, Rouge-L에서 **9점 이상**의 향상을 보였다. 이는 외부 지식 검색이 생성 품질에 결정적 영향을 미친다는 증거이다. BART가 파라미터 안에 인코딩한 지식만으로는 부족한 부분을, 검색된 문서가 효과적으로 보완하고 있음을 의미한다.

### Jeopardy 질문 생성

RAG의 생성 능력을 평가하기 위해, 엔티티를 입력으로 받아 Jeopardy 스타일의 팩토이드 질문을 생성하는 태스크를 수행했다. 인간 평가(A/B 테스트) 결과:

| 비교 | RAG 선호 | 상대 모델 선호 | 동등 |
|------|---------|-------------|-----|
| RAG vs BART | **42.7%** | 30.5% | 26.8% |
| RAG vs S2S+CT2 | **52.1%** | 31.1% | 16.8% |

RAG가 생성한 질문이 BART 단독 생성 대비 **더 사실적이고 구체적**이라는 평가를 받았다. 특히 RAG-Token 변형이 Jeopardy 스타일 질문 생성에서 가장 높은 인간 선호도를 기록했다. 이는 Jeopardy 질문이 여러 사실을 조합하여 구성되므로, 토큰별로 다른 문서를 참조하는 RAG-Token의 특성이 유리하게 작용한 것이다.

### FEVER 팩트 검증

FEVER(Fact Extraction and VERification) 벤치마크에서 RAG는 3-class 분류(SUPPORTS / REFUTES / NOT ENOUGH INFO)를 수행했다. 자연어 생성 방식으로 라벨을 생성하되, 별도의 IR(Information Retrieval) 파이프라인 없이 RAG 내부의 DPR이 검색을 담당한다:

| 모델 | 정확도 |
|------|------|
| 기존 SOTA (별도 IR 사용) | 72.5 |
| RAG (자체 검색) | **72.5** |

RAG는 전용 IR 시스템(TF-IDF + 문서 선택기) 없이도 기존 SOTA와 동등한 성능을 달성했다. 이는 end-to-end 학습된 검색기가 태스크에 특화된 전통적 IR 시스템을 대체할 수 있음을 시사한다. 특히, FEVER의 기존 SOTA 시스템은 수작업으로 설계된 다단계 IR 파이프라인(문서 검색 + 문장 선택 + 라벨 분류)을 사용하는 반면, RAG는 단일 모델로 검색부터 분류까지 수행한다.

### 검색 문서 수(k)에 따른 영향

![검색 문서 수(k) 변화에 따른 성능 추이 그래프](figures/fig_7.png)
*Figure 3: top-k 문서 수에 따른 성능 분석. 왼쪽: NaturalQuestions EM 스코어, 가운데: NQ 검색 재현율, 오른쪽: MS-MARCO Bleu-1 및 Rouge-L. RAG 모델들은 k=5 부근에서 최적 성능을 보이며, 검색 문서가 과다하면 노이즈로 인해 성능이 정체 또는 하락한다.*

논문은 top-k 문서 수에 따른 성능 변화도 분석했다. NaturalQuestions에서 $k$를 1에서 10까지 변화시킨 결과, $k=5$에서 최적 성능을 보였고, 그 이후로는 소폭 감소하거나 정체되었다. 이 결과에서 두 가지 중요한 통찰을 얻을 수 있다:

첫째, 검색 재현율(recall)은 $k$가 증가할수록 단조적으로 상승하지만, 최종 QA 성능은 $k=5$ 이후 오히려 감소한다. 이는 관련 없는 문서가 포함되면 생성기에 노이즈로 작용하여 답변 품질을 저해할 수 있음을 의미한다.

둘째, RAG-Token이 RAG-Sequence보다 $k$ 증가에 더 강건한 경향을 보인다. RAG-Token은 토큰별로 문서를 선택적으로 참조하므로, 관련 없는 문서의 영향을 자연스럽게 억제할 수 있기 때문이다.

## 의의 및 한계

### 의의

RAG 논문은 현대 LLM 시대의 검색 증강 생성 패러다임의 토대를 마련했다. 핵심 기여는 다음과 같다:

1. **지식의 외재화**: 모든 지식을 파라미터 안에 저장할 필요 없이 외부 저장소를 활용한다. 이를 통해 파라미터 수를 줄이면서도 지식 범위를 확장할 수 있다. RAG(600M 파라미터 + Wikipedia)가 T5-11B(11B 파라미터, 지식 내재화)보다 우수한 성능을 보인 것이 이를 입증한다.
2. **업데이트 용이성**: 문서 저장소만 갱신하면 새로운 지식을 즉시 반영할 수 있다. 모델을 재학습할 필요가 없어 운영 비용이 크게 절감된다. 논문에서도 문서 인덱스를 교체하여 "hot-swappable" 지식 업데이트가 가능함을 강조했다.
3. **해석 가능성**: 어떤 문서를 근거로 답변했는지 추적 가능하다. 검색된 top-k 문서를 반환하면 사용자가 답변의 근거를 직접 확인할 수 있다. 이는 의료, 법률 등 근거가 중요한 도메인에서 특히 가치 있다.
4. **범용 프레임워크**: QA, 자유 형식 생성, 팩트 검증 등 다양한 지식 집약적 NLP 태스크에 단일 아키텍처로 적용 가능하다. 이전 연구들이 추출형 QA에만 적용 가능했던 것과 대비된다.
5. **산업적 영향**: "RAG"라는 용어와 아키텍처 패턴이 산업 전반의 표준이 되었다. ChatGPT의 Browse with Bing, Perplexity AI, Microsoft Copilot 등 현대 AI 서비스의 핵심 기술이 RAG에 기반한다.

### 후속 연구와의 연결

RAG는 이후 수많은 후속 연구의 기반이 되었다:

| 후속 연구 | 핵심 개선점 | 연도 |
|----------|---------|-----|
| REALM (Guu et al.) | 사전학습 단계에서 검색 통합 | 2020 |
| FiD (Izacard & Grave) | 다중 문서의 교차 어텐션 인코딩 | 2021 |
| RETRO (Borgeaud et al.) | 청크 단위 교차 어텐션, 2조 토큰 스케일 | 2022 |
| Atlas (Izacard et al.) | few-shot 검색 증강 사전학습 | 2023 |
| Self-RAG (Asai et al.) | 적응적 검색 트리거 및 자기 비평 토큰 | 2023 |
| CRAG (Yan et al.) | 검색 결과 품질 평가 및 보정 | 2024 |
| Adaptive-RAG | 질문 난이도에 따른 동적 검색 전략 | 2024 |

특히 LLM의 환각 문제를 줄이기 위한 RAG 시스템은 현재 [[LangChain]], [[LlamaIndex]], Haystack 등 프로덕션 AI 프레임워크의 핵심 구성 요소가 되었다. 2024년 기준 기업 AI 응용 프로그램의 약 80% 이상이 RAG 패턴을 채택하고 있다는 업계 조사도 있다.

### 한계

1. **검색 병목**: 검색 품질이 전체 성능의 상한선이 된다. 관련 문서가 코퍼스에 없을 경우 성능이 급락하며, 검색기의 실패가 곧 전체 시스템의 실패로 이어진다. 이는 후속 연구인 Self-RAG에서 "검색이 필요한지 여부를 먼저 판단"하는 방식으로 개선되었다.
2. **문서 인코더 고정**: 학습 중 문서 인코더 $\text{BERT}_d$가 고정되므로, 태스크에 최적화된 검색이 보장되지 않는다. REALM은 이 문제를 주기적 인덱스 갱신으로 해결했으나, 계산 비용이 크다. 질문 인코더만 학습하는 비대칭 전략은 실용적이지만, 문서 인코더가 DPR 사전학습 시의 분포에 머물러 있다는 근본적 제약이 있다.
3. **컨텍스트 윈도우 제한**: 검색된 문서를 모두 컨텍스트에 담기 어렵다. 2020년 당시 BART의 최대 입력 길이(1024 토큰)가 제약이 되었다. 이후 FiD(Fusion-in-Decoder) 모델이 각 문서를 독립적으로 인코딩하여 이 제한을 완화했다.
4. **추론 지연**: 실시간 검색이 필요하므로 순수 생성 모델 대비 지연시간이 증가한다. FAISS 인덱스 접근과 top-k 문서별 생성 확률 계산에 추가 시간이 소요된다. 특히 RAG-Sequence의 Thorough Decoding은 후보 시퀀스 수 $\times$ 문서 수만큼의 forward pass가 필요하다.
5. **다국어 지원 부족**: Wikipedia 영어판을 코퍼스로 사용하여, 비영어권 태스크에 직접 적용이 어렵다. 한국어 RAG 시스템을 구축하려면 한국어 코퍼스와 한국어에 최적화된 검색기가 별도로 필요하다.
6. **단일 홉(single-hop) 검색**: 한 번의 검색으로만 문서를 가져오므로, 다단계 추론이 필요한 질문(multi-hop reasoning)에는 한계가 있다. 예를 들어 "아인슈타인이 태어난 도시의 현재 인구는?"은 두 번의 검색이 필요하다.

## 코드 예제

### RAG 파이프라인 구현 (PyTorch)

다음은 RAG의 핵심 구성 요소인 Dense Retriever와 생성 모델의 결합을 단순화하여 구현한 코드이다. 논문의 수식을 직접 코드로 매핑하여, RAG-Sequence와 RAG-Token의 주변화 차이를 명확히 보여준다.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


class DenseRetriever(nn.Module):
    """DPR 스타일의 밀집 검색기.

    질문과 문서를 각각 독립적인 인코더로 벡터화한 뒤,
    내적(dot product)으로 유사도를 계산한다.
    """
    def __init__(self, d_model=256, vocab_size=1000):
        super().__init__()
        # 질문 인코더와 문서 인코더를 별도로 구성 (파라미터 비공유)
        self.query_encoder = nn.Sequential(
            nn.Embedding(vocab_size, d_model),
            nn.TransformerEncoder(
                nn.TransformerEncoderLayer(d_model, nhead=8, batch_first=True),
                num_layers=2
            ),
        )
        self.doc_encoder = nn.Sequential(
            nn.Embedding(vocab_size, d_model),
            nn.TransformerEncoder(
                nn.TransformerEncoderLayer(d_model, nhead=8, batch_first=True),
                num_layers=2
            ),
        )

    def encode_query(self, q):
        """질문을 벡터로 인코딩 (CLS 토큰 위치 사용)."""
        return self.query_encoder(q)[:, 0, :]  # [B, d_model]

    def encode_docs(self, docs):
        """문서를 벡터로 인코딩."""
        return self.doc_encoder(docs)[:, 0, :]  # [N, d_model]

    def retrieve(self, query, doc_embeddings, top_k=5):
        """내적 기반 top-k 검색.

        p_eta(z|x) = softmax(q(x)^T * d(z))
        """
        q_emb = self.encode_query(query)  # [B, d_model]
        # 유사도: q^T * d
        scores = torch.matmul(q_emb, doc_embeddings.T)  # [B, N]
        top_scores, top_indices = scores.topk(top_k, dim=-1)
        # 검색 확률: softmax over top-k scores
        retrieval_probs = F.softmax(top_scores, dim=-1)  # [B, top_k]
        return top_indices, retrieval_probs


class RAGGenerator(nn.Module):
    """RAG의 생성 모델 (BART 단순화 버전).

    검색된 문서를 조건으로 답변을 생성한다.
    실제 논문에서는 BART-large (400M)를 사용한다.
    """
    def __init__(self, d_model=256, vocab_size=1000):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model)
        self.decoder = nn.TransformerDecoder(
            nn.TransformerDecoderLayer(d_model, nhead=8, batch_first=True),
            num_layers=4
        )
        self.output_head = nn.Linear(d_model, vocab_size)

    def forward(self, query_tokens, doc_tokens, target_tokens):
        """p_theta(y|x, z): 검색 문서를 조건으로 답변 생성."""
        # 질문 + 검색 문서를 concat하여 인코더 입력 구성
        # 실제 논문: input = x [SEP] z
        context = torch.cat([query_tokens, doc_tokens], dim=1)
        memory = self.embed(context)
        tgt = self.embed(target_tokens)
        output = self.decoder(tgt, memory)
        return self.output_head(output)  # [B, seq_len, vocab_size]


def rag_sequence_loss(generator, query, docs, targets, retrieval_probs):
    """
    RAG-Sequence 손실 함수.

    수식: p_RAG-Seq(y|x) = sum_z p(z|x) * prod_i p(y_i|x,z,y_{<i})

    각 문서별로 전체 시퀀스의 생성 확률을 계산한 후,
    검색 확률로 가중 합산하여 주변화한다.
    """
    batch_size, top_k = retrieval_probs.shape
    total_prob = torch.zeros(batch_size)

    for k in range(top_k):
        # k번째 문서로 전체 시퀀스의 생성 확률 계산
        logits = generator(query, docs[:, k, :], targets)
        log_probs = F.log_softmax(logits, dim=-1)
        # 타겟 토큰의 로그 확률 합산 -> 시퀀스 로그 확률
        token_log_probs = log_probs.gather(
            -1, targets.unsqueeze(-1)
        ).squeeze(-1).sum(dim=-1)  # [B]
        # p(z|x) * p(y|x,z) -- 시퀀스 수준에서 주변화
        total_prob += retrieval_probs[:, k] * token_log_probs.exp()

    loss = -torch.log(total_prob + 1e-10).mean()
    return loss


def rag_token_loss(generator, query, docs, targets, retrieval_probs):
    """
    RAG-Token 손실 함수.

    수식: p_RAG-Token(y|x) = prod_i sum_z p(z|x) * p(y_i|x,z,y_{<i})

    각 토큰 생성 시마다 문서에 대한 주변화를 수행한다.
    """
    batch_size, top_k = retrieval_probs.shape
    seq_len = targets.shape[1]
    # 각 문서별 토큰 확률을 수집
    all_token_probs = []  # [top_k, B, seq_len]

    for k in range(top_k):
        logits = generator(query, docs[:, k, :], targets)
        probs = F.softmax(logits, dim=-1)  # [B, seq_len, vocab]
        token_probs = probs.gather(
            -1, targets.unsqueeze(-1)
        ).squeeze(-1)  # [B, seq_len]
        all_token_probs.append(token_probs)

    # [top_k, B, seq_len] -> [B, seq_len, top_k]
    all_token_probs = torch.stack(all_token_probs, dim=-1)
    # 토큰별로 문서에 대한 가중 합산 (주변화)
    # retrieval_probs: [B, top_k] -> [B, 1, top_k]
    marginal_probs = (all_token_probs * retrieval_probs.unsqueeze(1)).sum(-1)
    # 로그 확률의 합 = 시퀀스 로그 확률
    loss = -torch.log(marginal_probs + 1e-10).sum(dim=-1).mean()
    return loss


# 사용 예시
retriever = DenseRetriever()
generator = RAGGenerator()

query = torch.randint(0, 1000, (2, 10))    # 배치 2, 시퀀스 길이 10
docs = torch.randint(0, 1000, (2, 5, 20))  # 5개 문서, 각 20토큰
targets = torch.randint(0, 1000, (2, 15))  # 답변 15토큰
retrieval_probs = F.softmax(torch.randn(2, 5), dim=-1)

# RAG-Sequence vs RAG-Token 비교
loss_seq = rag_sequence_loss(generator, query, docs, targets, retrieval_probs)
loss_tok = rag_token_loss(generator, query, docs, targets, retrieval_probs)
print(f"RAG-Sequence Loss: {loss_seq.item():.4f}")
print(f"RAG-Token Loss:    {loss_tok.item():.4f}")
```

### HuggingFace Transformers를 활용한 RAG 추론

HuggingFace Transformers 라이브러리에는 RAG 논문의 공식 구현체가 포함되어 있다. 다음은 사전학습된 RAG 모델을 사용하여 오픈 도메인 질의응답을 수행하는 예제이다.

```python
from transformers import RagTokenizer, RagRetriever, RagTokenForGeneration

# RAG-Token 모델과 검색기 로드
tokenizer = RagTokenizer.from_pretrained("facebook/rag-token-nq")
retriever = RagRetriever.from_pretrained(
    "facebook/rag-token-nq",
    index_name="exact",  # 또는 "compressed"로 메모리 절약
    use_dummy_dataset=True  # 데모용: 실제 사용 시 False
)
model = RagTokenForGeneration.from_pretrained(
    "facebook/rag-token-nq",
    retriever=retriever
)

# 질문 입력 및 답변 생성
question = "What is the capital of France?"
inputs = tokenizer(question, return_tensors="pt")

# generate() 내부에서 DPR 검색 + BART 생성이 자동 수행됨
output = model.generate(
    input_ids=inputs["input_ids"],
    num_beams=4,
    max_length=50
)

answer = tokenizer.batch_decode(output, skip_special_tokens=True)[0]
print(f"Q: {question}")
print(f"A: {answer}")
# 출력: A: Paris
```

> **핵심 포인트**: RAG는 검색 확률 $p_\eta(z|x)$와 생성 확률 $p_\theta(y|x,z)$를 주변화(marginalization)하여 결합한다. RAG-Sequence는 시퀀스 수준에서, RAG-Token은 토큰 수준에서 주변화를 수행하며, 이 차이가 정보 조합의 세밀함과 답변의 일관성에 영향을 미친다. 검색기가 반환한 문서의 품질이 높을수록 생성 모델이 더 정확한 답변을 생성할 수 있으며, 이 두 컴포넌트가 end-to-end로 공동 학습되는 것이 RAG의 핵심 설계 원칙이다.
