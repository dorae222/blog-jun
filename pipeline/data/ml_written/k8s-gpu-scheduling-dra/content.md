<!-- infographic-hero -->
![K8s GPU 스케줄링: Device Plugin에서 DRA까지 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: K8s GPU 스케줄링: Device Plugin에서 DRA까지 한 장 요약. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

# K8s GPU 스케줄링: Device Plugin에서 DRA까지

GPU 서빙은 container image보다 scheduling이 먼저 막히는 경우가 많다. Device Plugin은 GPU 같은 vendor-specific resource를 kubelet에 광고하는 안정적인 방식이다. DRA는 ResourceClaim, DeviceClass 같은 객체를 통해 더 명시적인 device allocation을 제공한다. MIG, topology, multi-node inference를 고민하는 시점에는 integer GPU request만으로 부족해진다.

![K8s GPU 스케줄링: Device Plugin에서 DRA까지 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: K8s GPU 스케줄링: Device Plugin에서 DRA까지 운영 흐름. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

## 어디까지 다루는 글인가

이 글은 GPU Pod YAML 작성법에서 멈추지 않는다. Device Plugin이 kubelet에 GPU resource를 광고하는 경로와 DRA가 ResourceClaim/DeviceClass로 장치 할당을 모델링하는 경로를 비교한다. MIG, topology, multi-node inference가 등장하는 시점의 판단 기준을 다룬다.

## 체크포인트

| 항목 | 확인 기준 |
|------|-----------|
| Resource name | `nvidia.com/gpu` 같은 extended resource가 실제 node에 광고되는가 |
| Topology | GPU/NUMA/NVLink 배치가 latency와 throughput에 영향을 주는가 |
| DRA | ResourceClaim lifecycle과 scheduler integration을 운영팀이 감당할 수 있는가 |
| Autoscaling | GPU 부족과 queue 증가를 같은 신호로 보지 않도록 metric을 분리했는가 |

## Device Plugin: GPU를 정수 리소스로 노출

Kubernetes는 CPU와 memory를 제외한 vendor 장치를 기본적으로 알지 못한다. 그래서 GPU를 쓰려면 node에서 device plugin이 kubelet에 장치를 광고해야 한다. NVIDIA의 k8s-device-plugin은 node의 GPU를 찾아 kubelet gRPC로 등록하고, kubelet은 이를 extended resource인 `nvidia.com/gpu`로 node allocatable에 올린다. Pod은 여기에 정수 개수를 요청한다.

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

extended resource는 규칙이 단순하다. requests와 limits가 같아야 하고, 정수만 가능하며, overcommit이 안 된다. 즉 "GPU 0.5개"나 "memory가 일정 크기 이상인 GPU" 같은 조건을 이 문법으로는 표현할 수 없다. 이 요청/제한 모델의 기본기는 [[ckad-09-resources-requests-limits|requests와 limits]]에서, scheduler가 이 값으로 node를 고르는 흐름은 [[ckad-10-scheduling-basics|scheduling 기본]]에서 확인한다.

한계는 공유와 속성 표현에서 드러난다. 하나의 물리 GPU를 여러 pod이 나눠 쓰려면 device plugin 문법 밖의 장치를 동원해야 한다. NVIDIA는 두 가지를 제공한다. MIG(Multi-Instance GPU)는 A100/H100 같은 GPU를 하드웨어로 격리된 인스턴스로 쪼개고, 각 프로필을 별도 resource name으로 광고한다.

```yaml
resources:
  limits:
    nvidia.com/mig-1g.5gb: 1
```

time-slicing은 한 GPU를 시분할로 여러 pod에 나눠 주지만 memory 격리가 없다. 어느 쪽이든 위 예시처럼 "정수 개수 요청"이라는 틀 안에서 resource name만 바꿔 표현하는 우회에 가깝다. 요청하는 쪽은 그 이름이 물리 GPU 한 장을 뜻하는지, 격리된 조각을 뜻하는지, 시분할 슬롯을 뜻하는지 문법만으로는 구분할 수 없다.

토폴로지도 device plugin의 약점이다. 같은 node 안에서도 GPU가 어느 NUMA node에 붙어 있는지, GPU 사이에 NVLink가 있는지에 따라 통신 지연과 대역폭이 달라진다. Topology Manager가 NUMA 정렬을 어느 정도 맞춰 주지만, "이 두 GPU는 NVLink로 연결돼야 한다" 같은 조건을 요청에 담기는 어렵다. 개수는 맞아도 배치가 나쁘면 multi-GPU 추론의 성능이 떨어진다.

## DRA: 파라미터화된 claim으로 장치를 요청

DRA(Dynamic Resource Allocation)는 이 표현력 문제를 정면으로 다루는 API다. GPU를 익명의 정수 카운터로 보지 않고, 속성을 가진 장치로 모델링한다. 핵심 객체는 다음과 같다.

- ResourceSlice: driver가 node에 어떤 장치가 있는지, 각 장치의 속성(모델, memory 크기, 연결 관계 등)을 게시한다.
- DeviceClass: 장치 범주와 selector를 정의한다. "이 종류의 GPU"라는 분류에 해당한다.
- ResourceClaim: pod이 필요한 장치를 요청하는 claim이다. 속성 조건을 selector로 표현하고, 여러 pod이나 container가 하나의 claim을 공유할 수도 있다.
- ResourceClaimTemplate: pod마다 claim을 자동 생성할 때 쓰는 템플릿이다.

차이의 본질은 "개수"에서 "조건"으로 넘어간 데 있다. Device Plugin에서는 scheduler가 `nvidia.com/gpu: 1`이라는 숫자만 보고 node를 골랐다. DRA에서는 claim이 "memory가 일정 이상이고 특정 세대인 장치"처럼 속성 기반 조건을 담고, scheduler가 ResourceSlice에 게시된 장치 속성과 이 조건을 매칭해 할당한다. 공유와 부분 할당도 우회가 아니라 API의 1급 개념으로 표현된다.

운영 측면에서도 역할이 갈린다. Device Plugin은 node 단위로 GPU를 광고하고 kubelet이 Allocate 시점에 장치를 pod에 붙이는, 오래 검증된 단순한 경로다. DRA는 admin이 DeviceClass로 장치 범주를 정의하고 사용자가 ResourceClaim으로 조건을 요청하는 식으로 관심사가 나뉜다. ResourceClaimTemplate을 Deployment에 붙이면 replica마다 claim이 생성되고, pod이 사라질 때 claim도 정리된다. 이 lifecycle이 하나 더 늘어난다는 점이 도입 비용이다.

| 축 | Device Plugin | DRA |
|------|---------------|-----|
| 요청 표현 | `nvidia.com/gpu` 정수 개수 | 속성 조건을 담은 ResourceClaim |
| 공유/분할 | MIG, time-slicing으로 우회 (별도 resource name) | claim 공유와 부분 할당을 1급으로 표현 |
| 속성/토폴로지 | Topology Manager로 부분적, 요청에 담기 어려움 | ResourceSlice 속성과 selector로 매칭 |
| 운영 복잡도 | 낮음, 오래 검증된 경로 | ResourceClaim lifecycle과 driver 관리 필요 |
| 적합한 상황 | GPU 정수 개수 요청으로 충분한 서빙 | 세밀한 공유, 속성 선택, 토폴로지 제약 |

정리하면 Device Plugin은 안정적이고 단순하지만 표현력이 정수 개수에 갇혀 있고, DRA는 속성/공유/부분 할당을 명시적으로 다루는 대신 ResourceClaim lifecycle과 driver를 운영이 감당해야 한다. 대부분의 단순한 "GPU 1개짜리 서빙"은 여전히 device plugin으로 충분하고, MIG 분할, 토폴로지 민감한 배치, 세밀한 공유가 얽히기 시작할 때 DRA의 값어치가 커진다.

## AI 서빙에서의 GPU 스케줄링

서빙 워크로드는 이 선택을 특히 예민하게 만든다. 큰 LLM은 한 장의 GPU에 다 올라가지 않아서 tensor parallel로 여러 GPU에 weight를 쪼개고, 그래도 부족하면 node를 넘어 pipeline parallel로 확장한다. 이때 node 사이 network topology가 성능을 좌우하므로, 단순히 "GPU 8개"가 아니라 "어디에 붙은 GPU 8개"가 문제가 된다.

메모리 축도 다르다. 추론 지연을 줄이는 KV cache는 context 길이와 동시 요청 수에 비례해 GPU memory를 소비한다. 같은 GPU라도 이 cache 여유가 batch 크기와 throughput을 결정한다. 반대로 작은 모델이 여러 개라면 GPU 한 장을 통째로 주는 대신 MIG로 쪼개 packing 효율을 올리는 편이 낫다. 이 서빙 런타임 레이어가 GPU를 실제로 어떻게 쓰는지는 [[vllm-serving-architecture|vLLM 서빙 아키텍처]]와 [[kserve-llminferenceservice-deep-dive|KServe LLMInferenceService]]에서 이어서 본다.

스케줄링이 막히면 증상은 대개 Pod Pending으로 나타난다. 이때는 `kubectl describe pod`의 Events에서 FailedScheduling과 "Insufficient nvidia.com/gpu" 같은 메시지를 먼저 읽는다. 원인은 보통 몇 가지로 좁혀진다. 요청한 GPU 개수를 가진 node가 없거나, GPU node에 걸린 taint를 pod이 toleration으로 받지 못했거나, nodeSelector/affinity가 실제 node label과 어긋난 경우다. 개수는 맞는데 성능이 안 나오는 반대 상황이라면 topology와 MIG 배치를 의심한다. "요청이 맞았다"와 "배치가 좋다"는 서로 다른 문제다.

## 언제 DRA로 넘어가는가

실무 판단은 단순하다. 워크로드가 GPU를 정수 개수로 요청하는 것으로 충분하고 공유가 필요 없다면 device plugin을 유지한다. 안정적이고 생태계 지원도 넓다. 반대로 다음 신호가 겹치면 DRA를 검토한다. 하나의 GPU를 여러 워크로드가 세밀하게 나눠 써야 하거나, memory 크기나 세대 같은 속성으로 장치를 골라야 하거나, MIG 프로필과 토폴로지 요구가 스케줄링 결정에 직접 들어가야 하는 경우다.

관측 관점에서는 GPU 부족 신호와 queue 적체 신호를 분리해서 봐야 한다. Pod이 Pending인 것과 서빙 queue가 길어지는 것은 원인이 다르다. 전자는 스케줄링/용량 문제이고, 후자는 배치돼 실행 중인 replica의 처리량 문제다. 이 둘을 같은 alert로 묶으면 GPU를 더 붙여야 할 때와 요청을 더 잘 배분해야 할 때를 구분하지 못한다. GPU 사용률, MIG 인스턴스별 점유, KV cache 여유, 그리고 요청 지연과 비용을 함께 보는 관측은 [[llm-observability-cost|LLM 관측성과 비용]]에서 다룬다.

## 관련 문서

- [[ckad-09-resources-requests-limits|requests와 limits]] - GPU 요청의 기반이 되는 리소스 모델
- [[ckad-10-scheduling-basics|Kubernetes scheduling 기본]] - scheduler가 node를 고르는 흐름
- [[ckad-02-kubernetes-architecture|Kubernetes 아키텍처]] - kubelet과 scheduler의 위치
- [[vllm-serving-architecture|vLLM 서빙 아키텍처]] - GPU를 소비하는 추론 런타임
- [[kserve-llminferenceservice-deep-dive|KServe LLMInferenceService]] - GPU 서빙 배포 추상화
- [[llm-serving-runtime-stack|LLM 서빙 런타임 스택]] - 서빙 레이어 전반
- [[ai-model-serving-platform-map|AI 모델 서빙 플랫폼 지도]] - 전체 서빙 분기점
- [[istio-gateway-inference-routing|Gateway 추론 라우팅]] - 추론 트래픽 라우팅
- [[llm-observability-cost|LLM 관측성과 비용]] - GPU/queue/비용 지표 분리
- [[deepspec-speculative-decoding|DeepSpec과 Speculative Decoding]] - GPU 처리량을 높이는 추론 최적화
- [[kubernetes-ai-serving-infra|Kubernetes AI Serving Infra]] - 이 글이 속한 Kubernetes 운영 경계

## 참고 자료

- [Kubernetes Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
- [Kubernetes DRA](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
