<!-- infographic-hero -->
![Big Data Collection and Visualization Pipeline with Python 핵심 요약](figures/infographic.svg)

*Figure: Big Data Collection and Visualization Pipeline with Python 한 장 요약 인포그래픽*

# Python으로 구축하는 빅데이터 수집 및 시각화 파이프라인

## 개요

데이터 엔지니어링에서 **데이터 수집(Data Collection)**과 **시각화(Visualization)**는 파이프라인의 시작과 끝을 이루는 핵심 단계다. 아무리 정교한 분석 모델이 있어도 원시 데이터를 효과적으로 수집하지 못하면 의미가 없고, 분석 결과를 직관적으로 시각화하지 못하면 의사결정에 활용할 수 없다.

이 글에서는 Python을 활용하여 **웹에서 뉴스 기사를 크롤링하고, 자연어 처리(NLP)를 통해 핵심 키워드를 추출하며, 시각화까지 완성하는 전체 파이프라인**을 구축한다. 실무에서 자주 사용하는 `requests`, `BeautifulSoup`, `KoNLPy`, `matplotlib`, `WordCloud` 라이브러리를 조합하여, 데이터 수집-처리-시각화의 전체 흐름을 이해할 수 있다.

## 핵심 개념

### 데이터 수집 파이프라인의 구성요소

데이터 수집 파이프라인은 크게 4단계로 구성된다:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  수집    │ →  │  전처리   │ →  │  분석    │ →  │  시각화   │
│ (Crawl)  │    │(Process) │    │(Analyze) │    │ (Visual) │
├──────────┤    ├──────────┤    ├──────────┤    ├──────────┤
│ requests │    │ KoNLPy   │    │ Counter  │    │matplotlib│
│ BS4      │    │ 형태소   │    │ 빈도분석 │    │WordCloud │
│newspaper │    │ 분석     │    │ 정렬     │    │ 차트     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 사용하는 주요 라이브러리

| 라이브러리 | 역할 | 설명 |
|-----------|------|------|
| `requests` | HTTP 요청 | URL에 GET/POST 요청을 보내 HTML 응답 수신 |
| `BeautifulSoup` (bs4) | HTML 파싱 | HTML/XML 문서를 파싱하여 원하는 요소 추출 |
| `newspaper3k` | 기사 추출 | URL에서 뉴스 기사 본문을 자동 추출 |
| `KoNLPy` (Okt) | 한국어 NLP | 형태소 분석, 명사 추출 등 한국어 자연어 처리 |
| `collections.Counter` | 빈도 계산 | 요소의 출현 횟수를 딕셔너리 형태로 반환 |
| `matplotlib` | 차트 생성 | 막대그래프, 파이 차트 등 다양한 시각화 |
| `wordcloud` | 워드클라우드 | 단어 빈도 기반 워드클라우드 이미지 생성 |

### 웹 크롤링 기초 개념

웹 크롤링(Web Crawling)은 프로그램을 이용하여 웹 페이지에서 데이터를 자동으로 수집하는 기술이다. 핵심 단계는 다음과 같다:

1. **HTTP 요청**: `requests.get(url)` → 서버로부터 HTML 응답 수신
2. **HTML 파싱**: `BeautifulSoup(response.text, 'lxml')` → DOM 트리 구성
3. **데이터 추출**: CSS 셀렉터/태그로 원하는 요소 선택
4. **후처리**: 텍스트 정제, 저장

```python
import requests
from bs4 import BeautifulSoup

# 1단계: HTTP 요청
response = requests.get("https://example.com")
print(response.status_code)  # 200 = 정상

# 2단계: HTML 파싱
soup = BeautifulSoup(response.text, 'lxml')

# 3단계: 데이터 추출
# find() - 첫 번째 매칭 요소
title = soup.find('h1').text

# select() - CSS 셀렉터로 모든 매칭 요소 (리스트 반환)
links = soup.select('div.content > a')
for link in links:
    print(link['href'], link.text)
```

## 아키텍처: 전체 파이프라인 설계

### 시스템 구조

```
┌─────────────────────────────────────────────────────┐
│                  전체 파이프라인 구조                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Input]                                            │
│   사용자 입력 → 키워드 + 페이지 수                    │
│                                                     │
│  [get_link()]                                       │
│   네이버 뉴스 검색 URL 구성 → HTML 파싱 →            │
│   뉴스 기사 링크 리스트 추출                          │
│                                                     │
│  [get_article()]                                    │
│   각 링크에서 기사 본문 추출 → 텍스트 파일 저장        │
│                                                     │
│  [wordcount()]                                      │
│   형태소 분석 → 명사 추출 → 빈도 계산 →              │
│   내림차순 정렬 → 결과 저장                          │
│                                                     │
│  [visualize()]                                      │
│   막대그래프 / 워드클라우드 생성 → 이미지 저장         │
│                                                     │
│  [Output]                                           │
│   crawling.txt + wordcount.txt +                    │
│   all_words.jpg + top_words.jpg + cloud.jpg          │
└─────────────────────────────────────────────────────┘
```

### 함수별 역할 정리

| 함수명 | 입력 | 출력 | 역할 |
|--------|------|------|------|
| `get_link()` | 키워드, 페이지수 | URL 리스트 | 검색 결과에서 뉴스 링크 추출 |
| `get_article()` | URL 리스트 | crawling.txt | 각 URL에서 기사 본문 수집 |
| `wordcount()` | crawling.txt | wordcount.txt | 명사 추출 및 빈도 분석 |
| `full_vis_bar()` | 빈도 데이터 | all_words.jpg | 전체 단어 막대그래프 |
| `top_n()` | 빈도 데이터 | top.txt | 상위 N개 단어 추출 |
| `topn_vis_bar()` | 상위 N개 | top_words.jpg | 상위 단어 막대그래프 |
| `wordcloud()` | crawling.txt | cloud.jpg | 워드클라우드 이미지 |

## 실전 예제

### Step 1: 뉴스 기사 링크 수집

```python
import requests
from bs4 import BeautifulSoup

# 네이버 뉴스 검색 URL 구성 요소
URL_BASE = "https://search.naver.com/search.naver?where=news&sm=tab_pge&query="
URL_PAGE = "&sort=0&photo=0&field=0&pd=0&ds=&de=&cluster_rank=29&start="

def get_link(keyword: str, page_range: int) -> list:
    """네이버 뉴스 검색 결과에서 기사 링크를 추출합니다."""
    links = []

    for page in range(page_range):
        current_page = 1 + page * 10  # 네이버 페이지네이션: 1, 11, 21...
        url = f"{URL_BASE}{keyword}{URL_PAGE}{current_page}"

        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        if response.status_code != 200:
            print(f"페이지 {page+1} 요청 실패: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, 'lxml')

        # 뉴스 기사 링크가 포함된 태그 선택
        url_tags = soup.select('div.news_area > a')

        for tag in url_tags:
            links.append(tag['href'])

    print(f"총 {len(links)}개의 기사 링크를 수집했습니다.")
    return links
```

**핵심 포인트:**
- `soup.select('상위태그 > 하위태그')`: CSS 셀렉터로 원하는 HTML 요소를 선택
- `tag['href']`: 태그의 `href` 속성값(링크 URL)을 추출
- User-Agent 헤더를 설정하여 차단 방지

### Step 2: 기사 본문 추출

```python
from newspaper import Article

def get_article(links: list, output_file: str, keyword: str) -> None:
    """기사 링크에서 본문을 추출하여 텍스트 파일로 저장합니다."""
    print('데이터를 불러오는 중...')
    success_count = 0

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, url in enumerate(links, 1):
            try:
                article = Article(url, language='ko')
                article.download()
                article.parse()

                f.write(article.title + '\n')
                f.write(article.text + '\n\n')
                success_count += 1

            except Exception as e:
                print(f"  - {i}번째 URL 크롤링 실패: {str(e)[:50]}")

    print(f"'{keyword}' 관련 뉴스 기사 {success_count}개가 저장되었습니다. ({output_file})")
```

**newspaper3k 라이브러리**는 URL만 입력하면 뉴스 기사의 제목과 본문을 자동으로 추출해주는 강력한 도구다. 다만 모든 사이트를 완벽히 지원하지는 않으므로, 실패 시 BeautifulSoup으로 직접 파싱하는 폴백(fallback) 로직을 추가하는 것이 좋다.

### Step 3: 형태소 분석 및 빈도 계산

```python
from konlpy.tag import Okt
from collections import Counter, OrderedDict

def wordcount(input_file: str, output_file: str) -> tuple:
    """텍스트 파일에서 명사를 추출하고 빈도를 계산합니다."""

    # 텍스트 읽기
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # 형태소 분석기로 명사 추출
    okt = Okt()
    all_nouns = okt.nouns(text)

    # 1글자 명사 제거 (의미 없는 단어 필터링)
    nouns = [noun for noun in all_nouns if len(noun) > 1]

    # 빈도 계산 및 내림차순 정렬
    counter = Counter(nouns)
    sorted_words = OrderedDict(
        sorted(counter.items(), key=lambda x: x[1], reverse=True)
    )

    # 결과 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        for word, count in sorted_words.items():
            f.write(f"{word}  {count}\n")

    print(f"단어 카운팅 완료: {len(sorted_words)}개 고유 명사 ({output_file})")
    return counter, sorted_words
```

**KoNLPy의 Okt(Open Korean Text) 형태소 분석기:**
- `okt.nouns(text)`: 텍스트에서 명사만 추출
- `okt.morphs(text)`: 모든 형태소 추출
- `okt.pos(text)`: 품사 태깅 결과 반환

**주의사항**: KoNLPy는 내부적으로 Java를 사용하므로, JDK 설치와 `JAVA_HOME` 환경변수 설정이 필요하다.

### Step 4: 시각화 - 막대그래프

```python
import matplotlib
import matplotlib.pyplot as plt

# 한글 폰트 설정 (OS별)
# Mac: 'AppleGothic', Windows: 'Malgun Gothic', Linux: 'NanumGothic'
matplotlib.rc('font', family='AppleGothic')
matplotlib.rcParams['axes.unicode_minus'] = False  # 마이너스 부호 깨짐 방지

def visualize_top_words(counter: Counter, n: int = 20) -> None:
    """상위 N개 단어를 막대그래프로 시각화합니다."""
    top_words = counter.most_common(n)
    words = [w for w, c in top_words]
    counts = [c for w, c in top_words]

    fig, ax = plt.subplots(figsize=(15, 8))
    bars = ax.bar(words, counts, color='#6799FF', edgecolor='white')

    # 막대 위에 수치 표시
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(count), ha='center', va='bottom', fontsize=10)

    ax.set_title(f'뉴스 기사 상위 {n}개 키워드 빈도', fontsize=20, pad=20)
    ax.set_xlabel('키워드', fontsize=14)
    ax.set_ylabel('빈도', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('top_words.jpg', dpi=150, bbox_inches='tight')
    plt.show()
    print('top_words.jpg 저장 완료')
```

### Step 5: 시각화 - 워드클라우드

```python
from wordcloud import WordCloud

def generate_wordcloud(input_file: str, output_file: str = 'cloud.jpg') -> None:
    """텍스트 파일에서 워드클라우드를 생성합니다."""

    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # 명사 추출 및 빈도 계산
    okt = Okt()
    nouns = [n for n in okt.nouns(text) if len(n) > 1]
    counter = Counter(nouns)
    top_words = counter.most_common(100)

    # 워드클라우드 생성
    wc = WordCloud(
        font_path='/System/Library/Fonts/AppleSDGothicNeo.ttc',  # Mac
        # font_path='C:/Windows/Fonts/malgun.ttf',  # Windows
        background_color='white',
        width=2500,
        height=1500,
        max_words=100,
        colormap='viridis',  # 컬러맵 설정
        prefer_horizontal=0.7
    )
    cloud = wc.generate_from_frequencies(dict(top_words))

    # 시각화 및 저장
    plt.figure(figsize=(20, 12))
    plt.imshow(cloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.show()
    print(f'{output_file} 저장 완료')
```

### 전체 파이프라인 실행

```python
import sys

def main():
    """전체 파이프라인을 실행합니다."""
    # 설정
    keyword = input("검색 키워드를 입력하세요: ")
    page_range = int(input("수집할 페이지 수를 입력하세요: "))

    crawl_file = "crawling.txt"
    count_file = "wordcount.txt"

    # 1단계: 링크 수집
    print("\n=== 1단계: 뉴스 링크 수집 ===")
    links = get_link(keyword, page_range)

    # 2단계: 기사 본문 수집
    print("\n=== 2단계: 기사 본문 수집 ===")
    get_article(links, crawl_file, keyword)

    # 3단계: 형태소 분석 및 빈도 계산
    print("\n=== 3단계: 형태소 분석 ===")
    counter, sorted_words = wordcount(crawl_file, count_file)

    # 4단계: 시각화
    print("\n=== 4단계: 시각화 ===")
    visualize_top_words(counter, n=20)
    generate_wordcloud(crawl_file)

    print("\n파이프라인 완료!")

if __name__ == '__main__':
    main()
```

## 비교 분석

### 데이터 수집 도구 비교

| 도구 | 수준 | 장점 | 단점 | 적합한 용도 |
|------|------|------|------|------------|
| **requests + BS4** | 기본 | 가볍고 유연, 학습 쉬움 | 동적 페이지 미지원 | 정적 HTML 크롤링 |
| **Selenium** | 고급 | 동적 페이지 지원, 브라우저 자동화 | 느림, 리소스 많이 사용 | JavaScript 렌더링 필요 시 |
| **Scrapy** | 프레임워크 | 대규모 크롤링, 비동기 처리 | 학습 곡선 높음 | 대량 데이터 수집 |
| **newspaper3k** | 특화 | 뉴스 기사 자동 추출 | 일부 사이트 미지원 | 뉴스 기사 전용 |
| **Playwright** | 최신 | 최신 브라우저 지원, 빠름 | 상대적 신생 | 현대 웹앱 크롤링 |

### 한국어 형태소 분석기 비교

| 분석기 | 속도 | 정확도 | 특징 |
|--------|------|--------|------|
| **Okt** (Twitter) | 빠름 | 보통 | 범용, 구어체에 강함 |
| **Komoran** | 보통 | 높음 | 세종 사전 기반 |
| **Mecab** | 매우 빠름 | 높음 | C 기반, 설치 복잡 |
| **Hannanum** | 느림 | 높음 | KAIST 개발 |
| **Kkma** | 느림 | 매우 높음 | 서울대 개발, 분석 정밀 |

### 현대적 데이터 수집 파이프라인 도구

실무에서는 단순 스크립트를 넘어 **오케스트레이션 도구**와 결합하여 파이프라인을 운영한다:

```
┌──────────────────────────────────────────────┐
│       현대적 데이터 수집 파이프라인 스택        │
├──────────────────────────────────────────────┤
│  오케스트레이션: Apache Airflow / Prefect      │
│  수집: Scrapy / Selenium / API 클라이언트      │
│  저장: S3 / GCS / PostgreSQL / MongoDB        │
│  처리: Spark / Pandas / dbt                   │
│  시각화: Superset / Grafana / Streamlit       │
│  모니터링: Prometheus / DataDog               │
└──────────────────────────────────────────────┘
```

## 마무리

이 글에서는 Python을 활용하여 웹 크롤링부터 자연어 처리, 시각화까지 이어지는 **데이터 수집 파이프라인의 전체 흐름**을 구현했다. 각 단계에서 사용한 핵심 라이브러리와 기법을 정리하면:

1. **수집**: `requests` + `BeautifulSoup`으로 HTML 파싱, `newspaper3k`로 기사 추출
2. **전처리**: `KoNLPy(Okt)`로 한국어 형태소 분석 및 명사 추출
3. **분석**: `Counter`로 단어 빈도 계산 및 정렬
4. **시각화**: `matplotlib`으로 막대그래프, `WordCloud`로 워드클라우드 생성

이 기본 파이프라인 패턴을 확장하면, Airflow로 스케줄링하고 S3에 저장하며 Spark로 대규모 처리하는 프로덕션급 데이터 파이프라인의 기반이 된다. 데이터 엔지니어링의 첫걸음은 이처럼 작은 파이프라인을 직접 구축하고 점진적으로 확장하는 것이다.

---

**참고 자료:**
- [BeautifulSoup 공식 문서](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [KoNLPy 공식 문서](https://konlpy.org/ko/latest/)
- [WordCloud 라이브러리](https://amueller.github.io/word_cloud/)
- [newspaper3k 공식 문서](https://newspaper.readthedocs.io/en/latest/)