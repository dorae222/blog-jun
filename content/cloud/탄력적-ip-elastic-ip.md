---
title: 탄력적 IP (Elastic IP)
slug: "탄력적-ip-elastic-ip"
category: cloud
tags: ["aws", "billing", "ec2", "elastic-ip", "eni", "networking", "private-ip", "public-ip"]
status: published
post_type: til
quality_score: 7.0
created_at: "2026-03-02T01:08:06.741401+00:00"
---

> **NOTE:** Public IP vs. Private IP
> 
> - 퍼블릭 IP : 인터넷 연결에 사용하는 IP
> - 프라이빗 IP : 회사나 집의 내부에서만 사용하는 IP 직접적으로 인터넷 연결이 안되며 인터넷 게이트웨이를 통해야 함

- 인스턴스 생성시 자동으로 할당 받은 Public IP는 인스턴스를 재시작하면 다른 IP로 재할당되어 Public IP 주소가 변경됩니다.
- Elastic IP는 인터넷에 연결 가능한 고정적(정적) 퍼블릭 IP 주소입니다.
- EC2 인스턴스의 ENI에 탄력적 IP 주소를 연결하면 인스턴스를 재시작해도 동일한 Public IP 주소로 접속할 수 있습니다.
- Elastic IP는 생성한 리전 내에서만 사용 가능하며 다른 리전으로 이전할 수 없습니다.
- 실행 중인 인스턴스와 연결되지 않은 탄력적 IP 주소에 대해서는 소액의 시간당 요금이 부과됩니다.