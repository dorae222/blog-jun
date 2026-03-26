# AWS Cloud Map -- 서비스 디스커버리 및 리소스 매핑 서비스 개요

## 개요

AWS Cloud Map은 애플리케이션 리소스를 사용자 정의 이름으로 등록하고 검색할 수 있는 **완전관리형 서비스 디스커버리(Service Discovery) 서비스**입니다. 현대의 클라우드 아키텍처에서는 마이크로서비스, 컨테이너, 서버리스 함수 등 수백 개의 서비스가 동적으로 생성되고 소멸됩니다. 이러한 환경에서 각 서비스의 위치(IP 주소, 포트 등)를 수동으로 관리하는 것은 사실상 불가능합니다.

AWS Cloud Map은 이 문제를 해결하기 위해 설계되었습니다. 애플리케이션이 실행 시점에 다른 서비스의 최신 위치 정보를 자동으로 조회할 수 있도록 하며, 헬스체크 기반으로 정상적인 인스턴스만 반환하여 트래픽의 안정성을 보장합니다. Amazon Route 53과 통합되어 DNS 기반 검색뿐만 아니라 API 기반 검색도 지원하므로, 다양한 아키텍처 패턴에 유연하게 적용할 수 있습니다.

## 핵심 기능

### 서비스 등록 및 검색

AWS Cloud Map의 가장 기본적인 기능은 **서비스 등록(Service Registration)**과 **서비스 검색(Service Discovery)**입니다. EC2 인스턴스, ECS 태스크, EKS 파드, Lambda 함수, 심지어 S3 버킷이나 DynamoDB 테이블 같은 비컴퓨팅 리소스까지 Cloud Map에 등록할 수 있습니다.

등록된 리소스는 사용자가 정의한 이름(예: `payment-service`, `order-api`)으로 조회할 수 있으며, IP 주소, 포트, URL 등의 속성 정보와 함께 커스텀 속성도 추가할 수 있습니다.

### 네임스페이스 관리

Cloud Map은 **네임스페이스(Namespace)** 단위로 서비스를 논리적으로 그룹화합니다. 네임스페이스는 크게 세 가지 유형이 있습니다.

| 네임스페이스 유형 | 검색 방식 | 사용 시나리오 |
|---|---|---|
| **HTTP 네임스페이스** | API 기반 검색만 지원 | 서버리스, 비DNS 환경 |
| **Public DNS 네임스페이스** | DNS + API 검색 | 인터넷에서 접근 가능한 서비스 |
| **Private DNS 네임스페이스** | DNS + API 검색 | VPC 내부 서비스 간 통신 |

### 헬스체크 통합

Cloud Map은 등록된 인스턴스의 상태를 지속적으로 확인합니다. Route 53 헬스체크 또는 커스텀 헬스체크를 통해 비정상 인스턴스를 자동으로 검색 결과에서 제외하여, 클라이언트가 항상 정상적인 엔드포인트로만 트래픽을 보낼 수 있도록 합니다.

헬스체크 방식은 다음과 같이 구분됩니다.

- **Route 53 헬스체크**: HTTP, HTTPS, TCP 프로토콜을 통해 엔드포인트의 상태를 확인합니다.
- **커스텀 헬스체크(Custom Health Check)**: 애플리케이션이 직접 Cloud Map API를 호출하여 인스턴스의 상태를 보고합니다. ECS, EKS 등 컨테이너 환경에서 주로 사용됩니다.

### ECS 및 EKS 통합

AWS Cloud Map은 Amazon ECS 및 Amazon EKS와 네이티브로 통합됩니다. ECS 서비스를 생성할 때 Cloud Map 서비스 디스커버리를 활성화하면, ECS 태스크가 시작되거나 종료될 때 자동으로 Cloud Map에 등록 및 해제됩니다. 별도의 사이드카 프록시나 서비스 메시 없이도 서비스 간 통신이 가능합니다.

### AWS App Mesh 통합

Cloud Map은 AWS App Mesh의 서비스 디스커버리 백엔드로 동작합니다. App Mesh가 트래픽 라우팅 정책을 관리하고, Cloud Map이 서비스의 실제 위치 정보를 제공하는 구조로, 서비스 메시 아키텍처를 더욱 효과적으로 구현할 수 있습니다.

## 아키텍처/동작 원리

### Cloud Map의 전체 아키텍처

```text
[마이크로서비스 A] ---> [AWS Cloud Map API] ---> 서비스 위치 반환
       |                      |                      |
       |              [네임스페이스]                    |
       |           /      |       \                  |
       |   [서비스1]  [서비스2]  [서비스3]              |
       |      |          |         |                  |
       |  [인스턴스]  [인스턴스]  [인스턴스]             |
       |                                              |
       +----------------------------------------------+
                   서비스 엔드포인트로 요청
```

Cloud Map의 동작 원리는 다음과 같습니다.

1. **네임스페이스 생성**: 서비스를 그룹화할 네임스페이스를 생성합니다. DNS 기반 또는 HTTP 기반을 선택할 수 있습니다.
2. **서비스 등록**: 네임스페이스 내에 서비스를 정의하고, 해당 서비스의 인스턴스(엔드포인트)를 등록합니다.
3. **인스턴스 등록/해제**: 리소스가 시작되면 인스턴스를 등록하고, 종료되면 해제합니다. ECS/EKS 환경에서는 이 과정이 자동으로 처리됩니다.
4. **서비스 검색**: 다른 서비스가 Cloud Map API 또는 DNS 쿼리를 통해 대상 서비스의 위치를 조회합니다.
5. **헬스체크 필터링**: 비정상 인스턴스는 검색 결과에서 자동 제외됩니다.

### DNS 기반 검색 vs API 기반 검색

| 구분 | DNS 기반 검색 | API 기반 검색 |
|---|---|---|
| 프로토콜 | DNS(Route 53) | HTTPS(Cloud Map API) |
| TTL 영향 | TTL에 따라 캐싱되므로 최신 정보 반영에 지연 가능 | 실시간으로 최신 정보 반환 |
| 클라이언트 변경 | DNS 해석만 하면 되므로 변경 불필요 | SDK/API 호출 코드 필요 |
| 커스텀 속성 | 지원하지 않음 | 커스텀 속성까지 조회 가능 |
| 적합한 환경 | 기존 DNS 기반 인프라 | 서버리스, 동적 환경 |

## 실전 활용

### Cloud Map 네임스페이스 생성

```bash
# Private DNS 네임스페이스 생성
aws servicediscovery create-private-dns-namespace \
  --name my-app.local \
  --vpc vpc-0123456789abcdef0 \
  --description "마이크로서비스 내부 통신용 네임스페이스"
```

### 서비스 등록

```bash
# Cloud Map 서비스 생성
aws servicediscovery create-service \
  --name payment-service \
  --namespace-id ns-abcdef1234567890 \
  --dns-config '{"DnsRecords": [{"Type": "A", "TTL": 60}]}' \
  --health-check-custom-config '{"FailureThreshold": 1}'
```

### 인스턴스 등록

```bash
# 서비스 인스턴스 등록
aws servicediscovery register-instance \
  --service-id srv-abcdef1234567890 \
  --instance-id i-0123456789abcdef0 \
  --attributes '{"AWS_INSTANCE_IPV4": "10.0.1.100", "AWS_INSTANCE_PORT": "8080", "version": "v2.1"}'
```

### 서비스 검색(API 기반)

```bash
# DiscoverInstances API를 통한 서비스 검색
aws servicediscovery discover-instances \
  --namespace-name my-app.local \
  --service-name payment-service \
  --health-status HEALTHY
```

반환 결과 예시:

```json
{
  "Instances": [
    {
      "InstanceId": "i-0123456789abcdef0",
      "NamespaceName": "my-app.local",
      "ServiceName": "payment-service",
      "HealthStatus": "HEALTHY",
      "Attributes": {
        "AWS_INSTANCE_IPV4": "10.0.1.100",
        "AWS_INSTANCE_PORT": "8080",
        "version": "v2.1"
      }
    }
  ]
}
```

### ECS 서비스에서 Cloud Map 통합

ECS 서비스를 생성할 때 서비스 디스커버리를 활성화하는 예시입니다.

```bash
# ECS 서비스 생성 시 Cloud Map 서비스 디스커버리 연동
aws ecs create-service \
  --cluster my-cluster \
  --service-name order-api \
  --task-definition order-api:3 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration '{"awsvpcConfiguration": {"subnets": ["subnet-abc123"], "securityGroups": ["sg-abc123"]}}' \
  --service-registries '[{"registryArn": "arn:aws:servicediscovery:ap-northeast-2:123456789012:service/srv-abcdef1234567890"}]'
```

### Python SDK를 활용한 서비스 검색

```python
import boto3

client = boto3.client('servicediscovery', region_name='ap-northeast-2')

# 정상 인스턴스만 조회
response = client.discover_instances(
    NamespaceName='my-app.local',
    ServiceName='payment-service',
    HealthStatus='HEALTHY',
    QueryParameters={
        'version': 'v2.1'  # 커스텀 속성 필터링
    }
)

for instance in response['Instances']:
    ip = instance['Attributes']['AWS_INSTANCE_IPV4']
    port = instance['Attributes']['AWS_INSTANCE_PORT']
    print(f"엔드포인트: {ip}:{port}")
```

## 모범 사례 및 보안

### 네임스페이스 설계 모범 사례

- **환경별 분리**: 개발(dev), 스테이징(staging), 프로덕션(prod) 환경별로 별도의 네임스페이스를 생성하여 서비스를 격리합니다.
- **Private DNS 네임스페이스 우선 사용**: VPC 내부 서비스 간 통신에는 Private DNS 네임스페이스를 사용하여 외부 노출을 방지합니다.
- **의미 있는 이름 체계**: `{환경}.{도메인}.local` 형태의 일관된 네이밍 규칙을 적용합니다 (예: `prod.payment.local`).

### IAM 권한 관리

Cloud Map 리소스에 대한 접근은 IAM 정책으로 세밀하게 제어해야 합니다. 최소 권한 원칙(Principle of Least Privilege)을 적용하여, 서비스가 필요로 하는 최소한의 권한만 부여합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "servicediscovery:DiscoverInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "servicediscovery:NamespaceName": "prod.my-app.local"
        }
      }
    }
  ]
}
```

### 헬스체크 설정 권장 사항

- **커스텀 헬스체크 사용**: ECS/EKS 환경에서는 Route 53 헬스체크보다 커스텀 헬스체크가 더 적합합니다. 컨테이너 오케스트레이터가 직접 상태를 보고하므로 더 정확한 상태 반영이 가능합니다.
- **FailureThreshold 적절히 설정**: 너무 낮으면 일시적인 장애에도 인스턴스가 제외되고, 너무 높으면 비정상 인스턴스로 트래픽이 전달될 수 있습니다.
- **TTL 최소화**: DNS 기반 검색을 사용하는 경우 TTL을 짧게 설정하여 변경 사항이 빠르게 반영되도록 합니다.

### 보안 고려사항

- **VPC 엔드포인트 활용**: Cloud Map API 호출이 인터넷을 거치지 않도록 VPC 엔드포인트를 설정합니다.
- **CloudTrail 감사 로깅**: Cloud Map API 호출을 CloudTrail로 기록하여 감사 추적을 유지합니다.
- **리소스 태깅**: 모든 Cloud Map 리소스에 일관된 태그를 부착하여 비용 추적과 접근 제어를 용이하게 합니다.

## 관련 서비스 비교

| 항목 | AWS Cloud Map | Amazon Route 53 | AWS App Mesh | Consul (HashiCorp) |
|---|---|---|---|---|
| 주요 역할 | 서비스 디스커버리 | DNS 서비스 | 서비스 메시 | 서비스 디스커버리 + 메시 |
| 검색 방식 | DNS + API | DNS | Envoy 프록시 | DNS + HTTP API |
| 헬스체크 | Route 53 + 커스텀 | Route 53 헬스체크 | Envoy 기반 | 에이전트 기반 |
| AWS 네이티브 통합 | ECS, EKS 네이티브 | 범용 DNS | ECS, EKS 통합 | 별도 설치 필요 |
| 커스텀 속성 | 지원 | 미지원 | 미지원 | Key-Value 지원 |
| 관리 복잡도 | 낮음 | 낮음 | 중간 | 높음 |
| 비용 | 리소스당 과금 | 호스팅 존 + 쿼리 | 무료(데이터 전송 별도) | 오픈소스/엔터프라이즈 |

Cloud Map은 AWS 네이티브 환경에서 서비스 디스커버리만 필요한 경우 가장 적합한 선택입니다. 트래픽 제어, mTLS 등 서비스 메시 기능까지 필요하다면 App Mesh와 함께 사용하는 것이 권장됩니다. 멀티클라우드 또는 하이브리드 환경에서는 Consul 같은 서드파티 솔루션이 더 적합할 수 있습니다.

## 요약

AWS Cloud Map은 마이크로서비스, 컨테이너, 서버리스 아키텍처에서 **서비스 디스커버리의 핵심 역할**을 수행하는 완전관리형 서비스입니다. DNS 기반과 API 기반의 두 가지 검색 방식을 지원하며, ECS/EKS와의 네이티브 통합으로 컨테이너 환경에서 특히 강력한 효용성을 발휘합니다.

| 항목 | 내용 |
|---|---|
| 서비스명 | AWS Cloud Map |
| 유형 | 완전관리형 서비스 디스커버리 서비스 |
| 핵심 기능 | 서비스 등록/검색, 헬스체크, DNS/API 검색, 커스텀 속성 |
| 통합 서비스 | ECS, EKS, App Mesh, Route 53, Lambda |
| 검색 방식 | DNS 기반(Route 53 연계) + API 기반(DiscoverInstances) |
| 적합 환경 | 마이크로서비스, 컨테이너 오토스케일링, 서버리스 |
| 과금 기준 | 등록된 리소스 수 + API 호출 수 |

동적으로 확장/축소되는 현대 클라우드 환경에서 수동 IP 관리의 한계를 극복하고, 서비스 간 통신의 안정성과 유연성을 확보하고자 한다면 AWS Cloud Map의 도입을 적극 검토해 보시기 바랍니다.