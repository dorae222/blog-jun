<!-- infographic-hero -->
![Job과 CronJob으로 배치 워크로드 실행하기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Job과 CronJob으로 배치 워크로드 실행하기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Job과 CronJob으로 배치 워크로드 실행하기

Deployment는 계속 실행되는 서비스를 유지하는 controller이고, Job은 완료되는 작업을 실행하는 controller다. 데이터 처리, migration, 일회성 관리 작업처럼 성공적으로 끝나는 것이 목표인 workload에는 Job이 더 적합하다.

CronJob은 정해진 스케줄에 따라 Job을 만든다. 중요한 것은 스케줄 자체보다 실패 재시도, 동시 실행 정책, history 보존 기준이다.

## 핵심 개념

- Job은 Pod가 성공적으로 종료될 때까지 실행을 관리한다.
- `backoffLimit`은 실패 재시도 횟수의 상한이다.
- CronJob의 `concurrencyPolicy`는 Allow, Forbid, Replace를 사용할 수 있다.
- batch workload는 로그와 완료 상태를 함께 확인해야 한다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hello
spec:
  schedule: "*/5 * * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: hello
              image: busybox:1.36
              command: ["sh", "-c", "date; echo hello"]
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f cronjob.yaml
kubectl get cronjob
kubectl get jobs
kubectl get pods --selector=job-name=<job-name>
kubectl logs job/<job-name>
kubectl describe job <job-name>
```

![Job과 CronJob으로 배치 워크로드 실행하기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Job과 CronJob으로 배치 워크로드 실행하기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

Job/CronJob 설명은 Deployment와 대비해서 쓰면 명확하다. 서비스처럼 계속 떠 있어야 하는가, 아니면 성공 종료가 목표인가를 먼저 묻고 controller를 고른다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| 종료 조건 | 작업이 성공 종료되는 프로세스인가 |
| RestartPolicy | Job Pod에 적절한 restartPolicy를 설정했는가 |
| Concurrency | CronJob 중복 실행이 허용되는가 |
| History | 완료된 Job과 Pod를 얼마나 보존할지 정했는가 |

## 자주 틀리는 지점

- **완료가 목표인 batch 작업을 Deployment로 실행한다** - Deployment는 Pod가 종료되면 계속 다시 띄우므로 한 번 끝나야 하는 작업이 무한 재시작에 걸린다. 성공 종료가 목표라면 Job, 스케줄 반복이 목표라면 CronJob을 고른다.
- **CronJob의 timezone과 실행 간격을 확인하지 않는다** - schedule은 기본적으로 kube-controller-manager 기준 시간(대개 UTC)으로 해석되므로 로컬 시간으로 착각하면 실행 시각이 어긋난다. 필요하면 `spec.timeZone`을 명시하고 `*/5 * * * *` 같은 표현이 의도한 주기인지 다시 본다.
- **이전 실행이 길어질 때 concurrencyPolicy를 정하지 않는다** - 기본값 Allow는 앞 실행이 끝나기 전에 다음 Job을 겹쳐 생성한다. 중복 실행이 위험한 작업이면 Forbid, 최신 실행만 남기려면 Replace를 지정한다.
- **Job 실패를 Job 객체만 보고 판단한다** - 실패 원인은 Job status가 아니라 Pod 로그와 event에 남는다. `kubectl logs job/<job-name>`과 `kubectl describe job`으로 backoffLimit이 소진되기 전에 무엇이 실패했는지 확인한다.

## 관련 문서

- [[ckad-15-rolling-update-rollback|Rolling Update와 Rollback]] - 이전 글, 계속 실행되는 Deployment의 버전 교체
- [[ckad-17-networkpolicy|NetworkPolicy 기본]] - 다음 글, Pod 간 트래픽 허용 모델
- [[ckad-05-replicaset-deployment|ReplicaSet과 Deployment]] - 계속 실행되는 controller와 완료되는 Job의 대비
- [[ckad-08-command-args-image|command와 args]] - Job과 CronJob container가 실행할 명령 지정
- [[ckad-09-resources-requests-limits|Resource requests와 limits]] - batch Pod의 자원 요청과 제한
- [[ckad-13-logs-events-debug|로그와 이벤트로 디버깅]] - Job 실패 원인을 로그와 event로 추적
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 시리즈 전체 흐름

## 참고 자료

- [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [TTL-after-finished Controller](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/)
