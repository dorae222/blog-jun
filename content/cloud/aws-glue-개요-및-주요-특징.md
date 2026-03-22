---
title: AWS Glue 개요 및 주요 특징
slug: "aws-glue-개요-및-주요-특징"
category: cloud
tags: ["aws", "aws-glue", "aws-glue-crawler", "aws-glue-studio", "data-catalog", "data-integration", "data-lake", "etl", "serverless"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.005428+00:00"
---

- Serverless
	- AWS Glue Data Catalog
	- AWS Glue Crawler
	- AWS Glue Studio
- AWS Glue는 배치 처리에 더 적합
- 데이터 분석을 위한 ETL(Extract, Transform and Load, 추출, 변환 및 로드) 서비스
- 다양한 소스에서 데이터 검색 및 추출, 데이터 강화, 정리, 정규화 및 결합, 데이터베이스, 데이터 웨어하우스 및 데이터 레이크에 데이터 로드 및 구성 등의 여러 작업을 포함

![](/media/posts/imported/aws/Pasted%20image%2020250609131154.png)
- AWS Glue에서 뷰를 생성하여 데이터에 대한 액세스를 제어 가능
	- 뷰를 통한 액세스 제어는 데이터 레벨의 세분화된 권한 관리에 적합하지 않음
	- 뷰를 통한 접근은 데이터의 실질적인 보안 제어를 제공하지 못할 수 있습니다.

Hive

---
AWS Glue는 분석 사용자가 여러 소스의 데이터를 쉽게 검색, 준비, 이동, 통합할 수 있도록 하는 서버리스 데이터 통합 서비스입니다. 분석, 기계 학습 및 애플리케이션 개발에 사용할 수 있습니다. 또한 작성, 작업 실행, 비즈니스 워크플로 구현을 위한 추가 생산성 및 데이터 운영 도구도 포함됩니다.

AWS Glue를 사용하면 70개 이상의 다양한 데이터 소스를 검색하여 연결하고 중앙 집중식 데이터 카탈로그에서 데이터를 관리할 수 있습니다. 추출, 변환, 로드(ETL) 파이프라인을 시각적으로 생성, 실행, 모니터링하여 데이터 레이크에 데이터를 로드할 수 있습니다. 또한 Amazon Athena, Amazon EMR, Amazon Redshift Spectrum을 사용하여 카탈로그화된 데이터를 즉시 검색하고 쿼리할 수 있습니다.

AWS Glue는 주요 데이터 통합 기능을 단일 서비스로 통합합니다. 여기에는 데이터 검색, 최신 ETL, 정제, 변환, 중앙 집중식 카탈로그화가 포함됩니다. 또한 서버리스이므로 관리할 인프라가 없습니다. ETL, ELT, 스트리밍과 같은 모든 워크로드를 하나의 서비스에서 유연하게 지원하므로 AWS Glue는 다양한 워크로드 및 사용자 유형에 걸쳐 사용자를 지원합니다.

또한 AWS Glue를 사용하면 아키텍처 전반에 걸쳐 데이터를 쉽게 통합할 수 있습니다. AWS 분석 서비스 및 Amazon S3 데이터 레이크와 통합됩니다. AWS Glue는 개발자에서 비즈니스 사용자에 이르기까지 모든 사용자가 사용하기 쉬운 통합 인터페이스 및 작업 작성 도구를 보유하고 있으며 다양한 기술 세트에 대한 맞춤형 솔루션을 제공합니다.

https://docs.aws.amazon.com/ko_kr/glue/latest/dg/what-is-glue.html