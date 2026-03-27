# GraphRAG 실전: 지식 그래프 기반 RAG 구축

## 들어가며

:::info
이 글은 [[61_graphrag|GraphRAG 논문 리뷰]]의 실전 가이드 편이다. 논문의 이론적 배경은 해당 글을 참조하라.
:::

기존 벡터 기반 RAG는 **"이 문서에서 X를 찾아줘"** 같은 로컬 질문에 강하지만, **"이 문서들의 공통 주제는 무엇인가?"** 같은 글로벌 질문에는 구조적으로 취약하다. 벡터 유사도 검색은 개별 청크 단위로 동작하기 때문에, 여러 문서에 걸친 관계나 전체적인 패턴을 파악하기 어렵다.

Microsoft의 GraphRAG는 지식 그래프(Knowledge Graph)를 활용하여 이 한계를 극복한다. 텍스트에서 엔티티와 관계를 추출하여 그래프를 구축하고, Leiden 알고리즘으로 커뮤니티를 탐지한 뒤, 각 커뮤니티의 요약을 생성하여 글로벌 질문에도 답할 수 있는 RAG 시스템을 만든다.

이 글에서는 Standard RAG, GraphRAG, KG-RAG 세 가지 패러다임을 비교하고, GraphRAG의 파이프라인을 단계별로 구현하는 방법을 다룬다.

---

## RAG 패러다임 비교

RAG 시스템은 검색 기반에 따라 세 가지 패러다임으로 분류할 수 있다.

### Standard RAG vs GraphRAG vs KG-RAG

| 비교 항목 | Standard RAG | GraphRAG | KG-RAG |
|----------|-------------|----------|--------|
| 검색 기반 | 벡터 유사도 | 지식 그래프 + 커뮤니티 요약 | 외부 지식 그래프 (Wikidata 등) |
| 인덱싱 방식 | 텍스트 임베딩 | LLM 기반 엔티티/관계 추출 | 기존 KG 연결 |
| 로컬 질문 성능 | 강함 | 강함 (+ 관계 정보) | 강함 (+ 구조화된 지식) |
| 글로벌 질문 성능 | 약함 | 매우 강함 | 보통 |
| 멀티홉 추론 | 약함 | 강함 (그래프 탐색) | 강함 (KG 경로 탐색) |
| 인덱싱 비용 | 낮음 (임베딩만) | 높음 (LLM 호출 다수) | 낮음 (기존 KG 활용) |
| 업데이트 비용 | 낮음 (증분 가능) | 높음 (재인덱싱 필요) | 중간 (KG 매핑 갱신) |
| 구현 복잡도 | 낮음 | 높음 | 중간 |
| 환각 제어 | 보통 | 좋음 (관계 기반 근거) | 좋음 (구조화된 근거) |
| 적합 시나리오 | 단순 QA, 문서 검색 | 분석/요약, 관계 파악 | 도메인 특화 QA |

### 질문 유형별 적합도

| 질문 유형 | Standard RAG | GraphRAG Local | GraphRAG Global | KG-RAG |
|----------|:-----------:|:-------------:|:---------------:|:------:|
| 특정 사실 질문 | 적합 | 적합 | 부적합 | 적합 |
| 멀티홉 질문 | 부적합 | 적합 | 보통 | 적합 |
| 전체 요약/트렌드 | 부적합 | 부적합 | 적합 | 부적합 |
| 비교 분석 | 보통 | 적합 | 적합 | 보통 |
| 인과 관계 추론 | 부적합 | 적합 | 보통 | 적합 |
| 개체 간 관계 질문 | 부적합 | 적합 | 보통 | 적합 |

---

## GraphRAG 파이프라인 개요

GraphRAG의 전체 파이프라인은 크게 **인덱싱 단계**와 **쿼리 단계**로 나뉜다.

### 인덱싱 파이프라인

```
텍스트 입력
  → 청킹 (300 토큰 단위)
  → 엔티티 추출 (LLM)
  → 관계 추출 (LLM)
  → 그래프 구축
  → 커뮤니티 탐지 (Leiden Algorithm)
  → 커뮤니티 요약 생성 (LLM)
  → 인덱스 저장 (Parquet)
```

### 쿼리 파이프라인

```
질문 입력
  → 로컬/글로벌 판단
  → Local: 관련 엔티티/관계 검색 → 서브그래프 컨텍스트 → 답변 생성
  → Global: 커뮤니티 요약 수집 → Map-Reduce 답변 생성
```

### 파이프라인 단계별 역할

| 단계 | 입력 | 출력 | 사용 모델 | 비용 비중 |
|------|------|------|----------|----------|
| 청킹 | 원본 텍스트 | 텍스트 청크 | 없음 | 0% |
| 엔티티 추출 | 텍스트 청크 | 엔티티 목록 | LLM | ~30% |
| 관계 추출 | 텍스트 청크 + 엔티티 | 관계 트리플 | LLM | ~30% |
| 그래프 구축 | 엔티티 + 관계 | NetworkX 그래프 | 없음 | 0% |
| 커뮤니티 탐지 | 그래프 | 커뮤니티 계층 | Leiden | 0% |
| 커뮤니티 요약 | 커뮤니티 멤버 | 요약 텍스트 | LLM | ~40% |

---

## 설치 및 초기화

### 환경 설정

```bash
pip install graphrag

# 프로젝트 초기화
python -m graphrag.index --init --root ./my-project
```

초기화 후 생성되는 디렉토리 구조:

```
my-project/
├── settings.yaml          # LLM, 임베딩, 파이프라인 설정
├── prompts/               # 엔티티/관계 추출 프롬프트
│   ├── entity_extraction.txt
│   └── summarize_descriptions.txt
├── input/                 # 입력 텍스트 파일 (.txt)
└── output/                # 인덱싱 결과 (Parquet)
```

### LLM 설정

`settings.yaml`에서 LLM과 임베딩 모델을 설정한다:

```yaml
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: openai_chat
  model: gpt-4o-mini     # 인덱싱에는 비용 효율적인 모델 권장
  max_tokens: 4096
  temperature: 0          # 엔티티 추출의 일관성을 위해

embeddings:
  llm:
    type: openai_embedding
    model: text-embedding-3-small

chunks:
  size: 300               # 청크 크기 (토큰)
  overlap: 100            # 청크 간 겹침

entity_extraction:
  max_gleanings: 1        # 추가 추출 라운드 수
```

---

## 엔티티 및 관계 추출

GraphRAG의 핵심은 LLM을 사용하여 텍스트에서 **엔티티(Entity)**와 **관계(Relation)**를 추출하는 것이다.

### 엔티티 추출 원리

엔티티 추출은 각 텍스트 청크에 대해 LLM을 호출하여 수행한다. 기본 프롬프트는 범용적이지만, 도메인에 맞게 커스터마이징하면 추출 품질이 크게 향상된다.

```python
# AI/ML 도메인 특화 엔티티 추출 프롬프트 예시
ENTITY_EXTRACTION_PROMPT = """
주어진 텍스트에서 다음 유형의 엔티티를 추출하라:

- MODEL: LLM, 아키텍처 (GPT-4, LLaMA, Transformer)
- TECHNIQUE: 학습/추론 기법 (RLHF, LoRA, RAG)
- DATASET: 벤치마크, 학습 데이터 (MMLU, HumanEval)
- ORGANIZATION: 연구 기관 (OpenAI, Google DeepMind, Meta)
- METRIC: 성능 지표 (perplexity, accuracy, F1)
- CONCEPT: 핵심 개념 (attention, tokenization, fine-tuning)

각 엔티티에 대해 다음 정보를 반환하라:
1. name: 엔티티 이름 (정규화된 형태)
2. type: 위 유형 중 하나
3. description: 텍스트 내 맥락에서의 설명 (1-2문장)

JSON 배열로 반환:
[{{"name": "GPT-4", "type": "MODEL", "description": "OpenAI가 개발한 대규모 언어 모델"}}]
"""
```

### 관계 추출 원리

관계 추출은 추출된 엔티티 쌍 사이의 관계를 식별한다. 각 관계는 **(소스 엔티티, 관계 설명, 타겟 엔티티, 강도)** 형태의 트리플로 표현된다.

```python
# 관계 추출 결과 예시
relations = [
    {
        "source": "GPT-4",
        "target": "Transformer",
        "description": "GPT-4는 Transformer 아키텍처를 기반으로 구축되었다",
        "weight": 9
    },
    {
        "source": "OpenAI",
        "target": "GPT-4",
        "description": "OpenAI가 GPT-4를 개발했다",
        "weight": 10
    },
    {
        "source": "GPT-4",
        "target": "RLHF",
        "description": "GPT-4는 RLHF로 정렬(alignment)되었다",
        "weight": 8
    },
]
```

### 엔티티/관계 추출 품질 개선 전략

| 전략 | 설명 | 효과 |
|------|------|------|
| 도메인 특화 프롬프트 | 엔티티 유형을 도메인에 맞게 정의 | 추출 정밀도 향상 |
| Gleanings (다회 추출) | 동일 청크에 대해 추가 추출 라운드 | 재현율 향상 (비용 증가) |
| 청크 크기 조절 | 작은 청크 (200-300 토큰) | 정밀도 향상, 비용 증가 |
| 청크 오버랩 | 인접 청크 간 겹침 (50-100 토큰) | 경계 엔티티 누락 방지 |
| 엔티티 정규화 | 동일 엔티티의 다른 표현 통합 | 그래프 품질 향상 |
| Few-shot 예시 | 프롬프트에 추출 예시 포함 | 일관성 향상 |

---

## Leiden 알고리즘과 커뮤니티 탐지

### Leiden 알고리즘 개요

GraphRAG에서 커뮤니티 탐지는 **Leiden 알고리즘**을 사용한다. Leiden은 Louvain 알고리즘의 개선판으로, 그래프를 **밀접하게 연결된 노드 그룹(커뮤니티)**으로 분할한다.

Leiden 알고리즘의 핵심 단계:

1. **노드 이동**: 각 노드를 모듈성(modularity)이 최대화되는 커뮤니티로 이동
2. **정제**: 잘못 분류된 노드를 재배치하여 품질 보장 (Louvain 대비 개선점)
3. **집약**: 커뮤니티를 단일 노드로 축소하여 상위 레벨 그래프 생성
4. **반복**: 상위 레벨에서 1-3단계 반복하여 계층적 커뮤니티 구조 생성

### Louvain vs Leiden

| 비교 항목 | Louvain | Leiden |
|----------|---------|--------|
| 커뮤니티 품질 | 불안정한 경우 있음 | 안정적 (정제 단계) |
| 연결성 보장 | 보장하지 않음 | 보장함 |
| 수렴 속도 | 빠름 | 비슷하거나 더 빠름 |
| 계층 구조 | 지원 | 지원 (더 안정적) |
| GraphRAG 사용 | 사용하지 않음 | 기본 알고리즘 |

### 커뮤니티 해상도 설정

`community_resolution` 파라미터로 커뮤니티의 세분도를 조절한다:

| 해상도 | 커뮤니티 수 | 커뮤니티 크기 | 적합 시나리오 |
|--------|:---------:|:----------:|------------|
| 낮음 (0.5 이하) | 적음 | 큼 | 넓은 주제 파악, 비용 절감 |
| 기본 (1.0) | 보통 | 보통 | 일반적 사용 |
| 높음 (2.0 이상) | 많음 | 작음 | 세밀한 주제 분류 필요 시 |

해상도가 높을수록 커뮤니티 요약 수가 증가하여 **LLM 호출 비용도 비례하여 증가**한다.

### 계층적 커뮤니티 구조

Leiden 알고리즘은 **계층적(hierarchical)** 커뮤니티 구조를 생성한다. GraphRAG는 이 계층을 활용하여 다양한 추상화 수준에서 질문에 답한다:

- **Level 0 (최하위)**: 가장 세밀한 커뮤니티, 구체적 주제
- **Level 1**: 중간 수준, 관련 주제 그룹
- **Level 2+ (상위)**: 가장 큰 커뮤니티, 광범위한 주제

글로벌 검색 시 어떤 레벨의 커뮤니티 요약을 사용할지에 따라 답변의 추상화 수준이 달라진다.

---

## 로컬 검색 vs 글로벌 검색

GraphRAG는 질문 유형에 따라 **로컬(Local)** 검색과 **글로벌(Global)** 검색을 제공한다. 이 둘의 차이를 이해하는 것이 GraphRAG 활용의 핵심이다.

### 로컬 검색 (Local Search)

로컬 검색은 **특정 엔티티와 그 주변 관계**를 탐색하여 답변을 생성한다.

**작동 방식**:
1. 질문에서 핵심 엔티티 식별
2. 해당 엔티티와 연결된 관계, 이웃 엔티티 수집
3. 관련 텍스트 청크, 커뮤니티 요약을 컨텍스트로 구성
4. LLM에 컨텍스트와 함께 질문을 전달하여 답변 생성

**적합한 질문 예시**:
- "Transformer의 self-attention 메커니즘을 설명해줘"
- "LoRA와 QLoRA의 차이점은?"
- "GPT-4가 사용한 학습 기법은?"

### 글로벌 검색 (Global Search)

글로벌 검색은 **커뮤니티 요약을 Map-Reduce 방식**으로 처리하여 코퍼스 전체에 걸친 질문에 답한다.

**작동 방식**:
1. 지정된 레벨의 모든 커뮤니티 요약을 수집
2. **Map 단계**: 각 커뮤니티 요약에 대해 부분 답변 생성
3. **Reduce 단계**: 부분 답변들을 종합하여 최종 답변 생성

**적합한 질문 예시**:
- "이 논문들의 공통 연구 트렌드는 무엇인가?"
- "이 코퍼스에서 다루는 주요 기술 분야를 요약해줘"
- "최근 LLM 연구의 주요 방향은?"

### 로컬 vs 글로벌 상세 비교

| 비교 항목 | Local Search | Global Search |
|----------|-------------|--------------|
| 검색 대상 | 엔티티 + 관계 + 청크 | 커뮤니티 요약 |
| 답변 범위 | 특정 엔티티 주변 | 코퍼스 전체 |
| LLM 호출 수 | 1회 | 커뮤니티 수 + 1회 (Map-Reduce) |
| 레이턴시 | 낮음 (1-3초) | 높음 (5-30초, 커뮤니티 수에 비례) |
| 토큰 소비 | 적음 | 많음 (모든 요약 처리) |
| 답변 품질 | 구체적, 사실 기반 | 종합적, 추상적 |
| 환각 위험 | 낮음 | 보통 (요약 기반) |
| 적합 질문 | 사실 확인, 관계 질문 | 트렌드, 요약, 비교 |

---

## 인덱싱 실행

### 인덱싱 명령

```bash
# input/ 폴더에 텍스트 파일(.txt) 배치 후 실행
python -m graphrag.index --root ./my-project
```

인덱싱 과정에서 수행되는 단계:

1. 텍스트를 청크로 분할 (기본 300 토큰, 100 토큰 겹침)
2. 각 청크에서 LLM으로 엔티티 추출
3. 각 청크에서 LLM으로 관계 추출
4. 엔티티/관계로 NetworkX 그래프 구축
5. Leiden 알고리즘으로 커뮤니티 탐지
6. 각 커뮤니티에 대해 LLM 요약 생성
7. 결과를 Parquet 파일로 저장

:::warning
**비용 주의**: 인덱싱은 모든 텍스트를 LLM으로 처리하므로, 100페이지 문서 기준 gpt-4o-mini로 약 $1-5의 비용이 발생한다. gpt-4o를 사용하면 10배 이상 증가한다. 반드시 소규모 데이터로 먼저 테스트하라.
:::

### 인덱싱 출력 구조

인덱싱이 완료되면 `output/` 디렉토리에 다음 Parquet 파일들이 생성된다:

| 파일 | 내용 | 주요 컬럼 |
|------|------|----------|
| `entities.parquet` | 추출된 엔티티 | name, type, description, community_id |
| `relationships.parquet` | 엔티티 간 관계 | source, target, description, weight |
| `communities.parquet` | 커뮤니티 정보 | id, level, members |
| `community_reports.parquet` | 커뮤니티 요약 | community_id, summary, findings |
| `text_units.parquet` | 텍스트 청크 | id, text, entity_ids |
| `covariates.parquet` | 공변량 (claim 등) | entity_id, covariate_type, value |

---

## 쿼리 실행

### CLI 기반 쿼리

```bash
# 로컬 검색 (특정 사실 질문)
python -m graphrag.query --root ./my-project \
  --method local \
  --query "Transformer의 self-attention 메커니즘을 설명해줘"

# 글로벌 검색 (전체 요약 질문)
python -m graphrag.query --root ./my-project \
  --method global \
  --query "이 논문들의 공통 연구 트렌드는 무엇인가?"
```

### Python API 기반 쿼리

```python
import asyncio
from graphrag.query.structured_search.local_search import LocalSearch
from graphrag.query.structured_search.global_search import GlobalSearch
from graphrag.query.llm.oai import ChatOpenAI

# LLM 초기화
llm = ChatOpenAI(model="gpt-4o", api_key="your-key")

# 로컬 검색 실행
local_search = LocalSearch(
    llm=llm,
    context_builder=context_builder,  # 인덱스에서 로드
    token_encoder=token_encoder,
)
result = asyncio.run(
    local_search.asearch("LoRA와 QLoRA의 차이점은?")
)
print(result.response)

# 글로벌 검색 실행
global_search = GlobalSearch(
    llm=llm,
    context_builder=global_context_builder,
    token_encoder=token_encoder,
    map_llm=llm,
    reduce_llm=llm,
)
result = asyncio.run(
    global_search.asearch("주요 연구 트렌드를 요약해줘")
)
print(result.response)
```

---

## 비용 분석

GraphRAG의 가장 큰 진입 장벽은 **인덱싱 비용**이다. 모든 텍스트가 LLM을 거치므로, 사전에 비용을 추정하는 것이 중요하다.

### 모델별 인덱싱 비용 비교

| 모델 | 입력 단가 (1M 토큰) | 출력 단가 (1M 토큰) | 100페이지 문서 예상 비용 | 1000페이지 예상 비용 |
|------|:------------------:|:------------------:|:--------------------:|:-------------------:|
| gpt-4o-mini | $0.15 | $0.60 | $1-3 | $10-30 |
| gpt-4o | $2.50 | $10.00 | $10-30 | $100-300 |
| gpt-4-turbo | $10.00 | $30.00 | $40-100 | $400-1000 |
| Claude 3.5 Sonnet | $3.00 | $15.00 | $15-40 | $150-400 |

### 단계별 비용 구성

| 단계 | 비용 비중 | 최적화 방법 |
|------|:--------:|-----------|
| 엔티티 추출 | ~30% | 청크 크기 증가, gleanings 축소 |
| 관계 추출 | ~30% | 엔티티 추출과 통합 프롬프트 |
| 커뮤니티 요약 | ~35% | 해상도 낮추기, 하위 커뮤니티 생략 |
| 임베딩 | ~5% | 저비용 임베딩 모델 사용 |

### 쿼리 비용 비교

| 쿼리 유형 | LLM 호출 수 | 평균 토큰 소비 | 평균 레이턴시 | 예상 비용 (gpt-4o-mini) |
|----------|:---------:|:-----------:|:----------:|:-------------------:|
| Local Search | 1회 | 2,000-5,000 | 1-3초 | $0.001-0.003 |
| Global Search | N+1회 | 10,000-50,000 | 5-30초 | $0.01-0.05 |
| Standard RAG | 1회 | 1,000-3,000 | 1-2초 | $0.0005-0.002 |

:::tip
**비용 절감 팁**: 인덱싱에는 `gpt-4o-mini`를 사용하고, 쿼리 시에만 `gpt-4o`를 사용하면 인덱싱 비용을 10배 이상 절감할 수 있다. 커뮤니티 해상도를 낮추는 것도 효과적이다.
:::

---

## 커스텀 엔티티 추출 설정

### 도메인별 프롬프트 커스터마이징

기본 프롬프트는 범용적이지만, 도메인에 맞게 `prompts/entity_extraction.txt`를 수정하면 추출 품질이 크게 향상된다.

| 도메인 | 엔티티 유형 예시 | 관계 유형 예시 |
|--------|----------------|--------------|
| AI/ML | MODEL, TECHNIQUE, DATASET, METRIC | trained_on, outperforms, extends |
| 의료 | DISEASE, DRUG, SYMPTOM, GENE | treats, causes, inhibits |
| 법률 | LAW, CASE, COURT, PARTY | cites, overrules, applies |
| 금융 | COMPANY, PRODUCT, MARKET, REGULATION | acquires, competes_with, regulates |
| 소프트웨어 | LIBRARY, FRAMEWORK, LANGUAGE, API | depends_on, implements, replaces |

### 추출 품질 평가 방법

인덱싱 결과를 점검하여 추출 품질을 확인한다:

```python
import pandas as pd

# 엔티티 분포 확인
entities = pd.read_parquet("output/entities.parquet")
print(f"총 엔티티 수: {len(entities)}")
print(f"\n엔티티 유형 분포:")
print(entities["type"].value_counts())

# 관계 분포 확인
relations = pd.read_parquet("output/relationships.parquet")
print(f"\n총 관계 수: {len(relations)}")
print(f"\n관계 가중치 통계:")
print(relations["weight"].describe())

# 커뮤니티 분포 확인
communities = pd.read_parquet("output/communities.parquet")
print(f"\n총 커뮤니티 수: {len(communities)}")
```

---

## 그래프 DB 활용: Neo4j 연동

GraphRAG의 Parquet 출력을 **Neo4j**에 로드하면 시각화와 복잡한 그래프 쿼리가 가능해진다.

### Neo4j로 그래프 데이터 로드

```python
from neo4j import GraphDatabase
import pandas as pd

driver = GraphDatabase.driver(
    "bolt://localhost:7687", auth=("neo4j", "password")
)

# Parquet에서 데이터 로드
entities = pd.read_parquet("output/entities.parquet")
relations = pd.read_parquet("output/relationships.parquet")

with driver.session() as session:
    # 엔티티 생성
    for _, row in entities.iterrows():
        session.run("""
            MERGE (e:Entity {name: $name})
            SET e.type = $type, e.description = $description
        """, name=row["name"], type=row["type"],
           description=row["description"])

    # 관계 생성
    for _, row in relations.iterrows():
        session.run("""
            MATCH (a:Entity {name: $source})
            MATCH (b:Entity {name: $target})
            MERGE (a)-[r:RELATED_TO {
                description: $desc, weight: $weight
            }]->(b)
        """, source=row["source"], target=row["target"],
           desc=row["description"], weight=row["weight"])
```

### Cypher 쿼리 예시

```cypher
// 특정 엔티티와 2홉 이내로 연결된 모든 엔티티
MATCH (n:Entity {name: "GPT-4"})-[*1..2]-(connected)
RETURN connected.name, connected.type

// 가장 많은 관계를 가진 엔티티 Top 10
MATCH (n:Entity)-[r]-()
RETURN n.name, n.type, COUNT(r) AS relation_count
ORDER BY relation_count DESC
LIMIT 10

// 두 엔티티 간 최단 경로
MATCH path = shortestPath(
    (a:Entity {name: "Transformer"})-[*]-(b:Entity {name: "BERT"})
)
RETURN path
```

---

## 성능 최적화

### 인덱싱 최적화

| 최적화 항목 | 기본값 | 권장값 | 효과 |
|-----------|:-----:|:-----:|------|
| LLM 모델 | gpt-4o | gpt-4o-mini | 비용 10배 절감 |
| 청크 크기 | 300 | 500-600 | LLM 호출 40% 감소, 추출 품질 소폭 저하 |
| 청크 오버랩 | 100 | 50 | 비용 소폭 감소 |
| Gleanings | 1 | 0 | 비용 30% 절감, 재현율 소폭 저하 |
| 해상도 | 1.0 | 0.5 | 커뮤니티 요약 비용 감소 |
| Batch 크기 | 1 | 10-20 | 처리 속도 향상 (Rate limit 주의) |

### 쿼리 최적화

| 최적화 항목 | 설명 | 효과 |
|-----------|------|------|
| 캐싱 | 반복 쿼리 결과 캐싱 | 레이턴시 90% 감소 |
| 로컬 우선 | 가능하면 로컬 검색 사용 | 비용 10배 절감 |
| 커뮤니티 레벨 선택 | 글로벌 검색 시 상위 레벨만 사용 | 처리 시간 단축 |
| 쿼리 라우팅 | 질문 유형 자동 분류 | 적절한 검색 방법 선택 |

### 증분 인덱싱 전략

새 문서 추가 시 전체 재인덱싱을 피하는 방법:

1. 새 문서의 엔티티/관계만 추출
2. 기존 그래프에 새 노드/엣지 병합
3. 영향받는 커뮤니티만 재탐지
4. 변경된 커뮤니티의 요약만 재생성

현재 Microsoft GraphRAG는 증분 인덱싱을 공식 지원하지 않으므로, 커스텀 구현이 필요하다.

---

## 하이브리드 RAG 전략

### 벡터 RAG + GraphRAG 결합

실전에서는 **두 방식을 결합**하는 하이브리드 전략이 가장 효과적이다. [[hybrid-search-reranking|하이브리드 검색]]의 원리를 GraphRAG에도 적용할 수 있다.

| 질문 유형 | 사용 전략 | 이유 |
|----------|---------|------|
| 단순 사실 질문 | Standard RAG | 빠르고 저렴 |
| 관계/비교 질문 | GraphRAG Local | 엔티티 간 관계 활용 |
| 멀티홉 질문 | GraphRAG Local | 그래프 경로 탐색 |
| 요약/트렌드 질문 | GraphRAG Global | 커뮤니티 요약 활용 |
| 도메인 지식 질문 | KG-RAG | 외부 KG 연결 |

### 질문 라우팅 구현

질문 유형에 따라 적절한 검색 방법을 자동 선택하는 라우터를 구현한다:

```python
from enum import Enum

class SearchStrategy(Enum):
    STANDARD_RAG = "standard"
    GRAPHRAG_LOCAL = "local"
    GRAPHRAG_GLOBAL = "global"

def route_query(query: str, llm) -> SearchStrategy:
    """질문 유형을 분류하여 적절한 검색 전략을 반환한다."""
    routing_prompt = f"""
    다음 질문을 분류하라:
    - "standard": 특정 사실을 묻는 단순 질문
    - "local": 엔티티 간 관계, 비교, 멀티홉 추론 질문
    - "global": 전체 요약, 트렌드, 패턴 분석 질문

    질문: {query}
    분류 (standard/local/global):
    """
    result = llm.invoke(routing_prompt).strip().lower()

    if "global" in result:
        return SearchStrategy.GRAPHRAG_GLOBAL
    elif "local" in result:
        return SearchStrategy.GRAPHRAG_LOCAL
    else:
        return SearchStrategy.STANDARD_RAG
```

---

## 선택 가이드

### 언제 Standard RAG를 사용할까

- 단순 QA가 주 사용 사례인 경우
- 코퍼스가 자주 변경되는 경우 (증분 업데이트 필요)
- 인덱싱 비용을 최소화해야 하는 경우
- 레이턴시가 중요한 실시간 서비스

### 언제 GraphRAG를 사용할까

- "이 문서들의 공통점은?" 같은 **글로벌 질문**이 필요한 경우
- 엔티티 간 **관계 탐색**이 중요한 경우
- 코퍼스가 **고정적**이거나 변경 빈도가 낮은 경우
- **분석/요약** 목적의 지식 기반 구축

### 언제 KG-RAG를 사용할까

- 이미 구축된 **외부 지식 그래프**(Wikidata, UMLS 등)가 있는 경우
- **도메인 특화** 구조화된 지식이 필요한 경우
- 의료, 법률 등 **정확한 팩트 체킹**이 중요한 도메인

### 의사 결정 플로우

| 조건 | 권장 전략 |
|------|---------|
| 글로벌 질문이 필요한가? → 예 | GraphRAG |
| 멀티홉 추론이 필요한가? → 예 | GraphRAG Local 또는 KG-RAG |
| 코퍼스가 자주 변경되는가? → 예 | Standard RAG |
| 외부 KG가 존재하는가? → 예 | KG-RAG |
| 인덱싱 비용 제한이 있는가? → 예 | Standard RAG |
| 위 모두 해당하지 않으면 | 하이브리드 (Standard + GraphRAG) |

---

## 관련 기술과의 연결

GraphRAG와 함께 활용할 수 있는 관련 기술들:

| 기술 | 역할 | 관련 글 |
|------|------|--------|
| 하이브리드 검색 + Reranking | 벡터 + 키워드 검색 결합 | [[hybrid-search-reranking]] |
| 컨텍스트 압축 | 검색 결과 압축으로 토큰 절감 | [[context-compression]] |
| DPR | 밀집 검색 기반 벡터 RAG | [[68_dpr]] |
| RAPTOR | 계층적 요약 기반 RAG | [[69_raptor]] |

RAPTOR와 GraphRAG는 모두 **계층적 구조**를 활용한다는 점에서 유사하지만, RAPTOR는 텍스트 요약 트리를, GraphRAG는 지식 그래프 커뮤니티를 기반으로 한다는 점에서 차이가 있다.

---

## 한계 및 주의사항

GraphRAG를 도입할 때 반드시 인지해야 할 한계점들:

| 한계 | 상세 설명 | 대응 방안 |
|------|---------|---------|
| 높은 인덱싱 비용 | 모든 텍스트가 LLM을 거침 | gpt-4o-mini 사용, 청크 크기 증가 |
| 재인덱싱 부담 | 문서 변경 시 전체 재인덱싱 필요 | 증분 인덱싱 커스텀 구현 |
| 추출 품질 의존성 | LLM 추출 오류가 그래프 전체에 전파 | 도메인 프롬프트 최적화, 검증 단계 추가 |
| 글로벌 검색 레이턴시 | Map-Reduce 방식으로 지연 발생 | 캐싱, 커뮤니티 레벨 제한 |
| 스키마 부재 | 비정형 엔티티/관계로 일관성 부족 | 엔티티 유형/관계 유형 명시적 정의 |

---

## 정리

GraphRAG는 **글로벌 질문에 답할 수 있는 유일한 RAG 패러다임**이다. 엔티티/관계 추출, Leiden 커뮤니티 탐지, 계층적 요약이라는 세 가지 핵심 요소를 통해 코퍼스 전체에 걸친 질문에 효과적으로 대응한다.

핵심 포인트:

- **Standard RAG**: 단순하고 저렴하지만, 글로벌 질문과 멀티홉 추론에 약함
- **GraphRAG**: 글로벌 질문과 관계 탐색에 강하지만, 인덱싱 비용이 높음
- **KG-RAG**: 외부 지식 그래프를 활용하여 도메인 특화 QA에 강함
- **하이브리드**: 실전에서는 Standard RAG + GraphRAG의 결합이 가장 효과적

인덱싱 비용이 진입 장벽이지만, gpt-4o-mini 활용과 커뮤니티 해상도 조절로 비용을 관리할 수 있다. 코퍼스가 고정되고 다양한 유형의 질문이 필요한 환경에서 GraphRAG의 가치는 명확하다.
