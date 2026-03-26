# AWS Panorama 개요 및 활용 가이드

## 개요

AWS Panorama는 온프레미스 환경에 설치된 IP 카메라의 영상 스트림을 대상으로 컴퓨터 비전(Computer Vision) 모델을 실행할 수 있게 해주는 머신러닝 어플라이언스 서비스입니다. 기존에 클라우드로 영상 데이터를 전송하여 분석하던 방식과 달리, Panorama는 엣지 디바이스에서 직접 추론을 수행하므로 저지연(Low Latency) 처리가 가능하고, 네트워크 대역폭 사용량을 획기적으로 줄일 수 있습니다.

제조업, 소매업, 물류, 헬스케어 등 다양한 산업에서 영상 기반 자동화 수요가 급증하고 있으며, AWS Panorama는 이러한 수요에 대응하기 위해 설계된 서비스입니다. 특히 보안 규정상 영상 데이터를 클라우드로 전송할 수 없는 환경에서도 AI 기반 영상 분석을 적용할 수 있다는 점이 핵심 강점입니다.

---

## 핵심 기능

### 엣지 디바이스 기반 추론

AWS Panorama Appliance는 NVIDIA GPU가 탑재된 전용 하드웨어 디바이스입니다. 이 디바이스에 컴퓨터 비전 모델을 배포하면, 연결된 IP 카메라의 RTSP 스트림을 로컬에서 직접 분석합니다. 클라우드 연결 없이도 추론이 가능하므로, 네트워크 장애 시에도 서비스가 중단되지 않습니다.

| 항목 | 사양 |
|------|------|
| GPU | NVIDIA Xavier 기반 |
| 지원 카메라 수 | 최대 8대 동시 스트림 |
| 영상 프로토콜 | RTSP |
| 네트워크 | 유선 이더넷 (PoE 지원) |
| 운영체제 | Linux 기반 커스텀 OS |

### 모델 배포 및 관리

AWS 콘솔 또는 API를 통해 학습된 모델을 엣지 디바이스로 원격 배포할 수 있습니다. SageMaker에서 학습한 모델을 직접 Panorama로 배포하는 워크플로우가 지원되며, 모델 버전 관리와 롤백도 가능합니다.

### 실시간 스트리밍 처리

카메라 영상 입력을 프레임 단위로 분석하여, 객체 감지(Object Detection), 이미지 분류(Classification), 세그멘테이션(Segmentation) 등 다양한 비전 태스크를 실시간으로 수행합니다. 분석 결과(메타데이터, 이벤트)는 AWS IoT Core, CloudWatch, S3 등으로 전송할 수 있습니다.

### AWS 서비스 통합

| 통합 서비스 | 역할 |
|-------------|------|
| Amazon SageMaker | 모델 학습 및 최적화 |
| Amazon S3 | 모델 아티팩트 저장, 분석 결과 저장 |
| AWS IoT Core | 디바이스 관리, 이벤트 라우팅 |
| Amazon CloudWatch | 디바이스 모니터링 및 로깅 |
| AWS Lambda | 이벤트 기반 후처리 로직 실행 |

### 보안 및 오프라인 동작

모델 전송 시 암호화(TLS)를 적용하며, 디바이스 인증에는 X.509 인증서를 사용합니다. 클라우드와 연결이 끊기더라도 로컬에서 추론을 계속 수행할 수 있어, 민감한 영상 데이터가 외부로 유출되지 않습니다.

---

## 아키텍처 / 동작 원리

AWS Panorama의 전체 아키텍처는 크게 클라우드 측과 엣지 측으로 나뉩니다.

```text
[클라우드 측]
  SageMaker (모델 학습)
       |
       v
  S3 (모델 아티팩트 저장)
       |
       v
  Panorama 콘솔 (앱 배포 관리)
       |
  ===== 네트워크 =====
       |
[엣지 측]
  Panorama Appliance
       |
       +--- IP Camera 1 (RTSP)
       +--- IP Camera 2 (RTSP)
       +--- IP Camera N (RTSP)
       |
       v
  로컬 추론 엔진 (GPU)
       |
       v
  분석 결과 → IoT Core / CloudWatch / S3
```

### 동작 흐름

1. **모델 준비**: SageMaker에서 컴퓨터 비전 모델을 학습하고, SageMaker Neo를 통해 엣지 디바이스에 최적화된 형태로 컴파일합니다.
2. **애플리케이션 패키징**: Panorama SDK를 사용하여 모델과 비즈니스 로직을 하나의 애플리케이션으로 패키징합니다.
3. **배포**: AWS Panorama 콘솔에서 타겟 디바이스를 선택하고 애플리케이션을 배포합니다.
4. **실행**: Panorama Appliance가 IP 카메라의 RTSP 스트림을 수신하고, GPU에서 프레임 단위 추론을 실행합니다.
5. **결과 전송**: 분석 결과(감지된 객체, 이벤트 등)를 IoT Core를 통해 클라우드로 전달하거나, 로컬 대시보드에 표시합니다.

### Panorama Application 구조

Panorama 애플리케이션은 다음 구성 요소로 이루어져 있습니다.

- **모델 노드(Model Node)**: ML 모델을 캡슐화한 컴포넌트
- **코드 노드(Code Node)**: Python 기반 비즈니스 로직 (전처리, 후처리)
- **카메라 노드(Camera Node)**: 영상 입력 소스 정의
- **출력 노드(Output Node)**: 결과를 디스플레이 또는 외부 서비스로 전달

---

## 실전 활용

### Panorama Appliance 프로비저닝

Panorama Appliance를 AWS 계정에 등록하는 과정은 AWS CLI를 통해 수행할 수 있습니다.

```bash
# Panorama 디바이스 등록
aws panorama create-node-from-template-job \
  --template-type RTSP_CAMERA_STREAM \
  --output-package-name my-camera \
  --output-package-version "1.0" \
  --node-name my-camera-node \
  --template-parameters '{"Username":"admin","Password":"password123","StreamUrl":"rtsp://192.168.1.100:554/stream"}'
```

### 디바이스 목록 조회

```bash
# 등록된 Panorama 디바이스 목록 조회
aws panorama list-devices

# 특정 디바이스 상세 정보 확인
aws panorama describe-device \
  --device-id device-xxxxxxxxxxxx
```

### 애플리케이션 배포

```bash
# 애플리케이션 인스턴스 생성 (배포)
aws panorama create-application-instance \
  --name "defect-detection-app" \
  --manifest-payload '{"PayloadData": "..."}' \
  --default-runtime-context-device device-xxxxxxxxxxxx \
  --description "제조 라인 불량품 감지 애플리케이션"

# 배포 상태 확인
aws panorama describe-application-instance \
  --application-instance-id instance-xxxxxxxxxxxx
```

### Python SDK를 활용한 Panorama 애플리케이션 코드 예시

```python
import panoramasdk
import cv2
import numpy as np

class Application(panoramasdk.node):
    def __init__(self):
        super().__init__()
        self.model = self.inputs.model.get()
    
    def process_streams(self):
        streams = self.inputs.video_in.get()
        
        for stream in streams:
            image = stream.image
            # 전처리
            resized = cv2.resize(image, (300, 300))
            normalized = resized.astype(np.float32) / 255.0
            
            # 모델 추론
            result = self.model.run(normalized)
            
            # 결과 처리
            detections = self.parse_detections(result)
            for det in detections:
                if det['confidence'] > 0.8:
                    self.send_alert(det)
            
            # 출력 스트림에 결과 오버레이
            stream.add_rect(det['bbox'][0], det['bbox'][1],
                           det['bbox'][2], det['bbox'][3])
        
        self.outputs.video_out.put(streams)
    
    def send_alert(self, detection):
        # IoT Core로 이벤트 전송
        self.call(
            "iot_publish",
            topic="panorama/alerts",
            payload=str(detection)
        )

def main():
    app = Application()
    while True:
        app.process_streams()

main()
```

### 활용 시나리오별 구현 가이드

#### 제조/공장 자동화

생산 라인에 설치된 카메라를 통해 제품의 외관 불량을 실시간으로 감지합니다. 불량이 감지되면 IoT Core를 통해 PLC(Programmable Logic Controller)에 신호를 보내 해당 제품을 라인에서 제거할 수 있습니다.

#### 소매점 분석

매장 내 카메라를 활용하여 고객 동선을 추적하고, 특정 진열대 앞에서의 체류 시간을 측정합니다. 이 데이터를 CloudWatch Metrics로 전송하면 시간대별 매장 혼잡도 대시보드를 구성할 수 있습니다.

#### 교통 및 안전 감시

주차장 카메라를 분석하여 빈 주차 공간을 실시간으로 파악하거나, 보안 카메라에서 무단 침입을 감지하여 즉시 알람을 발생시킬 수 있습니다.

#### 헬스케어 적용

병원 내 환자 낙상을 실시간으로 감지하거나, 멸균실의 위생 프로토콜 준수 여부(마스크 착용, 장갑 착용 등)를 자동으로 모니터링합니다.

---

## 모범 사례 및 보안

### 모델 최적화

엣지 디바이스는 클라우드 GPU에 비해 컴퓨팅 리소스가 제한적입니다. 따라서 다음과 같은 최적화를 적용하는 것이 중요합니다.

- **SageMaker Neo 컴파일**: 모델을 타겟 하드웨어에 최적화된 형태로 변환합니다.
- **모델 경량화**: MobileNet, EfficientNet-Lite 등 경량 아키텍처를 사용합니다.
- **양자화(Quantization)**: FP32 모델을 INT8로 변환하여 추론 속도를 높입니다.
- **입력 해상도 조정**: 불필요하게 높은 해상도는 추론 속도를 저하시킵니다.

### 네트워크 및 디바이스 보안

| 보안 영역 | 권장 사항 |
|-----------|----------|
| 디바이스 인증 | X.509 인증서 기반 상호 인증 사용 |
| 데이터 전송 | TLS 1.2 이상 암호화 적용 |
| 네트워크 격리 | 카메라 네트워크를 별도 VLAN으로 분리 |
| IAM 권한 | 최소 권한 원칙 적용 (Panorama 전용 IAM Role) |
| 펌웨어 업데이트 | OTA(Over-the-Air) 업데이트 활성화 |
| 물리 보안 | 디바이스 접근 통제 및 잠금 장치 사용 |

### IAM 정책 예시

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "panorama:DescribeDevice",
        "panorama:ListDevices",
        "panorama:CreateApplicationInstance",
        "panorama:DescribeApplicationInstance"
      ],
      "Resource": "arn:aws:panorama:ap-northeast-2:123456789012:device/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::my-panorama-models/*"
    }
  ]
}
```

### 운영 모니터링

- **CloudWatch 연동**: 디바이스 상태(CPU, GPU, 메모리 사용률), 추론 지연 시간, 에러율 등을 모니터링합니다.
- **CloudWatch Alarms**: 디바이스 오프라인, 높은 에러율 등에 대해 알람을 설정합니다.
- **로컬 로깅**: 네트워크 장애 시에도 로그를 로컬에 저장하고, 연결 복구 시 클라우드로 동기화합니다.

```bash
# CloudWatch에서 Panorama 디바이스 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace "AWS/Panorama" \
  --metric-name "InferenceLatency" \
  --dimensions Name=DeviceId,Value=device-xxxxxxxxxxxx \
  --start-time 2026-03-22T00:00:00Z \
  --end-time 2026-03-23T00:00:00Z \
  --period 3600 \
  --statistics Average
```

---

## 관련 서비스 비교

| 항목 | AWS Panorama | Amazon Rekognition | AWS DeepLens | Amazon Lookout for Vision |
|------|-------------|-------------------|-------------|-------------------------|
| 실행 위치 | 엣지 (온프레미스) | 클라우드 | 엣지 (단일 카메라) | 클라우드 |
| 주요 용도 | 다중 카메라 실시간 분석 | 이미지/비디오 분석 API | 학습용/프로토타입 | 산업 불량 감지 |
| 커스텀 모델 | 지원 (SageMaker) | 제한적 (Custom Labels) | 지원 | 지원 |
| 확장성 | 디바이스 추가로 확장 | 클라우드 자동 확장 | 단일 디바이스 | 클라우드 자동 확장 |
| 오프라인 동작 | 가능 | 불가 | 제한적 | 불가 |
| 지연 시간 | 매우 낮음 (로컬) | 높음 (네트워크 의존) | 낮음 (로컬) | 높음 (네트워크 의존) |
| 카메라 수 | 최대 8대/디바이스 | 제한 없음 (API) | 1대 | 제한 없음 (API) |
| 과금 방식 | 디바이스 구매 + 사용료 | API 호출 기반 | 디바이스 구매 | 추론 시간 기반 |

### 서비스 선택 가이드

- **엣지에서 다중 카메라를 실시간 분석**해야 한다면 **AWS Panorama**를 선택합니다.
- **이미 촬영된 이미지/비디오를 분석**하거나, **얼굴 인식/텍스트 감지** 등이 필요하다면 **Amazon Rekognition**이 적합합니다.
- **산업 환경의 제품 불량 감지**에 특화된 서비스가 필요하다면 **Amazon Lookout for Vision**을 고려합니다.
- **ML 학습 및 프로토타이핑** 목적이라면 **AWS DeepLens**(단종 예정)보다는 SageMaker + Panorama 조합을 권장합니다.

---

## 요약

AWS Panorama는 온프레미스 환경에서 IP 카메라 영상을 실시간으로 분석할 수 있는 엣지 컴퓨터 비전 플랫폼입니다. 주요 특징을 정리하면 다음과 같습니다.

| 항목 | 내용 |
|------|------|
| 서비스 유형 | 엣지 기반 컴퓨터 비전 어플라이언스 |
| 핵심 가치 | 저지연 실시간 영상 분석, 네트워크 비용 절감, 데이터 프라이버시 보호 |
| 주요 구성 | Panorama Appliance, Panorama SDK, AWS 콘솔 |
| 통합 서비스 | SageMaker, IoT Core, S3, CloudWatch, Lambda |
| 주요 활용처 | 제조 불량 감지, 매장 분석, 교통 감시, 헬스케어 모니터링 |
| 보안 | X.509 인증, TLS 암호화, 오프라인 동작 지원 |
| 확장 방법 | 디바이스 추가 배치로 수평 확장 |

AWS Panorama는 클라우드의 ML 역량을 엣지로 확장하여, 영상 데이터를 클라우드에 전송하지 않고도 고급 컴퓨터 비전 분석을 수행할 수 있게 해줍니다. 제조업, 소매업, 물류, 헬스케어 등 영상 기반 자동화가 필요한 산업에서 특히 강력한 솔루션이 될 수 있습니다.