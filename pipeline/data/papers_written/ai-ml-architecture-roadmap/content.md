# AI/ML 아키텍처 로드맵: Transformer에서 Agent까지

## 개요

인공지능과 머신러닝은 2017년 Transformer의 등장을 기점으로 폭발적인 발전을 이루었습니다. 단일 아키텍처에서 시작된 혁신은 자연어 처리, 이미지 생성, 컴퓨터 비전, 멀티모달, 자율 에이전트 등 다양한 영역으로 확장되었으며, 각 분야는 고유한 발전 궤적을 그리면서도 서로 깊이 연결되어 있습니다.

이 글은 AI/ML 분야의 **전체 지형도**를 조망합니다. 7개 핵심 영역 — LLM, Diffusion, Vision, SSM, Multimodal, Agent, Technique — 의 발전 흐름과 상호 관계를 정리하고, 각 분야별 학습 경로를 제시합니다.

### 왜 이 로드맵이 필요한가?

AI/ML 분야는 매주 수십 편의 논문이 발표되고, 새로운 모델이 쏟아지고 있습니다. 개별 논문을 깊이 이해하는 것도 중요하지만, 전체 흐름을 조망하지 못하면 숲을 보지 못하는 상황에 빠지기 쉽습니다. 이 로드맵은 각 분야의 핵심 논문과 아키텍처를 맥락 속에서 이해할 수 있도록 안내합니다.

---

## 핵심 흐름: AI/ML 기술 발전 타임라인

### Phase 1: 기초 확립 (2017-2019)

2017년 [Transformer](/post/transformer) 아키텍처의 발표는 현대 AI의 시작점입니다. Self-Attention 메커니즘으로 RNN/LSTM의 순차 처리 한계를 극복했으며, 이후 모든 주요 모델의 근간이 되었습니다.

- **2017**: [Transformer](/post/transformer) — Attention Is All You Need
- **2018**: [GPT-1](/post/gpt-1) — 단방향 언어 모델의 가능성 입증
- **2018**: [BERT](/post/bert) — 양방향 사전학습의 혁신
- **2018**: [ELMo](/post/elmo) — 문맥 기반 단어 임베딩
- **2019**: [GPT-2](/post/gpt-2) — 대규모 언어 모델의 등장
- **2019**: [RoBERTa](/post/roberta), [ALBERT](/post/albert), [XLNet](/post/xlnet) — BERT 변형 모델들

### Phase 2: 스케일링의 시대 (2020-2021)

모델 크기와 데이터 규모를 키우면 성능이 지속적으로 향상된다는 [Scaling Laws](/post/scaling-laws)가 발견되면서, 거대 모델 경쟁이 시작되었습니다. 동시에 Diffusion 기반 생성 모델과 Vision Transformer가 등장하며 새로운 패러다임이 열렸습니다.

- **2020**: [GPT-3](/post/gpt-3) — 175B 파라미터, Few-shot Learning
- **2020**: [DDPM](/post/ddpm) — 확산 모델의 실용화
- **2020**: [ViT](/post/vit) — Vision Transformer의 등장
- **2020**: [Scaling Laws](/post/scaling-laws) — 스케일링 법칙의 발견
- **2020**: [T5](/post/t5) — Text-to-Text 통합 프레임워크
- **2021**: [CLIP](/post/clip) — 비전-언어 연결의 시작
- **2021**: [DALL-E 2](/post/dalle-2), [GLIDE](/post/glide) — 텍스트 기반 이미지 생성
- **2021**: [DeiT](/post/deit) — 효율적 Vision Transformer 학습
- **2021**: [Chinchilla](/post/chinchilla) — 데이터 중심 스케일링

### Phase 3: 대중화와 다양화 (2022-2023)

오픈소스 LLM, Stable Diffusion, 멀티모달 모델이 등장하면서 AI 기술이 대중화되었습니다. 동시에 효율성과 정렬(alignment)이 핵심 연구 주제로 부상했습니다.

- **2022**: [InstructGPT](/post/instructgpt) — RLHF를 통한 모델 정렬
- **2022**: [LDM/Stable Diffusion](/post/ldm) — 잠재 공간 기반 확산 모델
- **2022**: [LLaMA](/post/llama) — 오픈소스 LLM의 시작
- **2022**: [LoRA](/post/lora), [QLoRA](/post/qlora) — 효율적 파인튜닝
- **2022**: [Flash Attention](/post/flash-attention) — 메모리 효율적 어텐션
- **2022**: [SAM](/post/sam) — Segment Anything
- **2022**: [S4](/post/s4) — State Space Models의 등장
- **2023**: [LLaMA 2](/post/llama-2), [Mistral 7B](/post/mistral-7b), [Mixtral](/post/mixtral) — 오픈소스 LLM 경쟁
- **2023**: [Mamba](/post/mamba) — 선택적 SSM으로 Transformer에 도전
- **2023**: [LLaVA](/post/llava) — 비전-언어 멀티모달 모델
- **2023**: [GPT-4](/post/gpt-4) — 멀티모달 거대 언어 모델
- **2023**: [DPO](/post/dpo) — 직접 선호도 최적화

### Phase 4: 전문화와 에이전트 (2024-현재)

각 분야가 전문화되면서 추론(reasoning), 멀티모달 통합, 자율 에이전트 등 새로운 방향으로 발전하고 있습니다.

- **2024**: [DeepSeek-V2](/post/deepseek-v2), [DeepSeek-V3](/post/deepseek-v3) — 효율적 MoE 아키텍처
- **2024**: [DeepSeek-R1](/post/deepseek-r1) — 추론 특화 모델
- **2024**: [Qwen2](/post/qwen2), [Qwen2.5](/post/qwen2-5) — 다국어 LLM
- **2024**: [Mamba-2](/post/mamba-2), [Jamba](/post/jamba) — SSM-Transformer 하이브리드
- **2024**: [SD3](/post/sd3), [FLUX](/post/flux) — 차세대 이미지 생성
- **2024**: [Sora](/post/sora) — 비디오 생성
- **2024**: [ReAct](/post/react), [AutoGen](/post/autogen) — AI Agent 프레임워크
- **2025**: [Claude 4](/post/claude-4), [GPT-5](/post/gpt-5) — 프론티어 모델의 진화
- **2025**: [Gemini 2.5](/post/gemini-2-5) — 네이티브 멀티모달
- **2025**: [A2A](/post/a2a), [MCP](/post/mcp) — 에이전트 통신 프로토콜
- **2025**: [Mamba-3](/post/mamba-3) — SSM의 지속적 발전

---

## 7개 핵심 영역 개요

### 1. LLM (Large Language Models)

대규모 언어 모델은 Transformer 기반의 자연어 처리 모델로, 텍스트 생성, 번역, 요약, 질의응답 등 다양한 언어 작업을 수행합니다. GPT 시리즈, LLaMA 시리즈, DeepSeek 시리즈 등이 대표적입니다.

**핵심 주제**: 아키텍처 설계, 스케일링, 정렬(RLHF/DPO), 효율적 추론, MoE

자세한 내용은 [LLM 핵심 논문 가이드](/post/llm-paper-guide)를 참고하세요.

| 모델 | 연도 | 핵심 기여 |
|------|------|----------|
| [Transformer](/post/transformer) | 2017 | Self-Attention 아키텍처 |
| [GPT-3](/post/gpt-3) | 2020 | Few-shot Learning, 175B |
| [LLaMA](/post/llama) | 2023 | 오픈소스 LLM |
| [Mixtral](/post/mixtral) | 2023 | Sparse MoE |
| [DeepSeek-V3](/post/deepseek-v3) | 2024 | 효율적 MoE |
| [Qwen3](/post/qwen3) | 2025 | 다국어 확장 |

### 2. Diffusion Models

확산 모델은 노이즈를 점진적으로 제거하여 데이터를 생성하는 방식으로, 이미지, 비디오, 오디오 생성에서 혁명적인 성과를 거두었습니다.

**핵심 주제**: Score Matching, DDPM/DDIM, Latent Diffusion, Flow Matching, Consistency Models

자세한 내용은 [Diffusion Models 완전 정복](/post/diffusion-models-guide)을 참고하세요.

| 모델 | 연도 | 핵심 기여 |
|------|------|----------|
| [DDPM](/post/ddpm) | 2020 | 확산 모델 실용화 |
| [LDM](/post/ldm) | 2022 | Latent Diffusion |
| [DALL-E 3](/post/dalle-3) | 2023 | 텍스트-이미지 생성 |
| [SD3](/post/sd3) | 2024 | MMDiT 아키텍처 |
| [FLUX](/post/flux) | 2024 | Flow Matching 기반 |
| [Sora](/post/sora) | 2024 | 비디오 생성 |

### 3. Computer Vision

딥러닝 기반 컴퓨터 비전은 ViT의 등장으로 CNN 중심 패러다임에서 Transformer 기반으로 전환되었습니다.

**핵심 주제**: Image Classification, Object Detection, Segmentation, Self-Supervised Learning

자세한 내용은 [컴퓨터 비전 딥러닝 로드맵](/post/computer-vision-dl-roadmap)을 참고하세요.

| 모델 | 연도 | 핵심 기여 |
|------|------|----------|
| [ViT](/post/vit) | 2020 | Vision Transformer |
| [DeiT](/post/deit) | 2021 | 효율적 ViT 학습 |
| [Swin Transformer](/post/swin-transformer) | 2021 | 계층적 Vision Transformer |
| [SAM](/post/sam) | 2023 | Segment Anything |
| [DINOv2](/post/dinov2) | 2023 | 자기지도 비전 학습 |
| [DETR](/post/detr) | 2020 | End-to-End Object Detection |

### 4. State Space Models (SSM)

SSM은 Transformer의 이차(O(n^2)) 복잡도 한계를 극복하기 위한 선형(O(n)) 복잡도 아키텍처입니다.

**핵심 주제**: S4, Mamba, Linear Attention, Hybrid 아키텍처

자세한 내용은 [State Space Models: S4에서 Mamba까지](/post/state-space-models-guide)를 참고하세요.

| 모델 | 연도 | 핵심 기여 |
|------|------|----------|
| [S4](/post/s4) | 2021 | SSM의 이론적 기초 |
| [H3](/post/h3) | 2022 | 언어 모델링용 SSM |
| [Mamba](/post/mamba) | 2023 | 선택적 SSM |
| [Jamba](/post/jamba) | 2024 | SSM-Transformer 하이브리드 |
| [Mamba-2](/post/mamba-2) | 2024 | State Space Duality |
| [RWKV-7](/post/rwkv-7) | 2024 | RNN-Transformer 하이브리드 |

### 5. Multimodal

여러 모달리티(텍스트, 이미지, 오디오, 비디오)를 통합 처리하는 모델로, 단일 모달리티의 한계를 넘어선 범용 AI를 지향합니다.

**핵심 주제**: Vision-Language, 이미지-텍스트 정렬, Unified Architecture

| 모델 | 연도 | 핵심 기여 |
|------|------|----------|
| [CLIP](/post/clip) | 2021 | 비전-언어 대조 학습 |
| [BLIP-2](/post/blip-2) | 2023 | 효율적 VLM |
| [LLaVA](/post/llava) | 2023 | 비전-언어 대화 |
| [GPT-4](/post/gpt-4) | 2023 | 멀티모달 LLM |
| [Gemini 2.5](/post/gemini-2-5) | 2025 | 네이티브 멀티모달 |
| [InternVL-3](/post/internvl-3) | 2025 | 오픈소스 VLM |

### 6. Agent

LLM을 핵심 두뇌로 활용하여 도구를 사용하고, 계획을 수립하며, 자율적으로 작업을 수행하는 AI 시스템입니다.

**핵심 주제**: 추론 프레임워크, 도구 활용, 멀티에이전트, 통신 프로토콜

자세한 내용은 [AI Agent 기술 지도](/post/ai-agent-technology-guide)를 참고하세요.

| 모델/프레임워크 | 연도 | 핵심 기여 |
|------|------|----------|
| [ReAct](/post/react) | 2022 | Reasoning + Acting |
| [Toolformer](/post/toolformer) | 2023 | 도구 자동 학습 |
| [AutoGen](/post/autogen) | 2023 | 멀티에이전트 프레임워크 |
| [SWE-Agent](/post/swe-agent) | 2024 | 코딩 에이전트 |
| [Claude Code](/post/claude-code) | 2025 | 프로덕션 코딩 에이전트 |
| [A2A](/post/a2a) | 2025 | 에이전트 간 통신 |

### 7. Technique

특정 분야에 국한되지 않고 모든 AI 모델에 적용되는 핵심 기법들입니다.

**핵심 주제**: Attention, 효율적 학습/추론, Scaling Laws, RAG, Alignment

자세한 내용은 [AI 핵심 기법 총정리](/post/ai-core-techniques-guide)를 참고하세요.

| 기법 | 연도 | 핵심 기여 |
|------|------|----------|
| [Flash Attention](/post/flash-attention) | 2022 | IO-aware 어텐션 |
| [LoRA](/post/lora) | 2021 | 효율적 파인튜닝 |
| [RAG](/post/rag) | 2020 | 검색 증강 생성 |
| [Chain-of-Thought](/post/cot) | 2022 | 단계별 추론 |
| [DPO](/post/dpo) | 2023 | 직접 선호도 최적화 |
| [Speculative Decoding](/post/speculative-decoding) | 2023 | 추론 가속화 |

---

## 영역 간 상호 관계

AI/ML의 7개 영역은 독립적으로 발전하는 것이 아니라 서로 깊이 연결되어 있습니다.

```
                    ┌─────────────┐
                    │  Technique  │
                    │ (공통 기법)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
         │   LLM   │  │Diffusion│  │ Vision │
         └────┬────┘  └───┬────┘  └───┬────┘
              │            │            │
              └────────┬───┘            │
                       │                │
                  ┌────▼────┐      ┌───▼────┐
                  │Multimodal│     │  SSM   │
                  └────┬────┘      └────────┘
                       │
                  ┌────▼────┐
                  │  Agent  │
                  └─────────┘
```

- **Technique → 전 영역**: Flash Attention, LoRA, Scaling Laws 등은 LLM, Diffusion, Vision 모두에 적용
- **LLM + Vision → Multimodal**: CLIP, LLaVA 등은 언어 모델과 비전 모델을 결합
- **LLM + Diffusion → Multimodal**: DALL-E, Emu3 등은 언어 이해와 이미지 생성을 통합
- **LLM → Agent**: LLM을 두뇌로 활용하여 도구 사용과 자율 행동을 구현
- **SSM → LLM**: Mamba, RWKV 등은 Transformer의 대안으로 언어 모델링에 도전

---

## 추천 학습 경로

### 초심자 (AI/ML 입문)

기본 개념과 핵심 아키텍처를 이해하는 단계입니다.

1. **머신러닝 기초**: [ML 개론](/post/ml-overview) → [ML 워크플로](/post/ml-workflow) → [편향-분산 트레이드오프](/post/bias-variance-tradeoff)
2. **딥러닝 기초**: [Transformer](/post/transformer) 아키텍처 이해
3. **주요 모델 체험**: [BERT](/post/bert), [GPT-3](/post/gpt-3) 논문 읽기
4. **분야 선택**: 관심 분야의 카테고리 가이드 참고

### 중급 (분야별 심화)

특정 분야를 깊이 파고드는 단계입니다.

1. **LLM 심화**: [LLM 핵심 논문 가이드](/post/llm-paper-guide) 따라가기
2. **생성 모델**: [Diffusion Models 완전 정복](/post/diffusion-models-guide) 학습
3. **비전**: [컴퓨터 비전 딥러닝 로드맵](/post/computer-vision-dl-roadmap) 학습
4. **핵심 기법**: [AI 핵심 기법 총정리](/post/ai-core-techniques-guide) 학습
5. **실전 코드**: 주요 모델 구현 및 파인튜닝 실습

### 고급 (연구/실무)

최신 연구 동향을 따라가고 실무에 적용하는 단계입니다.

1. **아키텍처 비교**: SSM vs Transformer, MoE 패턴 등 설계 트레이드오프 분석
2. **멀티모달 통합**: Vision-Language 모델, 영상 생성 모델 심화
3. **에이전트 시스템**: [AI Agent 기술 지도](/post/ai-agent-technology-guide) 학습 후 시스템 구축
4. **스케일링 연구**: [Scaling Laws](/post/scaling-laws), [Chinchilla](/post/chinchilla) 분석
5. **최신 논문 추적**: 각 분야별 최신 모델 논문 리뷰

---

## 주요 모델 전체 요약 테이블

| 영역 | 대표 모델 | 핵심 키워드 | 학습 가이드 |
|------|----------|------------|------------|
| LLM | GPT, LLaMA, DeepSeek, Qwen | 언어 모델, 스케일링, MoE | [LLM 가이드](/post/llm-paper-guide) |
| Diffusion | DDPM, LDM, FLUX, Sora | 노이즈 제거, 이미지/비디오 생성 | [Diffusion 가이드](/post/diffusion-models-guide) |
| Vision | ViT, SAM, DETR, DINOv2 | 이미지 분류, 세그멘테이션 | [Vision 가이드](/post/computer-vision-dl-roadmap) |
| SSM | S4, Mamba, Jamba, RWKV | 선형 복잡도, 긴 시퀀스 | [SSM 가이드](/post/state-space-models-guide) |
| Multimodal | CLIP, LLaVA, GPT-4, Gemini | 비전-언어, 통합 모델 | (본 가이드 참고) |
| Agent | ReAct, AutoGen, SWE-Agent | 도구 사용, 자율 행동 | [Agent 가이드](/post/ai-agent-technology-guide) |
| Technique | LoRA, Flash Attention, RAG | 효율성, 정렬, 검색 증강 | [기법 가이드](/post/ai-core-techniques-guide) |

---

## 참고 자료

이 블로그의 각 카테고리별 상세 가이드를 통해 더 깊이 있는 학습을 진행할 수 있습니다.

- [LLM 핵심 논문 가이드: 언어 모델의 진화](/post/llm-paper-guide)
- [Diffusion Models 완전 정복: DDPM에서 Stable Diffusion까지](/post/diffusion-models-guide)
- [컴퓨터 비전 딥러닝 로드맵](/post/computer-vision-dl-roadmap)
- [State Space Models: S4에서 Mamba까지](/post/state-space-models-guide)
- [AI Agent 기술 지도: ReAct에서 멀티에이전트까지](/post/ai-agent-technology-guide)
- [AWS & Cloud 인프라 학습 가이드](/post/aws-cloud-infrastructure-guide)
- [머신러닝 기초부터 실전까지: 학습 로드맵](/post/ml-fundamentals-roadmap)
- [AI 핵심 기법 총정리](/post/ai-core-techniques-guide)
