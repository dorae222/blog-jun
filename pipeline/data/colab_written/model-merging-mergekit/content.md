# Model Merging 실전: mergekit으로 모델 합성하기

## 들어가며

모델 A는 코딩에 강하고, 모델 B는 수학에 강하다. **두 모델의 장점을 결합한 모델 C**를 만들 수는 없을까?

**Model Merging**은 여러 모델의 가중치를 추가 학습 없이 **수학적으로 결합**하여 새로운 모델을 만드는 기법이다. 학습 비용이 들지 않고, GPU 하나로 몇 분 만에 수행할 수 있다는 점에서 매우 실용적이다.

Open LLM Leaderboard 상위 모델 중 상당수가 model merging으로 만들어졌다는 사실이 이 기법의 효과를 증명한다.

---

## Model Merging이 작동하는 이유

### Linear Mode Connectivity

같은 기본 모델에서 파인튜닝된 모델들은 **가중치 공간에서 서로 가까이** 위치한다. 이 모델들 사이의 선형 보간(linear interpolation)이 의미 있는 결과를 낳는 이유는, 파인튜닝이 기본 모델의 가중치를 **약간만** 변화시키기 때문이다.

```
기본 모델 (LLaMA-3-8B)
    ├── 파인튜닝 A: 코딩 특화 → 가중치 W_A
    └── 파인튜닝 B: 수학 특화 → 가중치 W_B

병합: W_merged = α × W_A + (1-α) × W_B
```

핵심 제약: **같은 기본 모델에서 파인튜닝된 모델들만** 병합이 의미 있다. 아키텍처가 다르거나 기본 모델이 다른 경우 병합이 불가능하거나 무의미하다.

---

## 주요 병합 알고리즘

### 1. Linear (가중 평균)

가장 단순한 방법. 각 모델의 가중치를 가중 평균한다.

$$W_{merged} = \alpha \cdot W_A + (1 - \alpha) \cdot W_B$$

장점: 직관적, 구현 간단
단점: 3개 이상 모델 병합 시 성능 저하 경향

### 2. SLERP (Spherical Linear Interpolation)

가중치를 **고차원 구면 위의 점**으로 취급하고, 구면 위에서 보간한다. 단순 선형 보간보다 **가중치의 방향과 크기를 더 잘 보존**한다.

$$W_{merged} = \frac{\sin((1-t)\theta)}{\sin\theta} W_A + \frac{\sin(t\theta)}{\sin\theta} W_B$$

SLERP는 **2개 모델 병합에만** 사용 가능하다. 3개 이상은 계층적으로 적용해야 한다.

### 3. TIES (TrIm, Elect Sign & Merge)

Yadav et al.(2023)이 제안한 방법. 단순 평균의 문제점을 해결한다:

1. **Trim**: 변화량이 작은 파라미터를 0으로 설정 (노이즈 제거)
2. **Elect Sign**: 각 파라미터에 대해 다수결로 부호 결정
3. **Merge**: 같은 부호의 값만 평균

TIES는 **간섭(interference) 문제**를 해결한다. 모델 A에서 양수 방향으로 변한 파라미터가 모델 B에서 음수 방향으로 변했다면, 단순 평균은 상쇄되어 정보 손실이 발생한다. TIES는 다수결로 방향을 통일하여 이를 방지한다.

### 4. DARE (Drop And REscale)

Yu et al.(2024)이 제안. TIES와 유사하지만, 무작위 드롭아웃을 사용한다:

1. 각 모델의 파인튜닝 delta(원래 모델과의 차이)를 계산
2. delta의 대부분을 **무작위로 0으로 설정** (드롭 확률 p)
3. 남은 값을 $\frac{1}{1-p}$로 **리스케일** (기대값 유지)
4. 리스케일된 delta를 병합

핵심 발견: 파인튜닝 delta의 **대부분은 중복**이므로, 90%를 제거해도 성능이 유지된다. 이를 통해 병합 시 간섭을 크게 줄일 수 있다.

---

## mergekit 실전

[mergekit](https://github.com/arcee-ai/mergekit)는 model merging을 위한 표준 도구다.

### 설치

```bash
pip install mergekit
```

### SLERP 병합 예제

`config.yaml`:
```yaml
slices:
  - sources:
      - model: NousResearch/Hermes-2-Pro-Llama-3-8B
        layer_range: [0, 32]
      - model: meta-math/MetaMath-Llama-3-8B
        layer_range: [0, 32]
merge_method: slerp
base_model: meta-llama/Meta-Llama-3-8B
parameters:
  t:
    - filter: self_attn
      value: [0, 0.5, 0.3, 0.7, 1]   # 레이어별 다른 비율
    - filter: mlp
      value: 0.5
    - value: 0.5
dtype: bfloat16
```

```bash
mergekit-yaml config.yaml ./merged-model --cuda --lazy-unpickle
```

### DARE-TIES 병합 (3개 모델)

```yaml
models:
  - model: NousResearch/Hermes-2-Pro-Llama-3-8B
    parameters:
      density: 0.5       # DARE 드롭 후 남기는 비율
      weight: 0.4        # 모델 A에 40% 가중치
  - model: meta-math/MetaMath-Llama-3-8B
    parameters:
      density: 0.5
      weight: 0.3
  - model: codellama/CodeLlama-8B
    parameters:
      density: 0.5
      weight: 0.3
merge_method: dare_ties
base_model: meta-llama/Meta-Llama-3-8B
parameters:
  int_space: "cs"        # cosine similarity 기반 간섭 해소
dtype: bfloat16
```

### 레이어별 병합 (Frankenmerging)

모델의 **다른 레이어를 다른 소스에서** 가져오는 방법:

```yaml
slices:
  - sources:
      - model: model_A
        layer_range: [0, 16]     # 하위 레이어는 모델 A
  - sources:
      - model: model_B
        layer_range: [16, 32]    # 상위 레이어는 모델 B
merge_method: passthrough
dtype: bfloat16
```

이 방법은 이론적 근거가 약하지만, 실험적으로 흥미로운 결과를 내기도 한다.

---

## 병합 전략 가이드

| 상황 | 권장 방법 | 이유 |
|------|----------|------|
| 2개 모델, 유사 도메인 | SLERP | 방향 보존, 안정적 |
| 2개 모델, 다른 도메인 | TIES | 간섭 해소 |
| 3개 이상 모델 | DARE-TIES | 다중 병합에 강건 |
| 실험적 시도 | Frankenmerge | 비용 0, 의외의 결과 |

### 병합 시 주의사항

1. **같은 기본 모델**: 반드시 동일 아키텍처 + 동일 기본 모델에서 파인튜닝된 모델만 병합
2. **평가**: Open LLM Leaderboard의 벤치마크로 병합 결과를 반드시 평가
3. **반복 실험**: 가중치($t$, density, weight)를 변화시키며 최적 조합 탐색
4. **Chat template 호환**: 병합된 모델의 chat template이 일관적인지 확인

---

## 한계

### 1. 능력의 단순 합산이 아님

모델 A의 코딩 능력 + 모델 B의 수학 능력 = 코딩+수학 모두 강한 모델... 이 항상 성립하지는 않는다. 병합은 **최선의 경우 두 능력의 절충**이고, 최악의 경우 **두 능력 모두 저하**된다.

### 2. 이론적 이해 부족

왜 특정 병합이 잘 작동하고 다른 것은 실패하는지에 대한 이론적 이해가 아직 부족하다. 현재는 주로 **실험적 탐색**에 의존한다.

### 3. 대형 모델에서의 불안정

70B+ 모델에서의 병합은 7B보다 불안정한 경향이 있다. 파라미터가 많을수록 간섭의 양도 증가하기 때문이다.

---

## 정리

Model Merging은 **추가 학습 없이 여러 모델의 장점을 결합**하는 효율적인 방법이다. GPU 하나로 몇 분 만에 수행할 수 있으며, Open LLM Leaderboard에서 그 효과가 검증되었다.

실전에서는 mergekit + DARE-TIES 조합이 가장 범용적이며, **데이터나 학습 없이 모델 성능을 개선**할 수 있는 유일한 방법이라는 점에서 파인튜닝의 보완재로서 가치가 있다.
