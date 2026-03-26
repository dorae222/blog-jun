# LLaVA: 시각적 인스트럭션 튜닝의 시작

## 개요

LLaVA(Large Language and Vision Assistant)는 2023년 4월 위스콘신-매디슨대학교와 Microsoft Research가 공동 발표한 멀티모달 언어 모델이다. Haotian Liu 등이 제안한 이 모델은 CLIP 비전 인코더와 LLaMA 언어 모델을 **단순한 선형 프로젝션 레이어 하나**로 연결하는 극도로 간결한 구조를 채택했다.

LLaVA의 가장 큰 기여는 두 가지이다. 첫째, **GPT-4를 활용한 멀티모달 인스트럭션 데이터 자동 생성** 방법론을 제시했다. 둘째, 단순한 아키텍처와 적은 학습 비용(약 $200)으로도 강력한 멀티모달 대화 능력을 달성할 수 있음을 보여, **멀티모달 AI 연구의 민주화**를 촉진했다. Science QA에서 GPT-4와 조합하여 92.53%의 정확도를 달성했다.

논문: [Visual Instruction Tuning](https://arxiv.org/abs/2304.08485) (NeurIPS 2023 Oral)

## 아키텍처 상세

다음 다이어그램은 LLaVA의 전체 아키텍처와 2단계 학습 파이프라인을 상세히 보여준다.

![LLaVA 전체 아키텍처 다이어그램 — CLIP 비전 인코더, 선형 프로젝션, LLaMA 디코더 구조](figures/architecture.png)
*Figure 1: LLaVA 아키텍처 개요 — CLIP ViT-L/14 비전 인코더, Visual-Language Projection, LLaMA 디코더의 전체 파이프라인과 2단계 학습 과정(Feature Alignment + Instruction Tuning). (Source: Liu et al.)*

### 전체 구조

LLaVA의 구조는 세 가지 컴포넌트로 구성된다:

1. **비전 인코더**: CLIP ViT-L/14 (고정)
2. **프로젝션 레이어**: 학습 가능한 선형 행렬 $W \in \mathbb{R}^{d_v \times d_l}$
3. **언어 모델**: LLaMA-7B 또는 LLaMA-13B

아래 그림은 LLaVA의 간결한 네트워크 구조를 보여준다. 비전 인코더의 시각 토큰이 프로젝션 레이어를 통해 언어 모델 공간으로 매핑되는 과정을 확인할 수 있다.

![LLaVA 네트워크 구조 — 비전 인코더, 프로젝션 W, 언어 모델의 간결한 연결](figures/fig_1.png)
*Figure 2: LLaVA 네트워크 구조 — 이미지 $X_v$가 비전 인코더를 통해 시각 특징 $Z_v$로 변환되고, 프로젝션 $W$를 통해 시각 토큰 $H_v$가 된다. 텍스트 토큰 $H_q$와 결합되어 언어 모델이 응답 $X_a$를 생성한다. (Source: arXiv 2304.08485)*

시각 정보 처리 과정:

$$H_v = W \cdot g(X_v)$$

여기서 $g(\cdot)$은 CLIP 비전 인코더, $X_v$는 입력 이미지, $W$는 프로젝션 행렬이다. 변환된 시각 토큰 $H_v$는 텍스트 토큰과 함께 LLaMA에 입력된다.

### 인스트럭션 데이터 생성

GPT-4를 활용하여 COCO 이미지 캡션으로부터 세 가지 유형의 인스트럭션 데이터를 자동 생성했다:

| 데이터 유형 | 설명 | 수량 |
|------------|------|------|
| Conversation | 이미지에 대한 다턴 대화 | 58K |
| Detailed Description | 상세한 이미지 설명 | 23K |
| Complex Reasoning | 복합 추론이 필요한 질문 | 77K |
| **합계** | **LLaVA-Instruct-158K** | **158K** |

이미지의 바운딩 박스와 캡션 정보를 GPT-4에 제공하고, 다양한 유형의 질문-답변 쌍을 생성하도록 프롬프트를 설계하였다. 이 방법론은 이후 대부분의 VLM 연구에서 합성 데이터 생성의 표준 접근법이 되었다.

### 2단계 학습

**Stage 1: 비전-언어 정렬 (Pre-training)**
- 데이터: CC3M에서 선별한 595K 이미지-캡션 쌍
- 학습 대상: 프로젝션 레이어 $W$만 학습 (비전 인코더 + LLM 고정)
- 비용: A100 1장, 약 4시간

**Stage 2: 비주얼 인스트럭션 튜닝 (Fine-tuning)**
- 데이터: LLaVA-Instruct-158K
- 학습 대상: 프로젝션 레이어 $W$ + LLM 전체 파인튜닝
- 비용: A100 8장, 약 24시간
- 총 비용: **약 $200**

## 핵심 혁신

### 1. 극도의 단순성

BLIP-2의 Q-Former(188M), Flamingo의 Perceiver Resampler(수십M)와 달리, LLaVA는 **단일 선형 레이어**(수M 파라미터)만으로 비전-언어 연결을 달성했다. 이 극단적 단순함은:
- 구현이 쉬워 수많은 후속 연구를 촉진
- 핵심 병목이 아키텍처가 아니라 데이터임을 시사
- LLaVA-1.5에서 MLP(2-layer)로 교체만으로 큰 성능 향상

### 2. GPT-4 기반 합성 데이터 생성

인간 주석 없이 GPT-4를 활용하여 고품질 멀티모달 인스트럭션 데이터를 자동 생성하는 방법론은 데이터 수집 비용을 획기적으로 줄였다. 이 접근은 ShareGPT4V, ALLaVA 등 후속 데이터셋에서 더욱 정교하게 발전하였다.

### 3. 오픈소스 생태계 형성

모델 가중치, 학습 코드, 데이터셋을 모두 공개하여 활발한 오픈소스 생태계를 형성했다. LLaVA-1.5, LLaVA-NeXT, LLaVA-OneVision 등으로 시리즈가 발전하고, 수백 개의 파생 연구가 탄생했다. 아래는 LLaVA의 멀티턴 대화 능력을 보여주는 예시이다. 이미지에 대해 연속적인 질문을 처리하며 맥락을 유지한다.

![LLaVA 멀티턴 대화 예시 — 냉장고 이미지를 보고 요리 추천 및 레시피를 제공하는 대화](figures/fig_7_1.png)
*Figure 3: LLaVA 멀티턴 대화 — 냉장고 이미지를 인식하고 요리 추천, 이어서 레시피를 제공하는 연속 대화 예시. 사용자의 의도를 정확히 파악하여 상세한 응답을 생성한다. (Source: arXiv 2304.08485)*

## 벤치마크/성능

| 벤치마크 | LLaVA-13B | GPT-4 (text only) | 비고 |
|----------|----------|-------------------|------|
| Science QA | 90.92% | 82.69% | LLaVA+GPT-4 = 92.53% |
| LLaVA-Bench (Conv) | 64.3 | 75.3 | GPT-4 대비 85.1% |
| LLaVA-Bench (Detail) | 72.5 | 75.3 | 상세 설명 |

LLaVA-1.5(후속 버전)에서 MLP 프로젝터와 추가 데이터로 크게 향상:

| 벤치마크 | LLaVA-1.5-13B | BLIP-2 | InstructBLIP |
|----------|-------------|--------|-------------|
| VQAv2 | **80.0%** | 65.0% | 72.5% |
| GQA | **63.3%** | 44.7% | 49.5% |
| TextVQA | **61.3%** | 42.5% | 50.7% |

## 관련 모델 비교

| 특성 | LLaVA | BLIP-2 | Flamingo | MiniGPT-4 |
|------|-------|--------|----------|-----------  |
| 프로젝터 | Linear → MLP | Q-Former | Perceiver | Linear |
| LLM 학습 | Full FT | Frozen | Frozen | Frozen |
| 학습 비용 | ~$200 | ~$10K | ~$100K+ | ~$300 |
| 데이터 규모 | 158K inst | 수십M | 수십B | 5K inst |
| 핵심 철학 | 단순함 | 효율적 브릿지 | 소수샷 | 대화형 |

## 학습 상세

| 항목 | Stage 1 | Stage 2 |
|------|---------|---------|
| 목적 | 비전-언어 정렬 | 인스트럭션 튜닝 |
| 데이터 | CC-595K | LLaVA-Instruct-158K |
| 학습 대상 | 프로젝션만 | 프로젝션 + LLM |
| 에폭 | 1 | 3 |
| 배치 크기 | 256 | 128 |
| 학습률 | 2e-3 | 2e-5 |
| GPU | A100 ×1 | A100 ×8 |
| 시간 | ~4시간 | ~24시간 |

## 실무 활용

```python
from llava.model.builder import load_pretrained_model
from llava.mm_utils import get_model_name_from_path, process_images
from llava.conversation import conv_templates

model_path = "liuhaotian/llava-v1.5-7b"
tokenizer, model, image_processor, context_len = load_pretrained_model(
    model_path, None, get_model_name_from_path(model_path)
)

# 이미지 + 텍스트 입력으로 대화
image = Image.open("photo.jpg")
query = "What do you see in this image?"

conv = conv_templates["v1"].copy()
conv.append_message(conv.roles[0], f"<image>\n{query}")
conv.append_message(conv.roles[1], None)
prompt = conv.get_prompt()
# ... generate response
```

### LLaVA 시리즈 발전

| 모델 | 발표 | 핵심 개선 | 주요 변경 |
|------|------|----------|----------|
| LLaVA | 2023.04 | 선형 프로젝터 | 최초의 비주얼 인스트럭션 튜닝 |
| LLaVA-1.5 | 2023.10 | MLP 프로젝터 | +ShareGPT 데이터, 336px |
| LLaVA-NeXT | 2024.01 | AnyRes | 동적 해상도, 더 큰 LLM |
| LLaVA-OneVision | 2024.08 | 멀티이미지+비디오 | 통합 시각 이해 |

## 한계 및 전망

### 한계

1. **환각(Hallucination)**: 이미지에 없는 내용을 생성하는 문제가 심각
2. **공간 추론**: 객체 위치, 크기, 관계 추론에 취약
3. **고해상도 처리**: 초기 버전은 224/336px 저해상도만 지원
4. **단일 이미지**: 다중 이미지, 비디오 처리 불가 (v1 기준)

### 전망

다음은 LLaVA가 손으로 그린 스케치를 HTML/JS 코드로 변환하는 시각-코드 생성 능력을 보여주는 예시이다.

![LLaVA 이미지-코드 변환 — 손그림 스케치에서 인터랙티브 웹사이트 코드 생성](figures/fig_6.png)
*Figure 4: LLaVA 시각-코드 생성 — 사용자가 그린 웹사이트 스케치를 인식하여 HTML/JS 코드를 생성하고, 실제 동작하는 인터랙티브 웹페이지로 변환한다. (Source: arXiv 2304.08485)*

LLaVA는 "단순함이 최고의 복잡함"이라는 철학을 멀티모달 AI에서 실증한 기념비적 연구이다. "비전 인코더 + 프로젝터 + LLM" 패턴은 2024-2025년 거의 모든 오픈소스 VLM의 표준 구조가 되었으며, GPT-4 기반 합성 데이터 생성은 데이터 엔지니어링의 새 지평을 열었다. LLaVA가 보여준 "적은 비용, 큰 임팩트"의 철학은 학술 연구의 접근성을 크게 높여 멀티모달 AI 분야의 폭발적 성장을 견인하였다.

## 관련 문서

- [[llava-onevision|LLaVA-OneVision]] — 후속 모델
- [[llama|LLaMA: Open and Efficient Foundation Language Models]] — 영감
- [[vit|An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale]] — 영감
- [[cogvlm|CogVLM]] — 영감을 줌
- [[minicpm-v|MiniCPM-V]] — 영감을 줌
- [[molmo|Molmo]] — 영감을 줌
