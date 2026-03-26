## 개요

추천 시스템(Recommendation System)은 사용자가 관심을 가질 만한 아이템을 자동으로 제안하는 정보 필터링 기술입니다. 넷플릭스의 영화 추천, 아마존의 상품 추천, 유튜브의 동영상 추천은 모두 이 기술을 기반으로 하며, 각 플랫폼 매출의 상당 부분을 책임집니다. 실제로 넷플릭스 시청의 약 80%가 추천 알고리즘에서 발생하며, 아마존 매출의 35%가 추천 시스템에서 비롯된다고 알려져 있습니다.

추천 시스템은 크게 **협업 필터링(Collaborative Filtering)**, **콘텐츠 기반 필터링(Content-Based Filtering)**, 두 방식을 결합한 **하이브리드 방식**으로 구분됩니다. 최근에는 Matrix Factorization(행렬 분해) 기법과 딥러닝 기반 추천 모델이 주류를 이루고 있습니다.

---

## 수학적 배경

### 유사도 측정: 코사인 유사도

두 사용자 또는 두 아이템의 유사도를 측정할 때 코사인 유사도가 자주 활용됩니다.

$$sim(u, v) = \frac{u \cdot v}{\|u\| \|v\|} = \frac{\sum_{i} u_i v_i}{\sqrt{\sum_i u_i^2} \cdot \sqrt{\sum_i v_i^2}}$$

값이 1에 가까울수록 두 벡터의 방향이 같아 유사도가 높고, 0에 가까울수록 유사도가 낮습니다. 평점 데이터처럼 값의 편향이 있을 때는 **Pearson 상관계수**를 대신 쓰기도 합니다.

$$sim_{pearson}(u, v) = \frac{\sum_i (u_i - \bar{u})(v_i - \bar{v})}{\sqrt{\sum_i (u_i - \bar{u})^2} \cdot \sqrt{\sum_i (v_i - \bar{v})^2}}$$

### Matrix Factorization

유저-아이템 평점 행렬 $R \in \mathbb{R}^{m \times n}$ (m명의 유저, n개의 아이템)을 두 개의 저차원 행렬로 분해합니다.

$$R \approx P \cdot Q^T$$

여기서 $P \in \mathbb{R}^{m \times k}$ 는 유저 잠재 요인 행렬, $Q \in \mathbb{R}^{n \times k}$ 는 아이템 잠재 요인 행렬, $k$ 는 잠재 요인(latent factor)의 차원입니다.

유저 $u$ 의 아이템 $i$ 에 대한 예측 평점은 다음과 같습니다.

$$\hat{r}_{ui} = p_u \cdot q_i^T$$

학습 목적함수(정규화 포함)는 다음과 같이 정의됩니다.

$$\min_{P, Q} \sum_{(u,i) \in \mathcal{K}} (r_{ui} - p_u q_i^T)^2 + \lambda (\|p_u\|^2 + \|q_i\|^2)$$

### ALS (Alternating Least Squares)

ALS는 P와 Q를 번갈아 고정시키며 최적화하는 방법입니다. P를 고정하면 Q에 대한 목적함수가 볼록(convex)해져 닫힌 해(closed-form solution)를 구할 수 있습니다.

$$q_i = (P^T P + \lambda I)^{-1} P^T r_i$$

$$p_u = (Q^T Q + \lambda I)^{-1} Q^T r_u$$

이를 수렴할 때까지 반복합니다. ALS는 SGD에 비해 병렬화가 쉬워 대규모 분산 환경(Spark MLlib 등)에서 자주 사용됩니다.

---

## 알고리즘

### 1. 협업 필터링 (Collaborative Filtering, CF)

**"비슷한 사람들은 비슷한 것을 좋아한다"** 는 가정에 기반합니다.

- **User-based CF**: 타겟 유저와 유사한 유저들을 찾고, 그들이 높게 평가한 아이템을 추천합니다. 유저 수가 많아지면 계산 비용이 커지는 단점이 있습니다.
- **Item-based CF**: 타겟 아이템과 유사한 아이템들을 찾아 추천합니다. 아이템 수가 유저 수보다 적어 안정적이며, 아마존에서 사용하는 방식으로 유명합니다.

예측 평점 수식 (User-based):

$$\hat{r}_{ui} = \bar{r}_u + \frac{\sum_{v \in N(u)} sim(u,v) \cdot (r_{vi} - \bar{r}_v)}{\sum_{v \in N(u)} |sim(u,v)|}$$

### 2. 콘텐츠 기반 필터링 (Content-Based Filtering)

아이템의 속성(장르, 키워드, 설명 등)을 피처로 표현하고, 유저가 좋아한 아이템과 유사한 아이템을 추천합니다. 새 아이템에 대해서도 즉시 추천할 수 있다는 장점이 있지만, 유저의 취향 다양성을 반영하기 어렵습니다.

### 3. Matrix Factorization (SVD / ALS)

- **SVD(Singular Value Decomposition)**: 희소 행렬에 직접 적용하기 어려워, 관측된 평점만 사용하는 **Funk SVD** 변형이 실무에서 주로 쓰입니다.
- **ALS**: 분산 처리에 적합한 알고리즘으로, 암묵적 피드백(조회수, 클릭 등)에도 확장 가능합니다.

### 4. 하이브리드 추천 (Hybrid Recommendation)

CF와 콘텐츠 기반 필터링의 장점을 결합합니다. 예를 들어 MF 결과와 콘텐츠 유사도 점수를 가중 합산하거나, 딥러닝 모델로 두 방식의 표현을 함께 학습시키는 방식이 있습니다.

---

## Python 구현

### surprise 라이브러리를 활용한 SVD

```python
from surprise import SVD, Dataset, Reader, accuracy
from surprise.model_selection import train_test_split
import pandas as pd

# 데이터 준비 (user_id, item_id, rating)
ratings_df = pd.DataFrame({
    'user_id': [1, 1, 2, 2, 3, 3, 4],
    'item_id': [101, 102, 101, 103, 102, 104, 103],
    'rating':  [5.0, 3.0, 4.0, 2.0, 5.0, 4.0, 3.0]
})

reader = Reader(rating_scale=(1, 5))
dataset = Dataset.load_from_df(ratings_df[['user_id', 'item_id', 'rating']], reader)

train_data, test_data = train_test_split(dataset, test_size=0.2, random_state=42)

# SVD 모델 학습
model = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42)
model.fit(train_data)

# 평가
predictions = model.test(test_data)
print(f'RMSE: {accuracy.rmse(predictions):.4f}')
print(f'MAE:  {accuracy.mae(predictions):.4f}')

# 특정 유저에게 아이템 추천
def get_top_n_recommendations(model, user_id, all_item_ids, rated_item_ids, n=5):
    unrated_items = [iid for iid in all_item_ids if iid not in rated_item_ids]
    predictions = [(iid, model.predict(user_id, iid).est) for iid in unrated_items]
    predictions.sort(key=lambda x: x[1], reverse=True)
    return predictions[:n]

all_items = ratings_df['item_id'].unique().tolist()
user_rated = ratings_df[ratings_df['user_id'] == 1]['item_id'].tolist()
recs = get_top_n_recommendations(model, user_id=1, all_item_ids=all_items,
                                  rated_item_ids=user_rated, n=3)
print('추천 아이템:', recs)
```

<!-- Execution error: ModuleNotFoundError: No module named 'surprise' -->

### sklearn cosine_similarity 기반 Item-based CF

```python
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# 유저-아이템 행렬 생성
ratings = {
    'user_1': {'item_A': 5, 'item_B': 3, 'item_C': 0, 'item_D': 1},
    'user_2': {'item_A': 4, 'item_B': 0, 'item_C': 4, 'item_D': 1},
    'user_3': {'item_A': 1, 'item_B': 1, 'item_C': 5, 'item_D': 0},
    'user_4': {'item_A': 1, 'item_B': 0, 'item_C': 4, 'item_D': 5},
}

df = pd.DataFrame(ratings).T.fillna(0)  # shape: (users, items)
print('유저-아이템 행렬:')
print(df)

# 아이템 간 코사인 유사도 계산 (아이템을 행으로 전치)
item_matrix = df.values.T  # shape: (items, users)
item_sim = cosine_similarity(item_matrix)
item_sim_df = pd.DataFrame(item_sim, index=df.columns, columns=df.columns)
print('\n아이템 유사도 행렬:')
print(item_sim_df.round(3))

# 특정 아이템과 가장 유사한 아이템 추천
def get_similar_items(item_sim_df, item_id, top_n=2):
    sim_scores = item_sim_df[item_id].drop(item_id).sort_values(ascending=False)
    return sim_scores.head(top_n)

print('\nitem_A와 유사한 아이템:')
print(get_similar_items(item_sim_df, 'item_A', top_n=2))

# Item-based CF 예측 평점
def predict_rating_item_based(user_ratings, item_sim_df, target_item, top_n=2):
    rated_items = {item: r for item, r in user_ratings.items() if r > 0 and item != target_item}
    sim_scores = item_sim_df[target_item][list(rated_items.keys())]
    top_similar = sim_scores.nlargest(top_n)

    numerator = sum(top_similar[item] * rated_items[item] for item in top_similar.index)
    denominator = sum(abs(s) for s in top_similar)
    return numerator / denominator if denominator > 0 else 0

user1_ratings = ratings['user_1']
pred = predict_rating_item_based(user1_ratings, item_sim_df, target_item='item_C')
print(f'\nuser_1의 item_C 예측 평점: {pred:.2f}')
```

```output
유저-아이템 행렬:
        item_A  item_B  item_C  item_D
user_1       5       3       0       1
user_2       4       0       4       1
user_3       1       1       5       0
user_4       1       0       4       5

아이템 유사도 행렬:
        item_A  item_B  item_C  item_D
item_A   1.000   0.772   0.505   0.411
item_B   0.772   1.000   0.209   0.183
item_C   0.505   0.209   1.000   0.612
item_D   0.411   0.183   0.612   1.000

item_A와 유사한 아이템:
item_B    0.771589
item_C    0.504973
Name: item_A, dtype: float64

user_1의 item_C 예측 평점: 2.81
```

---

## 시각화

### 유저-아이템 행렬 히트맵

```python
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 유저-아이템 평점 행렬 (0은 미평가)
rating_matrix = np.array([
    [5, 3, 0, 1, 4],
    [4, 0, 4, 1, 0],
    [1, 1, 5, 0, 2],
    [0, 0, 4, 5, 3],
    [3, 4, 0, 0, 5],
])

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 1) 유저-아이템 행렬 시각화
mask = rating_matrix == 0
sns.heatmap(rating_matrix, annot=True, fmt='d', cmap='YlOrRd',
            mask=mask, linewidths=0.5,
            xticklabels=[f'Item {i+1}' for i in range(5)],
            yticklabels=[f'User {i+1}' for i in range(5)],
            ax=axes[0])
axes[0].set_title('유저-아이템 평점 행렬\n(0: 미평가)', fontsize=13)
axes[0].set_xlabel('아이템')
axes[0].set_ylabel('유저')

# 2) SVD 잠재 요인 공간 시각화 (2D)
np.random.seed(42)
U = np.random.randn(5, 2)   # 유저 잠재 벡터
V = np.random.randn(5, 2)   # 아이템 잠재 벡터

axes[1].scatter(U[:, 0], U[:, 1], c='steelblue', s=120, zorder=5, label='Users')
axes[1].scatter(V[:, 0], V[:, 1], c='tomato', s=120, marker='^', zorder=5, label='Items')

for i, (x, y) in enumerate(U):
    axes[1].annotate(f'U{i+1}', (x, y), textcoords='offset points', xytext=(6, 4))
for i, (x, y) in enumerate(V):
    axes[1].annotate(f'I{i+1}', (x, y), textcoords='offset points', xytext=(6, 4))

axes[1].axhline(0, color='gray', linewidth=0.5)
axes[1].axvline(0, color='gray', linewidth=0.5)
axes[1].set_title('잠재 요인 공간 (2D)', fontsize=13)
axes[1].set_xlabel('잠재 요인 1')
axes[1].set_ylabel('잠재 요인 2')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('recommendation_visualization.png', dpi=150, bbox_inches='tight')
plt.show()
```

![Recommendation-Systems Fig 1](/media/figures/outputs/recommendation-systems/recommendation-systems_fig_1.png)

---

## 실전 팁

### Cold Start 문제

새로운 유저나 새로운 아이템에 대해 기존 데이터가 없어 추천이 어려운 상황입니다.

- **새 유저**: 초기 온보딩에서 선호도를 수집하거나, 인기 아이템을 기반으로 추천
- **새 아이템**: 콘텐츠 기반 필터링으로 속성 기반 추천, 또는 메타데이터 활용
- **하이브리드 전환**: 데이터가 쌓이면 점진적으로 CF 비중을 높이는 앙상블 전략

### 희소성 (Sparsity) 처리

실제 유저-아이템 행렬은 99% 이상이 결측값인 경우가 많습니다.

- **암묵적 피드백(Implicit Feedback)** 활용: 클릭, 조회, 구매 기록 등을 0/1 신호로 변환
- **정규화**: L2 정규화($\lambda$)로 과적합 방지
- **차원 축소**: 잠재 요인 수 $k$를 적절히 설정해 노이즈 제거

### 평가 지표

| 지표 | 수식 | 특징 |
|------|------|------|
| RMSE | $\sqrt{\frac{1}{N}\sum(r_{ui}-\hat{r}_{ui})^2}$ | 평점 예측 오차 |
| MAE | $\frac{1}{N}\sum|r_{ui}-\hat{r}_{ui}|$ | 이상치에 덜 민감 |
| Precision@K | $\frac{\text{상위 K개 중 관련 아이템 수}}{K}$ | 정밀도 |
| Recall@K | $\frac{\text{상위 K개 중 관련 아이템 수}}{\text{전체 관련 아이템 수}}$ | 재현율 |
| nDCG@K | $\frac{DCG@K}{IDCG@K}$ | 순위 품질 반영 |

**nDCG(Normalized Discounted Cumulative Gain)** 는 추천 순위가 얼마나 잘 맞는지를 로그 함수로 할인하며 평가합니다.

$$DCG@K = \sum_{i=1}^{K} \frac{rel_i}{\log_2(i+1)}$$

### 신뢰도 vs 관련성 트레이드오프

- **인기 아이템 편향**: 자주 노출된 아이템은 데이터가 많아 정확하지만, 롱테일 아이템 추천이 약해집니다.
- **다양성(Diversity)**: 비슷한 아이템만 추천하면 사용자가 지루함을 느낄 수 있으므로, 유사도뿐 아니라 다양성 점수를 함께 최적화하는 MMR(Maximal Marginal Relevance) 등이 사용됩니다.
- **A/B 테스트**: 오프라인 평가 지표(RMSE, nDCG)가 좋아도 온라인 CTR/CVR 개선으로 이어지지 않을 수 있으므로, 실제 서비스 배포 전에 반드시 A/B 테스트를 수행해야 합니다.

---

## 정리

추천 시스템은 데이터의 희소성, Cold Start, 확장성이라는 세 가지 핵심 도전을 풀어야 하는 분야입니다. 협업 필터링은 직관적이고 강력하지만 희소성에 취약하며, Matrix Factorization은 이를 보완하면서 잠재 요인을 학습합니다. 실전에서는 콘텐츠 기반 정보와 CF를 결합한 하이브리드 방식, 그리고 딥러닝 기반 모델(Neural Collaborative Filtering, Two-Tower 등)로 발전하고 있습니다. 평가 시에는 오프라인 지표와 온라인 실험을 모두 활용해 실제 비즈니스 임팩트를 검증하는 것이 중요합니다.