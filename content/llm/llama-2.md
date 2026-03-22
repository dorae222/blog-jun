---
title: "Llama 2: Open Foundation and Fine-Tuned Chat Models"
slug: "llama-2"
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.490096+00:00"
architecture_entry: "llama-2"
---

## 개요

Llama 2는 Meta AI가 2023년 7월 발표한 오픈 기반 언어 모델 시리즈다. Llama 1의 후속작으로, 7B, 13B, 34B, 70B 네 가지 크기가 있으며, 각각 사전학습 버전(Llama 2)과 채팅에 최적화된 파인튜닝 버전(Llama 2-Chat)이 공개되었다. 중요한 점은 **상업적 이용을 허용하는 라이선스**로 배포되어 기업과 연구자 모두가 자유롭게 활용할 수 있게 되었다는 점이다.

Llama 2는 유용성(helpfulness)과 안전성(safety)을 동시에 추구하는 정렬 접근법을 공개적으로 상세히 설명하여, RLHF 기반 안전한 챗 모델 개발의 방법론적 참고서 역할을 하고 있다.

## 배경 및 문제

### Llama 1의 한계

- 연구 전용 라이선스로 상업적 사용 불가
- 명령 따르기(instruction following) 훈련 미적용
- 안전성 정렬 부재
- 컨텍스트 길이 2048 토큰으로 제한

### 오픈소스 챗 모델의 필요성

ChatGPT, Claude 등 상용 챗 모델들은 가중치가 비공개다. 연구자들이 안전성, 정렬, 편향을 직접 분석하거나 개선하려면 공개된 고품질 챗 모델이 필요하다.

## 핵심 아이디어

### 사전학습 개선

- **2조(2T) 토큰**으로 학습 (Llama 1 대비 40% 증가)
- 컨텍스트 길이 **4096 토큰**으로 확장
- 더 많은 코드와 사실적 텍스트 포함

### Grouped Query Attention (GQA)

34B와 70B 모델에 **GQA(Grouped Query Attention)**를 적용한다. GQA는 Multi-Head Attention(MHA)과 Multi-Query Attention(MQA)의 중간 형태로, 여러 쿼리 헤드가 하나의 키-값 헤드를 공유한다.

$$\text{Attention}(Q_i, K_g, V_g) = \text{softmax}\left(\frac{Q_i K_g^\top}{\sqrt{d_k}}\right) V_g$$

여기서 $g$는 그룹 인덱스로, $G$개의 쿼리 그룹이 $G$개의 K-V 헤드를 공유한다. 이는 KV 캐시 크기를 대폭 줄여 대규모 배치 추론 시 메모리 효율을 높인다.

### 두 단계 RLHF 정렬

#### 지도 파인튜닝 (SFT)

고품질 대화 데이터로 기본 응답 능력을 학습한다. 데이터 품질을 위해 양보다 질을 우선시했다.

#### 두 개의 보상 모델

Llama 2-Chat의 핵심은 **유용성(helpfulness) 보상 모델**과 **안전성(safety) 보상 모델**을 별도로 훈련한다는 점이다.

$$r_{final} = r_{helpfulness} + \lambda \cdot r_{safety}$$

두 목표가 종종 상충하기 때문에(예: 안전하지만 쓸모없는 응답 vs 유용하지만 위험한 응답), 이를 분리해 관리한다.

#### PPO with Rejection Sampling

PPO와 함께 **거절 샘플링(Rejection Sampling)**을 활용한다. 모델이 생성한 K개의 응답 중 보상 모델 점수가 가장 높은 응답을 SFT 데이터로 추가하는 방식이다.

### Ghost Attention (GAtt)

멀티턴 대화에서 초반에 설정한 지시사항을 모델이 오랜 대화 후에도 기억하도록 하는 기법이다. 훈련 시 시스템 프롬프트를 대화의 각 사용자 메시지에 합성적으로 붙여 학습함으로써, 모델이 지시사항을 일관되게 따르도록 한다.

## 방법론

### 모델 구성

| 모델 | 파라미터 | 레이어 | 어텐션 헤드 | KV 헤드 | 컨텍스트 |
|------|---------|--------|------------|---------|----------|
| Llama 2-7B | 6.7B | 32 | 32 | 32 (MHA) | 4096 |
| Llama 2-13B | 13.0B | 40 | 40 | 40 (MHA) | 4096 |
| Llama 2-34B | 34.0B | 48 | 64 | 8 (GQA) | 4096 |
| Llama 2-70B | 68.9B | 80 | 64 | 8 (GQA) | 4096 |

### 인간 선호도 데이터

- 약 **100만 개**의 인간 어노테이션 수집
- 이진 비교(binary comparison) 형식
- 안전성 라벨 포함 (안전/경계선/위험)

## 실험 결과

### 사전학습 모델 벤치마크

| 모델 | MMLU | TriviaQA | HellaSwag | HumanEval |
|------|------|----------|-----------|----------|
| MPT-7B | 26.8 | 59.6 | 76.4 | 18.3 |
| Falcon-7B | 27.8 | 56.9 | 74.9 | - |
| Llama 1-13B | 46.9 | 63.0 | 79.2 | 15.8 |
| Llama 2-7B | 45.3 | 68.9 | 77.2 | 12.8 |
| Llama 2-70B | **68.9** | **87.6** | **87.3** | **29.9** |

### 챗 모델 선호도 (사람 평가)

| 모델 비교 | 선호율 (Llama 2-Chat 기준) |
|---------|-------------------------|
| Llama 2-Chat 70B vs GPT-3.5 | 약 동등 또는 우위 |
| Llama 2-Chat 70B vs Falcon-40B-Chat | 명확한 우위 |
| Llama 2-Chat 70B vs MPT-30B-Chat | 명확한 우위 |

### 안전성 벤치마크

| 모델 | 안전 위반율 (↓) |
|------|----------------|
| Vicuna-13B | 19.5% |
| GPT-3.5 Turbo | 6.1% |
| Llama 2-Chat 7B | 4.1% |
| Llama 2-Chat 70B | **3.4%** |

## 의의 및 한계

### 의의

- **상업적 오픈소스**: 기업이 자유롭게 사용할 수 있는 고품질 챗 모델 제공
- **안전성 연구 공개**: RLHF, 두 보상 모델, Ghost Attention 등 정렬 방법론의 상세 공개
- **GQA 실용화**: 대형 모델의 추론 효율 개선 기법 검증
- **책임 있는 AI 배포**: Red teaming, 안전성 평가, 사용 정책의 모범 사례

### 한계

- **영어 중심**: 다국어 능력이 제한적
- **컨텍스트 길이**: 4096 토큰으로 긴 문서 처리에 한계
- **수학/코드**: 특화 모델 대비 약점
- **Meta 사용 정책 제약**: 월간 활성 사용자 7억 명 이상 서비스는 별도 라이선스 필요

Llama 2는 오픈소스 AI 생태계에서 안전성과 유용성을 겸비한 챗 모델의 기준을 세웠으며, 이후 Code Llama, Llama 3 시리즈의 토대가 되었다.

## 코드 예제

### GQA (Grouped Query Attention) 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class GroupedQueryAttention(nn.Module):
    """LLaMA-2 70B에 도입된 Grouped Query Attention.
    num_kv_heads < num_heads 로 KV 캐시 크기를 줄임.
    """
    def __init__(self, d_model=4096, num_heads=32, num_kv_heads=8):
        super().__init__()
        assert num_heads % num_kv_heads == 0
        self.num_heads = num_heads
        self.num_kv_heads = num_kv_heads
        self.num_groups = num_heads // num_kv_heads  # 각 KV 헤드가 담당할 Q 헤드 수
        self.head_dim = d_model // num_heads

        self.Wq = nn.Linear(d_model, num_heads * self.head_dim, bias=False)
        self.Wk = nn.Linear(d_model, num_kv_heads * self.head_dim, bias=False)
        self.Wv = nn.Linear(d_model, num_kv_heads * self.head_dim, bias=False)
        self.Wo = nn.Linear(num_heads * self.head_dim, d_model, bias=False)

    def forward(self, x):
        B, T, _ = x.shape
        Q = self.Wq(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        K = self.Wk(x).view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)
        V = self.Wv(x).view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)

        # KV를 Q 헤드 수에 맞게 반복 확장
        K = K.repeat_interleave(self.num_groups, dim=1)  # (B, num_heads, T, head_dim)
        V = V.repeat_interleave(self.num_groups, dim=1)

        scale = math.sqrt(self.head_dim)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / scale
        # Causal mask (자기회귀)
        mask = torch.tril(torch.ones(T, T, device=x.device)).unsqueeze(0).unsqueeze(0)
        scores = scores.masked_fill(mask == 0, float('-inf'))
        attn = F.softmax(scores, dim=-1)
        out = torch.matmul(attn, V).transpose(1, 2).contiguous().view(B, T, -1)
        return self.Wo(out)

# 비교: MHA vs GQA 파라미터 수
d_model = 4096
mha_kv_params = 2 * d_model * d_model   # K,V 각 d_model×d_model
gqa_kv_params = 2 * d_model * (d_model // 4)  # KV 헤드를 1/4로
print(f"MHA KV 파라미터: {mha_kv_params:,}")   # 33,554,432
print(f"GQA KV 파라미터: {gqa_kv_params:,}")   # 8,388,608 (4배 감소)

# 테스트
gqa = GroupedQueryAttention(d_model=512, num_heads=8, num_kv_heads=2)
x = torch.randn(2, 16, 512)
out = gqa(x)
print(out.shape)  # (2, 16, 512)
```