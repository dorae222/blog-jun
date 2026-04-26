<!-- infographic-hero -->
![Mixtral of Experts 핵심 요약](figures/infographic.svg)

*Figure: Mixtral of Experts 한 장 요약 인포그래픽*

## 개요

Mixtral 8x7B는 Mistral AI가 2024년 1월 발표한 **희소 혼합 전문가(Sparse Mixture of Experts, SMoE)** 언어 모델이다. 모델 이름처럼 8개의 "전문가(expert)" FFN 레이어가 있으며, 각 토큰은 게이팅 네트워크(router)에 의해 그 중 **2개만 선택**되어 처리된다. 이를 통해 전체 파라미터는 46.7B이지만, 실제 추론 시에는 12.9B만 활성화되어 **더 적은 연산으로 더 큰 모델의 성능**을 달성한다.

Mixtral은 오픈 가중치(**Apache 2.0 라이선스**)로 공개되었으며, Llama 2 70B보다 대부분 벤치마크에서 우수하면서 추론 속도는 약 6배 빠르다. 명령 파인튜닝 버전인 Mixtral 8x7B Instruct는 MT-Bench에서 8.3을 기록하여 GPT-3.5 Turbo(8.32)와 동등한 수준을 보인다. 이 모델은 오픈소스 LLM 세계에 MoE 아키텍처를 본격적으로 도입한 이정표적 사례로, 이후 DeepSeek-MoE, Qwen-MoE, DBRX 등 다양한 MoE 모델 연구의 기폭제가 되었다.

## 배경 및 문제

### 스케일링의 계산 비용 문제

더 좋은 성능을 위해 모델을 키우면 추론 비용이 선형적으로 증가한다. 70B 모델은 7B 모델보다 약 10배 많은 GPU 메모리와 연산을 필요로 한다. FLOPs(부동소수점 연산 횟수)로 보면:

$$\text{FLOPs}_{\text{forward}} \approx 2 \times N_{\text{params}} \times T$$

여기서 $N_{\text{params}}$는 모델 파라미터 수, $T$는 토큰 수다. 70B 모델의 추론 비용은 7B 모델의 10배에 달한다. 실용적인 배포를 위해서는 **파라미터는 많지만 연산은 적은** 방법이 필요하다.

### 밀집 모델(Dense Model)의 한계

전통적인 Transformer는 **밀집 모델(dense model)**로, 모든 입력에 대해 모든 파라미터가 활성화된다. 이는 비효율적인데, 직관적으로 "Python 코드 생성"과 "프랑스어 번역"에 동일한 파라미터를 모두 사용할 필요는 없기 때문이다. 각 입력에 관련된 파라미터만 활성화하면 연산을 크게 줄일 수 있다.

### 혼합 전문가(MoE)의 역사

MoE 아키텍처는 오랜 역사를 가진다:

| 시기 | 연구 | 기여 |
|------|------|------|
| 1991 | Jacobs et al. | MoE 개념 최초 제안 |
| 2017 | Shazeer et al. | 희소 MoE를 LSTM에 적용 (137B 파라미터) |
| 2022 | Switch Transformer | Transformer에 MoE 적용, Top-1 라우팅 |
| 2022 | ST-MoE | 학습 안정성 개선, 부하 균형 보조 손실 |
| 2024 | **Mixtral 8x7B** | **오픈소스 대형 MoE 실용화** |
| 2024 | DeepSeek-MoE | Fine-grained 전문가 분할 |
| 2025 | DeepSeek-V3 | 보조 손실 없는 부하 균형 |

Mixtral은 이 계보에서 **오픈소스 실용적 MoE**의 분기점을 만든 모델이다.

## 핵심 아이디어

### 희소 MoE 레이어

Mixtral의 핵심 아이디어는 단순하면서도 강력하다. Mistral 7B의 아키텍처를 기반으로, 각 Transformer 레이어의 **FFN 서브레이어를 8개의 전문가 FFN으로 교체**한다. **어텐션 레이어는 그대로 공유**되므로, 모든 토큰이 동일한 셀프 어텐션을 통과한 뒤 라우터에 의해 적합한 전문가에게 분배된다.

아래 그림은 이 MoE 레이어의 구조를 보여준다. 라우터가 입력을 받아 전문가별 가중치를 산출하고, 선택된 전문가들의 출력을 가중 합산하여 최종 결과를 생성한다.

![Mixture of Experts 레이어의 구조 다이어그램](figures/fig_2.png)
*Figure 2: MoE 레이어의 전체 흐름. 라우터(gating network)가 입력 토큰에 대해 전문가별 가중치를 계산하고, 상위 2개 전문가만 선택하여 그 출력을 가중 합산한다. 선택되지 않은 전문가는 해당 토큰에 대해 연산을 수행하지 않으므로, 전체 파라미터의 일부만 활성화된다. (Jiang et al., 2024)*

각 토큰 $x$에 대해 게이팅 네트워크(router)가 8개 전문가 중 상위 2개를 선택한다:

$$\text{MoE}(x) = \sum_{i \in \text{TopK}(G(x), 2)} G_i(x) \cdot E_i(x)$$

게이팅 함수 $G(x)$:

$$G(x) = \text{Softmax}(\text{TopK}(x \cdot W_g, k=2))$$

여기서 $W_g \in \mathbb{R}^{d \times 8}$은 게이팅 가중치 행렬, $E_i$는 $i$번째 전문가의 SwiGLU FFN이다. TopK 연산은 상위 $k$개를 제외한 나머지 로짓을 $-\infty$로 마스킹한 후 softmax를 적용하여, 선택된 전문가의 가중치가 합이 1이 되도록 한다.

이 과정을 수식으로 풀어쓰면:

$$g(x) = W_g^\top x \in \mathbb{R}^8 \quad \text{(라우터 로짓)}$$

$$\text{Top2}(g) = \{i_1, i_2\} \text{ where } g_{i_1} \geq g_{i_2} \geq g_j \; \forall j \neq i_1, i_2$$

$$w_i = \frac{\exp(g_i)}{\exp(g_{i_1}) + \exp(g_{i_2})} \quad \text{for } i \in \{i_1, i_2\}$$

$$\text{output} = w_{i_1} \cdot E_{i_1}(x) + w_{i_2} \cdot E_{i_2}(x)$$

### 파라미터 효율 분석

| 항목 | 밀집 모델 | Mixtral 8x7B |
|------|---------|-------------|
| 전체 파라미터 | - | 46.7B |
| 추론 시 활성 파라미터 | $N$ | 12.9B (27.6%) |
| 어텐션 파라미터 | 공유 | 공유 (MoE 미적용) |
| FFN 파라미터 | 1개 | 8개 전문가 |
| 토큰당 FLOPs | $2N$ | $\approx 2 \times 12.9B$ |

토큰당 활성화되는 2개의 전문가 + 공유 어텐션 레이어의 연산량은 약 13B 밀집 모델과 동일하지만, 전체 파라미터 용량은 47B에 달하여 **훨씬 더 풍부한 지식을 저장**할 수 있다.

### 왜 Top-2인가?

Mixtral은 토큰당 2개의 전문가를 활성화하는 Top-2 라우팅을 사용한다. 이 선택의 근거:

- **Top-1**(Switch Transformer 방식): 연산 효율은 최고이지만 성능 하락이 큼
- **Top-2**: 성능과 효율의 최적 균형점. 두 전문가의 가중 합으로 더 세밀한 표현 가능
- **Top-3 이상**: 성능 향상이 미미하면서 연산량 증가

### 아키텍처 세부 사항

Mixtral은 Mistral 7B의 아키텍처를 거의 그대로 계승한다:
- **SWA(Sliding Window Attention)**: 윈도우 크기 4096
- **GQA(Grouped Query Attention)**: 32개 Q 헤드, 8개 KV 헤드
- **RoPE Positional Embedding**: 상대 위치 인코딩
- **RMSNorm**: Pre-normalization
- **SwiGLU 활성화 함수**: 게이팅 FFN
- **컨텍스트 길이**: **32K 토큰** (Mistral 7B의 4096에서 크게 확장)

## 방법론

### 모델 구성

| 항목 | 값 | 비교 (Llama 2-70B) |
|------|----|---------|
| 전체 파라미터 | 46.7B | 70B |
| 활성 파라미터 | 12.9B | 70B |
| 레이어 수 | 32 | 80 |
| 전문가 수/레이어 | 8 | - (밀집) |
| 활성 전문가/토큰 | 2 | - |
| 쿼리 헤드 수 | 32 | 64 |
| KV 헤드 수 | 8 | 8 |
| 히든 차원 | 4096 | 8192 |
| 전문가 FFN 차원 | 14336 | - |
| 컨텍스트 길이 | 32768 | 4096 |
| 토큰당 FLOPs | ~26B | ~140B |

주목할 점은 Mixtral이 Llama 2 70B 대비 토큰당 FLOPs가 약 5.4배 적다는 것이다. 레이어 수도 32개로 Llama 2 70B(80개)의 절반 이하이지만, 각 레이어가 8개의 전문가 FFN을 갖고 있어 전체 파라미터 용량에서는 상당한 규모를 확보한다.

### 분산 훈련과 전문가 병렬화

MoE 모델의 학습에는 **전문가 병렬화(Expert Parallelism, EP)**가 핵심이다:

1. **데이터 병렬(DP)**: 배치를 여러 GPU에 분산
2. **텐서 병렬(TP)**: 단일 레이어를 여러 GPU에 분할
3. **전문가 병렬(EP)**: 각 전문가를 다른 GPU에 배치

EP에서는 **All-to-All 통신**이 필요하다. 각 토큰이 선택된 전문가가 있는 GPU로 전송되어야 하기 때문이다:

$$\text{통신량} \propto B \times T \times k \times d$$

여기서 $B$는 배치 크기, $T$는 시퀀스 길이, $k$는 활성 전문가 수, $d$는 히든 차원이다. 이 통신 오버헤드가 MoE 학습의 주요 병목이지만, Mixtral은 이를 효율적으로 구현했다.

### 부하 균형 (Load Balancing)

MoE의 잠재적 문제는 **전문가 불균형(load imbalance)**이다. 특정 전문가에 토큰이 쏠리면 해당 전문가의 GPU만 과부하되고 나머지는 유휴 상태가 된다. Mixtral은 이를 방지하기 위해 보조 손실(auxiliary load balancing loss)을 사용한다:

$$\mathcal{L}_{\text{balance}} = \alpha \cdot N \cdot \sum_{i=1}^{N} f_i \cdot p_i$$

여기서 $f_i$는 전문가 $i$에 라우팅된 토큰 비율, $p_i$는 전문가 $i$의 평균 게이팅 확률, $\alpha$는 균형 계수, $N$은 전문가 수다. 완벽한 균형이면 $f_i = p_i = 1/N$이 된다.

## 실험 결과

### 주요 벤치마크 비교

Mixtral 8x7B의 가장 인상적인 결과는 12.9B 활성 파라미터만으로 70B급 밀집 모델과 대등하거나 우위의 성능을 달성한다는 점이다. 아래 벤치마크 비교 차트에서 Mixtral(노란색)이 모든 카테고리에서 Llama 2 70B를 포함한 비교 모델들을 능가하는 것을 확인할 수 있다.

![Mixtral 8x7B와 Llama 2, Mistral 7B의 종합 벤치마크 비교 차트](figures/fig_3.png)
*Figure 3: 주요 벤치마크 카테고리별 성능 비교. Mixtral 8x7B(노란색)는 MMLU, Knowledge, Reasoning, Comprehension, Math, Code 전 영역에서 Llama 2 70B(초록색)를 포함한 모든 비교 모델을 상회한다. 특히 Math와 Code 카테고리에서의 격차가 두드러진다. (Jiang et al., 2024)*

| 모델 | 활성 파라미터 | MMLU | HellaSwag | WinoGrande | ARC-c | HumanEval | MBPP | GSM8K | MATH |
|------|-----------|------|-----------|------------|-------|-----------|------|-------|----- |
| Llama 2-13B | 13B | 54.8 | 81.9 | 72.0 | 48.8 | 18.3 | 30.2 | 29.6 | 3.9 |
| Llama 2-70B | 70B | 69.8 | 87.1 | 80.0 | 57.4 | 29.9 | 49.8 | 59.4 | 13.5 |
| GPT-3.5 | ~175B? | 70.0 | 85.5 | 81.6 | 61.5 | 48.1 | - | 57.1 | - |
| **Mixtral 8x7B** | **12.9B** | **70.6** | **86.7** | **81.2** | **60.7** | **40.2** | **52.2** | **74.4** | **28.4** |

핵심 관찰:
- **MMLU 70.6**: Llama 2 70B(69.8)와 GPT-3.5(70.0) 모두 능가
- **GSM8K 74.4**: GPT-3.5(57.1)를 17점 이상 앞서는 압도적 수학 성능
- **MATH 28.4**: Llama 2 70B(13.5)의 2배 이상
- **코드(HumanEval 40.2, MBPP 52.2)**: Llama 2 70B 대비 큰 폭 향상
- 이 모든 것을 12.9B 활성 파라미터로 달성

### 활성 파라미터 대비 스케일링 효율

MoE 모델의 진정한 가치는 활성 파라미터 기준으로 평가할 때 드러난다. 아래 그림은 x축을 활성 파라미터 수로 놓고, Mixtral과 Llama 2의 성능을 비교한 것이다. Mixtral 8x7B는 12.9B 활성 파라미터만으로 70B 전체를 활성화하는 Llama 2 70B와 동등하거나 우수한 성능을 보인다.

![활성 파라미터 기준 Mixtral과 Llama 2의 스케일링 비교](figures/fig_4.png)
*Figure 4: 활성 파라미터(Active Params) 기준 성능 스케일링 비교. 주황색 선(Mistral/Mixtral)이 빨간색 선(Llama 2) 대비 동일 활성 파라미터에서 일관되게 높은 성능을 기록한다. 특히 Mixtral 8x7B는 12.9B 활성 파라미터로 Llama 2 70B(70B 활성) 수준의 성능을 6개 벤치마크에서 달성하여, MoE의 파라미터 효율성을 실증적으로 입증한다. (Jiang et al., 2024)*

이 결과는 "활성 파라미터당 성능"이라는 관점에서 MoE 아키텍처가 밀집 모델 대비 약 5배 이상의 효율을 달성할 수 있음을 보여준다.

### 긴 컨텍스트 처리 능력

Mixtral 8x7B는 Mistral 7B의 4K 컨텍스트에서 32K 토큰으로 크게 확장된 컨텍스트 윈도우를 지원한다. 이 능력을 검증하기 위해 논문에서는 Passkey Retrieval 테스트를 수행했다.

![32K 컨텍스트 범위에서의 Passkey 검색 정확도 히트맵](figures/fig_5_1.png)
*Figure 5a: Passkey Retrieval 평가 결과. X축은 시퀀스 길이, Y축은 passkey 삽입 위치로, 전 범위에서 거의 완벽한 초록색(정확도 1.0)을 보여 32K 토큰까지의 컨텍스트 처리 능력을 입증한다. (Jiang et al., 2024)*

히트맵이 전 영역에서 초록색을 유지한다는 것은, 시퀀스 길이와 삽입 위치에 관계없이 Mixtral이 정보를 정확하게 검색할 수 있음을 의미한다. 또한 컨텍스트 길이가 늘어날수록 퍼플렉시티가 지속적으로 감소하는 패턴도 확인되었다.

![컨텍스트 길이 증가에 따른 퍼플렉시티 감소 곡선](figures/fig_5_2.png)
*Figure 5b: 컨텍스트 길이가 늘어날수록 Mixtral 8x7B의 퍼플렉시티(perplexity)가 지속적으로 감소하는 그래프. 약 10K 토큰 이후에도 완만하게 계속 개선되어 32K 토큰까지 맥락 활용 능력이 유지됨을 확인할 수 있다. (Jiang et al., 2024)*

이 결과는 Mixtral이 Sliding Window Attention(SWA)과 확장된 컨텍스트 길이를 효과적으로 활용하여, 긴 문서 처리에서도 안정적인 성능을 발휘함을 보여준다.

### 추론 속도 비교

| 모델 | 활성 파라미터 | 상대적 처리량 | 토큰당 FLOPs |
|------|-------------|-------------|-------------|
| Llama 2-70B | 70B | 1x | ~140B |
| Mixtral 8x7B | 12.9B | **~6x** | ~26B |

동일한 하드웨어(예: 2x A100 80GB)에서 Mixtral은 Llama 2 70B보다 약 6배 빠른 처리량을 제공한다. 이는 활성 파라미터 비율(12.9B vs 70B = 5.4x)과 거의 일치한다.

### 다국어 성능

| 모델 | 독일어 (DE) | 프랑스어 (FR) | 이탈리아어 (IT) | 스페인어 (ES) | 평균 |
|------|-----------|-------------|--------------|-------------|------|
| Llama 2-70B | 52.4 | 54.0 | 48.6 | 63.9 | 54.7 |
| **Mixtral 8x7B** | **59.4** | **62.0** | **57.0** | **70.1** | **62.1** |

영어 외에도 유럽 언어에서 Llama 2 70B를 크게 능가한다. 이는 Mistral AI가 프랑스 기반이라는 점과도 관련이 있을 수 있다.

### Mixtral 8x7B Instruct

명령 파인튜닝 버전인 Mixtral 8x7B Instruct는 당시 오픈소스 모델 중 가장 높은 수준의 instruction following 능력을 보여주었다. 아래 리더보드에서 Mixtral Instruct가 GPT-3.5 Turbo, Claude-2.1 등 유료 API 모델들과 어깨를 나란히 하는 것을 확인할 수 있다.

![Chatbot Arena Elo 및 MT-Bench 리더보드](figures/fig_7.png)
*Figure 7: Chatbot Arena Elo Rating 및 MT-Bench 리더보드. Mixtral 8x7B Instruct v0.1이 Apache 2.0 라이선스의 오픈소스 모델임에도 Arena Elo 1121, MT-Bench 8.3을 기록하며, GPT-3.5 Turbo(1117, 8.39), Claude-2.1(1117, 8.18), Gemini Pro(1111) 등 유료 모델들과 동등한 수준에 위치한다. (Jiang et al., 2024)*

- **MT-Bench**: 8.3 (GPT-3.5 Turbo의 8.32와 사실상 동일)
- **Arena Elo**: 1121로 GPT-3.5 Turbo(1117)보다 높은 순위
- **AlpacaEval 2.0**: Claude-2.1, Gemini Pro를 능가

오픈소스 모델이 유료 API 모델과 동등한 대화 품질을 달성한 것은 Mixtral의 가장 실용적인 성과 중 하나다.

### 전문가 분석

Mixtral 논문에서 흥미로운 분석은 전문가들의 **전문화 패턴**이다. 아래 그림은 Python 코드와 수학 문제를 처리할 때 각 토큰에 어떤 전문가가 할당되는지를 레이어별로 시각화한 것이다. 색상이 전문가 번호를 나타내며, 동일한 텍스트라도 레이어 깊이에 따라 전문가 선택 패턴이 달라지는 것을 볼 수 있다.

![토큰별 전문가 선택 패턴 - Python 코드와 수학 문제 비교](figures/fig_9.png)
*Figure 9: 레이어 0, 15, 31에서의 토큰별 전문가 할당 시각화. 상단은 Python 코드, 하단은 수학 문제를 처리하는 경우이다. 초기 레이어(Layer 0)에서는 비교적 균등한 전문가 배정이 이루어지지만, 깊은 레이어(Layer 31)로 갈수록 코드의 구문 요소(예: 키워드, 연산자)와 수학 표현에 대해 특정 전문가가 집중적으로 선택되는 전문화 경향이 뚜렷해진다. (Jiang et al., 2024)*

주요 관찰:
- 각 전문가가 완전히 독립적인 도메인을 담당하는 것은 **아니다**
- 대신 구문(syntax)과 의미(semantics) 수준에서 부분적 전문화가 나타남
- 예: 특정 전문가가 코드 토큰에 더 자주 활성화되지만, 완전히 "코드 전문가"인 것은 아님
- 깊은 레이어일수록 전문가 선택의 차별화가 강해지는 경향
- 이는 MoE가 인간 직관적인 "전문가 분업"보다는 더 미묘한 계산적 분업을 학습함을 시사

이러한 토큰 수준의 분석을 넘어, 도메인 수준에서의 전문가 배정 비율을 살펴보면 부하 균형이 실제로 잘 작동하고 있음을 확인할 수 있다.

![도메인별 전문가 선택 비율 분포 (레이어 0, 15, 31)](figures/fig_8.png)
*Figure 8: ArXiv, GitHub, DM Mathematics 등 8개 도메인의 데이터를 처리할 때 각 전문가(Expert 0~7)가 선택되는 비율. 레이어 0, 15, 31 모두에서 특정 전문가에 과도하게 쏠리지 않고 전반적으로 균등한 분포를 보여, 보조 손실(auxiliary loss)에 의한 부하 균형이 효과적으로 작동하고 있음을 확인할 수 있다. (Jiang et al., 2024)*

레이어 0에서는 거의 완벽한 균등 분포를 보이지만, 레이어 15와 31로 갈수록 도메인 간 미세한 차이가 나타나기 시작한다. 이 경향은 전체 32개 레이어에 걸친 전문가 선택 비율 분포에서 더욱 명확하게 드러난다.

![전체 레이어에 걸친 전문가 선택 비율 분포](figures/fig_10.png)
*Figure 10: 모든 32개 레이어에서 8개 전문가 각각의 선택 비율(first choice, second choice 포함)을 보여주는 차트. 레이어가 깊어질수록 전문가 선택이 도메인에 따라 차별화되는 경향이 나타난다. (Jiang et al., 2024)*

마지막으로, 레이어에 따른 각 도메인 소스의 전문가 배정 비율 추이를 보면 전문화 패턴의 전체적인 흐름을 파악할 수 있다.

![레이어별 도메인 전문가 배정 비율 추이](figures/fig_11.png)
*Figure 11: 레이어(x축)에 따른 각 도메인 소스(ArXiv, GitHub, DM Mathematics 등)의 전문가 배정 비율 변화. 초기 레이어에서는 균등하다가 깊은 레이어로 갈수록 도메인별 전문화가 강화되는 패턴을 보인다. 이는 MoE 라우팅이 단순한 부하 분산을 넘어 의미적 전문화를 학습함을 시사한다. (Jiang et al., 2024)*

이러한 전문가 분석 결과들을 종합하면, Mixtral의 MoE 라우팅은 (1) 부하 균형을 전반적으로 잘 유지하면서도 (2) 깊은 레이어에서 도메인과 구문에 따른 부분적 전문화를 자연스럽게 학습하는 이중적 특성을 보여준다.

## 의의 및 한계

### 의의

- **MoE의 오픈소스 실용화**: 대규모 희소 MoE를 오픈 가중치로 공개한 선구적 사례. ST-MoE(Google) 등 이전 MoE 모델들은 가중치가 비공개였다.
- **효율성 패러다임 전환**: "더 큰 모델 = 더 느린 추론" 공식을 깨뜨렸다. 12.9B 활성 파라미터로 70B 밀집 모델을 능가.
- **수학/코드 강점**: GSM8K 74.4, MATH 28.4 등 수학/코드에서의 강점은 전문가 특화 효과를 보여준다.
- **32K 컨텍스트**: Mistral 7B(4K)에서 크게 확장된 긴 문서 처리 능력.
- **Apache 2.0**: 완전한 상업적 자유를 보장하는 라이선스.
- **MoE 연구 촉진**: 이후 DeepSeek-MoE, Qwen2-MoE, DBRX, Grok-1 등 다수의 MoE 모델 개발에 직접적인 영향을 미쳤다.

### 한계

- **높은 메모리 요구**: 추론 연산은 13B 수준이지만 **전체 가중치를 메모리에 올려야** 해서 46.7B 분량의 VRAM이 필요하다. FP16 기준 약 93GB로, 단일 A100 80GB에도 맞지 않는다.
- **전문가 불균형(Load Imbalance)**: 보조 손실로 완화하지만, 특정 도메인의 입력에서 여전히 불균형이 발생할 수 있다. 이는 GPU 활용률 저하로 이어진다.
- **학습 복잡성**: All-to-all 통신으로 인한 분산 학습의 복잡성이 높다. MoE 학습을 위한 인프라 요구사항이 밀집 모델보다 까다롭다.
- **해석 가능성**: 어떤 전문가가 어떤 능력을 담당하는지 명확하게 분석하기 어렵다. 논문에서도 전문가의 전문화가 직관적이지 않음을 보고한다.
- **학습 데이터 비공개**: Mistral 7B와 마찬가지로 학습 데이터 세부 사항이 공개되지 않았다.
- **메모리 대역폭 병목**: 추론 시 활성 파라미터는 적지만, 전문가 선택을 위해 라우터 계산과 전문가 가중치 로딩이 필요하여 메모리 대역폭이 병목이 될 수 있다.

### 후속 발전과 MoE 생태계

Mixtral 이후 MoE 아키텍처는 LLM의 주류 설계 패턴이 되었다:

| 모델 | 시기 | 전체/활성 파라미터 | 특징 |
|------|------|------------------|------|
| Mixtral 8x7B | 2024.01 | 46.7B / 12.9B | Top-2 라우팅 |
| DeepSeek-MoE | 2024.01 | 145B / 22B | Fine-grained 전문가 |
| DBRX | 2024.03 | 132B / 36B | Databricks, 16 전문가 |
| Mixtral 8x22B | 2024.04 | 176B / 39B | 스케일업 |
| DeepSeek-V3 | 2024.12 | 671B / 37B | 보조 손실 없는 균형 |
| Llama 4 | 2025 | MoE 기반 | Meta도 MoE 채택 |

## 코드 예제

### Sparse Mixture of Experts (MoE) FFN 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


class SwiGLUExpert(nn.Module):
    """단일 전문가 FFN (SwiGLU 활성화)."""
    def __init__(self, d_model: int, d_ff: int):
        super().__init__()
        self.w1 = nn.Linear(d_model, d_ff, bias=False)  # gate
        self.w2 = nn.Linear(d_ff, d_model, bias=False)  # down
        self.w3 = nn.Linear(d_model, d_ff, bias=False)  # up

    def forward(self, x):
        return self.w2(F.silu(self.w1(x)) * self.w3(x))


class SparseMoELayer(nn.Module):
    """Mixtral 방식 Sparse MoE FFN.
    각 토큰마다 라우터가 top-k 전문가를 선택하고,
    선택된 전문가의 출력을 가중 합산.

    핵심 수학:
    output(x) = Σ_{i∈TopK} softmax(router(x))_i · Expert_i(x)
    """
    def __init__(self, d_model: int = 4096, d_ff: int = 14336,
                 num_experts: int = 8, top_k: int = 2,
                 balance_coef: float = 0.01):
        super().__init__()
        self.num_experts = num_experts
        self.top_k = top_k
        self.balance_coef = balance_coef

        # 라우터 (게이팅 네트워크): d_model → num_experts
        self.router = nn.Linear(d_model, num_experts, bias=False)

        # 전문가 네트워크 (각각 독립적인 SwiGLU FFN)
        self.experts = nn.ModuleList([
            SwiGLUExpert(d_model, d_ff) for _ in range(num_experts)
        ])

    def forward(self, x: torch.Tensor):
        """x: (batch, seq_len, d_model)"""
        B, T, D = x.shape
        x_flat = x.view(-1, D)  # (B*T, D)
        num_tokens = x_flat.shape[0]

        # 1. 라우팅: 각 토큰마다 전문가 점수 계산
        router_logits = self.router(x_flat)  # (B*T, num_experts)

        # 2. Top-K 선택 + softmax 정규화
        top_k_logits, top_k_indices = torch.topk(
            router_logits, self.top_k, dim=-1
        )  # (B*T, top_k)
        top_k_weights = F.softmax(top_k_logits, dim=-1)  # 가중치 정규화

        # 3. 각 전문가 처리 및 가중 합산
        output = torch.zeros_like(x_flat)
        for expert_idx in range(self.num_experts):
            # 이 전문가를 선택한 토큰 찾기
            # top_k_indices: (B*T, top_k), expert_idx와 일치하는 위치 탐색
            expert_mask = (top_k_indices == expert_idx)  # (B*T, top_k)

            if not expert_mask.any():
                continue

            # 토큰 인덱스와 해당 가중치 추출
            token_indices = expert_mask.any(dim=-1).nonzero(as_tuple=True)[0]
            expert_input = x_flat[token_indices]
            expert_output = self.experts[expert_idx](expert_input)

            # 해당 전문가의 가중치
            weights = top_k_weights[token_indices]
            weight_mask = expert_mask[token_indices]
            expert_weights = (weights * weight_mask.float()).sum(dim=-1, keepdim=True)

            output[token_indices] += expert_weights * expert_output

        # 4. 부하 균형 보조 손실 계산
        self._aux_loss = self._compute_balance_loss(router_logits, top_k_indices)

        return output.view(B, T, D)

    def _compute_balance_loss(self, router_logits, selected_experts):
        """부하 균형 보조 손실.
        모든 전문가가 균등하게 선택되도록 유도.
        L_balance = α · N · Σ_i f_i · p_i
        """
        num_tokens = router_logits.shape[0]
        # f_i: 전문가 i에 할당된 토큰 비율
        expert_counts = torch.zeros(self.num_experts, device=router_logits.device)
        for k in range(self.top_k):
            expert_counts.scatter_add_(
                0, selected_experts[:, k],
                torch.ones(num_tokens, device=router_logits.device)
            )
        f = expert_counts / (num_tokens * self.top_k)

        # p_i: 전문가 i의 평균 라우팅 확률
        p = F.softmax(router_logits, dim=-1).mean(dim=0)

        return self.balance_coef * self.num_experts * (f * p).sum()


# === 테스트 ===
moe = SparseMoELayer(d_model=512, d_ff=1024, num_experts=8, top_k=2)
x = torch.randn(2, 10, 512)
out = moe(x)
print(f"MoE output: {out.shape}")  # (2, 10, 512)
print(f"Balance loss: {moe._aux_loss.item():.4f}")

# 전문가 선택 분포 확인
with torch.no_grad():
    router_logits = moe.router(x.view(-1, 512))
    _, selected = torch.topk(router_logits, 2, dim=-1)
    counts = torch.bincount(selected.view(-1), minlength=8)
print(f"전문가별 활성화 횟수: {counts.tolist()}")
print(f"이상적 분포: 각 {20*2//8}회 (20토큰 × 2 / 8전문가)")

# 파라미터 효율 분석
total_params = sum(p.numel() for p in moe.parameters())
active_params = sum(p.numel() for p in moe.router.parameters())
active_params += sum(p.numel() for p in moe.experts[0].parameters()) * 2  # top-2
print(f"\n전체 파라미터: {total_params:,}")
print(f"활성 파라미터(top-2): {active_params:,}")
print(f"활성 비율: {active_params/total_params*100:.1f}%")
```

> **Mixtral의 핵심 통찰**: 희소 MoE는 "더 큰 파라미터 공간에서 관련된 부분만 선택적으로 활성화"하는 아이디어다. 46.7B의 지식 용량을 가지면서 12.9B의 연산 비용만 소모하여, 70B 밀집 모델과 경쟁하면서 6배 빠른 추론을 달성한다. 이 패러다임은 이후 LLM 설계의 핵심 축이 되었다.

## 관련 문서

- [[mistral-7b|Mistral 7B]] ( 발전 기반
- [[mistral-large-3|Mistral Large 3 / Mistral 3]] ) 후속 모델
- [[deepseek-v2|DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model]] ( 영감을 줌
- [[jamba|Jamba: A Hybrid Transformer-Mamba Language Model]] ) 영감을 줌
