---
title: Amazon SageMaker Model Registry 개요 및 워크플로
slug: "amazon-sagemaker-model-registry-개요-및-워크플로"
category: cloud
tags: ["amazon-sagemaker", "aws", "ci-cd", "mlops", "model-deployment", "model-management", "model-registry", "model-versioning", "pipelines"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.643548+00:00"
---

Amazon SageMaker Model Registry를 사용하면 다음 작업을 수행할 수 있습니다.

- 프로덕션용 모델을 카탈로그화합니다.
- 모델 버전을 관리합니다.
- 훈련 지표와 같은 메타데이터를 모델과 연결합니다.
- 등록된 모델의 Amazon SageMaker Model Cards에서 정보를 봅니다.
- 모델 계보를 보고 추적성과 재현성을 확인합니다.
- 모델 수명 주기 동안 모델이 진행할 수 있는 스테이징 구성을 정의합니다.
- 모델의 승인 상태를 관리합니다.
- 모델을 프로덕션에 배포합니다.
- CI/CD를 사용하여 모델 배포를 자동화합니다.
- 다른 사용자와 모델을 공유합니다.

SageMaker 모델 레지스트리에서는 다양한 버전의 모델을 포함하는 모델(패키지) 그룹을 생성하여 모델을 카탈로그화할 수 있습니다. 특정 문제를 해결하기 위해 훈련한 모든 모델을 추적하는 모델 그룹을 생성한 다음, 훈련한 각 모델을 등록하면 모델 레지스트리가 해당 모델을 모델 그룹에 새 모델 버전으로 추가합니다. 마지막으로 모델 그룹을 SageMaker 모델 레지스트리 컬렉션에 추가하여 모델 그룹의 카테고리를 구성할 수 있습니다. 일반적인 워크플로는 다음과 같습니다.

- 모델 그룹을 생성합니다.
- 모델을 학습시키는 ML 파이프라인을 만듭니다. SageMaker Pipelines에 대한 자세한 내용은 [Pipelines 작업](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/pipelines-build.html) 섹션을 참조하세요.
- ML 파이프라인을 실행할 때마다 모델 버전을 생성하여 첫 단계에서 만든 모델 그룹에 등록합니다.
- 모델 그룹을 하나 이상의 모델 레지스트리 컬렉션에 추가합니다.

모델, 모델 버전 및 모델 그룹을 생성하고 사용하는 방법에 대한 자세한 내용은 [모델 레지스트리 모델, 모델 버전, 모델 그룹](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-registry-models.html) 섹션을 참조하세요. 선택적으로 모델 그룹을 컬렉션으로 추가로 그룹화하려면 [모델 레지스트리 컬렉션](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/modelcollections.html) 섹션을 참조하세요.

https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-registry.html