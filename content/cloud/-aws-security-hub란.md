---
title: "🛡️ AWS Security Hub란?"
slug: "-aws-security-hub란"
category: cloud
tags: ["aws", "aws-security-hub", "cloud-security", "compliance", "devsecops", "eventbridge", "guardduty", "inspector", "macie", "security"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.366524+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - Security Hub
---
## 🛡️ AWS Security Hub란?

**AWS Security Hub**는 **AWS 계정과 서비스 전반의 보안 상태를 중앙에서 확인하고 관리할 수 있도록 도와주는 보안 관제 서비스**입니다. 다양한 AWS 서비스 및 타사 보안 도구와 통합되어, 보안 관련 **경고(Alert)와 규정 준수 상태(Compliance)**를 통합하고 시각화할 수 있습니다.

---

### ✅ 주요 기능

#### 1. **보안 경고(Findings) 통합**

- 여러 **AWS 서비스 (예: GuardDuty, Inspector, Macie, Firewall Manager)** 및 **타사 솔루션 (예: CrowdStrike, Palo Alto 등)**에서 생성된 보안 경고를 **중앙에서 수집하고 통합**합니다.

- 이 경고는 **표준화된 형식 (AWS Security Finding Format, ASFF)** 으로 제공되어 분석이 쉽습니다.


#### 2. **보안 기준(Baseline) 및 규정 준수 검사**

- 다음과 같은 **보안 기준에 따른 자동 점검을 수행**합니다:
    
    - **CIS AWS Foundations Benchmark**
    
    - **AWS Foundational Security Best Practices**
    
    - **PCI DSS**, **NIST** 등
    
- 점검 결과는 ‘통과(Passed)’ 또는 ‘실패(Failed)’ 형식으로 리포트되며, **규정 준수 상태를 빠르게 파악**할 수 있습니다.
    

#### 3. **자동화된 대응 및 통합**

- **Amazon EventBridge와 연동**하여 특정 경고에 따라 **자동 조치**를 수행할 수 있습니다:
    
    - 예: 특정 조건의 경고 발생 시 Lambda 함수 실행, SNS 알림 전송 등
        
- **AWS Systems Manager Automation**과 연계하여 **자동 보안 수정 워크플로우**를 구성할 수 있습니다.
    

#### 4. **대시보드 제공**

- 시각화된 **보안 상태 요약 대시보드**를 제공합니다.
    
- 전체 AWS 리전 및 계정에 대한 **보안 리스크 현황을 한눈에 파악**할 수 있습니다.
    

---

### 🔄 통합 가능한 주요 AWS 서비스

|서비스|설명|
|---|---|
|**Amazon GuardDuty**|위협 탐지 서비스 (악성 활동, 비정상 API 호출 등)|
|**Amazon Inspector**|EC2 및 컨테이너 이미지의 취약점 평가|
|**Amazon Macie**|민감한 데이터(S3 내 개인정보 등) 자동 식별 및 보호|
|**AWS IAM Access Analyzer**|IAM 정책 분석 및 리소스 공개 여부 탐지|
|**AWS Firewall Manager**|조직 전체의 보안 정책 중앙 관리|

---

### 🧑‍💼 사용 사례 예시

- **보안 운영팀**이 여러 계정/리전에서 발생하는 보안 경고를 한 곳에서 확인
    
- **규정 준수 담당자**가 PCI DSS 등 규정 요구사항을 충족하는지 주기적으로 평가
    
- **DevSecOps** 파이프라인에서 자동화된 대응 실행 (예: S3 버킷 퍼블릭 공개 시 자동 차단)
    

---

### 💰 과금

- **Security Hub 자체 사용 요금**
    
- **통합된 다른 서비스 (예: GuardDuty, Inspector)**에 대한 별도 요금 발생
    
- **무료 평가판 제공 (30일)**
    

---

## 📝 요약

|항목|설명|
|---|---|
|핵심 기능|AWS 보안 이벤트 통합, 규정 준수 검사, 자동화된 대응|
|통합 가능|GuardDuty, Inspector, Macie, IAM Access Analyzer 등|
|시각화 제공|보안 상태 대시보드|
|규정 준수 지원|CIS, PCI DSS, NIST 등 보안 기준 자동 검사|
|적합 대상|보안 운영팀, 규정 준수 담당자, DevSecOps 팀|
