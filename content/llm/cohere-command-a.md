---
title: "Cohere Command A: 대규모 언어 모델"
slug: "cohere-command-a"
category: llm
tags: ["Agentic AI", "Cohere", "Cohere Command A", "enterprise-ai", "Function Calling", "Long Context", "rag"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.126681+00:00"
architecture_entry: "cohere-command-a"
---

# Cohere Command A: 기업 에이전틱 워크플로를 위한 111B 언어 모델

**Cohere** · **2025-03-13** · **Decoder-only** · **Proprietary (CC-NC 연구용 공개)**

## 개요

Cohere Command A는 Cohere가 2025년 3월 공개한 111B 파라미터 기업용 대형 언어 모델로, 256K 토큰의 초장문 컨텍스트를 지원한다. 기업 환경에서의 에이전틱 태스크, RAG(검색 증강 생성), 다국어 처리, 복잡한 분석 워크플로에 최적화되어 있다. GPT-4o 및 Claude 3.5 Sonnet 대비 유사하거나 우수한 성능을 보이면서도, 2개의 GPU 서버에서 셀프 호스팅이 가능한 실용적인 배포 효율성을 갖추고 있어 온프레미스 기업 배포에 적합하다.

Command A는 Cohere의 기업 AI 전략에서 핵심적인 위치를 차지한다. 기존 Command 시리즈가 범용 텍스트 생성에 초점을 맞췄다면, Command A는 에이전틱 워크플로—도구 호출, 멀티스텝 추론, 구조화된 출력을 통해 복잡한 비즈니스 프로세스를 자동화하는 능력—에 특화되었다. 23개 비즈니스 언어를 지원하여 글로벌 기업 환경에서의 실용성을 극대화하였으며, 특히 RAG 파이프라인에서의 사실성(factuality)이 크게 강화되어 기업의 내부 지식 기반 질의응답에 높은 신뢰성을 제공한다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

### 기본 구조

Command A는 현대 LLM의 표준 아키텍처 구성 요소를 채택하면서, 기업 배포에 최적화된 설계를 적용했다.

| 구성 요소 | 사양 |
|-----------|------|
| **파라미터** | 111B |
| **컨텍스트 길이** | 256K 토큰 |
| **어텐션** | Grouped Query Attention (GQA) |
| **정규화** | RMSNorm |
| **활성화 함수** | SwiGLU |
| **위치 인코딩** | RoPE |
| **어휘 크기** | 미공개 |
| **배포 요구** | H100 서버 2대 (16 GPU) |

### GQA 기반 효율적 어텐션

Command A는 GQA(Grouped Query Attention)를 채택하여 추론 시 KV 캐시 메모리를 절감한다. GQA에서는 Query 헤드가 여러 개의 그룹으로 나뉘어 각 그룹이 하나의 KV 헤드를 공유한다:

$$\text{GQA}: Q \in \mathbb{R}^{n_h \times d_h}, \quad K, V \in \mathbb{R}^{n_g \times d_h}, \quad n_g \ll n_h$$

이 구조 덕분에 256K라는 초장문 컨텍스트에서도 메모리 효율을 유지하면서 높은 처리량을 달성할 수 있다. 111B 규모의 모델이 단 2대의 H100 서버(총 16개 GPU)에서 구동 가능한 것은 GQA의 KV 캐시 절감 효과가 크게 기여한 것으로 보인다.

### RoPE를 통한 장문 컨텍스트 지원

RoPE(Rotary Position Embedding)는 상대적 위치를 복소수 회전으로 인코딩한다:

$$f(x_m, m) = x_m e^{im\theta}, \quad \theta_j = 10000^{-2j/d}$$

256K 토큰까지의 컨텍스트를 지원하기 위해 RoPE의 주파수 스케일링 기법(NTK-aware Scaling 또는 YaRN 계열)이 적용되었을 것으로 추정된다. 이를 통해 전체 코드베이스, 법률 문서, 재무 보고서 등 초장문 문서를 한 번에 처리할 수 있다.

### 에이전틱 기능 아키텍처

Command A의 에이전틱 워크플로 지원은 다음과 같은 기능으로 구현된다:

```python
import cohere

co = cohere.ClientV2(api_key="your-api-key")

# 멀티스텝 에이전트 워크플로 예시
tools = [
    {"type": "function", "function": {
        "name": "search_documents",
        "description": "Search internal knowledge base",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filters": {"type": "object"}
            }
        }
    }},
    {"type": "function", "function": {
        "name": "generate_report",
        "description": "Generate structured business report",
        "parameters": {
            "type": "object",
            "properties": {
                "template": {"type": "string"},
                "data": {"type": "array"}
            }
        }
    }}
]

response = co.chat(
    model="command-a",
    messages=[{"role": "user", "content": "지난 분기 매출 데이터를 분석하고 보고서를 생성해줘"}],
    tools=tools
)
```

## 핵심 혁신

Command A의 핵심 혁신은 세 가지이다. 첫째, **기업용 에이전틱 최적화**로 함수 호출(function calling), 구조화된 출력, 다단계 에이전트 실행에서 높은 신뢰성을 보인다. 23개 비즈니스 언어 지원으로 글로벌 기업 환경에서 단일 모델로 다국어 워크플로를 처리할 수 있다. 둘째, **RAG 최적화**로 검색된 문서에 기반한 응답 생성 시 환각(hallucination)을 최소화하고 근거 인용(citation) 정확도를 향상시켰다. 셋째, **배포 효율성**으로 111B 모델이 단 2대의 H100 서버에서 셀프 호스팅이 가능하여, 데이터 주권과 보안 요구사항이 엄격한 금융, 의료, 법률 분야에서 자체 인프라로 운영할 수 있다.

## 벤치마크/성능

| 벤치마크 | Command A | GPT-4o | Claude 3.5 Sonnet |
|---------|-----------|--------|-------------------|
| **에이전틱 태스크** | **경쟁력 있음** | 최고 수준 | 최고 수준 |
| **RAG 정확도** | **강화** | 양호 | 양호 |
| **다국어 (23개)** | **네이티브** | 양호 | 양호 |
| **함수 호출** | **높은 신뢰성** | 높음 | 높음 |
| **256K 컨텍스트** | **지원** | 128K | 200K |
| **온프레미스** | **2 서버** | 불가 | 불가 |

Command A는 벤치마크 최고 성능보다 기업 환경에서의 실용성과 배포 효율성에 집중한 모델이다.

## 학습

기업 도메인(법률, 금융, 의료, 기술) 데이터를 중심으로 사전 학습하였으며, 에이전틱 태스크와 RAG 시나리오에 최적화된 미세조정이 적용되었다. 구체적인 훈련 토큰 수 및 데이터 구성은 공개되지 않았으나, 함수 호출 및 도구 사용 특화 훈련이 포함된 것으로 알려져 있다. Cohere의 학습 파이프라인은 사전 학습 → SFT → RLHF/DPO 정렬의 표준 구조를 따르되, 에이전틱 태스크에 대한 별도의 정렬 단계가 포함된 것으로 보인다.

## 관련 모델

Command A는 Cohere의 Command 시리즈에서 가장 최신 모델로, Transformer 아키텍처에서 발전하였다. 기업 시장에서 GPT-4o, Claude 3.5 Sonnet과 직접 경쟁하며, 특히 온프레미스 배포와 에이전틱 기능에서 차별화를 추구한다.


### Agentic AI에 관하여

에이전틱 AI는 도구 사용, 멀티스텝 추론, 자율적 의사결정을 통해 복잡한 태스크를 수행하는 AI 시스템이다. MCP(Model Context Protocol) 기반 도구 사용과 적응적 추론 능력이 강화되어, 복잡한 워크플로 자동화와 장기 수평(long-horizon) 에이전트 작업을 수행할 수 있다.

## 실무 활용

### 1. API 기반 서비스
Cohere Command A은 API를 통해 접근 가능하며, 다양한 프로덕션 환경에서 활용된다.

### 2. 에이전트 시스템
function calling과 구조화된 출력을 활용한 에이전트 구축에 적합하다.

### 3. 전문 영역
RAG, Agentic AI 분야에서의 강점을 활용한 전문 서비스 구축이 가능하다.

## 한계 및 전망

### 한계

1. **아키텍처 비공개**: 구체적인 구조가 공개되지 않아 연구 재현이 불가능하다.
2. **API 의존**: 클라우드 API를 통해서만 접근 가능하다.
3. **비용**: 대규모 활용 시 비용이 상당할 수 있다.

### 전망

Cohere Command A은 RAG, Agentic AI, Function Calling 분야의 발전에 기여하며, 향후 더 발전된 후속 모델로 진화할 것으로 예상된다.

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다.

**모델 규모와 효율**: Cohere Command A은 111B 규모의 파라미터를 가지며, 256K 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### Long Context에 관하여

장문 컨텍스트 지원은 RoPE 확장(NTK-aware, YaRN, LongRoPE)이나 선형 어텐션 기법을 통해 수십만 토큰의 입력을 처리하는 능력이다. 대규모 코드베이스, 법률 문서, 장편 소설 등의 분석에 필수적이며, KV 캐시 관리와 어텐션 효율이 핵심 과제이다.

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Cohere Command A은 111B 규모의 파라미터를 가지며, 256K 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Cohere Command A은 111B 규모의 파라미터를 가지며, 256K 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Cohere Command A은 111B 규모의 파라미터를 가지며, 256K 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.

## 참고 자료

- [Cohere Command A 발표](https://cohere.com/blog/command-a)

## 관련 문서

- [[transformer|Transformer]] — 발전 기반
