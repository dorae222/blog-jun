---
title: "TFRecord 형식이란?"
slug: "tfrecord-형식이란"
category: cloud
tags: ["big-data", "data-pipeline", "data-serialization", "deep-learning", "machine-learning", "tensorflow", "tfrecord", "training-data"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.962342+00:00"
---

### ✅ TFRecord 형식이란?

**TFRecord**는 **TensorFlow에서 대규모 데이터를 효율적으로 저장·읽기 위해 사용하는 이진(바이너리) 데이터 형식**입니다. 주로 **학습 데이터셋을 직렬화하여 저장**하며, **샤딩(여러 파일로 분할)과 스트리밍을 통해 대용량 학습 시 I/O 성능을 최적화**할 수 있습니다.

---

## 🔧 주요 특징

|항목|설명|
|---|---|
|**이진 직렬화 포맷**|텍스트보다 저장 용량이 작고 읽기 속도가 빠름|
|**Sequence 지원**|순차적 데이터 접근에 적합|
|**TensorFlow 통합**|`tf.data.TFRecordDataset`으로 바로 읽기 가능|
|**샤딩·스트리밍 가능**|대규모 데이터셋을 여러 파일로 나누어 처리할 수 있음|
|**유연한 구조**|이미지, 오디오, 텍스트 등 다양한 타입을 Feature로 저장 가능|

---

## 🧪 데이터 구조

- **TFRecord 파일** 내부에는 **`tf.train.Example`** 단위로 데이터가 저장됩니다.
- 각 Example은 **`Features` → `Feature` → `BytesList/FloatList/Int64List`** 구조를 가집니다.

```text
TFRecord File
 ├─ Example 1
 │   └─ Features
 │       ├─ feature_a (Int64List)
 │       └─ feature_b (BytesList)
 ├─ Example 2
 │   └─ Features
 ...
```

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|TensorFlow에서 **데이터셋을 직렬화·이진 저장**하는 파일 형식|
|**장점**|I/O 효율 향상, 대규모 학습 지원, 스트리밍·샤딩에 유리|
|**활용 예**|이미지·텍스트·오디오 학습 데이터 및 대용량 ML 학습 파이프라인|
