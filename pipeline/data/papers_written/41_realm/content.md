<!-- infographic-hero -->
![REALM: Retrieval-Augmented Language Model Pre-Training 핵심 요약](figures/infographic.svg)

*Figure: REALM: Retrieval-Augmented Language Model Pre-Training 한 장 요약 인포그래픽*

## 개요

대규모 언어 모델(LLM)은 사전학습 과정에서 학습 코퍼스의 방대한 사실 지식(factual knowledge)을 모델 파라미터에 암묵적으로 저장합니다. BERT, GPT-2 등이 놀라운 성능을 보여준 배경에는 이러한 파라메트릭 지식 저장(parametric knowledge storage) 메커니즘이 있었습니다. 그러나 이 접근법에는 근본적인 한계가 존재합니다. 지식이 수억 개의 파라미터에 분산 저장되어 특정 사실의 인코딩 위치를 파악하기 어렵고, 세상의 지식은 끊임없이 변화하는데 모델 파라미터는 재학습 없이는 갱신할 수 없으며, 더 많은 지식을 저장하려면 모델 크기를 계속 키워야 하는 확장성 문제도 있습니다.

Guu et al.(2020)이 ICML 2020에서 발표한 **REALM(Retrieval-Augmented Language Model Pre-training)**은 이러한 근본적 한계를 사전학습 단계에서 정면으로 해결하는 새로운 패러다임을 제시합니다. REALM의 핵심 아이디어는 언어 모델이 예측을 수행할 때마다 수백만 개의 외부 문서로 구성된 코퍼스에서 관련 문서를 실시간으로 검색하여 추가 맥락으로 활용하는 것입니다. 사실 지식이 모델 파라미터가 아닌 외부 문서 저장소에 명시적으로 유지되므로, 저장소의 문서만 교체하면 모델 재학습 없이도 지식을 갱신할 수 있습니다.

REALM은 이후 등장한 RAG(Lewis et al., 2020), RETRO(Borgeaud et al., 2022), Atlas(Izacard et al., 2022) 등 검색 증강 생성(retrieval-augmented generation) 연구의 직접적인 출발점이 되었으며, 현대 LLM 시스템에서 보편적으로 활용되는 RAG 아키텍처의 이론적 토대를 마련한 선구적 연구입니다.

![REALM 아키텍처 파이프라인 개요](figures/architecture.png)
*REALM의 전체 아키텍처 파이프라인. 입력 쿼리가 BERT 기반 Dense Retriever를 통해 MIPS 인덱스에서 상위 k개 관련 문서를 검색하고, 검색된 패시지들을 BERT Masked LM(Generator/Reader)에 결합하여 최종 답변을 생성한다. 사전학습 단계에서부터 검색과 인코딩이 공동으로 학습되며, 비동기 인덱스 갱신을 통해 대규모 코퍼스 검색이 가능하다.*

---

## 배경 및 문제

### 파라메트릭 지식 저장의 한계

BERT(Devlin et al., 2019)와 GPT-2(Radford et al., 2019)의 성공 이후, 대규모 사전학습 모델이 상당한 양의 사실 지식을 파라미터에 저장할 수 있다는 사실이 알려졌습니다. Petroni et al.(2019)의 "Language Models as Knowledge Bases"에서는 BERT가 일정 수준의 관계형 지식을 암묵적으로 학습한다는 것을 보여주었습니다. 그러나 이 방식에는 다음과 같은 구조적 문제가 있습니다.

**해석 불가능성(Opacity)**: 모델이 "알베르트 아인슈타인은 1921년에 노벨 물리학상을 수상했다"라는 사실을 올바르게 예측하더라도, 이 지식이 어떤 파라미터에 어떤 형태로 저장되어 있는지 파악하는 것은 사실상 불가능합니다. 예측이 틀렸을 때 어떤 지식이 잘못 저장되었는지 디버깅할 수도 없습니다.

**정적 지식(Static Knowledge)**: 모델이 학습된 시점 이후의 정보는 반영할 수 없습니다. 2020년에 학습된 모델은 2021년 이후의 사건에 대해 답할 수 없으며, 잘못된 정보를 수정하려면 전체 또는 부분 재학습이 필요합니다.

**확장성 문제(Scalability)**: 더 많은 사실 지식을 저장하려면 모델의 파라미터 수를 늘려야 합니다. T5-11B와 같은 초대형 모델도 세계의 모든 사실을 담기에는 부족하며, 모델 크기 증가는 학습 비용과 추론 비용의 급격한 증가를 수반합니다.

### 기존 검색 통합 접근법의 한계

REALM 이전에도 외부 지식을 활용하려는 시도는 있었습니다. DrQA(Chen et al., 2017)는 TF-IDF 기반 문서 검색과 신경망 판독기를 결합하였고, DPR(Karpukhin et al., 2020)은 밀집 벡터 기반 검색을 제안하였습니다. 그러나 이러한 방법들은 모두 파인튜닝 또는 추론 단계에서만 검색을 도입했습니다. 사전학습된 모델이 이미 파라메트릭 지식에 의존하는 방식으로 학습된 후에야 검색이 추가되는 구조였기 때문에, 검색 기능이 모델의 표현 공간에 근본적으로 통합되지 못했습니다.

REALM의 핵심적 차별점은 **사전학습 단계에서부터** 검색을 통합한다는 것입니다. 모델이 처음 학습을 시작할 때부터 외부 문서를 검색하고 활용하는 방법을 함께 배우므로, 검색과 언어 이해가 근본적으로 통합된 표현(representation)을 학습할 수 있습니다.

---

## 핵심 아이디어

REALM의 핵심 아이디어는 **검색 증강 사전학습(Retrieval-Augmented Pre-training)**입니다. 전통적인 마스킹 언어 모델(Masked Language Model, MLM)에서는 입력 시퀀스 $x$만을 사용하여 마스킹된 토큰 $y$를 예측합니다.

$$p(y|x) = f_{\theta}(x)$$

REALM은 이 과정에 잠재 변수(latent variable) $z$를 도입합니다. $z$는 외부 문서 코퍼스 $\mathcal{Z}$에서 검색된 문서를 나타내며, 예측은 검색된 모든 문서에 대한 주변화(marginalization)를 통해 수행됩니다.

$$p(y|x) = \sum_{z \in \mathcal{Z}} p(z|x) \cdot p(y|z, x)$$

이 공식에서 $p(z|x)$는 **지식 검색기(Knowledge Retriever)**가 입력 $x$에 대해 문서 $z$를 검색할 확률이며, $p(y|z, x)$는 **지식 증강 인코더(Knowledge-Augmented Encoder)**가 검색된 문서 $z$와 입력 $x$를 함께 고려하여 정답 $y$를 예측할 확률입니다.

![REALM의 검색 증강 사전학습 전체 파이프라인](figures/fig_1.png)
*REALM의 검색 증강 사전학습 파이프라인. 마스킹된 입력 $x$에 대해 Neural Knowledge Retriever $p_\theta(z|x)$가 텍스트 지식 코퍼스 $\mathcal{Z}$에서 관련 문서를 검색하고, Knowledge-Augmented Encoder $p_\phi(y|x,z)$가 검색된 문서와 입력을 결합하여 마스킹된 토큰을 예측한다. 전체 과정이 end-to-end 역전파로 학습되며, 수백만 문서 규모의 검색을 처리하는 것이 핵심 기술적 과제이다 (Guu et al., 2020).*

이 공식화의 핵심적인 특성은 학습 과정에서 검색기 $p(z|x)$에 대한 명시적인 지도 신호(supervision)가 없다는 것입니다. 어떤 문서를 검색해야 하는지 레이블이 주어지지 않습니다. 대신, 최종 목표인 $\log p(y|x)$를 최대화하는 과정에서 그래디언트가 검색기로 역전파되어, 예측에 도움이 되는 문서를 더 높은 확률로 검색하도록 자동 학습됩니다. 이것이 REALM의 가장 우아한 설계입니다.

---

## 방법론

### Knowledge Retriever $p(z|x)$

지식 검색기는 입력 $x$가 주어졌을 때 문서 코퍼스 $\mathcal{Z}$에서 가장 관련성 높은 문서 $z$를 찾는 역할을 합니다. 검색기는 **이중 인코더(bi-encoder)** 구조를 사용합니다.

입력 $x$와 문서 $z$를 각각 독립적인 BERT 인코더로 임베딩합니다.

$$\text{Embed}_{\text{input}}(x) = W_{\text{input}} \cdot \text{BERT}_{\text{CLS}}(\text{join}_{\text{input}}(x))$$

$$\text{Embed}_{\text{doc}}(z) = W_{\text{doc}} \cdot \text{BERT}_{\text{CLS}}(\text{join}_{\text{doc}}(z_{\text{title}}, z_{\text{body}}))$$

여기서 $\text{join}_{\text{input}}(x) = [\text{CLS}] \ x \ [\text{SEP}]$이고, $\text{join}_{\text{doc}}(z_{\text{title}}, z_{\text{body}}) = [\text{CLS}] \ z_{\text{title}} \ [\text{SEP}] \ z_{\text{body}} \ [\text{SEP}]$입니다. $W_{\text{input}}$와 $W_{\text{doc}}$는 BERT의 hidden dimension(768)에서 더 낮은 차원의 임베딩 공간으로의 학습 가능한 투영 행렬(projection matrix)입니다.

두 임베딩 사이의 관련도 점수(relevance score)는 내적(inner product)으로 계산됩니다.

$$f(x, z) = \text{Embed}_{\text{input}}(x)^{\top} \cdot \text{Embed}_{\text{doc}}(z)$$

검색 확률은 전체 코퍼스에 대한 소프트맥스로 정의됩니다.

$$p(z|x) = \frac{\exp(f(x, z))}{\sum_{z' \in \mathcal{Z}} \exp(f(x, z'))}$$

이중 인코더 구조의 핵심적 이점은 입력과 문서를 독립적으로 인코딩할 수 있다는 점입니다. 문서 임베딩을 사전에 계산하여 인덱스에 저장해 두면, 추론 시에는 입력 임베딩만 계산한 후 MIPS(Maximum Inner Product Search)로 상위 $k$개 문서를 효율적으로 검색할 수 있습니다. 이 설계가 수백만 문서 규모의 코퍼스에서도 실시간 검색을 가능하게 하는 핵심입니다.

### Knowledge-Augmented Encoder $p(y|z, x)$

검색된 문서 $z$와 입력 $x$를 결합하여 마스킹된 토큰 $y$를 예측하는 인코더입니다. 입력과 문서를 하나의 시퀀스로 연결한 후 Transformer 인코더에 통과시킵니다.

$$\text{join}_{\text{REALM}}(x, z) = [\text{CLS}] \ x \ [\text{SEP}] \ z_{\text{title}} \ [\text{SEP}] \ z_{\text{body}} \ [\text{SEP}]$$

이 결합된 시퀀스를 BERT에 통과시켜 각 마스킹된 위치 $j$에서의 토큰 예측 확률을 계산합니다.

$$p(y_j | z, x) = \text{softmax}(W_j \cdot h_j + b_j)$$

여기서 $h_j$는 BERT의 마스킹 위치 $j$에 대응하는 출력 벡터이며, $W_j$와 $b_j$는 토큰 예측 헤드의 파라미터입니다. 검색기의 이중 인코더와 달리, 이 인코더는 입력과 문서를 하나의 시퀀스로 결합하여 처리하므로 토큰 간 교차 어텐션(cross-attention)을 통해 훨씬 풍부한 상호작용을 학습할 수 있습니다. 이중 인코더(효율성)와 교차 인코더(표현력)의 역할 분리는 이후 DPR, ColBERT 등 후속 연구에서도 표준적으로 채택된 설계 패턴입니다.

### 사전학습 목표: 주변 우도 최대화

REALM의 사전학습 목표는 마스킹된 토큰에 대한 로그 주변 우도(log marginal likelihood)를 최대화하는 것입니다.

$$\mathcal{L}_{\text{REALM}} = \sum_{j} \log p(y_j | x) = \sum_{j} \log \sum_{z \in \mathcal{Z}_{\text{top-}k}} p(z|x) \cdot p(y_j | z, x)$$

이 목표 함수의 그래디언트를 분석하면 검색기의 학습 동역학(dynamics)을 직관적으로 이해할 수 있습니다. 검색기 파라미터 $\theta$에 대한 그래디언트는 다음과 같습니다.

$$\nabla_{\theta} \log p(y|x) = \sum_{z} \frac{p(z|x) \cdot p(y|z,x)}{\sum_{z'} p(z'|x) \cdot p(y|z',x)} \nabla_{\theta} \log p(z|x)$$

$$= \sum_{z} r(z) \nabla_{\theta} \log p(z|x)$$

여기서 $r(z) = \frac{p(z|x) \cdot p(y|z,x)}{p(y|x)}$는 문서 $z$의 **보상 신호(reward signal)**로 해석할 수 있습니다. 문서 $z$가 정답 예측에 도움이 되면(즉, $p(y|z,x)$가 크면) $r(z)$가 커져서 해당 문서를 더 높은 확률로 검색하도록 검색기가 업데이트됩니다. 반대로 도움이 되지 않는 문서는 검색 확률이 낮아집니다.

이 구조는 REINFORCE 알고리즘과 유사하지만 결정적 차이가 있습니다. REINFORCE에서는 이산적(discrete) 행동 선택에 대한 기대 보상을 최적화하므로 높은 분산(variance)이 문제가 됩니다. 반면 REALM에서는 잠재 변수 $z$가 연속적인 임베딩 공간에서 정의되고, top-k 문서에 대한 직접적인 주변화가 가능하므로 분산 문제 없이 안정적으로 학습됩니다. 이는 기대값을 샘플링으로 근사하는 대신 직접 계산하는 것에 해당하므로, 학습 안정성 측면에서 큰 이점을 제공합니다.

### 비동기 MIPS 인덱스 갱신

전체 코퍼스 $\mathcal{Z}$에서 상위 $k$개 문서를 찾으려면, 모든 문서에 대해 관련도 점수 $f(x, z)$를 계산해야 합니다. 코퍼스 크기가 수백만에 달하므로 선형 탐색은 불가능하며, REALM은 이 문제를 MIPS(Maximum Inner Product Search)로 해결합니다.

$$z^{*} = \arg\max_{z \in \mathcal{Z}} f(x, z) = \arg\max_{z \in \mathcal{Z}} \text{Embed}_{\text{input}}(x)^{\top} \cdot \text{Embed}_{\text{doc}}(z)$$

MIPS는 사전에 모든 문서의 임베딩 $\text{Embed}_{\text{doc}}(z)$를 계산하여 인덱스에 저장한 후, 쿼리 벡터 $\text{Embed}_{\text{input}}(x)$와의 내적이 가장 큰 $k$개를 근사 최근접 이웃(approximate nearest neighbor) 알고리즘으로 빠르게 찾습니다.

그러나 학습 중에 문서 인코더 $\text{Embed}_{\text{doc}}$의 파라미터가 매 스텝마다 변하므로, 인덱스에 저장된 임베딩이 현재 모델의 임베딩과 달라지는 문제가 발생합니다. 매 스텝마다 전체 코퍼스(약 1,300만 청크)를 재인코딩하는 것은 계산적으로 불가능합니다.

![REALM 비동기 MIPS 인덱스 갱신 구조](figures/fig_3.png)
*REALM 사전학습에서의 비동기 MIPS 인덱스 갱신 메커니즘. Index builder가 이전 파라미터 $\theta'$로 전체 문서 임베딩을 재계산하여 MIPS 인덱스를 구축하는 동안, MLM trainer는 최신 파라미터 $\theta$로 학습을 계속한다. 주기적으로 $\theta' \leftarrow \theta$로 동기화하고 인덱스를 교체함으로써, 수백만 문서 규모에서도 효율적인 end-to-end 학습이 가능해진다 (Guu et al., 2020).*

REALM은 **비동기 인덱스 갱신(asynchronous index refresh)** 전략으로 이 문제를 해결합니다.

1. 별도의 백그라운드 프로세스(Index builder)가 학습과 병렬로 전체 코퍼스의 임베딩을 재계산합니다.
2. 매 $T$ 스텝(논문에서는 약 500 스텝)마다 인덱스를 새 임베딩으로 교체합니다.
3. 인덱스가 최대 $T$ 스텝 이전의 파라미터(stale $\theta'$)로 계산되었으므로 약간 구식이지만, 실험적으로 학습에 큰 영향이 없음을 확인했습니다.

이 설계의 핵심 가정은 문서 인코더의 파라미터가 $T$ 스텝 동안 크게 변하지 않는다는 것입니다. 사전학습이 진행될수록 파라미터 변화율이 줄어들기 때문에, 이 가정은 대체로 성립합니다. 인덱스 갱신에 필요한 추가 계산 비용은 전체 학습 FLOPs의 약 $1/T$ 비율에 해당합니다.

### 사전학습 데이터 설계

**문서 코퍼스**: Wikipedia 영문판 전체를 사용합니다. 각 문서는 최대 288개 wordpiece 토큰 길이의 청크(chunk)로 분할되며, 총 약 1,300만 개의 청크가 생성됩니다.

**세일리언트 스팬 마스킹(Salient Span Masking)**: REALM은 일반적인 무작위 토큰 마스킹 대신, 개체명(named entity) 또는 날짜와 같은 사실적 정보를 담고 있는 스팬을 우선적으로 마스킹하는 전략을 사용합니다. 예를 들어:

> "The 2019 Nobel Prize in Chemistry was awarded to [MASK] for the development of lithium-ion batteries."

모델은 정답 "John B. Goodenough, M. Stanley Whittingham, and Akira Yoshino"를 예측하기 위해 노벨 화학상 수상자에 대한 문서를 검색해야 합니다. "the", "for", "of" 등 기능어를 마스킹하는 것과 달리, 사실 지식을 포함한 스팬을 마스킹해야 검색기에 유의미한 학습 신호가 전달됩니다. 세일리언트 스팬은 BERT 기반 NER 태거와 정규식 기반 날짜 인식기로 후보를 추출한 후, CoNLL-2003 데이터셋에서 학습된 세일리언시 분류기를 사용하여 선택합니다.

**Null 문서 처리**: REALM은 특수한 null 문서 $z_{\emptyset}$(빈 문자열)를 코퍼스에 추가합니다. 모델이 "He is a [MASK] student"에서 "good"을 예측할 때는 외부 문서가 필요 없으므로, $p(z_{\emptyset}|x)$가 높아야 합니다. null 문서의 존재는 모델이 검색의 필요 여부를 스스로 판단할 수 있게 하여, 불필요한 검색으로 인한 성능 저하를 방지합니다. 이는 현대 RAG 시스템에서 adaptive retrieval(필요한 경우에만 검색)의 선구적 아이디어에 해당합니다.

### 파인튜닝: Open-domain QA

사전학습된 REALM을 Open-domain QA에 적용할 때, Knowledge-Augmented Encoder의 출력 레이어만 변경합니다. MLM 헤드 대신 추출형 QA 헤드를 사용합니다.

검색된 각 문서 $z$에서 답변 스팬 $a = (a_{\text{start}}, a_{\text{end}})$의 확률을 다음과 같이 계산합니다.

$$p(a|z, x) \propto \exp\left(\text{MLP}([h_{a_{\text{start}}}; h_{a_{\text{end}}}])\right)$$

최종 답변 확률은 검색 확률과 결합하여 주변화합니다.

$$p(a|x) = \sum_{z \in \mathcal{Z}_{\text{top-}k}} p(z|x) \cdot p(a|z, x)$$

파인튜닝 시에도 검색기의 파라미터가 함께 업데이트되므로, 검색기는 QA 태스크에 최적화된 문서를 검색하도록 추가 학습됩니다. 사전학습 단계에서 학습된 범용 검색 능력이 태스크 특화 검색 능력으로 전이(transfer)되는 것이며, 이 때문에 사전학습 단계에서의 검색 통합이 중요합니다.

---

## 실험 결과

### Open-domain QA 벤치마크

REALM은 세 가지 Open-domain QA 벤치마크에서 평가되었습니다. Exact Match(EM) 점수 기준 결과는 다음과 같습니다.

| 모델 | 파라미터 수 | NaturalQuestions | WebQuestions | CuratedTrec |
|------|-----------|------------------|--------------|-------------|
| DrQA (Chen et al., 2017) | - | - | 20.7 | 25.7 |
| BERTserini (Yang et al., 2019) | 110M | 38.6 | - | - |
| Multi-step Reasoner | - | 31.9 | - | - |
| ORQA (Lee et al., 2019) | 330M | 33.3 | 36.4 | 30.1 |
| T5-11B (Closed-book) | 11B | 34.5 | 37.4 | - |
| T5-11B+SSM (Closed-book) | 11B | 36.6 | 44.7 | - |
| **REALM (ours)** | **330M** | **40.4** | **40.7** | **46.8** |

REALM은 330M 파라미터만으로 11B 파라미터의 T5보다 NaturalQuestions에서 약 4%p 높은 성능을 달성했습니다. 이는 파라미터 수 기준으로 33배 작은 모델이 더 큰 모델을 능가한 결과입니다. CuratedTrec에서는 동일 규모의 ORQA 대비 16.7%p 더 높은 성능을 보였으며, 이 격차는 사전학습 단계에서의 검색 통합이 가져온 표현 학습의 질적 차이를 반영합니다.

한편 WebQuestions에서 T5-11B+SSM이 44.7로 REALM의 40.7을 능가합니다. T5가 33배 더 큰 파라미터를 사용하고 추가적인 세일리언트 스팬 마스킹(SSM) 사전학습을 수행한 결과이며, WebQuestions의 특성상 파라메트릭 지식이 충분한 질문이 많아 대형 모델의 암묵적 지식 저장이 유리하게 작용한 것으로 분석됩니다. 그러나 파라미터 효율성 관점에서 REALM의 접근법이 훨씬 매력적인 것은 명확합니다.

### Ablation Study: 각 구성 요소의 기여도

REALM의 핵심 설계 결정들이 최종 성능에 미치는 영향을 정량적으로 분석한 ablation study 결과입니다.

| 설정 | NaturalQuestions EM |
|------|--------------------|
| REALM (full) | 40.4 |
| REALM w/o pre-train retrieval | 37.2 (-3.2) |
| REALM w/o salient span masking | 38.5 (-1.9) |
| REALM w/o null document | 39.6 (-0.8) |
| REALM w/ random retrieval | 34.1 (-6.3) |

이 결과에서 세 가지 핵심 발견이 있습니다.

**사전학습 검색이 가장 중요한 기여 요소입니다.** 검색 통합을 파인튜닝 단계에서만 적용한 경우(w/o pre-train retrieval) NQ에서 3.2%p 하락했습니다. 모델이 이미 파라메트릭 지식에 의존하는 표현을 학습한 상태에서 검색을 추가하면, 검색 결과를 효과적으로 활용하는 능력이 제한됩니다. 이 결과는 REALM의 핵심 가설 -- "사전학습 단계에서의 검색 통합이 필수적" -- 을 강하게 뒷받침합니다.

**세일리언트 스팬 마스킹이 검색기 학습을 유도합니다.** 일반 무작위 마스킹 대비 1.9%p 향상이 관찰되었습니다. "the", "is" 같은 기능어를 마스킹하면 외부 지식 없이도 예측이 가능하므로 검색기에 유의미한 학습 신호가 전달되지 않습니다. 사실 정보를 담은 스팬을 마스킹해야 검색기가 관련 문서를 찾아야 하는 동기를 얻습니다.

**무작위 검색과의 6.3%p 차이가 검색기의 학습을 입증합니다.** 학습된 검색기 대신 무작위로 문서를 선택하면 무관한 노이즈가 인코더에 주입되어 오히려 성능이 크게 하락합니다. 이는 검색기가 단순한 키워드 매칭이 아니라 의미론적 관련도에 기반한 정교한 문서 선별을 학습했음을 반증합니다.

### 인덱스 갱신 빈도의 영향

비동기 인덱스 갱신 전략의 실용적 유효성을 검증한 결과입니다.

| 갱신 주기 $T$ | NaturalQuestions EM |
|--------------|--------------------|
| $T = 1$ (매 스텝) | 이론적 상한 (계산 불가) |
| $T = 500$ | 40.4 |
| $T = 5000$ | 39.8 |
| 갱신 없음 | 38.1 |

$T = 500$에서 $T = 5000$으로 갱신 주기를 10배 늘려도 성능 하락은 0.6%p에 불과합니다. 이는 문서 인코더의 파라미터가 수천 스텝 동안 급격히 변하지 않기 때문에, 약간 구식인(stale) 인덱스도 합리적으로 정확한 검색 결과를 제공함을 보여줍니다. 반면 인덱스를 전혀 갱신하지 않으면 2.3%p 하락하여, 학습 진행에 따른 표현 공간의 점진적 변화를 반영하는 주기적 갱신의 필요성을 확인할 수 있습니다.

이 결과는 실용적 관점에서 중요합니다. 인덱스 갱신 빈도를 10배 줄여도 성능 손실이 미미하므로, 계산 자원이 제한된 환경에서도 비동기 갱신 전략을 적용할 수 있습니다.

### 검색된 문서의 정성적 분석

학습이 진행됨에 따라 검색기가 점점 더 관련성 높은 문서를 찾는 것이 관찰되었습니다. 예를 들어 "In 1996, [MASK] won the Academy Award for Best Picture"라는 입력에 대해, 학습 초기에는 관련 없는 영화 기사가 검색되었지만 학습 후반에는 "Braveheart"에 대한 Wikipedia 문서가 상위에 검색되었습니다. 이는 검색기가 단순한 키워드 매칭(예: "Academy Award" 포함 문서)에서 의미론적 추론(정답을 포함한 문서를 선별)으로 발전하는 과정을 보여줍니다.

---

## 의의 및 한계

### 학술적 의의

**RAG 패러다임의 확립**: REALM은 검색 증강 생성(Retrieval-Augmented Generation) 패러다임의 이론적 기반을 마련했습니다. 잠재 변수로서의 문서 검색, 주변 우도를 통한 end-to-end 학습이라는 프레임워크는 이후 RAG(Lewis et al., 2020), FiD(Izacard & Grave, 2021), Atlas(Izacard et al., 2022), RETRO(Borgeaud et al., 2022) 등 후속 연구들의 직접적인 기반이 되었습니다.

**명시적 지식 분리**: 모델의 파라메트릭 지식과 외부 검색 지식을 명시적으로 분리함으로써, 지식의 갱신, 수정, 추적이 가능한 구조를 제시했습니다. 이는 현대 LLM 시스템에서 환각(hallucination) 문제를 완화하는 핵심 전략으로 자리잡았습니다.

**파라미터 효율성 입증**: 330M 파라미터의 REALM이 11B 파라미터의 T5를 능가한 결과는, 모델 크기 확대(scale-up)만이 지식 활용의 유일한 경로가 아니며 외부 지식 검색이라는 대안적 경로가 존재함을 보여주었습니다.

**해석 가능한 추론**: 모델이 어떤 문서를 참조하여 예측을 내렸는지 추적할 수 있어, 블랙박스 모델의 한계를 부분적으로 극복했습니다. 검색된 문서를 통해 모델의 추론 근거를 사후적으로 검증할 수 있다는 점은, 안전성과 신뢰성이 중요한 응용에서 큰 장점입니다.

### 실용적 의의

현대 LLM 애플리케이션에서 RAG는 거의 필수적인 구성 요소가 되었습니다. ChatGPT, Perplexity 등의 상용 시스템은 웹 검색을 통해 최신 정보를 제공하며, 기업용 LLM 시스템은 내부 문서 검색을 통해 도메인 특화 지식을 활용합니다. REALM이 제시한 "검색기와 언어 모델의 공동 학습"이라는 원리는 이 모든 시스템의 이론적 기반이 됩니다. 특히 검색기를 잠재 변수로 모델링하여 end-to-end로 학습할 수 있다는 가능성을 처음 보여준 것이 REALM의 가장 큰 실용적 기여입니다.

### 한계

**학습 복잡성**: 검색기와 언어 모델의 공동 학습은 표준 LM 학습보다 복잡합니다. MIPS 인덱스의 비동기 갱신은 분산 학습 인프라에 대한 추가적인 엔지니어링을 요구하며, 학습 파이프라인의 구현 난이도가 높아 재현(reproduction)이 쉽지 않습니다.

**검색 지연(Retrieval Latency)**: 추론 시 매 예측마다 MIPS 검색이 필요하므로, 순수 파라메트릭 모델 대비 추론 속도가 느립니다. 수백만 문서 규모의 인덱스에서 top-k 검색을 수행하는 시간이 전체 추론 시간의 상당 부분을 차지하며, 실시간 응답이 필요한 서비스에서는 병목이 될 수 있습니다.

**검색 오류 전파**: 검색기가 관련 없는 문서를 반환하면 인코더가 잘못된 맥락에 기반하여 예측하게 됩니다. 검색 품질이 최종 성능의 상한을 결정하는 구조이므로, 검색 실패가 직접적으로 성능 저하로 이어집니다. 특히 코퍼스에 답변을 포함한 문서가 존재하지 않는 경우, 모델은 원천적으로 정답을 도출할 수 없습니다.

**추출형 QA 한정**: REALM은 문서에서 답변 스팬을 추출하는 방식에 최적화되어 있어, 자유 형식 텍스트 생성(open-ended generation)에는 직접 적용이 어렵습니다. 이 한계는 이후 RAG(Lewis et al., 2020)에서 seq2seq 디코더(BART)와의 결합으로 해결되었습니다.

**단일 문서 참조**: REALM은 각 예측에서 독립적으로 검색된 개별 문서만을 참조합니다. 여러 문서에 분산된 정보를 종합하여 추론하는 다중 홉(multi-hop) 추론에는 구조적 한계가 있습니다. 이 문제는 이후 FiD(Fusion-in-Decoder)에서 여러 검색 문서를 디코더에서 융합하는 방식으로 개선되었습니다.

---

## 코드 예제

### 지식 검색기 (Knowledge Retriever)

이중 인코더 구조로 입력 $x$와 문서 $z$를 각각 임베딩하고 내적으로 관련도를 계산합니다.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import BertModel, BertTokenizer

class KnowledgeRetriever(nn.Module):
    """지식 검색기: 입력 x에 대해 문서 z의 관련도를 계산합니다."""

    def __init__(self, embed_dim=128):
        super().__init__()
        self.input_encoder = BertModel.from_pretrained("bert-base-uncased")
        self.doc_encoder = BertModel.from_pretrained("bert-base-uncased")
        self.input_proj = nn.Linear(768, embed_dim)
        self.doc_proj = nn.Linear(768, embed_dim)

    def embed_input(self, input_ids, attention_mask):
        # 입력 x의 CLS 임베딩을 투영
        outputs = self.input_encoder(input_ids, attention_mask=attention_mask)
        cls_embed = outputs.last_hidden_state[:, 0, :]  # [batch, 768]
        return self.input_proj(cls_embed)  # [batch, embed_dim]

    def embed_doc(self, doc_ids, doc_mask):
        # 문서 z의 CLS 임베딩을 투영
        outputs = self.doc_encoder(doc_ids, attention_mask=doc_mask)
        cls_embed = outputs.last_hidden_state[:, 0, :]  # [num_docs, 768]
        return self.doc_proj(cls_embed)  # [num_docs, embed_dim]

    def compute_relevance(self, input_embed, doc_embeds):
        # f(x, z) = Embed_input(x)^T * Embed_doc(z)
        scores = torch.matmul(input_embed, doc_embeds.T)  # [batch, num_docs]
        return scores

```

### 지식 증강 인코더 (Knowledge-Augmented Encoder)

검색된 문서 $z$와 입력 $x$를 결합하여 마스킹된 토큰 $y$를 예측하는 BERT 기반 인코더입니다.

```python
class KnowledgeAugmentedEncoder(nn.Module):
    """지식 증강 인코더: 입력 x와 문서 z를 결합하여 y를 예측합니다."""

    def __init__(self, vocab_size=30522):
        super().__init__()
        self.encoder = BertModel.from_pretrained("bert-base-uncased")
        self.mlm_head = nn.Linear(768, vocab_size)

    def forward(self, combined_ids, combined_mask, masked_positions):
        outputs = self.encoder(combined_ids, attention_mask=combined_mask)
        hidden = outputs.last_hidden_state  # [batch, seq_len, 768]
        # 마스킹된 위치의 표현 추출
        masked_hidden = hidden.gather(
            1, masked_positions.unsqueeze(-1).expand(-1, -1, 768)
        )  # [batch, num_masks, 768]
        logits = self.mlm_head(masked_hidden)  # [batch, num_masks, vocab_size]
        return logits

```

### REALM 전체 모델

검색기와 인코더를 결합하여 주변 우도(marginal likelihood)를 최대화하는 end-to-end 학습 구조입니다.

```python
class REALM(nn.Module):
    """REALM: 검색기와 인코더를 결합한 전체 모델입니다."""

    def __init__(self, top_k=5):
        super().__init__()
        self.retriever = KnowledgeRetriever()
        self.reader = KnowledgeAugmentedEncoder()
        self.top_k = top_k

    def forward(self, input_ids, input_mask, doc_ids, doc_masks,
                combined_inputs, combined_masks, masked_positions, labels):
        # 1단계: 검색 확률 계산 p(z|x)
        input_embed = self.retriever.embed_input(input_ids, input_mask)
        doc_embeds = self.retriever.embed_doc(doc_ids, doc_masks)
        relevance_scores = self.retriever.compute_relevance(
            input_embed, doc_embeds
        )  # [batch, num_docs]

        # top-k 문서 선택 (실제로는 MIPS로 수행)
        top_k_scores, top_k_indices = relevance_scores.topk(
            self.top_k, dim=-1
        )
        log_retrieval_probs = F.log_softmax(
            top_k_scores, dim=-1
        )  # [batch, top_k]

        # 2단계: 각 문서에 대해 p(y|z,x) 계산
        total_log_prob = []
        for k in range(self.top_k):
            logits = self.reader(
                combined_inputs[:, k], combined_masks[:, k],
                masked_positions
            )  # [batch, num_masks, vocab]
            token_log_probs = F.log_softmax(logits, dim=-1)
            target_log_probs = token_log_probs.gather(
                2, labels.unsqueeze(-1)
            ).squeeze(-1).sum(dim=-1)  # [batch]
            total_log_prob.append(
                log_retrieval_probs[:, k] + target_log_probs
            )

        # 3단계: 주변 우도(marginal likelihood) 계산
        # log p(y|x) = log sum_z p(z|x) * p(y|z,x)
        stacked = torch.stack(total_log_prob, dim=-1)  # [batch, top_k]
        log_marginal = torch.logsumexp(stacked, dim=-1)  # [batch]

        loss = -log_marginal.mean()
        return loss
```

위 코드에서 핵심적인 부분은 `forward` 메서드의 3단계 구조입니다. 검색 확률 $p(z|x)$와 예측 확률 $p(y|z,x)$를 로그 공간에서 합산한 후, `logsumexp`를 사용하여 주변 우도를 수치적으로 안정적으로 계산합니다. 실제 구현에서는 MIPS 인덱스를 활용한 효율적인 top-k 검색과 비동기 인덱스 갱신 로직이 추가되어야 합니다.

---

## 후속 연구와의 관계

| 논문 | 연도 | REALM과의 관계 |
|------|------|---------------|
| RAG (Lewis et al.) | 2020 | REALM의 추출형 QA 한계를 seq2seq 디코더(BART)로 극복하여 자유 형식 생성을 지원. 검색기 학습에는 DPR을 사용하여 사전학습 없이도 효과적인 검색 증강 생성을 달성 |
| DPR (Karpukhin et al.) | 2020 | REALM의 bi-encoder 검색기를 독립적으로 발전. 사전학습 없이 QA 쌍으로만 검색기를 학습하는 더 효율적인 방법을 제시 |
| FiD (Izacard & Grave) | 2021 | REALM의 단일 문서 참조 한계를 극복. 검색된 다수 문서를 Fusion-in-Decoder로 결합하여 multi-passage 추론을 강화 |
| RETRO (Borgeaud et al.) | 2022 | 검색 증강을 대규모 자기회귀 LM에 적용. 청크 단위 교차 어텐션(chunked cross-attention)을 도입하여 수조 토큰 규모의 검색 코퍼스를 활용 |
| Atlas (Izacard et al.) | 2022 | REALM + FiD 결합에 few-shot 학습 추가. 검색기-생성기 공동 학습을 고도화하여 64개 예제만으로 경쟁적 성능을 달성 |

REALM이 개척한 "사전학습 단계에서의 검색 통합"이라는 방향은 현재까지도 활발히 연구되고 있으며, 현대 RAG 시스템의 이론적 근간을 이루고 있습니다.
