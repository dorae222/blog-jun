# ELECTRA: 효율적 사전 학습의 새로운 패러다임

## 개요

**ELECTRA**(Efficiently Learning an Encoder that Classifies Token Replacements Accurately)는 2020년 3월 Stanford University와 Google Brain이 공동 발표한 사전 학습 모델로, BERT의 MLM(Masked Language Modeling) 사전 학습 방식이 가진 근본적 비효율성을 해결한 모델이다.

BERT의 MLM은 입력 토큰 중 15%만 마스킹하고 나머지 85%에서는 학습 신호를 받지 못한다. 이는 곧 각 학습 배치에서 토큰의 대부분이 모델 업데이트에 기여하지 않는다는 뜻이다. ELECTRA는 이 문제를 **Replaced Token Detection(RTD)**라는 새로운 사전 학습 태스크로 해결하여, **모든 입력 토큰(100%)을 학습 신호로 활용**한다. 결과적으로 ELECTRA-Small은 BERT-Base의 1/4 연산량으로 동일 성능을, ELECTRA-Large는 GLUE 90.9점으로 RoBERTa와 동등한 성능을 절반의 연산량으로 달성했다.

**참고 논문**: [ELECTRA](https://arxiv.org/abs/2003.10555) (Clark et al., 2020) | [코드](https://github.com/google-research/electra)

## 아키텍처 상세

### Generator-Discriminator 구조

ELECTRA는 GAN(Generative Adversarial Network)과 유사한 **생성기(Generator)-판별기(Discriminator)** 이중 구조를 사용하지만, 적대적 학습이 아닌 최대 우도(maximum likelihood) 학습을 적용한다.

| 구성 요소 | Generator | Discriminator |
|-----------|-----------|---------------|
| **역할** | [MASK] 토큰 복원 | 교체 토큰 탐지 |
| **크기** | 판별기의 1/4 | 전체 크기 |
| **학습 방법** | MLM (BERT와 동일) | RTD (이진 분류) |
| **사후 활용** | 폐기 | 다운스트림 파인튜닝 |

### 모델 사양

| 구성 요소 | Small | Base | Large |
|-----------|-------|------|-------|
| **파라미터** | 14M | 110M | 335M |
| **히든 차원** | 256 | 768 | 1024 |
| **레이어** | 12 | 12 | 24 |
| **어텐션 헤드** | 4 | 12 | 16 |
| **컨텍스트** | 512 | 512 | 512 |
| **어휘** | 30,522 | 30,522 | 30,522 |

### RTD 학습 과정

학습은 다음 4단계로 진행된다:

1. **마스킹**: 입력 시퀀스의 15% 토큰을 [MASK]로 교체
2. **생성**: 소형 Generator가 [MASK] 위치의 토큰을 예측하여 교체
3. **판별**: Discriminator가 **모든 위치**에서 "원본(original) vs 교체됨(replaced)"을 이진 분류
4. **업데이트**: Generator는 MLM 손실로, Discriminator는 RTD 손실로 동시 학습

### 손실 함수

전체 학습 손실은 Generator와 Discriminator 손실의 가중합이다:

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{MLM}}(\theta_G) + \lambda \cdot \mathcal{L}_{\text{RTD}}(\theta_D)$$

여기서 RTD 손실은 모든 위치 $t$에 대한 이진 크로스엔트로피이다:

$$\mathcal{L}_{\text{RTD}} = -\sum_{t=1}^{T} \left[ y_t \log D(x_t) + (1-y_t) \log(1 - D(x_t)) \right]$$

$y_t = 1$이면 원본, $y_t = 0$이면 교체된 토큰이다. MLM이 15% 위치에서만 학습하는 반면, RTD는 **T개 전체 위치에서 학습 신호**를 받으므로 샘플 효율이 약 4배 높다.

### Generator 크기 비율의 중요성

Generator와 Discriminator의 크기 비율은 성능에 큰 영향을 미친다. 논문에서 1:1, 1:2, 1:4 등 다양한 비율을 실험한 결과, **Generator가 Discriminator의 1/4일 때 최적**이라는 결론을 도출했다. Generator가 너무 크면 교체된 토큰이 원본과 너무 유사해져 판별이 쉬워지고, 너무 작으면 학습 신호가 노이즈가 된다.

## 핵심 혁신

### 1. 100% 토큰 활용의 학습 효율성

BERT의 MLM은 15% 마스킹 비율로 인해 각 배치에서 85%의 토큰이 낭비된다. ELECTRA의 RTD는 모든 토큰에서 학습하므로, 동일 연산량 대비 약 4배 많은 학습 신호를 얻는다.

### 2. 소형 모델에서의 압도적 효율

ELECTRA-Small(14M)은 GPT-1(110M)과 유사한 GLUE 성능을 달성하면서 파라미터는 1/8에 불과하다. 이는 제한된 연산 자원 환경에서 특히 큰 의미를 가진다.

### 3. GAN 구조의 NLP 적용

GAN의 Generator-Discriminator 프레임워크를 NLP 사전 학습에 성공적으로 적용한 첫 사례다. 단, 실제 적대적 학습이 아닌 MLM 기반 학습을 사용하여 학습 안정성을 확보했다.

## 벤치마크/성능

| 벤치마크 | BERT-Base | BERT-Large | ELECTRA-Base | ELECTRA-Large |
|---------|----------|-----------|-------------|---------------|
| **GLUE** | 79.6 | 84.6 | **85.1** | **90.9** |
| **SQuAD 2.0** | 76.3 | 81.8 | **86.8** | **88.7** |
| **연산량** | 1x | 4x | 1x | 4x |
| **대비 효율** | 기준 | 기준 | BERT-Base +5.5 | XLNet 능가 |

ELECTRA-Large는 GLUE 90.9로 BERT-Large(84.6), XLNet(90.5)을 모두 앞질렀으며, RoBERTa와 동등한 성능을 **절반의 연산량**으로 달성했다.

## 관련 모델 비교

| 특성 | BERT | RoBERTa | ELECTRA | ALBERT |
|------|------|---------|---------|--------|
| **학습 태스크** | MLM+NSP | MLM (no NSP) | **RTD** | MLM+SOP |
| **토큰 활용률** | 15% | 15% | **100%** | 15% |
| **효율화 방식** | - | 더 많은 데이터 | **학습 신호 밀도** | 파라미터 공유 |
| **GLUE (Large)** | 84.6 | 88.5 | **90.9** | 89.4 |
| **파라미터 (Base)** | 110M | 125M | 110M | 12M |

## 학습 상세

- **데이터**: BooksCorpus + English Wikipedia (BERT와 동일, 약 16GB)
- **옵티마이저**: Adam, lr=2e-4, $\beta$=(0.9, 0.999)
- **배치 크기**: 256
- **학습 기간**: Small: 1 GPU 4일, Base: 4 GPU 2일, Large: 64 V100 4일
- **토크나이저**: WordPiece 30,522 vocab
- **Dynamic Masking**: RoBERTa와 유사하게 매 에포크마다 마스킹 패턴 변경

## 실무 활용

### 1. 자원 제한 환경의 NLP

```python
from transformers import ElectraTokenizer, ElectraForSequenceClassification

tokenizer = ElectraTokenizer.from_pretrained('google/electra-small-discriminator')
model = ElectraForSequenceClassification.from_pretrained(
    'google/electra-small-discriminator', num_labels=2
)
# 14M 파라미터로 BERT-Base급 성능 달성
```

### 2. 모바일/엣지 배포

ELECTRA-Small(14M)은 모바일 기기에서도 실시간 추론이 가능한 크기로, ONNX 변환 후 경량 NLP 서비스에 적합하다.

### 3. 대규모 문서 분류

BERT 대비 더 적은 연산으로 동등한 분류 성능을 얻을 수 있어, 대규모 문서 분류 파이프라인의 비용을 절감한다.

## 한계 및 전망

### 한계

1. **생성 태스크 부적합**: 인코더 전용 모델이므로 텍스트 생성에는 사용할 수 없다.
2. **Generator 학습 낭비**: 사전 학습 후 Generator를 폐기하므로 학습 자원의 일부가 낭비된다.
3. **하이퍼파라미터 민감성**: Generator-Discriminator 크기 비율, $\lambda$ 가중치 등 추가 하이퍼파라미터가 존재한다.

### 전망

ELECTRA의 "학습 신호 밀도 극대화" 개념은 이후 DeBERTa, ALBERT v2 등에 영향을 미쳤으며, 효율적 사전 학습 연구의 중요한 방향성을 제시했다. LLM 시대에서도 사전 학습의 연산 효율성은 핵심 과제로 남아 있으며, ELECTRA의 아이디어는 여전히 유효하다.

---

**참고 논문**: [ELECTRA: Pre-training Text Encoders as Discriminators Rather Than Generators](https://arxiv.org/abs/2003.10555) (Clark et al., 2020)

## 관련 문서

- [[bert|BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding]] — 발전 기반
