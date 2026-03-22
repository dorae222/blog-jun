---
title: "LLaMA: Open and Efficient Foundation Language Models"
slug: llama
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.488027+00:00"
architecture_entry: llama
---

## 개요

LLaMA(Large Language Model Meta AI)는 Meta AI가 2023년 2월 발표한 오픈소스 기반 언어 모델 시리즈다. 7B, 13B, 33B, 65B 네 가지 크기로 공개되었으며, 모두 **공개적으로 접근 가능한 데이터만**으로 학습되었다. LLaMA의 가장 중요한 기여는 작은 모델로 큰 모델을 능가하는 성능을 보여준 것이다. LLaMA-65B는 GPT-3(175B)와 Chinchilla-70B에 필적하거나 이를 넘어서는 성능을 달성했다.

LLaMA는 이후 Alpaca, Vicuna, Llama 2 등 수많은 파생 연구의 기반이 되어 **오픈소스 LLM 생태계의 빅뱅**을 일으킨 모델로 평가된다.

## 배경 및 문제

### 대형 언어 모델의 접근성 문제

GPT-3, PaLM 등 강력한 대형 언어 모델들은 API를 통해서만 접근 가능하며, 가중치가 공개되지 않아 연구자들이 내부를 분석하거나 커스터마이징하기 어렵다. 이는 AI 안전성 연구, 해석 가능성 연구, 도메인 특화 적응 등에 심각한 제약이 된다.

### Chinchilla 법칙과 훈련 효율

Chinchilla 논문(Hoffmann et al., 2022)은 주어진 컴퓨팅 예산 내에서 모델 크기와 학습 토큰 수의 최적 비율을 제시했다. LLaMA는 이 관점에서 한발 더 나아가, **추론 시 효율**을 고려한 모델 설계를 추구한다. 훈련 비용보다 **배포 비용(inference cost)**이 더 중요할 수 있기 때문에, 더 많은 토큰으로 더 작은 모델을 학습하는 전략을 취한다.

## 핵심 아이디어

LLaMA는 Transformer 아키텍처를 기반으로 하되, 세 가지 핵심 개선을 적용한다.

### 1. Pre-normalization with RMSNorm

기존 GPT 계열 모델은 서브레이어 출력에 LayerNorm을 적용(Post-norm)하는 반면, LLaMA는 각 서브레이어의 **입력**에 RMSNorm을 적용(Pre-norm)한다.

$$\text{RMSNorm}(x) = \frac{x}{\text{RMS}(x)} \cdot g, \quad \text{RMS}(x) = \sqrt{\frac{1}{n}\sum_{i=1}^{n} x_i^2}$$

RMSNorm은 LayerNorm에서 평균 계산을 제거하여 계산 효율을 높이면서도 훈련 안정성을 유지한다.

### 2. SwiGLU 활성화 함수

ReLU 대신 **SwiGLU(Swish-Gated Linear Unit)**를 FFN에 사용한다.

$$\text{SwiGLU}(x, W, V, b, c) = \text{Swish}(xW + b) \otimes (xV + c)$$
$$\text{Swish}(x) = x \cdot \sigma(x)$$

SwiGLU는 PaLM 논문에서 처음 사용되어 성능 향상이 검증되었다. FFN의 차원은 $\frac{2}{3} \cdot 4d$로 조정하여 파라미터 수를 맞춘다.

### 3. Rotary Positional Embeddings (RoPE)

절대 Positional Embedding 대신 **RoPE (Rotary Position Embedding)**을 사용한다. RoPE는 어텐션 연산에서 상대적 위치 정보를 인코딩하여 더 긴 시퀀스로의 외삽(extrapolation)에 유리하다.

$$q_m^\top k_n = (R_m W_q x_m)^\top (R_n W_k x_n) = x_m^\top W_q^\top R_{n-m} W_k x_n$$

여기서 $R_m$은 $m$번째 위치에 대한 회전 행렬이다.

## 방법론

### 학습 데이터

총 **1.4조(1.4T) 토큰**으로 구성된 공개 데이터셋을 사용한다.

| 데이터셋 | 토큰 수 | 비율 |
|---------|---------|------|
| CommonCrawl | 1,188B | 67.0% |
| C4 | 224B | 12.0% |
| GitHub | 100B | 4.5% |
| Wikipedia | 22B | 4.5% |
| Books | 25B | 4.5% |
| ArXiv | 33B | 2.5% |
| StackExchange | 27B | 2.0% |

### 모델 구성

| 모델 | 파라미터 | 레이어 | 헤드 수 | 차원 |
|------|---------|--------|---------|------|
| LLaMA-7B | 6.7B | 32 | 32 | 4096 |
| LLaMA-13B | 13.0B | 40 | 40 | 5120 |
| LLaMA-33B | 32.5B | 60 | 52 | 6656 |
| LLaMA-65B | 65.2B | 80 | 64 | 8192 |

### 훈련 설정

- 옵티마이저: AdamW ($\beta_1=0.9$, $\beta_2=0.95$)
- 학습률: cosine decay, 최대 $3 \times 10^{-4}$
- 배치 크기: 4M 토큰
- 컨텍스트 길이: 2048 토큰
- 그래디언트 클리핑: 1.0
- 65B 모델: A100 80GB GPU 2048개로 21일 훈련

## 실험 결과

### Common Sense Reasoning

| 모델 | BoolQ | PIQA | HellaSwag | WinoGrande | ARC-e | ARC-c | OBQA |
|------|-------|------|-----------|------------|-------|-------|------|
| GPT-3 175B | 60.5 | 81.0 | 78.9 | 70.2 | 68.8 | 51.4 | 57.6 |
| LLaMA-7B | 76.5 | 79.8 | 76.1 | 70.1 | 72.8 | 47.6 | 57.2 |
| LLaMA-13B | 78.1 | 80.1 | 79.2 | 73.0 | 74.8 | 52.7 | 56.4 |
| LLaMA-65B | **85.3** | **82.8** | **86.1** | **82.6** | **79.0** | **56.0** | **60.2** |

### 코드 생성 (HumanEval)

| 모델 | pass@1 | pass@100 |
|------|--------|----------|
| GPT-3 | 0.0 | 0.0 |
| Codex 12B | 28.8 | 72.3 |
| LLaMA-7B | 10.5 | 36.5 |
| LLaMA-65B | 23.7 | 79.3 |

LLaMA-65B는 GPT-3(175B)를 대부분 태스크에서 능가하며, 일부에서 Chinchilla-70B와 동등하거나 우수한 성능을 보인다.

## 의의 및 한계

### 의의

- **오픈소스 생태계 촉발**: 가중치 공개로 수천 개의 파생 모델(Alpaca, Vicuna, WizardLM 등) 탄생
- **공개 데이터만으로 충분**: 독점 데이터 없이도 경쟁력 있는 모델 학습 가능 증명
- **추론 효율 중심 설계**: 작은 모델이 더 많은 토큰으로 훈련되면 실용성에서 우위
- **재현 가능성**: 학습 데이터와 방법론의 투명한 공개

### 한계

- **명령 따르기(instruction following) 미흡**: SFT나 RLHF 없이 사전학습만 했기에 지시 응답 성능이 제한적
- **안전성**: 정렬 훈련 없어 유해 콘텐츠 생성 가능성 존재
- **컨텍스트 길이**: 2048 토큰으로 제한
- **최초 비상업적 라이선스**: 연구 목적으로만 배포되어 상업적 활용 제한 (Llama 2에서 변경)

LLaMA는 오픈소스 AI 연구의 판도를 바꾼 이정표적 모델로, 이후 Llama 2, Llama 3 등으로 발전하며 Meta AI의 대표적 연구 시리즈가 되었다.\n\n## 코드 예제\n\n### LLaMA 핵심 구성 요소 (PyTorch)\n\n```python\nimport torch\nimport torch.nn as nn\nimport torch.nn.functional as F\n\nclass RMSNorm(nn.Module):\n    \"\"\"Root Mean Square Layer Normalization (LLaMA 사용).\n    LayerNorm 대비 평균 빼기 없이 분산으로만 정규화 → 빠르고 안정적.\n    \"\"\"\n    def __init__(self, dim, eps=1e-6):\n        super().__init__()\n        self.eps = eps\n        self.weight = nn.Parameter(torch.ones(dim))\n\n    def forward(self, x):\n        # RMS 계산 후 정규화\n        norm = x.pow(2).mean(-1, keepdim=True).add(self.eps).rsqrt()\n        return x * norm * self.weight\n\ndef precompute_freqs_cis(dim, max_seq_len, theta=10000.0):\n    \"\"\"RoPE 회전 행렬 사전 계산.\"\"\"\n    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2).float() / dim))\n    t = torch.arange(max_seq_len)\n    freqs = torch.outer(t, freqs)  # (max_seq, dim/2)\n    return torch.polar(torch.ones_like(freqs), freqs)  # 복소수 형태\n\ndef apply_rotary_emb(xq, xk, freqs_cis):\n    \"\"\"Query/Key에 RoPE 적용.\"\"\"\n    xq_c = torch.view_as_complex(xq.float().reshape(*xq.shape[:-1], -1, 2))\n    xk_c = torch.view_as_complex(xk.float().reshape(*xk.shape[:-1], -1, 2))\n    xq_out = torch.view_as_real(xq_c * freqs_cis).flatten(-2)\n    xk_out = torch.view_as_real(xk_c * freqs_cis).flatten(-2)\n    return xq_out.type_as(xq), xk_out.type_as(xk)\n\nclass SwiGLU(nn.Module):\n    \"\"\"SwiGLU 활성화 함수 (LLaMA FFN 사용).\n    FFN(x) = (xW1 ⊙ SiLU(xW3)) W2\n    \"\"\"\n    def __init__(self, dim, hidden_dim):\n        super().__init__()\n        self.w1 = nn.Linear(dim, hidden_dim, bias=False)  # gate\n        self.w2 = nn.Linear(hidden_dim, dim, bias=False)  # output\n        self.w3 = nn.Linear(dim, hidden_dim, bias=False)  # input\n\n    def forward(self, x):\n        return self.w2(F.silu(self.w1(x)) * self.w3(x))\n\n# 사용 예시\ndim, seq, batch = 512, 10, 2\nrms = RMSNorm(dim)\nffn = SwiGLU(dim, hidden_dim=4 * dim)\n\nx = torch.randn(batch, seq, dim)\nx_norm = rms(x)               # RMSNorm 적용\nout = ffn(x_norm)              # SwiGLU FFN\nprint(out.shape)               # (2, 10, 512)\n\n# RoPE 위치 인코딩\nhead_dim = 64\nfreqs = precompute_freqs_cis(head_dim, seq)\nxq = torch.randn(batch, seq, 8, head_dim)\nxk = torch.randn(batch, seq, 8, head_dim)\nxq_rot, xk_rot = apply_rotary_emb(xq, xk, freqs)\nprint(xq_rot.shape)            # (2, 10, 8, 64)\n```\n\n> **LLaMA의 핵심 개선점 3가지**: RMSNorm(평균 제거 없이 더 빠름), SwiGLU(ReLU 대비 성능 향상), RoPE(상대적 위치 인코딩으로 외삽 가능).