# GPT-Neo: 오픈소스 LLM 생태계의 시발점

## 개요

GPT-Neo는 2021년 3월 EleutherAI가 공개한 오픈소스 자기회귀 언어 모델 시리즈다. 이 모델의 탄생 배경을 이해하려면 당시의 시대적 맥락을 알아야 한다: 2020년 GPT-3가 발표된 후, 175B 파라미터의 강력한 모델은 OpenAI API를 통해서만 제한적으로 접근 가능했다. **"왜 가장 중요한 AI 기술이 한 회사에 의해 독점되어야 하는가?"**라는 질문에 답하기 위해, 전 세계 자원봉사 연구자들이 모여 EleutherAI를 결성하고 GPT-Neo를 만들었다.

125M, 1.3B, 2.7B 세 가지 크기로 공개된 GPT-Neo는 성능보다는 **"오픈소스로도 대규모 언어 모델을 만들 수 있다"**는 증명 자체가 목적이었다.

- **코드**: [GitHub](https://github.com/EleutherAI/gpt-neo)
- **라이선스**: Apache 2.0

아래 다이어그램은 GPT-Neo의 전체 아키텍처와 Local+Global Attention 교대 패턴을 보여준다.

![GPT-Neo 아키텍처 - Local+Global Attention 교대 패턴 기반 Transformer](figures/architecture.png)
*Figure 1: GPT-Neo 아키텍처(125M/1.3B/2.7B) - Local(짝수)과 Global(홀수) Attention을 교대 적용하는 Sparse Transformer 구조, MHA 확장 구조, 그리고 3가지 모델 변형. (EleutherAI, 2021)*

## 아키텍처 상세

### 모델 규모

| 구성 요소 | GPT-Neo 125M | GPT-Neo 1.3B | GPT-Neo 2.7B |
|-----------|-------------|-------------|-------------|
| 파라미터 수 | 125M | 1.3B | 2.7B |
| 레이어 수 | 12 | 24 | 32 |
| Hidden Dim | 768 | 2,048 | 2,560 |
| Attention Heads | 12 | 16 | 20 |
| Head Dim | 64 | 128 | 128 |
| Context Length | 2,048 | 2,048 | 2,048 |

공통 설정:
- **Vocab Size**: 50,257 (GPT-2 BPE)
- **정규화**: Pre-LayerNorm
- **활성화 함수**: GELU
- **위치 인코딩**: Learned Absolute

### 핵심 혁신: Local + Global Attention 교대 패턴

GPT-Neo의 가장 중요한 아키텍처 혁신은 Sparse Transformer(Child et al., 2019)에서 영감을 받은 **Local과 Global Attention의 교대 적용**이다:

**짝수 레이어 - Local Attention**:
$$\text{Attention}_{\text{local}}(Q,K,V) = \text{softmax}\left(\frac{QK^T_{\text{window}}}{\sqrt{d_k}}\right)V_{\text{window}}$$

각 토큰이 좌측 256개 토큰만 참조하며, 복잡도는 $O(n \cdot w)$ (w=256)이다.

**홀수 레이어 - Global Attention**:
표준 causal mask를 적용한 전체 어텐션으로, 복잡도는 $O(n^2)$이다.

이 교대 패턴의 이점:
- **로컬 레이어**: 인접 토큰 간 세밀한 구문적 관계 포착
- **글로벌 레이어**: 문서 수준의 장거리 의존성과 전역적 문맥 통합
- **메모리 효율**: GPT-2/3의 순수 글로벌 어텐션 대비 메모리 절감
- **성능 유지**: Longformer처럼 완전 로컬만 사용하는 것보다 장거리 의존성을 잘 포착

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class LocalAttention(nn.Module):
    """GPT-Neo의 Local Attention (window_size=256)"""
    def __init__(self, d_model, n_heads, window_size=256):
        super().__init__()
        self.n_heads = n_heads
        self.window_size = window_size
        self.d_k = d_model // n_heads
        self.qkv = nn.Linear(d_model, 3 * d_model)
        self.proj = nn.Linear(d_model, d_model)
    
    def forward(self, x):
        B, T, C = x.shape
        qkv = self.qkv(x).reshape(B, T, 3, self.n_heads, self.d_k)
        q, k, v = qkv.unbind(dim=2)
        
        # Local windowed attention mask
        # 각 토큰은 좌측 window_size 토큰만 참조
        mask = torch.ones(T, T, device=x.device).triu(diagonal=1).bool()
        local_mask = torch.ones(T, T, device=x.device).tril(
            diagonal=-(self.window_size + 1)
        ).bool()
        mask = mask | local_mask  # causal + local window
        
        attn = torch.einsum('bthd,bshd->bhts', q, k) / (self.d_k ** 0.5)
        attn = attn.masked_fill(mask.unsqueeze(0).unsqueeze(0), float('-inf'))
        attn = F.softmax(attn, dim=-1)
        
        out = torch.einsum('bhts,bshd->bthd', attn, v)
        out = out.reshape(B, T, C)
        return self.proj(out)
```

다음 다이어그램은 Local+Global Attention 교대 패턴의 상세 작동 원리를 보여준다. 레이어별 어텐션 마스크 비교, 복잡도 분석, 그리고 효과적 수용 영역(receptive field)의 확장을 시각화한다.

![GPT-Neo Local+Global Alternating Attention 상세 - 어텐션 마스크 비교와 복잡도 분석](figures/detail.png)
*Figure 2: GPT-Neo Local+Global Attention 상세 - 짝수 레이어의 Local Attention(window=256)과 홀수 레이어의 Global Attention 마스크 비교, 복잡도 분석($O(n \cdot w)$ vs $O(n^2)$), 그리고 교대 패턴을 통한 효과적 수용 영역 확장. (EleutherAI, 2021)*

## 벤치마크/성능

| 벤치마크 | GPT-Neo 125M | GPT-Neo 1.3B | GPT-Neo 2.7B |
|----------|-------------|-------------|-------------|
| Pile BPB | 0.7527 | - | 0.7165 |
| Pile PPL | 6.159 | - | 5.646 |
| LAMBADA (acc) | - | 57.2% | 62.2% |
| LAMBADA (PPL) | - | 7.50 | 5.63 |
| WikiText PPL | 13.10 | - | 11.39 |

### GPT-3와의 비교 (유사 규모)

| 모델 | 파라미터 | LAMBADA (acc) | HellaSwag |
|------|---------|--------------|----------|
| GPT-3 125M | 125M | 42.7% | 33.7% |
| GPT-Neo 125M | 125M | ~43% | ~34% |
| GPT-3 2.7B | 2.7B | 67.1% | 55.8% |
| GPT-Neo 2.7B | 2.7B | 62.2% | 55.8% |

GPT-Neo는 동일 규모의 GPT-3와 비교했을 때 **근접한 성능**을 보여주었으나, LAMBADA에서 약간의 차이가 있었다.

## 관련 모델 비교

| 특성 | GPT-2 | GPT-Neo | GPT-J | GPT-NeoX |
|------|-------|---------|-------|----------|
| 파라미터 | 1.5B | 2.7B | 6B | 20B |
| 어텐션 | Global | **Local+Global** | Global | Global |
| 위치 인코딩 | Learned | Learned | RoPE | RoPE |
| 학습 데이터 | WebText | The Pile | The Pile | The Pile |
| 프레임워크 | TF | JAX | JAX | PyTorch |
| 출시 | 2019 | **2021.03** | 2021.06 | 2022.04 |

## 학습 상세

### The Pile 데이터셋
EleutherAI가 자체 구축한 825GB (약 300B 토큰) 코퍼스:
- Wikipedia, arXiv, GitHub, PubMed, StackExchange 등 **22개 도메인**
- 단일 도메인 편향을 줄이기 위한 다양한 소스 혼합

### 학습 설정
- 토크나이저: GPT-2 BPE (50,257 vocab) 재사용
- 인프라: **Google TPU Research Cloud (TRC)** 프로그램
- TPU v3-256 Pod
- 프레임워크: JAX 기반 Mesh Transformer
- 학습 토큰:
  - 2.7B: ~420B 토큰 (The Pile 1.4 에폭)
  - 1.3B: ~380B 토큰
  - 125M: ~300B 토큰

## 실무 활용

### 1. 오픈소스 NLP 연구 기반
GPT-Neo는 오픈소스 LLM 연구의 초기 기반으로, 수많은 파인튜닝 연구에 활용되었다.

### 2. 텍스트 생성
Hugging Face를 통해 쉽게 접근 가능하며, 간단한 텍스트 생성 태스크에 활용 가능하다.

### 3. 스케일링 법칙 연구
125M/1.3B/2.7B 세 가지 크기로 제공되어 스케일링 효과를 연구하기에 적합하다.

### 4. 아키텍처 비교 연구
Local+Global Attention 패턴의 효과를 실증적으로 비교할 수 있는 모델이다.

## 한계 및 전망

### 한계
1. **제한된 규모**: 2.7B가 최대로, 대형 모델의 emergent abilities를 관찰하기 어렵다
2. **성능 격차**: 동일 규모 GPT-3 대비 일부 태스크에서 성능 차이가 존재한다
3. **영어 전용**: 다국어 지원이 없다
4. **아키텍처 한계**: Learned position embedding으로 길이 외삽이 제한적이다

### 전망
GPT-Neo의 진정한 유산은 성능이 아닌 **운동(movement)**에 있다. "오픈소스로도 대형 언어 모델을 만들 수 있다"는 것을 증명함으로써, GPT-J(6B), GPT-NeoX(20B), Pythia 시리즈 등 EleutherAI 후속 모델의 아키텍처적 기반이 되었고, 더 나아가 LLaMA, Falcon, Mistral 등 오픈소스 LLM 생태계 전체의 시발점이 되었다. The Pile 데이터셋과 Apache 2.0 라이선스로의 완전 공개는 이후 오픈소스 모델 공개 트렌드에 직접적인 영향을 미쳤다.

---

**참고 문헌**
- Black, S., et al. (2021). "GPT-Neo: Large Scale Autoregressive Language Modeling with Mesh-Tensorflow." EleutherAI.
- Gao, L., et al. (2020). "The Pile: An 800GB Dataset of Diverse Text for Language Modeling."
- Child, R., et al. (2019). "Generating Long Sequences with Sparse Transformers."

## 관련 문서

- [[gpt-j|GPT-J]] - 후속 모델
- [[gpt-2|GPT-2]] - 영감
