---
title: Amazon Comprehend 개요
slug: "amazon-comprehend-개요"
category: cloud
tags: ["amazon-comprehend", "aws", "language-detection", "machine-learning", "named-entity-recognition", "nlp", "sentiment-analysis", "text-analysis"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:04.968415+00:00"
---

> **NOTE:**
> - 텍스트 안에서 특정 항목을 찾아내는 서비스
> - 예: 분석 보고서에서 회사 이름 찾기, 부정적인 후기 식별, 또는 고객 서비스 상담에서 긍정적인 상호작용 탐지

Amazon Comprehend는 자연어 처리를 사용해 문서 내용에서 인사이트를 추출하는 서비스입니다. 문서 내의 개체(entity), 핵심 문구(key phrase), 언어, 감정(sentiment) 및 기타 일반적인 요소를 인식하여 의미 있는 인사이트를 제공합니다. 이를 통해 문서 구조에 대한 이해를 바탕으로 신규 서비스나 기능을 개발할 수 있습니다. 예를 들어, 소셜 네트워크 피드에서 제품에 대한 언급을 탐지하거나 대규모 문서 저장소에서 주요 문구를 스캔할 수 있습니다.

Amazon Comprehend 콘솔이나 API를 통해 문서 분석 기능에 접근할 수 있습니다. 소규모 워크로드에 대해서는 실시간 분석을 실행할 수 있고, 대규모 문서 집합에 대해서는 비동기식 분석 작업을 시작할 수 있습니다. 또한 Amazon Comprehend가 제공하는 사전 학습된 모델을 그대로 사용할 수 있으며, 분류(classification)와 개체 인식을 위해 자체 사용자 정의 모델을 학습시켜 사용할 수도 있습니다.

Amazon Comprehend는 분석 모델의 품질을 지속적으로 개선하기 위해 사용자의 콘텐츠를 저장할 수 있습니다. 자세한 내용은 [Amazon Comprehend 요금](https://aws.amazon.com/comprehend/faqs/)을 참조하세요.

모든 Amazon Comprehend 기능은 UTF-8 인코딩된 텍스트 문서를 입력으로 받습니다. 추가로 사용자 정의 분류 및 사용자 정의 개체 인식(custom entity recognition)은 이미지 파일, PDF 파일 및 Word 파일을 입력으로 처리할 수 있습니다.

Amazon Comprehend는 기능에 따라 여러 언어로 문서를 검사하고 분석할 수 있습니다. 지원되는 언어 목록은 [Amazon Comprehend에서 지원되는 언어](https://docs.aws.amazon.com/ko_kr/comprehend/latest/dg/supported-languages.html)를 참고하세요. 또한 Amazon Comprehend의 [지배적 언어](https://docs.aws.amazon.com/ko_kr/comprehend/latest/dg/how-languages.html) 기능은 문서에서 우세한(지배적) 언어를 판별하여 더 다양한 언어에 적용할 수 있도록 도와줍니다.

https://docs.aws.amazon.com/ko_kr/comprehend/latest/dg/what-is.html