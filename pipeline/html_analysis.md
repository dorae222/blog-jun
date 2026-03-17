# HTML 분석 결과 및 대처 케이스

## 1. 공통 페이지 구조

모든 134개 HTML 파일은 동일한 Notion 내보내기 구조를 따름:

```html
<article class="page sans">
  <header>
    <div class="page-header-icon">
      <span class="icon">🏅</span>  <!-- 또는 <img> -->
    </div>
    <h1 class="page-title">제목</h1>
    <p class="page-description">설명</p>  <!-- 선택 -->
  </header>
  <div class="page-body">
    <!-- 본문 -->
  </div>
</article>
```

**대처**: `page-title` → 포스트 제목으로 추출. `page-body` 내부만 마크다운 변환. `page-description` → summary 후보.

---

## 2. 전체 HTML 요소 패턴 (21 종류)

### 2.1 Toggle/Details (30+ 파일)
```html
<ul class="toggle">
  <li>
    <details open="">
      <summary style="font-weight:600;font-size:1.25em">제목</summary>
      <div class="indented">내용</div>
    </details>
  </li>
</ul>
```
변형: summary의 `font-size`로 헤딩 레벨 결정
- `1.5em` → `## ` (H2)
- `1.25em` → `### ` (H3)
- 스타일 없음 → `### ` (기본 H3)

주의사항:
- 3~5단계 중첩 가능
- `open=""` 속성 항상 존재 (펼침 상태)
- `<div class="indented">` 래퍼가 content를 감싸는 경우 있음

**대처**: 재귀적으로 처리. 중첩된 toggle도 같은 패턴이므로 depth 기반 헤딩 레벨 조정.

---

### 2.2 코드 블록 (25 파일, 디렉토리2만)
```html
<pre class="code code-wrap">
  <code class="language-Python">코드 내용</code>
</pre>
```
발견된 언어 14종: Python, JavaScript, Java, Bash, SQL, JSON, XML, CSS, HTML, R, Plain text, C, Scala, YAML

**대처**: `language-*` 클래스에서 언어 추출 → ` ```언어\n코드\n``` `. `html.unescape()` 필수.

---

### 2.3 이미지 (85 파일)
```html
<figure class="image">
  <a href="URL인코딩된/경로.png">
    <img src="URL인코딩된/경로.png"/>
  </a>
</figure>
```
이미지 경로 패턴 3가지: 상대 경로 (URL 인코딩), 외부 URL, Notion 아이콘

**대처**: `urllib.parse.unquote()` 디코딩 → HTML 파일 디렉토리 기준 해석. Notion 아이콘 제거. 외부 URL 유지. figcaption → alt text.

---

### 2.4 테이블 (26 파일)
**대처**: 첫 행을 헤더로, `|---|` 구분선 추가. 셀 내 `|`는 `\|`로 이스케이프.

### 2.5 Properties 테이블 (디렉토리1 전체 21파일)
```html
<table class="properties">
  <tr class="property-row property-row-multi_select">
    <th>기술 스택</th>
    <td><span class="selected-value select-value-color-blue">Python</span></td>
  </tr>
</table>
```
**대처**: 별도 메타데이터로 추출 → catalog. 마크다운 본문 제외.

### 2.6 Callout (18개, 디렉토리1만)
**대처**: `> **이모지 제목**\n> 내용` 블록쿼트 형식으로 변환.

### 2.7 Bookmark 링크 (30 파일)
**대처**: `[bookmark-title](href)` 형식.

### 2.8 Column 레이아웃 (모든 113 파일)
**대처**: 순차 평탄화.

### 2.9 수식/KaTeX (15+ 파일)
**대처**: `<annotation encoding="application/x-tex">`에서 LaTeX 추출 → `$...$` / `$$...$$`.

### 2.10 리스트 (거의 모든 파일)
**대처**: `- 항목` / `1. 항목` / `- [ ] 미완료` / `- [x] 완료`. 2-space 들여쓰기. 재귀.

### 2.11 인라인 서식
strong→`**`, em→`*`, code→`` ` ``, s→`~~`, a→`[text](url)`, mark→`**`

### 2.12 기타
hr→`---`, blockquote→`> `, link-to-page→제거, display:contents div→unwrap

---

## 3. 스킵 대상 페이지

인덱스: `[My Page]`, `포트폴리오`, `[ML & DL]`, `[ Deep Learning ]`, `[ Machine Learning ]`,
`[Big Data Solution]`, `[Front+Back]`, `[Etc]`, `[ Certificate ]`, `Paper Review`,
`[ TimeSeries Analysis ]`, `Statistical Analysis`

빈/최소(<200자): `Figma`, `CSS`, `HTML`, `JavaScript`

Certificate 카테고리 전체 제외.

---

## 4. 디렉토리별 특성 차이

| 특성 | 디렉토리1 (포트폴리오) | 디렉토리2 (지식베이스) |
|---|---|---|
| 파일 수 | 21 HTML | 113 HTML |
| 코드 블록 | 없음 | 25 파일 |
| Callout | 18개 | 없음 |
| Properties | 모든 파일 | 없음 |
| 이미지 | 45개 (외부 URL 다수) | 1,800+ (로컬 PNG) |
| 수식 | 없음 | 15+ 파일 |

---

## 5. 잠재적 문제

- URL 인코딩된 한국어 경로
- `Untitled.png` 충돌 → MD5 해시 기반 이름 변경
- Notion static URL 만료 가능 → 다운로드 시도, 실패 시 URL 유지
- 1,068 KB 대용량 파일 → OpenAI 15,000자 truncation
- 15개 비디오 → `[Video: 파일명.mp4]` 텍스트 대체
