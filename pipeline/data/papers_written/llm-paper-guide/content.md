<!-- infographic-hero -->
![LLM Core Paper Guide: Evolution of Language Models 핵심 요약](figures/infographic.svg)

*Figure: LLM Core Paper Guide: Evolution of Language Models 한 장 요약 인포그래픽*

# LLM 핵심 논문 가이드: 언어 모델의 진화

## 개요

대규모 언어 모델(Large Language Model, LLM)은 현대 AI의 핵심 기술입니다. 2017년 [[1_attention-is-all-you-need]]의 등장 이후 불과 8년 만에, 단순한 텍스트 생성기에서 범용 추론 엔진으로 변모했습니다. GPT와 BERT로 시작된 사전학습 혁명은 수천억 파라미터의 거대 모델, 효율적인 오픈소스 생태계, 그리고 수학 올림피아드를 푸는 추론 특화 모델로까지 발전했습니다.

이 가이드는 LLM의 핵심 논문과 아키텍처를 **시간순으로 정리**하고, 각 모델의 핵심 기여와 상호 영향 관계를 체계적으로 설명합니다. 수십 편의 논문을 개별적으로 읽기 전에, 먼저 이 가이드를 통해 전체 지형도를 파악하시기를 권합니다.

:::tip
이 가이드는 로드맵 성격의 개관 포스트입니다. 개별 모델의 심층 분석은 각 논문 리뷰 포스트에서 다루며, 아키텍처 기법의 상세 설명은 [[ai-core-techniques-guide]]를, 전체 AI/ML 지형도는 [[ai-ml-architecture-roadmap]]를 참고하세요.
:::

### 왜 LLM 논문을 체계적으로 공부해야 하는가?

LLM 분야는 매우 빠르게 발전하지만, 핵심 아이디어의 계보를 따라가면 뚜렷한 흐름이 보입니다.

| 발전 축 | 핵심 질문 | 대표 논문 |
|---------|----------|----------|
| Transformer | 시퀀스를 어떻게 병렬 처리할까? | Attention Is All You Need |
| Pre-training | 레이블 없는 데이터로 어떻게 학습할까? | GPT, BERT |
| Scaling | 모델을 키우면 무엇이 달라질까? | GPT-3, Scaling Laws |
| Alignment | 인간의 의도에 어떻게 맞출까? | InstructGPT, DPO |
| Efficiency | 더 적은 비용으로 같은 성능을 낼 수 있을까? | LLaMA, Mixtral, LoRA |
| Reasoning | LLM이 실제로 "사고"할 수 있을까? | O1, DeepSeek-R1 |

이 여섯 가지 축을 이해하면, 새로운 모델이 등장해도 그 위치를 빠르게 파악할 수 있습니다.

---

## Transformer 아키텍처의 세 갈래

현대 LLM을 이해하려면 Transformer 아키텍처가 세 가지 변형으로 분화된 과정을 먼저 파악해야 합니다. 원래 Transformer는 Encoder와 Decoder를 모두 갖춘 구조였지만, 이후 연구자들은 각각의 컴포넌트를 독립적으로 활용하는 방향으로 발전시켰습니다.

| 구분 | Encoder-only | Decoder-only | Encoder-Decoder |
|------|-------------|-------------|-----------------|
| 대표 모델 | BERT, RoBERTa, DeBERTa | GPT 시리즈, LLaMA, Mistral | T5, BART, UL2 |
| 학습 목적함수 | Masked Language Model (MLM) | Causal Language Model (CLM) | Span Corruption / Denoising |
| 입력 처리 | 양방향 (bidirectional) | 단방향 (autoregressive) | 양방향 인코딩 + 자기회귀 디코딩 |
| 주요 용도 | 분류, NER, 문장 유사도 | 텍스트 생성, 대화, 코드 | 번역, 요약, QA |
| 추론 방식 | 입력 전체를 한 번에 처리 | 토큰을 하나씩 순차 생성 | 입력 인코딩 후 순차 생성 |
| 스케일링 추세 | 수억 파라미터에서 정체 | 수천억 이상으로 계속 성장 | 110억(T5)에서 사실상 정체 |
| 현재 위상 | NLU 특화 태스크에서 여전히 활용 | LLM의 주류 아키텍처 | 일부 특수 태스크에서 사용 |

2020년 이후 LLM의 주류는 **Decoder-only** 아키텍처로 수렴했습니다. 그 이유는 단순합니다. 자기회귀 방식의 next-token prediction이 스케일링에 가장 유리하고, 충분히 큰 모델은 프롬프트만으로도 분류/추출/번역 등 거의 모든 NLP 태스크를 수행할 수 있기 때문입니다.

---

## 핵심 흐름: LLM 발전 타임라인

### Era 1: Transformer와 사전학습 (2017-2019)

현대 LLM의 근간이 되는 아키텍처와 사전학습 패러다임이 확립된 시기입니다.

**2017: Transformer의 탄생**

- [[1_attention-is-all-you-need]]: Self-Attention만으로 시퀀스 처리. Encoder-Decoder 구조로 번역 SOTA 달성. 모든 현대 LLM의 시작점.

**2018: 사전학습 혁명**

- [ELMo](/post/elmo): 문맥 의존적 단어 표현. BiLSTM 기반이지만 사전학습의 중요성을 입증.
- [GPT-1](/post/gpt-1): Transformer Decoder 기반 단방향 사전학습. 파인튜닝으로 다양한 NLP 태스크 해결. "사전학습 + 파인튜닝" 패러다임의 시작.
- [BERT](/post/bert): Transformer Encoder 기반 양방향 사전학습. Masked Language Model + Next Sentence Prediction으로 NLP 벤치마크 대부분에서 SOTA 달성.

**2019: BERT 변형과 확장**

- [RoBERTa](/post/roberta): BERT의 학습 전략 최적화. 더 많은 데이터, 더 긴 학습, Dynamic Masking.
- [ALBERT](/post/albert): 파라미터 공유로 BERT 경량화. Factorized Embedding, Cross-Layer Parameter Sharing.
- [XLNet](/post/xlnet): Permutation Language Model. 양방향 문맥을 자기회귀 방식으로 학습.
- [DistilBERT](/post/distilbert): Knowledge Distillation으로 BERT 60% 크기에 97% 성능 유지.
- [ELECTRA](/post/electra): Replaced Token Detection. Generator-Discriminator 구조로 효율적 학습.
- [DeBERTa](/post/deberta): Disentangled Attention. 위치와 내용 정보를 분리하여 처리.
- [GPT-2](/post/gpt-2): 1.5B 파라미터. Zero-shot 능력의 출현. "충분히 큰 언어 모델은 별도 학습 없이도 태스크를 수행한다."
- [[t5]]: 모든 NLP 태스크를 Text-to-Text 형식으로 통합. Encoder-Decoder 구조의 집대성.

### Era 2: 스케일링과 거대 모델 (2020-2022)

모델 크기를 키우면 새로운 능력이 창발(emergent)한다는 발견이 거대 모델 경쟁을 촉발했습니다.

**2020: 스케일링의 발견**

- [GPT-3](/post/gpt-3): 175B 파라미터. Few-shot Learning이 파인튜닝 없이도 가능함을 입증. In-context Learning의 시작.
- [Scaling Laws](/post/scaling-laws): 모델 크기, 데이터 크기, 연산량의 관계를 수학적으로 규명. Power Law 관계 발견.

**2021-2022: 대형 모델 경쟁**

- [Gopher](/post/gopher): DeepMind의 280B 모델. 지식 집약적 태스크에서 강점.
- [PaLM](/post/palm): Google의 540B 모델. Pathways 시스템으로 학습. Chain-of-Thought 추론 능력 확인.
- [BLOOM](/post/bloom): BigScience 프로젝트. 176B 오픈소스 다국어 모델.
- [Chinchilla](/post/chinchilla): 데이터 중심 스케일링. 같은 연산량이면 모델을 키우는 것보다 데이터를 늘리는 게 효율적.
- [OPT](/post/opt): Meta의 175B 오픈소스 모델. 학습 로그 공개로 재현성 확보.
- [FLAN-T5](/post/flan-t5): Instruction Tuning으로 T5 성능 대폭 향상. 다양한 태스크를 지시문으로 통합.

**2022: 정렬(Alignment)의 시대**

- [InstructGPT](/post/instructgpt): RLHF(Reinforcement Learning from Human Feedback)로 모델 정렬. ChatGPT의 기반 기술.
- [Constitutional AI](/post/constitutional-ai): Anthropic의 자기 개선 정렬 방식. AI가 스스로 피드백을 생성하고 개선.
- [UL2](/post/ul2): Mixture-of-Denoisers. 다양한 사전학습 목적함수를 하나로 통합.

### Era 3: 오픈소스와 효율화 (2023)

LLaMA의 등장으로 오픈소스 LLM 생태계가 폭발적으로 성장했습니다. "작지만 강한 모델"이 거대 모델에 대한 실질적 대안이 될 수 있음을 입증한 시기입니다.

**오픈소스 LLM의 폭발**

- [LLaMA](/post/llama): Meta의 7B-65B 오픈소스 모델. 작은 모델로도 경쟁력 있는 성능을 보여 오픈소스 LLM 시대를 개막.
- [LLaMA 2](/post/llama-2): 7B-70B. RLHF 적용, 상업적 사용 허가. Safety 학습 포함.
- [Mistral 7B](/post/mistral-7b): Sliding Window Attention, Grouped-Query Attention. 7B 모델로 LLaMA-2 13B 능가.
- [Mixtral](/post/mixtral): Sparse Mixture of Experts(MoE). 8개 전문가 중 2개만 활성화하여 효율적 추론.
- [Yi](/post/yi): 01.AI의 6B-34B 모델. 다국어, 긴 컨텍스트 지원.
- [Gemma](/post/gemma): Google의 2B-7B 경량 오픈 모델. Gemini 기술 기반.
- [Phi-3](/post/phi-3): Microsoft의 소형 모델(3.8B). 고품질 합성 데이터로 학습하여 크기 대비 높은 성능.
- [OLMo](/post/olmo): AI2의 완전 오픈소스(코드, 데이터, 학습 로그 전부 공개).
- [Falcon](/post/falcon): TII의 7B-180B 모델. 높은 품질의 웹 데이터로 학습.
- [Qwen2](/post/qwen2): Alibaba의 다국어 모델 시리즈. 0.5B부터 72B까지 다양한 크기.

**정렬 기법의 발전**

- [DPO](/post/dpo): Reward 모델 없이 직접 선호도 최적화. RLHF의 단순화된 대안으로 급부상.
- [Self-Rewarding LM](/post/self-rewarding-lm): 모델이 스스로 보상 신호를 생성하여 자기 개선.

### Era 4: MoE, 추론, 프론티어 (2024-현재)

MoE(Mixture of Experts) 아키텍처의 대중화, 추론(Reasoning) 특화 모델, 그리고 프론티어 모델의 지속적인 발전이 이 시기의 특징입니다.

**MoE 아키텍처의 부상**

- [DeepSeek-V2](/post/deepseek-v2): Multi-Head Latent Attention(MLA) + DeepSeekMoE. 효율적인 MoE 설계의 새로운 기준.
- [DeepSeek-V3](/post/deepseek-v3): Auxiliary-loss-free 부하 분산. 671B 파라미터 중 37B만 활성화.
- [Switch Transformer](/post/switch-transformer): 각 토큰을 하나의 전문가에게만 라우팅하는 단순화된 MoE.
- [Qwen2.5](/post/qwen2-5): 72B까지 확장된 다국어 MoE 모델.
- [[llama-3]]: Meta의 405B 최대 오픈소스 모델. Dense 아키텍처의 한계를 탐색.

**추론 특화 모델**

- [[deepseek-r1]]: RL 기반 추론 학습. 수학/코딩에서 O1 수준 성능. 오픈소스로 공개되어 추론 모델 연구를 가속화.
- [DeepSeek-R1-Zero](/post/deepseek-r1-zero): 지도학습 없이 순수 RL만으로 추론 능력 학습. "RL만으로도 체계적 사고가 출현한다"는 놀라운 발견.
- [O1](/post/o1): OpenAI의 추론 모델. Chain-of-Thought를 내부적으로 수행하여 복잡한 문제 해결.
- [O3](/post/o3): O1의 후속. 과학/수학 추론에서 전문가 수준. ARC-AGI 벤치마크에서 획기적 성능.
- [Phi-4-Reasoning](/post/phi-4-reasoning): 소형 모델에서도 추론 능력이 가능함을 입증.

**프론티어 모델**

- [[gpt-4]]: 멀티모달 입력 지원. 전문가 시험에서 인간 수준 성능 달성.
- [GPT-4o](/post/gpt-4o): 옴니모달. 텍스트, 이미지, 오디오를 하나의 모델로 통합 처리.
- [GPT-5](/post/gpt-5): 추론 능력의 대폭 향상. 에이전트 활용에 최적화.
- [Claude](/post/claude): Anthropic의 안전성 중심 LLM. Constitutional AI 기반 정렬.
- [Claude 4](/post/claude-4): 코딩, 추론, 에이전트 능력 강화. 장시간 자율 작업 수행 능력.
- [[gemini]]: Google의 네이티브 멀티모달 모델. 텍스트/이미지/비디오/코드 통합.
- [Gemini 2.5](/post/gemini-2-5): 100만 토큰 컨텍스트. 고급 추론 능력.
- [Qwen3](/post/qwen3): 하이브리드 사고 모델. "생각 모드"와 "즉답 모드" 전환 가능.
- [Kimi-K2](/post/kimi-k2): Muon 옵티마이저 기반 MoE. 새로운 최적화 기법 적용.

---

## 주요 LLM 아키텍처 요약 테이블

| 모델 | 연도 | 크기 | 핵심 기여 | 유형 |
|------|------|------|----------|------|
| [[1_attention-is-all-you-need]] | 2017 | - | Self-Attention 아키텍처 | 기초 |
| [GPT-1](/post/gpt-1) | 2018 | 117M | Decoder 사전학습 | Decoder |
| [BERT](/post/bert) | 2018 | 340M | 양방향 사전학습 (MLM) | Encoder |
| [GPT-2](/post/gpt-2) | 2019 | 1.5B | Zero-shot 능력 | Decoder |
| [[t5]] | 2019 | 11B | Text-to-Text 통합 | Enc-Dec |
| [GPT-3](/post/gpt-3) | 2020 | 175B | Few-shot, In-context Learning | Decoder |
| [PaLM](/post/palm) | 2022 | 540B | Pathways, CoT 확인 | Decoder |
| [Chinchilla](/post/chinchilla) | 2022 | 70B | Compute-optimal 스케일링 | Decoder |
| [LLaMA](/post/llama) | 2023 | 7-65B | 오픈소스 LLM 시대 개막 | Decoder |
| [LLaMA 2](/post/llama-2) | 2023 | 7-70B | RLHF, 상업 허가 | Decoder |
| [Mistral 7B](/post/mistral-7b) | 2023 | 7B | SWA, GQA | Decoder |
| [Mixtral](/post/mixtral) | 2023 | 8x7B | Sparse MoE | MoE |
| [Phi-3](/post/phi-3) | 2024 | 3.8B | 합성 데이터 학습 | Decoder |
| [DeepSeek-V2](/post/deepseek-v2) | 2024 | 236B | MLA + MoE | MoE |
| [DeepSeek-V3](/post/deepseek-v3) | 2024 | 671B | Aux-loss-free MoE | MoE |
| [[llama-3]] | 2024 | 8-405B | 최대 오픈소스 Dense 모델 | Decoder |
| [[deepseek-r1]] | 2025 | 671B | RL 기반 추론 | MoE |
| [[gpt-4]] | 2023 | - | 멀티모달, 전문가 수준 | Decoder |
| [Claude 4](/post/claude-4) | 2025 | - | 코딩/에이전트 특화 | Decoder |
| [Qwen3](/post/qwen3) | 2025 | 0.6-235B | 하이브리드 사고 | MoE |

---

## LLM의 핵심 기술 요소

### 1. Attention 메커니즘의 진화

Transformer의 핵심인 Attention은 지속적으로 개선되어 왔습니다. 원래의 Multi-Head Attention(MHA)에서 시작하여 추론 효율성과 성능을 동시에 추구하는 방향으로 발전했습니다.

| Attention 유형 | 제안 모델 | 핵심 아이디어 | KV Cache | 성능 |
|---------------|----------|-------------|----------|------|
| MHA (Multi-Head Attention) | Transformer (2017) | 각 헤드가 독립적인 Q, K, V | 헤드 수 x 차원 | 기준선 |
| MQA (Multi-Query Attention) | PaLM (2022) | 모든 헤드가 하나의 K, V 공유 | 1 x 차원 | 약간 하락 |
| GQA (Grouped-Query Attention) | LLaMA 2 (2023) | 헤드를 그룹으로 묶어 K, V 공유 | 그룹 수 x 차원 | MHA에 근접 |
| MLA (Multi-Head Latent Attention) | DeepSeek-V2 (2024) | K, V를 저랭크 잠재 공간으로 압축 | 매우 작음 | MHA 이상 |

MHA에서 GQA로의 전환은 LLaMA 2에서 시작되어 이제 거의 모든 최신 LLM이 채택하고 있습니다. DeepSeek-V2가 제안한 MLA는 KV Cache를 극적으로 줄이면서도 성능을 유지하는 새로운 접근법으로, DeepSeek-V3와 R1에서 그 효과가 입증되었습니다.

### 2. 위치 인코딩(Positional Encoding)

Transformer는 본질적으로 순서 정보가 없기 때문에 위치 인코딩이 필수적입니다. 위치 인코딩의 선택은 모델이 처리할 수 있는 컨텍스트 길이에 직접적인 영향을 미칩니다.

| 방식 | 유형 | 최대 길이 | 외삽 가능성 | 사용 모델 |
|------|------|----------|-----------|----------|
| Sinusoidal | 절대 위치 | 학습 시 고정 | 제한적 | 원래 Transformer |
| Learned Positional Embedding | 절대 위치 | 학습 시 고정 | 불가 | GPT-2, BERT |
| RoPE (Rotary Position Embedding) | 상대 위치 | 이론상 무한 | 좋음 | LLaMA, Qwen, Mistral |
| ALiBi (Attention with Linear Biases) | 상대 위치 | 이론상 무한 | 매우 좋음 | BLOOM, Falcon |
| YaRN | RoPE 확장 | 128K+ | 매우 좋음 | Mistral, Yi |

현재 주류는 **RoPE**입니다. 회전 행렬을 이용해 상대 위치 정보를 인코딩하며, NTK-aware scaling이나 YaRN 같은 확장 기법을 통해 학습 시보다 훨씬 긴 컨텍스트로 외삽(extrapolation)이 가능합니다. LLaMA, Qwen, Mistral 등 대부분의 최신 오픈소스 LLM이 RoPE를 채택하고 있습니다.

### 3. 스케일링 법칙(Scaling Laws)

스케일링 법칙은 LLM 연구의 방향을 결정하는 핵심 이론입니다. 두 가지 주요 연구가 LLM 개발 전략을 근본적으로 바꿨습니다.

**Kaplan Scaling Laws (2020, OpenAI)**

모델 파라미터 수 $N$, 데이터셋 크기 $D$, 연산량 $C$와 손실 $L$ 사이에 멱법칙(power law) 관계가 성립함을 발견했습니다.

$$L(N) \propto N^{-0.076}$$

핵심 주장: 고정된 연산 예산에서는 **모델 크기를 키우는 것**이 가장 효율적이다. 이 결론이 GPT-3(175B), PaLM(540B) 등 거대 모델 경쟁을 촉발했습니다.

**Chinchilla Scaling Laws (2022, DeepMind)**

Kaplan의 결론을 뒤집으며, 최적의 연산 배분은 모델 크기와 학습 데이터 크기를 **동일한 비율로 증가**시키는 것이라고 주장했습니다.

$$N_{opt} \propto C^{0.5}, \quad D_{opt} \propto C^{0.5}$$

핵심 결과: 70B 파라미터의 Chinchilla가 280B의 Gopher를 능가. 이후 LLaMA, Mistral 등 "작지만 충분한 데이터로 학습한 모델"이 주류가 되었습니다.

| 비교 항목 | Kaplan (2020) | Chinchilla (2022) |
|----------|-------------|------------------|
| 핵심 주장 | 모델을 키워라 | 모델과 데이터를 균형 있게 키워라 |
| 최적 비율 | 모델 크기 우선 | N:D 비율 약 1:20 |
| 결과 | GPT-3 (175B, 300B 토큰) | Chinchilla (70B, 1.4T 토큰) |
| 영향 | 거대 모델 경쟁 촉발 | 데이터 중심 접근으로 전환 |

### 4. MoE(Mixture of Experts) 아키텍처

MoE는 "모든 파라미터를 항상 사용할 필요는 없다"는 간단한 통찰에서 출발합니다. 전체 파라미터 수는 크지만 각 입력에 대해 일부 전문가(Expert)만 활성화하여, Dense 모델 대비 같은 추론 비용으로 훨씬 큰 모델 용량을 확보합니다.

**MoE의 핵심 구조:**

- **전문가(Expert)**: 각각 독립적인 FFN(Feed-Forward Network) 레이어
- **라우터(Router)**: 각 토큰을 어떤 전문가에게 보낼지 결정하는 게이팅 네트워크
- **Top-K 라우팅**: 전체 전문가 중 K개만 활성화 (Mixtral: Top-2, Switch: Top-1)

| MoE 모델 | 전체 파라미터 | 활성화 파라미터 | 전문가 수 | 라우팅 방식 | 핵심 혁신 |
|----------|-------------|--------------|----------|-----------|----------|
| Switch Transformer | 1.6T | ~100B | 128 | Top-1 | 단순화된 라우팅 |
| Mixtral 8x7B | 46.7B | 12.9B | 8 | Top-2 | Sparse MoE 대중화 |
| DeepSeek-V2 | 236B | 21B | 160 | Top-6 | Fine-grained Expert |
| DeepSeek-V3 | 671B | 37B | 256 | Top-8 | Aux-loss-free 부하 분산 |
| Qwen3 | 235B | ~22B | 128 | Top-8 | 하이브리드 사고 |

:::warning
MoE의 핵심 도전 과제는 **부하 분산(Load Balancing)**입니다. 특정 전문가에게 토큰이 집중되면 효율이 떨어지고 학습이 불안정해집니다. 초기에는 auxiliary loss를 추가하여 이를 해결했으나, DeepSeek-V3는 auxiliary loss 없이도 부하를 분산하는 방법을 제안하여 학습 안정성과 성능을 동시에 개선했습니다.
:::

### 5. 학습 파이프라인: Pre-training에서 RLHF까지

현대 LLM의 학습은 단순한 한 단계가 아니라 여러 단계의 정교한 파이프라인입니다.

| 단계 | 목적 | 데이터 | 연산 비용 | 결과 |
|------|------|--------|----------|------|
| **Pre-training** | 언어 이해/생성 능력 습득 | 수조 토큰의 웹 텍스트 | 매우 높음 (수백만 GPU-hours) | Base 모델 (GPT-3, LLaMA) |
| **SFT (Supervised Fine-Tuning)** | 지시 따르기 능력 | 수만~수십만 개의 instruction-response 쌍 | 중간 | Instruction 모델 |
| **RM (Reward Modeling)** | 인간 선호도 학습 | 응답 쌍에 대한 인간 비교 데이터 | 중간 | Reward Model |
| **RLHF / PPO** | 인간 선호에 맞춘 최적화 | RM의 보상 신호 | 높음 | 정렬된 모델 (ChatGPT) |
| **DPO** | RLHF의 단순화된 대안 | 선호/비선호 응답 쌍 | 중간 | 정렬된 모델 (Zephyr 등) |

이 파이프라인의 핵심 전환점은 **InstructGPT(2022)**입니다. Pre-training만으로는 사용자의 의도를 정확히 따르는 모델을 만들 수 없다는 것을 보여주며, SFT + RLHF 파이프라인을 확립했습니다. 이후 DPO는 복잡한 PPO 과정을 단일 손실 함수로 대체하여, 정렬 학습의 진입 장벽을 크게 낮췄습니다.

### 6. 추론 특화 모델(Reasoning Models)

2024년 후반부터 등장한 추론 특화 모델은 LLM의 새로운 패러다임을 열었습니다. 기존 LLM이 "빠르게 대답하는" System 1 사고였다면, 추론 모델은 "천천히 깊이 생각하는" System 2 사고를 구현합니다.

**O1 (OpenAI, 2024)**

- 내부 Chain-of-Thought를 통해 복잡한 문제를 단계적으로 해결
- 수학 올림피아드, 코딩 대회에서 전문가 수준 성능
- 추론 시간(test-time compute)을 늘릴수록 성능 향상

**DeepSeek-R1 (DeepSeek, 2025)**

- 순수 RL만으로 추론 능력을 학습한 R1-Zero가 먼저 등장
- R1-Zero에서 발견: RL만으로도 자기 검증, 반성, 단계적 추론이 자연 발생
- R1은 SFT + RL 파이프라인으로 안정성과 가독성 개선
- 오픈소스 공개로 추론 모델 연구의 민주화에 기여

추론 모델의 핵심 통찰은 **test-time compute scaling**입니다. 학습 시 연산량만이 아니라 추론 시 연산량도 성능에 직접 영향을 미친다는 것입니다. 이는 기존 Scaling Laws를 추론 시점으로 확장한 새로운 패러다임입니다.

### 7. 효율적 학습과 추론

LLM을 더 적은 자원으로 학습하고, 더 빠르게 추론하기 위한 기법들입니다.

**파인튜닝 효율화:**

- [LoRA](/post/lora): Low-Rank Adaptation. 원래 가중치를 동결하고 저랭크 행렬만 학습. 학습 파라미터를 0.1% 수준으로 축소.
- [QLoRA](/post/qlora): 4bit 양자화 + LoRA. 단일 소비자 GPU(48GB)로 65B 모델 파인튜닝 가능.

**추론 가속화:**

- [Flash Attention](/post/flash-attention): IO-aware 어텐션으로 메모리 접근을 최적화. 어텐션 연산 2-4배 가속.
- [Flash Attention 2](/post/flash-attention-2): 더 나은 병렬화와 워크 분배. 추가 2배 가속.
- [Speculative Decoding](/post/speculative-decoding): 작은 모델로 여러 토큰을 빠르게 생성(초안), 큰 모델로 한 번에 검증. 품질 손실 없이 2-3배 가속.
- [Paged Attention (vLLM)](/post/paged-attention): OS의 가상 메모리 페이징 개념을 KV Cache에 적용. 배치 처리 효율 대폭 향상.

### 8. 프롬프팅과 추론 기법

LLM의 성능을 학습 없이 끌어올리는 추론 시점 기법들입니다.

- [Chain-of-Thought (CoT)](/post/cot): "단계별로 생각해봐"라는 지시만으로 추론 능력 향상. PaLM에서 효과 입증.
- [Tree of Thoughts](/post/tree-of-thoughts): 여러 추론 경로를 트리 형태로 탐색. BFS/DFS로 최적 경로 발견.
- [Self-Consistency](/post/self-consistency): 같은 질문에 대해 여러 번 추론하고 다수결로 답변 신뢰도 향상.
- [In-context Learning](/post/gpt-3): 프롬프트에 예시를 포함하여 별도 학습 없이 태스크 수행.

---

## 추천 학습 경로

### 초심자 (LLM 입문)

Transformer의 기본 원리부터 시작하여 핵심 사전학습 모델과 정렬의 개념을 이해합니다.

| 순서 | 논문 | 학습 목표 | 예상 시간 |
|------|------|----------|----------|
| 1 | [[1_attention-is-all-you-need]] | Self-Attention, 인코더-디코더 구조 이해 | 3-4시간 |
| 2 | [BERT](/post/bert) | 양방향 사전학습, MLM 이해 | 2-3시간 |
| 3 | [GPT-3](/post/gpt-3) | 스케일링, Few-shot, In-context Learning | 2-3시간 |
| 4 | [LLaMA](/post/llama) | 현대 오픈소스 LLM의 구조 파악 | 2시간 |
| 5 | [InstructGPT](/post/instructgpt) | RLHF, 정렬의 개념 | 2-3시간 |

### 중급 (아키텍처 심화)

효율적인 설계와 학습 기법을 깊이 이해하고, 직접 파인튜닝을 수행할 수 있는 수준을 목표로 합니다.

| 순서 | 논문 | 학습 목표 | 선수 지식 |
|------|------|----------|----------|
| 1 | [Scaling Laws](/post/scaling-laws) + [Chinchilla](/post/chinchilla) | 스케일링 이론, 최적 학습 전략 | 초심자 과정 |
| 2 | [GQA](/post/gqa) + [RoPE](/post/roformer-rope) | 어텐션 최적화, 위치 인코딩 | Transformer 구조 |
| 3 | [LoRA](/post/lora) + [QLoRA](/post/qlora) | 효율적 파인튜닝 실습 | 기본 파인튜닝 경험 |
| 4 | [Flash Attention](/post/flash-attention) | 메모리 효율적 어텐션의 원리 | GPU 메모리 구조 기초 |
| 5 | [Mixtral](/post/mixtral) + [DeepSeek-V2](/post/deepseek-v2) | MoE 아키텍처 이해 | 스케일링 법칙 |
| 6 | [DPO](/post/dpo) | Reward Model 없는 정렬 기법 | RLHF 개념 |

### 고급 (최신 연구)

최전선의 연구 동향을 추적하고, 새로운 모델의 기여를 비판적으로 평가할 수 있는 수준을 목표로 합니다.

| 순서 | 논문 | 학습 목표 | 핵심 포인트 |
|------|------|----------|-----------|
| 1 | [DeepSeek-V3](/post/deepseek-v3) | 최신 MoE 설계, aux-loss-free 분산 | 671B 파라미터의 효율적 활용 |
| 2 | [[deepseek-r1]] | RL 기반 추론 학습, R1-Zero의 발견 | 추론 능력의 자연 발생 |
| 3 | [Qwen3](/post/qwen3) | 하이브리드 사고 모델 | 생각/즉답 모드 전환 |
| 4 | [[gpt-4]] + [Claude 4](/post/claude-4) | 프론티어 모델 분석 | 멀티모달, 에이전트 |
| 5 | [Speculative Decoding](/post/speculative-decoding) + [Paged Attention](/post/paged-attention) | 추론 최적화 기법 | 실제 서빙 환경 적용 |
| 6 | [Scaling Data-Constrained](/post/scaling-data-constrained) | 데이터 제약 상황의 스케일링 | 합성 데이터, 데이터 반복 |

---

## LLM 기술 발전 연대표

| 연도 | 핵심 이벤트 | 의의 |
|------|-----------|------|
| 2017 | Transformer 발표 | Self-Attention 아키텍처 탄생 |
| 2018 | GPT-1, BERT 발표 | 사전학습 + 파인튜닝 패러다임 확립 |
| 2019 | GPT-2, T5, BERT 변형들 | Zero-shot 가능성 확인, Text-to-Text 통합 |
| 2020 | GPT-3, Scaling Laws | Few-shot Learning, 스케일링 이론 정립 |
| 2022 | Chinchilla, InstructGPT | 데이터 중심 스케일링, RLHF 정렬 |
| 2022.11 | ChatGPT 출시 | LLM의 대중화, AI 산업 폭발 |
| 2023.02 | LLaMA 공개 | 오픈소스 LLM 생태계 시작 |
| 2023.03 | GPT-4 발표 | 멀티모달 프론티어 모델 |
| 2023.12 | Mixtral, Gemini 발표 | MoE 대중화, 네이티브 멀티모달 |
| 2024.01 | DeepSeek-V2 발표 | MLA + Fine-grained MoE |
| 2024.09 | O1 발표 | 추론 특화 모델 패러다임 시작 |
| 2025.01 | DeepSeek-R1 공개 | 오픈소스 추론 모델, RL만으로 추론 발생 |
| 2025 | GPT-5, Claude 4, Gemini 2.5 | 프론티어 모델 세대 교체 |

---

## 앞으로의 전망: LLM의 미래 방향

현재 LLM 연구는 다음 방향으로 빠르게 움직이고 있습니다.

1. **추론 능력 강화**: O1, R1 이후 "더 오래 생각하면 더 잘 푸는" 패러다임이 확산. Test-time compute scaling이 학습 시점의 스케일링만큼 중요해지고 있습니다.

2. **효율성 추구**: MoE, 양자화, Speculative Decoding 등을 통해 같은 성능을 더 적은 비용으로 달성하려는 노력이 계속됩니다. DeepSeek-V3가 $5.5M으로 GPT-4급 성능을 달성한 것이 대표적입니다.

3. **멀티모달 통합**: 텍스트, 이미지, 오디오, 비디오를 하나의 모델로 처리하는 네이티브 멀티모달 아키텍처가 표준이 되고 있습니다.

4. **에이전트 활용**: LLM이 도구를 사용하고, 계획을 세우고, 장시간 자율적으로 작업을 수행하는 에이전트 패러다임이 부상하고 있습니다.

5. **오픈소스 생태계**: LLaMA, Qwen, DeepSeek 등 오픈소스 모델이 상용 모델과 대등한 성능을 달성하며, 연구의 민주화가 가속되고 있습니다.

---

## 관련 가이드

- [[ai-ml-architecture-roadmap]] : 전체 AI/ML 지형도에서 LLM의 위치
- [[ai-core-techniques-guide]] : LLM에 사용되는 Attention, Normalization, 최적화 기법 상세
- [State Space Models 가이드](/post/state-space-models-guide) : Transformer의 대안 아키텍처 (Mamba, S4)
- [AI Agent 기술 지도](/post/ai-agent-technology-guide) : LLM 기반 에이전트 시스템 설계
