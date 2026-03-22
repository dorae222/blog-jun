---
title: SageMaker Script Mode
slug: "sagemaker-script-mode"
category: cloud
tags: ["aws", "distributed-training", "docker", "hyperparameters", "machine-learning", "pytorch", "sagemaker", "spot-instances", "tensorflow"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.721752+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - SageMaker Script Mode
---
## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | SageMaker Script Mode |
| **유형**           | 사전 제작된 **ML 프레임워크 컨테이너 + 사용자 스크립트 실행 모드** |
| **지원 프레임워크** | TensorFlow, PyTorch, MXNet, Hugging Face 등 |
| **목적**           | **사용자가 작성한 학습 스크립트를 SageMaker 제공 컨테이너에서 바로 실행**하여, Docker 이미지를 직접 만들지 않고도 학습 작업을 수행할 수 있음 |

---

## 🔧 동작 방식

1. **SageMaker 제공 프레임워크 컨테이너 선택**  
   예: TensorFlow, PyTorch 학습용 이미지
2. **사용자 학습 스크립트 업로드**  
   - 기존 로컬 학습 코드를 그대로 사용 가능  
   - `argparse`로 하이퍼파라미터를 받도록 구현하는 것을 권장
3. **SageMaker Estimator로 학습 실행**  
   - `entry_point`에 학습 스크립트 지정  
   - 데이터는 `/opt/ml/input/data`에 마운트되고,  
     모델 산출물은 `/opt/ml/model`에 저장됨
4. **분산 학습, 스팟 학습 등 SageMaker 기능과 연계 가능**

---

## 🧪 Python 예시

```python
from sagemaker.pytorch import PyTorch

estimator = PyTorch(
    entry_point='train.py',        # 사용자 학습 스크립트
    role='SageMakerRole',
    instance_type='ml.p3.2xlarge',
    framework_version='2.0',
    py_version='py310',
    hyperparameters={
        'epochs': 10,
        'batch_size': 32
    }
)

estimator.fit({'training': 's3://my-bucket/train-data'})
````

---

## ✅ 장점

- Docker 이미지를 직접 제작할 필요 없음
    
- 기존 로컬 학습 코드를 거의 그대로 활용 가능
    
- GPU/CPU 멀티 인스턴스 및 분산 학습 지원
    
- 스팟 인스턴스, 자동 확장 등 SageMaker 기능 활용 가능
    

---

## ⚠️ 유의사항

- 학습 스크립트는 SageMaker 컨테이너의 경로 규칙을 따라야 함  
    (`/opt/ml/input`·`/opt/ml/model` 등)
    
- 사용 가능한 프레임워크 및 Python 버전은 SageMaker에서 제공하는 범위 내에서 선택해야 함
    
- 하이퍼파라미터 처리를 위해 `argparse` 기반 코드를 권장
    

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|SageMaker가 제공하는 **프레임워크 컨테이너**에서 **사용자 학습 스크립트만 업로드해 실행**하는 모드|
|**장점**|컨테이너 관리 불필요, 코드 재사용 용이, 분산/스팟 학습 지원|
|**적합 대상**|TensorFlow·PyTorch 기반 학습 및 기존 코드의 빠른 클라우드 전환|
