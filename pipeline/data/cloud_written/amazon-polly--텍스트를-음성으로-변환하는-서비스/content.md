<!-- infographic-hero -->
![Amazon Polly -- 텍스트를 음성으로 변환하는 서비스 핵심 요약](figures/infographic.svg)

*Figure: Amazon Polly -- 텍스트를 음성으로 변환하는 서비스 한 장 요약 인포그래픽*

## 개요

Amazon Polly는 텍스트를 자연스러운 음성으로 변환하는 완전 관리형 Text-to-Speech(TTS) 서비스입니다. 딥러닝 기반의 음성 합성 기술을 사용하여 사람의 목소리와 유사한 고품질 오디오를 생성합니다. 60개 이상의 언어를 지원하며, 각 언어별로 다양한 음성(Voice)을 선택할 수 있습니다.

TTS 기술은 다양한 분야에서 활용됩니다.

- 접근성(Accessibility): 시각 장애인을 위한 콘텐츠 음성 변환
- IVR(Interactive Voice Response): 콜센터 자동 응답 시스템
- 이러닝(E-learning): 교육 콘텐츠 나레이션
- IoT 기기: 스마트 홈 기기의 음성 인터페이스
- 뉴스/콘텐츠: 기사나 블로그 포스트의 오디오 버전 생성
- 게임: NPC 대사 음성 생성

Amazon Polly는 Standard 엔진과 Neural(NTTS) 엔진, 그리고 최신 Long-Form 엔진과 Generative 엔진을 제공하여 다양한 사용 사례에 최적화된 음성을 생성합니다.

---

## 핵심 기능

### 1. 기본 텍스트-음성 변환

```bash
# 기본 TTS - MP3 파일 생성
aws polly synthesize-speech \
  --text "안녕하세요. Amazon Polly를 활용한 텍스트 음성 변환 테스트입니다." \
  --output-format mp3 \
  --voice-id Seoyeon \
  --engine neural \
  --region us-east-1 \
  output.mp3

# OGG 형식으로 출력 (웹 스트리밍에 적합)
aws polly synthesize-speech \
  --text "웹 브라우저에서 재생하기 좋은 형식입니다." \
  --output-format ogg_vorbis \
  --voice-id Seoyeon \
  --engine neural \
  --region us-east-1 \
  output.ogg

# PCM 형식 (전화 시스템용, 8kHz)
aws polly synthesize-speech \
  --text "전화 시스템에 적합한 형식입니다." \
  --output-format pcm \
  --sample-rate "8000" \
  --voice-id Seoyeon \
  --engine neural \
  --region us-east-1 \
  output.pcm
```

### 2. 사용 가능한 음성 조회

```bash
# 한국어 음성 목록 조회
aws polly describe-voices \
  --language-code ko-KR \
  --region us-east-1 \
  --output table

# Neural 엔진을 지원하는 전체 음성 조회
aws polly describe-voices \
  --engine neural \
  --query 'Voices[*].[Id,Name,LanguageName,Gender,SupportedEngines]' \
  --output table \
  --region us-east-1

# 영어(미국) 음성 중 여성 음성만 조회
aws polly describe-voices \
  --language-code en-US \
  --engine neural \
  --query 'Voices[?Gender==`Female`].[Id,Name]' \
  --output table \
  --region us-east-1
```

### 3. SSML (Speech Synthesis Markup Language)

SSML을 사용하면 음성 합성을 세밀하게 제어할 수 있습니다.

```bash
# SSML을 사용한 음성 합성
aws polly synthesize-speech \
  --text-type ssml \
  --text '<speak>
    <prosody rate="slow">천천히 읽어 드리겠습니다.</prosody>
    <break time="1s"/>
    <prosody rate="fast">이번에는 빠르게 읽어 드리겠습니다.</prosody>
    <break time="500ms"/>
    <emphasis level="strong">이 부분은 강조하여 읽겠습니다.</emphasis>
  </speak>' \
  --output-format mp3 \
  --voice-id Seoyeon \
  --engine neural \
  --region us-east-1 \
  ssml-output.mp3
```

주요 SSML 태그는 다음과 같습니다.

```
<speak>: 루트 요소
<break>: 일시 정지 삽입
  - time="500ms" 또는 time="1s"
  - strength="weak|medium|strong|x-strong"
<prosody>: 음높이, 속도, 볼륨 제어
  - rate="x-slow|slow|medium|fast|x-fast|80%"
  - pitch="x-low|low|medium|high|x-high|+20%"
  - volume="silent|x-soft|soft|medium|loud|x-loud|+6dB"
<emphasis>: 강조
  - level="strong|moderate|reduced"
<phoneme>: 발음 지정
  - alphabet="ipa|x-sampa"
  - ph="발음 기호"
<say-as>: 텍스트 해석 방식 지정
  - interpret-as="characters|spell-out|cardinal|ordinal|digits|fraction|unit|date|time|telephone|address"
<sub>: 대체 텍스트 발음
  - alias="대체 텍스트"
<lang>: 언어 전환
  - xml:lang="en-US"
<mark>: 음성 마크 (위치 동기화용)
  - name="마크이름"
```

```python
import boto3

polly = boto3.client('polly', region_name='us-east-1')

ssml_text = '''
<speak>
  <p>Amazon Polly는 다양한 SSML 기능을 지원합니다.</p>
  
  <p>숫자 읽기: <say-as interpret-as="cardinal">12345</say-as></p>
  
  <p>날짜 읽기: <say-as interpret-as="date" format="ymd">2024-03-15</say-as></p>
  
  <p>전화번호: <say-as interpret-as="telephone">010-1234-5678</say-as></p>
  
  <p>영어 발음 포함: 
    <lang xml:lang="en-US">Amazon Web Services</lang>는 
    클라우드 서비스 제공자입니다.
  </p>
  
  <p>
    <prosody volume="loud" rate="110%">
      이 문장은 조금 크고 빠르게 읽습니다.
    </prosody>
  </p>
</speak>
'''

response = polly.synthesize_speech(
    Text=ssml_text,
    TextType='ssml',
    OutputFormat='mp3',
    VoiceId='Seoyeon',
    Engine='neural'
)

with open('ssml-output.mp3', 'wb') as f:
    f.write(response['AudioStream'].read())

print(f"콘텐츠 타입: {response['ContentType']}")
print(f"요청 문자 수: {response['RequestCharacters']}")
```

### 4. Speech Marks (음성 마크)

음성 마크는 오디오 스트림 내 특정 위치 정보를 제공하여, 립싱크, 자막 동기화, 단어 하이라이트 등에 활용됩니다.

```bash
# Speech Marks 생성 (단어별 타이밍 정보)
aws polly synthesize-speech \
  --text "Amazon Polly는 텍스트를 음성으로 변환합니다." \
  --output-format json \
  --voice-id Seoyeon \
  --engine neural \
  --speech-mark-types '["word", "sentence"]' \
  --region us-east-1 \
  speech-marks.json
```

출력 형식은 다음과 같습니다.

```json
{"time": 0, "type": "sentence", "start": 0, "end": 28, "value": "Amazon Polly는 텍스트를 음성으로 변환합니다."}
{"time": 0, "type": "word", "start": 0, "end": 6, "value": "Amazon"}
{"time": 325, "type": "word", "start": 7, "end": 12, "value": "Polly"}
{"time": 610, "type": "word", "start": 12, "end": 14, "value": "는"}
```

### 5. 비동기 음성 합성 (Speech Synthesis Task)

긴 텍스트의 경우 비동기 작업으로 처리하여 S3에 저장합니다.

```bash
# 비동기 음성 합성 작업 시작
aws polly start-speech-synthesis-task \
  --text "여기에 아주 긴 텍스트가 들어갑니다. 책 한 챕터 분량의 텍스트도 처리할 수 있습니다..." \
  --output-format mp3 \
  --output-s3-bucket-name "my-polly-output" \
  --output-s3-key-prefix "audiobooks/" \
  --voice-id Seoyeon \
  --engine neural \
  --region us-east-1

# 작업 상태 확인
aws polly get-speech-synthesis-task \
  --task-id "task-abc123" \
  --region us-east-1

# 모든 비동기 작업 목록 조회
aws polly list-speech-synthesis-tasks \
  --status "completed" \
  --region us-east-1
```

### 6. 발음 사전 (Lexicon)

특정 단어나 약어의 발음을 커스터마이징합니다.

```bash
# 발음 사전 등록
aws polly put-lexicon \
  --name "TechTermsKorean" \
  --content '<?xml version="1.0" encoding="UTF-8"?>
<lexicon version="1.0"
  xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.w3.org/2005/01/pronunciation-lexicon"
  alphabet="ipa" xml:lang="ko-KR">
  <lexeme>
    <grapheme>AWS</grapheme>
    <alias>에이 더블유 에스</alias>
  </lexeme>
  <lexeme>
    <grapheme>API</grapheme>
    <alias>에이 피 아이</alias>
  </lexeme>
  <lexeme>
    <grapheme>SDK</grapheme>
    <alias>에스 디 케이</alias>
  </lexeme>
</lexicon>' \
  --region us-east-1

# 발음 사전을 적용하여 음성 합성
aws polly synthesize-speech \
  --text "AWS SDK를 사용하여 API를 호출합니다." \
  --output-format mp3 \
  --voice-id Seoyeon \
  --engine neural \
  --lexicon-names '["TechTermsKorean"]' \
  --region us-east-1 \
  lexicon-output.mp3

# 등록된 발음 사전 조회
aws polly list-lexicons --region us-east-1
```

---

## 아키텍처/동작 원리

### Amazon Polly 서비스 아키텍처

```
[클라이언트]
    |
    v
[Amazon Polly API]
    |
    +---> [텍스트 전처리]
    |       +--- 텍스트 정규화 (숫자, 날짜, 약어 변환)
    |       +--- SSML 파싱
    |       +--- Lexicon 적용
    |
    +---> [음성 합성 엔진]
    |       +--- Standard Engine (연결 합성 방식)
    |       +--- Neural Engine (딥러닝 기반 NTTS)
    |       +--- Long-Form Engine (긴 텍스트 최적화)
    |       +--- Generative Engine (최고 품질)
    |
    +---> [오디오 인코딩]
    |       +--- MP3 (범용)
    |       +--- OGG Vorbis (웹 스트리밍)
    |       +--- PCM (원시 오디오)
    |       +--- JSON (Speech Marks)
    |
    +---> [출력]
            +--- 실시간 스트리밍 응답
            +--- S3 저장 (비동기 작업)
```

### 엔진별 특성 비교

| 엔진 | 특징 | 적합한 사용 사례 | 비용 |
|------|------|------------------|------|
| Standard | 연결 합성 방식, 빠른 처리 | 대용량 처리, 비용 민감한 워크로드 | 낮음 |
| Neural (NTTS) | 딥러닝 기반, 자연스러운 음성 | 범용 TTS, 대부분의 사용 사례 | 중간 |
| Long-Form | 긴 텍스트에 최적화된 운율 | 오디오북, 긴 기사 읽기 | 중간 |
| Generative | 최신 생성형 AI 기반, 최고 품질 | 고품질 콘텐츠, 브랜드 음성 | 높음 |

### 실시간 스트리밍 처리

Polly는 전체 텍스트의 처리가 완료되기 전에 오디오 스트리밍을 시작할 수 있어, 대화형 애플리케이션에서 낮은 지연 시간을 제공합니다.

```python
import boto3

polly = boto3.client('polly', region_name='us-east-1')

# 스트리밍 응답 처리
response = polly.synthesize_speech(
    Text='긴 텍스트를 스트리밍 방식으로 처리합니다...',
    OutputFormat='mp3',
    VoiceId='Seoyeon',
    Engine='neural'
)

# 스트림 읽기
audio_stream = response['AudioStream']
chunk_size = 1024

with open('streamed-output.mp3', 'wb') as f:
    while True:
        chunk = audio_stream.read(chunk_size)
        if not chunk:
            break
        f.write(chunk)
```

---

## 실전 활용

### 사례 1: 블로그 포스트 오디오 변환 시스템

```python
import boto3
import re

def blog_to_audio(title, content, output_bucket, output_key):
    """
    블로그 포스트를 오디오 파일로 변환합니다.
    """
    polly = boto3.client('polly', region_name='us-east-1')
    
    # HTML/Markdown 태그 제거
    clean_text = re.sub(r'<[^>]+>', '', content)
    clean_text = re.sub(r'[#*`]', '', clean_text)
    
    # 코드 블록 제거
    clean_text = re.sub(r'```[\s\S]*?```', '코드 블록이 생략되었습니다.', clean_text)
    
    # SSML 구성
    ssml_text = f'''<speak>
        <prosody rate="95%">
            <p><emphasis level="strong">{title}</emphasis></p>
            <break time="1s"/>
            {clean_text}
        </prosody>
    </speak>'''
    
    # 비동기 작업으로 생성 (긴 텍스트)
    response = polly.start_speech_synthesis_task(
        Text=ssml_text,
        TextType='ssml',
        OutputFormat='mp3',
        OutputS3BucketName=output_bucket,
        OutputS3KeyPrefix=output_key,
        VoiceId='Seoyeon',
        Engine='long-form'
    )
    
    return response['SynthesisTask']['TaskId']
```

### 사례 2: 다국어 IVR 시스템

```python
import boto3

def generate_ivr_prompts():
    polly = boto3.client('polly', region_name='us-east-1')
    
    prompts = {
        'welcome_ko': {
            'text': '<speak>전화 주셔서 감사합니다. <break time="300ms"/> '
                    '상담원 연결은 <say-as interpret-as="cardinal">1</say-as>번, '
                    '주문 조회는 <say-as interpret-as="cardinal">2</say-as>번을 '
                    '눌러 주십시오.</speak>',
            'voice': 'Seoyeon',
            'lang': 'ko-KR'
        },
        'welcome_en': {
            'text': '<speak>Thank you for calling. <break time="300ms"/> '
                    'For agent, press <say-as interpret-as="cardinal">1</say-as>. '
                    'For order inquiry, press <say-as interpret-as="cardinal">2</say-as>.</speak>',
            'voice': 'Joanna',
            'lang': 'en-US'
        },
        'welcome_ja': {
            'text': '<speak>お電話ありがとうございます。<break time="300ms"/>'
                    'オペレーターは<say-as interpret-as="cardinal">1</say-as>番、'
                    '注文照会は<say-as interpret-as="cardinal">2</say-as>番を'
                    '押してください。</speak>',
            'voice': 'Mizuki',
            'lang': 'ja-JP'
        }
    }
    
    for name, config in prompts.items():
        response = polly.synthesize_speech(
            Text=config['text'],
            TextType='ssml',
            OutputFormat='pcm',
            SampleRate='8000',
            VoiceId=config['voice'],
            Engine='neural'
        )
        
        with open(f'{name}.pcm', 'wb') as f:
            f.write(response['AudioStream'].read())
        
        print(f"생성 완료: {name} ({config['lang']})")
```

---

## 모범 사례/보안

### 성능 최적화

- 3,000자 이상의 텍스트는 비동기 작업(StartSpeechSynthesisTask)을 사용합니다.
- 자주 사용되는 문구는 오디오를 캐싱하여 반복 API 호출을 줄입니다.
- 웹 애플리케이션에서는 OGG Vorbis 형식을 사용하여 파일 크기를 최적화합니다.
- Speech Marks를 활용할 때는 오디오 출력과 별도의 요청으로 분리하여 처리합니다.

### 보안 설정

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "polly:SynthesizeSpeech",
        "polly:DescribeVoices"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "polly:StartSpeechSynthesisTask",
        "polly:GetSpeechSynthesisTask"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "polly:OutputS3BucketName": "my-polly-output"
        }
      }
    }
  ]
}
```

### 비용 최적화

| 엔진 | 가격 (100만 자당, us-east-1) |
|------|-----------------------------|
| Standard | $4.00 |
| Neural | $16.00 |
| Long-Form | $100.00 |
| Generative | $30.00 |

- 품질 요구사항이 낮은 내부용 오디오에는 Standard 엔진을 사용합니다.
- 자주 재사용되는 오디오는 S3에 캐싱하여 중복 호출을 방지합니다.
- Free Tier: 처음 12개월간 매월 Standard 500만 자, Neural 100만 자 무료입니다.

---

## 관련 서비스 비교

| 항목 | Amazon Polly | Google Cloud TTS | Azure Speech | ElevenLabs |
|------|-------------|------------------|--------------|------------|
| 엔진 유형 | Standard/Neural/Long-Form/Generative | Standard/WaveNet/Neural2 | Neural/Custom Neural | 생성형 AI |
| 한국어 음성 | 1개 (Seoyeon) | 다수 | 다수 | 제한적 |
| SSML 지원 | 전체 지원 | 전체 지원 | 전체 지원 | 제한적 |
| 음성 복제 | 미지원 | 미지원 | Custom Neural Voice | 지원 |
| Speech Marks | 지원 | Timepoint 지원 | Viseme 지원 | 미지원 |
| 비동기 처리 | 지원 (S3 출력) | 지원 (GCS 출력) | Batch 지원 | 미지원 |
| 발음 사전 | Lexicon 지원 | 미지원 | 제한적 지원 | 미지원 |
| AWS 통합 | 네이티브 | SDK 기반 | SDK 기반 | SDK 기반 |

---

## 요약

Amazon Polly는 텍스트를 자연스러운 음성으로 변환하는 완전 관리형 TTS 서비스입니다. 주요 특징을 정리하면 다음과 같습니다.

- Standard, Neural, Long-Form, Generative 4가지 엔진을 제공하여 사용 사례와 비용에 맞는 최적의 음성 품질을 선택할 수 있습니다.
- SSML을 통해 발화 속도, 음높이, 볼륨, 강조, 일시 정지 등을 세밀하게 제어합니다.
- 60개 이상의 언어와 다양한 음성을 지원하며, 한국어는 Seoyeon 음성을 제공합니다.
- Speech Marks를 통해 오디오 내 단어별 타이밍 정보를 제공하여 자막 동기화, 립싱크에 활용합니다.
- Lexicon(발음 사전)으로 특정 단어의 발음을 커스터마이징할 수 있습니다.
- 비동기 Speech Synthesis Task를 통해 긴 텍스트를 S3에 자동 저장합니다.

Amazon Polly는 접근성 향상, IVR 시스템, 콘텐츠 오디오화, 이러닝 등 음성 인터페이스가 필요한 모든 애플리케이션에서 핵심적인 역할을 수행합니다.