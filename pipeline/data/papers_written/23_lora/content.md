## 개요

GPT-3(175B), PaLM(540B)과 같은 대규모 언어 모델(LLM)의 등장은 자연어 처리의 패러다임을 근본적으로 바꾸어 놓았습니다. 이러한 모델들은 사전학습(pre-training)을 통해 범용적인 언어 이해 능력을 획득하며, 특정 태스크에 대한 파인튜닝(fine-tuning)을 거쳐 뛰어난 성능을 발휘합니다. 그러나 모델의 규모가 기하급수적으로 커지면서, 전체 파인튜닝(full fine-tuning)에 필요한 계산 자원과 저장 비용이 감당할 수 없는 수준에 이르렀습니다.

이러한 배경에서 Microsoft Research의 Edward Hu 등이 2021년에 제안한 **LoRA(Low-Rank Adaptation)**는 파라미터 효율적 파인튜닝(Parameter-Efficient Fine-Tuning, PEFT) 분야의 결정적 전환점이 된 논문입니다. LoRA의 핵심 통찰은 파인튜닝 과정에서 발생하는 가중치 변화량 $\Delta W$가 본질적으로 낮은 랭크(intrinsic low rank)를 가진다는 것이며, 이를 두 개의 저랭크 행렬의 곱으로 근사하여 다음과 같이 표현할 수 있다는 것입니다:

$$W = W_0 + \Delta W = W_0 + BA$$

LoRA는 단순한 아이디어임에도 불구하고 세 가지 핵심 장점을 동시에 달성합니다. 첫째, 학습 파라미터 수를 전체 모델 대비 수만 배 이상 줄여 GPU 메모리 사용량을 획기적으로 감소시킵니다. 둘째, 학습된 저랭크 행렬을 원래 가중치에 병합(merge)할 수 있으므로 추론 시 추가적인 계산 비용이나 지연(latency)이 전혀 발생하지 않습니다. 셋째, 태스크별로 소규모의 LoRA 가중치만 교체하면 되므로 다중 태스크 배포가 매우 효율적입니다.

다음 그림은 LoRA의 전체적인 구조와 파라미터 효율성을 한눈에 보여줍니다.

![LoRA의 전체 구조 개요: 동결된 사전학습 가중치와 학습 가능한 저랭크 어댑터](figures/architecture.png)
*LoRA의 핵심 아이디어 요약. 사전학습된 가중치 $W_0$는 동결하고, 저랭크 행렬 $B$와 $A$의 곱($\Delta W = BA$)만 학습한다. $r=8$ 기준 전체 파라미터의 약 0.01%만 학습하면서도 전체 파인튜닝에 필적하는 성능을 달성한다.*

본 리뷰에서는 LoRA의 이론적 배경, 방법론, 실험 결과, 그리고 후속 연구와 실무 활용까지 포괄적으로 다루겠습니다.

## 배경 및 문제

### 전체 파인튜닝의 비용 문제

사전학습된 언어 모델 $P_\Phi(y|x)$가 주어졌을 때, 전체 파인튜닝은 모든 파라미터 $\Phi$를 태스크 데이터 $\mathcal{Z} = \{(x_i, y_i)\}$에 대해 최적화합니다.

$$\max_{\Phi} \sum_{(x,y) \in \mathcal{Z}} \sum_{t=1}^{|y|} \log P_\Phi(y_t \mid x, y_{<t})$$

이때 전체 파인튜닝은 가중치 업데이트량 $|\Delta\Phi|$가 원래 파라미터 수 $|\Phi_0|$와 동일합니다. GPT-3의 경우 $|\Phi_0| = 175 \times 10^9$이므로, 이는 다음과 같은 심각한 문제를 야기합니다.

| 항목 | 전체 파인튜닝 (GPT-3 175B) |
|------|---------------------------|
| 모델 파라미터 | 175B (약 350GB, FP16) |
| 옵티마이저 상태 (Adam) | 약 700GB (파라미터의 2배) |
| 그래디언트 | 약 350GB |
| 총 GPU 메모리 | 약 1.2TB 이상 |
| 체크포인트 저장 | 태스크당 약 350GB |
| 필요 GPU | A100 80GB 최소 16장 이상 |

단일 조직이 수십 개의 태스크에 대해 각각 전체 파인튜닝된 모델을 유지한다면, 저장 비용만 해도 수 TB에 달하며 배포 시 모델 전환 비용도 막대합니다.

### 기존 PEFT 방법들의 한계

LoRA 이전에도 파라미터 효율적 접근법들이 존재했지만, 각각 고유한 한계를 가지고 있었습니다.

**Adapter Tuning (Houlsby et al., 2019)**: 트랜스포머의 각 레이어에 소규모 MLP 모듈(adapter)을 삽입하여 해당 모듈만 학습합니다. 파라미터 효율성은 좋지만, 순차적인 추가 연산이 삽입되므로 추론 시 지연(latency)이 증가합니다. 특히 배치 크기가 작거나 시퀀스 길이가 긴 경우 이 오버헤드가 무시할 수 없습니다. 논문에서 보고한 바로는, 단일 GPU에서 GPT-2 Medium 기준 추론 지연이 약 20-30% 증가할 수 있습니다.

아래 그림은 Adapter 방식의 추론 지연 오버헤드를 배치 크기와 시퀀스 길이 조건별로 정량적으로 보여줍니다.

![Adapter 기반 방법의 추론 지연 오버헤드 히트맵](figures/fig_5.png)
*Adapter$^\text{H}$(상단)와 Adapter$^\text{L}$(하단)의 추론 지연 증가율(%, 기준: 어댑터 미적용). 배치 크기가 1이고 시퀀스 길이가 짧은 온라인 서빙 환경에서는 지연이 최대 30% 이상 증가한다. LoRA는 학습 후 가중치를 원본에 병합하므로 이러한 추론 오버헤드가 원천적으로 발생하지 않는다.*

**Prefix Tuning (Li & Liang, 2021)**: 입력 시퀀스 앞에 학습 가능한 연속 벡터(prefix)를 추가합니다. 학습 파라미터는 적지만, 사용 가능한 시퀀스 길이가 prefix 길이만큼 줄어들며, 최적화가 불안정하여 수렴이 어려울 수 있습니다.

**Prompt Tuning (Lester et al., 2021)**: Prefix Tuning의 간소화 버전으로, 입력 임베딩 단계에서만 학습 가능한 토큰을 추가합니다. 모델 규모가 충분히 클 때(10B 이상)만 전체 파인튜닝에 근접하는 성능을 보입니다.

이러한 방법들의 공통적인 문제는 **추론 효율성과 성능 사이의 트레이드오프**가 존재한다는 점이었습니다. LoRA는 이 트레이드오프를 근본적으로 해결합니다.

### 내재적 저랭크 가설 (Intrinsic Low-Rank Hypothesis)

LoRA의 이론적 기반은 Aghajanyan et al. (2020)의 "Intrinsic Dimensionality Explains the Effectiveness of Language Model Fine-Tuning" 연구에 있습니다. 이 연구에서는 사전학습된 언어 모델의 **내재적 차원(intrinsic dimension)**이 전체 파라미터 수에 비해 매우 낮다는 사실을 실증적으로 보였습니다. 예를 들어, RoBERTa-base(125M 파라미터)의 경우 내재적 차원이 약 200 정도에 불과했습니다.

LoRA는 이 관찰을 한 단계 더 확장하여, 파인튜닝 과정에서 발생하는 가중치 변화량 $\Delta W$ 자체가 낮은 랭크를 가진다고 가정합니다. 즉, 사전학습으로 이미 충분한 표현력을 갖춘 모델은 새로운 태스크에 적응할 때 가중치 공간의 극히 일부 방향만 변경하면 된다는 것입니다. 이 가설은 논문의 실험에서 $r=1$이나 $r=2$ 같은 극단적으로 낮은 랭크에서도 합리적인 성능을 보이는 것으로 뒷받침됩니다.

## 핵심 아이디어

### 저랭크 분해를 통한 가중치 업데이트

LoRA의 핵심은 사전학습된 가중치 행렬 $W_0$를 동결(freeze)하고, 가중치 변화량 $\Delta W$를 두 개의 저랭크 행렬의 곱으로 표현하는 것입니다.

$$h = W_0 x + \Delta W x = W_0 x + BA x$$

다음은 논문에서 제시한 LoRA의 재매개변수화(reparametrization) 구조를 나타낸 원본 다이어그램입니다.

![LoRA 저랭크 어댑터의 재매개변수화 구조](figures/fig_1.png)
*LoRA의 재매개변수화 구조. 사전학습된 가중치 $W \in \mathbb{R}^{d \times d}$는 동결하고, 다운 프로젝션 행렬 $A$($\mathcal{N}(0, \sigma^2)$로 초기화)와 업 프로젝션 행렬 $B$(영행렬로 초기화)만 학습한다. 학습 시작 시 $BA = 0$이므로 사전학습 모델의 출력에서 점진적으로 적응이 이루어진다.*

여기서 각 변수의 의미는 다음과 같습니다.

- $W_0 \in \mathbb{R}^{d \times k}$: 동결된 사전학습 가중치 (그래디언트 계산하지 않음)
- $A \in \mathbb{R}^{r \times k}$: 다운 프로젝션 행렬 (랜덤 가우시안 초기화)
- $B \in \mathbb{R}^{d \times r}$: 업 프로젝션 행렬 (영행렬로 초기화)
- $r \ll \min(d, k)$: 랭크 하이퍼파라미터 (일반적으로 1, 2, 4, 8, 16, 64 중 선택)

이 구조에서 입력 $x$는 먼저 $A$에 의해 $k$차원에서 $r$차원으로 축소(다운 프로젝션)된 후, $B$에 의해 다시 $d$차원으로 복원(업 프로젝션)됩니다. 이는 $\Delta W = BA$가 최대 랭크 $r$을 가지도록 제한하는 것과 동치입니다.

### 초기화 전략

LoRA의 초기화 방식은 학습 안정성에 매우 중요한 역할을 합니다.

- $A$: 가우시안 분포 $\mathcal{N}(0, \sigma^2)$로 랜덤 초기화 (Kaiming uniform 변형도 사용)
- $B$: 영행렬(zero matrix)로 초기화

이렇게 하면 학습 시작 시점에서 $\Delta W = BA = 0$이 되어, 모델의 출력이 사전학습된 원본 모델과 정확히 동일합니다. 이는 학습 초기의 안정성을 보장하는 핵심 설계입니다. 무작위 초기화로 시작하는 Adapter와 달리, LoRA는 사전학습된 모델의 출력을 정확한 시작점으로 삼아 점진적으로 적응해 나갑니다.

### 스케일링 팩터

실제 구현에서는 $\Delta W$에 스케일링 팩터 $\frac{\alpha}{r}$을 적용합니다.

$$h = W_0 x + \frac{\alpha}{r} BA x$$

여기서 $\alpha$는 고정된 상수(하이퍼파라미터)이며, 보통 $\alpha = r$로 설정하여 스케일링이 1이 되도록 합니다. 이 스케일링의 목적은 랭크 $r$을 변경할 때 학습률(learning rate)을 재조정할 필요가 없도록 하는 것입니다. $r$이 커지면 각 랭크가 기여하는 정도가 작아져야 하므로 $\frac{1}{r}$로 정규화하고, $\alpha$는 전체적인 LoRA 업데이트의 크기를 제어합니다.

실무에서는 $\alpha = 2r$이나 $\alpha = 32$ 같은 값을 사용하는 경우도 많으며, 이는 태스크와 모델에 따라 튜닝이 필요합니다.

### 파라미터 수 비교 분석

저랭크 분해의 파라미터 효율성을 구체적인 숫자로 분석해 보겠습니다.

단일 가중치 행렬 $W \in \mathbb{R}^{d \times k}$에 대해:

- 전체 파인튜닝: $d \times k$ 개의 학습 파라미터
- LoRA: $d \times r + r \times k$ 개의 학습 파라미터
- 압축 비율: $\frac{dk}{dr + rk} = \frac{dk}{r(d+k)}$

$d = k$인 정방행렬의 경우:

$$\text{압축 비율} = \frac{d^2}{2dr} = \frac{d}{2r}$$

구체적인 예시:

| 모델 | $d$ | $r$ | 전체 파라미터 | LoRA 파라미터 | 압축 비율 |
|------|-----|-----|-------------|-------------|--------|
| GPT-2 (768) | 768 | 8 | 589,824 | 12,288 | 48x |
| GPT-3 (12,288) | 12,288 | 4 | 150,994,944 | 98,304 | 1,536x |
| GPT-3 (12,288) | 12,288 | 8 | 150,994,944 | 196,608 | 768x |
| LLaMA-70B (8,192) | 8,192 | 16 | 67,108,864 | 262,144 | 256x |

GPT-3 175B 전체 모델 기준으로 보면, 96개 트랜스포머 레이어의 $W_q$와 $W_v$에 $r=4$로 LoRA를 적용하면 학습 파라미터는 약 4.7M개로, 전체 175B 대비 약 **37,000배 감소**합니다.

## 방법론

### 적용 대상 레이어 선택

트랜스포머 아키텍처에서 LoRA를 적용할 수 있는 가중치 행렬은 크게 두 부류입니다.

**셀프 어텐션 레이어의 프로젝션 행렬:**
- $W_q$ (Query 프로젝션)
- $W_k$ (Key 프로젝션)
- $W_v$ (Value 프로젝션)
- $W_o$ (Output 프로젝션)

**Feed-Forward Network(FFN) 레이어:**
- $W_{\text{up}}$ (업 프로젝션, 보통 $d \rightarrow 4d$)
- $W_{\text{down}}$ (다운 프로젝션, 보통 $4d \rightarrow d$)

논문에서는 GPT-3에 대해 어텐션 가중치만을 대상으로 실험하였으며, 동일한 총 파라미터 예산 하에서 다양한 조합을 비교했습니다.

| 적용 대상 | 랭크 $r$ | 학습 파라미터 | WikiSQL Acc. | MNLI Acc. |
|----------|---------|-------------|-------------|----------|
| $W_q$ 만 | 8 | 1.18M | 70.4 | 91.0 |
| $W_k$ 만 | 8 | 1.18M | 70.0 | 90.4 |
| $W_v$ 만 | 8 | 1.18M | 71.0 | 91.2 |
| $W_q, W_k$ | 4 | 1.18M | 70.8 | 90.7 |
| $W_q, W_v$ | 4 | 1.18M | **73.4** | **91.3** |
| $W_q, W_k, W_v, W_o$ | 2 | 1.18M | 72.6 | 91.0 |

실험 결과, **$W_q$와 $W_v$에 적용하는 것이 가장 효과적**이었습니다. 이는 Query와 Value 프로젝션이 태스크 특화 정보를 가장 잘 포착하기 때문으로 해석됩니다. 특히 동일한 파라미터 예산(1.18M) 하에서 랭크를 낮추더라도 더 많은 가중치 행렬에 분산 적용하는 것이 단일 행렬에 높은 랭크를 부여하는 것보다 효과적이라는 점이 주목할 만합니다. 다만, 최근 실무에서는 모델과 태스크에 따라 모든 선형 레이어(어텐션 + FFN)에 적용하는 것이 더 나은 경우도 보고되고 있습니다.

### 추론 시 가중치 병합 (Weight Merging)

LoRA의 가장 큰 실용적 장점은 추론 시 가중치 병합이 가능하다는 것입니다.

학습이 완료된 후, LoRA 가중치를 원래 가중치에 합산합니다.

$$W = W_0 + \frac{\alpha}{r} BA$$

이렇게 병합된 가중치 $W$는 원래 모델과 동일한 구조와 차원을 가지므로, 추론 시 아키텍처 변경이 전혀 필요 없습니다. 이는 Adapter 방식이 순차적 추가 연산을 필요로 하는 것과 근본적으로 다릅니다.

병합의 이점을 정리하면 다음과 같습니다.

1. **추론 지연 없음**: 원본 모델과 동일한 연산량
2. **배포 단순화**: 특별한 추론 프레임워크 불필요
3. **하드웨어 최적화 호환**: TensorRT, ONNX 등 기존 최적화 도구와 완벽 호환

### 다중 태스크 서빙 전략

LoRA는 다중 태스크 환경에서 특히 효율적입니다. 기반 모델 $W_0$를 GPU에 한 번만 로드한 상태에서, 태스크별 LoRA 가중치($B_i$, $A_i$)만 교체하면 됩니다.

$$W_{\text{task}_i} = W_0 + \frac{\alpha}{r} B_i A_i$$

저장 및 전환 비용을 비교하면 다음과 같습니다.

| 항목 | 전체 파인튜닝 | LoRA ($r=8$) |
|------|-------------|-------------|
| GPT-3 태스크별 저장 | 약 350GB | 약 35MB |
| 10개 태스크 총 저장 | 약 3.5TB | 약 350MB + 기반 모델 350GB |
| 태스크 전환 시간 | 수 분 (모델 전체 로드) | 수 밀리초 ($BA$ 교체) |

이러한 효율성 덕분에 단일 서버에서 수백 개의 LoRA 어댑터를 동시에 서빙하는 것이 가능하며, 이를 활용한 시스템으로 S-LoRA, Punica 등이 연구되었습니다.

### LoRA와 전체 파인튜닝의 관계

이론적으로 랭크 $r$을 $\min(d, k)$까지 올리면 LoRA의 표현력은 전체 파인튜닝과 동일해집니다. 즉, LoRA는 전체 파인튜닝의 일반화(generalization)로 볼 수 있으며, $r$을 통해 정규화(regularization)의 강도를 조절하는 것과 같습니다. 낮은 $r$은 강한 정규화 효과를 가져 과적합(overfitting)을 방지하는 데 도움이 됩니다.

## 실험 결과

### GPT-3 175B 자연어 생성 태스크

논문의 가장 인상적인 실험은 GPT-3 175B에 대한 자연어 생성(NLG) 태스크입니다. E2E NLG Challenge, WebNLG, DART 세 가지 벤치마크에서 평가하였습니다.

| 방법 | 학습 파라미터 | GPU 메모리 | E2E (BLEU) | WebNLG (BLEU) | DART (BLEU) |
|------|------------|----------|-----------|--------------|------------|
| FT (전체) | 175.0B | ~1.2TB | 68.2 | 46.2 | 46.0 |
| BitFit | 14.0M | ~350GB | 67.2 | 45.3 | 45.1 |
| Prefix Emb. | 0.8M | ~350GB | 66.4 | 44.7 | 43.5 |
| Prefix Layer | 20.2M | ~350GB | 66.6 | 45.3 | 44.1 |
| Adapter (H=256) | 40.1M | ~350GB | 66.3 | 45.9 | 45.2 |
| Adapter (H=64) | 11.1M | ~350GB | 66.9 | 44.7 | 44.5 |
| LoRA ($r=4$) | **4.7M** | ~350GB | **70.4** | **46.8** | **47.1** |
| LoRA ($r=8$) | 9.4M | ~350GB | 70.1 | 47.0 | 47.0 |

주목할 점은 LoRA가 전체 파인튜닝보다 파라미터를 **37,000배 이상** 줄이면서도, E2E에서 BLEU 70.4로 전체 파인튜닝(68.2)을 **2.2점 초과**했다는 것입니다. 이는 저랭크 제약이 일종의 정규화 역할을 하여 과적합을 방지한 결과로 해석됩니다.

아래 그림은 다양한 PEFT 방법들의 학습 파라미터 수 대비 성능을 시각적으로 비교한 것으로, LoRA의 파라미터 효율성이 타 방법 대비 얼마나 우수한지를 명확히 보여줍니다.

![GPT-3 175B에서 학습 파라미터 수 대비 WikiSQL 및 MNLI 검증 정확도 비교](figures/fig_2.png)
*GPT-3 175B에서의 학습 가능 파라미터 수 대비 WikiSQL(좌) 및 MNLI-matched(우) 검증 정확도. LoRA는 적은 파라미터로도 높은 성능을 달성하며, Adapter나 Prefix Tuning 대비 파레토 최적에 가까운 확장성을 보인다.*

### RoBERTa / DeBERTa GLUE 벤치마크

자연어 이해(NLU) 태스크에 대해서도 LoRA는 경쟁력 있는 결과를 보였습니다.

**RoBERTa-base (125M) 결과:**

| 방법 | 학습 파라미터 | MNLI | SST-2 | MRPC | CoLA | QNLI | QQP | RTE | STS-B | 평균 |
|------|------------|------|-------|------|------|------|-----|-----|-------|------|
| FT | 125.0M | 87.6 | 94.8 | 90.2 | 63.6 | 92.8 | 91.9 | 78.7 | 91.2 | 86.4 |
| Adapter (H=64) | 0.9M | 87.1 | 94.2 | 89.5 | 62.6 | 92.4 | 91.5 | 75.9 | 90.3 | 85.4 |
| LoRA ($r=8$) | 0.3M | 87.5 | 95.1 | 89.7 | 63.4 | 93.3 | 91.5 | 86.6 | 91.5 | **87.3** |

**DeBERTa-XXL (1.5B) 결과:**

| 방법 | 학습 파라미터 | MNLI | SST-2 | MRPC | CoLA | QNLI | 평균 |
|------|------------|------|-------|------|------|------|------|
| FT | 1.5B | 91.7 | 97.2 | 92.0 | 72.0 | 96.0 | 89.8 |
| LoRA ($r=8$) | 4.7M | 91.9 | 96.9 | 92.6 | 72.4 | 96.6 | **90.1** |

DeBERTa-XXL에서 LoRA는 전체 파인튜닝 대비 학습 파라미터를 **약 320배 줄이면서 오히려 평균 성능이 더 높았습니다**.

### 랭크 민감도 분석

LoRA의 핵심 하이퍼파라미터인 랭크 $r$에 대한 민감도 실험 결과입니다.

| 랭크 $r$ | 학습 파라미터 | WikiSQL (Acc.) | MultiNLI (Acc.) | SAMSum (R1) |
|---------|------------|---------------|----------------|------------|
| 1 | 0.15M | 68.8 | 90.7 | 51.3 |
| 2 | 0.30M | 71.9 | 91.0 | 52.1 |
| 4 | 0.59M | 73.4 | 91.3 | 52.5 |
| 8 | 1.18M | 73.7 | 91.4 | 52.4 |
| 16 | 2.36M | 73.8 | 91.3 | 52.6 |
| 64 | 9.44M | 73.9 | 91.4 | 52.5 |

핵심 관찰 사항:

1. **$r=4$ 이상에서 성능 포화**: $r$을 4에서 64로 16배 올려도 성능 향상은 미미합니다
2. **$r=1$에서도 합리적 성능**: 단일 랭크만으로도 68.8%의 정확도를 달성
3. **태스크별 최적 $r$ 상이**: 복잡한 태스크일수록 약간 높은 $r$이 유리한 경향

이 결과는 내재적 저랭크 가설을 강력히 뒷받침하며, 대부분의 태스크에서 $r \in [4, 16]$ 범위가 비용 대비 최적의 선택임을 시사합니다.

### 학습된 $\Delta W$의 랭크 분석

논문은 학습된 $\Delta W$가 실제로 낮은 랭크를 가지는지를 특이값 분해(SVD)를 통해 검증했습니다. 서로 다른 랭크 $r$로 학습한 LoRA 행렬 간의 부분공간 유사도(subspace similarity)를 측정한 결과, $r=8$과 $r=64$로 학습한 행렬의 상위 랭크-4 부분공간이 매우 높은 유사도를 보였습니다. 이는 가중치 업데이트의 핵심 정보가 매우 낮은 차원의 부분공간에 집중되어 있음을 의미합니다.

아래 그림은 이 분석의 핵심 결과를 보여줍니다. $r=8$로 학습한 행렬 $A$의 상위 특이 방향들이 $r=64$로 학습한 행렬에도 거의 그대로 포함되어 있어, 파인튜닝에 필요한 핵심 부분공간이 극히 저차원임을 시각적으로 확인할 수 있습니다.

![r=8과 r=64에서 학습된 LoRA 행렬의 부분공간 유사도](figures/fig_3.png)
*$\Delta W_q$와 $\Delta W_v$에서 $r=8$과 $r=64$로 학습한 행렬 $A$의 열 벡터 간 부분공간 유사도 $\phi(A_{r=64}, A_{r=8}, i, j)$. 좌측 두 패널은 전체 유사도 행렬, 우측 두 패널은 좌하단 삼각 영역을 확대한 것이다. $r=8$의 상위 방향이 $r=64$에서도 보존되며, 이는 $\Delta W$의 내재적 랭크가 매우 낮음을 의미한다.*

## 의의 및 한계

### 의의

**1. 파라미터 효율적 파인튜닝의 표준 확립**

LoRA는 PEFT 분야의 사실상 표준(de facto standard)이 되었습니다. 단순하고 직관적인 방법론, 추론 지연 없음, 뛰어난 성능이라는 삼박자를 갖추어 학계와 산업계 모두에서 폭넓게 채택되었습니다.

**2. LLM 민주화에 기여**

GPT-3급 모델의 파인튜닝에 필요한 자원을 수십 배 이상 줄여, 대규모 GPU 클러스터 없이도 개인 연구자나 소규모 팀이 LLM을 커스터마이징할 수 있는 길을 열었습니다.

**3. 방대한 후속 연구의 촉발**

LoRA를 기반으로 수많은 변형 기법들이 제안되었습니다.

- **QLoRA (Dettmers et al., 2023)**: 4비트 양자화와 LoRA를 결합하여 GPU 메모리를 추가로 4배 이상 절감. 단일 48GB GPU에서 65B 파라미터 모델 파인튜닝 가능
- **DoRA (Liu et al., 2024)**: 가중치를 크기(magnitude)와 방향(direction)으로 분리하여 방향 성분에만 LoRA를 적용. 전체 파인튜닝의 학습 패턴에 더 가까운 동작
- **AdaLoRA (Zhang et al., 2023)**: 레이어별로 중요도에 따라 랭크를 동적으로 할당
- **LoftQ (Li et al., 2023)**: 양자화 오차를 LoRA 초기화로 보상하여 QLoRA의 성능 격차를 줄임
- **LoRA+ (Hayou et al., 2024)**: $A$와 $B$ 행렬에 서로 다른 학습률을 적용하여 학습 효율 향상

**4. 다양한 도메인으로의 확장**

LoRA는 원래 NLP 태스크를 위해 설계되었지만, 다양한 도메인에서 핵심 기술로 활용되고 있습니다.

- **이미지 생성**: Stable Diffusion, SDXL의 스타일/캐릭터 커스터마이징
- **코드 생성**: Code LLaMA, StarCoder의 도메인 특화
- **의료 AI**: 의학 텍스트에 특화된 LLM 파인튜닝 (Med-PaLM 등)
- **멀티모달**: LLaVA 등 비전-언어 모델의 효율적 학습

**5. 풍부한 생태계**

HuggingFace의 PEFT 라이브러리를 중심으로 방대한 오픈소스 생태계가 형성되었습니다. HuggingFace Hub에는 수만 개의 LoRA 어댑터가 공유되고 있으며, vLLM, TGI 등 추론 프레임워크에서도 LoRA를 기본 지원합니다.

### 한계

**1. 최적 하이퍼파라미터 탐색 필요**

랭크 $r$, 스케일링 팩터 $\alpha$, 적용 대상 레이어의 최적 조합은 모델과 태스크에 따라 달라집니다. 체계적인 하이퍼파라미터 탐색이 필요하며, 이 자체가 추가적인 계산 비용을 발생시킵니다.

**2. 전체 파인튜닝 대비 성능 격차가 존재하는 경우**

태스크의 도메인이 사전학습 데이터와 크게 다르거나(예: 희소 언어, 전문 과학 용어), 모델이 근본적으로 새로운 지식을 습득해야 하는 경우에는 저랭크 가정이 성립하지 않을 수 있습니다. 이러한 경우 전체 파인튜닝이나 높은 랭크의 LoRA가 필요합니다.

**3. 다중 LoRA 어댑터의 합성 한계**

서로 다른 태스크로 학습된 LoRA 어댑터들을 단순히 합산하면 성능이 저하될 수 있습니다. LoRA 어댑터 간의 간섭(interference)을 최소화하는 합성 방법은 여전히 활발한 연구 주제입니다.

**4. 동적 추론 시의 오버헤드**

가중치 병합 없이 LoRA를 동적으로 적용하면(예: 배치 내에서 서로 다른 LoRA 적용), 추가 연산이 필요합니다. 대규모 서빙 환경에서 수천 개의 LoRA를 동시에 관리하는 것은 여전히 엔지니어링 과제입니다.

## 코드 예제

### LoRA 레이어의 직접 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import math

class LoRALayer(nn.Module):
    """LoRA 레이어: 가중치 변화량을 저랭크 행렬 BA로 근사.

    수식: delta_W = (alpha / r) * B @ A
    초기화: B=0, A=Kaiming uniform -> 학습 시작 시 delta_W = 0
    """
    def __init__(self, in_features: int, out_features: int,
                 rank: int = 4, alpha: float = 16.0, dropout: float = 0.0):
        super().__init__()
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank  # 스케일링 팩터

        # A: 다운 프로젝션 (in_features -> rank)
        self.lora_A = nn.Linear(in_features, rank, bias=False)
        # B: 업 프로젝션 (rank -> out_features)
        self.lora_B = nn.Linear(rank, out_features, bias=False)

        # 초기화: A는 Kaiming, B는 0 -> 초기 delta_W = 0
        nn.init.kaiming_uniform_(self.lora_A.weight, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B.weight)

        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # delta_W @ x = B(A(dropout(x))) * scaling
        return self.lora_B(self.lora_A(self.dropout(x))) * self.scaling


class LinearWithLoRA(nn.Module):
    """기존 Linear 레이어에 LoRA를 추가한 래퍼.
    원본 가중치는 동결, LoRA 파라미터만 학습.
    h = W0 @ x + (alpha/r) * B @ A @ x
    """
    def __init__(self, linear: nn.Linear, rank: int = 4, alpha: float = 16.0):
        super().__init__()
        self.linear = linear
        self.lora = LoRALayer(
            linear.in_features, linear.out_features, rank, alpha
        )
        # 원본 가중치 동결
        for param in self.linear.parameters():
            param.requires_grad = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x) + self.lora(x)  # W0*x + BA*x

    def merge_weights(self):
        """추론 최적화: LoRA 가중치를 원래 가중치에 병합.
        병합 후 추가 연산 없이 원본과 동일한 속도로 추론 가능.
        """
        with torch.no_grad():
            # delta_W = B.weight @ A.weight * scaling
            delta_W = (
                self.lora.lora_B.weight
                @ self.lora.lora_A.weight
                * self.lora.scaling
            )
            self.linear.weight.data += delta_W

    def get_lora_params(self) -> int:
        """LoRA 학습 파라미터 수 반환."""
        return sum(p.numel() for p in self.lora.parameters())


def apply_lora_to_model(
    model: nn.Module,
    rank: int = 4,
    alpha: float = 16.0,
    target_modules: list = None
) -> nn.Module:
    """모델의 특정 레이어에 LoRA를 자동 적용.

    Args:
        model: 대상 모델
        rank: LoRA 랭크
        alpha: 스케일링 팩터
        target_modules: LoRA를 적용할 모듈 이름 리스트
    """
    if target_modules is None:
        target_modules = ['q_proj', 'v_proj']  # 기본: Query, Value만

    for name, module in list(model.named_modules()):
        if any(target in name for target in target_modules):
            if isinstance(module, nn.Linear):
                parent = model
                parts = name.split('.')
                for part in parts[:-1]:
                    parent = getattr(parent, part)
                setattr(
                    parent, parts[-1],
                    LinearWithLoRA(module, rank, alpha)
                )

    # 학습 파라미터 통계
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"전체 파라미터: {total:,}")
    print(f"학습 파라미터: {trainable:,} ({trainable/total*100:.4f}%)")

    return model
```

### HuggingFace PEFT 라이브러리 활용

실무에서는 HuggingFace의 PEFT 라이브러리를 사용하여 몇 줄의 코드로 LoRA를 적용할 수 있습니다.

```python
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, Trainer
)
from datasets import load_dataset

# 1. 기반 모델 로드
model_name = "meta-llama/Llama-2-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto",  # 자동 GPU 할당
)

# 2. LoRA 설정
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,                    # 랭크 (4~64, 보통 8~16)
    lora_alpha=32,           # 스케일링 alpha (보통 2*r)
    lora_dropout=0.05,       # 드롭아웃
    target_modules=[
        "q_proj", "v_proj",  # 어텐션 Q, V 프로젝션
        "k_proj", "o_proj",  # 선택적: K, O 프로젝션
        "gate_proj",         # 선택적: FFN 게이트
        "up_proj", "down_proj",  # 선택적: FFN 업/다운
    ],
    bias="none",             # bias 학습 안 함
    modules_to_save=None,    # 전체 학습할 모듈 (예: embed, lm_head)
)

# 3. LoRA 적용
peft_model = get_peft_model(model, lora_config)
peft_model.print_trainable_parameters()
# 출력 예시: trainable params: 33,554,432 || all params: 6,771,970,048
#           || trainable%: 0.4957

# 4. 학습
training_args = TrainingArguments(
    output_dir="./lora-llama2-output",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    learning_rate=2e-4,      # LoRA에 적합한 학습률
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
)

trainer = Trainer(
    model=peft_model,
    args=training_args,
    train_dataset=train_dataset,
    tokenizer=tokenizer,
)
trainer.train()

# 5. 어댑터 저장 (수 MB ~ 수십 MB)
peft_model.save_pretrained("./lora-adapter")

# 6. 추론 시 로드
base_model = AutoModelForCausalLM.from_pretrained(model_name)
inference_model = PeftModel.from_pretrained(base_model, "./lora-adapter")

# 7. 가중치 병합 (선택적 - 추론 최적화)
merged_model = inference_model.merge_and_unload()
merged_model.save_pretrained("./merged-model")
```

### QLoRA와의 결합 (4비트 양자화 + LoRA)

```python
from transformers import BitsAndBytesConfig
import torch

# 4비트 양자화 설정
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",      # NormalFloat4
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,  # 이중 양자화
)

# 4비트로 모델 로드
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-70b-hf",
    quantization_config=bnb_config,
    device_map="auto",
)

# QLoRA = 4비트 양자화 모델 + LoRA
# 단일 A100 80GB GPU에서 70B 파라미터 모델 파인튜닝 가능
qlora_config = LoraConfig(
    r=64,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)
peft_model = get_peft_model(model, qlora_config)
```

## 관련 문서

- [[qlora|QLoRA: Efficient Finetuning of Quantized LLMs]] -- 후속 모델
