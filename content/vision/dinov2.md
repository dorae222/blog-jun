---
title: "DINOv2: 비전 트랜스포머 기반 모델"
slug: dinov2
category: vision
tags: ["DINOv2", "Knowledge Distillation", "Meta", "Self-Supervised Learning", "Vision Foundation Model"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.464837+00:00"
architecture_entry: dinov2
---

# DINOv2: 자기지도 비전 파운데이션 모델

**Meta/FAIR** · **2023-04-01** · **Vision** · **Apache-2.0**

## 개요

DINOv2는 2023년 Meta/FAIR의 Maxime Oquab 등이 발표한 자기지도 학습(Self-Supervised Learning) 기반 비전 파운데이션 모델이다. 레이블 없이 대규모 이미지 데이터만으로 학습하여 분류, 세그멘테이션, 깊이 추정, 인스턴스 검색 등 다양한 비전 태스크에서 범용적으로 활용 가능한 시각 특징을 생성한다. DINOv2는 기존 DINO(2021)의 자기증류(self-distillation) 프레임워크와 iBOT의 마스킹 이미지 모델링(MIM)을 결합하고, 체계적으로 정제된 1억 4,200만 장의 이미지 데이터셋(LVD-142M)으로 학습하여, 파인튜닝 없이 선형 프로빙(frozen backbone + linear classifier)만으로 ImageNet top-1 86.5%라는 놀라운 성능을 달성하였다.

DINOv2의 등장은 비전 분야에서도 NLP의 GPT/BERT처럼 "레이블 없는 대규모 사전학습 → 다운스트림 적용"이라는 파운데이션 모델 패러다임이 실현 가능함을 증명한 이정표적 연구이다. 기존의 CLIP이나 SigLIP이 텍스트-이미지 쌍이라는 약한 감독 신호를 필요로 했던 것과 달리, DINOv2는 어떠한 형태의 감독 신호(레이블, 캡션, 태그)도 없이 순수하게 시각 데이터만으로 범용 표현을 학습한다는 점에서 근본적으로 차별화된다. 특히 깊이 추정, 의미론적 세그멘테이션, 인스턴스 검색 등 CLIP이 직접 적용되기 어려운 밀집 예측(dense prediction) 태스크에서도 탁월한 성능을 발휘하며, 패치 수준의 풍부한 지역적 표현이 이를 가능하게 한다. DINOv2는 의료 영상, 위성 이미지, 제조 품질 검사 등 전문 도메인에서도 파인튜닝 없이 높은 성능을 보여 실무적 가치가 매우 높다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

### ViT 백본과 스케일링

DINOv2는 ViT(Vision Transformer) 아키텍처를 기반으로 하며, 기존 ViT-B/16(패치 크기 16)보다 세밀한 공간 해상도를 위해 14×14 패치 크기를 채택하였다. 다양한 규모의 모델을 제공하여 연산 제약에 따른 유연한 선택이 가능하다:

| 모델 | 레이어 | 히든 차원 | 헤드 수 | 파라미터 | 패치 크기 |
|------|--------|----------|--------|---------|----------|
| ViT-S/14 | 12 | 384 | 6 | 21M | 14×14 |
| ViT-B/14 | 12 | 768 | 12 | 86M | 14×14 |
| ViT-L/14 | 24 | 1024 | 16 | 307M | 14×14 |
| ViT-g/14 | 40 | 1536 | 24 | 1.1B | 14×14 |

518×518 입력 이미지에서 $37 \times 37 = 1{,}369$개의 패치 토큰을 생성하며, [CLS] 토큰을 포함하여 총 1,370개의 토큰 시퀀스를 처리한다. ViT-g/14가 주력 모델이며, 디스틸레이션을 통해 ViT-g의 지식을 ViT-S/B/L로 전달하여 경량 모델도 강력한 성능을 갖도록 한다.

### 학습 목표: DINO + iBOT 결합

DINOv2의 학습 프레임워크는 두 가지 자기지도 목표를 동시에 최적화하여, 전역적 의미 표현과 지역적 세밀 표현을 동시에 학습한다:

**1. 이미지 수준 DINO 자기증류 손실**: Student와 Teacher 네트워크의 [CLS] 토큰 출력 분포 간 교차 엔트로피를 최소화한다. Teacher는 Student의 EMA(Exponential Moving Average)로 업데이트되며, centering과 sharpening을 적용하여 표현 붕괴(mode collapse)를 방지한다:

$$\mathcal{L}_\text{DINO} = -\sum_{x \in \{x_1^g, x_2^g\}} \sum_{\substack{x' \in V \\ x' \neq x}} \sum_k p_t^{(k)}(x) \log p_s^{(k)}(x')$$

여기서 $p_t$와 $p_s$는 각각 Teacher와 Student의 softmax 출력(프로젝션 헤드 통과 후)이며, $V$는 글로벌+로컬 뷰의 집합이다. Teacher의 출력은 centering($c$를 빼서 특정 차원으로의 붕괴 방지)과 sharpening(낮은 온도 $\tau_t$로 분포 첨예화)을 거친다.

**2. 패치 수준 iBOT 마스킹 이미지 모델링 손실**: 입력 패치의 일부를 [MASK] 토큰으로 대체하고, 마스킹된 위치의 Teacher 패치 토큰 출력을 Student가 예측하도록 학습한다:

$$\mathcal{L}_\text{iBOT} = -\sum_{i \in \mathcal{M}} \sum_k q_t^{(i,k)} \log q_s^{(i,k)}$$

여기서 $\mathcal{M}$은 마스킹된 패치 인덱스 집합이고, $q_t^{(i,k)}$와 $q_s^{(i,k)}$는 패치 $i$에서의 Teacher/Student 출력 분포이다. 이 손실은 패치 수준의 세밀한 지역 표현을 학습하게 하여, 세그멘테이션이나 깊이 추정 같은 밀집 예측 태스크에서의 성능을 크게 향상시킨다.

### 멀티크롭 전략과 KoLeo 정규화

**멀티크롭**: 학습 시 하나의 이미지에서 2개의 글로벌 뷰(큰 크기 크롭, 해상도 224² 이상)와 다수의 로컬 뷰(작은 크기 크롭, 해상도 96²)를 생성한다. Teacher는 글로벌 뷰만 처리하고, Student는 모든 뷰를 처리하여, Student가 부분적 정보(로컬 뷰)로부터 전역적 의미를 추론하도록 강제한다. 이 비대칭 구조가 스케일 불변 표현 학습을 촉진한다.

**KoLeo 정규화**: 특징 공간에서 임베딩이 균일하게 분포하도록 Kozachenko-Leonenko(KoLeo) 정규화를 적용한다:

$$\mathcal{L}_\text{KoLeo} = -\frac{1}{n}\sum_{i=1}^{n} \log\!\left(d_{\text{nn}}(z_i)\right)$$

여기서 $d_{\text{nn}}(z_i)$는 배치 내에서 임베딩 $z_i$와 가장 가까운 이웃 간의 유클리드 거리이다. 이 정규화는 임베딩 공간의 차원 붕괴(dimensional collapse)를 방지하고 표현의 다양성과 균일성을 보장한다.

## 핵심 혁신

1. **LVD-142M 데이터셋 구축**: 웹에서 수집한 12억 이미지 후보에서 copy detection으로 중복 제거, NSFW 필터링, PII 처리(얼굴 블러링)를 거쳐 1.42억 이미지의 고품질 데이터셋을 구축하였다. ImageNet-1K의 이미지를 "앵커"로 사용하여 임베딩 공간에서 유사 이미지를 검색하는 retrieval 기반 방식으로 데이터 분포를 제어하였다. 무작위 웹 이미지보다 정제된 데이터가 모델 성능에 미치는 영향을 체계적으로 분석한 점이 주요 기여이다.

2. **스케일링 효율성**: Flash Attention(메모리 효율적 어텐션), FSDP(Fully Sharded Data Parallelism), xFormers 등 효율적 학습 기법을 종합 적용하여 1.1B 규모의 ViT-g를 64개 A100에서 안정적으로 학습하였다. 모델 디스틸레이션을 통해 ViT-g의 지식을 ViT-S/B/L로 효율적으로 전달한다.

3. **파인튜닝 없는 범용 특징**: CLIP과 달리 텍스트 감독 없이 학습했음에도, 선형 프로빙만으로 분류, 세그멘테이션, 깊이 추정, 검색 등 다양한 태스크에서 최고 수준의 성능을 달성한다. 패치 토큰의 풍부한 지역 표현이 밀집 예측 태스크에서 특히 강력하다.

## 벤치마크/성능

| 태스크 | DINOv2 ViT-g/14 | OpenCLIP ViT-G/14 | MAE ViT-H | 지도학습 ViT-L |
|--------|-----------------|-------------------|-----------|----|
| ImageNet 선형 프로빙 | **86.5%** | 80.1% | 76.6% | 85.0% |
| ImageNet k-NN | **83.5%** | - | - | - |
| ADE20K 세그멘테이션 (mIoU) | **49.0** | - | 48.1 | 47.6 |
| NYUd 깊이 추정 (RMSE↓) | **0.279** | - | 0.342 | - |
| Oxford-Paris 검색 (mAP) | **82.6** | - | - | - |
| 전이 학습 12개 벤치마크 평균 | **최고** | - | - | - |

DINOv2는 파인튜닝 없이 선형 프로빙만으로 다양한 비전 태스크에서 지도 학습 모델에 필적하거나 능가하는 성능을 달성한다. 특히 깊이 추정(RMSE 0.279 vs MAE 0.342)과 세그멘테이션(mIoU 49.0)에서의 강점이 두드러지며, 이는 패치 수준의 풍부한 지역 표현 덕분이다.

## 학습

- **데이터셋**: LVD-142M (1.42억 이미지, 레이블 없음, retrieval 기반 정제)
- **배치 크기**: 3072
- **옵티마이저**: AdamW ($\beta_1$=0.9, $\beta_2$=0.999)
- **Teacher EMA**: momentum $0.994 \to 1.0$ (cosine 스케줄)
- **Centering**: Sinkhorn-Knopp 정규화
- **GPU**: 64×A100 80GB
- **학습 기간**: 약 2주 (ViT-g/14)
- **해상도 적응**: 학습 후 518×518 해상도로 10 에폭 추가 적응 학습
- **디스틸레이션**: ViT-g를 Teacher로, ViT-S/B/L을 Student로 학습
- **학습 목표**: $\mathcal{L} = \mathcal{L}_\text{DINO} + \mathcal{L}_\text{iBOT} + \mathcal{L}_\text{KoLeo}$

## 관련 모델

DINOv2는 DINO(2021)의 자기증류와 iBOT의 패치 수준 MIM을 결합한 모델로, 이후 DINOv3(2025, 7B)로 스케일업되었다. CLIP/SigLIP과 달리 텍스트 정렬이 없어 제로샷 텍스트 기반 분류는 불가하지만, 밀집 예측 태스크에서는 우위를 보인다. Depth Anything, Grounding DINO, SAM 등 후속 모델의 비전 백본으로 널리 활용되며, 특히 의료 영상과 위성 이미지 분석에서 파인튜닝 없이 높은 성능을 보여 실무적 가치가 매우 높다.

## 참고 자료

- 논문: [DINOv2: Learning Robust Visual Features without Supervision](https://arxiv.org/abs/2304.07193)
- 코드: [github.com/facebookresearch/dinov2](https://github.com/facebookresearch/dinov2)

## 관련 문서

- [[vit|An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale]] — 발전 기반
- [[dinov3|DINOv3]] — 후속 모델