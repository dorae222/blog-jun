## 1. 개요 ( 이상 탐지의 특수성

대부분의 지도 학습 문제는 충분한 양의 레이블 데이터를 전제로 한다. 스팸 필터를 만들려면 스팸과 정상 메일이 골고루 있어야 하고, 암 진단 모델을 학습하려면 암 환자와 정상인의 데이터가 모두 필요하다. 그러나 **이상 탐지(Anomaly Detection)** 는 이 전제 자체가 성립하지 않는 환경에서 작동해야 한다.

이상 탐지가 다른 문제와 다른 이유는 크게 두 가지다.

**첫째, 극도의 클래스 불균형.** 신용카드 거래에서 사기 건수는 전체의 0.1% 미만이고, 공장 제품 불량률은 0.01% 수준인 경우도 흔하다. 이런 환경에서 단순히 "모두 정상"이라고 예측해도 99.9% 정확도가 나온다. 정확도 지표는 전혀 의미가 없고, 정밀도(Precision)·재현율(Recall)·AUC 같은 지표를 함께 사용해야 한다.

**둘째, 이상 레이블의 부재.** 어떤 데이터가 이상인지 사전에 알기 어렵다. 해킹 공격은 매번 새로운 형태로 등장하고, 금융 사기 수법은 끊임없이 진화한다. 알려진 이상 패턴으로만 학습한 모델은 새로운 유형의 이상을 탐지하지 못하는 **미지 이상(unknown anomaly)** 문제에 직면한다.

이러한 이유로 이상 탐지는 주로 **정상 데이터의 분포를 학습**하고, 그 분포에서 멀리 벗어난 샘플을 이상으로 판단하는 방식을 취한다. 이를 **비지도(unsupervised)** 또는 **반지도(semi-supervised)** 이상 탐지라 부른다.

---

## 2. 이상의 유형

이상(anomaly)은 단순히 '다른 것'이 아니라 **어떤 맥락에서 다른가**에 따라 세 가지 유형으로 분류된다.

### 포인트 이상 (Point Anomaly)

가장 직관적인 유형이다. 개별 데이터 포인트 하나가 나머지 전체와 비교했을 때 현저하게 다른 경우다. 예를 들어 평균 체온이 36.5°C인 데이터셋에서 42°C 관측값이 나타나면 포인트 이상으로 볼 수 있다. 금융 데이터에서 평소와 비교해 수백 배 큰 단일 거래도 이에 해당한다.

### 문맥적 이상 (Contextual Anomaly)

해당 데이터 포인트 자체는 정상 범위에 있지만, **특정 문맥(시점, 위치, 조건)** 에서는 비정상인 경우다. 한여름 기온 35°C는 정상이지만 한겨울에 35°C가 기록된다면 이상이다. 시계열 데이터에서 자주 등장하며, 단순히 수치만 보면 이상을 탐지할 수 없고 반드시 **주변 맥락**을 함께 고려해야 한다.

### 집단 이상 (Collective Anomaly)

개별 데이터 포인트 하나하나는 모두 정상 범위에 있지만, **특정 그룹 또는 패턴 전체**가 이상인 경우다. 심전도(ECG) 데이터에서 개별 심박수는 정상이지만 특정 구간의 리듬 패턴이 부정맥을 나타내는 경우가 대표적이다. 네트워크 트래픽에서도 개별 패킷은 정상이지만 짧은 시간 안에 대량으로 집중되는 패턴이 DDoS 공격 신호일 수 있다.

---

![이상 탐지 알고리즘 비교: 다양한 이상 탐지 기법의 결정 경계 비교](figures/anomaly_detection_comparison.png)
*이상 탐지 알고리즘 비교: 통계적 방법, Isolation Forest, LOF 등 주요 이상 탐지 알고리즘이 동일 데이터에서 생성하는 결정 경계의 차이를 보여준다.*

## 3. 통계적 방법

### Z-score 방법

가장 단순한 이상 탐지 방법이다. 각 데이터 포인트의 평균으로부터의 표준편차 거리를 계산한다.

$$z = \frac{x - \mu}{\sigma}$$

일반적으로 $|z| > 3$인 포인트를 이상으로 판단한다. 하지만 이 방법은 **정규 분포를 가정**하며, 이상치 자체가 평균과 표준편차를 왜곡시키는 마스킹(masking) 문제가 있다.

### IQR 방법

분위수(quantile)를 활용하기 때문에 분포 가정 없이 쓸 수 있는 비모수적 방법이다.

$$\text{IQR} = Q_3 - Q_1$$

하한: $Q_1 - 1.5 \times \text{IQR}$, 상한: $Q_3 + 1.5 \times \text{IQR}$ 범위를 벗어나는 값을 이상으로 본다. 박스플롯의 수염(whisker)이 바로 이 기준이다. 평균·표준편차 대신 중앙값·분위수를 사용하므로 이상치의 영향을 덜 받는다.

### 다변량 이상 탐지 ) 마할라노비스 거리

단변량 방법을 다변량으로 확장한 것이 **마할라노비스 거리(Mahalanobis Distance)** 다. 특성 간 상관관계를 반영하는 거리 척도로, 공분산 행렬 $\Sigma$를 활용한다.

$$D_M(\mathbf{x}) = \sqrt{(\mathbf{x} - \boldsymbol{\mu})^T \Sigma^{-1} (\mathbf{x} - \boldsymbol{\mu})}$$

가우시안 분포를 가정할 경우, $D_M^2$는 자유도 $p$인 카이제곱 분포를 따른다. 유의 수준 $\alpha$에 해당하는 임계값 $\chi^2_{p, 1-\alpha}$를 초과하면 이상으로 분류한다. 단, 데이터가 실제로 다변량 정규 분포를 따른다는 가정이 성립해야 하며, 공분산 행렬 추정에 충분한 샘플이 필요하다.

---

![이상 점수 분포: 정상 데이터와 이상 데이터의 이상 점수 히스토그램 비교](figures/anomaly_score_distribution.png)
*이상 점수 분포: 정상 데이터는 낮은 이상 점수에 집중되고, 이상 데이터는 높은 점수를 가지며 두 분포 사이의 임계값 설정이 핵심이다.*

## 4. Isolation Forest

### 핵심 아이디어

Isolation Forest는 2008년 Liu 등이 제안한 알고리즘으로, 이상 탐지에 특화된 트리 기반 앙상블이다. 핵심 직관은 단순하다. **이상 포인트는 정상 포인트보다 훨씬 쉽게 고립(isolate)된다.**

정상 데이터는 밀집되어 있어 고립시키려면 여러 번 분기가 필요하다. 반면 이상 데이터는 희박한 공간에 홀로 떨어져 있어 적은 분기만으로 고립된다. 이 차이를 분기 깊이(path length)로 측정한다.

### 알고리즘

1. 데이터에서 무작위로 부분 집합을 샘플링한다 (보통 256개).
2. 무작위로 특성 하나를 선택하고, 해당 특성의 최솟값~최댓값 사이에서 무작위로 분기 기준값을 선택해 트리를 성장시킨다.
3. 각 데이터 포인트가 트리에서 고립(리프 노드 도달)될 때까지의 분기 횟수, 즉 경로 길이(path length) $h(x)$를 측정한다.
4. $n_t$개의 트리에서 평균 경로 길이 $E[h(x)]$를 구하고, 이상 점수를 다음과 같이 정의한다.

$$\text{score}(x, n) = 2^{-\frac{E[h(x)]}{c(n)}}$$

여기서 $c(n) = 2H(n-1) - \frac{2(n-1)}{n}$은 $n$개 샘플로 구성된 이진 탐색 트리의 평균 경로 길이 기댓값이며, $H(i) = \ln(i) + 0.5772\ldots$ (오일러-마스케로니 상수)다.

이상 점수가 **1에 가까울수록 이상**에 가깝고, **0.5 이하면 정상**으로 간주한다.

### 장점

- 시간 복잡도 $O(n \log n)$으로, 대용량 데이터에도 효율적이다.
- 고차원 데이터에서도 성능이 잘 유지된다.
- 정규 분포 등 특정 분포 가정이 없다.
- 레이블 없이도 동작한다 (비지도 방법).

---

## 5. One-Class SVM

### 핵심 아이디어

One-Class SVM은 정상 데이터만을 학습하여 **정상 데이터를 둘러싸는 최소 초구(Hypersphere)** 를 찾는 알고리즘이다. 새로운 샘플이 이 초구 안에 있으면 정상, 밖에 있으면 이상으로 분류한다.

### 최적화 문제

특성 공간에서 반지름 $R$, 중심 $\mathbf{c}$인 초구를 정의하고, 대부분의 훈련 데이터가 초구 안에 포함되도록 반지름을 최소화한다.

$$\min_{R, \mathbf{c}, \boldsymbol{\xi}} R^2 + \frac{1}{\nu n}\sum_{i=1}^{n} \xi_i$$
$$\text{subject to} \quad \|\phi(\mathbf{x}_i) - \mathbf{c}\|^2 \leq R^2 + \xi_i, \quad \xi_i \geq 0$$

여기서 $\nu \in (0, 1]$는 이상 비율의 상한선이자 서포트 벡터 비율의 하한선 역할을 동시에 하는 하이퍼파라미터다. $\nu$가 작을수록 이상으로 분류하는 샘플이 줄어들고(엄격한 경계), 클수록 더 많은 샘플이 이상으로 분류된다.

### 커널 트릭 활용

SVM과 마찬가지로 커널 함수를 통해 고차원 공간에서 비선형 경계를 그릴 수 있다. 가장 많이 쓰이는 커널은 **RBF (가우시안) 커널**이다.

$$k(\mathbf{x}_i, \mathbf{x}_j) = \exp\left(-\gamma \|\mathbf{x}_i - \mathbf{x}_j\|^2\right)$$

$\gamma$가 크면 각 훈련 샘플의 영향 반경이 좁아져 복잡한 경계가 형성되고, 작으면 매끄러운 경계가 만들어진다.

### 한계

- 훈련 시간이 $O(n^2)$~$O(n^3)$으로 대용량 데이터에는 비효율적이다.
- $\nu$와 $\gamma$ 파라미터 튜닝이 중요하며, 정상 데이터만으로는 최적화 기준이 명확하지 않다.
- 고차원 희소 데이터에서는 성능이 저하될 수 있다.

---

## 6. LOF (Local Outlier Factor)

### 국소 밀도 비교

LOF는 전역적 기준이 아닌 **이웃과의 상대적 밀도**를 이용해 이상을 탐지한다. 핵심 아이디어는 이상 포인트가 있는 영역의 밀도는 이웃 영역의 밀도보다 훨씬 낮다는 것이다.

### 수식 정의

**k-거리** ($k\text{-dist}(x)$): 점 $x$로부터 $k$번째 가까운 이웃까지의 거리.

**도달 가능 거리** (Reachability Distance):
$$\text{reach-dist}_k(x, o) = \max\{k\text{-dist}(o),\; d(x, o)\}$$

$k\text{-dist}(o)$보다 $d(x, o)$가 작으면 $k\text{-dist}(o)$로 대체하여 근거리 밀도 추정의 노이즈를 줄인다.

**국소 도달 가능 밀도** (Local Reachability Density):
$$\text{lrd}_k(x) = \frac{|N_k(x)|}{\sum_{o \in N_k(x)} \text{reach-dist}_k(x, o)}$$

$N_k(x)$는 $x$의 $k$-이웃 집합이다.

**LOF 점수**:
$$\text{LOF}_k(x) = \frac{\sum_{o \in N_k(x)} \frac{\text{lrd}_k(o)}{\text{lrd}_k(x)}}{|N_k(x)|} = \frac{\text{avg. local density of neighbors}}{\text{local density of } x}$$

$\text{LOF}(x) \gg 1$이면 $x$의 밀도가 이웃보다 현저히 낮다는 의미로 **이상**이다. $\text{LOF}(x) \approx 1$이면 이웃과 비슷한 밀도로 **정상**이다.

### LOF의 강점과 약점

LOF는 밀도가 균일하지 않은 데이터, 즉 **다중 클러스터가 있거나 밀도 편차가 큰** 데이터에서 강점을 발휘한다. Z-score나 Isolation Forest처럼 전역 기준만 사용하면 놓칠 수 있는 **국소 이상**을 효과적으로 탐지한다.

단점은 $k$ 선택이 성능에 민감하게 영향을 미친다는 점과, 시간 복잡도가 $O(n^2)$에 달해 대용량 데이터에는 불리하다는 것이다.

---

## 7. AutoEncoder 기반 이상 탐지 (딥러닝)

딥러닝을 활용한 이상 탐지에서 가장 널리 쓰이는 접근법은 **AutoEncoder** 다. 정상 데이터만으로 AutoEncoder를 학습시키면, 모델은 정상 패턴을 효율적으로 인코딩하고 복원하는 방법을 익힌다.

추론 시에는 각 샘플의 **재구성 오차(Reconstruction Error)** 를 이상 점수로 사용한다.

$$\text{anomaly score}(x) = \|x - \hat{x}\|^2 = \|x - \text{Decoder}(\text{Encoder}(x))\|^2$$

정상 샘플은 학습된 패턴 내에 있으므로 재구성 오차가 작다. 반면 이상 샘플은 AutoEncoder가 한 번도 본 적 없는 패턴이므로 재구성이 실패하고 오차가 커진다.

**변형 AutoEncoder (VAE, Variational AutoEncoder)** 는 잠재 공간을 확률 분포로 모델링하여 더 정교한 이상 점수를 제공한다. 최근에는 Diffusion 모델이나 Transformer 기반의 이상 탐지도 활발히 연구되고 있다.

AutoEncoder 기반 이상 탐지는 특히 **이미지 데이터**에 강하다. 제조 공정의 결함 이미지 탐지, 의료 영상의 병변 탐지 등이 대표적인 응용이다.

---

## 8. 실전 활용 가이드

| 도메인 | 이상 유형 | 권장 방법 | 이유 |
|---|---|---|---|
| 금융 사기 탐지 | 포인트·문맥적 | 시간 패턴 + LOF | 거래 맥락·시간대 고려 필요 |
| 제조 불량 감지 | 포인트 | 이미지 AutoEncoder | 고차원 비정형 데이터 |
| 네트워크 침입 탐지 | 집단 | Isolation Forest | 대용량·고차원 로그 데이터 |
| 서버 장애 예측 | 문맥적 | 시계열 기반 LSTM-AE | 순서 의존성 존재 |
| 의료 이상 탐지 | 포인트·집단 | One-Class SVM | 소규모·고차원 데이터 |

**실전 체크리스트:**
- 이상의 유형(포인트·문맥·집단)을 먼저 정의한다.
- 레이블이 일부라도 있다면 반지도 방법을 고려한다.
- 평가 지표는 정확도가 아닌 **AUC-ROC, Average Precision** 을 사용한다.
- 임계값(threshold)은 비즈니스 맥락에 따라 조정한다. 금융 사기는 재현율을, 스팸 탐지는 정밀도를 우선한다.
- 이상 탐지 결과는 반드시 도메인 전문가의 검토를 거쳐야 한다.

---

## 9. Python 코드

### Isolation Forest와 LOF 비교

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

# 정상 데이터와 이상 데이터 생성
np.random.seed(42)

# 정상 클러스터
X_normal, _ = make_blobs(n_samples=300, centers=[[0, 0], [5, 5]],
                          cluster_std=0.8, random_state=42)
# 이상 데이터 (희소 공간에 산포)
X_anomaly = np.random.uniform(low=-6, high=12, size=(20, 2))

X = np.vstack([X_normal, X_anomaly])
y_true = np.array([1] * 300 + [-1] * 20)  # 1: 정상, -1: 이상

# 전처리
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --- Isolation Forest ---
iso_forest = IsolationForest(
    n_estimators=100,
    contamination=0.06,  # 예상 이상 비율
    random_state=42
)
iso_forest.fit(X_scaled)
if_pred = iso_forest.predict(X_scaled)       # 1: 정상, -1: 이상
if_scores = iso_forest.decision_function(X_scaled)  # 높을수록 정상

# --- LOF ---
lof = LocalOutlierFactor(
    n_neighbors=20,
    contamination=0.06
)
lof_pred = lof.fit_predict(X_scaled)         # 1: 정상, -1: 이상
lof_scores = lof.negative_outlier_factor_    # 낮을수록(음수 클수록) 이상

# --- 성능 비교 ---
from sklearn.metrics import classification_report, roc_auc_score

print("=== Isolation Forest ===")
print(classification_report(y_true, if_pred, target_names=['이상', '정상']))

print("=== LOF ===")
print(classification_report(y_true, lof_pred, target_names=['이상', '정상']))

# AUC 계산 (점수가 높을수록 정상 → 이상 점수로 뒤집기)
if_auc = roc_auc_score(y_true == -1, -if_scores)
lof_auc = roc_auc_score(y_true == -1, -lof_scores)
print(f"Isolation Forest AUC: {if_auc:.4f}")
print(f"LOF AUC:              {lof_auc:.4f}")

# --- 시각화 ---
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for ax, pred, title in zip(
    axes,
    [if_pred, lof_pred],
    ['Isolation Forest', 'LOF (Local Outlier Factor)']
):
    # 배경 색상
    xx, yy = np.meshgrid(
        np.linspace(X_scaled[:, 0].min() - 1, X_scaled[:, 0].max() + 1, 300),
        np.linspace(X_scaled[:, 1].min() - 1, X_scaled[:, 1].max() + 1, 300)
    )
    if title == 'Isolation Forest':
        Z = iso_forest.decision_function(np.c_[xx.ravel(), yy.ravel()])
    else:
        # LOF는 fit_predict이므로, 새 모델로 배경 계산
        lof_bg = LocalOutlierFactor(n_neighbors=20, contamination=0.06, novelty=True)
        lof_bg.fit(X_scaled)
        Z = lof_bg.decision_function(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    ax.contourf(xx, yy, Z, levels=20, cmap='RdYlGn', alpha=0.4)
    ax.contour(xx, yy, Z, levels=[0], colors='black', linewidths=1.5, linestyles='--')

    # 데이터 포인트
    colors = ['steelblue' if p == 1 else 'red' for p in pred]
    ax.scatter(X_scaled[:, 0], X_scaled[:, 1], c=colors,
               edgecolors='k', s=30, linewidths=0.5, alpha=0.8)
    ax.set_title(title, fontsize=13)
    ax.set_xlabel('Feature 1')
    ax.set_ylabel('Feature 2')

# 범례 추가
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='steelblue', label='정상 (예측)'),
                   Patch(facecolor='red', label='이상 (예측)')]
fig.legend(handles=legend_elements, loc='lower center',
           ncol=2, fontsize=11, bbox_to_anchor=(0.5, -0.05))

plt.suptitle('Isolation Forest vs LOF 이상 탐지 비교', fontsize=14, y=1.02)
plt.tight_layout()
plt.show()
```

```output
=== Isolation Forest ===
              precision    recall  f1-score   support

          이상       0.80      0.80      0.80        20
          정상       0.99      0.99      0.99       300

    accuracy                           0.97       320
   macro avg       0.89      0.89      0.89       320
weighted avg       0.97      0.97      0.97       320

=== LOF ===
              precision    recall  f1-score   support

          이상       0.80      0.80      0.80        20
          정상       0.99      0.99      0.99       300

    accuracy                           0.97       320
   macro avg       0.89      0.89      0.89       320
weighted avg       0.97      0.97      0.97       320

Isolation Forest AUC: 0.9653
LOF AUC:              0.9570
```

![이상 탐지 알고리즘 비교 결과](figures/anomaly_detection_comparison.png)

*Figure 1: 이상 탐지 결과: Isolation Forest와 LOF의 이상 탐지 결정 경계 및 AUC 성능을 비교한다.*

### AutoEncoder 기반 이상 탐지

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# 간단한 AutoEncoder 정의
class AnomalyAutoEncoder(nn.Module):
    def __init__(self, input_dim, latent_dim=8):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim)
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z)

# 정상 데이터만으로 학습
X_normal_tensor = torch.FloatTensor(X_scaled[:300])
dataset = TensorDataset(X_normal_tensor)
loader = DataLoader(dataset, batch_size=64, shuffle=True)

model = AnomalyAutoEncoder(input_dim=2, latent_dim=1)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.MSELoss()

for epoch in range(100):
    for (batch,) in loader:
        recon = model(batch)
        loss = criterion(recon, batch)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

# 재구성 오차로 이상 점수 계산
X_all_tensor = torch.FloatTensor(X_scaled)
with torch.no_grad():
    recon = model(X_all_tensor)
    recon_errors = ((X_all_tensor - recon) ** 2).mean(dim=1).numpy()

# 임계값 설정: 정상 데이터 95 퍼센타일
threshold = np.percentile(recon_errors[:300], 95)
ae_pred = np.where(recon_errors > threshold, -1, 1)

print("=== AutoEncoder 기반 이상 탐지 ===")
print(classification_report(y_true, ae_pred, target_names=['이상', '정상']))
ae_auc = roc_auc_score(y_true == -1, recon_errors)
print(f"AutoEncoder AUC: {ae_auc:.4f}")
```

<!-- Execution error: ModuleNotFoundError: No module named 'torch' -->

위 코드를 실행하면 세 가지 방법의 결정 경계와 성능 지표를 직접 비교할 수 있다. **데이터 특성에 따라 어떤 방법이 최적인지 달라지므로**, 실무에서는 항상 여러 방법을 비교 실험한 뒤 선택하는 것이 바람직하다. 레이블이 전혀 없는 경우라도 도메인 지식을 바탕으로 몇 개의 검증 이상 사례를 수동으로 확보하면 정량 평가가 가능해진다.