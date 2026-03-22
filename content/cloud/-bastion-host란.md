---
title: "🔐 Bastion Host란?"
slug: "-bastion-host란"
category: cloud
tags: ["aws", "bastion-host", "cloud-security", "ec2", "network-security", "rdp", "session-manager", "ssh"]
status: published
post_type: til
quality_score: 8.0
created_at: "2026-03-02T01:08:06.276194+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - 배스천 호스트
---
![](/media/posts/imported/aws/Pasted%20image%2020250708085038.png)
### 🔐 Bastion Host란?

- 외부에서 내부 네트워크에 접속할 수 있도록 하는 보안 게이트웨이 역할을 하는 서버입니다.

- 보통 퍼블릭 서브넷에 배치되며, 프라이빗 서브넷의 EC2 인스턴스에 SSH 또는 RDP로 접근할 수 있게 합니다.

- 네트워크 보안을 위해 관리자는 내부 리소스에 직접 접속하지 않고 먼저 Bastion Host를 통해 우회 접속하도록 구성합니다.

---

### 📌 예시 문장

- ✅ _"All administrative access to private EC2 instances is done through a **bastion host**."_

    - "모든 관리 접근은 베스천 호스트를 통해 이루어집니다."

---

### 💡 유의사항

- 보안을 위해 IP 제한, MFA 적용, 세션 로그 기록, SSH 키 관리 등을 철저히 해야 합니다.

- 대안으로는 **AWS Systems Manager Session Manager**를 사용할 수 있습니다. 이는 Bastion Host 없이도 안전한 접근을 가능하게 합니다.