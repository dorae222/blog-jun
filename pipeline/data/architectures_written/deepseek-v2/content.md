# DeepSeek-V2: MLA와 DeepSeekMoE로 KV 캐시 93.3%를 절감한 효율 혁명

## 개요

DeepSeek-V2는 DeepSeek AI가 2024년 5월 7일 공개한 236B MoE(Mixture of Experts) 언어 모델이다. 대형 언어 모델의 두 가지 핵심 병목인 **어텐션의 KV 캐시 메모리 비용**과 **MoE의 라우팅 비효율**을 동시에 해결한 아키텍처 혁신 모델로, 후속 모델인 DeepSeek-V3와 R1의 기술적 기반이 되었다.

이 모델은 MLA(Multi-head Latent Attention)로 KV 캐시를 93.3% 절감하고, DeepSeekMoE(공유 전문가 + 세분화된 라우팅 전문가)로 전문성과 공유 지식을 분리하여, **21B 활성 파라미터만으로 GPT-4 수준의 성능**을 달성했다. 이전 DeepSeek 67B 대비 42.5% 낮은 학습 비용이라는 놀라운 효율성으로, 중국 AI 스타트업의 기술 경쟁력을 전 세계에 알렸다.

## 아키텍처 상세

### 기본 구조

| 구성 요소 | 사양 |
|-----------|------|
| **전체 파라미터** | 236B |
| **활성 파라미터** | 21B (토큰당) |
| **레이어 수** | 60 |
| **히든 차원** | 5120 |
| **어텐션 헤드** | 128 |
| **전문가 수** | 160 (라우팅) + 2 (공유) |
| **활성 전문가** | 6 (라우팅) + 2 (공유) |
| **어휘 크기** | 102,400 |
| **컨텍스트 길이** | 128K |
| **위치 인코딩** | Decoupled RoPE |

### MLA (Multi-head Latent Attention)

MLA는 DeepSeek-V2의 가장 핵심적인 아키텍처 혁신으로, 표준 Multi-Head Attention(MHA)의 KV 캐시 문제를 근본적으로 해결한다.

**기존 MHA의 문제:**
표준 MHA에서 KV 캐시의 크기는 $O(n_h \cdot d_h \cdot l)$로, 어텐션 헤드 수 $n_h$, 헤드 차원 $d_h$, 시퀀스 길이 $l$에 비례한다. 128K 같은 장문 컨텍스트에서 이 메모리 비용은 치명적이다.

**MLA의 해결책:**
Key와 Value를 저차원 잠재 벡터(latent vector)로 압축한 뒤 업프로젝션하는 **Low-Rank Key-Value Joint Compression**을 사용한다:

$$c^{KV}_t = W^{DKV} h_t \in \mathbb{R}^{d_c}$$

$$k_t = W^{UK} c^{KV}_t, \quad v_t = W^{UV} c^{KV}_t$$

여기서 $c^{KV} \in \mathbb{R}^{512}$는 압축된 잠재 벡터이고, $d_c \ll n_h \cdot d_h$이다. 캐시에 저장하는 것은 전체 KV가 아닌 압축된 $c^{KV}$이므로, KV 캐시가 **93.3% 절감**된다.

Query도 유사하게 압축된다:
$$c^Q_t = W^{DQ} h_t \in \mathbb{R}^{1536}$$

**Decoupled RoPE:**
MLA에서 위치 인코딩을 적용하면 압축의 이점이 사라지는 문제를 해결하기 위해, 위치 인코딩을 별도의 행렬에 적용하는 **Decoupled RoPE** 기법을 도입했다:

$$k_t^R = \text{RoPE}(W^{KR} h_t)$$

최종 키는 $[k_t; k_t^R]$의 형태로 위치 정보와 콘텐츠 정보를 분리하여 처리한다.

### DeepSeekMoE

DeepSeekMoE는 기존 MoE의 두 가지 한계를 극복한다:

1. **공유 전문가(Shared Experts):** 2개의 전문가가 항상 활성화되어, 모든 토큰에 필요한 공통 지식을 처리한다.
2. **세분화된 전문가(Fine-Grained Experts):** 160개의 라우팅 전문가 중 6개를 선택하며, 각 전문가의 크기를 줄이고 수를 늘려 전문화를 극대화한다.

$$\text{FFN}(h) = \sum_{i=1}^{2} \text{FFN}_{\text{shared}}^i(h) + \sum_{j=1}^{6} g_j \cdot \text{FFN}_{\text{routed}}^{s_j}(h)$$

여기서 $g_j$는 라우팅 게이트 값, $s_j$는 선택된 전문가 인덱스이다.

## 핵심 혁신

### 1. KV 캐시 93.3% 절감
MLA를 통해 128K 토큰 컨텍스트에서도 KV 캐시 메모리가 기존 MHA의 6.7% 수준으로 줄어든다. 이는 장문 추론의 비용을 획기적으로 낮춘다.

### 2. 처리량 5.76배 향상
KV 캐시 절감과 효율적 MoE 구조 덕분에, 최대 생성 처리량이 DeepSeek 67B 대비 **5.76배** 향상되었다.

### 3. 학습 비용 42.5% 절감
동등 성능 달성에 필요한 학습 비용을 DeepSeek 67B 대비 42.5% 줄였다.

## 벤치마크/성능

| 벤치마크 | DeepSeek-V2 | DeepSeek 67B | Mixtral 8x22B | LLaMA-3 70B |
|----------|------------|-------------|--------------|-------------|
| **MMLU** | 78.5% | 71.3% | 77.8% | 79.5% |
| **HumanEval** | 81.1% | 73.8% | 75.0% | 81.7% |
| **GSM8K** | 79.2% | 63.4% | 78.6% | 83.0% |
| **활성 파라미터** | 21B | 67B | 39B | 70B |
| **KV 캐시 (MHA 대비)** | 6.7% | 100% | 12.5% (GQA) | 12.5% (GQA) |

DeepSeek-V2는 21B 활성 파라미터만으로 70B Dense 모델에 근접하는 성능을 달성한다.

## 관련 모델 비교

| 특성 | DeepSeek-V2 | Mixtral 8x22B | LLaMA-3 70B |
|------|------------|--------------|-------------|
| **타입** | Sparse MoE | Sparse MoE | Dense |
| **전체/활성** | 236B/21B | 176B/39B | 70B/70B |
| **어텐션** | MLA | GQA | GQA |
| **KV 캐시 절감** | 93.3% | 87.5% | 87.5% |
| **컨텍스트** | 128K | 65K | 8K |
| **오픈소스** | ✅ | ✅ | ✅ |

## 훈련 상세

- **학습 데이터**: 8.1T 토큰
- **하드웨어**: H800 GPU 클러스터
- **병렬화**: ZeRO-2 + Expert Parallelism + Pipeline Parallelism
- **Chat 버전**: SFT(1.5M 예시) + GRPO(Group Relative Policy Optimization) 강화학습

GRPO는 DeepSeek가 자체 개발한 강화학습 알고리즘으로, PPO 대비 메모리 효율이 높다:

$$\mathcal{L}_{\text{GRPO}} = -\mathbb{E}_{(x,y)\sim\pi_{\text{old}}} \left[ \frac{\pi_\theta(y|x)}{\pi_{\text{old}}(y|x)} \cdot \hat{A}_{\text{group}}(x,y) \right]$$

## 실무 활용

### 1. 고효율 API 서비스
21B 활성 파라미터로 추론 비용이 낮아, 대규모 API 서비스에 적합하다.

### 2. 장문 문서 처리
128K 컨텍스트와 MLA의 KV 캐시 절감으로 장문 처리가 효율적이다.

### 3. 오픈소스 연구 기반
MLA와 DeepSeekMoE의 구현이 공개되어, 후속 연구의 기반이 되었다.

## 한계 및 전망

### 한계
1. **절대 성능**: LLaMA-3 70B에 일부 벤치마크에서 뒤처진다.
2. **MoE 복잡성**: 전문가 병렬화가 필요하여 단일 GPU 배포가 어렵다.
3. **중국어 편향**: 훈련 데이터 구성상 중국어 성능이 상대적으로 높다.

### 전망
DeepSeek-V2의 MLA와 DeepSeekMoE는 후속 모델인 DeepSeek-V3(671B)와 DeepSeek-R1의 핵심 기반이 되었으며, Kimi K2 등 다른 모델에서도 MLA를 채택하는 등 업계 전반에 영향을 미쳤다. KV 캐시 압축과 세분화된 MoE는 대형 언어 모델의 효율화에 있어 필수적인 기술로 자리잡았다.

## 관련 문서

- [[deepseek-v3|DeepSeek-V3 Technical Report]] — 후속 모델
- [[deepseek-vl2|DeepSeek-VL2]] — 후속 모델
- [[mixtral|Mixtral of Experts]] — 영감
