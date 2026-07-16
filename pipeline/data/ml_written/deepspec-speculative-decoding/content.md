<!-- infographic-hero -->
![DeepSpec과 Speculative Decoding: draft model을 어떻게 훈련하고 평가할까 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: DeepSpec과 Speculative Decoding: draft model을 어떻게 훈련하고 평가할까 한 장 요약. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

# DeepSpec과 Speculative Decoding: draft model을 어떻게 훈련하고 평가할까

Speculative decoding은 작은 draft model이 후보 토큰을 먼저 만들고, 큰 target model이 이를 검증해 latency를 줄이는 방식이다. DeepSpec은 이 흐름을 데이터 준비, draft model 구현, 학습, 평가 코드로 나눈다. 운영 관점에서는 가속률만 보면 안 된다. acceptance rate, target model 호출 절감, 품질 손실, GPU memory overhead를 함께 봐야 한다.

![DeepSpec과 Speculative Decoding: draft model을 어떻게 훈련하고 평가할까 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: DeepSpec과 Speculative Decoding: draft model을 어떻게 훈련하고 평가할까 운영 흐름. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

## 어디까지 다루는 글인가

이 글은 speculative decoding을 이론 한 줄로 끝내지 않는다. draft model을 어떻게 만들고, target model이 어떤 방식으로 검증하며, acceptance rate와 품질 손실을 어떤 실험으로 봐야 하는지 DeepSpec 코드베이스 기준으로 정리한다.

## 왜 speculative decoding인가

autoregressive 디코딩은 토큰을 하나 생성할 때마다 모델 전체를 한 번 forward pass 해야 한다. 토큰 사이에 순차 의존성이 있어 이 과정을 병렬화하기 어렵고, 생성 길이가 늘어날수록 latency가 토큰 수에 비례해 쌓인다. 특히 큰 target model은 forward pass 한 번의 비용이 크기 때문에, 실제 서빙에서 이 순차 병목이 사용자 체감 지연의 대부분을 차지한다.

speculative decoding은 이 병목을 우회한다. 값이 싼 draft model이 다음 토큰 여러 개를 미리 제안(propose)하고, 비싼 target model이 그 후보 sequence를 한 번의 forward pass로 병렬 검증(verify)한다. target 분포와 일치하는 접두(prefix)까지는 그대로 채택(accept)하고, 처음으로 어긋나는 지점에서 거부(reject)한 뒤 그 자리를 target의 분포로 다시 sampling한다. 핵심은 이 accept/reject 규칙이 최종 출력 분포를 target model 단독 생성과 동일하게 유지하도록 설계된다는 점이다. 즉 품질을 떨어뜨리지 않고 target model의 forward pass 횟수만 줄이는 것이 목표다.

한 번의 검증에서 draft 후보 k개 중 앞의 몇 개가 채택되면, 그 스텝에서 target model은 여러 토큰을 한꺼번에 확정한 셈이 된다. 채택되는 토큰이 많을수록 같은 출력에 필요한 target forward pass가 줄고, latency가 내려간다. 반대로 채택이 거의 안 되면 검증 비용만 추가되어 이득이 사라진다.

## 검증은 어떻게 품질을 보존하는가

speculative decoding이 "품질 손실 없이"라고 말할 수 있는 이유는 검증 단계의 확률 규칙에 있다. draft 분포 $q$에서 뽑은 토큰 $x$를, target 분포 $p$가 얼마나 지지하느냐에 비례해 채택한다. 표준 speculative sampling 규칙은 채택 확률을 $\min\left(1, \frac{p(x)}{q(x)}\right)$로 둔다. draft가 target보다 그 토큰을 과하게 밀었다면($q(x) > p(x)$) 일정 확률로 거부하고, 그렇지 않으면 그대로 채택한다.

거부가 일어나면 그 자리는 버리는 것이 아니라 잔차 분포 $\left(p(x) - q(x)\right)_+$를 정규화한 값에서 다시 sampling한다. 이렇게 채택과 재sampling을 합치면 최종적으로 각 위치의 토큰은 target 분포 $p$에서 뽑은 것과 통계적으로 동일해진다. 즉 draft가 아무리 나빠도 출력 분포 자체는 target 단독 sampling과 같고, draft 품질은 오직 "얼마나 자주 채택되는가", 즉 속도에만 영향을 준다. 이 성질 덕분에 draft를 공격적으로 작게 잡아도 결과 품질을 걱정할 필요가 없다.

## draft model을 어떻게 훈련하고 선택하는가

speculative decoding의 이득은 draft model이 target 분포를 얼마나 잘 근사하느냐에 달려 있다. draft가 target과 자주 어긋나면 대부분의 후보가 거부되어 검증 비용만 늘고, draft가 너무 무거우면 제안 자체가 느려져 순차 병목이 draft 쪽으로 옮겨갈 뿐이다. 따라서 draft는 "충분히 빠르면서 target을 잘 흉내내는" 지점을 찾는 문제가 된다.

접근 방식은 크게 나뉜다. 첫째, 같은 계열의 작은 모델을 별도 draft로 쓰는 방식이다. target과 tokenizer, 사전학습 코퍼스를 공유하는 작은 모델은 분포가 가까워 acceptance가 높은 편이다. 둘째, target 자신의 hidden state를 재사용해 여러 토큰을 한 번에 예측하는 self-draft 계열이다. Medusa처럼 target에 여러 개의 예측 head를 붙여 다음 위치들을 병렬 추정하는 방식이 여기에 속한다. 별도 draft model을 서빙하지 않아도 되어 memory와 배포가 단순해지는 대신, head를 target에 맞춰 추가로 학습해야 한다.

DeepSpec은 이 흐름을 데이터 준비, draft model 구현, 학습, 평가 코드로 나눠 다룬다. draft를 학습할 때는 target의 출력을 정답으로 삼아 distillation 형태로 맞추는 경우가 많고, 학습 데이터 분포가 실제 서비스 traffic과 어긋나면 벤치마크에서 높던 acceptance가 프로덕션에서 떨어질 수 있다. 그래서 draft 학습은 모델 구조 선택만큼이나 어떤 prompt 분포로 맞추느냐가 중요하다.

## 무엇을 측정할 것인가

speculative decoding을 평가할 때 단일 speedup 숫자 하나로 판단하면 안 된다. 서로 다른 세 층위를 함께 봐야 한다.

- acceptance rate: draft가 제안한 토큰 중 target 검증을 통과한 비율. draft와 target 분포의 근접도를 직접 반영한다.
- 평균 accepted length: 한 번의 검증 스텝에서 확정되는 평균 토큰 수. 이 값이 클수록 target forward pass 한 번당 얻는 토큰이 많아진다.
- 실제 speedup: 위 두 값이 좋아도 최종 지연 감소는 하드웨어와 서빙 상황에 따라 달라진다. batch가 크거나 memory bandwidth가 이미 포화 상태면 이론적 이득이 그대로 나오지 않는다.

품질도 반드시 함께 본다. accept/reject 규칙이 분포를 보존하도록 구현되어 있다면 출력 품질은 target 단독과 같아야 하지만, 구현 오류나 근사(approximate) 검증을 쓰면 미세한 품질 하락이 생길 수 있다. 그래서 greedy와 temperature sampling 각각에서 baseline 대비 품질을 확인하고, 평균 latency만이 아니라 p95, p99 tail과 token throughput을 함께 기록한다. 구체적인 벤치마크 수치는 target/draft 조합과 하드웨어에 따라 크게 달라지므로, 자신의 환경에서 직접 측정한 값으로만 판단한다.

## 체크포인트

| 항목 | 확인 기준 |
|------|-----------|
| Acceptance | draft token이 target 검증을 얼마나 통과하는가 |
| Quality | greedy/temperature 설정에서 baseline 대비 품질 하락이 있는가 |
| Memory | draft model 추가로 GPU memory와 scheduling이 악화되지 않는가 |
| Metrics | latency 평균보다 p95, p99와 token throughput을 같이 보는가 |

## 서빙 스택에서 speculative decoding의 위치

speculative decoding은 모델을 바꾸거나 인프라를 새로 까는 기법이 아니라, 이미 배포된 target model의 디코딩 방식을 바꾸는 런타임 최적화다. 따라서 이 기법은 서빙 스택에서 runtime 계층에 속한다. 같은 계층에는 continuous batching, paged KV cache, quantization 같은 최적화가 함께 놓이고, 이들은 서로 상호작용한다. 예를 들어 batch가 커지면 continuous batching의 이득과 speculative decoding의 이득이 경합하는 구간이 생긴다.

실제 실행은 런타임이 담당한다. vLLM 같은 런타임이 speculative decoding을 어떻게 스케줄링하고 KV cache와 엮는지는 [[vllm-serving-architecture|vLLM 서빙 아키텍처]]에서, model, runtime, scheduler, gateway로 이어지는 서빙 스택 전체 구조는 [[llm-serving-runtime-stack|LLM 서빙 런타임 스택]]에서 다룬다. 이 글은 그 중 runtime 계층에서 "왜 여러 토큰을 미리 제안하고 검증하는가"를 설명하는 조각에 해당한다.

## 언제 이득이고 언제 손해인가

speculative decoding은 항상 이득이 아니다. 이득의 크기는 대체로 두 조건에 따라 갈린다.

첫째, batch 크기다. batch가 작고 요청이 드문 저지연 상황에서는 target model이 memory bandwidth에 묶여(memory-bound) forward pass 비용의 상당 부분이 고정 오버헤드다. 이때 여러 토큰을 한 번에 검증하면 그 고정 비용을 여러 토큰에 나눠 태우므로 이득이 크다. 반대로 batch가 커서 GPU가 이미 연산에 포화(compute-bound)된 상황에서는, 검증에 드는 추가 연산이 그대로 비용으로 잡혀 이득이 줄거나 오히려 손해가 될 수 있다.

둘째, draft와 target의 크기 비율과 근접도다. draft가 target 대비 충분히 가볍고 분포가 가까워 acceptance가 높으면 순이득이 크다. draft가 무겁거나 acceptance가 낮으면 제안과 검증의 추가 비용이 이득을 지운다. 그래서 도입 전에 자신의 traffic으로 acceptance rate와 평균 accepted length를 측정하고, 목표 batch 구간에서 실제 speedup이 남는지 확인하는 편이 안전하다.

DeepSpec처럼 draft 학습과 평가를 코드로 분리해 두면 이런 판단을 실험으로 뒷받침하기 쉽다. 최신 오픈 모델과 기법이 speculative decoding을 어떻게 함께 쓰는지는 [[latest-open-models-glm-deepspec-qwen-kimi|최신 오픈 모델 흐름]]에서 이어서 볼 수 있다.

## 관련 문서

- [[vllm-serving-architecture|vLLM 서빙 아키텍처]] - speculative decoding을 실제로 스케줄링하고 실행하는 런타임
- [[llm-serving-runtime-stack|LLM 서빙 런타임 스택]] - runtime 최적화가 놓이는 서빙 스택 전체 구조
- [[ai-model-serving-platform-map|AI 모델 서빙 플랫폼 지도]] - 서빙 스택 선택의 분기점
- [[latest-open-models-glm-deepspec-qwen-kimi|최신 오픈 모델 흐름]] - DeepSpec 등 최신 모델과 기법 동향
- [[llm-observability-cost|LLM 관측성과 비용]] - acceptance rate와 tail latency 지표의 운영
- [[model-inference-research-hub|모델 추론 연구 허브]] - 추론 최적화 연구 모음

## 참고 자료

- [DeepSpec GitHub](https://github.com/deepseek-ai/DeepSpec)
- [DSpark paper](https://github.com/deepseek-ai/DeepSpec/blob/main/DSpark_paper.pdf)
