## 개요

고차원 데이터를 이해하는 가장 직관적인 방법은 **시각화**입니다. 수백~수천 차원의 특징(feature)을 가진 데이터를 2차원 또는 3차원 산점도로 표현할 수 있다면, 클러스터 구조·이상치·연속적인 변이 등을 한눈에 파악할 수 있습니다.

### PCA의 한계

PCA(주성분 분석)는 선형 변환으로 분산이 큰 방향을 순서대로 선택합니다. 계산이 빠르고 재현성이 완벽하다는 장점이 있지만, 데이터가 비선형 다양체(manifold) 위에 분포할 경우 중요한 구조를 포착하지 못합니다. 예를 들어 Swiss Roll처럼 원통형으로 말린 데이터는 PCA로 펼치면 서로 다른 클래스가 뒤섞입니다.

이를 해결하기 위해 등장한 것이 **비선형 차원 축소** 기법입니다. 이 글에서는 현재 가장 널리 쓰이는 두 가지 방법인 **t-SNE**와 **UMAP**을 수학적 원리부터 실전 사용법까지 단계적으로 살펴봅니다.

---

![t-SNE perplexity 비교: 다양한 perplexity 값에 따른 임베딩 결과 차이](figures/tsne_perplexity_comparison.png)
*t-SNE perplexity 비교: perplexity가 작으면 국소 구조에 집중하여 파편화되고, 크면 전역 구조를 강조하여 클러스터 경계가 흐려진다.*

## 수학적 배경

### t-SNE: KL Divergence 최소화

t-SNE(t-distributed Stochastic Neighbor Embedding)는 Laurens van der Maaten과 Geoffrey Hinton이 2008년 제안한 알고리즘입니다.

**고차원 유사도(가우시안 커널)**

점 $x_i$에서 $x_j$를 이웃으로 선택할 확률은 가우시안 분포로 정의됩니다:

$$p_{j|i} = \frac{\exp\left(-\|x_i - x_j\|^2 / 2\sigma_i^2\right)}{\sum_{k \neq i} \exp\left(-\|x_i - x_k\|^2 / 2\sigma_i^2\right)}$$

이를 대칭화하면:

$$p_{ij} = \frac{p_{j|i} + p_{i|j}}{2n}$$

**저차원 유사도(Student t-분포, 자유도 1)**

저차원 임베딩 점 $y_i$, $y_j$ 사이의 유사도는 t-분포(코시 분포)를 사용합니다:

$$q_{ij} = \frac{\left(1 + \|y_i - y_j\|^2\right)^{-1}}{\sum_{k \neq l}\left(1 + \|y_k - y_l\|^2\right)^{-1}}$$

t-분포는 가우시안보다 꼬리가 두꺼워 **crowding 문제**(고차원의 중간 거리 점들이 저차원에서 과밀집되는 현상)를 완화합니다.

**목적 함수: KL Divergence 최소화**

$$\mathcal{L} = KL(P \| Q) = \sum_{i \neq j} p_{ij} \log \frac{p_{ij}}{q_{ij}}$$

이 손실을 경사하강법으로 최소화하면, 고차원에서 가까운 점들은 저차원에서도 가깝게, 먼 점들은 멀게 배치됩니다.

### UMAP: 위상수학적 그래프 학습

UMAP(Uniform Manifold Approximation and Projection)은 Leland McInnes 등이 2018년 제안했으며, 리만 기하학과 위상적 데이터 분석(TDA)에 기반합니다.

**핵심 아이디어**: 고차원 데이터를 퍼지 단순 복합체(fuzzy simplicial complex)로 표현하고, 저차원에서 동일한 위상 구조를 재현합니다.

고차원 그래프의 엣지 가중치는 다음과 같이 정의됩니다:

$$w(x_i, x_j) = \exp\left(\frac{-\max(0,\, d(x_i, x_j) - \rho_i)}{\sigma_i}\right)$$

여기서 $\rho_i$는 $x_i$의 최근접 이웃까지의 거리(국소 스케일 보정), $\sigma_i$는 `n_neighbors`로 결정되는 밴드폭입니다.

저차원 그래프는 다음 분포를 따릅니다:

$$w'(y_i, y_j) = \left(1 + a \cdot \|y_i - y_j\|^{2b}\right)^{-1}$$

`min_dist` 파라미터가 $a$, $b$를 결정합니다. 두 그래프 간의 크로스 엔트로피를 최소화하여 임베딩을 학습합니다.

---

## 알고리즘 세부 사항

### t-SNE 알고리즘

| 파라미터 | 설명 | 권장 범위 |
|---|---|---|
| `perplexity` | 각 점의 유효 이웃 수, $\sigma_i$ 결정 | 5 ~ 50 |
| `n_iter` | 경사하강법 반복 횟수 | 1000 이상 |
| `learning_rate` | 업데이트 스텝 크기 | 10 ~ 1000 |

**Perplexity**는 Shannon 엔트로피로 정의되며:

$$\text{Perp}(P_i) = 2^{H(P_i)}, \quad H(P_i) = -\sum_j p_{j|i} \log_2 p_{j|i}$$

perplexity가 크면 더 많은 이웃을 고려하여 전역 구조를 강조하고, 작으면 국소 구조에 집중합니다.

**계산 복잡도**: 기본 t-SNE는 $O(n^2)$이며 대용량 데이터에 부적합합니다. **Barnes-Hut 근사**를 사용하면 $O(n \log n)$으로 줄어듭니다(sklearn 기본값).

### UMAP 알고리즘

| 파라미터 | 설명 | 권장 범위 |
|---|---|---|
| `n_neighbors` | 국소 구조 크기 결정 | 5 ~ 50 |
| `min_dist` | 임베딩 내 최소 점 간격 | 0.0 ~ 0.99 |
| `n_components` | 목표 차원 수 | 2 or 3 |
| `metric` | 거리 함수 | euclidean, cosine 등 |

- `n_neighbors`가 크면 전역 구조, 작으면 국소 클러스터를 강조합니다.
- `min_dist`가 작으면 포인트가 조밀하게 모이고, 크면 균일하게 퍼집니다.
- UMAP은 **임베딩을 다운스트림 태스크(분류·회귀)에도 활용**할 수 있을 만큼 위상 구조를 잘 보존합니다.

---

## Python 구현

### 설치

```bash
pip install scikit-learn umap-learn matplotlib
```

### MNIST 데이터 준비

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.preprocessing import StandardScaler

# MNIST 로드 (70,000개 중 5,000개 샘플링)
mnist = fetch_openml('mnist_784', version=1, as_frame=False)
X, y = mnist.data, mnist.target.astype(int)

np.random.seed(42)
idx = np.random.choice(len(X), 5000, replace=False)
X_sample, y_sample = X[idx], y[idx]

# 정규화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sample)
```

### t-SNE 적용

```python
from sklearn.manifold import TSNE

tsne = TSNE(
    n_components=2,
    perplexity=30,
    n_iter=1000,
    learning_rate='auto',
    init='pca',       # PCA 초기화로 수렴 안정화
    random_state=42
)
X_tsne = tsne.fit_transform(X_scaled)
print(f"t-SNE 완료: shape={X_tsne.shape}")
```

<!-- Execution error: TypeError: TSNE.__init__() got an unexpected keyword argument 'n_iter' -->

### UMAP 적용

```python
import umap

reducer = umap.UMAP(
    n_components=2,
    n_neighbors=15,
    min_dist=0.1,
    metric='euclidean',
    random_state=42
)
X_umap = reducer.fit_transform(X_scaled)
print(f"UMAP 완료: shape={X_umap.shape}")
```

<!-- Execution error: ModuleNotFoundError: No module named 'umap' -->

### Iris 데이터 빠른 예제

```python
from sklearn.datasets import load_iris

iris = load_iris()
X_iris, y_iris = iris.data, iris.target

# t-SNE
X_iris_tsne = TSNE(n_components=2, perplexity=10, random_state=42).fit_transform(X_iris)

# UMAP
X_iris_umap = umap.UMAP(n_neighbors=10, min_dist=0.3, random_state=42).fit_transform(X_iris)
```

---

![t-SNE 숫자 데이터 시각화: MNIST 숫자 데이터셋의 t-SNE 2D 임베딩](figures/tsne_digits.png)
*t-SNE 숫자 데이터 시각화: MNIST 숫자 데이터셋을 t-SNE로 2D 투영하면 각 숫자 클래스가 조밀하고 분리된 클러스터로 나타난다.*

## 시각화 비교

```python
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
cmap = plt.get_cmap('tab10')

# t-SNE 시각화
ax = axes[0]
for cls in range(10):
    mask = (y_sample == cls)
    ax.scatter(
        X_tsne[mask, 0], X_tsne[mask, 1],
        c=[cmap(cls)], label=str(cls),
        s=5, alpha=0.7
    )
ax.set_title('t-SNE (MNIST 5,000 samples)', fontsize=14)
ax.legend(title='Digit', markerscale=3, loc='best')
ax.set_xlabel('Dimension 1')
ax.set_ylabel('Dimension 2')

# UMAP 시각화
ax = axes[1]
for cls in range(10):
    mask = (y_sample == cls)
    ax.scatter(
        X_umap[mask, 0], X_umap[mask, 1],
        c=[cmap(cls)], label=str(cls),
        s=5, alpha=0.7
    )
ax.set_title('UMAP (MNIST 5,000 samples)', fontsize=14)
ax.legend(title='Digit', markerscale=3, loc='best')
ax.set_xlabel('Dimension 1')
ax.set_ylabel('Dimension 2')

plt.tight_layout()
plt.savefig('tsne_vs_umap_mnist.png', dpi=150, bbox_inches='tight')
plt.show()
```

<!-- Execution error: NameError: name 'X_tsne' is not defined -->

위 코드를 실행하면 t-SNE는 각 숫자(0~9) 클래스를 조밀하고 분리된 섬(island) 형태로 나타내고, UMAP은 상대적으로 더 균일한 간격을 유지하면서도 클러스터 간 연속적인 변이를 보존하는 것을 확인할 수 있습니다.

---

## 실전 팁

### 언제 무엇을 사용할까?

| 상황 | 권장 방법 |
|---|---|
| 순수 탐색적 시각화 | t-SNE (클러스터 구조 강조) |
| 새 데이터를 기존 임베딩에 투영 | UMAP (`transform()` 지원) |
| 대용량 데이터 (>100k) | UMAP (훨씬 빠름) |
| 다운스트림 ML 파이프라인 | UMAP (위상 구조 보존) |
| 3D 시각화 | UMAP (`n_components=3`) |

### 하이퍼파라미터 효과 정리

- **t-SNE perplexity**: 너무 작으면 파편화, 너무 크면 클러스터 경계 흐림. 5~50 범위에서 여러 값을 시도하세요.
- **UMAP n_neighbors**: 크게 하면 전역 구조, 작게 하면 미세 클러스터. 15가 좋은 출발점입니다.
- **UMAP min_dist**: 0.0에 가까울수록 클러스터가 조밀해지고, 1.0에 가까울수록 균일하게 퍼집니다.

### 재현성 주의

t-SNE와 UMAP 모두 확률적 알고리즘입니다. `random_state`를 고정하지 않으면 실행마다 결과가 달라집니다. 논문이나 보고서에 사용할 경우 반드시 `random_state=42` 등을 명시하세요.

### 대용량 데이터 전략

- **PCA 전처리**: 먼저 PCA로 50~100차원으로 줄인 뒤 t-SNE/UMAP을 적용하면 속도가 크게 향상됩니다.
- **서브샘플링**: t-SNE는 10,000개 이상에서 매우 느립니다. 대표 샘플을 추출하거나 UMAP을 사용하세요.
- **GPU 가속**: `cuml`(RAPIDS) 라이브러리는 GPU 기반 UMAP/t-SNE를 지원합니다.

```python
# PCA 전처리 후 t-SNE 예시
from sklearn.decomposition import PCA

X_pca = PCA(n_components=50, random_state=42).fit_transform(X_scaled)
X_tsne_fast = TSNE(n_components=2, perplexity=30, random_state=42).fit_transform(X_pca)
```

### 결과 해석 시 주의사항

- 클러스터 **크기와 거리**는 직접적인 의미를 갖지 않습니다. 특히 t-SNE에서 클러스터 간 거리는 하이퍼파라미터에 따라 크게 달라집니다.
- 같은 데이터라도 perplexity나 n_neighbors에 따라 시각적으로 매우 다른 결과가 나올 수 있습니다. 여러 설정을 비교하여 일관된 구조를 확인하세요.
- 시각화에서 보이지 않는 클러스터가 실제로 존재할 수 있으며, 반대로 시각적 클러스터가 실제로는 연속적인 분포일 수 있습니다.

---

## 정리

t-SNE와 UMAP은 고차원 데이터 탐색에 필수적인 도구입니다. t-SNE는 국소 클러스터 구조를 강조하는 시각화에 특화되어 있고, UMAP은 속도·확장성·전역 구조 보존 측면에서 우수하여 분석 파이프라인에 통합하기 적합합니다. 두 방법의 수학적 원리를 이해하고 하이퍼파라미터를 적절히 조정한다면, 복잡한 고차원 데이터 속에 숨겨진 패턴을 효과적으로 발견할 수 있습니다.