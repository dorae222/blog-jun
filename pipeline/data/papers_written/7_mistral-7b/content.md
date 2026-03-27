## 개요

Mistral 7B는 프랑스 AI 스타트업 Mistral AI가 2023년 10월 발표한 7.3B 파라미터 언어 모델이다. 핵심 혁신은 **SWA(Sliding Window Attention)**와 **롤링 버퍼 KV 캐시(Rolling Buffer KV Cache)**로, 긴 시퀀스를 선형 메모리로 처리할 수 있다. 여기에 **GQA(Grouped Query Attention)**을 결합하여 추론 속도를 크게 향상시켰다.

결과적으로 Mistral 7B는 대부분의 평가 벤치마크에서 Llama 2 13B를 능가하는 성능을 **7B라는 작은 크기**에서 달성했다. 특히 MMLU에서 Llama 2 13B를 5.3점 차이로 앞서고, 코드(MBPP)와 수학(GSM8K)에서는 Llama 1 34B까지 능가한다.

Mistral AI는 이 모델을 **Apache 2.0 라이선스**로 공개하여 완전한 상업적 자유를 부여했으며, 이후 Mixtral 8x7B, Mistral Large, Mistral NeMo 등으로 이어지는 Mistral 모델 라인업의 출발점이 되었다. 특히 Mistral AI는 Meta, Google, OpenAI 등 미국 기업 중심의 LLM 생태계에서 유럽 기반 스타트업이 경쟁력 있는 오픈 모델을 제시할 수 있음을 입증했다는 점에서도 주목할 만하다.

다음 아키텍처 다이어그램은 Mistral 7B의 전체 구조와 핵심 설계 요소를 한눈에 보여준다.

![Mistral 7B 전체 아키텍처 다이어그램 ( SWA, GQA, SwiGLU FFN, RoPE, Rolling KV Cache 포함](figures/architecture.png)
*Figure 1: Mistral 7B 아키텍처 개요 ) 32개 Transformer 블록에 Sliding Window Attention + GQA, SwiGLU FFN, Pre-RMSNorm을 적용하고, Rolling KV Cache(윈도우 4096)로 메모리를 고정한다. (Jiang et al., 2023)*

## 배경 및 문제

### 표준 어텐션의 복잡도 문제

Transformer의 표준 Self-Attention은 시퀀스 길이 $n$에 대해 $O(n^2)$의 시간 및 메모리 복잡도를 가진다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right) V$$

이 연산은 $n \times n$ 크기의 어텐션 행렬을 구성해야 하므로, 시퀀스 길이가 4096에서 32768로 8배 늘어나면 메모리는 64배가 필요하다. KV 캐시를 사용하는 자기회귀 생성에서 모든 이전 토큰의 Key-Value를 저장해야 하므로, 긴 시퀀스에서 메모리 소비가 폭발적으로 증가한다:

$$\text{KV 캐시 크기} = 2 \times L \times n \times H \times d_k \times \text{sizeof(dtype)}$$

여기서 $L$은 레이어 수, $H$는 KV 헤드 수다. $n$이 커질수록 캐시가 선형적으로 증가하여 배치 처리가 어려워진다. 예를 들어, 32개 레이어, 32개 헤드, $d_k = 128$인 7B 모델에서 시퀀스 길이 32,768의 KV 캐시는 FP16 기준 약 16 GB에 달하며, 이는 모델 가중치 자체(약 14 GB)보다 더 큰 메모리를 차지한다.

### 작은 모델의 성능 한계

이전까지 7B 규모 모델은 13B 이상 모델에 비해 성능이 뚜렷하게 낮았다. Llama 2-7B와 Llama 2-13B 사이에는 MMLU 기준 약 10점의 격차가 존재했다. 이는 단순히 파라미터 수가 성능을 결정한다는 **스케일링 법칙(Scaling Law)**의 관점에서 자연스러운 결과로 받아들여졌다. 그러나 동일한 파라미터 수에서도 아키텍처 혁신, 학습 데이터 품질 향상, 하이퍼파라미터 최적화를 통해 성능을 극적으로 끌어올릴 수 있다는 가능성이 Chinchilla(Hoffmann et al., 2022) 연구 이후 제기되어 왔다. Mistral 7B는 이러한 가능성을 실증한 대표적 사례이다.

### 긴 시퀀스 처리의 실용적 필요

실제 응용에서는 긴 문서 요약, 코드 분석, 대화 기록 처리 등 수만 토큰의 입력을 다루는 경우가 빈번하다. 표준 어텐션으로는 이를 효율적으로 처리할 수 없으며, 어텐션의 희소성(sparsity)을 활용한 새로운 접근법이 필요했다. 자연어에서 대부분의 토큰은 가까운 이웃 토큰과 가장 강한 어텐션 관계를 맺는다는 관찰(locality of reference)이 이론적 기반이 된다.

### 기존 효율적 어텐션 방법들과의 비교

| 방법 | 핵심 아이디어 | 복잡도 | 한계 |
|------|-------------|--------|------|
| Longformer (2020) | 로컬 + 글로벌 어텐션 | $O(nW)$ | 인코더 중심, 디코더 적용 미비 |
| BigBird (2020) | 로컬 + 랜덤 + 글로벌 | $O(nW)$ | 랜덤 패턴의 불안정성 |
| Flash Attention (2022) | IO-aware 정확 어텐션 | $O(n^2)$ | 근본적 복잡도 미변경 |
| Multi-Query Attention (2019) | KV 헤드 공유 | $O(n^2)$ | 품질 저하 가능 |
| **Mistral SWA** | 윈도우 제한 + 다층 전파 | $O(nW)$ | 디코더에 최적화된 실용적 접근 |

Mistral 7B는 기존 효율적 어텐션 연구들의 핵심 아이디어를 차용하면서도, 대형 디코더 모델에서 **성능 저하 없이** 실용적으로 작동하는 최초의 사례를 만들어냈다.

## 핵심 아이디어

Mistral 7B의 핵심 혁신은 세 가지 기법의 시너지에 있다. Sliding Window Attention으로 어텐션 범위를 제한하고, Rolling Buffer KV Cache로 메모리를 고정시키며, Grouped Query Attention으로 추론 속도를 높인다. 이 세 기법이 독립적으로가 아니라 유기적으로 결합되어 효과를 극대화한다.

### 슬라이딩 윈도우 어텐션 (Sliding Window Attention, SWA)

SWA는 각 토큰이 전체 시퀀스가 아닌 **최근 $W$개의 토큰**에만 어텐션을 수행하도록 제한한다. 이는 Longformer(Beltagy et al., 2020)와 유사한 아이디어지만, Mistral은 이를 대형 디코더 모델에 효율적으로 적용한 최초의 실용적 사례다.

$$\text{SWA}(q_i, K, V) = \text{softmax}\left(\frac{q_i K_{[i-W+1:i]}^\top}{\sqrt{d_k}}\right) V_{[i-W+1:i]}$$

Mistral 7B에서 $W = 4096$을 사용한다. 단일 레이어의 어텐션 범위는 $W$로 제한되지만, 핵심 통찰은 **레이어를 거듭하면서 정보가 전파**된다는 것이다. 다음 그림은 Vanilla Attention과 SWA의 어텐션 행렬을 비교하고, 다층 구조에서 유효 컨텍스트가 확장되는 원리를 보여준다.

![Vanilla Attention과 Sliding Window Attention의 어텐션 행렬 비교 및 다층 구조를 통한 유효 컨텍스트 확장](figures/fig_1.png)
*Figure 2: Vanilla Attention(좌)은 모든 이전 토큰을 참조하여 $O(n^2)$ 복잡도를 가지는 반면, SWA(중)는 윈도우 $W$ 내의 토큰만 참조한다. 우측 다이어그램은 레이어가 쌓일수록 각 토큰의 유효 컨텍스트(receptive field)가 $W \times L$까지 확장되는 과정을 나타낸다. (Jiang et al., 2023)*

#### 정보 전파의 수학적 분석

$l$번째 레이어에서 토큰 $i$의 이론적 정보 접근 범위(receptive field)는:

$$\text{Receptive Field}(i, l) = [\max(0, i - l \cdot W), i]$$

32개 레이어에서 $W=4096$이면, 최상위 레이어의 이론적 접근 범위는:

$$32 \times 4096 = 131{,}072 \text{ 토큰}$$

이는 전체 시퀀스에 대한 어텐션 없이도 매우 긴 범위의 의존성을 캡처할 수 있음을 의미한다. 이 원리는 CNN에서의 receptive field 개념과 유사하다. CNN의 각 레이어가 $k \times k$ 커널로 로컬 패턴을 학습하되, 깊은 레이어에서는 넓은 범위의 패턴을 포착하는 것처럼, SWA도 각 레이어에서 로컬 어텐션을 수행하면서 깊은 레이어로 갈수록 더 먼 토큰의 정보를 간접적으로 수집한다.

물론 이론적 범위와 실질적 정보 전달 사이에는 차이가 있다. 각 레이어를 거칠 때마다 정보의 **감쇠(attenuation)**가 발생하므로, 실질적인 유효 컨텍스트는 이론적 수치보다 작을 수 있다. 그러나 실험적으로 SWA는 대부분의 자연어 태스크에서 전체 어텐션과 유사한 성능을 보이며, 이는 자연어의 대부분의 의존성이 로컬하다는 특성에 기인한다.

#### 복잡도 비교

| 어텐션 방식 | 시간 복잡도 | 공간 복잡도 | KV 캐시 |
|-----------|-----------|-----------|--------|
| 표준 (Full) | $O(n^2 d)$ | $O(n^2)$ | $O(n)$ (증가) |
| SWA | $O(nWd)$ | $O(nW)$ | $O(W)$ (고정) |

$W \ll n$일 때 SWA는 실질적으로 **선형 복잡도**에 가까워진다.

### 롤링 버퍼 KV 캐시 (Rolling Buffer KV Cache)

표준 KV 캐시는 모든 이전 토큰의 KV를 저장하지만, SWA에서는 최근 $W$개만 필요하다. **롤링 버퍼(Rolling Buffer)**는 크기 $W$의 고정 메모리에 위치 인덱스를 순환 방식(circular buffer)으로 덮어쓴다:

$$\text{cache\_k}[i \bmod W] = k_i, \quad \text{cache\_v}[i \bmod W] = v_i$$

이 방식은 운영체제의 원형 버퍼(circular buffer) 자료구조와 동일한 원리를 사용한다. 새로운 토큰이 들어오면 가장 오래된 토큰의 KV를 덮어쓰므로, 추가적인 메모리 할당이나 해제가 필요 없다. 다음 그림은 SWA에서 각 토큰이 참조하는 영역을 Past, Cache, Current로 구분하여, 롤링 버퍼가 어떤 범위의 KV를 유지하는지 직관적으로 보여준다.

![SWA의 Past, Cache, Current 어텐션 영역 구분](figures/fig_4.png)
*Figure 3: SWA에서 현재 토큰이 참조하는 영역을 세 가지로 분류한 도식. Past(노란색)는 이미 윈도우 밖으로 밀려난 토큰으로 더 이상 직접 참조할 수 없고, Cache(주황색)는 롤링 버퍼에 저장된 최근 $W$개의 토큰, Current(빨간색)는 현재 처리 중인 토큰이다. 롤링 버퍼는 Cache 영역만 유지함으로써 메모리를 고정시킨다. (Jiang et al., 2023)*

이를 통해 시퀀스 길이에 무관하게 **KV 캐시 메모리가 $O(W)$로 일정**하게 유지된다.

구체적 메모리 절감 예시:

| 시퀀스 길이 | 표준 캐시 (7B, FP16) | 롤링 버퍼 ($W=4096$) | 절감률 |
|-----------|--------------------|--------------------|-------|
| 4,096 | 2.0 GB | 2.0 GB | 1x |
| 8,192 | 4.0 GB | 2.0 GB | 2x |
| 32,768 | 16.0 GB | 2.0 GB | 8x |
| 131,072 | 64.0 GB | 2.0 GB | 32x |

시퀀스가 길어질수록 절감 효과가 극적으로 커진다. 특히 서빙 환경에서 동시에 여러 요청을 처리할 때, 고정된 KV 캐시 크기는 메모리 예산을 예측 가능하게 만들어 배치 스케줄링을 크게 단순화한다. 다음 그림은 배치 환경에서 롤링 버퍼가 여러 시퀀스에 걸쳐 어떻게 동작하는지를 타임스텝별로 시각화한다.

![롤링 버퍼 KV 캐시의 배치 처리 동작 시각화](figures/fig_3.png)
*Figure 4: 배치 내 서로 다른 길이의 시퀀스 3개에 대해 롤링 버퍼 KV 캐시가 동작하는 방식. 각 타임스텝($i$, $i+1$, $i+2$)에서 새 토큰(빨간색)이 추가되면 슬라이딩 윈도우가 오른쪽으로 이동하며, 윈도우 밖의 오래된 토큰은 캐시에서 자동으로 덮어쓰여진다. 시퀀스 길이가 다르더라도 각 시퀀스의 캐시 크기는 동일하게 $W$로 유지된다. (Jiang et al., 2023)*

### 프리필 청킹 (Chunked Prefill)

프롬프트(prefill)를 한 번에 처리하는 대신 크기 $W$의 청크로 나누어 처리한다. 각 청크는 자신의 토큰과 슬라이딩 윈도우에 있는 이전 청크 토큰에 어텐션한다.

구체적으로, 길이 $T$의 프롬프트가 주어지면 이를 $\lceil T/W \rceil$개의 청크로 분할한다. $j$번째 청크 $C_j$는 토큰 $[jW, (j+1)W)$ 범위를 포함하며, 어텐션 계산 시 $C_j$의 토큰들과 이전 청크 $C_{j-1}$에서 슬라이딩 윈도우에 해당하는 토큰들을 함께 참조한다. 수식으로 표현하면:

$$\text{Prefill}(C_j) = \text{SWA}(Q_{C_j}, K_{C_{j-1} \cup C_j}, V_{C_{j-1} \cup C_j})$$

이 기법의 장점:
1. **메모리 사용량 일정**: 아무리 긴 프롬프트도 $W$ 크기의 청크 단위로 처리하므로 피크 메모리가 일정
2. **GPU 활용률 향상**: 각 청크의 크기가 일정하여 GPU 연산 파이프라인이 효율적
3. **파이프라이닝 가능**: 한 청크의 어텐션 계산과 다음 청크의 프로젝션을 병렬 수행
4. **긴 프롬프트 지원**: 프롬프트 길이가 GPU 메모리를 초과하는 경우에도 처리 가능

### Grouped Query Attention (GQA)

SWA와 함께 GQA를 적용한다. GQA는 Multi-Head Attention(MHA)과 Multi-Query Attention(MQA) 사이의 중간 지점으로, 여러 쿼리 헤드가 하나의 KV 헤드를 공유하는 방식이다. Mistral 7B는 32개의 쿼리 헤드를 8개의 KV 헤드 그룹으로 나눈다($\text{ratio} = 4$). 이는 KV 캐시 크기를 추가로 4배 줄이고 추론 속도를 향상시킨다.

| 어텐션 방식 | 쿼리 헤드 | KV 헤드 | KV 캐시 비율 | 품질 |
|-----------|----------|---------|-------------|------|
| MHA | 32 | 32 | 1x | 최고 |
| GQA (Mistral) | 32 | 8 | 0.25x | 약간 저하 |
| MQA | 32 | 1 | 0.03x | 눈에 띄는 저하 |

GQA는 MQA보다 품질 저하가 적으면서도 상당한 메모리 절감을 달성하는 실용적 균형점이다.

SWA와 GQA의 결합 효과:

$$\text{최종 KV 캐시} = 2 \times L \times W \times G \times d_k \times \text{sizeof(dtype)}$$

표준 어텐션 + MHA 대비:
$$\text{절감률} = \frac{n}{W} \times \frac{H}{G}$$

$n=32768, W=4096, H=32, G=8$이면 절감률은 $8 \times 4 = 32$배다.

## 방법론

### 모델 구성

| 항목 | Mistral 7B | Llama 2-7B | 비고 |
|------|-----------|-----------|------|
| 파라미터 수 | 7.3B | 6.7B | Mistral이 약간 큼 |
| 레이어 수 | 32 | 32 | 동일 |
| 쿼리 헤드 수 | 32 | 32 | 동일 |
| KV 헤드 수 | 8 (GQA) | 32 (MHA) | 핵심 차이 |
| 히든 차원 | 4096 | 4096 | 동일 |
| FFN 차원 | 14336 | 11008 | +30% 증가 |
| 슬라이딩 윈도우 | 4096 | N/A (Full) | 핵심 차이 |
| 어휘 크기 | 32000 | 32000 | 동일 |
| 활성화 함수 | SwiGLU | SwiGLU | 동일 |
| 위치 인코딩 | RoPE | RoPE | 동일 |
| 정규화 | RMSNorm | RMSNorm | 동일 |

주목할 점은 FFN 차원이 14336으로 Llama 2-7B(11008)보다 약 30% 크다는 것이다. SwiGLU 활성화 함수는 게이트 메커니즘을 위해 3개의 가중치 행렬($W_{gate}, W_{up}, W_{down}$)을 사용하므로, FFN 차원의 증가는 유효 파라미터 수에 큰 영향을 미친다. 구체적으로 SwiGLU FFN의 연산은 다음과 같다:

$$\text{SwiGLU}(x) = (\text{Swish}(xW_{gate}) \odot xW_{up}) W_{down}$$

여기서 $W_{gate}, W_{up} \in \mathbb{R}^{d \times d_{ff}}$, $W_{down} \in \mathbb{R}^{d_{ff} \times d}$이다. FFN 차원이 14336이면 각 레이어의 FFN 파라미터는 $3 \times 4096 \times 14336 \approx 176M$으로, Llama 2-7B의 $3 \times 4096 \times 11008 \approx 135M$보다 약 30% 더 많다. 이 추가 용량이 성능 향상의 주요 요인 중 하나로 분석된다.

### 파인튜닝 변형

- **Mistral 7B Instruct**: 공개 데이터셋으로 지도 파인튜닝(SFT)된 명령 따르기 버전. DPO(Direct Preference Optimization)도 적용되어 인간 선호도에 더 잘 맞는 응답을 생성한다.

### 학습 데이터

논문에서 학습 데이터의 세부 구성은 공개하지 않았다. 이는 Mistral AI의 주요 비판점 중 하나로, 완전한 투명성을 추구하는 OLMo나 Dolma 프로젝트와 대조를 이룬다. 다만 토큰 수와 데이터 소스에 대한 일부 힌트에 따르면, 웹 크롤링, 코드, 학술 논문 등 다양한 소스를 활용한 것으로 추정된다. 일부 분석에서는 Mistral 7B의 코드 및 수학 벤치마크에서의 뛰어난 성능이 학습 데이터에서 코드와 수학 관련 데이터의 비중이 높았음을 시사한다고 지적한다.

## 실험 결과

### 주요 벤치마크 비교

Mistral 7B의 가장 인상적인 결과는 7B라는 소형 규모로 자신보다 2배~5배 큰 모델들을 전방위로 능가한다는 점이다. 다음 그림은 MMLU, Knowledge, Reasoning, Comprehension, Math, Code 등 주요 카테고리에서 Mistral 7B와 Llama 모델 간의 벤치마크 성능을 비교한다.

![Mistral 7B와 Llama 모델 간 벤치마크 성능 비교](figures/fig_5.png)
*Figure 5: MMLU, Knowledge, Reasoning, Comprehension(좌측)과 AGI Eval, Math, BBH, Code(우측) 카테고리별 성능 비교. Mistral 7B(주황색)가 Llama 2 7B(빨간색)는 물론 Llama 2 13B(하늘색), Llama 1 34B(초록색)까지 대부분의 벤치마크에서 능가한다. 특히 Math와 Code 영역에서의 격차가 두드러진다. (Jiang et al., 2023)*

| 모델 | 파라미터 | MMLU | HellaSwag | WinoGrande | ARC-e | ARC-c | MBPP | GSM8K |
|------|---------|------|-----------|------------|-------|-------|------|-------|
| Llama 2-7B | 6.7B | 45.3 | 77.2 | 69.2 | 76.1 | 46.2 | 20.8 | 14.6 |
| Llama 2-13B | 13.0B | 54.8 | 81.9 | 72.0 | 79.4 | 48.8 | 30.2 | 28.7 |
| Llama 1-34B | 32.5B | 55.8 | 82.6 | 76.0 | 79.0 | 50.9 | 37.4 | 35.6 |
| **Mistral 7B** | **7.3B** | **60.1** | **81.3** | **75.3** | **80.0** | **55.5** | **40.2** | **52.1** |

핵심 결과:
- **MMLU 60.1**: Llama 2 13B(54.8)를 5.3점 차이로 능가, Llama 1 34B(55.8)도 초과
- **MBPP 40.2**: 코드 생성에서 Llama 1 34B(37.4)보다 높음
- **GSM8K 52.1**: 수학에서 Llama 2 13B(28.7)의 거의 2배
- **ARC-c 55.5**: 추론 능력에서 Llama 1 34B(50.9)를 4.6점 차이로 앞섬

이 결과는 단순히 파라미터 수를 늘리는 것보다 아키텍처 혁신과 데이터 품질이 성능에 더 큰 영향을 미칠 수 있음을 시사한다. 특히 수학(GSM8K)에서의 압도적 성능 차이는 학습 데이터 구성의 영향이 클 것으로 추정된다.

이러한 성능 격차를 보다 직관적으로 표현한 것이 다음 그림이다. Mistral 7B의 성능이 Llama 2의 어느 규모에 해당하는지를 벤치마크별로 보여주어, 아키텍처 효율성의 의미를 한눈에 파악할 수 있다.

![Mistral 7B의 성능에 대응하는 Llama 2 동등 모델 크기](figures/fig_6.png)
*Figure 6: 벤치마크 카테고리별로 Mistral 7B와 동등한 성능을 내기 위해 필요한 Llama 2의 모델 크기를 나타낸 그래프. MMLU에서는 Llama 2 23B(3.3배), Reasoning에서는 Llama 2 38B(5.4배), Knowledge에서는 13B(1.9배), Comprehension에서는 21B(3배)에 해당하는 성능을 7B 규모에서 달성한다. 이는 Mistral 7B의 아키텍처 효율성이 단순한 모델 크기 증가 대비 3~5배의 파라미터 효율을 제공함을 의미한다. (Jiang et al., 2023)*

### 카테고리별 성능 분석

| 카테고리 | 벤치마크 | Mistral 7B | Llama 2-13B | 차이 |
|---------|---------|-----------|-------------|------|
| 상식 추론 | HellaSwag, WinoGrande, PIQA 등 평균 | 75.8 | 74.6 | +1.2 |
| 세계 지식 | NaturalQuestions, TriviaQA | 62.5 | 61.7 | +0.8 |
| 독해 | BoolQ, QuAC | 79.3 | 79.0 | +0.3 |
| 수학 | GSM8K, MATH | 52.1 | 28.7 | +23.4 |
| 코드 | HumanEval, MBPP | 30.5 | 24.3 | +6.2 |

수학과 코드에서의 격차가 특히 두드러진다. 상식 추론, 세계 지식, 독해와 같은 언어 이해 태스크에서는 13B 모델과 비등하거나 약간 앞서는 수준이지만, 논리적 추론이 필요한 수학과 코드 태스크에서는 압도적인 차이를 보인다.

### 추론 효율 분석

슬라이딩 윈도우 어텐션과 롤링 버퍼 덕분에 실제 서빙 환경에서 상당한 효율 향상을 달성한다:

| 지표 | 표준 어텐션 (Full) | SWA + Rolling Buffer | 개선 |
|------|-------------------|---------------------|------|
| 16K 토큰 추론 지연 | 1.0x (기준) | 0.6x | 40% 감소 |
| 32K 토큰 KV 메모리 | 16.0 GB | 2.0 GB | 8x 절감 |
| 최대 배치 크기 (A100 80GB) | 4 | 16+ | 4x 이상 |
| 처리량 (tok/s) | 1.0x | 1.8x | 80% 향상 |

특히 배치 처리에서의 효과가 크다. KV 캐시 메모리가 고정되므로 남는 GPU 메모리를 더 큰 배치에 할당할 수 있으며, 이는 서빙 비용 절감으로 직결된다.

### Mistral 7B Instruct 성능

| 비교 대상 | MT-Bench | 정렬 방법 | 비고 |
|---------|---------|----------|------|
| Llama 2 7B Chat | 6.27 | SFT + RLHF | PPO 기반 |
| Llama 2 13B Chat | 6.65 | SFT + RLHF | PPO 기반 |
| **Mistral 7B Instruct** | **6.84** | SFT + DPO | RLHF 없음 |

Mistral 7B Instruct는 RLHF 파이프라인 없이 SFT와 DPO만으로도 RLHF를 적용한 Llama 2 Chat 모델들보다 높은 대화 품질을 보인다. 이는 강화학습 기반 정렬(RLHF)의 복잡한 파이프라인 없이도 DPO와 같은 직접적 최적화 방법이 효과적일 수 있음을 시사한다.

아래 그림은 실제 사용자 평가 환경에서 Mistral 7B Instruct가 LLaMA 2 13B Chat과 직접 비교된 결과를 보여준다. 동일한 질문에 대해 두 모델의 응답을 나란히 비교하면 Mistral 7B Instruct의 응답 품질 우위를 확인할 수 있다.

![Mistral 7B Instruct와 LLaMA 2 13B Chat의 실제 대화 품질 비교](figures/fig_9.png)
*Figure 7: Chatbot Arena 스타일의 블라인드 평가에서 Mistral 7B Instruct v0.1과 LLaMA 2 13B Chat의 응답 비교. 7B 규모의 Mistral Instruct가 거의 2배 큰 LLaMA 2 13B Chat을 상대로 승리하며, SFT + DPO 정렬 전략의 효과를 실증한다. (Jiang et al., 2023)*

## 의의 및 한계

### 의의

- **SWA 실용화**: 슬라이딩 윈도우 어텐션을 대형 디코더 모델에 성공적으로 적용한 최초의 실용적 사례. Longformer 등에서 제안된 이론적 아이디어를 실제 성능 향상으로 연결했다.
- **소형 모델의 성능 한계 돌파**: 7B 모델이 13B~34B를 능가하는 새 기준을 수립했다. 이는 모델 크기만이 성능의 결정 요인이 아님을 입증한다.
- **효율성과 성능의 균형**: 실제 배포 환경에서 뛰어난 처리량을 제공하며, 단일 GPU(A100 40GB)에서도 FP16으로 추론이 가능하다.
- **Apache 2.0 완전 개방**: 어떤 제약도 없는 완전한 오픈소스 라이선스로 상업적 자유를 보장했다. 이는 Meta의 Llama 2 커뮤니티 라이선스보다 더 개방적이다.
- **Mixtral 기반 마련**: 이후 MoE 기반 Mixtral 8x7B, Mistral Large, Mistral NeMo 등으로 발전하는 기반을 마련했다.
- **유럽 AI 생태계**: 미국과 중국 중심의 LLM 연구에서 유럽(프랑스)의 경쟁력을 보여준 상징적 모델이다.
- **산업 표준 영향**: SWA와 GQA의 조합은 이후 많은 오픈 모델들이 채택하는 사실상의 표준이 되었다.

### 한계

- **긴 범위 의존성 약화**: 이론적으로 $W \times L$ 범위의 정보에 접근 가능하지만, 실제로는 SWA로 인해 매우 먼 토큰 간 의존성이 점차 약화된다. 이는 긴 문서 내 특정 사실을 참조하는 needle-in-a-haystack 유형의 태스크에서 한계로 나타날 수 있다. 후속 모델인 Mistral Large 2에서는 128K 컨텍스트를 지원하며 이 한계를 일부 극복했다.
- **정렬 부족**: Mistral 7B 베이스는 SFT만 적용되어 RLHF 기반 모델 대비 안전성 정렬이 제한적이다. Instruct 버전도 DPO 수준의 기본적인 정렬만 적용되었다.
- **학습 데이터 비공개**: 사전학습 데이터의 구성, 규모, 필터링 방법이 공개되지 않아 재현 불가능하다. "오픈 가중치(open weight)"이지 "오픈 소스(open source)"가 아니라는 비판이 있다.
- **다국어 제한**: 영어 중심으로 학습되어 한국어, 중국어 등 비영어 언어에서의 성능이 제한적이다.
- **윈도우 크기 선택의 딜레마**: $W=4096$은 경험적으로 설정된 값이며, 태스크에 따라 최적 윈도우 크기가 달라질 수 있다. 윈도우가 너무 작으면 중요한 장거리 의존성을 놓치고, 너무 크면 효율성 이점이 감소한다.
- **Ablation 부재**: 논문에서 SWA, GQA, 데이터 구성 등 각 요소의 개별 기여도를 분리하는 ablation study를 제공하지 않아, 성능 향상의 정확한 원인을 파악하기 어렵다.

### 후속 발전

| 모델 | 시기 | 파라미터 | 특징 |
|------|------|---------|------|
| Mixtral 8x7B | 2024.01 | 46.7B/12.9B 활성 | MoE, 8개 전문가 중 2개 활성 |
| Mistral Large | 2024.02 | 비공개 | 상용 API, GPT-4 경쟁 |
| Mistral NeMo | 2024.07 | 12B | NVIDIA 협업, Tekken 토크나이저 |
| Mistral Large 2 | 2024.07 | 123B | 128K 컨텍스트, 함수 호출 |
| Pixtral | 2024.09 | 12B | 비전-언어 멀티모달 |
| Mistral Small | 2024.09 | 22B | 비용 효율적 중형 모델 |

## 코드 예제

### Sliding Window Attention + Rolling Buffer KV Cache 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class RollingBufferKVCache:
    """Mistral 7B의 Rolling Buffer KV Cache.
    고정 크기 W의 원형 버퍼로 KV를 저장.
    시퀀스 길이에 무관하게 O(W) 메모리 유지.
    """
    def __init__(self, window_size: int, num_heads: int, head_dim: int,
                 dtype=torch.float16, device='cpu'):
        self.window_size = window_size
        self.cache_k = torch.zeros(1, num_heads, window_size, head_dim,
                                   dtype=dtype, device=device)
        self.cache_v = torch.zeros(1, num_heads, window_size, head_dim,
                                   dtype=dtype, device=device)
        self.pos = 0  # 현재까지 삽입된 토큰 수

    def update(self, k: torch.Tensor, v: torch.Tensor):
        """새 KV를 Rolling Buffer에 추가.
        오래된 항목은 자동으로 덮어쓰기.
        """
        seq_len = k.shape[2]
        for i in range(seq_len):
            idx = (self.pos + i) % self.window_size  # 원형 버퍼 인덱스
            self.cache_k[:, :, idx:idx+1, :] = k[:, :, i:i+1, :]
            self.cache_v[:, :, idx:idx+1, :] = v[:, :, i:i+1, :]
        self.pos += seq_len

        # 현재까지 유효한 캐시 범위 반환
        valid_len = min(self.pos, self.window_size)
        if self.pos <= self.window_size:
            return self.cache_k[:, :, :valid_len, :], self.cache_v[:, :, :valid_len, :]
        return self.cache_k, self.cache_v

    @property
    def memory_usage_mb(self):
        """캐시 메모리 사용량 (MB)."""
        return (self.cache_k.numel() + self.cache_v.numel()) * 2 / 1e6  # FP16


class GroupedQueryAttention(nn.Module):
    """Grouped Query Attention (GQA).
    32개 쿼리 헤드, 8개 KV 헤드 (4:1 비율).
    SWA와 결합하여 KV 캐시를 추가로 4배 절감.
    """
    def __init__(self, d_model: int = 4096, n_heads: int = 32,
                 n_kv_heads: int = 8, window_size: int = 4096):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.n_groups = n_heads // n_kv_heads  # 4
        self.head_dim = d_model // n_heads
        self.window_size = window_size

        self.wq = nn.Linear(d_model, n_heads * self.head_dim, bias=False)
        self.wk = nn.Linear(d_model, n_kv_heads * self.head_dim, bias=False)
        self.wv = nn.Linear(d_model, n_kv_heads * self.head_dim, bias=False)
        self.wo = nn.Linear(n_heads * self.head_dim, d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, D = x.shape

        q = self.wq(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.wk(x).view(B, T, self.n_kv_heads, self.head_dim).transpose(1, 2)
        v = self.wv(x).view(B, T, self.n_kv_heads, self.head_dim).transpose(1, 2)

        # KV 헤드를 쿼리 헤드 수에 맞춰 반복 확장
        k = k.repeat_interleave(self.n_groups, dim=1)  # (B, 32, T, D)
        v = v.repeat_interleave(self.n_groups, dim=1)  # (B, 32, T, D)

        # Sliding Window Attention 적용
        output = sliding_window_attention(q, k, v, self.window_size)
        output = output.transpose(1, 2).contiguous().view(B, T, -1)
        return self.wo(output)


def sliding_window_attention(
    Q: torch.Tensor, K: torch.Tensor, V: torch.Tensor,
    window_size: int = 4096
) -> torch.Tensor:
    """Sliding Window Attention (Mistral 7B 방식).
    각 토큰은 이전 window_size개의 토큰만 참조.

    복잡도: O(n*W*d) 시간, O(n*W) 공간
    표준 어텐션 대비: O(n^2*d) -> O(n*W*d), W << n일 때 큰 절감.

    Args:
        Q, K, V: (batch, heads, seq_len, head_dim)
        window_size: 각 토큰이 볼 수 있는 이전 토큰 수
    """
    B, H, T, D = Q.shape
    scale = math.sqrt(D)

    # 효율적 구현: 밴드 마스크로 전체 어텐션 행렬에서 윈도우 외 부분 마스킹
    # 실제 Mistral은 커스텀 CUDA 커널을 사용하지만, 여기서는 마스크 기반으로 구현
    scores = torch.matmul(Q, K.transpose(-2, -1)) / scale  # (B, H, T, T)

    # 슬라이딩 윈도우 + causal mask 생성
    row_idx = torch.arange(T, device=Q.device).unsqueeze(1)  # (T, 1)
    col_idx = torch.arange(T, device=Q.device).unsqueeze(0)  # (1, T)
    # causal: col <= row, window: col > row - window_size
    mask = (col_idx <= row_idx) & (col_idx > row_idx - window_size)

    scores = scores.masked_fill(~mask.unsqueeze(0).unsqueeze(0), float('-inf'))
    attn = F.softmax(scores, dim=-1)
    output = torch.matmul(attn, V)

    return output


# === 데모: SWA + GQA + Rolling Buffer 통합 ===
B, H, T, D = 1, 8, 64, 64
W = 16  # 짧은 윈도우로 데모

Q = torch.randn(B, H, T, D)
K = torch.randn(B, H, T, D)
V = torch.randn(B, H, T, D)

# SWA 출력
out_swa = sliding_window_attention(Q, K, V, window_size=W)
print(f"SWA output shape: {out_swa.shape}")  # (1, 8, 64, 64)

# 정보 전파 범위 계산
num_layers = 32
effective_context = num_layers * W
print(f"\n--- 정보 전파 분석 ---")
print(f"단일 레이어 어텐션 범위: {W} 토큰")
print(f"32 레이어 이론적 범위: {effective_context:,} 토큰")
print(f"이는 약 {effective_context * 4 // 1000}K 단어에 해당")

# Rolling Buffer KV Cache 데모
print(f"\n--- Rolling Buffer KV Cache ---")
cache = RollingBufferKVCache(window_size=16, num_heads=8, head_dim=64)
print(f"고정 캐시 메모리: {cache.memory_usage_mb:.2f} MB")

# 긴 시퀀스 시뮬레이션
for step in range(100):
    new_k = torch.randn(1, 8, 1, 64, dtype=torch.float16)
    new_v = torch.randn(1, 8, 1, 64, dtype=torch.float16)
    cached_k, cached_v = cache.update(new_k, new_v)

print(f"100 스텝 후 캐시 크기: {cached_k.shape}")  # (1, 8, 16, 64) - 항상 고정!
print(f"메모리는 시퀀스 길이에 무관하게 일정: {cache.memory_usage_mb:.2f} MB")

# GQA 모듈 데모
print(f"\n--- Grouped Query Attention ---")
gqa = GroupedQueryAttention(d_model=256, n_heads=8, n_kv_heads=2, window_size=16)
x = torch.randn(1, 32, 256)
out = gqa(x)
print(f"GQA output shape: {out.shape}")  # (1, 32, 256)
print(f"쿼리 헤드: {gqa.n_heads}, KV 헤드: {gqa.n_kv_heads}, 그룹 비율: {gqa.n_groups}:1")
print(f"KV 캐시 절감: {gqa.n_heads // gqa.n_kv_heads}x")
```

> **Mistral 7B의 핵심 혁신**: Sliding Window Attention은 각 레이어의 어텐션 범위를 $W$로 제한하되, 다층 구조를 통해 $W \times L$까지 정보를 전파한다. Rolling Buffer KV Cache는 시퀀스 길이에 무관한 고정 메모리 사용을 실현한다. GQA와의 결합으로 7B 모델이 13B~34B 모델을 능가하는 효율-성능의 새로운 패러다임을 제시했다.

## 관련 문서

- [[mixtral|Mixtral of Experts]] -- 후속 모델
- [[pixtral|Pixtral]] -- 후속 모델
- [[llama|LLaMA: Open and Efficient Foundation Language Models]] -- 영감
