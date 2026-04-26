<!-- infographic-hero -->
![ELMo 핵심 요약](figures/infographic.svg)

*Figure: ELMo 한 장 요약 인포그래픽*

# ELMo: 문맥화된 단어 임베딩의 시작

## 개요

**ELMo**(Embeddings from Language Models)는 2018년 2월 Allen Institute for AI(AI2)가 발표한 사전 학습 기반 단어 표현 모델로, NLP 분야에서 **문맥화된 임베딩(Contextualized Embeddings)**이라는 새로운 패러다임을 개척했다. "Deep contextualized word representations" (Peters et al., 2018) 논문으로 **ACL 2018 Best Paper**를 수상한 이 연구는, BERT로 이어지는 사전 학습 표현 학습 혁명의 직접적 선구자이다.

기존 Word2Vec, GloVe 같은 정적 임베딩은 단어 하나에 고정된 벡터 하나를 할당하므로, "bank"가 "은행"인지 "강둑"인지를 문맥으로 구분할 수 없었다. ELMo는 양방향 LSTM(BiLSTM)을 층층이 쌓아 **동일한 단어라도 문맥에 따라 다른 벡터 표현**을 생성하여, SQuAD, SNLI, SRL 등 6개 NLP 태스크에서 당시 SOTA를 크게 앞질렀다.

**참고 논문**: [Deep contextualized word representations](https://arxiv.org/abs/1802.05365) (Peters et al., 2018)

아래 다이어그램은 ELMo의 전체 아키텍처를 보여준다. Character CNN에서 시작하여 2층 BiLSTM을 거치고, 태스크별 가중 합산으로 최종 표현을 생성하는 구조가 핵심이다.

![ELMo 아키텍처 - Character CNN, BiLSTM, 가중 합산 전체 구조](figures/architecture.png)
*Figure 1: ELMo 아키텍처(93.6M 파라미터) - Character CNN 토큰 임베딩, 2층 BiLSTM(각 4096-dim→512 투사), 태스크별 가중 합산 메커니즘, 그리고 LSTM 셀 내부 구조. (Peters et al., 2018)*

## 아키텍처 상세

### 전체 구조

ELMo의 아키텍처는 세 개의 계층으로 구성된다:

| 계층 | 구성 | 출력 차원 |
|------|------|-----------|
| **1. Character CNN** | 2048 필터, 7개 크기 | 512 (투사 후) |
| **2. BiLSTM Layer 1** | 순방향 + 역방향 각 4096-dim | 512 (투사 후) |
| **3. BiLSTM Layer 2** | 순방향 + 역방향 각 4096-dim | 512 (투사 후) |

### Character CNN 입력

ELMo는 단어 수준이 아닌 **문자(character) 수준**에서 입력을 처리한다. 각 단어의 문자 시퀀스에 다양한 크기의 1D CNN 필터(폭 1~7, 총 2048개)를 적용한 후, Highway Network를 거쳐 512차원으로 투사한다. 이 방식의 핵심 장점은 **OOV(Out-of-Vocabulary) 문제를 완전히 제거**한다는 것이다. 처음 보는 단어도 문자 패턴을 통해 합리적인 임베딩을 생성할 수 있다.

### BiLSTM 언어 모델

두 개의 BiLSTM 레이어가 순방향과 역방향 언어 모델을 **각각 독립적으로** 학습한다:

$$p(t_1, t_2, \ldots, t_N) = \prod_{k=1}^{N} p(t_k | t_1, \ldots, t_{k-1}) \cdot p(t_k | t_{k+1}, \ldots, t_N)$$

순방향 LSTM은 왼쪽에서 오른쪽으로, 역방향 LSTM은 오른쪽에서 왼쪽으로 읽으며, 각 방향의 언어 모델 log-likelihood를 독립적으로 최대화한다.

### 가중 합산 (ELMo Representation)

ELMo의 핵심 아이디어는 **모든 레이어의 은닉 상태를 태스크별 가중치로 합산**하는 것이다:

$$\text{ELMo}_k = \gamma \sum_{j=0}^{L} s_j \cdot h_{k,j}$$

여기서 $h_{k,j}$는 $j$번째 레이어의 $k$번째 위치 은닉 상태, $s_j$는 softmax 정규화된 레이어별 가중치, $\gamma$는 태스크별 스케일링 파라미터이다. $s_j$와 $\gamma$는 **다운스트림 태스크마다 다르게 학습**되므로, 각 태스크가 필요로 하는 언어 정보를 선택적으로 추출할 수 있다.

### 레이어별 정보 분화

논문의 중요한 발견 중 하나는 BiLSTM의 각 레이어가 서로 다른 수준의 언어 정보를 포착한다는 것이다:

- **하위 레이어(Layer 0, Character CNN)**: 형태론적 정보 (접두사, 접미사, 품사)
- **중간 레이어(Layer 1)**: 구문론적 정보 (구문 구조, 의존 관계)
- **상위 레이어(Layer 2)**: 의미론적 정보 (단어 의미 중의성 해소, 문맥 의미)

이 발견은 이후 BERT에서도 확인되었으며, Transformer 레이어의 정보 분화 연구의 기초가 되었다.

아래 히트맵은 태스크별로 BiLSTM 각 레이어에 부여되는 가중치를 시각화한 것으로, 태스크마다 필요한 언어 정보 수준이 다름을 직접적으로 보여준다.

![태스크별 BiLSTM 레이어 가중치 시각화](figures/fig_2.png)
*Figure 3: 태스크별 BiLSTM 레이어 가중치 분포 - softmax 정규화된 가중치 히트맵. 하위 레이어(형태론)와 상위 레이어(의미론)의 기여가 태스크에 따라 다르게 나타난다. (Peters et al., 2018)*

## 핵심 혁신

### 1. 문맥화된 임베딩

"bank"라는 단어가 "I went to the bank to deposit money"에서는 금융 기관을, "The river bank was covered with flowers"에서는 강둑을 의미하도록 문맥에 따라 다른 벡터를 생성한다. 이는 Word2Vec/GloVe의 근본적 한계를 해결했다.

### 2. Feature-based Transfer Learning

ELMo는 사전 학습된 표현을 다운스트림 모델의 **추가 입력 특징(feature)**으로 사용하는 방식이다. BERT의 파인튜닝 방식과 달리, 기존 모델 아키텍처를 수정하지 않고 ELMo 벡터를 단순 연결(concatenation)하여 성능을 향상시킨다.

### 3. 사전 학습 → 전이 학습 패러다임의 개척

대규모 비지도 코퍼스에서 언어 모델을 사전 학습하고, 그 표현을 다양한 다운스트림 태스크에 전이하는 패러다임을 NLP에서 실질적으로 입증한 첫 대규모 성공 사례이다.

다음 그래프는 SNLI와 SRL 태스크에서 학습 데이터 비율(0.1%~100%)에 따른 ELMo 적용 전후 성능 변화를 보여준다. 특히 적은 데이터에서 ELMo의 효과가 극대화됨을 확인할 수 있다.

![SNLI 및 SRL에서 학습 데이터 크기에 따른 ELMo 성능 비교](figures/fig_1.png)
*Figure 2: ELMo 적용 전후 성능 비교 - 학습 데이터 비율을 0.1%에서 100%까지 변화시켰을 때 SNLI와 SRL 태스크의 성능 변화. 소량 데이터에서 ELMo의 이점이 가장 두드러진다. (Peters et al., 2018)*

## 벤치마크/성능

| 태스크 | 이전 SOTA | +ELMo | 개선폭 |
|--------|----------|-------|--------|
| **SQuAD** | 84.4 | **85.8** | +1.4 |
| **SNLI** | 88.6 | **88.7** | +0.1 |
| **SRL** | 81.4 | **84.6** | +3.2 |
| **NER** | 91.93 | **92.22** | +0.29 |
| **SST-5** | 53.7 | **54.7** | +1.0 |
| **Coref** | 67.2 | **70.4** | +3.2 |

6개 태스크 모두에서 ELMo 벡터를 추가하는 것만으로 SOTA를 갱신했다.

## 관련 모델 비교

| 특성 | Word2Vec | GloVe | ELMo | BERT |
|------|---------|-------|------|------|
| **발표** | 2013 | 2014 | **2018** | 2018 |
| **임베딩 유형** | 정적 | 정적 | **문맥화** | 문맥화 |
| **아키텍처** | Skip-gram | Co-occurrence | **BiLSTM** | Transformer |
| **양방향** | No | N/A | **Semi** (독립) | Yes (완전) |
| **전이 방식** | Feature | Feature | **Feature** | Fine-tuning |
| **OOV 처리** | 불가 | 불가 | **Char CNN** | WordPiece |
| **파라미터** | ~300dim | ~300dim | **93.6M** | 110M |

## 학습 상세

- **데이터**: 1 Billion Word Language Model Benchmark (약 8억 단어)
- **아키텍처**: Character CNN (2048 필터, 7개 크기) + Highway Network + 2-layer BiLSTM (4096-dim → 512 투사)
- **학습 방법**: 순방향/역방향 언어 모델 손실 각각 독립 최대화
- **하드웨어**: GPU 32개, 약 10일 학습
- **투사**: 각 LSTM 레이어의 4096-dim 출력을 512-dim으로 투사 (메모리 효율)

## 실무 활용

### 1. 기존 모델 성능 부스팅

```python
import allennlp
from allennlp.modules.elmo import Elmo

options_file = "https://allennlp.s3.amazonaws.com/models/elmo/2x4096_512_2048cnn_2xhighway/elmo_2x4096_512_2048cnn_2xhighway_options.json"
weight_file = "https://allennlp.s3.amazonaws.com/models/elmo/2x4096_512_2048cnn_2xhighway/elmo_2x4096_512_2048cnn_2xhighway_weights.hdf5"

elmo = Elmo(options_file, weight_file, 2)  # 2개 레이어 출력
# 기존 NLP 모델 입력에 ELMo 벡터를 concatenation
```

### 2. 단어 의미 중의성 해소

ELMo 벡터의 코사인 유사도를 통해 문맥 내 단어 의미를 구별할 수 있다.

### 3. 저자원 언어 NLP

Character CNN 기반이므로 형태론이 풍부한 언어(한국어, 터키어 등)에서도 OOV 없이 적용 가능하다.

## 한계 및 전망

### 한계

1. **양방향성의 한계**: 순방향과 역방향 LSTM이 독립적으로 학습되므로, BERT처럼 양쪽 문맥을 동시에 고려하지 못한다.
2. **LSTM의 병렬화 한계**: Transformer 대비 GPU 병렬 처리가 비효율적이다.
3. **Feature-based 한계**: 파인튜닝 대비 전이 학습 효과가 제한적이다.
4. **속도**: 추론 시 LSTM의 순차적 처리로 인해 Transformer 기반 모델보다 느리다.

### 전망

ELMo는 BERT, GPT 등 Transformer 기반 사전 학습 모델의 직접적 선구자로서 역사적 중요성이 크다. "문맥화된 표현"이라는 핵심 아이디어는 현대 모든 LLM의 기본 원리로 계승되었으며, 레이어별 정보 분화 현상은 Transformer 해석 연구(Probing, BERTology)의 이론적 기반이 되었다.

---

**참고 논문**: [Deep contextualized word representations](https://arxiv.org/abs/1802.05365) (Peters et al., 2018)
