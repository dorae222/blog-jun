---
title: S3 Glacier Vault Lock 정리
slug: "s3-glacier-vault-lock-정리"
category: cloud
tags: ["aws", "compliance", "data-protection", "data-retention", "glacier-vault-lock", "s3-glacier", "vault-lock", "worm-storage"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:07.498564+00:00"
---

### 📦 **S3 Glacier란?**

- **S3 Glacier**는 데이터를 장기간 저비용으로 보관하기 위한 AWS 스토리지 서비스입니다.  
  (예: 규정상 7년 보관해야 하는 로그나 백업 데이터 저장에 사용)

---

### 🔒 **그럼 Vault Lock이란?**

**Vault Lock**은 S3 Glacier에 있는 **Vault(보관소)**에 대해 **변경할 수 없는 WORM(Write Once Read Many) 정책을 적용**하는 기능입니다.

쉽게 말해:

> ✅ “이 보관소에 있는 데이터는 앞으로 절대 삭제·변경할 수 없도록 잠가버린다!”

라는 규칙을 AWS 레벨에서 강제로 적용하는 기능입니다.

---

### ✨ **어떻게 동작하나?**

1. **Vault Lock 정책(policy) 작성**
    
    - 예: “모든 데이터는 최소 7년간 삭제할 수 없다.”
        
2. **Vault Lock으로 정책을 잠금(Lock)**
    
    - 한 번 Lock하면 관리자라도 **해당 규칙을 수정하거나 우회할 수 없습니다.**
        
3. **이후에는 정책을 강제 적용**
    
    - 데이터를 실수로 지우거나 내부에서 규정 위반을 시도해도 삭제·수정이 불가능합니다.
        
---

### 📑 **왜 필요한가?**

- **규제/컴플라이언스 준수:**  
  금융·의료 등 분야에서는 “데이터를 최소 X년 동안 변경·삭제하면 안 된다”는 규제가 있습니다. Vault Lock은 AWS 수준에서 이를 강제하므로 감사 시 유리합니다.
    
- **데이터 보호:**  
  내부 실수나 악의적인 삭제로부터 데이터를 보호합니다.
    
---

### 📌 **비유로 이해하기**

🗄️ **일반 Vault:**  
열쇠를 가진 사람은 언제든 데이터를 꺼내거나 삭제할 수 있습니다.

🔐 **Vault Lock:**  
Vault에 데이터를 넣고 **AWS에게 열쇠를 영구적으로 맡겨서** 아무도 더 이상 그 안의 파일을 삭제할 수 없게 만드는 방식입니다.

---

### ✅ **정리**

|기능|설명|
|---|---|
|**Vault Lock**|S3 Glacier Vault에 불변 정책을 적용해 WORM 스토리지로 만듦|
|**장점**|규제 준수, 데이터 보호, 내부 실수 방지|
|**주의**|한 번 Lock하면 되돌릴 수 없음 (정책 수정 불가)|