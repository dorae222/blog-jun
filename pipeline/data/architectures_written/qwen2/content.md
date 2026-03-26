# Qwen2: 중국 오픈소스 LLM의 최전선에 선 다국어 모델

## 개요

Qwen2는 Alibaba Cloud(알리바바 클라우드)가 2024년 6월 6일 공개한 Qwen 시리즈의 2세대 언어 모델이다. 0.5B, 1.5B, 7B, 57B-A14B(MoE), 72B 다섯 가지 크기로 제공되며, 중국 빅테크가 오픈소스 LLM 최전선에 본격적으로 진입했음을 알린 모델이다.

Qwen2의 핵심 경쟁력은 세 가지이다: (1) 7T 토큰 이상의 고품질 다국어 데이터(29개 언어), (2) 151,936개의 대형 어휘로 CJK 언어 토큰화 효율 극대화, (3) YARN 기반 128K 컨텍스트 외삽. Qwen2-7B가 Llama-3-8B를 대부분의 벤치마크에서 능가하며, Qwen2-72B는 MMLU 84.2%를 달성했다.

다음 그림은 Qwen2의 전체 아키텍처를 보여준다.

![Qwen2 아키텍처 다이어그램](figures/architecture.png)
*Figure 1: Qwen2 아키텍처 — GQA 기반 어텐션, SwiGLU FFN, RoPE 위치 인코딩을 결합한 Dense Transformer 구조. 151K 어휘와 128K 컨텍스트를 지원한다. (Source: Alibaba Cloud)*

## 아키텍처 상세

### 기본 구조

| 구성 요소 | Qwen2-7B | Qwen2-72B | Qwen2-57B-A14B |
|---|---|---|---|
| 파라미터 | 7B | 72B | 57B (14B active) |
| Hidden Dimension | 3584 | 8192 | - |
| 레이어 수 | 28 | 80 | - |
| Attention Head (Q) | 28 | 64 | - |
| KV Head | 4 | 8 | - |
| 컨텍스트 길이 | 131,072 | 131,072 | 131,072 |
| 어휘 크기 | 151,936 | 151,936 | 151,936 |
| 위치 인코딩 | RoPE | RoPE | RoPE |
| 정규화 | RMSNorm | RMSNorm | RMSNorm |
| 활성화 함수 | SiLU (SwiGLU) | SiLU (SwiGLU) | SiLU (SwiGLU) |
| Attention 방식 | GQA | GQA | GQA |

### 151K 대형 어휘

Qwen2의 151,936개 어휘는 LLaMA의 32K 대비 약 4.7배이다. 이 대형 어휘의 핵심 효과:

$$\text{토큰 효율} = \frac{\text{원문 문자 수}}{\text{토큰 수}}$$

| 모델 | 어휘 크기 | 한국어 효율 | 중국어 효율 | 일본어 효율 |
|---|---|---|---|---|
| LLaMA-2 | 32K | 1.2x | 1.0x | 1.0x |
| Mistral | 32K | 1.2x | 1.0x | 1.0x |
| Qwen2 | 151K | 2.5x | 3.0x | 2.8x |
| Gemma | 256K | 2.8x | 3.2x | 3.0x |

CJK 문자에 최적화된 토큰이 대량 포함되어, 동일 텍스트에 대해 필요한 토큰 수가 크게 줄어든다.

### Grouped Query Attention (GQA)

Qwen2는 모든 크기에서 GQA를 채택했다. GQA는 MHA와 MQA의 중간 지점으로:

$$\text{GQA}: Q \in \mathbb{R}^{h_q \times d}, K \in \mathbb{R}^{h_{kv} \times d}, V \in \mathbb{R}^{h_{kv} \times d}$$

Qwen2-7B의 경우 $h_q = 28$, $h_{kv} = 4$로, KV 캐시가 MHA 대비 약 1/7로 감소한다.

### YARN 기반 128K 컨텍스트 외삽

YARN(Yet Another RoPE Extension)을 사용하여 기본 학습 컨텍스트 4,096에서 128K까지 위치 인코딩을 외삽한다:

$$\text{YARN}: \theta'_i = \theta_i \cdot s(i)$$

여기서 $s(i)$는 차원별 스케일링 팩터로, 저주파 성분은 덜 수정하고 고주파 성분은 더 많이 수정하여 외삽 품질을 유지한다. Dual Chunk Attention으로 긴 시퀀스에서의 어텐션 안정성도 확보했다.

다음 그림은 Qwen2 시리즈의 YARN 기반 128K 컨텍스트 외삽 성능을 Needle in a Haystack 테스트로 검증한 결과이다.

![Qwen2 Needle in a Haystack 테스트 결과](figures/fig_1.png)
*Figure 1: Qwen2 Instruct 모델의 Needle in a Haystack 테스트 — Qwen2-72B-Instruct는 128K 전체 컨텍스트에서 거의 완벽한 검색 정확도를 달성하며, YARN 기반 컨텍스트 외삽의 효과를 입증한다. (Source: Yang et al., 2024)*

## 핵심 혁신

### 1. 29개 언어 지원의 다국어 능력

영어와 중국어뿐 아니라 한국어, 일본어, 아랍어, 힌디어 등 29개 언어를 지원한다. 151K 어휘 속에 각 언어의 고유한 문자와 토큰이 포함되어 있어, 별도의 다국어 적응 없이도 다양한 언어에서 강력한 성능을 보인다.

### 2. Dense + MoE 듀얼 라인업

Qwen2는 Dense 모델(0.5B~72B)과 MoE 모델(57B-A14B)을 동시에 제공하여, 사용자가 배포 환경에 맞는 최적의 모델을 선택할 수 있다.

### 3. 통합 정렬 파이프라인

Instruct 버전은 SFT(Supervised Fine-Tuning), DPO(Direct Preference Optimization), RLHF를 통합한 3단계 정렬 파이프라인을 거친다.

## 벤치마크/성능

| 벤치마크 | Qwen2-7B | Qwen2-72B | Llama-3-8B | Mistral-7B |
|---|---|---|---|---|
| MMLU | 70.3% | 84.2% | 66.6% | 60.1% |
| HumanEval | 79.9% | 64.6% | 62.2% | 29.3% |
| MATH | 52.9% | 69.0% | 30.0% | 13.1% |
| GSM8K | 79.9% | 89.5% | 79.6% | 52.2% |
| C-Eval | 83.2% | 91.1% | 49.4% | 47.6% |
| MT-Bench | 8.41 | 9.12 | 8.05 | 7.60 |

Qwen2-7B는 MMLU 70.3%, HumanEval 79.9%로 Llama-3-8B를 명확히 능가한다. 72B 모델은 MMLU 84.2%로 오픈소스 최전선 수준이다.

## 관련 모델 비교

### Qwen 시리즈 진화

| 버전 | 출시 | 학습 토큰 | 어휘 | 컨텍스트 | 주요 변화 |
|---|---|---|---|---|---|
| Qwen1 | 2023.08 | 3T | 152K | 8K | 최초 공개 |
| Qwen1.5 | 2024.02 | 3T+ | 152K | 32K | 정렬 개선 |
| Qwen2 | 2024.06 | 7T | 152K | 128K | GQA, YARN, 29언어 |
| Qwen2.5 | 2024.09 | 18T | 152K | 128K | 수학/코드 강화 |
| Qwen3 | 2025.04 | 36T | 152K | 128K | 하이브리드 추론 |

### 동급 경쟁 모델 비교 (7B급)

| 특성 | Qwen2-7B | Llama-3-8B | Gemma-7B | Mistral-7B |
|---|---|---|---|---|
| 어휘 크기 | 152K | 128K | 256K | 32K |
| 컨텍스트 | 128K | 8K | 8K | 32K |
| Attention | GQA | GQA | MQA | GQA+SWA |
| 다국어 | 29언어 | 영어 중심 | 영어 중심 | 유럽어 중심 |
| MMLU | 70.3% | 66.6% | 64.6% | 60.1% |

## 실무 활용

### 배포 가이드

1. **중국어/CJK 서비스**: 151K 어휘로 중국어, 한국어, 일본어 서비스에 최적
2. **장문 처리**: 128K 컨텍스트로 긴 문서, 보고서 분석
3. **코드 생성**: HumanEval 79.9%(7B)로 코딩 어시스턴트 구축
4. **MoE 배포**: 57B-A14B로 대형 모델 성능을 효율적 비용으로 제공

### 프레임워크 지원

Hugging Face Transformers, vLLM, llama.cpp, Ollama 등 주요 프레임워크에서 모두 지원된다.

## 한계 및 전망

### 한계

1. **학습 데이터 비공개**: 7T 토큰의 구성과 비율이 완전히 공개되지 않음
2. **영어 편향**: 29개 언어를 지원하지만 학습 데이터에서 영어/중국어 비중이 압도적
3. **MoE 버전 제한**: 57B-A14B 단일 MoE 모델만 제공 (다양한 크기 부재)
4. **Qwen2.5에 빠르게 대체**: 3개월 만에 후속 버전 Qwen2.5가 등장하여 레거시화

### 전망

Qwen2는 중국 AI 생태계가 오픈소스 LLM 경쟁에서 미국을 추격하는 전환점이 된 모델이다. 7T 토큰 학습, 128K 컨텍스트, 29개 언어 지원이라는 조합은 당시 오픈소스 LLM 중 최고 수준이었다. 이후 Qwen2.5에서 18T 토큰으로 확장되고, Qwen3에서 하이브리드 추론이 추가되며 빠르게 진화하고 있다. Alibaba의 Qwen 시리즈는 중국뿐 아니라 글로벌 오픈소스 LLM 생태계에서 핵심적인 위치를 차지하고 있다.

## 관련 문서

- [[qwen2-5|Qwen2.5 Technical Report]] — 후속 모델
- [[qwen2-vl|Qwen2-VL]] — 후속 모델
- [[llama-2|Llama 2: Open Foundation and Fine-Tuned Chat Models]] — 영감
