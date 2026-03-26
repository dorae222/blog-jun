# Grounding DINO: 오픈셋 언어 기반 객체 탐지

**IDEA Research** · **2023-03-01** · **Vision** · **Apache-2.0**

## 개요

Grounding DINO는 2023년 IDEA Research의 Shilong Liu 등이 발표한 오픈셋(open-set) 객체 탐지 모델로, 자연어 텍스트로 설명된 임의의 객체를 이미지에서 탐지할 수 있는 혁신적 모델이다. 기존의 객체 탐지 모델은 COCO의 80 클래스, LVIS의 1,203 클래스 등 사전에 정의된 고정 카테고리(closed-set)만 탐지할 수 있었다. 학습 데이터에 포함되지 않은 새로운 클래스의 객체가 등장하면, 어노테이션 수집부터 시작하여 전체 모델을 재학습해야 하는 근본적 한계가 있었다. 이는 빠르게 변화하는 실무 환경에서 큰 비용과 시간 부담을 초래하였다.

Grounding DINO는 이 한계를 극복하여, "빨간 모자를 쓴 사람", "나무 위의 새", "깨진 창문", "빈 주차 공간" 같은 자유 텍스트 프롬프트로 탐지 대상을 실시간으로 지정할 수 있다. 학습 시 보지 못한 완전히 새로운 카테고리도 자연어로 기술하기만 하면 탐지가 가능하다. 이 모델은 DETR 계열의 DINO 탐지기(DN-DETR + DAB-DETR 계열)와 BERT 계열 텍스트 인코더를 긴밀하게 융합하여, 시각-언어 이해와 객체 탐지를 하나의 종단간 프레임워크에서 통합한다.

COCO 제로샷 탐지에서 52.5 AP를 달성하여 당시 SOTA를 기록하였으며, 기존 GLIP-L(49.8 AP)을 크게 능가하였다. SAM과 결합한 "Grounded SAM" 파이프라인은 텍스트만으로 객체 탐지와 세그멘테이션을 동시에 수행하는 강력한 도구로 실무에서 폭넓게 활용되고 있으며, 자동 데이터 어노테이션, 이미지 편집, 로보틱스 등 다양한 응용을 가능하게 하였다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

Grounding DINO의 아키텍처는 세 단계의 시각-언어 융합(tight fusion) 구조로 설계되어 있다. 기존 오픈 어휘 탐지 모델(OWL-ViT, GLIP)이 각 모달리티를 독립적으로 인코딩한 후 출력만 결합하는 얕은 융합(late fusion)을 사용한 것과 달리, Grounding DINO는 인코더 단계부터 양방향 교차 어텐션으로 깊은 융합(deep fusion)을 수행하여, 더 정밀한 텍스트-이미지 정렬을 달성한다.

### 1단계: 이중 인코더 특징 추출

**이미지 인코더**: Swin Transformer를 백본으로 사용하여 멀티스케일 특징 맵을 추출한다. Swin-T(Tiny, 28M)와 Swin-L(Large, 197M) 변종이 제공되며, 4단계($\frac{1}{4}$, $\frac{1}{8}$, $\frac{1}{16}$, $\frac{1}{32}$)의 계층적 특징을 생성하여 다양한 크기의 객체를 효과적으로 처리한다.

**텍스트 인코더**: BERT 기반 텍스트 인코더가 입력 텍스트를 토큰 단위 임베딩 $\mathbf{T} \in \mathbb{R}^{L \times d}$으로 변환한다. 입력 형식은 매우 유연하다: "cat . dog . person"처럼 카테고리를 점(.)으로 구분하거나, "a red car on the street" 같은 자연어 문장, "the largest object on the left" 같은 참조 표현(referring expression)까지 처리할 수 있다.

| 구성요소 | Grounding DINO-T | Grounding DINO-L |
|---------|-----------------|-----------------|
| 이미지 인코더 | Swin-T (28M) | Swin-L (197M) |
| 텍스트 인코더 | BERT-base (110M) | BERT-base (110M) |
| Feature Enhancer | 6 레이어 | 6 레이어 |
| 디코더 레이어 | 6 | 6 |
| 히든 차원 | 256 | 256 |
| 어텐션 헤드 | 8 | 8 |
| 총 파라미터 | ~172M | ~341M |

### 2단계: Feature Enhancer (특징 강화)

텍스트 특징과 이미지 특징 사이의 양방향 교차 어텐션(bidirectional cross-attention)을 수행하는 Feature Enhancer 모듈이 Grounding DINO의 핵심이다. 각 Feature Enhancer 레이어는 네 가지 서브 모듈로 구성된다:

$$\text{Image}' = \text{CrossAttn}(\text{Image}, \text{Text}) + \text{SelfAttn}(\text{Image})$$
$$\text{Text}' = \text{CrossAttn}(\text{Text}, \text{Image}) + \text{SelfAttn}(\text{Text})$$

이미지 → 텍스트 방향의 교차 어텐션은 텍스트의 의미 정보를 이미지 특징에 주입하고, 텍스트 → 이미지 방향의 교차 어텐션은 이미지의 시각 정보를 텍스트 특징에 반영한다. 이 양방향 융합이 여러 레이어에 걸쳐 반복됨으로써, 두 모달리티의 특징이 점진적으로 정렬(align)된다. Deformable attention을 이미지 쪽에 적용하여 멀티스케일 특징을 효율적으로 처리한다.

### 3단계: Language-Guided Query Selection과 Cross-Modality Decoder

**언어 유도 쿼리 선택(Language-Guided Query Selection)**: DETR의 학습 가능한 고정 객체 쿼리 대신, 텍스트 조건에 따라 동적으로 쿼리를 선택한다. Feature Enhancer를 통과한 이미지 특징과 텍스트 특징의 유사도 행렬을 계산하여, 텍스트와 관련성이 높은 위치에서 초기 앵커 박스와 쿼리를 생성한다:

$$\text{score}(i) = \max_j \left(\mathbf{F}_\text{img}^{(i)} \cdot \mathbf{F}_\text{text}^{(j)\top}\right)$$

상위 $N$개(기본 900) 위치가 쿼리로 선택되며, 이 쿼리들은 이미 텍스트와 관련된 위치에서 초기화되므로 수렴이 빠르고 불필요한 예측이 줄어든다.

**교차 모달 디코더(Cross-Modality Decoder)**: 선택된 쿼리가 이미지 특징과 텍스트 특징 양쪽에 교차 어텐션을 수행하여, 텍스트 조건부 객체 탐지를 완성한다. 각 쿼리의 최종 출력은 바운딩 박스 좌표 $(c_x, c_y, w, h)$와 텍스트 토큰별 유사도 벡터를 생성하며, 이 유사도가 클래스 확률을 대체한다. 따라서 고정된 클래스 집합이 아니라 임의의 텍스트에 대한 탐지가 가능해진다.

## 핵심 혁신

1. **깊은 교차 모달 융합**: 인코더 단계부터 다중 레이어에 걸친 양방향 교차 어텐션으로, 기존 얕은 융합 방식(GLIP의 dot-product fusion, OWL-ViT의 late fusion) 대비 텍스트-이미지 정렬 품질이 크게 향상된다. Ablation 결과, 깊은 융합이 COCO 제로샷 AP에서 +3.0 이상의 기여를 한다.

2. **텍스트 조건부 동적 쿼리**: 이미지와 텍스트의 유사도 기반으로 동적 생성되는 쿼리는, DETR의 고정 쿼리가 텍스트와 무관하게 전체 이미지를 탐색하는 비효율을 해결한다. 텍스트에 언급되지 않은 객체에 대한 false positive가 크게 감소한다.

3. **다양한 텍스트 포맷 지원**: 카테고리 나열("cat . dog"), 설명적 표현("a red car"), 참조 표현("the largest object on the left"), 속성 기반 쿼리("metallic objects"), 관계 표현("person holding a bag") 등을 통합적으로 처리한다.

4. **DINO-DETR 기반 종단간 탐지**: DN-DETR의 쿼리 디노이징과 DAB-DETR의 앵커 박스 쿼리를 활용하여, NMS 없이 종단간 탐지를 수행하면서도 빠른 수렴을 달성한다.

## 벤치마크/성능

| 모델 | COCO 제로샷 AP | COCO 파인튜닝 AP | LVIS AP_rare | 텍스트 입력 | NMS |
|------|---------------|-----------------|-------------|----------|-----|
| Grounding DINO-T | 48.4 | 57.2 | - | 자유 텍스트 | 불필요 |
| Grounding DINO-L | **52.5** | **59.4** | **32.7** | 자유 텍스트 | 불필요 |
| GLIP-L | 49.8 | 55.2 | 26.9 | 자유 텍스트 | 필요 |
| OWL-ViT v2 | 34.7 | - | - | 자유 텍스트 | 필요 |
| DINO-DETR | - | 63.4 | - | 고정 클래스 | 불필요 |
| Faster R-CNN-FPN | - | 42.0 | - | 고정 클래스 | 필요 |

Grounding DINO-L은 제로샷 52.5 AP로 GLIP-L(49.8)을 +2.7 AP 능가하며, LVIS의 희귀(rare) 카테고리에서 32.7로 GLIP(26.9)을 +5.8 능가한다. 이는 깊은 융합의 효과가 특히 드물거나 새로운 카테고리에서 두드러짐을 보여준다.

## 학습

Grounding DINO는 다양한 탐지 및 그라운딩 데이터셋을 혼합하여 2단계로 학습한다:

- **1단계 (오픈 어휘 탐지)**: Objects365(36.5M 박스, 365 클래스), GoldG(0.8M 그라운딩 쌍)
- **2단계 (그라운딩 파인튜닝)**: Cap4M(4M 캡션-이미지 쌍, 웹 크롤링), COCO, 추가 그라운딩 데이터
- **옵티마이저**: AdamW (학습률 1e-4, weight decay 1e-4)
- **에폭**: 12 (1단계) + 6 (2단계)
- **혼합 정밀도**: FP16
- **텍스트-이미지 매칭 손실**: 시그모이드 교차 엔트로피
  $$\mathcal{L}_\text{cls} = -\sum_{i} \left[ y_i \log \sigma(s_i) + (1-y_i) \log(1-\sigma(s_i)) \right]$$
- **박스 손실**: L1 + GIoU (DETR 계열 계승)
- **이분 매칭**: 헝가리안 알고리즘 기반

학습 시 텍스트 프롬프트를 다양하게 구성하여(카테고리 나열, 자연어 문장, 무작위 셔플 등) 텍스트 형식에 대한 강건성을 확보한다.

## 관련 모델

Grounding DINO는 DETR → DINO-DETR의 종단간 탐지 계보에 언어 이해를 결합한 모델이다. SAM과 결합한 "Grounded SAM" 파이프라인은 텍스트만으로 객체 탐지+세그멘테이션을 수행하는 강력한 도구로, 자동 데이터 어노테이션, 이미지 편집(인페인팅 마스크 생성), 로보틱스(파지 대상 식별)에 널리 사용된다. 후속 모델인 Grounding DINO 1.5/2.0에서 추론 속도와 정확도가 개선되었다.

## 참고 자료

- 논문: [Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection](https://arxiv.org/abs/2303.05499)
- 코드: [github.com/IDEA-Research/GroundingDINO](https://github.com/IDEA-Research/GroundingDINO)

## 관련 문서

- [[detr|DETR]] — 발전 기반