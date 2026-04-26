<!-- infographic-hero -->
![MiniCPM-V 핵심 요약](figures/infographic.svg)

*Figure: MiniCPM-V 한 장 요약 인포그래픽*

# MiniCPM-V: 스마트폰에서 동작하는 GPT-4V급 멀티모달 모델

## 개요

MiniCPM-V는 2024년 8월 Tsinghua 대학과 OpenBMB가 발표한 효율적인 멀티모달 모델이다. 핵심 목표는 **GPT-4V 수준의 멀티모달 이해 능력을 8B 파라미터 이하의 소형 모델로 달성하여, 스마트폰을 포함한 엣지 디바이스에서의 실시간 배포를 가능하게 하는 것**이다.

MiniCPM-V 2.6(최신 버전)은 Llama-3-8B를 LLM 백본으로, SigLIP-SO400M을 비전 인코더로 사용하며, **적응적 시각 인코딩(Adaptive Visual Encoding)**으로 임의 종횡비의 고해상도 이미지를 효율적으로 처리한다. 특히 **RLAIF-V**를 통한 환각 감소 정렬이 독자적 강점으로, 시각적 환각(hallucination)이 크게 줄어든 신뢰할 수 있는 응답을 생성한다. int4 양자화 적용 시 스마트폰 NPU에서 실시간 추론이 가능한 최초의 GPT-4V급 모델 중 하나이다.

논문: [MiniCPM-V: A GPT-4V Level MLLM on Your Phone](https://arxiv.org/abs/2408.01800)

## 아키텍처 상세

다음 다이어그램은 MiniCPM-V의 전체 아키텍처를 보여준다. 비전 인코더부터 LLM 백본, 엣지 배포 최적화까지의 전체 파이프라인을 확인할 수 있다.

![MiniCPM-V 전체 아키텍처 다이어그램 - Vision Encoder, Adaptive Encoding, LLM 백본 구조](figures/architecture.png)
*Figure 1: MiniCPM-V 아키텍처 개요 - SigLIP-SO400M 비전 인코더, 적응적 시각 인코딩, Llama-3-8B 백본의 전체 파이프라인과 엣지 배포 구성. (Source: OpenBMB)*

### 전체 구조

1. **비전 인코더**: SigLIP-SO400M/14 (400M params)
2. **적응적 시각 인코딩**: AnyRes 슬라이싱 + 2D RoPE
3. **MLP 프로젝터**: 비전 → 언어 공간 매핑
4. **LLM**: Llama-3-8B (또는 MiniCPM-3B)

### 적응적 시각 인코딩(Adaptive Visual Encoding)

아래 그림은 MiniCPM-V의 모델 구조와 적응적 시각 인코딩의 동작 원리를 보여준다. 이미지가 최적 그리드로 분할되어 인코딩되는 전체 과정을 확인할 수 있다.

![MiniCPM-V 모델 구조 및 적응적 시각 인코딩 - 이미지 분할과 슬라이스 인코딩 과정](figures/fig_3.png)
*Figure 2: MiniCPM-V 모델 구조 - (a) 비전 인코더, 압축 레이어, LLM의 전체 구조와 (b) 적응적 시각 인코딩의 이미지 분할 및 슬라이스 인코딩 과정. (Source: arXiv 2408.01800)*

MiniCPM-V의 이미지 처리 파이프라인은 세 단계로 구성된다:

**1단계: 최적 슬라이싱 결정**
이미지의 원본 해상도와 종횡비를 분석하여, 최소한의 정보 손실로 이미지를 분할할 최적 그리드를 결정한다:

$$\text{grid}^* = \arg\min_{(m,n) \in \mathcal{G}} \left| \frac{m}{n} - \frac{W}{H} \right| \quad \text{s.t.} \quad m \times n \leq N_{\max}$$

**2단계: SigLIP 인코딩**
각 슬라이스와 글로벌 이미지를 SigLIP으로 독립 인코딩하여 시각 토큰을 생성한다.

**3단계: 2D RoPE 적용**
시각 토큰에 2D Rotary Position Embedding을 적용하여 이미지 내 공간적 위치 정보를 정확히 전달한다. 이는 1D 위치 인코딩만 사용하는 모델 대비 OCR, 문서 레이아웃 이해에서 큰 이점을 제공한다:

$$\text{RoPE}_{2D}(x_{i,j}) = \text{RoPE}(x, \text{row}=i, \text{col}=j)$$

### RLAIF-V: 환각 감소 정렬

다음 그림은 RLAIF-V의 전체 프레임워크를 보여준다. 응답 생성, 피드백 수집, DPO 최적화의 3단계 파이프라인을 통해 환각을 체계적으로 줄인다.

![RLAIF-V 프레임워크 - 응답 생성, 피드백 수집, DPO를 통한 환각 감소 정렬 과정](figures/fig_4.png)
*Figure 3: RLAIF-V 프레임워크 - (a) 다중 응답 생성, (b) divide-and-conquer 방식 피드백 수집, (c) DPO를 통한 선호 학습으로 환각을 줄인다. (Source: arXiv 2408.01800)*

MiniCPM-V의 독자적 강점인 RLAIF-V는 AI 피드백을 활용한 강화학습이다:

1. 모델이 동일 이미지에 대해 여러 응답을 생성
2. AI 평가기(GPT-4V 등)가 각 응답의 정확성을 평가하여 선호/비선호 쌍 구성
3. DPO로 정확한 응답을 선호하도록 학습

이를 통해 이미지에 없는 객체를 언급하거나, 텍스트를 잘못 읽는 등의 환각 문제가 크게 줄어든다.

| 구성 요소 | MiniCPM-V 2.6 |
|-----------|--------------|
| LLM | Llama-3-8B |
| 비전 인코더 | SigLIP-SO400M |
| 총 파라미터 | ~8B |
| 이미지 해상도 | 최대 1344×1344 (동적) |
| 컨텍스트 길이 | 32,768 |
| 양자화 | int4 지원 (모바일 배포) |

## 핵심 혁신

### 1. 모바일 배포 가능한 GPT-4V급 성능

8B 파라미터에 int4 양자화를 적용하면 약 4GB 메모리로 동작하여, 최신 스마트폰의 NPU에서 실시간 추론이 가능하다. 이는 클라우드 의존 없는 프라이빗 멀티모달 AI를 실현한다.

### 2. 환각 감소 (RLAIF-V)

VLM의 고질적 문제인 시각적 환각을 체계적으로 줄이는 RLAIF-V 기법은, 의료, 문서 분석 등 정확성이 중요한 실무 환경에서 핵심적 가치를 가진다. 아래 예시는 MiniCPM-V와 GPT-4V의 환각 비교 결과를 보여준다.

![MiniCPM-V와 GPT-4V의 환각 비교 - MiniCPM-V가 더 정확한 시각 정보를 제공](figures/fig_10.png)
*Figure 4: 환각 비교 - MiniCPM-V 2.5는 GPT-4V 대비 시각적 환각이 적으며, 이미지의 세부 정보를 더 정확하게 기술한다. 빨간색은 환각 부분을 표시. (Source: arXiv 2408.01800)*

### 3. 다국어 OCR

30개 이상 언어의 OCR을 지원하며, 특히 중국어, 일본어, 한국어(CJK) 문자 인식에서 높은 정확도를 보인다.

## 벤치마크/성능

| 벤치마크 | MiniCPM-V 2.6 | GPT-4V | LLaVA-OV-7B | Qwen2-VL-7B |
|----------|-------------|--------|-----------|-----------|
| OCRBench | **85.2** | 78.0 | 62.4 | 83.0 |
| DocVQA | **90.8** | 87.2 | 83.7 | 89.3 |
| MMMU | **43.4** | 56.8 | 41.7 | 41.3 |
| TextVQA | **80.1** | 78.0 | 68.7 | 79.7 |
| RealWorldQA | **65.2** | 61.4 | - | 64.5 |
| 환각률 (POPE) | **8.2%** | 13.6% | 15.8% | 11.3% |

## 관련 모델 비교

| 특성 | MiniCPM-V | Phi-4-MM | Qwen2-VL-7B | LLaVA-OV-7B |
|------|-----------|---------|-----------|-----------|
| 파라미터 | 8B | 5.6B | 7B | 7B |
| 모바일 배포 | 가능 (int4) | 가능 | 어려움 | 어려움 |
| OCR 특화 | 강함 | 보통 | 강함 | 보통 |
| 환각 감소 | RLAIF-V | - | - | - |
| 오디오 지원 | 미지원 | 지원 | 미지원 | 미지원 |

## 학습 상세

3단계 학습 파이프라인:

**Stage 1: 비전-언어 정렬** - MLP 프로젝터 학습, 이미지-캡션 데이터
**Stage 2: 고해상도 멀티태스크 SFT** - VQA, OCR, 차트, 수학 등 혼합 데이터
**Stage 3: RLAIF-V 환각 감소 정렬** - AI 피드백 기반 DPO

## 실무 활용

```python
from transformers import AutoModel, AutoTokenizer
import torch
from PIL import Image

model = AutoModel.from_pretrained(
    "openbmb/MiniCPM-V-2_6",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
).to("cuda")
tokenizer = AutoTokenizer.from_pretrained(
    "openbmb/MiniCPM-V-2_6", trust_remote_code=True
)

image = Image.open("document.png").convert("RGB")
msgs = [{"role": "user", "content": [image, "이 문서의 내용을 읽어주세요."]}]
response = model.chat(image=None, msgs=msgs, tokenizer=tokenizer)
print(response)
```

## 한계 및 전망

### 한계

1. **추론 속도**: 고해상도 이미지에서 시각 토큰 수가 많아 모바일에서도 지연이 발생할 수 있다
2. **비디오 미지원**: 이미지 이해에 특화, 비디오 처리 능력 부재
3. **생성 불가**: 이미지 생성 기능 없음

### 전망

MiniCPM-V는 "소형 모델도 대형 모델과 경쟁할 수 있다"는 것을 실증하며, 온디바이스 AI의 실현 가능성을 보여주었다. 환각 감소 기술(RLAIF-V)은 VLM의 신뢰성을 높이는 핵심 기술로 향후 더 많은 모델에 적용될 것으로 전망된다. MiniCPM-V 시리즈는 이후 MiniCPM-o로 발전하여 음성 입출력까지 통합하는 방향으로 진화하고 있으며, 엣지 AI의 실용화를 선도하고 있다.

아래 그림은 MLLM 발전의 무어의 법칙을 보여준다. GPT-4V 수준 성능을 달성하는 데 필요한 모델 크기가 점차 줄어들고 있으며, 엣지 디바이스의 연산 능력은 증가하는 추세이다.

![MLLM의 무어의 법칙 - 모델 크기 감소 추세와 엣지 디바이스 연산 능력 증가](figures/fig_1.png)
*Figure 5: MLLM의 무어의 법칙 - GPT-4V 수준 성능을 위한 모델 크기(빨간 선)는 감소하고, 엣지 디바이스 연산 능력(파란 선)은 증가하여, 엣지 배포가 점점 현실화되고 있다. (Source: arXiv 2408.01800)*

특히 MiniCPM-V의 성공은 "데이터 품질과 학습 전략이 모델 크기를 보완할 수 있다"는 중요한 교훈을 제공한다. 8B 모델이 72B 모델과 특정 태스크에서 경쟁할 수 있는 것은, 고품질 인스트럭션 데이터와 RLAIF-V 같은 정교한 정렬 기법 덕분이다. 이는 소형 모델의 가능성을 보여주는 동시에, 모델 크기보다 학습 방법론이 더 중요할 수 있음을 시사한다. 양자화 기술의 발전과 함께, 향후 4비트 양자화 모델이 스마트폰에서 실시간으로 고해상도 이미지를 분석하는 시대가 열릴 전망이다.

## 관련 문서

- [[llava|Visual Instruction Tuning]] - 영감
