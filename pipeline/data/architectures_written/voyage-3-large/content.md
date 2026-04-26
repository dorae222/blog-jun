<!-- infographic-hero -->
![Voyage 3 Large 핵심 요약](figures/infographic.svg)

*Figure: Voyage 3 Large 한 장 요약 인포그래픽*

# Voyage 3 Large: 도메인 특화와 Matryoshka로 비용 효율을 잡은 상용 임베딩

## 개요

상용 임베딩 시장은 OpenAI, Cohere, Google 같은 대형 빅테크가 주도해 왔지만, Voyage AI는 임베딩과 reranker만 집중적으로 만드는 전문 스타트업으로 시작해 의미 있는 차별화를 만들었다. 2024년 MongoDB가 인수하여 MongoDB Atlas Vector Search와 깊게 통합되었고, 2025년 1월 공개된 Voyage 3 Large는 MTEB 종합 65.1점으로 NV-Embed v2(72.31)에는 못 미치지만 상용 라이벌인 OpenAI text-embedding-3-large(64.59), Cohere embed-english-v3(64.47)를 0.3-0.5점 우위로 앞섰다.

차별점은 세 가지다. 첫째, Matryoshka 학습으로 256/512/1024/2048 차원을 모두 지원하여 인덱스 비용을 적극 조절한다. 둘째, int8과 binary 양자화를 공식 제공해 인덱스 크기를 4배에서 32배까지 줄일 수 있다. 셋째, 도메인 특화 변형 모델군(voyage-finance-2, voyage-law-2, voyage-code-3)이 일반 임베딩 대비 도메인 retrieval에서 5-10% 추가 향상을 보인다. 가격은 $0.06/M tokens로 OpenAI의 절반 수준이라 비용 효율이 가장 큰 매력이다.

## 아키텍처 상세

| 항목 | 값 |
|------|----|
| 출시일 | 2025년 1월 |
| 백본 | 비공개 (transformer 기반 추정) |
| 출력 차원 | 256/512/1024/2048 (Matryoshka) |
| 컨텍스트 | 32768 토큰 |
| 양자화 지원 | float32, int8, binary |
| 라이선스 | Proprietary (API only) |
| 가격 | $0.06 / M input tokens |
| MTEB 종합 | 65.1 |
| 도메인 변형 | finance-2, law-2, code-3, multilingual-2 |

instruction-aware 임베딩으로 input_type 파라미터에 `query`, `document`, `classification` 등을 지정하면 임베딩이 task에 맞게 변한다. Matryoshka 학습과 양자화의 결합으로 1024차원 int8 임베딩이 OpenAI 3072차원 float32 대비 인덱스 크기 1/12, 검색 품질은 비슷하거나 우위라는 것이 Voyage AI의 핵심 마케팅 포인트다.

## 핵심 기법

### Matryoshka와 양자화의 결합

Matryoshka로 차원을 줄이는 것과 양자화로 비트 수를 줄이는 것은 직교적이다. 둘을 결합하면 인덱스 크기 절감 효과가 곱셈으로 늘어난다.

| 설정 | 차원 | 비트 | 벡터당 바이트 | 1B 벡터 인덱스 |
|------|------|------|---------------|-----------------|
| OpenAI 3072 fp32 | 3072 | 32 | 12,288 | 12.3 TB |
| Voyage 2048 fp32 | 2048 | 32 | 8,192 | 8.2 TB |
| Voyage 1024 fp32 | 1024 | 32 | 4,096 | 4.1 TB |
| Voyage 1024 int8 | 1024 | 8 | 1,024 | 1.0 TB |
| Voyage 512 int8 | 512 | 8 | 512 | 0.5 TB |
| Voyage 1024 binary | 1024 | 1 | 128 | 0.13 TB |

binary 양자화에서는 코사인 유사도 대신 Hamming distance를 사용하며, 검색 품질이 약 5-10% 떨어지지만 인덱스가 100배 작아져 in-memory 검색이 가능해진다. 일반적인 production 권장은 1024 int8로, 품질 손실 1점 이내에 인덱스 크기를 1/12로 줄이는 sweet spot이다.

### 도메인 특화 변형

Voyage AI의 가장 큰 차별점은 도메인별 fine-tuned 모델군이다.

| 변형 | 학습 도메인 | 특징 |
|------|-------------|------|
| voyage-finance-2 | SEC filing, EDGAR, 금융 뉴스 | 금융 용어 정밀 매칭 |
| voyage-law-2 | 법률 판례, 계약 | 법률 용어와 case law |
| voyage-code-3 | GitHub 코드, documentation | 자연어로 코드 검색 |
| voyage-multilingual-2 | 다국어 | 100+ 언어 지원 |
| voyage-3-large | 일반 도메인 | 범용 |

도메인 특화 모델은 base 모델을 도메인 corpora로 contrastive fine-tuning한 결과물이다. 예를 들어 voyage-code-3는 GitHub 코드 파일과 README/docstring 쌍으로 학습되어, "Python에서 dict를 정렬하는 방법" 같은 자연어 쿼리로 sorted(d.items(), key=lambda x: x[1]) 같은 코드를 검색한다. 일반 임베딩으로는 어휘가 달라 검색이 어려운 영역이다.

도메인 RAG에서 일반 임베딩 대비 5-10% retrieval 향상을 보고하며, 이는 production에서 답변 품질에 직접 영향을 준다.

### Contrastive Learning 손실

표준 InfoNCE 손실에 Matryoshka 차원별 가중치를 더한 형태다.

$$
\mathcal{L}_{\text{Voyage}} = \sum_{d \in \{256, 512, 1024, 2048\}} w_d \cdot \mathcal{L}_{\text{InfoNCE}}\big(\mathbf{z}_q[:d], \mathbf{z}_p[:d], \mathcal{N}\big)
$$

도메인 변형은 같은 손실 구조를 도메인 corpora에서 추가 학습한다. 양자화는 학습 후 calibration 또는 quantization-aware training(QAT)으로 적용된다.

### Cost-effective 가격 정책

Voyage 3 Large는 $0.06 / M input tokens로, 경쟁사 대비 다음과 같이 위치한다.

| 모델 | 가격 ($ / M tokens) |
|------|---------------------|
| OpenAI text-embedding-3-large | 0.13 |
| Cohere embed-english-v3 | 0.10 |
| Voyage 3 Large | 0.06 |
| Gemini Embedding 001 | 0.00015 (10배 저렴, 단 small input) |

Gemini Embedding 001이 표면적으로 가장 저렴하지만 Voyage는 도메인 특화 모델이 같은 가격이라는 점, MongoDB Atlas와 통합되어 vector store 비용까지 합산하면 종합 비용 효율이 좋다는 점에서 선호된다.

## 성능

MTEB 영어 리더보드(2024-2025).

| 모델 | 차원 | 평균 | Retrieval | Classification | Clustering |
|------|------|------|-----------|----------------|------------|
| NV-Embed v2 | 4096 | 72.31 | 62.65 | 87.15 | 58.46 |
| BGE-en-ICL | 4096 | 71.24 | 61.67 | 88.62 | 57.51 |
| Gemini Embedding 001 | 3072 | 68.32 | 67.71 | 79.40 | 54.59 |
| voyage-3-large | 1024 | 65.10 | 62.40 | 78.20 | 51.30 |
| OpenAI text-embedding-3-large | 3072 | 64.59 | 55.44 | 75.45 | 49.01 |
| Cohere embed-english-v3 | 1024 | 64.47 | 55.00 | 76.49 | 47.43 |

Voyage 3 Large는 NV-Embed/Gemini Embedding보다는 평균이 낮지만, 같은 1024차원의 Cohere/OpenAI 1024차원 옵션 대비 의미 있는 우위를 보인다. 특히 retrieval에서 62.40점은 Cohere(55.00), OpenAI 1024차원(54.0대) 대비 7-8점 우위로, RAG 응답 품질에 직접 영향을 준다.

### 도메인 특화 성능

| 모델 | 도메인 | 도메인 retrieval 점수 |
|------|--------|----------------------|
| voyage-3-large | 일반 | 62.4 |
| voyage-finance-2 | 금융 (FinanceBench) | 71.2 |
| voyage-law-2 | 법률 (LegalBench) | 68.5 |
| voyage-code-3 | 코드 (CoIR) | 73.0 |

도메인 모델은 자기 도메인 벤치마크에서 일반 임베딩 대비 8-10점 우위를 보이며, 이는 도메인 RAG의 검색 정확도에 결정적이다.

## 사용 사례

- **MongoDB Atlas Vector Search**: 인수 효과로 Atlas와 가장 깊은 통합. MongoDB 사용자라면 default 임베딩.
- **금융 RAG**: 사내 SEC 자료, 분석 리포트 검색에 voyage-finance-2.
- **법률 RAG**: 판례 검색, 계약 분석에 voyage-law-2.
- **코드 검색**: 자연어로 GitHub 코드베이스 검색, 또는 코드-문서 매칭에 voyage-code-3.
- **대규모 인덱스의 비용 절감**: 1024 int8 또는 binary 양자화로 인덱스 크기를 적극 줄여 in-memory 검색 가능.

## 코드 예제

Voyage AI Python SDK 호출 흐름이다.

```python
import voyageai
import numpy as np

vo = voyageai.Client(api_key="YOUR_API_KEY")

documents = [
    "RAG는 retriever와 generator로 구성된 검색-생성 시스템이다.",
    "Matryoshka 표현은 임베딩을 잘라써도 성능이 유지된다.",
    "양자화는 인덱스 크기를 줄이는 핵심 기법이다.",
]

# 문서 임베딩 (input_type="document")
doc_result = vo.embed(
    documents,
    model="voyage-3-large",
    input_type="document",
    output_dimension=1024,   # Matryoshka 잘라쓰기
    output_dtype="int8",     # 양자화
)
doc_vectors = np.array(doc_result.embeddings)

# 쿼리 임베딩 (input_type="query")
query = "임베딩을 작게 만드는 방법은?"
q_result = vo.embed(
    [query],
    model="voyage-3-large",
    input_type="query",
    output_dimension=1024,
    output_dtype="int8",
)
q_vec = np.array(q_result.embeddings[0])

# int8 정수 임베딩에서 코사인 유사도
def cosine_int8(a, b):
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    return (a @ b) / (np.linalg.norm(a) * np.linalg.norm(b))

scores = np.array([cosine_int8(q_vec, d) for d in doc_vectors])
top_idx = int(np.argmax(scores))
print(documents[top_idx], scores[top_idx])
```

`output_dimension`과 `output_dtype` 두 파라미터로 Matryoshka와 양자화를 동시에 조절할 수 있다는 것이 Voyage 3 Large의 운영적 강점이다.

## 한계 및 의의

API only 폐쇄형이라 self-hosting이 불가능하고, 데이터 거버넌스가 엄격한 환경에서는 사용이 어렵다. 또한 평균 점수 65.1은 NV-Embed v2/BGE-en-ICL/Gemini Embedding 등 상위 모델 대비 명확히 뒤진다. 도메인 특화 모델은 강력하지만 도메인 외 일반 텍스트에서는 voyage-3-large보다 떨어질 수 있다.

그럼에도 의의는 분명하다. 첫째, Matryoshka + 양자화 조합으로 인덱스 비용을 production 단위에서 의미 있게 줄이는 표준 운영 패턴을 제시했다. 둘째, 도메인 특화 임베딩 변형이 production RAG의 정확도를 직접 끌어올리는 효과적 수단임을 입증했다. 셋째, 임베딩 전문 스타트업이 빅테크 사이에서 명확한 차별화를 만들 수 있음을 보였고, MongoDB 인수로 vector database와 임베딩이 통합되는 트렌드의 신호탄이 되었다. RAG가 비용 민감 production 인프라로 정착하는 시대에, Voyage 3 Large는 가성비와 도메인 특화의 표준 후보다.

## 관련 문서

- [[gemini-embedding-001|Gemini Embedding 001]] - 상용 1위 임베딩
- [[nv-embed-v2|NV-Embed v2]] - OSS MTEB 1위
- [[bge-en-icl|BGE-en-ICL]] - OSS ICL 임베딩
- [[gemini-embedding-2|Gemini Embedding 2]] - 멀티모달 후속 모델
- [[rag|RAG]] - 임베딩 활용의 핵심 응용
