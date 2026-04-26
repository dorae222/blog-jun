<!-- infographic-hero -->
![CogVLM 핵심 요약](figures/infographic.svg)

*Figure: CogVLM 한 장 요약 인포그래픽*

# CogVLM: 시각 전문가 기반 깊은 시각-언어 융합

## 개요

CogVLM은 2023년 11월 Tsinghua 대학과 Zhipu AI가 공동 발표한 시각-언어 모델이다. 기존 멀티모달 모델들이 비전 인코더의 출력을 단순한 프로젝션이나 어댑터로 LLM에 연결하는 **얕은 융합(shallow fusion)** 방식을 사용한 것과 달리, CogVLM은 LLM의 **각 트랜스포머 레이어에 시각 전문가(Visual Expert) 모듈을 추가**하여 시각 토큰과 텍스트 토큰이 레이어마다 서로 다른 최적화된 변환을 받도록 하는 **깊은 융합(deep fusion)** 아키텍처를 제안하였다.

이 접근을 통해 시각 이해 능력이 크게 향상되어 NoCaps, Flickr30K, VQAv2, OKVQA, TextVQA, GQA 등 17개 벤치마크 중 10개에서 SOTA를 달성하였으며, 기존 LLM의 텍스트 능력을 전혀 손상시키지 않는 것이 특징이다.

논문: [CogVLM: Visual Expert for Pretrained Language Models](https://arxiv.org/abs/2311.03079)

다음 레이더 차트는 CogVLM이 다양한 멀티모달 벤치마크에서 기존 모델들을 전반적으로 능가하는 성능을 보여준다.

![CogVLM 멀티모달 벤치마크 성능 비교 - 17개 태스크에서의 종합 비교](figures/fig_1.png)
*Figure 1: CogVLM 멀티모달 성능 비교 - 다양한 벤치마크에서 CogVLM(보라색)이 Qwen-VL, LLaVA-1.5, InstructBLIP 등 기존 모델을 전반적으로 능가한다. (Source: Wang et al., 2023)*

## 아키텍처 상세

### 전체 구조

CogVLM은 세 가지 핵심 컴포넌트로 구성된다:

1. **비전 인코더**: EVA2-CLIP-E (4.4B params) - 이미지에서 시각 특징 추출
2. **MLP 어댑터**: 비전 인코더 출력을 LLM 히든 차원에 매핑
3. **LLM + Visual Expert**: Vicuna-7B 기반, 각 레이어에 시각 전문가 모듈 추가

### 시각 전문가(Visual Expert) 모듈

아래 그림은 CogVLM의 전체 아키텍처를 보여준다. (a)는 입력 처리 과정으로 ViT 인코더와 MLP 어댑터를 통한 시각 특징 매핑을, (b)는 Visual Expert 모듈의 내부 구조로 시각/텍스트 토큰에 별도의 QKV 행렬과 FFN을 적용하는 방식을 나타낸다.

![CogVLM 아키텍처 - 입력 처리 과정과 Visual Expert 모듈의 내부 구조](figures/fig_5.png)
*Figure 4: CogVLM 아키텍처 - (a) 이미지를 ViT로 인코딩한 뒤 MLP 어댑터로 텍스트 공간에 매핑하는 입력 처리, (b) 시각/텍스트 토큰에 각각 다른 QKV 행렬과 FFN을 적용하는 Visual Expert 구조. 보라색 부분만 학습 대상이다. (Source: Wang et al., 2023)*

CogVLM의 핵심 혁신이다. 각 트랜스포머 레이어에서 시각 토큰과 텍스트 토큰은 **서로 다른 선형 변환**을 받는다:

**어텐션 레이어에서의 처리:**
$$Q_{\text{text}} = x_{\text{text}} W_q^{\text{text}}, \quad Q_{\text{vis}} = x_{\text{vis}} W_q^{\text{vis}}$$
$$K_{\text{text}} = x_{\text{text}} W_k^{\text{text}}, \quad K_{\text{vis}} = x_{\text{vis}} W_k^{\text{vis}}$$
$$V_{\text{text}} = x_{\text{text}} W_v^{\text{text}}, \quad V_{\text{vis}} = x_{\text{vis}} W_v^{\text{vis}}$$

**FFN 레이어에서의 처리:**
$$\text{FFN}_{\text{text}}(x) = \text{SiLU}(x W_1^{\text{text}}) \cdot (x W_3^{\text{text}}) \cdot W_2^{\text{text}}$$
$$\text{FFN}_{\text{vis}}(x) = \text{SiLU}(x W_1^{\text{vis}}) \cdot (x W_3^{\text{vis}}) \cdot W_2^{\text{vis}}$$

텍스트 토큰은 원래 LLM의 가중치($W^{\text{text}}$)로, 시각 토큰은 새로 추가된 시각 전문가 가중치($W^{\text{vis}}$)로 처리된다. 중요한 점은 어텐션 계산 시 시각 토큰의 Q/K/V와 텍스트 토큰의 Q/K/V가 concat된 뒤 동일한 어텐션 연산에 참여한다는 것이다. 이로써 두 모달리티가 매 레이어에서 상호작용하면서도 각자의 표현 공간을 유지한다.

### 깊은 융합의 장점

| 융합 방식 | 대표 모델 | 특징 |
|-----------|----------|------|
| 프로젝션만 | LLaVA | 입력 단계 1회 변환 |
| Q-Former | BLIP-2 | 32개 쿼리로 정보 병목 |
| Cross-Attention | Flamingo | LLM 레이어 사이에 삽입 |
| **Visual Expert** | **CogVLM** | **모든 레이어에서 독립 변환** |

Visual Expert 방식은 모든 레이어에서 시각 토큰의 표현이 독립적으로 최적화되므로, 가장 깊은 수준의 시각-언어 정렬이 가능하다.

| 구성 요소 | 사양 |
|-----------|------|
| 비전 인코더 | EVA2-CLIP-E (4.4B, ViT-E/14) |
| LLM 기반 | Vicuna-7B (frozen text weights) |
| 시각 전문가 | 각 레이어 QKV + FFN 복제 (~6B 추가) |
| 총 파라미터 | 약 17B |
| 이미지 해상도 | 490×490 |
| 시각 토큰 수 | 1225 (35×35 패치) |

## 핵심 혁신

### 1. 텍스트 능력 보존

다음 그래프는 LLM의 텍스트 가중치를 직접 학습할 때 MMLU 점수가 급격히 하락하는 현상을 보여주며, Visual Expert를 통한 텍스트 능력 보존의 필요성을 입증한다.

![MMLU 점수 하락 - LLM 직접 학습 시 텍스트 능력 급격 저하](figures/fig_4.png)
*Figure 3: MMLU 점수와 학습 손실 - LLM의 언어 파라미터를 직접 학습하면 MMLU 점수가 47에서 24.9로 급락하여, 시각 전문가를 통한 분리 학습의 필요성을 입증한다. (Source: Wang et al., 2023)*

기존 LLM의 텍스트 파라미터를 완전히 고정(frozen)하고, 시각 전문가 파라미터만 학습하므로 원래 LLM의 언어 능력이 전혀 손상되지 않는다. 이는 LLaVA처럼 전체 LLM을 파인튜닝하여 텍스트 능력이 저하될 수 있는 문제를 원천적으로 방지한다.

### 2. 표현 공간 분리

시각 토큰과 텍스트 토큰이 같은 어텐션에 참여하되 서로 다른 선형 변환을 거치므로, 각 모달리티의 최적 표현 공간이 독립적으로 학습된다. 이는 단일 프로젝터로 비전 특징을 텍스트 공간에 억지로 매핑하는 것보다 더 풍부한 표현을 가능하게 한다.

### 3. Grounding 능력

CogVLM은 바운딩 박스 좌표를 텍스트 토큰으로 출력하는 CogAgent를 통해 이미지 내 객체를 정확히 위치 지정하는 grounding 능력도 갖추었다.

## 벤치마크/성능

| 벤치마크 | CogVLM-17B | LLaVA-1.5-13B | BLIP-2 | Qwen-VL |
|----------|-----------|--------------|--------|---------|
| NoCaps (CIDEr) | **128.3** | - | 107.5 | 121.4 |
| VQAv2 | **83.4%** | 80.0% | 65.0% | 79.5% |
| TextVQA | **70.4%** | 61.3% | 42.5% | 63.8% |
| GQA | **64.7%** | 63.3% | 44.7% | 59.3% |

## 관련 모델 비교

| 특성 | CogVLM | LLaVA | BLIP-2 | InternVL |
|------|--------|-------|--------|----------|
| 시각-언어 융합 깊이 | 모든 레이어 | 입력층만 | 32 쿼리 | 픽셀 셔플 |
| LLM 텍스트 능력 보존 | 완벽 | 일부 저하 | 완벽 | 완벽 |
| 추가 파라미터 | ~6B | 0 (전체 FT) | 188M | 적음 |
| 이미지 해상도 | 490px | 336px | 224px | 448px |

## 학습 상세

2단계 학습을 수행한다:

**Stage 1: 비전-언어 사전학습**
- 데이터: 1.5B 이미지-텍스트 쌍 (웹 크롤, 캡셔닝 데이터)
- 학습 대상: 시각 전문가 파라미터 + MLP 어댑터 (LLM 텍스트 가중치 고정)
- 태스크: 이미지 캡셔닝

**Stage 2: 멀티태스크 인스트럭션 튜닝**
- 데이터: VQA, 캡셔닝, grounding 등 멀티태스크 SFT 데이터
- 학습 대상: 동일 (시각 전문가 + 어댑터)

하드웨어: 8× A100 80GB GPU

다음은 CogVLM의 다양한 생성 결과로, OCR-Free 추론, 상세 묘사, 차트 이해, 밈 분석, 시각적 추론, grounding 등 폭넓은 멀티모달 능력을 보여준다.

![CogVLM 생성 샘플 - 다양한 멀티모달 태스크에서의 생성 결과](figures/fig_2.png)
*Figure 2: CogVLM 생성 샘플 - OCR-Free 추론, 상세 묘사, 차트 이해, 시각적 추론, grounding, 세계 지식 활용 등 다양한 태스크에서의 생성 결과. (Source: Wang et al., 2023)*

## 실무 활용

```python
from transformers import AutoModelForCausalLM, LlamaTokenizer
import torch
from PIL import Image

tokenizer = LlamaTokenizer.from_pretrained("lmsys/vicuna-7b-v1.5")
model = AutoModelForCausalLM.from_pretrained(
    "THUDM/cogvlm-chat-hf",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
).to("cuda")

image = Image.open("test.jpg").convert("RGB")
query = "이 이미지에서 무엇이 보이나요?"
inputs = model.build_conversation_input_ids(
    tokenizer, query=query, images=[image]
)
outputs = model.generate(**inputs, max_new_tokens=512)
print(tokenizer.decode(outputs[0]))
```

아래 그래프는 TDIUC 벤치마크에서 세부 질문 유형별 성능을 비교한 것으로, CogVLM이 Sentiment Understanding, Utility & Affordance, Object Recognition 등 대부분의 세부 카테고리에서 우수한 성능을 보인다.

![TDIUC 벤치마크 세부 성능 비교 - 세부 질문 유형별 정확도](figures/fig_6.png)
*Figure 5: TDIUC 벤치마크 세부 성능 - 감정 이해, 객체 인식, 속성 인식, 공간 관계 등 12개 세부 카테고리에서 CogVLM(보라색)이 기존 모델들을 능가한다. (Source: Wang et al., 2023)*

## 한계 및 전망

### 한계

1. **대규모 추가 파라미터**: 시각 전문가 추가로 약 6B 파라미터가 증가하여 추론 비용이 높다
2. **단일 이미지 한정**: 다중 이미지나 비디오 처리를 위한 설계가 부재하다
3. **고정된 LLM 한계**: 더 강력한 LLM으로 교체 시 시각 전문가를 처음부터 재학습해야 한다

### 전망

CogVLM의 Visual Expert 개념은 이후 CogVLM2, CogAgent 등으로 발전하였으며, "시각 토큰과 텍스트 토큰을 서로 다른 변환으로 처리"하는 아이디어는 MoE(Mixture of Experts) 기반 VLM과 맥을 같이한다. 향후 모달리티별로 특화된 전문가를 동적으로 활성화하는 방향으로 발전할 것으로 전망된다.

## 관련 문서

- [[llava|Visual Instruction Tuning]] - 영감
