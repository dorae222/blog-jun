## 개요

K-Means 클러스터링은 레이블 없는 데이터를 **K개의 군집(cluster)**으로 자동 분류하는 비지도 학습(Unsupervised Learning) 알고리즘입니다. 1957년 Stuart Lloyd가 펄스 부호 변조(PCM) 문제를 풀기 위해 고안했으며, 1982년 공식 논문으로 발표된 이후 산업 전반에서 가장 널리 쓰이는 군집화 기법으로 자리 잡았습니다.

핵심 아이디어는 단순합니다. 각 군집의 **중심(centroid)**을 정의하고, 모든 데이터 포인트를 가장 가까운 중심에 배정한 뒤, 배정 결과를 바탕으로 중심을 재계산하는 과정을 수렴할 때까지 반복합니다. 계산 비용이 낮고 구현이 직관적이라 탐색적 데이터 분석(EDA), 고객 세분화, 이미지 압축, 문서 분류 등 다양한 도메인에서 첫 번째 군집화 도구로 자주 선택됩니다.

---

## 수학적 배경

### 목적함수 (Objective Function)

K-Means의 목표는 **군집 내 제곱합(Within-Cluster Sum of Squares, WCSS)**을 최소화하는 것입니다.

$$J = \sum_{i=1}^{K} \sum_{x \in C_i} \|x - \mu_i\|^2$$

- $K$: 군집 수
- $C_i$: $i$번째 군집에 속하는 데이터 집합
- $\mu_i$: $i$번째 군집의 중심 벡터 ($\mu_i = \frac{1}{|C_i|} \sum_{x \in C_i} x$)
- $\|x - \mu_i\|^2$: 데이터 포인트 $x$와 군집 중심 사이의 유클리드 거리 제곱

이 최적화 문제는 NP-Hard임이 알려져 있으므로, Lloyd 알고리즘을 통해 **지역 최솟값(local minimum)**을 반복적으로 찾는 방식으로 근사 해를 구합니다.

### 배정 단계 (Assignment Step)

각 데이터 포인트 $x^{(j)}$를 가장 가까운 중심 $\mu_i$의 군집으로 배정합니다.

$$c^{(j)} = \arg\min_{i} \|x^{(j)} - \mu_i\|^2$$

### 갱신 단계 (Update Step)

각 군집에 배정된 데이터 포인트들의 평균으로 중심을 재계산합니다.

$$\mu_i = \frac{1}{|C_i|} \sum_{x \in C_i} x$$

두 단계를 중심 위치가 더 이상 변하지 않거나, 지정한 반복 횟수에 도달할 때까지 반복합니다.

---

![K-Means 반복 과정: 중심 이동과 클러스터 재배정의 반복적 수렴](figures/kmeans_iterations.png)
*K-Means 반복 과정: 초기 중심에서 시작하여 배정-갱신 단계를 반복하면서 클러스터 중심이 최적 위치로 수렴하는 과정을 보여준다.*

## 알고리즘 변형

### Lloyd 알고리즘 단계

1. **초기화**: K개의 중심을 무작위로 선택합니다.
2. **배정**: 각 데이터 포인트를 가장 가까운 중심에 배정합니다.
3. **갱신**: 각 군집의 평균으로 중심을 업데이트합니다.
4. **반복**: 중심이 수렴하거나 `max_iter`에 도달할 때까지 2-3을 반복합니다.

### K-Means++ 초기화

표준 K-Means의 가장 큰 단점은 초기 중심의 무작위 선택으로 인한 불안정성입니다. **K-Means++**는 이를 개선하여 초기 중심이 서로 멀리 떨어지도록 확률적으로 선택합니다.

1. 첫 번째 중심 $\mu_1$을 데이터에서 균등 무작위 선택합니다.
2. 나머지 중심 $\mu_k$는 각 데이터 포인트가 이미 선택된 중심들과의 최소 거리 제곱에 비례하는 확률 $D(x)^2$로 선택합니다.
3. K개의 중심이 모두 선택될 때까지 반복합니다.

K-Means++는 수렴 속도를 높이고, 전역 최솟값에 더 가까운 해를 찾을 확률을 높입니다. scikit-learn의 `KMeans`는 기본값으로 `init='k-means++'`를 사용합니다.

### Mini-Batch K-Means

대용량 데이터셋에서는 전체 데이터를 매 반복마다 처리하는 Lloyd 알고리즘이 느릴 수 있습니다. **Mini-Batch K-Means**는 매 반복마다 무작위로 추출한 소규모 배치(mini-batch)만 사용해 중심을 갱신합니다.

- 속도: 일반 K-Means보다 훨씬 빠름
- 품질: WCSS가 약간 증가할 수 있지만 대부분 실용적 수준
- 적합 사례: 수백만 건 이상의 대규모 데이터셋

### K-Medoids (PAM)

K-Means는 중심을 실제 데이터 포인트가 아닌 평균값으로 정의하므로, 이상치(outlier)에 민감합니다. **K-Medoids(Partitioning Around Medoids)**는 중심을 반드시 실제 데이터 포인트 중 하나로 제한합니다.

- 이상치에 강건(robust)
- 임의의 거리 척도(예: 맨해튼 거리, 코사인 유사도) 사용 가능
- 계산 비용이 K-Means보다 높음 ($O(K \cdot n^2)$)

---

## Python 구현

### 기본 K-Means 및 엘보우 방법

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# 샘플 데이터 생성
X, y_true = make_blobs(n_samples=500, centers=4, cluster_std=0.8, random_state=42)

# 필수: 스케일링
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ── 엘보우 방법 (Inertia 기반) ──────────────────────────
inertias = []
silhouette_scores = []
k_range = range(2, 11)

for k in k_range:
    km = KMeans(n_clusters=k, init='k-means++', n_init=10, random_state=42)
    km.fit(X_scaled)
    inertias.append(km.inertia_)          # WCSS
    silhouette_scores.append(silhouette_score(X_scaled, km.labels_))

print("K별 Inertia:", inertias)
print("K별 Silhouette Score:", silhouette_scores)
```

```output
K별 Inertia: [518.300445765582, 108.52756905308306, 18.65612803611449, 16.595477425430072, 14.814293521896422, 13.128886338259946, 11.62994216605812, 10.582351119146242, 9.603602827742957]
K별 Silhouette Score: [0.5726972776522599, 0.7666510516259168, 0.8392940455141259, 0.7117422907575142, 0.5781259044231806, 0.46013784903447946, 0.3517501111918402, 0.3486261363028759, 0.3546557181215523]
```

### 최적 K로 최종 모델 학습

```python
# 최적 K 선택 (예: 4)
optimal_k = 4
km_final = KMeans(n_clusters=optimal_k, init='k-means++', n_init=10, random_state=42)
km_final.fit(X_scaled)

labels = km_final.labels_
centroids = km_final.cluster_centers_

print(f"최종 Inertia: {km_final.inertia_:.4f}")
print(f"실루엣 계수: {silhouette_score(X_scaled, labels):.4f}")
```

```output
최종 Inertia: 18.6561
실루엣 계수: 0.8393
```

---

![엘보우 방법: 클러스터 수에 따른 Inertia 변화와 최적 K 선택](figures/elbow_method.png)
*엘보우 방법: Inertia가 급격히 감소하다가 완만해지는 엘보우 지점을 최적 클러스터 수 K로 선택한다.*

## 시각화

### 클러스터 결과 산점도 + 엘보우 곡선 + 실루엣 계수

```python
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# ── 1. 클러스터 결과 산점도 ──────────────────────────────
colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
for i in range(optimal_k):
    mask = labels == i
    axes[0].scatter(X_scaled[mask, 0], X_scaled[mask, 1],
                    c=colors[i], s=40, alpha=0.7, label=f'Cluster {i+1}')
axes[0].scatter(centroids[:, 0], centroids[:, 1],
                c='black', marker='X', s=200, zorder=5, label='Centroids')
axes[0].set_title('K-Means 클러스터링 결과', fontsize=13)
axes[0].set_xlabel('Feature 1 (scaled)')
axes[0].set_ylabel('Feature 2 (scaled)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# ── 2. 엘보우 곡선 ──────────────────────────────────────
axes[1].plot(list(k_range), inertias, 'bo-', linewidth=2, markersize=7)
axes[1].axvline(x=optimal_k, color='red', linestyle='--', alpha=0.7, label=f'K={optimal_k} (elbow)')
axes[1].set_title('엘보우 방법 (Inertia)', fontsize=13)
axes[1].set_xlabel('클러스터 수 K')
axes[1].set_ylabel('Inertia (WCSS)')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# ── 3. 실루엣 계수 ──────────────────────────────────────
axes[2].plot(list(k_range), silhouette_scores, 'gs-', linewidth=2, markersize=7)
axes[2].axvline(x=optimal_k, color='red', linestyle='--', alpha=0.7, label=f'K={optimal_k}')
axes[2].set_title('실루엣 계수 (Silhouette Score)', fontsize=13)
axes[2].set_xlabel('클러스터 수 K')
axes[2].set_ylabel('Silhouette Score')
axes[2].legend()
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('kmeans_analysis.png', dpi=150, bbox_inches='tight')
plt.show()
```

![Kmeans-Clustering Fig 1](/media/figures/outputs/kmeans-clustering/kmeans-clustering_fig_1.png)

### Mini-Batch K-Means 비교

```python
from sklearn.cluster import MiniBatchKMeans
import time

# 대용량 데이터 시뮬레이션
X_large, _ = make_blobs(n_samples=100_000, centers=4, random_state=42)
X_large_scaled = StandardScaler().fit_transform(X_large)

# 일반 K-Means
t0 = time.time()
km = KMeans(n_clusters=4, n_init=3, random_state=42).fit(X_large_scaled)
print(f"K-Means 소요 시간: {time.time()-t0:.2f}s | Inertia: {km.inertia_:.2f}")

# Mini-Batch K-Means
t0 = time.time()
mbkm = MiniBatchKMeans(n_clusters=4, batch_size=1024, n_init=3, random_state=42).fit(X_large_scaled)
print(f"Mini-Batch K-Means 소요 시간: {time.time()-t0:.2f}s | Inertia: {mbkm.inertia_:.2f}")
```

```output
K-Means 소요 시간: 0.21s | Inertia: 6141.42
Mini-Batch K-Means 소요 시간: 0.03s | Inertia: 6142.11
```

---

## 실전 팁

### 1. 스케일링은 필수입니다

K-Means는 유클리드 거리를 기반으로 하므로 피처의 단위(scale)에 매우 민감합니다. 예를 들어 나이(0-100)와 연봉(0-100,000,000)이 함께 있으면 연봉이 거리를 압도하여 나이가 군집화에 거의 영향을 미치지 않습니다. `StandardScaler` 또는 `MinMaxScaler`를 항상 적용하세요.

### 2. K 선택 방법

| 방법 | 설명 | 장단점 |
|------|------|---------|
| 엘보우 방법 | Inertia가 급격히 감소하다가 완만해지는 지점 | 직관적이지만 경계가 불명확할 때 있음 |
| 실루엣 계수 | 군집 내 응집도와 군집 간 분리도의 평균 ($-1 \sim 1$) | 높을수록 좋음, 계산 비용 $O(n^2)$ |
| Gap Statistic | 실제 데이터와 균일 분포 데이터의 Inertia 차이 비교 | 통계적 근거가 탄탄하나 구현 복잡 |
| BIC/AIC | GMM 기반 정보 기준 | K-Means에 직접 적용은 어려움 |

### 3. 구형 클러스터 가정의 한계

K-Means는 각 군집이 **구형(spherical)**이고 크기와 밀도가 비슷하다고 가정합니다. 다음과 같은 경우 K-Means가 잘 작동하지 않습니다.

- 초승달 모양, 동심원 형태의 데이터
- 군집 크기나 밀도가 크게 다른 경우
- 고차원 희소 데이터 (차원의 저주)

### 4. 비구형 데이터의 대안 알고리즘

| 알고리즘 | 특징 | 적합 상황 |
|-----------|------|-----------|
| DBSCAN | 밀도 기반, 노이즈 포인트 감지 | 불규칙 모양, 이상치 많은 데이터 |
| GMM | 확률적 소프트 배정, 타원형 군집 | 군집 크기·모양이 다양한 경우 |
| Spectral Clustering | 그래프 라플라시안 기반 | 비볼록(non-convex) 군집 |
| Hierarchical Clustering | 덴드로그램으로 계층 구조 파악 | K를 사전에 모를 때 탐색용 |

### 5. 여러 번 실행하세요

초기 중심 선택의 무작위성으로 인해 실행마다 결과가 달라질 수 있습니다. scikit-learn의 `n_init` 파라미터(기본값 10)를 활용해 여러 번 실행한 뒤 Inertia가 가장 낮은 결과를 선택하세요.

```python
# n_init=10: 10번 실행 후 최적 결과 반환
km = KMeans(n_clusters=4, init='k-means++', n_init=10, random_state=42)
```

---

## 정리

K-Means 클러스터링은 단순하면서도 강력한 비지도 학습 알고리즘입니다. 빠른 수렴 속도와 낮은 계산 비용 덕분에 대규모 데이터에도 적용 가능하며, K-Means++와 Mini-Batch 변형으로 실용성을 더욱 높일 수 있습니다. 다만 K를 사전에 지정해야 하고 구형 군집 가정이 있다는 한계를 인식하고, 필요에 따라 DBSCAN이나 GMM 같은 대안을 함께 검토하는 것이 좋은 실천입니다.