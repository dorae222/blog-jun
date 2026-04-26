<!-- infographic-hero -->
![Amazon CloudFront 핵심 요약](figures/infographic.svg)

*Figure: Amazon CloudFront 한 장 요약 인포그래픽*

# Amazon CloudFront 심층 분석

## 개요

Amazon CloudFront는 AWS가 운영하는 글로벌 콘텐츠 전송 네트워크(CDN, Content Delivery Network) 서비스입니다. 전 세계 450개 이상의 엣지 로케이션(Edge Location)과 13개 이상의 리전별 엣지 캐시(Regional Edge Cache)를 통해 정적/동적 웹 콘텐츠, API, 라이브/온디맨드 비디오 스트리밍 등을 최종 사용자에게 낮은 지연 시간으로 전송합니다.

CDN의 핵심 원리는 콘텐츠를 사용자와 가까운 서버에 캐싱하여 전송 거리를 줄이는 것입니다. 예를 들어 서울 리전(ap-northeast-2)에 원본 서버가 있고, 미국 사용자가 접속하는 경우, CDN 없이는 태평양을 건너 서울까지 왕복해야 합니다. CloudFront를 사용하면 미국의 엣지 로케이션에 캐싱된 콘텐츠를 바로 반환하여 지연 시간을 크게 줄일 수 있습니다.

CloudFront는 단순한 캐싱 CDN을 넘어서, DDoS 방어(AWS Shield), WAF 통합, 필드 레벨 암호화, 엣지 컴퓨팅(Lambda@Edge, CloudFront Functions) 등 다양한 보안 및 컴퓨팅 기능을 제공합니다.

### CloudFront를 사용해야 하는 이유

- **성능 향상**: 글로벌 엣지 네트워크를 통한 콘텐츠 전송으로 지연 시간을 대폭 줄입니다.
- **비용 절감**: 오리진 서버의 부하와 대역폭 비용을 줄입니다.
- **보안 강화**: HTTPS 강제, AWS Shield Standard (무료 DDoS 방어), WAF 통합을 제공합니다.
- **가용성 향상**: 오리진 장애 시 캐싱된 콘텐츠로 서비스를 유지할 수 있습니다.

## 핵심 기능

### 1. 배포(Distribution) 구성

CloudFront 배포는 콘텐츠 전송의 기본 단위입니다. 하나의 배포에 여러 오리진(Origin)과 캐시 동작(Cache Behavior)을 설정할 수 있습니다.

```bash
# CloudFront 배포 생성 (S3 오리진)
aws cloudfront create-distribution \
  --distribution-config '{
    "CallerReference": "my-distribution-2024-01",
    "Comment": "프로덕션 웹사이트 CDN",
    "Enabled": true,
    "Origins": {
      "Quantity": 2,
      "Items": [
        {
          "Id": "S3-static-assets",
          "DomainName": "my-app-static.s3.ap-northeast-2.amazonaws.com",
          "S3OriginConfig": {
            "OriginAccessIdentity": "origin-access-identity/cloudfront/E1A2B3C4D5"
          }
        },
        {
          "Id": "ALB-api-server",
          "DomainName": "api-alb-123456.ap-northeast-2.elb.amazonaws.com",
          "CustomOriginConfig": {
            "HTTPPort": 80,
            "HTTPSPort": 443,
            "OriginProtocolPolicy": "https-only",
            "OriginSslProtocols": {"Quantity": 1, "Items": ["TLSv1.2"]}
          }
        }
      ]
    },
    "DefaultCacheBehavior": {
      "TargetOriginId": "S3-static-assets",
      "ViewerProtocolPolicy": "redirect-to-https",
      "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
      "Compress": true,
      "AllowedMethods": {"Quantity": 2, "Items": ["HEAD", "GET"]}
    },
    "DefaultRootObject": "index.html"
  }'
```

### 2. 오리진(Origin) 유형

CloudFront는 다양한 유형의 오리진을 지원합니다.

**S3 버킷 오리진:**

```bash
# OAC(Origin Access Control) 생성 - S3 버킷 보호
aws cloudfront create-origin-access-control \
  --origin-access-control-config '{
    "Name": "my-s3-oac",
    "Description": "S3 버킷 접근 제어",
    "SigningProtocol": "sigv4",
    "SigningBehavior": "always",
    "OriginAccessControlOriginType": "s3"
  }'
```

OAC를 사용하면 S3 버킷에 대한 직접 접근을 차단하고, CloudFront를 통해서만 접근하도록 강제할 수 있습니다. 이전의 OAI(Origin Access Identity) 방식보다 보안이 강화되었습니다.

**커스텀 오리진 (ALB, EC2, 외부 서버):**

```bash
# 배포에 커스텀 오리진 추가
aws cloudfront update-distribution \
  --id "E1A2B3C4D5" \
  --distribution-config file://distribution-config.json
```

**오리진 그룹 (장애 조치):**

오리진 그룹을 사용하면 기본 오리진이 실패할 경우 보조 오리진으로 자동 장애 조치가 이루어집니다.

```json
{
  "OriginGroups": {
    "Quantity": 1,
    "Items": [{
      "Id": "failover-group",
      "FailoverCriteria": {
        "StatusCodes": {
          "Quantity": 4,
          "Items": [500, 502, 503, 504]
        }
      },
      "Members": {
        "Quantity": 2,
        "Items": [
          {"OriginId": "primary-origin"},
          {"OriginId": "secondary-origin"}
        ]
      }
    }]
  }
}
```

### 3. 캐시 정책(Cache Policy)

CloudFront는 캐시 정책을 통해 캐싱 동작을 세밀하게 제어합니다.

```bash
# 커스텀 캐시 정책 생성
aws cloudfront create-cache-policy \
  --cache-policy-config '{
    "Name": "custom-cache-policy",
    "Comment": "정적 자산용 캐시 정책",
    "DefaultTTL": 86400,
    "MaxTTL": 31536000,
    "MinTTL": 3600,
    "ParametersInCacheKeyAndForwardedToOrigin": {
      "EnableAcceptEncodingGzip": true,
      "EnableAcceptEncodingBrotli": true,
      "HeadersConfig": {
        "HeaderBehavior": "none"
      },
      "CookiesConfig": {
        "CookieBehavior": "none"
      },
      "QueryStringsConfig": {
        "QueryStringBehavior": "none"
      }
    }
  }'

# 관리형 캐시 정책 목록 조회
aws cloudfront list-cache-policies \
  --type managed \
  --query 'CachePolicyList.Items[].CachePolicy.{Id:Id,Name:CachePolicyConfig.Name,DefaultTTL:CachePolicyConfig.DefaultTTL}' \
  --output table
```

주요 관리형 캐시 정책:

- **CachingOptimized**: 정적 콘텐츠에 최적화 (기본 TTL 24시간)
- **CachingDisabled**: 캐싱 비활성화 (동적 콘텐츠용)
- **CachingOptimizedForUncompressedObjects**: 비압축 콘텐츠용

### 4. 캐시 무효화(Invalidation)

콘텐츠를 업데이트한 후 캐시를 강제로 삭제해야 하는 경우 캐시 무효화를 수행합니다.

```bash
# 특정 경로의 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id "E1A2B3C4D5" \
  --paths '{
    "Quantity": 3,
    "Items": [
      "/index.html",
      "/css/*",
      "/js/*"
    ]
  }'

# 전체 캐시 무효화 (비용 주의)
aws cloudfront create-invalidation \
  --distribution-id "E1A2B3C4D5" \
  --paths '{"Quantity": 1, "Items": ["/*"]}'

# 무효화 상태 확인
aws cloudfront get-invalidation \
  --distribution-id "E1A2B3C4D5" \
  --id "I1A2B3C4D5"
```

캐시 무효화는 월 1,000개 경로까지 무료이며, 초과 시 경로당 $0.005가 부과됩니다. 빈번한 무효화가 필요한 경우 파일명에 버전 해시를 포함하는 캐시 버스팅(Cache Busting) 전략을 권장합니다.

### 5. Lambda@Edge와 CloudFront Functions

엣지에서 코드를 실행하여 요청/응답을 커스터마이징할 수 있습니다.

**CloudFront Functions** (경량, 서브밀리초 지연):

```bash
# CloudFront Function 생성
aws cloudfront create-function \
  --name "url-rewrite" \
  --function-config '{
    "Comment": "URL 재작성 함수",
    "Runtime": "cloudfront-js-2.0"
  }' \
  --function-code file://url-rewrite.js
```

```javascript
// url-rewrite.js - SPA를 위한 URL 재작성
function handler(event) {
    var request = event.request;
    var uri = request.uri;
    
    // 확장자가 없는 경로는 index.html로 리다이렉트
    if (!uri.includes('.')) {
        request.uri = '/index.html';
    }
    
    return request;
}
```

**Lambda@Edge** (복잡한 로직, Node.js/Python):

```bash
# Lambda@Edge 함수는 us-east-1 리전에서 생성해야 합니다
aws lambda create-function \
  --function-name "image-resize-edge" \
  --runtime nodejs20.x \
  --role arn:aws:iam::123456789012:role/lambda-edge-role \
  --handler index.handler \
  --zip-file fileb://function.zip \
  --region us-east-1

# 함수 버전 게시 (Lambda@Edge는 버전이 필요)
aws lambda publish-version \
  --function-name "image-resize-edge" \
  --region us-east-1
```

두 서비스의 차이점:

| 항목 | CloudFront Functions | Lambda@Edge |
|------|---------------------|-------------|
| 실행 위치 | 엣지 로케이션 | 리전별 엣지 캐시 |
| 실행 시간 | 최대 1ms | 최대 5초 (Viewer), 30초 (Origin) |
| 메모리 | 2 MB | 128-3008 MB |
| 런타임 | JavaScript | Node.js, Python |
| 네트워크 접근 | 불가 | 가능 |
| 트리거 | Viewer Request/Response | 모든 4개 이벤트 |
| 비용 | $0.10/100만 호출 | $0.60/100만 호출 |

## 아키텍처/동작 원리

### CloudFront 콘텐츠 전송 흐름

```
[사용자]                [엣지 로케이션]         [리전별 엣지 캐시]      [오리진]
   |                        |                       |                    |
   |-- DNS 질의 ---------->|                       |                    |
   |   (d111.cloudfront.net)|                       |                    |
   |<-- 가장 가까운 엣지 IP|                       |                    |
   |                        |                       |                    |
   |-- HTTP 요청 ---------> |                       |                    |
   |                        |-- 캐시 확인           |                    |
   |                        |                       |                    |
   |   [캐시 히트]          |                       |                    |
   |<-- 즉시 응답 ---------|                       |                    |
   |                        |                       |                    |
   |   [캐시 미스]          |                       |                    |
   |                        |-- 상위 캐시 확인 ---->|                    |
   |                        |                       |-- 캐시 확인        |
   |                        |                       |                    |
   |                        |                       |   [캐시 미스]      |
   |                        |                       |-- 오리진 요청 ---->|
   |                        |                       |<-- 응답 ----------|
   |                        |<-- 캐싱 + 응답 ------|                    |
   |<-- 캐싱 + 응답 ------|                       |                    |
```

### Price Class

CloudFront는 Price Class를 통해 사용하는 엣지 로케이션 범위를 제한하고 비용을 절감할 수 있습니다.

- **Price Class All**: 모든 엣지 로케이션 사용 (최고 성능)
- **Price Class 200**: 대부분의 리전 (남미, 호주 제외)
- **Price Class 100**: 북미 + 유럽 엣지 로케이션만

```bash
# Price Class 변경
aws cloudfront update-distribution \
  --id "E1A2B3C4D5" \
  --if-match "E2QWRUHAPOMQZL" \
  --distribution-config file://config-with-price-class-200.json
```

### Signed URL과 Signed Cookie

프리미엄 콘텐츠나 비공개 콘텐츠에 대한 접근을 제어할 수 있습니다.

```bash
# CloudFront 키 그룹 생성
aws cloudfront create-public-key \
  --public-key-config '{
    "CallerReference": "my-public-key-2024",
    "Name": "my-signing-key",
    "EncodedKey": "-----BEGIN PUBLIC KEY-----\nMIIBI...\n-----END PUBLIC KEY-----"
  }'

aws cloudfront create-key-group \
  --key-group-config '{
    "Name": "my-key-group",
    "Items": ["K1A2B3C4D5"],
    "Comment": "콘텐츠 서명용 키 그룹"
  }'
```

```python
# Python으로 Signed URL 생성
from datetime import datetime, timedelta
import boto3
from botocore.signers import CloudFrontSigner
import rsa

def rsa_signer(message):
    with open('private_key.pem', 'rb') as f:
        private_key = rsa.PrivateKey.load_pkcs1(f.read())
    return rsa.sign(message, private_key, 'SHA-1')

cf_signer = CloudFrontSigner('K1A2B3C4D5', rsa_signer)

signed_url = cf_signer.generate_presigned_url(
    url='https://d111.cloudfront.net/premium/video.mp4',
    date_less_than=datetime.utcnow() + timedelta(hours=1)
)

print(signed_url)
```

## 실전 활용

### 사례 1: SPA(Single Page Application) 호스팅

React, Vue 등 SPA를 S3 + CloudFront로 호스팅하는 패턴입니다.

```bash
# S3 버킷 생성 (정적 웹 호스팅)
aws s3 mb s3://my-spa-bucket

# 빌드 결과물 업로드
aws s3 sync ./build s3://my-spa-bucket \
  --delete \
  --cache-control "public, max-age=31536000" \
  --exclude "index.html"

# index.html은 캐시하지 않음
aws s3 cp ./build/index.html s3://my-spa-bucket/ \
  --cache-control "no-cache, no-store, must-revalidate"

# CloudFront 배포에서 커스텀 에러 응답 설정 (SPA 라우팅 지원)
# 403/404 에러 시 /index.html 반환, 200 상태 코드
aws cloudfront update-distribution \
  --id "E1A2B3C4D5" \
  --if-match "ETAG_HERE" \
  --distribution-config file://spa-distribution.json
```

```json
{
  "CustomErrorResponses": {
    "Quantity": 2,
    "Items": [
      {
        "ErrorCode": 403,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 10
      },
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 10
      }
    ]
  }
}
```

### 사례 2: 멀티 오리진 아키텍처

하나의 CloudFront 배포에서 경로별로 다른 오리진을 매핑하는 패턴입니다.

```json
{
  "CacheBehaviors": {
    "Quantity": 2,
    "Items": [
      {
        "PathPattern": "/api/*",
        "TargetOriginId": "ALB-api-server",
        "ViewerProtocolPolicy": "https-only",
        "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
        "AllowedMethods": {
          "Quantity": 7,
          "Items": ["HEAD", "DELETE", "POST", "GET", "OPTIONS", "PUT", "PATCH"]
        }
      },
      {
        "PathPattern": "/images/*",
        "TargetOriginId": "S3-images-bucket",
        "ViewerProtocolPolicy": "redirect-to-https",
        "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
        "Compress": true
      }
    ]
  }
}
```

### 사례 3: 보안 헤더 추가

CloudFront Functions를 사용하여 보안 헤더를 추가합니다.

```javascript
// security-headers.js
function handler(event) {
    var response = event.response;
    var headers = response.headers;
    
    headers['strict-transport-security'] = {
        value: 'max-age=63072000; includeSubdomains; preload'
    };
    headers['x-content-type-options'] = { value: 'nosniff' };
    headers['x-frame-options'] = { value: 'DENY' };
    headers['x-xss-protection'] = { value: '1; mode=block' };
    headers['content-security-policy'] = {
        value: "default-src 'self'; script-src 'self'"
    };
    headers['referrer-policy'] = { value: 'strict-origin-when-cross-origin' };
    
    return response;
}
```

## 모범 사례/보안

### HTTPS 강제

```bash
# 모든 요청을 HTTPS로 리다이렉트
# ViewerProtocolPolicy: redirect-to-https

# ACM 인증서 (us-east-1 리전에서 발급)
aws acm request-certificate \
  --domain-name "cdn.example.com" \
  --subject-alternative-names "*.example.com" \
  --validation-method DNS \
  --region us-east-1
```

### AWS Shield 및 WAF 통합

```bash
# WAF WebACL을 CloudFront 배포에 연결
aws wafv2 associate-web-acl \
  --web-acl-arn "arn:aws:wafv2:us-east-1:123456789012:global/webacl/cloudfront-protection/abc123" \
  --resource-arn "arn:aws:cloudfront::123456789012:distribution/E1A2B3C4D5"
```

### 모니터링

```bash
# CloudFront 실시간 로그 설정
aws cloudfront create-realtime-log-config \
  --name "production-realtime-logs" \
  --sampling-rate 100 \
  --fields "timestamp" "c-ip" "cs-method" "cs-uri-stem" "sc-status" "sc-bytes" "time-taken" "x-edge-result-type" \
  --end-points '[{
    "StreamType": "Kinesis",
    "KinesisStreamConfig": {
      "RoleARN": "arn:aws:iam::123456789012:role/CloudFrontRealtimeLogRole",
      "StreamARN": "arn:aws:kinesis:ap-northeast-2:123456789012:stream/cloudfront-logs"
    }
  }]'

# CloudWatch 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value=E1A2B3C4D5 Name=Region,Value=Global \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-02T00:00:00Z" \
  --period 3600 \
  --statistics Sum
```

### 비용 최적화

- Price Class를 적절히 선택하여 불필요한 엣지 로케이션 사용을 줄입니다.
- 캐시 적중률(Cache Hit Ratio)을 모니터링하고 최적화합니다.
- 캐시 무효화 대신 파일명 버전 해시(Cache Busting)를 사용합니다.
- Gzip/Brotli 압축을 활성화하여 데이터 전송량을 줄입니다.

## 관련 서비스 비교

### CloudFront vs S3 직접 서빙

| 항목 | CloudFront + S3 | S3 직접 서빙 |
|------|----------------|---------------|
| 지연 시간 | 낮음 (엣지 캐시) | 높음 (리전 간 거리) |
| HTTPS | 커스텀 도메인 지원 | S3 버킷 이름 제약 |
| 보안 | WAF, Shield 통합 | 제한적 |
| 비용 | CDN 과금 추가 | S3 전송 비용만 |
| 엣지 컴퓨팅 | Lambda@Edge, CF Functions | 미지원 |

### CloudFront vs Global Accelerator

| 항목 | CloudFront | Global Accelerator |
|------|-----------|--------------------|
| 목적 | 콘텐츠 캐싱/전송 | 네트워크 경로 최적화 |
| 캐싱 | 지원 | 미지원 |
| 프로토콜 | HTTP/HTTPS/WebSocket | TCP/UDP |
| 고정 IP | 미지원 | 2개 Anycast IP 제공 |
| 사용 사례 | 웹사이트, API, 미디어 | 게임, IoT, VoIP |

### CloudFront vs 타사 CDN (Cloudflare, Akamai)

| 항목 | CloudFront | Cloudflare | Akamai |
|------|-----------|-----------|--------|
| AWS 통합 | 네이티브 | API 기반 | API 기반 |
| 무료 플랜 | 없음 (Free Tier 1TB) | 있음 | 없음 |
| DDoS 방어 | Shield Standard 무료 | 기본 포함 | 별도 과금 |
| 엣지 컴퓨팅 | Lambda@Edge, CF Functions | Workers | EdgeWorkers |
| 엣지 수 | 450+ | 300+ | 4,200+ |

## 요약

Amazon CloudFront는 AWS 생태계에서 콘텐츠 전송의 핵심 역할을 담당하는 글로벌 CDN 서비스입니다. 단순한 캐싱을 넘어 보안, 엣지 컴퓨팅, 오리진 장애 조치 등 현대 웹 아키텍처에 필요한 다양한 기능을 제공합니다.

핵심 포인트를 정리하면 다음과 같습니다.

- 450개 이상의 글로벌 엣지 로케이션과 리전별 엣지 캐시를 통해 저지연 콘텐츠 전송을 보장합니다.
- OAC를 사용하여 S3 버킷에 대한 직접 접근을 차단하고 CloudFront를 통해서만 접근하도록 합니다.
- 캐시 정책으로 세밀한 캐싱 제어가 가능하며, 캐시 무효화보다 파일명 버전 해시 전략을 권장합니다.
- CloudFront Functions와 Lambda@Edge를 활용하여 엣지에서 요청/응답을 커스터마이징할 수 있습니다.
- AWS Shield Standard(무료)와 WAF 통합으로 DDoS 방어와 웹 보안을 강화합니다.
- Price Class 선택, 캐시 적중률 최적화, 압축 활성화로 비용을 절감할 수 있습니다.