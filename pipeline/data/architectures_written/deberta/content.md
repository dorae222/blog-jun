# DeBERTa: 분리 어텐션으로 BERT를 넘어선 인코더 모델

## 1. 개요

DeBERTa(Decoding-enhanced BERT with Disentangled Attention)는 2021년 Microsoft Research가 발표한 사전 학습 언어 모델이다. BERT 계열 모델들이 토큰의 **내용(content)**과 **위치(position)** 정보를 하나의 벡터로 합산하여 어텐션을 계산하는 방식의 한계를 지적하고, 이 두 정보를 **분리된(disentangled) 행렬**로 처리하는 혁신적인 어텐션 메커니즘을 제안했다.

DeBERTa의 등장은 BERT → RoBERTa → ALBERT → ELECTRA로 이어지던 인코더 모델 진화 계보에서 결정적인 전환점이 되었다. 특히 SuperGLUE 벤치마크에서 **인간 성능(89.8점)을 최초로 넘는 90.3점**을 기록하며, NLU(Natural Language Understanding) 분야에서 슈퍼휴먼 성능의 시대를 열었다.

- **논문**: [DeBERTa: Decoding-enhanced BERT with Disentangled Attention](https://arxiv.org/abs/2006.03654)
- **조직**: Microsoft Research
- **공개일**: 2021년 6월
- **라이선스**: MIT

## 2. 아키텍처 상세

다음 다이어그램은 DeBERTa의 전체 아키텍처를 보여준다. Disentangled Attention과 Enhanced Mask Decoder가 핵심 구성 요소이다.

![DeBERTa 전체 아키텍처 다이어그램 — Disentangled Attention과 Enhanced Mask Decoder 구조](figures/architecture.png)
*Figure 1: DeBERTa 아키텍처 — 내용(content)과 위치(position) 벡터를 분리하여 어텐션을 계산하고, 최상위 레이어에서 EMD를 통해 절대 위치를 주입하는 구조. (Source: DeBERTa 논문)*

### 2.1 Disentangled Attention 메커니즘

BERT에서 각 토큰의 표현은 다음과 같이 내용 임베딩과 위치 임베딩의 합으로 구성된다:

$$H_i = E(x_i) + P(i)$$

이 합산된 벡터로 어텐션을 계산하면, 내용과 위치 정보가 뒤섞여 모델이 "어떤 내용이 어떤 위치에 있을 때 중요한지"를 세밀하게 학습하기 어렵다.

DeBERTa는 이를 근본적으로 해결한다. 각 토큰은 **두 개의 독립 벡터**를 유지한다:
- **내용 벡터** $H_i^c$: 토큰의 의미 정보
- **위치 벡터** $P_{i|j}^r$: 상대적 위치 정보

어텐션 스코어는 세 개의 항으로 분해된다:

$$A_{ij} = \underbrace{H_i^c W_q^c (H_j^c W_k^c)^T}_{\text{content-to-content}} + \underbrace{H_i^c W_q^c (P_{i|j} W_k^p)^T}_{\text{content-to-position}} + \underbrace{P_{i|j} W_q^p (H_j^c W_k^c)^T}_{\text{position-to-content}}$$

| 항 | 의미 | 예시 |
|---|---|---|
| $A_{c2c}$ | 내용 간 유사도 | "고양이"와 "동물"의 의미적 관련성 |
| $A_{c2p}$ | 내용이 특정 위치를 주목 | 주어가 바로 다음 동사 위치에 주목 |
| $A_{p2c}$ | 위치가 특정 내용을 주목 | 문장 첫 위치가 주어 역할 토큰에 주목 |

주목할 점은 **position-to-position($A_{p2p}$) 항은 제거**했다는 것이다. 실험적으로 이 항은 성능 기여가 미미하여 효율성을 위해 생략되었다.

### 2.2 Enhanced Mask Decoder (EMD)

Disentangled Attention은 사전 학습 중 상대 위치만 사용하므로, **절대 위치 정보가 손실**될 수 있다. 예를 들어 "Store" 다음에 빈칸이 올 때, "is"인지 "was"인지 판단하려면 문장 내 절대 위치(주어 위치, 시제 위치 등)가 필요하다.

아래 그림은 기존 BERT 디코딩 레이어와 DeBERTa의 Enhanced Mask Decoder를 비교한 것이다.

![BERT 디코딩 레이어 — 히든 상태 H로부터 Q, K, V를 직접 생성하는 표준 구조](figures/fig_5.png)
*Figure 2: (a) BERT 디코딩 레이어 — 히든 상태 H에서 Q, K, V를 생성하여 Language Model Head로 전달하는 단순한 구조. (Source: DeBERTa 논문)*

![DeBERTa의 Enhanced Mask Decoder — 절대 위치 정보 I를 추가로 주입하여 Query를 생성하는 구조](figures/fig_6.png)
*Figure 3: (b) Enhanced Mask Decoder — 절대 위치 임베딩 I를 별도로 주입하여 Query를 구성하고, n번 반복하여 디코딩 정확도를 높이는 구조. (Source: DeBERTa 논문)*

EMD는 이 문제를 해결하기 위해 **최상위 Transformer 레이어 이후에 절대 위치 임베딩을 주입**한다:

$$H_{\text{final}} = \text{EMD}(H_{\text{top}}, P_{\text{abs}})$$

이 방식은 모델이 상대 위치로 대부분의 문맥을 학습한 뒤, 마지막 디코딩 단계에서만 절대 위치를 참조하므로 두 정보의 간섭을 최소화한다.

### 2.3 모델 스펙

| 구성 | Base | Large | XL |
|---|---|---|---|
| 파라미터 | 86M | 350M | 1.5B |
| 히든 차원 | 768 | 1024 | 1536 |
| 레이어 수 | 12 | 24 | 24 |
| 어텐션 헤드 | 12 | 16 | 24 |
| 어휘 크기 | 128,100 | 128,100 | 128,100 |
| 컨텍스트 | 512 | 512 | 512 |

## 3. 핵심 혁신

### 3.1 위치 인코딩의 패러다임 전환

BERT 이후 위치 인코딩 방식의 진화를 살펴보면:

| 모델 | 위치 인코딩 방식 | 특징 |
|---|---|---|
| BERT | Learned Absolute | 학습 가능 절대 위치 |
| Transformer-XL | Relative Bias | 상대 위치 편향 |
| T5 | Relative Attention Bias | 버킷 기반 상대 위치 |
| **DeBERTa** | **Disentangled Relative** | **내용/위치 완전 분리** |
| RoPE (LLaMA) | Rotary Embedding | 회전 행렬 기반 상대 위치 |

DeBERTa의 분리 어텐션은 이후 RoPE 등 현대적 위치 인코딩 설계에도 영향을 미쳤다.

### 3.2 DeBERTaV3: ELECTRA와의 결합

DeBERTaV3는 ELECTRA의 RTD(Replaced Token Detection) 사전 학습 방식을 DeBERTa에 결합한 버전이다. MLM 대신 생성기가 만든 대체 토큰을 판별하는 방식으로, 모든 토큰 위치에서 학습 신호를 받아 효율이 크게 향상된다.

```python
# DeBERTaV3 사용 예시 (HuggingFace)
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-base")
model = AutoModel.from_pretrained("microsoft/deberta-v3-base")

inputs = tokenizer("DeBERTa는 분리 어텐션을 사용합니다.", return_tensors="pt")
outputs = model(**inputs)
# outputs.last_hidden_state: [batch, seq_len, 768]
```

## 4. 벤치마크 및 성능

### 4.1 SuperGLUE 결과

| 모델 | SuperGLUE | MNLI | SQuAD 2.0 |
|---|---|---|---|
| BERT-Large | 78.3 | 86.7 | 83.1 |
| RoBERTa-Large | 84.6 | 90.2 | 89.4 |
| ELECTRA-Large | 88.0 | 90.9 | - |
| **DeBERTa-Large** | **90.3** | **91.1** | **90.7** |
| 인간 성능 | 89.8 | - | 89.5 |

DeBERTa는 SuperGLUE에서 인간 기준선을 **0.5점 초과**하며 최초의 슈퍼휴먼 NLU 성능을 달성했다.

다음 그래프는 사전 학습 스텝 수에 따른 MNLI 정확도 변화를 보여준다. DeBERTa가 동일 학습량 대비 일관되게 높은 성능을 달성하는 것을 확인할 수 있다.

![사전 학습 스텝에 따른 MNLI 정확도 비교 — DeBERTa vs RoBERTa vs XLNet](figures/fig_1_1.png)
*Figure 4: MNLI 개발 세트 정확도 — DeBERTa(Base)가 RoBERTa, XLNet 대비 모든 학습 스텝에서 우위를 보이며, RoBERTa-ReImp보다도 빠르게 수렴한다. (Source: DeBERTa 논문)*

### 4.2 학습 효율

동일 파라미터 수(350M) 기준, DeBERTa-Large는 RoBERTa-Large 대비:
- SuperGLUE: +5.7점
- SQuAD 2.0: +1.3점
- MNLI: +0.9점

을 기록하며, 분리 어텐션의 효과를 실증했다.

다음은 DeBERTa와 RoBERTa 및 DeBERTa 변형 모델들의 어텐션 패턴을 비교한 것이다. 분리 어텐션의 각 구성 요소가 어텐션 분포에 미치는 영향을 시각적으로 확인할 수 있다.

![DeBERTa, RoBERTa, DeBERTa 변형 모델의 마지막 레이어 어텐션 패턴 비교 히트맵](figures/fig_7.png)
*Figure 5: 마지막 레이어 어텐션 패턴 비교 — DeBERTa(전체), RoBERTa, EMD 제거 버전, C2P 제거 버전, P2C 제거 버전 순서로 비교. DeBERTa가 가장 선명하고 구조화된 어텐션 패턴을 보인다. (Source: DeBERTa 논문)*

## 5. 관련 모델 비교

| 특성 | BERT | RoBERTa | ELECTRA | DeBERTa |
|---|---|---|---|---|
| 위치 인코딩 | 절대 | 절대 | 절대 | **분리 상대** |
| 사전 학습 | MLM+NSP | MLM(동적) | RTD | MLM → V3:RTD |
| 학습 신호 활용 | 15% | 15% | 100% | 15% → V3:100% |
| SuperGLUE | 78.3 | 84.6 | 88.0 | **90.3** |
| 핵심 기여 | 양방향 사전학습 | 학습 레시피 최적화 | 효율적 사전학습 | **어텐션 구조 혁신** |

## 6. 학습 상세

- **데이터**: 78GB (Wikipedia, BooksCorpus, OpenWebText, CC-News, Stories)
- **배치 크기**: 2,048
- **옵티마이저**: Adam (lr=1e-4)
- **학습 스텝**: 500K
- **하드웨어**: XL/XXL은 64 A100 GPU
- **DeBERTaV3**: ELECTRA RTD 방식 결합

## 7. 한계 및 전망

### 한계

1. **컨텍스트 길이 제한**: 512 토큰으로 고정되어 있어 긴 문서 처리에 한계가 있다. 현대 LLM의 128K+ 컨텍스트와 비교하면 매우 짧다.
2. **인코더 전용 구조**: 생성(generation) 태스크에는 적합하지 않으며, 분류/추출 태스크에 특화되어 있다.
3. **분리 어텐션의 오버헤드**: 세 개의 어텐션 항을 계산해야 하므로 표준 어텐션 대비 연산량이 약 1.5배 증가한다.

### 전망

DeBERTa의 핵심 통찰인 "내용과 위치 정보의 분리"는 현대 LLM 설계에도 계속 영향을 미치고 있다:

- **RoPE**의 회전 행렬 기반 상대 위치 인코딩은 DeBERTa의 분리 철학을 계승
- **DeBERTaV3-base**는 2026년 현재에도 GLUE/SuperGLUE 파인튜닝 태스크의 실질적 표준 베이스라인
- 분류, NER, 질의응답 등 **판별적(discriminative) NLU 태스크**에서는 여전히 최고 수준의 성능-효율 비를 제공

DeBERTa는 "더 큰 모델이 더 좋다"는 단순한 스케일링 접근을 넘어, **어텐션 메커니즘 자체의 구조적 개선**이 얼마나 큰 성능 향상을 가져올 수 있는지를 보여준 모범 사례로 남아 있다.

## 관련 문서

- [[bert|BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding]] — 발전 기반
