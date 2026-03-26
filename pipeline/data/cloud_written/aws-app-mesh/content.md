## 개요

AWS App Mesh는 마이크로서비스 간 통신을 표준화하고 제어할 수 있게 해주는 서비스 메시(Service Mesh) 서비스입니다. 마이크로서비스 아키텍처가 확장됨에 따라, 서비스 간 통신의 복잡성은 기하급수적으로 증가합니다. 각 서비스의 트래픽 라우팅, 재시도 로직, 타임아웃, 서킷 브레이커, TLS 암호화, 관측성 등을 개별적으로 구현하면 중복 코드가 늘어나고 일관성을 유지하기 어려워집니다.

App Mesh는 이러한 네트워킹 관심사를 애플리케이션 코드에서 분리하여 인프라 수준에서 일관되게 관리합니다. 내부적으로 Envoy 프록시를 사이드카 패턴으로 배포하여, 모든 서비스 간 트래픽이 Envoy를 통과하도록 합니다. 이를 통해 애플리케이션 코드를 수정하지 않고도 트래픽 관리, 보안, 관측성을 확보할 수 있습니다.

본 글에서는 App Mesh의 핵심 개념, 아키텍처, 실전 구성 방법, 그리고 서비스 메시 도입 시의 고려사항까지 상세히 다루겠습니다.

## 핵심 기능

### App Mesh 핵심 리소스

**1. Mesh**: 서비스 메시의 최상위 논리적 경계입니다.

```bash
# Mesh 생성
aws appmesh create-mesh \
  --mesh-name "my-app-mesh" \
  --spec '{"egressFilter": {"type": "DROP_ALL"}}' \
  --tags '[{"key": "Environment", "value": "production"}]'

# Mesh 조회
aws appmesh describe-mesh --mesh-name "my-app-mesh"
```

`egressFilter`의 `DROP_ALL`은 메시 내에서 정의되지 않은 외부 서비스로의 트래픽을 차단합니다. `ALLOW_ALL`로 설정하면 외부 트래픽을 허용합니다.

**2. Virtual Service**: 서비스의 추상화된 이름입니다. 실제 트래픽 대상(Virtual Node 또는 Virtual Router)을 지정합니다.

```bash
# Virtual Service 생성 (Virtual Router 사용)
aws appmesh create-virtual-service \
  --mesh-name "my-app-mesh" \
  --virtual-service-name "api.myapp.local" \
  --spec '{
    "provider": {
      "virtualRouter": {
        "virtualRouterName": "api-router"
      }
    }
  }'

# Virtual Service 생성 (Virtual Node 직접 지정)
aws appmesh create-virtual-service \
  --mesh-name "my-app-mesh" \
  --virtual-service-name "database.myapp.local" \
  --spec '{
    "provider": {
      "virtualNode": {
        "virtualNodeName": "database-node"
      }
    }
  }'
```

**3. Virtual Node**: 실제 서비스 인스턴스(ECS 태스크, EKS Pod, EC2 인스턴스)를 나타내는 논리적 포인터입니다.

```bash
# Virtual Node 생성
aws appmesh create-virtual-node \
  --mesh-name "my-app-mesh" \
  --virtual-node-name "api-v1" \
  --spec '{
    "serviceDiscovery": {
      "awsCloudMap": {
        "namespaceName": "myapp.local",
        "serviceName": "api",
        "attributes": [{"key": "version", "value": "v1"}]
      }
    },
    "listeners": [{
      "portMapping": {"port": 8080, "protocol": "http"},
      "healthCheck": {
        "protocol": "http",
        "path": "/health",
        "port": 8080,
        "healthyThreshold": 2,
        "unhealthyThreshold": 3,
        "timeoutMillis": 5000,
        "intervalMillis": 10000
      },
      "timeout": {
        "http": {
          "perRequest": {"value": 30, "unit": "s"},
          "idle": {"value": 300, "unit": "s"}
        }
      },
      "outlierDetection": {
        "maxServerErrors": 5,
        "interval": {"value": 10, "unit": "s"},
        "baseEjectionDuration": {"value": 30, "unit": "s"},
        "maxEjectionPercent": 50
      }
    }],
    "backends": [
      {"virtualService": {"virtualServiceName": "database.myapp.local"}},
      {"virtualService": {"virtualServiceName": "cache.myapp.local"}}
    ],
    "logging": {
      "accessLog": {
        "file": {"path": "/dev/stdout"}
      }
    }
  }'
```

**4. Virtual Router & Route**: 트래픽 라우팅 규칙을 정의합니다.

```bash
# Virtual Router 생성
aws appmesh create-virtual-router \
  --mesh-name "my-app-mesh" \
  --virtual-router-name "api-router" \
  --spec '{
    "listeners": [{
      "portMapping": {"port": 8080, "protocol": "http"}
    }]
  }'

# Route 생성 (가중치 기반 라우팅)
aws appmesh create-route \
  --mesh-name "my-app-mesh" \
  --virtual-router-name "api-router" \
  --route-name "api-route" \
  --spec '{
    "httpRoute": {
      "match": {
        "prefix": "/"
      },
      "action": {
        "weightedTargets": [
          {"virtualNode": "api-v1", "weight": 90},
          {"virtualNode": "api-v2", "weight": 10}
        ]
      },
      "retryPolicy": {
        "httpRetryEvents": ["server-error", "gateway-error"],
        "maxRetries": 3,
        "perRetryTimeout": {"value": 5, "unit": "s"}
      },
      "timeout": {
        "perRequest": {"value": 30, "unit": "s"},
        "idle": {"value": 300, "unit": "s"}
      }
    },
    "priority": 100
  }'
```

**5. Virtual Gateway**: 메시 외부에서 메시 내부 서비스로 진입하는 게이트웨이입니다.

```bash
# Virtual Gateway 생성
aws appmesh create-virtual-gateway \
  --mesh-name "my-app-mesh" \
  --virtual-gateway-name "ingress-gateway" \
  --spec '{
    "listeners": [{
      "portMapping": {"port": 8080, "protocol": "http"},
      "healthCheck": {
        "protocol": "http",
        "path": "/health",
        "port": 8080,
        "healthyThreshold": 2,
        "unhealthyThreshold": 3,
        "timeoutMillis": 5000,
        "intervalMillis": 10000
      }
    }],
    "logging": {
      "accessLog": {
        "file": {"path": "/dev/stdout"}
      }
    }
  }'

# Gateway Route 생성
aws appmesh create-gateway-route \
  --mesh-name "my-app-mesh" \
  --virtual-gateway-name "ingress-gateway" \
  --gateway-route-name "api-gateway-route" \
  --spec '{
    "httpRoute": {
      "match": {"prefix": "/api"},
      "action": {
        "target": {
          "virtualService": {
            "virtualServiceName": "api.myapp.local"
          }
        }
      }
    }
  }'
```

### TLS 암호화

서비스 간 통신을 mTLS(mutual TLS)로 암호화할 수 있습니다.

```bash
# ACM Private CA 인증서를 사용한 TLS 설정이 포함된 Virtual Node
aws appmesh update-virtual-node \
  --mesh-name "my-app-mesh" \
  --virtual-node-name "api-v1" \
  --spec '{
    "serviceDiscovery": {
      "awsCloudMap": {
        "namespaceName": "myapp.local",
        "serviceName": "api"
      }
    },
    "listeners": [{
      "portMapping": {"port": 8080, "protocol": "http"},
      "tls": {
        "mode": "STRICT",
        "certificate": {
          "acm": {
            "certificateArn": "arn:aws:acm:ap-northeast-2:123456789012:certificate/abc-123"
          }
        },
        "validation": {
          "trust": {
            "acm": {
              "certificateAuthorityArns": ["arn:aws:acm-pca:ap-northeast-2:123456789012:certificate-authority/abc"]
            }
          }
        }
      }
    }],
    "backends": [
      {"virtualService": {"virtualServiceName": "database.myapp.local"}}
    ]
  }'
```

## 아키텍처/동작 원리

### Envoy 사이드카 패턴

```
[Service A Container]     [Envoy Proxy Sidecar]
  ├── Application  ────>    ├── Route Rules
  │   (port 8080)           ├── Retry Policy
  └── Code has no           ├── Circuit Breaker
      networking logic      ├── TLS Termination
                            ├── Metrics/Traces
                            └── Access Logs
                               |
                               v
                    [Envoy Proxy Sidecar]
                      (Service B side)
                               |
                               v
                    [Service B Container]
```

App Mesh는 각 서비스 인스턴스 옆에 Envoy 프록시를 사이드카로 배포합니다. 모든 인바운드/아웃바운드 트래픽은 Envoy를 통과하며, App Mesh 컨트롤 플레인이 Envoy의 설정을 동적으로 관리합니다.

### 컨트롤 플레인과 데이터 플레인

- **컨트롤 플레인 (App Mesh)**: 라우팅 규칙, 정책, 서비스 디스커버리 정보를 관리하고 Envoy에 전달합니다.
- **데이터 플레인 (Envoy Proxy)**: 실제 트래픽을 처리합니다. 컨트롤 플레인에서 받은 설정에 따라 라우팅, 로드 밸런싱, 재시도, 서킷 브레이킹을 수행합니다.

### 서비스 디스커버리 통합

App Mesh는 두 가지 서비스 디스커버리 방식을 지원합니다.

- **AWS Cloud Map**: DNS 또는 API 기반 서비스 디스커버리. ECS, EKS 모두에서 사용 가능합니다.
- **DNS**: 기존 DNS 기반 서비스 디스커버리 (Route 53, CoreDNS 등).

### 트래픽 흐름

```
[Client]
   |
   v
[Virtual Gateway (Envoy)]
   |
   v (Gateway Route)
[Virtual Service: api.myapp.local]
   |
   v (Virtual Router)
[Route: /api/* -> weighted targets]
   |
   ├── 90% -> Virtual Node: api-v1 -> Envoy -> Service A v1
   └── 10% -> Virtual Node: api-v2 -> Envoy -> Service A v2
```

## 실전 활용

### 사례 1: 카나리 배포 (Canary Deployment)

```bash
# 새 버전 Virtual Node 생성
aws appmesh create-virtual-node \
  --mesh-name "my-app-mesh" \
  --virtual-node-name "api-v2" \
  --spec '{
    "serviceDiscovery": {
      "awsCloudMap": {
        "namespaceName": "myapp.local",
        "serviceName": "api",
        "attributes": [{"key": "version", "value": "v2"}]
      }
    },
    "listeners": [{
      "portMapping": {"port": 8080, "protocol": "http"}
    }],
    "backends": [
      {"virtualService": {"virtualServiceName": "database.myapp.local"}}
    ]
  }'

# 카나리: 5% 트래픽을 v2로
aws appmesh update-route \
  --mesh-name "my-app-mesh" \
  --virtual-router-name "api-router" \
  --route-name "api-route" \
  --spec '{
    "httpRoute": {
      "match": {"prefix": "/"},
      "action": {
        "weightedTargets": [
          {"virtualNode": "api-v1", "weight": 95},
          {"virtualNode": "api-v2", "weight": 5}
        ]
      }
    }
  }'

# 점진적으로 트래픽 증가: 50%
aws appmesh update-route \
  --mesh-name "my-app-mesh" \
  --virtual-router-name "api-router" \
  --route-name "api-route" \
  --spec '{
    "httpRoute": {
      "match": {"prefix": "/"},
      "action": {
        "weightedTargets": [
          {"virtualNode": "api-v1", "weight": 50},
          {"virtualNode": "api-v2", "weight": 50}
        ]
      }
    }
  }'

# 완전 전환: 100%
aws appmesh update-route \
  --mesh-name "my-app-mesh" \
  --virtual-router-name "api-router" \
  --route-name "api-route" \
  --spec '{
    "httpRoute": {
      "match": {"prefix": "/"},
      "action": {
        "weightedTargets": [
          {"virtualNode": "api-v2", "weight": 100}
        ]
      }
    }
  }'
```

### 사례 2: 헤더 기반 라우팅

```bash
# 특정 헤더가 있는 요청을 v2로 라우팅
aws appmesh create-route \
  --mesh-name "my-app-mesh" \
  --virtual-router-name "api-router" \
  --route-name "api-beta-route" \
  --spec '{
    "httpRoute": {
      "match": {
        "prefix": "/",
        "headers": [{
          "name": "x-beta-user",
          "match": {"exact": "true"}
        }]
      },
      "action": {
        "weightedTargets": [
          {"virtualNode": "api-v2", "weight": 100}
        ]
      }
    },
    "priority": 10
  }'
```

### 사례 3: ECS에서 App Mesh 사용

ECS Task Definition에 Envoy 사이드카를 추가하는 패턴입니다.

```json
{
  "family": "api-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "proxyConfiguration": {
    "type": "APPMESH",
    "containerName": "envoy",
    "properties": [
      {"name": "IgnoredUID", "value": "1337"},
      {"name": "ProxyIngressPort", "value": "15000"},
      {"name": "ProxyEgressPort", "value": "15001"},
      {"name": "AppPorts", "value": "8080"},
      {"name": "EgressIgnoredIPs", "value": "169.254.170.2,169.254.169.254"}
    ]
  },
  "containerDefinitions": [
    {
      "name": "app",
      "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/api:v1",
      "portMappings": [{"containerPort": 8080}],
      "essential": true,
      "dependsOn": [{"containerName": "envoy", "condition": "HEALTHY"}]
    },
    {
      "name": "envoy",
      "image": "840364872350.dkr.ecr.ap-northeast-2.amazonaws.com/aws-appmesh-envoy:v1.27.0.0-prod",
      "essential": true,
      "environment": [
        {"name": "APPMESH_RESOURCE_ARN", "value": "arn:aws:appmesh:ap-northeast-2:123456789012:mesh/my-app-mesh/virtualNode/api-v1"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -s http://localhost:9901/server_info | grep state | grep -q LIVE"],
        "interval": 5,
        "timeout": 2,
        "retries": 3,
        "startPeriod": 10
      },
      "user": "1337"
    }
  ]
}
```

### 사례 4: 관측성 - X-Ray 통합

```bash
# X-Ray 트레이싱이 활성화된 Virtual Node
aws appmesh update-virtual-node \
  --mesh-name "my-app-mesh" \
  --virtual-node-name "api-v1" \
  --spec '{
    "serviceDiscovery": {
      "awsCloudMap": {
        "namespaceName": "myapp.local",
        "serviceName": "api"
      }
    },
    "listeners": [{"portMapping": {"port": 8080, "protocol": "http"}}],
    "backends": [{"virtualService": {"virtualServiceName": "database.myapp.local"}}],
    "backendDefaults": {
      "clientPolicy": {}
    },
    "logging": {
      "accessLog": {
        "file": {"path": "/dev/stdout"}
      }
    }
  }'
```

Envoy에서 생성되는 메트릭은 CloudWatch, Prometheus, Datadog 등으로 수집할 수 있습니다. 주요 메트릭은 다음과 같습니다.

- `envoy_http_downstream_rq_total`: 총 요청 수
- `envoy_http_downstream_rq_xx`: HTTP 상태 코드별 요청 수
- `envoy_cluster_upstream_rq_time`: 업스트림 응답 시간
- `envoy_cluster_outlier_detection_ejections_active`: 서킷 브레이커로 제외된 호스트 수

### 리소스 관리

```bash
# Mesh 내 모든 Virtual Service 조회
aws appmesh list-virtual-services --mesh-name "my-app-mesh"

# Mesh 내 모든 Virtual Node 조회
aws appmesh list-virtual-nodes --mesh-name "my-app-mesh"

# 특정 Virtual Node 상세 정보
aws appmesh describe-virtual-node \
  --mesh-name "my-app-mesh" \
  --virtual-node-name "api-v1"

# Route 목록 조회
aws appmesh list-routes \
  --mesh-name "my-app-mesh" \
  --virtual-router-name "api-router"
```

## 모범 사례/보안

### 1. mTLS 활성화

- 프로덕션 환경에서는 반드시 서비스 간 mTLS를 활성화합니다.
- ACM Private CA 또는 SDS(Secret Discovery Service)를 통해 인증서를 관리합니다.
- 인증서 자동 갱신을 설정하여 만료로 인한 장애를 방지합니다.

### 2. 이그레스 필터 설정

```bash
# DROP_ALL로 설정하여 명시적으로 정의된 서비스만 통신 허용
aws appmesh update-mesh \
  --mesh-name "my-app-mesh" \
  --spec '{"egressFilter": {"type": "DROP_ALL"}}'
```

### 3. 재시도 정책 설계

- 멱등성이 보장되는 요청(GET, PUT)에만 재시도를 적용합니다.
- 재시도 횟수와 타임아웃을 적절히 설정하여 Thundering Herd를 방지합니다.
- 서킷 브레이커(Outlier Detection)와 함께 사용하여 장애 전파를 차단합니다.

### 4. Envoy 이미지 관리

- AWS에서 제공하는 공식 Envoy 이미지를 사용합니다.
- 정기적으로 최신 버전으로 업데이트하여 보안 패치를 적용합니다.

### 5. 관측성 확보

- CloudWatch Container Insights로 Envoy 메트릭을 수집합니다.
- AWS X-Ray로 분산 추적을 활성화하여 서비스 간 호출 체인을 시각화합니다.
- 액세스 로그를 활성화하여 모든 요청을 기록합니다.

## 관련 서비스 비교

| 항목 | AWS App Mesh | Istio (on EKS) | Linkerd (on EKS) | AWS VPC Lattice |
|------|-------------|---------------|-----------------|----------------|
| 관리 모델 | AWS 관리형 | 자체 관리 | 자체 관리 | AWS 관리형 |
| 프록시 | Envoy | Envoy | linkerd2-proxy | 내장 (AWS 관리) |
| 지원 플랫폼 | ECS, EKS, EC2 | Kubernetes | Kubernetes | ECS, EKS, Lambda, EC2 |
| mTLS | 지원 | 지원 | 지원 (기본 활성화) | 지원 |
| 트래픽 관리 | 가중치, 헤더 기반 | 매우 풍부 | 기본적 | 가중치 기반 |
| 관측성 | X-Ray, CloudWatch | Kiali, Jaeger, Prometheus | Linkerd Dashboard | CloudWatch |
| 복잡도 | 중간 | 높음 | 낮음 | 낮음 |
| 비용 | 무료 (Envoy 리소스만) | 무료 (운영 비용) | 무료 (운영 비용) | 요청 기반 과금 |
| 상태 | 유지보수 모드 | 활발한 개발 | 활발한 개발 | 활발한 개발 |

중요한 참고사항: AWS는 2024년부터 **Amazon VPC Lattice**를 App Mesh의 후속으로 권장하고 있습니다. 새로운 서비스 메시 도입을 검토하는 경우 VPC Lattice를 우선 고려하는 것이 좋습니다.

## 요약

AWS App Mesh는 Envoy 프록시 기반의 서비스 메시로, 마이크로서비스 간 통신을 인프라 수준에서 관리합니다. 핵심 내용을 정리하면 다음과 같습니다.

- **핵심 리소스**: Mesh, Virtual Service, Virtual Node, Virtual Router, Route, Virtual Gateway로 구성됩니다.
- **Envoy 사이드카**: 각 서비스 인스턴스 옆에 Envoy 프록시를 배포하여 모든 트래픽을 제어합니다.
- **트래픽 관리**: 가중치 기반 라우팅, 헤더 기반 라우팅, 재시도 정책, 서킷 브레이커 등을 코드 변경 없이 설정합니다.
- **카나리 배포**: Route의 가중치를 점진적으로 조절하여 안전한 배포를 수행합니다.
- **보안**: mTLS로 서비스 간 통신을 암호화하고, 이그레스 필터로 외부 통신을 제어합니다.
- **관측성**: CloudWatch, X-Ray와 통합하여 메트릭, 트레이싱, 로깅을 확보합니다.
- **멀티 플랫폼**: ECS, EKS, EC2 환경을 모두 지원합니다.
- **향후 방향**: AWS는 VPC Lattice를 차세대 서비스 메시로 권장하고 있으므로, 새 프로젝트에서는 VPC Lattice도 함께 검토합니다.

서비스 메시는 마이크로서비스의 복잡성을 관리하는 강력한 도구이지만, 운영 복잡도가 증가하는 트레이드오프가 있으므로 서비스 수와 팀 역량을 고려하여 도입을 결정해야 합니다.