# Amazon SageMaker Studio Classic - 레거시 ML 통합 개발 환경

## 개요

Amazon SageMaker Studio Classic은 SageMaker의 첫 번째 세대 통합 ML 개발 환경입니다. 커스텀 JupyterLab 3를 기반으로 구축되었으며, 데이터 준비부터 모델 배포까지 전체 ML 워크플로우를 웹 브라우저에서 수행할 수 있는 환경을 제공합니다.

2023년 말 신규 SageMaker Studio가 출시되면서, Studio Classic은 레거시 환경으로 분류되었습니다. AWS는 기존 Studio Classic 사용자에게 신규 Studio로의 마이그레이션을 권장하고 있으며, 마이그레이션 도구와 가이드를 제공합니다.

Studio Classic과 신규 Studio의 핵심 차이점은 아키텍처에 있습니다. Studio Classic은 사용자별 단일 EFS 볼륨을 공유하는 구조인 반면, 신규 Studio는 Space별 독립 EBS 볼륨을 사용하여 격리성과 성능이 개선되었습니다.

## 핵심 기능

### 커스텀 JupyterLab 환경

Studio Classic은 JupyterLab 3를 AWS 서비스와 깊이 통합하여 커스터마이징한 환경을 제공합니다. 왼쪽 사이드바에서 SageMaker 리소스(Experiments, Endpoints, Models 등)를 직접 탐색하고 관리할 수 있습니다.

### Kernel Gateway Apps

Studio Classic에서는 노트북 커널이 별도의 컨테이너(Kernel Gateway App)에서 실행됩니다. 각 커널 이미지는 사전 구성된 ML 프레임워크와 라이브러리를 포함합니다.

| 이미지 유형 | 포함 프레임워크 | 인스턴스 유형 |
|------------|---------------|-------------|
| Data Science 3.0 | pandas, scikit-learn, matplotlib | CPU |
| TensorFlow 2.x | TensorFlow, Keras | CPU/GPU |
| PyTorch 2.x | PyTorch, torchvision | CPU/GPU |
| MXNet 1.x | Apache MXNet | CPU/GPU |
| SparkMagic | PySpark (EMR 연동) | CPU |

### EFS 기반 영구 스토리지

각 사용자에게 Amazon EFS(Elastic File System) 볼륨이 할당됩니다. 노트북 파일, 코드, 데이터셋 등이 EFS에 저장되어 커널을 변경하거나 인스턴스를 종료해도 데이터가 유지됩니다.

### SageMaker 서비스 통합

Studio Classic 인터페이스에서 다음 서비스에 직접 접근할 수 있습니다.

- SageMaker Experiments: 실험 추적 및 비교 시각화
- SageMaker Debugger: 훈련 작업 디버깅 및 프로파일링
- SageMaker Model Monitor: 배포된 모델 품질 모니터링
- SageMaker Pipelines: ML 워크플로우 DAG 시각화 및 실행
- SageMaker Feature Store: 특성 저장소 탐색
- SageMaker Data Wrangler: 시각적 데이터 전처리

## 아키텍처 및 동작 원리

Studio Classic의 내부 아키텍처는 다음과 같이 구성됩니다.

```
[SageMaker Domain]
    |
    +-- [User Profile]
            |
            +-- [JupyterServer App] (Studio UI 서빙)
            |       +-- ml.t3.medium (고정)
            |
            +-- [KernelGateway App 1] (Data Science 커널)
            |       +-- ml.t3.medium ~ ml.p3.16xlarge
            |       +-- EFS Mount (/home/sagemaker-user/)
            |
            +-- [KernelGateway App 2] (PyTorch 커널)
            |       +-- ml.g4dn.xlarge
            |       +-- EFS Mount (/home/sagemaker-user/)
            |
            +-- [Amazon EFS] (사용자별 영구 스토리지)
                    +-- /home/sagemaker-user/
```

JupyterServer App은 Studio UI를 서빙하는 경량 앱으로, ml.t3.medium에서 고정 실행됩니다. KernelGateway App은 실제 노트북 커널이 실행되는 컨테이너로, 사용자가 선택한 인스턴스 유형에서 실행됩니다. 여러 커널을 동시에 실행할 수 있으며, 각각 독립적인 인스턴스를 사용합니다.

EFS 볼륨은 모든 KernelGateway App에 동일한 경로(/home/sagemaker-user/)로 마운트되어, 커널 간 파일 공유가 자연스럽게 이루어집니다.

## 실전 활용

### AWS CLI를 사용한 Studio Classic Domain 설정

```bash
# Studio Classic Domain 생성
aws sagemaker create-domain \
    --domain-name ml-classic-studio \
    --auth-mode IAM \
    --default-user-settings '{
        "ExecutionRole": "arn:aws:iam::123456789012:role/SageMakerStudioRole",
        "SecurityGroups": ["sg-0abc123"]
    }' \
    --subnet-ids subnet-0abc123 subnet-0def456 \
    --vpc-id vpc-0abc123

# User Profile 생성
aws sagemaker create-user-profile \
    --domain-id d-abcdefg123 \
    --user-profile-name researcher-park

# Presigned URL 생성하여 Studio 접속
aws sagemaker create-presigned-domain-url \
    --domain-id d-abcdefg123 \
    --user-profile-name researcher-park \
    --query AuthorizedUrl --output text

# 실행 중인 앱 확인
aws sagemaker list-apps \
    --domain-id d-abcdefg123 \
    --user-profile-name researcher-park \
    --query 'Apps[].{Type:AppType,Name:AppName,Status:Status,Instance:ResourceSpec.InstanceType}' \
    --output table

# 유휴 커널 앱 종료 (비용 절감)
aws sagemaker delete-app \
    --domain-id d-abcdefg123 \
    --user-profile-name researcher-park \
    --app-type KernelGateway \
    --app-name datascience-1-0-ml-t3-medium-1234567890
```

### Lifecycle Configuration으로 자동 설정

```bash
# Studio Classic용 Lifecycle Config 생성
aws sagemaker create-studio-lifecycle-config \
    --studio-lifecycle-config-name classic-auto-shutdown \
    --studio-lifecycle-config-content $(cat << 'EOF' | base64
#!/bin/bash
set -e
# 자동 종료 확장 설치 (유휴 시간 기반)
IDLE_TIME=3600  # 1시간
pip install sagemaker-studio-auto-shutdown-extension
jlpm config set "@jupyterlab/notebook-extension:tracker" '{"shutdownTimeout": '$IDLE_TIME'}'
echo "Auto-shutdown configured: ${IDLE_TIME}s idle timeout"
EOF
) \
    --studio-lifecycle-config-app-type KernelGateway
```

### 신규 Studio로 마이그레이션

```bash
# 현재 Studio Classic 사용 현황 조회
aws sagemaker list-apps \
    --domain-id d-abcdefg123 \
    --query 'Apps[?AppType==`KernelGateway`].{User:UserProfileName,Instance:ResourceSpec.InstanceType,Status:Status}' \
    --output table

# EFS 데이터를 S3로 백업
aws s3 sync /home/sagemaker-user/ s3://my-bucket/studio-backup/ \
    --exclude ".local/*" \
    --exclude ".cache/*"

# Domain 설정을 신규 Studio로 업데이트
aws sagemaker update-domain \
    --domain-id d-abcdefg123 \
    --default-user-settings '{
        "StudioWebPortal": "ENABLED",
        "DefaultLandingUri": "studio::"
    }'
```

## 모범 사례 및 보안

### 비용 관리

- KernelGateway App은 실행 중인 동안 인스턴스 비용이 발생합니다. 사용하지 않는 커널을 적극적으로 종료합니다.
- Auto-shutdown 확장을 설치하여 유휴 커널을 자동 종료합니다. 기본 유휴 시간은 1시간을 권장합니다.
- EFS 볼륨에 불필요한 대용량 데이터를 저장하지 않습니다. 데이터셋은 S3에 보관하고 필요할 때 로드합니다.
- CloudWatch 메트릭과 AWS Budgets를 활용하여 Studio 사용 비용을 모니터링합니다.

### 보안

- VpcOnly 모드로 Domain을 생성하여 인터넷 직접 접근을 차단합니다.
- 보안 그룹으로 Studio 인스턴스 간 트래픽과 외부 접근을 제어합니다.
- IAM 역할에 최소 권한 원칙을 적용하고, 사용자별로 S3 버킷 접근 범위를 제한합니다.
- EFS 볼륨에 KMS 암호화를 적용하여 저장 데이터를 보호합니다.

### 마이그레이션 권장

- 신규 프로젝트는 반드시 신규 SageMaker Studio에서 시작합니다.
- 기존 Studio Classic 환경은 단계적으로 신규 Studio로 마이그레이션합니다.
- EFS 데이터를 S3로 백업한 후 신규 Studio의 EBS 볼륨으로 복원합니다.



### EFS 볼륨 관리 및 비용

Studio Classic의 EFS 볼륨은 사용자가 저장한 데이터 양에 따라 비용이 발생합니다. 노트북 파일, 데이터셋, 모델 체크포인트 등이 EFS에 누적되므로, 정기적으로 불필요한 파일을 정리하는 것이 중요합니다.

```bash
# EFS 사용량 확인 (Studio 터미널에서)
du -sh /home/sagemaker-user/*

# 대용량 파일 탐색
find /home/sagemaker-user -type f -size +100M -exec ls -lh {} \;

# 모델 체크포인트 정리 (오래된 것 삭제)
find /home/sagemaker-user/checkpoints -name "*.ckpt" -mtime +30 -delete
```

EFS 볼륨의 데이터는 사용자 프로필 삭제 시에만 완전히 제거됩니다. Domain을 삭제하더라도 EFS 볼륨은 별도로 관리해야 하므로 주의가 필요합니다.

### Custom Image 활용

Studio Classic에서는 커스텀 Docker 이미지를 KernelGateway 이미지로 등록하여 사용할 수 있습니다. 팀 공통 라이브러리와 환경을 표준화하는 데 유용합니다.

```bash
# 커스텀 이미지를 SageMaker Image로 등록
aws sagemaker create-image \
    --image-name custom-ds-image \
    --role-arn arn:aws:iam::123456789012:role/SageMakerStudioRole

# 이미지 버전 생성 (ECR 이미지 참조)
aws sagemaker create-image-version \
    --image-name custom-ds-image \
    --base-image 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/custom-ds:latest

# Domain에 커스텀 이미지 추가
aws sagemaker update-domain \
    --domain-id d-abcdefg123 \
    --default-user-settings '{
        "KernelGatewayAppSettings": {
            "CustomImages": [{
                "ImageName": "custom-ds-image",
                "ImageVersionNumber": 1,
                "AppImageConfigName": "custom-ds-config"
            }]
        }
    }'
```

### Git 연동 구성

Studio Classic에서 Git 저장소를 연동하면 코드 버전 관리와 팀 협업이 가능합니다.

```bash
# Git 저장소를 Domain에 연결
aws sagemaker create-code-repository \
    --code-repository-name team-ml-repo \
    --git-config '{
        "RepositoryUrl": "https://github.com/myorg/ml-experiments.git",
        "Branch": "main",
        "SecretArn": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:github-token"
    }'

# 사용자 프로필에 기본 저장소 설정
aws sagemaker update-user-profile \
    --domain-id d-abcdefg123 \
    --user-profile-name researcher-park \
    --user-settings '{
        "JupyterServerAppSettings": {
            "DefaultResourceSpec": {},
            "CodeRepositories": [{"RepositoryUrl": "https://github.com/myorg/ml-experiments.git"}]
        }
    }'
```

### SageMaker Experiments 통합

Studio Classic의 가장 강력한 기능 중 하나는 Experiments와의 시각적 통합입니다. 실험 결과를 차트로 비교하고, 최적의 하이퍼파라미터 조합을 찾는 작업을 GUI에서 수행할 수 있습니다.

```python
from sagemaker.experiments import Run

with Run(experiment_name="bert-classification", run_name="run-001") as run:
    run.log_parameter("learning_rate", 0.001)
    run.log_parameter("batch_size", 32)
    run.log_parameter("epochs", 10)
    
    for epoch in range(10):
        train_loss = train_one_epoch(model, train_loader)
        val_accuracy = evaluate(model, val_loader)
        run.log_metric("train_loss", train_loss, step=epoch)
        run.log_metric("val_accuracy", val_accuracy, step=epoch)
```

Studio Classic UI에서 Experiments 탭을 열면 모든 실행의 메트릭을 테이블과 차트로 비교할 수 있습니다.

## 관련 서비스 비교

| 항목 | Studio Classic | 신규 Studio | Notebook Instances |
|------|---------------|------------|-------------------|
| 기반 | 커스텀 JupyterLab 3 | JupyterLab 4 + Code Editor | 표준 Jupyter |
| 스토리지 | EFS (공유) | EBS (Space별 격리) | EBS (인스턴스별) |
| 커널 관리 | KernelGateway App | Space 내장 | 인스턴스 내장 |
| VS Code | 미지원 | Code Editor 내장 | 미지원 |
| 시작 시간 | 느림 (EFS 마운트) | 빠름 (EBS 직접 연결) | 보통 |
| 격리성 | 사용자 수준 | Space 수준 | 인스턴스 수준 |
| 상태 | 레거시 (마이그레이션 권장) | 권장 | 유지 |

## 요약

Amazon SageMaker Studio Classic은 첫 번째 세대 SageMaker 통합 ML 개발 환경으로, 커스텀 JupyterLab 3 기반에 EFS 영구 스토리지를 제공합니다. SageMaker의 주요 서비스(Experiments, Pipelines, Model Monitor 등)와 깊이 통합되어 있어 ML 워크플로우 전반을 단일 환경에서 관리할 수 있습니다. 다만, 2023년 출시된 신규 SageMaker Studio가 JupyterLab 4, Code Editor(VS Code), Space 기반 격리 등 다양한 개선을 제공하므로, 기존 Studio Classic 사용자는 신규 Studio로의 마이그레이션을 적극 검토하시기 바랍니다.