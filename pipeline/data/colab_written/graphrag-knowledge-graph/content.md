# GraphRAG 실전: 지식 그래프 기반 RAG 구축

## 들어가며

:::info
이 글은 [[graphrag|GraphRAG 논문 리뷰]]의 실전 가이드 편이다. 논문의 이론적 배경은 해당 글을 참조하라.
:::

기존 벡터 기반 RAG는 **"이 문서에서 X를 찾아줘"** 같은 로컬 질문에 강하지만, **"이 문서들의 공통 주제는?"** 같은 글로벌 질문에는 취약하다. [[graphrag|GraphRAG]]는 지식 그래프를 활용하여 이 한계를 극복한다.

이 글에서는 Microsoft의 GraphRAG를 실전에 적용하는 방법을 단계별로 다룬다.

---

## GraphRAG 파이프라인 개요

```
텍스트 입력 → 청킹 → 엔티티/관계 추출(LLM) → 그래프 구축
→ 커뮤니티 탐지(Leiden) → 커뮤니티 요약(LLM) → 인덱스 저장

질문 → 로컬/글로벌 판단 → 검색 → 답변 생성
```

### 1단계: 설치 및 초기화

```bash
pip install graphrag

# 프로젝트 초기화
python -m graphrag.index --init --root ./my-project
```

`settings.yaml`에서 LLM 설정:
```yaml
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: openai_chat
  model: gpt-4o-mini     # 비용 절약
  max_tokens: 4096

embeddings:
  llm:
    type: openai_embedding
    model: text-embedding-3-small
```

### 2단계: 인덱싱

```bash
# input/ 폴더에 텍스트 파일 배치
python -m graphrag.index --root ./my-project
```

인덱싱 과정:
1. 텍스트를 청크로 분할 (기본 300 토큰)
2. 각 청크에서 LLM으로 엔티티/관계 추출
3. Leiden 알고리즘으로 커뮤니티 탐지
4. 각 커뮤니티에 대해 LLM 요약 생성
5. 결과를 Parquet 파일로 저장

:::warning
**비용 주의**: 인덱싱은 모든 텍스트를 LLM으로 처리하므로, 100페이지 문서 기준 gpt-4o-mini로 약 $1-5의 비용이 발생한다. gpt-4o를 사용하면 10배 이상 증가한다.
:::

### 3단계: 쿼리

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

---

## 커스텀 엔티티 추출

기본 엔티티 추출 프롬프트는 범용적이지만, 도메인 특화가 필요한 경우 `prompts/entity_extraction.txt`를 수정한다.

```
# AI/ML 도메인 특화 예시
추출 대상 엔티티 유형:
- MODEL: LLM, 아키텍처 (GPT-4, LLaMA, Transformer)
- TECHNIQUE: 학습/추론 기법 (RLHF, LoRA, RAG)
- DATASET: 벤치마크, 학습 데이터 (MMLU, HumanEval)
- ORGANIZATION: 연구 기관 (OpenAI, Google, Meta)
- METRIC: 성능 지표 (perplexity, accuracy, F1)
```

---

## 벡터 RAG vs GraphRAG

| 비교 항목 | 벡터 RAG | GraphRAG |
|----------|---------|---------|
| 인덱싱 비용 | 낮음 (임베딩만) | 높음 (LLM 호출) |
| 로컬 질문 | 강함 | 강함 (+ 관계 정보) |
| 글로벌 질문 | 약함 | 강함 |
| 멀티홉 추론 | 약함 | 강함 (그래프 탐색) |
| 업데이트 비용 | 낮음 (증분) | 높음 (재인덱싱) |
| 구현 복잡도 | 낮음 | 높음 |

### 하이브리드 전략

실전에서는 **두 방식을 결합**하는 것이 최선인 경우가 많다:

1. **기본 검색**: 벡터 RAG (빠르고 저렴)
2. **복잡한 질문**: GraphRAG 로컬 검색 (관계 기반)
3. **요약/분석**: GraphRAG 글로벌 검색

질문 라우터를 두어 질문 유형에 따라 적절한 검색 방법을 선택하면 비용과 성능을 모두 최적화할 수 있다.

---

## 그래프 DB 활용: Neo4j 연동

GraphRAG의 그래프를 **Neo4j**에 저장하면 시각화와 복잡한 쿼리가 가능하다:

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# 그래프 데이터 로드 (GraphRAG 출력에서)
with driver.session() as session:
    # 엔티티 생성
    session.run("""
        MERGE (e:Entity {name: $name})
        SET e.type = $type, e.description = $description
    """, name="GPT-4", type="MODEL", description="OpenAI의 대형 언어 모델")

    # 관계 생성
    session.run("""
        MATCH (a:Entity {name: $from_name})
        MATCH (b:Entity {name: $to_name})
        MERGE (a)-[r:RELATED_TO {description: $desc}]->(b)
    """, from_name="GPT-4", to_name="Transformer", desc="기반 아키텍처")
```

Neo4j Cypher 쿼리로 복잡한 관계 탐색:
```cypher
-- GPT-4와 2홉 이내로 연결된 모든 엔티티
MATCH (n:Entity {name: "GPT-4"})-[*1..2]-(connected)
RETURN connected.name, connected.type
```

---

## 성능 최적화 팁

### 1. LLM 비용 절감
- 인덱싱에는 `gpt-4o-mini` 사용 (품질 대비 비용 최적)
- 쿼리 시에만 `gpt-4o` 사용
- 청크 크기 조절: 큰 청크 → LLM 호출 횟수 감소, 추출 품질 저하 트레이드오프

### 2. 커뮤니티 해상도
- `community_resolution` 파라미터로 커뮤니티 세분도 조절
- 높은 해상도: 세밀한 주제 분류, 많은 커뮤니티
- 낮은 해상도: 큰 주제 그룹, 적은 커뮤니티

### 3. 증분 인덱싱
새 문서 추가 시 전체 재인덱싱 대신:
- 새 문서의 엔티티/관계만 추출
- 기존 그래프에 병합
- 커뮤니티 재탐지 (영향 범위만)

---

## 정리

GraphRAG는 **글로벌 질문에 답할 수 있는 유일한 RAG 패러다임**이다. 인덱싱 비용이 높다는 단점이 있지만, 코퍼스가 고정되고 다양한 유형의 질문이 필요한 환경에서는 그 가치가 명확하다.

실전에서는 벡터 RAG + GraphRAG의 **하이브리드 전략**이 가장 효과적이며, 질문 유형에 따른 라우팅으로 비용과 성능을 모두 관리할 수 있다.
