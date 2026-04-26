<!-- infographic-hero -->
![Amazon SageMaker Notebook 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker Notebook 한 장 요약 인포그래픽*

# Amazon SageMaker Notebook

## 개요

Amazon SageMaker Notebook Instances는 Jupyter 노트북 환경을 제공하는 완전 관리형 ML 개발 인스턴스입니다. 데이터 탐색, 모델 프로토타이핑, 실험, 그리고 SageMaker의 다양한 서비스를 활용하기 위한 통합 개발 환경으로, ML 프로젝트의 시작점 역할을 합니다.

전통적으로 ML 개발 환경을 구축하려면 GPU 드라이버 설치, CUDA 설정, 프레임워크 호환성 관리, Jupyter 서버 설정 등 수많은 사전 작업이 필요합니다. SageMaker Notebook Instances는 이 모든 과정을 자동화하여, 인스턴스를 생성하는 즉시 완전히 구성된 ML 개발 환경을 사용할 수 있습니다.

SageMaker Notebook Instances가 제공하는 핵심 가치는 다음과 같습니다.

- **사전 구성된 환경**: TensorFlow, PyTorch, MXNet, Scikit-learn 등 주요 ML 프레임워크가 사전 설치되어 있습니다.
- **유연한 인스턴스 선택**: CPU부터 고성능 GPU까지 다양한 인스턴스 타입을 필요에 따라 선택할 수 있습니다.
- **영구 스토리지**: EBS 볼륨을 통해 노트북과 데이터를 인스턴스 중지 후에도 유지할 수 있습니다.
- **SageMaker 통합**: SageMaker의 훈련, 배포, 파이프라인 등 모든 기능을 노트북에서 직접 활용할 수 있습니다.
- **보안**: IAM, VPC, KMS 등 AWS 보안 서비스와 통합됩니다.

참고로 SageMaker Notebook Instance는 SageMaker Studio와는 별개의 서비스입니다. Studio는 웹 기반 IDE로서 더 풍부한 기능을 제공하지만, Notebook Instance는 전통적인 Jupyter 환경을 선호하는 사용자에게 적합합니다.

## 핵심 기능

### 1. 인스턴스 생성 및 구성

Notebook Instance를 생성할 때 다양한 옵션을 설정할 수 있습니다.

```bash
# Notebook Instance 생성
aws sagemaker create-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --instance-type ml.t3.medium \
  --role-arn "arn:aws:iam::123456789012:role/SageMakerNotebookRole" \
  --volume-size-in-gb 50 \
  --default-code-repository "https://github.com/myorg/ml-project.git" \
  --root-access Enabled \
  --platform-identifier "notebook-al2-v2" \
  --region us-east-1

# 생성 상태 확인
aws sagemaker describe-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --region us-east-1 \
  --query '{Status: NotebookInstanceStatus, InstanceType: InstanceType, Url: Url}'
```

### 2. 인스턴스 타입 선택 가이드

사용 목적에 따라 적절한 인스턴스 타입을 선택하는 것이 중요합니다.

**데이터 탐색/전처리 (CPU)**:
- `ml.t3.medium`: 경량 작업, 비용 효율적 (2 vCPU, 4GB RAM)
- `ml.t3.xlarge`: 중간 규모 데이터셋 (4 vCPU, 16GB RAM)
- `ml.m5.4xlarge`: 대규모 데이터 전처리 (16 vCPU, 64GB RAM)

**모델 프로토타이핑 (GPU)**:
- `ml.g4dn.xlarge`: 기본 딥러닝 개발 (T4 GPU, 16GB GPU RAM)
- `ml.g5.xlarge`: 중간 규모 모델 (A10G GPU, 24GB GPU RAM)
- `ml.p3.2xlarge`: 대규모 모델 (V100 GPU, 16GB GPU RAM)

**대규모 실험 (Multi-GPU)**:
- `ml.g5.12xlarge`: 4x A10G GPU
- `ml.p3.8xlarge`: 4x V100 GPU

### 3. 라이프사이클 설정(Lifecycle Configuration)

라이프사이클 설정을 통해 인스턴스 생성/시작 시 자동으로 실행되는 스크립트를 정의할 수 있습니다. 환경 커스터마이징, 패키지 설치, 자동 종료 등에 활용됩니다.

```bash
# 라이프사이클 설정 생성
aws sagemaker create-notebook-instance-lifecycle-config \
  --notebook-instance-lifecycle-config-name "ml-dev-lifecycle" \
  --on-create Content=$(cat <<'SCRIPT' | base64
#!/bin/bash
set -e

# 추가 Python 패키지 설치
sudo -u ec2-user -i <<'EOF'
pip install transformers datasets accelerate
pip install wandb mlflow
pip install plotly dash
EOF

# Git 설정
sudo -u ec2-user -i <<'EOF'
git config --global user.name "ML Developer"
git config --global user.email "dev@example.com"
EOF

echo "OnCreate 설정 완료"
SCRIPT
) \
  --on-start Content=$(cat <<'SCRIPT' | base64
#!/bin/bash
set -e

# 자동 종료 스크립트 설정 (1시간 유휴 시)
IDLE_TIME=3600

echo "#!/bin/bash
while true; do
    IDLE_SECONDS=\$(cat /proc/uptime | awk '{print \$2}' | cut -d. -f1)
    if [ \$IDLE_SECONDS -gt $IDLE_TIME ]; then
        echo 'Notebook idle, stopping instance'
        aws sagemaker stop-notebook-instance --notebook-instance-name ml-dev-notebook
        break
    fi
    sleep 300
done" > /home/ec2-user/auto-stop.sh
chmod +x /home/ec2-user/auto-stop.sh
nohup /home/ec2-user/auto-stop.sh &

echo "OnStart 설정 완료"
SCRIPT
) \
  --region us-east-1

# 라이프사이클 설정을 Notebook Instance에 연결
aws sagemaker update-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --lifecycle-config-name "ml-dev-lifecycle" \
  --region us-east-1
```

### 4. Git 리포지토리 통합

Notebook Instance에 Git 리포지토리를 연결하여 코드 버전 관리를 수행할 수 있습니다.

```bash
# Git 리포지토리 등록
aws sagemaker create-code-repository \
  --code-repository-name "ml-project-repo" \
  --git-config '{
    "RepositoryUrl": "https://github.com/myorg/ml-project.git",
    "Branch": "main",
    "SecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:github-token"
  }' \
  --region us-east-1

# Notebook Instance에 연결
aws sagemaker update-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --default-code-repository "ml-project-repo" \
  --additional-code-repositories "ml-utils-repo" "ml-data-repo" \
  --region us-east-1
```

### 5. 커스텀 커널 관리

Jupyter 노트북에서 사용할 커스텀 커널을 생성할 수 있습니다.

```python
# 커스텀 conda 환경 생성 스크립트 (라이프사이클에서 실행)
# on-create.sh 에 포함
custom_env_script = """
#!/bin/bash
sudo -u ec2-user -i <<'EOF'

# NLP 전용 환경 생성
conda create -n nlp-env python=3.10 -y
source activate nlp-env
pip install transformers datasets tokenizers sentencepiece
pip install torch torchvision torchaudio
pip install ipykernel
python -m ipykernel install --user --name nlp-env --display-name "Python (NLP)"

# CV 전용 환경 생성
conda create -n cv-env python=3.10 -y
source activate cv-env
pip install torch torchvision timm albumentations
pip install opencv-python-headless pillow
pip install ipykernel
python -m ipykernel install --user --name cv-env --display-name "Python (CV)"

EOF
"""
```

## 아키텍처/동작 원리

### Notebook Instance 내부 구조

Notebook Instance는 내부적으로 다음과 같은 구조로 동작합니다.

1. **EC2 인스턴스**: 선택한 인스턴스 타입의 EC2 인스턴스가 프로비저닝됩니다. SageMaker가 관리하는 VPC 내에서 실행됩니다.

2. **EBS 볼륨**: `/home/ec2-user/SageMaker/` 디렉토리에 마운트되는 EBS 볼륨입니다. 이 볼륨은 인스턴스를 중지해도 유지되며, 노트북 파일, 데이터, 커스텀 환경 등이 저장됩니다.

3. **Jupyter 서버**: JupyterLab과 클래식 Jupyter Notebook 서버가 실행되며, HTTPS를 통해 접근합니다.

4. **사전 설치 환경**: Amazon Linux 2 기반으로, Anaconda 배포판과 여러 conda 환경이 사전 구성되어 있습니다.

5. **SageMaker SDK**: boto3와 SageMaker Python SDK가 사전 설치되어 있어, 노트북에서 직접 SageMaker 서비스를 호출할 수 있습니다.

### 네트워크 아키텍처

기본적으로 Notebook Instance는 SageMaker 관리형 VPC에서 실행되며, 인터넷에 접근할 수 있습니다. 보안이 중요한 환경에서는 사용자의 VPC 내에 배치하고, 인터넷 접근을 차단할 수 있습니다.

```
[사용자 브라우저]
      |
    HTTPS (presigned URL)
      |
[SageMaker API] --> [Notebook Instance]
                          |
                    [EBS Volume] -- /home/ec2-user/SageMaker/
                          |
                    [VPC/Subnet] -- 선택적 VPC 설정
                          |
                    [S3, SageMaker API] -- AWS 서비스 접근
```

### 인스턴스 상태 관리

Notebook Instance는 다음과 같은 상태를 가집니다.

- **InService**: 실행 중 (과금 발생)
- **Stopped**: 중지됨 (EBS 볼륨 비용만 발생)
- **Pending**: 시작 중
- **Stopping**: 중지 중
- **Updating**: 설정 업데이트 중
- **Failed**: 시작 실패

```bash
# 인스턴스 상태 확인
aws sagemaker describe-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --region us-east-1 \
  --query '{Status: NotebookInstanceStatus, InstanceType: InstanceType, VolumeSizeInGB: VolumeSizeInGB}'

# 인스턴스 시작
aws sagemaker start-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --region us-east-1

# 인스턴스 중지
aws sagemaker stop-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --region us-east-1
```

## 실전 활용

### 사례 1: 데이터 과학 팀의 표준 노트북 환경 구축

팀 전체에서 일관된 개발 환경을 사용할 수 있도록 표준화된 Notebook Instance를 구성합니다.

```python
import boto3
import base64

sm_client = boto3.client('sagemaker')

# 표준 라이프사이클 스크립트
on_create_script = """#!/bin/bash
set -e

# 팀 표준 패키지 설치
sudo -u ec2-user -i <<'EOF'
pip install --upgrade pip
pip install pandas numpy scikit-learn matplotlib seaborn
pip install boto3 sagemaker
pip install jupyter-contrib-nbextensions
jupyter contrib nbextension install --user

# JupyterLab 확장 설치
pip install jupyterlab-git jupyterlab-lsp

# 팀 공용 유틸리티 설치
pip install git+https://github.com/myorg/ml-utils.git
EOF
"""

on_start_script = """#!/bin/bash
set -e

# 자동 종료 설정 (2시간 유휴 시)
WAGE_TIMEOUT=7200
echo "자동 종료 타이머 설정: ${WAGE_TIMEOUT}초"

# S3에서 최신 설정 동기화
sudo -u ec2-user -i <<'EOF'
aws s3 sync s3://team-config/notebook-setup/ ~/SageMaker/.config/ --quiet
EOF
"""

# 라이프사이클 설정 생성
sm_client.create_notebook_instance_lifecycle_config(
    NotebookInstanceLifecycleConfigName='team-standard-lifecycle',
    OnCreate=[{
        'Content': base64.b64encode(on_create_script.encode()).decode()
    }],
    OnStart=[{
        'Content': base64.b64encode(on_start_script.encode()).decode()
    }]
)

# 팀원별 Notebook Instance 생성
team_members = [
    {'name': 'ds-alice', 'instance': 'ml.t3.xlarge'},
    {'name': 'ds-bob', 'instance': 'ml.g4dn.xlarge'},
    {'name': 'ds-charlie', 'instance': 'ml.t3.medium'}
]

for member in team_members:
    sm_client.create_notebook_instance(
        NotebookInstanceName=member['name'],
        InstanceType=member['instance'],
        RoleArn='arn:aws:iam::123456789012:role/SageMakerNotebookRole',
        LifecycleConfigName='team-standard-lifecycle',
        VolumeSizeInGB=100,
        RootAccess='Disabled',
        Tags=[
            {'Key': 'Team', 'Value': 'data-science'},
            {'Key': 'Owner', 'Value': member['name']}
        ]
    )
    print(f"인스턴스 생성: {member['name']} ({member['instance']})")
```

### 사례 2: GPU 인스턴스를 활용한 모델 프로토타이핑

```python
# Notebook 내에서 실행하는 모델 프로토타이핑 코드
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import sagemaker

# GPU 사용 가능 여부 확인
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"사용 디바이스: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU 메모리: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")

# 간단한 모델 프로토타이핑
model = nn.Sequential(
    nn.Linear(784, 256),
    nn.ReLU(),
    nn.Dropout(0.2),
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Dropout(0.2),
    nn.Linear(128, 10)
).to(device)

print(f"모델 파라미터 수: {sum(p.numel() for p in model.parameters()):,}")

# 프로토타이핑이 완료되면 SageMaker Training Job으로 전환
from sagemaker.pytorch import PyTorch

estimator = PyTorch(
    entry_point='train.py',
    source_dir='./src',
    role=sagemaker.get_execution_role(),
    instance_count=1,
    instance_type='ml.p3.2xlarge',
    framework_version='2.0',
    py_version='py310',
    hyperparameters={
        'epochs': 50,
        'batch_size': 128,
        'learning_rate': 0.001
    }
)

# 대규모 훈련은 Training Job으로 실행
estimator.fit({'training': 's3://my-bucket/data/train/'})
```

### 사례 3: 비용 관리를 위한 자동 종료 설정

```bash
# 모든 실행 중인 Notebook Instance 목록 확인
aws sagemaker list-notebook-instances \
  --status-equals InService \
  --region us-east-1 \
  --query 'NotebookInstances[].{Name: NotebookInstanceName, Type: InstanceType, Created: CreationTime}' \
  --output table

# 특정 인스턴스의 인스턴스 타입 변경 (중지 후)
aws sagemaker stop-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --region us-east-1

# 상태가 Stopped가 될 때까지 대기 후 인스턴스 타입 변경
aws sagemaker update-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --instance-type ml.g5.xlarge \
  --volume-size-in-gb 100 \
  --region us-east-1

# 변경된 인스턴스 타입으로 재시작
aws sagemaker start-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --region us-east-1
```

## 모범 사례/보안

### 보안 모범 사례

1. **Root 접근 비활성화**: 프로덕션 환경에서는 `RootAccess`를 `Disabled`로 설정합니다.

2. **VPC 내 배치**: 민감한 데이터를 다루는 경우 Notebook Instance를 프라이빗 서브넷에 배치합니다.

3. **Direct Internet Access 비활성화**: VPC 내에서 NAT Gateway 또는 VPC Endpoint를 통해서만 인터넷에 접근하도록 합니다.

4. **EBS 볼륨 암호화**: KMS 키를 사용하여 EBS 볼륨을 암호화합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "NotebookMinimalAccess",
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreatePresignedNotebookInstanceUrl",
        "sagemaker:StartNotebookInstance",
        "sagemaker:StopNotebookInstance",
        "sagemaker:DescribeNotebookInstance"
      ],
      "Resource": "arn:aws:sagemaker:us-east-1:123456789012:notebook-instance/${aws:PrincipalTag/NotebookName}"
    },
    {
      "Sid": "DenyLargeInstances",
      "Effect": "Deny",
      "Action": "sagemaker:CreateNotebookInstance",
      "Resource": "*",
      "Condition": {
        "ForAnyValue:StringLike": {
          "sagemaker:InstanceTypes": ["ml.p3*", "ml.p4*"]
        }
      }
    }
  ]
}
```

### 비용 최적화 모범 사례

1. **자동 종료 설정**: 라이프사이클 스크립트로 유휴 시 자동 종료를 구현합니다.
2. **적절한 인스턴스 크기**: 작업 요구사항에 맞는 최소 인스턴스를 선택합니다.
3. **인스턴스 타입 전환**: 탐색 작업에는 CPU, 훈련에는 GPU로 전환합니다.
4. **대규모 훈련은 Training Job 사용**: Notebook에서 직접 훈련하지 말고 SageMaker Training Job을 활용합니다.
5. **EBS 볼륨 크기 최적화**: 필요 이상으로 큰 볼륨을 할당하지 않습니다.

```bash
# 비용 관련 태그가 없는 인스턴스 확인
aws sagemaker list-notebook-instances \
  --region us-east-1 \
  --query 'NotebookInstances[].NotebookInstanceName' \
  --output text
```

## 관련 서비스 비교

### Notebook Instance vs SageMaker Studio

| 항목 | Notebook Instance | SageMaker Studio |
|------|-------------------|------------------|
| 환경 | 전통적 Jupyter | 웹 기반 IDE |
| 인스턴스 관리 | 사용자가 직접 | 자동 (커널별 인스턴스) |
| 협업 | 제한적 | 공유 공간 지원 |
| 비용 | 인스턴스 상시 과금 | 사용 시에만 과금 |
| 커스터마이징 | 라이프사이클 스크립트 | Docker 이미지 |
| SageMaker 통합 | SDK 기반 | UI 통합 |
| 적합한 사용자 | Jupyter 숙련자 | 팀 단위 협업 |

### Notebook Instance vs EC2 + Jupyter

| 항목 | Notebook Instance | EC2 + Jupyter |
|------|-------------------|---------------|
| 설정 복잡도 | 낮음 (원클릭) | 높음 (직접 설정) |
| ML 프레임워크 | 사전 설치 | 직접 설치 |
| SageMaker 통합 | 네이티브 | 수동 설정 |
| 비용 | SageMaker 요금 | EC2 요금 (약간 저렴) |
| 유연성 | 제한적 | 완전한 제어 |

### Notebook Instance vs Google Colab

| 항목 | Notebook Instance | Google Colab |
|------|-------------------|-------------|
| 비용 | 유료 (인스턴스 기반) | 무료 티어 있음 |
| GPU 접근 | 보장 (선택 가능) | 제한적 (가용성에 따라) |
| 실행 시간 | 무제한 | 최대 12시간 |
| 데이터 보안 | AWS 보안 (VPC 등) | Google 관리 |
| 스토리지 | 영구 EBS | 세션 종료 시 삭제 |
| AWS 통합 | 네이티브 | 추가 설정 필요 |

## 요약

Amazon SageMaker Notebook Instances는 ML 개발을 위한 완전 관리형 Jupyter 환경입니다. 주요 내용을 정리하면 다음과 같습니다.

- 사전 구성된 ML 프레임워크와 도구가 설치되어 있어 즉시 개발을 시작할 수 있습니다.
- 작업 유형에 따라 CPU(데이터 탐색)부터 GPU(모델 프로토타이핑)까지 인스턴스 타입을 유연하게 선택할 수 있습니다.
- 라이프사이클 스크립트를 통해 환경 커스터마이징, 자동 종료, 패키지 설치 등을 자동화할 수 있습니다.
- Git 리포지토리를 연결하여 코드 버전 관리를 수행할 수 있습니다.
- EBS 볼륨은 인스턴스 중지 후에도 유지되므로, 작업 중인 데이터와 노트북이 보존됩니다.
- 보안을 위해 Root 접근 비활성화, VPC 내 배치, EBS 암호화를 적용하는 것이 중요합니다.
- 비용 최적화를 위해 자동 종료 설정, 적절한 인스턴스 선택, 대규모 훈련의 Training Job 전환이 필수적입니다.
- 팀 단위 협업이 필요한 경우 SageMaker Studio로의 전환을 검토하는 것을 권장합니다.

Notebook Instance는 개인 ML 개발 환경으로서 여전히 유효한 선택이며, 특히 전통적인 Jupyter 환경을 선호하거나, 간단한 프로토타이핑과 실험을 빠르게 수행해야 하는 상황에 적합합니다.