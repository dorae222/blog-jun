---
title: "인프라 as Code (IaC): Terraform 중심 실전 가이드"
slug: "infrastructure-as-code"
category: cloud
tags: ["devops", "terraform", "iac", "infrastructure"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# 인프라 as Code (IaC): Terraform 중심 실전 가이드

## 1. IaC란 무엇인가

**Infrastructure as Code(IaC)**는 인프라를 수동으로 관리하는 대신, **코드로 선언하고 자동화**하는 접근 방식이다.

전통적으로 서버를 구성할 때는 관리자가 콘솔에 접속하여 수동으로 설정했다. 이 방식은 다음과 같은 문제가 있다:

```
수동 관리의 문제점:

개발자 A가 서버 구성  ──▶  "내 서버에서는 잘 되는데?"
    │
    ├── 어떤 패키지를 설치했는지 기억 안 남
    ├── 설정 파일을 어디서 수정했는지 모름
    ├── 같은 환경을 다시 만들 수 없음
    └── 다른 사람이 인수인계 받기 어려움

        ↓  IaC 도입  ↓

코드로 인프라 정의  ──▶  "코드가 곧 문서이자 실행 가능한 인프라"
    │
    ├── Git으로 변경 이력 추적
    ├── PR 리뷰로 인프라 변경 검증
    ├── 동일한 환경을 언제든 재생성
    └── 누구나 코드를 읽고 이해 가능
```

---

## 2. IaC의 장점

### 버전 관리 (Version Control)

```
commit abc1234 - "VPC 서브넷 추가"
commit def5678 - "보안그룹 규칙 수정"
commit ghi9012 - "오토스케일링 설정 변경"
    │
    └── 누가, 언제, 왜 인프라를 변경했는지 추적 가능
        문제 발생 시 이전 커밋으로 롤백 가능
```

### 재현성 (Reproducibility)

```
동일한 Terraform 코드로:

Production 환경  ─┐
Staging 환경     ─┤── 동일한 인프라 구조
Development 환경 ─┤   (변수만 다름)
DR 환경          ─┘
```

### 자동화 (Automation)

```
PR 머지 → CI/CD 파이프라인 → terraform plan → 승인 → terraform apply
    │
    └── 사람의 개입 최소화, 실수 방지, 속도 향상
```

### 추가 장점

| 장점 | 설명 |
|------|------|
| **협업** | 코드 리뷰를 통한 인프라 변경 검토 |
| **테스트** | 인프라 코드에 대한 자동화 테스트 가능 |
| **문서화** | 코드 자체가 인프라의 현재 상태를 문서화 |
| **비용 최적화** | 리소스를 코드로 관리하여 불필요한 리소스 파악 |
| **컴플라이언스** | 정책을 코드로 강제 (Policy as Code) |

---

## 3. 선언적 vs 명령적 접근

IaC 도구는 크게 두 가지 접근 방식으로 나뉜다:

### 선언적 (Declarative)

**"무엇(What)"**을 원하는지 정의한다. 도구가 현재 상태와 원하는 상태의 차이를 계산하여 적용한다.

```hcl
# Terraform (선언적)
# "이런 상태가 되어야 한다"

resource "aws_instance" "web" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.medium"

  tags = {
    Name = "web-server"
  }
}

# 이미 존재하면 변경사항만 적용
# 없으면 새로 생성
# 코드에 없는 리소스는 삭제 대상
```

### 명령적 (Imperative)

**"어떻게(How)"** 수행할지 단계별로 지시한다.

```yaml
# Ansible (명령적 성격이 강함)
# "이 단계들을 순서대로 수행하라"

- name: Install nginx
  apt:
    name: nginx
    state: present

- name: Start nginx
  service:
    name: nginx
    state: started

- name: Copy config file
  copy:
    src: nginx.conf
    dest: /etc/nginx/nginx.conf
```

### 비교

| 구분 | 선언적 | 명령적 |
|------|--------|--------|
| **정의** | 원하는 최종 상태 | 수행할 단계 |
| **멱등성** | 도구가 자동 보장 | 개발자가 직접 관리 |
| **학습 곡선** | 중간 | 낮음 (절차적) |
| **대표 도구** | Terraform, CloudFormation | Ansible, Chef |
| **적합한 대상** | 인프라 프로비저닝 | 서버 내부 설정 관리 |

> 실무에서는 **Terraform(인프라 프로비저닝) + Ansible(서버 구성 관리)**를 함께 사용하는 패턴이 일반적이다.

---

## 4. Terraform 소개

**Terraform**은 HashiCorp에서 개발한 오픈소스 IaC 도구로, **HCL(HashiCorp Configuration Language)**을 사용하여 인프라를 정의한다.

### 주요 특징

- **멀티 클라우드**: AWS, GCP, Azure 등 다양한 클라우드 프로바이더 지원
- **선언적 언어**: 원하는 상태를 정의하면 자동으로 실행 계획 수립
- **상태 관리**: 인프라의 현재 상태를 추적하고 관리
- **모듈 시스템**: 재사용 가능한 인프라 컴포넌트 구성
- **대규모 에코시스템**: 수천 개의 프로바이더와 모듈 지원

---

## 5. Terraform 핵심 개념

### Provider

클라우드 서비스나 외부 API와 통신하는 플러그인이다:

```hcl
# AWS 프로바이더 설정
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.7.0"
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "my-project"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

### Resource

관리할 인프라 리소스를 정의한다:

```hcl
# VPC 생성
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# 서브넷 생성
resource "aws_subnet" "public" {
  count             = length(var.public_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.public_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
    Tier = "public"
  }
}

# EC2 인스턴스
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.public[0].id

  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = templatefile("${path.module}/scripts/init.sh", {
    app_port = var.app_port
  })

  tags = {
    Name = "${var.project_name}-web"
  }
}
```

### Data Source

기존 리소스의 정보를 조회한다:

```hcl
# 최신 Ubuntu AMI 조회
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical 공식 계정

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-*-22.04-amd64-server-*"]
  }
}

# 현재 AWS 계정 정보
data "aws_caller_identity" "current" {}

# 사용 예시
output "account_id" {
  value = data.aws_caller_identity.current.account_id
}
```

### Variable & Output

```hcl
# variables.tf
variable "environment" {
  description = "배포 환경 (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment는 dev, staging, prod 중 하나여야 합니다."
  }
}

variable "instance_type" {
  description = "EC2 인스턴스 타입"
  type        = string
  default     = "t3.medium"
}

variable "public_subnet_cidrs" {
  description = "퍼블릭 서브넷 CIDR 목록"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "db_password" {
  description = "데이터베이스 비밀번호"
  type        = string
  sensitive   = true                # 출력에서 마스킹
}

# outputs.tf
output "vpc_id" {
  description = "생성된 VPC의 ID"
  value       = aws_vpc.main.id
}

output "web_instance_public_ip" {
  description = "웹 서버 퍼블릭 IP"
  value       = aws_instance.web.public_ip
}
```

---

## 6. Terraform 워크플로우

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  init    │───▶│  plan    │───▶│  apply   │───▶│ destroy  │
│          │    │          │    │          │    │ (선택)    │
│ 초기화    │    │ 실행계획  │    │ 적용     │    │ 삭제     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 각 단계 상세

```bash
# 1. Init: 프로바이더 다운로드, 백엔드 초기화
terraform init

# 2. Validate: 구문 검증
terraform validate

# 3. Format: 코드 포맷팅
terraform fmt -recursive

# 4. Plan: 변경 사항 미리 확인
terraform plan -out=tfplan
# + 생성, ~ 수정, - 삭제 표시

# 5. Apply: 실제 인프라에 적용
terraform apply tfplan
# 또는 terraform apply -auto-approve (주의: 프로덕션에서는 사용 자제)

# 6. Destroy: 모든 리소스 삭제
terraform destroy
```

### Plan 출력 예시

```
Terraform will perform the following actions:

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami                    = "ami-0abcdef1234567890"
      + instance_type          = "t3.medium"
      + public_ip              = (known after apply)
      + tags                   = {
          + "Name" = "my-project-web"
        }
    }

  # aws_security_group.web will be modified
  ~ resource "aws_security_group" "web" {
      ~ ingress = [
          + {
              + from_port   = 443
              + to_port     = 443
              + protocol    = "tcp"
              + cidr_blocks = ["0.0.0.0/0"]
            },
        ]
    }

Plan: 1 to add, 1 to change, 0 to destroy.
```

---

## 7. 상태 관리

Terraform은 **terraform.tfstate** 파일로 인프라의 현재 상태를 추적한다.

### 로컬 상태의 문제점

```
개발자 A의 로컬          개발자 B의 로컬
┌─────────────────┐    ┌─────────────────┐
│ terraform.tfstate│    │ terraform.tfstate│
│ (서로 다른 상태) │    │ (서로 다른 상태) │
└─────────────────┘    └─────────────────┘
        │                      │
        └──── 충돌 발생! ──────┘
```

### 리모트 백엔드 설정

팀 작업 시 반드시 리모트 백엔드를 사용해야 한다:

```hcl
# S3 + DynamoDB 백엔드 (AWS)
terraform {
  backend "s3" {
    bucket         = "my-project-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "ap-northeast-2"
    encrypt        = true
    dynamodb_table = "terraform-lock"     # 동시 실행 방지 (잠금)
  }
}
```

```
리모트 백엔드 구조:

개발자 A ──┐                     ┌── S3 Bucket
           ├──▶ DynamoDB Lock ──▶│   terraform.tfstate
개발자 B ──┘    (동시 실행 방지)   └── (암호화 저장)
```

### 상태 관리 명령어

```bash
# 상태에 있는 리소스 목록 조회
terraform state list

# 특정 리소스 상세 정보
terraform state show aws_instance.web

# 상태에서 리소스 제거 (인프라는 유지, 관리만 해제)
terraform state rm aws_instance.web

# 리소스를 다른 이름으로 이동 (리팩토링 시)
terraform state mv aws_instance.web aws_instance.web_server

# 외부에서 생성된 리소스를 상태에 추가
terraform import aws_instance.web i-0abc123def456789
```

---

## 8. 모듈화 패턴

### 디렉토리 구조

```
infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       └── terraform.tfvars
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ec2/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── rds/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── global/
    ├── iam/
    └── dns/
```

### 모듈 정의

```hcl
# modules/vpc/main.tf
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

resource "aws_subnet" "public" {
  count             = length(var.public_subnet_cidrs)
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.public_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-public-${count.index + 1}"
  }
}

# modules/vpc/variables.tf
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type = list(string)
}

variable "availability_zones" {
  type = list(string)
}

# modules/vpc/outputs.tf
output "vpc_id" {
  value = aws_vpc.this.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}
```

### 모듈 사용

```hcl
# environments/prod/main.tf
module "vpc" {
  source = "../../modules/vpc"

  project_name        = "my-project"
  environment         = "prod"
  vpc_cidr            = "10.0.0.0/16"
  public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
  availability_zones  = ["ap-northeast-2a", "ap-northeast-2c"]
}

module "web" {
  source = "../../modules/ec2"

  project_name  = "my-project"
  environment   = "prod"
  instance_type = "t3.large"
  subnet_id     = module.vpc.public_subnet_ids[0]  # 모듈 출력 참조
}
```

---

## 9. Terraform vs CloudFormation vs Pulumi 비교표

| 항목 | Terraform | CloudFormation | Pulumi |
|------|-----------|---------------|--------|
| **개발사** | HashiCorp | AWS | Pulumi Inc. |
| **언어** | HCL | JSON/YAML | Python, TypeScript, Go 등 |
| **멀티 클라우드** | 지원 | AWS 전용 | 지원 |
| **상태 관리** | tfstate (로컬/리모트) | AWS 자동 관리 | Pulumi Cloud / 자체 |
| **학습 곡선** | 중간 (HCL 학습) | 낮음 (AWS 사용자) | 낮음 (기존 언어 사용) |
| **에코시스템** | 매우 넓음 (3000+ providers) | AWS 완벽 지원 | 성장 중 |
| **드리프트 감지** | plan 시 확인 | 드리프트 감지 기능 | preview 시 확인 |
| **가격** | 오픈소스 / Cloud 유료 | 무료 (AWS 내) | 오픈소스 / Cloud 유료 |
| **테스트** | Terratest, tftest | TaskCat | 일반 테스트 프레임워크 |
| **적합한 경우** | 멀티 클라우드, 범용 | AWS 올인 | 프로그래밍 선호 |

### 선택 가이드

```
Q1. AWS만 사용하는가?
    └── YES → CloudFormation (네이티브 통합)
    └── NO  → Q2

Q2. 프로그래밍 언어로 인프라를 정의하고 싶은가?
    └── YES → Pulumi (TypeScript, Python 등)
    └── NO  → Terraform (HCL, 업계 표준)
```

---

## 10. IaC 베스트 프랙티스

### 코드 관리

1. **모든 인프라를 코드로 관리**: 콘솔에서의 수동 변경을 금지한다
2. **작은 단위로 변경**: 한 번에 큰 변경보다 작은 변경을 자주 적용한다
3. **코드 리뷰 필수**: 인프라 변경도 PR 리뷰를 거친다
4. **환경별 변수 분리**: `terraform.tfvars`로 환경별 설정을 관리한다

### 보안

```hcl
# 민감 정보는 변수로 분리하고 sensitive 표시
variable "db_password" {
  type      = string
  sensitive = true
}

# terraform.tfvars는 .gitignore에 추가
# 시크릿은 외부 시크릿 매니저 연동
data "aws_secretsmanager_secret_version" "db" {
  secret_id = "my-project/db-password"
}
```

### CI/CD 통합

```yaml
# GitHub Actions에서 Terraform 실행
name: Terraform

on:
  pull_request:
    paths: ['infrastructure/**']
  push:
    branches: [main]
    paths: ['infrastructure/**']

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.0

      - name: Terraform Init
        run: terraform init
        working-directory: infrastructure/environments/prod

      - name: Terraform Plan
        run: terraform plan -no-color
        working-directory: infrastructure/environments/prod

  apply:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    needs: plan
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init && terraform apply -auto-approve
        working-directory: infrastructure/environments/prod
```

### 기타 베스트 프랙티스

| 항목 | 설명 |
|------|------|
| **상태 파일 암호화** | 리모트 백엔드에서 암호화 활성화 |
| **잠금(Lock) 사용** | DynamoDB 등으로 동시 실행 방지 |
| **태깅 표준화** | 모든 리소스에 일관된 태그 적용 |
| **모듈 버전 관리** | 모듈에 버전을 부여하고 변경 추적 |
| **destroy 보호** | 중요 리소스에 `prevent_destroy` 설정 |
| **정기적 Plan** | 드리프트를 감지하기 위해 주기적으로 plan 실행 |

```hcl
# 실수로 삭제 방지
resource "aws_rds_instance" "main" {
  # ...

  lifecycle {
    prevent_destroy = true    # destroy 시 에러 발생
  }
}
```

---

## 마무리

IaC는 현대 인프라 관리의 핵심 패러다임이다. 핵심 포인트를 정리하면:

- IaC를 도입하면 **재현성, 버전 관리, 자동화**라는 세 가지 핵심 가치를 얻는다
- **Terraform**은 멀티 클라우드 환경에서 가장 널리 사용되는 IaC 도구다
- **모듈화**를 통해 재사용성과 유지보수성을 높인다
- **리모트 상태 관리**와 **잠금**으로 팀 협업 시 충돌을 방지한다
- **CI/CD 파이프라인에 통합**하여 인프라 변경도 자동화된 검증을 거치게 한다

다음 글에서는 인프라를 안정적으로 운영하기 위한 **모니터링과 옵저버빌리티** 전략을 다룰 예정이다.
