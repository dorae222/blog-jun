## 개요

Self-RAG는 2023년 워싱턴대학교의 Akari Asai 등이 발표한 논문으로, **ICLR 2024에서 Oral 발표(상위 1%)**로 선정되었다. 이 논문은 언어 모델에 **자기 반성(self-reflection)** 능력을 부여하여 검색과 생성의 품질을 스스로 제어하는 방법을 제안한다. 기존 RAG 시스템은 모든 입력에 대해 무조건 외부 문서를 검색하므로, 간단한 질문이나 검색이 불필요한 경우에도 불필요한 연산과 노이즈가 발생할 수 있었다. Self-RAG는 이를 해결하기 위해 **반성 토큰(reflection token)**이라는 특수 토큰을 도입한다.

다음 그림은 기존 RAG와 Self-RAG의 동작 방식 차이를 보여준다.

![기존 RAG와 Self-RAG의 동작 방식 비교 — Self-RAG는 검색 필요성을 동적으로 판단하고 생성 결과를 자기 비평한다](figures/fig_1.png)
*Figure 1: Standard RAG vs Self-RAG 비교. 기존 RAG(왼쪽)는 모든 입력에 대해 무조건 검색을 수행하고 검색 문서를 그대로 사용하는 반면, Self-RAG(오른쪽)는 (1) 검색 필요성을 온디맨드로 판단하고, (2) 여러 문서에 대해 병렬로 세그먼트를 생성한 뒤, (3) 반성 토큰([IsRel], [IsSup])으로 각 후보를 비평하여 최적의 세그먼트를 선택한다. 하단의 에세이 요청처럼 검색이 불필요한 경우에는 [Retrieve]=No로 판단하여 직접 생성한다.*

핵심적인 기여는 검색, 생성, 비평이라는 세 가지 역할을 **단일 모델**로 통합했다는 점이다. 기존에는 검색기, 생성기, 비평기(critic)가 각각 별도의 모델이었으나, Self-RAG는 반성 토큰을 어휘에 추가하는 것만으로 이 세 가지를 하나의 모델에서 수행한다. 구체적으로, 모델은 텍스트를 생성하는 도중에 `[Retrieve]`, `[IsRel]`, `[IsSup]`, `[IsUse]`라는 네 가지 특수 토큰을 출력하며, 이를 통해 검색의 필요성을 판단하고, 검색된 문서의 품질을 평가하고, 자신이 생성한 텍스트가 근거에 의해 뒷받침되는지를 스스로 검증한다. ICLR 2024 발표 이후 약 700건 이상 인용되며, 적응적 RAG 연구의 기반이 되었다.

## 배경 및 문제

### 기존 RAG의 한계

표준 RAG(Lewis et al., 2020)는 검색 증강 생성의 기초를 마련했지만, 실제 배포 환경에서 다음과 같은 구조적 문제가 두드러진다:

1. **무조건적 검색(Always-Retrieve)**: 입력이 단순한 인사말("안녕하세요"), 창의적 글쓰기 요청("시를 하나 써줘"), 또는 모델이 이미 잘 아는 상식적 질문이더라도 항상 검색을 수행한다. 이는 불필요한 연산 비용과 지연 시간을 초래한다. 저자들의 분석에 따르면, 실제 사용자 질의 중 약 30~40%는 외부 검색 없이도 모델의 파라메트릭 지식만으로 충분히 답변할 수 있는 것으로 나타났다.
2. **검색 품질 비평 부재**: 검색된 문서가 실제로 답변에 유용한지 검증하지 않는다. 검색기가 잘못된 문서를 반환하면, 생성기가 그 잘못된 정보를 기반으로 답변을 생성할 수 있다. 이는 특히 의학, 법률 등 고신뢰성이 요구되는 도메인에서 심각한 위험 요인이 된다.
3. **생성 품질 비평 부재**: 생성된 텍스트가 검색 문서에 의해 충분히 지지되는지 평가하지 않는다. 모델이 검색 문서와 무관한 내용을 hallucinate할 수 있다. 기존 RAG에서는 검색된 문서를 프롬프트에 삽입하기만 할 뿐, 생성 결과가 해당 문서의 내용을 정확히 반영하는지에 대한 사후 검증이 전혀 이루어지지 않는다.
4. **적응성 부재**: 태스크 유형에 따라 검색 빈도나 방식을 조절하지 못한다. QA에는 높은 사실성이, 창의적 글쓰기에는 다양성이 필요하지만 기존 RAG는 이를 구분하지 않는다.

이러한 한계를 형식적으로 정리하면, 기존 RAG의 생성 과정은 다음과 같이 표현된다:

$$p(y|x) = \sum_{d \in \mathcal{D}} p(y|x, d) \cdot p(d|x)$$

여기서 검색 $p(d|x)$는 모든 입력 $x$에 대해 항상 수행되며, 검색 결과 $d$의 품질에 대한 평가가 없고, 생성 $p(y|x,d)$에 대한 자기 검증도 존재하지 않는다. Self-RAG는 이 세 가지 결함을 모두 반성 토큰이라는 단일 메커니즘으로 해결한다.

### 선행 연구: 적응적 검색의 시도들

Self-RAG 이전에도 적응적 검색에 대한 다양한 시도가 있었다.

| 선행 연구 | 접근 방식 | 한계 |
|----------|---------|-----|
| FLARE (Jiang et al., 2023) | 생성 중 토큰 확률이 낮아지면 검색 트리거 | 불확실성 추정 정확도에 의존, 검색 품질 미평가 |
| Toolformer (Schick et al., 2023) | API 호출을 학습하여 도구 사용 | 검색 필요성의 명시적 판단 부재 |
| REPLUG (Shi et al., 2023) | 검색 문서를 언어 모델 확률로 재순위화 | 문서 순위만 조정, 검색 여부 판단 불가 |
| kNN-LM (Khandelwal et al., 2020) | 토큰 수준 최근접 이웃 검색 | 세그먼트 수준 제어 불가, 높은 연산 비용 |

FLARE는 생성 중 불확실성이 높아지면 검색을 트리거하는 방식을 제안했으나, 불확실성 추정의 정확도에 의존하며 검색 결과의 품질을 평가하지 않았다. Toolformer는 도구 호출을 학습하지만, 검색의 필요성을 명시적으로 판단하지는 않았다. REPLUG는 검색된 문서를 언어 모델의 perplexity를 기준으로 재순위화하지만, 검색 자체를 수행할지 여부는 판단하지 못한다.

Self-RAG는 이러한 문제를 **반성 토큰을 통한 자기 비평**으로 종합적으로 해결한다. 핵심 차이점은 검색의 필요성 판단, 검색 결과의 품질 평가, 생성 결과의 근거 검증이라는 세 가지 기능을 하나의 통합된 프레임워크에서 수행한다는 것이다.

## 핵심 아이디어

### 반성 토큰의 형식적 정의 (Reflection Tokens)

Self-RAG는 네 가지 유형의 특수 반성 토큰을 정의한다. 이 토큰들은 모델의 기존 어휘 $\mathcal{V}$에 추가되어 확장된 어휘 $\mathcal{V}' = \mathcal{V} \cup \{r_1, r_2, \ldots, r_m\}$를 구성한다.

| 토큰 유형 | 역할 | 출력 공간 | 생성 시점 |
|---------|------|----------|----------|
| `[Retrieve]` | 검색 필요 여부 판단 | $\{\text{yes}, \text{no}, \text{continue}\}$ | 세그먼트 시작 시 |
| `[IsRel]` | 검색 문서의 관련성 평가 | $\{\text{relevant}, \text{irrelevant}\}$ | 문서 검색 직후 |
| `[IsSup]` | 생성 텍스트의 문서 지지 여부 | $\{\text{fully supported}, \text{partially supported}, \text{no support}\}$ | 세그먼트 생성 후 |
| `[IsUse]` | 최종 응답의 유용성 평가 | $\{1, 2, 3, 4, 5\}$ (정수 척도) | 응답 완료 후 |

이 토큰들은 기존 어휘(vocabulary)에 추가되어, 모델이 일반 텍스트 토큰을 생성하는 것과 동일한 방식으로 자연스럽게 생성된다. 이것이 Self-RAG의 핵심 설계 원리이다 -- 별도의 분류기나 비평 모델이 필요 없이, **단일 언어 모델이 텍스트 생성과 메타 판단을 동시에 수행**한다.

각 반성 토큰의 확률 분포는 다음과 같이 정의된다. `[Retrieve]` 토큰의 경우:

$$p_\theta(\text{[Retrieve]} = r | x, y_{<t}) = \text{softmax}(W_r \cdot h_t + b_r)$$

여기서 $h_t$는 현재 시점의 은닉 상태, $W_r$과 $b_r$은 반성 토큰에 대응하는 출력 가중치이다. 핵심은 이 가중치들이 일반 어휘 토큰의 출력 가중치와 함께 동일한 LM head에서 학습된다는 것이다. 따라서 반성 토큰 생성은 추가적인 분류 헤드나 별도 모듈 없이 표준 next-token prediction으로 수행된다.

`[Retrieve]` 토큰의 세 가지 값은 각각 다른 의미를 갖는다:
- **yes**: 현재 맥락에서 외부 지식이 필요하다. 검색기를 호출한다.
- **no**: 모델의 파라메트릭 지식으로 충분하다. 검색 없이 직접 생성한다.
- **continue**: 이전에 검색한 문서를 계속 참조하면서 생성을 이어간다.

### 생성 과정 상세

입력 $x$와 이전까지 생성된 텍스트 $y_{<t}$가 주어졌을 때, Self-RAG의 생성 과정은 다음과 같다:

**Step 1: 검색 필요성 판단**
$$\hat{r} = \arg\max_r p_\theta(r | x, y_{<t}), \quad r \in \{\text{yes, no, continue}\}$$

모델은 현재 맥락을 보고 외부 지식이 필요한지 스스로 판단한다. "2+2는?"같은 간단한 질문에는 `no`를, "2024년 노벨 물리학상 수상자는?"에는 `yes`를 출력한다.

**Step 2: 검색 수행 (if $\hat{r}$ = yes)**
$$\{d_1, d_2, \ldots, d_k\} = \text{Retrieve}(x, y_{<t})$$

현재 입력과 이전 생성 텍스트를 쿼리로 사용하여 외부 코퍼스에서 상위 $k$개 문서를 검색한다. 저자들은 Contriever-MS MARCO를 검색기로 사용하였으며, 기본적으로 $k=5$로 설정하였다.

**Step 3: 관련성 평가 및 세그먼트 생성**
각 문서 $d_i$에 대해 관련성을 평가하고 조건부 텍스트를 생성한다:
$$\hat{y}_t^{(i)}, \hat{c}_t^{(i)} = \arg\max_{y, c} p_\theta(y, c | x, y_{<t}, d_i)$$

여기서 $c$는 `[IsRel]`과 `[IsSup]` 토큰값을 포함하는 비평 토큰 시퀀스이다. 모델은 문서를 읽고 답변을 생성하면서 동시에 그 문서가 관련 있는지, 생성된 텍스트가 문서에 의해 지지되는지를 판단한다. 생성 순서를 구체적으로 기술하면 다음과 같다:

$$\underbrace{x}_{\text{입력}} \to \underbrace{[\text{Retrieve}]=\text{yes}}_{\text{검색 판단}} \to \underbrace{d_i}_{\text{검색 문서}} \to \underbrace{[\text{IsRel}]=\text{relevant}}_{\text{관련성 평가}} \to \underbrace{y_t}_{\text{생성 텍스트}} \to \underbrace{[\text{IsSup}]=\text{fully}}_{\text{지지도 평가}} \to \underbrace{[\text{IsUse}]=5}_{\text{유용성 평가}}$$

이처럼 반성 토큰은 생성 시퀀스 내에 인터리브(interleave)되어 자연스럽게 출력된다.

**Step 4: 세그먼트 선택 (Segment-level Beam Search)**

`[IsUse]` 점수, `[IsSup]` 값, `[IsRel]` 값을 조합하여 최적 세그먼트를 선택한다:
$$\hat{y}_t = \arg\max_{y^{(i)}} \left[ w_{\text{rel}} \cdot \text{score}_{\text{rel}}(d_i) + w_{\text{sup}} \cdot \text{score}_{\text{sup}}(y^{(i)}) + w_{\text{use}} \cdot \text{score}_{\text{use}}(y^{(i)}) \right]$$

각 점수 함수는 반성 토큰의 softmax 확률로 정의된다. 예를 들어 `[IsSup]`의 경우:

$$\text{score}_{\text{sup}}(y^{(i)}) = \frac{p_\theta(\text{[IsSup]}=\text{fully} | \cdot)}{p_\theta(\text{[IsSup]}=\text{fully} | \cdot) + p_\theta(\text{[IsSup]}=\text{no support} | \cdot)}$$

가중치 $w_{\text{rel}}, w_{\text{sup}}, w_{\text{use}}$는 추론 시 태스크에 맞게 조절할 수 있다. 이것이 Self-RAG의 중요한 장점인 **추론 시 유연한 제어**이다. 기존의 RLHF 기반 접근법이 학습 시에 보상 함수를 고정해야 하는 것과 달리, Self-RAG는 추론 시점에 사용 목적에 맞게 동작을 커스터마이징할 수 있다.

## 방법론

다음 그림은 Self-RAG의 전체 아키텍처 파이프라인을 보여준다. Contriever-MS MARCO 검색기가 관련 패시지를 검색하고, Llama2-7B/13B 기반 Generator가 반성 토큰과 함께 답변을 생성하는 구조이다.

![Self-RAG 아키텍처 파이프라인 — 검색기(Contriever-MS MARCO), 생성기(Llama2-7B/13B), 반성 토큰의 통합 구조](figures/architecture.png)
*Self-RAG 아키텍처 파이프라인. 입력 쿼리가 들어오면 Contriever-MS MARCO 검색기가 관련 패시지를 검색하고, Llama2-7B/13B 기반 Generator가 검색된 문서를 조건으로 답변을 생성한다. 이때 [Retrieve], [IsRel], [IsSup], [IsUse] 반성 토큰이 생성 과정에 통합되어 검색 필요성 판단부터 생성 품질 검증까지 단일 모델 내에서 수행된다.*

다음 그림은 Self-RAG의 학습 데이터가 어떻게 구성되는지를 구체적으로 보여준다. 검색이 불필요한 경우와 필요한 경우에 반성 토큰이 다르게 삽입된다.

![Self-RAG 학습 예시 — 검색 불필요(여름 휴가 에세이)와 검색 필요(미국 주 이름 유래) 두 가지 학습 샘플](figures/fig_2.png)
*Figure 2: Self-RAG 학습 데이터 예시. 왼쪽(에세이 요청)은 검색이 불필요하여 [Retrieve]=No와 [IsUse] 토큰만 삽입되고, 오른쪽(사실 기반 질문)은 Retriever가 호출되어 [IsRel], [IsSup] 등 모든 반성 토큰이 포함된다. (Asai et al., 2023)*

### Critic 모델 학습 (반성 토큰 레이블링)

Self-RAG의 학습 파이프라인에서 가장 핵심적인 단계는 Critic 모델의 학습이다. 이 과정은 다음과 같이 진행된다:

**1단계: GPT-4 기반 시드 데이터 생성**

각 반성 토큰 유형별로 GPT-4에 few-shot 프롬프트를 제공하여 레이블을 수집한다. 예를 들어 `[IsRel]` 토큰의 경우, GPT-4에게 다음과 같은 형태의 프롬프트를 제공한다:

> "주어진 질문과 검색 문서를 읽고, 이 문서가 질문에 답하는 데 관련이 있는지 판단하세요. 'relevant' 또는 'irrelevant'로 답하세요."

각 반성 토큰 유형별로 약 4K~20K개의 GPT-4 레이블을 수집한다. 저자들은 이 과정에서 GPT-4의 레이블 정확도가 약 90% 이상임을 검증하였다.

**2단계: Critic 모델 학습**

수집된 GPT-4 레이블로 소형 Critic 모델(Llama2-7B 기반)을 파인튜닝한다. Critic 모델의 학습 목적 함수는 다음과 같다:

$$\mathcal{L}_{\text{critic}}(\phi) = -\sum_{i=1}^{N} \log p_\phi(c_i | x_i, d_i, y_i)$$

여기서 $c_i$는 GPT-4가 생성한 반성 토큰 레이블, $\phi$는 Critic 모델의 파라미터이다. 학습된 Critic은 GPT-4의 판단 능력을 근사하면서도 GPT-4 대비 수십 배 저렴한 비용으로 대규모 레이블링을 수행할 수 있다.

**3단계: 대규모 학습 데이터 레이블링**

학습된 Critic 모델을 사용하여 150K 이상의 학습 샘플에 반성 토큰을 자동 부착한다. 각 학습 샘플의 텍스트 세그먼트마다 `[Retrieve]`, `[IsRel]`, `[IsSup]`, `[IsUse]` 토큰이 적절한 위치에 삽입된다.

### Generator 모델 학습

반성 토큰이 포함된 증강 데이터로 Llama2-7B/13B를 파인튜닝한다. 학습 목적 함수는 표준 next-token prediction이다:

$$\mathcal{L}(\theta) = -\sum_{t=1}^{T} \log p_\theta(y_t^* | x, y_{<t}^*)$$

여기서 $y^*$는 반성 토큰이 삽입된 정답 시퀀스이다. 일반 텍스트 토큰과 반성 토큰이 동일한 next-token prediction 프레임워크에서 학습된다. 이 설계의 핵심적인 이점은 반성 토큰 생성을 위한 별도의 학습 목적 함수나 보상 모델이 필요하지 않다는 것이다. RLHF처럼 별도의 보상 모델을 학습시키고 PPO로 최적화하는 복잡한 과정 없이, 단순한 supervised fine-tuning만으로 자기 비평 능력을 학습시킬 수 있다.

학습에 사용된 데이터는 다양한 출처에서 수집되었다:
- **Open-domain QA**: Natural Questions, TriviaQA 등의 QA 데이터셋
- **Fact verification**: FEVER, PubHealth 등의 팩트 검증 데이터셋
- **Long-form generation**: ASQA, ELI5 등의 장문 생성 데이터셋
- **기타**: 위키피디아 기반 다양한 지식 집약적 태스크

### 추론 과정 (Inference)

추론 시에는 segment-level beam search를 수행한다. 전체 응답을 한 번에 생성하는 대신, 텍스트를 여러 세그먼트로 나누어 각 세그먼트마다 검색 필요성을 판단하고 최적의 후보를 선택한다.

추론 시 반성 토큰의 가중치를 조정하여 사용 사례에 맞게 동작을 제어할 수 있다:
- **사실성 중시 태스크** (의학 QA, 법률 검색): `[IsSup]` 토큰 가중치 증가 $\rightarrow$ fully supported 답변 우선
- **다양성 중시 태스크** (창의적 글쓰기): 검색 빈도 감소, `[IsUse]` 가중치 증가
- **속도 중시**: `[Retrieve]` = no 비율 증가로 불필요한 검색 최소화

이러한 추론 시 제어 가능성은 별도의 재학습 없이도 다양한 배포 시나리오에 대응할 수 있게 한다. 예를 들어 동일한 모델 체크포인트를 사용하면서, 의학 상담 챗봇에서는 사실성 중시 설정을, 창작 도우미에서는 다양성 중시 설정을 적용할 수 있다.

### 기존 RAG 대비 아키텍처 비교

| 구성 요소 | 기존 RAG | Self-RAG |
|---------|---------|----------|
| 검색 결정 | 항상 검색 (고정) | 모델이 동적 판단 (`[Retrieve]`) |
| 문서 품질 평가 | 없음 | `[IsRel]` 토큰으로 자동 평가 |
| 생성 품질 검증 | 없음 | `[IsSup]` 토큰으로 근거 지지 확인 |
| 응답 유용성 평가 | 없음 | `[IsUse]` 토큰으로 종합 평가 |
| 추론 시 제어 | 불가능 | 가중치 조절로 태스크별 커스터마이징 |
| 학습 방식 | End-to-end 또는 분리 학습 | Supervised fine-tuning (반성 토큰 포함) |
| 필요 모델 수 | 검색기 + 생성기 (+ 선택적 리랭커) | 검색기 + 단일 생성/비평 통합 모델 |

## 실험 결과

### 오픈 도메인 QA

| 모델 | PopQA | TriviaQA-unfiltered | PubHealth | ARC-Challenge |
|-----|-------|---------------------|-----------|---------------|
| ChatGPT | 29.3 | 74.7 | 70.1 | 79.3 |
| Llama2-chat 13B | 20.0 | 63.5 | 57.6 | 67.6 |
| Llama2 + RAG (standard) | 48.7 | 66.4 | 50.0 | - |
| Perplexity.ai | 34.8 | - | - | - |
| **Self-RAG 7B** | **50.8** | **61.8** | **72.4** | **75.4** |
| **Self-RAG 13B** | **54.9** | **67.3** | **78.2** | **80.3** |

Self-RAG 13B는 **6개의 다양한 태스크에서 ChatGPT와 retrieval-augmented Llama2-chat을 능가**했다. 특히 PopQA(롱테일 지식 QA)에서 ChatGPT 대비 약 25%p 높은 정확도를 기록했는데, 이는 적응적 검색이 롱테일 지식에 특히 효과적임을 보여준다. 롱테일 엔티티에 대한 질문은 모델의 파라메트릭 지식만으로는 답변하기 어렵기 때문에, `[Retrieve]=yes` 판단이 정확하게 이루어지는 것이 중요하다.

PubHealth에서의 결과도 주목할 만하다. Self-RAG 13B는 78.2%를 달성하여 ChatGPT(70.1%)를 8.1%p 상회하였다. 공중보건 관련 주장의 진위를 검증하는 이 태스크에서, `[IsSup]` 토큰이 생성된 판단이 검색된 의학 문서에 의해 충분히 뒷받침되는지를 확인하는 역할을 효과적으로 수행한 것이다.

다음 그림은 학습 데이터 규모가 PopQA 성능에 미치는 영향을 보여준다.

![학습 데이터 수(k 단위)에 따른 PopQA 성능 향상 곡선](figures/fig_6_1.png)
*Figure 3e: 학습 데이터 수 증가에 따른 PopQA 성능 변화. 10K에서 150K로 데이터가 증가함에 따라 성능이 꾸준히 향상되며, 충분한 학습 데이터가 적응적 검색 능력 습득에 중요함을 보여준다. (Asai et al., 2023)*

### 팩트 검증: Bio Generation

| 모델 | Factuality (%) | 유용성 점수 |
|-----|---------------|----------|
| Llama2-chat 13B | 55.0 | 3.2 |
| Llama2 + RAG | 66.0 | 3.5 |
| ChatGPT | 71.0 | 3.8 |
| **Self-RAG 7B** | **74.0** | **3.7** |
| **Self-RAG 13B** | **80.0** | **4.1** |

Self-RAG는 전기(biography) 생성 태스크에서 **사실성(factuality) 80%**를 달성하여, ChatGPT의 71%를 크게 상회했다. 이는 `[IsSup]` 토큰이 hallucination을 효과적으로 억제하기 때문이다. 인물의 출생지, 학력, 경력 등 사실적 정보를 생성할 때, 각 주장이 검색된 문서에 의해 fully supported인지를 확인함으로써 거짓 정보의 생성을 방지한다.

### 장문 생성 태스크 (ASQA, QAMPARI)

Self-RAG는 인용 정밀도(citation precision)와 재현율(citation recall)에서 기존 RAG 대비 평균 **10% 이상 향상**을 보였다. 이는 `[IsSup]` 토큰이 생성된 각 주장이 특정 문서에 의해 지지되는지를 명시적으로 추적하기 때문이다.

| 모델 | ASQA (EM) | Citation Precision | Citation Recall |
|-----|-----------|-------------------|----------------|
| Llama2-chat 13B | 21.9 | 43.8 | 42.1 |
| Llama2 + RAG | 23.5 | 60.1 | 52.3 |
| ChatGPT + RAG | 25.1 | 62.8 | 55.7 |
| **Self-RAG 7B** | **25.3** | **65.4** | **58.9** |
| **Self-RAG 13B** | **28.6** | **70.2** | **63.5** |

ASQA는 하나의 질문에 대해 여러 관점의 답변과 인용을 제공해야 하는 태스크이다. Self-RAG 13B는 ChatGPT + RAG 대비 citation precision에서 7.4%p, citation recall에서 7.8%p 향상을 보였다. 이는 세그먼트 단위로 근거 지지도를 평가하는 `[IsSup]` 메커니즘이 인용의 정확성을 크게 개선한다는 것을 의미한다.

다음 그림은 학습 데이터 규모에 따른 ASQA 인용 정밀도의 변화를 보여준다.

![학습 데이터 수에 따른 ASQA 인용 정밀도 — 반성 토큰 학습 효과](figures/fig_9.png)
*Figure 3g: 학습 데이터 규모에 따른 ASQA 인용 정밀도(citation precision). 데이터 증가에 따라 인용 정확성이 꾸준히 향상되며, 장문 생성에서도 Self-RAG의 자기 비평 메커니즘이 효과적임을 입증한다. (Asai et al., 2023)*

### Ablation Study: 반성 토큰의 효과

다음 그림은 `[IsSup]` 가중치 변화에 따라 인용 정밀도와 텍스트 다양성(MAUVE) 사이에 명확한 트레이드오프가 존재함을 보여준다.

![[IsSup] 토큰 가중치 변화에 따른 인용 정밀도(Precision)와 MAUVE 점수의 트레이드오프](figures/fig_3_1.png)
*Figure 3a: [IsSup] 가중치 증가에 따른 인용 정밀도(상단)와 MAUVE 다양성 점수(하단) 변화. 사실성이 높아질수록 텍스트 다양성이 감소하는 트레이드오프를 보여주며, 추론 시 가중치로 균형을 조절할 수 있다. (Asai et al., 2023)*

각 반성 토큰을 제거한 ablation 실험은 Self-RAG의 설계 결정의 합리성을 검증한다:

| 제거 요소 | PopQA 변화 | Bio Factuality 변화 | ASQA Citation Precision 변화 |
|---------|-----------|-------------------|---------------------------|
| `[Retrieve]` 제거 | -5.2%p | -3.1%p | -2.8%p |
| `[IsRel]` 제거 | -3.4%p | -2.5%p | -6.3%p |
| `[IsSup]` 제거 | -2.1%p | -8.1%p | -5.7%p |
| `[IsUse]` 제거 | -1.8%p | -1.4%p | -3.2%p |
| 모든 반성 토큰 제거 | -9.7%p | -14.0%p | -12.5%p |

모든 반성 토큰이 각각 독립적으로 성능에 기여함이 확인되었다. 특히 `[IsSup]`의 제거가 Bio Factuality에 가장 큰 영향을 미치고(-8.1%p), `[IsRel]`의 제거가 Citation Precision에 가장 큰 영향을 미친다(-6.3%p)는 점이 주목할 만하다. 이는 각 반성 토큰이 서로 다른 측면의 품질을 담당하고 있음을 보여준다.

### 추론 시 커스터마이제이션 분석

Self-RAG의 독특한 장점 중 하나는 추론 시 반성 토큰의 가중치를 조절하여 재학습 없이 모델 동작을 커스터마이징할 수 있다는 것이다. 다음 그림은 `[IsSup]` 가중치 변화에 따른 인용 정밀도와 텍스트 다양성(MAUVE) 간의 트레이드오프를 보여준다.

![IsSup 가중치에 따른 인용 정밀도와 MAUVE 점수의 트레이드오프](figures/fig_4.png)
*[IsSup] 가중치 조정에 따른 커스터마이제이션 효과. 가중치를 높이면 인용 정밀도(Precision)가 향상되지만 텍스트 다양성(MAUVE)은 감소하는 트레이드오프가 존재한다. 이를 통해 사실성 중시 태스크와 다양성 중시 태스크에 동일한 모델을 재학습 없이 적용할 수 있다.*

`[IsSup]` 가중치를 0에서 2로 높이면, 인용 정밀도는 약 69%에서 71%로 향상되는 반면, MAUVE 점수는 약 95에서 88로 감소한다. 이 결과는 사실성과 다양성 사이의 명확한 트레이드오프를 보여주며, 배포 환경에 따라 최적의 균형점을 선택할 수 있음을 시사한다.

### 검색 빈도 분석

저자들은 Self-RAG가 태스크에 따라 실제로 검색 빈도를 적응적으로 조절하는지를 분석하였다:

| 태스크 유형 | 검색 비율 (Retrieve=yes) |
|-----------|----------------------|
| PopQA (롱테일 지식 QA) | 약 85% |
| TriviaQA (일반 상식 QA) | 약 55% |
| Bio Generation (전기 생성) | 약 78% |
| 창의적 글쓰기 | 약 20% |

롱테일 지식이 필요한 PopQA에서는 85%의 높은 검색 비율을, 모델이 이미 잘 알고 있는 일반 상식 QA에서는 55%로 낮아지고, 창의적 글쓰기에서는 20%로 크게 감소한다. 이는 `[Retrieve]` 토큰이 태스크의 특성에 따라 적응적으로 동작하고 있음을 보여주는 실증적 근거이다.

다음 그림은 검색 임계값(retrieval threshold)을 조절했을 때 정확도와 검색 빈도가 어떻게 변화하는지를 정량적으로 보여준다.

![검색 임계값에 따른 PubHealth와 PopQA의 정확도 및 검색 빈도 변화](figures/fig_5.png)
*검색 임계값(Retrieval Threshold)에 따른 성능 변화. PubHealth(상단)에서는 임계값을 높여 검색 빈도를 줄여도 정확도가 거의 유지되는 반면, PopQA(하단)에서는 검색 빈도 감소에 따라 정확도가 크게 하락한다. 이는 PubHealth의 경우 모델의 파라메트릭 지식으로 상당 부분 대응 가능하지만, 롱테일 지식이 필요한 PopQA에서는 외부 검색이 필수적임을 보여준다.*

PubHealth에서는 임계값을 0.7까지 높여도(검색 빈도가 거의 0에 가까워져도) 정확도가 99.1%를 유지하는 반면, PopQA에서는 임계값 0.7에서 정확도가 약 25%까지 급격히 하락한다. 이 비대칭적 패턴은 Self-RAG가 태스크별 검색 필요성을 정확히 인식하고 있음을 보여주며, 실제 배포 시 임계값 설정을 통해 연산 비용과 정확도 간의 최적 균형을 찾을 수 있다는 실용적 시사점을 제공한다.

## 의의 및 한계

### 의의

1. **적응적 검색 패러다임 제시**: 태스크 복잡도에 따라 검색 여부를 동적으로 결정하여 효율성을 향상시켰다. 불필요한 검색을 줄여 추론 비용을 절감하며, 이는 기존 always-retrieve 방식의 근본적 한계를 해결한다.
2. **자기 감사(self-audit) 메커니즘**: 생성된 내용이 근거 문서에 의해 지지되는지 스스로 검증한다. 이는 hallucination 감지의 새로운 패러다임을 제시하며, 외부 검증기 없이도 모델 자체적으로 사실 정확성을 관리할 수 있다.
3. **단일 모델 통합**: 별도의 Critic 모델 없이 하나의 모델로 검색, 생성, 비평을 모두 수행한다. 배포 및 유지보수가 간편하며, 모델 간 통신 오버헤드가 없다.
4. **추론 시 제어 가능성**: 반성 토큰 가중치 조정으로 재학습 없이 태스크별 동작을 커스터마이징할 수 있다. 이는 하나의 체크포인트로 다양한 응용 시나리오에 대응 가능하게 한다.
5. **RLHF 대비 학습 효율성**: 보상 모델 학습과 PPO 최적화가 필요한 RLHF와 달리, 단순한 supervised fine-tuning만으로 자기 비평 능력을 학습시킬 수 있다.

### 후속 연구와의 연결

Self-RAG의 아이디어는 이후 다양한 후속 연구에 영향을 미쳤다:

| 후속 연구 | Self-RAG에서 받은 영감 | 개선점 |
|----------|-------------------|-------|
| [[CRAG]] (Corrective RAG) | 검색 결과의 품질 평가 및 보정 | 외부 웹 검색을 보정 수단으로 추가 |
| FLARE+ | 적응적 검색 트리거링 개선 | 문장 수준 세밀한 검색 제어 |
| ReSP | 반성 기반 검색 계획 | 다단계 검색 계획 수립 |
| OPEN-RAG | 오픈 도메인 적응적 RAG | 도메인 무관 적응적 검색 |
| Adaptive-RAG | 질의 복잡도 기반 전략 선택 | 복잡도 분류기로 검색 전략 결정 |

### 한계

1. **학습 데이터 의존성**: 반성 토큰 레이블 생성을 위해 GPT-4가 필요하여 데이터 구축 비용이 높다. GPT-4 API 호출 비용이 전체 파이프라인의 주요 비용 요인이 되며, 새로운 도메인으로 확장할 때마다 추가적인 레이블링 비용이 발생한다.
2. **반성 토큰 정확도**: 학습된 모델의 자기 비평이 항상 정확하지 않을 수 있다. 특히 Critic 학습 데이터의 편향이 모델에 전이될 수 있으며, 모델이 자신의 hallucination을 `[IsSup]=fully supported`로 잘못 판단하는 경우가 존재한다.
3. **복잡한 추론 제한**: 다단계 추론(multi-hop reasoning)이 필요한 태스크에서는 여전히 한계가 있다. 한 번의 검색으로 해결할 수 없는 질문에 대한 처리가 부족하며, 여러 문서를 순차적으로 참조해야 하는 복잡한 질의에는 적합하지 않다.
4. **지연 시간 증가**: 다중 세그먼트 생성 및 비교로 인해 표준 RAG 대비 추론 속도가 2~3배 감소한다. 각 세그먼트마다 $k$개 문서에 대해 병렬 생성 및 비교를 수행해야 하므로, 실시간 응답이 필요한 서비스에서는 제약이 될 수 있다.
5. **반성 토큰 가중치 튜닝**: 추론 시 가중치 조절이 가능하지만, 최적 가중치를 찾는 것은 여전히 수동적인 과정이다. 태스크별 최적 가중치를 자동으로 탐색하는 메커니즘이 부재하다.
6. **모델 크기 제약**: 논문에서 실험한 모델은 Llama2-7B/13B로, 현재 기준에서는 비교적 소형이다. 더 큰 모델(70B+)에서의 반성 토큰 효과나, 이미 강력한 기반 모델에서의 추가적 이점에 대한 검증이 부족하다.

## 코드 예제

### Self-RAG 추론 파이프라인 (PyTorch)

```python
import torch
import torch.nn.functional as F
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

# 반성 토큰 ID 정의 (어휘에 추가된 특수 토큰)
SPECIAL_TOKENS = {
    "[Retrieve]=yes": 32000,
    "[Retrieve]=no": 32001,
    "[Retrieve]=continue": 32002,
    "[IsRel]=relevant": 32003,
    "[IsRel]=irrelevant": 32004,
    "[IsSup]=fully": 32005,
    "[IsSup]=partially": 32006,
    "[IsSup]=no_support": 32007,
    "[IsUse]=1": 32008,
    "[IsUse]=2": 32009,
    "[IsUse]=3": 32010,
    "[IsUse]=4": 32011,
    "[IsUse]=5": 32012,
}


@dataclass
class ReflectionConfig:
    """추론 시 반성 토큰 가중치 설정."""
    w_rel: float = 1.0   # [IsRel] 가중치
    w_sup: float = 1.0   # [IsSup] 가중치
    w_use: float = 0.5   # [IsUse] 가중치
    retrieve_threshold: float = 0.5  # [Retrieve]=yes 판단 임계값
    top_k_docs: int = 5  # 검색할 문서 수


class SelfRAGModel:
    """Self-RAG 추론 파이프라인 (단순화)."""

    def __init__(self, model, tokenizer, retriever, config: ReflectionConfig):
        self.model = model
        self.tokenizer = tokenizer
        self.retriever = retriever
        self.config = config

    def should_retrieve(self, input_ids: torch.Tensor) -> bool:
        """Step 1: [Retrieve] 토큰으로 검색 필요성 판단."""
        logits = self.model(input_ids).logits
        retrieve_probs = torch.softmax(logits[:, -1, :], dim=-1)
        # yes / no / continue 확률 비교
        p_yes = retrieve_probs[0, SPECIAL_TOKENS["[Retrieve]=yes"]].item()
        p_no = retrieve_probs[0, SPECIAL_TOKENS["[Retrieve]=no"]].item()
        return p_yes > self.config.retrieve_threshold

    def extract_reflection_scores(
        self, logits: torch.Tensor
    ) -> Dict[str, float]:
        """생성된 시퀀스에서 반성 토큰 확률을 추출."""
        probs = torch.softmax(logits[:, -1, :], dim=-1)
        # [IsRel] 점수: relevant 확률의 정규화
        p_rel = probs[0, SPECIAL_TOKENS["[IsRel]=relevant"]].item()
        p_irrel = probs[0, SPECIAL_TOKENS["[IsRel]=irrelevant"]].item()
        score_rel = p_rel / (p_rel + p_irrel + 1e-8)
        # [IsSup] 점수: fully supported 확률의 정규화
        p_full = probs[0, SPECIAL_TOKENS["[IsSup]=fully"]].item()
        p_none = probs[0, SPECIAL_TOKENS["[IsSup]=no_support"]].item()
        score_sup = p_full / (p_full + p_none + 1e-8)
        # [IsUse] 점수: 가중 평균
        score_use = sum(
            (i + 1) * probs[0, SPECIAL_TOKENS[f"[IsUse]={i+1}"]].item()
            for i in range(5)
        ) / 5.0
        return {"IsRel": score_rel, "IsSup": score_sup, "IsUse": score_use}

    def score_segment(self, reflection_scores: Dict[str, float]) -> float:
        """Step 4: 반성 토큰 점수를 종합하여 세그먼트 순위 계산."""
        return (
            self.config.w_rel * reflection_scores["IsRel"]
            + self.config.w_sup * reflection_scores["IsSup"]
            + self.config.w_use * reflection_scores["IsUse"]
        )

    def generate_with_reflection(self, query: str) -> str:
        """Self-RAG 전체 추론 루프."""
        input_ids = self.tokenizer.encode(query, return_tensors="pt")
        output_segments = []

        for step in range(10):  # 최대 10 세그먼트
            # Step 1: 검색 필요 여부 판단
            if self.should_retrieve(input_ids):
                # Step 2: 문서 검색
                docs = self.retriever.search(
                    query, top_k=self.config.top_k_docs
                )
                # Step 3: 각 문서별로 세그먼트 생성 + 반성 토큰 추출
                candidates = []
                for doc in docs:
                    doc_ids = self.tokenizer.encode(doc.text)
                    combined = torch.cat([input_ids, doc_ids], dim=-1)
                    output = self.model.generate(combined, max_new_tokens=128)
                    logits = self.model(output).logits
                    scores = self.extract_reflection_scores(logits)
                    total = self.score_segment(scores)
                    candidates.append((output, total, scores))
                # Step 4: 최고 점수 세그먼트 선택
                best = max(candidates, key=lambda x: x[1])
                output_segments.append(best[0])
            else:
                # 검색 없이 직접 생성
                output = self.model.generate(
                    input_ids, max_new_tokens=128
                )
                output_segments.append(output)

            # 다음 세그먼트를 위해 입력 업데이트
            input_ids = torch.cat(
                [input_ids] + [seg for seg in output_segments[-1:]],
                dim=-1
            )

        return self.tokenizer.decode(
            torch.cat(output_segments, dim=-1)[0]
        )


# 태스크별 설정 예시
factual_config = ReflectionConfig(
    w_rel=1.0, w_sup=2.0, w_use=0.5  # 사실성 중시: IsSup 가중치 최대
)
creative_config = ReflectionConfig(
    w_rel=0.3, w_sup=0.3, w_use=2.0  # 창의성 중시: IsUse 가중치 최대
)
fast_config = ReflectionConfig(
    retrieve_threshold=0.8  # 속도 중시: 검색 임계값 상향으로 검색 최소화
)
```

> **핵심 포인트**: Self-RAG의 반성 토큰은 검색, 생성, 비평을 단일 모델 내에서 통합합니다. 추론 시 `ReflectionConfig`의 가중치를 조절하면 별도 재학습 없이도 사실성 중시, 창의성 중시, 속도 중시 등 다양한 모드로 전환할 수 있습니다. 특히 `extract_reflection_scores` 메서드에서 보듯이, 반성 토큰의 softmax 확률을 정규화하여 점수를 산출하고, 이를 가중합으로 조합하는 것이 segment-level beam search의 핵심입니다.