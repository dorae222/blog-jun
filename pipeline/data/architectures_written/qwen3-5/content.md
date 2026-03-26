# Qwen3.5

**Alibaba** · **2026-02-16** · **Decoder-only** · **Sparse MoE** · **오픈소스**

## 개요

Qwen3.5는 2026년 2월 Alibaba Cloud가 공개한 차세대 대규모 언어 모델로, Qwen3의 순수 Transformer 구조에서 벗어나 Gated DeltaNet(선형 어텐션)과 표준 GQA를 3:1 비율로 교차 배치하는 하이브리드 어텐션 아키텍처를 최초로 도입했다. 플래그십 모델 Qwen3.5-397B-A17B는 총 397B 파라미터 중 토큰당 17B만 활성화하는 대규모 MoE 구조(512 전문가, 10 라우팅 + 1 공유 전문가)를 채택하여, Qwen3-Max 대비 32K 컨텍스트에서 8.6배, 256K에서 19배 빠른 디코딩 처리량을 달성했다. 네이티브 262K 컨텍스트 윈도우와 201개 언어 지원, 조기 융합(early fusion) 멀티모달 훈련을 통해 텍스트·이미지·비디오를 단일 모델에서 처리하며, 에이전틱 AI 태스크에 특화된 도구 사용(MCP) 및 적응적 추론 능력을 갖추었다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

Qwen3.5의 핵심 혁신은 Gated DeltaNet 하이브리드 어텐션이다. 60개 레이어가 15개 반복 블록(3×(DeltaNet→MoE) + 1×(GQA→MoE))으로 구성되어, 선형 어텐션이 시퀀스 길이에 대해 거의 선형 복잡도로 처리하고, 매 4번째 블록에서 풀 어텐션이 장거리 의존성을 포착한다. DeltaNet은 Mamba2의 게이트 감쇠(gated decay)에 델타 규칙(delta rule) 기반 은닉 상태 업데이트를 결합해, 기존 선형 어텐션의 표현력 한계를 극복했다. MoE 계층은 512개 전문가 중 10개를 라우팅하고 1개 공유 전문가가 항상 활성화되어 훈련 안정성을 확보한다. 어휘 크기를 150K→250K로 확장해 대부분 언어에서 인코딩 효율이 10~60% 향상되었고, QK-Norm을 도입해 대규모 훈련 시 안정적 그래디언트 흐름을 보장한다. Small(0.8B~9B) 밀집 모델과 Medium(27B~122B-A10B) MoE 모델 등 다양한 변형이 함께 제공된다.

## 모델 사양

| 항목 | 값 |
|------|---|
| 파라미터 | 397B (A17B) |
| 컨텍스트 길이 | 262144 |
| 어텐션 | Hybrid (Gated DeltaNet + GQA) |
| 정규화 | RMSNorm |
| 활성화 | SwiGLU |
| 위치 인코딩 | RoPE |
| 어휘 크기 | 250000 |
| 히든 차원 | 미공개 |
| 레이어 수 | 60 |
| 어텐션 헤드 | 미공개 |
| 전문가 수 | 512 (활성: 11) |

### 핵심 개념

- **Gated DeltaNet**
- **Hybrid Attention**
- **MoE**
- **Early Fusion Multimodal**
- **Agentic AI**
- **Multilingual**
- **FP8 Training**

## 학습

Qwen3.5는 수조 개의 멀티모달 토큰에 대한 조기 융합(early fusion) 사전학습을 수행하며, 비전과 언어 컴포넌트에 이질적 병렬화(heterogeneous parallelism)를 분리 적용해 텍스트 전용 대비 거의 100% 훈련 처리량을 유지한다. 네이티브 FP8 파이프라인이 활성화·MoE 라우팅·GEMM 연산에 저정밀도를 적용하되, 런타임 모니터링으로 민감한 레이어는 BF16을 유지해 약 50% 활성화 메모리 절감을 달성했다. 사후학습(post-training)에서는 백만 에이전트 환경의 비동기 RL 인프라를 구축하여, 점진적으로 복잡해지는 태스크 분포에서 장기 수평(long-horizon) 에이전틱 능력을 강화했다. Qwen3의 3단계 사전학습 파이프라인에서 확립된 스케일링 법칙 연구를 계승하면서, Dense/MoE 각각에 최적화된 학습률 스케줄러와 배치 크기를 체계적으로 조정했다.

### 관련 모델

- **qwen3** — 발전 기반

### 어텐션 메커니즘: GQA

GQA(Grouped Query Attention)는 Query 헤드를 여러 그룹으로 나누어 각 그룹이 하나의 KV 헤드를 공유하는 어텐션 변형이다:

$$\text{GQA}: Q \in \mathbb{R}^{n_h \times d_h}, \quad K, V \in \mathbb{R}^{n_g \times d_h}, \quad n_g \ll n_h$$

이를 통해 MHA 대비 KV 캐시 메모리를 $n_h / n_g$배 절감하면서도 MHA에 근접하는 성능을 유지한다. MQA(Multi-Query Attention)가 단일 KV 헤드로 인해 품질 저하가 발생할 수 있는 반면, GQA는 적절한 수의 KV 그룹을 사용하여 성능과 효율의 균형을 맞춘다.
### 실무 코드 예시

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("qwen3-5", torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("qwen3-5")

# Qwen3.5 추론 예시
messages = [{"role": "user", "content": "트랜스포머 아키텍처의 핵심 원리를 설명해줘"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=500, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

다음 그림은 Qwen3.5의 핵심인 Gated DeltaNet과 GQA의 3:1 하이브리드 어텐션 인터리빙 구조를 상세히 보여준다.

![Qwen3.5 하이브리드 어텐션 아키텍처 상세도](figures/detail.png)
*Figure 2: Qwen3.5 하이브리드 어텐션 상세 — Gated DeltaNet 선형 어텐션(좌)과 GQA 풀 어텐션(우)이 3:1 비율로 교차 배치되어, 선형 복잡도의 효율성과 장거리 의존성 포착을 동시에 달성한다. (Source: Alibaba Cloud)*

## 핵심 혁신

### 1. Gated DeltaNet

Gated DeltaNet은 선형 어텐션에 델타 규칙 기반 동적 메모리 관리를 결합한 메커니즘이다. Mamba2의 게이트 감쇠(gated decay)에 델타 규칙 기반 은닉 상태 업데이트를 결합하여, 기존 선형 어텐션의 표현력 한계를 극복하면서 시퀀스 길이에 대해 선형 복잡도를 유지한다.

### 2. Hybrid Attention

하이브리드 어텐션은 풀 어텐션(GQA)과 선형 어텐션(Gated DeltaNet)을 교차 배치하여 전역 의존성 포착과 선형 복잡도를 동시에 달성하는 설계이다. Qwen3.5에서 3:1(DeltaNet:GQA) 비율로 적용되어 256K 컨텍스트에서 19배 빠른 디코딩을 실현했다.

### 3. MoE

Mixture of Experts(MoE)는 입력 토큰에 따라 일부 전문가만 활성화하여, 전체 파라미터의 표현력을 유지하면서 추론 비용을 절감하는 아키텍처이다. 전문가 간 부하 균형과 라우팅 효율성이 핵심 과제이며, 보조 손실이나 동적 편향 조정으로 균형을 유지한다.

### 4. Early Fusion Multimodal

조기 융합(Early Fusion) 멀티모달은 사전학습 단계부터 텍스트, 이미지, 비디오 등 다양한 양식을 통합하여 학습하는 방식이다. 후기 융합 대비 양식 간 더 깊은 상호작용을 학습하며, 이질적 병렬화를 통해 텍스트 전용 대비 거의 100% 훈련 처리량을 유지할 수 있다.


## 벤치마크/성능

Qwen3.5은 Gated DeltaNet, Hybrid Attention, MoE 분야에서 동급 모델 대비 경쟁력 있는 성능을 보인다.


## 실무 활용

### 1. 파인튜닝 베이스 모델
Qwen3.5은 오픈소스로 공개되어 LoRA, QLoRA 등의 PEFT 기법을 활용한 도메인 특화 파인튜닝이 가능하다. 의료, 법률, 금융 등 특정 도메인의 데이터로 미세조정하면 전문적인 AI 어시스턴트를 구축할 수 있다.

### 2. 추론 배포
Qwen3.5은 다양한 추론 프레임워크(vLLM, TGI, ONNX Runtime 등)에서 지원되며, 양자화(GPTQ, AWQ, GGUF)를 통해 효율적인 서버 배포가 가능하다.

### 3. 연구 베이스라인
Qwen3.5은 Gated DeltaNet, Hybrid Attention 연구의 표준 베이스라인으로 활용된다.

## 한계 및 전망

### 한계

1. **배포 인프라**: 397B (A17B) 규모의 모델은 충분한 GPU 인프라가 필요하다.
2. **학습 데이터 편향**: 사전 학습 데이터의 특성에 따라 특정 도메인이나 언어에서 편향이 존재할 수 있다.
3. **환각(Hallucination)**: 모든 언어 모델과 마찬가지로 사실이 아닌 정보를 자신 있게 생성할 수 있으며, 사실 검증 메커니즘이 필요하다.

### 전망

Qwen3.5은 Gated DeltaNet, Hybrid Attention, MoE 분야에서의 강점을 바탕으로, 향후 더 발전된 후속 모델이나 특화된 변형 모델로 진화할 것으로 예상된다. 에이전틱 AI와 멀티모달 처리 능력의 강화가 주요 발전 방향이 될 것이다.
### 위치 인코딩: RoPE

RoPE(Rotary Position Embedding)는 위치 정보를 복소수 회전으로 인코딩하여 상대적 위치를 자연스럽게 포착한다:

$$f(x_m, m) = x_m e^{im\theta}, \quad \theta_j = 10000^{-2j/d}$$

이 방식은 절대 위치 임베딩의 한계를 극복하며, 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽(extrapolation)이 가능하다는 핵심 장점이 있다. NTK-aware Scaling이나 YaRN 등의 확장 기법을 적용하면 학습 컨텍스트의 수십 배까지 외삽할 수 있다.

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Qwen3.5은 397B (A17B) 규모의 파라미터를 가지며, 262144 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Qwen3.5은 397B (A17B) 규모의 파라미터를 가지며, 262144 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Qwen3.5은 397B (A17B) 규모의 파라미터를 가지며, 262144 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Qwen3.5은 397B (A17B) 규모의 파라미터를 가지며, 262144 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.

## 참고 자료

- [코드](https://github.com/QwenLM/Qwen3.5)

## 관련 문서

- [[qwen3|Qwen3]] — 발전 기반
