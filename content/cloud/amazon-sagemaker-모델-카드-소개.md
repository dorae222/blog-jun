---
title: Amazon SageMaker 모델 카드 소개
slug: "amazon-sagemaker-모델-카드-소개"
category: cloud
tags: ["amazon-sagemaker", "aws", "machine-learning", "mlops", "model-cards", "model-documentation", "model-governance", "responsible-ai"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.866182+00:00"
---

Amazon SageMaker 모델 카드를 사용하면 기계 학습(ML) 모델에 대한 주요 세부 정보를 한곳에 문서화하여 거버넌스 및 보고를 간소화할 수 있습니다. 모델 카드는 모델 수명 주기 전반에 걸쳐 중요한 정보를 캡처하며 책임 있는 AI 관행을 구현하는 데 도움이 됩니다.

모델 카드는 모델의 용도와 위험 등급, 학습 세부 정보 및 지표, 평가 결과 및 관찰, 추가 설명(예: 고려 사항, 권장 사항, 사용자 지정 정보)과 같은 항목을 체계적으로 정리합니다. 모델 카드를 활용하면 다음 작업을 수행할 수 있습니다.

- 모델 사용 방법에 대한 지침을 제공합니다.
- 모델 훈련과 성능에 대한 상세 설명으로 감사 활동을 지원합니다.
- 비즈니스 목표를 지원하기 위한 모델의 용도를 전달합니다.

모델 카드는 문서화할 정보에 대한 권장 가이드를 제시하며 사용자 지정 정보 필드를 포함합니다. 모델 카드를 만든 후에는 PDF로 내보내거나 다운로드하여 관련 이해관계자와 공유할 수 있습니다. 모델 카드의 승인 상태를 업데이트하는 것을 제외한 모든 편집은 모델 변경 내역의 불변 기록을 유지하기 위해 새 버전의 모델 카드를 생성합니다.

###### 주제

- [사전 조건](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-cards.html#model-cards-prerequisites)
- [모델의 용도](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-cards.html#model-cards-intended-uses)
- [위험 등급](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-cards.html#model-cards-risk-rating)
- [모델 카드 JSON 스키마](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-cards.html#model-cards-json-schema)
- [모델 카드 생성](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-cards-create.html)
- [모델 카드 작업](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-cards-manage.html)
- [Amazon SageMaker Model Cards에 대한 교차 계정 지원 설정](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-cards-xaccount.html)
- [모델 카드용 하위 수준 SageMaker API](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-cards-apis.html)
- [모델 카드 FAQ](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-cards-faqs.html)

## 사전 조건

Amazon SageMaker 모델 카드를 사용하려면 모델 카드를 생성, 편집, 보고 및 내보낼 수 있는 권한이 있어야 합니다.

## 모델의 용도

모델의 용도를 명시하면 모델 개발자와 사용자가 모델을 책임감 있게 훈련·배포하는 데 필요한 정보를 확보할 수 있습니다. 모델의 용도 설명에는 해당 모델을 사용하기에 적합한 시나리오와 사용이 권장되지 않는 시나리오를 모두 포함해야 합니다.

다음 항목을 포함하는 것이 좋습니다.

- 모델의 일반 목적
- 모델의 의도된 사용 사례
- 모델의 의도하지 않은 사용 사례
- 모델을 개발할 때 세운 전제

모델의 용도 설명은 기술적 세부 사항을 넘어 프로덕션 환경에서 모델을 어떻게 활용할지, 어떤 시나리오에 적합한지, 추가 고려 사항(예: 모델에 사용할 데이터 유형 또는 개발 중 가정한 사항) 등을 명확히 해야 합니다.

## 위험 등급

개발자는 서로 다른 위험 수준을 가진 여러 사용 사례에 맞춘 ML 모델을 만듭니다. 예를 들어 대출 승인 모델은 이메일 분류 모델보다 더 높은 위험을 가질 수 있습니다. 모델 카드에는 모델의 다양한 위험 프로필을 반영하여 위험 등급을 분류할 수 있는 필드가 제공됩니다.

이 위험 등급 값은 `unknown`, `low`, `medium` 또는 `high`가 될 수 있습니다. 이러한 필드를 사용해 알 수 없음, 낮음, 중간 또는 고위험 모델에 라벨을 부여함으로써 조직이 특정 모델을 프로덕션에 적용할 때의 내부 규정을 준수하도록 돕습니다.

https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-cards.html