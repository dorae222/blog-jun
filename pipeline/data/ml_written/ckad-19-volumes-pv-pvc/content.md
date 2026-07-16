<!-- infographic-hero -->
![Volume, PV, PVC, StorageClass 기본기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Volume, PV, PVC, StorageClass 기본기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Volume, PV, PVC, StorageClass 기본기

컨테이너 filesystem은 일시적이다. Pod가 재생성되어도 데이터를 유지해야 하면 Kubernetes volume과 persistent storage 모델을 이해해야 한다. Pod는 보통 PV를 직접 참조하지 않고 PVC를 통해 필요한 storage를 요청한다.

StorageClass는 동적 provisioning의 기준이다. cloud 환경에서는 CSI driver와 StorageClass 조합으로 PV가 자동 생성되는 경우가 많다.

## 핵심 개념

- `emptyDir`은 Pod lifecycle과 함께 사라지는 임시 volume이다.
- PVC는 storage 요청이고 PV는 cluster storage 공급이다.
- accessModes는 volume이 node와 Pod에 어떻게 mount될 수 있는지 표현한다.
- StorageClass는 동적 PV 생성과 reclaim policy의 기준이 될 수 있다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: app-with-pvc
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["sh", "-c", "echo hello > /data/hello.txt; sleep 3600"]
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: data
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f storage.yaml
kubectl get pvc,pv
kubectl describe pvc data
kubectl exec app-with-pvc -- cat /data/hello.txt
kubectl get storageclass
```

![Volume, PV, PVC, StorageClass 기본기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Volume, PV, PVC, StorageClass 기본기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

storage 글은 Pod volume과 cluster persistent volume을 분리해서 설명해야 한다. `volumes`와 `volumeMounts`의 차이, PVC와 PV의 binding, StorageClass의 dynamic provisioning을 한 흐름으로 연결한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Mount | volumeMount name이 volumes name과 일치하는가 |
| Binding | PVC 상태가 Bound인가 |
| AccessMode | workload 배치 방식과 access mode가 맞는가 |
| Reclaim | PV reclaim policy와 데이터 삭제 기대가 일치하는가 |

## 자주 틀리는 지점

- **emptyDir을 영구 저장소로 착각한다** - emptyDir은 Pod가 사라지면 함께 지워지는 임시 volume이라 재생성 후 데이터가 남지 않는다. Pod lifecycle을 넘어 데이터를 유지하려면 PVC로 PV를 요청해야 한다.
- **PVC가 Pending인데 Pod 문제로만 본다** - PVC Pending은 대개 조건에 맞는 PV가 없거나 StorageClass가 없거나 provisioning이 실패한 상태다. `kubectl describe pvc`의 event를 보고 storage 쪽 원인을 먼저 확인한다.
- **ReadWriteOnce volume을 여러 node에서 동시에 쓰려 한다** - ReadWriteOnce accessMode는 한 node에만 mount된다. 여러 node의 Pod가 동시에 써야 하면 ReadWriteMany를 지원하는 storage가 필요하고, 임의로 RWO를 여러 곳에 붙이면 스케줄링이나 mount가 막힌다.
- **PVC 삭제와 실제 storage 삭제의 관계를 확인하지 않는다** - PV의 reclaimPolicy가 Retain이면 PVC를 지워도 데이터가 남고, Delete면 backing storage까지 사라진다. 삭제 기대와 reclaimPolicy가 일치하는지 미리 맞춘다.

## 관련 문서

- [[ckad-18-ingress|Service와 Ingress]] - 이전 글, 애플리케이션 노출
- [[ckad-20-statefulset-headless|StatefulSet과 Headless Service]] - 다음 글, Pod별 PVC를 만드는 volumeClaimTemplates
- [[ckad-03-pod-yaml|Pod YAML 기초]] - volumes와 volumeMounts를 선언하는 Pod spec
- [[ckad-07-configmap-secret-env|ConfigMap과 Secret]] - 설정을 volume으로 mount하는 또 다른 방식
- [[ckad-11-multicontainer-pods|멀티 컨테이너 Pod]] - 컨테이너 사이 emptyDir 공유 패턴
- [[ckad-13-logs-events-debug|로그와 이벤트로 디버깅]] - PVC Pending과 mount 실패를 event로 진단
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 시리즈 전체 흐름

## 참고 자료

- [Volumes](https://kubernetes.io/docs/concepts/storage/volumes/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
