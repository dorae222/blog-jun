# 컴퓨터 비전 딥러닝 로드맵

## 개요

컴퓨터 비전은 딥러닝의 발전과 함께 가장 극적인 변화를 겪은 분야입니다. 2012년 AlexNet이 ImageNet 대회에서 압도적 성능을 보여준 이래, CNN이 10년 가까이 비전의 표준 아키텍처로 군림했습니다. 그러나 2020년 ViT(Vision Transformer)의 등장은 이 패러다임을 근본적으로 뒤흔들었고, 이미지 분류, 객체 탐지, 세그멘테이션, 자기지도 학습 등 모든 하위 영역에서 Transformer 기반 접근법이 주류로 자리잡았습니다.

이 가이드는 딥러닝 기반 컴퓨터 비전의 **핵심 모델과 기법**을 체계적으로 정리합니다. CNN 시대의 유산부터 Vision Transformer 계열의 발전, Object Detection과 Segmentation의 혁신, 그리고 Vision-Language 모델까지 전체 흐름을 조망합니다. 각 시대(Era)별로 핵심 모델을 비교 분석하고, 실무 학습 경로를 제안합니다.

### 왜 컴퓨터 비전을 공부해야 하는가?

컴퓨터 비전은 자율주행, 의료 영상, 로보틱스, AR/VR, 산업 검사 등 실세계 응용에 직결되는 핵심 기술입니다. 최근에는 멀티모달 AI의 "눈" 역할을 담당하며, LLM과 결합하여 더욱 강력한 AI 시스템을 구성하고 있습니다. [[clip]], LLaVA, GPT-4V 등 최신 멀티모달 모델을 이해하려면 비전 기초가 필수적입니다.

:::info
컴퓨터 비전은 단독 분야가 아니라 현대 AI의 교차점입니다. NLP(Transformer 아키텍처 차용), 생성 모델(Diffusion, GAN), 강화학습(로보틱스), 멀티모달(VLM) 등 거의 모든 AI 분야와 연결됩니다. 비전을 깊이 이해하면 AI 전반의 흐름을 파악하는 데 큰 도움이 됩니다.
:::

### 이 로드맵의 구성

| 섹션 | 내용 | 대상 독자 |
|------|------|----------|
| Era 1: CNN의 시대 | AlexNet부터 EfficientNet까지 CNN 핵심 모델 | 입문자 |
| Era 2: Vision Transformer | ViT, DeiT, Swin 등 Transformer 전환기 | 입문~중급 |
| Era 3: 자기지도 학습 | MAE, DINO 계열의 사전학습 혁명 | 중급 |
| Era 4: 탐지와 세그멘테이션 | DETR, SAM 등 태스크 특화 모델 | 중급~고급 |
| Vision-Language 모델 | CLIP, BLIP-2, LLaVA 등 멀티모달 | 고급 |
| 학습 경로 | 수준별 추천 논문과 학습 순서 | 전체 |

---

## Era 1: CNN의 시대 (2012-2019)

AlexNet(2012)이 ImageNet Large Scale Visual Recognition Challenge(ILSVRC)에서 기존 전통적 방법 대비 압도적 성능 차이(top-5 error 16.4%)를 보여준 이후, CNN은 약 8년간 컴퓨터 비전의 지배적 아키텍처로 군림했습니다. 이 시기에 확립된 핵심 아이디어들(깊은 네트워크, skip connection, 다중 스케일 처리, 경량화)은 이후 Transformer 시대에도 여전히 활용되고 있습니다.

### CNN 핵심 모델 비교

| 모델 | 연도 | 깊이 | 핵심 기여 | ImageNet Top-5 Error | 파라미터 수 |
|------|------|------|----------|---------------------|------------|
| AlexNet | 2012 | 8층 | GPU 학습, ReLU, Dropout | 16.4% | 60M |
| VGGNet | 2014 | 19층 | 3x3 필터 반복의 효과 | 7.3% | 144M |
| GoogLeNet/Inception | 2014 | 22층 | 다중 스케일 합성곱 (Inception 모듈) | 6.7% | 5M |
| ResNet | 2015 | 152층 | Skip Connection (잔차 학습) | 3.6% | 60M |
| DenseNet | 2017 | 201층 | Dense Connection (특징 재활용) | - | 20M |
| MobileNet v2 | 2018 | - | Depthwise Separable Conv (경량화) | - | 3.4M |
| EfficientNet | 2019 | - | Compound Scaling (폭/깊이/해상도 동시 조정) | 2.9% | 66M |

### CNN 시대의 핵심 설계 원리

**1. 깊이의 힘 (Depth Matters)**

VGGNet은 3x3이라는 작은 필터를 깊이 쌓는 것만으로도 큰 수용 영역(receptive field)을 확보할 수 있음을 증명했습니다. 3x3 필터 3개를 쌓으면 7x7 필터 1개와 동일한 수용 영역을 가지면서, 파라미터 수는 더 적고 비선형성은 더 풍부합니다.

**2. 잔차 학습 (Residual Learning)**

ResNet의 skip connection은 CNN 역사상 가장 중요한 아이디어 중 하나입니다. $F(x) + x$ 형태의 잔차 학습을 통해 gradient vanishing 문제를 해결하고, 수백 층의 매우 깊은 네트워크 학습을 가능하게 했습니다. 이 아이디어는 이후 Transformer의 residual connection에도 그대로 이어집니다.

**3. 효율성과 스케일링**

MobileNet은 Depthwise Separable Convolution으로 연산량을 극적으로 줄였고, EfficientNet은 네트워크의 폭(width), 깊이(depth), 입력 해상도(resolution)를 동시에 최적화하는 Compound Scaling을 제안했습니다.

| 스케일링 차원 | 설명 | 효과 |
|-------------|------|------|
| 깊이 (Depth) | 레이어 수 증가 | 복잡한 특징 학습 가능, 과적합 위험 |
| 폭 (Width) | 채널 수 증가 | 세밀한 특징 포착, 메모리 소비 증가 |
| 해상도 (Resolution) | 입력 이미지 크기 증가 | 세부 패턴 포착, 연산량 증가 |
| Compound (EfficientNet) | 세 차원 동시 조정 | 최적 균형점에서 성능 극대화 |

---

## Era 2: Vision Transformer의 등장 (2020-2022)

2017년 NLP 분야에서 발표된 [[1_attention-is-all-you-need]] 논문의 Transformer 아키텍처가 비전 영역까지 확장되면서, CNN 중심 패러다임에 근본적인 전환이 시작되었습니다. 핵심 전환점은 2020년 ViT(Vision Transformer)의 등장입니다.

### CNN에서 Transformer로: 패러다임 전환

CNN과 Vision Transformer의 근본적 차이를 이해하는 것이 중요합니다.

| 비교 항목 | CNN | Vision Transformer |
|----------|-----|-------------------|
| 기본 연산 | 합성곱 (로컬 패턴) | Self-Attention (글로벌 관계) |
| 수용 영역 | 레이어별 점진적 확장 | 첫 레이어부터 전체 이미지 |
| 귀납적 편향 | 강함 (지역성, 이동 불변성) | 약함 (대규모 데이터로 학습) |
| 데이터 효율성 | 적은 데이터로도 학습 가능 | 대규모 데이터 필요 (JFT-300M 등) |
| 스케일링 | 한계 존재 | 데이터/모델 크기에 비례하여 성능 향상 |
| 위치 정보 | 합성곱 자체에 내재 | Positional Embedding으로 명시적 부여 |

:::tip
ViT의 핵심 통찰은 "이미지도 시퀀스다"라는 관점입니다. 이미지를 16x16 패치로 분할하면 NLP의 토큰 시퀀스와 동일한 형태가 되며, Transformer를 수정 없이 적용할 수 있습니다. 이 단순한 아이디어가 비전 분야 전체를 바꿨습니다.
:::

### Vision Transformer 핵심 모델 비교

| 모델 | 연도 | 핵심 아이디어 | 사전학습 데이터 | ImageNet Top-1 | 특징 |
|------|------|-------------|---------------|---------------|------|
| [ViT](/post/vit) | 2020 | 이미지 패치 + 순수 Transformer | JFT-300M | 88.6% | 대규모 사전학습 시 CNN 능가 |
| [DeiT](/post/deit) | 2021 | Knowledge Distillation Token | ImageNet-1K만 | 85.2% | 데이터 효율적 학습 |
| [Swin Transformer](/post/swin-transformer) | 2021 | Shifted Window + 계층적 구조 | ImageNet-1K | 87.3% | 다운스트림 태스크 범용 백본 |
| BEiT | 2021 | Visual Token 예측 (DALL-E 토크나이저) | ImageNet-1K | 86.3% | 비전판 BERT |
| CvT | 2021 | Conv + Transformer 하이브리드 | ImageNet-1K | 87.7% | CNN의 귀납적 편향 활용 |

**ViT (Vision Transformer, 2020)**: 이미지를 16x16 패치로 분할하여 각 패치를 선형 프로젝션한 뒤, 표준 Transformer 인코더에 입력합니다. JFT-300M과 같은 대규모 데이터셋으로 사전학습하면 CNN을 능가하지만, ImageNet-1K만으로 학습하면 CNN보다 뒤처집니다. 이는 Transformer가 CNN 대비 귀납적 편향이 약하기 때문입니다.

**DeiT (Data-efficient Image Transformer, 2021)**: ViT의 데이터 의존성 문제를 해결합니다. Distillation Token을 추가하여 CNN 교사 모델(RegNet 등)의 지식을 증류하고, 강력한 데이터 증강(RandAugment, Mixup, CutMix)을 적용하여 ImageNet-1K만으로도 경쟁력 있는 성능을 달성했습니다.

**Swin Transformer (2021)**: 계층적(hierarchical) 구조와 Shifted Window Attention을 도입하여 Vision Transformer의 실용성을 크게 높였습니다. Window 내에서만 어텐션을 계산하므로 이미지 크기에 대해 선형 복잡도를 가지며, 계층적 특징 맵을 생성하여 객체 탐지, 세그멘테이션 등 다운스트림 태스크에 범용적으로 사용할 수 있습니다.

---

## Era 3: 자기지도 학습과 기반 모델 (2022-2024)

레이블 없이 대규모 이미지로 강력한 표현(representation)을 사전학습하는 자기지도 학습(Self-Supervised Learning, SSL)이 비전 분야의 새로운 패러다임으로 부상했습니다. NLP에서 BERT, GPT가 보여준 것처럼, 비전에서도 대규모 비지도 사전학습이 다양한 다운스트림 태스크의 성능을 극적으로 향상시킵니다.

### 자기지도 학습 접근법 분류

비전 자기지도 학습은 크게 세 가지 패러다임으로 나뉩니다.

| 패러다임 | 대표 모델 | 핵심 원리 | NLP 대응 |
|---------|----------|---------|---------|
| 마스킹 복원 (Masked Image Modeling) | [MAE](/post/mae), BEiT | 이미지 패치의 일부를 마스킹하고 복원 | BERT |
| 자기 증류 (Self-Distillation) | [DINOv2](/post/dinov2), DINO | Student-Teacher 네트워크 간 표현 일치 | - |
| 대조 학습 (Contrastive Learning) | MoCo, SimCLR | 같은 이미지의 다른 뷰는 가깝게, 다른 이미지는 멀게 | - |
| 예측적 학습 (Predictive Learning) | [V-JEPA 2](/post/v-jepa-2), I-JEPA | 잠재 공간에서 마스킹된 영역의 표현을 예측 | - |

### 핵심 자기지도 학습 모델

**MAE (Masked Autoencoder, 2022)**: 이미지 패치의 75%를 무작위로 마스킹하고, 보이는 25%의 패치만으로 마스킹된 패치를 복원하도록 학습합니다. NLP의 BERT에서 영감을 받았지만, 이미지의 정보 밀도가 텍스트보다 낮기 때문에 훨씬 높은 마스킹 비율(75% vs 15%)을 사용합니다. 비대칭 인코더-디코더 구조를 사용하여 사전학습 효율이 매우 높습니다.

**DINOv2 (2023)**: Meta에서 공개한 대규모 자기지도 비전 기반 모델입니다. 142M개의 큐레이션된 이미지(LVD-142M)로 학습한 ViT-g/14 모델로, 이미지 분류, 세그멘테이션, 깊이 추정, 검색 등 다양한 태스크에서 파인튜닝 없이도(linear probing) 우수한 성능을 보입니다. Self-distillation + centering + sharpening 기법을 결합합니다.

**V-JEPA 2 (2025)**: Meta의 비디오 자기지도 학습 모델로, Joint Embedding Predictive Architecture를 비디오에 확장했습니다. 픽셀 공간이 아닌 잠재 공간(latent space)에서 마스킹된 영역의 표현을 예측하므로, 저수준 디테일보다 고수준 의미를 학습합니다.

### 자기지도 학습 모델 성능 비교

| 모델 | 연도 | 학습 데이터 | 백본 | ImageNet Linear Probing | 학습 방식 |
|------|------|-----------|------|------------------------|----------|
| [MAE](/post/mae) | 2022 | ImageNet-1K | ViT-H/14 | 76.6% | 마스킹 복원 |
| DINO | 2021 | ImageNet-1K | ViT-S/16 | 77.0% | 자기 증류 |
| [DINOv2](/post/dinov2) | 2023 | LVD-142M | ViT-g/14 | 86.5% | 자기 증류 + 마스킹 |
| I-JEPA | 2023 | ImageNet-1K | ViT-H/14 | 82.0% | 잠재 공간 예측 |
| [V-JEPA 2](/post/v-jepa-2) | 2025 | 비디오 | ViT-H | - | 비디오 잠재 공간 예측 |

---

## Era 4: Object Detection의 혁명

객체 탐지(Object Detection)는 이미지 내 객체의 위치(bounding box)와 클래스를 동시에 예측하는 태스크입니다. 이 분야는 R-CNN에서 시작하여 YOLO, SSD 등을 거치며 발전했고, DETR에 이르러 Transformer 기반의 end-to-end 패러다임으로 전환되었습니다.

### Object Detection 발전 타임라인

| 모델 | 연도 | 유형 | 핵심 기여 | 속도 | 정확도 (COCO mAP) |
|------|------|------|----------|------|------------------|
| R-CNN | 2014 | Two-stage | Region Proposal + CNN 분류 | 느림 (47s/img) | 58.5 |
| Fast R-CNN | 2015 | Two-stage | RoI Pooling으로 특징 공유 | 중간 (0.3s) | 66.9 |
| Faster R-CNN | 2015 | Two-stage | RPN (Region Proposal Network) | 중간 (0.2s) | 69.9 |
| SSD | 2016 | One-stage | 다중 스케일 특징 맵에서 직접 탐지 | 빠름 | 74.3 |
| YOLOv1 | 2016 | One-stage | 이미지를 그리드로 분할, 한 번에 탐지 | 매우 빠름 | 63.4 |
| YOLOv3 | 2018 | One-stage | FPN + Darknet-53 백본 | 매우 빠름 | 57.9 |
| [DETR](/post/detr) | 2020 | Transformer | End-to-End, 앵커/NMS 제거 | 중간 | 44.9 |
| DINO (Detection) | 2022 | Transformer | Denoising Anchor Boxes | 중간 | 63.3 |
| [Grounding DINO](/post/grounding-dino) | 2023 | Transformer | 텍스트 쿼리 기반 오픈 어휘 탐지 | 중간 | - |

### Two-stage vs One-stage vs Transformer 비교

| 비교 항목 | Two-stage (Faster R-CNN) | One-stage (YOLO) | Transformer (DETR) |
|----------|------------------------|-----------------|-------------------|
| 파이프라인 | 영역 제안 → 분류/회귀 | 단일 네트워크로 직접 예측 | 집합 예측 (Set Prediction) |
| 앵커 박스 | 필요 (9종 앵커) | 필요 (프리셋 크기) | 불필요 (Object Query) |
| NMS | 필요 | 필요 | 불필요 (Bipartite Matching) |
| 추론 속도 | 느림 | 빠름 (실시간 가능) | 중간 |
| 소형 객체 | 우수 | 취약 | 초기 약함, 개선 중 |
| 수작업 구성 요소 | 많음 | 중간 | 최소 |

**DETR (2020)**: Object Detection의 패러다임을 근본적으로 바꾼 모델입니다. CNN 백본에서 추출한 특징을 Transformer 인코더-디코더에 입력하고, 학습 가능한 Object Query를 통해 객체를 예측합니다. Hungarian Algorithm 기반의 Bipartite Matching Loss로 예측-정답 쌍을 일대일 매칭하여, 앵커 박스 설정과 NMS 후처리를 완전히 제거했습니다.

**Grounding DINO (2023)**: 텍스트 쿼리로 임의의 객체를 탐지하는 Open-Vocabulary Detection 모델입니다. DINO 탐지 모델과 언어 모델(BERT)을 결합하여, 학습 시 보지 못한 카테고리의 객체도 자연어 설명만으로 탐지할 수 있습니다. SAM과 결합하면 텍스트 기반의 세그멘테이션도 가능합니다.

---

## Segment Anything과 범용 세그멘테이션

세그멘테이션은 이미지의 각 픽셀을 분류하는 태스크로, Semantic Segmentation(클래스별), Instance Segmentation(객체별), Panoptic Segmentation(둘의 결합)으로 나뉩니다. SAM의 등장으로 "프롬프트 기반 범용 세그멘테이션"이라는 새로운 패러다임이 열렸습니다.

### 세그멘테이션 모델 발전사

| 모델 | 연도 | 유형 | 핵심 기여 | 학습 데이터 규모 |
|------|------|------|----------|----------------|
| FCN | 2015 | Semantic | 첫 end-to-end 세그멘테이션 CNN | PASCAL VOC |
| U-Net | 2015 | Semantic | 인코더-디코더 + Skip Connection (의료 영상) | 소규모 의료 데이터 |
| Mask R-CNN | 2017 | Instance | Faster R-CNN + Mask Branch | COCO |
| DeepLab v3+ | 2018 | Semantic | Atrous Conv + ASPP + 인코더-디코더 | PASCAL VOC, Cityscapes |
| [SAM](/post/sam) | 2023 | Promptable | 프롬프트 기반 범용 세그멘테이션 | SA-1B (11M 이미지, 1.1B 마스크) |
| [SAM 2](/post/sam-2) | 2024 | Video | 비디오 세그멘테이션 + Streaming Architecture | SA-V (50.9K 비디오) |

**SAM (Segment Anything Model, 2023)**: 비전의 기반 모델(Foundation Model)로, 포인트, 박스, 텍스트 등 다양한 프롬프트로 어떤 객체든 세그멘테이션할 수 있습니다. 11M개 이미지에서 1.1B개의 마스크(SA-1B 데이터셋)로 학습되었으며, Image Encoder(ViT-H) + Prompt Encoder + Mask Decoder의 3단 구조로 이루어져 있습니다.

**SAM 2 (2024)**: SAM을 비디오로 확장한 모델입니다. Streaming Architecture를 채택하여, 이전 프레임의 메모리를 활용해 비디오 전체에 걸쳐 일관된 객체 추적과 세그멘테이션을 수행합니다. 첫 프레임에서 프롬프트를 주면, 이후 프레임에서 자동으로 해당 객체를 추적합니다.

:::warning
SAM은 "Segment Anything"이라는 이름처럼 범용 세그멘테이션을 목표로 하지만, 의료 영상이나 위성 영상 등 학습 데이터에 포함되지 않은 도메인에서는 성능이 저하될 수 있습니다. 도메인 특화 데이터로 파인튜닝하거나, MedSAM 같은 특화 모델을 사용하는 것이 권장됩니다.
:::

---

## Vision-Language 모델의 발전

비전과 언어를 연결하는 Vision-Language Model(VLM)은 최근 AI에서 가장 활발한 연구 분야 중 하나입니다. 이미지 이해, 시각적 질의응답, 이미지 캡셔닝, 시각 기반 추론 등 다양한 태스크를 수행합니다.

### VLM 아키텍처 유형별 비교

비전과 언어를 연결하는 방법은 크게 네 가지 패러다임으로 발전해 왔습니다.

| 패러다임 | 대표 모델 | 연결 방식 | 장점 | 단점 |
|---------|----------|---------|------|------|
| 대조 학습 (Contrastive) | [[clip]], [SigLIP](/post/siglip) | 이미지-텍스트 유사도 학습 | 제로샷 분류, 검색에 강함 | 생성 불가, 세밀한 이해 한계 |
| Bridge 모듈 | [[blip-2]], [Flamingo](/post/flamingo) | 비전 인코더와 LLM 사이에 연결 모듈 삽입 | 기존 모델 재활용 가능 | 추가 모듈 학습 필요 |
| 직접 프로젝션 | [LLaVA](/post/llava) | 비전 특징을 LLM 입력 공간에 선형 매핑 | 구조 단순, 학습 효율적 | 프로젝션 품질에 의존 |
| 네이티브 멀티모달 | [Chameleon](/post/chameleon), [Emu3](/post/emu3) | 이미지를 토큰으로 변환, 단일 모델로 처리 | 이해+생성 통합 | 대규모 학습 필요 |

### 주요 Vision-Language 모델 비교

| 모델 | 연도 | 아키텍처 패러다임 | 비전 인코더 | LLM | 핵심 기여 |
|------|------|-----------------|-----------|-----|----------|
| [[clip]] | 2021 | 대조 학습 | ViT-L/14 | - | 4억 이미지-텍스트 쌍 대조 학습, 제로샷 분류 |
| [SigLIP](/post/siglip) | 2023 | 대조 학습 | ViT | - | Sigmoid Loss로 CLIP 개선 (배치 내 쌍 독립) |
| [[blip-2]] | 2023 | Bridge (Q-Former) | EVA-ViT-G | FlanT5/OPT | Q-Former로 비전-언어 연결, 효율적 학습 |
| [Flamingo](/post/flamingo) | 2022 | Bridge (Perceiver) | NFNet | Chinchilla | Few-shot Visual QA, Perceiver Resampler |
| [LLaVA](/post/llava) | 2023 | 직접 프로젝션 | CLIP ViT-L | Vicuna | 비전-언어 대화, GPT-4 생성 학습 데이터 |
| [LLaVA-OneVision](/post/llava-onevision) | 2024 | 직접 프로젝션 | SigLIP | Qwen2 | 이미지/비디오/멀티이미지 통합 |
| [InternVL-3](/post/internvl-3) | 2025 | 하이브리드 | InternViT-6B | InternLM2 | 오픈소스 최강 VLM |
| [Janus Pro](/post/janus-pro) | 2025 | 분리 인코딩 | SigLIP (이해) / VQ (생성) | DeepSeek-LLM | 이해/생성 인코더 분리 |

### CLIP: 비전-언어 연결의 기반

[[clip]] (Contrastive Language-Image Pre-training)은 현대 VLM의 초석입니다. 4억 개의 이미지-텍스트 쌍을 대조 학습(contrastive learning)하여, 이미지와 텍스트를 동일한 임베딩 공간에 정렬합니다. 이를 통해 학습 시 보지 못한 카테고리에 대해서도 자연어 설명만으로 분류가 가능한 제로샷(zero-shot) 능력을 획득했습니다.

CLIP의 비전 인코더는 이후 LLaVA, BLIP-2, Stable Diffusion 등 수많은 모델의 비전 백본으로 재활용되며, 현대 멀티모달 AI의 핵심 구성 요소가 되었습니다.

---

## 비전 기술의 핵심 개념 정리

### 1. 어텐션 메커니즘의 비전 적용

Transformer의 Self-Attention을 비전에 적용하는 방식은 다양하게 발전했습니다.

| 어텐션 유형 | 대표 모델 | 복잡도 | 특징 |
|-----------|----------|-------|------|
| 글로벌 어텐션 | ViT | $O(n^2)$ | 전체 패치 간 관계 계산 |
| 윈도우 어텐션 | Swin Transformer | $O(n)$ | 로컬 윈도우 내에서만 계산 |
| Cross-Attention | DETR, BLIP-2 | $O(nm)$ | 두 시퀀스 간 관계 (쿼리-이미지) |
| Deformable Attention | Deformable DETR | $O(n)$ | 학습된 소수의 키 포인트만 참조 |

### 2. 패치 임베딩과 위치 인코딩

Vision Transformer에서 이미지를 시퀀스로 변환하는 방법입니다.

- **고정 크기 패치 분할**: ViT, DeiT에서 사용. 이미지를 $P \times P$ (보통 16x16) 패치로 분할 후 선형 프로젝션
- **계층적 패치 분할**: Swin Transformer에서 사용. 초기에 작은 패치(4x4)로 시작하여 점진적으로 병합(patch merging)
- **가변 해상도**: NaViT, SigLIP 2에서 사용. 원본 종횡비를 유지하며 패치 수를 동적으로 조절

### 3. 비전-언어 정렬 (Vision-Language Alignment)

비전 인코더의 출력을 LLM이 이해할 수 있는 형태로 변환하는 것이 VLM의 핵심 과제입니다.

- **대조 학습 정렬**: CLIP 방식. 이미지와 텍스트의 임베딩 공간을 공유하도록 학습
- **Q-Former 정렬**: BLIP-2 방식. 학습 가능한 쿼리 토큰이 비전 특징에서 LLM에 적합한 표현을 추출
- **선형 프로젝션 정렬**: LLaVA 방식. 단순한 MLP로 비전 특징을 LLM 토큰 공간에 매핑
- **토큰화 정렬**: Chameleon 방식. 이미지를 VQ-VAE 토큰으로 변환하여 텍스트 토큰과 동일하게 처리

---

## 비전과 다른 분야의 교차점

컴퓨터 비전은 현대 AI의 거의 모든 분야와 긴밀히 연결되어 있습니다.

| 교차 분야 | 대표 모델 | 핵심 연결 | 응용 |
|----------|----------|---------|------|
| Vision + LLM | [LLaVA](/post/llava), GPT-4V | 비전 인코더 + LLM 결합 | 멀티모달 대화, 이미지 분석 |
| Vision + Diffusion | ControlNet, DALL-E 3 | 비전 조건부 이미지 생성 | 이미지 생성/편집/인페인팅 |
| Vision + 3D | NeRF, 3D Gaussian Splatting | 2D 이미지에서 3D 복원 | 3D 재구성, 뷰 합성 |
| Vision + Agent | Computer Use, WebVoyager | 시각 입력 기반 행동 결정 | GUI 자동화, 웹 브라우징 |
| Vision + Robotics | RT-2, PaLM-E | 비전 이해 + 로봇 제어 | 자율 조작, 내비게이션 |
| Vision + Medical | MedSAM, BiomedCLIP | 의료 영상 특화 | 병변 탐지, 진단 보조 |

---

## 추천 학습 경로

### 초심자 (컴퓨터 비전 입문)

CNN 기초와 Vision Transformer의 핵심 원리를 이해하는 단계입니다. 수학적 기반(선형대수, 확률론)이 있다면 더 수월합니다.

**학습 순서**:
1. CNN 기초 개념 이해 (합성곱, 풀링, 활성화 함수, ResNet의 skip connection)
2. [ViT](/post/vit) 논문 정독 - Vision Transformer의 기본 원리와 패치 임베딩 이해
3. [DeiT](/post/deit) - 효율적 ViT 학습과 Knowledge Distillation
4. [Swin Transformer](/post/swin-transformer) - 계층적 비전 Transformer와 윈도우 어텐션
5. [[clip]] - 비전-언어 연결의 출발점, 대조 학습 이해

**추천 실습**: ImageNet 서브셋으로 ViT 파인튜닝, CLIP으로 제로샷 이미지 분류 실험

### 중급 (분야별 심화)

세부 분야별로 깊이 있게 학습합니다. 관심 분야에 따라 트랙을 선택하세요.

**Detection & Segmentation 트랙**:
1. [DETR](/post/detr) - End-to-End Detection과 Bipartite Matching 이해
2. [Grounding DINO](/post/grounding-dino) - Open-Vocabulary Detection
3. [SAM](/post/sam) - Segment Anything와 프롬프트 기반 세그멘테이션
4. [SAM 2](/post/sam-2) - 비디오 세그멘테이션과 Streaming Architecture

**Self-Supervised Learning 트랙**:
1. [MAE](/post/mae) - Masked Autoencoder의 원리와 높은 마스킹 비율의 의미
2. [DINOv2](/post/dinov2) - 대규모 자기지도 학습과 범용 비전 표현
3. [V-JEPA 2](/post/v-jepa-2) - 비디오 자기지도 학습과 잠재 공간 예측

**Vision-Language 트랙**:
1. [[clip]] + [SigLIP](/post/siglip) - 대조 학습 패러다임의 발전
2. [[blip-2]] - Q-Former를 통한 비전-LLM 연결
3. [LLaVA](/post/llava) - 프로젝션 방식의 VLM과 학습 데이터 구축

### 고급 (최신 연구 및 응용)

최전선의 비전 연구를 추적하고, 실제 시스템에 적용하는 단계입니다.

1. [InternVL-3](/post/internvl-3) - 최신 오픈소스 VLM의 아키텍처와 학습 전략
2. [PaliGemma 2](/post/paligemma-2) - 효율적 VLM과 다양한 다운스트림 태스크
3. [Chameleon](/post/chameleon) + [Emu3](/post/emu3) - 네이티브 멀티모달 아키텍처
4. [Janus Pro](/post/janus-pro) - 이해/생성 인코더 분리 전략
5. [[diffusion-models-guide]] - Diffusion 기반 비전과의 연결
6. Embodied AI - RT-2, PaLM-E 등 로보틱스와의 결합

:::tip
논문을 읽을 때는 "이 논문이 해결하려는 문제가 무엇인가?"를 먼저 파악하세요. 기술적 디테일보다 **문제 정의와 핵심 아이디어**를 이해하는 것이 중요합니다. 각 모델이 이전 모델의 어떤 한계를 극복했는지를 추적하면 전체 발전 흐름이 명확해집니다.
:::

---

## 관련 카테고리

- [[ai-ml-architecture-roadmap|전체 AI/ML 지형도]]
- [[diffusion-models-guide|비전과 밀접한 확산 모델 가이드]]
- [AI 핵심 기법 총정리](/post/ai-core-techniques-guide) - 비전에 사용되는 핵심 기법
- [LLM 핵심 논문 가이드](/post/llm-paper-guide) - 멀티모달 LLM과의 연결
