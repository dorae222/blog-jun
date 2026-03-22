---
title: Active Directory(액티브 디렉터리) 개요
slug: "active-directory액티브-디렉터리-개요"
category: cloud
tags: ["active-directory", "ad-connector", "authentication", "authorization", "aws", "domain-controller", "group-policy", "identity-management"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.688095+00:00"
---

**Active Directory(액티브 디렉터리)**는
👉 **Microsoft가 개발한 디렉터리 서비스(Directory Service)**로,
기업이나 조직에서 **사용자·컴퓨터·네트워크 리소스를 중앙에서 관리하고 인증**하기 위해 사용됩니다.

- AD Connector

---

### ✨ **핵심 개념**

✅ **디렉터리 서비스란?**

- 네트워크 상의 사용자, 그룹, 컴퓨터, 프린터, 서버 등 **리소스와 그 속성 정보**를 구조적으로 저장하고 관리하는 서비스.
    

✅ **Active Directory의 역할**

- 사용자가 네트워크에 로그인할 때 **계정 인증(Authentication)**
    
- 사용자와 그룹별로 **권한(Authorization)** 부여
    
- 조직 내 수많은 계정과 자원을 **중앙에서 통합 관리**
    
- 도메인 기반의 네트워크 관리(예: `company.local`)
    
---

### 🏢 **구성 요소 예시**

- **도메인 컨트롤러(Domain Controller)**  
    Active Directory 데이터베이스를 저장하고 인증을 담당하는 서버.
    
- **사용자(User), 그룹(Group)**  
    계정과 권한을 정의하여 접근 제어를 쉽게 관리.
    
- **OU(Organizational Unit, 조직 단위)**  
    부서나 지역 단위로 리소스를 논리적으로 묶어 관리.
    
- **그룹 정책(Group Policy)**  
    사용자나 컴퓨터에 대해 **보안 설정, 데스크톱 환경, 소프트웨어 배포** 등을 일괄 적용.
    
---

### 🔒 **사용 이유와 장점**

✅ **중앙 집중식 관리** – 사용자, 장비, 권한을 한곳에서 관리  
✅ **강력한 보안** – 도메인 기반 인증과 세밀한 권한 제어  
✅ **확장성** – 수백, 수천 명의 계정도 효율적으로 운영  
✅ **다른 서비스와 연동** – AWS Managed Microsoft AD나 SSO 등과 쉽게 통합

---

💡 **정리하면:**  
**Active Directory**는 기업 네트워크의 사용자·리소스 관리, 인증 및 권한 부여를 중앙에서 처리하는 **Microsoft의 디렉터리 서비스**입니다.
   
AD는 기업 내 **통합 인증(SSO, Single Sign-On)** 및 **권한 정책 관리**를 위한 핵심 인프라입니다.