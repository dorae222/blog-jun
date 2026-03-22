---
title: AD Connector
slug: "ad-connector"
category: cloud
tags: ["active-directory", "ad-connector", "amazon-rds", "amazon-workspaces", "aws", "aws-directory-service", "aws-sso", "hybrid-cloud", "identity-management"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.219264+00:00"
---

**AD Connector**는  
👉 **AWS 디렉터리 서비스(AWS Directory Service)** 가 제공하는 **프록시(Proxy) 서비스**로,  
온프레미스(사내) 환경에 이미 구축된 **Microsoft Active Directory(AD)** 를 **AWS 클라우드 리소스와 직접 연동**할 수 있도록 해줍니다.

---

### ✨ **AD Connector의 역할**

✅ **클라우드에 AD를 새로 만들지 않아도 됨**

- 기존 온프레미스 Active Directory를 그대로 사용하면서  
    AWS의 서비스(Amazon WorkSpaces, Amazon RDS, AWS SSO 등)에서 **AD 계정을 사용한 인증**이 가능.
    

✅ **프록시 방식**

- 클라우드에 실제 사용자 계정 데이터를 복제하지 않음.
    
- AWS 리소스가 사용자 인증이 필요할 때, AD Connector가 **온프레미스 AD에 인증 요청을 전달**하고 결과를 받아서 처리.
    

✅ **운영 편의성**

- 별도의 동기화나 복잡한 구성 없이, 몇 분 만에 기존 AD를 AWS 서비스와 연동 가능.
    

---

### 🏗️ **사용 시나리오 예시**

- **Amazon WorkSpaces**에서 온프레미스 AD 계정으로 로그인해야 할 때
    
- **Amazon RDS for SQL Server**에서 Windows 인증을 사용해야 할 때
    
- AWS Management Console 접근을 온프레미스 AD 계정으로 통합 관리하고 싶을 때
    

---

### 🔒 **보안 및 특징**

- **데이터 복제 없음** → 보안 정책 그대로 유지
    
- **온프레미스 AD 정책**(비밀번호 정책, 그룹 정책 등)을 그대로 적용 가능
    
- AWS에서 관리형으로 제공되므로 설치·패치·유지보수 부담이 적음
    

---

✅ **정리하면:**  
**AD Connector**는 **AWS 리소스가 온프레미스 Active Directory를 그대로 사용하도록 해주는 관리형 프록시 서비스**입니다.  
기존 AD 환경을 그대로 살리면서 클라우드 자원까지 통합 관리하고 싶을 때 유용합니다.