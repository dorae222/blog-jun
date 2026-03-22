#!/usr/bin/env python3
"""
entry.json → content.json 자동 생성 스크립트.
entry.json의 description, key_detail, training_detail, specs를 기반으로
구조화된 마크다운 content.json을 생성한다.

사용법:
    python pipeline/generate_arch_content.py              # 전체 생성
    python pipeline/generate_arch_content.py --dry-run    # 미리보기
    python pipeline/generate_arch_content.py --slug bert  # 특정 slug만
"""
import json
import argparse
from pathlib import Path


ARCH_DIR = Path(__file__).resolve().parent / "data" / "architectures_written"

# architecture_category → 한글 카테고리명
CATEGORY_NAMES = {
    'llm': '대규모 언어 모델 (LLM)',
    'ssm': '상태 공간 모델 (SSM)',
    'diffusion': '확산 모델 (Diffusion)',
    'vision': '비전 모델 (Vision)',
    'multimodal': '멀티모달 모델 (Multimodal)',
    'agent': 'AI 에이전트 (Agent)',
    'technique': '핵심 기법 (Technique)',
}

# branch_type → 한글
BRANCH_NAMES = {
    'decoder_only': 'Decoder-only',
    'encoder_only': 'Encoder-only',
    'encoder_decoder': 'Encoder-Decoder',
    'ssm': 'State Space Model',
    'hybrid': 'Hybrid',
    'diffusion': 'Diffusion',
    'vision': 'Vision',
    'multimodal': 'Multimodal',
    'agent': 'Agent Framework',
}

# decoder_type → 한글
DECODER_NAMES = {
    'dense': 'Dense',
    'sparse_moe': 'Sparse MoE',
    'soft_moe': 'Soft MoE',
    'ssm': 'SSM',
    'hybrid_ssm': 'Hybrid SSM',
    'diffusion_unet': 'Diffusion UNet',
    'diffusion_dit': 'Diffusion DiT',
    'agent': 'Agent',
}


def generate_title_ko(entry: dict) -> str:
    """한글 제목 생성."""
    name = entry['name']
    cat = entry.get('architecture_category', '')
    org = entry.get('organization', '')
    desc = entry.get('description', '')

    # 짧은 설명을 제목에 활용
    if cat == 'llm':
        if 'MoE' in str(entry.get('decoder_type', '')) or 'MoE' in desc:
            return f"{name}: MoE 기반 대규모 언어 모델"
        elif entry.get('is_open_source'):
            return f"{name}: 오픈소스 대규모 언어 모델"
        else:
            return f"{name}: 대규모 언어 모델"
    elif cat == 'ssm':
        return f"{name}: 상태 공간 기반 시퀀스 모델"
    elif cat == 'diffusion':
        if 'video' in desc.lower() or 'video' in name.lower():
            return f"{name}: 확산 기반 비디오 생성 모델"
        else:
            return f"{name}: 확산 기반 이미지 생성 모델"
    elif cat == 'vision':
        return f"{name}: 비전 트랜스포머 기반 모델"
    elif cat == 'multimodal':
        return f"{name}: 멀티모달 AI 모델"
    elif cat == 'agent':
        return f"{name}: AI 에이전트 프레임워크"
    elif cat == 'technique':
        return f"{name}: AI 핵심 기법"
    return f"{name}"


def generate_summary(entry: dict) -> str:
    """요약 생성 (500자 이내)."""
    parts = []
    desc = entry.get('description', '')
    if desc:
        # 첫 2-3문장 추출
        sentences = desc.replace('。', '.').split('.')
        summary_text = '.'.join(sentences[:3]).strip()
        if summary_text and not summary_text.endswith('.'):
            summary_text += '.'
        parts.append(summary_text)

    return ' '.join(parts)[:500]


def build_specs_table(entry: dict) -> str:
    """스펙 테이블 생성."""
    specs = []
    if entry.get('param_scale'):
        specs.append(f"| 파라미터 | {entry['param_scale']} |")
    if entry.get('context_length'):
        specs.append(f"| 컨텍스트 길이 | {entry['context_length']} |")
    if entry.get('attention_type'):
        specs.append(f"| 어텐션 | {entry['attention_type']} |")
    if entry.get('normalization'):
        specs.append(f"| 정규화 | {entry['normalization']} |")
    if entry.get('activation'):
        specs.append(f"| 활성화 | {entry['activation']} |")
    if entry.get('position_encoding'):
        specs.append(f"| 위치 인코딩 | {entry['position_encoding']} |")
    if entry.get('vocab_size'):
        specs.append(f"| 어휘 크기 | {entry['vocab_size']} |")
    if entry.get('hidden_dim'):
        specs.append(f"| 히든 차원 | {entry['hidden_dim']} |")
    if entry.get('num_layers'):
        specs.append(f"| 레이어 수 | {entry['num_layers']} |")
    if entry.get('num_heads'):
        specs.append(f"| 어텐션 헤드 | {entry['num_heads']} |")
    if entry.get('num_experts'):
        active = entry.get('active_experts', 'N/A')
        specs.append(f"| 전문가 수 | {entry['num_experts']} (활성: {active}) |")

    if not specs:
        return ""

    header = "| 항목 | 값 |\n|------|---|\n"
    return header + "\n".join(specs)


def build_concepts_section(entry: dict) -> str:
    """핵심 개념 섹션."""
    concepts = entry.get('concepts', [])
    if not concepts:
        return ""

    items = [f"- **{c}**" for c in concepts]
    return "### 핵심 개념\n\n" + "\n".join(items)


def build_relations_section(entry: dict) -> str:
    """관련 모델 섹션 (entry.json relations 기반)."""
    relations = entry.get('relations', [])
    if not relations:
        return ""

    type_labels = {
        'evolved_from': '발전 기반',
        'inspired_by': '영감',
        'technique_used': '사용 기법',
        'variant_of': '변형',
    }

    items = []
    for rel in relations:
        label = type_labels.get(rel['type'], rel['type'])
        items.append(f"- **{rel['to']}** — {label}")

    return "### 관련 모델\n\n" + "\n".join(items)


def generate_content(entry: dict) -> str:
    """전체 마크다운 콘텐츠 생성."""
    name = entry['name']
    slug = entry['slug']
    cat = entry.get('architecture_category', '')
    cat_name = CATEGORY_NAMES.get(cat, cat)
    org = entry.get('organization', '')
    release = entry.get('release_date', '')
    desc = entry.get('description', '')
    key_detail = entry.get('key_detail', '')
    training = entry.get('training_detail', '')
    branch = BRANCH_NAMES.get(entry.get('branch_type', ''), '')
    decoder = DECODER_NAMES.get(entry.get('decoder_type', ''), '')

    sections = []

    # 제목
    sections.append(f"# {name}\n")

    # 메타 정보
    meta_parts = []
    if org:
        meta_parts.append(f"**{org}**")
    if release:
        meta_parts.append(f"**{release}**")
    if branch:
        meta_parts.append(f"**{branch}**")
    if decoder and decoder != branch:
        meta_parts.append(f"**{decoder}**")
    if entry.get('is_open_source'):
        meta_parts.append("**오픈소스**")
    elif entry.get('license_type') == 'proprietary':
        meta_parts.append("**Proprietary**")
    if meta_parts:
        sections.append(" · ".join(meta_parts) + "\n")

    # 개요
    if desc:
        sections.append(f"## 개요\n\n{desc}\n")

    # 아키텍처 다이어그램 참조
    sections.append("![Architecture](figures/architecture.svg)\n")

    # 아키텍처 상세
    if key_detail:
        sections.append(f"## 아키텍처 상세\n\n{key_detail}\n")

    # 스펙 테이블
    specs = build_specs_table(entry)
    if specs:
        sections.append(f"## 모델 사양\n\n{specs}\n")

    # 핵심 개념
    concepts = build_concepts_section(entry)
    if concepts:
        sections.append(concepts + "\n")

    # 학습
    if training:
        sections.append(f"## 학습\n\n{training}\n")

    # 관련 모델
    rels = build_relations_section(entry)
    if rels:
        sections.append(rels + "\n")

    # 참고 자료
    links = []
    if entry.get('paper_url'):
        links.append(f"- [논문]({entry['paper_url']})")
    if entry.get('code_url'):
        links.append(f"- [코드]({entry['code_url']})")
    if links:
        sections.append("## 참고 자료\n\n" + "\n".join(links) + "\n")

    return "\n".join(sections)


def generate_tags(entry: dict) -> list[str]:
    """태그 생성 (카테고리 중복 제거)."""
    # 카테고리 중복 태그 제거 대상
    category_tags = {
        'LLM', 'llm', 'Transformer', 'transformer',
        'SSM', 'ssm', 'Diffusion', 'diffusion',
        'Vision', 'vision', 'Multimodal', 'multimodal',
        'Agent', 'agent', 'AI', 'ai', 'AI/ML',
        'NLP', 'nlp', 'Deep Learning', 'Machine Learning',
    }

    tags = set()

    # concepts에서 태그 추출
    for c in entry.get('concepts', []):
        if c not in category_tags:
            tags.add(c)

    # organization 추가
    org = entry.get('organization', '')
    if org:
        # 짧은 org명만 태그로
        org_short = org.split('/')[0].split(',')[0].strip()
        if len(org_short) <= 30:
            tags.add(org_short)

    # name 자체 추가
    tags.add(entry['name'])

    return sorted(tags)


def process_entry(slug: str, dry_run: bool = False) -> bool:
    """단일 entry 처리."""
    entry_dir = ARCH_DIR / slug
    entry_json = entry_dir / "entry.json"
    content_json = entry_dir / "content.json"

    if not entry_json.exists():
        print(f"  [SKIP] entry.json 없음: {slug}")
        return False

    if content_json.exists():
        print(f"  [SKIP] content.json 이미 존재: {slug}")
        return False

    with open(entry_json, encoding="utf-8") as f:
        entry = json.load(f)

    title_ko = generate_title_ko(entry)
    summary = generate_summary(entry)
    content = generate_content(entry)
    tags = generate_tags(entry)

    data = {
        "slug": entry['slug'],
        "title": entry['name'],
        "title_ko": title_ko,
        "summary": summary,
        "content": content,
        "tags": tags,
    }

    if dry_run:
        words = len(content.split())
        print(f"  [DRY-RUN] {slug}: {words} words, {len(tags)} tags → {title_ko}")
        return True

    with open(content_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    words = len(content.split())
    print(f"  [CREATE] {slug}: {words} words, {len(tags)} tags")
    return True


def main():
    parser = argparse.ArgumentParser(description='entry.json → content.json 생성')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    parser.add_argument('--slug', type=str, help='특정 slug만 처리')
    args = parser.parse_args()

    prefix = "[DRY-RUN] " if args.dry_run else ""
    print(f"\n{prefix}generate_arch_content.py 시작")
    print("=" * 60)

    created = 0

    if args.slug:
        if process_entry(args.slug, args.dry_run):
            created = 1
    else:
        for entry_dir in sorted(ARCH_DIR.iterdir()):
            if not entry_dir.is_dir():
                continue
            if process_entry(entry_dir.name, args.dry_run):
                created += 1

    print("=" * 60)
    print(f"{prefix}완료: {created}개 content.json 생성")


if __name__ == "__main__":
    main()
