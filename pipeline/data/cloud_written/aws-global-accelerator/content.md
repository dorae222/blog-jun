## 개요

AWS Global Accelerator는 AWS의 글로벌 네트워크 인프라를 활용하여 애플리케이션의 가용성과 성능을 향상시키는 네트워킹 서비스입니다. 일반적인 인터넷 트래픽은 여러 네트워크를 거치며 경로가 가변적이지만, Global Accelerator를 사용하면 사용자의 트래픽이 가장 가까운 AWS 엣지 로케이션으로 진입한 후 AWS의 전용 글로벌 네트워크를 통해 최적의 경로로 전달됩니다.

Global Accelerator는 고정된 두 개의 Anycast IP 주소를 제공합니다. 이 IP 주소는 전 세계 어디에서든 동일하게 사용할 수 있으며, DNS 변경 없이도 백엔드 엔드포인트를 변경하거나 리전 간 페일오버를 수행할 수 있습니다. 이는 DNS TTL에 의존하는 기존 장애 복구 방식보다 훨씬 빠르고 안정적입니다.

이 글에서는 Global Accelerator의 핵심 개념, 동작 원리, 실전 구성 방법, 그리고 유사 서비스인 CloudFront와의 차이점을 상세히 살펴보겠습니다.

## 핵심 기능

### Anycast IP

Global Accelerator를 생성하면 두 개의 고정 Anycast IP 주소가 할당됩니다. Anycast는 동일한 IP 주소를 전 세계 여러 지점에서 광고하는 네트워킹 기술입니다. 클라이언트가 이 IP로 요청을 보내면, BGP 라우팅에 의해 네트워크적으로 가장 가까운 AWS 엣지 로케이션으로 자동 라우팅됩니다.

이 Anycast IP의 장점은 다음과 같습니다.

- **DNS 독립성**: IP 주소가 고정이므로 DNS 변경 없이 백엔드를 변경할 수 있습니다.
- **즉각적인 페일오버**: DNS TTL 전파를 기다릴 필요가 없습니다.
- **방화벽 허용 목록 관리 용이**: 고정 IP이므로 파트너사 방화벽 규칙에 등록하기 쉽습니다.

### 리스너(Listener)

리스너는 클라이언트로부터의 인바운드 연결을 처리하는 구성 요소입니다. TCP 또는 UDP 프로토콜과 포트 범위를 지정합니다.

```json
{
  "Protocol": "TCP",
  "PortRanges": [
    {
      "FromPort": 80,
      "ToPort": 80
    },
    {
      "FromPort": 443,
      "ToPort": 443
    }
  ],
  "ClientAffinity": "SOURCE_IP"
}
```

ClientAffinity를 `SOURCE_IP`로 설정하면 동일한 소스 IP의 요청이 항상 같은 엔드포인트로 전달됩니다. 이는 세션 상태를 유지해야 하는 애플리케이션에 유용합니다.

### 엔드포인트 그룹(Endpoint Group)

엔드포인트 그룹은 AWS 리전 단위로 구성됩니다. 각 엔드포인트 그룹에는 트래픽 다이얼(Traffic Dial) 설정이 있어 해당 리전으로 전달되는 트래픽 비율을 0~100%로 조절할 수 있습니다.

이 기능은 다음 시나리오에서 매우 유용합니다.

- **블루/그린 배포**: 새 리전에 점진적으로 트래픽을 이동
- **리전 유지보수**: 특정 리전의 트래픽을 0%로 설정하여 다른 리전으로 전환
- **성능 테스트**: 소량의 트래픽으로 새 리전의 성능 검증

### 엔드포인트(Endpoint)

엔드포인트는 실제 트래픽을 처리하는 AWS 리소스입니다. 지원되는 엔드포인트 유형은 다음과 같습니다.

- **Application Load Balancer (ALB)**
- **Network Load Balancer (NLB)**
- **EC2 인스턴스**
- **Elastic IP 주소**

각 엔드포인트에는 가중치(Weight)를 설정할 수 있어 엔드포인트 그룹 내에서의 트래픽 분배 비율을 조절할 수 있습니다. 가중치 범위는 0~255입니다.

### 상태 확인(Health Check)

엔드포인트 그룹은 엔드포인트의 상태를 지속적으로 확인합니다. ALB나 NLB를 엔드포인트로 사용하는 경우 해당 로드 밸런서의 상태 확인을 상속하거나, 별도의 상태 확인을 구성할 수 있습니다.

비정상(Unhealthy) 엔드포인트가 감지되면 트래픽이 자동으로 다른 정상 엔드포인트로 전환됩니다. 엔드포인트 그룹 내 모든 엔드포인트가 비정상인 경우에는 다른 리전의 엔드포인트 그룹으로 페일오버됩니다.

### Client IP Preservation

Global Accelerator는 ALB 엔드포인트에 대해 클라이언트의 원본 IP 주소를 보존할 수 있습니다. 이 기능을 활성화하면 ALB의 X-Forwarded-For 헤더에 클라이언트의 실제 IP가 포함됩니다.

## 아키텍처/동작 원리

### 트래픽 흐름

Global Accelerator의 트래픽 흐름을 단계별로 살펴보겠습니다.

```
1. 클라이언트 --> Anycast IP로 요청
2. BGP 라우팅 --> 가장 가까운 AWS 엣지 로케이션으로 진입
3. AWS 글로벌 네트워크 --> 최적 경로로 목적지 리전으로 전달
4. 엔드포인트 그룹 --> 가중치 기반으로 엔드포인트 선택
5. 엔드포인트 --> 실제 트래픽 처리 (ALB/NLB/EC2/EIP)
```

핵심은 2번 단계입니다. 인터넷 트래픽이 AWS 네트워크에 최대한 빨리 진입하여 AWS의 최적화된 네트워크를 통해 전달되므로, 공중 인터넷을 통과하는 것보다 성능이 크게 향상됩니다.

AWS의 공식 문서에 따르면, Global Accelerator를 사용하면 인터넷 대비 최대 60%까지 성능이 향상될 수 있습니다.

### 장애 시 페일오버 동작

**엔드포인트 수준 장애**: 하나의 엔드포인트가 비정상이면 같은 엔드포인트 그룹의 다른 정상 엔드포인트로 트래픽이 전환됩니다. 전환 시간은 약 30초 이내입니다.

**리전 수준 장애**: 엔드포인트 그룹 내 모든 엔드포인트가 비정상이면 다른 리전의 엔드포인트 그룹으로 자동 페일오버됩니다. 이때 DNS 변경이 필요 없으므로 페일오버가 즉각적입니다.

### Standard vs Custom Routing Accelerator

Global Accelerator는 두 가지 유형의 Accelerator를 제공합니다.

**Standard Accelerator**는 가장 일반적인 유형으로, 상태 확인 기반의 자동 페일오버와 트래픽 분배를 제공합니다.

**Custom Routing Accelerator**는 다수의 사용자를 특정 EC2 인스턴스의 특정 포트로 결정론적으로 라우팅해야 하는 경우에 사용합니다. 게임 서버, 실시간 통신, IoT 등의 워크로드에 적합합니다.

## 실전 활용

### 멀티 리전 웹 애플리케이션 구성

서울(ap-northeast-2)과 도쿄(ap-northeast-1) 리전에 걸친 멀티 리전 웹 애플리케이션을 구성해보겠습니다.

**Step 1: Accelerator 생성**

```bash
# Global Accelerator 생성
aws globalaccelerator create-accelerator \
  --name "prod-web-accelerator" \
  --ip-address-type IPV4 \
  --enabled \
  --tags Key=Environment,Value=Production \
  --region us-west-2
```

참고: Global Accelerator의 API 엔드포인트는 us-west-2 리전에 있으므로 `--region us-west-2`를 명시해야 합니다.

**Step 2: 리스너 생성**

```bash
# HTTPS 리스너 생성
aws globalaccelerator create-listener \
  --accelerator-arn arn:aws:globalaccelerator::123456789012:accelerator/abcd-1234 \
  --port-ranges FromPort=443,ToPort=443 \
  --protocol TCP \
  --client-affinity SOURCE_IP \
  --region us-west-2
```

**Step 3: 엔드포인트 그룹 생성**

```bash
# 서울 리전 엔드포인트 그룹
aws globalaccelerator create-endpoint-group \
  --listener-arn arn:aws:globalaccelerator::123456789012:accelerator/abcd-1234/listener/efgh-5678 \
  --endpoint-group-region ap-northeast-2 \
  --traffic-dial-percentage 70 \
  --health-check-protocol HTTPS \
  --health-check-path "/health" \
  --health-check-interval-seconds 10 \
  --threshold-count 3 \
  --endpoint-configurations \
    EndpointId=arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/app/prod-alb/abcdef,Weight=128,ClientIPPreservationEnabled=true \
  --region us-west-2

# 도쿄 리전 엔드포인트 그룹
aws globalaccelerator create-endpoint-group \
  --listener-arn arn:aws:globalaccelerator::123456789012:accelerator/abcd-1234/listener/efgh-5678 \
  --endpoint-group-region ap-northeast-1 \
  --traffic-dial-percentage 30 \
  --health-check-protocol HTTPS \
  --health-check-path "/health" \
  --health-check-interval-seconds 10 \
  --threshold-count 3 \
  --endpoint-configurations \
    EndpointId=arn:aws:elasticloadbalancing:ap-northeast-1:123456789012:loadbalancer/app/prod-alb-tokyo/ghijkl,Weight=128,ClientIPPreservationEnabled=true \
  --region us-west-2
```

### 블루/그린 배포 시나리오

트래픽 다이얼을 활용한 블루/그린 배포를 수행합니다.

```bash
# 1단계: 새 리전(Green)에 10% 트래픽 전환
aws globalaccelerator update-endpoint-group \
  --endpoint-group-arn arn:aws:globalaccelerator::123456789012:accelerator/abcd-1234/listener/efgh-5678/endpoint-group/ijkl-green \
  --traffic-dial-percentage 10 \
  --region us-west-2

# 2단계: 모니터링 후 50%로 증가
aws globalaccelerator update-endpoint-group \
  --endpoint-group-arn arn:aws:globalaccelerator::123456789012:accelerator/abcd-1234/listener/efgh-5678/endpoint-group/ijkl-green \
  --traffic-dial-percentage 50 \
  --region us-west-2

# 3단계: 완전 전환 (100%)
aws globalaccelerator update-endpoint-group \
  --endpoint-group-arn arn:aws:globalaccelerator::123456789012:accelerator/abcd-1234/listener/efgh-5678/endpoint-group/ijkl-green \
  --traffic-dial-percentage 100 \
  --region us-west-2

# 기존 리전(Blue) 트래픽 제거
aws globalaccelerator update-endpoint-group \
  --endpoint-group-arn arn:aws:globalaccelerator::123456789012:accelerator/abcd-1234/listener/efgh-5678/endpoint-group/ijkl-blue \
  --traffic-dial-percentage 0 \
  --region us-west-2
```

### Accelerator 상태 모니터링

```bash
# Accelerator 목록 및 상태 확인
aws globalaccelerator list-accelerators \
  --query 'Accelerators[*].{Name:Name,Status:Status,IPs:IpSets[0].IpAddresses}' \
  --output table \
  --region us-west-2

# 엔드포인트 그룹 상태 확인
aws globalaccelerator describe-endpoint-group \
  --endpoint-group-arn arn:aws:globalaccelerator::123456789012:accelerator/abcd-1234/listener/efgh-5678/endpoint-group/ijkl-9012 \
  --query '{Region:EndpointGroupRegion,TrafficDial:TrafficDialPercentage,Endpoints:EndpointDescriptions[*].{Id:EndpointId,Weight:Weight,Health:HealthState}}' \
  --output json \
  --region us-west-2

# CloudWatch 메트릭으로 트래픽 모니터링
aws cloudwatch get-metric-statistics \
  --namespace AWS/GlobalAccelerator \
  --metric-name ProcessedBytesIn \
  --dimensions Name=Accelerator,Value=abcd-1234 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### Flow Logs 활성화

Global Accelerator의 트래픽을 분석하기 위해 Flow Logs를 S3에 저장할 수 있습니다.

```bash
# Flow Logs 활성화
aws globalaccelerator update-accelerator-attributes \
  --accelerator-arn arn:aws:globalaccelerator::123456789012:accelerator/abcd-1234 \
  --flow-logs-enabled \
  --flow-logs-s3-bucket "my-ga-flow-logs-bucket" \
  --flow-logs-s3-prefix "global-accelerator/" \
  --region us-west-2
```

## 모범 사례/보안

### 성능 최적화

1. **엔드포인트에 ALB를 사용합니다.** ALB를 사용하면 Client IP Preservation 기능을 활용할 수 있고, ALB의 다양한 라우팅 기능(경로 기반, 호스트 기반 등)과 결합할 수 있습니다.

2. **상태 확인 간격을 적절히 설정합니다.** 기본 30초보다 10초로 줄이면 장애 감지 속도가 빨라지지만, 상태 확인 트래픽이 증가합니다.

3. **Client Affinity를 신중히 선택합니다.** 세션 상태가 없는 stateless 애플리케이션에서는 NONE을 사용하여 최적의 부하 분산을 달성합니다.

### 보안 모범 사례

1. **AWS Shield Advanced와 통합합니다.** Global Accelerator의 Anycast IP는 자동으로 AWS Shield Standard의 보호를 받습니다. DDoS 공격에 대한 더 강력한 보호가 필요한 경우 Shield Advanced를 활성화합니다.

2. **보안 그룹과 ACL을 적절히 구성합니다.** Client IP Preservation을 활성화한 경우 보안 그룹에서 클라이언트 IP를 기반으로 접근 제어를 할 수 있습니다.

3. **IAM 정책으로 Global Accelerator 관리 권한을 제한합니다.** 특히 엔드포인트 변경이나 Accelerator 삭제 권한은 최소한의 관리자에게만 부여합니다.

4. **Flow Logs를 활성화하여 트래픽을 감사합니다.** 비정상적인 트래픽 패턴을 탐지하기 위해 Flow Logs를 S3에 저장하고 Athena 등으로 분석합니다.

### 비용 고려사항

- Global Accelerator는 시간당 고정 요금 + 전송된 데이터에 대한 DT(Data Transfer) 프리미엄 요금이 부과됩니다.
- DT 프리미엄은 트래픽이 전달되는 AWS 엣지 로케이션과 엔드포인트 리전 간의 거리에 따라 다릅니다.
- 비용 대비 성능 이점을 정확히 평가하려면 실제 트래픽 패턴으로 POC(Proof of Concept)를 수행하는 것을 권장합니다.

## 관련 서비스 비교

### Global Accelerator vs CloudFront

| 특성 | Global Accelerator | CloudFront |
|------|-------------------|------------|
| 주요 용도 | TCP/UDP 애플리케이션 가속 | HTTP/HTTPS 콘텐츠 전송 |
| 캐싱 | 없음 | 있음 (엣지 캐싱) |
| 프로토콜 | TCP, UDP | HTTP, HTTPS, WebSocket |
| IP 주소 | 고정 Anycast IP 2개 | 가변 IP (도메인 기반) |
| 엔드포인트 | ALB, NLB, EC2, EIP | S3, ALB, EC2, 커스텀 오리진 |
| 콘텐츠 변환 | 없음 | 지원 (Lambda@Edge) |
| 페일오버 | 즉각적 (IP 기반) | DNS TTL 의존 |
| DDoS 보호 | Shield Standard/Advanced | Shield Standard/Advanced |

**Global Accelerator를 선택해야 하는 경우:**
- TCP/UDP 기반의 non-HTTP 워크로드 (게임, IoT, VoIP)
- 고정 IP가 필요한 경우 (방화벽 허용 목록, 금융 규제 등)
- 즉각적인 리전 간 페일오버가 필요한 경우
- 캐싱이 불가능한 동적 콘텐츠 중심의 워크로드

**CloudFront를 선택해야 하는 경우:**
- 정적 콘텐츠 전송 (이미지, CSS, JS 등)
- HTTP/HTTPS 워크로드
- 엣지 캐싱으로 오리진 부하를 줄여야 하는 경우
- Lambda@Edge를 통한 엣지 컴퓨팅이 필요한 경우

### Global Accelerator vs Route 53

Route 53의 지연 시간 기반 라우팅이나 장애 조치 라우팅도 멀티 리전 트래픽 관리에 사용할 수 있지만, 페일오버 시 DNS TTL에 의존한다는 한계가 있습니다. Global Accelerator는 IP 수준에서 즉각적인 페일오버를 수행하므로 더 빠른 장애 복구가 가능합니다.

## 요약

AWS Global Accelerator는 글로벌 애플리케이션의 성능과 가용성을 향상시키는 핵심 네트워킹 서비스입니다. 주요 내용을 정리하면 다음과 같습니다.

- 두 개의 고정 Anycast IP를 제공하여 DNS에 의존하지 않는 즉각적인 페일오버를 지원합니다.
- AWS의 글로벌 네트워크를 활용하여 인터넷 대비 최대 60% 성능 향상을 달성할 수 있습니다.
- 트래픽 다이얼과 엔드포인트 가중치를 통해 세밀한 트래픽 관리가 가능합니다.
- ALB, NLB, EC2, EIP 등 다양한 엔드포인트를 지원합니다.
- 상태 확인 기반의 자동 페일오버로 고가용성을 확보합니다.
- CloudFront와는 보완적인 관계이며, 워크로드 특성에 따라 적절한 서비스를 선택해야 합니다.
- AWS Shield와 통합되어 DDoS 보호를 제공합니다.