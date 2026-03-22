---
title: AWS Transfer Family
slug: "aws-transfer-family"
category: cloud
tags: ["amazon-efs", "amazon-s3", "aws", "aws-transfer-family", "ftp", "ftps", "iam", "kms", "sftp"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.546214+00:00"
---

**AWS Transfer Family**는
✅ **SFTP(SSH File Transfer Protocol)**,
✅ **FTPS(File Transfer Protocol over SSL)**,
✅ **FTP(File Transfer Protocol)**
와 같은 **표준 파일 전송 프로토콜을 사용하여 Amazon S3 또는 Amazon EFS로 데이터를 전송할 수 있도록 지원하는 완전관리형 서비스**입니다.

---

### ✨ **주요 특징**

✅ **표준 프로토콜 지원**

- 별도의 애플리케이션 변경 없이 기존 SFTP, FTPS, FTP 클라이언트로 S3 또는 EFS에 접근할 수 있습니다.


✅ **완전관리형**

- 전용 파일 전송 서버를 직접 설치, 운영, 패치할 필요가 없습니다.

- AWS가 서버 운영, 가용성, 보안 패치를 모두 관리합니다.


✅ **확장성과 내구성**

- Amazon S3나 EFS를 스토리지로 사용하므로 고내구성과 확장성을 자동으로 확보할 수 있습니다.


✅ **보안과 규정 준수**

- AWS Identity and Access Management(IAM), AWS Key Management Service(KMS), VPC 엔드포인트, AWS CloudTrail 등을 활용해 보안과 감사 추적을 손쉽게 적용할 수 있습니다.


✅ **고객 인증 옵션**

- 서비스 자체의 사용자 관리뿐 아니라 기존 **Active Directory**, **LDAP**, **커스텀 인증** 등과 연동할 수 있습니다.

---

### 💡 **언제 사용하나요?**

- 기존에 SFTP/FTPS/FTP 기반의 파일 전송 워크플로를 사용 중이며, **클라우드 마이그레이션이나 클라우드 기반 스토리지(S3, EFS)를 그대로 이용하고 싶을 때**

- 별도의 전용 서버 관리 부담을 줄이고, **안정적이고 안전한 데이터 전송 채널**이 필요할 때

---

**정리하면:**
👉 **AWS Transfer Family = SFTP/FTPS/FTP 프로토콜로 S3/EFS에 안전하게 파일을 전송·수신할 수 있게 해주는 AWS의 완전관리형 서비스**입니다.