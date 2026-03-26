# CLIP: 대조 학습 기반 시각-언어 사전학습 모델

## 개요

CLIP(Contrastive Language-Image Pre-training)은 2021년 1월 OpenAI가 발표한 시각-언어 사전학습 모델이다. 인터넷에서 수집한 4억 쌍의 이미지-텍스트 데이터(WebImageText, WIT)로 대조 학습을 수행하여, 이미지와 텍스트를 동일한 임베딩 공간에 정렬한다. CLIP의 가장 혁신적인 특성은 별도의 파인튜닝 없이 자연어 설명만으로 이미지를 분류하는 **제로샷 전이(zero-shot transfer)** 능력이다.

기존 컴퓨터 비전 모델은 ImageNet과 같은 고정된 레이블 세트에 의존했지만, CLIP은 "a photo of a dog", "a photo of a cat"과 같은 자연어 프롬프트를 분류기로 사용할 수 있어, 사전에 정의되지 않은 카테고리에 대해서도 분류가 가능하다. 이러한 유연성 덕분에 CLIP은 이후 DALL-E, Stable Diffusion, LLaVA 등 수많은 멀티모달 연구의 기반 모델로 자리잡았다.

논문: [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020)

다음 다이어그램은 CLIP의 대조 학습 방식과 제로샷 추론 과정을 보여준다.

![CLIP의 대조 사전학습과 제로샷 분류 과정](figures/fig_1.png)
*Figure 1: CLIP 접근법 요약 — (1) 학습 시 이미지-텍스트 배치의 올바른 쌍을 예측하도록 이미지/텍스트 인코더를 동시 학습. (2) 추론 시 학습된 텍스트 인코더가 클래스 설명을 임베딩하여 제로샷 분류기를 합성한다. (Source: Radford et al., 2021)*

## 아키텍처 상세

CLIP은 **이중 인코더(dual encoder)** 구조로 구성된다.

### 이미지 인코더

두 가지 변형이 존재한다:
- **ResNet 계열**: ResNet-50, ResNet-101, RN50x4, RN50x16, RN50x64
- **ViT 계열**: ViT-B/32, ViT-B/16, ViT-L/14, ViT-L/14@336px

최고 성능 모델인 ViT-L/14@336px는 336x336 해상도의 이미지를 14x14 패치로 분할하여 처리한다.

### 텍스트 인코더

63M 파라미터의 트랜스포머로, 최대 77 토큰을 처리한다. 49,408개 어휘의 BPE 토크나이저를 사용하며, `[EOS]` 토큰의 최종 히든 스테이트를 텍스트 임베딩으로 사용한다.

### 대조 학습 (Contrastive Learning)

배치 내 $N$개의 이미지-텍스트 쌍에 대해 $N \times N$ 유사도 행렬을 계산한다:

$$\mathcal{L} = -\frac{1}{2N}\sum_{i=1}^{N}\left[\log\frac{\exp(\text{sim}(I_i, T_i)/\tau)}{\sum_{j=1}^{N}\exp(\text{sim}(I_i, T_j)/\tau)} + \log\frac{\exp(\text{sim}(T_i, I_i)/\tau)}{\sum_{j=1}^{N}\exp(\text{sim}(T_i, I_j)/\tau)}\right]$$

여기서 $\tau$는 학습 가능한 온도 파라미터이며, $\text{sim}(\cdot, \cdot)$은 코사인 유사도이다. 대각 원소(매칭 쌍)의 유사도는 최대화하고, 나머지(비매칭 쌍)는 최소화한다.

### 아키텍처 스펙 요약

| 구성 요소 | 사양 |
|-----------|------|
| 이미지 인코더 | ViT-L/14 (428M params) |
| 텍스트 인코더 | Transformer (63M params) |
| 임베딩 차원 | 768 |
| 레이어 수 | 12 (ViT) |
| 어텐션 헤드 | 12 |
| 어휘 크기 | 49,408 |
| 위치 인코딩 | Learned |
| 활성화 함수 | GELU |

## 핵심 혁신

### 1. 자연어를 감독 신호로 활용

기존 비전 모델이 고정된 클래스 레이블(1000개 ImageNet 클래스 등)에 의존한 것과 달리, CLIP은 자연어 텍스트를 감독 신호로 사용한다. 이를 통해:
- 사전 정의된 카테고리에 구애받지 않는 유연한 분류
- 새로운 도메인으로의 자연스러운 전이
- 임의의 시각적 개념에 대한 제로샷 인식

### 2. 대규모 웹 데이터 활용

400M 이미지-텍스트 쌍의 WIT 데이터셋을 자체 수집하여 사용했다. 이는 당시 공개된 시각-언어 데이터셋(COCO의 ~118K, CC3M의 ~3M)보다 수백 배 큰 규모로, 데이터 스케일의 중요성을 실증했다.

### 3. 학습 가능한 온도 파라미터

대조 손실의 날카로움을 조절하는 온도 $\tau$를 학습 가능한 파라미터로 설정하여, 학습 과정에서 자동으로 최적 온도를 찾도록 했다.

## 벤치마크/성능

### ImageNet 제로샷 분류

| 모델 | Top-1 Accuracy | 비고 |
|------|---------------|------|
| CLIP ViT-L/14@336px | **76.2%** | 제로샷, 파인튜닝 없음 |
| ResNet-50 (supervised) | 76.1% | ImageNet 1.28M으로 학습 |
| Visual N-Grams | 11.5% | 이전 제로샷 SOTA |

### 분포 이동(Distribution Shift) 강인성

| 데이터셋 | CLIP | ResNet-50 |
|----------|------|----------|
| ImageNet Sketch | **60.2%** | 25.2% |
| ImageNet Adversarial | **77.1%** | 2.7% |
| ImageNet-R | **77.7%** | 36.2% |

프롬프트 엔지니어링(80개 컨텍스트 프롬프트 앙상블)을 적용하면 약 5%p 추가 향상이 가능하다.

CLIP의 제로샷 성능은 27개 데이터셋 중 16개에서 지도학습 ResNet-50의 선형 분류기를 능가한다.

![27개 데이터셋에서 제로샷 CLIP vs 지도학습 ResNet-50 선형 분류기 비교](figures/fig_5.png)
*Figure 2: 제로샷 CLIP vs 지도학습 기준 — 27개 데이터셋 중 16개에서 제로샷 CLIP이 ResNet-50 기반 지도학습 선형 분류기를 능가하며, StanfordCars(+28.9%), Country211(+23.2%) 등에서 큰 격차를 보인다. (Source: Radford et al., 2021)*

CLIP의 선형 프로브 성능은 기존 최고 비전 모델들과 비교했을 때도 우수하다.

![CLIP과 기존 비전 모델들의 선형 프로브 성능 비교](figures/fig_10.png)
*Figure 3: 선형 프로브 성능 비교 — CLIP ViT-L/14@336px가 EfficientNet, SimCLRv2, ViT 등 기존 비전 모델 대비 GFLOPs 효율성과 정확도 모두에서 우위를 보인다. (Source: Radford et al., 2021)*

분포 이동에 대한 강인성 측면에서도 CLIP은 두드러진 특성을 보인다.

![CLIP의 분포 이동 강인성 — ImageNet 대비 자연 분포 이동 데이터셋 성능](figures/fig_13_1.png)
*Figure 4: 분포 이동 강인성 — 동일한 ImageNet 정확도에서 Zero-Shot CLIP이 표준 ImageNet 학습 모델 대비 자연 분포 이동 데이터셋에서 훨씬 높은 성능을 유지하며, 강인성 격차를 최대 75% 축소한다. (Source: Radford et al., 2021)*

## 관련 모델 비교

| 특성 | CLIP | SigLIP | ALIGN | BLIP |
|------|------|--------|-------|------|
| 발표 연도 | 2021 | 2023 | 2021 | 2022 |
| 손실 함수 | Softmax InfoNCE | Sigmoid | Softmax InfoNCE | ITC+ITM+LM |
| 배치 크기 의존성 | 높음 (32K) | 낮음 | 높음 | 중간 |
| 텍스트 생성 | 불가 | 불가 | 불가 | 가능 |
| 주요 용도 | 임베딩 정렬 | 임베딩 정렬 | 임베딩 정렬 | 이해+생성 |

## 실무 활용

### 제로샷 이미지 분류

```python
import torch
import clip
from PIL import Image

model, preprocess = clip.load("ViT-L/14", device="cuda")

image = preprocess(Image.open("photo.jpg")).unsqueeze(0).to("cuda")
text = clip.tokenize(["a dog", "a cat", "a bird"]).to("cuda")

with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)
    logits = (image_features @ text_features.T) * model.logit_scale.exp()
    probs = logits.softmax(dim=-1)

print(probs)  # [[0.95, 0.03, 0.02]]
```

### 활용 분야

1. **이미지 검색**: 텍스트 쿼리로 이미지 데이터베이스 검색
2. **콘텐츠 필터링**: 부적절한 이미지 자동 감지
3. **멀티모달 모델의 비전 백본**: LLaVA, Stable Diffusion 등의 이미지 인코더
4. **데이터 큐레이션**: 대규모 이미지-텍스트 데이터셋의 품질 필터링

## 한계 및 전망

### 한계

1. **세밀한 시각 이해 부족**: 객체의 속성(색상, 크기, 위치)이나 관계 추론에 취약
2. **추상적/복잡한 작업**: 사진 속 텍스트 읽기(OCR), 계수(counting) 등에서 성능 저조
3. **사회적 편향**: 웹 데이터에 내재된 편향이 모델에 반영될 수 있음
4. **텍스트 길이 제한**: 최대 77 토큰으로, 긴 설명 처리에 한계

### 전망

CLIP은 시각-언어 표현 학습의 새 지평을 연 모델로, 이후 등장한 거의 모든 멀티모달 모델에 직간접적 영향을 미쳤다. SigLIP(Sigmoid 손실), OpenCLIP(LAION 데이터), MetaCLIP(메타데이터 기반 큐레이션) 등 다양한 개선 연구가 진행 중이며, 2024년 이후에는 SigLIP-SO400M이 많은 VLM의 표준 비전 인코더로 자리잡고 있다. CLIP의 핵심 아이디어인 "자연어를 통한 시각 이해"는 현재 AI 연구의 근간을 이루고 있다.

## 관련 문서

- [[transformer|Transformer]] — 발전 기반
- [[blip-2|BLIP-2]] — 후속 모델
- [[internvl|InternVL]] — 후속 모델
- [[siglip|SigLIP]] — 후속 모델
- [[flamingo|Flamingo]] — 영감을 줌
- [[vit|An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale]] — 사용 기법
- [[dalle-2|DALL·E 2]] — 적용 모델
