# Pixtral: Mistral의 네이티브 비전 인코더와 임의 해상도 처리

## 개요

Pixtral은 2024년 10월 Mistral AI가 발표한 12B 파라미터 멀티모달 모델이다. Mistral의 첫 번째 멀티모달 모델이자, 기존 비전 인코더(CLIP, SigLIP 등)를 차용하지 않고 **400M 파라미터의 새로운 비전 인코더를 처음부터(from scratch) 학습**한 것이 특징이다.

Pixtral의 비전 인코더는 **2D RoPE(Rotary Position Embedding)**를 적용하여 임의 해상도와 종횡비의 이미지를 고정 크기로 리사이즈하지 않고 그대로 처리한다. 128K 토큰의 긴 컨텍스트에서 다수의 이미지와 텍스트를 혼합하여 처리하는 문서 이해 능력이 탁월하며, 특히 여러 페이지의 PDF 문서를 한 번에 분석하는 시나리오에서 강점을 보인다.

논문: [Pixtral 12B](https://arxiv.org/abs/2410.07073)

## 아키텍처 상세

다음은 Pixtral의 전체 아키텍처를 상세히 나타낸 다이어그램이다. 비전 인코더부터 멀티모달 디코더까지의 데이터 흐름을 확인할 수 있다.

![Pixtral 12B 전체 아키텍처 다이어그램 — 비전 인코더, 멀티모달 퓨전, 디코더 구조](figures/architecture.png)
*Figure 1: Pixtral 12B 아키텍처 개요 — Vision Encoder(400M), Multimodal Fusion, Mistral-NeMo-12B 디코더의 전체 파이프라인. (Source: Mistral AI)*

### 전체 구조

1. **비전 인코더**: Pixtral ViT (400M params, 처음부터 학습)
2. **연결**: 이미지 토큰을 텍스트 시퀀스에 직접 삽입
3. **언어 모델**: Mistral-NeMo-12B

### 2D RoPE 비전 인코더

Pixtral의 비전 인코더는 ViT 구조를 기반으로 하되, 핵심적인 차이가 있다:

**기존 ViT**: 이미지를 고정 크기(224/384px)로 리사이즈 → 고정 패치 수
**Pixtral ViT**: 원본 이미지 크기 유지 → 가변 패치 수 + 2D RoPE

아래 그림은 Pixtral 비전 인코더의 내부 구조를 보여준다. Block-diagonal attention mask와 RoPE-2D가 가변 크기 이미지를 어떻게 처리하는지 확인할 수 있다.

![Pixtral 비전 인코더 구조 — RoPE-2D와 Block-diagonal attention을 활용한 가변 해상도 이미지 처리](figures/fig_3.png)
*Figure 2: Pixtral Vision Encoder — 이미지 패치에 RoPE-2D 위치 인코딩을 적용하고, Block-diagonal attention mask로 시퀀스 패킹을 지원한다. (Source: arXiv 2410.07073)*

2D RoPE는 각 패치의 (행, 열) 위치를 독립적으로 인코딩한다:

$$\text{RoPE}_{2D}(x_{i,j}) = x \cdot \begin{bmatrix} \cos(i\theta) & -\sin(i\theta) \\ \sin(i\theta) & \cos(i\theta) \end{bmatrix} \otimes \begin{bmatrix} \cos(j\theta) & -\sin(j\theta) \\ \sin(j\theta) & \cos(j\theta) \end{bmatrix}$$

이 방식의 장점:
- **해상도 불변**: 학습 시와 다른 해상도의 이미지도 자연스럽게 처리
- **종횡비 보존**: 정사각형으로 패딩/크롭하지 않아 정보 손실 없음
- **위치 정확성**: 2D 공간 관계를 정확히 인코딩하여 OCR, 레이아웃 이해에 유리

### 이미지 시퀀스 구성

이미지의 2D 구조를 보존하기 위해 **행 구분자(row separator)** 특수 토큰을 사용한다:

```
[IMG] p11 p12 p13 p14 [ROW] p21 p22 p23 p24 [ROW] p31 p32 p33 p34 [/IMG]
```

여기서 `pij`는 (i행, j열) 패치의 시각 토큰이며, [ROW]는 행 경계를 표시한다. 이 구조적 정보가 LLM에 전달되어 이미지 내 공간 관계를 더 정확히 추론할 수 있다.

### 128K 컨텍스트 다중 이미지

다음 그림은 Pixtral의 전체 멀티모달 파이프라인을 보여준다. 여러 이미지와 텍스트가 하나의 시퀀스로 통합되어 디코더에 입력되는 과정을 확인할 수 있다.

![Pixtral 멀티모달 아키텍처 — 다중 이미지와 텍스트를 하나의 시퀀스로 처리하는 구조](figures/fig_4.png)
*Figure 3: Pixtral 전체 멀티모달 구조 — 비전 인코더가 이미지를 토큰화하고, 텍스트 토큰과 함께 멀티모달 디코더에 입력된다. 128K 컨텍스트 내에서 임의 개수의 이미지를 처리할 수 있다. (Source: arXiv 2410.07073)*

128K 토큰 컨텍스트에서 여러 장의 이미지와 텍스트를 자유롭게 혼합할 수 있다:

```
[문서 1페이지 이미지] [문서 2페이지 이미지] ... [문서 N페이지 이미지]
"이 문서를 요약해주세요."
```

이 능력은 멀티페이지 PDF 분석, 다중 차트 비교, 여러 이미지의 관계 추론 등에서 핵심적이다.

| 구성 요소 | 사양 |
|-----------|------|
| 비전 인코더 | Pixtral ViT (400M, 2D RoPE) |
| LLM | Mistral-NeMo-12B |
| 총 파라미터 | ~12B |
| 컨텍스트 길이 | 131,072 (128K) |
| 패치 크기 | 16×16 |
| 위치 인코딩 | 2D RoPE (비전) + RoPE (텍스트) |

## 핵심 혁신

### 1. 처음부터 학습한 비전 인코더

CLIP이나 SigLIP 같은 기존 인코더를 사용하지 않고, 목적에 최적화된 비전 인코더를 처음부터 학습하였다. 이를 통해 2D RoPE 등 원하는 기법을 자유롭게 적용할 수 있었다. 아래 그래프는 Pixtral ViT가 기존 CLIPA 인코더 대비 문서 이해 태스크에서 얼마나 큰 성능 향상을 보이는지 나타낸다.

![Pixtral ViT vs CLIPA 비전 인코더 성능 비교 — 문서 이해 태스크에서의 정확도 차이](figures/fig_7.png)
*Figure 5: 비전 인코더 ablation 비교 — Pixtral ViT는 ChartQA, DocVQA 등 문서 이해 태스크에서 CLIPA 대비 큰 폭의 성능 향상을 보이며, 자체 학습 인코더의 효과를 입증한다. (Source: arXiv 2410.07073)*

### 2. 2D RoPE

기존 ViT의 1D 위치 인코딩 대비 이미지의 2D 공간 구조를 정확히 인코딩하며, RoPE의 외삽(extrapolation) 특성으로 학습 시보다 큰 해상도의 이미지도 처리 가능하다.

### 3. 긴 컨텍스트 멀티모달

128K 컨텍스트에서 다수 이미지를 처리하는 능력은 실무에서 매우 유용하다. 보고서, 논문, 매뉴얼 등 다중 페이지 문서를 한 번에 분석할 수 있다.

## 벤치마크/성능

Pixtral은 동일 파라미터 규모의 오픈 모델 중에서 멀티모달 벤치마크 성능이 가장 우수하다. 아래 그래프는 모델 크기 대비 성능(MM-MT-Bench)을 비교한 결과이다.

![Pixtral 12B 성능 비교 — MM-MT-Bench에서 동급 모델 대비 최고 성능/비용 효율](figures/fig_1_1.png)
*Figure 4: Pixtral 성능 비교 (MM-MT-Bench) — 12B 파라미터로 72B 모델에 준하는 성능을 달성하며, 동일 규모에서 최고의 성능/비용 효율을 보인다. (Source: arXiv 2410.07073)*

| 벤치마크 | Pixtral-12B | LLaVA-OV-7B | Qwen2-VL-7B |
|----------|-----------|-----------|-----------|
| MMMU | **52.5** | 41.7 | 41.3 |
| MathVista | **58.0** | 57.8 | 58.2 |
| DocVQA | **85.2** | 83.7 | 89.3 |
| ChartQA | **81.8** | 76.3 | 83.0 |
| 다중 이미지 추론 | 강함 | 보통 | 보통 |

## 관련 모델 비교

| 특성 | Pixtral | Qwen2-VL | LLaVA-OV | InternVL 2 |
|------|---------|---------|---------|-----------|
| 비전 인코더 | 자체 학습 (400M) | ViT-675M | SigLIP-400M | InternViT-6B |
| 위치 인코딩 | 2D RoPE | M-RoPE | Learned | Learned |
| 컨텍스트 | 128K | 32K | 32K | 32K |
| 다중 이미지 | 강함 (128K) | 보통 | 보통 | 보통 |
| 임의 해상도 | 네이티브 | 네이티브 | AnyRes | 동적 타일 |

## 학습 상세

2단계 학습:

**Stage 1: 비전 인코더 사전학습**
- 대규모 이미지-텍스트 데이터로 400M 비전 인코더를 처음부터 학습
- 2D RoPE 적용, 다양한 해상도의 이미지 포함

**Stage 2: 멀티모달 통합 학습**
- 비전 인코더 + Mistral-NeMo-12B 통합
- 문서, OCR, 차트, 일반 VQA 데이터 혼합
- 점진적으로 시퀀스 길이를 늘려 128K까지 확장

## 실무 활용

```python
from mistral_inference.transformer import Transformer
from mistral_common.tokens.tokenizers.mistral import MistralTokenizer

tokenizer = MistralTokenizer.from_file("pixtral-12b/tokenizer.model.v1")
model = Transformer.from_folder("pixtral-12b")

# 다중 페이지 문서 분석
images = [Image.open(f"page_{i}.png") for i in range(10)]
prompt = "이 10페이지 문서의 핵심 내용을 요약해주세요."
# ... tokenize and generate
```

## 한계 및 전망

### 한계

1. **비전 인코더 크기**: 400M은 InternViT-6B 대비 작아 매우 세밀한 시각 이해에 한계
2. **비디오 미지원**: 이미지 처리에 특화, 비디오 이해 미구현
3. **Mistral 생태계 의존**: HuggingFace와의 통합이 다른 모델 대비 불완전

### 전망

Pixtral은 이후 Pixtral Large(124B MoE)로 확장되며 Mistral의 멀티모달 라인업을 구축하고 있다. 2D RoPE의 효과가 검증됨에 따라 더 많은 VLM에서 채택될 것으로 예상되며, 128K 멀티모달 컨텍스트는 긴 문서 분석의 새로운 표준이 되고 있다.

Pixtral의 2D RoPE 비전 인코더는 특히 **해상도 외삽(extrapolation)** 능력에서 강점을 보인다. 학습 시 사용된 해상도보다 큰 이미지를 추론 시에 처리해도 성능 저하가 적은데, 이는 RoPE의 위치 외삽 특성 덕분이다. 기존 학습된(learned) 위치 임베딩은 학습 시 본 해상도에만 동작하지만, RoPE는 회전 행렬의 연속성으로 인해 미지의 위치에서도 합리적인 위치 인코딩을 생성한다. 이 특성은 실무에서 매우 실용적이다. 학습 시 1024px까지만 사용했더라도, 추론 시 2048px 이미지를 처리할 수 있어, 고해상도 문서 스캔이나 대형 포스터 분석 등에 유연하게 대응할 수 있기 때문이다.

## 관련 문서

- [[mistral-7b|Mistral 7B]] — 발전 기반
- [[vit|An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale]] — 사용 기법
