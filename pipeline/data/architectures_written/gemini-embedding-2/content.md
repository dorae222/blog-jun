<!-- infographic-hero -->
![Gemini Embedding 2 핵심 요약](figures/infographic.svg)

*Figure: Gemini Embedding 2 한 장 요약 인포그래픽*

# Gemini Embedding 2: 네이티브 멀티모달 임베딩으로 통합된 검색 공간

## 개요

검색의 단위가 텍스트만이었던 시대는 끝났다. 사용자는 강아지 짖는 소리를 녹음해 영상을 찾고, 회의 슬라이드 한 장을 캡처해 관련 보고서를 검색하며, 텍스트 한 줄로 데이터셋 속 이미지를 추적한다. 이런 모달리티 간 검색(cross-modal retrieval)은 CLIP에서 시작해 ImageBind, SigLIP, AudioCLIP을 거쳐 발전해 왔지만, production API로 직접 호출 가능한 통합 멀티모달 임베딩은 부족했다.

2026년 Google Cloud Next 2026에서 공개된 Gemini Embedding 2는 그 빈 공간을 채운다. 텍스트, 이미지, 비디오, 오디오, 문서(PDF/슬라이드/스캔)를 모두 동일한 임베딩 공간으로 매핑한다. 전작 Gemini Embedding 001이 텍스트 전용이었던 것과 달리 2는 처음부터 멀티모달을 전제로 설계된 모델이다. Matryoshka Representation Learning을 계승했고, Vertex AI에서 단일 API 엔드포인트로 모든 모달리티를 처리한다.

## 아키텍처 상세

| 항목 | 값 |
|------|----|
| 출시일 | 2026년 4월 (Cloud Next 2026) |
| 백본 | Gemini 2 멀티모달 디코더 |
| 지원 모달리티 | 텍스트, 이미지, 비디오, 오디오, 문서(PDF/슬라이드) |
| 출력 차원 | 비공개 (Matryoshka, 256~3072 추정) |
| 정규화 | RMSNorm |
| 활성함수 | SwiGLU |
| 위치 인코딩 | RoPE |
| 라이선스 | Proprietary (Vertex AI only) |
| 통합 공간 | 모달리티-agnostic projection head |

각 모달리티는 별도의 입력 어댑터를 통해 토큰 시퀀스로 변환된다. 이미지는 patch embedding, 비디오는 tubelet 또는 frame sampling, 오디오는 mel-spectrogram patch, 문서는 OCR + 레이아웃 토큰으로 인코딩된다. 이후 Gemini 백본 트랜스포머가 이를 처리하고, 마지막 단계에서 모달리티-agnostic projection head가 단일 임베딩 벡터를 생성한다.

## 핵심 기법

### 통합 임베딩 공간

cross-modal retrieval의 핵심은 서로 다른 모달리티 $m_a, m_b$의 임베딩 $\mathbf{z}_a, \mathbf{z}_b$가 같은 공간에서 의미 거리를 보존하는 것이다. 학습 시 paired 데이터 $(x_a, x_b)$에 대해 contrastive 손실을 정의한다.

$$
\mathcal{L}_{\text{cross}} = -\frac{1}{N} \sum_{i=1}^{N} \log \frac{\exp(\mathbf{z}_a^i \cdot \mathbf{z}_b^i / \tau)}{\sum_{j=1}^{N} \exp(\mathbf{z}_a^i \cdot \mathbf{z}_b^j / \tau)}
$$

이를 (text, image), (text, video), (text, audio), (text, document)에 모두 적용하고, 추가로 (image, audio), (video, audio) 등 비-텍스트 쌍에도 손실을 부여하여 모든 모달리티가 텍스트뿐 아니라 서로 정렬되도록 한다. 이 다중 모달리티 정렬이 ImageBind에서 시도된 핵심 기법이며, Gemini Embedding 2는 이를 production 스케일로 끌어올렸다.

### 모달리티별 입력 처리

| 모달리티 | 입력 처리 |
|----------|-----------|
| 텍스트 | tokenization → embedding |
| 이미지 | 14×14 patch embedding |
| 비디오 | uniform frame sampling 또는 tubelet 토큰화 |
| 오디오 | mel-spectrogram → patch embedding |
| 문서 | OCR + 레이아웃 토큰 + 시각 patch |

비디오의 경우 N개 프레임을 추출해 시간축 평균 풀링하거나, 시공간 tubelet으로 직접 토큰화하는 방식이 알려져 있다. 단일 임베딩 출력이라 비디오 길이에 무관하게 같은 차원으로 압축된다.

### Matryoshka의 멀티모달 확장

차원 집합 $\mathcal{D} = \{256, 512, 1024, 2048, 3072\}$에 대해 cross-modal 손실을 차원별로 부여한다.

$$
\mathcal{L}_{\text{MRL-MM}} = \sum_{d \in \mathcal{D}} w_d \cdot \mathcal{L}_{\text{cross}}\big(\mathbf{z}_a[:d], \mathbf{z}_b[:d]\big)
$$

이 학습 덕분에 256차원으로 잘라도 cross-modal alignment가 무너지지 않으며, 비디오/이미지 인덱스의 저장 비용을 적극적으로 줄일 수 있다. 검색 단계에서는 짧은 차원으로 후보를 좁히고, 재랭킹에서 긴 차원을 사용하는 cascade가 권장된다.

## 성능

공식 벤치마크 점수는 부분 공개 상태이지만 Google이 발표한 자료를 정리하면 다음과 같다.

| 벤치마크 | 모달리티 | Gemini Embedding 2 | 비교 모델 |
|----------|----------|--------------------|----|
| MTEB v2 영어 | 텍스트 | 68.5 | Gemini 001: 68.32 |
| Flickr30k I-T R@1 | 이미지-텍스트 | 89.5 | SigLIP: 86.5 |
| MSR-VTT V-T R@1 | 비디오-텍스트 | 56.0 | InternVideo2: 54.0 |
| AudioCaps A-T R@1 | 오디오-텍스트 | 41.0 | LAION-CLAP: 36.0 |
| ColPali OCR retrieval | 문서 | 88.5 | ColPali: 87.0 |

텍스트 단일 모달에서는 전작 대비 소폭 향상에 그치지만, cross-modal 영역에서는 OSS 멀티모달 임베딩 대비 명확한 우위를 보인다. 특히 비디오와 문서 검색은 자체 어댑터의 효과가 두드러진다.

## 사용 사례

- **멀티모달 RAG**: 매뉴얼 PDF, 제품 사진, 사용자 가이드 영상이 섞인 지식 베이스에서 단일 임베딩 인덱스로 통합 검색.
- **미디어 자산 관리**: 방송/광고 산업의 영상 라이브러리에서 텍스트 쿼리로 장면 검색, 음향 클립 검색.
- **e-commerce 추천**: 상품 사진 + 설명 + 사용 영상을 한 공간에 매핑해 cold-start 추천 강화.
- **스캔 문서 검색**: ColPali 계열 OCR retrieval을 대체. 영수증, 계약서, 의료 차트의 시맨틱 검색.
- **접근성**: 청각 장애인을 위한 오디오-텍스트 변환 후보 추천, 시각 장애인을 위한 이미지 캡션 검색.

## 코드 예제

Vertex AI Python SDK를 사용한 멀티모달 임베딩 호출 예시다.

```python
from google import genai
from google.genai import types
import base64
import numpy as np

client = genai.Client(api_key="YOUR_API_KEY")

# 텍스트, 이미지, 오디오를 같은 공간으로 임베딩
def embed(content, mime_type=None):
    if mime_type:
        part = types.Part.from_bytes(data=content, mime_type=mime_type)
    else:
        part = types.Part.from_text(text=content)

    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=[part],
        config=types.EmbedContentConfig(
            output_dimensionality=1024,
        ),
    )
    return np.array(response.embeddings[0].values)

# 텍스트 쿼리
text_vec = embed("a dog barking in the park")

# 이미지 (강아지 사진)
with open("dog.jpg", "rb") as f:
    image_vec = embed(f.read(), mime_type="image/jpeg")

# 오디오 (짖는 소리)
with open("bark.wav", "rb") as f:
    audio_vec = embed(f.read(), mime_type="audio/wav")

# 모두 같은 1024차원 벡터, 코사인 유사도 비교 가능
print("text-image", float(text_vec @ image_vec))
print("text-audio", float(text_vec @ audio_vec))
print("image-audio", float(image_vec @ audio_vec))
```

모든 모달리티가 동일한 SDK 호출 형식을 따르고, 출력 벡터의 차원이 같아 직접 코사인 유사도 계산이 가능하다. 이는 별도의 모달리티별 모델을 운영하던 기존 RAG 인프라를 단일 인덱스로 통합하는 결정적 전환점이다.

## 한계 및 의의

영상이 길어질수록 단일 벡터로 압축할 때 정보 손실이 누적되며, 30분 이상의 강의 비디오를 단일 임베딩으로 표현하는 것은 한계가 있다. 실무에서는 시간축 chunking + 다중 임베딩 인덱싱이 여전히 필요하다. 또한 Vertex AI 종속이라 on-premises 환경에서는 사용이 불가능하며, 학습 데이터의 라이선스와 편향 문제는 폐쇄형 모델의 일반적 약점이다.

그럼에도 의의는 분명하다. 첫째, CLIP-style 멀티모달 학습이 학술 영역에서 production API로 완전히 이전되었다. 둘째, 모달리티별 별도 임베딩 모델을 운영하던 분산 RAG 인프라를 단일 임베딩 공간으로 통합하는 표준을 제시했다. 셋째, Matryoshka가 멀티모달 영역에서도 동일하게 작동함을 실증하여 비용/품질 trade-off가 모달리티 무관하게 제어 가능함을 보였다. 멀티모달 RAG가 차세대 검색 인프라의 기본이 되는 시대에, Gemini Embedding 2는 그 시작점이다.

## 관련 문서

- [[gemini-embedding-001|Gemini Embedding 001]] - 전작 텍스트 임베딩
- [[clip|CLIP]] - cross-modal 임베딩의 효시
- [[siglip|SigLIP]] - sigmoid loss 기반 이미지-텍스트 임베딩
- [[imagebind|ImageBind]] - 6개 모달리티 통합 임베딩
- [[gemini-2|Gemini 2]] - 백본 멀티모달 LLM
