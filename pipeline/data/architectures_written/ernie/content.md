# ERNIE: 지식 통합 기반 사전 학습의 선구자

## 개요

**ERNIE**(Enhanced Representation through Knowledge Integration)는 2019년 4월 Baidu가 발표한 지식 강화 사전 학습 모델로, BERT가 텍스트의 표면적 통계 패턴에만 의존하는 한계를 극복하기 위해 **지식 그래프와 개체 수준 정보를 사전 학습에 통합**하는 선구적 접근법을 제시했다.

BERT의 MLM은 개별 토큰을 무작위로 마스킹하므로, 모델이 "바이든"을 "바"+"이"+"든"의 개별 조각으로만 복원하면 된다. 하지만 ERNIE는 **"바이든" 전체를 하나의 개체로 마스킹**하여 모델이 세계 지식을 활용해야만 복원할 수 있도록 유도한다. 이 Entity Masking과 Phrase Masking을 통해 중국어 NLP 태스크에서 BERT 대비 최대 10%의 성능 향상을 달성했으며, 이후 ERNIE 2.0, 3.0, Bot 시리즈로 확장되어 중국어 LLM 연구의 기초를 닦았다.

**참고 논문**: [ERNIE: Enhanced Representation through Knowledge Integration](https://arxiv.org/abs/1904.09223) (Sun et al., 2019)

## 아키텍처 상세

### 기본 구조

ERNIE의 기본 아키텍처는 BERT와 동일한 Transformer Encoder이다.

| 구성 요소 | Base | Large |
|-----------|------|-------|
| **파라미터** | 114M | 340M |
| **레이어** | 12 | 24 |
| **히든 차원** | 768 | 1024 |
| **어텐션 헤드** | 12 | 16 |
| **컨텍스트** | 512 | 512 |
| **어휘** | 18,000 (중국어 BPE) | 18,000 |

### 3단계 마스킹 전략

ERNIE의 핵심 혁신은 단어, 구문, 개체의 3가지 수준에서 단계적으로 마스킹을 수행하는 것이다:

#### 1. Basic-level Masking

BERT와 동일한 **토큰 수준** 무작위 마스킹이다. 개별 문자나 서브워드를 마스킹하여 기본적인 언어 패턴을 학습한다.

```
입력: 바이든 대통령이 백악관에서 연설했다
마스킹: 바[MASK]든 대통령이 [MASK]악관에서 연설했다
```

#### 2. Phrase Masking

**어절 및 구문 단위** 전체를 마스킹하여 구문 구조와 관용 표현을 학습한다.

```
입력: 바이든 대통령이 백악관에서 연설했다
마스킹: 바이든 [MASK][MASK][MASK] 백악관에서 연설했다
```

#### 3. Entity Masking

**인명, 지명, 기관명 등 개체명 전체**를 마스킹하여 세계 지식을 학습에 활용하도록 유도한다.

```
입력: 바이든 대통령이 백악관에서 연설했다
마스킹: [MASK][MASK][MASK] 대통령이 [MASK][MASK][MASK]에서 연설했다
```

개체 전체가 마스킹되면 문맥 단서만으로 "바이든"과 "백악관"을 추론해야 하므로, 모델은 자연스럽게 실세계 지식을 내재화하게 된다.

### Dialogue Language Model (DLM)

ERNIE는 대화 맥락 학습을 위한 추가 태스크인 **DLM**을 도입했다. 다중 턴 대화 데이터에서 질문-응답 쌍의 관련성을 판단하는 태스크로, 개방형 대화 이해 능력을 사전 학습 단계에 내재화한다.

### ERNIE 2.0: 연속 멀티태스크 사전 학습

ERNIE 2.0은 7가지 학습 태스크를 동시에 학습하는 **Continual Multi-task Pre-training**으로 확장되었다:

| 태스크 유형 | 세부 태스크 |
|------------|------------|
| **단어 수준** | Knowledge Masking, Token-Document Relation |
| **구조 수준** | Sentence Reordering, Sentence Distance |
| **의미 수준** | Discourse Relation, IR Relevance, Entity Masking |

## 핵심 혁신

### 1. 지식 통합 사전 학습

기존 BERT가 순수 텍스트 통계에만 의존하는 반면, ERNIE는 개체명, 구문 구조, 지식 그래프 정보를 학습 과정에 통합한다. 이는 모델이 단순한 언어 패턴을 넘어 세계 지식을 내재화하도록 유도하는 선구적 접근법이다.

### 2. 중국어 NLP 특화

중국어는 공백 없이 문자가 연결되는 특성상, 토큰 수준 마스킹이 영어보다 더 비효율적이다. ERNIE의 개체/구문 마스킹은 이 특성에 특히 효과적이며, 중국어 NLP 생태계에서 BERT 대비 확실한 우위를 점했다.

### 3. 다중 소스 데이터 활용

위키피디아, 백과사전, 뉴스, 커뮤니티(Tieba) 등 다양한 소스의 데이터를 학습에 활용하여 지식의 범위와 깊이를 확대했다.

## 벤치마크/성능

| 벤치마크 | BERT-Chinese | ERNIE | 개선폭 |
|---------|-------------|-------|--------|
| **XNLI** | 77.8% | **79.9%** | +2.1%p |
| **CMRC** (F1) | 82.7 | **87.5** | +4.8 |
| **MSRA NER** | 92.6% | **93.8%** | +1.2%p |
| **LCQMC** | 87.0% | **89.7%** | +2.7%p |
| **ChnSentiCorp** | 94.3% | **95.4%** | +1.1%p |

ERNIE 2.0은 GLUE 영어 벤치마크에서도 BERT를 크게 능가하며 다국어 범용성을 입증했다.

## 관련 모델 비교

| 특성 | BERT | ERNIE | ERNIE 2.0 | RoBERTa |
|------|------|-------|-----------|----------|
| **마스킹** | 토큰 | **개체+구문** | 7가지 태스크 | 토큰 |
| **지식 통합** | 없음 | **있음** | 강화 | 없음 |
| **주 대상 언어** | 영어 | **중국어** | 다국어 | 영어 |
| **대화 학습** | 없음 | **DLM** | 확장 | 없음 |
| **연속 학습** | 없음 | 없음 | **있음** | 없음 |

## 학습 상세

- **데이터**: 중국어 위키피디아 + 바이두 백과사전 + 바이두 뉴스 + 바이두 Tieba (총 수십 GB)
- **어휘**: 중국어 BPE 18,000 vocab
- **학습 절차**: BERT 사전 학습 후 Phrase/Entity 마스킹으로 추가 학습
- **옵티마이저**: Adam, lr=5e-4
- **배치 크기**: 512
- **학습 스텝**: 500K
- **프레임워크**: PaddlePaddle (Baidu의 자체 프레임워크)

## 실무 활용

### 1. 중국어 NER (개체명 인식)

```python
import paddle
from paddlenlp.transformers import ErnieTokenizer, ErnieForTokenClassification

tokenizer = ErnieTokenizer.from_pretrained('ernie-1.0')
model = ErnieForTokenClassification.from_pretrained('ernie-1.0', num_classes=7)
# Entity Masking으로 사전 학습된 ERNIE가 NER에서 특히 우수한 성능
```

### 2. 중국어 검색 및 추천

바이두 검색 엔진에서 실제로 ERNIE를 활용하여 검색 관련성 판단과 문서 이해를 수행한다.

### 3. 다국어 크로스-링구얼 전이

ERNIE 2.0 이후 다국어 지원이 강화되어, 중국어-영어 간 크로스-링구얼 태스크에도 활용된다.

## 한계 및 전망

### 한계

1. **PaddlePaddle 종속성**: Baidu의 자체 프레임워크에 의존하여 PyTorch/TensorFlow 생태계와의 호환성이 제한적이다.
2. **개체명 인식 의존**: Entity Masking을 위해 개체명 인식(NER) 전처리가 필요하다.
3. **인코더 전용**: BERT와 마찬가지로 생성 태스크에는 부적합하다.

### 전망

ERNIE의 "지식 통합 사전 학습" 개념은 이후 ERNIE 3.0(2021, 100B+), ERNIE Bot(2023, ChatGPT 경쟁), ERNIE 4.0으로 이어지며 Baidu의 LLM 전략의 핵심이 되었다. 구조화된 지식을 언어 모델에 주입하는 접근법은 RAG(검색 증강 생성)와 함께 현대 LLM의 사실성 향상에 중요한 방향을 제시한다.

---

**참고 논문**: [ERNIE: Enhanced Representation through Knowledge Integration](https://arxiv.org/abs/1904.09223) (Sun et al., 2019)

## 관련 문서

- [[bert|BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding]] — 영감
