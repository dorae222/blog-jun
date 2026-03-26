# AI 핵심 기법 총정리

## 개요

AI 모델의 성능은 아키텍처만으로 결정되지 않습니다. Attention 메커니즘, 효율적 학습법, 추론 최적화, 정렬 기법, 검색 증강 생성(RAG), Scaling Laws 등 **모든 AI 분야에 공통으로 적용되는 핵심 기법**들이 모델의 실질적인 능력을 좌우합니다.

이 가이드는 LLM, Diffusion, Vision, Agent 등 특정 분야에 국한되지 않고, AI 전반에 걸쳐 활용되는 기반 기술들을 체계적으로 정리합니다. 개별 논문의 세부 사항보다는 **기법 간의 관계와 발전 맥락**을 이해하는 데 초점을 맞춥니다.

### 왜 핵심 기법을 따로 정리해야 하는가?

AI의 핵심 기법들은 여러 분야에 걸쳐 사용됩니다. Flash Attention은 LLM에서도, Diffusion 모델에서도 사용됩니다. LoRA는 LLM 파인튜닝에서 시작했지만 Stable Diffusion, Vision 모델에서도 활용됩니다. 이런 공통 기법들을 별도로 이해하면, 새로운 분야를 학습할 때 전이 효과가 극대화됩니다.

---

## 핵심 기법 분류

AI 핵심 기법은 크게 6가지 영역으로 분류됩니다.

1. **Attention과 아키텍처 기법** — Transformer 구성 요소의 개선
2. **효율적 학습 (Efficient Training)** — 적은 자원으로 학습하는 방법
3. **효율적 추론 (Efficient Inference)** — 빠르고 저렴한 추론
4. **Scaling Laws와 데이터** — 모델/데이터 규모와 성능의 관계
5. **RAG와 지식 증강** — 외부 지식을 활용한 성능 향상
6. **정렬과 추론 강화** — 모델의 행동을 인간 의도에 맞추는 기법

---

## 1. Attention과 아키텍처 기법

Transformer의 핵심인 Attention 메커니즘과 관련 아키텍처 개선 기법들입니다.

### Attention 메커니즘의 발전

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| Multi-Head Attention | 2017 | 여러 표현 부분공간에서 동시 어텐션 | [Transformer](/post/transformer) |
| Grouped-Query Attention (GQA) | 2023 | KV 헤드 그룹 공유로 메모리 절감 | [GQA](/post/gqa) |
| Multi-Head Latent Attention (MLA) | 2024 | KV를 저차원 잠재 공간으로 압축 | [DeepSeek-V2](/post/deepseek-v2) |
| Sliding Window Attention | 2023 | 지역적 어텐션으로 긴 시퀀스 처리 | [Mistral 7B](/post/mistral-7b) |

**Attention의 핵심 발전 방향**: Full Attention → Multi-Head → GQA (KV 공유) → MLA (잠재 압축)

각 단계는 성능을 유지하면서 메모리 사용량을 줄이는 방향으로 진화했습니다. MHA에서 GQA로 전환하면 KV 캐시 크기가 헤드 수에 비례하여 감소하며, MLA는 이를 더 극적으로 압축합니다.

### 위치 인코딩

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| Sinusoidal PE | 2017 | 절대 위치 인코딩 | [Transformer](/post/transformer) |
| RoPE | 2021 | 회전 위치 임베딩, 상대적 위치 | [RoPE](/post/roformer-rope) |
| ALiBi | 2022 | 어텐션 바이어스, 외삽 능력 | - |

**RoPE**는 현재 대부분의 LLM(LLaMA, Mistral, Qwen 등)이 채택한 표준 위치 인코딩입니다. 회전 행렬을 통해 상대적 위치 정보를 인코딩하며, 학습하지 않은 더 긴 시퀀스에 대한 외삽(extrapolation)이 가능합니다.

### 정규화와 아키텍처 패턴

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| Pre-Norm vs Post-Norm | 2020 | 정규화 위치에 따른 학습 안정성 | [Layer Norm](/post/layer-norm-transformer) |
| MoE (Mixture of Experts) | 2017+ | 조건부 계산, 효율적 스케일링 | [Switch Transformer](/post/switch-transformer), [Mixtral](/post/mixtral) |
| Sparse MoE | 2022+ | 일부 전문가만 활성화 | [DeepSeek-V3](/post/deepseek-v3) |

**Mixture of Experts(MoE)**는 모델 크기를 키우면서 계산 비용은 일정하게 유지할 수 있는 핵심 기법입니다.

- [Switch Transformer](/post/switch-transformer): 각 토큰을 하나의 전문가에게만 라우팅 (Top-1)
- [Mixtral](/post/mixtral): 8개 전문가 중 2개 활성화 (Top-2)
- [DeepSeek-V3](/post/deepseek-v3): Auxiliary-loss-free 부하 분산으로 MoE 학습 안정화

---

## 2. 효율적 학습 (Efficient Training)

대규모 모델을 적은 자원으로 학습하는 기법들입니다.

### 파라미터 효율적 파인튜닝 (PEFT)

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| LoRA | 2021 | 저랭크 적응, 0.1% 파라미터만 학습 | [LoRA](/post/lora) |
| QLoRA | 2023 | 4-bit 양자화 + LoRA | [QLoRA](/post/qlora) |

[LoRA (Low-Rank Adaptation)](/post/lora)는 AI 분야에서 가장 영향력 있는 기법 중 하나입니다. 사전학습된 가중치 행렬 W에 저랭크 분해 ΔW = BA를 추가하여, 원래 모델의 0.1% 파라미터만으로도 전체 파인튜닝에 가까운 성능을 달성합니다.

[QLoRA](/post/qlora)는 여기에 4-bit 양자화를 결합하여, 소비자용 GPU(24GB)에서도 65B 모델의 파인튜닝을 가능하게 했습니다. NormalFloat4 데이터 타입, Double Quantization, Paged Optimizers가 핵심입니다.

### 모델 경량화

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| Knowledge Distillation | 2015+ | 큰 모델의 지식을 작은 모델로 전이 | [DistilBERT](/post/distilbert) |
| Structured Pruning | 2023 | 구조적 가지치기로 모델 축소 | [Sheared LLaMA](/post/sheared-llama) |

---

## 3. 효율적 추론 (Efficient Inference)

학습된 모델을 빠르고 저렴하게 서빙하는 기법들입니다.

### 메모리 효율적 어텐션

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| Flash Attention | 2022 | IO-aware 어텐션, 타일링, 온라인 Softmax | [Flash Attention](/post/flash-attention) |
| Flash Attention 2 | 2023 | 개선된 병렬화, 비대칭 워크 분배 | [Flash Attention 2](/post/flash-attention-2) |
| Paged Attention (vLLM) | 2023 | OS 페이징 개념을 KV 캐시에 적용 | [Paged Attention](/post/paged-attention) |

[Flash Attention](/post/flash-attention)은 어텐션 계산의 메모리 복잡도를 O(n^2)에서 O(n)으로 줄인 획기적인 기법입니다. GPU의 SRAM과 HBM 사이의 IO 비용을 최소화하는 타일링(tiling) 전략을 사용합니다. 현재 거의 모든 LLM 학습과 추론에서 표준으로 사용됩니다.

[Paged Attention](/post/paged-attention)은 추론 시 KV 캐시를 OS의 가상 메모리 페이징처럼 관리하여, 배치 처리 시 메모리 활용률을 극대화합니다. vLLM 라이브러리의 핵심 기술입니다.

### 추론 가속

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| Speculative Decoding | 2023 | 작은 모델로 초안, 큰 모델로 검증 | [Speculative Decoding 논문](/post/speculative-decoding), [서베이](/post/closer-look-at-efficient-inference-methods-a-survey-of-speculative-decoding), [심층 서베이](/post/speculative-decoding-and-beyond-an-in-depth-survey-of-techniques) |

[Speculative Decoding](/post/speculative-decoding)은 작은 "드래프트" 모델이 여러 토큰을 빠르게 생성하고, 큰 "타겟" 모델이 이를 한 번에 검증하는 방식입니다. 출력 분포를 변경하지 않으면서 2-3배 속도 향상을 달성합니다.

---

## 4. Scaling Laws와 데이터

모델/데이터 규모와 성능의 관계를 규명하고, 학습 효율을 최적화하는 연구입니다.

| 연구 | 연도 | 핵심 발견 | 관련 포스트 |
|------|------|----------|------------|
| Scaling Laws (Kaplan) | 2020 | 파라미터/데이터/연산의 Power Law 관계 | [Scaling Laws](/post/scaling-laws) |
| Chinchilla | 2022 | Compute-optimal: 데이터를 더 늘려야 | [Chinchilla](/post/chinchilla) |
| Scaling Data-Constrained | 2023 | 데이터 제약 하의 최적 전략 | [Scaling Data-Constrained](/post/scaling-data-constrained) |
| Architecture & Objectives | 2023 | 아키텍처/목적함수별 스케일링 차이 | [Architecture & Objectives](/post/architecture-pretraining-objectives) |

**Scaling Laws의 핵심 메시지**: AI 모델의 성능은 모델 크기(N), 데이터 크기(D), 연산량(C)에 대해 예측 가능한 Power Law를 따릅니다. 이를 통해 학습 전에 최적의 자원 배분을 결정할 수 있습니다.

- [Kaplan et al.](/post/scaling-laws): 모델 크기를 키우는 것이 가장 효율적
- [Chinchilla](/post/chinchilla): 데이터도 비례하여 늘려야 최적 (모델 크기 N ∝ 데이터 D)

---

## 5. RAG와 지식 증강

모델의 내부 지식만으로는 한계가 있을 때, 외부 지식을 검색하여 활용하는 기법입니다.

### RAG (Retrieval-Augmented Generation) 계열

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| RAG (원본) | 2020 | 검색 + 생성 통합 | [RAG](/post/rag) |
| REALM | 2020 | 사전학습 단계부터 검색 통합 | [REALM](/post/realm) |
| In-Context RALM | 2023 | 추론 시 검색 결과를 컨텍스트에 삽입 | [In-Context RALM](/post/in-context-ralm) |
| Self-RAG | 2023 | 검색 필요성을 스스로 판단 | [Self-RAG](/post/self-rag) |
| ARES | 2024 | RAG 시스템의 자동 평가 | [ARES](/post/ares-rag-eval) |

[RAG](/post/rag)는 LLM의 가장 중요한 보완 기법 중 하나입니다. 외부 문서 저장소에서 관련 정보를 검색하여 프롬프트에 포함시킴으로써, 모델이 최신 정보와 도메인 지식을 활용할 수 있게 합니다. 할루시네이션을 줄이고 답변의 근거를 제공할 수 있습니다.

[Self-RAG](/post/self-rag)는 RAG를 한 단계 발전시켜, 모델이 스스로 "검색이 필요한가?", "검색 결과가 관련 있는가?", "답변이 검색 결과에 기반하는가?"를 판단합니다.

### Instruction Tuning과 프롬프팅

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| Instruction Tuning | 2022 | 지시문 기반 파인튜닝 | [FLAN](/post/flan) |
| Scaling Instruction FT | 2022 | 태스크 수 증가에 따른 성능 향상 | [Scaling Instruction FT](/post/scaling-instruction-finetuning) |
| Multitask Prompted Training | 2022 | 다중 태스크 프롬프트 학습 | [T0/Multitask](/post/multitask-prompted-training) |
| Rethinking Demonstrations | 2022 | ICL에서 레이블 정확성의 역할 | [Rethinking Demos](/post/rethinking-demonstrations) |

---

## 6. 정렬과 추론 강화 (Alignment & Reasoning)

모델의 행동을 인간의 의도와 가치에 맞추고, 추론 능력을 강화하는 기법입니다.

### 정렬 (Alignment) 기법

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| RLHF | 2022 | SFT → Reward Model → PPO | [InstructGPT](/post/instructgpt) |
| Constitutional AI | 2022 | 자기 비판 기반 정렬 | [Constitutional AI](/post/constitutional-ai) |
| DPO | 2023 | Reward Model 없는 직접 최적화 | [DPO](/post/dpo) |
| Training Helpful & Harmless | 2022 | 유용성과 안전성의 균형 | [Helpful & Harmless](/post/training-helpful-harmless) |
| Self-Rewarding LM | 2024 | 자기 보상 생성 | [Self-Rewarding LM](/post/self-rewarding-lm) |

**정렬의 발전 경로**: RLHF (PPO 기반) → DPO (직접 최적화) → Self-Rewarding (자기 개선)

[RLHF](/post/instructgpt)는 ChatGPT를 가능하게 한 핵심 기술입니다. 사람의 선호도 데이터로 보상 모델을 학습하고, PPO로 LLM을 최적화합니다. 하지만 보상 모델 학습과 PPO의 복잡성이 단점입니다.

[DPO](/post/dpo)는 이를 극적으로 단순화했습니다. 보상 모델 없이 직접 선호/비선호 쌍으로 LLM을 최적화합니다. 수학적으로 RLHF의 최적 해와 동치임을 증명했습니다.

### 추론 강화 (Reasoning) 기법

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| Chain-of-Thought (CoT) | 2022 | 단계별 추론 유도 | [CoT](/post/cot) |
| Self-Consistency | 2022 | 다중 추론 경로 투표 | [Self-Consistency](/post/self-consistency) |
| Tree of Thoughts | 2023 | 트리 구조 추론 탐색 | [Tree of Thoughts](/post/tree-of-thoughts) |

[Chain-of-Thought](/post/cot)는 "Let's think step by step"이라는 간단한 프롬프트만으로도 LLM의 수학적 추론, 논리적 사고 능력을 크게 향상시킵니다. 이후 Self-Consistency, Tree of Thoughts 등으로 확장되었으며, O1, DeepSeek-R1 등 추론 특화 모델의 이론적 기반이 되었습니다.

### 모델 평가와 벤치마크

| 기법 | 연도 | 핵심 기여 | 관련 포스트 |
|------|------|----------|------------|
| Chatbot Arena | 2023 | ELO 기반 모델 랭킹 | [Chatbot Arena](/post/chatbot-arena) |
| AgentBench | 2023 | 에이전트 능력 벤치마크 | [AgentBench](/post/agentbench) |
| MEGAVERSE | 2023 | 다국어 평가 | [MEGAVERSE](/post/megaverse) |
| Detecting Pretraining Data | 2023 | 데이터 오염 탐지 | [Detecting Pretraining](/post/detecting-pretraining-data) |
| Scalable Extraction | 2023 | 모델에서 학습 데이터 추출 | [Scalable Extraction](/post/scalable-extraction) |

---

## 기법 간 상호 관계

각 기법은 독립적으로 존재하는 것이 아니라 서로 결합하여 시너지를 냅니다.

### 학습 파이프라인에서의 기법 조합

```
사전학습:
  Scaling Laws → 최적 모델/데이터 크기 결정
  Flash Attention → 학습 효율화
  MoE → 조건부 계산으로 효율적 스케일링

파인튜닝:
  LoRA/QLoRA → 적은 자원으로 파인튜닝
  Instruction Tuning → 지시문 따르기 학습
  RLHF/DPO → 인간 선호도 정렬

추론:
  Flash Attention → 메모리 효율적 어텐션
  Paged Attention → KV 캐시 최적화
  Speculative Decoding → 생성 속도 향상
  RAG → 외부 지식 활용
  CoT → 추론 능력 강화
```

### 적용 분야별 핵심 기법

| 분야 | 핵심 기법 | 관련 가이드 |
|------|----------|------------|
| LLM | Scaling Laws, MoE, RLHF/DPO, Flash Attention | [LLM 가이드](/post/llm-paper-guide) |
| Diffusion | CFG, Flow Matching, DiT | [Diffusion 가이드](/post/diffusion-models-guide) |
| Vision | Self-Supervised Learning, CLIP | [Vision 가이드](/post/computer-vision-dl-roadmap) |
| SSM | Selective Mechanism, SSD | [SSM 가이드](/post/state-space-models-guide) |
| Agent | CoT, ReAct, Tool Use, RAG | [Agent 가이드](/post/ai-agent-technology-guide) |

---

## 추천 학습 경로

### 초심자 (핵심 기법 입문)

가장 영향력 있는 핵심 기법을 먼저 이해합니다.

1. [Transformer](/post/transformer) — Self-Attention의 기본
2. [LoRA](/post/lora) — 효율적 파인튜닝의 원리
3. [RAG](/post/rag) — 검색 증강 생성
4. [Chain-of-Thought](/post/cot) — 추론 강화 기법
5. [InstructGPT](/post/instructgpt) — RLHF의 기본

### 중급 (기법 심화)

각 기법의 변형과 최적화를 학습합니다.

**Attention & 아키텍처**:
1. [GQA](/post/gqa) + [RoPE](/post/roformer-rope) — 어텐션 최적화
2. [Flash Attention](/post/flash-attention) → [Flash Attention 2](/post/flash-attention-2) — 메모리 효율화
3. [Switch Transformer](/post/switch-transformer) → [Mixtral](/post/mixtral) → [DeepSeek-V3](/post/deepseek-v3) — MoE

**학습 & 정렬**:
4. [QLoRA](/post/qlora) — 양자화 + LoRA
5. [DPO](/post/dpo) — 직접 선호도 최적화
6. [Constitutional AI](/post/constitutional-ai) — 자기 비판 정렬

**추론 & 지식**:
7. [Self-RAG](/post/self-rag) — 자기 판단 검색
8. [Speculative Decoding](/post/speculative-decoding) — 추론 가속
9. [Paged Attention](/post/paged-attention) — 서빙 최적화

### 고급 (연구/실무)

최신 기법과 통합적 이해를 추구합니다.

1. [Scaling Laws](/post/scaling-laws) + [Chinchilla](/post/chinchilla) — 스케일링 이론
2. [DeepSeek-V3](/post/deepseek-v3) — 최신 MoE 설계
3. [Self-Rewarding LM](/post/self-rewarding-lm) — 자기 개선 정렬
4. [Speculative Decoding 서베이](/post/speculative-decoding-and-beyond-an-in-depth-survey-of-techniques) — 추론 최적화 전체 조망
5. [ARES](/post/ares-rag-eval) — RAG 시스템 평가
6. [Layer Norm](/post/layer-norm-transformer) + [Architecture & Objectives](/post/architecture-pretraining-objectives) — 아키텍처 설계 원칙

---

## 주요 기법 한눈에 보기

| 영역 | 핵심 기법 | 한 줄 설명 |
|------|----------|-----------|
| Attention | [GQA](/post/gqa) | KV 헤드 공유로 메모리 절감 |
| Attention | [Flash Attention](/post/flash-attention) | IO-aware 타일링으로 O(n) 메모리 |
| 위치 인코딩 | [RoPE](/post/roformer-rope) | 회전 기반 상대 위치 |
| MoE | [Mixtral](/post/mixtral) | 8개 중 2개 전문가 활성화 |
| 파인튜닝 | [LoRA](/post/lora) | 저랭크 적응, 0.1% 파라미터 |
| 파인튜닝 | [QLoRA](/post/qlora) | 4-bit + LoRA |
| 추론 가속 | [Speculative Decoding](/post/speculative-decoding) | 초안-검증 방식 |
| 서빙 | [Paged Attention](/post/paged-attention) | KV 캐시 페이징 |
| 스케일링 | [Scaling Laws](/post/scaling-laws) | N, D, C의 Power Law |
| 지식 증강 | [RAG](/post/rag) | 검색 + 생성 |
| 정렬 | [DPO](/post/dpo) | 직접 선호도 최적화 |
| 추론 | [CoT](/post/cot) | 단계별 추론 유도 |

---

## 관련 카테고리

- [AI/ML 아키텍처 로드맵](/post/ai-ml-architecture-roadmap) — 전체 AI/ML 지형도
- [LLM 핵심 논문 가이드](/post/llm-paper-guide) — LLM에서의 기법 적용
- [Diffusion Models 완전 정복](/post/diffusion-models-guide) — 생성 모델에서의 기법
- [State Space Models 가이드](/post/state-space-models-guide) — Attention의 대안
- [머신러닝 기초부터 실전까지](/post/ml-fundamentals-roadmap) — ML 이론 기초
