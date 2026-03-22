---
title: Amazon SageMaker 서버리스 추론
slug: "amazon-sagemaker-서버리스-추론"
category: cloud
tags: ["amazon-sagemaker", "auto-scaling", "aws", "inference", "mlops", "provisioned-concurrency", "serverless", "serverless-computing"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.677468+00:00"
---

> **NOTE:** 공식 문서 정의
> 이 기능을 통해 사용자는 인프라를 관리하지 않고도 추론 모델을 배포할 수 있습니다.
> 트래픽에 따라 자동으로 확장되며, 비용 효율적이고 서버리스 방식으로 예측을 수행하도록 특별히 설계되었습니다.

Amazon SageMaker 서버리스 추론은 기본 인프라를 구성하거나 관리하지 않고도 ML 모델을 배포하고 확장할 수 있도록 설계된 추론 옵션입니다. 온디맨드 서버리스 추론은 트래픽이 불규칙하거나 콜드 스타트를 허용할 수 있는 워크로드에 적합합니다. 서버리스 엔드포인트는 컴퓨팅 리소스를 자동으로 시작하고 트래픽에 따라 확장·축소하므로 인스턴스 유형을 선택하거나 조정 정책을 관리할 필요가 없습니다. 이를 통해 서버 선택 및 관리에 따른 반복적이고 부담스러운 작업이 사라집니다. 서버리스 추론은 AWS Lambda와 통합되어 고가용성, 내장된 내결함성 및 자동 확장 기능을 제공합니다. 트래픽 패턴이 드물거나 예측 불가능한 경우, 요청이 없을 때 엔드포인트를 0으로 축소할 수 있는 종량제 방식은 비용 효율적인 선택이 될 수 있습니다. 온디맨드 서버리스 추론 요금에 대한 자세한 내용은 [Amazon SageMaker 요금](https://aws.amazon.com/sagemaker/pricing/)을 참고하세요.

선택적으로 서버리스 추론에 프로비저닝된 동시성을 함께 사용할 수 있습니다. 트래픽 폭증이 예측 가능한 경우 프로비저닝된 동시성을 제공하는 서버리스 추론이 비용 효율적인 대안이 될 수 있습니다. 프로비저닝된 동시성을 사용하면 엔드포인트를 따뜻하게 유지하여 예측 가능한 성능과 빠른 응답 시간을 확보할 수 있습니다. SageMaker AI는 할당된 프로비저닝된 동시성에 대해 컴퓨팅 리소스를 초기화하여 밀리초 이내에 응답할 준비가 되도록 합니다. 프로비저닝된 동시성을 사용하는 서버리스 추론에서는, 추론 요청을 처리하는 데 사용된 컴퓨팅 용량(밀리초 단위 청구)과 처리한 데이터 양에 대해 요금이 부과됩니다. 또한 구성한 메모리, 프로비저닝 기간, 활성화된 동시성 양에 따라 프로비저닝된 동시성 사용에 대한 비용이 발생합니다. 프로비저닝된 동시성을 사용하는 서버리스 추론 요금에 대한 자세한 내용은 [Amazon SageMaker 요금](https://aws.amazon.com/sagemaker/pricing/)을 참고하세요.

서버리스 추론은 MLOps 파이프라인과 통합하여 ML 워크플로를 간소화할 수 있으며, 서버리스 엔드포인트를 통해 [모델 레지스트리](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/model-registry.html)에 등록된 모델을 호스팅할 수 있습니다.

서버리스 추론은 미국 동부(버지니아 북부), 미국 동부(오하이오), 미국 서부(캘리포니아 북부), 미국 서부(오레곤), 아프리카(케이프타운), 아시아 태평양(홍콩), 아시아 태평양(뭄바이), 아시아 태평양(도쿄), 아시아 태평양(서울), 아시아 태평양(오사카), 아시아 태평양(싱가포르), 아시아 태평양(시드니), 캐나다(중부), 유럽(프랑크푸르트), 유럽(아일랜드), 유럽(런던), 유럽(파리), 유럽(스톡홀름), 유럽(밀라노), 중동(바레인), 남아메리카(상파울루)의 21개 AWS 리전에서 정식으로 제공됩니다. Amazon SageMaker AI 리전 가용성에 대한 자세한 내용은 [AWS 리전 서비스 목록](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/)을 참고하세요.

## 작동 방법

다음 다이어그램은 온디맨드 서버리스 추론의 워크플로와 서버리스 엔드포인트 사용의 이점을 보여줍니다.

![](/media/posts/imported/aws/Pasted%20image%2020250609174834.png)

온디맨드 서버리스 엔드포인트를 생성하면 SageMaker AI가 컴퓨팅 리소스를 프로비저닝하고 관리합니다. 이후 엔드포인트로 추론 요청을 보내면 모델의 예측 응답을 받을 수 있습니다. SageMaker AI는 요청 트래픽을 처리하기 위해 필요에 따라 컴퓨팅 리소스를 확장·축소하며, 사용한 만큼만 비용을 지불합니다.

프로비저닝된 동시성의 경우 서버리스 추론은 Application Auto Scaling과도 통합되어 대상 지표나 일정에 따라 프로비저닝된 동시성을 관리할 수 있습니다. 자세한 내용은 [서버리스 엔드포인트에 맞게 프로비저닝된 동시성의 자동 확장](https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/serverless-endpoints-autoscale.html) 섹션을 참고하세요.

https://docs.aws.amazon.com/ko_kr/sagemaker/latest/dg/serverless-endpoints.html