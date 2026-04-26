<!-- infographic-hero -->
![Amazon Q Business -- 엔터프라이즈용 생성형 AI 기반 업무 비서 핵심 요약](figures/infographic.svg)

*Figure: Amazon Q Business -- 엔터프라이즈용 생성형 AI 기반 업무 비서 한 장 요약 인포그래픽*

## 개요

Amazon Q Business는 기업 내부의 데이터, 문서, 시스템을 기반으로 동작하는 완전 관리형 생성형 AI 비서 서비스입니다. 직원들이 자연어로 질문하면 사내 문서, Wiki, Confluence, SharePoint, Salesforce, ServiceNow 등 다양한 엔터프라이즈 데이터 소스에서 관련 정보를 검색하고, 정확한 답변을 생성하여 제공합니다.

기업 환경에서 생성형 AI를 도입할 때 가장 큰 과제는 기업 고유의 지식과 데이터를 AI에 안전하게 통합하는 것입니다. Amazon Q Business는 이 과제를 해결하기 위해 다음과 같은 기능을 제공합니다.

- **40개 이상의 데이터 소스 커넥터**: S3, Confluence, SharePoint, Salesforce, ServiceNow, Slack, Jira, Google Drive 등
- **기존 권한 체계 유지**: 데이터 소스의 ACL(Access Control List)을 그대로 반영하여, 사용자가 접근 권한이 있는 문서만 기반으로 답변합니다.
- **플러그인 (Plugins)**: Jira 티켓 생성, ServiceNow 인시던트 등록, Salesforce 케이스 업데이트 등 외부 시스템에 대한 액션을 수행합니다.
- **가드레일**: 응답의 품질과 안전성을 보장하는 내장 보호 메커니즘을 제공합니다.
- **IAM Identity Center 통합**: 기업의 기존 IdP(Active Directory, Okta 등)와 연동하여 사용자를 인증합니다.

---

## 핵심 기능

### 1. 애플리케이션 생성

```bash
# Amazon Q Business 애플리케이션 생성
aws qbusiness create-application \
  --display-name "사내 지식 비서" \
  --description "전사 문서 기반 AI 비서" \
  --role-arn "arn:aws:iam::123456789012:role/QBusinessServiceRole" \
  --identity-center-instance-arn "arn:aws:sso:::instance/ssoins-abc123" \
  --region us-east-1

# 애플리케이션 목록 조회
aws qbusiness list-applications \
  --region us-east-1

# 애플리케이션 상세 정보 확인
aws qbusiness get-application \
  --application-id "app-abc123" \
  --region us-east-1
```

### 2. 인덱스 (Index) 생성

인덱스는 문서를 저장하고 검색하는 핵심 구성 요소입니다.

```bash
# 인덱스 생성
aws qbusiness create-index \
  --application-id "app-abc123" \
  --display-name "company-knowledge-index" \
  --description "사내 문서 인덱스" \
  --type ENTERPRISE \
  --capacity-configuration '{
    "units": 1
  }' \
  --region us-east-1
```

### 3. 데이터 소스 커넥터

Amazon Q Business의 핵심 강점은 풍부한 데이터 소스 커넥터입니다.

```bash
# S3 데이터 소스 연결
aws qbusiness create-data-source \
  --application-id "app-abc123" \
  --index-id "idx-xyz789" \
  --display-name "company-docs-s3" \
  --description "S3에 저장된 사내 문서" \
  --role-arn "arn:aws:iam::123456789012:role/QBusinessDataSourceRole" \
  --configuration '{
    "type": "S3",
    "connectionConfiguration": {
      "repositoryEndpointMetadata": {
        "BucketName": "company-documents"
      }
    },
    "repositoryConfigurations": {
      "document": {
        "fieldMappings": [
          {"indexFieldName": "_document_title", "indexFieldType": "STRING", "dataSourceFieldName": "title"},
          {"indexFieldName": "_document_body", "indexFieldType": "STRING", "dataSourceFieldName": "body"}
        ]
      }
    },
    "syncMode": "FULL_CRAWL",
    "additionalProperties": {
      "inclusionPrefixes": ["docs/", "policies/", "guides/"],
      "exclusionPatterns": ["*.tmp", "*.bak"]
    }
  }' \
  --sync-schedule 'rate(1 day)' \
  --region us-east-1

# Confluence 데이터 소스 연결
aws qbusiness create-data-source \
  --application-id "app-abc123" \
  --index-id "idx-xyz789" \
  --display-name "confluence-wiki" \
  --description "Confluence 사내 Wiki" \
  --role-arn "arn:aws:iam::123456789012:role/QBusinessDataSourceRole" \
  --configuration '{
    "type": "CONFLUENCEV2",
    "connectionConfiguration": {
      "repositoryEndpointMetadata": {
        "hostUrl": "https://company.atlassian.net/wiki",
        "authType": "OAuth2"
      }
    },
    "repositoryConfigurations": {
      "space": {
        "fieldMappings": [
          {"indexFieldName": "space_key", "indexFieldType": "STRING", "dataSourceFieldName": "spaceKey"}
        ]
      },
      "page": {
        "fieldMappings": [
          {"indexFieldName": "_document_title", "indexFieldType": "STRING", "dataSourceFieldName": "title"}
        ]
      }
    },
    "syncMode": "FULL_CRAWL"
  }' \
  --sync-schedule 'rate(6 hours)' \
  --region us-east-1
```

### 4. 데이터 동기화

```bash
# 데이터 소스 동기화 시작
aws qbusiness start-data-source-sync-job \
  --application-id "app-abc123" \
  --index-id "idx-xyz789" \
  --data-source-id "ds-def456" \
  --region us-east-1

# 동기화 작업 상태 조회
aws qbusiness list-data-source-sync-jobs \
  --application-id "app-abc123" \
  --index-id "idx-xyz789" \
  --data-source-id "ds-def456" \
  --region us-east-1
```

### 5. 웹 익스피리언스 (Web Experience)

사용자가 접근할 수 있는 웹 기반 채팅 인터페이스를 생성합니다.

```bash
# 웹 익스피리언스 생성
aws qbusiness create-web-experience \
  --application-id "app-abc123" \
  --title "사내 AI 비서" \
  --subtitle "무엇이든 물어보십시오" \
  --welcome-message "안녕하세요. 사내 문서와 지식을 기반으로 질문에 답변해 드립니다. 무엇을 도와드릴까요?" \
  --role-arn "arn:aws:iam::123456789012:role/QBusinessWebExperienceRole" \
  --region us-east-1

# 웹 익스피리언스 URL 조회
aws qbusiness get-web-experience \
  --application-id "app-abc123" \
  --web-experience-id "we-ghi012" \
  --query 'defaultEndpoint' \
  --region us-east-1
```

### 6. 플러그인 (Plugins)

외부 시스템에 대한 액션을 수행하는 플러그인을 구성합니다.

```bash
# Jira 플러그인 생성
aws qbusiness create-plugin \
  --application-id "app-abc123" \
  --display-name "Jira 티켓 관리" \
  --type JIRA \
  --auth-configuration '{
    "oAuth2ClientCredentialConfiguration": {
      "secretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:jira-oauth-abc123",
      "roleArn": "arn:aws:iam::123456789012:role/QBusinessPluginRole"
    }
  }' \
  --server-url "https://company.atlassian.net" \
  --region us-east-1

# ServiceNow 플러그인 생성
aws qbusiness create-plugin \
  --application-id "app-abc123" \
  --display-name "ServiceNow 인시던트 관리" \
  --type SERVICE_NOW \
  --auth-configuration '{
    "oAuth2ClientCredentialConfiguration": {
      "secretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:servicenow-oauth-xyz",
      "roleArn": "arn:aws:iam::123456789012:role/QBusinessPluginRole"
    }
  }' \
  --server-url "https://company.service-now.com" \
  --region us-east-1
```

### 7. 가드레일 및 관리 제어

```bash
# 응답 차단 주제 설정
aws qbusiness update-application \
  --application-id "app-abc123" \
  --attachments-configuration '{"attachmentsControlMode": "ENABLED"}' \
  --region us-east-1

# 사용자별 대화 기록 조회
aws qbusiness list-conversations \
  --application-id "app-abc123" \
  --user-id "user@company.com" \
  --region us-east-1
```

---

## 아키텍처/동작 원리

### 전체 아키텍처

```
[사용자]
    |
    v
[IAM Identity Center 인증]
    |
    v
[Web Experience (채팅 UI)]
    |
    v
[Amazon Q Business Application]
    |
    +---> [질의 처리 엔진]
    |       +--- 사용자 질의 분석
    |       +--- ACL 기반 문서 필터링
    |       +--- 관련 문서 검색 (인덱스)
    |       +--- 응답 생성 (FM)
    |       +--- 가드레일 적용
    |
    +---> [인덱스]
    |       +--- S3 문서
    |       +--- Confluence 페이지
    |       +--- SharePoint 문서
    |       +--- Salesforce 기사
    |       +--- Slack 메시지
    |       +--- (기타 40+ 커넥터)
    |
    +---> [플러그인]
            +--- Jira (티켓 생성/조회)
            +--- ServiceNow (인시던트 관리)
            +--- Salesforce (케이스 업데이트)
            +--- Zendesk (티켓 관리)
            +--- 커스텀 플러그인
```

### ACL 기반 접근 제어 원리

Amazon Q Business의 가장 중요한 보안 메커니즘은 데이터 소스의 기존 접근 제어를 그대로 유지하는 것입니다.

```
[사용자 A (영업팀)]
    |
    v
[IAM Identity Center 인증]
    |
    v
[ACL 매핑]
  - Confluence: 영업팀 스페이스 접근 가능
  - SharePoint: 영업 폴더 접근 가능
  - Salesforce: 자신의 계정 데이터만 접근 가능
    |
    v
[문서 검색 시 ACL 필터 적용]
  - 영업 관련 문서만 검색 대상에 포함
  - 인사/재무 등 비인가 문서는 자동 제외
    |
    v
[영업팀 관련 답변만 생성]
```

### 응답 생성 흐름

1. 사용자가 자연어로 질문합니다.
2. IAM Identity Center를 통해 사용자 신원과 그룹 멤버십을 확인합니다.
3. 질의를 분석하여 검색 쿼리를 생성합니다.
4. 인덱스에서 관련 문서를 검색하되, 사용자의 ACL에 기반하여 접근 가능한 문서만 반환합니다.
5. 검색된 문서를 컨텍스트로 사용하여 FM이 답변을 생성합니다.
6. 가드레일을 적용하여 부적절한 응답을 필터링합니다.
7. 답변과 함께 출처 문서의 링크를 제공합니다.

---

## 실전 활용

### 사례 1: IT 헬프데스크 자동화

IT 부서의 지원 요청을 Amazon Q Business로 자동화하는 시나리오입니다.

**구성 단계**:

1. IT 문서(Confluence Wiki, SharePoint)를 데이터 소스로 연결합니다.
2. ServiceNow 플러그인을 구성하여 인시던트 생성 기능을 추가합니다.
3. 웹 익스피리언스를 생성하여 직원들이 접근할 수 있게 합니다.

**사용자 시나리오**:
- 직원: "VPN에 연결할 수 없습니다. 어떻게 해야 하나요?"
- Q Business: IT Wiki에서 VPN 연결 가이드를 검색하여 단계별 해결 방법을 제공합니다.
- 직원: "시도했지만 여전히 안 됩니다. 인시던트를 생성해 주십시오."
- Q Business: ServiceNow 플러그인을 통해 인시던트를 자동 생성합니다.

### 사례 2: API를 통한 프로그래밍 방식 접근

```python
import boto3

qbusiness = boto3.client('qbusiness', region_name='us-east-1')

# 대화 시작 및 질의
response = qbusiness.chat_sync(
    applicationId='app-abc123',
    userMessage='올해 회사의 휴가 정책이 변경된 사항이 있나요?',
    userId='user@company.com'
)

print(f"답변: {response['systemMessage']}")

# 출처 문서 확인
for source in response.get('sourceAttributions', []):
    print(f"출처: {source['title']} - {source['url']}")
    print(f"관련 텍스트: {source['snippet']}")
```

### 사례 3: 커스텀 플러그인 (Custom Plugin)

```bash
# 커스텀 플러그인 생성 (OpenAPI 스키마 기반)
aws qbusiness create-plugin \
  --application-id "app-abc123" \
  --display-name "사내 예약 시스템" \
  --type CUSTOM \
  --auth-configuration '{
    "basicAuthConfiguration": {
      "secretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:booking-api-creds",
      "roleArn": "arn:aws:iam::123456789012:role/QBusinessPluginRole"
    }
  }' \
  --custom-plugin-configuration '{
    "description": "회의실 및 장비 예약 시스템",
    "apiSchemaType": "OPEN_API_V3_SCHEMA",
    "apiSchema": {
      "s3": {
        "bucket": "my-plugin-schemas",
        "key": "booking-api-schema.yaml"
      }
    }
  }' \
  --region us-east-1
```

---

## 모범 사례/보안

### 데이터 보안

- 모든 데이터는 AWS 계정 내에서 처리되며, 외부로 유출되지 않습니다.
- 인덱스 데이터는 KMS로 암호화됩니다.
- ACL 기반 접근 제어를 통해 사용자별로 접근 가능한 문서를 제한합니다.
- 관리자는 대화 기록을 모니터링하고 감사할 수 있습니다.

### 배포 모범 사례

- 데이터 소스 동기화 일정을 적절히 설정합니다. 자주 변경되는 소스는 짧은 주기로, 안정적인 소스는 긴 주기로 동기화합니다.
- 인덱스 용량을 실제 문서량에 맞게 설정합니다.
- 웹 익스피리언스의 환영 메시지를 통해 사용자에게 시스템의 범위와 한계를 안내합니다.
- 파일럿 그룹으로 먼저 배포하여 응답 품질을 검증한 후 전사 확대합니다.

### 비용 구조

Amazon Q Business의 비용은 주로 다음 요소로 구성됩니다.

- **인덱스 비용**: 인덱스 유닛당 시간 과금
- **커넥터 비용**: 데이터 소스 동기화 시 문서 스캔 건수 기반
- **사용자 라이선스**: 사용자 유형(Q Business Lite / Q Business Pro)에 따른 월간 구독

```bash
# 비용 모니터링을 위한 CloudWatch 알람
aws cloudwatch put-metric-alarm \
  --alarm-name "qbusiness-query-volume" \
  --alarm-description "Q Business 일일 쿼리량 모니터링" \
  --namespace "AWS/QBusiness" \
  --metric-name "QueryCount" \
  --statistic Sum \
  --period 86400 \
  --threshold 10000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:us-east-1:123456789012:qbusiness-alerts" \
  --region us-east-1
```

---

## 관련 서비스 비교

| 항목 | Amazon Q Business | Amazon Kendra | Microsoft Copilot | Google Vertex AI Search |
|------|-------------------|---------------|--------------------|--------------------------|
| 서비스 유형 | 생성형 AI 비서 | 지능형 검색 | 생성형 AI 비서 | 지능형 검색 + 대화 |
| 답변 방식 | 생성형 답변 + 출처 | 검색 결과 반환 | 생성형 답변 + 출처 | 검색 + 요약 |
| 데이터 커넥터 | 40개 이상 | 40개 이상 | Microsoft 365 중심 | Google Workspace 중심 |
| 플러그인/액션 | Jira, ServiceNow 등 | 미지원 | Microsoft 365 액션 | 제한적 |
| ACL 지원 | 네이티브 지원 | 네이티브 지원 | Microsoft 365 ACL | Google Workspace ACL |
| IdP 통합 | IAM Identity Center | IAM Identity Center | Azure AD | Google Workspace |
| 적합한 환경 | AWS/멀티소스 환경 | 검색 특화 워크로드 | Microsoft 환경 | Google 환경 |

---

## 요약

Amazon Q Business는 기업 내부 데이터를 기반으로 동작하는 완전 관리형 생성형 AI 비서 서비스입니다. 주요 특징을 정리하면 다음과 같습니다.

- 40개 이상의 엔터프라이즈 데이터 소스 커넥터(S3, Confluence, SharePoint, Salesforce, Slack, Jira 등)를 제공합니다.
- 데이터 소스의 기존 ACL(접근 제어)을 그대로 반영하여, 사용자가 권한이 있는 문서만 기반으로 답변합니다.
- 플러그인을 통해 Jira 티켓 생성, ServiceNow 인시던트 등록 등 외부 시스템에 대한 액션을 수행합니다.
- IAM Identity Center 통합으로 기업의 기존 IdP(Active Directory, Okta 등)와 원활하게 연동됩니다.
- 웹 익스피리언스를 통해 코딩 없이 직원용 채팅 인터페이스를 즉시 배포할 수 있습니다.
- 모든 데이터는 AWS 계정 내에서 처리되며, KMS 암호화와 감사 로깅을 지원합니다.

Amazon Q Business는 기업의 분산된 지식을 통합하여 직원의 생산성을 향상시키는 핵심 AI 도구로, 특히 다양한 데이터 소스를 보유한 조직에서 큰 가치를 발휘합니다.