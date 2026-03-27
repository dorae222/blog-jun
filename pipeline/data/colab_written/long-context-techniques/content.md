# Long Context LLM: 100K+ 토큰 처리의 원리와 기법

## 들어가며

2023년까지 대부분의 LLM은 4K~8K 토큰의 컨텍스트 윈도우를 가졌다. 2024년에는 Gemini 1.5(1M+), Claude 3(200K), GPT-4 Turbo(128K)로 급격히 확장되었다. 2025년에는 1M 토큰 이상이 표준이 되어가고 있다.

이 글에서는 컨텍스트 윈도우를 확장하는 **핵심 기법**과 **효율적인 장문 처리 전략**을 다룬다.

---

## 왜 Long Context가 어려운가

### Attention의 이차 복잡도

Transformer의 Self-Attention은 시퀀스 길이 $n$에 대해 $O(n^2)$ 연산이 필요하다:

- 4K 토큰: 16M 연산 (기준)
- 128K 토큰: 16.4B 연산 (**1,024배**)
- 1M 토큰: 1T 연산 (**62,500배**)

### KV-Cache 메모리

추론 시 KV-Cache는 시퀀스 길이에 비례하여 증가:

$$\text{KV 메모리} = 2 \times L \times d \times n \times \text{precision}$$

128K 토큰 + 32 레이어 + 4096 차원 + FP16:
- $2 \times 32 \times 4096 \times 128000 \times 2$ = **약 64GB**

이는 단일 GPU의 VRAM을 초과할 수 있다.

---

## 위치 인코딩 확장

### RoPE (Rotary Position Embedding) 복습

현재 대부분의 LLM이 사용하는 위치 인코딩. 위치 $m$에서의 쿼리-키 내적이 상대적 거리 $m-n$에만 의존하도록 설계되었다.

문제: 학습 시 최대 길이(예: 4K)보다 긴 시퀀스에서는 **학습하지 않은 위치에 대한 외삽(extrapolation)**이 필요하며, 이는 성능 저하를 야기한다.

### Position Interpolation (PI)

Chen et al.(2023)의 방법. 학습된 위치 범위를 **압축**하여 더 긴 시퀀스를 수용한다:

$$f'(x, m) = f(x, \frac{m \cdot L}{L'})$$

4K로 학습된 모델에 32K 컨텍스트를 적용하려면, 위치 인덱스를 $\frac{1}{8}$로 스케일링한다.

장점: 소량의 추가 학습으로 효과적
한계: 해상도가 낮아져 가까운 토큰 간 구분력 감소

### YaRN (Yet another RoPE extensioN)

Peng et al.(2023)이 Position Interpolation을 개선한 방법:

- **주파수별 차등 스케일링**: 고주파(짧은 거리)와 저주파(긴 거리) 성분을 다르게 처리
- 고주파 → 보간 없이 유지 (가까운 토큰 구분력 보존)
- 저주파 → 보간 적용 (먼 토큰까지 확장)

YaRN은 PI보다 **같은 확장 비율에서 더 높은 성능**을 달성하며, 현재 많은 오픈소스 모델이 채택하고 있다.

---

## 효율적 장문 처리

### Sliding Window Attention

Mistral/Mixtral이 채택한 방법. 각 토큰이 **최근 W개의 토큰에만** 어텐션을 수행한다.

```
윈도우 크기 W = 4096

토큰 위치 0~4095: 전체 어텐션
토큰 위치 4096: 위치 1~4096에만 어텐션 (0은 제외)
토큰 위치 8192: 위치 4097~8192에만 어텐션
```

복잡도: $O(n \cdot W)$ — 시퀀스 길이에 선형
한계: 윈도우 밖의 정보에 접근 불가 (다만 레이어 쌓기로 간접 접근 가능)

### Ring Attention

Liu et al.(2023)의 방법. 긴 시퀀스를 **여러 디바이스에 분할**하고, 각 디바이스가 자신의 청크에 대해 어텐션을 수행하면서 KV를 링 형태로 전달한다.

```
Device 0: 토큰 0~32K → 자체 어텐션 + Device 1의 KV 수신
Device 1: 토큰 32K~64K → 자체 어텐션 + Device 2의 KV 수신
Device 2: 토큰 64K~96K → 자체 어텐션 + Device 0의 KV 수신
```

이론적으로 **디바이스 수에 비례하여 컨텍스트 길이를 확장**할 수 있다.

### Flash Attention과의 관계

[[inference-optimization-mfu|Flash Attention]]은 어텐션의 **연산 효율**을 높이는 것이지, 복잡도 자체를 줄이지는 않는다. 그러나 메모리 효율이 크게 개선되어, **같은 GPU에서 더 긴 시퀀스를 처리**할 수 있게 한다.

---

## KV-Cache 최적화

Long Context에서 KV-Cache가 병목이 되므로, 이를 최적화하는 기법이 중요하다:

### GQA (Grouped Query Attention)

KV 헤드를 그룹으로 묶어 KV-Cache를 줄인다. LLaMA-3, Qwen2.5 등이 채택.

- MHA: Q=32, K=32, V=32 → KV 메모리 100%
- GQA (8그룹): Q=32, K=8, V=8 → KV 메모리 **25%**

### KV-Cache 양자화

KV-Cache의 정밀도를 FP16 → INT8/INT4로 줄여 메모리 절감:
- FP16 → INT8: 메모리 50% 절감, 품질 저하 미미
- FP16 → INT4: 메모리 75% 절감, 약간의 품질 저하

### KV-Cache 압축

중요하지 않은 토큰의 KV를 제거하거나 병합하는 방법:
- **H2O (Heavy Hitter Oracle)**: 어텐션 점수가 높은 토큰의 KV만 유지
- **StreamingLLM**: 초기 몇 개 토큰 + 최근 윈도우만 유지

---

## "Lost in the Middle" 문제

Liu et al.(2023)의 발견: LLM이 긴 컨텍스트의 **처음과 끝**에 위치한 정보는 잘 활용하지만, **중간에 위치한 정보는 무시**하는 경향이 있다.

이유:
- 어텐션이 시작과 끝에 집중하는 편향
- 학습 데이터에서 중요 정보가 시작/끝에 위치하는 패턴

실전 시사점:
- RAG에서 중요한 문서를 **처음 또는 끝**에 배치
- 매우 긴 입력에서는 [[context-compression|Context Compression]]으로 핵심만 추출

---

## 정리

| 기법 | 목적 | 효과 |
|------|------|------|
| Position Interpolation | 위치 인코딩 확장 | 소량 학습으로 4~8배 확장 |
| YaRN | 개선된 RoPE 확장 | PI보다 높은 품질 |
| Sliding Window | 어텐션 복잡도 감소 | 선형 복잡도, 원거리 정보 제한 |
| Ring Attention | 다중 디바이스 분산 | 디바이스 수에 비례한 확장 |
| GQA | KV-Cache 절감 | 75% 메모리 절감 |
| KV-Cache 양자화 | KV-Cache 정밀도 감소 | 50~75% 절감 |

Long Context는 단순히 "더 긴 입력을 받는 것"이 아니라, **메모리, 연산, 정보 활용**의 세 가지 차원에서의 최적화 문제다. 어떤 기법을 조합할지는 모델 크기, 하드웨어, 그리고 실제 사용 패턴에 따라 결정해야 한다.
