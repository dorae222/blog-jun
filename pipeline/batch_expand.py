#!/usr/bin/env python3
"""
Batch expand content.json files for remaining LLM architecture blog posts.
Updates only the 'content' field while preserving all other fields.
Preserves existing ## 관련 문서 sections.
"""
import json
import os
import re

BASE_DIR = "/Users/dorae222/Documents/Obsidian/blog-jun/pipeline/data/architectures_written"

def get_related_docs_section(content):
    match = re.search(r'(## 관련 문서\s*\n.*)', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def update_content(slug, new_content):
    content_path = os.path.join(BASE_DIR, slug, "content.json")
    with open(content_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    existing_content = data.get("content", "")
    existing_related = get_related_docs_section(existing_content)
    new_related = get_related_docs_section(new_content)
    final = new_content.strip()
    if existing_related and not new_related:
        final = final + "\n\n" + existing_related + "\n"
    data["content"] = final
    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    wc = len(final.split())
    print(f"  {slug}: {wc} words")
    return wc

# ===== CONTENT DEFINITIONS =====

CONTENT = {}

CONTENT["jamba-1-6"] = """# Jamba 1.6: SSM-Transformer 하이브리드의 대규모 진화

## 개요

**Jamba 1.6**은 AI21 Labs가 2025년 3월 27일 공개한 하이브리드 SSM-트랜스포머 아키텍처 언어 모델로, 초대형 Jamba의 후속작이다. 398B 전체 파라미터 중 **52B만 활성화**하는 MoE 구조와 Mamba SSM을 결합하여, 256K 토큰의 초장문 컨텍스트를 기존 순수 트랜스포머 대비 훨씬 낮은 메모리 비용으로 처리한다.

Jamba 1.6의 핵심 가치는 **처리량(throughput)**에 있다. 동급 모델 대비 3배 이상의 처리 효율을 달성하며, 특히 기업용 장문 문서 처리와 다중 문서 RAG 시나리오에 최적화되어 있다.

## 아키텍처 상세

### SSM-Attention 인터리브드 설계

| 구성 요소 | 사양 |
|-----------|------|
| **전체 파라미터** | 398B |
| **활성 파라미터** | 52B |
| **컨텍스트** | 256K |
| **어텐션** | Hybrid: Attention + Mamba SSM |
| **정규화** | RMSNorm |
| **활성화** | SwiGLU |
| **어휘** | 65,536 |

Jamba 1.6의 핵심은 Mamba SSM 레이어와 어텐션 레이어의 **인터리브드(interleaved)** 설계이다. 트랜스포머의 어텐션 레이어는 정확한 전역 컨텍스트 포착에 강점이 있고, Mamba SSM 레이어는 $O(1)$ 메모리로 장문 시퀀스를 효율적으로 처리한다.

### Mamba SSM의 메모리 효율

Mamba의 상태 공간 모델은 시퀀스를 재귀적으로 처리하며, KV 캐시 대신 **고정 크기 상태 벡터**만 유지한다:

$$h_t = \\bar{A} h_{t-1} + \\bar{B} x_t$$

이 특성으로 인해 시퀀스 길이가 256K로 늘어나도 Mamba 레이어의 메모리 사용량은 거의 일정하다. 반면 순수 Attention 모델은 KV 캐시가 시퀀스 길이에 비례하여 증가한다.

### Jamba → Jamba 1.6 진화

| 특성 | Jamba | Jamba 1.6 |
|------|-------|-----------|
| **전체 파라미터** | 52B | **398B** |
| **활성 파라미터** | 12B | **52B** |
| **활성화** | SiLU | **SwiGLU** |
| **규모 확장** | 7.6x | - |

## 핵심 혁신

### 1. 대규모 하이브리드 SSM-MoE

398B 파라미터 규모에서 SSM과 MoE를 동시에 성공적으로 운용한 것은, 두 기법의 대규모 결합이 실용적으로 가능함을 보여준다.

### 2. KV 캐시 최소화

Mamba 레이어가 모델의 대부분을 차지하므로, 256K 컨텍스트에서도 KV 캐시 메모리 사용이 최소화된다. 이는 동시 사용자가 많은 서빙 환경에서 큰 장점이다.

### 3. 기업용 장문 처리 특화

법률 문서, 기업 보고서, 코드베이스 전체 분석 등 장문 컨텍스트가 필수적인 기업 환경에 최적화되어 있다.

## 벤치마크/성능

| 벤치마크 | Jamba 1.6 | Llama-3-70B | Mixtral 8x22B |
|---------|----------|------------|--------------|
| **처리량** | **3x+** | 1x | ~1.5x |
| **256K 처리** | 가능 | 제한적 | 제한적 |
| **KV 캐시** | **최소** | 큼 | 중간 |

## 관련 모델 비교

| 특성 | Jamba | Jamba 1.6 | Mixtral | Llama-3 |
|------|-------|-----------|---------|---------|
| **SSM 레이어** | 있음 | **있음** | 없음 | 없음 |
| **MoE** | 16/2 | **있음** | 8/2 | 없음 |
| **파라미터 (전체/활성)** | 52B/12B | **398B/52B** | 176B/39B | 405B/405B |
| **장문 효율** | 높음 | **최고** | 중간 | 낮음 |

## 학습 상세

- **데이터**: 대규모 다국어 데이터 + 코드 + 명령 수행 데이터 (구체적 토큰 수 미공개)
- **특화 훈련**: 장문 컨텍스트 연속성을 위한 특화 훈련 기법 적용
- **라이선스**: Jamba Open Model License (연구/상업용 제한)

## 실무 활용

### 1. 기업 장문 문서 분석
256K 컨텍스트로 법률 계약서, 규정집, 재무 보고서 전문을 처리할 수 있다.

### 2. 다중 문서 RAG
여러 문서를 한 번에 컨텍스트에 넣어 크로스-도큐먼트 질의응답이 가능하다.

### 3. 고처리량 API 서비스
동급 대비 3배의 처리량으로 대규모 동시 요청 환경에 적합하다.

## 한계 및 전망

### 한계

1. **Mamba 생태계 미성숙**: SSM 레이어의 하드웨어 최적화가 Attention 대비 부족하다.
2. **데이터 미공개**: 학습 데이터의 구체적 구성이 비공개이다.
3. **라이선스 제한**: 완전한 Apache 2.0이 아닌 제한적 라이선스이다.

### 전망

Jamba 1.6은 SSM-Transformer 하이브리드 아키텍처의 대규모 확장 가능성을 입증했다. Qwen3.5의 DeltaNet 하이브리드와 함께, 순수 Transformer를 넘어서는 아키텍처 혁신이 본격화되고 있음을 보여준다.

---

**참고**: [Jamba 1.6 Blog](https://www.ai21.com/blog/jamba-1-6)"""

CONTENT["kimi-k2"] = """# Kimi K2: MuonClip 옵티마이저와 에이전틱 AI의 만남

## 개요

**Kimi K2**는 Moonshot AI가 2025년 7월 11일 공개한 1조(1T) 파라미터 규모의 희소 MoE 언어 모델이다. 토큰당 **32B만 활성화**하는 효율적 구조로, 에이전틱 태스크와 코딩 분야에서 DeepSeek-V3, GPT-4.1, Claude Sonnet 4를 능가하는 성능을 기록했다. **Apache 2.0 라이선스**로 오픈소스 공개되었다.

DeepSeek-V3의 MLA(Multi-Head Latent Attention) 아키텍처에서 영감을 받아 설계되었으며, **MuonClip 옵티마이저**라는 독자적 훈련 혁신을 도입하여 대규모 MoE 모델의 학습 안정성을 크게 향상시켰다.

**참고 논문**: [Kimi K2 Technical Report](https://arxiv.org/abs/2507.20534)

## 아키텍처 상세

### MLA (Multi-Head Latent Attention)

MLA는 DeepSeek-V2에서 창안된 어텐션 메커니즘으로, KV 캐시를 저차원 잠재 벡터로 압축한다:

$$c^{KV}_t = W^{DKV} h_t \\in \\mathbb{R}^{d_c}, \\quad d_c \\ll n_h \\cdot d_h$$

이를 통해 KV 캐시 비용을 $O(n_h \\cdot d_h)$에서 $O(d_c)$로 대폭 절감하여, 긴 컨텍스트에서 메모리 병목을 해소한다.

### 모델 사양

| 구성 요소 | 사양 |
|-----------|------|
| **전체 파라미터** | 1T |
| **활성 파라미터** | 32B |
| **컨텍스트** | 128K |
| **어텐션** | MLA |
| **정규화** | RMSNorm |
| **활성화** | SwiGLU |
| **위치 인코딩** | RoPE |

### MuonClip 옵티마이저

Kimi K2의 핵심 훈련 혁신이다. 기존 AdamW 대비 QK 레이어의 훈련 안정성을 극적으로 향상시켰다:

1. **Muon 업데이트**: Shampoo 계열의 2차 최적화 기법을 경량화
2. **Gradient Clipping**: 큰 그래디언트를 클리핑하여 훈련 불안정 방지
3. **QK 레이어 특화**: 어텐션의 Query-Key 레이어에 선택적으로 적용

MuonClip은 기존 AdamW 대비 동일 스텝 수에서 더 낮은 손실을 달성하며, 특히 MoE 모델의 대규모 학습에서 효과가 크다.

### 보조 손실 없는 전문가 부하 균형

DeepSeek-V3에서 도입된 편향 항 동적 조정 방식을 채택하여, 별도의 auxiliary loss 없이도 전문가 간 부하를 균형 있게 유지한다.

## 핵심 혁신

### 1. 에이전틱 AI 최적화

도구 사용(tool use), 멀티스텝 추론, 코드 생성 벤치마크에서 오픈소스 최고 성능을 달성했다. 함수 호출의 정확성과 장기 에이전트 작업의 목표 유지 능력이 특히 뛰어나다.

### 2. MuonClip의 훈련 안정성

대규모 MoE 모델 학습에서 흔히 발생하는 불안정 문제를 MuonClip으로 해결하여, 15T 토큰 이상의 대규모 학습을 안정적으로 완주했다.

### 3. 오픈소스 1T 모델

Apache 2.0 라이선스로 1T 파라미터 모델을 공개한 것은 오픈소스 AI 생태계에 대한 중요한 기여이다.

## 벤치마크/성능

| 벤치마크 | Kimi K2 | DeepSeek-V3 | GPT-4.1 | Claude Sonnet 4 |
|---------|---------|------------|---------|----------------|
| **에이전틱 태스크** | **최고** | 높음 | 높음 | 높음 |
| **코딩** | **최고 (오픈소스)** | 높음 | 최고 (전체) | 높음 |
| **도구 사용** | **최고** | 높음 | 높음 | 높음 |

## 관련 모델 비교

| 특성 | DeepSeek-V3 | Kimi K2 | LLaMA-3 405B |
|------|------------|---------|-------------|
| **전체/활성** | 671B/37B | **1T/32B** | 405B/405B |
| **어텐션** | MLA | **MLA** | GQA |
| **옵티마이저** | AdamW | **MuonClip** | AdamW |
| **에이전틱** | 양호 | **최고** | 양호 |
| **오픈소스** | 예 | **예** | 예 |

## 학습 상세

- **데이터**: 15T 토큰 이상의 다국어·코드·수학 데이터
- **옵티마이저**: MuonClip (QK 레이어) + AdamW (나머지)
- **정렬**: 에이전틱 SFT + RL 기반 정렬
- **특화 데이터**: 코드·수학·에이전트 데이터 비율 강화
- **라이선스**: Apache 2.0 (가중치: Modified Apache 2.0)

## 실무 활용

### 1. AI 에이전트 엔진
도구 호출과 멀티스텝 추론에 최적화되어 복잡한 워크플로를 자동화하는 에이전트의 핵심 엔진으로 적합하다.

### 2. 코딩 어시스턴트
오픈소스 코딩 모델 중 최고 성능으로, 자체 배포 코딩 도구에 활용할 수 있다.

### 3. 오픈소스 파인튜닝
Apache 2.0 라이선스로 자유로운 도메인 특화 파인튜닝이 가능하다.

## 한계 및 전망

### 한계

1. **배포 인프라**: 1T 모델은 다수의 GPU가 필요하여 소규모 배포가 어렵다.
2. **MuonClip 재현**: 옵티마이저의 세부 구현이 완전히 공개되지 않았다.
3. **데이터 미공개**: 학습 데이터의 구체적 구성이 비공개이다.

### 전망

Kimi K2는 에이전틱 AI에 특화된 오픈소스 대형 모델로, MuonClip 옵티마이저는 향후 대규모 MoE 훈련의 새로운 표준이 될 수 있다. 후속 모델 Kimi K2.5에서는 추론과 에이전트 능력이 더욱 강화될 것으로 예상된다.

---

**참고 논문**: [Kimi K2](https://arxiv.org/abs/2507.20534)"""

CONTENT["llama"] = """# LLaMA: 오픈소스 LLM 혁명의 기폭제

## 개요

**LLaMA**(Large Language Model Meta AI)는 Meta AI가 2023년 2월 연구자 대상으로 공개한 오픈소스 LLM 시리즈로, **'공개 데이터만으로도 강력한 모델을 만들 수 있다'**는 명제를 입증했다. Chinchilla 스케일링 법칙을 따라 작은 파라미터로 더 많은 토큰을 학습하는 전략을 취해, 65B LLaMA가 GPT-3(175B)에 필적하고 **13B 모델이 GPT-3를 여러 벤치마크에서 능가**했다.

가중치 공개로 Alpaca, Vicuna, WizardLM 등 수백 개의 파생 모델이 탄생하며 오픈소스 LLM 생태계 폭발의 기폭제가 되었다. 이후 거의 모든 오픈 LLM(LLaMA 2, Mistral, Yi, Qwen 등)이 LLaMA 아키텍처를 기반으로 삼는다.

**참고 논문**: [LLaMA: Open and Efficient Foundation Language Models](https://arxiv.org/abs/2302.13971) (Touvron et al., 2023)

## 아키텍처 상세

### GPT 대비 3대 아키텍처 개선

LLaMA는 GPT-2/3의 Transformer Decoder 구조에서 3가지 핵심 개선을 적용했다:

#### 1. RMSNorm (Pre-Norm)

$$\\text{RMSNorm}(x) = \\frac{x}{\\sqrt{\\frac{1}{n} \\sum_{i=1}^{n} x_i^2}} \\cdot \\gamma$$

LayerNorm에서 평균 계산을 생략한 RMSNorm을 어텐션 **전에** 적용한다. 이는 학습 안정성을 높이면서 연산량을 줄인다.

#### 2. SwiGLU 활성화

$$\\text{SwiGLU}(x) = \\text{SiLU}(xW_1) \\otimes (xW_2)$$

GELU/ReLU 대비 동일 파라미터 수에서 더 나은 성능을 제공하는 게이팅 활성화 함수이다. FFN 차원이 $\\frac{2}{3} \\times 4d$로 조정되어 파라미터 수를 유지한다.

#### 3. RoPE (Rotary Position Embedding)

$$f(x_m, m) = x_m e^{im\\theta}$$

어텐션 내 상대적 위치를 회전 행렬로 인코딩하여, 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽이 가능하다.

### 모델 사양

| 모델 | 파라미터 | 레이어 | 히든 | 헤드 |
|------|---------|--------|------|------|
| LLaMA-7B | 7B | 32 | 4,096 | 32 |
| LLaMA-13B | 13B | 40 | 5,120 | 40 |
| LLaMA-33B | 33B | 60 | 6,656 | 52 |
| LLaMA-65B | 65B | 80 | 8,192 | 64 |

**토크나이저**: BPE SentencePiece (32K vocab)

## 핵심 혁신

### 1. 공개 데이터만으로 강력한 성능

모든 학습 데이터가 공개 출처이다: CommonCrawl(67%), C4(15%), GitHub(4.5%), Wikipedia(4.5%), Books(4.5%), ArXiv(2.5%), StackExchange(2%). 총 1.4T 토큰.

### 2. Chinchilla 스케일링 법칙 적용

파라미터를 줄이고 데이터를 늘리는 전략으로 GPT-3보다 훨씬 적은 파라미터로 동등한 성능을 달성했다.

### 3. 오픈소스 생태계 폭발

LLaMA의 가중치 공개(초기 유출 후 공식 공개)는 오픈소스 LLM 생태계의 폭발적 성장을 촉발했다:
- **Alpaca** (Stanford): 52K 인스트럭션으로 파인튜닝
- **Vicuna** (LMSYS): ShareGPT 데이터로 파인튜닝
- **WizardLM**: Evol-Instruct로 복잡한 인스트럭션 생성

## 벤치마크/성능

| 벤치마크 | GPT-3 (175B) | LLaMA-13B | LLaMA-65B |
|---------|-------------|----------|----------|
| **MMLU** | 43.9% | **46.9%** | **63.4%** |
| **HumanEval** | - | 15.8% | **23.7%** |
| **HellaSwag** | 78.9% | 76.2% | **84.2%** |
| **NQ (5-shot)** | - | 25.4% | **33.0%** |
| **ARC-C** | - | 47.6% | **56.0%** |

LLaMA-13B는 MMLU에서 GPT-3를 3%p 능가하며, 이는 1/13 파라미터로 달성한 것이다.

## 관련 모델 비교

| 특성 | GPT-3 | Chinchilla | LLaMA | Mistral 7B |
|------|-------|-----------|-------|-----------|
| **파라미터** | 175B | 70B | 65B | 7.3B |
| **학습 토큰** | 300B | 1.4T | **1.4T** | 미공개 |
| **컨텍스트** | 2,048 | 2,048 | 2,048 | 8,192 |
| **오픈소스** | 아니오 | 아니오 | **예** | **예** |
| **아키텍처 영향** | GPT 계열 | - | **LLaMA 계열** | LLaMA 계열 |

## 학습 상세

- **데이터**: CommonCrawl(67%) + C4(15%) + GitHub(4.5%) + Wikipedia(4.5%) + Books(4.5%) + ArXiv(2.5%) + StackExchange(2%), 총 1.4T 토큰
- **옵티마이저**: AdamW, $\\beta$=(0.9, 0.95), lr cosine decay (최고 3e-4)
- **배치**: 4M 토큰
- **하드웨어**: 2,048개 A100 80GB (65B 모델: 약 21일)
- **Flash Attention**: 적용하여 학습 효율 향상

## 실무 활용

### 1. 파인튜닝 베이스 모델

```python
from transformers import LlamaForCausalLM, LlamaTokenizer

model = LlamaForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
tokenizer = LlamaTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
# LoRA, QLoRA 등으로 효율적 파인튜닝 가능
```

### 2. 아키텍처 표준
RMSNorm + SwiGLU + RoPE 조합이 현대 LLM의 사실상 표준이 되었다.

### 3. 양자화 및 경량 추론
GPTQ, GGML 등으로 양자화하여 소비자 하드웨어에서도 실행 가능하다.

## 한계 및 전망

### 한계

1. **짧은 컨텍스트**: 2,048 토큰으로 장문 처리에 제한이 있다.
2. **GQA 미적용**: MHA를 사용하여 추론 시 KV 캐시 비용이 높다.
3. **초기 라이선스 혼란**: 연구 전용으로 시작하여 상업적 활용에 제약이 있었다.

### 전망

LLaMA는 오픈소스 LLM의 '리눅스 순간'을 만든 모델이다. LLaMA 2(상업 라이선스), LLaMA 3(128K 컨텍스트, GQA), LLaMA 4(MoE)로 이어지는 진화는 Meta의 오픈소스 전략의 핵심이며, 전체 AI 생태계의 방향을 바꾸었다.

---

**참고 논문**: [LLaMA: Open and Efficient Foundation Language Models](https://arxiv.org/abs/2302.13971) (Touvron et al., 2023)"""

CONTENT["llama-2"] = """# LLaMA 2: 오픈소스 Chat 모델의 기준을 세운 모델

## 개요

**LLaMA 2**는 Meta AI와 Microsoft가 2023년 7월 18일 연구 및 **상업적 이용이 모두 가능한 라이선스**로 공개한 LLaMA의 후속 모델이다. 단순한 성능 개선을 넘어, 오픈소스 커뮤니티가 전체 RLHF 파이프라인의 결과물을 직접 활용할 수 있게 한 **LLaMA-2-Chat**을 함께 제공했다.

컨텍스트 길이를 2배(2,048→4,096) 확장하고, 대형 모델(34B/70B)에 GQA를 도입해 추론 효율을 대폭 개선했다. 또한 **Ghost Attention(GAtt)** 기법으로 멀티턴 대화에서 초기 시스템 프롬프트 지시를 일관되게 유지하는 문제를 해결했다.

**참고 논문**: [Llama 2: Open Foundation and Fine-Tuned Chat Models](https://arxiv.org/abs/2307.09288) (Touvron et al., 2023)

## 아키텍처 상세

### LLaMA 대비 3대 변화

#### 1. 컨텍스트 확장 (2K → 4K)

학습 데이터를 1.4T에서 **2T 토큰**으로 40% 확대하면서, 컨텍스트 길이를 4,096으로 확장했다.

#### 2. GQA (Grouped Query Attention)

34B와 70B 모델에 GQA를 도입했다:

$$\\text{GQA}: Q \\in \\mathbb{R}^{n_h \\times d_h}, \\quad K, V \\in \\mathbb{R}^{n_g \\times d_h}$$

70B 기준: Q 64헤드, KV 8헤드 → KV 캐시 **8배 감소**, 추론 처리량 크게 향상.

#### 3. Ghost Attention (GAtt)

멀티턴 대화에서 시스템 프롬프트를 일관되게 유지하기 위한 기법이다. SFT 데이터 구성 시 시스템 메시지를 **모든 대화 턴에 가상으로 삽입**하여, 모델이 장기 대화에서도 초기 지시를 잊지 않도록 한다.

### 모델 사양

| 모델 | 파라미터 | 레이어 | 히든 | 어텐션 |
|------|---------|--------|------|--------|
| 7B | 7B | 32 | 4,096 | MHA (32 헤드) |
| 13B | 13B | 40 | 5,120 | MHA (40 헤드) |
| 34B | 34B | 48 | 8,192 | **GQA** (48Q/6KV) |
| 70B | 70B | 80 | 8,192 | **GQA** (64Q/8KV) |

## 핵심 혁신

### 1. 상업적 오픈소스 Chat 모델

LLaMA-2-Chat은 RLHF(Rejection Sampling + PPO)가 적용된 완성된 Chat 모델을 상업 라이선스로 제공한 최초의 대규모 오픈소스 모델이다.

### 2. Rejection Sampling + PPO

InstructGPT의 PPO만 사용하는 방식에서 한 단계 진화하여, 여러 응답을 생성한 후 보상 모델로 최상위 응답을 선택하는 **Rejection Sampling**을 PPO 전에 적용했다.

### 3. Safety RLHF

안전성을 별도 축으로 최적화하여, 유용성과 안전성을 동시에 달성하는 멀티-목표 정렬을 구현했다.

## 벤치마크/성능

| 벤치마크 | LLaMA-2-7B | LLaMA-2-70B | LLaMA-1-65B |
|---------|-----------|------------|------------|
| **MMLU** | 45.3% | **68.9%** | 63.4% |
| **GSM8K** | 14.6% | **56.8%** | - |
| **HumanEval** | 12.8% | **29.9%** | 23.7% |
| **MT-Bench (Chat)** | 6.27 | **6.86** | - |

## 관련 모델 비교

| 특성 | LLaMA | LLaMA 2 | ChatGPT | Mistral 7B |
|------|-------|---------|---------|-----------|
| **파라미터** | 65B | 70B | 미공개 | 7.3B |
| **컨텍스트** | 2,048 | **4,096** | 4,096 | **8,192** |
| **GQA** | 없음 | **있음** (34B/70B) | - | **있음** |
| **Chat 모델** | 없음 | **있음** | 있음 | Instruct |
| **상업 라이선스** | 없음 | **있음** | API 전용 | Apache 2.0 |

## 학습 상세

- **사전 학습**: 2T 토큰 (LLaMA 대비 40% 증가, 공개 데이터)
- **Chat SFT**: 27,540개 어노테이션 (Meta 내부 품질 선별)
- **RLHF**: Rejection Sampling + PPO
- **Reward Model**: 70B 기반 별도 학습
- **하드웨어**: A100 80GB 2,000개
- **배치**: 4M 토큰

## 실무 활용

### 1. 상업용 Chat 서비스
상업 라이선스로 고객 서비스 챗봇, 내부 지식 어시스턴트 등을 구축할 수 있다.

### 2. RLHF 연구 베이스라인
Chat 모델과 기반 모델을 모두 공개하여, RLHF 연구의 표준 베이스라인으로 활용된다.

### 3. 파인튜닝 출발점
LoRA/QLoRA를 활용한 도메인 특화 파인튜닝의 출발점으로 널리 사용된다.

## 한계 및 전망

### 한계

1. **컨텍스트 제한**: 4,096은 현대 기준으로 짧다.
2. **소형 모델의 GQA 미적용**: 7B/13B에는 GQA가 적용되지 않았다.
3. **RLHF 파이프라인 미공개**: Chat 모델의 가중치는 공개되었으나 RLHF 학습 코드는 비공개이다.

### 전망

LLaMA 2는 오픈소스 Chat 모델의 기준을 세웠으며, LLaMA 3에서 128K 컨텍스트와 15T 토큰으로 대폭 확장되었다. GQA와 Ghost Attention은 이후 모델들의 표준 기법이 되었다.

---

**참고 논문**: [Llama 2: Open Foundation and Fine-Tuned Chat Models](https://arxiv.org/abs/2307.09288) (Touvron et al., 2023)"""

CONTENT["mistral-7b"] = """# Mistral 7B: '작지만 강한' 효율적 LLM의 선언

## 개요

**Mistral 7B**는 Mistral AI가 2023년 10월 10일 Apache 2.0 라이선스로 공개한 7.3B 파라미터 모델로, '7B급에서 이렇게 강력할 수 있다'는 것을 업계에 충격적으로 보여준 모델이다. **GQA와 Sliding Window Attention(SWA)**이라는 두 가지 효율화 기법을 결합해 추론 속도와 긴 시퀀스 처리 모두를 해결했다.

발표 직후 **Llama-2-13B를 모든 벤치마크에서 능가**하고 Llama-2-34B에도 근접하는 성능을 보여, '작지만 강한' 효율적 LLM 시대를 열었다. 이후 Mixtral의 기반이 되었고, 수십 개의 파인튜닝 파생 모델이 탄생했다.

**참고 논문**: [Mistral 7B](https://arxiv.org/abs/2310.06825) (Jiang et al., 2023)

## 아키텍처 상세

### 모델 사양

| 구성 요소 | 사양 |
|-----------|------|
| **파라미터** | 7.3B |
| **레이어** | 32 |
| **히든 차원** | 4,096 |
| **Q 헤드** | 32 |
| **KV 헤드** | 8 (GQA) |
| **컨텍스트** | 8,192 (SWA로 32K+ 가능) |
| **FFN 차원** | 14,336 |
| **어휘** | 32,000 |

### GQA (Grouped Query Attention)

Q 헤드 32개, KV 헤드 8개로 KV 캐시를 **4배 절감**한다:

$$\\text{GQA}: Q \\in \\mathbb{R}^{32 \\times 128}, \\quad K, V \\in \\mathbb{R}^{8 \\times 128}$$

동일 품질을 유지하면서 추론 처리량이 크게 향상된다.

### Sliding Window Attention (SWA)

Mistral 7B의 가장 독특한 혁신이다. 각 레이어에서 현재 위치 기준 **W=4,096 토큰** 윈도우 내에서만 어텐션을 수행한다:

$$\\text{Attention}(q_i) = \\text{softmax}\\left(\\frac{q_i K_{[i-W, i]}^T}{\\sqrt{d}}\\right) V_{[i-W, i]}$$

이를 통해 각 레이어의 복잡도가 $O(W \\cdot n)$이 되며, 여러 레이어를 거치면서 **수용 영역(receptive field)이 확장**된다:

$$\\text{최대 수용 영역} = W \\times L = 4,096 \\times 32 = 131,072$$

이론적으로 32개 레이어를 통해 약 131K 토큰의 간접적 문맥 접근이 가능하다.

### Rolling Buffer KV 캐시

SWA와 결합하여 KV 캐시 크기를 윈도우 크기 W로 **상수화**한다:

```python
# Rolling Buffer KV 캐시
cache_position = position % window_size  # 순환 버퍼
kv_cache[cache_position] = new_kv
```

시퀀스 길이에 관계없이 KV 캐시가 일정하므로, 긴 시퀀스에서도 메모리 사용이 안정적이다.

## 핵심 혁신

### 1. 7B급 최강 성능

Llama-2-7B 대비: MMLU +7%p, HumanEval +14%p, GSM8K +27%p. 13B 모델을 능가하는 성능을 7B로 달성했다.

### 2. SWA의 실용적 장문 처리

순수 어텐션의 $O(n^2)$ 메모리를 $O(W \\cdot n)$으로 줄이면서, 다층 레이어의 수용 영역 확장으로 장거리 의존성도 간접적으로 포착한다.

### 3. Apache 2.0 완전 오픈소스

LLaMA의 제한적 라이선스와 달리, 상업적 활용을 포함한 완전한 Apache 2.0 라이선스로 공개되어 생태계 확장에 기여했다.

## 벤치마크/성능

| 벤치마크 | Mistral 7B | Llama-2-7B | Llama-2-13B |
|---------|-----------|-----------|------------|
| **MMLU** | **62.5%** | 45.3% | 54.8% |
| **HumanEval** | **30.5%** | 12.8% | 18.3% |
| **GSM8K** | **52.2%** | 14.6% | 28.7% |
| **HellaSwag** | **83.3%** | 78.6% | 80.7% |
| **ARC-C** | **58.8%** | 53.1% | 56.8% |

## 관련 모델 비교

| 특성 | LLaMA 7B | Mistral 7B | Phi-2 (2.7B) | LLaMA-2 13B |
|------|---------|-----------|-------------|------------|
| **어텐션** | MHA | **GQA+SWA** | MHA | MHA |
| **컨텍스트** | 2,048 | **8,192+** | 2,048 | 4,096 |
| **MMLU** | 35.1% | **62.5%** | 56.7% | 54.8% |
| **라이선스** | 연구용 | **Apache 2.0** | MIT | 상업 가능 |

## 학습 상세

- **데이터**: 미공개 (고품질 필터링된 웹 데이터 추정)
- **SWA 구현**: xFormers 라이브러리 활용
- **Instruct 버전**: 공개 인스트럭션 데이터셋으로 SFT (RLHF 미적용)
- **하이퍼파라미터**: 미공개

## 실무 활용

### 1. 효율적 추론 서버
GQA + SWA로 동급 대비 빠른 추론이 가능하며, vLLM 등에서 최적화 지원이 풍부하다.

### 2. 파인튜닝 기반 모델
OpenHermes, Dolphin, NeuralChat 등 수십 개의 파인튜닝 모델의 기반이 되었다.

### 3. 엣지 배포
7B 파라미터로 소비자 GPU(4-bit 양자화 시 ~4GB)에서도 실행 가능하다.

## 한계 및 전망

### 한계

1. **학습 데이터 미공개**: 데이터 구성과 양이 공개되지 않아 재현이 어렵다.
2. **SWA 한계**: 윈도우 밖의 정확한 정보 검색이 필요한 태스크에서 약점이 있다.
3. **Instruct 버전 제한**: RLHF 없이 SFT만 적용되어 Chat 품질이 제한적이다.

### 전망

Mistral 7B는 Mixtral 8x7B(MoE), Mistral Large 등으로 이어지는 Mistral AI의 기반이 되었다. SWA 기법은 이후 여러 모델에서 참조되었으며, '작지만 강한 모델'이라는 방향성은 Phi, Gemma 등 소형 모델 연구의 촉매가 되었다.

---

**참고 논문**: [Mistral 7B](https://arxiv.org/abs/2310.06825) (Jiang et al., 2023)"""

CONTENT["t5"] = """# T5: 텍스트-투-텍스트 통합 프레임워크의 정립

## 개요

**T5**(Text-to-Text Transfer Transformer)는 2019년 10월 Google Research가 발표한 인코더-디코더 모델로, **모든 NLP 태스크를 텍스트 입력 → 텍스트 출력**으로 통일하는 '텍스트-투-텍스트' 프레임워크를 제안하여 전이 학습 패러다임을 재정립했다. 분류, 요약, 번역, 질의응답, 추론 등 이질적인 태스크를 **단일 모델과 동일한 손실 함수**로 학습할 수 있다는 점에서 진정한 범용 언어 모델의 가능성을 입증했다.

750GB에 달하는 **C4(Colossal Clean Crawled Corpus)** 데이터셋을 구축·공개했으며, 11B 모델로 GLUE, SuperGLUE, CNN/DM, SQuAD 등 다수 벤치마크에서 당시 SOTA를 달성했다.

**참고 논문**: [Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer](https://arxiv.org/abs/1910.10683) (Raffel et al., 2019)

## 아키텍처 상세

### 텍스트-투-텍스트 프레임워크

모든 태스크를 접두사(prefix)로 표현하여 통일된 형식으로 처리한다:

- **번역**: `"translate English to German: The house is wonderful."` → `"Das Haus ist wunderbar."`
- **분류**: `"sentiment: This movie was great."` → `"positive"`
- **요약**: `"summarize: Long article text..."` → `"Summary text"`

이 방식으로 멀티태스크 학습이 단순 배치 샘플링 문제가 된다.

### 인코더-디코더 구조

| 구성 요소 | Small | Base | Large | 3B | 11B |
|-----------|-------|------|-------|----|-----|
| **파라미터** | 60M | 220M | 770M | 3B | 11B |
| **레이어 (각)** | 6 | 12 | 24 | 24 | 24 |
| **히든** | 512 | 768 | 1,024 | 1,024 | 1,024 |
| **어텐션 헤드** | 8 | 12 | 16 | 32 | 128 |

### Relative Attention Bias

T5는 절대 위치 임베딩을 제거하고 **상대 위치 편향(Relative Attention Bias)**만 사용한다:

$$A_{ij} = \\frac{Q_i K_j^T}{\\sqrt{d}} + b(i-j)$$

여기서 $b(i-j)$는 상대 위치 $i-j$에 따른 학습 가능한 편향 값이다. 버킷 기반으로 이산화하여 먼 거리의 위치 정보를 효율적으로 처리한다.

### Span Corruption 사전 학습

입력의 15%를 다양한 길이(평균 3토큰)의 **스팬(span)으로 마스킹**하고, 단일 sentinel 토큰으로 대체한다:

```
입력: Thank you [X] me to your party [Y] week
출력: [X] for inviting [Y] last [Z]
```

BERT의 토큰 단위 마스킹보다 효율적이며, 디코더가 연속된 텍스트를 생성하도록 학습된다.

## 핵심 혁신

### 1. 통합 프레임워크

분류, 생성, 변환, 추론 등 모든 NLP 태스크를 하나의 프레임워크로 통합한 것은 이후 GPT-3의 인컨텍스트 러닝과 LLM의 범용 태스크 수행에 직접적 영감을 제공했다.

### 2. C4 데이터셋

Common Crawl에서 중복 제거, 저품질 필터링을 거쳐 구축한 **750GB 규모의 정제된 영어 코퍼스**를 공개했다. 이는 이후 mC4, RefinedWeb 등 대규모 데이터셋 구축의 기준이 되었다.

### 3. 체계적 비교 연구

논문은 아키텍처(인코더-디코더 vs 디코더-only), 사전 학습 목표(MLM vs Span Corruption vs LM), 학습 전략 등을 체계적으로 비교하여 최적 구성을 도출했다.

## 벤치마크/성능

| 벤치마크 | BERT-Large | T5-Base | T5-11B |
|---------|----------|--------|--------|
| **GLUE** | 84.6 | 83.3 | **90.3** |
| **SuperGLUE** | ~69 | 79.3 | **88.9** |
| **SQuAD (EM)** | 80.8 | 82.1 | **86.3** |
| **CNN/DM (R-L)** | - | 38.2 | **43.5** |

## 관련 모델 비교

| 특성 | BERT | GPT-2 | T5 | mT5 |
|------|------|-------|-----|------|
| **아키텍처** | Encoder | Decoder | **Enc-Dec** | Enc-Dec |
| **사전 학습** | MLM+NSP | LM | **Span Corruption** | Span Corruption |
| **다국어** | 제한적 | 영어 | 영어 | **101개 언어** |
| **출력 형식** | 분류 | 생성 | **텍스트 통합** | 텍스트 통합 |
| **데이터셋** | 16GB | 40GB | **750GB (C4)** | 6.4TB (mC4) |

## 학습 상세

- **데이터**: C4 (Colossal Clean Crawled Corpus, 750GB)
- **토크나이저**: SentencePiece unigram LM, 32,100 vocab
- **옵티마이저**: Adafactor (메모리 효율화)
- **배치**: 128 (Small) ~ 2,048 (11B)
- **학습률**: 역제곱근(inverse square root) 스케줄
- **스텝**: 1M
- **하드웨어**: TPU v3, 11B는 1,024 코어

## 실무 활용

### 1. 요약 및 번역

```python
from transformers import T5ForConditionalGeneration, T5Tokenizer

model = T5ForConditionalGeneration.from_pretrained("t5-base")
tokenizer = T5Tokenizer.from_pretrained("t5-base")

input_text = "summarize: Long article about AI research..."
inputs = tokenizer(input_text, return_tensors="pt")
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0]))
```

### 2. 멀티태스크 학습
하나의 모델로 번역, 요약, 분류, QA를 동시에 수행할 수 있다.

### 3. 연구 베이스라인
인코더-디코더 아키텍처 연구의 표준 베이스라인으로 널리 사용된다.

## 한계 및 전망

### 한계

1. **인코더-디코더 비효율**: 디코더-only 모델 대비 대화형 생성에서 비효율적이다.
2. **짧은 컨텍스트**: 512 토큰 입력으로 장문 처리에 한계가 있다.
3. **대규모 확장 한계**: 11B 이후 더 큰 T5 모델은 공개되지 않았다.

### 전망

T5의 텍스트-투-텍스트 철학은 GPT-3, ChatGPT의 "모든 것을 대화로" 접근법의 이론적 선구자이다. mT5, Switch Transformer, Flan-T5 등으로 확장되었으며, 인코더-디코더 구조는 요약, 번역 등 특정 생성 태스크에서 여전히 디코더-only 대비 장점을 가진다.

---

**참고 논문**: [Exploring the Limits of Transfer Learning](https://arxiv.org/abs/1910.10683) (Raffel et al., 2019)"""

CONTENT["switch-transformer"] = """# Switch Transformer: Top-1 라우팅으로 MoE의 실용성을 입증

## 개요

**Switch Transformer**는 2021년 1월 Google Research가 발표한 Sparse Mixture-of-Experts 모델로, 기존 MoE의 복잡한 라우팅을 **'각 토큰당 하나의 전문가만 선택(Top-1 라우팅)'**으로 단순화해 연산 효율과 확장성을 동시에 달성했다. T5 아키텍처의 FFN 레이어를 N개의 전문가 네트워크로 교체하고, 가벼운 라우터가 각 토큰을 단 하나의 전문가에 할당한다.

동일 FLOP 대비 T5 대비 **학습 속도 7배 향상**, 1.6조 파라미터 Switch-C가 T5-XXL(11B) 대비 **4배 빠른 학습 수렴**을 보였다. 조 단위 파라미터 학습의 실용적 가능성을 처음 입증한 MoE 모델이다.

**참고 논문**: [Switch Transformers: Scaling to Trillion Parameter Models](https://arxiv.org/abs/2101.03961) (Fedus et al., 2021)

## 아키텍처 상세

### Top-1 Switch Routing

기존 MoE(Shazeer et al., 2017)는 Top-2 전문가를 선택했지만, Switch Transformer는 **Top-1만 선택**한다:

$$g_i = \\frac{e^{W_r \\cdot x}}{\\sum_j e^{W_r \\cdot x}} \\quad \\rightarrow \\quad \\text{expert} = \\arg\\max_i g_i$$

Top-1 선택의 장점:
- 라우팅 연산량 **절반** 감소
- 구현 단순화
- 통신 비용 감소 (각 토큰이 하나의 전문가 디바이스에만 전송)

### 모델 사양

| 변형 | 전문가 수 | 전체 파라미터 | 활성 파라미터 |
|------|----------|-------------|-------------|
| Switch-Base | 128 | 7B | ~220M |
| Switch-Large | 128 | 26B | ~770M |
| Switch-XXL | 64 | 395B | ~11B |
| **Switch-C** | **2,048** | **1.6T** | ~11B |

### Expert Capacity Buffer

전문가당 처리 가능한 최대 토큰 수를 설정한다:

$$\\text{Expert Capacity} = \\left(\\frac{n}{e}\\right) \\times \\text{capacity\\_factor}$$

여기서 $n$은 배치 내 토큰 수, $e$는 전문가 수이다. capacity_factor $\\geq 1.0$으로 설정하여 약간의 여유를 확보하며, 용량을 초과하는 토큰은 **잔차 연결(residual connection)으로 패스스루**된다.

### 보조 로드 밸런싱 손실

전문가 간 부하를 균등하게 유지하기 위한 보조 손실이다:

$$\\mathcal{L}_{\\text{aux}} = \\alpha \\cdot N \\cdot \\sum_{i=1}^{N} f_i \\cdot P_i$$

여기서 $f_i$는 전문가 $i$에 할당된 토큰 비율, $P_i$는 전문가 $i$에 대한 평균 라우팅 확률이다. $\\alpha$는 보조 손실 가중치(일반적으로 0.01)이다.

## 핵심 혁신

### 1. MoE 단순화

Top-2에서 Top-1으로의 전환은 단순한 변경처럼 보이지만, MoE 시스템의 복잡도를 대폭 줄이면서 동등 이상의 성능을 달성했다.

### 2. 조 단위 파라미터 실용화

1.6T 파라미터 Switch-C를 TPU 클러스터에서 안정적으로 학습한 것은, 트릴리온 스케일 학습의 실용성을 처음 입증한 것이다.

### 3. T5 프레임워크 활용

기존 T5 아키텍처의 FFN만 전문가로 교체하여, 검증된 인코더-디코더 프레임워크 위에서 MoE를 적용했다.

## 벤치마크/성능

| 모델 | 파라미터 | 학습 속도 (vs T5) | SuperGLUE |
|------|---------|-------------------|-----------|
| T5-Base | 220M | 1x | 74.6 |
| Switch-Base | 7B (128 expert) | **7x** | 81.2 |
| T5-XXL | 11B | 1x | 88.9 |
| Switch-XXL | 395B (64 expert) | **4x** | 90.4 |

## 관련 모델 비교

| 특성 | T5 | Switch | GShard | Mixtral |
|------|-----|--------|--------|---------|
| **라우팅** | - | **Top-1** | Top-2 | Top-2 |
| **아키텍처** | Enc-Dec | Enc-Dec | Enc-Dec | **Dec-only** |
| **최대 규모** | 11B | **1.6T** | 600B | 176B |
| **학습 안정성** | 안정 | bf16 필요 | 보통 | 안정 |

## 학습 상세

- **데이터**: C4 (T5와 동일)
- **토크나이저**: SentencePiece 32,100 vocab
- **옵티마이저**: Adafactor
- **배치**: 2,048, 500K 스텝
- **정밀도**: bf16 혼합 정밀도 (학습 안정성 핵심)
- **하드웨어**: 2,048 TPU v3 코어, 각 전문가 별도 코어 배치

## 실무 활용

### 1. 대규모 학습 효율화
동일 FLOP 예산에서 더 큰 모델을 더 빠르게 학습할 수 있어, 연구 기관의 학습 효율을 극대화한다.

### 2. MoE 연구 기반
Top-1 라우팅, 전문가 용량 관리, 부하 균형 등 이후 MoE 연구의 기본 프레임워크를 제공했다.

### 3. 추론 효율화
활성 파라미터가 전체의 일부이므로, 적절한 전문가 병렬화로 추론 비용을 관리할 수 있다.

## 한계 및 전망

### 한계

1. **학습 불안정**: MoE 학습은 Dense 모델보다 불안정하며, bf16 정밀도가 필수적이다.
2. **토큰 드롭**: 전문가 용량 초과 시 토큰이 드롭되어 정보 손실이 발생할 수 있다.
3. **Expert Collapse**: 일부 전문가만 활용되고 나머지가 퇴화하는 현상이 있다.

### 전망

Switch Transformer의 Top-1 라우팅과 부하 균형 전략은 Mixtral, DeepSeek MoE, LLaMA 4 등 이후 MoE 모델들의 기반 기술이 되었다. 특히 DeepSeek-V3의 auxiliary-loss-free 부하 균형은 Switch Transformer의 보조 손실 접근법을 개선한 것이다.

---

**참고 논문**: [Switch Transformers](https://arxiv.org/abs/2101.03961) (Fedus et al., 2021)"""

def main():
    total = 0
    for slug, content in CONTENT.items():
        wc = update_content(slug, content)
        total += 1
    print(f"\nDone: {total} models updated")

if __name__ == "__main__":
    main()
