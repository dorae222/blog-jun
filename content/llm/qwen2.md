---
title: Qwen2 Technical Report
slug: qwen2
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.369085+00:00"
architecture_entry: qwen2
---

## 개요

Qwen2는 알리바바 그룹의 Qwen 팀이 2024년 발표한 두 번째 세대 대형 언어 모델 시리즈다. Qwen1.5의 후속으로, 0.5B, 1.5B, 7B, 57B-A14B(MoE), 72B 다섯 가지 밀집(dense) 크기와 하나의 MoE 변형이 공개되었다. 특히 **Dual Chunk Attention(DCA)**과 **YARN(Yet Another RoPE Extension)**을 결합하여 최대 **128K 토큰** 컨텍스트를 지원하는 것이 핵심이다.

7조(7T) 토큰의 방대한 데이터로 학습되었으며, 29개 언어를 지원해 특히 중국어와 동아시아 언어 처리에서 강점을 보인다. Qwen2-72B는 동급 오픈소스 모델들을 광범위한 벤치마크에서 능가한다.

## 배경 및 문제

### 1세대 Qwen의 한계

Qwen1.5는 다국어 지원과 오픈소스 공개에서 진전을 이뤘으나, 컨텍스트 길이(최대 32K), 추론 효율성, 수학/코드 특화 능력에서 개선 여지가 있었다.

### 긴 컨텍스트의 기술적 난관

RoPE(Rotary Position Embedding)는 훈련 길이를 초과하는 시퀀스에 대해 성능이 급격히 저하된다. 또한 어텐션 연산의 $O(n^2)$ 복잡도는 128K 토큰 처리를 매우 비효율적으로 만든다.

## 핵심 아이디어

### Grouped Query Attention (GQA)

모든 Qwen2 모델에 GQA를 적용한다. 쿼리 헤드 수($H_q$)가 KV 헤드 수($H_{kv}$)보다 많으며, 여러 쿼리가 하나의 KV 헤드를 공유한다.

$$\text{GQA}(Q, K, V) = \text{Concat}\left(\text{head}_1, \ldots, \text{head}_{H_q}\right) W^O$$

$$\text{head}_i = \text{Attention}(Q_i W_i^Q, K_{\lfloor i/g \rfloor} W^K, V_{\lfloor i/g \rfloor} W^V)$$

여기서 $g = H_q / H_{kv}$는 그룹 크기다.

### Dual Chunk Attention (DCA)

DCA는 긴 시퀀스를 처리할 때 어텐션을 **청크 내(intra-chunk)**와 **청크 간(inter-chunk)**으로 분리하여 계산한다.

- **Intra-chunk Attention**: 같은 청크 내 토큰 간 표준 어텐션 (상대 위치 완전 보존)
- **Inter-chunk Attention**: 다른 청크의 토큰 간 어텐션 (청크 요약 표현 사용)

이를 통해 긴 시퀀스에서도 위치 정보를 효율적으로 유지하면서 계산 복잡도를 줄인다.

$$\text{DCA}(Q, K, V) = \text{IntraAttn}(Q, K, V) + \text{InterAttn}(Q, K_{chunk}, V_{chunk})$$

### YARN (RoPE 외삽)

훈련 시 컨텍스트보다 긴 시퀀스를 처리하기 위해 YARN을 사용한다. YARN은 RoPE의 회전 주파수를 동적으로 스케일링한다.

$$\theta_i^{YARN} = \begin{cases} \theta_i & \text{if } i \in \text{low freq} \\ s \cdot \theta_i & \text{if } i \in \text{high freq} \\ \text{interpolated} & \text{otherwise} \end{cases}$$

4K 토큰으로 훈련된 모델이 128K 토큰으로 외삽될 수 있도록 한다.

### 사전학습 데이터

- **총 토큰**: 7조(7T)
- **언어**: 29개 (영어, 중국어, 일본어, 한국어 등)
- **데이터 품질**: 다단계 필터링, 중복 제거, 품질 점수 기반 선별

## 방법론

### 모델 구성

| 모델 | 파라미터 | 레이어 | Q 헤드 | KV 헤드 | 컨텍스트 |
|------|---------|--------|--------|---------|----------|
| Qwen2-0.5B | 0.49B | 24 | 14 | 2 | 32K |
| Qwen2-1.5B | 1.54B | 28 | 16 | 2 | 32K |
| Qwen2-7B | 7.07B | 28 | 28 | 4 | 128K |
| Qwen2-57B-A14B | 57.4B (14.7B active) | 28 | 64 | 8 | 64K |
| Qwen2-72B | 72.7B | 80 | 64 | 8 | 128K |

### 정렬 훈련

사전학습 후 **SFT + RLHF** 파이프라인을 적용하여 Qwen2-Instruct 모델을 만든다. DPO(Direct Preference Optimization)도 병행하여 사용한다.

## 실험 결과

### 일반 능력 벤치마크

| 모델 | MMLU | GSM8K | HumanEval | IFEval | MBPP |
|------|------|-------|-----------|--------|------|
| Llama 3-8B | 66.6 | 79.6 | 62.2 | 76.8 | 65.0 |
| Mistral-7B | 64.2 | 52.2 | 40.2 | - | 49.0 |
| **Qwen2-7B** | **70.3** | **89.9** | **79.9** | **77.6** | **75.2** |
| Llama 3-70B | 82.0 | 93.0 | 81.7 | 86.2 | 80.2 |
| **Qwen2-72B** | **84.2** | **93.2** | **86.0** | **87.6** | **82.6** |

### 다국어 벤치마크

| 모델 | 중국어 | 일본어 | 한국어 | 아랍어 |
|------|--------|--------|--------|--------|
| Llama 3-70B | 74.3 | 68.1 | 62.8 | 59.0 |
| Qwen2-72B | **91.1** | **79.3** | **73.2** | **71.5** |

특히 중국어와 동아시아 언어에서 Llama 3-70B를 크게 앞선다.

### 긴 컨텍스트 성능

Needle-in-a-Haystack 평가에서 Qwen2-72B는 128K 토큰 길이까지 거의 완벽한 검색 정확도를 유지한다.

## 의의 및 한계

### 의의

- **긴 컨텍스트 오픈소스**: DCA + YARN으로 128K 오픈소스 모델의 실용적 기준 수립
- **다국어 선두**: 29개 언어 지원, 특히 아시아권 언어에서 강점
- **규모 대비 성능**: Qwen2-7B가 Llama 3-8B를 대부분 벤치마크에서 능가
- **MoE 변형 제공**: 57B-A14B로 비용 효율적 대용량 모델 제공

### 한계

- **훈련 데이터 세부사항 제한적 공개**: 데이터 구성의 완전한 투명성 부족
- **안전성 정렬 지속 과제**: 29개 언어 전반에 걸친 일관된 안전성 확보 어려움
- **서구권 벤치마크 편향**: MMLU, HumanEval 등은 영어 중심으로, 다국어 우위가 실제 사용성에서 다를 수 있음

Qwen2는 Qwen 시리즈를 글로벌 경쟁력 있는 오픈소스 LLM으로 자리매김시켰으며, 이후 Qwen2.5, Qwen2-VL 등 멀티모달 확장의 기반이 되었다.