---
title: "SageMaker Debugger 규칙: tensor_variance로 텐서 분산 감지"
slug: "sagemaker-debugger-규칙-tensor_variance로-텐서-분산-감지"
category: cloud
tags: ["amazon-sagemaker", "anomaly-detection", "aws", "deep-learning", "model-monitoring", "sagemaker-debugger", "tensor", "tensorflow", "variance"]
status: published
post_type: tutorial
quality_score: 8.0
created_at: "2026-03-02T01:08:08.132492+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

## 🧩 Quick Summary

| 항목        | 설명                                                               |
| --------- | ---------------------------------------------------------------- |
| **규칙 이름** | `tensor_variance`                                                |
| **도구**    | Amazon SageMaker Debugger                                    |
| **역할**    | 학습/추론 중 수집된 텐서(tensor)들의 **분산(variance)** 값이 특정 임계값을 초과하는 경우를 감지 |
| **활용 목적** | 모델의 **비정상적인 텐서 변화** 탐지 및 경고 (예: 폭주, 발산 등)                        |

> 🚨 **의미**: 학습 또는 추론 중 특정 텐서의 값들이 **너무 많이 퍼져 있거나 급변**할 경우, Debugger가 이를 감지해 경고하도록 하는 **자동화된 이상 탐지 규칙**

---

## 🔍 tensor_variance 규칙 설명

- 텐서(tensor)의 값 분산이 **사전에 정의된 임계값(예: 1.0, 10.0 등)**을 초과하면 경고를 발생시킴
- 주로 **가중치(weight), 그래디언트(gradient), 활성화(activation)** 등 주요 텐서에 적용
- 비정상적으로 큰 분산은 **학습 불안정, 이상 추론 결과, 모델 폭주** 등의 징후일 수 있음

---

## ✅ 사용 예시 (Python SDK)

```python
from sagemaker.debugger import Rule, rule_configs

estimator = TensorFlow(
    entry_point='train.py',
    role='SageMakerRole',
    instance_type='ml.p3.2xlarge',
    rules=[
        Rule.sagemaker(rule_configs.tensor_variance(threshold=5.0))
    ]
)
```
