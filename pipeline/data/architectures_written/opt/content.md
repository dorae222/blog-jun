<!-- infographic-hero -->
![OPT 핵심 요약](figures/infographic.svg)

*Figure: OPT 한 장 요약 인포그래픽*

# OPT: GPT-3의 오픈소스 재현과 LLM 연구 민주화

## 개요

OPT(Open Pre-trained Transformer)는 2022년 5월 Meta AI가 공개한 175B 파라미터 규모의 오픈소스 대형 언어 모델이다. OPT의 핵심 목표는 명확했다: **GPT-3급 모델을 연구 커뮤니티에 완전히 공개하여 LLM 연구의 문턱을 낮추자.**

OPT 이전에 GPT-3(175B)는 API를 통해서만 접근 가능했고, 내부 구조와 학습 과정은 베일에 싸여 있었다. Meta는 OPT를 통해 **가중치, 학습 코드, 심지어 학습 로그까지** 모두 공개하여, 대형 모델 학습에서 발생하는 실질적인 문제(불안정성, 발산 등)와 해결 과정을 커뮤니티와 공유했다.

- **논문**: [OPT: Open Pre-trained Transformer Language Models](https://arxiv.org/abs/2205.01068)
- **코드**: [metaseq (GitHub)](https://github.com/facebookresearch/metaseq)
- **라이선스**: Non-commercial Research

## 아키텍처 상세

다음 다이어그램은 OPT-175B의 전체 아키텍처와 주요 구성 요소를 보여준다.

![OPT-175B 전체 아키텍처 다이어그램 - Pre-LayerNorm 적용 Decoder-Only Transformer 구조](figures/architecture.png)
*Figure 1: OPT-175B 아키텍처 - GPT-3와 동일한 Decoder-Only 구조에 Pre-LayerNorm을 적용. 96개 레이어, 96개 어텐션 헤드, Hidden Dim 12,288의 대규모 모델이다. (Source: OPT 논문)*

OPT는 GPT-3의 아키텍처를 **충실히 재현**하되 Pre-LayerNorm을 적용한 구조이다:

| 구성 요소 | OPT-175B |
|-----------|----------|
| 파라미터 수 | 175B |
| 레이어 수 | 96 |
| Hidden Dim | 12,288 |
| Attention Heads | 96 |
| Vocab Size | 50,272 |
| Context Length | 2,048 |
| 정규화 | **Pre-LayerNorm** |
| 활성화 함수 | ReLU |
| 위치 인코딩 | Learned Absolute |

### 모델 크기 시리즈

| 모델 | 파라미터 | 레이어 | Hidden Dim | Heads |
|------|---------|--------|-----------|-------|
| OPT-125M | 125M | 12 | 768 | 12 |
| OPT-350M | 350M | 24 | 1,024 | 16 |
| OPT-1.3B | 1.3B | 24 | 2,048 | 32 |
| OPT-2.7B | 2.7B | 32 | 2,560 | 32 |
| OPT-6.7B | 6.7B | 32 | 4,096 | 32 |
| OPT-13B | 13B | 40 | 5,120 | 40 |
| OPT-30B | 30B | 48 | 7,168 | 56 |
| OPT-66B | 66B | 64 | 9,216 | 72 |
| OPT-175B | 175B | 96 | 12,288 | 96 |

총 9개의 크기로 제공되어 다양한 연구 환경에서 활용 가능하다.

### Pre-LayerNorm

GPT-3의 Post-LayerNorm과 달리 OPT는 **Pre-LayerNorm**을 채택했다. 어텐션과 FFN 전에 LayerNorm을 적용하여 깊은 네트워크에서의 학습 안정성을 개선한다:

$$x_{l+1} = x_l + \text{Attention}(\text{LayerNorm}(x_l))$$
$$x_{l+2} = x_{l+1} + \text{FFN}(\text{LayerNorm}(x_{l+1}))$$

## 핵심 혁신: 투명성과 재현 가능성

### 학습 로그북

OPT의 가장 독특한 기여는 **학습 로그북(Logbook)**의 공개이다. 175B 모델을 학습하면서 발생한 모든 문제와 해결 과정을 상세히 기록했다:

1. **학습 불안정성**: 특정 스텝에서 loss가 갑자기 발산하는 현상 발생
2. **학습률 재설정**: 불안정 구간에서 learning rate를 이전 안정 구간으로 되돌림
3. **그래디언트 클리핑**: 기울기 폭발을 방지하기 위한 클리핑 값 조정
4. **체크포인트 복원**: 발산 시 이전 체크포인트에서 재시작

이러한 실질적인 노하우는 이전에는 대기업 내부에서만 공유되던 것으로, 커뮤니티에 큰 가치를 제공했다.

아래 그래프는 OPT-175B 학습 중 적용된 경험적 학습률 스케줄과 그에 따른 검증 퍼플렉서티 변화를 보여준다.

![OPT-175B의 경험적 학습률 스케줄 - 불안정 구간에서 학습률을 수동으로 낮춘 기록](figures/fig_1.png)
*Figure 2: OPT-175B 학습률 스케줄 - 불안정성이 발생할 때마다 학습률을 수동으로 낮추는 경험적 접근을 적용했다. 약 140K 이터레이션에 걸친 학습 과정이 기록되어 있다. (Source: OPT 논문)*

![OPT-175B 검증 퍼플렉서티 변화 - 학습률 조정의 효과가 반영된 안정적인 수렴 곡선](figures/fig_2.png)
*Figure 3: 검증 퍼플렉서티 - 학습률 조정에 따른 일시적 변동이 관찰되지만, 전반적으로 안정적인 하강 곡선을 보인다. (Source: OPT 논문)*

```python
from transformers import AutoTokenizer, OPTForCausalLM
import torch

# OPT 모델 로드
tokenizer = AutoTokenizer.from_pretrained('facebook/opt-1.3b')
model = OPTForCausalLM.from_pretrained('facebook/opt-1.3b')

# 텍스트 생성
prompt = "The key innovation of OPT is"
inputs = tokenizer(prompt, return_tensors='pt')

with torch.no_grad():
    outputs = model.generate(
        inputs['input_ids'],
        max_length=100,
        do_sample=True,
        temperature=0.7,
        top_p=0.9
    )

print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 벤치마크/성능

OPT-175B는 GPT-3와 유사한 수준의 성능을 보여준다:

| 벤치마크 | OPT-175B | GPT-3 175B | 비교 |
|----------|----------|-----------|------|
| 전체 제로샷 평균 | **GPT-3 수준** | baseline | 10/16 태스크 일치 |
| HellaSwag | ~79% | ~79% | 동등 |
| PIQA | ~81% | ~81% | 동등 |
| StoryCloze | ~84% | ~84% | 동등 |
| 탄소 배출 | **1/7** | baseline | 7배 효율적 |

다음 그래프는 모델 크기에 따른 OPT와 GPT-3의 제로샷 성능 비교를 보여준다. 두 모델이 스케일링에 따라 매우 유사한 성능 궤적을 그리는 것을 확인할 수 있다.

![OPT와 GPT-3의 제로샷 NLP 평가 평균 - 모델 크기별 성능 비교](figures/fig_3.png)
*Figure 4: 14개 NLP 태스크 제로샷 평균 정확도 - OPT(실선)와 GPT-3(점선)가 125M~175B 범위에서 거의 동일한 스케일링 패턴을 보인다. (Source: OPT 논문)*

![OPT와 GPT-3의 멀티샷 NLP 평가 - 0/1/32-shot 설정별 성능 비교](figures/fig_4.png)
*Figure 5: 멀티샷 NLP 평가 - 0-shot(파란색), 1-shot(주황색), 32-shot(녹색) 설정에서 OPT(원형)와 GPT-3(X) 비교. Few-shot에서는 GPT-3가 약간 우위를 보이는 태스크도 존재한다. (Source: OPT 논문)*

### 핵심 결과
- 16개 제로샷 태스크 중 **10개에서 GPT-3와 동등**
- 나머지 6개에서는 성능 편차 존재
- **GPT-3 대비 1/7의 탄소 배출**로 유사 성능 달성
- 125M부터 175B까지 일관된 스케일링 효과 확인

## 관련 모델 비교

| 특성 | GPT-3 | OPT | BLOOM | LLaMA |
|------|-------|-----|-------|-------|
| 파라미터 | 175B | 175B | 176B | 65B |
| 오픈소스 | X | **O (가중치+코드+로그)** | O | O |
| 학습 로그 공개 | X | **O** | 부분 | X |
| 탄소 효율 | 1x | **7x** | - | - |
| 라이선스 | 비공개 | 비상업 연구 | RAIL | 연구용 |
| 학습 데이터 | 비공개 | **The Pile + Reddit** | ROOTS | 공개 |
| 위치 인코딩 | Learned | Learned | ALiBi | RoPE |

## 학습 상세

### 데이터셋
- **The Pile** (주요 데이터)
- **Reddit 공개 데이터**
- 다양한 웹 코퍼스
- 총 **~180B 토큰**

### 학습 인프라
- **992개 A100 80GB GPU**
- 학습 기간: 약 **2개월**
- **Metaseq** 프레임워크 (Meta 자체 분산 학습)
- Fully Sharded Data Parallel (FSDP) + Megatron-LM Tensor Parallelism
- GPU 활용률: 최대 **147 TFLOP/s per GPU**

## 실무 활용

### 1. LLM 연구 베이스라인
9가지 크기의 모델이 제공되어 스케일링 법칙 연구에 이상적인 베이스라인이다.

### 2. 학습 과정 연구
공개된 학습 로그를 통해 대형 모델 학습의 불안정성과 해결 방법을 연구할 수 있다.

### 3. 모델 압축 연구
다양한 크기의 체크포인트가 제공되어 지식 증류(knowledge distillation) 연구에 활용 가능하다.

### 4. 편향/안전성 연구
가중치가 공개되어 모델의 편향, 독성, 공정성에 대한 심층 분석이 가능하다.

## 한계 및 전망

### 한계
1. **비상업 라이선스**: 연구 목적으로만 사용 가능하여 상업적 활용이 제한된다
2. **성능 편차**: 일부 태스크에서 GPT-3에 미달하는 성능을 보인다
3. **단일 언어**: 영어 중심으로 다국어 지원이 부족하다
4. **아키텍처 보수성**: RoPE, SwiGLU 등 최신 기법을 채택하지 않았다

### 전망
OPT는 **오픈소스 LLM 시대의 문을 연 선구적 모델**이다. GPT-3 수준의 모델을 완전히 공개함으로써, 이후 LLaMA, BLOOM, Falcon 등 더 강력한 오픈소스 모델들이 등장하는 생태계의 토대를 마련했다. 특히 학습 로그북이라는 실용적 투명성의 전통은 이후 모델들의 기술 보고서 작성 관행에 영향을 미쳤다.

---

**참고 문헌**
- Zhang, S., et al. (2022). "OPT: Open Pre-trained Transformer Language Models." arXiv:2205.01068
- Brown, T. B., et al. (2020). "Language Models are Few-Shot Learners." (GPT-3)
- Gao, L., et al. (2020). "The Pile: An 800GB Dataset of Diverse Text for Language Modeling."

## 관련 문서

- [[gpt-3|Language Models are Few-Shot Learners (GPT-3)]] - 영감
