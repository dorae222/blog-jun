<!-- infographic-hero -->
![Mastra 핵심 요약](figures/infographic.svg)

*Figure: Mastra 한 장 요약 인포그래픽*

# Mastra: TypeScript 우선 풀스택 AI 에이전트 프레임워크

**Mastra** · **2024-10** · **Agent Framework** · **Apache-2.0**

## 개요

Mastra는 Gatsby의 공동 창업자였던 Sam Bhagwat과 동료들이 2024년 10월 공개한 TypeScript 우선 AI 에이전트 프레임워크다. 그동안 LangChain, LlamaIndex, AutoGen, CrewAI 같은 주요 에이전트 라이브러리는 모두 Python을 1순위 언어로 두고 있었고, JavaScript/TypeScript 포트는 후순위로 유지되었다. 그러나 실제 웹 프론트엔드와 풀스택 개발의 절반 이상이 TypeScript로 작성되며, Vercel AI SDK가 React 생태계의 표준 LLM 클라이언트로 자리잡으면서 TypeScript 진영에 멀티 에이전트 워크플로를 위한 본격적인 추상화가 절실해졌다. Mastra는 정확히 이 빈자리를 채운다.

Mastra의 차별성은 워크플로 엔진과 에이전트 추상화를 동등한 일급 개념으로 두는 데 있다. 다른 프레임워크들이 에이전트를 중심에 두고 워크플로를 부산물로 취급하는 반면, Mastra는 결정적(deterministic) 비즈니스 로직은 워크플로로, 비결정적(non-deterministic) LLM 추론은 에이전트로 분리한다. 이 분리는 프로덕션 환경에서 디버깅과 책임 분담을 명확히 한다. 결제 처리 같은 결정적 단계는 워크플로 step으로 표현되고, "고객 문의 의도 분류"처럼 LLM이 판단해야 할 부분만 에이전트에 위임된다.

라이선스는 Apache 2.0이며 GitHub 스타가 빠르게 증가하고 있다. SoftBank의 Satto Workspace, Marsh McLennan이 7만 5천 명 사원용으로 도입한 사내 검색 도구가 대표적인 엔터프라이즈 사례로 공개되어 있다.

## 아키텍처

Mastra의 컴포넌트는 다음과 같이 계층화된다. 최하단에 Vercel AI SDK가 위치하여 LLM 공급자 추상화를 담당하고, 그 위에 Mastra Core가 워크플로, 에이전트, 도구, 메모리, RAG, 평가, 음성 모듈을 제공한다. 최상단의 mastra dev CLI는 로컬 playground와 핫 리로드 환경을 띄워주며, mastra deploy는 Vercel, Cloudflare Workers, Netlify 등으로의 배포를 자동화한다.

워크플로 엔진은 Inngest와 비슷한 이벤트 기반 결정적 실행 모델을 채택한다. 각 step은 입력 스키마(Zod 기반)와 출력 스키마를 가지며 실패 시 자동 재시도, 부분 재실행(replay)을 지원한다. 에이전트는 자체 메모리 스토어를 가지며 도구 호출 결과가 워킹 메모리에 자동으로 기록된다.

## 핵심 컴포넌트

### Agent

```typescript
import { Mastra } from "@mastra/core";
import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";

const supportAgent = new Agent({
  name: "Support",
  instructions: "고객의 기술 문의에 답변하고 필요하면 KB를 검색한다.",
  model: openai("gpt-4o"),
  tools: { searchKnowledgeBase },
});
```

### Workflow

워크플로는 step의 그래프로 구성되며 then, branch, parallel, dountil, foreach 같은 제어 흐름 연산자를 제공한다.

```typescript
import { createWorkflow, createStep } from "@mastra/core/workflows";
import { z } from "zod";

const fetchOrder = createStep({
  id: "fetch-order",
  inputSchema: z.object({ orderId: z.string() }),
  outputSchema: z.object({ status: z.string(), total: z.number() }),
  execute: async ({ inputData }) => {
    return await api.getOrder(inputData.orderId);
  },
});

const triageRefund = createStep({
  id: "triage-refund",
  inputSchema: z.object({ status: z.string(), total: z.number() }),
  outputSchema: z.object({ approved: z.boolean(), reason: z.string() }),
  execute: async ({ inputData, mastra }) => {
    const agent = mastra.getAgent("refundAgent");
    const result = await agent.generate(
      `다음 주문의 환불 가능 여부를 판단하세요: ${JSON.stringify(inputData)}`,
    );
    return JSON.parse(result.text);
  },
});

const refundWorkflow = createWorkflow({
  id: "refund",
  inputSchema: z.object({ orderId: z.string() }),
  outputSchema: z.object({ approved: z.boolean() }),
})
  .then(fetchOrder)
  .then(triageRefund)
  .commit();
```

### Memory

워킹 메모리(working memory)는 사용자별로 자동 갱신되는 텍스트 슬롯이고, 의미적 메모리(semantic memory)는 pgvector나 Pinecone에 임베딩으로 저장된다. 절차적 메모리는 도구 호출 패턴을 학습해 자주 쓰는 시퀀스를 짧게 만든다.

### Evals

Mastra는 LLM-as-judge 기반 평가 모듈을 빌트인으로 제공한다. faithfulness, hallucination, toxicity, bias 같은 표준 메트릭이 즉시 사용 가능하며, 사용자 정의 메트릭도 정의할 수 있다.

### Voice

Voice 모듈은 OpenAI Realtime API, Deepgram, ElevenLabs 등의 STT/TTS를 통합 인터페이스로 묶는다. 동일한 Agent 정의가 텍스트 채팅과 음성 통화에서 재사용된다.

### mastra dev

```bash
npx mastra dev
```

명령 한 번이면 localhost:4111에 playground가 뜬다. 모든 워크플로의 그래프, 에이전트의 도구 호출 트레이스, 메모리 상태, 평가 결과가 실시간으로 시각화된다.

## 코드 예제

다음은 RAG 기반 지원 에이전트를 Next.js 라우트에서 사용하는 패턴이다.

```typescript
// src/mastra/index.ts
import { Mastra } from "@mastra/core";
import { PgVector } from "@mastra/pg";
import { supportAgent } from "./agents/support";
import { refundWorkflow } from "./workflows/refund";

export const mastra = new Mastra({
  agents: { supportAgent },
  workflows: { refundWorkflow },
  vectors: {
    pgVector: new PgVector({ connectionString: process.env.DATABASE_URL }),
  },
});
```

```typescript
// app/api/chat/route.ts
import { mastra } from "@/src/mastra";

export async function POST(req: Request) {
  const { message, threadId } = await req.json();
  const agent = mastra.getAgent("supportAgent");
  const stream = await agent.stream(message, {
    memory: { thread: threadId, resource: "user-123" },
  });
  return stream.toDataStreamResponse();
}
```

## 사용 사례

### SoftBank Satto Workspace

SoftBank가 사원용 AI 워크스페이스 Satto에 Mastra를 채택했다. 결정적 워크플로(휴가 신청, 비용 보고)와 에이전트(자유로운 사내 문의)를 한 SDK에서 처리한다.

### Marsh McLennan 사내 검색

7만 5천 명 사원이 사용하는 사내 지식 검색 도구가 Mastra 기반으로 구축되었다. RAG, 메모리, 평가가 한 패키지에 통합되어 있어 통합 비용을 크게 줄였다.

### Vercel 풀스택 SaaS

Next.js + Vercel 환경의 SaaS에서 가장 매끄럽게 동작한다. Edge Runtime에서도 가벼운 실행이 가능하다.

## 비교

| 항목 | Mastra | LangGraph (JS) | Vercel AI SDK | OpenAI Agents SDK |
|------|--------|----------------|----------------|--------------------|
| 언어 | TypeScript | TypeScript | TypeScript | Python |
| 워크플로 | 일급 추상화 | StateGraph | 미지원 | 핸드오프 기반 |
| RAG | 빌트인 | 미통합 | 미지원 | 미지원 |
| 메모리 계층 | 3단계 | 단일 | 미지원 | 단일 |
| 평가 | 빌트인 | LangSmith | 미지원 | 빌트인 트레이싱 |
| 음성 | 빌트인 | 미지원 | 별도 | Realtime API |
| 로컬 IDE | mastra dev | LangGraph Studio | 미지원 | 미지원 |
| Next.js 친화성 | 매우 높음 | 보통 | 매우 높음 | 낮음 |

## 한계

첫째, TypeScript 전용이다. Python 백엔드와 혼합 환경을 운용하면 추상화가 두 갈래로 갈리는 부담이 있다. 둘째, 에코시스템 성숙도가 LangChain 대비 낮다. 통합되지 않은 도구는 직접 어댑터를 작성해야 한다. 셋째, Inngest 스타일 결정적 실행이 강력하지만 학습 곡선이 있다. step 분리, 재시도 정책, 멱등성 보장을 의식적으로 설계해야 한다. 넷째, 평가 모듈이 빌트인이지만 Braintrust, Arize 같은 전문 평가 플랫폼만큼 정교하지는 않다.

## 관련 문서

- [[openai-agents-sdk|OpenAI Agents SDK]] - 핸드오프 중심 멀티 에이전트 프레임워크
- [[langgraph-deep-dive|LangGraph 심층 분석]] - 그래프 기반 에이전트 오케스트레이션
- [[mcp|Model Context Protocol]] - 도구 통합 표준 프로토콜
