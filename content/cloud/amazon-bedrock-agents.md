---
title: Amazon Bedrock Agents
slug: "amazon-bedrock-agents"
category: cloud
tags: ["agents", "amazon-bedrock", "api", "automation", "aws", "generative-ai", "knowledge-base", "orchestration"]
status: published
post_type: tutorial
quality_score: 9.0
created_at: "2026-03-02T01:08:04.833615+00:00"
---

> **NOTE:**
> - task 자동화
> - External Tool 연동

Amazon Bedrock Agents는 애플리케이션에서 자율 에이전트를 구축하고 구성할 수 있는 기능을 제공합니다. 에이전트를 통해 최종 사용자가 조직 데이터와 사용자 입력을 기반으로 작업을 완료하도록 도울 수 있습니다. 에이전트는 파운데이션 모델(FM), 데이터 소스, 소프트웨어 애플리케이션, 사용자 대화 간의 상호 작용을 오케스트레이션하며, API를 자동으로 직접 호출해 작업을 수행하고 지식 기반을 간접 호출해 해당 작업을 보완하는 정보를 얻습니다. 에이전트를 통합하면 개발 노력을 단축하여 생성형 인공 지능(생성형 AI) 애플리케이션을 빠르게 제공할 수 있습니다.

에이전트를 사용하면 고객을 위해 작업을 자동화하고 질문에 답변할 수 있습니다. 예를 들어, 고객의 보험 청구를 처리해 주거나 고객의 여행 예약을 도와주는 에이전트를 만들 수 있습니다. 용량 프로비저닝, 인프라 관리 또는 사용자 지정 코드 작성에 대해 걱정할 필요가 없습니다. Amazon Bedrock은 프롬프트 엔지니어링, 메모리, 모니터링, 암호화, 사용자 권한, API 간접 호출 등을 관리합니다.

에이전트는 다음과 같은 작업을 수행할 수 있습니다.

- 파운데이션 모델을 확장하여 사용자 요청을 이해하고, 에이전트가 수행해야 할 작업을 더 작은 단계로 세분화합니다.
- 자연스러운 대화를 통해 사용자로부터 추가 정보를 수집합니다.
- 회사 시스템에 API 직접 호출을 수행하여 고객 요청을 이행하기 위한 조치를 취합니다.
- 데이터 소스를 쿼리하여 성능과 정확성을 높입니다.

에이전트를 사용하려면 다음 단계를 따르세요.

1. (선택 사항) 지식 기반을 생성하여 프라이빗 데이터를 이 데이터베이스에 저장합니다. 자세한 내용은 [Amazon Bedrock 지식 기반을 사용하여 데이터 검색 및 AI 응답 생성](https://docs.aws.amazon.com/ko_kr/bedrock/latest/userguide/knowledge-base.html) 섹션을 참조하세요.

2. 사용 사례에 맞게 에이전트를 구성하고 다음 구성 요소 중 적어도 하나 이상을 추가합니다.

    - 에이전트가 수행할 수 있는 작업 그룹을 하나 이상 정의해야 합니다. 작업 그룹을 정의하는 방법과 에이전트가 작업 그룹을 처리하는 방법은 [작업 그룹을 사용하여 에이전트가 수행할 작업 정의](https://docs.aws.amazon.com/ko_kr/bedrock/latest/userguide/agents-action-create.html) 섹션을 참고하세요.
    
    - 지식 기반을 에이전트에 연결하여 성능을 강화할 수 있습니다. 자세한 내용은 [지식 기반을 사용하여 에이전트에 대한 응답 생성 강화](https://docs.aws.amazon.com/ko_kr/bedrock/latest/userguide/agents-kb-add.html) 섹션을 참고하세요.

3. (선택 사항) 에이전트의 사전 처리, 오케스트레이션, 지식 기반 응답 생성, 사후 처리 단계에 대한 프롬프트 템플릿을 수정하여 특정 사용 사례에 맞게 동작을 사용자 지정합니다. 자세한 내용은 [Amazon Bedrock의 고급 프롬프트 템플릿을 사용하여 에이전트의 정확도 향상](https://docs.aws.amazon.com/ko_kr/bedrock/latest/userguide/advanced-prompts.html) 섹션을 참조하세요.

4. Amazon Bedrock 콘솔에서 또는 `TSTALIASID`에 대한 API 직접 호출을 통해 에이전트를 테스트하고 필요하면 구성을 수정합니다. 추적(trace)을 사용하여 오케스트레이션의 각 단계에서 에이전트의 추론 과정을 검사할 수 있습니다. 자세한 내용은 [에이전트 동작 테스트 및 문제 해결](https://docs.aws.amazon.com/ko_kr/bedrock/latest/userguide/agents-test.html) 및 [trace를 사용하여 에이전트의 단계별 추론 프로세스 추적](https://docs.aws.amazon.com/ko_kr/bedrock/latest/userguide/trace-events.html) 섹션을 참조하세요.

5. 에이전트를 충분히 다듬어 애플리케이션에 배포할 준비가 되면, 에이전트의 특정 버전을 가리키는 별칭을 생성합니다. 자세한 내용은 [애플리케이션에서 Amazon Bedrock 에이전트 배포 및 사용](https://docs.aws.amazon.com/ko_kr/bedrock/latest/userguide/agents-deploy.html) 섹션을 참조하세요.

6. 애플리케이션에서 에이전트 별칭에 대한 API 호출을 수행하도록 설정합니다.

7. 에이전트의 동작을 반복적으로 개선하며 필요에 따라 더 많은 버전과 별칭을 생성합니다.

https://docs.aws.amazon.com/ko_kr/bedrock/latest/userguide/agents.html