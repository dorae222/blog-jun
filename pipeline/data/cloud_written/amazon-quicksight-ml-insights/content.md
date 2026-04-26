<!-- infographic-hero -->
![Amazon QuickSight ML Insights 핵심 요약](figures/infographic.svg)

*Figure: Amazon QuickSight ML Insights 한 장 요약 인포그래픽*

# Amazon QuickSight ML Insights

## 개요

Amazon QuickSight ML Insights는 QuickSight에 내장된 기계 학습(Machine Learning) 기반 분석 기능입니다. 데이터 과학 전문 지식 없이도 이상 탐지(Anomaly Detection), 예측(Forecasting), 자동 서술(Auto-Narratives) 등의 고급 분석 기능을 대시보드에서 바로 활용할 수 있습니다.

전통적으로 ML 기반 분석을 수행하려면 데이터 과학 팀이 별도의 ML 파이프라인을 구축해야 했습니다. QuickSight ML Insights는 이러한 복잡성을 추상화하여, 비즈니스 사용자가 클릭 몇 번만으로 ML 기반 인사이트를 얻을 수 있도록 합니다.

ML Insights의 주요 기능은 다음과 같습니다.

- **이상 탐지(Anomaly Detection)**: Random Cut Forest(RCF) 알고리즘을 사용하여 데이터의 비정상적인 패턴을 자동으로 감지합니다.
- **예측(Forecasting)**: 시계열 데이터를 기반으로 미래 값을 예측합니다.
- **자동 서술(Auto-Narratives)**: 데이터의 핵심 인사이트를 자연어로 자동 생성합니다.
- **기여도 분석(Contribution Analysis)**: 이상 현상의 원인이 되는 주요 요인을 자동으로 분석합니다.
- **Amazon Q in QuickSight**: 자연어 질의를 통한 데이터 분석 기능입니다.

이 기능들은 QuickSight Enterprise 에디션에서 사용할 수 있으며, 추가 비용 없이 제공됩니다.

## 핵심 기능

### 1. 이상 탐지 (Anomaly Detection)

QuickSight의 이상 탐지는 Amazon의 Random Cut Forest(RCF) 알고리즘을 기반으로 합니다. RCF는 비지도 학습 알고리즘으로, 레이블이 없는 데이터에서도 이상치를 효과적으로 탐지할 수 있습니다.

#### 주요 특징

- **비지도 학습**: 별도의 학습 데이터나 레이블링이 필요 없습니다.
- **실시간 분석**: SPICE 데이터 새로고침과 함께 이상 탐지 결과가 업데이트됩니다.
- **다차원 분석**: 여러 측정값과 차원의 조합에서 이상을 탐지합니다.
- **기여도 분석**: 이상이 탐지되면 어떤 차원이 이상에 가장 크게 기여했는지 자동으로 분석합니다.

```bash
# QuickSight 분석에서 이상 탐지 인사이트 설정을 포함한 템플릿 조회
aws quicksight describe-template \
  --aws-account-id 123456789012 \
  --template-id anomaly-detection-template \
  --query 'Template.{Name:Name,Version:Version.VersionNumber}'

# SPICE 데이터셋 새로고침 (이상 탐지 결과 업데이트를 위해)
aws quicksight create-ingestion \
  --aws-account-id 123456789012 \
  --data-set-id sales-metrics-dataset \
  --ingestion-id anomaly-refresh-$(date +%Y%m%d%H%M%S)

# 새로고침 상태 확인
aws quicksight describe-ingestion \
  --aws-account-id 123456789012 \
  --data-set-id sales-metrics-dataset \
  --ingestion-id anomaly-refresh-20240115120000
```

#### 이상 탐지 설정 방법

1. QuickSight 분석에서 시계열 시각화(라인 차트 등)를 생성합니다.
2. 시각화 메뉴에서 "Insights" 탭을 선택합니다.
3. "Anomaly detection" 인사이트를 추가합니다.
4. 분석할 측정값, 차원, 시간 범위를 설정합니다.
5. 이상 탐지 감도(민감도)를 조절합니다.

#### 감도 설정

감도는 Low, Medium, High, Very High, Custom 중에서 선택할 수 있습니다. 높은 감도를 설정하면 더 많은 이상이 탐지되지만 오탐(False Positive)의 가능성도 높아집니다. 비즈니스 요구사항에 따라 적절한 감도를 선택해야 합니다.

### 2. 예측 (Forecasting)

QuickSight의 예측 기능은 시계열 데이터의 패턴을 학습하여 미래 값을 예측합니다. 계절성(Seasonality), 트렌드(Trend) 등을 자동으로 감지하여 예측 모델을 생성합니다.

#### 주요 특징

- **자동 모델 선택**: 데이터의 특성에 따라 최적의 예측 모델을 자동으로 선택합니다.
- **신뢰 구간**: 예측 결과에 대한 신뢰 구간(Confidence Interval)을 함께 표시합니다.
- **계절성 자동 감지**: 일별, 주별, 월별, 연별 계절성 패턴을 자동으로 감지합니다.
- **사용자 정의 기간**: 예측 기간을 사용자가 자유롭게 설정할 수 있습니다.

```bash
# 예측 기능이 포함된 분석 조회
aws quicksight describe-analysis \
  --aws-account-id 123456789012 \
  --analysis-id sales-forecast-analysis \
  --query 'Analysis.{Name:Name,Status:Status,Sheets:Sheets[].Name}'

# 분석을 대시보드로 퍼블리싱 (예측 인사이트 포함)
aws quicksight create-dashboard \
  --aws-account-id 123456789012 \
  --dashboard-id forecast-dashboard \
  --name "Sales Forecast Dashboard" \
  --source-entity '{
    "SourceTemplate": {
      "DataSetReferences": [{
        "DataSetPlaceholder": "sales_data",
        "DataSetArn": "arn:aws:quicksight:ap-northeast-2:123456789012:dataset/sales-dataset"
      }],
      "Arn": "arn:aws:quicksight:ap-northeast-2:123456789012:template/forecast-template"
    }
  }'
```

#### 예측 설정 방법

1. 시간 축이 포함된 라인 차트를 생성합니다.
2. 시각화의 "Format Visual" 설정에서 "Forecast" 항목을 활성화합니다.
3. 예측 기간(Periods Forward), 계절 수(Seasonal Periods), 신뢰 구간(Prediction Interval)을 설정합니다.

### 3. 자동 서술 (Auto-Narratives)

자동 서술 기능은 데이터의 핵심 인사이트를 자연어 문장으로 자동 생성합니다. 대시보드에 텍스트 기반의 요약을 추가하여, 비전문가도 데이터의 의미를 쉽게 이해할 수 있도록 도와줍니다.

#### 주요 특징

- **동적 업데이트**: 필터나 매개변수가 변경되면 서술 내용도 자동으로 업데이트됩니다.
- **커스터마이징**: 기본 생성된 서술을 수정하거나, 계산 필드를 참조하는 커스텀 서술을 작성할 수 있습니다.
- **다국어 지원**: 영어를 기본으로 지원하며, 한국어 등 다양한 언어로도 서술을 생성할 수 있습니다.

### 4. 기여도 분석 (Contribution Analysis)

이상이 탐지되었을 때, 어떤 차원(Dimension)이 해당 이상에 가장 크게 기여했는지 자동으로 분석합니다. 예를 들어, 매출이 급감한 경우 어떤 지역, 제품 카테고리, 채널이 원인인지 파악할 수 있습니다.

#### 분석 프로세스

1. 이상 탐지에서 이상 포인트가 발견됩니다.
2. 시스템이 자동으로 모든 차원 조합을 분석합니다.
3. 각 차원별 기여도를 계산하여 순위를 매깁니다.
4. 상위 기여 요인을 사용자에게 시각적으로 제시합니다.

### 5. Amazon Q in QuickSight

Amazon Q 통합은 생성형 AI를 활용한 자연어 데이터 분석 기능입니다.

- **자연어 질의**: "지난 분기 대비 매출 성장률은?" 같은 자연어 질문에 답변합니다.
- **시각화 자동 생성**: 질문의 맥락에 맞는 시각화를 자동으로 생성합니다.
- **데이터 스토리**: 데이터 인사이트를 기반으로 프레젠테이션 자료를 자동 생성합니다.
- **Executive Summary**: 대시보드의 핵심 인사이트를 요약 보고서로 자동 생성합니다.

## 아키텍처/동작 원리

### Random Cut Forest (RCF) 알고리즘

QuickSight의 이상 탐지에 사용되는 RCF 알고리즘은 Amazon이 개발한 비지도 학습 알고리즘입니다.

#### 동작 원리

1. **트리 구축**: 데이터 포인트를 무작위로 선택하고, 무작위 차원과 분할 점을 사용하여 이진 트리를 구축합니다.
2. **포레스트 구성**: 여러 개의 트리를 구성하여 포레스트를 형성합니다.
3. **이상 점수 계산**: 새로운 데이터 포인트가 트리에 삽입될 때, 트리 구조의 변화 정도(displacement)를 기반으로 이상 점수를 계산합니다.
4. **임계값 적용**: 이상 점수가 설정된 임계값(감도)을 초과하면 이상으로 판별합니다.

```
[시계열 데이터] --> [RCF 모델 학습] --> [이상 점수 계산] --> [기여도 분석]
       |                |                    |                  |
   SPICE에서      자동 트리 구축       임계값 비교         차원별 분석
   데이터 로드    (비지도 학습)        (감도 기반)        (Top-N 요인)
```

### 예측 모델

QuickSight의 예측 기능은 내부적으로 여러 시계열 예측 알고리즘을 사용합니다.

- **추세 분해(Trend Decomposition)**: 시계열 데이터를 추세, 계절성, 잔차로 분해합니다.
- **지수 평활법(Exponential Smoothing)**: 최근 데이터에 더 높은 가중치를 부여하는 예측 방법입니다.
- **ARIMA**: 자기회귀 이동평균 모델로 복잡한 시계열 패턴을 모델링합니다.

QuickSight는 이러한 알고리즘 중 데이터에 가장 적합한 것을 자동으로 선택하며, 사용자가 직접 알고리즘을 선택할 필요가 없습니다.

### SPICE와의 통합

ML Insights는 SPICE 엔진과 긴밀하게 통합되어 있습니다. SPICE에 데이터가 임포트되면 ML 모델이 자동으로 학습되고, 데이터 새로고침 시 모델도 함께 업데이트됩니다.

## 실전 활용

### 활용 사례 1: 전자상거래 매출 이상 탐지

전자상거래 플랫폼의 일별 매출 데이터에서 이상 패턴을 감지하고, 원인을 분석하는 대시보드를 구축합니다.

```bash
# 매출 데이터셋 생성 (S3에서 SPICE로 임포트)
aws quicksight create-data-set \
  --aws-account-id 123456789012 \
  --data-set-id ecommerce-sales \
  --name "E-Commerce Sales Data" \
  --import-mode SPICE \
  --physical-table-map '{
    "s3-sales": {
      "S3Source": {
        "DataSourceArn": "arn:aws:quicksight:ap-northeast-2:123456789012:datasource/s3-source",
        "InputColumns": [
          {"Name": "date", "Type": "STRING"},
          {"Name": "category", "Type": "STRING"},
          {"Name": "region", "Type": "STRING"},
          {"Name": "channel", "Type": "STRING"},
          {"Name": "revenue", "Type": "DECIMAL"},
          {"Name": "orders", "Type": "INTEGER"}
        ],
        "UploadSettings": {
          "Format": "CSV",
          "StartFromRow": 1,
          "ContainsHeader": true,
          "Delimiter": ","
        }
      }
    }
  }'
```

#### 이상 탐지 구성 예시

- **측정값**: 일별 매출(revenue), 주문 수(orders)
- **차원**: 카테고리(category), 지역(region), 채널(channel)
- **감도**: Medium (비즈니스 임팩트가 큰 이상만 필터링)
- **기여도 분석**: 이상 발생 시 카테고리, 지역, 채널별 기여도 자동 분석

### 활용 사례 2: 재고 수요 예측

과거 판매 데이터를 기반으로 향후 30일간의 제품별 수요를 예측하여 재고 관리에 활용합니다.

#### 예측 설정

- **예측 기간**: 30일 (Periods Forward: 30)
- **계절 수**: 7 (주간 패턴 반영)
- **신뢰 구간**: 80% (Prediction Interval: 80)
- **집계 단위**: 일별 (Day)

### 활용 사례 3: KPI 대시보드에 자동 서술 추가

경영진 대시보드에 자동 서술을 추가하여, 주요 KPI의 변동 사항을 자연어로 요약합니다.

```bash
# 대시보드 목록 조회
aws quicksight list-dashboards \
  --aws-account-id 123456789012 \
  --query 'DashboardSummaryList[].{Name:Name,DashboardId:DashboardId,LastPublished:LastPublishedTime}' \
  --output table

# 대시보드 권한 설정 (경영진 그룹에 접근 권한 부여)
aws quicksight update-dashboard-permissions \
  --aws-account-id 123456789012 \
  --dashboard-id executive-kpi-dashboard \
  --grant-permissions '[{
    "Principal": "arn:aws:quicksight:ap-northeast-2:123456789012:group/default/executives",
    "Actions": [
      "quicksight:DescribeDashboard",
      "quicksight:ListDashboardVersions",
      "quicksight:QueryDashboard"
    ]
  }]'
```

### 활용 사례 4: 마케팅 캠페인 효과 분석

마케팅 캠페인 전후의 지표 변화를 이상 탐지와 예측 기능으로 분석하여, 캠페인의 실제 효과를 정량적으로 측정합니다.

- **기준선 설정**: 캠페인 이전 데이터로 예측 모델을 생성하여 기준선을 설정합니다.
- **효과 측정**: 실제 값과 예측 값의 차이를 캠페인 효과로 측정합니다.
- **이상 탐지**: 캠페인 기간 동안의 이상적인 증가를 자동으로 감지합니다.

## 모범 사례/보안

### ML Insights 활용 모범 사례

1. **충분한 데이터 확보**: 이상 탐지와 예측 모두 충분한 과거 데이터가 필요합니다. 최소 2주 이상의 데이터를 권장하며, 계절성을 정확히 포착하려면 최소 2개 주기 이상의 데이터가 필요합니다.

2. **적절한 감도 설정**: 이상 탐지의 감도는 비즈니스 요구사항에 맞게 조절합니다. 처음에는 Medium으로 시작하고, 결과를 검토하면서 조절하는 것을 권장합니다.

3. **차원 선택 최적화**: 기여도 분석에 사용할 차원은 비즈니스적으로 의미 있는 것들만 포함합니다. 너무 많은 차원을 추가하면 분석 시간이 길어지고 결과의 해석이 어려워집니다.

4. **데이터 품질 관리**: ML 모델의 결과는 입력 데이터의 품질에 크게 의존합니다. 결측값, 이상 입력값, 데이터 형식 오류 등을 사전에 정리합니다.

5. **정기적인 모델 검증**: ML Insights의 결과를 주기적으로 검증하고, 비즈니스 컨텍스트와 일치하는지 확인합니다.

### 보안 고려사항

1. **데이터 접근 제어**: RLS/CLS를 적용하여 ML Insights 결과도 사용자별 접근 권한에 맞게 필터링되도록 합니다.
2. **감사 로그**: CloudTrail을 통해 ML Insights 기능의 사용 이력을 추적합니다.
3. **민감 데이터 처리**: ML 분석에 사용되는 데이터에 개인정보가 포함되지 않도록 데이터셋 구성 시 주의합니다.

```bash
# CloudTrail에서 QuickSight ML 관련 이벤트 조회
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=quicksight.amazonaws.com \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-31T23:59:59Z \
  --query 'Events[?contains(EventName, `Insight`) || contains(EventName, `Dashboard`)].{Time:EventTime,Event:EventName,User:Username}' \
  --output table
```

## 관련 서비스 비교

| 항목 | QuickSight ML Insights | Amazon SageMaker Canvas | Amazon Forecast | Amazon Lookout for Metrics |
|------|----------------------|------------------------|-----------------|---------------------------|
| 대상 사용자 | 비즈니스 사용자 | 비즈니스 분석가 | 개발자/분석가 | 개발자/운영팀 |
| ML 전문성 | 불필요 | 불필요 | 중간 | 중간 |
| 이상 탐지 | 지원 (RCF) | 미지원 | 미지원 | 지원 (다양한 알고리즘) |
| 예측 | 지원 (자동) | 지원 (No-Code) | 지원 (고급) | 미지원 |
| 시각화 | 내장 대시보드 | Canvas UI | 외부 연동 필요 | 콘솔/API |
| 커스터마이징 | 제한적 | 중간 | 높음 | 중간 |
| 비용 | QuickSight에 포함 | 별도 과금 | 별도 과금 | 별도 과금 |
| 적합한 용도 | 대시보드 내 인사이트 | No-Code ML | 정밀 수요 예측 | 지표 모니터링 |

### 선택 기준

- **QuickSight ML Insights**: 대시보드에서 바로 ML 인사이트를 확인하고 싶은 경우에 적합합니다. 별도의 ML 파이프라인 없이 빠르게 인사이트를 얻을 수 있습니다.
- **Amazon SageMaker Canvas**: 코드 없이 커스텀 ML 모델을 구축하고 싶은 경우에 적합합니다.
- **Amazon Forecast**: 수요 예측, 재고 계획 등 정밀한 예측이 필요한 경우에 적합합니다.
- **Amazon Lookout for Metrics**: 다양한 비즈니스 지표를 종합적으로 모니터링하고 이상을 탐지해야 하는 경우에 적합합니다.

## 요약

Amazon QuickSight ML Insights는 비즈니스 사용자가 ML 전문 지식 없이도 고급 분석을 수행할 수 있게 해주는 강력한 기능입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **이상 탐지**: RCF 알고리즘 기반의 비지도 학습으로 데이터의 이상 패턴을 자동 감지합니다.
- **기여도 분석**: 이상의 원인이 되는 주요 차원을 자동으로 식별하여, 신속한 원인 분석이 가능합니다.
- **예측**: 시계열 데이터의 트렌드와 계절성을 자동으로 학습하여 미래 값을 예측합니다.
- **자동 서술**: 데이터의 핵심 인사이트를 자연어로 요약하여 비전문가의 이해를 돕습니다.
- **Amazon Q 통합**: 생성형 AI를 통해 자연어로 데이터를 질의하고 분석할 수 있습니다.
- **추가 비용 없음**: Enterprise 에디션에 기본 포함되어 별도의 ML 서비스 비용이 발생하지 않습니다.

ML Insights는 별도의 ML 파이프라인을 구축하지 않고도 빠르게 데이터 인사이트를 얻고 싶은 조직에게 매우 유용한 기능입니다. 다만, 정밀한 예측이나 고급 커스터마이징이 필요한 경우에는 Amazon Forecast나 SageMaker와 같은 전용 ML 서비스를 함께 활용하는 것을 권장합니다.