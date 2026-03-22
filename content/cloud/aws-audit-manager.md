---
title: AWS Audit Manager
slug: "aws-audit-manager"
category: cloud
tags: ["audit-manager", "aws", "cloud-security", "compliance", "compliance-frameworks", "evidence-collection", "governance", "multi-cloud"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.380549+00:00"
---

AWS Audit Manager를 사용하면 AWS 사용량을 지속적으로 감사하여 위험과 규정 및 업계 표준 준수를 관리하는 작업을 간소화할 수 있습니다. _Audit Manager는 증거 수집을 자동화하여 정책, 절차 및 활동(컨트롤이라고도 함)이 효과적으로 운영되는지 더 쉽게 평가할 수 있도록 합니다._ 감사 기간 동안 Audit Manager는 컨트롤에 대한 이해관계자의 검토를 관리하므로, 수작업을 대폭 줄여 감사에 바로 사용할 수 있는 보고서를 생성할 수 있습니다.

Audit Manager는 지정된 규정 준수 표준 또는 규정에 대한 평가를 구조화하고 자동화하는 사전 구축된 프레임워크를 제공합니다. 프레임워크에는 설명과 테스트 절차가 포함된 사전 구축된 컨트롤 모음이 포함되며, 이러한 컨트롤은 해당 규정 준수 표준 또는 규정의 요구사항에 따라 그룹화됩니다. 또한 내부 감사의 특정 요구사항을 충족하도록 프레임워크와 컨트롤을 사용자 지정할 수 있습니다.

모든 프레임워크에서 평가를 생성할 수 있습니다. 평가를 생성하면 Audit Manager가 자동으로 리소스 평가를 실행하여 감사 범위로 정의한 AWS 계정에 대한 데이터를 수집합니다. 수집된 데이터는 감사에 적합한 증거로 자동 변환되고, 보안·변경 관리·비즈니스 연속성·소프트웨어 라이선싱 등 관련 컨트롤에 첨부되어 규정 준수를 입증하는 데 사용됩니다. 이 증거 수집 프로세스는 평가를 작성할 때부터 진행됩니다. 감사를 완료하여 더 이상 증거 수집이 필요하지 않으면 평가 상태를 _비활성으로_ 변경하여 증거 수집을 중단할 수 있습니다.

## Audit Manager 기능

AWS Audit Manager를 사용하면 다음 작업을 수행할 수 있습니다.

- 빠르게 시작  - 다양한 규정 준수 표준 및 규정을 지원하는 사전 구축된 프레임워크 갤러리에서 선택하여 [첫 번째 평가를 작성하세요](https://docs.aws.amazon.com/audit-manager/latest/userguide/tutorial-for-audit-owners.html). 그런 다음 자동 증거 수집을 시작하여 AWS 서비스 사용량을 감사합니다.

- 하이브리드 또는 멀티클라우드 환경에서 증거 업로드 및 관리  - Audit Manager가 AWS 환경에서 수집하는 증거 외에도 온프레미스 또는 멀티클라우드 환경에서 확보한 증거를 [업로드](https://docs.aws.amazon.com/audit-manager/latest/userguide/upload-evidence.html)하고 중앙에서 관리할 수 있습니다.

- 공통 규정 준수 표준 및 규정 지원  - [AWS Audit Manager 표준 프레임워크](https://docs.aws.amazon.com/audit-manager/latest/userguide/framework-overviews.html) 중 하나를 선택하세요. 이들 프레임워크는 공통 규정 준수 표준 및 규정에 대한 사전 구축된 컨트롤 매핑을 제공합니다. 여기에는 CIS 벤치마크, PCI DSS, GDPR, HIPAA, SOC2, GxP 및 AWS 운영 모범 사례가 포함됩니다.

- 진행 중인 평가 모니터링  - Audit Manager [대시보드](https://docs.aws.amazon.com/audit-manager/latest/userguide/dashboard.html)를 사용하여 활성 평가에 대한 분석을 보고, 수정이 필요한 규정을 준수하지 않는 증거를 빠르게 식별할 수 있습니다.

- 증거 검색  - [증거 찾기](https://docs.aws.amazon.com/ko_kr/audit-manager/latest/userguide/evidence-finder.html) 기능을 사용하여 검색 쿼리와 관련된 증거를 빠르게 찾을 수 있습니다. 검색 결과에서 평가 보고서를 생성하거나 결과를 CSV 형식으로 내보낼 수 있습니다.

- **사용자 지정 컨트롤 생성**  - [처음부터 자체 컨트롤을 생성](https://docs.aws.amazon.com/audit-manager/latest/userguide/customize-control-from-scratch.html)하거나 [기존 표준 컨트롤 또는 사용자 지정 컨트롤의 편집 가능한 복사본을 생성](https://docs.aws.amazon.com/audit-manager/latest/userguide/customize-control-from-existing.html)할 수 있습니다. 또한 사용자 지정 컨트롤을 통해 위험 평가 질문을 만들고 해당 질문에 대한 응답을 수동 증거로 저장할 수 있습니다.

- **엔터프라이즈 컨트롤을 사전 정의된 AWS 데이터 소스 그룹에 매핑**  - 공통 목표를 나타내는 컨트롤을 선택하고 이를 사용해 규정 준수 요구사항 포트폴리오에 대한 증거를 수집하도록 [사용자 지정 컨트롤을 생성](https://docs.aws.amazon.com/audit-manager/latest/userguide/customize-control-from-scratch.html)할 수 있습니다.

- 사용자 지정 프레임워크 생성  - 내부 감사의 특정 요구사항에 맞게 표준 또는 사용자 지정 컨트롤을 사용하여 [자체 프레임워크를 생성](https://docs.aws.amazon.com/audit-manager/latest/userguide/custom-frameworks.html)할 수 있습니다.

- 사용자 지정 프레임워크 공유  - [사용자 지정 Audit Manager 프레임워크를 다른 AWS 계정과 공유](https://docs.aws.amazon.com/audit-manager/latest/userguide/share-custom-framework.html)하거나 자신의 계정으로 다른 AWS 리전에 복제할 수 있습니다.

- 팀 간 협업 지원  - 관련 증거를 검토하고 의견을 추가하며 각 컨트롤의 상태를 업데이트할 수 있도록 주제 전문가에게 [컨트롤 세트를 위임](https://docs.aws.amazon.com/audit-manager/latest/userguide/delegate-for-audit-owners.html)할 수 있습니다.

- 감사자용 보고서 작성  - 감사를 위해 수집된 관련 증거를 요약하는 [평가 보고서를 생성](https://docs.aws.amazon.com/audit-manager/latest/userguide/generate-assessment-report.html)하고, 자세한 증거가 포함된 폴더에 연결할 수 있습니다.

- 증거 무결성 보장  - [증거를 변경하지 않고 안전한 장소에 보관하세요](https://docs.aws.amazon.com/audit-manager/latest/userguide/settings-destination.html).

https://docs.aws.amazon.com/ko_kr/audit-manager/latest/userguide/what-is.html

###### 참고