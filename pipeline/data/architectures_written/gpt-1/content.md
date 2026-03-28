# GPT-1: Generative Pre-trained Transformer

## 개요

**GPT-1**(Generative Pre-trained Transformer)은 OpenAI가 2018년 6월 "Improving Language Understanding by Generative Pre-Training" 논문을 통해 발표한 모델이다. 이 모델은 **대규모 비지도 사전학습(unsupervised pre-training)**과 **지도 미세조정(supervised fine-tuning)**이라는 2단계 학습 패러다임을 제시하여, 이후 NLP 분야의 연구 방향을 근본적으로 변화시켰다.

GPT-1 이전의 NLP 연구는 태스크별로 특화된 아키텍처를 설계하고, 각 태스크에 맞는 레이블 데이터로 학습하는 방식이 주류였다. 하지만 레이블 데이터는 수집 비용이 높고 양이 제한적이라는 근본적인 한계가 있었다. GPT-1은 **방대한 비라벨 텍스트에서 범용적 언어 표현을 학습**한 뒤, 이를 특정 태스크에 전이하는 접근법으로 이 문제를 해결했다.

## 아키텍처 상세

![GPT-1 Transformer 디코더 아키텍처](figures/architecture.png)

*Figure 1: GPT-1의 12-layer Transformer Decoder 아키텍처와 태스크별 입력 변환 구조. (Radford et al., 2018)*

### Transformer 디코더 기반 구조

GPT-1은 Transformer의 **디코더 블록 12개**를 쌓은 구조다. 원래 Transformer의 Encoder-Decoder 구조에서 디코더 부분만을 활용했으며, Cross-Attention을 제거하고 **Causal(Masked) Self-Attention**만 사용한다.

주요 하이퍼파라미터:
- Hidden dimension: 768
- Attention heads: 12
- FFN inner dimension: 3072 (4배)
- Vocabulary: 40,000 (BPE)
- Context length: 512 토큰
- 총 파라미터: 117M

### 사전학습 목적함수: 자기회귀 언어 모델링 (Next Token Prediction)

GPT-1의 사전학습은 **다음 토큰 예측(Next Token Prediction)**이라는 자기회귀(autoregressive) 언어 모델링 목적함수를 사용한다. 입력 시퀀스 $\mathcal{U} = (u_1, \ldots, u_n)$에 대해 다음 토큰 예측 확률을 최대화한다:

$$L_1(\mathcal{U}) = \sum_i \log P(u_i \mid u_{i-k}, \ldots, u_{i-1}; \Theta)$$

여기서 $k$는 컨텍스트 윈도우 크기(512), $\Theta$는 모델 파라미터다.

이 목적함수의 핵심 아이디어는 단순하다. 모델이 이전에 등장한 토큰들의 문맥을 보고 다음에 올 토큰을 예측하는 과정을 반복하면서, 자연어의 통계적 구조를 학습한다는 것이다. 다음 토큰을 정확히 예측하려면 모델은 문법, 의미론, 상식 추론, 심지어 세계 지식까지 내재화해야 한다. 이처럼 단순한 목적함수가 풍부한 언어 표현을 학습시킬 수 있다는 것이 GPT 시리즈의 근본적 통찰이다.

### 비지도 사전학습 방법론

사전학습 데이터로는 **BooksCorpus** 데이터셋(약 7,000권의 미출판 도서, ~5GB 텍스트)을 사용했다. 이 데이터셋은 연속적인 긴 텍스트를 제공하여 모델이 장거리 의존성(long-range dependency)을 학습하는 데 적합했다.

학습 설정은 다음과 같다:
- **옵티마이저**: Adam (lr = 2.5e-4, 워밍업 후 코사인 감쇠)
- **배치 크기**: 64
- **에포크**: 약 100 에포크
- **정규화**: Dropout 0.1, Attention Dropout 0.1
- **활성화 함수**: GELU (당시로서는 비주류였으나 GPT-1이 채택하면서 후속 모델들의 표준이 됨)

주목할 점은 사전학습이 완전히 비지도(unsupervised)라는 것이다. 레이블이 필요 없으므로 웹에서 수집 가능한 방대한 텍스트를 그대로 활용할 수 있다. 이는 레이블 데이터 부족이라는 NLP의 고질적 문제를 우회하는 핵심 전략이었다.

### 미세조정 접근법

미세조정 시에는 태스크별 지도 학습 손실 $L_2$와 언어 모델링 손실 $L_1$을 결합한다:

$$L_3(\mathcal{C}) = L_2(\mathcal{C}) + \lambda \cdot L_1(\mathcal{C})$$

$\lambda = 0.5$로 설정하여, 미세조정 중에도 언어 모델링 능력을 유지하도록 했다. 이 **보조 목적함수(auxiliary objective)** 접근법은 미세조정의 수렴 속도를 높이고 일반화 성능을 개선하는 효과가 있었다.

미세조정의 구체적 절차는 다음과 같다:

1. **입력 변환**: 각 태스크의 입력을 연속 토큰 시퀀스로 변환 (아래 '태스크별 입력 변환' 참조)
2. **분류 헤드 추가**: 최종 Transformer 블록의 출력에 선형 레이어를 추가하여 태스크별 예측 수행
3. **학습**: 학습률 6.25e-5, 배치 크기 32로 약 3 에포크만 학습

미세조정에 필요한 학습 시간은 단일 GPU에서 수 시간 이내로, 매우 효율적이었다. 이는 사전학습된 표현이 이미 충분한 언어 지식을 내포하고 있기 때문이다. 미세조정에서 변경되는 파라미터는 사전학습된 Transformer의 전체 파라미터 + 태스크별 선형 헤드뿐이며, 별도의 태스크 특화 아키텍처가 필요 없다는 점이 핵심이다.

### 태스크별 입력 변환

GPT-1의 중요한 설계 결정은 다양한 태스크를 **최소한의 아키텍처 변경**으로 처리하는 것이다. 분류, 함의(entailment), 유사도, 다지선다 등의 태스크를 토큰 시퀀스 형태로 변환하여 동일한 모델에 입력한다:

- **분류**: `[시작] 텍스트 [추출]`
- **함의**: `[시작] 전제 [구분] 가설 [추출]`
- **유사도**: 두 방향 모두 입력 후 합산
- **다지선다**: 각 선택지별로 독립 인코딩

### PyTorch 구현 예시

```python
import torch
import torch.nn as nn

class GPT1Block(nn.Module):
    def __init__(self, d_model=768, n_heads=12, d_ff=3072, dropout=0.1):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout)
        )
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, attn_mask=None):
        # Post-Norm: LayerNorm(x + SubLayer(x))
        attn_out, _ = self.attn(x, x, x, attn_mask=attn_mask)
        x = self.ln1(x + self.dropout(attn_out))
        ffn_out = self.ffn(x)
        x = self.ln2(x + ffn_out)
        return x

class GPT1(nn.Module):
    def __init__(self, vocab_size=40000, d_model=768, n_layers=12, n_heads=12, max_len=512):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(max_len, d_model)  # Learned Absolute
        self.blocks = nn.ModuleList([GPT1Block(d_model, n_heads) for _ in range(n_layers)])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)

    def forward(self, x):
        B, T = x.shape
        pos = torch.arange(T, device=x.device).unsqueeze(0)
        h = self.tok_emb(x) + self.pos_emb(pos)
        mask = torch.triu(torch.ones(T, T, device=x.device), diagonal=1).bool()
        for block in self.blocks:
            h = block(h, attn_mask=mask)
        h = self.ln_f(h)
        return self.head(h)
```

## 핵심 혁신

### 1. 사전학습-미세조정 패러다임의 확립

GPT-1은 "비지도 사전학습 → 지도 미세조정"이라는 2단계 접근법을 대규모로 검증한 최초의 모델이다. 이 패러다임은 BERT와 함께 NLP 연구의 표준이 되었다.

### 2. Transformer 디코더의 언어 모델링 적용

기존 Transformer가 주로 Encoder-Decoder 구조로 번역에 사용된 것과 달리, GPT-1은 **디코더만으로 자기회귀적 언어 모델링**이 강력한 범용 표현을 학습할 수 있음을 보였다.

### 3. 최소 아키텍처 변경의 전이 학습

태스크마다 새로운 아키텍처를 설계하는 대신, **입력 형식만 변환**하여 동일한 모델로 다양한 태스크를 처리할 수 있음을 입증했다.

## 벤치마크/성능

| 벤치마크 | GPT-1 | 이전 SOTA | 개선폭 |
|---------|-------|----------|-------|
| GLUE 전체 | 72.8 | 68.9 | +3.9 |
| Story Cloze | 86.5 | 77.6 | +8.9 |
| RACE | 59.0 | 53.3 | +5.7 |
| MNLI | 82.1 | 80.6 | +1.5 |
| QNLI | 88.1 | 82.3 | +5.8 |
| QQP | 70.3 | 66.1 | +4.2 |

12개 벤치마크 태스크 중 **9개에서 SOTA**를 달성했다.

## 관련 모델 비교

| 특성 | ELMo (2018.02) | GPT-1 (2018.06) | BERT (2018.10) |
|------|---------------|----------------|----------------|
| 아키텍처 | BiLSTM | Transformer Decoder | Transformer Encoder |
| 방향성 | 양방향 (독립) | 단방향 (왼→오) | 양방향 (동시) |
| 사전학습 | LM | LM | MLM + NSP |
| 전이 방식 | Feature-based | Fine-tuning | Fine-tuning |
| 파라미터 | 94M | 117M | 110M/340M |
| GLUE | 66.5 | 72.8 | 80.2 |

### GPT-1 vs BERT: 사전학습 방식의 근본적 차이

GPT-1과 BERT는 같은 시기에 등장한 사전학습 모델이지만, 접근 방식이 근본적으로 다르다.

**GPT-1의 자기회귀 언어 모델링(Autoregressive LM)**은 왼쪽에서 오른쪽으로 순차적으로 다음 토큰을 예측한다. 각 토큰은 자신의 왼쪽 문맥만 참조할 수 있다. 이 방식은 텍스트 생성에 자연스럽지만, "오른쪽 문맥"을 볼 수 없다는 한계가 있다. 예를 들어 "나는 __ 먹었다"에서 빈칸을 채울 때, GPT-1은 "나는"이라는 왼쪽 문맥만 사용할 수 있다.

**BERT의 마스크드 언어 모델링(Masked LM)**은 입력 토큰의 15%를 무작위로 마스킹한 뒤, 양방향 문맥을 모두 활용하여 마스킹된 토큰을 예측한다. 위 예시에서 BERT는 "나는"과 "먹었다" 양쪽을 모두 참조할 수 있다. 이 차이가 NLI, QA 등 문맥 이해 태스크에서 BERT가 GPT-1을 능가한 주요 원인이다.

$$\text{GPT-1 (AR):} \quad P(x_t \mid x_{<t}) \qquad \text{vs} \qquad \text{BERT (MLM):} \quad P(x_t \mid x_{\neq t})$$

그러나 GPT-1의 단방향 접근은 텍스트 생성(generation)에 본질적으로 유리하며, 이는 이후 GPT-2, GPT-3를 거쳐 ChatGPT로 이어지는 생성형 AI 혁명의 기반이 되었다. BERT가 "이해(understanding)"에 강했다면, GPT 계열은 "생성(generation)"에서 압도적 우위를 점했고, 결국 생성 패러다임이 AI 산업을 주도하게 되었다.

### 최초의 GPT로서의 역사적 의의

GPT-1은 단순한 모델 하나를 넘어, **세 가지 핵심 아이디어의 출발점**이었다:

1. **스케일링 가설의 기원**: "모델을 키우고 데이터를 늘리면 성능이 좋아진다"는 직관을 117M이라는 (당시) 대규모 모델로 처음 실증했다. 이 가설은 GPT-2(1.5B) → GPT-3(175B) → GPT-4(~1.8T 추정)로 이어지는 급격한 스케일업의 근거가 되었다.
2. **제로샷/퓨샷 학습의 단초**: GPT-1 논문에서는 이미 사전학습만으로도 태스크 성능이 향상되는 "제로샷 행동(zero-shot behavior)"을 관찰했다. Transformer 레이어가 깊어질수록 다운스트림 태스크 성능이 꾸준히 증가하는 것을 확인했으며, 이는 모델이 사전학습 과정에서 태스크 관련 지식을 내재화함을 시사한다.
3. **범용 언어 모델의 가능성**: 하나의 사전학습된 모델로 분류, 함의, 유사도, 다지선다 등 이질적인 태스크를 처리할 수 있다는 것을 증명하며, "하나의 모델이 모든 것을 한다"는 Foundation Model 개념의 씨앗을 뿌렸다.

## 실무 활용

GPT-1 자체는 현재 직접 사용되는 경우가 드물지만, 그 설계 철학은 현대 NLP의 근간을 이룬다:

- **사전학습-미세조정 파이프라인**: 현재 모든 NLP 프로젝트의 표준 워크플로우
- **자기회귀 언어 모델링**: GPT-2, GPT-3, GPT-4로 이어지는 스케일링의 출발점
- **보조 목적함수 기법**: 멀티태스크 학습, 정규화 기법으로 확장

## 한계 및 전망

### 한계

1. **단방향 문맥만 활용**: 왼쪽에서 오른쪽으로만 읽으므로, 양방향 문맥이 필요한 태스크(NLI, QA 등)에서 BERT에 뒤처짐. 특히 두 문장 간 관계를 파악하는 자연어 추론(NLI)에서 이 한계가 두드러졌다.
2. **작은 학습 데이터**: BooksCorpus(~5GB, 약 8억 토큰)만 사용하여 데이터 다양성이 부족. 도서 데이터 위주로 뉴스, 위키, 코드, 대화 등 다른 도메인의 텍스트를 학습하지 못했다. 이후 GPT-2는 WebText(~40GB)를, GPT-3는 ~570GB의 필터링된 웹 데이터를 사용하며 이 한계를 극복했다.
3. **짧은 컨텍스트**: 512 토큰으로 긴 문서 처리에 한계. 일반적인 영문 문서 1~2페이지 분량에 해당하며, 논문, 법률 문서, 소설 등 긴 텍스트의 전체 맥락을 파악할 수 없다.
4. **제한된 스케일**: 117M 파라미터는 이후 모델들에 비해 매우 작은 규모. GPT-3(175B)의 약 1/1500 수준이며, 이로 인해 복잡한 추론이나 다단계 논리에서 성능이 제한적이다.
5. **생성 품질의 한계**: 117M 규모에서는 유창하고 일관된 긴 텍스트 생성이 어렵다. 몇 문장을 넘어가면 주제에서 벗어나거나 반복적인 패턴이 나타나는 경향이 있었다.
6. **BPE 토크나이저의 비효율**: 40,000 어휘 크기의 BPE 토크나이저는 비영어권 언어에서 특히 비효율적이었으며, 희귀 단어나 전문 용어 처리에 한계가 있었다.

### 전망

GPT-1은 "더 큰 모델, 더 많은 데이터, 더 긴 학습"이라는 스케일링 가설의 출발점이 되었다. GPT-2(1.5B), GPT-3(175B), GPT-4(~1.8T)로 이어지는 급격한 스케일업은 GPT-1이 제시한 방향의 직접적 연장선이다.

---

**참고 논문**: [Improving Language Understanding by Generative Pre-Training](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf) (Radford et al., 2018)

## 관련 문서

- [[transformer|Transformer]] — 발전 기반
- [[gpt-2|GPT-2]] — 후속 모델
