---
title: "Claude (1~3.5 시리즈): Anthropic의 Constitutional AI 기반 대형 언어 모델"
slug: claude
category: llm
tags: ["Alignment", "Anthropic", "Claude", "Constitutional AI", "Harmless AI", "Multimodal", "RLAIF", "RLHF", "Safety"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.472927+00:00"
architecture_entry: claude
---

# Claude (1~3.5 시리즈): Anthropic의 Constitutional AI 기반 대형 언어 모델

## 개요

Claude는 Anthropic이 개발한 대규모 언어 모델 시리즈로, 2023년 3월 첫 공개 이후 Claude 1, Claude 2, Claude 3(Haiku, Sonnet, Opus), Claude 3.5 시리즈까지 지속적으로 진화해왔다. GPT-3에서 영감을 받아 설계되었지만, 단순한 성능 극대화보다 **안전성(safety)**과 **무해성(harmlessness)**을 우선시하는 독자적 방향으로 발전해왔다.

Anthropic은 OpenAI 출신 연구자들이 설립한 AI 안전 연구 기업으로, 그들의 핵심 연구 성과인 **Constitutional AI(CAI)**를 실제 제품에 접목한 대표적 사례가 바로 Claude이다. 기존 RLHF 방식이 인간 라벨러의 주관적 판단에 의존하는 반면, CAI는 사전 정의된 원칙 집합(헌법)에 따라 모델이 스스로 출력을 비판·수정하도록 훈련한다.

## 아키텍처 상세

### 기본 구조

Claude 시리즈는 **Decoder-only Transformer** 구조를 기반으로 하며, 추정되는 주요 구성 요소는 다음과 같다:

- **Attention**: Multi-Head Attention (MHA)
- **정규화**: RMSNorm
- **활성화 함수**: SwiGLU
- **위치 인코딩**: RoPE (Rotary Position Embedding)
- **컨텍스트 길이**: 200K 토큰 (Claude 3 기준)

Anthropic은 GPT나 LLaMA와 달리 기술 보고서(Technical Report)를 공개하지 않고, **시스템 카드(Model Card)** 형태로만 안전성 평가 결과를 투명하게 공개하는 정책을 유지한다. 따라서 정확한 파라미터 수, 레이어 수, 히든 차원 등은 비공개 상태이다.

### Claude 3 시리즈 구성

Claude 3는 세 가지 티어로 구성된다:

| 모델 | 특징 | 용도 |
|------|------|------|
| **Haiku** | 경량, 빠른 추론 | 실시간 챗봇, 간단한 작업 |
| **Sonnet** | 성능-비용 균형 | 일반 목적, 코딩, 분석 |
| **Opus** | 최고 성능 | 복잡한 추론, 연구 |

## 핵심 혁신

### 1. Constitutional AI (CAI)

CAI는 Claude의 정렬(alignment) 방법론의 핵심이다. 기존 RLHF가 인간 라벨러의 직접적 피드백에 의존하는 반면, CAI는 다음과 같은 2단계 프로세스를 따른다:

**1단계 - 자기 비판 (Self-Critique):**
모델이 출력을 생성한 후, 사전 정의된 원칙("헌법")에 따라 자신의 출력을 비판하고 수정한다.

**2단계 - RLAIF (RL from AI Feedback):**
인간 피드백 대신 AI 자체가 헌법적 원칙에 근거해 피드백을 생성하여 강화학습을 진행한다.

이 접근법의 수학적 핵심은 보상 함수 $R(x, y)$를 인간 라벨러가 아닌 AI 모델이 생성한다는 점이다:

$$R_{\text{RLAIF}}(x, y) = \mathbb{E}_{\text{AI}}[\text{preference}(y | x, \text{constitution})]$$

### 2. 200K 토큰 초장문 컨텍스트

Claude 3부터 200K 토큰(약 15만 단어)의 컨텍스트 윈도우를 지원한다. RoPE 기반 위치 인코딩의 외삽(extrapolation) 능력을 활용하여, 전체 소설이나 대규모 코드베이스를 한 번에 처리할 수 있다.

### 3. 멀티모달 입력 지원

Claude 3 시리즈부터 이미지와 문서를 직접 입력으로 받아 처리할 수 있는 멀티모달 기능을 지원한다. 다이어그램 해석, 차트 분석, 문서 OCR 등이 가능하다.

## 벤치마크/성능

### Claude 3.5 Sonnet 주요 벤치마크

| 벤치마크 | Claude 3.5 Sonnet | GPT-4o | Claude 3 Opus |
|----------|------------------|--------|---------------|
| **MMLU** (5-shot) | 88.7% | 87.2% | 86.8% |
| **HumanEval** | 92.0% | 90.2% | 84.9% |
| **GSM8K** | 96.4% | 95.8% | 95.0% |
| **GPQA** | 67.2% | 53.6% | 50.4% |
| **MATH** | 71.1% | 76.6% | 60.1% |

Claude 3.5 Sonnet은 코딩(HumanEval 92.0%)과 일반 지식(MMLU 88.7%)에서 GPT-4o를 소폭 앞서며, 이전 플래그십인 Claude 3 Opus를 모든 벤치마크에서 능가하면서도 **2배 빠른 추론 속도**를 유지한다.

## 관련 모델 비교

| 특성 | Claude 3.5 Sonnet | GPT-4o | Gemini 1.5 Pro |
|------|-------------------|--------|----------------|
| **개발사** | Anthropic | OpenAI | Google |
| **아키텍처** | Dense Transformer | 미공개 (Dense 추정) | MoE |
| **컨텍스트** | 200K | 128K | 1M |
| **멀티모달** | 이미지 입력 | 이미지+오디오 | 이미지+비디오+오디오 |
| **정렬 방법** | CAI + RLAIF | RLHF | RLHF |
| **오픈소스** | ❌ | ❌ | ❌ |
| **안전 접근법** | Constitutional AI | 안전 팀 + RLHF | 안전 필터링 |

## 훈련 파이프라인

Claude의 훈련은 크게 3단계로 구성된다:

1. **대규모 사전 학습 (Pretraining):** 웹 크롤링, 코드, 학술 문헌 등 대규모 코퍼스로 기본 언어 능력 학습
2. **SFT (Supervised Fine-Tuning):** 고품질 시연 데이터로 지시 따르기(instruction following) 능력 학습
3. **RLHF + RLAIF:** 인간 피드백과 AI 피드백을 병용한 강화학습으로 안전성과 유용성 최적화

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{RLHF}} + \alpha \cdot \mathcal{L}_{\text{RLAIF}} + \beta \cdot \text{KL}(\pi_{\theta} \| \pi_{\text{ref}})$$

여기서 $\pi_{\theta}$는 현재 정책, $\pi_{\text{ref}}$는 참조 정책, $\alpha$와 $\beta$는 가중치 하이퍼파라미터이다.

## 실무 활용

### 1. 코딩 에이전트
Claude 3.5 Sonnet의 Artifacts 기능은 코드 생성과 실행을 하나의 워크플로로 통합하여, 프로토타이핑과 디버깅 효율을 크게 높였다.

### 2. 장문 문서 분석
200K 토큰 컨텍스트를 활용하여 법률 문서, 학술 논문, 대규모 코드베이스를 한 번에 분석할 수 있다.

### 3. API 통합
Anthropic Messages API를 통해 기업 시스템에 통합할 수 있으며, AWS Bedrock, Google Cloud Vertex AI 등 주요 클라우드 플랫폼에서도 제공된다.

### 4. 안전한 AI 배포
Constitutional AI 기반의 정렬 덕분에, 민감한 도메인(의료, 법률, 금융)에서도 비교적 안전하게 배포할 수 있다.

## 한계 및 전망

### 한계
1. **비공개 아키텍처:** 기술 보고서가 없어 학술적 재현이 불가능하다.
2. **독점 모델:** 오픈소스가 아니므로 로컬 배포나 커스터마이징이 제한된다.
3. **수학/추론 약점:** MATH 벤치마크(71.1%)에서 GPT-4o(76.6%)에 뒤처지며, 복잡한 수학 추론에서 상대적 약점을 보인다.
4. **출력 전용 멀티모달:** 이미지 생성은 지원하지 않으며, 입력에서만 멀티모달을 지원한다.

### 전망
Claude 시리즈는 이후 Claude 4(Opus 4), Claude 4.5로 진화하며, 에이전틱(agentic) AI와 안전성 연구의 최전선에서 계속 발전하고 있다. Anthropic의 ASL(AI Safety Level) 프레임워크에 따라 모델의 능력이 증가할수록 더 엄격한 안전 조치가 적용되며, 이는 AI 안전 연구와 실용적 배포 사이의 균형을 추구하는 Anthropic의 철학을 반영한다. Constitutional AI의 진화, 더 긴 컨텍스트 윈도우, 그리고 에이전트 워크플로 지원이 Claude 시리즈의 핵심 발전 방향이 될 것이다.

## 관련 문서

- [[claude-4|Claude Opus 4]] — 후속 모델
- [[computer-use|Claude Computer Use]] — 후속 모델
- [[gpt-3|Language Models are Few-Shot Learners (GPT-3)]] — 영감
