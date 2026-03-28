# XLNet: 순열 언어 모델링으로 BERT의 한계를 넘다

## 개요

XLNet은 2019년 6월 카네기 멜론 대학교(CMU)와 Google Brain이 공동으로 발표한 언어 모델로, 자기회귀(Autoregressive, AR) 방식과 BERT의 양방향 문맥 학습의 장점을 동시에 포착하는 **순열 언어 모델링(Permutation Language Modeling, PLM)** 패러다임을 제안했다.

BERT가 NLP 분야를 혁신한 이후, 연구자들은 BERT의 두 가지 근본적 한계를 인식했다:
1. **프리트레인·파인튜닝 불일치**: `[MASK]` 토큰은 사전 학습에만 존재하고 실제 입력에는 없다
2. **마스킹 토큰 간 독립성 가정**: 여러 `[MASK]`가 동시에 예측될 때 서로의 의존성을 무시한다

XLNet은 이 두 문제를 근본적으로 해결하면서, 총 18개 NLP 태스크에서 BERT를 능가하는 새로운 SOTA를 달성했다.

- **논문**: [XLNet: Generalized Autoregressive Pretraining for Language Understanding](https://arxiv.org/abs/1906.08237)
- **코드**: [GitHub](https://github.com/zihangdai/xlnet)
- **라이선스**: Apache 2.0

## 아키텍처 상세

다음 다이어그램은 XLNet의 전체 아키텍처를 보여준다. Permutation Language Modeling, Two-Stream Attention, Segment Recurrence가 핵심 구성 요소이다.

![XLNet 전체 아키텍처 다이어그램 - PLM, Two-Stream Attention, Transformer-XL 기반 구조](figures/architecture.png)
*Figure 1: XLNet 아키텍처 - 순열 언어 모델링으로 양방향 문맥을 학습하고, Two-Stream Attention으로 정보 누출을 방지하며, Transformer-XL의 세그먼트 반복으로 장거리 의존성을 포착한다. (Source: XLNet 논문)*

### 모델 규모

| 구성 요소 | XLNet-Base | XLNet-Large |
|-----------|-----------|-------------|
| 파라미터 수 | 110M | 340M |
| 레이어 수 | 12 | 24 |
| Hidden Dim | 768 | 1024 |
| Attention Heads | 12 | 16 |
| Vocab Size | 32,000 | 32,000 |
| Context Length | 512 | 512 (+ 세그먼트 반복) |

### Transformer-XL 백본

XLNet은 Transformer-XL을 백본으로 사용한다. 핵심은 **세그먼트 반복(Segment Recurrence)** 메커니즘으로, 이전 세그먼트의 히든 스테이트를 캐시에 저장하고 다음 세그먼트 처리 시 재활용한다:

$$h_{\tau+1}^{(n)} = \text{TransformerLayer}\left([\widetilde{h}_{\tau}^{(n-1)} \circ h_{\tau+1}^{(n-1)}], \theta\right)$$

여기서 $\widetilde{h}_{\tau}^{(n-1)}$는 이전 세그먼트의 캐시된 히든 스테이트이다. 이를 통해 효과적 컨텍스트 길이가 2048 토큰 이상으로 확장된다.

### 상대 위치 인코딩

Transformer-XL의 **상대 위치 인코딩(Relative Position Encoding)**을 사용하여, 절대 위치가 아닌 토큰 간 상대적 거리를 인코딩한다. 이는 길이 일반화(length generalization)에 유리하다.

## 핵심 혁신: 순열 언어 모델링과 Two-Stream Attention

### 순열 언어 모델링 (PLM)

길이 $T$의 시퀀스에 대해 가능한 모든 순열 $\mathcal{Z}_T$ ($T!$가지) 중 하나를 샘플링하여, 해당 순서로 다음 토큰을 예측한다:

$$\max_{\theta} \; \mathbb{E}_{\mathbf{z} \sim \mathcal{Z}_T} \left[ \sum_{t=1}^{T} \log p_{\theta}(x_{z_t} \mid \mathbf{x}_{\mathbf{z}_{<t}}) \right]$$

이 방식은 AR 목적 함수를 유지하면서 양방향 문맥을 학습한다. 예를 들어 시퀀스 [A, B, C, D]에서 순열 [3, 1, 4, 2]가 샘플링되면:
- C를 먼저 예측 (문맥 없음)
- A를 예측 (C를 참조)
- D를 예측 (C, A를 참조)
- B를 예측 (C, A, D를 참조 = 양방향 문맥!)

다음 그림은 동일한 시퀀스 [x1, x2, x3, x4]에서 x3을 예측할 때, 서로 다른 분해 순서(factorization order)에 따라 참조하는 문맥이 달라지는 과정을 보여준다.

![순열 언어 모델링 - 4가지 분해 순서에 따른 x3 예측 과정](figures/fig_11.png)
*Figure 2: 순열 언어 모델링 예시 - 동일한 x3을 예측하지만, 분해 순서에 따라 참조 가능한 토큰이 달라진다. 이를 통해 자기회귀 방식으로도 양방향 문맥 학습이 가능해진다. (Source: XLNet 논문)*

### Two-Stream Self-Attention

PLM을 구현하려면 예측 시 **정보 누출(information leakage)**을 방지해야 한다. 이를 위해 두 가지 스트림을 병렬로 유지한다:

**1. Content Stream** $h_{z_t}^{(m)}$: 위치와 내용 모두 인식
$$h_{z_t}^{(m)} \leftarrow \text{Attention}(Q=h_{z_t}^{(m-1)}, KV=h_{\mathbf{z}_{\leq t}}^{(m-1)})$$

**2. Query Stream** $g_{z_t}^{(m)}$: 위치만 알고 내용은 모름
$$g_{z_t}^{(m)} \leftarrow \text{Attention}(Q=g_{z_t}^{(m-1)}, KV=h_{\mathbf{z}_{<t}}^{(m-1)})$$

아래 그림은 Two-Stream Attention의 전체 구조를 시각화한 것이다. (a) Content Stream, (b) Query Stream, (c) 전체 PLM 학습 과정과 어텐션 마스크를 함께 보여준다.

![Two-Stream Self-Attention 구조 - Content Stream, Query Stream, 전체 PLM 흐름](figures/fig_1.png)
*Figure 3: Two-Stream Self-Attention - (a) Content Stream은 자기 자신을 포함한 모든 토큰을 참조하고, (b) Query Stream은 자기 자신의 내용을 제외하고 위치 정보만 사용한다. (c) 전체 PLM 학습 흐름과 어텐션 마스크. (Source: XLNet 논문)*

```python
import torch
import torch.nn as nn

class TwoStreamAttention(nn.Module):
    """XLNet의 Two-Stream Self-Attention 개념적 구현"""
    def __init__(self, d_model, n_heads):
        super().__init__()
        self.content_attn = nn.MultiheadAttention(d_model, n_heads)
        self.query_attn = nn.MultiheadAttention(d_model, n_heads)
    
    def forward(self, h, g, perm_mask):
        # Content Stream: 위치와 내용 모두 참조
        h_new, _ = self.content_attn(h, h, h, attn_mask=perm_mask)
        # Query Stream: 위치만 참조, 자기 자신의 내용은 제외
        g_new, _ = self.query_attn(g, h, h, attn_mask=perm_mask)
        return h_new, g_new
```

## 벤치마크/성능

XLNet-Large는 발표 당시 18개 태스크에서 BERT를 능가했다:

| 벤치마크 | 메트릭 | BERT-Large | XLNet-Large | 향상 |
|----------|--------|-----------|-------------|------|
| GLUE | Score | 82.1 | **88.4** | +6.3 |
| SQuAD 2.0 | EM | 80.0 | **87.9** | +7.9 |
| SQuAD 2.0 | F1 | 83.1 | **89.8** | +6.7 |
| RACE (Reading) | Accuracy | 72.0 | **81.8** | +9.8 |
| MNLI | Accuracy | 86.6 | **90.8** | +4.2 |
| SST-2 | Accuracy | 94.9 | **96.8** | +1.9 |

GLUE 88.4점은 당시 인간 성능(87.1)을 1.3포인트 초과하는 기록이었다.

다음은 XLNet의 Content Stream이 순열 [3, 2, 4, 1]에서 각 위치별로 어떤 토큰들을 참조하는지를 상세히 보여주는 그림이다.

![Content Stream의 Joint View와 Split View - 순열 순서에 따른 어텐션 연결 상세](figures/fig_12.png)
*Figure 4: Content Stream 상세 - 분해 순서 [3, 2, 4, 1]에서 각 위치의 Content Stream이 참조하는 토큰들의 관계를 Joint View(상단)와 개별 Position View(하단)로 분리하여 보여준다. (Source: XLNet 논문)*

## 관련 모델 비교

| 특성 | BERT | GPT-2 | XLNet | RoBERTa |
|------|------|-------|-------|---------|
| 학습 목표 | MLM | AR LM | Permutation LM | MLM |
| 양방향 문맥 | O (마스킹) | X | O (순열) | O (마스킹) |
| [MASK] 사용 | O | X | **X** | O |
| 토큰 간 의존성 | 독립 | 순차 | **순차** | 독립 |
| 장거리 의존성 | 512 | 1024 | **2048+** | 512 |
| 위치 인코딩 | 절대 | 절대 | **상대** | 절대 |

## 학습 상세

### 데이터셋
- BooksCorpus + Wikipedia + Giga5 + ClueWeb 09-B + Common Crawl
- 총 **126GB**

### 학습 설정
- 토크나이저: SentencePiece (32,000 vocab)
- 배치 크기: 8,192
- Optimizer: Adam (lr = 1e-4)
- Warmup: 20K 스텝, linear warmup
- 인프라: **512 TPU v3**, 약 32일 학습 (Large)
- 메모리 절감: recomputation(gradient checkpointing) 사용

## 실무 활용

### 1. 자연어 이해 태스크
GLUE/SuperGLUE 스타일의 분류·추론 태스크에서 뛰어난 성능을 발휘한다.

### 2. 질의 응답
SQuAD 2.0에서의 우수한 성능은 실무 QA 시스템에 직접 적용 가능하다.

### 3. 독해 이해
RACE 등 긴 문맥 독해 태스크에서 Transformer-XL 기반 장거리 의존성 포착 능력이 빛난다.

### 4. 감정 분석
SST-2에서 96.8%의 정확도는 상업적 감정 분석 파이프라인에 충분한 수준이다.

## 한계 및 전망

### 한계
1. **높은 학습 비용**: 512 TPU v3에서 32일이라는 막대한 학습 자원이 필요하다
2. **복잡한 구현**: Two-Stream Attention과 순열 마스크의 구현이 복잡하다
3. **추론 속도**: 두 스트림을 유지해야 하므로 BERT 대비 추론이 느리다
4. **Encoder-only 한계**: 생성 태스크에는 적합하지 않다

### 전망
XLNet이 제시한 핵심 통찰-AR 방식으로도 양방향 문맥을 학습할 수 있다-은 이후 연구에 큰 영향을 미쳤다. 직접적으로 XLNet 아키텍처를 계승한 모델은 많지 않지만, PLM의 개념은 UniLM 등 통합 언어 모델 연구에 영감을 주었으며, Transformer-XL의 상대 위치 인코딩은 이후 RoPE, ALiBi 등 현대 위치 인코딩 기법의 토대가 되었다.

---

**참고 문헌**
- Yang, Z., et al. (2019). "XLNet: Generalized Autoregressive Pretraining for Language Understanding." NeurIPS 2019.
- Dai, Z., et al. (2019). "Transformer-XL: Attentive Language Models Beyond a Fixed-Length Context."
- Devlin, J., et al. (2018). "BERT: Pre-training of Deep Bidirectional Transformers."

## 관련 문서

- [[transformer|Transformer]] - 발전 기반
- [[bert|BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding]] - 영감
