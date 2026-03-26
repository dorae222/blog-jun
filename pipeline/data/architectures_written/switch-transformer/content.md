# Switch Transformer: Top-1 라우팅으로 MoE의 실용성을 입증

## 개요

**Switch Transformer**는 2021년 1월 Google Research가 발표한 Sparse Mixture-of-Experts 모델로, 기존 MoE의 복잡한 라우팅을 **'각 토큰당 하나의 전문가만 선택(Top-1 라우팅)'**으로 단순화해 연산 효율과 확장성을 동시에 달성했다. T5 아키텍처의 FFN 레이어를 N개의 전문가 네트워크로 교체하고, 가벼운 라우터가 각 토큰을 단 하나의 전문가에 할당한다.

동일 FLOP 대비 T5 대비 **학습 속도 7배 향상**, 1.6조 파라미터 Switch-C가 T5-XXL(11B) 대비 **4배 빠른 학습 수렴**을 보였다. 조 단위 파라미터 학습의 실용적 가능성을 처음 입증한 MoE 모델이다.

**참고 논문**: [Switch Transformers: Scaling to Trillion Parameter Models](https://arxiv.org/abs/2101.03961) (Fedus et al., 2021)

## 아키텍처 상세

다음 다이어그램은 Switch Transformer의 전체 아키텍처와 Top-1 MoE 라우팅 메커니즘을 보여준다.

![Switch Transformer 전체 아키텍처 — Top-1 MoE 라우팅, Expert FFN, 보조 로드 밸런싱 손실](figures/architecture.png)
*Figure 1: Switch Transformer 아키텍처 — T5 기반 인코더-디코더 구조에서 FFN을 다수의 Expert로 교체하고, Switch Router가 각 토큰을 Top-1 Expert에 할당한다. (Source: Switch Transformer 논문)*

### Top-1 Switch Routing

기존 MoE(Shazeer et al., 2017)는 Top-2 전문가를 선택했지만, Switch Transformer는 **Top-1만 선택**한다:

$$g_i = \frac{e^{W_r \cdot x}}{\sum_j e^{W_r \cdot x}} \quad \rightarrow \quad \text{expert} = \arg\max_i g_i$$

Top-1 선택의 장점:
- 라우팅 연산량 **절반** 감소
- 구현 단순화
- 통신 비용 감소 (각 토큰이 하나의 전문가 디바이스에만 전송)

### 모델 사양

| 변형 | 전문가 수 | 전체 파라미터 | 활성 파라미터 |
|------|----------|-------------|-------------|
| Switch-Base | 128 | 7B | ~220M |
| Switch-Large | 128 | 26B | ~770M |
| Switch-XXL | 64 | 395B | ~11B |
| **Switch-C** | **2,048** | **1.6T** | ~11B |

아래 그림은 Switch Transformer 인코더 블록의 동작을 구체적으로 보여준다. 각 토큰이 라우터에 의해 독립적으로 하나의 FFN Expert에 할당되는 과정이 시각화되어 있다.

![Switch Transformer 인코더 블록 — 토큰별 독립 라우팅으로 4개 Expert 중 하나를 선택](figures/fig_2.png)
*Figure 2: Switch FFN 레이어 — "More"와 "Parameters" 토큰이 각각 다른 Expert로 라우팅되는 과정. 라우터가 각 토큰에 대해 가장 높은 확률의 Expert를 선택하고, 게이트 값을 곱하여 출력한다. (Source: Switch Transformer 논문)*

### Expert Capacity Buffer

전문가당 처리 가능한 최대 토큰 수를 설정한다:

$$\text{Expert Capacity} = \left(\frac{n}{e}\right) \times \text{capacity\_factor}$$

여기서 $n$은 배치 내 토큰 수, $e$는 전문가 수이다. capacity_factor $\geq 1.0$으로 설정하여 약간의 여유를 확보하며, 용량을 초과하는 토큰은 **잔차 연결(residual connection)으로 패스스루**된다.

다음 그림은 토큰 라우팅 동학과 capacity factor의 역할을 시각화한 것이다. 전문가 간 부하가 불균등할 때 오버플로가 발생하는 문제와 capacity factor로 이를 완화하는 방식을 보여준다.

![토큰 라우팅 동학 — Capacity Factor에 따른 오버플로 처리 방식 비교](figures/fig_3.png)
*Figure 3: 토큰 라우팅과 Capacity Factor — (좌) 기본 설정, (중앙) Capacity Factor 1.0에서 오버플로 발생(빨간 점선), (우) Capacity Factor 1.5에서 여유 슬롯으로 오버플로 완화. (Source: Switch Transformer 논문)*

### 보조 로드 밸런싱 손실

전문가 간 부하를 균등하게 유지하기 위한 보조 손실이다:

$$\mathcal{L}_{\text{aux}} = \alpha \cdot N \cdot \sum_{i=1}^{N} f_i \cdot P_i$$

여기서 $f_i$는 전문가 $i$에 할당된 토큰 비율, $P_i$는 전문가 $i$에 대한 평균 라우팅 확률이다. $\alpha$는 보조 손실 가중치(일반적으로 0.01)이다.

## 핵심 혁신

### 1. MoE 단순화

Top-2에서 Top-1으로의 전환은 단순한 변경처럼 보이지만, MoE 시스템의 복잡도를 대폭 줄이면서 동등 이상의 성능을 달성했다.

### 2. 조 단위 파라미터 실용화

1.6T 파라미터 Switch-C를 TPU 클러스터에서 안정적으로 학습한 것은, 트릴리온 스케일 학습의 실용성을 처음 입증한 것이다.

### 3. T5 프레임워크 활용

기존 T5 아키텍처의 FFN만 전문가로 교체하여, 검증된 인코더-디코더 프레임워크 위에서 MoE를 적용했다.

다음 그래프는 Switch Transformer의 학습 속도 이점을 보여준다. 동일 FLOP 예산에서 Switch-Base 64 Expert 모델이 T5-Base 대비 7배 빠르게 동일 품질에 도달한다.

![Switch Transformer의 학습 속도 이점 — T5 대비 7배 빠른 수렴](figures/fig_5.png)
*Figure 4: 학습 속도 비교 — Switch-Base 64 Expert 모델(녹색)이 T5-Base(보라색) 대비 동일 퍼플렉서티를 1/7 시간에 달성한다. 32개 TPUv3 코어, 동일 FLOP 기준. (Source: Switch Transformer 논문)*

## 벤치마크/성능

| 모델 | 파라미터 | 학습 속도 (vs T5) | SuperGLUE |
|------|---------|-------------------|-----------|
| T5-Base | 220M | 1x | 74.6 |
| Switch-Base | 7B (128 expert) | **7x** | 81.2 |
| T5-XXL | 11B | 1x | 88.9 |
| Switch-XXL | 395B (64 expert) | **4x** | 90.4 |

## 관련 모델 비교

| 특성 | T5 | Switch | GShard | Mixtral |
|------|-----|--------|--------|---------|
| **라우팅** | - | **Top-1** | Top-2 | Top-2 |
| **아키텍처** | Enc-Dec | Enc-Dec | Enc-Dec | **Dec-only** |
| **최대 규모** | 11B | **1.6T** | 600B | 176B |
| **학습 안정성** | 안정 | bf16 필요 | 보통 | 안정 |

## 학습 상세

- **데이터**: C4 (T5와 동일)
- **토크나이저**: SentencePiece 32,100 vocab
- **옵티마이저**: Adafactor
- **배치**: 2,048, 500K 스텝
- **정밀도**: bf16 혼합 정밀도 (학습 안정성 핵심)
- **하드웨어**: 2,048 TPU v3 코어, 각 전문가 별도 코어 배치

## 실무 활용

### 1. 대규모 학습 효율화
동일 FLOP 예산에서 더 큰 모델을 더 빠르게 학습할 수 있어, 연구 기관의 학습 효율을 극대화한다.

### 2. MoE 연구 기반
Top-1 라우팅, 전문가 용량 관리, 부하 균형 등 이후 MoE 연구의 기본 프레임워크를 제공했다.

다국어 사전 학습에서도 Switch Transformer는 강력한 성능을 보인다. 아래 그래프는 101개 언어에 대한 Switch Transformer와 Dense Baseline의 퍼플렉서티 비교이다.

![101개 언어에서 Switch Transformer vs Dense Baseline 퍼플렉서티 비교](figures/fig_7.png)
*Figure 5: 다국어 사전 학습 결과 — 101개 언어 전체에서 Switch Transformer(파란색)가 Dense Baseline(주황색) 대비 일관되게 낮은 퍼플렉서티를 달성한다. (Source: Switch Transformer 논문)*

### 3. 추론 효율화
활성 파라미터가 전체의 일부이므로, 적절한 전문가 병렬화로 추론 비용을 관리할 수 있다.

## 한계 및 전망

### 한계

1. **학습 불안정**: MoE 학습은 Dense 모델보다 불안정하며, bf16 정밀도가 필수적이다.
2. **토큰 드롭**: 전문가 용량 초과 시 토큰이 드롭되어 정보 손실이 발생할 수 있다.
3. **Expert Collapse**: 일부 전문가만 활용되고 나머지가 퇴화하는 현상이 있다.

### 전망

Switch Transformer의 Top-1 라우팅과 부하 균형 전략은 Mixtral, DeepSeek MoE, LLaMA 4 등 이후 MoE 모델들의 기반 기술이 되었다. 특히 DeepSeek-V3의 auxiliary-loss-free 부하 균형은 Switch Transformer의 보조 손실 접근법을 개선한 것이다.

### 어텐션 메커니즘: MHA

Multi-Head Attention(MHA)은 Transformer의 핵심 메커니즘으로, 입력을 여러 헤드로 분할하여 병렬적으로 어텐션을 계산한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O$$

각 헤드는 서로 다른 표현 부분공간(subspace)에서 정보를 추출하며, 결과를 결합하여 풍부한 표현을 학습한다. 추론 시에는 모든 Q 헤드에 대해 별도의 KV를 유지해야 하므로 KV 캐시 비용이 높다는 단점이 있다.
### 실무 코드 예시

```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

model = AutoModelForSeq2SeqLM.from_pretrained("switch-transformer")
tokenizer = AutoTokenizer.from_pretrained("switch-transformer")

# Switch Transformer 추론 예시 (텍스트-투-텍스트)
input_text = "summarize: 인공지능 기술은 최근 급격한 발전을 이루었으며, 특히 대형 언어 모델의 등장으로 자연어 처리 분야에서 혁신적인 변화가 일어나고 있다."
inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
outputs = model.generate(**inputs, max_length=150)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다.

**모델 규모와 효율**: Switch Transformer은 7B (Base) / 26B / 395B / 1.6T 규모의 파라미터를 가지며, 512 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: Switch Transformer은 7B (Base) / 26B / 395B / 1.6T 규모의 파라미터를 가지며, 512 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: Switch Transformer은 7B (Base) / 26B / 395B / 1.6T 규모의 파라미터를 가지며, 512 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: Switch Transformer은 7B (Base) / 26B / 395B / 1.6T 규모의 파라미터를 가지며, 512 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: Switch Transformer은 7B (Base) / 26B / 395B / 1.6T 규모의 파라미터를 가지며, 512 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.

---

**참고 논문**: [Switch Transformers](https://arxiv.org/abs/2101.03961) (Fedus et al., 2021)

## 관련 문서

- [[t5|T5]] — 발전 기반
