#!/usr/bin/env python3
"""
paper_review content.json 영문 기술 용어 보존 처리 스크립트
- 한글 번역 병기 제거, 영문 용어로 통일
- \(...\) → $...$ 포맷 변환
- 코드 블록, LaTeX 수식 내부 수정 금지
"""

import json
import re
import os
import glob
from pathlib import Path

# ──────────────────────────────────────────────
# 치환 규칙 (순서 중요: 더 구체적인 것 먼저)
# ──────────────────────────────────────────────
REPLACEMENTS = [
    # 수식 포맷 변환 (코드 블록 밖에서만)
    # \( ... \) → $ ... $ 는 별도 처리

    # 헤딩 내 한글(영문) 패턴
    (r'### 인코더 \(Encoder\)', '### Encoder'),
    (r'### 디코더 \(Decoder\)', '### Decoder'),
    (r'### 인코더\(Encoder\)', '### Encoder'),
    (r'### 디코더\(Decoder\)', '### Decoder'),
    (r'## 인코더 \(Encoder\)', '## Encoder'),
    (r'## 디코더 \(Decoder\)', '## Decoder'),

    # 인라인 한글(영문) 패턴
    (r'순환 신경망\(RNN\)', 'RNN'),
    (r'순환 신경망 \(RNN\)', 'RNN'),
    (r'합성곱 신경망\(CNN\)', 'CNN'),
    (r'합성곱 신경망 \(CNN\)', 'CNN'),
    (r'레이어 정규화\(Layer Normalization\)', 'Layer Normalization'),
    (r'레이어 정규화 \(Layer Normalization\)', 'Layer Normalization'),
    (r'잔차 연결\(Residual Connection\)', 'Residual Connection'),
    (r'잔차 연결 \(Residual Connection\)', 'Residual Connection'),
    (r'쿼리\(Query\)', 'Query'),
    (r'쿼리 \(Query\)', 'Query'),
    (r'키\(Key\)', 'Key'),
    (r'키 \(Key\)', 'Key'),
    (r'값\(Value\)', 'Value'),
    (r'값 \(Value\)', 'Value'),
    (r'미세 조정\(Fine-tuning\)', 'Fine-tuning'),
    (r'미세 조정 \(Fine-tuning\)', 'Fine-tuning'),
    (r'미세조정\(Fine-tuning\)', 'Fine-tuning'),
    (r'사전 훈련\(Pre-training\)', 'Pre-training'),
    (r'사전 훈련 \(Pre-training\)', 'Pre-training'),
    (r'사전훈련\(Pre-training\)', 'Pre-training'),
    (r'임베딩\(Embedding\)', 'Embedding'),
    (r'임베딩 \(Embedding\)', 'Embedding'),
    (r'어텐션\(Attention\)', 'Attention'),
    (r'어텐션 \(Attention\)', 'Attention'),
    (r'인코더\(Encoder\)', 'Encoder'),
    (r'인코더 \(Encoder\)', 'Encoder'),
    (r'디코더\(Decoder\)', 'Decoder'),
    (r'디코더 \(Decoder\)', 'Decoder'),
    (r'셀프 어텐션\(Self-Attention\)', 'Self-Attention'),
    (r'셀프 어텐션 \(Self-Attention\)', 'Self-Attention'),
    (r'크로스 어텐션\(Cross-Attention\)', 'Cross-Attention'),
    (r'크로스 어텐션 \(Cross-Attention\)', 'Cross-Attention'),
    (r'멀티 헤드 어텐션\(Multi-Head Attention\)', 'Multi-Head Attention'),
    (r'멀티헤드 어텐션\(Multi-Head Attention\)', 'Multi-Head Attention'),
    (r'피드 포워드\(Feed-Forward\)', 'Feed-Forward'),
    (r'피드포워드\(Feed-Forward\)', 'Feed-Forward'),
    (r'배치 정규화\(Batch Normalization\)', 'Batch Normalization'),
    (r'배치 정규화 \(Batch Normalization\)', 'Batch Normalization'),
    (r'그룹 쿼리 어텐션\(Grouped Query Attention\)', 'Grouped Query Attention'),
    (r'그룹 쿼리 어텐션 \(GQA\)', 'GQA (Grouped Query Attention)'),
    (r'슬라이딩 윈도우 어텐션\(Sliding Window Attention\)', 'Sliding Window Attention'),
    (r'회전 위치 임베딩\(RoPE\)', 'RoPE (Rotary Position Embedding)'),
    (r'회전 위치 인코딩\(RoPE\)', 'RoPE (Rotary Position Embedding)'),
    (r'전문가 혼합\(Mixture of Experts\)', 'Mixture of Experts (MoE)'),
    (r'전문가 혼합 \(MoE\)', 'Mixture of Experts (MoE)'),
    (r'지식 증류\(Knowledge Distillation\)', 'Knowledge Distillation'),
    (r'양자화\(Quantization\)', 'Quantization'),
    (r'가지치기\(Pruning\)', 'Pruning'),
    (r'과적합\(Overfitting\)', 'Overfitting'),
    (r'과소적합\(Underfitting\)', 'Underfitting'),
    (r'드롭아웃\(Dropout\)', 'Dropout'),
    (r'정규화\(Normalization\)', 'Normalization'),
    (r'토크나이저\(Tokenizer\)', 'Tokenizer'),
    (r'어휘 \(Vocabulary\)', 'Vocabulary'),
    (r'어휘\(Vocabulary\)', 'Vocabulary'),
    (r'컨텍스트 윈도우\(Context Window\)', 'Context Window'),
    (r'컨텍스트 \(Context\)', 'Context'),
    (r'프롬프트\(Prompt\)', 'Prompt'),
    (r'프롬프트 튜닝\(Prompt Tuning\)', 'Prompt Tuning'),
    (r'파인튜닝\(Fine-tuning\)', 'Fine-tuning'),
    (r'파인 튜닝\(Fine-tuning\)', 'Fine-tuning'),
    (r'강화 학습\(Reinforcement Learning\)', 'Reinforcement Learning'),
    (r'강화학습\(RL\)', 'Reinforcement Learning (RL)'),

    # 추가 어텐션 패턴
    (r'슬라이딩 윈도우 어텐션\(SWA, Sliding Window Attention\)', 'SWA (Sliding Window Attention)'),
    (r'\*\*슬라이딩 윈도우 어텐션\(SWA, Sliding Window Attention\)\*\*', '**SWA (Sliding Window Attention)**'),
    (r'슬라이딩 윈도우 어텐션\(SWA\)', 'SWA (Sliding Window Attention)'),
    (r'그룹 쿼리 어텐션\(GQA\)', 'GQA (Grouped Query Attention)'),
    (r'멀티헤드 어텐션\(MHA\)', 'Multi-Head Attention (MHA)'),
    (r'멀티 헤드 어텐션\(MHA\)', 'Multi-Head Attention (MHA)'),
    (r'단방향 어텐션\(causal attention\)', 'causal attention'),
    (r'단방향 어텐션\(Causal Attention\)', 'Causal Attention'),

    # 추가 임베딩 패턴
    (r'밀집 임베딩\(dense embedding\)', 'dense embedding'),
    (r'밀집 임베딩 \(dense embedding\)', 'dense embedding'),

    # 인코더-디코더 패턴
    (r'\*\*인코더-디코더 \(Encoder-Decoder\)\*\*', '**Encoder-Decoder**'),
    (r'인코더-디코더 \(Encoder-Decoder\)', 'Encoder-Decoder'),
    (r'인코더-디코더\(Encoder-Decoder\)', 'Encoder-Decoder'),

    # Knowledge-Augmented Encoder
    (r'지식 증강 인코더 \(Knowledge-Augmented Encoder\)', 'Knowledge-Augmented Encoder'),
    (r'지식 증강 인코더\(Knowledge-Augmented Encoder\)', 'Knowledge-Augmented Encoder'),

    # 독립 한글 기술 용어 (괄호 없는 단독 사용)
    (r'순환 신경망', 'RNN'),
    (r'합성곱 신경망', 'CNN'),
    (r'잔차 연결', 'Residual Connection'),
    (r'레이어 정규화', 'Layer Normalization'),

    # 사인·코사인 위치 인코딩 (구체적 패턴 먼저)
    (r'사인·코사인 위치 인코딩', 'Positional Encoding (Sinusoidal)'),
    (r'사인/코사인 위치 인코딩', 'Positional Encoding (Sinusoidal)'),

    # 위치 인코딩 (일반)
    (r'위치 인코딩', 'Positional Encoding'),
    (r'위치 임베딩', 'Positional Embedding'),

    # 드롭아웃 제거 (표에서)
    (r'드롭아웃 제거', 'Dropout 제거'),

    # 표 헤더 치환
    (r'\|헤드 수 = 1\|', '|heads = 1|'),
    (r'헤드 수 = 1', 'heads = 1'),
    (r'\| 학습 비용', '| Training Cost'),
    (r'학습 비용 \(FLOPs\)', 'Training Cost (FLOPs)'),
    (r'학습 비용\(FLOPs\)', 'Training Cost (FLOPs)'),
    (r'기계 번역', 'Machine Translation'),
]


def split_content_by_code_blocks(text):
    """
    텍스트를 코드 블록(```)과 나머지로 분리.
    반환: [(is_code, segment), ...]
    """
    parts = []
    # ``` 구분자로 나눔
    pattern = re.compile(r'(```[\s\S]*?```)', re.MULTILINE)
    last_end = 0
    for m in pattern.finditer(text):
        if m.start() > last_end:
            parts.append((False, text[last_end:m.start()]))
        parts.append((True, m.group(0)))
        last_end = m.end()
    if last_end < len(text):
        parts.append((False, text[last_end:]))
    return parts


def convert_latex_parens(text):
    """
    \( ... \) → $ ... $
    \[ ... \] → $$ ... $$
    코드 블록 밖에서만 처리됨 (이 함수는 non-code segment에서만 호출)
    """
    # \[ ... \] → $$ ... $$ (먼저 처리)
    text = re.sub(r'\\\[([\s\S]*?)\\\]', r'$$\1$$', text)
    # \( ... \) → $ ... $
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text)
    return text


def apply_replacements(text):
    """non-code 세그먼트에 모든 치환 규칙 적용"""
    for pattern, replacement in REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    return text


def process_content(content):
    """content 문자열 전체 처리"""
    parts = split_content_by_code_blocks(content)
    result = []
    for is_code, segment in parts:
        if is_code:
            result.append(segment)
        else:
            segment = convert_latex_parens(segment)
            segment = apply_replacements(segment)
            result.append(segment)
    return ''.join(result)


def process_file(filepath):
    """단일 content.json 파일 처리"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    original_content = data.get('content', '')
    new_content = process_content(original_content)

    if new_content != original_content:
        data['content'] = new_content
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    return False


def main():
    base_dir = Path(__file__).parent / 'data' / 'papers_written'
    files = sorted(glob.glob(str(base_dir / '*' / 'content.json')))

    print(f"처리 대상: {len(files)}개 파일")
    modified = 0
    for filepath in files:
        changed = process_file(filepath)
        folder = Path(filepath).parent.name
        status = "✓ 수정" if changed else "  변경없음"
        print(f"  {status}: {folder}")
        if changed:
            modified += 1

    print(f"\n완료: {modified}/{len(files)}개 파일 수정됨")


if __name__ == '__main__':
    main()
