## 개요

DiffuSeq(Gong et al., ICLR 2023)는 확산 모델(Diffusion Model)을 **조건부 Seq2Seq 텍스트 생성**에 직접 적용한 연구다. 기존 언어 모델이 자기회귀(autoregressive) 방식으로 토큰을 하나씩 순차적으로 생성하는 것과 달리, DiffuSeq는 목표 시퀀스 전체를 연속 임베딩 공간(continuous embedding space)에서 반복적으로 탈노이징(denoising)하며 **비자기회귀(non-autoregressive)** 방식으로 한 번에 생성한다.

핵심 기여는 세 가지로 요약된다:
1. 소스 시퀀스를 조건으로 활용하는 **부분 노이징(partial noising)** 전략
2. Classifier-Free Guidance의 Seq2Seq 확장
3. 최종 샘플 선택을 위한 **MBR(Minimum Bayes Risk) 디코딩**

## 배경 및 문제

확산 모델은 이미지 생성(DALL-E 2, Stable Diffusion 등)에서 탁월한 성능을 보였지만, 텍스트는 본질적으로 **이산(discrete) 공간**에 존재하기 때문에 연속 확산 과정을 직접 적용하기 어렵다. Diffusion-LM(Li et al., 2022)은 단어 임베딩 공간에서 연속 확산을 수행해 이 간극을 좁혔으나, 비조건부(unconditional) 또는 classifier-guided 생성에 한정되어 있어 입력 시퀀스가 주어졌을 때 출력 시퀀스를 생성하는 **Seq2Seq** 설정에는 적합하지 않았다.

아래 그림은 기존 확산 모델 접근법과 DiffuSeq의 차이를 직관적으로 보여준다.

![비조건부, Classifier-guided, Classifier-free 확산 모델 비교](figures/fig_1.png)
*Figure 1. 연속 공간에서의 확산 모델 비교. (a) 비조건부 가우시안 확산, (b) Diffusion-LM의 classifier-guided 방식, (c) DiffuSeq의 classifier-free 방식. DiffuSeq는 조건 신호(주황색 점)가 공간 내 점(파란색)으로 직접 가이드를 제공하여 별도의 classifier 없이도 조건부 생성을 수행한다.*

자기회귀 모델(T5, BART 등)은 Seq2Seq에서 강력한 성능을 보이지만, **노출 편향(exposure bias)** -- 학습 시에는 정답 토큰을 보지만 추론 시에는 자신의 예측에 의존하는 불일치 -- 과 좌-우 방향의 **순차적 의존성 가정**의 한계가 있다. DiffuSeq는 확산 모델의 반복적 정제(iterative refinement) 능력을 Seq2Seq 프레임워크에 결합해 이러한 문제를 우회하고자 한다.

다음 그림은 DiffuSeq를 포함한 다양한 생성 모델의 확률 그래프 모델(graphical model) 비교를 보여준다.

![AR, NAR, Iterative NAR, DiffuSeq 그래프 모델 비교](figures/fig_9.png)
*Figure 2. 자기회귀(AR), 완전 비자기회귀(Fully NAR), 반복적 비자기회귀(Iterative NAR), DiffuSeq 모델의 그래프 모델 비교. 회색 노드는 소스 시퀀스에 대한 의존성을 나타내고, 흰색 노드는 소스와 독립적인 노드를 의미한다. DiffuSeq는 반복적 정제를 통해 모든 목표 토큰이 소스에 의존하면서도 토큰 간 양방향 의존성을 포착한다.*

## 핵심 아이디어

**부분 노이징(Partial Noising)**이 DiffuSeq의 핵심이다. 소스 시퀀스 $\mathbf{w}^x$와 목표 시퀀스 $\mathbf{w}^y$를 각각 임베딩 함수 $\text{Emb}(\cdot)$을 통해 연속 벡터로 변환한 뒤, **목표 임베딩 $\mathbf{z}_0^y = \text{Emb}(\mathbf{w}^y)$에만 가우시안 노이즈를 추가**하고 소스 임베딩 $\mathbf{z}_0^x = \text{Emb}(\mathbf{w}^x)$는 깨끗한 상태로 유지한다. 두 표현을 연결(concatenate)하여 모델의 입력을 구성한다:

$$\mathbf{x}_t = \text{concat}(\text{Emb}(\mathbf{w}^x),\ \mathbf{z}_t^y)$$

여기서 $\mathbf{z}_t^y$는 시각 $t$에서 노이즈가 추가된 목표 임베딩이다. 이 구조 덕분에 소스 시퀀스가 Transformer의 self-attention 메커니즘 전반에 걸쳐 목표 시퀀스 탈노이징 과정에 **자연스럽게 개입**할 수 있다. 별도의 encoder-decoder 구조 없이도 소스 조건이 모든 attention layer에서 목표 토큰에 직접 영향을 미친다.

## 방법론

### 순방향 프로세스 (Forward Process)

DiffuSeq의 순방향 프로세스는 표준 DDPM의 가우시안 노이즈 스케줄을 **목표 임베딩에만** 적용한다. 시각 $t$에서의 노이즈 추가는 다음과 같이 정의된다:

$$q(\mathbf{z}_t^y \mid \mathbf{z}_0^y) = \mathcal{N}(\mathbf{z}_t^y;\ \sqrt{\bar{\alpha}_t}\, \mathbf{z}_0^y,\ (1-\bar{\alpha}_t)\mathbf{I})$$

여기서 $\bar{\alpha}_t = \prod_{s=1}^{t}(1-\beta_s)$는 누적 노이즈 스케줄이다. 핵심은 **소스 임베딩이 $t$에 관계없이 $\mathbf{z}_0^x$로 고정**된다는 점이다. 이를 통해 역방향 과정에서 소스 정보가 손실 없이 조건으로 활용된다.

아래 그림은 DiffuSeq의 전체 확산 과정을 시각적으로 보여준다.

![DiffuSeq 부분 노이징 확산 과정](figures/fig_2.png)
*Figure 3. DiffuSeq의 확산 과정. 소스 $\mathbf{w}^x$와 목표 $\mathbf{w}^y$를 연속 공간 $\mathbf{z}_0$로 변환한 뒤, 목표 영역에만 부분 가우시안 노이즈를 반복적으로 추가한다. 역방향 과정에서는 소스 임베딩을 깨끗한 조건으로 유지하면서 목표 임베딩만 탈노이징한다.*

### 역방향 프로세스 (Reverse Process)

역방향 프로세스에서는 Transformer 기반 노이즈 예측 네트워크 $\epsilon_\theta$가 연결된 입력 $(\mathbf{z}_0^x, \mathbf{z}_t^y, t)$를 받아 추가된 노이즈를 추정한다. 학습 목적 함수는 표준 DDPM의 단순화된 목적 함수와 동일한 형태를 따른다:

$$\mathcal{L}_{\text{simple}}(\theta) = \mathbb{E}_{q(\mathbf{z}_0^y|\mathbf{w}^y)}\,\mathbb{E}_{t,\,\epsilon}\left[\|\epsilon_\theta(\mathbf{z}_t^y,\ \mathbf{z}_0^x,\ t) - \epsilon\|^2\right]$$

추가로, 임베딩 공간과 이산 토큰 공간 사이의 정렬을 강화하기 위해 Diffusion-LM에서 도입된 **앵커 손실(anchor loss)**을 보조적으로 사용한다:

$$\mathcal{L}_{\text{anchor}} = \|\mathbf{z}_0 - \text{Emb}(\mathbf{w})\|^2$$

최종 손실은 두 항의 가중합으로 구성된다.

### Classifier-Free Guidance 적용

이미지 도메인에서 조건부 생성 품질을 크게 향상시킨 Classifier-Free Guidance(CFG)를 Seq2Seq 설정에 맞게 확장한다. 학습 시 일정 확률 $p_{\text{uncond}}$로 소스 임베딩을 **null 벡터** $\emptyset$로 대체해 조건 없는 예측을 함께 학습하고, 추론 시 두 예측을 선형 보간하여 조건 반영 강도를 조절한다:

$$\tilde{\epsilon}_\theta = \epsilon_\theta(\mathbf{z}_t^y, \emptyset, t) + s \cdot \big(\epsilon_\theta(\mathbf{z}_t^y, \mathbf{z}_0^x, t) - \epsilon_\theta(\mathbf{z}_t^y, \emptyset, t)\big)$$

가이던스 스케일 $s$가 핵심 하이퍼파라미터로, $s > 1$이면 소스 조건에 대한 의존도를 높여 **품질(fidelity)**이 향상되고, $s < 1$이면 조건 의존도를 낮춰 **다양성(diversity)**이 증가한다.

### MBR(Minimum Bayes Risk) 디코딩

확산 모델은 확률적 샘플링 특성상 한 번의 추론으로 **여러 다양한 후보 샘플**을 생성할 수 있다. MBR 디코딩은 $N$개 후보 샘플 집합 $\mathcal{S} = \{y_1, \ldots, y_N\}$ 중에서 전체 후보에 대해 평균적으로 가장 높은 유사도를 달성하는 샘플을 최종 출력으로 선택한다:

$$\hat{y} = \arg\max_{y_i \in \mathcal{S}} \frac{1}{N} \sum_{j=1}^{N} \text{BLEU}(y_i, y_j)$$

이를 통해 단순히 가장 그럴듯한 단일 샘플이 아닌, **집합 수준에서 대표성이 높은** 합의(consensus) 출력을 얻는다. 이 전략은 자기회귀 모델에서는 활용하기 어려운, 확산 모델의 고유한 장점이다.

## 실험 결과

네 가지 Seq2Seq 벤치마크에서 DiffuSeq의 성능을 평가했다.

### 태스크별 정량적 결과

**Text Simplification (Newsela):**

| 모델 | SARI ↑ | FKGL ↓ | BLEU ↑ |
|------|--------|--------|--------|
| LSTM | 31.2 | 5.3 | 22.1 |
| GPT2-base | 33.5 | 4.8 | 25.3 |
| GPT2-large | 34.1 | 4.6 | 26.7 |
| DiffuSeq | 33.8 | 4.7 | 25.9 |
| DiffuSeq + MBR | **34.6** | **4.5** | **27.2** |

**Paraphrase Generation (QQP):**

| 모델 | BLEU ↑ | ROUGE-L ↑ | div-4 ↑ | iBLEU ↑ |
|------|--------|-----------|---------|---------|
| GPT2-base | 18.5 | 42.3 | 0.52 | 8.2 |
| GPT2-large | 19.1 | 43.0 | 0.48 | 8.6 |
| DiffuSeq | 17.8 | 41.5 | **0.71** | 7.9 |
| DiffuSeq + MBR | **19.4** | **43.2** | 0.65 | **8.8** |

**Question Generation (SQuAD):**

| 모델 | BLEU-4 ↑ | ROUGE-L ↑ | METEOR ↑ | div-4 ↑ |
|------|----------|-----------|----------|---------|
| ProphetNet | 14.5 | 39.2 | 21.3 | 0.41 |
| BART-base | 13.8 | 38.7 | 20.8 | 0.38 |
| GPT2-base | 12.1 | 36.5 | 19.2 | 0.45 |
| GPT2-large | 13.2 | 37.8 | 20.1 | 0.42 |
| DiffuSeq | 12.8 | 37.2 | 19.8 | **0.72** |
| DiffuSeq + MBR | **14.8** | **39.5** | **21.5** | 0.68 |

**Machine Translation (IWSLT14 De→En):**

| 모델 | BLEU ↑ | 유형 | 비고 |
|------|--------|------|------|
| NAT (Gu et al.) | 28.3 | 비자기회귀 | 기존 NAR 대표 |
| CMLM | 30.5 | 반복 NAR | 마스크 예측 반복 |
| DiffuSeq | 29.8 | 확산 기반 | 2000 스텝 |
| DiffuSeq + MBR | **31.2** | 확산 기반 | MBR 후처리 |
| Transformer (base) | 34.4 | 자기회귀 | 참고용 상한 |

:::info
DiffuSeq의 가장 두드러진 강점은 **다양성(div-4)** 지표에서 나타난다. 모든 태스크에서 자기회귀 모델 대비 유의미하게 높은 다양성을 보이며, MBR 디코딩을 적용하면 품질도 AR 수준에 도달하거나 상회한다. 이는 확산 모델 고유의 확률적 생성 특성이 Seq2Seq 태스크에서 실질적 이점으로 작용함을 보여준다.
:::

### 품질-다양성 트레이드오프

DiffuSeq의 가장 두드러진 특성 중 하나는 품질(quality)과 다양성(diversity) 사이의 트레이드오프를 명시적으로 제어할 수 있다는 점이다. 아래 그림은 질문 생성 태스크에서 이 트레이드오프를 시각화한 결과다.

![품질-다양성 트레이드오프 시각화](figures/fig_5.png)
*Figure 4. 질문 생성 태스크에서의 품질(BLEU)-다양성(div-4) 트레이드오프. DiffuSeq는 가이던스 스케일 $s$를 조절함으로써 품질-다양성 파레토 프론티어 위를 이동할 수 있다. GPT2 변형들은 고정된 단일 지점에 위치하는 반면, DiffuSeq는 유연한 제어가 가능하다.*

CFG 가이던스 스케일 $s$를 높이면 BLEU 점수(품질)가 올라가지만 다양성(div-4)은 감소하고, $s$를 낮추면 반대 경향을 보인다. GPT2-base, GPT2-large 같은 자기회귀 모델은 이러한 연속적인 제어가 불가능하여 그래프 상에서 고정된 점으로 나타난다.

아래 그림은 질문 생성 태스크에서 DiffuSeq와 다양한 베이스라인 모델들의 품질-다양성 위치를 비교한 것이다.

![질문 생성에서의 모델별 품질-다양성 비교](figures/fig_3_2.png)
*Figure 5: 질문 생성(Question Generation) 태스크에서의 품질(BLEU)-다양성(div-4) 비교. DiffuSeq(주황)는 가이던스 스케일 조절을 통해 다양한 트레이드오프 지점을 탐색할 수 있으며, NAR-LevT, GPVAE-T5 등 비자기회귀 베이스라인보다 우수한 파레토 프론티어를 형성한다. (Gong et al., 2023)*

MBR 디코딩의 효과는 후보 수 $|\mathcal{S}|$에 따른 BLEU 변화에서 명확히 확인된다. 아래 그림은 Text Simplification과 Paraphrase 태스크에서 후보 수를 1에서 20으로 늘렸을 때의 BLEU 향상을 보여준다.

![MBR 디코딩의 후보 수에 따른 BLEU 향상](figures/fig_3_1.png)
*Figure 6: MBR 디코딩에서 후보 수 $|\mathcal{S}|$에 따른 BLEU 변화 — Text Simplification(좌)과 Paraphrase(우) 태스크에서 DiffuSeq는 후보 수가 증가할수록 일관되게 BLEU가 향상되며, GPT2 베이스라인을 능가한다. (Gong et al., 2023)*

이러한 BLEU 향상은 확산 모델이 생성하는 다양한 샘플들 사이에서 최적의 대표 샘플을 효과적으로 선별할 수 있음을 보여준다.

MBR 디코딩의 원리를 더 직관적으로 설명하면, 확산 모델은 동일한 소스 입력에 대해 매번 다른 노이즈로부터 샘플링하므로 다양한 후보를 생성한다. 이 후보들 중 "다른 후보들과 가장 유사한" 샘플을 선택하면, 극단적인 변이(outlier)를 배제하고 핵심 의미를 잘 포착한 대표 샘플을 얻을 수 있다. 이는 앙상블(ensemble)의 효과와 유사하며, 자기회귀 모델의 beam search가 하나의 탐색 경로에서 최적을 찾는 것과 대조적으로, MBR은 독립적인 다수의 경로에서 합의를 도출한다.

![MBR 디코딩의 후보 수에 따른 BLEU 향상 - Text Simplification, Paraphrase](figures/fig_4.png)
*Figure 6-2: MBR 디코딩에서 후보 수 $|\mathcal{S}|$에 따른 BLEU 변화 (추가 실험). DiffuSeq(주황)와 GPT2 베이스라인(파란)의 비교. 후보 수가 증가할수록 DiffuSeq의 BLEU 향상이 GPT2보다 가파르며, 이는 확산 모델의 샘플 다양성이 MBR에서 더 큰 이점을 제공함을 보여준다. (Gong et al., 2023)*

### 생성 과정에서의 품질 변화

확산 과정의 진행에 따라 BLEU와 다양성(div-4) 점수가 어떻게 변화하는지 추적하면, DiffuSeq의 반복적 정제 메커니즘을 직관적으로 이해할 수 있다.

![생성 과정 진행에 따른 BLEU/div-4 변화](figures/fig_6_1.png)
*Figure 7: Text Simplification 태스크에서 생성 과정 진행(%)에 따른 BLEU(파란)와 div-4(주황) 변화 — 초기 스텝에서 다양성이 급격히 형성되고, 이후 점진적으로 BLEU가 수렴하며 품질이 안정화된다. (Gong et al., 2023)*

### 추론 속도와 품질

확산 모델의 실용적 한계 중 하나인 추론 속도에 대해서도 분석이 이루어졌다. 아래 그림은 샘플링 스텝 수에 따른 BLEU 점수와 생성 속도의 관계를 보여준다.

![샘플링 스텝에 따른 BLEU 점수와 추론 속도](figures/fig_6_2.png)
*Figure 5. 질문 생성 태스크에서 샘플링 스텝 수에 따른 DiffuSeq의 BLEU 점수(파란 선)와 생성 속도(주황 막대). 점선은 GPT2-large의 BLEU와 속도 기준선을 나타낸다. 스텝 수가 2000일 때 GPT2-large를 상회하는 BLEU를 달성하지만, 생성 속도는 상당히 느리다.*

샘플링 스텝 수를 줄이면 추론 속도는 빨라지지만 품질이 하락하는 트레이드오프가 존재한다. 2000 스텝에서 GPT2-large를 능가하는 BLEU를 달성하지만, 생성 속도(samples/sec)는 크게 뒤처진다. 이는 확산 기반 텍스트 생성의 실용화를 위해 효율적인 샘플링 기법(DDIM 등)의 적용이 필수적임을 시사한다.

구체적인 스텝별 성능과 속도를 정리하면:

| 샘플링 스텝 | BLEU (QG) | 속도 (samples/sec) | GPT2-large 대비 |
|------------|-----------|-------------------|----------------|
| 100 | 9.5 | ~8.0 | BLEU 열등, 속도 동등 |
| 500 | 12.0 | ~2.5 | BLEU 근접, 속도 3x 느림 |
| 1000 | 13.5 | ~1.2 | BLEU 동등, 속도 7x 느림 |
| 2000 | 14.8 | ~0.6 | BLEU 우수, 속도 13x 느림 |
| GPT2-large | 13.2 | ~8.0 | 기준선 |

:::warning
DiffuSeq의 추론 속도는 실용적 배포에서 가장 큰 병목이다. 후속 연구인 DiffuSeq-v2는 DDIM 스타일의 빠른 샘플링을 적용하여 스텝 수를 10분의 1로 줄이면서도 품질 저하를 최소화했다.
:::

### 어블레이션 스터디

DiffuSeq의 주요 설계 선택들의 기여를 분석하기 위한 어블레이션 결과:

| 설정 | QG BLEU | QG div-4 | 비고 |
|------|---------|----------|------|
| DiffuSeq (full) | 14.8 | 0.72 | 전체 모델 |
| - 부분 노이징 (전체 노이징) | 10.2 | 0.68 | 소스 정보 손실 |
| - CFG | 13.1 | 0.75 | 조건 반영 약화 |
| - 앵커 손실 | 13.5 | 0.70 | 토큰 정렬 저하 |
| - MBR (greedy 선택) | 12.8 | 0.72 | 최적 샘플 선택 불가 |
| - self-conditioning | 14.0 | 0.71 | 반복 정제 약화 |

부분 노이징이 가장 큰 영향을 미치며, 이를 제거하고 전체 시퀀스에 노이즈를 추가하면 BLEU가 약 4.6 하락한다. 이는 소스 정보의 보존이 Seq2Seq 확산 모델에서 얼마나 핵심적인지를 보여준다.

## 의의 및 한계

### 의의

DiffuSeq는 확산 모델을 Seq2Seq 조건부 생성으로 확장한 **선구적 연구**다. 부분 노이징이라는 단순하지만 효과적인 설계로 소스 정보를 확산 과정 전반에 흘려 넣고, 비자기회귀 생성의 **출력 다양성**을 MBR 디코딩과 결합해 실용적인 성능을 확보했다. 특히 품질-다양성 트레이드오프를 연속적으로 제어할 수 있다는 점은 자기회귀 모델에서는 달성하기 어려운 고유한 장점이다. 이후 SeqDiffuSeq, GENIE, DiffuSeq-v2 등 다수의 후속 연구에 영향을 주었다.

### 한계

- **추론 속도**: 수백~수천 번의 탈노이징 스텝이 필요하며, 빠른 샘플링(DDIM 등)을 적용해도 T5/BART 대비 상당한 지연이 발생한다.
- **임베딩-토큰 정렬**: 긴 시퀀스에서 연속 임베딩 공간과 이산 토큰 공간 사이의 정렬(rounding)이 불완전해 생성 품질이 저하될 수 있다.
- **사전학습 부재**: GPT-4 등 대규모 사전학습 언어 모델과 달리, DiffuSeq는 태스크별로 처음부터 학습하므로 범용 언어 지식 활용에 한계가 있다.
- **길이 예측**: 비자기회귀 생성 특성상 목표 시퀀스의 길이를 사전에 결정하거나 예측해야 하는 추가적인 제약이 존재한다.

### 후속 연구에 미친 영향

DiffuSeq는 텍스트 확산 모델 연구의 중요한 이정표가 되었다. 주요 후속 연구와의 관계를 정리하면:

| 후속 연구 | DiffuSeq와의 관계 | 개선점 |
|-----------|------------------|--------|
| SeqDiffuSeq | 동일 프레임워크 확장 | 토큰별 적응형 노이즈 스케줄 |
| DiffuSeq-v2 | 직접적 후속 | DDIM 기반 가속, 스텝 수 감소 |
| GENIE | 유사 동기 | 연속 확산 + 사전학습 통합 |
| Diffusion-LM | 선행 연구 | DiffuSeq의 Seq2Seq 확장 기반 |
| MDLM | 방향 전환 | 이산 공간에서 직접 확산, 연속 임베딩 불필요 |

DiffuSeq가 보여준 "연속 임베딩 공간에서의 텍스트 확산"이라는 접근은, 이후 MDLM, SEDD 등 "이산 공간에서의 직접 확산"이라는 대안적 방향이 더 유망할 수 있다는 연구 결과와 대비된다. 연속 공간 접근의 장점(부드러운 보간, CFG 적용 용이)과 이산 공간 접근의 장점(라운딩 오류 없음, 언어 모델링 직접 최적화)은 각각의 응용에 따라 적합성이 달라질 수 있다.

## 코드 예제

아래는 부분 노이징과 조건부 입력 구성을 PyTorch 스타일로 단순화한 예시다.

```python
import torch
import torch.nn as nn

class DiffuSeqForwardProcess:
    """DiffuSeq 순방향 프로세스: 목표 임베딩에만 노이즈 추가"""

    def __init__(self, num_timesteps: int = 2000, beta_start: float = 1e-4, beta_end: float = 0.02):
        betas = torch.linspace(beta_start, beta_end, num_timesteps)
        alphas = 1.0 - betas
        self.alphas_bar = torch.cumprod(alphas, dim=0)  # \bar{\alpha}_t

    def q_sample(self, z0_y: torch.Tensor, t: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """목표 임베딩 z0_y에 시각 t의 노이즈를 추가. 소스는 건드리지 않음."""
        alpha_bar_t = self.alphas_bar[t].view(-1, 1, 1)  # (B, 1, 1)
        eps = torch.randn_like(z0_y)
        zt_y = alpha_bar_t.sqrt() * z0_y + (1 - alpha_bar_t).sqrt() * eps
        return zt_y, eps


class DiffuSeqModel(nn.Module):
    """소스 임베딩을 조건으로 목표 노이즈를 예측하는 Transformer"""

    def __init__(self, embed_dim: int = 128, num_heads: int = 8, num_layers: int = 6):
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim, nhead=num_heads, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.time_embed = nn.Embedding(2000, embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)

    def forward(
        self,
        z0_x: torch.Tensor,   # 소스 임베딩 (B, src_len, D) — 노이즈 없음
        zt_y: torch.Tensor,   # 목표 노이즈 임베딩 (B, tgt_len, D)
        t: torch.Tensor,      # 타임스텝 (B,)
    ) -> torch.Tensor:
        # 타임스텝 임베딩을 목표 시퀀스의 각 위치에 더함
        t_emb = self.time_embed(t).unsqueeze(1)          # (B, 1, D)
        zt_y = zt_y + t_emb                              # 시간 조건 주입

        # 소스(조건)와 목표(노이즈)를 연결해 Transformer에 입력
        x = torch.cat([z0_x, zt_y], dim=1)              # (B, src+tgt, D)
        h = self.transformer(x)

        # 목표 시퀀스 위치만 추출해 노이즈 예측
        src_len = z0_x.size(1)
        eps_pred = self.out_proj(h[:, src_len:, :])      # (B, tgt_len, D)
        return eps_pred


def compute_diffu_seq_loss(
    model: DiffuSeqModel,
    forward_process: DiffuSeqForwardProcess,
    z0_x: torch.Tensor,
    z0_y: torch.Tensor,
    device: str = "cpu",
) -> torch.Tensor:
    """DiffuSeq 학습 손실: ||eps_theta(zt_y, z0_x, t) - eps||^2"""
    B = z0_y.size(0)
    t = torch.randint(0, len(forward_process.alphas_bar), (B,), device=device)
    zt_y, eps = forward_process.q_sample(z0_y, t)
    eps_pred = model(z0_x, zt_y, t)
    loss = ((eps_pred - eps) ** 2).mean()
    return loss
```

## 관련 문서

- Diffusion-LM (Li et al., 2022): 연속 임베딩 공간에서의 비조건부 텍스트 확산 기초
- DDPM (Ho et al., NeurIPS 2020): 가우시안 확산 모델 원형
- Classifier-Free Guidance (Ho & Salimans, 2022): 조건 강도 조절 기법
- GENIE (Lin et al., 2023): 확산 기반 Seq2Seq 후속 연구
- SeqDiffuSeq (Yuan et al., 2022): 토큰 단위 적응형 노이즈 스케줄
