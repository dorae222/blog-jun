## 개요

자연어 처리(NLP)는 컴퓨터가 인간의 언어를 이해하고 생성하는 분야입니다. GPT나 BERT 같은 대형 언어 모델이 등장하기 전, NLP는 전통적인 머신러닝 기법과 수작업 특징 공학(feature engineering)에 의존했습니다. 이 포스트에서는 텍스트를 수치 벡터로 변환하는 핵심 기법들을 단계적으로 살펴봅니다.

전통적 NLP 파이프라인의 핵심 질문은 하나입니다: **어떻게 텍스트를 모델이 처리할 수 있는 숫자로 바꿀 것인가?** Bag-of-Words(BoW)처럼 단순한 빈도 기반 표현부터 Word2Vec처럼 의미적 관계를 포착하는 분산 표현(distributed representation)까지, 각 방법은 서로 다른 트레이드오프를 갖습니다.

---

## 수학적 배경

### TF-IDF

TF-IDF(Term Frequency–Inverse Document Frequency)는 단어의 중요도를 문서 내 빈도와 전체 문서 집합에서의 희귀도를 조합해 측정합니다.

$$tf\text{-}idf(t, d, D) = tf(t, d) \cdot \log\frac{|D|}{df(t)}$$

- $tf(t, d)$: 문서 $d$ 내에서 단어 $t$의 출현 빈도
- $|D|$: 전체 문서 수
- $df(t)$: 단어 $t$가 등장하는 문서 수

IDF 항은 "the", "is" 같은 일반적 단어의 가중치를 낮추고, 해당 문서에서만 자주 나타나는 전문 용어의 가중치를 높입니다. 실무에서는 분모에 1을 더해 0 나누기를 방지하는 스무딩(smoothing)을 적용합니다.

### Word2Vec 목적함수

Word2Vec은 주변 단어(context)를 이용해 단어의 밀집 벡터(dense vector)를 학습합니다.

**CBOW (Continuous Bag-of-Words)**: 주변 단어들로 중심 단어를 예측합니다.

$$\mathcal{L}_{CBOW} = -\log P(w_t \mid w_{t-c}, \ldots, w_{t-1}, w_{t+1}, \ldots, w_{t+c})$$

**Skip-gram**: 중심 단어로 주변 단어들을 예측합니다.

$$\mathcal{L}_{SG} = -\sum_{-c \leq j \leq c,\, j \neq 0} \log P(w_{t+j} \mid w_t)$$

소프트맥스 계산 비용을 줄이기 위해 **Negative Sampling**을 사용합니다. $k$개의 노이즈 단어를 샘플링하여 이진 분류 문제로 전환합니다.

$$\mathcal{L}_{NS} = \log \sigma(\mathbf{v}_{w_O}^\top \mathbf{v}_{w_I}) + \sum_{i=1}^{k} \mathbb{E}_{w_i \sim P_n(w)}\left[\log \sigma(-\mathbf{v}_{w_i}^\top \mathbf{v}_{w_I})\right]$$

### 코사인 유사도

두 단어 벡터 간의 의미적 유사도는 코사인 유사도로 측정합니다.

$$\cos(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$

코사인 유사도는 벡터의 크기가 아닌 방향에 의존하기 때문에, 문서 길이에 무관한 비교가 가능합니다.

---

![TF-IDF 시각화: 문서-단어 TF-IDF 가중치 행렬의 히트맵 표현](figures/tfidf_visualization.png)
*TF-IDF 시각화: 각 문서에서 단어의 TF-IDF 가중치를 히트맵으로 표현하면 문서별 핵심 키워드를 직관적으로 파악할 수 있다.*

## 알고리즘

### 1. Bag-of-Words (BoW)

BoW는 텍스트를 단어 빈도의 벡터로 표현하는 가장 단순한 방법입니다. 단어 순서와 문법 구조를 무시하고 오직 단어의 등장 여부/빈도만 고려합니다.

- **장점**: 구현이 단순하고 계산 비용이 낮음
- **단점**: 문맥 정보 손실, 고차원 희소(sparse) 행렬, OOV(Out-of-Vocabulary) 문제

### 2. TF-IDF

BoW의 단순 빈도를 개선하여 단어의 문서 내 중요도를 반영합니다. `sklearn`의 `TfidfVectorizer`로 원-라인 구현이 가능합니다.

### 3. Word2Vec (CBOW / Skip-gram / Negative Sampling)

Google이 2013년 발표한 Word2Vec은 밀집 임베딩(dense embedding)의 시대를 열었습니다. 단어들이 의미적으로 유사하면 벡터 공간에서도 가깝게 위치합니다.

- `king - man + woman ≈ queen` 같은 선형 유추(analogy) 관계가 벡터 연산으로 표현됩니다.
- **CBOW**: 학습 속도가 빠르고 자주 등장하는 단어에 유리
- **Skip-gram**: 희귀 단어 처리에 강하고 데이터가 적을 때 유리

### 4. GloVe (Global Vectors)

Stanford가 제안한 GloVe는 전역 단어-단어 동시 등장(co-occurrence) 행렬을 이용합니다. Word2Vec의 지역적 문맥 창(local window)과 달리, 전체 코퍼스의 통계를 활용하여 안정적인 임베딩을 학습합니다.

### 5. fastText

Facebook AI가 개발한 fastText는 단어를 character n-gram의 합으로 표현합니다. 예를 들어 "apple"은 `<ap`, `app`, `ppl`, `ple`, `le>` 등의 n-gram으로 분해됩니다.

- **OOV 처리**: 학습 어휘에 없는 단어도 n-gram으로 표현 가능
- **형태소 풍부 언어**: 한국어, 독일어 등에서 특히 효과적

### 6. 텍스트 분류 파이프라인

전통적 NLP 분류 파이프라인은 다음 단계로 구성됩니다.

1. 텍스트 수집 및 레이블링
2. 전처리 (소문자화, 특수문자 제거, 토크나이징, 불용어 제거)
3. 특징 추출 (TF-IDF 또는 임베딩 평균)
4. 분류기 학습 (로지스틱 회귀, SVM, 나이브 베이즈)
5. 평가 (Accuracy, F1-score, 혼동 행렬)

---

## Python 구현

### TF-IDF 벡터화 및 텍스트 분류

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import numpy as np

# 예시 데이터 (감성 분류)
corpus = [
    "이 영화 정말 재미있어요",
    "최고의 작품입니다 강추",
    "시간 낭비 별로예요",
    "너무 지루하고 실망스러운 영화",
    "배우들 연기가 훌륭합니다",
    "스토리가 엉망이에요",
]
labels = [1, 1, 0, 0, 1, 0]  # 1: 긍정, 0: 부정

X_train, X_test, y_train, y_test = train_test_split(
    corpus, labels, test_size=0.33, random_state=42
)

# TF-IDF + Logistic Regression 파이프라인
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        analyzer="char_wb",   # 한국어에는 형태소 단위보다 문자 n-gram이 유용
        ngram_range=(2, 4),
        min_df=1,
        sublinear_tf=True     # log(1 + tf) 스케일링
    )),
    ("clf", LogisticRegression(max_iter=1000, C=1.0))
])

pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
print(classification_report(y_test, y_pred, target_names=["부정", "긍정"]))
```

```output
precision    recall  f1-score   support

          부정       0.00      0.00      0.00       0.0
          긍정       0.00      0.00      0.00       2.0

    accuracy                           0.00       2.0
   macro avg       0.00      0.00      0.00       2.0
weighted avg       0.00      0.00      0.00       2.0
```

### gensim Word2Vec 학습

```python
from gensim.models import Word2Vec
from konlpy.tag import Okt  # 한국어 형태소 분석기

okt = Okt()

def tokenize(text):
    """한국어 명사+동사 추출"""
    return okt.morphs(text, stem=True)

# 코퍼스 토크나이징
tokenized_corpus = [tokenize(doc) for doc in corpus]

# Word2Vec 학습
model = Word2Vec(
    sentences=tokenized_corpus,
    vector_size=100,    # 임베딩 차원
    window=5,           # 문맥 창 크기
    min_count=1,        # 최소 빈도 (실제론 5 이상 권장)
    sg=1,               # 0: CBOW, 1: Skip-gram
    negative=5,         # Negative Sampling 수
    epochs=10,
    seed=42
)

# 유사 단어 검색
if "영화" in model.wv:
    similar = model.wv.most_similar("영화", topn=5)
    print("'영화'와 유사한 단어:", similar)

# 단어 유추
# model.wv.most_similar(positive=["왕", "여성"], negative=["남성"])
```

<!-- Execution error: ModuleNotFoundError: No module named 'gensim' -->

### TF-IDF 벡터화 후 임베딩 평균으로 분류

```python
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

class Word2VecTransformer(BaseEstimator, TransformerMixin):
    """gensim Word2Vec 모델을 sklearn 파이프라인에 통합"""

    def __init__(self, w2v_model, tokenizer):
        self.w2v_model = w2v_model
        self.tokenizer = tokenizer

    def _doc_to_vec(self, doc):
        tokens = self.tokenizer(doc)
        vecs = [
            self.w2v_model.wv[t]
            for t in tokens
            if t in self.w2v_model.wv
        ]
        return np.mean(vecs, axis=0) if vecs else np.zeros(self.w2v_model.vector_size)

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return np.array([self._doc_to_vec(doc) for doc in X])

# Word2Vec + Logistic Regression 파이프라인
w2v_pipeline = Pipeline([
    ("w2v", Word2VecTransformer(model, tokenize)),
    ("clf", LogisticRegression(max_iter=1000))
])

w2v_pipeline.fit(X_train, y_train)
print("W2V 파이프라인 정확도:", w2v_pipeline.score(X_test, y_test))
```

<!-- Execution error: NameError: name 'model' is not defined -->

---

![Zipf 법칙: 자연어 텍스트에서 단어 빈도와 순위의 멱법칙 관계](figures/zipf_law.png)
*Zipf 법칙: 소수의 단어가 전체 텍스트의 대부분을 차지하고, 대다수의 단어는 극히 드물게 등장하는 멱법칙 분포를 따른다.*

## 시각화

### 단어 벡터 t-SNE 시각화

```python
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from sklearn.manifold import TSNE
import numpy as np

# 한국어 폰트 설정 (Mac: AppleGothic, Linux: NanumGothic)
plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False

# 학습된 단어 벡터 추출
words = list(model.wv.index_to_key[:50])  # 상위 50개 단어
vectors = np.array([model.wv[w] for w in words])

# t-SNE로 2차원 축소
tsne = TSNE(n_components=2, random_state=42, perplexity=10, n_iter=1000)
vectors_2d = tsne.fit_transform(vectors)

# 시각화
fig, ax = plt.subplots(figsize=(12, 8))
ax.scatter(vectors_2d[:, 0], vectors_2d[:, 1], alpha=0.6, s=80)

for i, word in enumerate(words):
    ax.annotate(word, (vectors_2d[i, 0], vectors_2d[i, 1]),
                fontsize=9, alpha=0.8)

ax.set_title("Word2Vec 단어 벡터 t-SNE 시각화", fontsize=14)
ax.set_xlabel("t-SNE 1")
ax.set_ylabel("t-SNE 2")
plt.tight_layout()
plt.savefig("word2vec_tsne.png", dpi=150, bbox_inches="tight")
plt.show()
```

<!-- Execution error: NameError: name 'model' is not defined -->

### 단어 유사도 히트맵

```python
import seaborn as sns

# 관심 단어 선택
target_words = ["영화", "배우", "스토리", "음악", "감독", "재미"]

# 유사도 행렬 계산
valid_words = [w for w in target_words if w in model.wv]
n = len(valid_words)
sim_matrix = np.zeros((n, n))

for i, w1 in enumerate(valid_words):
    for j, w2 in enumerate(valid_words):
        sim_matrix[i, j] = model.wv.similarity(w1, w2)

# 히트맵 시각화
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(
    sim_matrix,
    xticklabels=valid_words,
    yticklabels=valid_words,
    annot=True,
    fmt=".2f",
    cmap="RdYlGn",
    vmin=-1, vmax=1,
    ax=ax
)
ax.set_title("단어 간 코사인 유사도 히트맵", fontsize=13)
plt.tight_layout()
plt.savefig("word_similarity_heatmap.png", dpi=150, bbox_inches="tight")
plt.show()
```

<!-- Execution error: NameError: name 'model' is not defined -->

---

## 실전 팁

### 1. 전처리: Tokenization & Stopwords

한국어 NLP에서 전처리는 영어보다 까다롭습니다. 교착어 특성상 형태소 분석이 필수적입니다.

- **형태소 분석기 선택**: KoNLPy의 `Okt`(빠름), `Kkma`(정확), `Mecab`(빠르고 정확, 별도 설치 필요)
- **불용어 처리**: 조사, 어미, 접속사 등을 제거합니다. 한국어 불용어 리스트는 직접 구축하거나 오픈소스 목록을 활용합니다.
- **정규화**: 반복 문자 제거 (`ㅋㅋㅋㅋ→ㅋㅋ`), 이모지 처리, URL 제거

```python
import re

def preprocess_ko(text):
    text = re.sub(r"http\S+", "", text)          # URL 제거
    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", "", text)  # 특수문자 제거
    text = re.sub(r"(.)\\1{2,}", r"\\1\\1", text)    # 반복 문자 정규화
    return text.strip()
```

### 2. OOV (Out-of-Vocabulary) 처리

- **TF-IDF**: 훈련 어휘에 없는 단어는 무시됩니다. `min_df`를 낮추거나 character n-gram을 사용합니다.
- **Word2Vec**: `<UNK>` 토큰을 추가하거나, 유사 단어 벡터의 평균으로 대체합니다.
- **fastText**: n-gram 기반이므로 OOV 단어도 서브워드로 표현 가능합니다. 한국어 OOV 처리에 가장 강건합니다.

### 3. 임베딩 차원 선택

| 데이터 규모 | 권장 차원 | 비고 |
|---|---|---|
| 소규모 (~10만 문장) | 50–100 | 과적합 방지 |
| 중규모 (~100만 문장) | 100–200 | 표준 설정 |
| 대규모 (~1억 문장 이상) | 200–300 | GloVe, fastText 사전학습 활용 |

차원이 클수록 표현력이 높아지지만, 훈련 데이터가 충분하지 않으면 오히려 성능이 낮아집니다. 경험적으로 50~200 사이에서 교차 검증으로 선택합니다.

### 4. 딥러닝 임베딩과 비교

| 특성 | Word2Vec / GloVe | BERT / RoBERTa |
|---|---|---|
| 문맥 독립성 | 단어마다 하나의 고정 벡터 | 문장에 따라 동적으로 변하는 벡터 |
| 다의어 처리 | 어려움 ("배" = 과일/신체/교통수단 구분 불가) | 가능 (문맥 반영) |
| 학습 비용 | 낮음 | 높음 (GPU 필수) |
| 소규모 데이터 | 오히려 안정적 | 파인튜닝에 충분한 데이터 필요 |
| 해석 가능성 | 상대적으로 높음 | 낮음 (블랙박스) |

전통적 임베딩은 계산 자원이 제한된 환경이나, 빠른 프로토타이핑, 도메인 특화 소규모 데이터셋에서 여전히 경쟁력이 있습니다.

---

## 정리

전통적 NLP 기법들은 딥러닝 시대에도 여전히 실용적입니다. TF-IDF는 검색 엔진의 기본 구성 요소로 사용되고, Word2Vec은 추천 시스템의 아이템 임베딩에 광범위하게 활용됩니다. 핵심은 **데이터 규모, 계산 자원, 정확도 요구사항**에 맞는 방법을 선택하는 것입니다. 다음 단계로는 토픽 모델링(LDA), 추천 시스템, 차원 축소(t-SNE/UMAP)와의 조합을 탐구해 보세요.