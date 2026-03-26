# LLM 핵심 논문 가이드: 언어 모델의 진화

## 개요

대규모 언어 모델(Large Language Model, LLM)은 현대 AI의 핵심입니다. 2017년 [Transformer](/post/transformer)의 등장 이후 불과 8년 만에 GPT, BERT에서 시작하여 수천억 파라미터의 거대 모델, 효율적인 오픈소스 모델, 그리고 추론 특화 모델까지 놀라운 발전을 이루었습니다.

이 가이드는 LLM의 핵심 논문과 아키텍처를 **시간순으로 정리**하고, 각 모델의 핵심 기여와 상호 영향 관계를 체계적으로 설명합니다. 수십 편의 논문을 개별적으로 읽기 전에, 먼저 이 가이드를 통해 전체 흐름을 파악하시기를 권합니다.

### 왜 LLM 논문을 체계적으로 공부해야 하는가?

LLM 분야는 매우 빠르게 발전하고 있지만, 핵심 아이디어의 계보를 따라가면 뚜렷한 흐름이 보입니다. Transformer → Pre-training → Scaling → Alignment → Efficiency → Reasoning으로 이어지는 발전 축을 이해하면, 새로운 모델이 등장해도 그 위치를 빠르게 파악할 수 있습니다.

---

## 핵심 흐름: LLM 발전 타임라인

### Era 1: Transformer와 사전학습 (2017-2019)

현대 LLM의 근간이 되는 아키텍처와 사전학습 패러다임이 확립된 시기입니다.

**2017 — Transformer의 탄생**

- [Transformer](/post/transformer): Self-Attention만으로 시퀀스 처리. Encoder-Decoder 구조로 번역 SOTA 달성. 모든 현대 LLM의 시작점.

**2018 — 사전학습 혁명**

- [ELMo](/post/elmo): 문맥 의존적 단어 표현. BiLSTM 기반이지만 사전학습의 중요성을 입증.
- [GPT-1](/post/gpt-1): Transformer Decoder 기반 단방향 사전학습. 파인튜닝으로 다양한 NLP 태스크 해결.
- [BERT](/post/bert): Transformer Encoder 기반 양방향 사전학습. Masked Language Model + Next Sentence Prediction. NLP 벤치마크 대부분에서 SOTA 달성.

**2019 — BERT 변형과 확장**

- [RoBERTa](/post/roberta): BERT의 학습 전략 최적화. 더 많은 데이터, 더 긴 학습, Dynamic Masking.
- [ALBERT](/post/albert): 파라미터 공유로 BERT 경량화. Factorized Embedding, Cross-Layer Parameter Sharing.
- [XLNet](/post/xlnet): Permutation Language Model. 양방향 문맥을 자기회귀 방식으로 학습.
- [DistilBERT](/post/distilbert): Knowledge Distillation으로 BERT 60% 크기에 97% 성능 유지.
- [ELECTRA](/post/electra): Replaced Token Detection. Generator-Discriminator 구조로 효율적 학습.
- [DeBERTa](/post/deberta): Disentangled Attention. 위치와 내용 정보 분리.
- [GPT-2](/post/gpt-2): 1.5B 파라미터. Zero-shot 능력의 출현.

### Era 2: 스케일링과 거대 모델 (2020-2022)

모델 크기를 키우면 새로운 능력이 창발(emergent)한다는 발견이 거대 모델 경쟁을 촉발했습니다.

**2020 — 스케일링의 발견**

- [GPT-3](/post/gpt-3): 175B 파라미터. Few-shot Learning이 파인튜닝 없이도 가능함을 입증. In-context Learning의 시작.
- [Scaling Laws](/post/scaling-laws): 모델 크기, 데이터 크기, 연산량의 관계를 수학적으로 규명. Power Law 관계 발견.
- [T5](/post/t5): 모든 NLP 태스크를 Text-to-Text 형식으로 통합. Encoder-Decoder 구조의 집대성.

**2021 — 대형 모델 경쟁**

- [Gopher](/post/gopher): DeepMind의 280B 모델. 지식 집약적 태스크에서 강점.
- [PaLM](/post/palm): Google의 540B 모델. Pathways 시스템으로 학습. Chain-of-Thought 추론 능력 확인.
- [BLOOM](/post/bloom): BigScience 프로젝트. 176B 오픈소스 다국어 모델.
- [GPT-NeoX](/post/gpt-neo), [GPT-J](/post/gpt-j): EleutherAI의 오픈소스 LLM.
- [Chinchilla](/post/chinchilla): 데이터 중심 스케일링. 같은 연산량이면 모델을 키우는 것보다 데이터를 늘리는 게 효율적.
- [OPT](/post/opt): Meta의 175B 오픈소스 모델. 학습 로그 공개.
- [FLAN-T5](/post/flan-t5): Instruction Tuning으로 T5 성능 대폭 향상.

**2022 — 정렬(Alignment)의 시대**

- [InstructGPT](/post/instructgpt): RLHF(Reinforcement Learning from Human Feedback)로 모델 정렬. ChatGPT의 기반 기술.
- [Constitutional AI](/post/constitutional-ai): Anthropic의 자기 개선 정렬 방식. AI가 스스로 피드백 생성.
- [UL2](/post/ul2): Mixture-of-Denoisers. 다양한 사전학습 목적함수 통합.

### Era 3: 오픈소스와 효율화 (2023)

LLaMA의 등장으로 오픈소스 LLM 생태계가 폭발적으로 성장했습니다. 동시에 더 작은 모델로 더 좋은 성능을 내려는 효율화 연구가 활발해졌습니다.

**오픈소스 LLM의 폭발**

- [LLaMA](/post/llama): Meta의 7B-65B 오픈소스 모델. 작은 모델로도 경쟁력 있는 성능을 보여 오픈소스 LLM 시대를 개막.
- [LLaMA 2](/post/llama-2): 7B-70B. RLHF 적용, 상업적 사용 허가. Safety 학습 포함.
- [Mistral 7B](/post/mistral-7b): Sliding Window Attention, Grouped-Query Attention. 7B 모델로 LLaMA-2 13B 능가.
- [Mixtral](/post/mixtral): Sparse Mixture of Experts(MoE). 8개 전문가 중 2개만 활성화하여 효율적 추론.
- [Yi](/post/yi): 01.AI의 6B-34B 모델. 다국어, 긴 컨텍스트 지원.
- [Gemma](/post/gemma): Google의 2B-7B 경량 오픈 모델. Gemini 기술 기반.
- [Phi-3](/post/phi-3): Microsoft의 소형 모델(3.8B). 고품질 합성 데이터로 학습.
- [OLMo](/post/olmo): AI2의 완전 오픈소스(코드, 데이터, 학습 로그 전부 공개).
- [Falcon](/post/falcon): TII의 7B-180B 모델. 높은 품질의 웹 데이터로 학습.
- [Qwen2](/post/qwen2): Alibaba의 다국어 모델 시리즈.

**정렬 기법의 발전**

- [DPO](/post/dpo): Reward 모델 없이 직접 선호도 최적화. RLHF의 단순화된 대안.
- [Self-Rewarding LM](/post/self-rewarding-lm): 모델이 스스로 보상 신호를 생성하여 자기 개선.

### Era 4: MoE, 추론, 프론티어 (2024-현재)

MoE(Mixture of Experts) 아키텍처의 대중화, 추론(Reasoning) 특화 모델, 그리고 프론티어 모델의 지속적인 발전이 이 시기의 특징입니다.

**MoE 아키텍처의 부상**

- [DeepSeek-V2](/post/deepseek-v2): Multi-Head Latent Attention(MLA) + DeepSeekMoE. 효율적인 MoE 설계.
- [DeepSeek-V3](/post/deepseek-v3): Auxiliary-loss-free 부하 분산. 671B 파라미터, 37B 활성화.
- [Switch Transformer](/post/switch-transformer): 각 토큰을 하나의 전문가에게만 라우팅하는 단순화된 MoE.
- [Qwen2.5](/post/qwen2-5): 72B까지 확장된 다국어 MoE 모델.
- [LLaMA 3](/post/llama-3): Meta의 405B 최대 오픈소스 모델.

**추론 특화 모델**

- [DeepSeek-R1](/post/deepseek-r1): RL 기반 추론 학습. 수학/코딩에서 o1 수준 성능.
- [DeepSeek-R1-Zero](/post/deepseek-r1-zero): 지도학습 없이 순수 RL만으로 추론 능력 학습.
- [O1](/post/o1): OpenAI의 추론 모델. Chain-of-Thought를 내부적으로 수행.
- [O3](/post/o3): O1의 후속. 과학/수학 추론에서 전문가 수준.
- [Phi-4-Reasoning](/post/phi-4-reasoning): 소형 모델에서의 추론 능력.

**프론티어 모델**

- [GPT-4](/post/gpt-4): 멀티모달 입력 지원. 전문가 시험에서 인간 수준.
- [GPT-4o](/post/gpt-4o): 옴니모달. 텍스트, 이미지, 오디오 통합 처리.
- [GPT-5](/post/gpt-5): 추론 능력의 대폭 향상.
- [Claude](/post/claude): Anthropic의 안전성 중심 LLM.
- [Claude 4](/post/claude-4): 코딩, 추론, 에이전트 능력 강화.
- [Gemini](/post/gemini): Google의 네이티브 멀티모달 모델.
- [Gemini 2.5](/post/gemini-2-5): 100만 토큰 컨텍스트. 고급 추론.
- [Qwen3](/post/qwen3): 하이브리드 사고 모델. 다국어 확장.
- [Kimi-K2](/post/kimi-k2): Muon 옵티마이저 기반 MoE.

---

## 주요 LLM 아키텍처 요약 테이블

| 모델 | 연도 | 크기 | 핵심 기여 | 유형 |
|------|------|------|----------|------|
| [Transformer](/post/transformer) | 2017 | - | Self-Attention 아키텍처 | 기초 |
| [GPT-1](/post/gpt-1) | 2018 | 117M | Decoder 사전학습 | Decoder |
| [BERT](/post/bert) | 2018 | 340M | 양방향 사전학습 | Encoder |
| [GPT-2](/post/gpt-2) | 2019 | 1.5B | Zero-shot 능력 | Decoder |
| [T5](/post/t5) | 2019 | 11B | Text-to-Text 통합 | Enc-Dec |
| [GPT-3](/post/gpt-3) | 2020 | 175B | Few-shot, ICL | Decoder |
| [PaLM](/post/palm) | 2022 | 540B | Pathways, CoT 확인 | Decoder |
| [Chinchilla](/post/chinchilla) | 2022 | 70B | Compute-optimal 스케일링 | Decoder |
| [LLaMA](/post/llama) | 2023 | 7-65B | 오픈소스 LLM | Decoder |
| [LLaMA 2](/post/llama-2) | 2023 | 7-70B | RLHF, 상업 허가 | Decoder |
| [Mistral 7B](/post/mistral-7b) | 2023 | 7B | SWA, GQA | Decoder |
| [Mixtral](/post/mixtral) | 2023 | 8x7B | Sparse MoE | MoE |
| [Gemma](/post/gemma) | 2023 | 2-7B | Gemini 기술 기반 경량 모델 | Decoder |
| [Phi-3](/post/phi-3) | 2024 | 3.8B | 합성 데이터 학습 | Decoder |
| [Qwen2](/post/qwen2) | 2024 | 0.5-72B | 다국어 | Decoder |
| [DeepSeek-V2](/post/deepseek-v2) | 2024 | 236B | MLA + MoE | MoE |
| [DeepSeek-V3](/post/deepseek-v3) | 2024 | 671B | Aux-loss-free MoE | MoE |
| [LLaMA 3](/post/llama-3) | 2024 | 8-405B | 최대 오픈소스 | Decoder |
| [DeepSeek-R1](/post/deepseek-r1) | 2025 | 671B | RL 기반 추론 | MoE |
| [GPT-5](/post/gpt-5) | 2025 | - | 고급 추론 | Decoder |
| [Claude 4](/post/claude-4) | 2025 | - | 코딩/에이전트 | Decoder |
| [Qwen3](/post/qwen3) | 2025 | 0.6-235B | 하이브리드 사고 | MoE |

---

## LLM의 핵심 기술 요소

### 1. 아키텍처 혁신

Transformer 기본 구조 위에 다양한 개선이 이루어졌습니다.

- **Attention 개선**: [GQA (Grouped-Query Attention)](/post/gqa), [MLA (Multi-Head Latent Attention)](/post/deepseek-v2)
- **위치 인코딩**: [RoPE (Rotary Position Embedding)](/post/roformer-rope)
- **정규화**: [Pre-Norm vs Post-Norm](/post/layer-norm-transformer)
- **MoE**: [Switch Transformer](/post/switch-transformer), [Mixtral](/post/mixtral), [DeepSeek-V3](/post/deepseek-v3)
- **대안 아키텍처**: [FNet](/post/fnet) (FFT 기반), [RetNet](/post/retnet) (Retention 메커니즘)

### 2. 스케일링 이론

- [Scaling Laws](/post/scaling-laws): 파라미터, 데이터, 연산량의 Power Law 관계
- [Chinchilla](/post/chinchilla): Compute-optimal 스케일링 → 데이터 중심 접근
- [Scaling Data-Constrained](/post/scaling-data-constrained): 데이터 제약 하의 스케일링
- [Sheared LLaMA](/post/sheared-llama): 구조적 가지치기를 통한 모델 축소

### 3. 정렬(Alignment)

- [InstructGPT](/post/instructgpt): SFT → Reward Model → PPO 파이프라인
- [Constitutional AI](/post/constitutional-ai): 자기 비판 기반 정렬
- [DPO](/post/dpo): Reward Model 없는 직접 최적화
- [Training Helpful and Harmless](/post/training-helpful-harmless): 유용성과 안전성의 균형

### 4. 효율적 학습과 추론

- [LoRA](/post/lora): Low-Rank Adaptation. 소수 파라미터만 학습.
- [QLoRA](/post/qlora): 4bit 양자화 + LoRA. 소비자 GPU로 학습 가능.
- [Flash Attention](/post/flash-attention): IO-aware 어텐션으로 메모리 절감.
- [Flash Attention 2](/post/flash-attention-2): 더 나은 병렬화와 워크 분배.
- [Speculative Decoding](/post/speculative-decoding): 작은 모델로 초안, 큰 모델로 검증.
- [Paged Attention (vLLM)](/post/paged-attention): 메모리 페이징으로 배치 처리 효율화.

### 5. 프롬프팅과 추론

- [Chain-of-Thought](/post/cot): 단계별 추론으로 복잡한 문제 해결
- [Tree of Thoughts](/post/tree-of-thoughts): 여러 추론 경로 탐색
- [Self-Consistency](/post/self-consistency): 다수결로 답변 신뢰도 향상
- [In-context Learning](/post/gpt-3): 예시만으로 태스크 학습

---

## 추천 학습 경로

### 초심자 (LLM 입문)

Transformer부터 시작하여 핵심 사전학습 모델을 이해합니다.

1. [Transformer](/post/transformer) — 모든 LLM의 기초
2. [BERT](/post/bert) — 양방향 사전학습의 이해
3. [GPT-3](/post/gpt-3) — 스케일링과 Few-shot Learning
4. [LLaMA](/post/llama) — 오픈소스 LLM의 구조
5. [InstructGPT](/post/instructgpt) — RLHF를 통한 정렬

### 중급 (아키텍처 심화)

효율적인 설계와 학습 기법을 깊이 이해합니다.

1. [Scaling Laws](/post/scaling-laws) + [Chinchilla](/post/chinchilla) — 스케일링 이론
2. [GQA](/post/gqa) + [RoPE](/post/roformer-rope) — 어텐션 최적화
3. [LoRA](/post/lora) + [QLoRA](/post/qlora) — 효율적 파인튜닝
4. [Flash Attention](/post/flash-attention) — 메모리 효율적 어텐션
5. [Mixtral](/post/mixtral) + [DeepSeek-V2](/post/deepseek-v2) — MoE 아키텍처
6. [DPO](/post/dpo) — 정렬 기법

### 고급 (최신 연구)

최전선의 연구 동향을 추적합니다.

1. [DeepSeek-V3](/post/deepseek-v3) — 최신 MoE 설계
2. [DeepSeek-R1](/post/deepseek-r1) — RL 기반 추론 학습
3. [Qwen3](/post/qwen3) — 하이브리드 사고 모델
4. [GPT-5](/post/gpt-5) + [Claude 4](/post/claude-4) — 프론티어 모델 분석
5. [Speculative Decoding](/post/speculative-decoding) + [Paged Attention](/post/paged-attention) — 추론 최적화
6. [Scaling Data-Constrained](/post/scaling-data-constrained) — 데이터 제약 연구

---

## 관련 카테고리

- [AI/ML 아키텍처 로드맵](/post/ai-ml-architecture-roadmap) — 전체 AI/ML 지형도
- [AI 핵심 기법 총정리](/post/ai-core-techniques-guide) — LLM에 사용되는 핵심 기법들
- [State Space Models 가이드](/post/state-space-models-guide) — Transformer의 대안 아키텍처
- [AI Agent 기술 지도](/post/ai-agent-technology-guide) — LLM 기반 에이전트 시스템
