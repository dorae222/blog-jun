## 개요

Llama 2는 Meta AI가 2023년 7월 발표한 오픈 기반 언어 모델 시리즈다. Llama 1의 후속작으로, 7B, 13B, 34B, 70B 네 가지 크기가 있으며, 각각 사전학습 버전(Llama 2)과 채팅에 최적화된 파인튜닝 버전(Llama 2-Chat)이 공개되었다. 가장 중요한 변화는 **상업적 이용을 허용하는 라이선스**로 배포되어 기업과 연구자 모두가 자유롭게 활용할 수 있게 되었다는 점이다.

2026년 3월 기준 Google Scholar 인용 수가 약 7,700회 이상을 기록하며, 2023년 AI 분야에서 가장 영향력 있는 논문 중 하나로 평가된다. Llama 2는 유용성(helpfulness)과 안전성(safety)을 동시에 추구하는 정렬 접근법을 공개적으로 상세히 설명하여, RLHF 기반 안전한 챗 모델 개발의 **방법론적 교과서** 역할을 하고 있다.

## 배경 및 문제

### Llama 1의 한계

Llama 1은 오픈소스 LLM 생태계를 촉발시킨 획기적인 모델이었지만, 몇 가지 중요한 한계가 있었다:

- **연구 전용 라이선스**: 상업적 사용이 불가하여 기업의 실질적 활용에 제약
- **명령 따르기(instruction following) 훈련 미적용**: SFT나 RLHF 없이 사전학습만 진행하여 대화 능력이 제한적
- **안전성 정렬 부재**: 유해 콘텐츠 생성 가능성에 대한 체계적 대응 없음
- **컨텍스트 길이 2048 토큰**: 긴 문서 처리나 복잡한 대화에 한계

### 오픈소스 챗 모델의 필요성

ChatGPT, Claude 등 상용 챗 모델들은 가중치가 비공개다. 연구자들이 안전성, 정렬(alignment), 편향(bias)을 직접 분석하거나 개선하려면 공개된 고품질 챗 모델이 필요하다. 당시 오픈소스 진영에서는 Alpaca, Vicuna 등 Llama 1 기반 파생 모델들이 있었지만, 체계적인 RLHF 정렬 없이 SFT만 적용된 수준이었다.

### 안전성-유용성 트레이드오프

챗 모델 정렬에서 가장 근본적인 문제는 **안전성과 유용성 사이의 상충관계**다. 모델을 지나치게 안전하게 만들면 유용한 응답도 거절하게 되고(과도한 거절, over-refusal), 유용성만 추구하면 위험한 콘텐츠를 생성할 수 있다. Llama 2는 이 문제를 두 개의 분리된 보상 모델로 해결하는 혁신적인 접근법을 제시했다.

## 핵심 아이디어

Llama 2 논문의 핵심 기여는 크게 두 축으로 나뉜다. 첫째는 **오픈 기반 모델(Open Foundation Model)**로서의 사전학습 개선이고, 둘째는 **파인튜닝된 챗 모델(Fine-Tuned Chat Model)**로서의 RLHF 기반 정렬이다.

### 사전학습 개선

Llama 1 대비 세 가지 핵심 개선이 이루어졌다:

- **2조(2T) 토큰**으로 학습량 40% 증가 (Llama 1: 1.4T)
- 컨텍스트 길이 **4096 토큰**으로 2배 확장
- 더 많은 코드와 사실적 텍스트(factual text) 비율 증가

학습 토큰 수 증가의 효과는 스케일링 법칙으로 설명할 수 있다:

$$\mathcal{L}(N, D) \approx \frac{A}{N^\alpha} + \frac{B}{D^\beta} + \mathcal{L}_\infty$$

여기서 $N$은 파라미터 수, $D$는 토큰 수다. $D$를 1.4T에서 2T로 증가시키면 $\frac{B}{D^\beta}$ 항이 줄어들어 전체 손실이 감소한다.

사전학습 데이터는 공개적으로 이용 가능한 온라인 소스에서 수집되었다. Meta는 개인 정보를 포함할 가능성이 있는 사이트에서의 데이터를 최소화하고, 사실적 정보의 비율을 높이기 위해 위키피디아, 학술 논문, 코드 저장소 등 신뢰할 수 있는 소스의 비율을 조절했다. 토크나이저는 Llama 1과 동일한 BPE(Byte Pair Encoding) 기반으로, 어휘 크기는 32,000 토큰이다.

### Grouped Query Attention (GQA)

34B와 70B 모델에 **GQA(Grouped Query Attention)**를 적용한 것이 아키텍처 측면에서 가장 중요한 변화다. GQA는 Ainslie et al.(2023)이 제안한 방법으로, Multi-Head Attention(MHA)과 Multi-Query Attention(MQA)의 중간 형태다.

**MHA vs GQA vs MQA 비교:**

| 방식 | Q 헤드 | KV 헤드 | KV 캐시 크기 | 성능 |
|------|--------|---------|------------|------|
| MHA | $H$ | $H$ | $H \times d_k$ | 최고 |
| GQA | $H$ | $G$ ($1 < G < H$) | $G \times d_k$ | MHA에 근접 |
| MQA | $H$ | $1$ | $1 \times d_k$ | 약간 하락 |

GQA에서 여러 쿼리 헤드가 하나의 키-값 헤드를 공유한다:

$$\text{Attention}(Q_i, K_{g(i)}, V_{g(i)}) = \text{softmax}\left(\frac{Q_i K_{g(i)}^\top}{\sqrt{d_k}}\right) V_{g(i)}$$

여기서 $g(i) = \lfloor i \cdot G / H \rfloor$는 쿼리 헤드 $i$가 속하는 KV 그룹 인덱스다. Llama 2-70B에서는 $H=64$개의 쿼리 헤드가 $G=8$개의 KV 헤드를 공유하므로, KV 캐시 크기가 MHA 대비 **8배 감소**한다.

이 절감은 대규모 배치 추론 시 특히 중요하다:

$$\text{KV 캐시 메모리} = 2 \times L \times T \times G \times d_k \times \text{sizeof(dtype)}$$

70B 모델에서 $L=80, T=4096, G=8, d_k=128$이면, MHA 대비 약 8배 적은 메모리로 KV 캐시를 유지할 수 있다.

Meta는 기존 MHA 체크포인트에서 GQA로의 **업트레이닝(uptraining)** 전략을 사용했다. 기존 MHA의 여러 KV 헤드를 평균 풀링(mean pooling)하여 GQA의 KV 헤드로 초기화한 뒤, 원래 사전학습 토큰의 일부를 추가 학습한다.

### 두 단계 RLHF 정렬

Llama 2-Chat의 정렬 과정은 세 단계로 구성된다:

#### 1단계: 지도 파인튜닝 (SFT)

고품질 대화 데이터로 기본 응답 능력을 학습한다. Meta는 데이터 **양보다 질**을 우선시했다. 흥미로운 발견은 소수의 고품질 데이터(수만 개)가 수백만 개의 저품질 데이터보다 더 효과적이라는 것이다:

> "We found that SFT annotations in the order of tens of thousands was enough to achieve a high quality result."

이는 이후 LIMA 논문("Less Is More for Alignment")에서도 확인된 중요한 통찰이다.

#### 2단계: 두 개의 보상 모델

Llama 2-Chat의 핵심 혁신은 **유용성(helpfulness) 보상 모델**과 **안전성(safety) 보상 모델**을 별도로 훈련한다는 점이다. 두 목표가 종종 상충하기 때문에 이를 분리해 관리한다:

$$r_{\text{final}} = r_{\text{helpfulness}} + \lambda \cdot \max(0, r_{\text{safety}} - \tau)$$

여기서 $\lambda$는 안전성 가중치, $\tau$는 안전성 임계값이다. 안전성 점수가 임계값 이상이면 유용성에 집중하고, 미달이면 안전성을 우선시하는 동적 균형 전략이다.

보상 모델 학습에는 약 **100만 개**의 인간 어노테이션이 수집되었으며, 각 비교 쌍에는 선호도(chosen/rejected)와 안전성 라벨(안전/경계선/위험)이 포함된다. 어노테이션 데이터는 주차별로 수집되었으며, 각 배치(batch)에서 보상 모델의 정확도가 점진적으로 향상되었다. Meta는 보상 모델의 크기가 정렬 품질에 직접적으로 영향을 미친다는 것을 발견하고, 가장 큰 Llama 2-70B를 보상 모델의 백본으로 사용했다.

다음 그림은 유용성 보상 모델의 학습 과정에서 데이터 배치가 누적됨에 따라 정확도가 점진적으로 향상되는 추이를 보여준다. 70B 모델이 가장 높은 정확도를 달성하며, 보상 모델 크기의 중요성을 실증적으로 확인할 수 있다.

![보상 모델 학습 데이터 누적에 따른 정확도 향상 추이](figures/fig_7.png)
*보상 모델의 데이터 배치별 정확도 변화. 70B 백본(빨간선)이 7B(파란선), 13B(초록선)보다 일관되게 높은 정확도를 보이며, GPT-4 수준(점선)에 근접한다.*

보상 모델의 손실 함수:

$$\mathcal{L}_{\text{reward}} = -\log\sigma(r_\theta(x, y_c) - r_\theta(x, y_r) - m(r))$$

여기서 $y_c$는 선호 응답, $y_r$은 비선호 응답, $m(r)$은 선호도 등급에 따른 마진이다. 마진 $m(r)$은 "significantly better", "slightly better" 등 어노테이터가 제공한 선호 강도에 따라 다르게 설정되어, 명확한 선호 차이가 있는 쌍에서 더 큰 보상 격차를 학습하도록 유도한다.

#### 3단계: PPO with Rejection Sampling

PPO(Proximal Policy Optimization)와 함께 **거절 샘플링(Rejection Sampling Fine-tuning, RSFT)**을 활용한다. RSFT는 다음과 같이 작동한다:

1. 현재 정책에서 프롬프트당 $K$개의 응답 생성 (보통 $K=10 \sim 25$)
2. 보상 모델로 각 응답 점수 매기기
3. 최고 점수 응답을 SFT 데이터로 추가
4. 이 데이터로 모델 재학습

이 방식은 PPO의 불안정성 문제를 완화하면서도 효과적인 정렬을 달성한다. Meta의 실험에 따르면 RSFT만으로도 상당한 성능 향상이 가능하며, PPO와 결합하면 최상의 결과를 얻는다. 특히 RSFT에서 샘플 수 $K$를 늘릴수록 최고 보상 점수의 기댓값이 증가하는데, 이는 다음과 같은 order statistics 관계로 설명된다:

$$\mathbb{E}[\max(r_1, r_2, \ldots, r_K)] \propto \sqrt{\log K}$$

아래 그림은 이 관계를 실증적으로 보여준다. 샘플 수 $N$이 증가할수록 최고 보상 점수(파란선)는 대수적으로 상승하지만, 중앙값(주황선)은 거의 변하지 않는다. 이는 RSFT가 분포의 꼬리(tail)에서 고품질 응답을 선별하는 메커니즘임을 명확히 보여준다.

![Rejection Sampling 샘플 수에 따른 최고 보상 점수 변화](figures/fig_8.png)
*Rejection Sampling에서 샘플 수 N과 보상 점수의 관계. 샘플 수가 증가하면 최고 보상 점수(파란선)는 꾸준히 상승하지만 중앙값(주황선)은 정체되어, best-of-N 선별 전략의 효과를 보여준다.*

### Ghost Attention (GAtt)

멀티턴 대화에서 초반에 설정한 지시사항(시스템 프롬프트)을 모델이 오랜 대화 후에도 기억하도록 하는 기법이다. 일반적으로 챗 모델은 대화가 길어지면 초기 지시를 잊어버리는 문제가 있다.

GAtt의 핵심 아이디어:
1. 훈련 시 시스템 프롬프트를 대화의 **각 사용자 메시지에 합성적으로 연결(concatenate)**하여 학습
2. 그러나 이전 턴의 시스템 프롬프트 토큰에 대한 **어텐션 손실(loss)은 0으로 설정** (loss masking)
3. 추론 시에는 시스템 프롬프트를 처음에 한 번만 제공

이를 통해 모델은 시스템 프롬프트의 지시사항을 대화 전반에 걸쳐 일관되게 따르게 된다. 실험에서 GAtt 적용 후 20턴 이상의 대화에서도 시스템 프롬프트 준수율이 크게 향상되었다.

## 방법론

### 모델 구성

| 모델 | 파라미터 | 레이어 | 어텐션 헤드 | KV 헤드 | 히든 차원 | 컨텍스트 |
|------|---------|--------|------------|---------|----------|----------|
| Llama 2-7B | 6.7B | 32 | 32 | 32 (MHA) | 4096 | 4096 |
| Llama 2-13B | 13.0B | 40 | 40 | 40 (MHA) | 5120 | 4096 |
| Llama 2-34B | 34.0B | 48 | 64 | 8 (GQA) | 8192 | 4096 |
| Llama 2-70B | 68.9B | 80 | 64 | 8 (GQA) | 8192 | 4096 |

모든 모델은 RMSNorm 정규화, SwiGLU 활성화 함수, Rotary Positional Embedding(RoPE)을 사용하며, 이 구성은 Llama 1과 동일하다. 7B와 13B 모델은 표준 MHA를 유지하고, 34B와 70B에만 GQA를 적용한 것은 대형 모델에서의 추론 효율이 더 중요하기 때문이다.

### 사전학습 인프라 및 탄소 배출

Llama 2의 사전학습에는 상당한 컴퓨팅 자원이 투입되었다. 논문에서는 GPU 시간과 탄소 배출량을 투명하게 공개했다.

| 모델 | GPU 시간 (A100) | 전력 소비 (W) | 탄소 배출 (tCO2eq) |
|------|----------------|--------------|-------------------|
| Llama 2-7B | 184,320 | 400 | 31.22 |
| Llama 2-13B | 368,640 | 400 | 62.44 |
| Llama 2-34B | 1,038,336 | 350 | 153.90 |
| Llama 2-70B | 1,720,320 | 400 | 291.42 |
| **총합** | **3,311,616** | - | **539.00** |

이 탄소 배출량은 GPT-4의 추정 탄소 배출량(비공개이나 수천 tCO2eq로 추정)에 비하면 상대적으로 적은 편이다. Meta는 100% 재생 에너지를 사용하여 실질 배출량을 상쇄했다고 보고했다. 이러한 투명한 탄소 배출 보고는 대형 모델 학습의 환경적 영향을 인식하는 중요한 선례가 되었다.

### 훈련 설정

- **옵티마이저**: AdamW ($\beta_1=0.9$, $\beta_2=0.95$, $\epsilon=10^{-5}$)
- **학습률**: cosine 스케줄, 최대 $3 \times 10^{-4}$, 워밍업 2000 스텝
- **가중치 감쇠**: 0.1
- **그래디언트 클리핑**: 1.0
- **배치 크기**: 4M 토큰
- **총 학습**: 2T 토큰
- **70B 모델**: A100 80GB GPU 2048개, 약 1,720,320 GPU-시간

### 안전성 훈련 (Safety Training)

Meta는 안전성 확보를 위해 다층적인 접근법을 적용했다. 이 과정은 학술적으로 매우 상세하게 문서화되어 있어, 이후 안전한 LLM 개발의 표준 참고 자료가 되었다.

**안전성 훈련 파이프라인:**

1. **안전성 SFT 데이터**: 적대적 프롬프트에 대한 안전한 응답 패턴을 시연하는 데이터 수집. 어노테이터에게 다양한 위험 카테고리(폭력, 자해, 범죄, 성적 콘텐츠, 혐오 발언 등)에 해당하는 프롬프트를 작성하게 하고, 이에 대한 안전한 거절 응답을 학습 데이터에 포함
2. **안전성 RLHF**: 안전성 보상 모델을 별도로 훈련하여, 위험한 응답에 낮은 점수를 부여. 유용성 보상 모델과 분리함으로써 두 목표 간 상충을 관리
3. **Red Teaming**: 350명 이상의 내외부 전문가가 참여하여 모델의 취약점을 체계적으로 탐색. 단일 턴 공격뿐만 아니라 멀티턴 대화를 통한 점진적 유도(jailbreaking) 시나리오도 포함
4. **컨텍스트 증류(Context Distillation)**: 안전성 관련 시스템 프롬프트를 사전에 포함시킨 상태에서 모델이 생성한 안전한 응답을 수집하고, 이를 시스템 프롬프트 없이도 같은 수준의 안전한 응답을 하도록 증류

이 다층적 접근법의 결과, Llama 2-Chat은 안전성 위반율에서 GPT-3.5 Turbo를 능가하는 성과를 달성했다.

### 정렬 훈련 반복

Meta는 RLHF를 **5번의 반복(iteration)**으로 수행했다. 각 반복에서:
1. 현재 모델로 새 응답 생성
2. 인간 어노테이터가 비교 평가
3. 보상 모델 재학습
4. RSFT + PPO 수행

이 반복적 접근법으로 모델 품질이 점진적으로 개선되었다. 초기 RLHF v1에서는 주로 응답 형식과 기본적인 유용성이 개선되고, 후기 반복에서는 미묘한 안전성 판단과 복잡한 지시 따르기 능력이 향상되는 패턴이 관찰되었다.

## 실험 결과

### 사전학습 모델 벤치마크

| 모델 | 파라미터 | MMLU | TriviaQA | NaturalQ | HellaSwag | HumanEval | GSM8K |
|------|---------|------|----------|----------|-----------|-----------|-------|
| MPT-7B | 7B | 26.8 | 59.6 | 19.8 | 76.4 | 18.3 | 6.8 |
| Falcon-7B | 7B | 27.8 | 56.9 | 18.1 | 74.9 | - | 6.8 |
| Llama 1-7B | 7B | 35.1 | 61.6 | 21.0 | 76.1 | 11.4 | 11.0 |
| Llama 1-13B | 13B | 46.9 | 63.0 | 22.5 | 79.2 | 15.8 | 17.8 |
| Llama 2-7B | 7B | 45.3 | 68.9 | 25.7 | 77.2 | 12.8 | 14.6 |
| Llama 2-13B | 13B | 54.8 | 77.2 | 30.7 | 80.7 | 18.3 | 28.7 |
| Llama 2-70B | 70B | **68.9** | **87.6** | **44.3** | **87.3** | **29.9** | **56.8** |

Llama 2-70B는 모든 오픈소스 모델 중 최고 성능을 달성하며, 비공개 모델인 GPT-3.5에도 근접한다. 특히 주목할 점은 Llama 2-7B가 Llama 1-13B(두 배 큰 모델)에 거의 근접하는 성능을 보인다는 것이다. 이는 학습 토큰 수 증가(1.4T에서 2T)의 효과를 잘 보여준다.

### 비공개 모델과의 비교

Llama 2-70B와 비공개 모델 간의 격차도 분석할 가치가 있다:

| 벤치마크 | Llama 2-70B | GPT-3.5 | GPT-4 |
|---------|------------|---------|-------|
| MMLU (5-shot) | 68.9 | 70.0 | 86.4 |
| GSM8K (8-shot) | 56.8 | 57.1 | 92.0 |
| HumanEval (0-shot) | 29.9 | 48.1 | 67.0 |

GPT-3.5와는 대부분의 벤치마크에서 동등하지만, GPT-4와는 여전히 상당한 격차가 존재한다. 이 격차는 이후 Llama 3.1-405B에 이르러서야 상당 부분 해소된다.

### 챗 모델 인간 평가

약 4,000건의 단일 턴 및 멀티턴 프롬프트에 대해 인간 평가자가 선호도를 비교한 결과:

| 비교 | Llama 2-Chat 승률 | 동점 | 상대 승률 |
|------|------------------|------|----------|
| 70B vs ChatGPT | 36% | 31% | 33% |
| 70B vs Falcon-40B-Instruct | 72% | 13% | 15% |
| 70B vs MPT-30B-Chat | 75% | 12% | 13% |
| 70B vs Vicuna-33B | 66% | 17% | 17% |

Llama 2-Chat 70B는 ChatGPT(GPT-3.5 Turbo)와 거의 동등한 수준이며, 다른 모든 오픈소스 챗 모델을 크게 앞선다.

아래 그림은 GPT-4를 심판으로 한 평가에서 Llama 2-Chat 70B가 유용성(Helpfulness)과 안전성(Safety) 두 축 모두에서 경쟁 모델들을 압도하는 결과를 보여준다. 녹색 영역은 Llama 2가 상대 모델보다 우수한 구간으로, ChatGPT를 포함한 모든 비교 대상이 이 영역 내에 위치한다.

![유용성과 안전성 두 축에서의 모델 비교](figures/fig_1_2.png)
*Llama 2-Chat 70B 대비 경쟁 모델들의 유용성(Helpfulness)과 안전성(Safety) Win Rate. 녹색 영역은 Llama 2가 우수한 구간이며, ChatGPT를 포함한 모든 모델이 이 영역에 위치한다. GPT-4 심판 기준.*

### 안전성 벤치마크

안전성 평가는 다양한 유해 카테고리(폭력, 성적 콘텐츠, 범죄 조장, 자해 등)에 대한 위반율로 측정한다:

| 모델 | 안전 위반율 (하위) | 유용성 점수 (상위) |
|------|----------------|----------------|
| Vicuna-13B | 19.5% | 3.2 |
| Falcon-40B-Instruct | 13.2% | 3.0 |
| GPT-3.5 Turbo | 6.1% | 3.8 |
| Llama 2-Chat 7B | 4.1% | 3.5 |
| Llama 2-Chat 13B | 3.8% | 3.6 |
| Llama 2-Chat 70B | **3.4%** | **3.7** |

다음 그림은 이 안전성 평가 결과를 시각적으로 비교한 것이다. Llama 2-Chat 시리즈(7B/13B/34B/70B)가 모든 비교 대상 모델보다 현저히 낮은 위반율을 기록하며, 특히 GPT-3.5 Turbo(ChatGPT)보다도 안전한 것을 확인할 수 있다.

![주요 챗 모델의 안전성 위반율 비교](figures/fig_4.png)
*주요 챗 모델의 안전성 위반율(%) 비교. Llama 2-Chat 시리즈(짙은 파란색)가 Vicuna, MPT, PaLM-Bison 등 경쟁 모델 대비 현저히 낮은 위반율을 기록하며, ChatGPT(약 5%)에도 앞선다.*

### 유해 카테고리별 안전성 상세 평가

논문에서는 카테고리별 세부 안전성 평가 결과도 제시했다:

| 유해 카테고리 | Llama 2-Chat 70B 위반율 | ChatGPT 위반율 |
|-------------|----------------------|---------------|
| 폭력 및 범죄 | 2.8% | 5.0% |
| 성적 콘텐츠 | 1.5% | 3.2% |
| 무기 및 약물 | 4.2% | 7.8% |
| 자해 | 1.2% | 2.1% |
| 혐오 발언 | 3.1% | 6.5% |
| 개인 정보 침해 | 5.8% | 8.9% |

대부분의 카테고리에서 Llama 2-Chat이 ChatGPT보다 낮은 위반율을 기록했다. 이는 안전성 전용 보상 모델이 각 카테고리에 특화된 판단을 학습할 수 있었기 때문이다.

### RLHF 반복별 개선

정렬 훈련의 반복 횟수에 따른 성능 변화:

| 반복 | 유용성 점수 | 안전성 점수 |
|------|-----------|----------|
| SFT만 | 3.1 | 2.8 |
| RLHF v1 | 3.4 | 3.5 |
| RLHF v2 | 3.5 | 3.7 |
| RLHF v3 | 3.6 | 3.8 |
| RLHF v5 | 3.7 | 4.0 |

주목할 점은 SFT에서 RLHF v1으로의 전환에서 가장 큰 점프가 발생한다는 것이다. 특히 안전성 점수가 2.8에서 3.5로 크게 향상되었으며, 이는 안전성 보상 모델이 즉각적인 효과를 발휘한다는 것을 보여준다.

다음 그림은 RLHF 반복 과정 전체를 유용성과 무해성(harmlessness) 두 축으로 시각화한 것이다. SFT-v1에서 시작하여 RLHF-v5(with PPO)에 이르기까지, 두 지표가 동시에 향상되는 파레토 개선(Pareto improvement) 궤적을 명확히 확인할 수 있다. 이는 두 개의 분리된 보상 모델이 안전성-유용성 트레이드오프를 효과적으로 관리한다는 핵심 주장을 실증적으로 뒷받침한다.

![RLHF 반복에 따른 유용성-무해성 동시 개선 궤적](figures/fig_12_1.png)
*RLHF 반복에 따른 유용성(Helpfulness)과 무해성(Harmlessness) 점수 변화. SFT-v1(좌하단)에서 RLHF-v5+PPO(우상단)로 갈수록 두 지표가 동시에 향상되는 파레토 개선 궤적을 보인다. Meta 보상 모델 기준.*

### 흥미로운 발견: 도구 사용의 자발적 등장

논문에서 보고된 주목할 만한 현상 중 하나는, RLHF 훈련 과정에서 모델이 **도구 사용(tool use)을 명시적으로 가르치지 않았음에도 자발적으로** 검색 엔진 호출이나 계산기 사용을 시도하기 시작했다는 것이다. 이는 정렬 훈련이 모델의 내재된 능력을 끌어내는 효과가 있음을 시사한다. 유용성 보상 모델이 정확한 답변에 높은 점수를 부여하므로, 모델이 정확성을 높이기 위해 외부 도구를 활용하는 전략을 스스로 학습한 것으로 해석된다.

## 의의 및 한계

### 의의

- **상업적 오픈소스 시대 개막**: 기업이 자유롭게 사용할 수 있는 고품질 챗 모델을 제공하여, 수많은 스타트업과 기업이 자체 AI 서비스를 구축할 수 있게 했다
- **RLHF 방법론의 공개 교과서**: 보상 모델 설계, 데이터 수집, 반복적 정렬 과정 등을 투명하게 문서화하여 정렬 연구의 표준 참고 자료가 되었다
- **두 보상 모델 전략**: 안전성과 유용성을 분리 관리하는 접근법은 이후 많은 정렬 연구에서 채택되었다
- **GQA 실용화**: 대형 모델의 추론 효율 개선 기법을 실전에서 검증하여, 이후 Mistral, Qwen, Yi 등 대부분의 후속 모델이 GQA를 채택하게 했다
- **Ghost Attention**: 멀티턴 대화에서의 지시 따르기 문제에 대한 실용적 해결책을 제시
- **책임 있는 AI 배포의 모범**: Red teaming, 안전성 평가 체계, 사용 정책(Acceptable Use Policy), 탄소 배출 보고 등을 포함한 포괄적인 AI 안전 프레임워크를 제시
- **생태계 촉진**: Llama 2 공개 이후 수천 개의 파인튜닝 변형 모델이 Hugging Face 등에 등장하며 오픈소스 LLM 생태계가 폭발적으로 성장

### 한계

- **영어 중심**: 학습 데이터가 주로 영어로 구성되어 다국어 능력이 제한적이다. 한국어, 중국어 등에서의 성능은 Qwen, Yi 등 다국어 특화 모델에 비해 현저히 낮다.
- **컨텍스트 길이**: 4096 토큰으로 긴 문서나 코드 처리에 한계가 있다. 동시기 Claude 2(100K), GPT-4 Turbo(128K) 대비 크게 부족했다.
- **수학/코드 약점**: GSM8K 56.8%, HumanEval 29.9%로 수학/코드 특화 모델 대비 상당한 격차가 있다.
- **Meta 사용 정책 제약**: 월간 활성 사용자 7억 명 이상 서비스는 별도 라이선스가 필요하며, 이는 완전한 오픈소스와는 차이가 있다. OSI(Open Source Initiative) 기준의 오픈소스 정의와 일치하지 않는다는 비판도 존재한다.
- **RLHF 비용**: 반복적 인간 어노테이션과 보상 모델 학습에 상당한 비용이 소요되어, 소규모 연구 기관에서의 재현이 어렵다. 약 100만 개의 어노테이션 수집에 필요한 비용은 수백만 달러 수준으로 추정된다.
- **과도한 거절(Over-refusal)**: 안전성 훈련의 부작용으로, 완전히 무해한 질문에 대해서도 불필요하게 거절하는 경향이 관찰되었다. 예를 들어 역사적 사건에 대한 학술적 질문도 때때로 거부되는 사례가 보고되었다.

### 후속 발전

Llama 2는 오픈소스 AI 생태계에서 안전성과 유용성을 겸비한 챗 모델의 기준을 세웠으며, 이후 Code Llama(코드 특화), Purple Llama(안전성 도구), Llama 3/3.1(성능 대폭 향상), Llama 4(MoE 아키텍처) 등으로 발전했다. 특히 Llama 3.1-405B는 GPT-4 수준의 성능을 오픈소스로 달성하며 이 계보의 중요성을 입증했다.

## 코드 예제

### GQA (Grouped Query Attention) 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class GroupedQueryAttention(nn.Module):
    """Llama 2 70B에 도입된 Grouped Query Attention.
    num_kv_heads < num_heads 로 KV 캐시 크기를 줄이면서
    MHA에 근접하는 성능을 유지.

    핵심: 여러 Q 헤드가 하나의 KV 헤드를 공유
    MHA(H=H) -> GQA(G<H) -> MQA(G=1)의 스펙트럼 상 중간점
    """
    def __init__(
        self,
        d_model: int = 4096,
        num_heads: int = 32,
        num_kv_heads: int = 8,
        max_seq_len: int = 4096,
    ):
        super().__init__()
        assert num_heads % num_kv_heads == 0, "num_heads must be divisible by num_kv_heads"
        self.num_heads = num_heads
        self.num_kv_heads = num_kv_heads
        self.num_groups = num_heads // num_kv_heads  # 각 KV 헤드가 담당할 Q 헤드 수
        self.head_dim = d_model // num_heads
        self.scale = self.head_dim ** -0.5

        # Q는 전체 헤드 수, K/V는 KV 헤드 수만큼만
        self.Wq = nn.Linear(d_model, num_heads * self.head_dim, bias=False)
        self.Wk = nn.Linear(d_model, num_kv_heads * self.head_dim, bias=False)
        self.Wv = nn.Linear(d_model, num_kv_heads * self.head_dim, bias=False)
        self.Wo = nn.Linear(num_heads * self.head_dim, d_model, bias=False)

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None):
        B, T, D = x.shape

        # 프로젝션
        Q = self.Wq(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        K = self.Wk(x).view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)
        V = self.Wv(x).view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)

        # KV를 Q 헤드 수에 맞게 반복 확장
        # (B, num_kv_heads, T, head_dim) -> (B, num_heads, T, head_dim)
        K = K.repeat_interleave(self.num_groups, dim=1)
        V = V.repeat_interleave(self.num_groups, dim=1)

        # Scaled Dot-Product Attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale  # (B, H, T, T)

        # Causal mask (자기회귀)
        if mask is None:
            mask = torch.tril(torch.ones(T, T, device=x.device, dtype=torch.bool))
        scores = scores.masked_fill(~mask.unsqueeze(0).unsqueeze(0), float('-inf'))

        attn = F.softmax(scores, dim=-1)
        out = torch.matmul(attn, V)  # (B, H, T, head_dim)
        out = out.transpose(1, 2).contiguous().view(B, T, -1)
        return self.Wo(out)


def compare_kv_cache_memory():
    """MHA vs GQA KV 캐시 메모리 비교.
    Llama 2-70B 설정: d_model=8192, H=64, G=8
    """
    d_model = 8192
    num_layers = 80
    seq_len = 4096
    dtype_bytes = 2  # float16

    # MHA: 모든 헤드가 독립적 KV
    mha_kv_cache = 2 * num_layers * seq_len * d_model * dtype_bytes

    # GQA: KV 헤드 수만큼만 저장 (8/64 = 1/8)
    num_kv_heads = 8
    head_dim = d_model // 64  # 128
    gqa_kv_cache = 2 * num_layers * seq_len * num_kv_heads * head_dim * dtype_bytes

    print(f"MHA KV 캐시: {mha_kv_cache / 1e9:.1f} GB")
    print(f"GQA KV 캐시: {gqa_kv_cache / 1e9:.1f} GB")
    print(f"절감 비율: {mha_kv_cache / gqa_kv_cache:.0f}x")


# MHA vs GQA 파라미터 비교
d_model = 4096
mha_kv_params = 2 * d_model * d_model   # K,V 각 d_model x d_model
gqa_kv_params = 2 * d_model * (d_model // 4)  # KV 헤드를 1/4로
print(f"MHA KV 파라미터: {mha_kv_params:,}")   # 33,554,432
print(f"GQA KV 파라미터: {gqa_kv_params:,}")   # 8,388,608 (4배 감소)

compare_kv_cache_memory()
# MHA KV 캐시: 10.7 GB
# GQA KV 캐시: 1.3 GB
# 절감 비율: 8x

# GQA 동작 테스트
gqa = GroupedQueryAttention(d_model=512, num_heads=8, num_kv_heads=2)
x = torch.randn(2, 16, 512)
out = gqa(x)
print(f"\nGQA output: {out.shape}")  # (2, 16, 512)
print(f"Q 파라미터: {gqa.Wq.weight.numel():,}")
print(f"K 파라미터: {gqa.Wk.weight.numel():,} (Q의 1/{8//2})")
print(f"V 파라미터: {gqa.Wv.weight.numel():,} (Q의 1/{8//2})")
```

> **Llama 2의 핵심 기여**: 상업적 오픈소스 라이선스로 AI 생태계를 변화시켰으며, GQA로 추론 효율을 개선하고, 두 개의 분리된 보상 모델(유용성 + 안전성)로 RLHF의 새로운 표준을 제시했다. Ghost Attention은 멀티턴 대화에서 시스템 프롬프트 준수 문제를 해결하는 실용적 기법이다.

## 관련 문서

- [[llama|LLaMA: Open and Efficient Foundation Language Models]] -- 발전 기반
- [[llama-3|LLaMA 3]] -- 후속 모델
- [[qwen2|Qwen2 Technical Report]] -- 영감을 줌
