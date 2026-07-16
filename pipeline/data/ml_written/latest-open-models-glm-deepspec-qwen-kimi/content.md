<!-- infographic-hero -->
![최신 오픈 모델 흐름: GLM-5.2, DeepSpec, Qwen, Kimi 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: 최신 오픈 모델 흐름: GLM-5.2, DeepSpec, Qwen, Kimi 한 장 요약. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

# 최신 오픈 모델 흐름: GLM-5.2, DeepSpec, Qwen, Kimi

모델 글은 benchmark 순위보다 운영 특성을 먼저 본다. long context, tool use, reasoning mode, 라이선스, serving 비용, fine-tuning 가능성이 실제 선택 기준이다. GLM-5.2는 공식 문서 기준 1M context와 long-horizon coding agent를 전면에 둔다. DeepSpec은 모델 자체라기보다 speculative decoding 연구/실험 codebase다. Qwen과 Kimi 계열은 agentic coding, 긴 컨텍스트, tool-use 성능 비교에서 함께 봐야 한다.

![최신 오픈 모델 흐름: GLM-5.2, DeepSpec, Qwen, Kimi 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: 최신 오픈 모델 흐름: GLM-5.2, DeepSpec, Qwen, Kimi 운영 흐름. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

## 어디까지 다루는 글인가

이 글은 새 모델 발표를 뉴스처럼 나열하지 않는다. GLM-5.2처럼 long-context와 coding agent를 앞세운 모델, DeepSpec처럼 추론 가속 codebase에 가까운 프로젝트, Qwen/Kimi처럼 실제 agentic coding과 tool-use 비교에서 자주 등장하는 계열을 같은 표에 올려 운영 관점으로 비교한다. 여기서 다루는 사실은 각 프로젝트의 공식 문서와 원문 저장소에서 확인되는 범위로 한정한다. 새로운 버전이나 파라미터 수, 벤치마크 점수를 이 글에서 만들어 붙이지 않는다.

## 오픈 모델을 읽는 다섯 가지 축

오픈 모델은 발표 순서나 benchmark 순위로 줄 세우기보다, 아래 다섯 축으로 각 모델의 위치를 잡는 편이 운영에 가깝다. 이 글에서 다루는 GLM-5.2, DeepSpec, Qwen, Kimi도 이 축 위에 놓고 보면 서로 다른 문제를 푸는 프로젝트라는 점이 분명해진다.

| 축 | 무엇을 보나 | 확인 기준 |
|----|------------|-----------|
| License | 진짜 open weight인지, 재배포와 fine-tuning, 사내 서비스가 허용되는지 | 라이선스 문서에서 상업적 사용과 재배포 범위를 직접 확인했는가 |
| 크기와 구조 | dense인지 MoE인지, 활성 파라미터가 서빙 메모리에 주는 영향 | 모델 카드에서 구조와 요구 메모리를 확인했는가 |
| Context 길이 | 긴 컨텍스트가 실제 코드베이스나 문서 묶음에서 latency와 비용을 감당하는가 | 최대 context와 그때의 처리량을 함께 확인했는가 |
| 추론 최적화 | speculative decoding, batching, KV cache 재사용 같은 가속 경로가 있는가 | runtime이 지원하는 최적화 경로를 확인했는가 |
| Serving 친화성 | vLLM, sglang, TGI 같은 runtime 지원과 quantization 경로가 있는가 | runtime 지원과 quantization 산출물이 실제로 있는가 |

주의할 점은 이 다섯 축이 모두 "모델 자체"에 관한 것은 아니라는 것이다. License와 크기는 모델의 성질이지만, 추론 최적화와 serving 친화성은 모델보다 runtime과 하드웨어가 결정하는 부분이 크다. 그래서 같은 모델도 어떤 runtime에 올리느냐에 따라 실무 평가가 달라진다. 여기에 tool use가 한 축 더 붙는다. agent loop에서 도구 호출이 끊겼을 때 복구되는지는 모델과 runtime이 함께 만드는 특성이라, 뒤에서 Qwen/Kimi를 볼 때 따로 짚는다.

## 본문 모델들을 축 위에 다시 놓기

앞의 다섯 축으로 이 글의 대상을 다시 정리하면 다음과 같다. 새로운 수치를 더하지 않고, 공식 문서와 원문 저장소에서 확인되는 범위만 위치로 표시한다.

GLM-5.2는 Context 길이 축에서 앞선다. 공식 문서 기준 1M context와 long-horizon coding agent를 전면에 두고, 큰 코드베이스를 통째로 넘겨 작업하는 codebase takeover를 시각 중심에 둔다. 이 모델을 평가할 때 핵심 질문은 성능 점수가 아니라, 그 긴 컨텍스트를 실제로 감당할 메모리와 처리량을 확보할 수 있는지다.

DeepSpec은 축 자체가 다르다. foundation model이 아니라 speculative decoding 연구와 실험 codebase에 가깝다. 즉 "어떤 모델을 고를까" 축이 아니라 "고른 모델을 어떻게 더 빨리 돌릴까"라는 추론 최적화 축에 속한다. 다른 세 계열과 같은 표의 모델 칸에 나란히 올리면 비교 자체가 어긋난다.

Qwen과 Kimi 계열은 agentic coding, 긴 컨텍스트, tool-use 성능 비교에서 자주 함께 등장한다. 그래서 이 둘은 개별 점수보다 tool-use loop에서의 실패 복구, 즉 함수 호출과 MCP tool 사용이 끊겼을 때 작업을 이어받는 능력을 나란히 놓고 보는 편이 낫다. License와 serving 친화성 축에서 실제 채택 후보가 되려면, 재배포 조건과 runtime 지원을 각 모델 카드에서 따로 확인해야 한다.

## 서빙 관점: 오픈 모델을 실제로 돌릴 때

오픈 모델의 값어치는 웨이트를 받아 직접 서빙할 수 있다는 데 있지만, 그 순간부터는 모델 성질보다 runtime과 하드웨어가 체감 성능을 결정한다. 세 가지를 먼저 본다.

첫째, GPU 메모리다. 긴 컨텍스트는 그 자체로 KV cache 메모리를 빠르게 키운다. GLM-5.2처럼 1M context를 앞세운 모델은, 최대 길이를 실제로 채워 쓰는 순간 메모리와 처리량이 함께 압박받는다. 최대 context 값과 그때의 batch 크기를 분리해서 확인해야 한다.

둘째, quantization이다. 웨이트를 낮은 정밀도로 바꾸면 메모리와 비용을 줄일 수 있지만, 모델마다 지원되는 quantization 산출물과 품질 저하 폭이 다르다. runtime이 어떤 형식을 읽을 수 있는지까지 함께 봐야 실제로 배포 가능한 경로가 된다.

셋째, runtime 선택이다. vLLM, sglang, TGI 같은 서빙 런타임은 batching, cache, 스케줄링 방식이 서로 다르다. 같은 모델도 어느 런타임에 올리느냐에 따라 latency와 throughput이 달라진다. 런타임 내부 구조는 [[vllm-serving-architecture|vLLM 서빙 아키텍처]]와 [[llm-serving-runtime-stack|LLM 서빙 런타임 스택]]에서 계층별로 나눠 본다.

추론 속도를 더 끌어올리는 방향으로는 speculative decoding이 있다. 이 글의 DeepSpec이 바로 그 계열의 실험 codebase이며, draft model로 토큰을 미리 제안하고 본 모델이 검증하는 구조는 [[deepspec-speculative-decoding|DeepSpec과 Speculative Decoding]]에서 이어서 본다.

## 실무 관점: 모델 선택 기준

정리하면 오픈 모델을 고르는 순서는 benchmark가 아니라 제약에서 시작한다.

먼저 License를 고정한다. 사내 서비스, 재배포, fine-tuning 조건이 맞지 않으면 성능이 아무리 좋아도 후보에서 빠진다. 다음으로 Context와 비용의 균형을 본다. 긴 컨텍스트가 필요한 작업인지, 아니면 chunking과 검색으로 충분한지에 따라 필요한 모델이 달라진다. 그다음 serving 경로를 확인한다. 원하는 runtime과 quantization이 지원되지 않으면 배포 자체가 막힌다. 마지막으로 tool-use 신뢰성을 본다. agent loop에서 도구 호출이 끊겼을 때 복구가 되는지가, 데모와 프로덕션을 가르는 지점이다.

이 순서의 목적은 선택지를 넓히는 것이 아니라 줄이는 것이다. 벤치마크 표 한 장으로 결정하려 하면 매번 새 모델 발표에 흔들리지만, 제약에서 시작하면 후보가 몇 개로 좁혀진다. 관측 측면에서는 model, route, queue_time, ttft, itl, input/output tokens, cache_hit 같은 축을 미리 정해 두면, 어떤 모델이 실제로 비용과 지연을 얼마나 쓰는지 나중에 재구성할 수 있다.

## 자주 나오는 오해

- 벤치마크 점수만 보고 운영 모델을 고른다. 점수는 운영 특성인 latency, 비용, license, tool-use 안정성을 설명하지 못한다.
- 1M context를 chunking과 RAG의 완전한 대체재로 오해한다. 긴 컨텍스트는 선택지를 넓히지만, 그만큼 메모리와 비용을 요구한다.
- DeepSpec 같은 draft decoding 프로젝트를 foundation model과 같은 축에서 비교한다. 하나는 모델 선택 축, 다른 하나는 추론 최적화 축이다.

## 관련 문서

- [[ai-model-serving-platform-map|AI 모델 서빙 플랫폼 지도]] - 오픈 모델을 어느 플랫폼에 올릴지 정하는 전체 분기점
- [[model-inference-research-hub|모델 추론 리서치 허브]] - 모델 선택과 추론 연구 글의 상위 목차
- [[deepspec-speculative-decoding|DeepSpec과 Speculative Decoding]] - 추론 가속과 draft decoding 이어 읽기
- [[vllm-serving-architecture|vLLM 서빙 아키텍처]] - 오픈 모델 runtime 내부 구조
- [[llm-serving-runtime-stack|LLM 서빙 런타임 스택]] - 서빙 런타임 계층 비교
- [[llm-observability-cost|LLM 관측성과 비용]] - 서빙 비용과 운영 지표
- [[ai-inference-paper-review-roadmap|AI Inference 논문 리뷰 로드맵]] - 추론 연구 논문 흐름

## 모델/추론 연구 파트

이 글은 AI 서빙 플랫폼 목차의 한 항목이 아니라 모델 선택과 추론 연구 파트의 독립 글이다. [[ai-inference-paper-review-roadmap|AI Inference Paper Review Roadmap]]에서 논문 흐름을 먼저 보고, [[deepspec-speculative-decoding|DeepSpec과 Speculative Decoding]]에서 추론 가속으로 이어서 읽는다.

## 참고 자료

- [GLM-5.2 docs](https://docs.z.ai/guides/llm/glm-5.2)
- [DeepSpec GitHub](https://github.com/deepseek-ai/DeepSpec)
