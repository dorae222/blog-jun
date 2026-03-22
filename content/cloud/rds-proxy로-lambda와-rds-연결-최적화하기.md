---
title: RDS Proxy로 Lambda와 RDS 연결 최적화하기
slug: "rds-proxy로-lambda와-rds-연결-최적화하기"
category: cloud
tags: ["aws", "aws-iam", "connection-pooling", "database", "high-availability", "lambda", "rds", "rds-proxy", "secrets-manager"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:07.327275+00:00"
---

- RDS Proxy는 Connection Pooling(연결 풀)을 활용한다.
    - Connection Pooling을 통해 DB 연결을 공유하여 **DB 연결을 재사용(re-use)** 할 수 있게 한다.
    - 이를 통해 DB 서버의 부하를 낮추고 애플리케이션 성능을 개선할 수 있다.
- 클라이언트(애플리케이션)는 RDS Proxy의 엔드포인트를 통해 연결한다.
- 여러 애플리케이션 연결 간에 데이터베이스 연결을 공유할 수 있으므로 **데이터베이스 리소스를 효율적으로 사용**할 수 있다.
- DB 장애 조치 시간 감소
    - 애플리케이션 연결을 유지한 채로 예비 DB 인스턴스로 자동 연결된다.
- 보안 개선
    - 필요에 따라 DB에 AWS IAM 인증을 적용하고, AWS Secrets Manager에 자격 증명을 안전하게 저장할 수 있다.
- DB 성능 유지
    - 데이터베이스 연결 풀을 설정해 매번 새 DB 연결을 여는 데 필요한 메모리 및 CPU 오버헤드 없이 풀에서 연결을 재사용한다.
    - 연결 요청이 지정된 한도를 초과하면 애플리케이션 연결을 거부해 과도한 부하를 줄인다. (DB에서 열린 연결 수를 제어하는 방식)

1. **연결 풀링 (Connection Pooling)**:

   * Lambda 함수는 매 호출마다 새로운 DB 연결을 생성 → RDS 연결 수 초과 발생 가능
   * RDS Proxy는 연결을 **재사용**하여 연결 수를 크게 줄인다.

2. **자동 장애 복구**:

   * DB 인스턴스 장애 시 프록시가 자동으로 재연결을 관리한다.
   * 애플리케이션에서 별도의 재시도 및 복구 로직을 구현할 필요가 줄어든다.

3. **운영 오버헤드 최소화**:

   * AWS 관리형 서비스이므로 별도 유지보수가 거의 필요 없다.
   * **RDS와 Lambda 연결을 위한 AWS 권장 아키텍처**에 부합한다.

4. **비용 효율적**:

   * DB를 확장하거나 마이그레이션하지 않고도 성능·안정성 문제를 해결할 수 있다.
   * 사용량 기반 과금 모델로 비용을 관리할 수 있다.

📌 즉, **애플리케이션 코드 최소 수정으로 성능과 안정성 확보**가 가능하다.