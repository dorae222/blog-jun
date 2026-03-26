---
name: figure-annotate
description: Claude Code 멀티모달 figure 분석 + 캡션 개선
allowed-tools: Bash(python *), Read, Edit, Glob
---
Claude Code multimodal figure annotation:

1. 대상 figure 확인:
   `pipeline/data/{type}_written/{slug}/figures/`
   - papers_written, architectures_written, ml_written, colab_written, data_written

2. Claude Code가 Read 도구로 PNG/SVG 직접 분석:
   Read pipeline/data/{type}_written/{slug}/figures/{filename}.png
   → 분석 후 적절한 한국어 캡션 작성

3. content.md에 figure 삽입 (표준 형식):
   ```markdown
   ![한국어 alt text](figures/filename.png)

   *Figure N: 한국어 캡션. (Author, Year)*
   ```

4. Figure 선별 기준:
   - 논문당 핵심 3~5개만 선별
   - 참고용/레포트 이미지 배제
   - 아키텍처 다이어그램, 실험 결과, 핵심 개념도 우선

5. DB 반영:
   `python pipeline/import_{type}_written.py --update`

참고: `figures/metadata.json` (ar5iv 크롤링 메타데이터) 활용 가능
