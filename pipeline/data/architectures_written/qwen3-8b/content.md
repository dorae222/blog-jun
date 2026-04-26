<!-- infographic-hero -->
![Qwen3-8B 핵심 요약](figures/infographic.svg)

*Figure: Qwen3-8B 한 장 요약 인포그래픽*

# Qwen3-8B: 8B Dense의 한계를 끌어올린 멀티링구얼 에이전트 모델

## 개요

Qwen3-8B는 Alibaba Cloud가 2025년 4월 29일 공개한 Qwen3 시리즈의 8B Dense 변형이다. Qwen3 시리즈는 0.6B / 1.7B / 4B / 8B / 14B / 32B Dense 라인업과 30B-A3B / 235B-A22B MoE 라인업으로 구성되며, 8B는 그중 SLM(Small Language Model)과 중대형 모델 사이의 실용적 균형점에 해당한다.

8B Dense는 단일 GPU(H100 또는 RTX 4090) 추론이 가능하고, 4bit 양자화 시 16GB 정도의 메모리로 동작하며, 자체 호스팅 RAG와 에이전트 시스템의 백본으로 가장 자주 채택되는 클래스이다. Qwen3-8B는 이러한 클래스의 표준에 119개 언어 지원, 듀얼 모드 추론(thinking/non-thinking), 강력한 함수 호출(function calling) 능력을 결합하여, Llama 3.1 8B Instruct, Mistral 7B v0.3, Gemma 2 9B를 종합 벤치마크에서 능가한다.

특히 Qwen3-8B는 시리즈 최상위 모델인 Qwen3-235B-A22B에서 logit-level distillation된 추론 능력을 계승하여, 동일 규모를 from-scratch로 학습한 모델보다 수학·코드·논리 추론에서 명확한 우위를 보인다. Apache 2.0 라이선스로 상업적 활용도 자유롭다.

## 아키텍처 상세

### 기본 구조

| 구성 요소 | 사양 |
|-----------|------|
| **아키텍처** | Dense Decoder-only Transformer |
| **파라미터 수** | 8.19B |
| **레이어 수** | 36 |
| **히든 차원** | 4,096 |
| **FFN 중간 차원** | 12,288 |
| **어텐션 헤드** | 32 (Q) / 8 (KV) |
| **어텐션** | Grouped Query Attention (GQA, 4:1) |
| **정규화** | RMSNorm |
| **활성화 함수** | SwiGLU |
| **위치 인코딩** | RoPE (theta=1,000,000) |
| **컨텍스트 길이** | 32K (YaRN 확장 시 131K) |
| **어휘 수** | 151,936 (Qwen 공통 토크나이저) |

### Qwen3 Dense 라인업 내 위치

| 모델 | 파라미터 | 레이어 | 히든 | KV 헤드 |
|------|---------|--------|------|---------|
| Qwen3-0.6B | 0.6B | 28 | 1,024 | 8 |
| Qwen3-1.7B | 1.7B | 28 | 2,048 | 8 |
| Qwen3-4B | 4B | 36 | 2,560 | 8 |
| **Qwen3-8B** | **8B** | **36** | **4,096** | **8** |
| Qwen3-14B | 14B | 40 | 5,120 | 8 |
| Qwen3-32B | 32B | 64 | 5,120 | 8 |

8B와 4B는 동일한 36 레이어를 공유하면서 히든 차원(2,560 → 4,096)으로 차별화되었다. 모든 모델이 KV 헤드 8개로 통일되어 있어 KV 캐시 메모리가 효율적이다.

## 핵심 혁신

### 1. Thinking / Non-Thinking 듀얼 모드

Qwen3 시리즈 공통의 핵심 혁신으로, 시스템 프롬프트나 토크나이저 옵션의 `enable_thinking` 플래그로 두 모드를 전환한다.

- **Thinking Mode**: `<think>...</think>` 블록에서 단계별 추론 후 답변 생성. 수학, 코딩, 논리 문제에 적합.
- **Non-Thinking Mode**: 직접 답변 생성. 일반 채팅, 빠른 응답이 필요한 경우.

```
# Thinking 활성화 예
messages = [{"role": "user", "content": "..."}]
text = tokenizer.apply_chat_template(
    messages, tokenize=False, enable_thinking=True
)
```

8B 모델에서도 thinking 활성화 시 GSM8K, MATH 점수가 비활성 대비 평균 7-15점 향상된다.

### 2. 235B MoE에서의 Distillation

Qwen3-8B는 단순 from-scratch 학습이 아니라, Qwen3-235B-A22B MoE의 logit 분포를 distillation 타겟으로 활용하였다. 이는 다음과 같은 손실로 학습된다.

$$\mathcal{L}_{\text{distill}} = \alpha \cdot \text{CE}(y, \hat{y}_{\text{8B}}) + (1 - \alpha) \cdot \text{KL}(\hat{y}_{\text{235B}} \| \hat{y}_{\text{8B}})$$

여기서 $\hat{y}_{\text{235B}}$는 큰 모델의 soft label, $\hat{y}_{\text{8B}}$는 학습 중인 8B 모델의 출력 분포이다. 이 distillation 덕분에 8B 모델임에도 추론 능력에서 동급 from-scratch 모델 대비 명확한 우위를 가진다.

### 3. 119개 언어 지원

Qwen3-8B는 119개 자연어와 지원 언어 군으로 학습되었다. 이는 Llama 3.1 8B(8개 주요 언어)나 SmolLM3(6개 유럽 언어) 대비 압도적으로 넓은 범위이다. 한국어, 일본어, 중국어 등 동아시아 언어 성능도 뛰어나며, 베트남어, 태국어, 인도네시아어 등 동남아 언어도 견고하게 지원한다.

### 4. 에이전트 친화 설계

Qwen3-8B는 ReAct, Qwen-Agent, MCP(Model Context Protocol)와 직접 호환된다. SFT 단계에서 다음 도구 호출 데이터로 학습되었다.

- 함수 호출(Function Calling) - JSON 스키마 기반
- 다단계 도구 사용(Multi-step Tool Use)
- 코드 인터프리터 호출
- 웹 검색·문서 검색 통합

특히 BFCL(Berkeley Function Calling Leaderboard) v3에서 동급 8B 모델 중 최고 점수를 기록한다.

## 성능 비교

### 동급 8B 모델 종합 벤치마크

| 모델 | MMLU | GSM8K | MATH | HumanEval | BFCL | MMLU-Pro |
|------|------|-------|------|-----------|------|----------|
| **Qwen3-8B (thinking)** | 76.2 | 92.4 | 70.3 | 84.8 | 75.2 | 56.7 |
| Qwen3-8B (non-thinking) | 73.4 | 84.9 | 56.6 | 80.5 | 70.1 | 51.2 |
| Llama 3.1 8B Instruct | 69.4 | 84.5 | 30.0 | 72.6 | 60.4 | 41.2 |
| Mistral 7B v0.3 Instruct | 60.1 | 50.3 | 13.1 | 40.2 | 45.3 | 30.1 |
| Gemma 2 9B Instruct | 71.3 | 76.7 | 36.6 | 67.7 | 58.2 | 46.7 |
| Qwen2.5 7B Instruct | 74.2 | 85.4 | 49.8 | 84.8 | 67.4 | 48.5 |

Thinking 모드 활성화 시 Qwen3-8B는 거의 모든 벤치마크에서 동급 모델을 압도하며, 특히 MATH(70.3 vs Llama 3.1의 30.0)에서 큰 격차를 보인다.

### 상위 모델 및 클로즈드 소스 대비

| 벤치마크 | Qwen3-8B (think) | Qwen3-32B (think) | Qwen3-235B (think) | GPT-4o-mini | Claude Haiku 3.5 |
|----------|------------------|-------------------|---------------------|-------------|-------------------|
| MMLU | 76.2 | 81.1 | 84.5 | 82.0 | 81.4 |
| GSM8K | 92.4 | 95.4 | 96.8 | 91.4 | 91.3 |
| HumanEval | 84.8 | 89.0 | 91.5 | 87.2 | 88.4 |

8B 모델임에도 GPT-4o-mini, Claude Haiku 3.5에 근접하거나 일부 벤치마크에서는 동등한 성능을 보인다.

## 사용 사례

### 1. 자체 호스팅 RAG 시스템

32K 컨텍스트와 119개 언어 지원으로 다국어 문서 RAG에 최적화되어 있다. vLLM, SGLang, Ollama와 통합하여 자체 호스팅 시 토큰당 비용을 클로즈드 모델 대비 1/20 이하로 낮출 수 있다.

### 2. 에이전트 시스템 백본

BFCL v3 최상위 점수와 MCP 호환성으로 LangGraph, AutoGen, CrewAI 등 에이전트 프레임워크의 LLM 백본으로 적합하다. 다단계 도구 호출에서도 신뢰성이 높다.

### 3. 다국어 챗봇

한국어, 일본어, 중국어, 베트남어, 태국어 등 아시아 언어 챗봇 구축 시 가장 균형 잡힌 8B 모델이다. 영어 외 언어에서도 thinking 모드가 정상 작동한다.

### 4. 코드 어시스턴트

HumanEval 84.8(thinking)으로 Qwen2.5-Coder-7B에 근접한 코드 생성 능력을 보인다. 200+ 프로그래밍 언어를 지원하며, IDE 플러그인의 로컬 LLM 백엔드로 활용된다.

### 5. 비용 효율 추론 워크로드

대량 분류, 요약, 데이터 라벨링 등에서 thinking 모드를 끄고(non-thinking) 사용하면 빠른 처리량을 얻을 수 있다. RTX 4090 단일 GPU로 vLLM 기준 초당 80-120 토큰을 생성한다.

## 한계 및 의의

### 한계

1. **컨텍스트 길이 제한**: 기본 32K로 Qwen3-32B/235B(128K)나 Claude(200K)에 비해 짧다. YaRN으로 131K까지 확장 가능하나 정확도 손실이 발생한다.
2. **상위 모델과의 추론 격차**: thinking 활성화에도 Qwen3-32B Dense 대비 MMLU 5점, MATH 10점 정도 뒤처진다. 복잡한 멀티홉 추론은 상위 모델이 필요하다.
3. **Vision 미지원**: Qwen3-VL과 별개의 모델로, 텍스트 전용이다. 멀티모달 입력은 Qwen3-VL 또는 Qwen3-Omni를 사용해야 한다.
4. **Distillation 의존성**: 235B MoE에서 distillation된 결과이므로, 원본 데이터 분포 외 영역에서는 8B의 본질적 한계가 드러난다.
5. **메모리 요구사항**: bf16 추론 시 약 16GB GPU 메모리가 필요하여, 일부 엣지 디바이스에서는 양자화 없이 실행이 어렵다.

### 의의

Qwen3-8B는 "8B 클래스의 새 기준"을 세운 모델이다. distillation을 통해 소형 모델이 대형 모델의 추론 능력을 이식 받을 수 있음을 강력히 입증하였고, thinking 모드의 8B 적용 가능성도 확인하였다. 119개 언어 지원과 Apache 2.0 라이선스는 글로벌 자체 호스팅 AI 인프라 구축의 핵심 자산이 된다.

특히 Qwen3 시리즈의 가족(family) 전략은 흥미롭다. 0.6B(엣지) → 8B(자체 호스팅) → 32B(고성능) → 235B MoE(최고 성능)의 연속 스펙트럼을 동일 토크나이저, 동일 추론 인터페이스로 제공함으로써, 사용자는 워크로드별로 모델을 자유롭게 교체할 수 있다. Qwen3-8B는 이 스펙트럼의 "sweet spot"으로 자리잡으며, 이후 Qwen3.5, Qwen4 시리즈의 8B 변형도 동일한 설계 철학을 계승할 것으로 예상된다.

## 관련 문서

- [[qwen3|Qwen3]] - Qwen3 시리즈 전체 아키텍처
- [[qwen2-5|Qwen2.5]] - 직전 세대 7B 모델
- [[qwen3-vl|Qwen3-VL]] - 비전-언어 변형
- [[qwen3-omni|Qwen3-Omni]] - 멀티모달 변형
- [[smollm3-3b|SmolLM3-3B]] - 더 작은 풀 오픈 SLM
- [[mistral-small-3|Mistral Small 3]] - 같은 efficiency 카테고리의 24B 모델
