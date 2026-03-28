# BLOOM: 전 세계 연구자가 만든 오픈소스 다국어 LLM

## 개요

BLOOM(BigScience Large Open-science Open-access Multilingual Language Model)은 2022년 11월 **BigScience** 프로젝트를 통해 공개된 176B 파라미터 규모의 대형 언어 모델이다. 전 세계 70개국 이상에서 **1,000명 이상의 연구자**가 약 1년간 협업하여 만든 이 모델은, 대형 언어 모델 연구가 소수 대기업에 의해 독점되는 현실에 대한 학술 커뮤니티의 응답이었다.

BLOOM의 가장 큰 의미는 기술적 성능보다 **과정의 투명성**에 있다. 학습 데이터 구성부터 모델 설계, 학습 과정, 최종 공개까지 전 과정이 문서화되어 공개되었으며, 이는 AI 연구의 민주화와 재현 가능성(reproducibility) 측면에서 선례를 남겼다.

- **논문**: [BLOOM: A 176B-Parameter Open-Access Multilingual Language Model](https://arxiv.org/abs/2211.05100)
- **코드**: [BigScience Workshop (GitHub)](https://github.com/bigscience-workshop/bigscience)
- **라이선스**: RAIL (Responsible AI License)

## 아키텍처 상세

다음 다이어그램은 BLOOM-176B의 전체 아키텍처와 ALiBi 위치 인코딩의 동작 방식을 보여준다.

![BLOOM-176B 전체 아키텍처 다이어그램 - ALiBi 위치 인코딩 적용 Decoder-Only 구조](figures/architecture.png)
*Figure 1: BLOOM-176B 아키텍처 - 70개 레이어, 112개 어텐션 헤드, 250,880 어휘 크기의 대규모 Decoder-Only Transformer. ALiBi 위치 인코딩과 BPE 토크나이저를 사용한다. (Source: BLOOM 논문)*

BLOOM은 GPT-3 스타일의 **Decoder-only Transformer** 구조를 채택한다:

| 구성 요소 | 값 |
|-----------|----|
| 파라미터 수 | 176B |
| 레이어 수 | 70 |
| Hidden Dim | 14,336 |
| Attention Heads | 112 |
| Vocab Size | **250,880** |
| Context Length | 2,048 |
| 정규화 | LayerNorm |
| 활성화 함수 | GeLU |
| 위치 인코딩 | **ALiBi** |

### ALiBi (Attention with Linear Biases)

BLOOM의 핵심 아키텍처 선택은 **ALiBi 위치 인코딩**이다. 기존의 sinusoidal이나 learned position embedding 대신, 어텐션 점수에 거리에 비례하는 선형 편향을 직접 더한다:

$$\text{softmax}\left(q_i K^T + m \cdot [-(i-1), -(i-2), \ldots, -1, 0]\right)$$

여기서 $m$은 각 어텐션 헤드마다 다른 고정 기울기이다. ALiBi의 장점:
- **길이 외삽(extrapolation)**: 학습 시 사용한 최대 시퀀스 길이를 넘어서도 일반화 가능
- **학습 파라미터 없음**: 위치 임베딩을 학습할 필요가 없어 효율적
- **구현 단순성**: 어텐션 마스크에 선형 편향만 추가하면 됨

아래 그림은 BLOOM의 아키텍처를 논문에서 제시한 상세 뷰로 보여준다. 특히 ALiBi 마스크가 Key-Query product에 선형 편향으로 적용되는 과정이 시각화되어 있다.

![BLOOM 아키텍처 상세 - Decoder Block, Multi-Head Attention, ALiBi 마스크 적용 과정](figures/fig_5.png)
*Figure 2: BLOOM 아키텍처 상세 - (좌) 70개 Decoder Block 구조, (중앙) Multi-Head Attention 구성, (우) ALiBi 마스크가 Key-Query product에 선형 편향(k_head)으로 더해지는 방식. (Source: BLOOM 논문)*

### 대규모 어휘 사전 (250,880)

다국어 처리의 핵심인 250,880개의 어휘는 BPE(Byte-Pair Encoding) 토크나이저로 구성되었다. 영어 외 언어에서도 토큰 효율성을 유지하여, 비영어 텍스트를 처리할 때 토큰 수가 불필요하게 늘어나는 문제를 완화한다.

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# BLOOM 모델 로드 (작은 버전으로 시연)
tokenizer = AutoTokenizer.from_pretrained('bigscience/bloom-560m')
model = AutoModelForCausalLM.from_pretrained('bigscience/bloom-560m')

# 다국어 텍스트 생성
prompts = [
    "The future of AI is",          # 영어
    "L'avenir de l'IA est",         # 프랑스어
    "人工知能の未来は",                # 일본어
    "인공지능의 미래는",               # 한국어
]

for prompt in prompts:
    inputs = tokenizer(prompt, return_tensors='pt')
    outputs = model.generate(
        inputs['input_ids'],
        max_length=50,
        do_sample=True,
        temperature=0.7
    )
    print(f"{prompt} → {tokenizer.decode(outputs[0], skip_special_tokens=True)}")
```

## 핵심 혁신

### 1. 개방형 협업 모델
1,000명 이상의 연구자가 데이터 수집, 모델 설계, 학습, 평가 등 모든 과정에 참여한 전례 없는 규모의 협업 프로젝트이다.

### 2. ROOTS 데이터셋
- 498개 Hugging Face 데이터셋 통합
- 46개 자연어 + 13개 프로그래밍 언어
- 영어 30%, 프랑스어 13%, 나머지 다국어
- 총 **366B 토큰 (1.6TB)**
- 데이터 거버넌스 위원회의 윤리적 검토 포함

다음 트리맵은 ROOTS 코퍼스의 언어 구성을 보여준다. 인도유럽어족과 시노티벳어족이 전체의 대부분을 차지하지만, 저자원 언어도 포함되어 있다.

![ROOTS 코퍼스 언어 구성 트리맵 - 46개 자연어의 어족별 분포](figures/fig_3_1.png)
*Figure 3: ROOTS 코퍼스 언어 분포 - 인도유럽어족(프랑스어, 스페인어, 영어 등)과 시노티벳어족(중국어)이 1,321.89GB로 주요 비중을 차지하며, 아프로아시아어족(아랍어), 남아시아어족(베트남어) 등 다양한 언어가 포함된다. (Source: BLOOM 논문)*

### 3. 완전 투명한 학습 과정
학습 로그, 체크포인트, 데이터 처리 코드까지 모두 공개되어 재현 가능성을 극대화했다.

## 벤치마크/성능

| 벤치마크 | BLOOM-176B | OPT-175B | GPT-3 175B |
|----------|-----------|----------|------------|
| Ax-b | **BLOOM 우세** | - | - |
| CB | **BLOOM 우세** | - | - |
| WiC | **BLOOM 우세** | - | - |
| 다국어 요약 | **BLOOM 우세** | OPT 열세 | - |
| 저자원 언어 번역 | **M2M 수준** | 미지원 | 미지원 |

아래 그래프는 SuperGLUE 1-shot 벤치마크에서 BLOOM과 OPT의 스케일링 비교를 보여준다. 모델 크기 증가에 따른 성능 변화를 태스크별로 확인할 수 있다.

![SuperGLUE 1-shot 벤치마크에서 BLOOM과 OPT의 스케일링 비교](figures/fig_8.png)
*Figure 5: SuperGLUE 1-shot 태스크별 BLOOM vs OPT 스케일링 - Ax-b, CB, WiC 등에서 BLOOM이 OPT와 유사하거나 우수한 스케일링을 보이며, 특히 대규모 모델에서 두드러진다. (Source: BLOOM 논문)*

### 다국어 특화 성능
- 다국어 요약에서 OPT-175B보다 일관되게 우수
- 저자원 언어 번역에서 지도 학습 모델(M2M)에 필적하는 성능
- 46개 언어 전반에 걸친 균형 잡힌 성능

## 관련 모델 비교

| 특성 | GPT-3 | OPT | BLOOM | LLaMA |
|------|-------|-----|-------|-------|
| 파라미터 | 175B | 175B | **176B** | 65B |
| 오픈소스 | X | O (연구) | **O (상업 가능)** | O (연구) |
| 다국어 지원 | 영어 중심 | 영어 중심 | **46개 언어** | 영어 중심 |
| 어휘 크기 | 50,257 | 50,272 | **250,880** | 32,000 |
| 위치 인코딩 | Learned | Learned | **ALiBi** | RoPE |
| 학습 데이터 투명성 | X | 부분 | **완전 공개** | 부분 |
| 협업 규모 | OpenAI | Meta | **1,000+ 연구자** | Meta |

## 학습 상세

### 데이터셋
- **ROOTS**: 366B 토큰 (1.6TB)
- 영어 30%, 프랑스어 13%, 스페인어, 포르투갈어, 아랍어, 중국어 등
- 13개 프로그래밍 언어 포함

### 학습 인프라
- **Jean Zay 슈퍼컴퓨터** (프랑스 국립 컴퓨팅 센터)
- **384개 A100 80GB GPU**
- 학습 기간: 약 **105일 (3.5개월)**
- **Megatron-DeepSpeed** 프레임워크
- 3D 병렬화: 텐서 + 파이프라인 + 데이터 병렬화

다음 그림은 384개 A100 GPU에서 BLOOM을 학습하기 위한 3D 병렬화 전략을 보여준다.

![BLOOM 학습을 위한 3D 병렬화 전략 - 데이터, 텐서, 파이프라인 병렬화의 조합](figures/fig_6.png)
*Figure 4: 3D 병렬화 구조 - 데이터 병렬화(DP=8), 텐서 병렬화(TP=4), 파이프라인 병렬화(PP=12)를 결합하여 384개 A100 GPU에서 176B 모델을 학습한다. 한 모델 복제본이 48개 GPU를 사용한다. (Source: BLOOM 논문)*

## 실무 활용

### 1. 다국어 NLP
46개 언어를 지원하여 다국어 텍스트 생성, 번역, 분류에 활용할 수 있다.

### 2. 저자원 언어 연구
영어 중심 LLM이 지원하지 않는 저자원 언어에 대한 연구 기반을 제공한다.

### 3. BLOOMZ / mT0
BLOOM에 다국어 명령어 튜닝을 적용한 BLOOMZ는 다국어 제로샷 태스크에 강력한 성능을 보인다.

### 4. AI 윤리 연구
투명한 데이터 거버넌스와 편향 분석이 포함되어 책임감 있는 AI 연구의 참고 사례가 된다.

## 한계 및 전망

### 한계
1. **영어 성능**: 영어 단일 태스크에서는 GPT-3, OPT에 비해 상대적으로 약하다
2. **컨텍스트 길이**: 2,048 토큰으로 현대 기준에서 짧다
3. **추론 비용**: 176B 파라미터로 배포와 추론에 막대한 자원이 필요하다
4. **데이터 품질**: 다양한 출처의 데이터 품질 편차가 존재한다

### 전망
BLOOM은 **기술적 성과보다 사회적 의미가 더 큰 모델**이다. 대형 LLM 개발이 소수 기업의 전유물이 될 수 있다는 우려 속에서, 학술 커뮤니티가 충분히 경쟁력 있는 모델을 만들 수 있음을 증명했다. ROOTS 데이터셋의 투명한 거버넌스, RAIL 라이선스의 책임감 있는 사용 조건, 그리고 글로벌 협업 모델은 이후 오픈소스 AI 프로젝트의 표준이 되었다. BLOOMZ와 같은 파생 모델을 통해 다국어 NLP 생태계 발전에 지속적으로 기여하고 있다.

---

**참고 문헌**
- Workshop, B. S., et al. (2022). "BLOOM: A 176B-Parameter Open-Access Multilingual Language Model." arXiv:2211.05100
- Press, O., Smith, N. A., & Lewis, M. (2021). "Train Short, Test Long: Attention with Linear Biases Enables Input Length Extrapolation." (ALiBi)
- Muennighoff, N., et al. (2022). "Crosslingual Generalization through Multitask Finetuning." (BLOOMZ)

## 관련 문서

- [[gpt-3|Language Models are Few-Shot Learners (GPT-3)]] - 영감
