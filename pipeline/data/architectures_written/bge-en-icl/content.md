<!-- infographic-hero -->
![BGE-en-ICL 핵심 요약](figures/infographic.svg)

*Figure: BGE-en-ICL 한 장 요약 인포그래픽*

# BGE-en-ICL: In-Context Learning을 임베딩으로 가져온 BAAI 오픈 모델

## 개요

In-Context Learning(ICL)은 LLM의 핵심 능력 중 하나다. 프롬프트에 몇 가지 예제를 보여주면 모델이 task의 패턴을 추론해 새 입력에 적용한다. 그런데 임베딩 모델은 이 메커니즘을 활용해본 적이 없었다. 임베딩은 보통 단일 텍스트를 단일 벡터로 매핑하는 결정적 함수이고, prompt가 있다면 instruction 한 줄 정도였다.

2024년 9월 BAAI가 공개한 BGE-en-ICL은 이 가정을 깬다. 쿼리 앞에 task instruction과 함께 few-shot 예제를 prepending하면 임베딩이 task-aware하게 변하면서 검색 품질이 추가로 올라간다. Mistral 7B 백본, 4096차원, 8K 컨텍스트, MIT 라이선스. MTEB v2 영어 평균 71.24점으로 NV-Embed v2(72.31)에 근소하게 뒤지지만, 분류 카테고리에서는 88.62점으로 더 우수하다. 무엇보다 MIT 라이선스로 상업적 사용에 제약이 없어, NVIDIA 라이선스가 부담스러운 스타트업에 표준 OSS 임베딩 후보로 자리 잡았다.

## 아키텍처 상세

| 항목 | 값 |
|------|----|
| 출시일 | 2024년 9월 |
| 백본 | Mistral 7B (양방향 attention) |
| 파라미터 | 약 7.11B |
| 출력 차원 | 4096 |
| 컨텍스트 | 8192 토큰 |
| 정규화 | RMSNorm |
| 활성함수 | SwiGLU |
| 위치 인코딩 | RoPE |
| 풀링 | last-token pooling |
| 라이선스 | MIT |
| MTEB v2 영어 | 71.24 |

NV-Embed v2와 같은 Mistral 7B 백본을 쓰지만, 풀링은 단순한 last-token pooling을 유지하고 추론 시점의 prompt formatting에 차별점을 둔다. 마지막 토큰의 hidden state $\mathbf{h}_T \in \mathbb{R}^{4096}$를 L2 정규화하여 임베딩으로 사용한다.

## 핵심 기법

### In-Context Learning 임베딩

BGE-en-ICL의 입력 prompt 형식은 다음과 같다.

```
<instruction>
<example_1_query>\t<example_1_response>
<example_2_query>\t<example_2_response>
...
<example_k_query>\t<example_k_response>
<query>
```

여기서 `\t`는 탭 구분자이고, response는 문서 또는 정답 텍스트의 짧은 요약이다. 모델은 학습 시점에 이런 포맷의 입력을 본 적이 있어, few-shot 예제로부터 task의 의도(검색? 분류? 유사도? 클러스터링?)와 표현 스타일(짧은 답변? 긴 패시지?)을 추론한다. 결과적으로 같은 쿼리라도 demo가 다르면 임베딩이 다르게 나오고, 잘 선택된 demo는 zero-shot 대비 평균 1~2점 추가 향상을 만든다.

이는 텍스트 LLM의 ICL이 임베딩 영역으로 확장된 것이다. instruction-only 모델(e5-instruct, Gemini Embedding의 task type)에서 한 단계 더 나아가, 자유 형식의 demo로 임베딩 동작을 조절할 수 있다.

### 양방향 Attention과 Last-Token Pooling

NV-Embed와 마찬가지로 Mistral 7B의 causal mask를 제거해 양방향으로 만들지만, 풀링은 last-token pooling을 그대로 유지한다. 이유는 ICL prompt에서 마지막 토큰이 쿼리의 마지막 토큰이고, 양방향 attention 덕에 이 토큰이 시퀀스 전체(instruction + demos + query)의 정보를 모두 흡수하기 때문이다. Latent Attention Layer 같은 추가 모듈 없이도 last-token이 충분한 풀러 역할을 한다는 가정이다.

### Contrastive Learning과 Hard Negatives

학습 손실은 표준 InfoNCE다.

$$
\mathcal{L}_{\text{InfoNCE}} = -\frac{1}{N} \sum_{i=1}^{N} \log \frac{\exp(\mathbf{z}_q^i \cdot \mathbf{z}_p^i / \tau)}{\exp(\mathbf{z}_q^i \cdot \mathbf{z}_p^i / \tau) + \sum_{n \in \mathcal{N}_i} \exp(\mathbf{z}_q^i \cdot \mathbf{z}_n / \tau)}
$$

특이점은 $\mathbf{z}_q^i$가 ICL prompt를 통과한 임베딩이라는 것이다. 학습 시 batch마다 query에 demo를 동적으로 sampling하여 prepending하고, 이 demo가 다양한 task signal을 제공하도록 큐레이팅한다. 이로써 모델은 demo 형식에 강건해지고, 추론 시점에 사용자가 demo를 새로 구성해도 task signal을 안정적으로 추출한다.

### 학습 단계

| 단계 | 데이터 | 핵심 |
|------|--------|------|
| 1단계 | 800M 약지도 텍스트 쌍 | 표현 공간 사전학습 |
| 2단계 | NLI, MS MARCO, NQ 등 | instruction tuning + InfoNCE |
| 3단계 | task-specific demo formatting | ICL signal 학습 |

## 성능

MTEB v2 영어 리더보드(2024-2025).

| 모델 | 차원 | 평균 | Retrieval | Classification | Clustering |
|------|------|------|-----------|----------------|------------|
| NV-Embed v2 | 4096 | 72.31 | 62.65 | 87.15 | 58.46 |
| BGE-en-ICL | 4096 | 71.24 | 61.67 | 88.62 | 57.51 |
| Stella-en-1.5B-v5 | 8192 | 71.19 | 61.01 | 87.63 | 57.69 |
| bge-large-en-v1.5 | 1024 | 64.23 | 54.29 | 75.97 | 46.08 |
| Gemini Embedding 001 | 3072 | 68.32 | 67.71 | 79.40 | 54.59 |

BGE-en-ICL이 분류에서 88.62점으로 NV-Embed v2의 87.15보다 높다. 이는 ICL demo가 분류 task의 클래스 분포를 모델에 직접 전달하여 임베딩이 클래스 분리에 유리하게 정렬되기 때문이다.

### few-shot 개수에 따른 성능

| Demo 개수 | 평균 점수 |
|-----------|-----------|
| 0 (zero-shot) | 70.05 |
| 1 | 70.62 |
| 2 | 71.10 |
| 4 | 71.24 |
| 8 | 71.05 (소폭 감소) |

4-shot 부근이 sweet spot이고, 8-shot 이상은 prompt가 너무 길어져 query 정보가 희석된다. 8K 컨텍스트의 절반 가까이를 demo가 차지하면 임베딩 품질이 오히려 떨어진다.

## 사용 사례

- **task-specific RAG**: 검색 task별로 다른 demo를 미리 준비하여 같은 모델로 다양한 도메인을 커버.
- **분류 파이프라인**: 클래스별 대표 예제를 demo로 넣어 zero-shot 분류 정확도 향상.
- **상업 자유도가 필요한 OSS 인프라**: MIT 라이선스로 SaaS 제품 내장 자유.
- **기존 BGE 시리즈 업그레이드**: bge-large-en-v1.5(335M, 1024차원)에서 더 높은 품질이 필요할 때 BGE-en-ICL로 전환.

## 코드 예제

`sentence-transformers` 또는 transformers로 BGE-en-ICL을 사용하는 흐름이다.

```python
from sentence_transformers import SentenceTransformer
import torch

model = SentenceTransformer(
    "BAAI/bge-en-icl",
    trust_remote_code=True,
    device="cuda",
    model_kwargs={"torch_dtype": torch.bfloat16},
)

# task instruction과 few-shot demo
instruction = (
    "Given a question, retrieve passages that answer the question."
)
demos = [
    ("What is RAG?",
     "RAG combines a retriever and a generator for knowledge-grounded answers."),
    ("How does Transformer work?",
     "Transformer uses self-attention to model token interactions."),
]

def format_query(query, instruction, demos):
    demo_str = "\n".join([f"{q}\t{a}" for q, a in demos])
    return f"<instruct>{instruction}\n{demo_str}\n<query>{query}"

queries = ["임베딩 모델의 차원은 어떻게 정해지는가?"]
documents = [
    "임베딩 차원은 모델 학습 시 hidden_dim으로 결정되며, 큰 차원은 표현력을 높인다.",
    "Transformer는 multi-head attention과 feed-forward 레이어로 구성된다.",
    "RAG는 외부 지식 검색 후 LLM에 컨텍스트로 주입한다.",
]

prefixed_queries = [format_query(q, instruction, demos) for q in queries]

# 쿼리는 ICL prompt, 문서는 raw 텍스트로 인코딩
query_embs = model.encode(prefixed_queries, normalize_embeddings=True)
doc_embs = model.encode(documents, normalize_embeddings=True)

scores = query_embs @ doc_embs.T
print(scores)
```

demo는 task와 도메인에 맞게 큐레이팅되어야 효과가 있다. 잘못된 demo(엉뚱한 도메인 또는 형식 불일치)는 오히려 zero-shot보다 성능을 떨어뜨릴 수 있다.

## 한계 및 의의

7.11B 파라미터로 inference 비용이 BGE 시리즈의 경량 모델 대비 크고, ICL prompt가 길어질수록 처리 시간이 비례해 늘어난다. 또한 demo 큐레이션이 사용자 책임이고, 부적절한 demo는 성능을 깎는다. last-token pooling은 단순하지만 시퀀스 매우 길 때 표현력 손실 가능성이 있어 32K 컨텍스트로 확장하지 못했다.

그럼에도 의의는 분명하다. 첫째, 임베딩 모델이 결정적 함수에서 prompt-conditioned 함수로 진화할 수 있음을 실증했다. 둘째, MIT 라이선스로 상업 자유도가 높은 OSS 임베딩 중 최상위 성능을 제공해 NVIDIA 라이선스 부담을 피하려는 사용자에게 명확한 대안을 제시했다. 셋째, BGE 시리즈의 진화 경로(bge-large → bge-m3 → bge-en-ICL)에서 ICL이 차세대 임베딩의 핵심 패러다임임을 천명했다. 향후 임베딩 모델은 단일 벡터 함수가 아니라 prompt-aware adapter로 발전할 가능성이 높고, BGE-en-ICL은 그 시작점이다.

## 관련 문서

- [[mistral-7b|Mistral 7B]] - 백본 LLM
- [[bge-m3|BGE-M3]] - 다언어 dense + sparse 통합 임베딩
- [[nv-embed-v2|NV-Embed v2]] - 오픈 모델 MTEB 평균 1위
- [[gemini-embedding-001|Gemini Embedding 001]] - 상용 임베딩 1위
- [[stella|Stella-en-1.5B-v5]] - 또 다른 OSS 고성능 임베딩
