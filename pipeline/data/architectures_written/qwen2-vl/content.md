# Qwen2-VL: 동적 해상도와 M-RoPE로 달성한 오픈소스 최강 VLM

## 개요

Qwen2-VL은 2024년 9월 Alibaba가 발표한 시각-언어 모델이다. 두 가지 핵심 혁신이 이 모델을 정의한다: **네이티브 동적 해상도(Naive Dynamic Resolution)** 처리와 **멀티모달 로터리 위치 임베딩(M-RoPE, Multimodal Rotary Position Embedding)**이다.

기존 VLM들이 이미지를 고정 크기로 리사이즈하거나 그리드로 분할하여 처리한 것과 달리, Qwen2-VL은 이미지의 원본 해상도에 비례한 수의 시각 토큰을 직접 사용하여 정보 손실을 최소화한다. M-RoPE는 텍스트의 1D 위치, 이미지의 2D 위치(행/열), 비디오의 3D 위치(행/열/시간)를 하나의 통합된 RoPE 프레임워크로 처리하여, 모달리티 간 위치 정보의 일관성을 보장한다.

2B, 7B, 72B 세 가지 크기로 제공되며, 발표 당시 오픈소스 모델 중 최고 수준의 시각 이해 성능을 달성하여 GPT-4V와 경쟁하는 수준에 도달했다.

논문: [Qwen2-VL: Enhancing Vision-Language Model's Perception of the World at Any Resolution](https://arxiv.org/abs/2409.12191)

아래 다이어그램은 Qwen2-VL의 전체 아키텍처를 보여준다. 다양한 해상도의 이미지와 비디오를 네이티브 해상도로 입력받아 각각에 비례하는 시각 토큰으로 처리하는 구조가 핵심이다.

![Qwen2-VL 아키텍처 — 네이티브 해상도 입력과 동적 토큰 처리](figures/fig_2.jpg)
*Figure 1: Qwen2-VL 아키텍처 개요 — Vision Encoder가 다양한 해상도의 이미지/비디오를 네이티브 해상도 그대로 처리하여 비례적인 토큰 수를 생성하고, QwenLM Decoder가 통합 시퀀스로 처리한다. (Source: Wang et al., 2024)*

## 아키텍처 상세

### 전체 구조

1. **비전 인코더**: ViT-675M (자체 학습, 14×14 패치)
2. **MLP 프로젝터**: 2-layer MLP (비전 → 언어 매핑)
3. **언어 모델**: Qwen2-2B / 7B / 72B

### 네이티브 동적 해상도(Naive Dynamic Resolution)

기존 방식과의 차이:

| 방식 | 처리 방법 | 문제점 |
|------|---------|--------|
| 고정 리사이즈 | 모든 이미지 → 224px | 고해상도 정보 손실 |
| AnyRes (LLaVA) | 그리드 분할 + 개별 인코딩 | 타일 경계 정보 단절 |
| **동적 해상도 (Qwen2-VL)** | **원본 비례 토큰 수** | **정보 보존 극대화** |

Qwen2-VL의 동적 해상도 처리:

$$n_{\text{tokens}} = \left\lceil \frac{H}{14} \right\rceil \times \left\lceil \frac{W}{14} \right\rceil / 4$$

여기서 /4는 2×2 풀링으로 시각 토큰 수를 1/4로 압축하는 것이다. 예를 들어:
- 224×224 이미지: 16×16/4 = 64 토큰
- 1344×896 이미지: 96×64/4 = 1536 토큰

고해상도 이미지는 더 많은 토큰으로, 저해상도는 적은 토큰으로 처리하여 정보 밀도를 일정하게 유지한다.

### M-RoPE (Multimodal Rotary Position Embedding)

M-RoPE는 RoPE를 세 가지 모달리티의 위치 정보에 맞게 확장한 것이다:

**텍스트**: 1D 위치 (순서)
$$\text{RoPE}_{\text{text}}(x_t) = \text{RoPE}(x, \text{pos}=t)$$

**이미지**: 2D 위치 (행, 열)
$$\text{RoPE}_{\text{image}}(x_{i,j}) = \text{RoPE}(x, \text{height}=i, \text{width}=j, \text{temporal}=0)$$

**비디오**: 3D 위치 (행, 열, 시간)
$$\text{RoPE}_{\text{video}}(x_{i,j,t}) = \text{RoPE}(x, \text{height}=i, \text{width}=j, \text{temporal}=t)$$

RoPE의 주파수 차원을 세 그룹으로 분할하여 각각 height, width, temporal 위치를 인코딩한다. 텍스트의 경우 세 차원이 동일한 값을 가져 1D로 동작한다. 아래 그림은 M-RoPE가 비디오와 텍스트의 위치 정보를 통합하는 방식을 보여준다.

![M-RoPE의 temporal, height, width 차원 분리 인코딩](figures/fig_3.png)
*Figure 2: M-RoPE 구조 — RoPE의 주파수 차원을 temporal, height, width 세 축으로 분해하여 이미지(2D), 비디오(3D), 텍스트(1D)의 위치 정보를 하나의 통합 프레임워크로 처리한다. (Source: Wang et al., 2024)*

| 구성 요소 | Qwen2-VL-72B |
|-----------|-------------|
| 비전 인코더 | ViT-675M (14×14 패치) |
| LLM | Qwen2-72B |
| 위치 인코딩 | M-RoPE |
| 컨텍스트 길이 | 32,768 |
| 히든 차원 | 8192 |
| 레이어 수 | 80 |

## 핵심 혁신

### 1. 네이티브 동적 해상도

이미지를 인위적으로 분할하지 않고 원본 해상도에 비례한 토큰으로 처리하여, 타일 경계에서의 정보 단절 문제가 없다. 이는 문서 내 표, 차트 등 연속적인 시각 요소 이해에서 특히 유리하다. 다음은 최소 해상도(min_pixels) 설정에 따른 벤치마크 성능 변화이다.

![min_pixels 설정에 따른 다양한 벤치마크 성능 변화](figures/fig_4.png)
*Figure 3: 동적 해상도 효과 — 이미지 최소 해상도를 높이면 InfoVQA, OCRBench 등 세밀한 인식이 필요한 태스크에서 성능이 향상되어, 해상도와 인식 품질의 직접적 상관관계를 보여준다. (Source: Wang et al., 2024)*

### 2. M-RoPE

텍스트·이미지·비디오의 위치 정보를 하나의 통합된 프레임워크로 처리하여, 모달리티 전환 시 위치 정보의 불일치가 없다. 비디오의 시간 차원까지 자연스럽게 인코딩하여 별도의 시간적 모듈 없이 비디오를 이해한다.

### 3. 강력한 OCR 및 문서 이해

동적 해상도 + M-RoPE의 결합으로 고해상도 문서의 세밀한 텍스트를 정확히 인식하고, 레이아웃 구조를 이해하여 표, 차트, 수식 등을 정확히 해석한다.

## 벤치마크/성능

| 벤치마크 | Qwen2-VL-72B | GPT-4V | InternVL2-76B | LLaVA-OV-72B |
|----------|-------------|--------|-------------|------------|
| MMMU | **54.1** | 56.8 | 51.2 | 56.8 |
| DocVQA | **93.1** | 87.2 | 91.6 | 91.3 |
| OCRBench | **85.5** | 78.0 | 83.9 | 71.3 |
| MathVista | **70.5** | 58.1 | 65.5 | 67.5 |
| VideoMME | **63.3** | — | 60.7 | 66.2 |

## 관련 모델 비교

| 특성 | Qwen2-VL | Pixtral | InternVL 2 | LLaVA-OV |
|------|---------|---------|-----------|---------|
| 해상도 처리 | 동적 (원본 비례) | 임의 (2D RoPE) | 동적 타일링 | AnyRes |
| 위치 인코딩 | **M-RoPE** | 2D RoPE | Learned | RoPE |
| 비디오 이해 | 3D M-RoPE | 미지원 | 프레임 시퀀스 | 프레임 시퀀스 |
| 컨텍스트 | 32K | 128K | 32K | 32K |

M-RoPE 덕분에 Qwen2-VL은 학습 시 최대 시퀀스 길이를 넘어서는 추론도 안정적으로 수행한다.

![학습 시퀀스 길이를 초과한 추론에서의 M-RoPE 길이 외삽 성능](figures/fig_5.png)
*Figure 4: M-RoPE 길이 외삽 — 학습 최대 길이(16,384 토큰)를 초과하는 추론 시퀀스에서도 Video-MME 성능이 안정적으로 유지되어, M-RoPE의 외삽 능력을 입증한다. (Source: Wang et al., 2024)*

모델 크기와 학습 데이터의 증가에 따른 성능 향상 패턴은 다음과 같다.

![모델 크기 및 학습 진행에 따른 성능 스케일링](figures/fig_6.jpg)
*Figure 5: 스케일링 거동 — (a) 2B→8B→72B 파라미터 증가에 따라 OCR, 비디오, VQA 등 모든 능력이 일관되게 향상. (b) 학습 토큰 증가에 따라 다양한 벤치마크에서 꾸준한 성능 개선이 관찰된다. (Source: Wang et al., 2024)*

## 학습 상세

2단계 학습:

**Stage 1: 비전 인코더 사전학습**
- ViT-675M을 대규모 이미지-텍스트 데이터로 학습
- 다양한 해상도의 이미지를 동적으로 처리

**Stage 2: 통합 파인튜닝**
- 웹 이미지-텍스트, OCR, 비디오 데이터 혼합
- 동적 배치 구성: 같은 배치 내에 다양한 해상도의 이미지 혼합
- M-RoPE로 모든 모달리티의 위치 정보 통합

## 실무 활용

```python
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import torch

model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct", torch_dtype=torch.bfloat16
).to("cuda")
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")

messages = [{"role": "user", "content": [{"type": "image", "image": "document.png"}, {"type": "text", "text": "이 문서의 표를 읽어주세요."}]}]

inputs = processor(text=processor.apply_chat_template(messages), images=["document.png"], return_tensors="pt").to("cuda")
output = model.generate(**inputs, max_new_tokens=500)
```

## 한계 및 전망

### 한계

1. **토큰 수 변동**: 동적 해상도로 인해 이미지별 토큰 수가 크게 다르므로, 배치 처리 시 패딩 비효율이 발생한다
2. **고해상도 비용**: 매우 큰 이미지는 수천 개의 시각 토큰을 생성하여 추론 비용이 급증한다
3. **Dense 모델 한계**: 72B 밀집 모델로 MoE 대비 추론 효율이 낮다

### 전망

Qwen2-VL의 동적 해상도와 M-RoPE는 이후 Qwen3-VL에서 향상된 추론 능력과 결합되어 더욱 강력한 모델로 발전하고 있다. M-RoPE의 우아한 설계는 다른 VLM에도 영향을 미치며, 특히 비디오 이해에서의 시간 차원 인코딩은 중요한 기여이다.

## 관련 문서

- [[qwen2|Qwen2 Technical Report]] — 발전 기반
- [[qwen3-vl|Qwen3-VL]] — 후속 모델
