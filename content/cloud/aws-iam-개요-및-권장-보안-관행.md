---
title: AWS IAM 개요 및 권장 보안 관행
slug: "aws-iam-개요-및-권장-보안-관행"
category: cloud
tags: ["access-control", "aws", "iam", "identity-and-access-management", "mfa", "policies", "roles", "security", "users"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:06.987914+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
aliases:
  - IAM
---

> **Note:**
> 
> - AWS 계정 및 권한 관리 서비스
> - AWS 서비스와 리소스에 대한 액세스 관리
> - 사용자, 그룹, 역할, 정책으로 구성
> - 리전에 속하는 서비스가 아닌 글로벌 서비스
> - 계정 보안 강화를 위한 권장 사항
>     - 루트 계정은 최초 사용자 계정 생성 이후 가능하면 사용하지 않을 것
>     - 사용자 계정(IAM 사용자)으로 서비스를 사용하고, 사용자에게는 필요한 최소 권한만 부여(최소 권한 원칙)
>     - 루트 계정과 개별 사용자 계정에 강력한 암호 정책과 다단계 인증(MFA) 적용
>     - 사용자의 암호 복잡성 요구사항과 교체 주기 정의

### IAM 자격 증명
- 사용자(User): 개인 또는 애플리케이션을 위한 특정 권한을 가진 ID
- 그룹(Group):
    - 개발팀, 운영팀 등의 사용자 집합
    - AWS 서비스 요청을 생성하기 위한 일련의 권한을 정의하는 IAM 엔터티
- 역할(Role): 특정 개인에 속하지 않는 특정 권한을 가진 ID

### IAM 사용자
- 단일 개인 또는 애플리케이션에 대해 특정 권한을 갖는 AWS 계정 내 자격 증명
- 보통 한 사람과 연관(한 명의 실제 사용자)
- 암호 또는 액세스 키 같은 장기 자격 증명을 통해 접근

> **information:** Dump
> - IAM 사용자는 반드시 사용자 그룹에 속할 필요는 없음
> - IAM 정책은 사용자에게 직접 연결될 수 있음
> - IAM 사용자는 여러 사용자 그룹에 속할 수 있음
> - IAM 사용자 그룹은 다른 사용자 그룹의 멤버가 될 수 없음
> - IAM 사용자는 자신만의 자격 증명을 통해 AWS 서비스에 액세스함
>     - 사용자 이름
>     - 비밀번호 또는 액세스 키

---
### IAM 정책 개요
- AWS 리소스에 대한 액세스 권한을 정의한 문서
- 사용자, 그룹, 역할에 정책을 연결하여 사용
- User Data: ==JSON== 문서 형식으로 이루어짐
- 정책이 명시적으로 허용하지 않으면 기본적으로 모든 요청은 거부(Deny)

##### IAM 정책 JSON 문서 구조
- Effect(효과): Allow 또는 Deny로 액세스 허용/거부 지정
- Action(조치): 정책이 허용하거나 거부하는 작업 목록
- Resource(리소스): 작업이 적용되는 리소스
- Condition(조건): 정책이 적용되는 상세 조건(선택사항)

> **information:** Dump
> - IAM 정책의 문장은 SID, Effect, Principal, Action, Resource, Condition으로 구성됨
> - 버전(Version)은 IAM 정책 자체의 일부이지, 문장의 일부가 아님


#### IAM Security Tools
- IAM Credentials Report (계정 수준)
    - 계정의 모든 사용자와 각 사용자 자격 증명의 상태를 나열한 리포트
- IAM Access Advisor (사용자 수준)
    - Access Advisor는 사용자에게 부여된 서비스 권한과 해당 서비스들이 마지막으로 사용된 시점을 보여줌
    - 이 정보를 사용해 정책을 수정하면 최소 권한 원칙을 적용하는 데 도움됨

---

- AWS IAM Identity Center
- Amazon Cognito
- AWS RAM
- Multi Factor Authentication
