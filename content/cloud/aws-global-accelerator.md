---
title: AWS Global Accelerator
slug: "aws-global-accelerator"
category: cloud
tags: ["anycast", "aws", "aws-global-accelerator", "cloud-architecture", "disaster-recovery", "load-balancing", "networking", "performance", "saa"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.832441+00:00"
---

## 1. 개요

- **AWS Global Accelerator**는 전 세계 AWS 엣지 로케이션(Edge Location)을 활용해 애플리케이션의 가용성 및 성능을 향상시키는 네트워크 서비스입니다.

- 사용자는 고정된 글로벌 Anycast IP 주소로 요청을 전송하면, AWS 네트워크 내에서 가장 최적의 엔드포인트(리전·AZ 내의 ALB/NLB/EC2 등)로 라우팅됩니다.

- 핵심 목적은 글로벌 사용자 분산 처리, 재해 복구 시 빠른 장애 전환, 그리고 지연 시간 최소화입니다.

## 2. 주요 구성 요소

1. **Accelerator**
    
    - 2개의 고가용성 Anycast IPv4 주소 제공
    
    - 퍼블릭 및 프라이빗(기가바이트 전용) Accelerator 생성 가능
    
2. **Listener**
    
    - 클라이언트 요청을 수신하는 포트/프로토콜(UDP/TCP) 설정
    
3. **Endpoint Group**
    
    - 리전별 엔드포인트 집합
    
    - 리전당 하나 이상의 엔드포인트(로드 밸런서·EC2·Elastic IP 등) 지정
    
    - **Traffic Dial**: 리전별 트래픽 비율 조정(0–100%)
    
4. **Endpoint**
    
    - ALB, NLB, EC2 인스턴스, Elastic IP 주소 지원
    
    - 가용성 및 성능 향상을 위해 다수의 AZ에 중복 구성 권장
    

## 3. 동작 원리

1. 사용자가 Anycast IP로 접속합니다.

2. DNS가 아닌 네트워크 라우팅(BGP Anycast)을 통해 가장 가까운 AWS 엣지 로케이션으로 접속합니다.

3. AWS 글로벌 네트워크(Backbone)를 통해 최적 경로로 리전의 Endpoint Group으로 전달됩니다.

4. 정기적 헬스 체크(HTTP/TCP/HTTPS) 결과에 따라 비정상 인스턴스를 제외합니다.

5. 장애 발생 시 동일 리전 내의 다른 AZ 또는 다른 리전의 엔드포인트로 자동으로 재연결됩니다.

## 4. 특징 및 이점

- **고정 IP 제공**: 애플리케이션 IP가 변경되지 않아 클라이언트 화이트리스트 관리를 용이하게 합니다.

- **지연시간 최소화**: AWS 글로벌 백본망을 이용해 인터넷 환경 변동성의 영향을 줄입니다.

- **자동 장애 전환**: 헬스 체크 기반으로 빠른 장애 복구가 가능합니다.

- **트래픽 제어**: Traffic Dial로 리전별 트래픽 분산 비율을 제어할 수 있어 A/B 테스트나 단계적 롤아웃에 유용합니다.

- **운영 단순화**: 복잡한 DNS 기반 분산 대신 단일 Anycast IP를 활용할 수 있습니다.

## 5. 사용 사례

- **글로벌 웹 애플리케이션**: 사용자가 지리적으로 분산되어 있을 때 지연 시간을 최적화합니다.

- **재해 복구(Disaster Recovery)**: 리전 장애 시 자동 트래픽 전환으로 비즈니스 연속성을 보장합니다.

- **A/B 테스트 & Canary Deploy**: 특정 리전으로 트래픽 일부만 보내 단계적 릴리즈를 수행합니다.

- **게임 서버 & 미디어 스트리밍**: 실시간 성능이 요구되거나 지연 시간에 민감한 서비스에 적합합니다.

## 6. AWS SAA 시험 대비 포인트

1. **Anycast IP vs. CloudFront**
    
    - Global Accelerator: L4 네트워크 레벨(최적 경로·정적 IP)
        
    - CloudFront: CDN(캐싱) 서비스, L7(HTTP/HTTPS)에서 캐싱 및 보안 기능 강화
        
2. **엔드포인트 종류** 숙지
    
    - ALB/NLB/EC2/Elastic IP
        
3. **헬스 체크 옵션**
    
    - 프로토콜(TCP/HTTP/HTTPS) 및 포트 지정
    
    - 헬스 체크 간격 및 재시도 설정
        
4. **Traffic Dial** 활용법
    
    - 특정 리전으로의 트래픽 비율을 조정하는 실습 필요
        
5. **보안 통합**
    
    - AWS WAF, Shield Advanced와 연동하여 DDoS 보호 가능
    

## 7. 비용 요약

- **Accelerator 시간당 요금**: 생성된 Accelerator 수 × 시간

- **Data Transfer**: 엣지 로케이션 → Endpoint로 전달되는 아웃바운드 바이트별 과금

- **헬스 체크 비용**: 헬스 체크 요청 수에 따른 추가 소액 과금