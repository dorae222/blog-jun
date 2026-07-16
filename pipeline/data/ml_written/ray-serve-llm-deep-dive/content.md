<!-- infographic-hero -->
![Ray Serve LLM: Python-native Multi-node Serving Graph 핵심 요약](figures/infographic.svg?v=runtime-tabs-20260706)

*Figure 1: Ray Serve LLM: Python-native Multi-node Serving Graph 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# Ray Serve LLM: Python-native Multi-node Serving Graph

Ray Serve는 Kubernetes CRD가 아니라 Python-native serving layer다. KServe가 model serving을 Kubernetes API로 선언한다면, Ray Serve는 Python deployment graph와 Ray actor/replica로 online inference application을 구성한다. 그래서 Ray Serve는 KServe와 같은 글에 묶어 설명하면 핵심이 흐려진다.

Ray Serve LLM 문서 기준 Ray Serve LLM은 production LLM serving을 위한 scalable framework이며 OpenAI-compatible API, multi-node/multi-model deployment, autoscaling, custom routing, vLLM/SGLang 같은 engine 연동을 강조한다. 이 글은 Ray Serve를 독립 파트로 두고, 언제 Ray Serve가 맞는지와 어떤 운영 지표를 봐야 하는지 정리한다.

## Ray Serve를 선택하는 기준

Ray Serve가 강한 영역은 Python graph다. retrieval, rerank, policy, moderation, prompt assembly, model call, postprocess, tool call 같은 단계를 하나의 Python application graph로 조립하고 싶다면 Ray Serve가 자연스럽다. 단일 model endpoint만 필요하다면 vLLM server나 KServe CRD가 더 단순할 수 있다. 그러나 여러 model, 여러 stage, custom routing, Python business logic이 섞이면 Ray Serve의 장점이 커진다.

Ray Serve는 framework-agnostic serving layer이므로 PyTorch, TensorFlow, scikit-learn, arbitrary Python logic도 함께 배치할 수 있다. LLM workload에서는 vLLM 같은 engine을 Ray Serve deployment 안에서 사용하고, Serve가 HTTP ingress, replica, autoscaling, graph orchestration을 담당하는 형태가 많다.

## Actor, replica, graph

Ray Serve 운영에서는 Pod보다 actor와 replica를 봐야 한다. Kubernetes 위에서 Ray cluster를 돌리더라도 장애 분석은 Ray head, worker, placement group, replica state, queue depth, autoscaling decision으로 내려간다. Kubernetes `Running`은 Ray Serve application이 건강하다는 뜻이 아니다.

Deployment graph는 강력하지만 versioning이 중요하다. model version, prompt version, retriever version, postprocess logic이 Python 코드 안에 섞이면 GitOps diff만으로 운영자가 변경 범위를 파악하기 어렵다. 따라서 Ray Serve application도 config, model URI, route, graph version, rollout policy를 명확히 문서화해야 한다.

## Multi-node와 routing

Ray Serve LLM은 multi-node inference, prefill-decode disaggregation, custom routing, multi-LoRA, engine-agnostic architecture 같은 고급 패턴을 지원한다. 이 기능은 모델이 커지고 traffic이 다양해질수록 중요해진다. prefix-aware routing이나 session-aware routing은 cache hit와 tail latency에 직접 영향을 준다.

그러나 routing logic을 Python 코드로 자유롭게 만들 수 있다는 것은 운영 책임도 커진다는 뜻이다. 어떤 request가 어떤 replica로 갔는지, cache locality가 어떻게 결정됐는지, autoscaler가 왜 scale out하지 않았는지 추적 가능해야 한다. Ray dashboard와 Prometheus metric, application log를 같은 request id로 묶어야 한다.

## Ray Serve 파트에서 파생할 글

| 글 후보 | 다룰 내용 | 연결 글 |
|---|---|---|
| Ray Serve graph 설계 | deployment graph, ingress, handle, dependency | 이 글 |
| Ray Serve LLM with vLLM | vLLM engine replica, OpenAI API, streaming | [[vllm-serving-architecture|vLLM]] |
| Ray autoscaling | Serve replica autoscaling, Ray cluster autoscaler | Kubernetes GPU 글 |
| Ray Data LLM | offline batch inference와 online Serve 분리 | 데이터 파이프라인 글 |
| Ray vs KServe | Python graph와 CRD control plane 선택 | [[kserve-ray-serve-llm|비교 허브]] |

## 운영 Runbook

요청이 느리면 HTTP ingress만 보지 말고 Serve queue와 deployment graph stage latency를 본다. model stage가 느린지, retrieval stage가 느린지, routing stage가 느린지 분리한다. replica가 부족하면 Serve autoscaling metric과 Ray cluster autoscaler를 같이 본다. worker가 죽으면 Kubernetes Pod event와 Ray actor failure를 함께 확인한다. OpenAI-compatible API가 깨지면 engine(vLLM/SGLang)과 Serve wrapper 중 어느 쪽이 응답 형식을 바꿨는지 contract test로 확인한다.

## 기존 글과 이어서 보기

- generation engine은 [[vllm-serving-architecture|vLLM]]에서 본다.
- Kubernetes 기반 resource와 GPU 배치는 [[kubernetes-ai-serving-infra|Kubernetes AI Serving Infra]]에서 본다.
- KServe와 선택 기준은 [[kserve-ray-serve-llm|KServe vs Ray Serve]]에서 본다.
- 전체 runtime 입구는 [[llm-serving-runtime-stack|LLM Serving Runtime Stack]]에 둔다.

## 참고 자료

- [Ray Serve documentation](https://docs.ray.io/en/latest/serve/index.html)
- [Ray Serve LLM documentation](https://docs.ray.io/en/latest/serve/llm/index.html)
- [Ray Data LLM documentation](https://docs.ray.io/en/latest/data/working-with-llms.html)

## Deployment config와 code versioning

Ray Serve는 Python 코드로 graph를 만들기 때문에 유연하지만, 그만큼 versioning 규칙이 중요하다. model URI, prompt template, retriever config, rerank policy, postprocess logic, routing rule이 모두 Python 안에 숨으면 운영자는 diff를 읽기 어렵다. production에서는 graph code와 runtime config를 분리하고, config는 GitOps나 release artifact로 추적한다.

Ray Serve deployment에는 replica 수, autoscaling policy, max ongoing requests, resource requirements, route prefix, health check가 들어간다. 이 값들은 Kubernetes Deployment의 replicas와 비슷해 보이지만 Ray Serve scheduler와 actor lifecycle을 거친다. 따라서 `kubectl get pods`만으로는 충분하지 않고 Ray Serve application status와 replica 상태를 확인해야 한다.

## Graph stage별 관측성

Ray Serve가 빛나는 곳은 multi-stage application이다. 하지만 multi-stage일수록 stage별 latency를 기록하지 않으면 병목이 보이지 않는다. retrieval, rerank, policy, model generation, postprocess, tool call을 각각 span으로 남긴다. request id가 graph 전체를 관통해야 하고, Ray actor log와 application log가 같은 id를 가져야 한다.

Ray dashboard는 cluster와 Serve 상태를 보는 데 유용하지만, business metric을 대신하지는 않는다. model별 token/sec, tenant별 quota, retrieval hit, answer quality 같은 지표는 application layer에서 붙여야 한다. Ray Serve와 vLLM metric을 함께 볼 수 있어야 "graph가 느린지 engine이 느린지"를 분리할 수 있다.

## Kubernetes 위의 Ray Serve

Kubernetes에서 Ray Serve를 운영하면 두 control plane이 겹친다. Kubernetes는 Pod와 Node를 관리하고, Ray는 actor와 worker를 관리한다. 장애가 나면 둘을 모두 봐야 한다. Pod가 정상이어도 Ray actor가 재시작 중일 수 있고, Ray worker는 정상이어도 Gateway route가 잘못될 수 있다. KubeRay를 쓴다면 RayCluster, RayService, head/worker Pod, Serve deployment 상태를 함께 문서화한다.

Ray Serve는 실험과 복잡한 graph에 강하지만, platform governance가 약해지지 않도록 release, rollback, observability, security boundary를 명확히 해야 한다. 자유로운 Python graph는 장점이면서 운영 리스크이기도 하다.

## 실제로 분리해서 쓸 하위 목차

Ray Serve 탭은 Python application 운영 관점으로 확장한다. 첫째, Ray Serve 기본 글에서는 deployment, ingress, handle, replica, autoscaling을 다룬다. 둘째, Ray Serve LLM 글에서는 vLLM/SGLang engine, OpenAI-compatible API, streaming을 다룬다. 셋째, serving graph 글에서는 retrieval, rerank, policy, generation, postprocess를 stage로 나눈다. 넷째, Ray on Kubernetes 글에서는 KubeRay, RayCluster, RayService, head/worker Pod, placement group을 다룬다. 다섯째, autoscaling 글에서는 Serve replica autoscaling과 cluster autoscaler를 같이 본다. 여섯째, observability 글에서는 Ray dashboard, Prometheus, stage latency, actor failure, request tracing을 다룬다.

이렇게 나누면 Ray Serve는 KServe와 비교되는 배포 도구가 아니라, Python-native serving graph와 Ray runtime을 학습하는 독립 트랙이 된다. 특히 복잡한 agent/RAG pipeline을 운영하려면 Ray Serve 쪽 글이 별도로 쌓여야 한다.

## 운영 문서 최소 구성

이 runtime 파트의 모든 후속 글은 같은 형식을 따른다. 먼저 어떤 request path를 책임지는지 한 문장으로 정의한다. 다음으로 배포 단위, 설정값, metric, 장애 증상, rollback 단위를 표로 적는다. 마지막에는 "이 runtime이 맡지 않는 책임"을 명시한다. 이 경계가 있어야 vLLM, TEI, KServe, Ray Serve가 서로 섞이지 않고 독립 탭처럼 쌓인다.

![Ray Serve LLM: Python-native Multi-node Serving Graph 운영 구조](figures/architecture.svg?v=runtime-tabs-20260706)

*Figure 2: Ray Serve LLM: Python-native Multi-node Serving Graph 운영 구조. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
