# DETR: 종단간 객체 탐지 트랜스포머

**Meta/FAIR** · **2020-05-01** · **Vision** · **Apache-2.0**

## 개요

DETR(DEtection TRansformer)는 2020년 Meta/FAIR의 Nicolas Carion 등이 발표한 종단간(end-to-end) 객체 탐지 모델로, 컴퓨터 비전의 객체 탐지 패러다임을 근본적으로 변혁한 연구이다. 기존의 객체 탐지 파이프라인은 앵커 박스 설계(9가지 비율/스케일 조합), Region Proposal Network(RPN), Non-Maximum Suppression(NMS 임계값 튜닝), Feature Pyramid Network(FPN), 양성/음성 샘플 비율 설정, 그리고 복잡한 후처리 과정이 필수적이었다. Faster R-CNN, RetinaNet, YOLO 등 모든 주류 탐지기가 이러한 수작업 구성요소에 의존했으며, 이들의 하이퍼파라미터는 데이터셋과 도메인에 따라 세밀한 조정이 필요했다.

DETR는 이 모든 수작업 구성요소를 단번에 제거하고, 트랜스포머의 집합 예측(set prediction) 능력을 활용하여 이미지에서 직접 객체 집합을 예측하는 단순하고 우아한 프레임워크를 제시하였다. 핵심 아이디어는 객체 탐지를 "집합 예측 문제"로 재정의하고, 헝가리안 알고리즘을 사용한 이분 매칭(bipartite matching)으로 예측과 정답의 일대일 대응을 구조적으로 보장하는 것이다. 이를 통해 중복 탐지가 원천적으로 방지되어 NMS가 완전히 불필요해졌다. COCO 벤치마크에서 고도로 최적화된 Faster R-CNN과 동등한 42.0 AP를 달성하면서도, 코드베이스는 기존 탐지기의 절반 이하로 간결해졌다. DETR의 등장은 이후 Deformable DETR, DN-DETR, DAB-DETR, DINO-DETR, Grounding DINO, RT-DETR 등 DETR 계열 모델의 풍성한 연구 생태계를 촉발하였다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

다음 다이어그램은 DETR의 전체 파이프라인을 보여준다.

![DETR 전체 아키텍처 — CNN 백본, 트랜스포머 인코더-디코더, 예측 헤드](figures/fig_2.png)
*Figure 1: DETR 아키텍처 — CNN 백본으로 이미지 특징을 추출하고, 트랜스포머 인코더-디코더에 입력한 뒤, 학습 가능한 객체 쿼리를 통해 클래스와 바운딩 박스를 병렬로 예측한다. (Source: Carion et al., 2020)*

DETR는 세 가지 핵심 구성요소로 이루어진다: CNN 백본, 트랜스포머 인코더-디코더, 그리고 이분 매칭 기반 손실 함수이다.

### CNN 백본과 위치 인코딩

ResNet-50 또는 ResNet-101을 백본으로 사용하여 입력 이미지에서 고수준 특징 맵을 추출한다. 입력 이미지가 $H_0 \times W_0$일 때, 백본은 $C = 2048$ 채널의 $\frac{H_0}{32} \times \frac{W_0}{32}$ 크기 특징 맵을 출력한다. 이 특징 맵을 $1 \times 1$ 컨볼루션으로 채널 수를 $d = 256$으로 축소한 뒤, 공간 차원을 $H \cdot W$ 길이의 시퀀스로 펼친다. 각 위치에 2D 사인 위치 인코딩을 추가하여 공간 정보를 보존한다:

$$\text{PE}(x, y, 2i) = \sin\!\left(\frac{x}{10000^{2i/d}}\right),\quad \text{PE}(x, y, 2i+1) = \cos\!\left(\frac{x}{10000^{2i/d}}\right)$$

$x$와 $y$ 방향의 인코딩을 각각 $d/2$ 차원으로 생성한 뒤 연결(concatenate)하여 총 $d = 256$ 차원의 위치 임베딩을 생성한다. DC5(dilated C5) 변종에서는 마지막 ResNet 단계에서 stride를 제거하고 dilated convolution을 사용하여 해상도를 2배로 높인다.

### 트랜스포머 인코더

6개의 인코더 레이어(각각 8-head Multi-Head Self-Attention, ReLU 활성화, LayerNorm)가 특징 맵 시퀀스에 전역 셀프 어텐션을 적용한다. 모든 공간 위치 간의 관계를 모델링하여, 객체 간의 전역적 맥락 정보가 특징에 반영된다. 예를 들어, 한 사람이 다른 사람에게 가려져 있는 상황에서 가림 관계를 인식하거나, 테이블 위의 물체들의 공간적 배치를 파악하는 데 전역 어텐션이 핵심적인 역할을 한다. 아래 시각화는 인코더가 개별 객체 인스턴스를 분리하는 능력을 보여준다.

![인코더 셀프 어텐션 시각화 — 참조 포인트별 어텐션 맵](figures/fig_3.png)
*Figure 2: 인코더 셀프 어텐션 시각화 — 각 참조 포인트에서의 어텐션 맵이 개별 소 인스턴스를 명확히 분리하여, 인코더가 전역 문맥에서 객체 인스턴스를 구분하는 능력을 보여준다. (Source: Carion et al., 2020)*

### 트랜스포머 디코더와 객체 쿼리

DETR의 가장 혁신적인 요소는 **학습 가능한 객체 쿼리(object queries)**이다. $N$개(기본값 100)의 학습 가능한 벡터 $\mathbf{q}_i \in \mathbb{R}^d$가 디코더에 입력되며, 각 쿼리는 다음 과정을 거쳐 하나의 객체 예측을 담당한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right)V$$

디코더 내에서 (1) 쿼리 간 셀프 어텐션은 쿼리들이 서로 다른 객체에 특화되도록 분화(specialization)를 촉진하고, (2) 쿼리-인코더 출력 간 교차 어텐션은 각 쿼리가 이미지의 관련 영역에 주목하도록 유도한다. 학습 후 시각화하면 각 쿼리가 특정 공간 영역과 객체 크기에 자연스럽게 특화되는 것을 확인할 수 있다. 아래는 디코더가 각 예측 객체에 대해 사지(extremities)에 집중하는 어텐션 패턴이다.

![디코더 어텐션 시각화 — 객체별로 다른 색상으로 어텐션 스코어 표시](figures/fig_7_1.png)
*Figure 3: 디코더 어텐션 시각화 — 각 예측 객체에 대해 디코더가 다리, 머리 등 객체의 사지(extremities)에 집중하며, 서로 다른 객체를 명확히 구분하여 탐지한다. (Source: Carion et al., 2020)* 최종적으로 각 쿼리는 독립적인 FFN 헤드를 통해 클래스 확률 $\hat{p}_i \in \mathbb{R}^{C+1}$ (배경 클래스 포함)과 바운딩 박스 좌표 $\hat{b}_i = (c_x, c_y, w, h) \in [0,1]^4$를 출력한다.

| 구성요소 | 사양 |
|---------|------|
| 백본 | ResNet-50/101 (ImageNet 사전학습) |
| 인코더 레이어 | 6 |
| 디코더 레이어 | 6 |
| 히든 차원 $d$ | 256 |
| 어텐션 헤드 | 8 |
| 객체 쿼리 수 $N$ | 100 |
| FFN 히든 차원 | 2048 |
| 총 파라미터 | 41M (R50) / 60M (R101) |

### 이분 매칭 손실

DETR의 학습 손실은 헝가리안 알고리즘(Hungarian Algorithm)을 사용한 이분 매칭으로 설계된다. $N$개의 예측과 $M$개의 정답($M \leq N$, 나머지는 "no object" $\varnothing$로 패딩) 사이에 최적의 일대일 순열 매칭 $\hat{\sigma}$를 찾는다:

$$\hat{\sigma} = \underset{\sigma \in \mathfrak{S}_N}{\arg\min} \sum_{i=1}^{N} \mathcal{L}_\text{match}(y_i, \hat{y}_{\sigma(i)})$$

매칭 비용 $\mathcal{L}_\text{match}$는 분류 확률, L1 박스 거리, GIoU(Generalized IoU)의 가중합이다. 최적 매칭이 결정된 후, 학습 손실은 매칭된 쌍에 대해 계산된다:

$$\mathcal{L}_\text{Hungarian} = \sum_{i=1}^{N}\left[-\log \hat{p}_{\hat{\sigma}(i)}(c_i) + \mathbb{1}_{\{c_i \neq \varnothing\}} \left(\lambda_\text{L1}\|b_i - \hat{b}_{\hat{\sigma}(i)}\|_1 + \lambda_\text{giou}\mathcal{L}_\text{giou}(b_i, \hat{b}_{\hat{\sigma}(i)})\right)\right]$$

이 방식으로 각 정답 객체에 정확히 하나의 예측만 매칭되므로, 중복 탐지가 구조적으로 방지되어 NMS가 완전히 불필요해진다. 헝가리안 알고리즘의 시간 복잡도는 $O(N^3)$이나, $N=100$ 정도에서는 무시할 수 있는 수준이다.

다음 그래프는 디코더 레이어별 AP 변화를 통해 NMS의 불필요성을 입증한다.

![디코더 레이어별 AP 및 NMS 적용 여부에 따른 성능 변화](figures/fig_5.png)
*Figure 4: NMS 불필요성 입증 — 디코더 후반 레이어에서 NMS 적용 시 오히려 AP가 하락하여 (TP 제거), DETR의 이분 매칭이 중복 탐지를 구조적으로 방지함을 보여준다. (Source: Carion et al., 2020)*

## 핵심 혁신

1. **NMS 완전 제거**: 이분 매칭이 예측-정답 간 일대일 대응을 구조적으로 보장하므로, 중복 탐지가 원천적으로 발생하지 않는다. 이는 NMS 임계값이라는 데이터셋 의존적 하이퍼파라미터를 제거하여 탐지 파이프라인의 복잡도를 획기적으로 줄인다.

2. **앵커 프리(Anchor-free) 설계**: 사전 정의된 앵커 박스, 앵커 비율, 앵커 스케일이 전혀 필요 없다. 객체 쿼리가 학습을 통해 자연스럽게 다양한 위치, 크기, 종횡비의 객체를 탐색하도록 특화된다.

3. **전역 추론 능력**: 전역 셀프/교차 어텐션을 통해 이미지 전체 맥락에서 객체를 탐지하므로, 큰 객체(AP_L 61.1 vs Faster R-CNN 53.4)와 객체 간 관계 파악에서 월등한 강점을 보인다.

4. **통합 파노라마 세그멘테이션**: 마스크 헤드(어텐션 맵 기반)만 추가하면 동일 프레임워크에서 파노라마 세그멘테이션(stuff + things 동시 분할)으로 자연스럽게 확장된다.

## 벤치마크/성능

| 모델 | 백본 | COCO AP | AP₅₀ | AP_S | AP_M | AP_L | 파라미터 |
|------|------|---------|------|------|------|------|---------|
| DETR | R50 | 42.0 | 62.4 | 20.5 | 45.3 | 61.1 | 41M |
| DETR-DC5 | R50 | 43.3 | 63.1 | 22.5 | 47.3 | 61.1 | 41M |
| DETR | R101 | 43.5 | 63.8 | 21.9 | 46.9 | 61.8 | 60M |
| DETR-DC5 | R101 | 44.9 | 64.7 | 23.7 | 49.5 | 62.3 | 60M |
| Faster R-CNN-FPN | R50 | 42.0 | 62.1 | 26.6 | 44.4 | 53.4 | 42M |
| Faster R-CNN-FPN | R101 | 44.0 | 63.9 | 27.2 | 46.1 | 55.4 | 60M |

DETR의 전역 어텐션 덕분에 학습 데이터에 없는 수준의 객체 밀도에서도 일반화 능력을 보인다.

![학습 데이터에 없는 24마리 이상의 기린 탐지 — 분포 밖 일반화](figures/fig_6.jpg)
*Figure 5: 분포 밖 일반화 — 학습 데이터에 최대 13마리의 기린만 존재했지만, DETR은 24마리 이상의 기린도 어려움 없이 탐지한다. 전역 어텐션이 임의 개수의 객체 탐지를 가능하게 한다. (Source: Carion et al., 2020)*

DETR-R50은 Faster R-CNN-R50-FPN과 동등한 전체 AP(42.0)를 달성하며, AP_L(대형 객체)에서 61.1 vs 53.4로 큰 격차를 보인다. 반면 AP_S(소형 객체)에서는 20.5 vs 26.6으로 열세인데, 이는 전역 어텐션의 해상도 한계와 단일 스케일 특징 맵에 기인한다. 이 약점은 후속 모델 Deformable DETR에서 멀티스케일 변형 어텐션으로 해결되었다.

## 학습

COCO 2017 탐지 데이터셋(118K 학습 이미지, 5K 검증 이미지, 80 클래스)으로 300 에폭 학습한다. ResNet 백본은 ImageNet 사전학습 가중치로 초기화하며, 트랜스포머 부분은 Xavier 초기화를 사용한다. 주요 설정은 다음과 같다:

- **옵티마이저**: AdamW
- **학습률**: 트랜스포머 1e-4, 백본 1e-5 (200 에폭에서 1/10으로 감소)
- **Weight decay**: 1e-4
- **배치 크기**: 64 (8×V100 GPU)
- **학습 시간**: 약 3일 (300 에폭, 8×V100)
- **Dropout**: 인코더/디코더 어텐션에 0.1
- **손실 가중치**: $\lambda_\text{L1} = 5$, $\lambda_\text{giou} = 2$, $\lambda_\text{cls} = 1$
- **보조 손실**: 각 디코더 레이어의 출력에서 보조 예측 손실 적용

300 에폭이라는 긴 학습은 DETR의 알려진 약점이다. Faster R-CNN이 12 에폭만에 수렴하는 것에 비해 25배 이상 오래 걸리며, 이는 객체 쿼리가 특정 공간 영역에 특화되는 과정이 느리기 때문이다.

## 관련 모델

DETR는 객체 탐지의 트랜스포머 시대를 연 선구적 모델이다. 수렴 속도 문제를 해결한 Deformable DETR(변형 가능 어텐션, 50 에폭), 쿼리 디노이징의 DN-DETR, 앵커 기반 쿼리의 DAB-DETR, 자기지도 사전학습의 DINO-DETR, 오픈셋 탐지의 Grounding DINO, 실시간 탐지의 RT-DETR 등으로 발전하며, DETR 계열은 현재 객체 탐지의 주류 패러다임이 되었다.

## 참고 자료

- 논문: [End-to-End Object Detection with Transformers](https://arxiv.org/abs/2005.12872)
- 코드: [github.com/facebookresearch/detr](https://github.com/facebookresearch/detr)

## 관련 문서

- [[transformer|Transformer]] — 발전 기반
- [[grounding-dino|Grounding DINO]] — 후속 모델