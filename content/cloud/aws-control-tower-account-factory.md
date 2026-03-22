---
title: AWS Control Tower Account Factory
slug: "aws-control-tower-account-factory"
category: cloud
tags: ["account-factory", "aws", "aws-control-tower", "aws-organizations", "governance", "landing-zone", "networking", "service-catalog", "sso"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.644696+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

---
aliases:
  - AFT
  - Control Tower Account Factory
  - Account Factory

---

> **NOTE:**
> - **표준화된 계정 템플릿**을 통해 새 계정 생성 및 구성 자동화

## 🏗️ AWS Control Tower Account Factory란?

**AWS Control Tower Account Factory**는 조직 내에서 **표준화된 방식으로 AWS 계정을 자동으로 생성하고 구성**할 수 있도록 지원하는 기능입니다. 이는 **AWS Control Tower**의 핵심 구성 요소 중 하나로, 계정 생성 자동화, 표준 가드레일 적용, 네트워크 구성 등을 함께 처리할 수 있게 해줍니다.

---

### 🔍 개념 요약

**Account Factory**는 Control Tower에서 제공하는 **계정 프로비저닝 자동화 도구**로, **Service Catalog**를 기반으로 동작합니다.

> 즉, 조직 내 여러 팀이 **표준 템플릿을 기반으로 새로운 계정을 빠르게 생성**하고, 보안·거버넌스·네트워크 설정이 자동으로 적용되도록 할 수 있습니다.

---

### ✅ 주요 기능

|기능|설명|
|---|---|
|**표준화된 계정 생성**|사전 정의된 템플릿을 기반으로 AWS 계정을 자동 생성|
|**조직에 계정 등록**|생성된 계정은 AWS Organizations의 일원으로 자동 추가됨|
|**가드레일 자동 적용**|보안, 규정 준수, 운영 관련 가드레일이 자동 적용|
|**OU(Organizational Unit) 설정**|원하는 조직 단위(OU)에 계정 배정 가능|
|**네트워크 환경 선택**|계정의 VPC 구성 (CIDR 범위 등) 지정 가능|
|**AWS SSO 사용자 매핑**|사용자 액세스를 제어하는 권한 셋을 자동 연결 가능|

---

### ⚙️ 동작 방식

1. 관리자는 AWS Control Tower의 **Account Factory 콘솔 또는 Service Catalog 포털**을 통해 계정 생성 요청을 시작합니다.
    
2. 사용자는 다음을 지정할 수 있습니다:
    
    - 계정 이름 / 이메일
        
    - 할당할 OU
        
    - 네트워크 구성(CIDR 블록 등)
        
    - SSO 사용자 접근 권한
        
3. 생성된 계정은 자동으로:
    
    - AWS Organizations에 가입되고
        
    - Control Tower 가드레일이 적용되며
        
    - Landing zone 설정이 반영됩니다
        

---

### 🧑‍💼 사용 시나리오

- **기업에서 팀별 또는 프로젝트별 AWS 계정을 분리 관리**하고 싶을 때
    
- **DevOps 팀이 중앙 거버넌스 정책을 유지하면서 계정 생성 자동화**가 필요할 때
    
- **보안 및 규정 준수를 위반하지 않는 범위 내에서 자율성을 허용**하고자 할 때
    

---

### 🏛️ 구성도 요약

```
Control Tower
│
├── Landing Zone (기초 환경)
│
├── Account Factory
│    ├── 계정 프로비저닝 템플릿
│    ├── 네트워크 구성
│    └── SSO 권한 설정
│
└── 결과: 완전한 구성의 신규 AWS 계정 생성
```

---

### 📌 요약

|항목|설명|
|---|---|
|용도|표준화된 AWS 계정 생성 및 구성 자동화|
|기반 기술|AWS Service Catalog|
|주요 기능|OU 지정, 네트워크 구성, 가드레일 자동 적용, SSO 설정|
|대상|거버넌스 + 대규모 계정 관리가 필요한 기업 환경|