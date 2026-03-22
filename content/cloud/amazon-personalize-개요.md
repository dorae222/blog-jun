---
title: Amazon Personalize 개요
slug: "amazon-personalize-개요"
category: cloud
tags: ["amazon-personalize", "aws", "batch-processing", "data-wrangler", "machine-learning", "personalization", "real-time", "recommendation-systems", "sagemaker"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.458434+00:00"
---

Amazon Personalize는 데이터를 사용하여 사용자에게 항목 추천을 생성하는 완전관리형 기계 학습 서비스입니다. 또한 특정 항목 또는 항목 메타데이터에 대한 사용자의 선호도를 기반으로 사용자 세그먼트를 생성할 수 있습니다.

일반적인 사용 사례는 다음과 같습니다.

- **동영상 스트리밍 앱 개인 맞춤** — 사전 구성되거나 사용자 지정 가능한 Personalize 리소스를 사용하여 스트리밍 앱에 여러 유형의 개인 맞춤형 동영상 추천을 추가할 수 있습니다. 예: 가장 적합한 추천 제품, X와 유사한 제품, 가장 인기 있는 제품 동영상 추천 등.

- **전자상거래 앱에 제품 추천 추가** — 사전 구성되거나 사용자 지정 가능한 Personalize 리소스를 사용하여 여러 유형의 개인 맞춤형 제품 추천을 소매 앱에 추가할 수 있습니다. 예: 추천 제품, 자주 함께 구매한 제품 및 X를 본 고객도 보는 제품 추천.

- **앱에 실시간 차선책(백업) 작업 추천 추가** — 사용자 지정 가능한 Amazon Personalize 리소스를 사용하여 사용자의 행동을 기반으로 사용자가 행할 가능성이 가장 높은 작업을 추천할 수 있습니다. 예: 로열티 프로그램 등록, 모바일 앱 다운로드 또는 홍보 이메일 구독을 위한 실시간 추천 추가.

- **개인 맞춤형 이메일 생성** — 사용자 지정 가능한 Personalize 리소스를 사용하여 이메일 목록의 모든 사용자에 대한 배치 추천을 생성할 수 있습니다. 그런 다음 [AWS 서비스](https://docs.aws.amazon.com/ko_kr/personalize/latest/dg/what-is-personalize.html#related-services) 또는 [타사 서비스](https://docs.aws.amazon.com/ko_kr/personalize/latest/dg/what-is-personalize.html#third-parties)를 사용해 카탈로그의 항목을 추천하는 개인 맞춤형 이메일을 보낼 수 있습니다.

- **타겟 마케팅 캠페인 생성** — Personalize를 사용하여 카탈로그의 항목과 상호작용할 가능성이 높은 사용자 세그먼트를 생성할 수 있습니다. 그런 다음 [AWS 서비스](https://docs.aws.amazon.com/ko_kr/personalize/latest/dg/what-is-personalize.html#related-services) 또는 [타사](https://docs.aws.amazon.com/ko_kr/personalize/latest/dg/what-is-personalize.html#third-parties) 서비스를 사용해 다양한 항목을 다양한 사용자 세그먼트에 홍보하는 타겟 마케팅 캠페인을 만들 수 있습니다.

- **검색 결과 개인 맞춤** — 사용자 지정 가능한 Personalize 리소스를 사용하여 사용자에 맞게 검색 결과를 개인화할 수 있습니다. 예를 들어, Personalize는 [OpenSearch](https://docs.aws.amazon.com/ko_kr/personalize/latest/dg/personalize-opensearch.html)로 생성한 검색 결과의 순위를 다시 매길 수 있습니다.

대부분의 사용 사례에서 Amazon Personalize는 주로 항목 상호작용 데이터를 기반으로 추천을 생성합니다. 항목 상호작용 데이터는 사용자가 카탈로그의 항목과 상호작용하면서 생성되며, 예를 들어 사용자가 항목을 클릭하는 경우가 있습니다. 항목 상호작용 데이터는 과거의 대량 상호작용 레코드를 담은 CSV 파일과 사용자가 카탈로그와 상호작용할 때 발생하는 실시간 이벤트 모두에서 가져올 수 있습니다. Amazon Personalize는 장르, 가격, 성별 등 항목 및 사용자 메타데이터도 활용합니다. 또한 차선책(백업) 작업 시나리오에서는 작업 및 작업 상호작용 데이터가 사용됩니다.

대량 데이터를 가져올 때는 Amazon SageMaker AI Data Wrangler를 사용하여 40개 이상의 소스에서 데이터를 가져오고 Personalize에 맞게 준비할 수 있습니다. 자세한 내용은 [Amazon SageMaker AI Data Wrangler를 사용하여 대량 데이터 준비 및 가져오기](https://docs.aws.amazon.com/ko_kr/personalize/latest/dg/preparing-importing-with-data-wrangler.html) 단원을 참조하십시오.

Personalize에는 실시간 개인 맞춤을 위한 API 작업과 대량 추천 및 사용자 세그먼트를 위한 배치 작업이 포함되어 있습니다. 비즈니스 도메인에 맞춘 사전 최적화된 추천으로 빠르게 시작하거나 구성 가능한 사용자 지정 리소스를 직접 생성하여 사용할 수 있습니다.

자세한 내용은 공식 문서를 참고하세요: https://docs.aws.amazon.com/ko_kr/personalize/latest/dg/what-is-personalize.html