"""
infographic_v3 어댑터 - 카테고리별 metadata → render_card 인자 매핑.

각 카테고리(papers/architectures/cloud/ml/data/colab)의 content.json/entry.json을
infographic_v3.render_card()의 입력으로 변환한다.

데이터가 빈약한 카테고리(cloud/ml/data/colab)는 합리적 기본값으로 채운다.
"""
from __future__ import annotations
import re
from typing import Any


# ──────────────────────────────────────────────────────────────────
# 카테고리 매핑 (content category → infographic_v3 ACCENT key)
# ──────────────────────────────────────────────────────────────────

PAPER_CAT_TO_ACCENT = {
    "transformer": "llm",
    "llm": "llm",
    "moe": "moe",
    "ssm": "ssm",
    "diffusion": "diffusion",
    "vision": "vision",
    "multimodal": "multimodal",
    "agent": "agent",
    "technique": "technique",
    "efficiency": "efficiency",
    "embedding": "embedding",
    "rag": "rag",
    "reasoning": "llm",
    "code": "llm",
    "training": "technique",
}

ARCH_CAT_TO_ACCENT = {
    "llm": "llm", "moe": "moe", "ssm": "ssm", "diffusion": "diffusion",
    "vision": "vision", "multimodal": "multimodal", "agent": "agent",
    "technique": "technique", "efficiency": "efficiency",
    "embedding": "embedding", "rag": "rag",
}


def _summary_to_subtitle(summary: str, max_len: int = 70) -> str:
    """summary 첫 문장 → 한 줄 부제 (60-70자). et al./Mr. 등 약어는 건너뜀."""
    if not summary:
        return ""
    s = summary.strip()
    # 첫 문장 추출 - et al./Mr./Dr./i.e./e.g. 등 약어 직후 마침표 무시
    abbrev = re.compile(r"\b(et al|Mr|Mrs|Dr|Jr|Sr|i\.e|e\.g|cf|vs)\.")
    # 약어를 임시로 치환
    placeholder = ""
    masked = abbrev.sub(lambda m: m.group(0).replace(".", placeholder), s)
    m = re.match(r"^([^.!?。]+[.!?。])", masked)
    first = m.group(1) if m else masked
    first = first.replace(placeholder, ".").strip()
    if len(first) > max_len:
        # 단어 경계로 자르기
        cut = first[:max_len].rsplit(" ", 1)[0]
        first = cut + "…"
    return first


def _tags_to_concepts(tags: list[str], n: int = 4) -> list[str]:
    """tag 슬러그 → 사람이 읽는 concept (영문 자본화 + 하이픈→스페이스)"""
    concepts = []
    for t in tags[:n * 2]:
        c = str(t).replace("-", " ").replace("_", " ").strip()
        if not c:
            continue
        # 자본화: 단어 단위로 첫 글자만
        c = " ".join(w.capitalize() if w.islower() else w for w in c.split())
        if c not in concepts:
            concepts.append(c)
        if len(concepts) >= n:
            break
    return concepts


def _extract_year(release_date: str) -> str:
    """'2025-04-09' / '2024' / '' → 'YYYY' or ''"""
    if not release_date:
        return ""
    m = re.match(r"(\d{4})", str(release_date))
    return m.group(1) if m else ""


def _extract_param_scale(text: str) -> tuple[str, str] | None:
    """summary에서 'X B / Y B' 또는 'X 활성화' 같은 Total/Active 추출.
    e.g. '671B 총 파라미터에서 37B만 활성화' → ('37B', '671B')
    """
    # 패턴 1: 'X B 활성화' 또는 'X B만 활성'
    m_active = re.search(r"(\d+\.?\d*)\s*B\s*(?:만\s*)?활성", text)
    m_total = re.search(r"(\d+\.?\d*)\s*[BT]\s*(?:총|전체|파라미터)", text)
    if m_active and m_total:
        active = f"{m_active.group(1)}B"
        total_num = m_total.group(1)
        total_unit = "T" if "T" in m_total.group(0) else "B"
        return (active, f"{total_num}{total_unit}")
    # 패턴 2: 'X B / Y T' 같은 슬래시 형태
    m_slash = re.search(r"(\d+\.?\d*)\s*B\s*/\s*(\d+\.?\d*)\s*([BT])", text)
    if m_slash:
        return (f"{m_slash.group(1)}B", f"{m_slash.group(2)}{m_slash.group(3)}")
    return None


def _extract_bench_scores(text: str) -> list[dict]:
    """summary 텍스트에서 벤치마크 점수 추출 (정규식 기반)

    예: "EN-DE 28.4 BLEU, EN-FR 41.0 BLEU" → [
      {"name": "EN-DE", "value": "28.4", "scale": 0.284, "note": "BLEU"},
      ...
    ]
    """
    rows = []
    # 패턴: "<name> <number> <unit>" 또는 "<unit>: <number>"
    patterns = [
        r"(MMLU|GPQA|MATH(?:-500)?|SWE[- ]bench(?:\s+Verified)?|HumanEval|BLEU|BEIR|AIME(?:\s+\d+)?|LiveCodeBench|MMMU|GSM8K)\s*[:\s]+(\d+\.?\d*)\s*%?",
        r"(\d+\.?\d*)\s*(BLEU|F1|accuracy)",
        r"([A-Z][A-Za-z\-]{2,})\s+(\d+\.?\d*)\s*BLEU",
    ]
    seen_names = set()
    for pat in patterns:
        for m in re.finditer(pat, text):
            groups = m.groups()
            if len(groups) >= 2:
                name = groups[0]
                value = groups[1]
                if not name or name in seen_names:
                    continue
                if not re.match(r"^\d", value):
                    name, value = value, name
                if name in seen_names:
                    continue
                try:
                    f = float(value)
                    scale = min(1.0, f / 100) if f > 1 else f
                    rows.append({"name": name, "value": value, "scale": scale, "note": ""})
                    seen_names.add(name)
                except ValueError:
                    pass
            if len(rows) >= 4:
                break
        if len(rows) >= 4:
            break
    return rows[:4]


# ──────────────────────────────────────────────────────────────────
# 카테고리별 어댑터
# ──────────────────────────────────────────────────────────────────

def adapt_paper(content_json: dict) -> dict:
    """papers_written/{slug}/content.json → render_card kwargs"""
    cat_raw = (content_json.get("category") or "").lower()
    sub_cat = (content_json.get("sub_category") or "").lower()
    accent = PAPER_CAT_TO_ACCENT.get(cat_raw) or PAPER_CAT_TO_ACCENT.get(sub_cat) or "llm"

    title = content_json.get("title") or content_json.get("title_ko") or "Paper"
    authors = content_json.get("authors") or "Authors"
    year = content_json.get("year") or ""
    venue = content_json.get("venue") or ""
    summary = content_json.get("summary") or ""
    tags = content_json.get("tags") or []

    # specs (4) - dedup + 다양한 정보 우선순위
    specs_raw = []
    if venue:
        specs_raw.append(("Venue", venue))
    if year:
        specs_raw.append(("Year", str(year)))
    if cat_raw:
        specs_raw.append(("Category", cat_raw.upper()))
    if content_json.get("arxiv_url"):
        arxiv_id = content_json["arxiv_url"].rstrip("/").split("/")[-1]
        specs_raw.append(("arXiv", arxiv_id))
    if content_json.get("related_architecture"):
        specs_raw.append(("Architecture", content_json["related_architecture"]))
    if tags:
        specs_raw.append(("Topics", ", ".join(tags[:3])))
    # dedup by label
    seen_labels = set()
    specs = []
    for label, val in specs_raw:
        if label not in seen_labels and val:
            specs.append((label, val))
            seen_labels.add(label)
    while len(specs) < 4:
        specs.append(("Type", "Paper Review"))
        break

    # 벤치마크 + 파라미터 스케일 추출
    bench_rows = _extract_bench_scores(summary)
    param_pair = _extract_param_scale(summary)

    # graphic 결정 (우선순위)
    if cat_raw == "moe" and param_pair:
        active, total = param_pair
        graphic_type = "donut"
        graphic_args = {"active": active, "total": total}
    elif bench_rows and len(bench_rows) >= 2:
        top = bench_rows[0]
        graphic_type = "paper_diff"
        graphic_args = {
            "bench": top["name"],
            "ours": f'{top["value"]}{"%" if float(top["value"]) <= 100 else ""}',
            "baseline": "—",
            "diff": f'+{top["value"]} {top.get("note") or ""}'.strip(),
        }
    elif param_pair:
        active, total = param_pair
        graphic_type = "big_metric"
        graphic_args = {
            "value": total,
            "label": "Parameters",
            "sub_label": f"{active} active" if active != total else "dense",
        }
    else:
        graphic_type = "big_metric"
        graphic_args = {
            "value": venue if venue and len(venue) <= 8 else (str(year) if year else "Paper"),
            "label": cat_raw.upper() if cat_raw else "Research",
            "sub_label": authors,
        }

    # evidence: 항상 제공 (벤치 우선 → 태그 fallback)
    if bench_rows and len(bench_rows) >= 2:
        evidence_type = "bench_bars"
        evidence_args = {"rows": bench_rows}
    else:
        # 태그 기반 stack fallback
        evidence_type = "stack"
        items = []
        if venue:
            items.append({"label": "Venue", "value": venue, "note": str(year) if year else ""})
        if content_json.get("related_architecture"):
            items.append({"label": "Architecture", "value": content_json["related_architecture"], "note": "linked"})
        items.append({"label": "Topics", "value": tags[0] if tags else "research", "note": f"{len(tags)} tags"})
        # 최소 3개 보장
        while len(items) < 3:
            items.append({"label": "Format", "value": "Paper Review", "note": "summary"})
        evidence_args = {"title": "Paper highlights", "items": items[:3]}

    return {
        "category": accent,
        "name": title,
        "org": authors,
        "year": str(year) if year else "",
        "subtitle": _summary_to_subtitle(summary),
        "specs": specs[:4],
        "concepts": _tags_to_concepts(tags, 4),
        "graphic_type": graphic_type,
        "graphic_args": graphic_args,
        "evidence_type": evidence_type,
        "evidence_args": evidence_args,
        "kpis": [
            {"label": "Year", "value": str(year) if year else "—", "sub": venue or "preprint"},
            {"label": "Tags", "value": str(len(tags)), "sub": "topics"},
            {"label": "Open", "value": "arXiv" if content_json.get("arxiv_url") else "—", "sub": "preprint"},
        ],
        "lineage": "",
    }


def adapt_architecture(entry_json: dict) -> dict:
    """architectures_written/{slug}/entry.json → render_card kwargs"""
    cat_raw = (entry_json.get("architecture_category") or "").lower()
    branch = (entry_json.get("branch_type") or "").lower()
    accent = ARCH_CAT_TO_ACCENT.get(cat_raw) or ARCH_CAT_TO_ACCENT.get(branch) or "llm"

    name = entry_json.get("name") or "Architecture"
    org = entry_json.get("organization") or "—"
    year = _extract_year(entry_json.get("release_date") or "")
    desc = entry_json.get("description") or ""
    concepts = entry_json.get("concepts") or []
    param_scale = entry_json.get("param_scale") or ""
    context_length = entry_json.get("context_length") or ""
    attention_type = entry_json.get("attention_type") or ""
    license_type = entry_json.get("license_type") or ""

    # specs (4) - dedup
    specs_raw = []
    if entry_json.get("decoder_type"):
        specs_raw.append(("Type", entry_json["decoder_type"]))
    if attention_type:
        specs_raw.append(("Attention", attention_type))
    if param_scale:
        specs_raw.append(("Parameters", param_scale))
    if context_length:
        specs_raw.append(("Context", context_length))
    if license_type:
        specs_raw.append(("License", license_type))
    if entry_json.get("activation"):
        specs_raw.append(("Activation", entry_json["activation"]))
    if entry_json.get("position_encoding"):
        specs_raw.append(("Pos. Encoding", entry_json["position_encoding"]))
    seen_labels = set()
    specs = []
    for label, val in specs_raw:
        if label not in seen_labels and val:
            specs.append((label, val))
            seen_labels.add(label)
    if len(specs) < 4:
        specs.append(("Open Source", "Yes" if entry_json.get("is_open_source") else "Closed"))
    while len(specs) < 4:
        specs.append(("Org", org))

    # graphic 결정: MoE면 donut, params 있으면 big_metric, 그 외 big_metric
    num_experts = entry_json.get("num_experts")
    active_experts = entry_json.get("active_experts")
    if cat_raw == "moe" and num_experts and active_experts:
        graphic_type = "donut"
        graphic_args = {"active": f"{active_experts}", "total": f"{num_experts}"}
    elif param_scale:
        graphic_type = "big_metric"
        graphic_args = {
            "value": param_scale,
            "label": "Parameters",
            "sub_label": f"context: {context_length}" if context_length else (entry_json.get("decoder_type") or ""),
        }
    else:
        graphic_type = "big_metric"
        graphic_args = {
            "value": year or "—",
            "label": cat_raw.upper() or "Architecture",
            "sub_label": org,
        }

    # evidence: 주요 사양 표
    evidence_type = "table"
    rows = []
    for label, value in specs[:3]:
        rows.append([label, str(value), ""])
    if entry_json.get("num_layers"):
        rows.append(["Layers", str(entry_json["num_layers"]), f"hidden_dim={entry_json.get('hidden_dim') or '—'}"])
    if not rows:
        evidence_type = None
        evidence_args = None
    else:
        evidence_args = {
            "title": "Architecture details",
            "headers": ["Component", "Value", "Notes"],
            "rows": rows[:3],
        }

    # lineage from relations
    lineage = ""
    relations = entry_json.get("relations") or []
    for r in relations:
        if r.get("type") in ("evolved_from", "successor_of", "improved"):
            lineage = f"{r.get('to', '')} → {entry_json.get('slug', '')}"
            break

    return {
        "category": accent,
        "name": name,
        "org": org,
        "year": year,
        "subtitle": _summary_to_subtitle(desc),
        "specs": specs[:4],
        "concepts": [c for c in concepts if c][:4] or _tags_to_concepts([cat_raw, branch], 4),
        "graphic_type": graphic_type,
        "graphic_args": graphic_args,
        "evidence_type": evidence_type,
        "evidence_args": evidence_args,
        "kpis": [
            {"label": "Year", "value": year or "—", "sub": "release"},
            {"label": "License", "value": license_type or "—", "sub": "—"},
            {"label": "Open", "value": "✓" if entry_json.get("is_open_source") else "—", "sub": "weights"},
        ],
        "lineage": lineage,
    }


# AWS 카테고리 → 인포그래픽 카테고리 매핑
AWS_CAT_MAP = {
    "aws-compute": "aws_compute",
    "aws-storage": "aws_storage",
    "aws-database": "aws_database",
    "aws-networking": "aws_networking",
    "aws-security": "aws_security",
    "aws-analytics": "aws_analytics",
    "aws-ai-ml": "aws_ai_ml",
    "aws-integration": "aws_integration",
    "aws-management": "aws_management",
    "aws-devtools": "aws_management",
}

# 일반적인 AWS flow 추정 (서비스별 hardcode)
AWS_FLOWS = {
    "aws-compute": ("Event source", "Compute", "Storage / DB"),
    "aws-storage": ("App / Client", "Storage", "Lambda / Athena"),
    "aws-database": ("Application", "Database", "Cache / Backup"),
    "aws-networking": ("Client", "Network", "Origin / Service"),
    "aws-security": ("Identity", "Security", "Resource"),
    "aws-analytics": ("Source", "Analytics", "Visualization"),
    "aws-ai-ml": ("Data", "Model", "Endpoint"),
    "aws-integration": ("Producer", "Integration", "Consumer"),
    "aws-management": ("Resource", "Management", "Action / Log"),
}


def adapt_cloud(content_json: dict) -> dict:
    """cloud_written/{slug}/content.json → render_card kwargs (AWS 서비스)"""
    cat_slug = (content_json.get("category_slug") or "").lower()
    accent = AWS_CAT_MAP.get(cat_slug, "aws_compute")

    title = content_json.get("title") or "AWS Service"
    summary = content_json.get("summary") or ""
    tags = content_json.get("tags") or []

    flow = AWS_FLOWS.get(cat_slug, ("Source", "Service", "Output"))
    # 서비스명을 action 자리에 (제목에서 'Amazon ' 또는 'AWS ' 제거)
    action = re.sub(r"^(Amazon|AWS)\s+", "", title)

    specs = [
        ("Category", cat_slug.replace("-", " ").upper() if cat_slug else "AWS"),
        ("Type", "Managed Service"),
        ("Tags", ", ".join(tags[:3]) if tags else "AWS"),
        ("Provider", "Amazon Web Services"),
    ]

    return {
        "category": accent,
        "name": action,
        "org": "AWS",
        "year": "",
        "subtitle": _summary_to_subtitle(summary),
        "specs": specs,
        "concepts": _tags_to_concepts(tags, 4),
        "graphic_type": "aws_flow",
        "graphic_args": {"trigger": flow[0], "action": action[:14], "output": flow[2]},
        "evidence_type": "stack",
        "evidence_args": {
            "title": "Common usage patterns",
            "items": [
                {"label": "Use Case", "value": tags[0] if tags else "Service", "note": "primary"},
                {"label": "Integrates", "value": tags[1] if len(tags) > 1 else "—", "note": "with"},
                {"label": "Scale", "value": "Managed", "note": "auto-scaling"},
            ],
        },
        "kpis": [
            {"label": "Service", "value": "Managed", "sub": "AWS-operated"},
            {"label": "SLA", "value": "99.9%+", "sub": "typical"},
            {"label": "Tags", "value": str(len(tags)), "sub": "topics"},
        ],
        "lineage": "",
    }


# ML/Data/Colab — 가벼운 메타데이터, 간단한 카드
def _topic_stack_fallback(tags: list[str], category_label: str) -> dict:
    """tag 기반 evidence stack fallback (최대 3개)"""
    items = []
    for t in tags[:3]:
        items.append({
            "label": "Topic",
            "value": str(t).replace("-", " ").title()[:18],
            "note": category_label,
        })
    while len(items) < 3:
        items.append({"label": "Format", "value": "Article", "note": category_label})
    return {"title": "Topic coverage", "items": items}


def adapt_ml(content_json: dict) -> dict:
    title = content_json.get("title") or content_json.get("title_ko") or "ML Topic"
    sub_cat = (content_json.get("sub_category") or "fundamentals").lower()
    summary = content_json.get("summary") or ""
    tags = content_json.get("tags") or []
    sub_label = sub_cat.replace("-", " ").title()

    return {
        "category": "technique",
        "name": title,
        "org": "Machine Learning",
        "year": "",
        "subtitle": _summary_to_subtitle(summary),
        "specs": [
            ("Subcategory", sub_label),
            ("Tags", ", ".join(tags[:3]) if tags else "—"),
            ("Type", "Educational"),
            ("Format", "Article / Tutorial"),
        ],
        "concepts": _tags_to_concepts(tags, 4),
        "graphic_type": "big_metric",
        "graphic_args": {
            "value": str(len(tags)),
            "label": "Concepts covered",
            "sub_label": sub_label,
        },
        "evidence_type": "stack",
        "evidence_args": _topic_stack_fallback(tags, sub_label),
        "kpis": [
            {"label": "Topic", "value": sub_label[:10], "sub": "subcategory"},
            {"label": "Tags", "value": str(len(tags)), "sub": "topics"},
            {"label": "Type", "value": "Article", "sub": "tutorial"},
        ],
        "lineage": "",
    }


def adapt_data(content_json: dict) -> dict:
    title = content_json.get("title") or "Data Topic"
    cat_slug = (content_json.get("category_slug") or "data").lower()
    summary = content_json.get("summary") or ""
    tags = content_json.get("tags") or []
    cat_label = cat_slug.replace("-", " ").title()
    return {
        "category": "technique",
        "name": title,
        "org": "Data Engineering",
        "year": "",
        "subtitle": _summary_to_subtitle(summary),
        "specs": [
            ("Category", cat_label),
            ("Type", "Engineering"),
            ("Tags", ", ".join(tags[:3]) if tags else "—"),
            ("Domain", "Data Pipeline / Storage"),
        ],
        "concepts": _tags_to_concepts(tags, 4),
        "graphic_type": "big_metric",
        "graphic_args": {
            "value": str(len(tags)),
            "label": "Concepts",
            "sub_label": cat_label,
        },
        "evidence_type": "stack",
        "evidence_args": _topic_stack_fallback(tags, cat_label),
        "kpis": [
            {"label": "Domain", "value": cat_slug[:10].title(), "sub": "data"},
            {"label": "Tags", "value": str(len(tags)), "sub": "topics"},
            {"label": "Type", "value": "Article", "sub": "engineering"},
        ],
        "lineage": "",
    }


def adapt_colab(content_json: dict) -> dict:
    title = content_json.get("title") or "Tutorial"
    cat_slug = (content_json.get("category_slug") or "tutorial").lower()
    summary = content_json.get("summary") or ""
    tags = content_json.get("tags") or []
    series_slug = content_json.get("series_slug") or ""
    series_order = content_json.get("series_order") or ""
    cat_label = cat_slug.replace("-", " ").title()
    lineage = f"{series_order:>02} of series {series_slug}" if series_order and series_slug else ""

    return {
        "category": "technique",
        "name": title,
        "org": "Tutorial",
        "year": "",
        "subtitle": _summary_to_subtitle(summary),
        "specs": [
            ("Format", "Hands-on Tutorial"),
            ("Category", cat_label),
            ("Series", series_slug or "—"),
            ("Tags", ", ".join(tags[:3]) if tags else "—"),
        ],
        "concepts": _tags_to_concepts(tags, 4),
        "graphic_type": "big_metric",
        "graphic_args": {
            "value": "Hands-on",
            "label": "Tutorial",
            "sub_label": cat_label,
        },
        "evidence_type": "stack",
        "evidence_args": _topic_stack_fallback(tags, cat_label),
        "kpis": [
            {"label": "Series", "value": (series_slug[:10] if series_slug else "—"), "sub": f"order {series_order}" if series_order else "standalone"},
            {"label": "Tags", "value": str(len(tags)), "sub": "topics"},
            {"label": "Type", "value": "Tutorial", "sub": "step-by-step"},
        ],
        "lineage": lineage,
    }


# ──────────────────────────────────────────────────────────────────
# 디스패처
# ──────────────────────────────────────────────────────────────────

def adapt(content_type: str, data: dict) -> dict:
    """content_type ∈ {paper, architecture, cloud, ml, data, colab}"""
    fn = {
        "paper": adapt_paper,
        "architecture": adapt_architecture,
        "cloud": adapt_cloud,
        "ml": adapt_ml,
        "data": adapt_data,
        "colab": adapt_colab,
    }.get(content_type)
    if not fn:
        raise ValueError(f"unknown content_type: {content_type}")
    return fn(data)
