# GPT-J: RoPE와 Parallel Transformer의 선구자

## 개요

GPT-J-6B는 2021년 6월 EleutherAI가 공개한 6B 파라미터 오픈소스 자기회귀 언어 모델이다. GPT-J의 역사적 의의는 단순한 성능이 아니라 **두 가지 아키텍처 혁신**에 있다:

1. **RoPE(Rotary Position Embedding)**: 이후 LLaMA, PaLM, Mistral 등 거의 모든 현대 LLM이 채택한 위치 인코딩 표준을 대규모 모델에서 최초로 검증
2. **Parallel Transformer Block**: Attention과 FFN을 병렬로 계산하여 학습 속도를 15% 향상시킨 구조로, 이후 PaLM에서도 채택

이러한 기법들 덕분에 GPT-J는 단순한 "오픈소스 GPT-3 클론"을 넘어, 현대 LLM 아키텍처의 핵심 구성 요소를 선도한 모델로 평가받는다.

- **코드/논문**: [mesh-transformer-jax (GitHub)](https://github.com/kingoflolz/mesh-transformer-jax)
- **라이선스**: Apache 2.0

## 아키텍처 상세

| 구성 요소 | 값 |
|-----------|----|
| 파라미터 수 | 6B |
| 레이어 수 | 28 |
| Hidden Dim | 4,096 |
| Attention Heads | 16 |
| Head Dim | 256 |
| Vocab Size | 50,257 |
| Context Length | 2,048 |
| 정규화 | LayerNorm (Pre-Norm) |
| 활성화 함수 | GELU |
| 위치 인코딩 | **RoPE** |
| FFN 구조 | **Parallel Transformer Block** |

### RoPE (Rotary Position Embedding)

GPT-J가 대규모 모델에 처음으로 적용한 RoPE는 절대 위치 임베딩 대신 **회전 행렬(rotation matrix)**을 사용하여 상대적 위치 정보를 인코딩한다:

$$f(q, m) = q \cdot e^{im\theta}$$

여기서 $m$은 위치, $\theta$는 주파수이다. 2차원 단위로 분해하면:

$$\begin{pmatrix} q_{2k} \\ q_{2k+1} \end{pmatrix} \mapsto \begin{pmatrix} \cos(m\theta_k) & -\sin(m\theta_k) \\ \sin(m\theta_k) & \cos(m\theta_k) \end{pmatrix} \begin{pmatrix} q_{2k} \\ q_{2k+1} \end{pmatrix}$$

RoPE의 핵심 장점:
- **상대적 위치 인코딩**: 두 토큰의 내적이 자연스럽게 상대적 거리에 의존
- **길이 외삽**: 학습 시보다 긴 시퀀스에 대한 일반화 가능
- **학습 불필요**: 수학적으로 결정되어 추가 파라미터가 없음

### Parallel Transformer Block

기존 Sequential 구조와 GPT-J의 Parallel 구조를 비교하면:

**Sequential (기존)**:
$$x_{l+1} = x_l + \text{Attention}(\text{LN}(x_l))$$
$$x_{l+2} = x_{l+1} + \text{FFN}(\text{LN}(x_{l+1}))$$

**Parallel (GPT-J)**:
$$x_{l+1} = x_l + \text{Attention}(\text{LN}(x_l)) + \text{FFN}(\text{LN}(x_l))$$

Attention과 FFN을 **동시에 계산하고 합산**함으로써:
- GPU utilization 개선
- 통신 오버헤드 감소
- 약 **15% 학습 속도 향상** (동일 품질 유지)

```python
import torch
import torch.nn as nn

class ParallelTransformerBlock(nn.Module):
    """GPT-J의 Parallel Transformer Block"""
    def __init__(self, d_model, n_heads, d_ff):
        super().__init__()
        self.ln = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Linear(d_ff, d_model)
        )
    
    def forward(self, x):
        # Pre-Norm
        normed = self.ln(x)
        # Attention과 FFN을 병렬로 계산
        attn_out, _ = self.attn(normed, normed, normed)
        ffn_out = self.ffn(normed)
        # 합산
        return x + attn_out + ffn_out

# 사용 예시
block = ParallelTransformerBlock(d_model=4096, n_heads=16, d_ff=16384)
x = torch.randn(1, 512, 4096)
out = block(x)  # (1, 512, 4096)
```

## 벤치마크/성능

GPT-J-6B는 GPT-3 6.7B(Curie)에 근접한 성능을 보였다:

| 벤치마크 | GPT-J-6B | GPT-3 6.7B | GPT-Neo 2.7B |
|----------|----------|-----------|-------------|
| LAMBADA (acc) | **69.7%** | ~69% | 62.2% |
| HellaSwag | **66.1%** | ~67% | 55.8% |
| PIQA | **76.5%** | ~76% | 72.1% |
| Winogrande | **65.0%** | ~65% | 57.2% |
| ARC (Easy) | **67.0%** | ~68% | 61.1% |

### 핵심 결과
- GPT-3 6.7B(Curie)와 **거의 동등한 성능**
- GPT-Neo 2.7B 대비 **125% 학습 효율** 향상
- 코드 생성, 번역 등에서 GPT-3 수준의 성능
- 공개 당시 **가장 큰 오픈소스 GPT-3 아키텍처 모델**

## 관련 모델 비교

| 특성 | GPT-Neo 2.7B | GPT-J 6B | GPT-NeoX 20B | GPT-3 6.7B |
|------|-------------|----------|-------------|------------|
| 파라미터 | 2.7B | **6B** | 20B | 6.7B |
| 위치 인코딩 | Learned | **RoPE** | RoPE | Learned |
| Transformer Block | Sequential | **Parallel** | Parallel | Sequential |
| 어텐션 패턴 | Local+Global | Full | Full | Full |
| 오픈소스 | O | **O** | O | X |
| 학습 프레임워크 | JAX | JAX | PyTorch | - |

## 학습 상세

### 데이터셋
- **The Pile**: 825GB, 22개 소스 혼합 코퍼스
- 총 학습 토큰: **~402B**
- Wikipedia, arXiv, GitHub, PubMed, StackExchange 등

### 학습 설정
- Optimizer: Adam (lr = 6e-4)
- Warmup: 3,000 steps, cosine decay
- 토크나이저: GPT-2 BPE (50,257 vocab)
- 인프라: **Google TPU v3-256** (256 칩)
- 학습 기간: **약 5주**
- 학습 비용: **~$15,000-$20,000** (추정)
- 프레임워크: **JAX/Haiku** + mesh-transformer-jax

## 실무 활용

### 1. 코드 생성
GPT-J는 The Pile에 GitHub 코드가 포함되어 코드 생성에서 강력한 성능을 보인다.

### 2. 오픈소스 챗봇 기반
다수의 초기 오픈소스 챗봇(예: Pygmalion)이 GPT-J를 기반으로 파인튜닝되었다.

### 3. 엣지 디바이스 배포
6B 파라미터는 양자화를 통해 단일 GPU에서 구동 가능하여, 온프레미스 배포에 적합하다.

### 4. 아키텍처 연구
RoPE와 Parallel Block의 효과를 실증적으로 연구할 수 있는 적절한 규모의 모델이다.

## 한계 및 전망

### 한계
1. **6B 규모**: 현대 기준으로는 소형 모델에 속한다
2. **영어 중심**: 다국어 능력이 제한적이다
3. **정렬 미적용**: SFT/RLHF가 적용되지 않아 유해한 출력이 가능하다
4. **JAX 의존성**: PyTorch 생태계와의 호환성이 제한적이었다 (이후 변환됨)

### 전망
GPT-J는 **현대 LLM의 두 가지 핵심 구성 요소(RoPE, Parallel Block)를 대중화한 선구적 모델**이다. 직접적인 후속 모델은 GPT-NeoX(20B), Pythia 시리즈 등이며, 아키텍처적 영향은 LLaMA, PaLM, Falcon 등 거의 모든 현대 LLM으로 확대되었다. 특히 $15,000-$20,000이라는 상대적으로 저렴한 학습 비용은, 학술 기관과 스타트업도 의미 있는 LLM을 훈련할 수 있다는 가능성을 보여주었다.

---

**참고 문헌**
- Wang, B., & Komatsuzaki, A. (2021). "GPT-J-6B: A 6 Billion Parameter Autoregressive Language Model." mesh-transformer-jax.
- Su, J., et al. (2021). "RoFormer: Enhanced Transformer with Rotary Position Embedding."
- Chowdhery, A., et al. (2022). "PaLM: Scaling Language Modeling with Pathways." (Parallel Block 채택)

## 관련 문서

- [[gpt-neo|GPT-Neo]] — 발전 기반
