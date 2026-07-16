<!-- infographic-hero -->
![KServe와 Ray Serve 선택 기준 핵심 요약](figures/infographic.svg?v=runtime-tabs-20260706)

*Figure 1: KServe와 Ray Serve 선택 기준. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# KServe vs Ray Serve: CRD Control Plane과 Python Serving Graph

이 글은 더 이상 KServe와 Ray Serve를 한 글 안에서 모두 자세히 설명하지 않는다. 상세 설명은 [[kserve-llminferenceservice-deep-dive|KServe LLMInferenceService]]와 [[ray-serve-llm-deep-dive|Ray Serve LLM]]로 분리했고, 이 글은 선택 기준과 교차 링크 허브로 둔다.

![KServe와 Ray Serve 비교 구조도](figures/architecture.svg?v=runtime-tabs-20260706)

*Figure 2: KServe와 Ray Serve의 책임 경계 비교. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

## 먼저 나눌 질문

KServe는 Kubernetes CRD와 controller 중심이다. model deployment를 YAML로 선언하고, controller가 Deployment, Service, Gateway route, status condition을 reconcile한다. ArgoCD, RBAC, namespace, policy, audit가 중요한 platform에서는 KServe가 자연스럽다.

Ray Serve는 Python graph와 Ray actor 중심이다. retrieval, policy, model call, postprocess, tool call 같은 여러 단계를 Python application으로 묶고, replica와 autoscaling을 Ray runtime으로 관리한다. 복잡한 serving graph와 custom routing이 핵심이면 Ray Serve가 자연스럽다.

## 비교표

| 기준 | KServe | Ray Serve |
|---|---|---|
| 중심 API | Kubernetes CRD | Python deployment graph |
| 운영 경계 | namespace, RBAC, GitOps, Gateway | Ray cluster, actor, replica, graph |
| 강점 | 선언형 lifecycle, platform governance | 유연한 Python orchestration, multi-stage pipeline |
| LLM runtime | vLLM 등 runtime을 CRD로 감싼다 | vLLM/SGLang 등을 graph 안에 붙인다 |
| 관측성 | CRD condition, Kubernetes event, route metric | Ray dashboard, Serve metric, stage latency |

## 같이 쓰는 경우

둘 중 하나만 선택해야 하는 것은 아니다. cluster platform은 KServe로 표준 model endpoint를 관리하고, 특정 팀의 복잡한 agent/RAG pipeline은 Ray Serve로 운영할 수 있다. 다만 같은 traffic path에서 둘을 섞을 때는 책임을 분명히 해야 한다. KServe가 endpoint lifecycle을 맡는지, Ray Serve가 application graph를 맡는지, Gateway가 어느 layer로 traffic을 보내는지 명확해야 한다.

## 이어서 읽기

- [[kserve-llminferenceservice-deep-dive|KServe LLMInferenceService]]
- [[ray-serve-llm-deep-dive|Ray Serve LLM]]
- [[vllm-serving-architecture|vLLM Serving Runtime]]
- [[kubernetes-ai-serving-infra|Kubernetes AI Serving Infra]]

## 참고 자료

- [KServe LLMInferenceService](https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview)
- [Ray Serve LLM](https://docs.ray.io/en/latest/serve/llm/index.html)
