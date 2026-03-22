---
title: Amazon CloudFront
slug: "amazon-cloudfront"
category: cloud
tags: ["aws", "aws-s3", "cdn", "cloudfront", "edge-locations", "http", "https", "web-performance"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.882023+00:00"
---

- HTTP/HTTPS 기반 콘텐츠 전송에 최적화
- 주로 캐시된 콘텐츠 전송에 사용되며, 실시간 애플리케이션 트래픽 라우팅에는 적합하지 않음
- content delivery network service(CDN)

Amazon CloudFront는 .html, .css, .js 및 이미지 파일과 같은 정적 및 동적 웹 콘텐츠를 사용자에게 더 빠르게 배포하도록 지원하는 웹 서비스입니다. CloudFront는 전 세계의 엣지 로케이션(데이터 센터) 네트워크를 통해 콘텐츠를 제공합니다. 사용자가 CloudFront로 제공되는 콘텐츠를 요청하면, 해당 요청은 지연 시간이 가장 낮은 엣지 로케이션으로 라우팅되어 가능한 최고의 성능으로 콘텐츠가 제공됩니다.

> **NOTE:**
> - 콘텐츠가 이미 지연 시간이 가장 낮은 엣지 로케이션에 있는 경우 CloudFront가 콘텐츠를 즉시 제공합니다.
> - 콘텐츠가 엣지 로케이션에 없는 경우 CloudFront는 콘텐츠의 최종 버전에 대한 소스로 지정된 오리진(Amazon S3 버킷, MediaPackage 채널, HTTP 서버(예: 웹 서버) 등)에서 콘텐츠를 검색합니다.

> **특징:**
> - 사용자와 가까운 엣지 로케이션에서 데이터 전송
> - 글로벌 배포
> - 전 세계 사용자에게 최상의 경험 제공
> - 콘텐츠 지연 시간을 최소화하면서 제공
> - 비디오 콘텐츠 등의 실시간 스트리밍 배포 지원
> - 해외 사용자에 대한 웹사이트 속도 향상으로 향상된 브라우징 경험 제공
> - EC2 등의 오리진 서버 부하 감소
> - 오리진에서 CloudFront로 전송되는 비용은 부과되지 않아 비용 절감 효과
> - 사용자의 요청 헤더 값(디바이스, 최종 사용자의 위치, 최종 사용자가 사용하는 언어 등)에 따라 서로 다른 버전의 콘텐츠를 캐싱하여 제공 가능

예를 들어, CloudFront가 아닌 일반 웹 서버에서 이미지를 제공한다고 가정해보겠습니다. 예를 들어 `https://example.com/sunsetphoto.png` URL로 sunsetphoto.png라는 이미지를 서비스할 수 있습니다.

사용자는 이 URL로 접속해 이미지를 볼 수 있지만, 해당 요청이 인터넷 상의 여러 네트워크를 통해 라우팅된다는 사실은 사용자에게는 잘 드러나지 않습니다.

CloudFront는 AWS 백본 네트워크를 활용해 각 사용자 요청을 가장 효과적으로 서비스할 수 있는 엣지 로케이션으로 라우팅함으로써 콘텐츠 배포 속도를 높입니다. 일반적으로 CloudFront 엣지 로케이션이 최종 사용자에게 가장 빠르게 콘텐츠를 제공합니다. AWS 네트워크를 사용하면 사용자의 요청이 통과해야 하는 네트워크 수가 줄어들어 성능이 향상됩니다. 이로 인해 파일의 첫 바이트를 로드하는 데 걸리는 지연 시간이 줄어들고 데이터 전송 속도가 빨라집니다.

또한 파일(객체)의 사본이 전 세계 여러 엣지 로케이션에 유지(또는 캐시)되므로 안정성과 가용성이 향상됩니다.

https://docs.aws.amazon.com/ko_kr/AmazonCloudFront/latest/DeveloperGuide/Introduction.html