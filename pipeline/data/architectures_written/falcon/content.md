# Falcon: 데이터 품질이 모든 것을 결정한다

## 개요

Falcon은 아랍에미리트 기술혁신연구소(Technology Innovation Institute, TII)가 2023년 5월 공개한 오픈소스 대형 언어 모델이다. 7B, 40B, 180B 세 가지 크기로 제공되며, 공개 직후 **Hugging Face OpenLLM 리더보드 1위**를 차지하며 오픈소스 LLM 커뮤니티에 큰 충격을 주었다.

Falcon의 핵심 철학은 명확하다: **"더 큰 모델보다 더 좋은 데이터가 중요하다."** 자체 구축한 RefinedWeb 데이터셋을 통해 CommonCrawl에서 5조 토큰 이상의 고품질 텍스트를 추출하고, 이를 기반으로 적은 학습 토큰으로도 높은 성능을 달성했다.

- **논문**: [The Falcon Series of Open Language Models](https://arxiv.org/abs/2311.16867)
- **모델**: [Hugging Face - tiiuae](https://huggingface.co/tiiuae)
- **라이선스**: Apache 2.0

Falcon-180B의 PaLM 시리즈와의 성능 비교는 아래 그래프에서 확인할 수 있다.

![Falcon-180B와 PaLM 시리즈의 1-shot 성능 비교 - PaLM-2 Large에 근접하는 성능](figures/fig_1.png)
*Figure 1: Falcon-180B와 PaLM 시리즈의 1-shot 성능 비교 - Falcon-180B(보라색)는 PaLM-2 Large에 거의 근접하는 성능을 달성하며, PaLM-2 Medium을 상회한다. (Source: Almazrouei et al., 2023)*

## 아키텍처 상세

### Falcon-180B 주요 사양

| 구성 요소 | Falcon-7B | Falcon-40B | Falcon-180B |
|-----------|----------|-----------|------------|
| 파라미터 수 | 7B | 40B | 180B |
| 레이어 수 | 32 | 60 | 80 |
| Hidden Dim | 4,544 | 8,192 | 14,848 |
| Attention Heads | 71 | 128 | 232 |
| KV Heads | 1 (MQA) | 8 (GQA) | 8 (GQA) |
| Vocab Size | 65,024 | 65,024 | 65,024 |
| Context Length | 2,048 | 2,048 | 2,048 |
| 정규화 | LayerNorm | LayerNorm | LayerNorm |
| 활성화 함수 | GeLU | GeLU | GeLU |
| 위치 인코딩 | **RoPE** | **RoPE** | **RoPE** |

### Multi-Query Attention (MQA)

Falcon-7B는 **MQA(Multi-Query Attention)**를 채택한다. 표준 MHA가 각 헤드마다 독립적인 Key와 Value를 사용하는 반면, MQA는 **모든 헤드가 하나의 Key-Value를 공유**한다:

$$\text{MQA}: \text{Attention}(Q_h, K_{\text{shared}}, V_{\text{shared}})$$

이를 통해:
- **KV 캐시 메모리 대폭 절감**: 헤드 수만큼 감소
- **디코딩 속도 향상**: 메모리 대역폭 병목 완화
- **품질 유지**: 소량의 품질 저하만 발생

Falcon-40B와 180B는 MQA의 변형인 **GQA(Grouped Query Attention)**를 사용하여 품질과 효율의 균형을 맞춘다.

### FlashAttention

Falcon은 **FlashAttention**을 결합하여 어텐션 계산의 메모리 효율을 더욱 최적화한다. IO-aware 알고리즘으로 GPU HBM과 SRAM 간의 데이터 이동을 최소화하여, 표준 어텐션 대비 2-4배 빠른 속도를 달성한다.

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Falcon 모델 로드
tokenizer = AutoTokenizer.from_pretrained('tiiuae/falcon-7b')
model = AutoModelForCausalLM.from_pretrained(
    'tiiuae/falcon-7b',
    torch_dtype=torch.bfloat16,
    device_map='auto'
)

# 텍스트 생성
prompt = "The most important factor in training a large language model is"
inputs = tokenizer(prompt, return_tensors='pt').to(model.device)

outputs = model.generate(
    **inputs,
    max_length=200,
    do_sample=True,
    temperature=0.7,
    top_p=0.9
)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 핵심 혁신: RefinedWeb 데이터셋

Falcon의 진정한 혁신은 아키텍처가 아닌 **데이터**에 있다. 아래 그림은 모델 스케일링에서 데이터 스케일링으로의 패러다임 전환을 보여준다.

![사전학습 패러다임 변화 - 모델 크기만 키우던 시대에서 데이터도 함께 스케일링하는 시대로 전환](figures/fig_3.png)
*Figure 2: 사전학습 패러다임의 변화 - Chinchilla(2022) 이전에는 모델 크기만 증가시키고 데이터셋 크기는 약 300B 토큰으로 고정했으나, 이후 모델과 데이터를 함께 스케일링하는 방향으로 전환되었다. (Source: Almazrouei et al., 2023)*

### RefinedWeb
- CommonCrawl을 **엄격하게 필터링·중복 제거**
- 5조 토큰 이상의 고품질 영어 웹 텍스트 확보
- 기존 웹 크롤링 데이터 대비 **훨씬 높은 품질**
- 학습 데이터의 약 **80%**를 구성

### 데이터 품질 우선 전략
Falcon은 "적은 데이터라도 고품질이면 더 좋은 모델이 나온다"는 가설을 실증했다. 이 전략은 이후 Mistral, LLaMA 2 등 다수의 오픈소스 모델에 영향을 미쳤다.

흥미롭게도, 고품질 웹 데이터만으로도 큐레이팅된 데이터와 동등한 성능을 달성할 수 있다.

![웹 데이터 vs 큐레이팅된 데이터 비교 - RefinedWeb 단독으로도 경쟁력 있는 제로샷 성능](figures/fig_4.png)
*Figure 3: 데이터 혼합 비율에 따른 제로샷 성능 - RefinedWeb(웹 데이터) 단독 학습이 대화, 서적, 기술 데이터를 혼합한 것과 동등하거나 더 나은 성능을 보이며, 특정 큐레이팅된 데이터에 대한 과도한 의존은 오히려 성능을 저하시킨다. (Source: Almazrouei et al., 2023)*

RefinedWeb의 Macrodata Refinement 파이프라인은 CommonCrawl의 약 90%를 제거하여 고품질 데이터를 확보한다.

![Macrodata Refinement 파이프라인 - CommonCrawl에서 약 90%의 문서를 필터링하여 고품질 데이터 추출](figures/fig_6.png)
*Figure 4: Macrodata Refinement 파이프라인 단계별 데이터 제거 비율 - URL 필터링, 텍스트 추출, 언어 식별, 반복 제거, 품질 필터링, 중복 제거를 거치며 원본의 약 10%만 최종 학습 데이터로 남는다. (Source: Penedo et al., 2023)*

## 벤치마크/성능

### OpenLLM Leaderboard

| 모델 | 리더보드 점수 | MMLU | HellaSwag | ARC |
|------|-------------|------|----------|-----|
| **Falcon-180B** | **68.74** | 70.4% | 88.3% | 69.8% |
| LLaMA-2-70B | 67.35 | 69.8% | 87.3% | 67.3% |
| LLaMA-65B | 64.23 | 63.4% | 84.2% | 63.5% |

### 상용 모델과의 비교

| 비교 대상 | Falcon-180B 위치 |
|-----------|----------------|
| GPT-4 | 약간 뒤처짐 |
| PaLM-2 Large (Bard) | **동등** (절반 크기) |
| PaLM-2 Medium | **능가** |
| LLaMA 2 70B | **능가** |

Falcon-180B는 PaLM-2 Medium을 여러 벤치마크에서 능가하고, PaLM-2 Large(당시 Bard 모델)에 필적하는 성능을 보여주었다.

## 관련 모델 비교

| 특성 | LLaMA 65B | LLaMA 2 70B | Falcon 180B | GPT-3.5 |
|------|----------|------------|------------|--------|
| 파라미터 | 65B | 70B | **180B** | 비공개 |
| 어텐션 | MHA | GQA | **MQA/GQA** | 비공개 |
| 데이터 | 1.4T 토큰 | 2T 토큰 | **3.5T 토큰** | 비공개 |
| 데이터 품질 | 공개 데이터 | 비공개 | **RefinedWeb** | 비공개 |
| 위치 인코딩 | RoPE | RoPE | **RoPE** | 비공개 |
| 라이선스 | 연구용 | 상업 가능 | **Apache 2.0** | API only |

## 학습 상세

### 데이터셋
- **RefinedWeb** 포함 약 **3.5조 토큰**
- 고품질 웹 텍스트가 학습 데이터의 ~80%
- 나머지: 코드, 학술 논문, 대화 등

### 학습 인프라
- Falcon-40B: **384개 A100 80GB GPU**
- Falcon-180B: 더 대규모 클러스터
- 학습 안정성: **Z-Loss 정규화** 적용

## 실무 활용

### 1. 상업적 활용
Apache 2.0 라이선스로 제약 없는 상업적 사용이 가능하다.

### 2. 기업용 챗봇
Falcon-7B-Instruct는 단일 GPU에서 구동 가능한 경량 챗봇 기반 모델이다.

### 3. 코드 생성
RefinedWeb에 포함된 코드 데이터 덕분에 코드 생성 태스크에서도 우수한 성능을 보인다.

### 4. 데이터 품질 연구
RefinedWeb의 방법론은 자체 데이터 파이프라인 구축의 참고 사례가 된다.

Falcon 시리즈의 스케일별 성능은 다른 모델들과 비교했을 때 일관되게 우수하다.

![Falcon 시리즈의 스케일별 성능 - 모든 규모에서 기존 모델 대비 강력한 성능 향상](figures/fig_14.png)
*Figure 5: Falcon 시리즈의 스케일별 제로샷 성능 - HellaSwag, LAMBADA, Winogrande 등 6개 벤치마크 종합 정확도에서 Falcon(분홍색)이 모든 스케일에서 기존 모델을 상회하며, RefinedWeb만으로 학습한 모델도 GPT-3 시리즈에 준하는 성능을 보인다. (Source: Almazrouei et al., 2023)*

## 한계 및 전망

### 한계
1. **컨텍스트 길이**: 2,048 토큰으로 현대 기준에서 짧다
2. **180B 추론 비용**: 배포에 상당한 GPU 자원이 필요하다
3. **영어 중심**: 다국어 지원이 제한적이다
4. **GeLU 사용**: SwiGLU 대비 성능이 약간 열등할 수 있다

### 전망
Falcon은 **"데이터 품질 > 모델 크기"**라는 패러다임을 실증한 중요한 모델이다. RefinedWeb의 데이터 파이프라인 방법론은 이후 많은 오픈소스 프로젝트에서 참고되었으며, 아랍에미리트라는 비전통적인 AI 연구 주체가 세계 최고 수준의 모델을 공개했다는 점에서도 의미가 크다. Falcon 2 시리즈를 통해 TII는 지속적으로 오픈소스 LLM 생태계에 기여하고 있다.

---

**참고 문헌**
- Almazrouei, E., et al. (2023). "The Falcon Series of Open Language Models." arXiv:2311.16867
- Penedo, G., et al. (2023). "The RefinedWeb Dataset for Falcon LLM."
- Shazeer, N. (2019). "Fast Transformer Decoding: One Write-Head is All You Need." (MQA)

## 관련 문서

- [[gpt-3|Language Models are Few-Shot Learners (GPT-3)]] - 영감
- [[flash-attention|FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness]] - 사용 기법
