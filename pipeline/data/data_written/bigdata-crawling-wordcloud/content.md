# 네이버 뉴스 크롤링과 워드클라우드 시각화 실전 가이드

## 개요

특정 주제에 대해 뉴스 기사가 어떤 키워드를 중심으로 보도되고 있는지 파악하려면, 기사를 하나하나 읽어보는 것만으로는 한계가 있습니다. 수십, 수백 건의 기사를 직접 분석하는 것은 시간과 비용 면에서 비효율적이기 때문입니다.

이 글에서는 Python을 활용하여 네이버 뉴스 검색 결과를 자동으로 크롤링하고, 수집한 기사 본문에서 한국어 명사를 추출한 뒤, 빈도 분석과 워드클라우드 시각화까지 수행하는 전체 파이프라인을 구현합니다. 직접 진행해본 경험을 바탕으로, 각 단계에서 막히기 쉬운 부분과 해결 방법을 함께 정리했습니다.

개발 환경은 Python 3.8.10이며, 필요한 라이브러리는 다음 명령어로 한 번에 설치할 수 있습니다.

```bash
pip install requests bs4 lxml newspaper3k konlpy numpy matplotlib wordcloud
```

## 핵심 개념

### 파이프라인 구성

이번 프로젝트의 파이프라인은 네 단계로 이루어져 있습니다.

1. 링크 수집 -- 네이버 뉴스 검색 결과에서 기사 URL을 추출합니다.
2. 본문 수집 -- 각 URL에 접근하여 기사 제목과 본문 텍스트를 가져옵니다.
3. 형태소 분석 -- 수집한 텍스트에서 한국어 명사를 추출하고 빈도를 집계합니다.
4. 시각화 -- 빈도 데이터를 막대그래프와 워드클라우드로 표현합니다.

각 단계는 독립적인 함수로 분리되어 있어서, 필요에 따라 특정 단계만 재실행하거나 중간 결과를 파일로 저장해두고 이어서 작업할 수 있습니다.

### 사용 라이브러리

| 모듈 | 역할 |
|------|------|
| `requests` | HTTP 요청 처리 |
| `bs4 (BeautifulSoup)` | HTML/XML 파싱 |
| `newspaper (Article)` | URL에서 뉴스 기사 텍스트 추출 |
| `konlpy.tag (Okt)` | 한국어 형태소 분석 |
| `collections.Counter` | 시퀀스 데이터 빈도 카운팅 |
| `matplotlib` | 차트/플롯 시각화 |
| `wordcloud` | WordCloud 이미지 생성 |

처음에는 어떤 모듈이 반드시 필요한지 확신이 없었는데, 위 조합으로 작업을 진행하니 형태소 분석부터 시각화까지 매끄럽게 이어졌습니다. requests와 BeautifulSoup이 크롤링의 기본 뼈대를 담당하고, newspaper3k가 기사 본문 추출을 자동화해주며, KoNLPy가 한국어 텍스트 처리의 핵심을 맡는 구조입니다.

### 웹 크롤링의 기본 원리

웹 크롤링은 프로그램이 사람 대신 웹 페이지에 접근하여 데이터를 수집하는 기술입니다. 기본 흐름은 다음과 같습니다.

- `requests.get(url)`로 서버에 HTTP 요청을 보내 HTML 응답을 받습니다.
- `BeautifulSoup`이 받아온 HTML 텍스트를 파싱하여 DOM 트리를 구성합니다.
- CSS 셀렉터나 태그명으로 원하는 요소를 탐색하여 데이터를 추출합니다.

네이버 뉴스 검색의 경우, 검색 결과 페이지의 HTML 구조에서 각 기사로 연결되는 링크 태그를 찾아내는 것이 첫 번째 과제입니다.

## 실전 코드

### 모듈 임포트 및 URL 설정

```python
import sys
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from konlpy.tag import Okt
from collections import Counter, OrderedDict
import matplotlib
import matplotlib.pyplot as plt

URL_BEFORE_KEYWORD  = "https://search.naver.com/search.naver?where=news&sm=tab_pge&query="
URL_BEFORE_PAGE_NUM = "&sort=0&photo=0&field=0&pd=0&ds=&de=&cluster_rank=29&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so:r,p:all,a:all&start="

font_name = 'Malgun Gothic'  # Mac은 'Apple Gothic'
```

위 코드에서 `URL_BEFORE_KEYWORD`와 `URL_BEFORE_PAGE_NUM`은 네이버 뉴스 검색 URL의 패턴을 그대로 분해한 것입니다. 키워드와 페이지 번호를 사이에 끼워 넣으면 완성된 검색 URL이 됩니다.

`font_name` 설정은 사소해 보이지만, Matplotlib에서 한글을 출력할 때 폰트를 지정하지 않으면 글자가 깨져서 네모 상자로 표시됩니다. 개인적으로 이 문제로 한참 시간을 소비한 적이 있는데, OS에 맞는 폰트명을 정확히 지정하는 것이 해결책이었습니다. Mac에서는 `AppleGothic`, Windows에서는 `Malgun Gothic`, Linux에서는 `NanumGothic`을 사용하면 됩니다.

### get_link -- 검색 결과에서 링크 추출

```python
def get_link(key_word, page_range):
    link = []
    for page in range(page_range):
        current_page = 1 + page * 10
        crawling_url_list = URL_BEFORE_KEYWORD + key_word + URL_BEFORE_PAGE_NUM + str(current_page)

        response = requests.get(crawling_url_list)
        soup = BeautifulSoup(response.text, 'lxml')

        url_tag = soup.select('div.news_area > a')  # 뉴스 링크 태그 선택

        for url in url_tag:
            link.append(url['href'])

    return link
```

네이버 뉴스 검색 결과는 한 페이지에 10개의 기사를 보여주며, 페이지네이션은 `start` 파라미터로 1, 11, 21 순서로 증가합니다. `1 + page * 10` 계산식이 이 패턴을 반영한 것입니다.

`soup.select('div.news_area > a')`는 CSS 셀렉터를 사용하여 뉴스 영역 내의 링크 태그를 선택합니다. 이 부분에서 주의할 점이 있습니다. 네이버는 주기적으로 HTML 구조를 변경하기 때문에, 이 셀렉터가 동작하지 않을 수 있습니다. 그런 경우 브라우저의 개발자 도구(F12)를 열어 현재 페이지의 HTML 구조를 확인하고, 셀렉터를 수정해야 합니다.

### get_article -- 기사 본문 수집 및 저장

```python
def get_article(file1, link, key_word, page_range):
    print('데이터를 불러오는 중')
    with open(file1, 'w', encoding='utf8') as f:
        i = 1
        for url2 in link:
            article = Article(url2, language='ko')
            try:
                article.download()
                article.parse()
            except:
                print('-', i, '번째 URL을 크롤링할 수 없습니다')

            f.write(article.title)
            f.write(article.text)
            i += 1

    print('- 네이버 뉴스', key_word, '관련 뉴스기사', str(page_range), '페이지 저장 완료')
```

`newspaper` 라이브러리의 `Article` 클래스는 URL을 받아서 해당 페이지의 기사 제목(`article.title`)과 본문(`article.text`)을 자동으로 추출합니다. `language='ko'`를 지정하면 한국어 기사에 최적화된 추출을 수행합니다.

다만 모든 뉴스 사이트의 구조를 완벽하게 지원하지는 않습니다. 사이트에 따라 본문을 제대로 가져오지 못하는 경우가 있기 때문에, `try-except` 블록으로 예외를 처리하는 것이 실용적입니다. 실제로 수십 개의 URL을 처리하다 보면 일부는 반드시 실패하므로, 이 예외 처리가 없으면 전체 파이프라인이 중간에 멈추게 됩니다.

### wordcount -- 형태소 분석 및 빈도 집계

```python
def wordcount(file1, file2):
    f = open(file1, 'r', encoding='utf8')
    g = open(file2, 'w', encoding='utf8')

    engine = Okt()
    data = f.read()
    all_nouns = engine.nouns(data)               # 명사 추출
    nouns = [n for n in all_nouns if len(n) > 1] # 1글자 명사 제거

    global count, by_num
    count  = Counter(nouns)
    by_num = OrderedDict(sorted(count.items(), key=lambda t: t[1], reverse=True))

    for w, n in zip(by_num.keys(), by_num.values()):
        g.write('%s  %d\n' % (w, n))

    print('- 단어 카운팅 완료 (wordcount.txt)')
    f.close(); g.close()
```

KoNLPy의 `Okt` 형태소 분석기에서 `nouns()` 메서드를 호출하면 입력 텍스트에서 명사만 추출하여 리스트로 반환합니다. 이때 한 글자짜리 명사(예: '것', '수', '등')는 분석에 노이즈를 만들기 때문에, 리스트 컴프리헨션으로 2글자 이상인 명사만 필터링합니다.

`Counter`는 리스트 내 각 요소의 등장 횟수를 딕셔너리 형태로 집계해주는 표준 라이브러리입니다. 이를 `OrderedDict`로 감싸고 빈도 내림차순으로 정렬하면, 가장 많이 등장한 단어부터 순서대로 결과를 확인할 수 있습니다.

한국어 텍스트 분석에서 `Okt`의 `nouns()` 메서드만으로도 꽤 괜찮은 결과를 얻을 수 있었습니다. 하지만 특정 도메인의 전문 용어나 신조어는 사전에 등록되어 있지 않아 누락될 수 있으므로, 필요하다면 사용자 사전을 추가하거나 불용어(stopwords) 목록을 별도로 관리하는 것이 좋습니다.

### 시각화 -- 막대그래프 생성

```python
def full_vis_bar(by_name):
    # 빈도 15 미만 단어 제거
    for w, n in list(by_num.items()):
        if n < 15:
            del by_num[w]

    fig = plt.gcf()
    fig.set_size_inches(20, 10)
    matplotlib.rc('font', family=font_name, size=10)
    plt.title('기사에 나온 전체 단어 빈도 수', fontsize=30)
    plt.xlabel('단어', fontsize=20)
    plt.ylabel('해당 단어 수', fontsize=20)
    plt.bar(by_num.keys(), by_num.values(), color="#6799FF")
    plt.xticks(rotation=45)
    plt.savefig('all_words.jpg')
    plt.show()

def topn_vis_bar(top):
    fig = plt.gcf()
    fig.set_size_inches(15, 10)
    matplotlib.rc('font', family=font_name, size=20)
    plt.title('기사에 나온 전체 단어 빈도 수', fontsize=35)
    plt.bar(top.keys(), top.values(), color="#FFA7A7")
    plt.savefig('top_words.jpg')
    plt.show()
```

`full_vis_bar` 함수는 빈도가 15 미만인 단어를 제거하고 나머지를 모두 막대그래프로 표시합니다. 기사 수가 많을수록 고유 단어 수도 늘어나므로, 임계값을 조정하여 그래프의 가독성을 확보할 수 있습니다.

`topn_vis_bar` 함수는 상위 N개 단어만 별도로 시각화합니다. 전체 단어 그래프가 너무 밀집되어 읽기 어려울 때, 핵심 키워드만 골라서 보여주는 용도입니다.

시각화 과정에서 한글 폰트 설정과 `plt.savefig()` 호출 순서가 문제를 일으킬 수 있습니다. `plt.show()`를 `plt.savefig()`보다 먼저 호출하면 빈 이미지가 저장되므로, 반드시 저장을 먼저 하고 화면 출력을 나중에 해야 합니다.

### main -- 전체 파이프라인 실행

```python
def main(argv):
    if len(argv) != 3:
        print('인자 값을 정확히 입력하세요')
        return

    key_word   = argv[1]
    page_range = int(argv[2])

    link = get_link(key_word, page_range)
    get_article("crawling.txt", link, key_word, page_range)
    wordcount("crawling.txt", "wordcount.txt")
    top_n("top.txt")
    topn_vis_bar(top)

if __name__ == '__main__':
    main(sys.argv)
```

커맨드라인에서 키워드와 페이지 수를 인자로 받아 전체 파이프라인을 순차적으로 실행합니다.

```bash
python naver_crawling.py 빅데이터 3
```

위 명령어를 실행하면 '빅데이터' 키워드로 네이버 뉴스 3페이지(약 30개 기사)를 크롤링하고, 형태소 분석 결과를 `wordcount.txt`에 저장한 뒤, 상위 단어 막대그래프를 생성합니다.

실전에서 사용할 때는 인자 검사를 좀 더 엄격하게 하고, 파일 경로를 절대 경로로 지정하며, 이미 수집한 데이터가 있으면 크롤링 단계를 건너뛰는 로직을 추가하면 반복 실행이 훨씬 편리해집니다.

### 워드클라우드 생성

위 파이프라인에 워드클라우드 생성 기능을 추가한 별도 스크립트입니다.

```python
from wordcloud import WordCloud

def wordcloud(filename):
    with open(filename, encoding='utf8') as f:
        data = f.read()

        engine    = Okt()
        all_nouns = engine.nouns(data)
        nouns     = [n for n in all_nouns if len(n) > 1]
        count     = Counter(nouns)
        tags      = count.most_common(100)

        wc    = WordCloud(font_path='malgun', background_color=(168, 237, 244), width=2500, height=1500)
        cloud = wc.generate_from_frequencies(dict(tags))

        plt.imshow(cloud, interpolation='bilinear')
        plt.axis('off')
        plt.savefig('cloud.jpg')
        plt.show()
```

```bash
python naver_crawling2.py 인공지능 5
```

`WordCloud` 객체를 생성할 때 `font_path` 파라미터에 한글 폰트 경로를 지정하지 않으면 한글이 깨져서 표시됩니다. Windows에서는 `'malgun'` 또는 `'C:/Windows/Fonts/malgun.ttf'`, Mac에서는 `'/System/Library/Fonts/AppleSDGothicNeo.ttc'`처럼 시스템에 설치된 폰트의 정확한 경로를 넣어야 합니다.

`generate_from_frequencies()`는 `{단어: 빈도}` 형태의 딕셔너리를 받아서 빈도에 비례하는 크기로 단어를 배치합니다. `most_common(100)`으로 상위 100개 단어만 선택한 것은, 너무 많은 단어를 넣으면 워드클라우드가 지나치게 밀집되어 가독성이 떨어지기 때문입니다.

`background_color`에 RGB 튜플 `(168, 237, 244)`을 지정하여 연한 하늘색 배경을 적용했는데, `'white'`나 `'black'` 같은 문자열도 사용할 수 있습니다. `width`와 `height`는 생성되는 이미지의 픽셀 크기이며, 값이 클수록 해상도가 높아지지만 생성 시간도 늘어납니다.

## 활용 사례

### 여론 동향 모니터링

특정 기업명이나 정책 키워드로 뉴스를 수집하고 워드클라우드를 생성하면, 해당 주제가 어떤 맥락에서 보도되고 있는지 한눈에 파악할 수 있습니다. 예를 들어 '인공지능'으로 크롤링했을 때 '규제', '일자리', '투자' 같은 단어가 상위에 나타난다면, 현재 언론이 해당 기술을 어떤 관점에서 다루고 있는지 간접적으로 확인할 수 있습니다.

### 경쟁사 분석

자사와 경쟁사 이름을 각각 키워드로 넣고 워드클라우드를 비교하면, 각 기업이 어떤 이슈와 함께 언급되고 있는지 비교 분석이 가능합니다. 시계열로 매주 데이터를 수집하면 언론 노출 트렌드의 변화도 추적할 수 있습니다.

### 학술 연구 키워드 분석

크롤링 대상을 뉴스 대신 학술 논문 사이트로 변경하면, 특정 연구 분야에서 자주 등장하는 용어를 파악하여 연구 트렌드를 분석하는 데 활용할 수 있습니다. `get_link` 함수의 URL 패턴과 CSS 셀렉터만 수정하면 다른 사이트에도 동일한 파이프라인을 적용할 수 있습니다.

### 파이프라인 확장 방향

이 기본 구조를 발전시키면 다음과 같은 확장이 가능합니다.

- Apache Airflow와 연동하여 정기적으로 자동 수집하도록 스케줄링할 수 있습니다.
- 수집한 데이터를 PostgreSQL이나 MongoDB에 저장하면 이력 관리와 쿼리 기반 분석이 가능합니다.
- Streamlit으로 대시보드를 구성하면, 키워드를 입력하고 즉시 워드클라우드를 확인하는 웹 애플리케이션을 만들 수 있습니다.
- 형태소 분석기를 Okt에서 Mecab으로 교체하면 처리 속도를 크게 개선할 수 있습니다. Mecab은 C 기반이라 대용량 텍스트 처리에 유리합니다.

## 정리

이 글에서는 네이버 뉴스 크롤링부터 워드클라우드 시각화까지, Python으로 구현하는 텍스트 데이터 수집 및 분석 파이프라인을 다루었습니다. 각 단계를 다시 요약하면 다음과 같습니다.

- 수집: `requests`와 `BeautifulSoup`으로 네이버 뉴스 검색 결과를 파싱하고, `newspaper3k`의 `Article` 클래스로 기사 본문을 추출합니다.
- 분석: `KoNLPy`의 `Okt` 형태소 분석기로 명사를 추출하고, `Counter`로 빈도를 집계합니다.
- 시각화: `matplotlib`으로 막대그래프를 그리고, `WordCloud`로 빈도 기반 워드클라우드를 생성합니다.

작업 과정에서 가장 자주 부딪힌 문제는 세 가지였습니다. 첫째, 네이버의 HTML 구조 변경으로 CSS 셀렉터가 동작하지 않는 문제입니다. 이는 브라우저 개발자 도구로 현재 구조를 확인하여 해결할 수 있습니다. 둘째, Matplotlib과 WordCloud에서 한글 폰트가 깨지는 문제입니다. OS에 맞는 폰트 경로를 정확히 지정해야 합니다. 셋째, newspaper3k가 일부 사이트의 본문을 제대로 추출하지 못하는 문제입니다. 예외 처리를 추가하여 실패한 URL을 건너뛰도록 하면 전체 파이프라인이 중단되지 않습니다.

이 파이프라인은 구조가 단순하여 다른 사이트나 다른 형태의 텍스트 분석에도 쉽게 응용할 수 있습니다. URL 패턴과 셀렉터만 바꾸면 크롤링 대상을 변경할 수 있고, 형태소 분석과 시각화 부분은 그대로 재사용할 수 있기 때문입니다.