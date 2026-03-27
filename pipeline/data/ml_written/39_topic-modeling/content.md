## 개요

수천, 수만 건의 뉴스 기사나 논문이 있을 때 사람이 직접 읽지 않고도 "이 문서들은 어떤 주제들로 이루어져 있는가?"를 파악할 수 있다면 얼마나 유용할까요? **토픽 모델링(Topic Modeling)**은 바로 이 질문에 답하는 비지도 학습(Unsupervised Learning) 기법입니다.

토픽 모델링의 핵심 가정은 **하나의 문서가 여러 주제(topic)의 혼합으로 구성되어 있고, 각 주제는 특정 단어들의 확률 분포로 표현된다**는 것입니다. 이를 통해 알고리즘은 문서 집합 전체를 분석해 반복적으로 함께 등장하는 단어 패턴을 찾아내고, 그것을 하나의 '토픽'으로 정의합니다.

대표적인 두 가지 방법론은 다음과 같습니다.

- **LDA (Latent Dirichlet Allocation)**: 확률적 생성 모델로, 문서와 단어 뒤에 숨겨진(잠재적인) 토픽 구조를 디리클레 분포를 활용해 추론합니다.
- **NMF (Non-negative Matrix Factorization)**: 문서-단어 행렬을 두 개의 비음수 행렬로 분해하여 토픽을 추출하는 대수적 접근법입니다.

---

## 수학적 배경

### LDA: 디리클레 분포와 생성 모델

LDA는 다음과 같은 두 가지 핵심 확률 분포를 사용합니다.

**1. 문서-토픽 분포 (Document-Topic Distribution)**

각 문서 $d$는 $K$개의 토픽에 대한 혼합 비율 $\theta_d$를 가집니다. 이 비율은 디리클레 분포에서 샘플링됩니다.

$$\theta_d \sim \text{Dir}(\alpha)$$

여기서 $\alpha$는 디리클레 분포의 하이퍼파라미터로, 값이 작을수록 문서가 소수의 토픽에 집중되고, 값이 클수록 여러 토픽에 고르게 분포합니다.

**2. 토픽-단어 분포 (Topic-Word Distribution)**

각 토픽 $k$는 어휘 $V$에 대한 단어 분포 $\phi_k$를 가집니다.

$$\phi_k \sim \text{Dir}(\beta)$$

$\beta$는 각 토픽 내 단어 분포의 집중도를 조절하는 하이퍼파라미터입니다.

**LDA의 완전한 생성 과정**은 다음과 같습니다.

$$P(w, z, \theta, \phi \mid \alpha, \beta) = \prod_{k=1}^{K} P(\phi_k \mid \beta) \prod_{d=1}^{D} P(\theta_d \mid \alpha) \prod_{n=1}^{N_d} P(z_{d,n} \mid \theta_d) P(w_{d,n} \mid \phi_{z_{d,n}})$$

### NMF: 비음수 행렬 분해

NMF는 문서-단어 행렬 $V \in \mathbb{R}^{D \times V}$를 다음과 같이 두 행렬의 곱으로 근사합니다.

$$V \approx W H$$

- $V$: $D \times V$ 문서-단어 행렬 (TF-IDF 또는 TF 값)
- $W$: $D \times K$ 문서-토픽 행렬 (각 문서의 토픽 가중치)
- $H$: $K \times V$ 토픽-단어 행렬 (각 토픽의 단어 가중치)

**비음수 제약 조건** ($W \geq 0$, $H \geq 0$)은 결과 해석을 직관적으로 만들어줍니다. 음수값 없이 '부분의 합'으로 전체를 표현하므로, 각 토픽이 단어들의 순수한 기여도로 해석됩니다.

목적 함수는 다음을 최소화하는 방향으로 학습됩니다.

$$\min_{W, H \geq 0} \| V - WH \|_F^2$$

---

![토픽-단어 히트맵: 각 토픽별 주요 단어의 확률 분포를 히트맵으로 시각화](figures/topic_word_heatmap.png)
*토픽-단어 히트맵: 각 토픽이 어떤 단어들로 구성되어 있는지 한눈에 파악할 수 있으며, 토픽 간 차별화된 단어 분포를 보여준다.*

## 알고리즘 상세

### LDA 학습 알고리즘

**Gibbs Sampling (깁스 샘플링)**은 LDA에서 가장 널리 사용되는 추론 방법입니다. MCMC 기반으로, 각 단어의 토픽 할당 $z_{d,n}$을 나머지 모든 단어의 할당이 주어진 조건에서 샘플링하며 반복합니다.

$$P(z_{d,n} = k \mid z_{-d,n}, w) \propto \frac{n_{d,k}^{-d,n} + \alpha}{n_{d,\cdot}^{-d,n} + K\alpha} \cdot \frac{n_{k,w_{d,n}}^{-d,n} + \beta}{n_{k,\cdot}^{-d,n} + V\beta}$$

**Variational Bayes (변분 베이즈)**는 사후 분포를 단순한 분포족으로 근사하여 최적화하는 방식으로, 대규모 데이터에서 더 빠르게 수렴합니다.

### NMF 학습 알고리즘

NMF는 **교번 최소제곱법(Alternating Least Squares, ALS)**으로 학습됩니다. $W$를 고정하고 $H$를 업데이트, 다시 $H$를 고정하고 $W$를 업데이트하는 과정을 비음수 제약을 유지하며 반복합니다.

### LDA vs NMF 비교

| 항목 | LDA | NMF |
|------|-----|-----|
| 접근 방식 | 확률적 생성 모델 | 대수적 행렬 분해 |
| 입력 | TF (빈도) | TF-IDF (권장) |
| 해석 | 확률로 해석 가능 | 가중치로 해석 |
| 속도 | 상대적으로 느림 | 빠름 |
| 토픽 경계 | 소프트 (중복 가능) | 더 명확한 경향 |
| 하이퍼파라미터 | $\alpha$, $\beta$, $K$ | $K$, 정규화 방식 |

---

## Python 구현

### 데이터 준비 및 벡터화

```python
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
import numpy as np

# 예시 문서 (실제로는 전처리된 텍스트 사용)
documents = [
    "machine learning deep learning neural network",
    "stock market finance investment portfolio",
    "python programming software development code",
    "neural network training gradient descent backpropagation",
    "bond yield interest rate inflation economy",
    "data science feature engineering model evaluation",
]

# LDA용: CountVectorizer (빈도 기반)
cv = CountVectorizer(max_df=0.95, min_df=2, stop_words='english')
X_counts = cv.fit_transform(documents)

# NMF용: TfidfVectorizer (TF-IDF 기반)
tfidf = TfidfVectorizer(max_df=0.95, min_df=2, stop_words='english')
X_tfidf = tfidf.fit_transform(documents)

print(f"문서 수: {X_counts.shape[0]}, 어휘 크기: {X_counts.shape[1]}")
```

```output
문서 수: 6, 어휘 크기: 2
```

### LDA 모델 학습

```python
# LDA 모델 초기화 및 학습
n_topics = 3

lda_model = LatentDirichletAllocation(
    n_components=n_topics,
    max_iter=20,
    learning_method='online',   # 'batch' 또는 'online'
    random_state=42,
    doc_topic_prior=0.1,        # alpha: 문서-토픽 집중도
    topic_word_prior=0.01       # beta: 토픽-단어 집중도
)
lda_model.fit(X_counts)

# 토픽별 상위 단어 출력
feature_names = cv.get_feature_names_out()

def print_top_words(model, feature_names, n_top_words=10):
    for topic_idx, topic in enumerate(model.components_):
        top_words = [feature_names[i] for i in topic.argsort()[:-n_top_words-1:-1]]
        print(f"토픽 #{topic_idx}: {' | '.join(top_words)}")

print("=== LDA 토픽 ===")
print_top_words(lda_model, feature_names)

# 문서별 토픽 분포 확인
doc_topic_dist = lda_model.transform(X_counts)
print(f"\n첫 번째 문서의 토픽 분포: {doc_topic_dist[0].round(3)}")
```

```output
=== LDA 토픽 ===
토픽 #0: network | neural
토픽 #1: neural | network
토픽 #2: network | neural

첫 번째 문서의 토픽 분포: [0.043 0.043 0.913]
```

### NMF 모델 학습

```python
# NMF 모델 초기화 및 학습
nmf_model = NMF(
    n_components=n_topics,
    init='nndsvd',              # 초기화 방법 ('random', 'nndsvd', 'nndsvda')
    max_iter=200,
    random_state=42,
    alpha_W=0.1,                # W 행렬 정규화
    alpha_H=0.1                 # H 행렬 정규화
)
nmf_model.fit(X_tfidf)

feature_names_tfidf = tfidf.get_feature_names_out()

print("=== NMF 토픽 ===")
print_top_words(nmf_model, feature_names_tfidf)

# 문서별 토픽 가중치 확인
doc_topic_weights = nmf_model.transform(X_tfidf)
print(f"\n첫 번째 문서의 토픽 가중치: {doc_topic_weights[0].round(3)}")
```

<!-- Execution error: ValueError: init = 'nndsvd' can only be used when n_components <= min(n_samples, n_features) -->

### 최적 토픽 수 결정 (Perplexity & Coherence)

```python
import matplotlib.pyplot as plt

# LDA Perplexity 기반 토픽 수 선택
topic_range = range(2, 15)
perplexities = []

for k in topic_range:
    lda = LatentDirichletAllocation(
        n_components=k, random_state=42,
        learning_method='batch', max_iter=30
    )
    lda.fit(X_counts)
    perplexities.append(lda.perplexity(X_counts))

plt.figure(figsize=(8, 4))
plt.plot(topic_range, perplexities, marker='o')
plt.xlabel('토픽 수 (K)')
plt.ylabel('Perplexity')
plt.title('LDA Perplexity vs 토픽 수')
plt.grid(True)
plt.tight_layout()
plt.savefig('lda_perplexity.png', dpi=150)
plt.show()

# 낮을수록 좋음, 그래프의 'elbow' 지점이 최적 K
print(f"최소 perplexity: {min(perplexities):.2f} (K={topic_range[np.argmin(perplexities)]})")
```

```output
최소 perplexity: 3.93 (K=2)
```

![Topic-Modeling Fig 1](/media/figures/outputs/topic-modeling/topic-modeling_fig_1.png)

---

![문서-토픽 분포: 각 문서가 어떤 토픽들의 혼합으로 구성되어 있는지 시각화](figures/document_topic_distribution.png)
*문서-토픽 분포: 각 문서는 여러 토픽의 혼합으로 표현되며, 문서별 토픽 비중 차이를 통해 문서 간 유사성과 차이를 파악할 수 있다.*

## 시각화

### pyLDAvis를 활용한 인터랙티브 시각화

```python
import pyLDAvis
import pyLDAvis.lda_model

# pyLDAvis 시각화 (Jupyter Notebook 환경)
pyLDAvis.enable_notebook()

vis_data = pyLDAvis.lda_model.prepare(
    lda_model,
    X_counts,
    cv,
    mds='tsne'          # 토픽 간 거리를 t-SNE로 배치
)
pyLDAvis.display(vis_data)

# HTML 파일로 저장
pyLDAvis.save_html(vis_data, 'lda_visualization.html')
print("시각화 저장 완료: lda_visualization.html")
```

<!-- Execution error: ModuleNotFoundError: No module named 'pyLDAvis' -->

pyLDAvis는 두 가지 핵심 시각을 제공합니다. 왼쪽 패널에서는 토픽 간 거리를 2D로 보여주며, 원이 클수록 해당 토픽의 문서 비중이 큽니다. 오른쪽 패널에서는 선택한 토픽의 상위 단어와 전체 빈도 대비 토픽 내 빈도를 비교합니다.

### 토픽별 상위 단어 바차트

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_top_words_bar(model, feature_names, n_top_words=10, title='토픽 상위 단어'):
    n_topics = model.components_.shape[0]
    fig, axes = plt.subplots(1, n_topics, figsize=(5 * n_topics, 5), sharey=False)

    for topic_idx, (ax, topic) in enumerate(zip(axes, model.components_)):
        top_indices = topic.argsort()[:-n_top_words-1:-1]
        top_words = [feature_names[i] for i in top_indices]
        top_weights = topic[top_indices]
        top_weights_norm = top_weights / top_weights.sum()

        bars = ax.barh(top_words[::-1], top_weights_norm[::-1], color='steelblue')
        ax.set_title(f'토픽 #{topic_idx}', fontsize=13, fontweight='bold')
        ax.set_xlabel('가중치')
        ax.tick_params(axis='y', labelsize=10)

    fig.suptitle(title, fontsize=15, y=1.02)
    plt.tight_layout()
    plt.savefig('topic_top_words.png', dpi=150, bbox_inches='tight')
    plt.show()

plot_top_words_bar(lda_model, feature_names, title='LDA 토픽 상위 단어')
plot_top_words_bar(nmf_model, feature_names_tfidf, title='NMF 토픽 상위 단어')
```

<!-- Execution error: NameError: name 'feature_names_tfidf' is not defined -->

### 워드클라우드 생성

```python
from wordcloud import WordCloud

def plot_topic_wordclouds(model, feature_names, n_topics):
    fig, axes = plt.subplots(1, n_topics, figsize=(6 * n_topics, 5))

    for topic_idx, (ax, topic) in enumerate(zip(axes, model.components_)):
        word_weights = {feature_names[i]: topic[i] for i in range(len(feature_names))}
        wc = WordCloud(
            width=400, height=300,
            background_color='white',
            colormap='Blues'
        ).generate_from_frequencies(word_weights)

        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(f'토픽 #{topic_idx}', fontsize=13)

    plt.tight_layout()
    plt.savefig('topic_wordclouds.png', dpi=150)
    plt.show()

plot_topic_wordclouds(lda_model, feature_names, n_topics)
```

<!-- Execution error: ModuleNotFoundError: No module named 'wordcloud' -->

---

## 실전 팁

### 1. 최적 토픽 수 선택

토픽 수 $K$는 모델의 품질에 결정적 영향을 미칩니다.

- **Perplexity**: LDA에서 $\log P(w)$를 기반으로 계산하며, 낮을수록 좋습니다. 단, 너무 낮으면 과적합을 의심해야 합니다.
- **Coherence Score**: 토픽 내 상위 단어들이 얼마나 의미적으로 연관되어 있는지 측정합니다 (`gensim` 라이브러리의 `CoherenceModel` 사용). **높을수록 좋습니다**.
- **실용적 방법**: $K$를 5, 10, 20, 30 등으로 늘려가며 토픽 목록을 사람이 직접 평가하는 **주제 해석 가능성(human interpretability)**이 가장 신뢰할 수 있는 기준입니다.

### 2. 전처리의 중요성

토픽 모델링 품질은 전처리에 크게 좌우됩니다.

- **불용어 제거**: 'the', 'is', '이', '가' 등 의미 없는 단어 제거
- **어간 추출 / 표제어 추출**: 'running', 'ran' → 'run'으로 통일
- **최소/최대 빈도 필터링**: `min_df`, `max_df` 설정으로 희귀어·지배어 제거
- **N-gram 고려**: 'machine learning', 'deep learning' 같은 복합어를 단일 단위로 처리

### 3. LDA vs NMF: 언제 무엇을 쓸까?

**LDA를 선택할 때**:
- 확률적 해석이 필요한 경우 ("이 문서는 37% 확률로 토픽 A")
- 문서가 여러 토픽을 동등하게 다루는 경우
- 하이퍼파라미터 튜닝 여건이 있는 경우

**NMF를 선택할 때**:
- 빠른 실행이 필요한 경우 (대용량 데이터)
- 토픽이 명확하게 구분되기를 기대하는 경우
- TF-IDF 가중치를 활용하고 싶은 경우
- 간단하고 해석 가능한 결과를 원할 때

**공통 권고사항**: 두 방법 모두 시도해보고, 토픽 해석 가능성을 기준으로 최종 선택하세요. 도메인 전문가의 피드백이 있다면 더욱 효과적입니다.

---

## 마무리

토픽 모델링은 레이블이 없는 방대한 텍스트 데이터를 탐색하는 강력한 출발점입니다. LDA는 확률적 생성 모델로서 이론적 탄탄함을, NMF는 빠른 속도와 명확한 토픽 분리를 제공합니다. 실제 프로젝트에서는 전처리에 충분한 시간을 투자하고, 여러 $K$ 값을 실험하며, 반드시 사람이 토픽 품질을 검토하는 과정을 거치는 것이 성공의 핵심입니다.