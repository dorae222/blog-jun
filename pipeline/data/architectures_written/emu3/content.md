# Emu3: 다음 토큰 예측만으로 달성하는 통합 멀티모달

## 개요

Emu3는 2024년 9월 BAAI(북경인공지능연구원)가 발표한 통합 멀티모달 모델이다. 이 모델의 핵심 주장은 명확하다: **확산 모델이나 CLIP 같은 전문 컴포넌트 없이, 오직 다음 토큰 예측(next-token prediction)만으로 이미지 이해, 이미지 생성, 비디오 생성을 모두 수행할 수 있다.**

Chameleon이 제시한 조기 융합 방향을 이어받되, Emu3는 한 단계 더 나아가 **비디오**까지 이산 토큰 프레임워크에 통합하고, **DPO(Direct Preference Optimization)**를 이미지 생성에 적용하여 생성 품질을 크게 향상시켰다. 8B 파라미터 규모에서 텍스트-이미지 생성 품질이 SDXL과 경쟁하고, 이미지 이해에서 LLaVA-1.6에 근접하는 성능을 보여, 단일 아키텍처로 이해와 생성을 모두 달성하는 것이 실현 가능함을 입증하였다.

논문: [Emu3: Next-Token Prediction is All You Need](https://arxiv.org/abs/2409.18869)

## 아키텍처 상세

### 전체 구조

Emu3의 구조는 세 가지 컴포넌트로 구성된다:

1. **SBER-VQGAN 토크나이저**: 이미지/비디오를 이산 토큰으로 변환 (코드북 크기 32,768)
2. **BPE 텍스트 토크나이저**: 텍스트를 이산 토큰으로 변환
3. **통합 자기회귀 트랜스포머**: 8B 파라미터, 모든 모달리티를 동일한 모델로 처리

통합 어휘 크기:
$$V_{\text{total}} = V_{\text{text}} + V_{\text{visual}} + V_{\text{special}} = 151,851 + 32,768 + 3 = 184,622$$

### SBER-VQGAN 토크나이저

Emu3의 비주얼 토크나이저는 기존 VQ-VAE를 개선한 SBER-VQGAN이다:

- **시간적 다운샘플링**: 비디오의 시간 차원을 4배 압축
- **공간적 다운샘플링**: 이미지/비디오의 공간 차원을 8배 압축
- **코드북**: 32,768개 코드 (Chameleon의 8,192보다 4배 큼)

이미지 예시 ($512 \times 512$):
$$I \rightarrow \text{SBER-VQGAN} \rightarrow \mathbf{z} \in \{0, ..., 32767\}^{64 \times 64} = 4096 \text{ 토큰}$$

비디오 예시 ($T$ 프레임):
$$V \rightarrow \text{SBER-VQGAN} \rightarrow \mathbf{z} \in \{0, ..., 32767\}^{T/4 \times 64 \times 64}$$

### 트랜스포머 아키텍처

| 항목 | 값 |
|------|---|
| 파라미터 | 8B |
| 어텐션 | Grouped Query Attention (GQA) |
| 정규화 | RMSNorm |
| 활성화 | SiLU |
| 위치 인코딩 | RoPE |
| 컨텍스트 길이 | 8192 |
| 히든 차원 | 4096 |
| 레이어 수 | 32 |
| 어텐션 헤드 | 32 (KV 헤드: 8) |
| 통합 어휘 | 184,622 |

## 핵심 혁신

### 1. 비디오까지 통합한 이산 토큰 프레임워크

Chameleon이 이미지-텍스트 통합에 그친 반면, Emu3는 비디오를 시간-공간 VQ 토크나이저로 이산화하여 동일한 프레임워크에 포함시켰다. 이로써 텍스트-이미지, 텍스트-비디오, 이미지-텍스트, 비디오-텍스트 변환이 모두 동일한 다음 토큰 예측으로 처리된다.

### 2. 이미지 생성에 DPO 적용

이미지 생성 품질을 향상시키기 위해 **DPO(Direct Preference Optimization)**를 자기회귀 이미지 생성에 최초로 적용하였다:

$$\mathcal{L}_{\text{DPO}} = -\mathbb{E}\left[\log\sigma\left(\beta \log\frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log\frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)}\right)\right]$$

여기서 $y_w$는 선호된 이미지, $y_l$은 비선호 이미지이다. 이를 통해 CFG(Classifier-Free Guidance) 없이도 안정적이고 고품질의 이미지 생성이 가능하다.

### 3. 확산 모델 없는 순수 자기회귀 생성

DALL-E 3, Stable Diffusion 등의 확산 모델과 달리, 순수하게 다음 토큰 예측만으로 고품질 이미지를 생성한다. 이는 텍스트 생성과 동일한 인프라를 사용할 수 있어 배포 및 서빙이 단순해지는 실용적 장점이 있다.

## 벤치마크/성능

### 이미지 생성

| 모델 | GenEval (Overall) | DPG-Bench |
|------|------------------|-----------|
| Emu3 (+ DPO) | **0.68** | **80.6** |
| SDXL | 0.55 | 74.7 |
| LlamaGen | 0.32 | — |
| DALL-E 3 | 0.67 | 83.5 |

### 이미지 이해

| 모델 | MMBench | MMMU | VQAv2 |
|------|---------|------|-------|
| Emu3 | 58.5 | 31.6 | — |
| LLaVA-1.6-7B | 67.4 | 35.8 | — |
| Chameleon-7B | — | — | 57.1 |

## 관련 모델 비교

| 특성 | Emu3 | Chameleon | Transfusion | Show-o2 |
|------|------|-----------|-------------|---------|
| 이미지 표현 | 이산(VQ) | 이산(VQ) | 연속(VAE) | 이산(VQ) |
| 생성 방식 | 자기회귀 | 자기회귀 | 자기회귀+확산 | 자기회귀+마스킹 |
| 비디오 지원 | 가능 | 미지원 | 미지원 | 미지원 |
| DPO 정렬 | 적용 | 미적용 | 미적용 | 적용 |
| 코드북 크기 | 32,768 | 8,192 | — | — |

## 학습 상세

3단계 학습 파이프라인:

**Stage 1: SBER-VQGAN 토크나이저 학습**
- 대규모 이미지/비디오 데이터로 VQ 토크나이저 사전학습
- 32,768개 코드북, 시공간 다운샘플링

**Stage 2: 통합 사전학습**
- 약 600B 멀티모달 토큰 (이미지 + 비디오 + 텍스트)
- AdamW 옵티마이저, cosine 스케줄러
- 이미지·비디오·텍스트 데이터 균형 혼합

**Stage 3: SFT + DPO 정렬**
- 멀티모달 인스트럭션 튜닝 (이해 + 생성)
- DPO로 이미지 생성 품질 향상

## 실무 활용

```python
# Emu3 추론 (개념적 코드)
from emu3 import Emu3ForCausalLM, Emu3Processor

model = Emu3ForCausalLM.from_pretrained("BAAI/Emu3-Gen")
processor = Emu3Processor.from_pretrained("BAAI/Emu3-Gen")

# 이미지 생성
inputs = processor(text="A serene lake surrounded by mountains at sunset")
image_tokens = model.generate(**inputs, modality="image")
image = processor.decode_image(image_tokens)

# 이미지 이해
inputs = processor(text="Describe this image.", images=["photo.jpg"])
response = model.generate(**inputs, modality="text")
print(processor.decode(response))
```

## 한계 및 전망

### 한계

1. **이미지 생성 품질**: DALL-E 3, SD3 등 전문 확산 모델 대비 여전히 열위하며, VQ 토크나이제이션의 고질적 정보 손실 문제가 남아있다
2. **이해 성능**: 동일 크기의 전문 이해 모델(LLaVA-1.6)보다 이해 성능이 낮아, 이해-생성 트레이드오프가 존재한다
3. **생성 속도**: 이미지당 4096개 토큰을 자기회귀로 생성하므로 확산 모델 대비 생성 속도가 느리다

### 전망

Emu3는 "다음 토큰 예측이 전부"라는 강력한 메시지를 통해 통합 멀티모달 모델의 실현 가능성을 보여주었다. VQ 토크나이저의 품질이 향상되고 모델 규모가 확대되면, 이해와 생성 모두에서 전문 모델을 능가하는 진정한 통합 멀티모달 모델이 등장할 것으로 기대된다.

## 관련 문서

- [[chameleon|Chameleon]] — 영감
