---
title: "Claude Computer Use: AI 에이전트 프레임워크"
slug: "computer-use"
category: agent
tags: ["Anthropic", "Claude Computer Use", "Computer Use", "GUI Automation", "Screenshot Understanding"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.231433+00:00"
architecture_entry: "computer-use"
---

# Claude Computer Use: AI의 GUI 직접 제어

**Anthropic** · **2024-10-22** · **GUI Automation** · **상용 API**

## 개요

Claude Computer Use는 Anthropic이 2024년 10월 Claude 3.5 Sonnet과 함께 공개(베타)한 기능으로, Claude가 스크린샷을 입력으로 받아 마우스 클릭, 키보드 입력, 스크롤 등 GUI 조작 명령을 출력함으로써 컴퓨터를 직접 제어하는 능력이다. 이는 AI가 기존 RPA(로봇 프로세스 자동화) 도구와 근본적으로 다른 방식으로 컴퓨터를 조작할 수 있음을 보여준 선구적 기술이다.

기존 RPA는 미리 정의된 스크립트와 UI 요소 식별자(CSS 선택자, XPath 등)에 의존했다. UI가 조금만 변경되어도 스크립트가 깨지는 취약성이 있었다. Computer Use는 시각적 이해를 기반으로 동적으로 인터페이스를 탐색하므로, UI 변경에 강건하고 사전 프로그래밍 없이도 임의의 GUI 애플리케이션을 조작할 수 있다.

수학적으로 Computer Use의 동작을 표현하면, 각 시점 $t$에서 스크린샷 이미지 $I_t$를 관찰하고 GUI 액션 $a_t$를 생성하는 정책(policy) $\pi$를 실행하는 것이다.

$$a_t = \pi(I_t, I_{t-1}, ..., I_1, \text{goal})$$

이는 부분 관측 마르코프 결정 과정(POMDP)의 프레임워크와 유사하며, 스크린샷이라는 고차원 관측을 통해 최적의 GUI 액션 시퀀스를 결정하는 문제로 볼 수 있다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

Computer Use는 Claude의 기존 멀티모달(비전) 능력과 tool use API를 결합한 아키텍처로 구현된다.

### 도구 구성

Computer Use는 세 가지 도구 타입을 사용한다.

| 도구 | 기능 | 액션 |
|------|------|------|
| `computer` | GUI 직접 조작 | mouse_move, left_click, right_click, double_click, drag, scroll, type, key, screenshot |
| `text_editor` | 파일 내용 보기/편집 | view, write |
| `bash` | 셸 명령 실행 | command |

### 에이전틱 루프

```
사용자: "Chrome에서 서울 날씨를 검색해줘"

[Screenshot #1] → Claude 분석: "Chrome 아이콘이 하단 작업표시줄에 보입니다"
  Action: mouse_move(x=960, y=1060) → left_click()

[Screenshot #2] → Claude 분석: "Chrome이 열렸고 주소창이 보입니다"
  Action: left_click(x=500, y=65) → type("서울 날씨")

[Screenshot #3] → Claude 분석: "검색어가 입력되었습니다"
  Action: key("Return")

[Screenshot #4] → Claude 분석: "날씨 검색 결과가 표시됨"
  Report: "현재 서울 기온은 15°C, 맑음입니다."
```

각 스크린샷에서 Claude는 다음 정보를 추출한다.
- 현재 화면 상태 인식 (어떤 앱이 열려 있는가)
- UI 요소 위치 파악 (버튼, 입력 필드, 메뉴의 좌표)
- 목표 대비 진행 상황 평가
- 다음 최적 액션 결정

### 좌표 시스템과 해상도

Claude는 스크린샷을 분석하여 UI 요소의 픽셀 좌표 $(x, y)$를 추정한다. 해상도와 스케일링 설정이 정확도에 직접적 영향을 미치므로, Anthropic은 XGA(1024x768) 해상도를 권장한다. 고해상도 디스플레이에서는 스케일링으로 인해 좌표 추정 오차가 증가할 수 있다.

### 안전한 실행 환경

Anthropic은 Computer Use를 Docker 컨테이너 같은 격리된 환경에서 사용할 것을 강력히 권장한다. 레퍼런스 구현으로 제공되는 Docker 이미지에는 Ubuntu 데스크톱, Firefox, Python 등이 사전 설치되어 있다.

```bash
# Anthropic 레퍼런스 Docker 이미지 실행
docker run -p 5900:5900 -p 8501:8501 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo
```

## 핵심 혁신

1. **비전 기반 GUI 이해**: DOM 구조나 접근성 API 없이 순수하게 스크린샷 이미지만으로 UI 요소를 인식하고 상호작용한다. 이는 모든 운영체제와 애플리케이션에 범용적으로 적용 가능한 접근이다.

2. **제로 설정(Zero-configuration)**: 자동화 대상 애플리케이션에 대한 사전 설정이나 통합 작업이 필요 없다. 인간이 마우스와 키보드로 할 수 있는 작업이라면 원칙적으로 자동화 가능하다.

3. **동적 적응**: 예상치 못한 팝업, 로딩 화면, 에러 메시지 등에 대해 인간처럼 판단하고 대응한다. 기존 RPA의 경직된 스크립트 실행과 대조적이다.

4. **멀티모달 추론**: 화면의 시각적 레이아웃, 텍스트 내용, 아이콘 의미 등을 종합적으로 이해하여 최적의 액션을 결정한다.

## 벤치마크/성능

| 벤치마크 | Claude 3.5 Sonnet (v1) | Claude 3.5 Sonnet (v2) | 인간 | 이전 SOTA |
|---------|----------------------|----------------------|------|----------|
| OSWorld | 14.9% | 22.0% | 72.4% | 7.8% |
| WebArena | - | 개선됨 | - | - |

Claude 3.5 Sonnet은 OSWorld 벤치마크에서 기존 최고 성능(7.8%)의 거의 두 배인 14.9%를 달성했다. 업데이트 버전에서 22.0%로 향상되었으나, 인간 성능(72.4%)과는 상당한 격차가 있어 발전 여지가 크다.

## 구현

**레거시 시스템 자동화**: API가 없는 오래된 데스크톱 애플리케이션(ERP, 레거시 관리 툴)의 작업을 GUI 조작으로 자동화할 수 있다. 특히 윈도우 기반 기업 시스템에서 유용하다.

**QA 테스트 자동화**: 자연어로 테스트 시나리오를 기술하면 Computer Use가 해당 시나리오를 GUI에서 실행하고 결과를 보고한다. Selenium이나 Cypress 같은 테스트 프레임워크의 스크립트 유지보수 부담을 줄인다.

**크로스 애플리케이션 워크플로**: 이메일에서 첨부 파일을 다운로드하고, 스프레드시트에서 데이터를 추출하며, 웹 폼에 입력하는 등 여러 애플리케이션에 걸친 작업을 자동화한다.

## 관련 모델

Computer Use는 Claude 3.5 Sonnet의 비전 능력을 기반으로 구축되었다. 이후 OpenAI의 Operator(CUA), Manus 등 유사한 GUI 자동화 시스템에 직접적 영감을 주었다. 데스크톱 전체를 대상으로 하는 Computer Use와 달리, Operator는 브라우저에 특화되었고, Manus는 GUI와 API를 이중으로 활용한다.

## 참고 자료

- [Anthropic Blog: Introducing Computer Use](https://www.anthropic.com/news/3-5-models-and-computer-use)
- [Anthropic Computer Use Documentation](https://docs.anthropic.com/en/docs/build-with-claude/computer-use)

## 관련 문서

- [[claude|Claude (1-3.5 Series)]] — 발전 기반
- [[manus|Manus]] — 영감을 줌
- [[operator|Operator (CUA)]] — 영감을 줌
