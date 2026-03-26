# LLaVA-OneVision: 단일 모델로 모든 시각 이해를 통합

## 개요

LLaVA-OneVision은 2024년 8월 ByteDance와 UW(워싱턴대학교)가 공동 발표한 통합 멀티모달 모델이다. LLaVA 시리즈의 최신작으로, **단일 이미지, 다중 이미지, 비디오 이해**를 하나의 모델로 처리하는 것이 핵심 목표이다.

기존 VLM들은 단일 이미지 이해에 특화되어 있거나, 비디오를 위해 별도의 시간적 모듈을 추가해야 했다. LLaVA-OneVision은 **AnyRes(Any Resolution)** 기법으로 고해상도 이미지를 그리드 분할하여 처리하고, 비디오를 "시간순으로 나열된 다중 이미지"로 통합하여 단일 모델로 모든 시각 입력을 유연하게 다룬다. 0.5B부터 72B까지 다양한 크기로 제공되며, Qwen2 LLM을 기반으로 시각 이해 성능에서 오픈소스 최고 수준을 달성하였다.

논문: [LLaVA-OneVision: Easy Visual Task Transfer](https://arxiv.org/abs/2408.03326)

## 아키텍처 상세

### 전체 구조

아래 그림은 LLaVA-OneVision의 전체 네트워크 아키텍처를 보여준다. 단일 이미지, 다중 이미지, 비디오를 하나의 파이프라인으로 처리하는 구조가 핵심이다.

![LLaVA-OneVision 네트워크 아키텍처 — SigLIP 비전 인코더, MLP 프로젝터, Qwen2 LLM으로 구성](figures/fig_1.png)
*Figure 1: LLaVA-OneVision 네트워크 아키텍처 — SigLIP 비전 인코더가 단일/다중 이미지 및 비디오 프레임을 인코딩하고, 2-layer MLP 프로젝터가 시각 토큰을 언어 공간으로 매핑하며, Qwen2 LLM이 언어 응답을 생성한다. (Source: Li et al., 2024)*

LLaVA-OneVision은 LLaVA의 간결한 아키텍처를 유지한다:

1. **비전 인코더**: SigLIP-SO400M/14 (400M params)
2. **MLP 프로젝터**: 2-layer MLP (비전 → 언어 공간 매핑)
3. **언어 모델**: Qwen2-0.5B / 7B / 72B

### AnyRes 고해상도 처리

AnyRes는 임의 해상도의 이미지를 효율적으로 처리하는 핵심 기법이다. 아래 그림은 개선된 Higher AnyRes와 기존 AnyRes의 비교를 보여준다.

![Higher AnyRes와 기존 AnyRes 비교 — Bilinear Interpolation을 통한 고해상도 이미지 처리](figures/fig_2.png)
*Figure 2: AnyRes 시각 표현 전략 비교 — (a) Higher AnyRes는 고해상도 이미지를 그리드 분할 후 개별 인코딩하고, Bilinear Interpolation으로 공간 관계를 보존한다. (b) 기존 AnyRes는 단순 분할-인코딩-평탄화 방식을 사용한다. (Source: Li et al., 2024)*

$$I \in \mathbb{R}^{H \times W \times 3} \rightarrow \{T_{\text{base}}, T_{1,1}, T_{1,2}, ..., T_{m,n}\}$$

처리 과정:
1. **베이스 이미지**: 전체 이미지를 384×384로 리사이즈하여 글로벌 컨텍스트 제공
2. **그리드 분할**: 원본 이미지를 최적 그리드(예: 2×2, 3×2)로 분할하여 각 타일 384×384
3. **개별 인코딩**: 각 타일을 SigLIP으로 독립 인코딩
4. **통합**: 베이스 + 타일 시각 토큰을 LLM에 입력

예를 들어 1024×768 이미지는 2×2 그리드 + 베이스 = 5개 타일로 처리된다.

### 다중 이미지 및 비디오 처리

LLaVA-OneVision의 핵심 통찰은 **비디오 = 시간순 다중 이미지**라는 것이다:

- **단일 이미지**: AnyRes로 고해상도 처리
- **다중 이미지**: 각 이미지를 순서대로 시각 토큰으로 변환하여 나열
- **비디오**: 균일 샘플링된 프레임을 다중 이미지처럼 처리

이 통합적 접근으로 별도의 시간적 모듈(temporal attention 등) 없이도 비디오 이해가 가능하다. 아래 그림은 각 시나리오별 시각 토큰 할당 전략을 보여준다.

![단일 이미지, 다중 이미지, 비디오 시나리오별 시각 토큰 할당 전략](figures/fig_3.png)
*Figure 3: 시나리오별 시각 토큰 할당 전략 — 단일/다중 이미지와 비디오에서 최대 시각 토큰 수를 유사하게 유지하여 크로스-시나리오 능력 전이를 촉진한다. SigLIP의 384x384 입력 기준 729개 토큰이 기본 단위이다. (Source: Li et al., 2024)*

| 구성 요소 | 사양 |
|-----------|------|
| 비전 인코더 | SigLIP-SO400M/14 |
| LLM | Qwen2-7B / 72B |
| 프로젝터 | 2-layer MLP |
| 이미지 해상도 | 384 base + AnyRes 타일 |
| 최대 타일 수 | 12 |
| 비디오 프레임 | 최대 32 프레임 |
| 컨텍스트 길이 | 32,768 |

## 핵심 혁신

### 1. 단일-다중-비디오 통합

하나의 아키텍처, 하나의 학습 파이프라인으로 세 가지 시각 입력 유형을 모두 처리한다. 이는 배포와 서빙의 복잡성을 크게 줄여준다.

### 2. 태스크 전이(Task Transfer)

단일 이미지로 학습한 능력이 다중 이미지와 비디오 이해로 자연스럽게 전이된다. "Easy Visual Task Transfer"라는 부제가 이를 나타낸다.

### 3. 체계적 학습 레시피

3단계 학습 파이프라인을 통해 점진적으로 능력을 확장하는 체계적 접근을 제시하였다. 특히 Stage 2에서 학습된 단일 이미지 이해 능력이 Stage 3의 다중 이미지/비디오로 자연스럽게 전이되는 현상은, 시각 이해의 근본 능력이 입력 형태에 무관하게 일반화될 수 있음을 보여준다.

### 4. 데이터 레시피의 중요성

아래 그림은 OneVision 1.6M 데이터셋의 구성을 보여준다. 단일 이미지, 다중 이미지, 비디오 데이터가 균형 있게 배합된 것이 핵심이다.

![OneVision 1.6M 데이터셋 구성 — 단일 이미지, 다중 이미지, 비디오 데이터 분포](figures/fig_5.png)
*Figure 4: OneVision 1.6M 데이터셋 구성 — 단일 이미지, 다중 이미지, 비디오 데이터를 포함하는 고품질 데이터 컬렉션의 카테고리별 분포. 외측 원은 전체 카테고리 비율, 내측 원은 서브셋 분포를 나타낸다. (Source: Li et al., 2024)*

LLaVA-OneVision은 다양한 데이터 혼합 비율을 실험하여 최적의 학습 레시피를 도출하였다. VQA, OCR, 차트/다이어그램, 과학/수학, 비디오 캡셔닝 등 데이터 카테고리별 비율이 최종 성능에 큰 영향을 미치며, 이 데이터 레시피 자체가 중요한 연구 기여이다. AnyRes의 타일 수와 시각 토큰 수가 학습 효율과 성능 간의 트레이드오프를 결정하며, 최대 12개 타일까지 지원하여 4K 이상의 고해상도 문서 분석도 가능하다.

## 벤치마크/성능

### 단일 이미지

| 벤치마크 | LLaVA-OV-72B | InternVL2-76B | Qwen2-VL-72B |
|----------|------------|-------------|-------------|
| MMBench | **85.9** | 84.6 | 83.0 |
| MMMU | **56.8** | 51.2 | 54.1 |
| MathVista | **67.5** | 65.5 | 70.5 |

### 비디오

| 벤치마크 | LLaVA-OV-72B | GPT-4V | InternVL2-76B |
|----------|------------|--------|-------------|
| VideoMME | **66.2** | — | 60.7 |
| MVBench | **67.5** | — | 64.2 |

## 관련 모델 비교

| 특성 | LLaVA-OV | InternVL 2 | Qwen2-VL | MiniCPM-V |
|------|---------|-----------|---------|-----------|
| 비전 인코더 | SigLIP-400M | InternViT-6B | ViT-675M | SigLIP-400M |
| 이미지 처리 | AnyRes | 동적 타일링 | 동적 해상도 | AnyRes |
| 비디오 방식 | 프레임 시퀀스 | 프레임 시퀀스 | 3D RoPE | 프레임 시퀀스 |
| LLM | Qwen2 | InternLM2 | Qwen2 | Llama-3 |
| 모델 크기 | 0.5B~72B | 2B~76B | 2B~72B | 3B~8B |

## 학습 상세

3단계 학습 파이프라인:

**Stage 1: 비전-언어 정렬**
- MLP 프로젝터만 학습
- 이미지-캡션 데이터 사용
- SigLIP + LLM 고정

**Stage 2: 고해상도 단일 이미지 파인튜닝**
- AnyRes 적용, 전체 모델 파인튜닝
- VQA, OCR, 캡셔닝, 차트·다이어그램 데이터 혼합
- LLaVA-OneVision 데이터 레시피 적용

**Stage 3: 다중 이미지 + 비디오 파인튜닝**
- Stage 2에서 학습된 단일 이미지 능력을 기반으로
- 다중 이미지 데이터 + 비디오 데이터로 추가 파인튜닝
- 단일 이미지 성능을 유지하면서 다중/비디오 능력 추가

## 실무 활용

```python
from llava.model.builder import load_pretrained_model
from llava.mm_utils import process_images, tokenizer_image_token

model_path = "lmms-lab/llava-onevision-qwen2-7b-ov"
tokenizer, model, image_processor, _ = load_pretrained_model(
    model_path, None, "llava_qwen"
)

# 단일 이미지 QA
image = Image.open("chart.png")
response = model.generate(
    images=[image],
    prompt="이 차트의 트렌드를 분석해주세요."
)

# 비디오 이해
frames = extract_frames("video.mp4", num_frames=16)
response = model.generate(
    images=frames,
    prompt="이 비디오에서 일어나는 일을 설명해주세요."
)
```

## 한계 및 전망

### 한계

1. **비디오 길이**: 32프레임 제한으로 긴 비디오의 세부 이해에 한계
2. **시간적 추론**: 별도의 시간적 모듈이 없어 정교한 시간 관계 추론에 약할 수 있다
3. **생성 불가**: 이미지/비디오 이해에 특화, 생성 능력 부재

### 전망

LLaVA-OneVision은 LLaVA 시리즈의 "단순함" 철학을 유지하면서 시각 이해의 범위를 크게 확장하였다. 단일·다중·비디오를 통합하는 접근은 실용적 배포 관점에서 매우 유용하며, 향후 오디오, 3D 등 추가 모달리티로의 확장과 이미지 생성 능력의 통합이 기대된다.

## 관련 문서

- [[llava|Visual Instruction Tuning]] — 발전 기반
