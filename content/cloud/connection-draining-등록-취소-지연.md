---
title: Connection Draining (등록 취소 지연)
slug: "connection-draining-등록-취소-지연"
category: cloud
tags: ["autoscaling", "aws", "connection-draining", "deregistration-delay", "ec2", "elb", "healthchecks", "load-balancer"]
status: published
post_type: til
quality_score: 8.0
created_at: "2026-03-02T01:08:06.541767+00:00"
---

![Connection Draining](/media/posts/imported/aws/Pasted%20image%2020250706192732.png)

- 인스턴스가 등록 취소되었거나 비정상 상태일 때, 진행 중인 요청이 완료될 수 있도록 일정 시간을 보장해 주는 기능
- Auto Scaling 등으로 인스턴스가 등록 취소된 경우 해당 인스턴스로 더 이상의 신규 요청을 보내지 않도록 하는 기능
- 인스턴스에 진행 중인 요청이 있을 때 설정해 둔 시간(Draining parameter) 동안 연결을 유지하여 요청이 완료되도록 하고, 해당 시간이 지나면 더 이상 그 인스턴스로 연결 요청을 보내지 않음
- 요청 지연 시간이 짧은 경우에는 짧은 값으로 설정하는 것이 좋음
  - 예: 요청 시간이 1초 이하일 때 Draining parameter를 약 30초로 설정
- 업로드나 장시간 지속되는 요청이 있는 경우에는 상대적으로 높은 값으로 설정하면 됨
- 그렇다면 EC2 인스턴스가 바로 사라지지 않겠지?