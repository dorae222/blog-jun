# UL2: 노이즈 제거 혼합으로 언어 학습 패러다임을 통합하다

## 개요

UL2(Unified Language Learner)는 2022년 5월 Google Research가 발표한 인코더-디코더 모델로, 기존 사전 학습 패러다임의 근본적인 한계를 극복하기 위해 **노이즈 제거 혼합(Mixture of Denoisers, MoD)** 프레임워크를 제안했다.

기존 접근법의 문제:
- **MLM (BERT)**: 이해 태스크에 강하지만 생성에 약하다
- **AR LM (GPT)**: 생성에 강하지만 양방향 문맥을 활용하지 못한다
- **Span Corruption (T5)**: 중간 길이 복원에 편향되어 있다

UL2는 이 세 가지를 **하나의 통합 프레임워크**로 결합하여, 20B 파라미터라는 상대적으로 작은 규모로 GPT-3(175B)를 다수 벤치마크에서 능가하는 놀라운 효율성을 보여주었다.

- **논문**: [UL2: Unifying Language Learning Paradigms](https://arxiv.org/abs/2205.05131)
- **코드**: [GitHub](https://github.com/google-research/google-research/tree/master/ul2)
- **라이선스**: Apache 2.0

## 아키텍처 상세

UL2는 T5 아키텍처를 기반으로 한 인코더-디코더 구조이다:

| 구성 요소 | 값 |
|-----------|----|
| 파라미터 수 | 20B |
| 인코더+디코더 레이어 | 32 |
| Hidden Dim | 4,096 |
| Attention Heads | 64 |
| Vocab Size | 32,100 |
| Context Length | 512 (입력) / 512 (출력) |
| 정규화 | RMSNorm (Pre-Norm) |
| 활성화 함수 | ReLU |
| 위치 인코딩 | Relative Attention Bias |

### Relative Attention Bias

T5에서 도입된 상대 위치 편향(Relative Attention Bias)을 사용한다. 별도의 위치 임베딩 대신, 어텐션 점수에 상대적 거리 기반 편향을 더한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}} + B\right)V$$

여기서 $B \in \mathbb{R}^{T \times T}$는 학습 가능한 상대 위치 편향 행렬이다.

## 핵심 혁신: Mixture of Denoisers (MoD)

MoD는 세 가지 노이즈 제거 목표를 혼합한다:

### 1. R-Denoiser (Regular)
T5 방식의 짧은 스팬 마스킹·복원이다:
- 스팬 길이: 평균 3 토큰
- 마스킹 비율: 15%
- **이해(understanding) 태스크에 유리**

### 2. S-Denoiser (Sequential)
GPT 방식의 접두사-완성(prefix-to-suffix) 자기회귀 생성이다:
- 입력의 앞부분을 접두사로, 뒷부분을 타겟으로 사용
- **생성(generation) 태스크에 유리**

### 3. X-Denoiser (Extreme)
매우 긴 스팬을 마스킹하여 복원하는 극단적 노이즈 제거이다:
- 마스킹 비율: 50~75%
- 스팬 길이: 매우 길음
- **긴 문맥 이해와 생성 모두에 유리**

### Mode Token

각 노이즈 유형을 구분하기 위해 입력 앞에 **모드 토큰**을 삽입한다:
- `[R]`: R-Denoiser 모드
- `[S]`: S-Denoiser 모드  
- `[X]`: X-Denoiser 모드

이 모드 토큰은 파인튜닝과 추론 시에도 사용할 수 있어, **원하는 생성 방식을 명시적으로 제어**할 수 있다.

```python
import torch
from transformers import AutoTokenizer, T5ForConditionalGeneration

# UL2 모델 로드
tokenizer = AutoTokenizer.from_pretrained('google/ul2')
model = T5ForConditionalGeneration.from_pretrained('google/ul2')

# S-Denoiser 모드로 텍스트 생성
input_text = "[S2S] Summarize: UL2 is a unified language learner that combines \
multiple pretraining paradigms into a single framework."

inputs = tokenizer(input_text, return_tensors='pt')
outputs = model.generate(
    inputs['input_ids'],
    max_length=100,
    num_beams=4
)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 벤치마크/성능

UL2(20B)는 훨씬 큰 모델들을 능가하는 놀라운 효율성을 보여주었다:

| 벤치마크 | UL2 (20B) | T5-XXL (11B) | GPT-3 (175B) |
|----------|-----------|-------------|-------------|
| SuperGLUE (0-shot) | **71.2** | 58.4 | 68.9 |
| 1-shot 요약 | **T5 대비 3배** | baseline | - |
| 평균 (9개 설정) | **+43.6% vs T5** | baseline | +76.1% vs LM |
| 지도학습 NLP 50개 | **SOTA** | - | - |

### 핵심 결과
- T5 baseline 대비 평균 **+43.6%** 성능 향상
- 언어 모델 baseline 대비 **+76.1%** 성능 향상
- 제로샷 SuperGLUE에서 **175B GPT-3 능가**
- 1-shot 요약에서 T5-XXL의 **3배 성능**
- 50개 지도학습 NLP 태스크에서 **SOTA**

## 관련 모델 비교

| 특성 | T5 | GPT-3 | UL2 | Flan-UL2 |
|------|-----|-------|-----|----------|
| 구조 | Enc-Dec | Dec-only | Enc-Dec | Enc-Dec |
| 사전학습 | Span Corruption | AR LM | **MoD (R+S+X)** | MoD + Flan |
| 파라미터 | 11B (XXL) | 175B | 20B | 20B |
| 이해 능력 | 강함 | 보통 | **강함** | 강함 |
| 생성 능력 | 보통 | 강함 | **강함** | 강함 |
| 인컨텍스트 학습 | 약함 | 강함 | **강함** | 매우 강함 |
| 모드 제어 | X | X | **O** | O |

## 학습 상세

### 데이터셋
- **C4 (Colossal Clean Crawled Corpus)**

### 학습 설정
- 토크나이저: SentencePiece (32,100 vocab)
- Optimizer: Adafactor
- 배치 크기: 1,024
- 학습 스텝: 1M
- 인프라: **512 TPU v4** 코어, 약 2주 학습
- 세 노이즈 제거 목표를 **균등 샘플링**으로 혼합
- Flan-UL2: UL2 체크포인트에 Flan 명령어 튜닝 적용

## 실무 활용

### 1. 범용 NLP 백본
모드 토큰을 통해 이해·생성·긴 문맥 태스크를 하나의 모델로 처리할 수 있다.

### 2. 인컨텍스트 학습
제로샷/퓨샷 성능이 뛰어나 파인튜닝 없이도 다양한 태스크에 적용 가능하다.

### 3. 연구 베이스라인
오픈소스로 공개되어 사전 학습 패러다임 연구의 강력한 베이스라인으로 활용된다.

### 4. Flan-UL2
Flan 명령어 튜닝을 적용한 Flan-UL2는 오픈소스 최강 모델 중 하나로 평가받으며, 실무 NLP 파이프라인에서 널리 사용된다.

## 한계 및 전망

### 한계
1. **Encoder-Decoder 오버헤드**: Decoder-only 모델 대비 추론 비용이 높다
2. **컨텍스트 길이**: 512 토큰으로 제한되어 현대 LLM 대비 짧다
3. **20B 규모**: 현재 기준으로는 중소형 모델에 속한다
4. **단일 데이터셋**: C4만으로 학습되어 데이터 다양성이 제한적이다

### 전망
UL2가 제시한 **"하나의 모델로 모든 패러다임을 통합"**이라는 비전은 이후 LLM 연구에 지대한 영향을 미쳤다. MoD의 핵심 통찰—다양한 사전 학습 목표를 혼합하면 개별 목표보다 우수하다—은 PaLM, Gemini 등 Google의 후속 모델 설계에도 반영되었다. 특히 모드 토큰을 통한 **명시적 생성 방식 제어**는 현대 프롬프트 엔지니어링의 선구적 개념으로 평가할 수 있다.

---

**참고 문헌**
- Tay, Y., et al. (2022). "UL2: Unifying Language Learning Paradigms." arXiv:2205.05131
- Raffel, C., et al. (2019). "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer." (T5)
- Chung, H. W., et al. (2022). "Scaling Instruction-Finetuned Language Models." (Flan)

## 관련 문서

- [[t5|T5]] — 발전 기반
