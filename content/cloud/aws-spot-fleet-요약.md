---
title: AWS Spot Fleet 요약
slug: "aws-spot-fleet-요약"
category: cloud
tags: ["availability", "aws", "capacity-optimized", "cost-optimization", "diversified", "ec2", "on-demand", "spot-fleet", "spot-instances"]
status: published
post_type: til
quality_score: 8.0
created_at: "2026-03-02T01:08:07.905574+00:00"
---

- Fleet: 무리, 집합
- Spot 인스턴스의 집합 + (optional) On-Demand 인스턴스
- Spot Fleet will try to meet the target capacity with price constraints
	- Define possible launch pools: EC2 Instance, OS, Availability Zone
	- Can have multiple lauch pools, so that the fleet can choose
	- Spot Fleet stops launching instances when reaching capacity or max cost
- Stratiges to allocate Spot Instances
	1. ==Lowest Price==: from the pool with the lowest price
	   (cost optimization, short workload)
	2. ==Diversified==: distributed across all pod
	   (great for availability, long workload)
	3. ==Capacity Optimized==: pool with the optimal capacity for the number of instances
	4. ==Price Capacity Optimized==(**recommended**): pools with highest capacity available, the the select the pool with the lowest price
	   (best choice for most workloads)
- Spot Fleet는 가격 제약 내에서 target capacity를 충족하도록 설계되어 있습니다. 가능한 launch pools(예: EC2 Instance 유형, OS, Availability Zone)를 정의하고 여러 launch pools를 지정해 Fleet가 선택하도록 할 수 있습니다. 목표 용량에 도달하거나 max cost에 도달하면 Spot Fleet는 인스턴스 생성(launch)을 중지합니다.
- Spot 인스턴스 할당 전략:
	1. ==Lowest Price==: 가장 낮은 가격의 pool에서 우선 할당 (비용 최적화, 짧은 워크로드)
	2. ==Diversified==: 모든 pool에 분산 배치 (높은 가용성에 유리, 장기 워크로드)
	3. ==Capacity Optimized==: 요구 인스턴스 수에 대해 용량이 최적인 pool 선택
	4. ==Price Capacity Optimized==(**recommended**): 가용 용량이 높은 pool을 우선 고려한 뒤, 그 중에서 가격이 가장 낮은 pool을 선택 (대부분의 워크로드에 권장)
- Spot Fleet는 자동으로 가장 낮은 가격의 Spot 인스턴스를 요청할 수 있게 해줍니다.