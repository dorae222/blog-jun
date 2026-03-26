# GPT-4: 멀티모달 대형 언어 모델

## 개요

**GPT-4**는 OpenAI가 2023년 3월 14일 공개한 **멀티모달 대형 언어 모델**로, 텍스트와 이미지를 입력으로 처리할 수 있는 최초의 GPT 시리즈 모델이다. 공식 기술 보고서에서는 구체적인 아키텍처와 파라미터 수를 공개하지 않았으나, 외부 분석에 따르면 약 **8개의 220B 전문가 모델로 구성된 Mixture of Experts(MoE)** 구조로 추정된다.

GPT-4는 단순한 벤치마크 성능을 넘어, **인간 수준의 전문적 추론 능력**을 보여준 최초의 AI 모델이다. 사법시험, 의학 면허시험, SAT 등 다양한 인간 시험에서 상위 10% 수준의 성과를 달성하며, AI가 전문 영역에서도 실질적인 도구가 될 수 있음을 입증했다.

## 아키텍처 상세

### Mixture of Experts (MoE) 구조 (추정)

공식적으로 확인되지는 않았으나, 외부 분석에 기반한 추정 구조:

- **전문가 수**: 16개
- **활성 전문가**: 2개 (각 토큰 처리 시)
- **총 파라미터**: ~1.8T
- **활성 파라미터**: ~220B (추론 시)
- **컨텍스트**: 8K → 32K → **128K** (점진적 확장)

MoE 구조의 핵심은 **라우팅 메커니즘**이다. 각 토큰이 전체 전문가 중 일부(Top-K)만 활성화하므로, 총 파라미터 수 대비 추론 비용이 크게 절감된다:

$$y = \sum_{i=1}^{K} g_i \cdot E_i(x), \quad g = \text{TopK}(\text{softmax}(W_g \cdot x))$$

### 멀티모달 처리

GPT-4V(Vision)는 이미지를 패치(patch) 단위로 분할하고, 각 패치를 Vision Encoder(ViT 기반 추정)를 통해 토큰 임베딩으로 변환한 후 언어 모델의 입력 시퀀스에 합류시킨다.

### 위치 인코딩

GPT-3의 Learned Absolute에서 **RoPE(Rotary Position Embedding)**로 전환한 것으로 추정된다. RoPE는 상대 위치 정보를 회전 행렬로 인코딩하여, 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽 성능이 우수하다:

$$f(x_m, m) = x_m e^{im\theta}$$

### Function Calling

GPT-4는 **Function Calling** 기능을 통해 외부 도구와 상호작용할 수 있다:

```python
import openai

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "서울의 현재 날씨를 알려줘"}],
    functions=[{
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "도시명"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    }]
)
```

## 핵심 혁신

### 1. 인간 수준의 전문적 추론

다양한 전문 시험에서 인간 상위 퍼센타일 성과:

| 시험 | GPT-4 성적 | 인간 대비 |
|------|----------|----------|
| Uniform Bar Exam | 298/400 | 상위 ~10% |
| SAT Reading | 710/800 | 93 퍼센타일 |
| SAT Math | 700/800 | 89 퍼센타일 |
| GRE Quantitative | 163/170 | 80 퍼센타일 |
| AP Biology | 5 | 최고 등급 |
| LSAT | ~163 | 상위 ~12% |

### 2. 멀티모달 입력 처리

텍스트뿐 아니라 이미지를 입력으로 받아 차트 해석, 문서 이해, 시각적 추론 등을 수행한다.

### 3. 예측 가능한 스케일링

GPT-4 프로젝트의 중요한 성과 중 하나는 **소규모 모델의 성능으로 대규모 모델의 성능을 예측**할 수 있는 인프라를 구축한 것이다.

## 벤치마크/성능

| 벤치마크 | GPT-3.5 | GPT-4 | 개선폭 |
|---------|---------|-------|-------|
| MMLU (5-shot) | 70.0% | **86.4%** | +16.4% |
| HellaSwag (10-shot) | 85.5% | **95.3%** | +9.8% |
| HumanEval (0-shot) | 48.1% | **67.0%** | +18.9% |
| WinoGrande | 81.6% | **87.5%** | +5.9% |
| Bar Exam | ~10 퍼센타일 | **~90 퍼센타일** | 대폭 향상 |

MMLU에서 GPT-4는 26개 비영어 언어에서도 영어 SOTA를 능가하는 다국어 성능을 보였다.

## 관련 모델 비교

| 특성 | GPT-3 | GPT-3.5/ChatGPT | GPT-4 |
|------|-------|-----------------|-------|
| 파라미터 | 175B (Dense) | ~175B | ~1.8T (MoE) |
| 컨텍스트 | 2048 | 4096 | **128K** |
| 멀티모달 | No | No | **Yes** |
| MMLU | ~43% (FS) | 70% | **86.4%** |
| 정렬 | 기본 | RLHF | **강화 RLHF** |
| Function Calling | No | 제한적 | **Yes** |
| 배포 | API | ChatGPT + API | ChatGPT + API |

## 실무 활용

### 주요 활용 분야

1. **ChatGPT Plus**: 소비자용 대화형 AI의 핵심 엔진
2. **GitHub Copilot**: 코드 생성 및 리뷰
3. **Bing Chat (Copilot)**: 검색 통합 AI 어시스턴트
4. **기업 솔루션**: 문서 분석, 고객 서비스, 법률 리서치
5. **교육**: 개인화 튜터링, 시험 준비
6. **의료**: 진단 보조, 의학 문헌 분석

### 에이전트 활용

Function Calling과 System Prompt를 결합하여 복잡한 워크플로우를 자동화하는 **AI 에이전트** 구축이 가능해졌다.

## 한계 및 전망

### 한계

1. **아키텍처 비공개**: 재현 불가능한 폐쇄형 모델
2. **환각**: 여전히 사실이 아닌 정보를 자신 있게 생성
3. **시간 제약**: 학습 데이터 컷오프 이후 정보에 대한 무지
4. **비용**: 128K 컨텍스트 사용 시 높은 API 비용
5. **멀티모달 한계**: 이미지 생성은 불가, 입력만 처리

### 전망

GPT-4는 AI의 **범용성(generality)**이 특정 수준을 넘으면 실용적 가치가 급격히 증가한다는 것을 보여주었다. 이후 GPT-4 Turbo(비용 절감), GPT-4V(비전 강화), GPT-4o(옴니 모달)로 이어지는 빠른 반복 업데이트가 진행되었고, GPT-4.1과 GPT-5로의 진화가 계속되고 있다.

### 어텐션 메커니즘: MHA

Multi-Head Attention(MHA)은 Transformer의 핵심 메커니즘으로, 입력을 여러 헤드로 분할하여 병렬적으로 어텐션을 계산한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O$$

각 헤드는 서로 다른 표현 부분공간(subspace)에서 정보를 추출하며, 결과를 결합하여 풍부한 표현을 학습한다. 추론 시에는 모든 Q 헤드에 대해 별도의 KV를 유지해야 하므로 KV 캐시 비용이 높다는 단점이 있다.
### 스케일링 법칙과의 관계

Chinchilla 스케일링 법칙에 따르면, 모델 파라미터 수 $N$과 학습 토큰 수 $D$의 최적 비율은 다음과 같이 결정된다:

$$L(N, D) = \frac{A}{N^\alpha} + \frac{B}{D^\beta} + E$$

여기서 $\alpha \approx 0.34$, $\beta \approx 0.28$이다. 이 법칙은 학습 예산이 주어졌을 때 모델 크기와 데이터 양의 최적 균형점을 결정하는 데 핵심적인 역할을 하며, 이 모델의 학습 전략에도 영향을 미쳤을 것으로 추정된다.

### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**모델 규모와 효율**: GPT-4은 ~1.8T (rumored MoE) 규모의 파라미터를 가지며, 128000 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: GPT-4은 ~1.8T (rumored MoE) 규모의 파라미터를 가지며, 128000 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: GPT-4은 ~1.8T (rumored MoE) 규모의 파라미터를 가지며, 128000 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: GPT-4은 ~1.8T (rumored MoE) 규모의 파라미터를 가지며, 128000 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.

---

**참고 논문**: [GPT-4 Technical Report](https://arxiv.org/abs/2303.08774) (OpenAI, 2023)

## 관련 문서

- [[gpt-3|Language Models are Few-Shot Learners (GPT-3)]] — 발전 기반
- [[instructgpt|Training language models to follow instructions with human feedback]] — 발전 기반
- [[gpt-4-1|GPT-4.1]] — 후속 모델
- [[gpt-4o|GPT-4o]] — 후속 모델
- [[gpt-5|GPT-5]] — 후속 모델
- [[o1|OpenAI o1]] — 후속 모델
- [[grok-3|Grok 3]] — 영감을 줌
