<!-- infographic-hero -->
![DBSCAN and Hierarchical Clustering 핵심 요약](figures/infographic.svg)

*Figure: DBSCAN and Hierarchical Clustering 한 장 요약 인포그래픽*

## 개요

K-Means는 군집화의 대표 알고리즘이지만 세 가지 근본적인 한계를 가집니다.

- **비구형 클러스터 처리 불가**: 원형 분포를 가정하므로 초승달, 나선형 등 복잡한 형태의 클러스터를 식별하지 못합니다.
- **노이즈(이상치) 처리 부재**: 모든 데이터 포인트를 반드시 어느 군집에 할당하므로 이상치가 군집 결과를 왜곡합니다.
- **계층 구조 표현 불가**: 단일 스케일에서만 군집화하며, 데이터 내 계층적 유사성 구조를 포착하지 못합니다.

이러한 한계를 극복하기 위해 **DBSCAN**(Density-Based Spatial Clustering of Applications with Noise)과 **계층적 클러스터링**(Hierarchical Clustering)이 개발되었습니다. DBSCAN은 밀도를 기준으로 군집과 노이즈를 동시에 탐지하고, 계층적 클러스터링은 덴드로그램(dendrogram)을 통해 데이터의 계층 구조를 시각화합니다.

---

## 수학적 배경

### DBSCAN의 핵심 개념

DBSCAN은 두 개의 하이퍼파라미터 $\varepsilon$과 $\text{MinPts}$로 정의됩니다.

**$\varepsilon$-이웃 (ε-neighborhood)**

데이터 포인트 $p$의 $\varepsilon$-이웃은 다음과 같이 정의됩니다:

$$N_\varepsilon(p) = \{ q \in D \mid \text{dist}(p, q) \leq \varepsilon \}$$

여기서 $D$는 전체 데이터셋이며, $\text{dist}$는 보통 유클리드 거리를 사용합니다.

**포인트 유형 분류**

각 데이터 포인트는 다음 세 가지 중 하나로 분류됩니다:

- **Core Point (핵심 포인트)**: $|N_\varepsilon(p)| \geq \text{MinPts}$를 만족하는 포인트. 충분히 밀집된 영역의 중심입니다.
- **Border Point (경계 포인트)**: Core Point는 아니지만 어떤 Core Point의 $\varepsilon$-이웃 안에 속하는 포인트.
- **Noise Point (노이즈 포인트)**: Core Point도 Border Point도 아닌 포인트. 이상치로 취급됩니다.

**밀도 직접 도달 가능성 (Directly Density-Reachable)**

$q$가 $p$로부터 직접 밀도 도달 가능하려면:

$$q \in N_\varepsilon(p) \quad \text{and} \quad |N_\varepsilon(p)| \geq \text{MinPts}$$

**밀도 연결성 (Density-Connected)**

두 포인트 $p$, $q$가 밀도 연결되어 있으면 동일한 군집에 속합니다. 이를 통해 임의 형태의 군집 경계를 추적할 수 있습니다.

### 계층적 클러스터링의 연결 기준

두 군집 $A$, $B$ 사이의 거리를 정의하는 **연결 기준(Linkage Criterion)**은 군집 형태에 결정적 영향을 줍니다.

| 기준 | 수식 | 특징 |
|------|------|------|
| Single Linkage | $d(A,B) = \min_{a \in A, b \in B} d(a,b)$ | 체인 효과 발생, 세장형 군집 |
| Complete Linkage | $d(A,B) = \max_{a \in A, b \in B} d(a,b)$ | 컴팩트한 구형 군집 |
| Average Linkage | $d(A,B) = \frac{1}{|A||B|} \sum_{a \in A} \sum_{b \in B} d(a,b)$ | 중간적 특성, 균형 잡힌 군집 |
| Ward Linkage | $\Delta(A,B) = \frac{|A||B|}{|A|+|B|} \|\bar{a} - \bar{b}\|^2$ | 분산 최소화, 균등 크기 군집 |

Ward 기준은 두 군집을 합칠 때 증가하는 총 분산(SSE)을 최소화하므로 일반적으로 가장 좋은 결과를 냅니다.

---

![DBSCAN과 계층적 클러스터링 비교: 밀도 기반과 계층 기반 군집화의 결과 차이](figures/dbscan_vs_hierarchical.png)
*DBSCAN과 계층적 클러스터링 비교: DBSCAN은 임의 형태의 군집과 노이즈를 탐지하고, 계층적 클러스터링은 덴드로그램으로 데이터의 계층 구조를 파악한다.*

## 알고리즘

### DBSCAN 알고리즘

```
DBSCAN(D, ε, MinPts):
  label 모든 포인트를 UNVISITED로 초기화
  for each 미방문 포인트 p in D:
    p를 VISITED로 표시
    neighbors = N_ε(p)  # ε-이웃 조회
    if |neighbors| < MinPts:
      p를 NOISE로 표시
    else:
      새 군집 C 생성
      C에 p 추가
      seed_set = neighbors - {p}
      for each q in seed_set:
        if q가 UNVISITED:
          q를 VISITED로 표시
          q_neighbors = N_ε(q)
          if |q_neighbors| >= MinPts:
            seed_set = seed_set ∪ q_neighbors
        if q가 아직 어떤 군집에도 속하지 않으면:
          C에 q 추가
  return 군집 레이블
```

시간 복잡도는 공간 인덱스(kd-tree, ball-tree) 사용 시 $O(n \log n)$이며, 최악의 경우 $O(n^2)$입니다.

### 계층적 클러스터링: 응집형 vs 분할형

**응집형 (Agglomerative, Bottom-Up)**
1. 각 데이터 포인트를 독립 군집으로 시작 ($n$개 군집)
2. 가장 가까운 두 군집을 반복적으로 합병
3. 모든 포인트가 하나의 군집이 될 때까지 반복
4. 덴드로그램을 원하는 높이에서 절단하여 $k$개 군집 획득

**분할형 (Divisive, Top-Down)**
1. 모든 데이터를 하나의 군집으로 시작
2. 가장 이질적인 군집을 반복적으로 분할
3. 각 포인트가 개별 군집이 될 때까지 반복
4. 일반적으로 응집형보다 계산 비용이 높아 덜 사용됨

### OPTICS 개요

OPTICS(Ordering Points To Identify the Clustering Structure)는 DBSCAN의 확장으로, 단일 $\varepsilon$ 대신 **도달 가능 거리(Reachability Distance)** 플롯을 생성합니다. 이를 통해 다양한 밀도의 군집을 자동으로 탐지할 수 있어, DBSCAN의 가장 큰 약점인 불균일 밀도 문제를 해결합니다.

---

## Python 구현

### 데이터 준비 및 DBSCAN

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_moons, make_blobs
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage

# 비구형 데이터 생성 (K-Means가 실패하는 케이스)
X_moons, _ = make_moons(n_samples=300, noise=0.05, random_state=42)
X_moons = StandardScaler().fit_transform(X_moons)

# DBSCAN 적용
dbscan = DBSCAN(eps=0.3, min_samples=5)
labels = dbscan.fit_predict(X_moons)

# 포인트 유형 분류
core_mask = np.zeros_like(labels, dtype=bool)
core_mask[dbscan.core_sample_indices_] = True
noise_mask = labels == -1
border_mask = ~core_mask & ~noise_mask

print(f"군집 수: {len(set(labels)) - (1 if -1 in labels else 0)}")
print(f"Core Points: {core_mask.sum()}")
print(f"Border Points: {border_mask.sum()}")
print(f"Noise Points: {noise_mask.sum()}")
```

```output
군집 수: 2
Core Points: 299
Border Points: 1
Noise Points: 0
```

### AgglomerativeClustering (sklearn)

```python
from sklearn.cluster import AgglomerativeClustering

# 여러 연결 기준 비교
X_blobs, _ = make_blobs(n_samples=150, centers=3, random_state=42)

linkage_methods = ['ward', 'complete', 'average', 'single']
results = {}

for method in linkage_methods:
    model = AgglomerativeClustering(n_clusters=3, linkage=method)
    results[method] = model.fit_predict(X_blobs)
    print(f"{method} linkage 완료")

# Ward 연결 기준이 일반적으로 가장 균형 잡힌 결과 제공
ward_model = AgglomerativeClustering(n_clusters=3, linkage='ward')
ward_labels = ward_model.fit_predict(X_blobs)
```

```output
ward linkage 완료
complete linkage 완료
average linkage 완료
single linkage 완료
```

### scipy 덴드로그램

```python
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist

# 소규모 데이터로 덴드로그램 시각화
X_small, _ = make_blobs(n_samples=30, centers=3, random_state=42)

# 연결 행렬 계산 (Ward 방법)
Z = linkage(X_small, method='ward')

plt.figure(figsize=(14, 6))
dendrogram(
    Z,
    leaf_rotation=90,
    leaf_font_size=10,
    color_threshold=10  # 이 높이에서 절단하면 3개 군집
)
plt.title('Ward 연결 기준 덴드로그램', fontsize=14)
plt.xlabel('데이터 포인트 인덱스')
plt.ylabel('거리 (병합 비용)')
plt.axhline(y=10, color='red', linestyle='--', label='절단 기준선')
plt.legend()
plt.tight_layout()
plt.show()
```

![계층적 클러스터링 덴드로그램](figures/dbscan_vs_hierarchical.png)

*Figure 1: 계층적 클러스터링 덴드로그램: 병합 과정과 절단 기준선을 통해 최적 군집 수를 결정하는 과정을 보여준다.*

### 최적 군집 수 결정 (덴드로그램 활용)

```python
def find_optimal_clusters(Z, threshold_ratio=0.7):
    """
    덴드로그램에서 가장 큰 점프(병합 거리 증가)를 찾아
    최적 군집 수를 제안합니다.
    """
    last_merges = Z[-10:, 2]  # 마지막 10번의 병합 거리
    acceleration = np.diff(last_merges, 2)  # 2차 차분
    k = acceleration[::-1].argmax() + 2  # 가장 큰 가속도 지점
    print(f"추천 군집 수: {k}")
    return k

optimal_k = find_optimal_clusters(Z)
```

```output
추천 군집 수: 3
```

---

![DBSCAN eps 파라미터 효과: 엡실론 값에 따른 군집 결과 변화](figures/dbscan_eps_effect.png)
*DBSCAN eps 파라미터 효과: eps 값이 작으면 군집이 세분화되고 노이즈가 많아지며, 크면 군집이 병합되는 과정을 보여준다.*

## 시각화

### DBSCAN 결과: Core/Border/Noise 색상 구분

```python
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# --- 왼쪽: K-Means 결과 (실패 케이스) ---
from sklearn.cluster import KMeans
kmeans_labels = KMeans(n_clusters=2, random_state=42).fit_predict(X_moons)
axes[0].scatter(X_moons[:, 0], X_moons[:, 1],
                c=kmeans_labels, cmap='Set1', alpha=0.7, s=40)
axes[0].set_title('K-Means (실패: 비구형 클러스터)', fontsize=12)
axes[0].set_xlabel('Feature 1')
axes[0].set_ylabel('Feature 2')

# --- 오른쪽: DBSCAN 결과 (성공 케이스) ---
unique_labels = set(labels)
colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

for label, color in zip(unique_labels, colors):
    if label == -1:
        # 노이즈 포인트: 검은색 X 마커
        mask = labels == label
        axes[1].scatter(X_moons[mask, 0], X_moons[mask, 1],
                        c='black', marker='x', s=80, label='Noise', zorder=5)
    else:
        mask = labels == label
        # Core Points: 큰 원
        core_pts = mask & core_mask
        axes[1].scatter(X_moons[core_pts, 0], X_moons[core_pts, 1],
                        c=[color], s=80, alpha=0.9,
                        label=f'Cluster {label} (Core)')
        # Border Points: 작은 원, 테두리 강조
        border_pts = mask & border_mask
        axes[1].scatter(X_moons[border_pts, 0], X_moons[border_pts, 1],
                        c=[color], s=40, alpha=0.5, edgecolors='black',
                        label=f'Cluster {label} (Border)')

axes[1].set_title('DBSCAN (성공: Core/Border/Noise 구분)', fontsize=12)
axes[1].set_xlabel('Feature 1')
axes[1].legend(loc='upper right', fontsize=8)
plt.tight_layout()
plt.savefig('dbscan_result.png', dpi=150, bbox_inches='tight')
plt.show()
```

![DBSCAN 결과 시각화](figures/dbscan_eps_effect.png)

*Figure 2: DBSCAN vs K-Means 비교: 비구형 클러스터에서 K-Means가 실패하는 반면 DBSCAN은 Core/Border/Noise를 구분하여 성공적으로 군집화한다.*

---

## 실전 팁

### DBSCAN 파라미터 선택법

**ε (엡실론) 선택: k-거리 그래프**

ε을 경험적으로 선택하는 가장 효과적인 방법은 k-NN 거리 플롯입니다:

```python
from sklearn.neighbors import NearestNeighbors

# MinPts = 5로 설정할 경우, k=4 (자기 자신 제외)
k = 4
neighbors = NearestNeighbors(n_neighbors=k)
neighbors.fit(X_moons)
distances, _ = neighbors.kneighbors(X_moons)

# k번째 이웃까지의 거리를 정렬하여 '팔꿈치 지점'을 ε으로 선택
sorted_distances = np.sort(distances[:, -1])[::-1]
plt.figure(figsize=(8, 4))
plt.plot(sorted_distances)
plt.xlabel('데이터 포인트 (정렬됨)')
plt.ylabel(f'{k}-NN 거리')
plt.title('k-거리 그래프: 팔꿈치 지점 = 최적 ε')
plt.axhline(y=0.3, color='red', linestyle='--', label='ε = 0.3')
plt.legend()
plt.show()
```

![k-거리 그래프](figures/dbscan_eps_effect.png)

*Figure 3: k-거리 그래프: k-NN 거리를 정렬하여 팔꿈치 지점에서 최적 ε 값을 결정하는 DBSCAN 파라미터 선택 방법을 보여준다.*

**MinPts 선택 경험 법칙**

- 일반적으로 $\text{MinPts} \geq D + 1$ (D: 데이터 차원)
- 잡음이 많은 데이터: $\text{MinPts} = 2 \times D$
- 소규모 데이터셋: $\text{MinPts} = 3$, 대규모: $\text{MinPts} = 5 \sim 10$
- 노이즈가 많을수록 MinPts를 크게 설정

### DBSCAN vs 계층적 클러스터링: 언제 무엇을 쓸까?

| 상황 | 추천 알고리즘 | 이유 |
|------|--------------|------|
| 군집 수를 모름 + 노이즈 존재 | DBSCAN | 자동으로 군집 수 결정, 노이즈 분리 |
| 비구형 복잡한 경계 | DBSCAN | 밀도 기반으로 임의 형태 탐지 |
| 데이터 계층 구조 분석 필요 | 계층적 클러스터링 | 덴드로그램으로 계층 시각화 |
| 소규모 데이터 (< 10,000) | 계층적 클러스터링 | $O(n^2)$ 메모리도 허용 가능 |
| 대규모 데이터 (> 100,000) | DBSCAN (+ 공간 인덱스) | kd-tree로 $O(n \log n)$ 달성 |
| 불균일 밀도 군집 | OPTICS | DBSCAN보다 강건한 밀도 기반 탐지 |
| 군집 수 $k$ 이미 알고 있음 | 계층적 (절단) 또는 K-Means | 덴드로그램 절단으로 정확히 $k$개 |

### 주의사항 및 전처리

1. **스케일 정규화 필수**: DBSCAN은 거리 기반이므로 `StandardScaler` 또는 `MinMaxScaler` 적용이 필수적입니다.
2. **고차원 문제 (차원의 저주)**: 차원이 높아질수록 모든 포인트 간 거리가 유사해져 ε 선택이 어려워집니다. PCA/UMAP으로 차원 축소 후 적용을 권장합니다.
3. **계층적 클러스터링의 메모리**: $n \times n$ 거리 행렬이 필요하므로 $n > 10{,}000$에서는 메모리 문제가 발생합니다. 대안으로 `sklearn`의 `connectivity` 파라미터를 활용한 희소 행렬 방식을 사용하세요.

---

## 정리

DBSCAN과 계층적 클러스터링은 K-Means의 보완재로, 서로 다른 강점을 가집니다. 실제 분석에서는 데이터 형태, 규모, 노이즈 수준, 그리고 군집 수 사전 지식 여부에 따라 알고리즘을 선택해야 합니다. 탐색적 단계에서는 계층적 클러스터링의 덴드로그램으로 데이터 구조를 파악하고, 이상치가 중요한 비즈니스 문제에서는 DBSCAN을 우선적으로 검토하세요.