<!-- infographic-hero -->
![mT5 핵심 요약](figures/infographic.svg)

*Figure: mT5 한 장 요약 인포그래픽*

# mT5

**Google Research** · **2021-01-05** · **Encoder-Decoder** · **Dense** · **오픈소스**

## 개요

mT5(Multilingual T5)는 2021년 Google Research가 발표한 T5의 다국어 확장 버전으로, 영어 전용 C4 대신 101개 언어를 포함하는 mC4(Multilingual C4) 데이터셋으로 사전 학습했다. T5의 텍스트-투-텍스트 통합 프레임워크와 스팬 노이즈 제거 목표를 그대로 유지하면서, 250,112개 토큰의 대용량 SentencePiece vocab으로 다국어 토크나이징 능력을 대폭 강화했다. XTREME·XNLI·TyDi QA 등 다국어 벤치마크에서 mBERT와 XLM-R을 능가하며 당시 최고 수준의 다국어 성능을 달성했다. 비영어권 NLP 연구의 표준 베이스라인으로 널리 활용된다.

![mT5 아키텍처 - 101개 언어 지원 Encoder-Decoder 구조의 다국어 텍스트-투-텍스트 모델](figures/architecture.svg)

*Figure 1: mT5 아키텍처 - T5의 Encoder-Decoder 구조와 스팬 노이즈 제거 목표를 유지하면서, 250K vocab SentencePiece와 mC4 다국어 코퍼스로 101개 언어를 지원한다.*

## 아키텍처 상세

mC4 데이터셋: Common Crawl에서 101개 언어 텍스트를 정제한 6.4TB 규모의 다국어 코퍼스. 언어별 샘플링은 온도 기반 가중 샘플링(temperature T=1000)을 사용해 저자원 언어도 일정 비율로 학습. 어휘: SentencePiece unigram LM 250,112 vocab(T5의 32,100 대비 약 8배)으로 101개 언어의 문자 체계를 포괄. T5와 동일한 스팬 노이즈 제거 사전 학습 목표 유지. 파인튜닝 시 영어 데이터만으로 학습해도 다른 언어로 제로샷 전이가 가능한 크로스-링구얼 전이(cross-lingual transfer) 능력을 보유한다.

## 모델 사양

| 항목 | 값 |
|------|---|
| 파라미터 | 300M (Small) / 580M (Base) / 1.2B (Large) / 3.7B (XL) / 13B (XXL) |
| 컨텍스트 길이 | 512 (input) / 128 (output default) |
| 어텐션 | MHA (Relative Attention Bias) |
| 정규화 | RMSNorm (Pre-Norm) |
| 활성화 | ReLU (FFN) |
| 위치 인코딩 | Relative Attention Bias |
| 어휘 크기 | 250112 |
| 히든 차원 | 512 (Small) / 768 (Base) / 1024 (Large) / 2048 (XL) / 4096 (XXL) |
| 레이어 수 | 8 (Small) / 12 (Base) / 24 (Large) / 24 (XL) / 24 (XXL) |
| 어텐션 헤드 | 6 (Small) / 12 (Base) / 16 (Large) / 32 (XL) / 64 (XXL) |

### 핵심 개념

- **Multilingual**
- **mC4 Dataset**
- **Cross-lingual Transfer**
- **Temperature Sampling**
- **Large Vocabulary**

## 학습

mC4(6.4TB, 101개 언어). SentencePiece unigram LM 250,112 vocab. Adafactor optimizer. 배치 1M 토큰, 1M 스텝. 온도 가중 샘플링으로 저자원 언어 과샘플링. 256~1024 TPU v3 코어. Small부터 XXL까지 5가지 크기 공개.

### 관련 모델

- **t5** - 변형

### 어텐션 메커니즘: MHA

Multi-Head Attention(MHA)은 Transformer의 핵심 메커니즘으로, 입력을 여러 헤드로 분할하여 병렬적으로 어텐션을 계산한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O$$

각 헤드는 서로 다른 표현 부분공간(subspace)에서 정보를 추출하며, 결과를 결합하여 풍부한 표현을 학습한다. 추론 시에는 모든 Q 헤드에 대해 별도의 KV를 유지해야 하므로 KV 캐시 비용이 높다는 단점이 있다.
### 실무 코드 예시

```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

model = AutoModelForSeq2SeqLM.from_pretrained("mt5")
tokenizer = AutoTokenizer.from_pretrained("mt5")

# mT5 추론 예시 (텍스트-투-텍스트)
input_text = "summarize: 인공지능 기술은 최근 급격한 발전을 이루었으며, 특히 대형 언어 모델의 등장으로 자연어 처리 분야에서 혁신적인 변화가 일어나고 있다."
inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
outputs = model.generate(**inputs, max_length=150)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

다음 그림은 mC4 데이터셋의 언어별 페이지 수와 샘플링 비율 간의 관계를 보여준다.

![mC4 데이터셋의 언어별 분포와 샘플링 비율](figures/fig_1.png)
*Figure 2: mC4 언어별 페이지 수(왼쪽 축)와 샘플링 지수에 따른 학습 비율(오른쪽 축) - 최종 모델은 alpha=0.3을 사용하여 저자원 언어의 과소표현 문제를 완화한다. (Source: Xue et al., 2021)*

모델 규모가 커질수록 제로샷 크로스-링구얼 전이 능력이 향상되는 것을 다음 그림에서 확인할 수 있다.

![TyDi QA 태스크에서의 모델 크기별 성능 비교](figures/fig_2.png)
*Figure 3: TyDi QA GoldP 태스크의 평균 F1 - 모델 규모가 커질수록 Zero-Shot 성능이 In-Language Multitask에 수렴하여, 대형 모델에서 크로스-링구얼 전이의 효과가 극대화됨을 보여준다. (Source: Xue et al., 2021)*

## 핵심 혁신

### 1. Multilingual

다국어 지원은 여러 언어에 대한 통합 표현 공간을 형성하여 크로스-링구얼 전이를 가능하게 한다. 대규모 어휘와 온도 기반 샘플링으로 저자원 언어에 대한 성능도 확보하며, 한 언어에서 학습한 태스크 지식이 다른 언어로 자연스럽게 전이되는 제로샷 크로스-링구얼 전이가 핵심 능력이다.

### 2. mC4 Dataset

mC4(Multilingual C4)는 Common Crawl에서 101개 언어 텍스트를 정제한 6.4TB 규모의 다국어 코퍼스이다. 언어별 샘플링은 온도 기반 가중 샘플링을 사용하여 저자원 언어도 일정 비율로 학습에 포함시키며, 다국어 LLM 학습의 표준 데이터셋으로 자리잡았다.

### 3. Cross-lingual Transfer

크로스-링구얼 전이는 한 언어(주로 영어)에서 학습한 태스크 지식이 다른 언어로 자연스럽게 전이되는 능력이다. 다국어 사전 학습을 통해 공유 표현 공간이 형성될 때 발생하며, 영어 파인튜닝만으로 다른 언어에서도 태스크 수행이 가능해진다.

### 4. Temperature Sampling

온도 기반 샘플링은 데이터 분포를 온도 파라미터로 조절하는 기법이다. $p_l \propto |D_l|^{1/T}$ 형태로, 높은 온도는 저자원 언어의 비율을 높여 균등한 다국어 학습을 촉진한다. 너무 높은 온도는 고자원 언어의 학습을 저해할 수 있으므로 최적 온도 탐색이 중요하다.


## 벤치마크/성능

mT5은 Multilingual, mC4 Dataset, Cross-lingual Transfer 분야에서 동급 모델 대비 경쟁력 있는 성능을 보인다.


## 실무 활용

### 1. 파인튜닝 베이스 모델
mT5은 오픈소스로 공개되어 LoRA, QLoRA 등의 PEFT 기법을 활용한 도메인 특화 파인튜닝이 가능하다. 의료, 법률, 금융 등 특정 도메인의 데이터로 미세조정하면 전문적인 AI 어시스턴트를 구축할 수 있다.

### 2. 추론 배포
mT5은 다양한 추론 프레임워크(vLLM, TGI, ONNX Runtime 등)에서 지원되며, 양자화(GPTQ, AWQ, GGUF)를 통해 엣지 디바이스에서도 실행할 수 있다.

### 3. 연구 베이스라인
mT5은 Multilingual, mC4 Dataset 연구의 표준 베이스라인으로 활용된다.

## 한계 및 전망

### 한계

1. **배포 인프라**: 300M (Small) / 580M (Base) / 1.2B (Large) / 3.7B (XL) / 13B (XXL) 규모의 모델은 충분한 GPU 인프라가 필요하다.
2. **학습 데이터 편향**: 사전 학습 데이터의 특성에 따라 특정 도메인이나 언어에서 편향이 존재할 수 있다.
3. **환각(Hallucination)**: 모든 언어 모델과 마찬가지로 사실이 아닌 정보를 자신 있게 생성할 수 있으며, 사실 검증 메커니즘이 필요하다.

### 전망

mT5은 Multilingual, mC4 Dataset, Cross-lingual Transfer 분야에서의 강점을 바탕으로, 향후 더 발전된 후속 모델이나 특화된 변형 모델로 진화할 것으로 예상된다. 데이터 품질 개선과 효율적 학습 기법의 발전이 핵심 연구 방향이다.
### 스케일링 법칙과의 관계

Chinchilla 스케일링 법칙에 따르면, 모델 파라미터 수 $N$과 학습 토큰 수 $D$의 최적 비율은 다음과 같이 결정된다:

$$L(N, D) = \frac{A}{N^\alpha} + \frac{B}{D^\beta} + E$$

여기서 $\alpha \approx 0.34$, $\beta \approx 0.28$이다. 이 법칙은 학습 예산이 주어졌을 때 모델 크기와 데이터 양의 최적 균형점을 결정하는 데 핵심적인 역할을 하며, 이 모델의 학습 전략에도 영향을 미쳤을 것으로 추정된다.

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: mT5은 300M (Small) / 580M (Base) / 1.2B (Large) / 3.7B (XL) / 13B (XXL) 규모의 파라미터를 가지며, 512 (input) / 128 (output default) 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: mT5은 300M (Small) / 580M (Base) / 1.2B (Large) / 3.7B (XL) / 13B (XXL) 규모의 파라미터를 가지며, 512 (input) / 128 (output default) 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: mT5은 300M (Small) / 580M (Base) / 1.2B (Large) / 3.7B (XL) / 13B (XXL) 규모의 파라미터를 가지며, 512 (input) / 128 (output default) 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: mT5은 300M (Small) / 580M (Base) / 1.2B (Large) / 3.7B (XL) / 13B (XXL) 규모의 파라미터를 가지며, 512 (input) / 128 (output default) 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.

## 참고 자료

- [논문](https://arxiv.org/abs/2010.11934)
- [코드](https://github.com/google-research/multilingual-t5)

## 관련 문서

- [[t5|T5]] - 변형 원본
