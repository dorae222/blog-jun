---
title: "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding"
slug: bert
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.416136+00:00"
architecture_entry: bert
---

## 개요

**BERT(Bidirectional Encoder Representations from Transformers)**는 Google AI Language 팀의 Devlin et al.(2018)이 발표한 획기적인 사전 학습 언어 모델입니다. 기존의 단방향 언어 모델과 달리, Transformer 인코더의 Self-Attention을 활용해 **모든 레이어에서 왼쪽과 오른쪽 문맥을 동시에** 고려합니다. GLUE, SQuAD, SWAG 등 11개 NLP 벤치마크에서 당시 최고 성능을 기록했으며, 사전 학습 + 파인튜닝 패러다임을 NLP 전반에 정착시킨 핵심 논문입니다.

## 배경 및 문제 정의

### 기존 사전 학습 방식의 한계

BERT 이전에는 크게 두 가지 방식으로 언어 표현을 사전 학습했습니다:

1. **특성 기반(Feature-based) 방식**: ELMo처럼 사전 학습된 표현을 다운스트림 태스크의 특성으로 사용. 하지만 단방향(좌→우 또는 우→좌) 또는 단순 연결(concatenation) 방식으로 양방향 문맥을 완전히 활용하지 못함
2. **Fine-tuning 방식**: GPT처럼 사전 학습 파라미터를 다운스트림 태스크에 맞게 미세 조정. 하지만 GPT는 좌→우 단방향 언어 모델이라 각 토큰이 이전 토큰만 볼 수 있음

질의응답, 자연어 추론 같은 태스크는 양방향 문맥 이해가 필수적인데, 이를 충족시키는 모델이 없었습니다.

### "깊은 양방향"의 필요성

"양방향"을 단순히 구현하면 각 단어가 자기 자신을 간접적으로 "볼" 수 있어(trivial prediction) 의미 있는 학습이 어렵습니다. BERT는 이를 **Masked Language Modeling**으로 해결합니다.

## 핵심 아이디어

### 1. Masked Language Modeling (MLM)

입력 토큰의 15%를 무작위로 마스킹하고, 마스킹된 토큰을 예측하도록 모델을 훈련합니다:

$$\mathcal{L}_{\text{MLM}} = -\mathbb{E}_{x \sim \mathcal{D}} \sum_{i \in \mathcal{M}} \log P(x_i \mid \hat{x})$$

여기서 $\mathcal{M}$은 마스킹된 위치의 집합, $\hat{x}$는 마스킹된 입력입니다.

마스킹 전략:
- 80%: `[MASK]` 토큰으로 교체
- 10%: 랜덤 토큰으로 교체
- 10%: 원래 토큰 유지

이 전략으로 모델은 어떤 토큰이 마스킹되었는지 알 수 없어 모든 토큰의 표현을 학습하게 됩니다.

### 2. Next Sentence Prediction (NSP)

두 문장 A, B가 주어졌을 때 B가 A의 실제 다음 문장인지 이진 분류:

- **IsNext**: 50% 확률로 실제 다음 문장
- **NotNext**: 50% 확률로 코퍼스에서 랜덤 추출한 문장

이 태스크는 질의응답, 자연어 추론처럼 두 문장 간의 관계를 이해해야 하는 태스크를 위해 설계되었습니다.

### 입력 표현

BERT의 입력은 세 가지 임베딩의 합으로 구성됩니다:

$$E_{\text{input}} = E_{\text{token}} + E_{\text{segment}} + E_{\text{position}}$$

- **Token Embedding**: WordPiece 토크나이저로 분리된 서브워드 임베딩
- **Segment Embedding**: 문장 A/B 구분
- **Position Embedding**: 위치 정보 (학습된 파라미터)

특수 토큰:
- `[CLS]`: 분류 태스크에 사용하는 문장 표현
- `[SEP]`: 문장 구분자

## 아키텍처 / 방법론

BERT는 Transformer 인코더만을 사용합니다. 두 가지 크기를 제안합니다:

| 모델 | 레이어 수 ($L$) | 히든 크기 ($H$) | 어텐션 헤드 ($A$) | 파라미터 수 |
|------|-------------|--------------|----------------|----------|
| BERT-Base | 12 | 768 | 12 | 110M |
| BERT-Large | 24 | 1024 | 16 | 340M |

### 다운스트림 태스크 파인튜닝

BERT는 최소한의 수정으로 다양한 태스크에 적용할 수 있습니다:

- **문장 분류**: `[CLS]` 토큰 위에 분류 레이어 추가
- **토큰 분류(NER, POS)**: 각 토큰 출력 위에 레이어 추가
- **질의응답(SQuAD)**: 시작·끝 위치 예측 레이어 추가
- **자연어 추론(NLI)**: 문장 쌍 입력 후 `[CLS]` 분류

## 실험 결과

### GLUE 벤치마크

| 모델 | MNLI(m/mm) | QQP | QNLI | SST-2 | CoLA | STS-B | MRPC | RTE | **평균** |
|------|-----------|-----|------|-------|------|-------|------|-----|--------|
| GPT | 82.1/81.4 | 70.3 | 87.4 | 91.3 | 45.4 | 80.0 | 82.3 | 56.0 | 72.8 |
| BERT-Base | 84.6/83.4 | 71.2 | 90.5 | 93.5 | 52.1 | 85.8 | 88.9 | 66.4 | 79.6 |
| **BERT-Large** | **86.7/85.9** | **72.1** | **92.7** | **94.9** | **60.5** | **86.5** | **89.3** | **70.1** | **82.1** |

### SQuAD 1.1 (질의응답)

| 모델 | EM | F1 |
|------|-----|----|
| 앙상블 최고 성능 (이전) | 86.0 | 91.7 |
| BERT-Base | 80.8 | 88.5 |
| **BERT-Large** | **84.1** | **90.9** |
| BERT-Large (앙상블) | **87.4** | **93.2** |

### Ablation Study

| 모델 | MNLI | SQuAD |
|------|------|-------|
| BERT-Base | 84.6 | 88.5 |
| - NSP 제거 | 83.9 | 88.0 |
| - MLM → 좌→우 LM | 82.1 | 84.3 |
| - 양방향성 제거 | 79.1 | 83.2 |

## 의의 및 한계

### 의의

- **사전 학습 + 파인튜닝 패러다임 확립**: 레이블 데이터 없이도 강력한 범용 표현을 학습하고, 소량의 레이블 데이터로 파인튜닝하는 방식을 NLP 표준으로 만들었습니다
- **양방향 문맥 학습**: 모든 레이어에서 양방향 Attention을 활용해 문장 내 단어들의 풍부한 문맥적 의미를 포착
- **광범위한 영향**: RoBERTa, ALBERT, DistilBERT, XLNet, DeBERTa 등 수많은 후속 연구의 기반

### 한계

- **[MASK] 토큰 불일치**: 사전 학습 시 사용한 `[MASK]` 토큰이 파인튜닝 시에는 등장하지 않아 train-test mismatch 발생
- **NSP의 효과 논란**: 이후 RoBERTa 연구에서 NSP가 실제로는 성능에 큰 도움이 안 될 수 있음을 보임
- **단방향 생성 불가**: 인코더 구조이므로 텍스트 생성에 직접 활용하기 어려움
- **[MASK] 위치 독립 가정**: MLM은 마스킹된 토큰들이 서로 독립적이라 가정하여 토큰 간 상관관계를 완전히 포착하지 못함 (XLNet이 이를 해결)
- **고정 길이 제약**: 최대 512 토큰으로 긴 문서 처리에 제한\n\n## 코드 예제\n\n### BERT 파인튜닝 (Hugging Face Transformers)\n\n```python\nimport torch\nfrom transformers import BertTokenizer, BertForSequenceClassification\nfrom torch.optim import AdamW\n\n# BERT 토크나이저 & 모델 로드\ntokenizer = BertTokenizer.from_pretrained('bert-base-uncased')\nmodel = BertForSequenceClassification.from_pretrained(\n    'bert-base-uncased', num_labels=2\n)\n\ndef tokenize(texts, max_length=128):\n    \"\"\"텍스트를 BERT 입력 형식으로 변환.\"\"\"\n    return tokenizer(\n        texts, padding='max_length', truncation=True,\n        max_length=max_length, return_tensors='pt'\n    )\n\n# 예시 데이터\ntexts = [\"I love this movie!\", \"This film was terrible.\"]\nlabels = torch.tensor([1, 0])  # positive/negative\n\n# 토크나이징\ninputs = tokenize(texts)\nprint(\"input_ids shape:\", inputs['input_ids'].shape)  # (2, 128)\n# [CLS] 토큰(id=101)이 각 시퀀스 시작, [SEP] 토큰(id=102)이 끝\nprint(\"첫 번째 시퀀스 앞 5개 토큰:\", inputs['input_ids'][0][:5].tolist())\n\n# 순전파\noptimizer = AdamW(model.parameters(), lr=2e-5)\nmodel.train()\noutputs = model(**inputs, labels=labels)\nloss = outputs.loss\nlogits = outputs.logits\nprint(f\"Loss: {loss.item():.4f}\")\nprint(f\"Logits: {logits}\")  # (2, 2) — num_labels=2\n\n# 역전파\nloss.backward()\noptimizer.step()\noptimizer.zero_grad()\n\n# 추론\nmodel.eval()\nwith torch.no_grad():\n    test_inputs = tokenize([\"An excellent performance!\"])\n    pred = model(**test_inputs).logits.argmax(dim=-1)\nprint(\"예측 클래스:\", pred.item())  # 0: negative, 1: positive\n```\n\n> **Note**: `[CLS]` 토큰의 최종 히든 상태가 분류 헤드의 입력으로 사용됩니다. BERT는 MLM으로 사전 학습된 표현을 파인튜닝만으로 활용합니다.