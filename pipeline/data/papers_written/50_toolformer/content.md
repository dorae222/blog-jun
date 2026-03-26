## 개요

**Toolformer: Language Models Can Teach Themselves to Use Tools** (Schick et al., 2023)는 Meta AI Research에서 발표한 논문으로, NeurIPS 2023에 채택되었습니다. 이 연구는 언어 모델(LM)이 **외부 도구(API)**를 **자기 지도(self-supervised) 방식**으로 학습하여 활용할 수 있음을 체계적으로 보여줍니다.

대규모 언어 모델(LLM)은 방대한 텍스트 데이터로 사전학습되어 언어 이해와 생성에서 뛰어난 능력을 보이지만, 학습 시점에 고정된 파라미터에 지식이 인코딩되어 있어 여러 근본적인 한계를 가집니다. 최신 정보 검색, 정확한 수치 계산, 다국어 번역 등의 과제에서 언어 모델은 구조적으로 어려움을 겪습니다. Toolformer는 이러한 한계를 극복하기 위해, LLM 자체를 활용하여 텍스트 내에서 도구 호출이 유용한 위치를 자동으로 식별하고, 그 정보를 파인튜닝 데이터로 활용하는 방법을 제안합니다.

핵심 결과로, GPT-J(6.7B) 기반 Toolformer가 Calculator, Wikipedia Search, QA 시스템, 번역기, Calendar라는 5가지 도구를 활용하여, 수학 추론(SVAMP)에서 GPT-3(175B)를 **2배 이상 능가**하고, 사실 질의응답(TriviaQA)에서도 GPT-3를 **3.6%p 초과**하는 제로샷 성능을 달성합니다. 파라미터 수가 약 26배 적은 모델이 도구 활용만으로 더 큰 모델을 압도하는 결과는, 파라미터 스케일링 이외의 성능 향상 경로가 실재함을 보여주는 중요한 증거입니다.

![Toolformer 자기 지도 도구 학습 파이프라인 전체 구조](figures/architecture.png)
*Toolformer의 자기 지도 도구 학습 파이프라인. API 호출 위치 샘플링, 외부 도구 실행, 손실 기반 필터링, 증강 데이터 파인튜닝의 4단계로 구성되며, Calculator, QA, Search, Translator, Calendar 5가지 외부 도구를 활용한다.*

## 배경 및 문제

### 언어 모델의 구조적 한계

대규모 언어 모델은 방대한 텍스트 코퍼스에서 다음 토큰을 예측하는 방식으로 학습됩니다. 이 패러다임은 언어 이해와 생성에서 놀라운 성과를 보이지만, 본질적인 제약을 수반합니다.

**지식의 시점 제한(Knowledge Cutoff)**: 학습이 완료된 이후에 발생한 사건이나 변경된 정보에 대해서는 정확한 답변을 제공할 수 없습니다. 2022년에 학습이 종료된 모델은 2023년의 사건에 대해 정확히 답할 수 없으며, 이는 모델의 파라미터를 갱신하지 않는 한 해결할 수 없는 문제입니다.

**수치 연산의 부정확성**: 언어 모델은 토큰 단위의 패턴 매칭으로 학습되므로, 복잡한 수학 연산을 정확히 수행하는 것이 구조적으로 어렵습니다. 예를 들어 $347 \times 892 = 309,524$와 같은 곱셈은 학습 데이터에서 이 정확한 조합을 본 적이 없다면 올바르게 계산하기 어렵습니다. 더 일반적으로, 다단계 산술 연산이 필요한 서술형 문제에서 오류가 누적되는 현상이 빈번합니다.

**환각(Hallucination)**: 모델이 학습 데이터에 포함되지 않았거나 빈도가 낮은 사실에 대해 그럴듯하지만 틀린 답변을 생성하는 현상은 잘 알려진 문제입니다. 특히 long-tail 지식에 대한 질문에서 이 문제가 두드러집니다.

**다국어 처리의 불균형**: 영어 중심의 학습 데이터로 인해 저자원 언어(low-resource language)에 대한 성능이 크게 떨어집니다. 이는 영어 이외의 언어로 된 텍스트를 이해하거나 생성할 때 정보 손실로 이어집니다.

### 기존 도구 활용 접근법의 한계

Toolformer 이전에도 언어 모델에 외부 도구를 연결하려는 시도들이 있었습니다. 이들 접근법은 크게 세 가지로 분류할 수 있습니다.

**인간 주석 의존 방식**: WebGPT(Nakano et al., 2021)와 LaMDA(Thoppilan et al., 2022)는 인간이 직접 도구 사용 예시를 작성하여 학습 데이터를 구성합니다. 고품질 데이터를 확보할 수 있지만, 확장성에 근본적인 한계가 있으며 새로운 도구를 추가할 때마다 비용이 높은 주석 작업이 필요합니다.

**작업 특화 파인튜닝**: Karpas et al.(2022)의 MRKL 시스템이나 Cobbe et al.(2021)의 계산기 활용 방식은 특정 작업에 대해서만 도구를 사용하도록 학습됩니다. 도구 사용의 일반성을 확보하지 못하며, 모델이 스스로 언제 도구를 사용할지 결정하지 못합니다.

**프롬프트 엔지니어링 기반 방식**: [[react|ReAct]](Yao et al., 2022)와 같은 방식은 프롬프트에 도구 사용 지시를 포함하여 인컨텍스트 학습으로 도구 호출을 유도합니다. 별도의 파인튜닝 없이 사용할 수 있지만, 프롬프트 길이 제한과 불안정한 출력이 문제입니다.

Toolformer는 이 세 가지 접근법의 한계를 동시에 극복합니다.

| 문제 | 기존 방식 | Toolformer |
|------|-----------|------------|
| 학습 데이터 생성 | 인간 주석 필요 | 자기 지도 자동 생성 |
| 도구 사용 시점 결정 | 규칙 기반 / 수동 | 모델 자율 결정 |
| 새 도구 추가 비용 | 높음 (재주석) | 낮음 (few-shot 예시만) |
| 언어 능력 유지 | 작업 특화로 저하 가능 | 원본 성능 보존 |
| 범용성 | 특정 작업에 제한 | 다양한 작업에 적용 |

## 핵심 아이디어: Self-Supervised Tool Learning

Toolformer의 핵심 아이디어는 한 문장으로 요약할 수 있습니다: **도구 사용의 유용성을 언어 모델링 손실로 직접 측정하여, 유용한 경우에만 학습 데이터에 포함시킨다.**

이 아이디어는 정보 이론적으로 명확한 근거를 가집니다. 언어 모델의 목표는 다음 토큰에 대한 예측 확률을 최대화하는 것, 즉 cross-entropy 손실을 최소화하는 것입니다.

$$\mathcal{L}(\theta) = -\sum_{t=1}^{T} \log P_{\theta}(x_t \mid x_{<t})$$

여기서 $x_t$는 시퀀스의 $t$번째 토큰이고, $x_{<t}$는 그 이전까지의 토큰 시퀀스입니다. 만약 특정 위치 $i$에 API 호출 결과 $r$을 삽입했을 때 후속 토큰들의 예측 손실이 유의미하게 감소한다면, 해당 API 호출은 모델에게 실질적으로 유용한 정보를 제공하는 것입니다.

이를 형식화하면, 위치 $i$에서의 API 호출 $c_i$의 유용성은 다음과 같이 정의됩니다.

$$\Delta L_i(c_i) = L_i(\text{without tool}) - L_i(\text{with tool result})$$

$\Delta L_i > 0$이면 API 호출이 유용하며, 이 값이 임계값 $\tau$ 이상이면 해당 호출은 학습 데이터에 포함됩니다.

이 self-supervised 접근법의 핵심 장점은 **도구의 유용성을 객관적으로 측정**할 수 있다는 것입니다. 인간의 주관적 판단이 아니라, 언어 모델링이라는 명확한 목적 함수에 기반하여 도구 사용 여부를 결정합니다. 또한 이 방식은 **도구에 구애받지 않습니다(tool-agnostic)** -- 어떤 종류의 API든 텍스트 입출력만 가능하면 동일한 프레임워크에 통합할 수 있습니다.

이 아이디어의 우아함은 순환적 자기 참조에 있습니다. 언어 모델의 성능을 개선하기 위해 도구를 도입하는데, 어떤 도구 호출이 유용한지를 판단하는 것도 언어 모델 자체의 손실 함수를 통해 이루어집니다. 외부의 인간 평가자나 별도의 판별 모델이 필요 없습니다.

## 방법론

Toolformer의 전체 파이프라인은 세 단계로 구성됩니다: (1) API 호출 후보 생성(Sampling), (2) 유용성 기반 필터링(Filtering), (3) 증강 데이터로 파인튜닝(Fine-tuning).

### API 호출 표현 방식

Toolformer는 도구 호출을 텍스트 시퀀스 내에 특수 토큰으로 인라인 삽입합니다. 호출 형식은 다음과 같습니다.

$$\langle \text{API} \rangle \; a_c(i_c) \rightarrow r \; \langle /\text{API} \rangle$$

여기서 $a_c$는 API 이름, $i_c$는 입력 인자, $r$은 반환값입니다. 특수 토큰 $\langle \text{API} \rangle$와 $\langle /\text{API} \rangle$는 API 호출의 시작과 끝을 표시합니다.

![Toolformer의 다양한 API 호출 인라인 삽입 예시](figures/fig_1.png)
*Toolformer의 예시 출력. 모델이 자율적으로 QA 시스템, Calculator, 번역기(MT), Wikipedia 검색 등 다양한 API를 호출하여 텍스트 완성에 필요한 정보를 획득한다. 각 도구는 색상으로 구분되며, 호출 결과가 텍스트에 인라인으로 삽입된다. (Schick et al., 2023, Figure 1)*

이 인라인 삽입 방식의 장점은 언어 모델의 기존 아키텍처를 전혀 변경할 필요가 없다는 것입니다. API 호출은 단순히 추가 토큰으로 처리되며, 기존의 next-token prediction 학습 방식이 그대로 유지됩니다. 구체적 예시는 다음과 같습니다.

```
The Eiffel Tower is [WikiSearch("Eiffel Tower") -> a wrought-iron lattice
tower on the Champ de Mars in Paris] 330 metres tall.
```

```
Out of 1400 items, [Calculator(1400 / 100) -> 14] were selected.
```

```
Today is [Calendar() -> January 15, 2023] a national holiday.
```

### 1단계: API 호출 후보 생성 (Sampling)

원본 텍스트 시퀀스 $x = x_1, x_2, \ldots, x_n$의 각 위치 $i$에서 API 호출 후보를 생성합니다.

**Few-shot 프롬프트 구성**: 각 도구에 대해 3-5개의 인컨텍스트 예시를 포함한 프롬프트를 구성합니다. 이 예시들은 "원본 텍스트에 API 호출을 삽입한 형태"로 작성됩니다. 아래 그림은 QA 도구에 대한 실제 프롬프트 예시로, 모델이 텍스트 내에서 질문을 생성하여 API를 호출하는 패턴을 학습하는 방식을 보여줍니다.

![QA 도구에 대한 few-shot 프롬프트 예시](figures/fig_3.png)
*Figure 3: QA 도구를 위한 프롬프트 $P(\mathbf{x})$ 구성 예시 -- 입력 텍스트에 대해 API 호출을 삽입하는 방법을 보여주는 인컨텍스트 예시로, 모델이 사실적 정보가 필요한 위치에서 적절한 질문을 생성하여 QA API를 호출하도록 유도한다. (Schick et al., 2023)*

예를 들어 Calculator의 경우:

```
입력: He was 47 when he died, so he was born in 1990 - 47 = 1943.
출력: He was 47 when he died, so he was born in
  [Calculator(1990 - 47) -> 1943] 1943.
```

**위치 선정**: 모든 토큰 위치에서 API 호출을 시도하면 계산 비용이 막대하므로, 효율적인 사전 필터링이 필요합니다. 모델이 API 호출 시작 토큰 $\langle \text{API} \rangle$를 생성할 확률이 충분히 높은 위치만을 후보로 선정합니다.

**후보 샘플링**: 선정된 각 위치 $i$에서 최대 $k = 5$개의 서로 다른 API 호출 후보 $c_{i,1}, c_{i,2}, \ldots, c_{i,k}$를 top-$k$ 샘플링으로 생성합니다. 각 후보는 API 이름과 입력 인자의 쌍 $(a_c, i_c)$입니다.

### 2단계: 유용성 기반 필터링 (Filtering)

이 단계가 Toolformer의 핵심 혁신입니다. 생성된 모든 API 호출 후보 중에서 실제로 언어 모델링 성능을 개선하는 것만 남깁니다.

![Toolformer의 API 호출 후보 샘플링과 손실 기반 필터링 과정](figures/fig_2.png)
*Toolformer의 핵심 파이프라인. 입력 텍스트에서 위치 $i$를 선정하고 API 호출 후보 $c_i^1, c_i^2, \ldots, c_i^k$를 샘플링한 뒤, 실행 결과를 포함했을 때 손실 $L_i$가 감소하는 호출만 선별하여 증강 데이터 $\mathbf{x}^*$를 구성한다. (Schick et al., 2023, Figure 2)*

각 후보 $c_i$에 대해 먼저 실제로 API를 호출하여 결과 $r_i$를 얻습니다. 그런 다음 세 가지 조건에서의 weighted cross-entropy 손실을 계산합니다.

**조건 1 -- API 호출 결과 포함 ($L_i^+$)**: API 호출 구문과 그 결과를 모두 포함한 상태에서 위치 $i$ 이후 토큰들의 손실을 계산합니다.

$$L_i^+ = -\sum_{j=i}^{n} w_j \cdot \log P_{\theta}\left(x_j \mid x_{<i}, e(c_i, r_i), x_{i:j-1}\right)$$

여기서 $e(c_i, r_i)$는 API 호출 $c_i$와 결과 $r_i$를 포함한 시퀀스이고, $w_j$는 위치 $j$의 가중치입니다.

**조건 2 -- API 호출 없음 ($L_i^-$)**: 원래 텍스트 그대로, API 호출이 없는 상태에서의 손실입니다.

$$L_i^- = -\sum_{j=i}^{n} w_j \cdot \log P_{\theta}\left(x_j \mid x_{<j}\right)$$

**조건 3 -- API 호출 구문만, 결과 없음 ($L_i^\emptyset$)**: API 호출 구문은 삽입하되 반환 결과를 빈 문자열로 대체한 상태에서의 손실입니다.

$$L_i^\emptyset = -\sum_{j=i}^{n} w_j \cdot \log P_{\theta}\left(x_j \mid x_{<i}, e(c_i, \epsilon), x_{i:j-1}\right)$$

**최종 필터링 조건**:

$$L_i^+ + \tau \leq \min\left(L_i^-, L_i^\emptyset\right)$$

논문에서는 $\tau = 1.0$을 사용합니다. 이 조건의 의미를 분해하면 다음과 같습니다.

- $L_i^+ < L_i^-$: API 결과가 있을 때 없을 때보다 후속 토큰 예측이 더 정확해야 합니다.
- $L_i^+ < L_i^\emptyset$: API **결과 자체**가 도움이 되어야 합니다. 단순히 API 호출 구문이 존재하는 것만으로는 부족합니다.
- $\tau = 1.0$: 개선 폭이 이 임계값 이상이어야 합니다. 미미한 개선은 노이즈일 가능성이 높으므로 배제합니다.

$L_i^\emptyset$를 별도로 계산하는 이유는 중요합니다. 일부 경우 API 호출 구문 자체가 일종의 "힌트"로 작용할 수 있습니다. 예를 들어, `[Calculator(` 라는 토큰이 나타나면 "다음에는 숫자가 올 것"이라는 단서가 됩니다. $L_i^\emptyset$와의 비교는 이러한 편향을 제거하여, API의 **실제 반환 결과**가 정보적 가치를 가지는 경우만 선별합니다.

### 3단계: 증강 데이터로 파인튜닝 (Fine-tuning)

필터링을 통과한 API 호출들을 원본 텍스트에 삽입하여 증강된 데이터셋 $\mathcal{C}^*$를 구성합니다. 이 데이터셋으로 GPT-J(6.7B)를 표준 언어 모델링 목적함수로 파인튜닝합니다.

**학습 데이터 구성 세부사항**:
- 원본 말뭉치: CCNet의 일부(약 수백만 문서)
- 각 도구별로 독립적으로 API 호출을 샘플링하고 필터링
- 한 문장에 여러 도구의 호출이 동시에 포함될 수 있음
- 필터링 통과율: Calculator 약 12%, WikiSearch 약 4% (도구마다 상이)
- 증강 데이터와 원본 데이터를 혼합하여 언어 능력 유지

파인튜닝 과정에서 모델은 다음 네 가지를 동시에 학습합니다.

1. **언제** 도구를 호출할지 (API 시작 토큰의 생성 확률 학습)
2. **어떤** 도구를 사용할지 (API 이름 선택)
3. **무엇을** 입력할지 (API 인자 구성)
4. **결과를 어떻게** 활용할지 (API 결과 이후의 텍스트 생성)

### 추론 시 동작

파인튜닝된 모델의 추론(inference) 과정은 다음과 같습니다.

1. 모델이 일반 텍스트를 생성하다가 API 시작 토큰 $\langle \text{API} \rangle$를 출력합니다.
2. API 이름과 입력 인자가 생성된 후, $\rightarrow$ 토큰이 나타나면 디코딩을 일시 중지합니다.
3. 파싱된 API 이름과 인자로 해당 도구를 실제 호출하여 결과를 받습니다.
4. 결과를 토큰 시퀀스에 삽입하고 $\langle /\text{API} \rangle$ 토큰을 추가합니다.
5. 이후 일반 텍스트 생성을 재개합니다.

```
입력: "The population of Tokyo is"
생성: "The population of Tokyo is [WikiSearch("population Tokyo")"
  -> 디코딩 중지, API 호출
  -> 결과: "approximately 13.96 million as of 2023"
삽입: "The population of Tokyo is [WikiSearch("population Tokyo")
  -> approximately 13.96 million as of 2023]
  about 14 million."
```

이 과정에서 외부 오케스트레이션 시스템이 필요 없습니다. 모델 자체가 도구 호출 여부, 도구 선택, 입력 구성을 모두 자율적으로 결정합니다.

### 5가지 도구의 구성

| 도구 | API 형식 | 보완하는 한계 | 구현 방식 |
|------|----------|--------------|----------|
| Calculator | `[Calculator(expr) -> result]` | 수치 연산 부정확성 | Python `eval()` |
| Wikipedia Search | `[WikiSearch(query) -> snippet]` | 지식 시점 제한, 환각 | BM25 기반 검색 |
| Machine Translation | `[MT(text, lang) -> translation]` | 다국어 처리 불균형 | NLLB-600M |
| Calendar | `[Calendar() -> date]` | 현재 시간 정보 부재 | 시스템 시계 |
| Question Answering | `[QA(question) -> answer]` | 사실 기반 질의응답 | Atlas(Few-shot QA 모델) |

각 도구는 **텍스트 입력 -> 텍스트 출력** 인터페이스를 가지며, 이 단순한 인터페이스 덕분에 언어 모델의 토큰 시퀀스에 자연스럽게 삽입됩니다. 도구 간에 공유되는 인터페이스가 동일하므로, 새로운 도구를 추가할 때 모델 아키텍처를 변경할 필요가 없습니다.

## 실험 결과

### 평가 설정

- **기반 모델**: GPT-J (6.7B 파라미터, EleutherAI)
- **학습 데이터**: CCNet 서브셋에서 자동 생성된 API 호출 증강 데이터
- **비교 대상**: GPT-J (6.7B, vanilla), OPT (66B), GPT-3 (175B)
- **평가 방식**: 모든 벤치마크에서 **제로샷(zero-shot)** 설정

### 수학 추론 벤치마크

수치 계산이 필요한 수학 추론 벤치마크에서 Toolformer는 Calculator 도구의 활용으로 극적인 성능 향상을 달성합니다.

| 모델 | 파라미터 수 | SVAMP | MAWPS | ASDiv-Aug |
|------|-----------|-------|-------|-----------|
| GPT-J (vanilla) | 6.7B | 6.2% | 18.9% | 12.7% |
| OPT | 66B | 8.7% | 31.8% | 19.3% |
| GPT-3 | 175B | 14.0% | 42.7% | 25.1% |
| **Toolformer** | **6.7B** | **29.4%** | **44.0%** | **40.2%** |

SVAMP에서의 결과가 가장 인상적입니다. Toolformer(6.7B)는 GPT-3(175B) 대비 **2.1배**의 정확도를 달성하며, 파라미터 수는 약 $1/26$에 불과합니다.

$$\frac{\text{Toolformer}_{\text{SVAMP}}}{\text{GPT-3}_{\text{SVAMP}}} = \frac{29.4}{14.0} \approx 2.1\times \quad \text{(모델 크기: } \frac{6.7}{175} \approx 0.038\text{)}$$

ASDiv-Aug에서도 40.2%로 GPT-3(25.1%)를 1.6배 능가합니다. 이 결과는 **도구 사용이 순수 파라미터 스케일링을 특정 과제에서 압도할 수 있음**을 강력히 시사합니다. 다만 MAWPS에서는 GPT-3(42.7%)와 Toolformer(44.0%)의 차이가 상대적으로 작은데, 이는 MAWPS 문제가 단순 계산보다 언어 이해에 더 의존하는 특성 때문으로 분석됩니다.

### 사실 질의응답 벤치마크

Wikipedia 검색 및 QA 도구가 사실 기반 질의응답에 미치는 영향을 평가합니다.

| 모델 | 파라미터 수 | TriviaQA | WebQS | NQ |
|------|-----------|----------|-------|----|
| GPT-J (vanilla) | 6.7B | 37.7% | 11.6% | 7.1% |
| OPT | 66B | 54.7% | 14.6% | 10.8% |
| GPT-3 | 175B | 63.9% | 18.1% | 14.6% |
| **Toolformer** | **6.7B** | **67.5%** | **22.0%** | **16.8%** |

TriviaQA에서 Toolformer는 GPT-3를 **3.6%p** 초과합니다. 이는 WikiSearch와 QA 도구를 통해 모델 내부 지식에 포함되지 않은 사실 관계를 외부에서 검색하여 보완한 결과입니다. WebQuestions(+3.9%p)와 NQ(+2.2%p)에서도 동일한 경향이 나타납니다.

특히 TriviaQA에서 vanilla GPT-J(37.7%)와 Toolformer(67.5%)의 차이가 29.8%p에 달하는 것은 주목할 만합니다. 동일한 모델 아키텍처와 파라미터 수에서 도구 사용만으로 이만큼의 성능 향상이 가능하다는 것을 보여줍니다.

### 다국어 질의응답 (MLQA)

Machine Translation 도구의 효과를 MLQA 벤치마크로 평가합니다. MT 도구를 통해 비영어 질문을 영어로 번역한 뒤 처리하거나, 영어로 된 지식을 검색하여 활용합니다.

| 모델 | 독일어 | 스페인어 | 아랍어 | 힌디어 | 베트남어 | 중국어 |
|------|--------|----------|--------|--------|----------|--------|
| GPT-J (vanilla) | 16.4 | 19.8 | 8.3 | 10.1 | 14.3 | 12.0 |
| **Toolformer** | **22.8** | **25.1** | **14.6** | **16.2** | **19.7** | **17.5** |

모든 언어에서 유의미한 개선이 관찰되며, 특히 저자원 언어(아랍어 +6.3, 힌디어 +6.1)에서 상대적 개선 폭이 더 큽니다.

### 시간 관련 질의 (TempLAMA/LAMA)

Calendar 도구를 사용한 시간 관련 질의 처리 결과입니다.

| 모델 | 파라미터 수 | TempLAMA |
|------|-----------|----------|
| GPT-J (vanilla) | 6.7B | 22.1% |
| OPT | 66B | 25.4% |
| GPT-3 | 175B | 27.3% |
| **Toolformer** | **6.7B** | **32.4%** |

"오늘", "현재", "올해" 등 시간 표현이 포함된 질의에서 Calendar 도구는 정확한 날짜 정보를 제공하여 GPT-3 대비 **5.1%p**의 성능 향상을 가져옵니다.

### 모델 크기와 도구 사용의 상호작용

![모델 크기별 API 호출 유무에 따른 벤치마크 성능 비교](figures/fig_4.png)
*GPT-2 계열 모델(Small~XL)과 GPT-J의 LAMA, 수학, QA 벤치마크 평균 성능. API 호출이 소형 모델에는 도움이 되지 않지만, 모델 크기가 커질수록 도구 활용 효과가 급격히 증가한다. 대형 모델에서도 API 호출 유무에 따른 성능 격차는 지속적으로 유지된다. (Schick et al., 2023, Figure 4)*

Figure 4는 도구 활용 능력이 모델 크기에 대한 **창발적(emergent) 속성**임을 시사합니다. GPT-2 Small/Medium 수준에서는 API 호출이 오히려 성능을 저하시키지만, GPT-2 XL(1.5B) 이상에서부터 도구 활용 이점이 나타나기 시작하며, GPT-J(6.7B)에서 그 효과가 극대화됩니다. 이는 도구를 "올바르게" 사용하려면 일정 수준 이상의 언어 이해 능력이 전제되어야 함을 의미합니다.

### 언어 모델링 성능 유지

도구 호출 데이터로 파인튜닝하더라도 기본 언어 모델링 능력이 유지되는지 확인합니다.

$$\text{PPL}_{\text{WikiText-103, vanilla}} = 14.8 \quad \rightarrow \quad \text{PPL}_{\text{WikiText-103, Toolformer}} = 14.9$$

Perplexity 증가가 0.1에 불과하여, 도구 사용 학습이 원래의 언어 능력에 거의 영향을 미치지 않음을 확인할 수 있습니다. 이는 증강 데이터와 원본 데이터를 혼합하여 파인튜닝하는 전략이 효과적으로 작동함을 보여줍니다.

### Ablation Study

논문에서는 각 설계 요소의 기여를 분석하는 ablation 실험을 수행합니다.

| 설정 | SVAMP | TriviaQA |
|------|-------|----------|
| Toolformer (full) | 29.4 | 67.5 |
| $L_i^\emptyset$ 필터 조건 제거 | 22.1 | 61.3 |
| 필터링 없이 모든 후보 사용 | 15.8 | 48.7 |
| 단일 도구만 학습 | 27.6 | 65.2 |
| $\tau = 0.5$ (낮은 임계값) | 25.3 | 64.1 |
| $\tau = 2.0$ (높은 임계값) | 24.8 | 62.9 |

핵심 관찰 결과:

1. **필터링의 결정적 중요성**: 필터링 없이 모든 API 호출을 사용하면 SVAMP가 29.4% -> 15.8%로 급락합니다. 노이즈가 많은 API 호출이 모델을 혼란시키며, 도구 활용의 이점이 크게 감소합니다.

2. **$L_i^\emptyset$의 역할**: 빈 결과 조건($L_i^\emptyset$)을 필터에서 제거하면 성능이 하락합니다(SVAMP: 29.4% -> 22.1%). 이는 API 호출 구문 자체가 주는 편향을 제거하는 것이 중요함을 보여줍니다.

3. **임계값 $\tau$의 민감도**: $\tau = 1.0$이 최적이며, $\tau = 0.5$에서는 노이즈가 유입되어 성능 하락, $\tau = 2.0$에서는 유용한 데이터가 과도하게 제거되어 성능 하락이 발생합니다.

4. **다중 도구 통합의 이점**: 5가지 도구를 함께 학습하면 개별 학습(27.6/65.2) 대비 약간 더 나은 성능(29.4/67.5)을 보입니다. 도구 간 간섭 없이 시너지가 발생하는 것으로 해석됩니다.

## 의의 및 한계

### 학술적 의의

**자기 지도 방식의 도구 학습 가능성 입증**: Toolformer 이전에는 도구 사용을 LLM에 가르치려면 인간 주석 데이터가 필수적이라는 것이 지배적 가정이었습니다. 이 연구는 언어 모델 자체의 손실 함수만으로 도구 사용 데이터의 생성과 품질 관리가 가능함을 보여, 이 가정을 반증했습니다.

**파라미터 스케일링에 대한 대안 제시**: 6.7B 모델이 175B 모델에 필적하거나 초과하는 결과는, 모든 능력을 파라미터 안에 인코딩하는 것만이 유일한 경로가 아님을 시사합니다. 외부 도구의 활용은 모델 크기를 늘리지 않고도 특정 능력을 극대화할 수 있는 직교적(orthogonal) 접근법입니다.

**도구 사용 LLM 연구의 선구**: Toolformer는 이후 발표된 HuggingGPT(Shen et al., 2023), ToolBench/ToolLLM(Qin et al., 2023), Gorilla(Patil et al., 2023), AnyTool(Du et al., 2024) 등 다수의 도구 활용 연구에 직접적 영향을 미쳤습니다. OpenAI의 Function Calling, Anthropic의 Tool Use, Google의 Function Calling 등 상용 LLM 서비스의 도구 호출 기능도 Toolformer가 제시한 "텍스트 시퀀스 내 도구 호출 삽입"이라는 아이디어를 계승한 것입니다.

### 실용적 의의

**도구 확장의 낮은 비용**: 새로운 도구를 추가할 때 필요한 것은 해당 도구의 few-shot 예시 몇 개와 API 엔드포인트뿐입니다. 대규모 주석 작업이 불필요하므로, 도메인 특화 도구를 빠르게 통합할 수 있습니다.

**소규모 모델의 실용성**: 도구 활용을 통해 6.7B 규모의 모델로도 강력한 성능을 달성할 수 있다는 점은, 추론 비용(inference cost)과 배포 용이성 측면에서 실질적 가치가 있습니다. 추론 시 FLOPs 기준으로 GPT-3 대비 약 $1/26$의 비용으로 유사한 성능을 얻을 수 있습니다.

### 한계

**도구 체이닝(Tool Chaining) 불가**: Toolformer는 한 위치에 하나의 도구 호출만 수행합니다. 여러 도구를 순차적으로 연계하는 것이 불가능합니다. 예를 들어 "파리의 인구를 검색한 뒤 그 숫자의 제곱근을 계산"하는 다단계 작업은 처리할 수 없습니다.

$$\text{WikiSearch}(\text{"Paris population"}) \rightarrow \text{Calculator}(\sqrt{\text{result}})$$

이러한 체인형 호출은 [[react|ReAct]]와 같은 후속 프레임워크에서 해결됩니다.

**교사 모델 의존성**: 데이터 생성 과정에서 API 호출 후보를 샘플링하려면 충분히 강력한 LLM이 필요합니다. 이는 완전히 자율적인 학습이라 보기 어려운 측면이 있습니다. 교사 모델 없이 동작하는 도구 학습 방법은 여전히 열린 연구 문제입니다.

**오류 처리 메커니즘 부재**: API 호출이 잘못된 결과를 반환하더라도 이를 감지하거나 재시도하는 메커니즘이 없습니다. Wikipedia 검색이 관련 없는 문서를 반환하거나 Calculator가 잘못된 수식을 입력받으면, 오류가 그대로 최종 출력에 반영됩니다.

**정적 도구 세트**: 학습 시 고정된 5가지 도구만 사용하며, 추론 시 새로운 도구를 동적으로 추가하는 것이 불가능합니다. 실제 환경에는 수천 개의 API가 존재하므로, 이 제약은 실용적 활용을 제한합니다.

**인터랙티브 도구 사용 불가**: 웹 브라우저 조작이나 코드 실행 환경과 같은 상태 기반(stateful) 도구는 지원되지 않습니다. Toolformer의 도구는 모두 단일 요청-응답 패턴의 무상태(stateless) API에 한정됩니다.

**Few-shot 프롬프트의 수동 설계**: 각 도구에 대한 few-shot 예시는 인간이 직접 설계해야 합니다. 예시의 품질이 후보 생성의 질에 직접 영향을 미치므로, 이 부분은 여전히 수동 개입이 필요한 병목입니다.

## 코드 예제

### Toolformer 스타일 API 호출 파서 구현

Toolformer의 API 호출 형식을 파싱하고 실행하는 구현 예시입니다.

```python
import re
import math
from typing import Callable
from datetime import datetime


class ToolformerParser:
    """Toolformer 스타일의 API 호출을 파싱하고 실행하는 클래스."""

    # API 호출 패턴: [API_NAME(args) -> result]
    API_PATTERN = re.compile(
        r'\[(?P<api_name>\w+)\((?P<args>[^)]*)\)'
        r'(?:\s*->\s*(?P<result>[^\]]*))?\]'
    )

    def __init__(self):
        self.tools: dict[str, Callable] = {
            'Calculator': self._calculator,
            'Calendar': self._calendar,
            'WikiSearch': self._wiki_search,
            'MT': self._translate,
            'QA': self._question_answer,
        }

    def _calculator(self, expression: str) -> str:
        """수식을 평가합니다."""
        allowed_names = {
            'sqrt': math.sqrt, 'pow': pow,
            'abs': abs, 'round': round,
        }
        try:
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(result)
        except Exception as e:
            return f"Error: {e}"

    def _calendar(self, _: str = "") -> str:
        """현재 날짜를 반환합니다."""
        return datetime.now().strftime("%B %d, %Y")

    def _wiki_search(self, query: str) -> str:
        """Wikipedia 검색 시뮬레이션."""
        return f"[Result for '{query}']"

    def _translate(self, args: str) -> str:
        """번역 시뮬레이션."""
        return f"[Translation of {args}]"

    def _question_answer(self, question: str) -> str:
        """QA 시뮬레이션."""
        return f"[Answer to '{question}']"

    def parse_and_execute(self, text: str) -> str:
        """텍스트 내 API 호출을 파싱, 실행, 결과 삽입."""
        def replace_api_call(match):
            api_name = match.group('api_name')
            args = match.group('args').strip().strip('"\'')

            if api_name not in self.tools:
                return match.group(0)

            result = self.tools[api_name](args)
            return f"[{api_name}({match.group('args')}) -> {result}]"

        return self.API_PATTERN.sub(replace_api_call, text)


# 사용 예시
parser = ToolformerParser()

print(parser.parse_and_execute(
    "The answer is [Calculator(1400 / 100)] items."
))
# 출력: The answer is [Calculator(1400 / 100) -> 14.0] items.

print(parser.parse_and_execute(
    "Today is [Calendar()]."
))
# 출력: Today is [Calendar() -> March 23, 2026].
```

### 유용성 기반 필터링 로직

Toolformer의 핵심인 필터링 로직을 의사 코드로 표현한 예시입니다.

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def compute_continuation_loss(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prefix: str,
    continuation: str,
) -> float:
    """prefix 조건에서 continuation의 cross-entropy 손실을 계산합니다."""
    full_text = prefix + continuation
    inputs = tokenizer(full_text, return_tensors="pt")
    prefix_len = len(tokenizer(prefix)["input_ids"])

    with torch.no_grad():
        outputs = model(**inputs)

    # continuation 부분만 손실 계산
    logits = outputs.logits[0, prefix_len - 1:-1, :]
    labels = inputs["input_ids"][0, prefix_len:]
    loss = torch.nn.functional.cross_entropy(
        logits, labels, reduction='mean'
    )
    return loss.item()


def filter_api_call(
    model, tokenizer,
    text_before: str,
    text_after: str,
    api_call: str,     # 예: 'Calculator(1+1)'
    api_result: str,   # 예: '2'
    tau: float = 1.0,
) -> bool:
    """API 호출의 유용성을 판별합니다.

    Returns:
        True이면 학습 데이터에 포함
    """
    # L_i^+: API 호출 + 결과 포함
    loss_plus = compute_continuation_loss(
        model, tokenizer,
        f"{text_before} [{api_call} -> {api_result}] ",
        text_after
    )

    # L_i^-: API 호출 없음 (원문)
    loss_minus = compute_continuation_loss(
        model, tokenizer,
        f"{text_before} ",
        text_after
    )

    # L_i^emptyset: API 호출 있으나 결과 없음
    loss_empty = compute_continuation_loss(
        model, tokenizer,
        f"{text_before} [{api_call} -> ] ",
        text_after
    )

    # 필터링 조건
    return (loss_plus + tau) <= min(loss_minus, loss_empty)
```

## 후속 연구와의 관계

Toolformer가 개척한 "LLM + 도구" 패러다임은 이후 다양한 방향으로 확장되었습니다.

| 연구 | 연도 | 핵심 확장 | Toolformer와의 차이 |
|------|------|----------|--------------------|
| [[react\|ReAct]] | 2022 | 추론과 행동의 교차 수행 | 다단계 도구 체이닝 지원 |
| HuggingGPT | 2023 | HuggingFace 모델을 도구로 활용 | AI 모델 자체를 도구로 사용 |
| ToolBench / ToolLLM | 2023 | 16,000+ 실세계 API로 확장 | 대규모 도구 세트 지원 |
| Gorilla | 2023 | API 문서 기반 정확한 호출 생성 | 문서 기반 retrieval 활용 |
| OpenAI Function Calling | 2023 | 상용 제품에서의 구현 | 구조화된 JSON 스키마 사용 |
| Anthropic Tool Use | 2024 | 구조화된 도구 정의 및 호출 | XML 기반 도구 인터페이스 |
| AnyTool | 2024 | 셀프 리플렉션 기반 도구 선택 | 동적 도구 발견 메커니즘 |

Toolformer의 자기 지도 방식은 이후 연구들이 인간 주석 데이터를 최소화하면서 도구 사용 능력을 학습하는 데 핵심적인 영감을 제공했습니다. 현재 주요 LLM 서비스의 도구 호출 기능이 Toolformer의 철학을 상용 수준에서 구현한 사례라는 점에서, 이 논문의 영향력은 학술적 범위를 넘어 산업 전반에 걸쳐 있습니다.

## 관련 문서

- [[react|ReAct]] -- 추론과 행동을 결합한 도구 사용 프레임워크
- [[rag|RAG]] -- 외부 지식 검색을 활용한 생성 방식
