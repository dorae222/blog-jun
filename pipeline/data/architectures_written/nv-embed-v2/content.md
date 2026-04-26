<!-- infographic-hero -->
![NV-Embed v2 핵심 요약](figures/infographic.svg)

*Figure: NV-Embed v2 한 장 요약 인포그래픽*

# NV-Embed v2: LLM을 임베딩으로 변환한 MTEB 오픈 1위

## 개요

대형 언어모델은 단어 다음 토큰을 예측하기 위해 학습되었지만, 그 과정에서 풍부한 의미 표현을 부수적으로 획득한다. 그렇다면 LLM을 그대로 임베딩 모델로 쓸 수 있을까? 단순한 평균 풀링이나 마지막 토큰 풀링은 잘 작동하지 않는다. causal mask 때문에 토큰들이 서로를 충분히 참조하지 못하고, 풀링 방식이 검색 품질에 결정적이기 때문이다.

NV-Embed v2는 이 문제를 정면으로 해결했다. Mistral 7B를 백본으로 두되 causal mask를 제거해 양방향 attention으로 만들고, 마지막 hidden state를 풀링하기 위한 Latent Attention Layer를 도입한다. 결과는 MTEB v2 영어 평균 72.31점으로 오픈 모델 1위, 상용 OpenAI text-embedding-3-large(64.59), Cohere embed-english-v3(64.47)를 큰 차이로 앞선다. 4096차원, 32K 컨텍스트의 사양에 Hugging Face에서 가중치를 다운로드해 self-hosting할 수 있다는 점이 결합되어, 데이터 거버넌스가 중요한 산업에서 표준 오픈 임베딩 모델로 자리 잡았다.

## 아키텍처 상세

| 항목 | 값 |
|------|----|
| 출시일 | 2024년 9월 |
| 백본 | Mistral 7B (causal mask 제거 후 양방향) |
| 파라미터 | 약 7.85B |
| 출력 차원 | 4096 |
| 컨텍스트 | 32768 토큰 |
| 정규화 | RMSNorm |
| 활성함수 | SwiGLU |
| 위치 인코딩 | RoPE (base 늘림) |
| 풀링 | Latent Attention Layer |
| 라이선스 | NVIDIA AI Foundation Model License |
| MTEB v2 영어 | 72.31 |

Mistral 7B의 32개 트랜스포머 레이어를 통과한 마지막 hidden state $\mathbf{H} \in \mathbb{R}^{T \times d}$($T$는 토큰 수, $d=4096$)를 Latent Attention Layer로 단일 벡터 $\mathbf{z} \in \mathbb{R}^{4096}$으로 압축한다.

## 핵심 기법

### Latent Attention Layer

기존 LLM 기반 임베딩(GTE, E5-Mistral, BGE-Mistral)은 마지막 토큰의 hidden state를 그대로 임베딩으로 쓰거나(last-token pooling), 모든 토큰의 평균(mean pooling)을 사용했다. NV-Embed는 이 둘 모두 sub-optimal이라 보고, 학습 가능한 latent query 벡터들 $\mathbf{Q}_{\text{latent}} \in \mathbb{R}^{r \times d}$($r=512$ 제안)를 도입해 cross-attention으로 풀링한다.

$$
\mathbf{O} = \text{softmax}\left(\frac{\mathbf{Q}_{\text{latent}} \mathbf{H}^\top}{\sqrt{d}}\right) \mathbf{H}
$$

이후 $\mathbf{O} \in \mathbb{R}^{r \times d}$를 mean pooling하여 단일 벡터로 만든다. 이 방식은 입력 시퀀스 길이에 무관한 고정 크기 출력을 보장하며, latent query가 시퀀스 어디에서든 관련 정보를 추출하는 학습 가능한 풀러 역할을 한다. 단일 latent attention 레이어 추가만으로 평균 점수가 약 1점 이상 상승했다고 보고되었다.

### 양방향 Attention 변환

디코더 LLM은 causal mask로 미래 토큰을 보지 못하지만, 임베딩은 시퀀스 전체의 의미를 포착해야 한다. NV-Embed는 mask를 모두 1로 설정해 양방향 attention으로 만든 뒤 contrastive 학습을 수행한다. 이 단순한 수정만으로 검색 품질이 의미 있게 올라가며, 디코더 LLM이 인코더로 변신할 수 있음을 실증한다.

### 2단계 Contrastive Learning

| 단계 | 데이터 | 손실 |
|------|--------|------|
| 1단계 | MS MARCO, NQ, HotpotQA, Trivia QA 등 retrieval | InfoNCE + hard negatives |
| 2단계 | 1단계 + Amazon Reviews, classification, clustering, STS | 멀티태스크 InfoNCE |

InfoNCE 손실은 다음과 같다.

$$
\mathcal{L}_{\text{InfoNCE}} = -\frac{1}{N} \sum_{i=1}^{N} \log \frac{\exp(\mathbf{z}_q^i \cdot \mathbf{z}_p^i / \tau)}{\exp(\mathbf{z}_q^i \cdot \mathbf{z}_p^i / \tau) + \sum_{n \in \mathcal{N}_i} \exp(\mathbf{z}_q^i \cdot \mathbf{z}_n / \tau)}
$$

$\mathcal{N}_i$는 in-batch negatives와 hard negatives의 합집합이다. Hard negatives는 BM25로 채굴한 의미상 비슷하지만 정답이 아닌 문서로, 모델이 미세한 의미 차이를 학습하도록 강제한다. 2단계에서는 retrieval뿐 아니라 분류/클러스터링/STS 데이터를 섞어 일반화 능력을 끌어올렸고, 이것이 MTEB의 다양한 카테고리에서 균형 잡힌 점수를 만든다.

## 성능

MTEB v2 영어 리더보드 비교(2024-2025 기준).

| 모델 | 차원 | 평균 | Retrieval | Classification | Clustering | Reranking |
|------|------|------|-----------|----------------|------------|-----------|
| NV-Embed v2 | 4096 | 72.31 | 62.65 | 87.15 | 58.46 | 60.65 |
| BGE-en-ICL | 4096 | 71.24 | 61.67 | 88.62 | 57.51 | 60.13 |
| Stella-en-1.5B-v5 | 8192 | 71.19 | 61.01 | 87.63 | 57.69 | 60.40 |
| Gemini Embedding 001 | 3072 | 68.32 | 67.71 | 79.40 | 54.59 | 59.10 |
| voyage-3-large | 1024 | 65.10 | 62.40 | 78.20 | 51.30 | 57.80 |
| OpenAI text-embedding-3-large | 3072 | 64.59 | 55.44 | 75.45 | 49.01 | 56.15 |

분류와 클러스터링에서 압도적이고, retrieval에서도 최상위권이다. Gemini Embedding 001이 retrieval 카테고리에서는 더 높은 점수를 보이지만, 종합 평균에서는 NV-Embed v2가 앞선다. 이는 LLM 백본의 풍부한 의미 표현이 분류/클러스터링 같이 글로벌한 의미 이해가 필요한 태스크에서 특히 유리함을 보여준다.

### 차원 vs 성능 trade-off

NV-Embed v2는 Matryoshka 학습이 아니라서 잘라쓰기는 권장되지 않는다. 운영에서 인덱스 크기가 부담되면 PCA나 Random Projection으로 사후 차원 축소가 가능하지만, Matryoshka처럼 무료로 차원을 줄이지는 못한다. 4096차원은 RAG에서 인덱스 크기가 크고 검색 지연이 길어지므로, 대규모 시스템에서는 Gemini Embedding처럼 Matryoshka 모델과 비교해 최종 선택이 필요하다.

## 사용 사례

- **사내 RAG**: 데이터 거버넌스가 중요한 금융/의료/정부에서 self-hosted 임베딩으로 활용. vLLM 또는 TensorRT-LLM으로 추론 최적화.
- **분류 파이프라인**: 임베딩을 logistic regression이나 XGBoost 입력으로 사용하면 fine-tuning 없이도 높은 분류 성능을 얻을 수 있다.
- **클러스터링/topic modeling**: HDBSCAN이나 K-means로 대규모 코퍼스 자동 분류. 평균 58.46점은 OSS 임베딩 중 최상위.
- **연구 벤치마크**: MTEB의 표준 baseline. 새 임베딩 기법은 NV-Embed v2와 비교되어야 의미가 있다.
- **재랭킹 백본**: BGE Reranker나 Cohere Rerank와 결합한 2단계 검색에서 1단계 임베딩으로 활용.

## 코드 예제

`sentence-transformers`로 NV-Embed v2를 사용하는 기본 흐름이다.

```python
from sentence_transformers import SentenceTransformer
import torch

# 모델 로드 (Hugging Face에서 자동 다운로드, 약 16GB)
model = SentenceTransformer(
    "nvidia/NV-Embed-v2",
    trust_remote_code=True,
    device="cuda",
    model_kwargs={"torch_dtype": torch.bfloat16},
)

# instruction prefix가 retrieval 품질을 좌우한다
task_instruction = (
    "Given a question, retrieve passages that answer the question."
)

queries = ["RAG의 핵심 구성 요소는 무엇인가?"]
documents = [
    "RAG는 retriever와 generator로 구성된 검색-생성 파이프라인이다.",
    "Transformer는 attention 메커니즘으로 토큰 간 관계를 학습한다.",
    "임베딩 차원이 클수록 표현력은 늘지만 인덱스 비용도 늘어난다.",
]

# 쿼리는 instruction을 prepending
prefixed_queries = [
    f"Instruct: {task_instruction}\nQuery: {q}" for q in queries
]

# 문서는 instruction 없이 인코딩
query_embs = model.encode(prefixed_queries, normalize_embeddings=True)
doc_embs = model.encode(documents, normalize_embeddings=True)

# 코사인 유사도 (이미 정규화되었으므로 dot product = cosine)
scores = query_embs @ doc_embs.T
print(scores)
```

NV-Embed v2의 instruction-aware 학습 덕에 task-specific prompt를 정확히 포맷팅하는 것이 검색 품질을 좌우한다. Hugging Face 모델 카드에 태스크별 권장 instruction이 정리되어 있으니 참조해야 한다.

## 한계 및 의의

7.85B 파라미터로 inference 비용이 BGE-large(335M) 대비 25배 이상이고, 4096차원 임베딩은 인덱스 메모리 부담이 크다. 또한 NVIDIA AI Foundation Model License는 비상업 무료이지만 상업적 사용은 별도 협상이 필요해 스타트업이 production에 그대로 쓰기 어렵다. Matryoshka 학습이 빠져 있어 차원 축소도 자유롭지 못하다.

그럼에도 의의는 명확하다. 첫째, 디코더 LLM을 임베딩 모델로 변환할 때 양방향 attention과 Latent Attention Layer 두 가지가 결정적임을 실증했다. 둘째, 2단계 contrastive learning(retrieval 단독 → 멀티태스크 혼합) 전략이 MTEB 균형 점수를 만드는 표준 레시피임을 정립했다. 셋째, OSS 임베딩이 상용 OpenAI/Cohere를 평균 점수에서 앞서는 시대를 열었고, 이후 BGE-en-ICL, Stella, gte-Qwen2 등 LLM 기반 OSS 임베딩의 흐름을 가속화했다. RAG 인프라가 LLM 본체와 함께 발전하는 시대의 상징적 모델이다.

## 관련 문서

- [[mistral-7b|Mistral 7B]] - 백본 LLM
- [[bge-en-icl|BGE-en-ICL]] - In-Context Learning 기반 OSS 임베딩
- [[gemini-embedding-001|Gemini Embedding 001]] - 상용 임베딩 1위
- [[voyage-3-large|Voyage 3 Large]] - 도메인 특화 상용 임베딩
- [[bge-m3|BGE-M3]] - 다언어 dense + sparse 통합 임베딩
