#!/usr/bin/env python3
"""
Figure 삽입 헬퍼 스크립트

사용법:
  python insert_figures.py <content.json 경로> <삽입 설정 JSON 파일 경로>

설정 JSON 형식:
[
  {
    "filename": "fig_1.png",
    "section": "## 방법론",
    "alt": "Transformer 전체 아키텍처",
    "caption": "Figure 1: Transformer 모델 아키텍처. 인코더(왼쪽)와 디코더(오른쪽)로 구성된 seq2seq 구조. (Vaswani et al., 2017)",
    "after_nth_paragraph": 1
  },
  ...
]

after_nth_paragraph: 섹션 헤더 이후 몇 번째 문단 뒤에 삽입할지 (1-indexed, 기본값 1)
"""
import json
import re
import sys
import os


def insert_figure_into_section(content: str, section_heading: str, figure_md: str, after_nth: int = 1) -> str:
    """
    지정한 섹션 헤더 이후 N번째 문단 뒤에 figure markdown을 삽입합니다.
    섹션을 찾지 못하면 content를 그대로 반환합니다.
    """
    # 섹션 헤더 위치 찾기
    escaped = re.escape(section_heading)
    match = re.search(r'^' + escaped + r'\s*$', content, re.MULTILINE)
    if not match:
        # 섹션을 찾지 못함
        print(f"  [WARN] 섹션 '{section_heading}' 찾지 못함 — 삽입 건너뜀", file=sys.stderr)
        return content

    section_start = match.end()

    # 다음 섹션 헤더 (## 또는 ###) 위치 찾기
    next_section = re.search(r'\n##+ ', content[section_start:])
    if next_section:
        section_end = section_start + next_section.start()
    else:
        section_end = len(content)

    section_body = content[section_start:section_end]

    # 해당 섹션 내 문단 경계 찾기 (빈 줄 기준)
    paragraphs = re.split(r'\n\n+', section_body.strip())
    if not paragraphs:
        # 빈 섹션이면 헤더 바로 뒤에 삽입
        insert_point = section_start
        new_content = content[:insert_point] + '\n\n' + figure_md + content[insert_point:]
        return new_content

    # N번째 문단 이후 삽입 위치 계산
    n = min(after_nth, len(paragraphs))
    # 실제 삽입 위치: 섹션 시작 + N개 문단 길이 누적
    accumulated = 0
    raw = section_body
    for i, para in enumerate(paragraphs):
        # 각 문단의 위치를 raw 텍스트에서 찾기
        pos = raw.find(para.strip(), accumulated)
        if pos >= 0:
            accumulated = pos + len(para.strip())
        if i + 1 >= n:
            break

    # 실제 content에서의 삽입 위치
    # section_start에서 시작, raw 내 accumulated 위치에 삽입
    raw_strip_offset = len(section_body) - len(section_body.lstrip('\n'))
    insert_offset = section_start + raw_strip_offset + accumulated

    # figure가 이미 삽입되어 있는지 확인 (figures/xxx.png 패턴으로 추출)
    img_match = re.search(r'\(figures/([^)]+)\)', figure_md)
    basename = img_match.group(1) if img_match else ''
    if basename and basename in content:
        print(f"  [SKIP] {basename} 이미 본문에 존재 — 중복 삽입 건너뜀", file=sys.stderr)
        return content

    # 삽입
    new_content = content[:insert_offset] + '\n\n' + figure_md + content[insert_offset:]
    return new_content


def main():
    if len(sys.argv) < 3:
        print("사용법: python insert_figures.py <content.json> <insertions.json>")
        sys.exit(1)

    content_path = sys.argv[1]
    insertions_path = sys.argv[2]

    with open(content_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(insertions_path, 'r', encoding='utf-8') as f:
        insertions = json.load(f)

    # content.md 우선, 없으면 content.json['content'] 폴백
    content_md_path = os.path.join(os.path.dirname(content_path), 'content.md')
    use_md = os.path.exists(content_md_path)
    if use_md:
        with open(content_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = data['content']
    inserted = 0

    for item in insertions:
        filename = item['filename']
        section = item['section']
        alt = item.get('alt', '')
        caption = item.get('caption', '')
        after_nth = item.get('after_nth_paragraph', 1)

        figure_md = f'![{alt}](figures/{filename})\n*{caption}*'
        new_content = insert_figure_into_section(content, section, figure_md, after_nth)

        if new_content != content:
            print(f"  [OK] {filename} → {section}")
            content = new_content
            inserted += 1
        else:
            if filename in content:
                print(f"  [SKIP] {filename} 이미 존재")
            else:
                print(f"  [FAIL] {filename} 삽입 실패")

    if use_md:
        with open(content_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n완료: {inserted}/{len(insertions)}개 figure 삽입 → {content_md_path}")
    else:
        data['content'] = content
        test = json.loads(json.dumps(data))
        assert test['content'] == content, "JSON 인코딩 오류"
        with open(content_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n완료: {inserted}/{len(insertions)}개 figure 삽입 → {content_path}")


if __name__ == '__main__':
    main()
