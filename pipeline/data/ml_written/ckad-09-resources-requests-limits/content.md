<!-- infographic-hero -->
![requests, limits, quota로 리소스 제어하기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: requests, limits, quota로 리소스 제어하기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# requests, limits, quota로 리소스 제어하기

Kubernetes에서 resource request는 scheduler를 위한 정보이고 limit은 런타임 상한이다. request를 너무 낮게 잡으면 과밀 배치가 발생하고, limit을 너무 낮게 잡으면 정상 부하에서도 throttling이나 OOMKilled가 발생할 수 있다.

Namespace 단위 운영에서는 ResourceQuota와 LimitRange를 함께 사용해 기본값과 총량을 통제한다.

## 핵심 개념

- CPU request는 scheduling 기준이고 CPU limit은 throttling 상한으로 작동한다.
- Memory limit을 넘으면 container가 OOMKilled될 수 있다.
- requests와 limits 설정 조합은 QoS class에 영향을 준다.
- ResourceQuota는 namespace 전체 사용량을 제한하고 LimitRange는 기본값과 per-object 범위를 제한한다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: bounded-app
spec:
  containers:
    - name: app
      image: nginx:1.27
      resources:
        requests:
          cpu: "100m"
          memory: "128Mi"
        limits:
          cpu: "500m"
          memory: "256Mi"
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f resources.yaml
kubectl describe pod bounded-app
kubectl top pod bounded-app
kubectl get resourcequota -n default
kubectl describe limitrange -n default
```

![requests, limits, quota로 리소스 제어하기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: requests, limits, quota로 리소스 제어하기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

리소스 설정은 숫자만 나열하지 말고 scheduling과 runtime의 차이를 분명히 설명한다. 특히 CPU와 memory는 limit 초과 시 동작이 다르다. GPU는 extended resource로 request/limit이 특수하게 취급되므로 별도 GPU scheduling 글로 연결한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Request | scheduler가 배치할 최소 필요량이 현실적인가 |
| Limit | 정상 peak에서 throttling/OOM이 발생하지 않는가 |
| Quota | namespace quota 때문에 생성이 거부되지 않는가 |
| QoS | 원하는 QoS class가 만들어지는 설정인가 |

## 흔한 실수

- request 없이 limit만 설정해 배치 밀도를 예측하기 어렵게 만든다.
- memory limit을 작게 잡고 OOMKilled를 애플리케이션 버그로만 본다.
- namespace ResourceQuota가 있는 환경에서 request를 빠뜨린다.
- GPU request를 CPU/memory와 같은 방식으로 autoscaling한다고 가정한다.

## 시험 포인트

- `requests`는 scheduler가 배치할 node를 고를 때 쓰는 최소 필요량이고, `limits`는 runtime에서 걸리는 상한이다. 같은 숫자라도 역할이 다르므로 둘을 분리해서 설명할 수 있어야 한다.
- CPU와 memory는 limit 초과 시 동작이 다르다. CPU limit을 넘으면 throttling으로 속도가 느려지고, memory limit을 넘으면 container가 OOMKilled로 종료된다. OOMKilled를 무조건 애플리케이션 버그로만 보지 않는다.
- `requests`와 `limits`를 어떻게 조합하느냐가 Pod의 QoS class를 결정한다. 원하는 QoS class가 나오는 설정인지 확인한다.
- ResourceQuota가 걸린 namespace에서는 `requests`나 `limits`를 빠뜨리면 Pod 생성 자체가 거부될 수 있다. LimitRange는 기본값과 per-object 범위를 채워 주므로, `kubectl describe limitrange`로 현재 기본값을 먼저 본다.

## 관련 문서

- [[ckad-08-command-args-image|image, command, args]] - 이전 글, 리소스 상한을 붙일 container의 실행 방식
- [[ckad-10-scheduling-basics|스케줄링 기본기]] - 다음 글, requests를 기준으로 scheduler가 node를 고르는 단계
- [[ckad-06-namespace-service-basics|Namespace와 Service 기본기]] - ResourceQuota와 LimitRange가 적용되는 namespace 경계
- [[ckad-13-logs-events-debug|로그, 이벤트, 디버깅]] - OOMKilled와 throttling을 이벤트로 확인하는 방법
- [[ckad-12-probes-health-checks|Probe와 health check]] - 재시작 반복이 리소스 부족인지 probe 실패인지 구분
- [[ckad-16-jobs-cronjobs|Job과 CronJob]] - batch 워크로드에도 같은 requests/limits 원칙을 적용
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 전체 시리즈에서 이 글의 위치

## 참고 자료

- [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)
- [Limit Ranges](https://kubernetes.io/docs/concepts/policy/limit-range/)
