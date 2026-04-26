<!-- infographic-hero -->
![LLaVA 핵심 요약](figures/infographic.svg)

*Figure: LLaVA 한 장 요약 인포그래픽*

# LLaVA: 시각적 인스트럭션 튜닝의 시작

## 개요

LLaVA(Large Language and Vision Assistant)는 2023년 4월 위스콘신-매디슨대학교와 Microsoft Research가 공동 발표한 멀티모달 언어 모델이다. Haotian Liu 등이 제안한 이 모델은 CLIP 비전 인코더와 LLaMA 언어 모델을 **단순한 선형 프로젝션 레이어 하나**로 연결하는 극도로 간결한 구조를 채택했다.

LLaVA의 가장 큰 기여는 두 가지이다. 첫째, **GPT-4를 활용한 멀티모달 인스트럭션 데이터 자동 생성** 방법론을 제시했다. 둘째, 단순한 아키텍처와 적은 학습 비용(약 $200)으로도 강력한 멀티모달 대화 능력을 달성할 수 있음을 보여, **멀티모달 AI 연구의 민주화**를 촉진했다. Science QA에서 GPT-4와 조합하여 92.53%의 정확도를 달성했다.

논문: [Visual Instruction Tuning](https://arxiv.org/abs/2304.08485) (NeurIPS 2023 Oral)

## 아키텍처 상세

다음 다이어그램은 LLaVA의 전체 아키텍처와 2단계 학습 파이프라인을 상세히 보여준다.

![LLaVA 전체 아키텍처 다이어그램 - CLIP 비전 인코더, 선형 프로젝션, LLaMA 디코더 구조](figures/architecture.png)
*Figure 1: LLaVA 아키텍처 개요 - CLIP ViT-L/14 비전 인코더, Visual-Language Projection, LLaMA 디코더의 전체 파이프라인과 2단계 학습 과정(Feature Alignment + Instruction Tuning). (Source: Liu et al.)*

### 전체 구조

LLaVA의 구조는 세 가지 컴포넌트로 구성된다:

1. **비전 인코더**: CLIP ViT-L/14 (고정)
2. **프로젝션 레이어**: 학습 가능한 선형 행렬 $W \in \mathbb{R}^{d_v \times d_l}$
3. **언어 모델**: LLaMA-7B 또는 LLaMA-13B

아래 그림은 LLaVA의 간결한 네트워크 구조를 보여준다. 비전 인코더의 시각 토큰이 프로젝션 레이어를 통해 언어 모델 공간으로 매핑되는 과정을 확인할 수 있다.

![LLaVA 네트워크 구조 - 비전 인코더, 프로젝션 W, 언어 모델의 간결한 연결](figures/fig_1.png)
*Figure 2: LLaVA 네트워크 구조 - 이미지 $X_v$가 비전 인코더를 통해 시각 특징 $Z_v$로 변환되고, 프로젝션 $W$를 통해 시각 토큰 $H_v$가 된다. 텍스트 토큰 $H_q$와 결합되어 언어 모델이 응답 $X_a$를 생성한다. (Source: arXiv 2304.08485)*

시각 정보 처리 과정:

$$H_v = W \cdot g(X_v)$$

여기서 $g(\cdot)$은 CLIP 비전 인코더, $X_v$는 입력 이미지, $W$는 프로젝션 행렬이다. 변환된 시각 토큰 $H_v$는 텍스트 토큰과 함께 LLaMA에 입력된다.

### GPT-4 기반 인스트럭션 데이터 생성

LLaVA의 가장 혁신적인 기여 중 하나는 GPT-4를 활용한 멀티모달 인스트럭션 데이터 자동 생성 방법론이다. 이 접근의 핵심은 GPT-4가 이미지를 직접 보지 못하는 한계를 **텍스트 기반 이미지 표현**으로 우회한 것이다.

구체적인 데이터 생성 파이프라인은 다음과 같다:

1. **이미지의 텍스트 표현 구성**: COCO 데이터셋의 각 이미지에 대해 (a) 5개의 캡션, (b) 객체별 바운딩 박스 좌표와 카테고리를 텍스트로 구성한다.
2. **시드 프롬프트 설계**: 각 데이터 유형별로 Few-shot 예시를 포함한 시스템 프롬프트를 설계하여, GPT-4가 이미지 내용을 기반으로 자연스러운 질문-답변을 생성하도록 유도한다.
3. **다양성 보장**: Conversation, Detailed Description, Complex Reasoning 세 가지 유형을 분리 생성하여 데이터의 다양성을 확보한다.

세 가지 유형의 인스트럭션 데이터를 자동 생성했다:

| 데이터 유형 | 설명 | 수량 |
|------------|------|------|
| Conversation | 이미지에 대한 다턴 대화 | 58K |
| Detailed Description | 상세한 이미지 설명 | 23K |
| Complex Reasoning | 복합 추론이 필요한 질문 | 77K |
| **합계** | **LLaVA-Instruct-158K** | **158K** |

**Conversation 데이터**는 일상적인 이미지 질의응답을 모방하며, 사용자가 이미지에 대해 여러 번 질문하는 다턴 대화 형태이다. **Detailed Description**은 이미지의 내용을 빠짐없이 상세하게 서술하는 단일 턴 데이터로, 모델의 시각적 그라운딩 능력을 강화한다. **Complex Reasoning**은 이미지에서 관찰 가능한 정보를 바탕으로 추론, 비교, 판단을 요구하는 질문으로, 모델의 논리적 사고 능력을 향상시킨다.

이 GPT-4 기반 데이터 생성 방법론은 이후 거의 모든 VLM 연구에서 합성 데이터 생성의 표준 접근법이 되었으며, ShareGPT4V, ALLaVA, Cambrian-1 등이 이를 더욱 정교하게 발전시켰다.

### 2단계 학습: 핵심 설계 원리

LLaVA의 2단계 학습은 "먼저 정렬하고, 그 다음에 튜닝한다"는 원칙을 따른다. 이 분리가 왜 중요한지 각 단계의 역할과 설계 의도를 상세히 살펴본다.

**Stage 1: 비전-언어 특성 정렬 (Feature Alignment Pre-training)**

이 단계의 목표는 CLIP 비전 인코더의 시각 특성 공간과 LLaMA의 언어 특성 공간을 **프로젝션 레이어 $W$를 통해 정렬**하는 것이다. CLIP과 LLaMA는 각각 독립적으로 사전학습된 모델이므로, 두 모델의 특성 공간은 전혀 다른 분포를 가진다. Stage 1에서 프로젝션 레이어만 학습함으로써, 시각 토큰이 언어 모델이 이해할 수 있는 "언어"로 번역되도록 한다.

- 데이터: CC3M(Conceptual Captions)에서 선별한 595K 이미지-캡션 쌍
- 학습 대상: 프로젝션 레이어 $W$만 학습 (비전 인코더 + LLM 완전 고정)
- 비용: A100 1장, 약 4시간
- 학습 형식: 이미지를 보고 캡션을 생성하는 단순 이미지-캡션 매칭 태스크

이 단계에서 비전 인코더와 LLM을 고정하는 이유는 두 가지이다. 첫째, 사전학습된 표현을 보존하여 이미 학습된 시각적/언어적 지식을 유지한다. 둘째, 프로젝션 레이어만 학습하므로 파라미터 수가 극소(수M)하여 적은 데이터로도 효과적인 정렬이 가능하다.

**Stage 2: 비주얼 인스트럭션 튜닝 (End-to-End Fine-tuning)**

정렬된 프로젝션 레이어를 기반으로, LLM 전체를 인스트럭션 데이터로 파인튜닝한다. 이 단계에서 모델은 단순 캡션 생성을 넘어 복잡한 시각적 질의응답, 추론, 대화 능력을 학습한다.

- 데이터: LLaVA-Instruct-158K
- 학습 대상: 프로젝션 레이어 $W$ + LLM 전체 파인튜닝 (비전 인코더는 고정 유지)
- 비용: A100 8장, 약 24시간
- 총 비용: **약 $200**

Stage 2에서 비전 인코더를 여전히 고정하는 이유는 CLIP의 강력한 시각 표현을 보존하기 위함이다. LLM만 파인튜닝함으로써, 시각 정보를 "이해하는 방식"은 유지하면서 "응답하는 방식"만 인스트럭션에 맞게 조정한다.

## 핵심 혁신

### 1. 프로젝션 레이어 설계와 극도의 단순성

LLaVA의 프로젝션 설계를 선행 연구와 비교하면 그 단순함이 더욱 명확해진다.

**Flamingo (DeepMind, 2022)**: Perceiver Resampler(수십M 파라미터)를 사용하여 가변 길이의 시각 토큰을 고정 수의 잠재 토큰으로 압축한다. 또한 Gated Cross-Attention 레이어를 LLM의 각 레이어에 삽입하여 시각 정보를 주입하므로, LLM 아키텍처 자체를 수정해야 한다.

**BLIP-2 (Salesforce, 2023)**: Q-Former(188M 파라미터)라는 별도의 Transformer 모듈을 도입하여, 학습 가능한 쿼리 토큰이 시각 특성과 Cross-Attention을 수행한다. 2단계 사전학습(Image-Text Matching + Image-Grounded Text Generation)이 필요하며, 구현과 재현이 복잡하다.

**LLaVA**: 이에 비해 LLaVA는 **단일 선형 레이어** $W \in \mathbb{R}^{d_v \times d_l}$(수M 파라미터)만으로 비전-언어 연결을 달성했다. CLIP ViT-L/14의 출력 차원(1024)을 LLaMA의 히든 차원(4096)으로 투영하는 단순한 행렬 곱셈이 전부이다. 이 극단적 단순함은:
- 구현이 쉬워 수많은 후속 연구를 촉진
- 핵심 병목이 아키텍처가 아니라 데이터임을 시사
- LLaVA-1.5에서 2-layer MLP로 교체만으로 전 벤치마크에서 큰 성능 향상을 달성하여, 프로젝션 설계의 중요성을 입증

### 2. GPT-4 기반 합성 데이터 생성

인간 주석 없이 GPT-4를 활용하여 고품질 멀티모달 인스트럭션 데이터를 자동 생성하는 방법론은 데이터 수집 비용을 획기적으로 줄였다. 이 접근은 ShareGPT4V, ALLaVA 등 후속 데이터셋에서 더욱 정교하게 발전하였다.

### 3. 오픈소스 생태계 형성

모델 가중치, 학습 코드, 데이터셋을 모두 공개하여 활발한 오픈소스 생태계를 형성했다. LLaVA-1.5, LLaVA-NeXT, LLaVA-OneVision 등으로 시리즈가 발전하고, 수백 개의 파생 연구가 탄생했다. 아래는 LLaVA의 멀티턴 대화 능력을 보여주는 예시이다. 이미지에 대해 연속적인 질문을 처리하며 맥락을 유지한다.

![LLaVA 멀티턴 대화 예시 - 냉장고 이미지를 보고 요리 추천 및 레시피를 제공하는 대화](figures/fig_7_1.png)
*Figure 3: LLaVA 멀티턴 대화 - 냉장고 이미지를 인식하고 요리 추천, 이어서 레시피를 제공하는 연속 대화 예시. 사용자의 의도를 정확히 파악하여 상세한 응답을 생성한다. (Source: arXiv 2304.08485)*

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

### LLaVA 시리즈의 진화

LLaVA의 단순한 아키텍처는 각 컴포넌트의 독립적 개선을 용이하게 만들었으며, 후속 버전들이 이를 체계적으로 발전시켰다.

**LLaVA-1.5 (2023.10)**: 가장 영향력 있는 업그레이드로, 세 가지 핵심 변경이 이루어졌다. (1) 선형 프로젝터를 2-layer MLP(GELU 활성화)로 교체하여 비전-언어 매핑의 표현력을 향상시켰다. (2) 입력 해상도를 224px에서 336px로 확대하여 세밀한 시각 정보 처리 능력을 개선했다. (3) ShareGPT의 텍스트 대화 데이터를 추가하여 언어 능력을 보강했다. 이 변경만으로 VQAv2에서 80.0%, GQA에서 63.3%를 달성하여 당시 오픈소스 VLM 중 최고 성능을 기록했다.

**LLaVA-NeXT (2024.01)**: 동적 해상도 처리(AnyRes) 기법을 도입하여 고해상도 이미지를 효과적으로 처리할 수 있게 되었다. 입력 이미지를 여러 타일로 분할하고 각각을 독립적으로 인코딩한 후 결합하는 방식으로, 해상도 제약을 크게 완화했다. 또한 Mistral-7B, Yi-34B 등 더 강력한 LLM 백본을 도입했다.

**LLaVA-OneVision (2024.08)**: 단일 이미지를 넘어 다중 이미지와 비디오 이해를 통합한 범용 시각 모델이다. 3단계 학습(단일 이미지 → 다중 이미지 → 비디오)을 통해 다양한 시각적 입력을 처리할 수 있다.

## 한계 및 과제

### 근본적 한계

1. **환각(Hallucination)**: 이미지에 없는 객체, 속성, 관계를 생성하는 문제가 심각하다. 이는 LLM의 언어적 사전지식이 시각적 증거보다 우선하여 발생하며, POPE 벤치마크에서 LLaVA-1.5도 약 86%의 정확도에 머물러 14%의 환각률을 보인다.
2. **공간 추론 취약성**: "왼쪽 객체와 오른쪽 객체 중 어느 것이 더 큰가?" 같은 공간적 관계 추론에 취약하다. CLIP 비전 인코더가 전역 이미지 특성에 특화되어 있어, 세밀한 공간 정보가 프로젝션 과정에서 손실된다.
3. **고해상도 처리 제약**: 초기 LLaVA는 224px(CLIP 기본 해상도)만 지원하여, 문서 OCR, 차트 이해 등 세밀한 시각 정보가 필요한 태스크에서 한계를 보인다. LLaVA-1.5에서 336px, LLaVA-NeXT에서 AnyRes로 점진적 개선이 이루어졌으나, 여전히 원본 이미지의 상당한 정보 손실이 존재한다.
4. **단일 이미지 제약**: LLaVA v1 기준으로 단일 이미지만 처리 가능하며, 다중 이미지 비교, 비디오 이해, 문서 다페이지 처리 등이 불가능하다. LLaVA-OneVision에서야 이 제약이 해소되었다.
5. **시각 토큰 수 고정**: CLIP ViT-L/14는 항상 576개(24x24)의 시각 토큰을 생성하며, 이미지 복잡도에 관계없이 동일한 토큰 수가 할당된다. 단순한 이미지에는 과도하고, 복잡한 이미지에는 부족한 비효율이 존재한다.

### 전망

다음은 LLaVA가 손으로 그린 스케치를 HTML/JS 코드로 변환하는 시각-코드 생성 능력을 보여주는 예시이다.

![LLaVA 이미지-코드 변환 - 손그림 스케치에서 인터랙티브 웹사이트 코드 생성](figures/fig_6.png)
*Figure 4: LLaVA 시각-코드 생성 - 사용자가 그린 웹사이트 스케치를 인식하여 HTML/JS 코드를 생성하고, 실제 동작하는 인터랙티브 웹페이지로 변환한다. (Source: arXiv 2304.08485)*

LLaVA는 "단순함이 최고의 복잡함"이라는 철학을 멀티모달 AI에서 실증한 기념비적 연구이다. "비전 인코더 + 프로젝터 + LLM" 패턴은 2024-2025년 거의 모든 오픈소스 VLM의 표준 구조가 되었으며, GPT-4 기반 합성 데이터 생성은 데이터 엔지니어링의 새 지평을 열었다. LLaVA가 보여준 "적은 비용, 큰 임팩트"의 철학은 학술 연구의 접근성을 크게 높여 멀티모달 AI 분야의 폭발적 성장을 견인하였다.

## 관련 문서

- [[llava-onevision|LLaVA-OneVision]] - 후속 모델
- [[llama|LLaMA: Open and Efficient Foundation Language Models]] - 영감
- [[vit|An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale]] - 영감
- [[cogvlm|CogVLM]] - 영감을 줌
- [[minicpm-v|MiniCPM-V]] - 영감을 줌
- [[molmo|Molmo]] - 영감을 줌
