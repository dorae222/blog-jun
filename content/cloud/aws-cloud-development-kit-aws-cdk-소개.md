---
title: AWS Cloud Development Kit (AWS CDK) 소개
slug: "aws-cloud-development-kit-aws-cdk-소개"
category: cloud
tags: ["aws", "aws-cdk", "cloudformation", "devops", "iac", "infrastructure-as-code", "s3", "terraform", "typescript"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.493300+00:00"
---

**AWS Cloud Development Kit (AWS CDK)**는 AWS 리소스를 **프로그래밍 언어를 사용하여 코드로 정의하고 관리**할 수 있게 해주는 오픈소스 소프트웨어 개발 프레임워크입니다. 인프라를 코드로 다루는 **Infrastructure as Code (IaC)** 도구 중 하나이며, AWS의 CloudFormation을 기반으로 동작합니다.

---

## 🔧 핵심 개념

### 1. **Infrastructure as Code (IaC)**

AWS CDK를 사용하면 AWS 리소스를 **YAML이나 JSON이 아닌 TypeScript, Python, Java, C# 같은 일반적인 프로그래밍 언어로 정의**할 수 있습니다. 이를 통해 조건문, 반복문, 모듈화 등 프로그래밍의 장점을 인프라 설계에 그대로 적용할 수 있습니다.

### 2. **Construct**

CDK에서 인프라 구성 요소는 **Construct**라는 객체로 표현됩니다. 예:

```ts
new s3.Bucket(this, 'MyBucket');
```

이처럼 `Bucket`은 하나의 Construct이며, 여러 Construct를 조합해 더 복잡한 인프라를 구성할 수 있습니다.

### 3. **Stack**

Stack은 하나 이상의 Construct를 포함하는 배포 단위로, 최종적으로는 AWS CloudFormation Stack으로 변환되어 배포됩니다.

### 4. **App**

CDK 애플리케이션 전체를 구성하는 루트 객체로, 여러 Stack을 포함할 수 있습니다.

---

## 🚀 주요 장점

|기능|설명|
|---|---|
|✅ 친숙한 언어 사용|TypeScript, Python, Java, C# 등 기존 애플리케이션 개발에 사용하던 언어로 인프라 정의|
|✅ 추상화 및 재사용성|Construct를 모듈화해 여러 프로젝트에서 재사용 가능|
|✅ CloudFormation 기반|CDK가 생성한 코드는 CloudFormation으로 변환되어 안전하고 일관된 배포 가능|
|✅ IDE 지원|코드 자동완성, 타입 검사, 디버깅 등 개발자 친화적인 도구 사용 가능|

---

## 🛠️ 예시 (TypeScript)

```ts
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';

class MyStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    new s3.Bucket(this, 'MyBucket', {
      versioned: true
    });
  }
}

const app = new cdk.App();
new MyStack(app, 'MyStack');
```

이 코드는 버전 관리가 켜진 S3 버킷을 생성합니다.

---

## 📦 AWS CDK와 Terraform, CloudFormation 비교

|기능|CDK|Terraform|CloudFormation|
|---|---|---|---|
|언어 지원|다수의 언어 (TS, Python 등)|HCL|JSON/YAML|
|추상화 수준|높음|중간|낮음|
|상태 관리|CloudFormation에 위임|자체 상태 파일|CloudFormation 관리|
|학습 곡선|프로그래머에게 익숙함|별도 언어 학습 필요|비교적 단순하지만 덜 유연|

---

## 📚 참고 리소스

- [AWS CDK 공식 사이트](https://aws.amazon.com/cdk/)
    
- [GitHub 리포지토리](https://github.com/aws/aws-cdk)
    
- [AWS CDK Workshop](https://cdkworkshop.com/)