<!-- infographic-hero -->
![InternVL 핵심 요약](figures/infographic.svg)

*Figure: InternVL 한 장 요약 인포그래픽*

# InternVL: 대규모 비전 인코더로 CLIP의 한계를 넘다

## 개요

InternVL은 2023년 12월 Shanghai AI Lab에서 발표한 6B 파라미터 비전 파운데이션 모델이다. 핵심 문제의식은 명확하다: **비전 인코더의 규모가 LLM에 비해 너무 작다.** GPT-4, LLaMA 등 언어 모델이 수백억~수천억 파라미터로 성장하는 동안, CLIP ViT-L(300M), ViT-G(1B) 등 비전 인코더는 수억~수십억 파라미터에 머물러 있었다.

InternVL은 이 불균형을 해소하기 위해 **InternViT-6B**라는 6B 파라미터의 대규모 비전 인코더를 구축하고, InternLM-7B 언어 모델과 결합하여 CLIP을 능가하는 제로샷 시각-언어 이해를 달성했다. 이후 InternVL 1.5, 2.0, 2.5, 3.0으로 이어지는 멀티모달 LLM 시리즈의 비전 백본 역할을 하며, 오픈소스 VLM 생태계에서 핵심적인 위치를 차지하고 있다.

논문: [InternVL: Scaling up Vision Foundation Models and Aligning for Generic Visual-Linguistic Tasks](https://arxiv.org/abs/2312.14238)

아래 그림은 기존 비전 파운데이션 모델 패러다임과 InternVL의 차이를 보여준다.

![비전 파운데이션 모델 패러다임 비교 - 전통적 비전 모델, CLIP, InternVL](figures/fig_1.png)
*Figure 1: 비전 파운데이션 모델 패러다임 비교 - (a) 전통적 분류 기반 비전 모델, (b) CLIP 스타일 비전-언어 대조 학습, (c) InternVL은 6B 규모 비전 인코더를 LLM과 정렬하여 대조 및 생성 태스크 모두 처리한다. (Source: Chen et al., 2023)*

## 아키텍처 상세

### 전체 구조

InternVL은 세 가지 컴포넌트로 구성된다:

1. **InternViT-6B**: 6B 파라미터 비전 트랜스포머 (이미지 인코더)
2. **QLLaMA**: InternLM-7B 기반 언어 모델 (언어 디코더)
3. **픽셀 셔플(Pixel Shuffle) 프로젝터**: 비전-언어 연결 모듈

### InternViT-6B 아키텍처

| 항목 | InternViT-6B | CLIP ViT-L | EVA-CLIP ViT-G |
|------|-------------|-----------|---------------|
| 파라미터 | **6B** | 300M | 1B |
| 히든 차원 | 3200 | 1024 | 1408 |
| 레이어 수 | 48 | 24 | 40 |
| 어텐션 헤드 | 25 | 16 | 16 |
| 입력 해상도 | 448×448 | 224×224 | 224×224 |
| 패치 크기 | 14×14 | 14×14 | 14×14 |

InternViT-6B는 기존 ViT-L 대비 **20배 큰 규모**로, 고해상도 이미지에서 더욱 세밀한 시각 특징을 추출한다. 448×448 입력 해상도를 사용하여 1024개의 시각 토큰을 생성한다.

### 점진적 정렬 전략(Progressive Alignment)

InternVL의 학습은 세 단계로 진행된다. 아래 그림은 각 단계에서의 모듈 구성과 학습 가능한 가중치를 시각적으로 보여준다.

![InternVL 3단계 점진적 학습 전략 - 대조 학습, 생성 학습, 지도 미세조정](figures/fig_3.png)
*Figure 2: InternVL 점진적 학습 전략 - Stage 1에서 대조 학습으로 비전-언어 공유 공간을 구축하고, Stage 2에서 생성 학습으로 캡셔닝 능력을 획득하며, Stage 3에서 지도 미세조정으로 VQA 및 멀티모달 대화를 지원한다. (Source: Chen et al., 2023)*

**Stage 1: 대조 학습 (Contrastive Learning)**
- CLIP 스타일의 이미지-텍스트 대조 학습
- 대규모 웹 이미지-텍스트 데이터 사용
- 비전 인코더와 텍스트 인코더의 공유 임베딩 공간 구축

$$\mathcal{L}_{\text{contrastive}} = -\log\frac{\exp(\text{sim}(I_i, T_i)/\tau)}{\sum_j \exp(\text{sim}(I_i, T_j)/\tau)}$$

**Stage 2: 생성 학습 (Generative Learning)**
- 비전 인코더 출력을 언어 모델에 연결하여 캡셔닝 학습
- 픽셀 셔플 프로젝터로 시각 토큰을 LLM 공간에 매핑

**Stage 3: 멀티태스크 파인튜닝**
- VQA, 캡셔닝, grounding 등 다양한 다운스트림 태스크로 미세조정

### 픽셀 셔플 프로젝터

비전 인코더의 출력 토큰 수를 줄이면서 정보를 보존하는 기법이다:

$$\text{Pixel Shuffle}: \mathbb{R}^{H \times W \times C} \rightarrow \mathbb{R}^{H/2 \times W/2 \times 4C}$$

인접한 4개의 패치를 채널 방향으로 합치고 선형 변환하여, 시각 토큰 수를 1/4로 줄인다. 1024개 → 256개 시각 토큰으로 압축하여 LLM의 컨텍스트 효율을 높인다.

## 핵심 혁신

### 1. 비전 인코더 스케일업

"비전 인코더도 LLM만큼 커야 한다"는 명확한 메시지를 전달하였다. 6B 파라미터의 InternViT는 당시 공개된 가장 큰 비전 인코더로, 이후 InternVL 시리즈 전체의 시각적 근간이 되었다.

### 2. 점진적 정렬

한 번에 모든 것을 학습하지 않고, 대조 → 생성 → 멀티태스크 순으로 점진적으로 비전-언어 정렬을 깊게 하는 전략은 학습 안정성을 크게 높인다.

### 3. 범용 비전 백본

InternViT-6B는 분류, 검출, 세그멘테이션, 멀티모달 이해 등 다양한 비전 태스크에서 범용적으로 사용 가능한 비전 파운데이션 모델로 설계되었다. 아래 그림은 InternVL의 다양한 활용 방식을 보여준다.

![InternVL의 다양한 활용 방식 - 대조 태스크, 생성 태스크, 멀티모달 대화](figures/fig_4.png)
*Figure 3: InternVL 활용 방식 - 비전 인코더와 언어 미들웨어를 유연하게 결합하여 대조 태스크(검색, 분류), 생성 태스크(캡셔닝), 멀티모달 대화 등 다양한 비전-언어 태스크를 처리한다. (Source: Chen et al., 2023)*

InternVL은 이미지 분류, 비디오 분류, 이미지-텍스트 검색, 캡셔닝, 멀티모달 대화 등 범용 시각-언어 태스크 전반에서 최고 성능을 달성했다.

![다양한 시각-언어 태스크에서의 InternVL 성능 비교 - 이미지/비디오 분류, 검색, 캡셔닝, 대화](figures/fig_2.png)
*Figure 4: InternVL 벤치마크 성능 비교 - 이미지 분류, 비디오 분류, 이미지-텍스트 검색, 캡셔닝, 멀티모달 대화 등 모든 범용 시각-언어 태스크에서 기존 모델 대비 최고 성능을 달성한다. 공개 데이터로만 학습된 모델만 포함. (Source: Chen et al., 2023)*

## 벤치마크/성능

| 벤치마크 | InternVL-6B | CLIP ViT-G | EVA-CLIP ViT-G |
|----------|-----------|-----------|---------------|
| ImageNet (0-shot) | **83.2%** | 80.1% | 82.0% |
| COCO 검출 (AP) | **64.2** | 58.7 | 62.4 |
| ADE20K 세그 (mIoU) | **58.8** | 52.3 | 55.1 |

## 관련 모델 비교

| 특성 | InternVL | CLIP | SigLIP | EVA-CLIP |
|------|---------|------|--------|----------|
| 비전 인코더 크기 | 6B | 300M~1B | 400M | 1B |
| 해상도 | 448 | 224~336 | 384 | 224 |
| 점진적 정렬 | 3단계 | 1단계 | 1단계 | 1단계 |
| LLM 통합 | InternLM-7B | 없음 | 없음 | 없음 |
| 후속 VLM | InternVL 1.5~3 | 다수 VLM | 다수 VLM | CogVLM |

## 학습 상세

- **데이터**: 수십억 웹 이미지-텍스트 쌍 (LAION, CC 등)
- **인프라**: 64× A100 GPU, 수주간 학습
- **옵티마이저**: AdamW
- **학습률**: cosine decay 스케줄
- **해상도**: 448×448 (Stage 1~2), 다양한 해상도 (Stage 3)

## 실무 활용

```python
from transformers import AutoModel, AutoTokenizer
import torch

model = AutoModel.from_pretrained(
    "OpenGVLab/InternVL-Chat-V1-5",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
).to("cuda")
tokenizer = AutoTokenizer.from_pretrained(
    "OpenGVLab/InternVL-Chat-V1-5",
    trust_remote_code=True
)

# InternVL-Chat으로 이미지 QA
pixel_values = load_image("test.jpg")
response = model.chat(tokenizer, pixel_values, "이 이미지를 설명해주세요.")
print(response)
```

### InternVL 시리즈 발전

| 버전 | 발표 | 비전 인코더 | LLM | 핵심 개선 |
|------|------|-----------|-----|----------|
| InternVL | 2023.12 | InternViT-6B | InternLM-7B | 대규모 비전 인코더 |
| InternVL 1.5 | 2024.04 | InternViT-6B | InternLM2-20B | 동적 해상도 |
| InternVL 2 | 2024.07 | InternViT-6B | InternLM2-76B | MoE, 멀티이미지 |
| InternVL 3 | 2025.01 | InternViT-6B | MoE-78B | 네이티브 멀티모달 사전학습 |

## 한계 및 전망

### 한계

1. **비전 인코더 크기 부담**: 6B 비전 인코더로 인해 총 파라미터가 크고 추론 비용이 높다
2. **초기 버전 한계**: InternVL 1.0은 단일 이미지 처리에 한정, 다중 이미지/비디오 미지원
3. **학습 비용**: 6B 비전 인코더 학습에 대규모 GPU 클러스터와 수주간 시간이 필요

### 전망

InternVL은 "비전 인코더도 LLM처럼 스케일업해야 한다"는 명제를 실증하였으며, 이 InternViT-6B 기반 위에 InternVL 3까지 지속 발전하며 오픈소스 VLM 생태계를 선도하고 있다. 비전 인코더 스케일업의 효과가 반복적으로 검증되면서, 향후 더 큰 비전 인코더와 더 강력한 LLM의 결합이 가속화될 전망이다.

## 관련 문서

- [[clip|CLIP]] - 발전 기반
- [[internvl-3|InternVL 3]] - 후속 모델
