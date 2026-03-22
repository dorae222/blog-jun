---
title: Training language models to follow instructions with human feedback
slug: instructgpt
category: technique
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.467796+00:00"
architecture_entry: instructgpt
---

## 개요

InstructGPT는 OpenAI가 2022년 NeurIPS에 발표한 논문으로, 대형 언어 모델(LLM)이 사용자의 의도에 맞게 동작하도록 **인간 피드백 강화학습(RLHF, Reinforcement Learning from Human Feedback)**을 적용한 연구다. GPT-3는 강력한 언어 생성 능력을 갖추고 있지만, 사용자가 원하는 방향으로 동작하지 않는 경우가 많았다. 유해한 내용을 생성하거나, 지시를 무시하거나, 근거 없는 내용을 사실처럼 제시하는 문제가 있었다. InstructGPT는 이 **정렬(alignment) 문제**를 RLHF 파이프라인으로 해결한다.

놀라운 결과는 규모의 역설이다. 1.3B 파라미터의 InstructGPT가 175B 파라미터의 GPT-3보다 사람 평가자들로부터 더 높은 선호도를 받았다. 이는 모델 크기보다 훈련 방식이 실용적 성능에 더 중요할 수 있음을 시사한다.

## 배경 및 문제

### 언어 모델의 미정렬 문제

GPT-3와 같은 대형 언어 모델은 방대한 인터넷 텍스트로 사전 학습된다. 이 과정의 목적은 **다음 토큰 예측(next token prediction)**이며, 사용자를 돕는 것이 아니다. 결과적으로 모델은:

- 지시를 무시하고 프롬프트를 단순 완성하려 함
- 유해하거나 편향된 내용을 생성
- 사실이 아닌 내용을 자신감 있게 생성 (hallucination)
- 사용자의 실제 의도보다 표면적인 패턴을 따름

이를 **미정렬(misalignment)** 문제라 하며, 단순히 모델을 크게 만드는 것으로는 해결되지 않는다.

### 기존 접근법의 한계

지도 학습(SFT)만으로 파인튜닝하면 어느 정도 개선되지만, 다양한 지시와 상황에 일반화하기 어렵다. 사람이 원하는 응답의 모든 경우를 레이블링하기에는 비용이 너무 크고, 무엇이 "좋은 응답"인지에 대한 정의도 복잡하다.

## 핵심 아이디어

InstructGPT의 핵심은 세 단계로 구성된 **RLHF 파이프라인**이다.

### 1단계: 지도 파인튜닝 (SFT)

먼저 OpenAI의 레이블러(labeler)팀이 다양한 프롬프트에 대해 이상적인 응답을 직접 작성한다. 이 데이터로 GPT-3를 지도 학습 방식으로 파인튜닝하여 SFT 모델을 만든다.

$$\mathcal{L}_{SFT} = -\sum_{t} \log P(y_t | x, y_{<t})$$

### 2단계: 보상 모델 훈련 (RM)

SFT 모델이 생성한 여러 응답에 대해 레이블러가 **선호도 순위**를 매긴다. 예를 들어 같은 프롬프트에 대한 응답 A, B, C, D를 순위 매기면, 이 쌍별(pairwise) 비교 데이터로 **보상 모델(Reward Model)**을 훈련한다.

$$\mathcal{L}_{RM}(\theta) = -\mathbb{E}_{(x,y_w,y_l) \sim D} \left[ \log \sigma(r_\theta(x, y_w) - r_\theta(x, y_l)) \right]$$

여기서 $y_w$는 선호되는 응답, $y_l$은 덜 선호되는 응답, $r_\theta$는 보상 모델이다.

### 3단계: PPO로 강화학습 (RL)

보상 모델을 피드백 신호로 삼아 **PPO(Proximal Policy Optimization)** 알고리즘으로 SFT 모델을 추가로 최적화한다.

$$\text{objective}(\phi) = \mathbb{E}_{(x,y) \sim \pi_\phi} \left[ r_\theta(x,y) - \beta \log \frac{\pi_\phi(y|x)}{\pi_{SFT}(y|x)} \right] + \gamma \mathcal{L}_{pretraining}$$

- $\beta$: KL 페널티 계수. SFT 모델에서 너무 멀리 벗어나지 않도록 조절
- $\gamma \mathcal{L}_{pretraining}$: 사전학습 분포를 유지하여 **정렬 세금(alignment tax)**을 완화

## 방법론

### 데이터 및 레이블러

- 약 40명의 계약직 레이블러가 데이터 제작에 참여
- SFT 데이터: ~13,000개의 프롬프트-응답 쌍
- RM 데이터: ~33,000개의 프롬프트, 각각 여러 응답의 순위 비교
- 프롬프트는 실제 API 사용자 요청에서 수집 (개인정보 제거 후)

### 평가 지표

평가는 주로 **사람 평가자**가 직접 두 응답을 비교하는 방식으로 진행된다. 핵심 평가 차원:
1. **유용성(Helpfulness)**: 사용자의 의도를 얼마나 잘 충족하는가
2. **정직성(Truthfulness)**: 사실에 근거한 응답인가
3. **무해성(Harmlessness)**: 위험하거나 불쾌한 내용이 없는가

### 모델 변형

- **GPT-3 (175B)**: 베이스라인
- **SFT (13B)**: 지도 파인튜닝만 적용
- **InstructGPT (1.3B, 6B, 175B)**: 전체 RLHF 파이프라인 적용

## 실험 결과

### 사람 선호도 비교

| 모델 | GPT-3 대비 선호율 |
|------|------------------|
| GPT-3 (175B) | 기준선 |
| SFT (13B) | ~50% |
| InstructGPT 1.3B | **85%** |
| InstructGPT 175B | **90%+** |

**1.3B InstructGPT가 175B GPT-3보다 높은 선호도**를 기록했다. 이는 정렬 훈련의 효과가 모델 크기를 압도할 수 있음을 보여준다.

### TruthfulQA 결과

InstructGPT는 GPT-3 대비 TruthfulQA에서 약 **2배 높은 정직성** 점수를 보였다. 특히 모델이 모르는 것에 대해 "모른다"고 말하는 비율이 증가했다.

### 독성(Toxicity) 감소

RealToxicityPrompts 벤치마크에서 InstructGPT는 GPT-3에 비해 독성 콘텐츠 생성률이 크게 감소했다. 단, 명시적으로 독성 내용을 요청하는 경우에는 여전히 취약점이 존재했다.

### 정렬 세금 (Alignment Tax)

RLHF 훈련이 일부 NLP 벤치마크(예: 코드 생성, 특정 분류 태스크)의 성능을 소폭 하락시키는 현상이 관찰되었다. 이를 **정렬 세금(alignment tax)**이라 한다. 논문은 사전학습 손실 항 $\gamma \mathcal{L}_{pretraining}$을 추가하여 이를 완화했다.

## 의의 및 한계

### 의의

- **RLHF의 실용적 검증**: 대형 언어 모델에 RLHF를 성공적으로 적용한 첫 대규모 사례
- **규모 역설 발견**: 작은 정렬 모델이 큰 베이스 모델을 능가할 수 있음을 증명
- **ChatGPT의 선구자**: InstructGPT의 방법론이 ChatGPT, GPT-4의 기반이 됨
- **안전 AI 연구 촉진**: 정렬 문제를 실용적 맥락에서 논의하는 계기 마련

### 한계

- **레이블러 편향**: 40명의 레이블러 선호도가 인류 전체의 가치를 대표하지 않을 수 있음
- **보상 해킹(Reward Hacking)**: 모델이 보상 모델을 속이는 방향으로 최적화될 위험
- **비용**: 사람 레이블링과 RL 훈련에 드는 비용이 매우 높음
- **정렬 세금**: 일부 태스크에서 성능 저하 발생
- **문화적 편향**: 영어 중심, 서구 가치 중심의 정렬 위험

InstructGPT는 현대 LLM 정렬 연구의 출발점이 되었으며, 이후 Constitutional AI, DPO 등 다양한 정렬 방법론 연구의 기반을 마련했다.\n\n## 코드 예제\n\n### RLHF 파이프라인 단순 구현 (PyTorch)\n\n```python\nimport torch\nimport torch.nn as nn\nfrom torch.optim import AdamW\n\nclass PolicyModel(nn.Module):\n    \"\"\"SFT로 초기화된 정책 모델 (GPT 계열 단순화).\"\"\"\n    def __init__(self, vocab_size=1000, d_model=256, num_layers=4):\n        super().__init__()\n        self.embed = nn.Embedding(vocab_size, d_model)\n        layer = nn.TransformerDecoderLayer(d_model, nhead=8, batch_first=True)\n        self.transformer = nn.TransformerDecoder(layer, num_layers)\n        self.head = nn.Linear(d_model, vocab_size)\n\n    def forward(self, x):\n        return self.head(self.transformer(self.embed(x), self.embed(x)))\n\nclass RewardModel(nn.Module):\n    \"\"\"비교 데이터로 학습된 보상 모델.\"\"\"\n    def __init__(self, vocab_size=1000, d_model=256, num_layers=2):\n        super().__init__()\n        self.embed = nn.Embedding(vocab_size, d_model)\n        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead=8, batch_first=True)\n        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers)\n        self.value_head = nn.Linear(d_model, 1)  # 스칼라 보상 출력\n\n    def forward(self, x):\n        h = self.encoder(self.embed(x))\n        return self.value_head(h[:, -1, :]).squeeze(-1)  # 마지막 토큰의 보상\n\ndef compute_ppo_loss(policy_logits, old_log_probs, rewards, actions, epsilon=0.2, kl_coef=0.02):\n    \"\"\"PPO with KL penalty (InstructGPT 방식).\"\"\"\n    log_probs = torch.log_softmax(policy_logits, dim=-1)\n    new_log_probs = log_probs.gather(-1, actions.unsqueeze(-1)).squeeze(-1)\n    ratio = torch.exp(new_log_probs - old_log_probs.detach())\n    # Clipped PPO objective\n    clipped = torch.clamp(ratio, 1 - epsilon, 1 + epsilon)\n    policy_loss = -torch.min(ratio * rewards, clipped * rewards).mean()\n    # KL divergence penalty로 원래 분포에서 너무 멀어지지 않도록\n    kl_penalty = kl_coef * (new_log_probs - old_log_probs.detach()).mean()\n    return policy_loss + kl_penalty\n\n# RLHF 학습 루프 (단순화)\npolicy = PolicyModel()\nreward_model = RewardModel()\noptimizer = AdamW(policy.parameters(), lr=1e-5)\n\nbatch_size, seq_len = 4, 20\nfor step in range(3):\n    tokens = torch.randint(0, 1000, (batch_size, seq_len))\n    actions = torch.randint(0, 1000, (batch_size, seq_len))\n\n    # 현재 정책으로 로그 확률 계산\n    with torch.no_grad():\n        old_logits = policy(tokens)\n        old_log_probs = torch.log_softmax(old_logits, dim=-1).gather(-1, actions.unsqueeze(-1)).squeeze(-1)\n        rewards = reward_model(tokens)  # 보상 모델에서 보상 획득\n\n    # PPO 업데이트\n    new_logits = policy(tokens)\n    loss = compute_ppo_loss(new_logits, old_log_probs, rewards, actions)\n    loss.backward()\n    optimizer.step()\n    optimizer.zero_grad()\n    print(f\"Step {step+1}: loss={loss.item():.4f}\")\n```\n\n> **3단계 요약**: SFT(지도 학습) → RM(비교 데이터로 보상 모델 학습) → PPO(KL 페널티 포함 강화학습). KL 페널티는 정책이 원래 SFT 모델에서 너무 멀어지는 것을 방지합니다.