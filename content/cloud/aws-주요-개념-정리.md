---
title: AWS 주요 개념 정리
slug: "aws-주요-개념-정리"
category: cloud
tags: ["api-gateway", "aws", "cloudfront", "direct-connect", "dynamodb", "elasticache", "fargate", "iam", "s3"]
status: published
post_type: til
quality_score: 8.0
created_at: "2026-03-02T01:08:07.590526+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

- AWS Fargate
- Amazon CloudFront
  - 보안 강화 → S3 버킷에 대해 OAI(Origin Access Identity) 대신 OAC(Origin Access Control) 사용 권장
  - S3에 파일을 업로드하는 행위를 'ingress'라고 칭함
- AWS Global Accelerator
  - 
- Amazon DynamoDB: 사용자 비밀(Secret) 기반 인증이 아님
- Elastic IP vs Route53(TTL) vs Load Balancers
- Amazon ElastiCache
  - In-Memory DB
  - 세션 정보와 쿠키 저장에 사용
  - Amazon DynamoDB도 대안으로 활용 가능
- Elastic Network Interface: ENI
- ASG: AWS Auto Scaling
- ![](/media/posts/imported/aws/Pasted%20image%2020250703073938.png)
- ![](/media/posts/imported/aws/Pasted%20image%2020250703074042.png)
- 배치 그룹
  - 클러스터
  - 스프레드
  - 파티션: Hadoop
- Amazon DynamoDB
  - DAX Caching Layer
- Amazon API Gateway
- AWS Outposts
- **액세스 키 공유는 보안상 매우 위험**
- **키 수동 갱신은 운영 오버헤드**가 크고 자동화가 어렵고, 침해 가능성 존재
- ACM은 주로 **HTTPS, TLS 연결 인증** 용도
- Network Address Translation: NAT
- AWS Site-to-Site VPN : 온프레미스 환경과 AWS 간의 보안 연결
- VPC 피어링 : 같은 리전 내, 다른 리전 간, 다른 AWS 계정 간 가능
- Anycast : 네트워크 트래픽을 가장 가까운 노드로 전송하는 라우팅 방식
- Direct Connect : 온프레미스와 AWS 간에 DX(Direct Connect) Location을 통한 전용선으로 프라이빗 네트워크 연결 생성
- Data Sync : 온프레미스 스토리지, AWS 스토리지 서비스, 다른 클라우드 공급자 간 데이터 복사를 간소화·자동화하는 데이터 마이그레이션 서비스
- RDS Proxy
- Amazon Inspector
- Amazon GuardDuty
- S3 Glacier Deep Archive
- AWS IAM Identity Center