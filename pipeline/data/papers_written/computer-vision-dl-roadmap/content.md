# 컴퓨터 비전 딥러닝 로드맵

## 개요

컴퓨터 비전은 딥러닝의 발전과 함께 가장 극적인 변화를 겪은 분야입니다. CNN이 지배하던 패러다임은 2020년 [ViT (Vision Transformer)](/post/vit)의 등장으로 근본적인 전환을 맞이했고, 이후 이미지 분류, 객체 탐지, 세그멘테이션, 자기지도 학습 등 모든 하위 영역에서 Transformer 기반 접근법이 주류로 자리잡았습니다.

이 가이드는 딥러닝 기반 컴퓨터 비전의 **핵심 모델과 기법**을 체계적으로 정리합니다. Vision Transformer 계열의 발전, Object Detection과 Segmentation의 혁신, 그리고 Vision-Language 모델까지 전체 흐름을 조망합니다.

### 왜 컴퓨터 비전을 공부해야 하는가?

컴퓨터 비전은 자율주행, 의료 영상, 로보틱스, AR/VR 등 실세계 응용에 직결되는 핵심 기술입니다. 최근에는 멀티모달 AI의 "눈" 역할을 담당하며, LLM과 결합하여 더욱 강력한 AI 시스템을 구성하고 있습니다. CLIP, LLaVA, GPT-4V 등 최신 멀티모달 모델을 이해하려면 비전 기초가 필수적입니다.

---

## 핵심 흐름: 컴퓨터 비전 기술 발전 타임라인

### Era 1: CNN의 시대 (2012-2019)

AlexNet(2012)부터 EfficientNet(2019)까지 CNN이 컴퓨터 비전을 지배한 시기입니다. ResNet의 skip connection, Inception의 다중 스케일 처리 등 핵심 아이디어가 이 시기에 확립되었습니다.

- **2012**: AlexNet — ImageNet 분류에서 딥러닝의 우월성 입증
- **2014**: VGGNet — 깊은 네트워크의 효과 검증
- **2014**: GoogLeNet/Inception — 다중 스케일 합성곱
- **2015**: ResNet — Skip Connection, 매우 깊은 네트워크 학습 가능
- **2017**: MobileNet — 경량 CNN
- **2019**: EfficientNet — Compound Scaling

### Era 2: Vision Transformer의 등장 (2020-2021)

Transformer가 NLP를 넘어 비전 영역까지 장악하기 시작한 전환점입니다.

- [ViT](/post/vit) (2020): 이미지를 16x16 패치로 분할하여 Transformer에 입력. 대규모 사전학습 시 CNN 능가. Vision Transformer 시대의 개막.
- [DeiT](/post/deit) (2021): Data-efficient Image Transformers. Knowledge Distillation으로 ViT를 ImageNet만으로 학습. 토큰 기반 지식 증류.
- [Swin Transformer](/post/swin-transformer) (2021): 계층적(hierarchical) 구조 + Shifted Window Attention. 다양한 스케일의 특징 추출. 객체 탐지, 세그멘테이션에서 CNN 완전 대체.
- [MAE (Masked Autoencoder)](/post/mae) (2022): 이미지 패치의 75%를 마스킹하고 복원하는 자기지도 학습. NLP의 BERT에서 영감. 효율적인 비전 사전학습.

### Era 3: 자기지도 학습과 기반 모델 (2022-2023)

레이블 없이 대규모 이미지로 사전학습하는 자기지도 학습(Self-Supervised Learning)이 주류가 되었습니다.

- [DINOv2](/post/dinov2) (2023): Meta의 대규모 자기지도 비전 모델. 142M 이미지로 학습. ViT-g/14. 이미지 분류, 세그멘테이션, 깊이 추정 등 다양한 태스크에서 범용적으로 활용.
- [DINOv3](/post/dinov3) (2025): DINOv2의 후속. 더 큰 규모와 개선된 학습 방법.
- [V-JEPA 2](/post/v-jepa-2) (2025): Meta의 비디오 자기지도 학습 모델. 비디오 이해와 예측.

### Era 4: Object Detection의 혁명

객체 탐지 분야도 Transformer 기반으로 전환되면서 앵커, NMS 등 기존의 복잡한 파이프라인이 크게 단순화되었습니다.

- [DETR](/post/detr) (2020): End-to-End Object Detection with Transformers. 앵커 박스, NMS 등 수작업 구성 요소 제거. Set Prediction으로 재정의. Bipartite Matching Loss.
- [Grounding DINO](/post/grounding-dino) (2023): 텍스트 쿼리로 객체 탐지. 오픈 어휘(open-vocabulary) 탐지. DINO + 언어 모델 결합.

### Era 5: Segment Anything과 범용 세그멘테이션

- [SAM (Segment Anything Model)](/post/sam) (2023): 프롬프트(포인트, 박스, 텍스트)로 어떤 객체든 세그멘테이션. 11M 이미지, 1.1B 마스크로 학습. 비전의 기반 모델(Foundation Model).
- [SAM 2](/post/sam-2) (2024): 비디오 세그멘테이션으로 확장. Streaming Architecture. 실시간 비디오 세그멘테이션.
- [SAM 3](/post/sam-3) (2025): 3D 인식과 향상된 세그멘테이션 능력.

---

## 주요 모델 요약 테이블

### Image Classification

| 모델 | 연도 | 핵심 기여 | 구조 |
|------|------|----------|------|
| [ViT](/post/vit) | 2020 | 이미지 패치 + Transformer | Transformer |
| [DeiT](/post/deit) | 2021 | Knowledge Distillation | Transformer |
| [Swin Transformer](/post/swin-transformer) | 2021 | Shifted Window, 계층적 | Transformer |
| [MAE](/post/mae) | 2022 | Masked Autoencoder | Transformer |
| [DINOv2](/post/dinov2) | 2023 | 대규모 자기지도 학습 | Transformer |
| [DINOv3](/post/dinov3) | 2025 | 향상된 자기지도 학습 | Transformer |

### Object Detection

| 모델 | 연도 | 핵심 기여 | 특징 |
|------|------|----------|------|
| [DETR](/post/detr) | 2020 | End-to-End Detection | Bipartite Matching |
| [Grounding DINO](/post/grounding-dino) | 2023 | Open-Vocabulary Detection | 텍스트 쿼리 지원 |

### Segmentation

| 모델 | 연도 | 핵심 기여 | 특징 |
|------|------|----------|------|
| [SAM](/post/sam) | 2023 | Segment Anything | 프롬프트 기반 |
| [SAM 2](/post/sam-2) | 2024 | 비디오 세그멘테이션 | Streaming |
| [SAM 3](/post/sam-3) | 2025 | 3D 세그멘테이션 | 3D 인식 |

### Vision-Language Models

| 모델 | 연도 | 핵심 기여 | 방식 |
|------|------|----------|------|
| [CLIP](/post/clip) | 2021 | 비전-언어 대조 학습 | Contrastive |
| [SigLIP](/post/siglip) | 2023 | Sigmoid Loss 대조 학습 | Contrastive |
| [SigLIP 2](/post/siglip-2) | 2024 | 멀티태스크 비전 인코더 | Contrastive+ |
| [BLIP-2](/post/blip-2) | 2023 | Q-Former 기반 VLM | Bridge |
| [LLaVA](/post/llava) | 2023 | 비전-언어 대화 | Projection |
| [LLaVA-OneVision](/post/llava-onevision) | 2024 | 단일 모델 멀티 태스크 | Unified |
| [InternVL](/post/internvl) | 2024 | 스케일러블 VLM | Dynamic |
| [InternVL-3](/post/internvl-3) | 2025 | 오픈소스 VLM 최강 | Enhanced |
| [PaliGemma 2](/post/paligemma-2) | 2024 | 효율적 VLM | Transfer |
| [Flamingo](/post/flamingo) | 2022 | Few-shot Visual QA | Perceiver |

### Multimodal (Vision + Language + Generation)

| 모델 | 연도 | 핵심 기여 | 특징 |
|------|------|----------|------|
| [Chameleon](/post/chameleon) | 2024 | 네이티브 멀티모달 | 토큰 기반 |
| [Emu3](/post/emu3) | 2024 | 이해+생성 통합 | Next-token |
| [Janus Pro](/post/janus-pro) | 2025 | 분리된 인코딩 | 이해/생성 분리 |
| [Pixtral](/post/pixtral) | 2024 | Mistral 비전 확장 | Variable-res |
| [CogVLM](/post/cogvlm) | 2023 | 시각 전문가 모듈 | Visual Expert |
| [Molmo](/post/molmo) | 2024 | 오픈소스 VLM | Pointing |

---

## 비전 기술의 핵심 개념

### 1. Vision Transformer의 핵심 설계

**패치 임베딩**: 이미지를 고정 크기 패치(보통 16x16)로 분할하여 1D 시퀀스로 변환합니다. 이는 NLP에서의 토큰화에 해당합니다.

- **[ViT](/post/vit)**: 고정 크기 패치, 선형 프로젝션
- **[Swin Transformer](/post/swin-transformer)**: Window 기반 어텐션으로 계산 비용 절감
- **[DeiT](/post/deit)**: Distillation Token으로 효율적 학습

**자기지도 학습**: 레이블 없이 대규모 이미지로 강력한 표현을 학습합니다.

- **[MAE](/post/mae)**: 마스킹 + 복원 (BERT 방식)
- **[DINOv2](/post/dinov2)**: Self-Distillation + EMA Teacher
- **[V-JEPA 2](/post/v-jepa-2)**: 비디오에서의 예측적 학습

### 2. Detection과 Segmentation의 패러다임 변화

전통적 객체 탐지는 앵커 박스 설정, NMS(Non-Maximum Suppression), RPN(Region Proposal Network) 등 복잡한 수작업 구성 요소가 필요했습니다. [DETR](/post/detr)은 이를 집합 예측 문제로 재정의하여 end-to-end 학습을 가능하게 했습니다.

[SAM](/post/sam)은 세그멘테이션에서 비슷한 혁명을 일으켰습니다. 프롬프트(포인트, 박스, 텍스트)만으로 어떤 객체든 세그멘테이션할 수 있는 범용 모델을 제시했습니다.

### 3. Vision-Language 연결

비전과 언어를 연결하는 방법은 크게 세 가지로 발전했습니다.

1. **대조 학습**: [CLIP](/post/clip), [SigLIP](/post/siglip) — 이미지-텍스트 쌍의 유사도 학습
2. **Bridge 모듈**: [BLIP-2](/post/blip-2), [Flamingo](/post/flamingo) — 비전 인코더와 LLM 사이의 연결 모듈
3. **직접 프로젝션**: [LLaVA](/post/llava) — 비전 특징을 LLM 입력 공간에 직접 매핑

---

## 추천 학습 경로

### 초심자 (컴퓨터 비전 입문)

CNN 기초와 Vision Transformer의 핵심을 이해합니다.

1. CNN 기초 (ResNet, VGG 개념 이해)
2. [ViT](/post/vit) — Vision Transformer의 기본 원리
3. [DeiT](/post/deit) — 효율적 ViT 학습
4. [Swin Transformer](/post/swin-transformer) — 계층적 비전 Transformer
5. [CLIP](/post/clip) — 비전-언어 연결의 시작

### 중급 (분야별 심화)

세부 분야별로 깊이 있게 학습합니다.

**Detection & Segmentation 트랙**:
1. [DETR](/post/detr) — End-to-End Detection
2. [Grounding DINO](/post/grounding-dino) — Open-Vocabulary Detection
3. [SAM](/post/sam) — Segment Anything
4. [SAM 2](/post/sam-2) — 비디오 세그멘테이션

**Self-Supervised Learning 트랙**:
1. [MAE](/post/mae) — Masked Autoencoder
2. [DINOv2](/post/dinov2) — 대규모 자기지도 학습
3. [V-JEPA 2](/post/v-jepa-2) — 비디오 자기지도 학습

**Vision-Language 트랙**:
1. [CLIP](/post/clip) + [SigLIP](/post/siglip) — 대조 학습
2. [BLIP-2](/post/blip-2) — Bridge 방식
3. [LLaVA](/post/llava) → [LLaVA-OneVision](/post/llava-onevision) — 프로젝션 방식

### 고급 (최신 연구)

최전선의 비전 연구를 추적합니다.

1. [DINOv3](/post/dinov3) — 최신 자기지도 학습
2. [SAM 3](/post/sam-3) — 3D 세그멘테이션
3. [InternVL-3](/post/internvl-3) — 최신 VLM
4. [PaliGemma 2](/post/paligemma-2) — 효율적 VLM
5. [Chameleon](/post/chameleon) + [Emu3](/post/emu3) — 네이티브 멀티모달
6. Diffusion 기반 비전: [DiT](/post/dit), [SD3](/post/sd3)

---

## 비전과 다른 분야의 교차점

컴퓨터 비전은 다른 AI 분야와 긴밀히 연결되어 있습니다.

| 교차 분야 | 대표 모델 | 설명 |
|----------|----------|------|
| Vision + LLM | [LLaVA](/post/llava), [GPT-4](/post/gpt-4) | 멀티모달 대화 |
| Vision + Diffusion | [ControlNet](/post/controlnet), [DALL-E 3](/post/dalle-3) | 이미지 생성/편집 |
| Vision + SSM | 비전 Mamba 변형 | 선형 복잡도 비전 |
| Vision + Agent | [Computer Use](/post/computer-use) | 시각 기반 에이전트 |

---

## 관련 카테고리

- [AI/ML 아키텍처 로드맵](/post/ai-ml-architecture-roadmap) — 전체 AI/ML 지형도
- [Diffusion Models 완전 정복](/post/diffusion-models-guide) — 비전과 밀접한 확산 모델
- [AI 핵심 기법 총정리](/post/ai-core-techniques-guide) — 비전에 사용되는 핵심 기법
- [LLM 핵심 논문 가이드](/post/llm-paper-guide) — 멀티모달 LLM과의 연결
