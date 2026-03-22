---
title: Amazon RDS Blue/Green 배포와 카나리(Canary) 배포 개요
slug: "amazon-rds-bluegreen-배포와-카나리canary-배포-개요"
category: cloud
tags: ["amazon-rds", "aws", "blue-green-deployment", "canary-deployment", "deployment-strategy", "devops", "release-management", "zero-downtime"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.557885+00:00"
---

> **NOTE:**
> - Amazon RDS **Blue/Green 배포**는 **안전하고 효율적인 데이터베이스 업데이트**를 지원하는 기능입니다. 메이저 및 마이너 버전 업그레이드, DB 엔진 타입 변경 등 다양한 RDS 업데이트 작업 시 **다운타임 최소화**와 **위험 감소**를 제공합니다. [[참조링크](https://tech.cloud.nongshim.co.kr/blog/aws/2482/)]

- All at once: Shift everything, monitor, terminate blue fleet
- Canary: Shift a small portion of traffic and monitor
- Linear: Shift traffic in linearly spaced steps


- **소수 트래픽 우선 전환**
    
    - 전체 트래픽 중 아주 작은 비율(예: 1~5%)만 새 버전으로 라우팅합니다.
        
    - 나머지 트래픽은 기존의 안정된 버전이 처리합니다.
        
- **모니터링 및 검증**
    
    - 카나리 환경(소수 인스턴스)에 할당된 트래픽을 집중적으로 모니터링합니다.
        
    - 오류율, 응답 시간, 리소스 사용량, 로그 등을 면밀히 살펴보고, 문제가 발견되면 즉시 롤백합니다.
        
- **점진적 확대**
    
    - 카나리 배포가 안정적이라고 판단되면 트래픽 비율을 점진적으로 늘려 전체 롤아웃합니다.
        
    - 문제 발생 시 어느 단계에서든 롤백이 가능하므로 전체 서비스 다운타임이나 대규모 버그 노출을 방지할 수 있습니다.
        
- **주요 장점**
    
    - **리스크 최소화**: 새 버전의 치명적 버그가 전체 사용자를 덮치는 것을 방지합니다.
        
    - **빠른 피드백**: 실제 사용자 환경에서 소규모로 검증하여 빠르게 이슈를 발견할 수 있습니다.
        
    - **무중단 배포**: 전체 서비스 가용성을 유지하면서 배포할 수 있습니다.
        
- **왜 ‘카나리’인가?**
    
    - 옛날 탄광에서 유독가스 누출 징후를 감지하기 위해 새장 안에 카나리(작은 새)를 풀어놨던 관행에서 유래했습니다.
        
    - 카나리가 먼저 위험 신호(가스 중독)를 보이면, 광부들은 위험을 감지하고 대피했습니다.
        
    - 소프트웨어 배포에서도 카나리는 먼저 위험을 감지하는 역할을 하므로 같은 이름을 사용합니다.