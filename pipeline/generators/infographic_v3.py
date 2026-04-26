"""
인포그래픽 v4 - 정보 밀도 + 3:2 비율 재설계.

설계 원칙:
1. 1200x800 (3:2) - 16:7 와이드 폐기, 정보 위주
2. 4-zone 레이아웃:
   - HEADER: meta + headline (y=0~210)
   - HERO: 좌측 4 specs + 우측 graphic (y=230~490)
   - KPI: 3-4 metric cards 풀폭 (y=520~640)
   - FOOTER: concepts + watermark (y=680~770)
3. 카테고리별 단일 액센트 (cardColors.js 동기)
4. 정보 밀도: spec 4-5개, KPI 3개, concepts 4-5개
5. 자동 폰트/클램핑
"""
from __future__ import annotations


# ──────────────────────────────────────────────────────────────────
# 디자인 토큰
# ──────────────────────────────────────────────────────────────────

W, H = 1200, 920
PAD_X = 56

# Zones (y coordinates)
HEADER_TOP = 56
TITLE_Y = 130
SUBTITLE_Y = 184
HERO_TOP = 240
HERO_BOTTOM = 490
EVIDENCE_TOP = 520
EVIDENCE_BOTTOM = 660
KPI_TOP = 690
KPI_BOTTOM = 800
FOOTER_TOP = 840

# 좌측/우측 컬럼
LEFT_X = PAD_X + 24       # 80
LEFT_W = 440
RIGHT_X = 600
RIGHT_W = W - RIGHT_X - PAD_X - 24  # 520

# 카테고리별 단일 액센트 컬러 (cardColors.js 동기)
ACCENT = {
    "llm":         "#3b82f6",
    "moe":         "#8b5cf6",
    "ssm":         "#06b6d4",
    "diffusion":   "#f97316",
    "vision":      "#0ea5e9",
    "multimodal":  "#a855f7",
    "agent":       "#ef4444",
    "technique":   "#64748b",
    "efficiency":  "#f59e0b",
    "embedding":   "#10b981",
    "rag":         "#0ea5e9",
    "aws_compute":     "#FF9900",
    "aws_storage":     "#3F8624",
    "aws_database":    "#C925D1",
    "aws_networking":  "#8C4FFF",
    "aws_security":    "#DD344C",
    "aws_analytics":   "#1A73E8",
    "aws_ai_ml":       "#01A88D",
    "aws_integration": "#F59E0B",
    "aws_management":  "#E7157B",
    "default":     "#3b82f6",
}

LABEL = {
    "llm": "LLM", "moe": "MoE", "ssm": "SSM", "diffusion": "Diffusion",
    "vision": "Vision", "multimodal": "Multimodal", "agent": "Agent",
    "technique": "Technique", "efficiency": "Efficiency", "embedding": "Embedding",
    "rag": "RAG", "aws_compute": "Compute", "aws_storage": "Storage",
    "aws_database": "Database", "aws_networking": "Networking",
    "aws_security": "Security", "aws_analytics": "Analytics",
    "aws_ai_ml": "AI/ML", "aws_integration": "Integration",
    "aws_management": "Management", "default": "",
}


def _esc(s: str | None) -> str:
    if not s:
        return ""
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&apos;"))


def _clip(s: str, n: int) -> str:
    if not s:
        return ""
    return s if len(s) <= n else s[:n - 1] + "…"


def _title_size(name: str) -> int:
    n = len(name)
    if n <= 14:
        return 56
    if n <= 22:
        return 48
    if n <= 32:
        return 40
    return 32


def _parse_param_size(s: str) -> float:
    """'49B', '1.6T', '405B' → B 단위 정규화"""
    if not s:
        return 0
    s = s.replace(",", "").strip()
    multiplier = 1
    if s.endswith("T"):
        multiplier = 1000
        s = s[:-1]
    elif s.endswith("B"):
        multiplier = 1
        s = s[:-1]
    elif s.endswith("M"):
        multiplier = 0.001
        s = s[:-1]
    try:
        return float(s) * multiplier
    except ValueError:
        return 0


# ──────────────────────────────────────────────────────────────────
# 공통 컴포넌트
# ──────────────────────────────────────────────────────────────────

def _open(w=W, h=H) -> str:
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="\'Inter\', -apple-system, \'Apple SD Gothic Neo\', \'Noto Sans KR\', sans-serif">')


def _defs(accent: str) -> str:
    return f'''  <defs>
    <radialGradient id="bg-blue" cx="15%" cy="20%" r="55%">
      <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="bg-purple" cx="85%" cy="80%" r="55%">
      <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0"/>
    </radialGradient>
    <filter id="cardSh" x="-3%" y="-3%" width="106%" height="108%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="14"/>
      <feOffset dx="0" dy="6"/>
      <feComponentTransfer><feFuncA type="linear" slope="0.06"/></feComponentTransfer>
      <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="{accent}"/>
    </marker>
  </defs>'''


def _bg(w=W, h=H) -> str:
    return f'''  <rect width="{w}" height="{h}" fill="#ffffff"/>
  <rect width="{w}" height="{h}" fill="url(#bg-blue)"/>
  <rect width="{w}" height="{h}" fill="url(#bg-purple)"/>'''


def _card(x=32, y=24, w=W - 64, h=H - 48) -> str:
    return f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="rgba(255,255,255,0.85)" filter="url(#cardSh)"/>'


def _meta_line(category: str, org: str, year: str | int, accent: str, lineage: str = "") -> str:
    label = LABEL.get(category, "")
    org_e = _esc(org)
    year_e = _esc(str(year))
    chip_w = max(48, len(label) * 8 + 16)

    parts = [f'''  <g transform="translate({LEFT_X}, {HEADER_TOP})">
    <rect x="0" y="0" width="{chip_w}" height="22" rx="11" fill="{accent}" fill-opacity="0.12"/>
    <text x="{chip_w//2}" y="15" text-anchor="middle" font-size="11" font-weight="700" fill="{accent}" letter-spacing="0.8">{label}</text>
    <text x="{chip_w + 14}" y="15" font-size="13" font-weight="500" fill="#475569">{org_e}</text>
    <circle cx="{chip_w + 14 + len(org_e) * 7 + 12}" cy="11" r="2" fill="#cbd5e1"/>
    <text x="{chip_w + 14 + len(org_e) * 7 + 22}" y="15" font-size="13" font-weight="500" fill="#64748b">{year_e}</text>''']
    if lineage:
        parts.append(f'    <text x="{W - 2 * PAD_X - 24}" y="15" text-anchor="end" font-size="12" font-weight="500" fill="#94a3b8">{_esc(lineage)}</text>')
    parts.append('  </g>')
    return "\n".join(parts)


def _headline_block(name: str, subtitle: str) -> str:
    name_e = _esc(name)
    sub_e = _esc(_clip(subtitle, 80))
    fs = _title_size(name)

    return f'''  <g transform="translate({LEFT_X}, {TITLE_Y})">
    <text font-size="{fs}" font-weight="800" fill="#0f172a" letter-spacing="-1.5">{name_e}</text>
    <text x="0" y="{fs + 4}" font-size="16" font-weight="400" fill="#475569" letter-spacing="-0.2">{sub_e}</text>
  </g>'''


def _section_label(text: str, x: int, y: int, accent: str) -> str:
    return f'  <text x="{x}" y="{y}" font-size="10" font-weight="700" fill="{accent}" letter-spacing="1.5">{_esc(text).upper()}</text>'


def _spec_list(specs: list[tuple[str, str]], y_offset: int = HERO_TOP) -> str:
    """좌측 핵심 사양 (4개)"""
    parts = [f'  <g transform="translate({LEFT_X}, {y_offset})">']
    for i, (label, value) in enumerate(specs[:4]):
        y = i * 60
        parts.append(f'''    <g transform="translate(0, {y})">
      <text x="0" y="0" font-size="10" font-weight="700" fill="#94a3b8" letter-spacing="1.2">{_esc(label).upper()}</text>
      <text x="0" y="22" font-size="15" font-weight="600" fill="#0f172a">{_esc(_clip(value, 50))}</text>
      <line x1="0" y1="40" x2="{LEFT_W - 24}" y2="40" stroke="#f1f5f9" stroke-width="1"/>
    </g>''')
    parts.append('  </g>')
    return "\n".join(parts)


def _kpi_strip(metrics: list[dict], accent: str) -> str:
    """하단 KPI 카드 (3-4개 풀폭)"""
    n = min(len(metrics), 4)
    if n == 0:
        return ""
    inner_w = W - 2 * (LEFT_X)
    gap = 16
    card_w = (inner_w - gap * (n - 1)) // n
    parts = [f'  <g transform="translate({LEFT_X}, {KPI_TOP})">']
    for i, m in enumerate(metrics[:n]):
        x = i * (card_w + gap)
        label = _esc(m.get("label", "")).upper()
        value = _esc(m.get("value", ""))
        sub = _esc(m.get("sub", ""))
        parts.append(f'''    <g transform="translate({x}, 0)">
      <rect x="0" y="0" width="{card_w}" height="110" rx="12" fill="white" stroke="#e2e8f0" stroke-width="1"/>
      <rect x="0" y="0" width="3" height="110" rx="1.5" fill="{accent}"/>
      <text x="22" y="28" font-size="10" font-weight="700" fill="#94a3b8" letter-spacing="1.2">{label}</text>
      <text x="22" y="68" font-size="32" font-weight="900" fill="#0f172a" letter-spacing="-1">{value}</text>
      <text x="22" y="92" font-size="12" font-weight="500" fill="#64748b">{sub}</text>
    </g>''')
    parts.append('  </g>')
    return "\n".join(parts)


def _footer(concepts: list[str], accent: str) -> str:
    parts = [f'  <line x1="{LEFT_X}" y1="{FOOTER_TOP - 20}" x2="{W - LEFT_X}" y2="{FOOTER_TOP - 20}" stroke="#e2e8f0" stroke-width="1"/>']
    parts.append(f'  <g transform="translate({LEFT_X}, {FOOTER_TOP + 20})">')
    cx = 0
    for i, c in enumerate(concepts[:5]):
        c_e = _esc(c)
        w = max(70, len(c_e) * 8 + 18)
        opacity_text = 1.0 - (i * 0.08)
        opacity_fill = 0.06 + i * 0.02
        opacity_stroke = 0.22 - i * 0.03
        parts.append(f'''    <g transform="translate({cx}, 0)">
      <rect x="0" y="-15" width="{w}" height="22" rx="11" fill="{accent}" fill-opacity="{opacity_fill:.2f}" stroke="{accent}" stroke-opacity="{opacity_stroke:.2f}" stroke-width="1"/>
      <text x="{w//2}" y="0" text-anchor="middle" font-size="11" font-weight="600" fill="{accent}" fill-opacity="{opacity_text:.2f}">{c_e}</text>
    </g>''')
        cx += w + 8
    parts.append(f'    <text x="{W - 2 * LEFT_X}" y="0" text-anchor="end" font-size="10" font-weight="500" fill="#94a3b8" letter-spacing="0.5">blog.dorae222.com</text>')
    parts.append('  </g>')
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────
# 우측 hero graphic (HERO_TOP ~ HERO_BOTTOM, 약 250px 세로)
# 모든 graphic 의 (0, 0) = (RIGHT_X, HERO_TOP) 기준
# ──────────────────────────────────────────────────────────────────

def _graphic_big_metric(value: str, label: str, sub_label: str, accent: str) -> str:
    """LLM Frontier - 큰 숫자"""
    return f'''  <g transform="translate({RIGHT_X}, {HERO_TOP})">
    <rect x="0" y="0" width="{RIGHT_W}" height="{HERO_BOTTOM - HERO_TOP}" rx="14" fill="{accent}" fill-opacity="0.04"/>
    <text x="32" y="40" font-size="11" font-weight="700" fill="{accent}" letter-spacing="1.5">{_esc(label).upper()}</text>
    <text x="32" y="170" font-size="120" font-weight="900" fill="#0f172a" letter-spacing="-5">{_esc(value)}</text>
    <text x="32" y="210" font-size="14" font-weight="500" fill="#64748b">{_esc(sub_label)}</text>
    <line x1="32" y1="225" x2="{RIGHT_W - 32}" y2="225" stroke="{accent}" stroke-opacity="0.2" stroke-width="1"/>
  </g>'''


def _graphic_donut(active: str, total: str, accent: str) -> str:
    """MoE - 도넛 + 정확한 비율"""
    active_n = _parse_param_size(active)
    total_n = _parse_param_size(total)
    ratio = (active_n / total_n) if total_n > 0 else 0
    circumference = 2 * 3.14159 * 96
    arc = circumference * ratio
    if 0 < arc < 12:
        arc = 12
    gap = circumference - arc
    pct = ratio * 100
    cx = RIGHT_W // 2
    cy = (HERO_BOTTOM - HERO_TOP) // 2
    return f'''  <g transform="translate({RIGHT_X}, {HERO_TOP})">
    <rect x="0" y="0" width="{RIGHT_W}" height="{HERO_BOTTOM - HERO_TOP}" rx="14" fill="{accent}" fill-opacity="0.04"/>
    <g transform="translate({cx}, {cy})">
      <circle cx="0" cy="0" r="96" fill="none" stroke="#e2e8f0" stroke-width="20"/>
      <circle cx="0" cy="0" r="96" fill="none" stroke="{accent}" stroke-width="20" stroke-linecap="round"
              stroke-dasharray="{arc:.1f} {gap:.1f}" transform="rotate(-90)"/>
      <text x="0" y="-12" text-anchor="middle" font-size="11" font-weight="700" fill="#94a3b8" letter-spacing="1.2">ACTIVE</text>
      <text x="0" y="20" text-anchor="middle" font-size="36" font-weight="900" fill="#0f172a">{_esc(active)}</text>
      <text x="0" y="44" text-anchor="middle" font-size="13" font-weight="500" fill="#64748b">{pct:.1f}% of {_esc(total)}</text>
    </g>
  </g>'''


def _graphic_size_bar(small_label: str, small_size: str, big_label: str, big_size: str, accent: str) -> str:
    """SLM - 사이즈 비교"""
    bar_w = RIGHT_W - 80
    small_n = _parse_param_size(small_size)
    big_n = _parse_param_size(big_size)
    small_bar = max(40, int(bar_w * (small_n / big_n))) if big_n > 0 else 40
    return f'''  <g transform="translate({RIGHT_X}, {HERO_TOP})">
    <rect x="0" y="0" width="{RIGHT_W}" height="{HERO_BOTTOM - HERO_TOP}" rx="14" fill="{accent}" fill-opacity="0.04"/>
    <text x="32" y="40" font-size="11" font-weight="700" fill="{accent}" letter-spacing="1.5">SIZE COMPARISON</text>

    <g transform="translate(32, 80)">
      <text x="0" y="0" font-size="14" font-weight="700" fill="#0f172a">{_esc(small_label)}</text>
      <text x="{bar_w}" y="0" text-anchor="end" font-size="14" font-weight="800" fill="{accent}">{_esc(small_size)}</text>
      <rect x="0" y="14" width="{small_bar}" height="20" rx="10" fill="{accent}"/>
    </g>

    <g transform="translate(32, 150)">
      <text x="0" y="0" font-size="14" font-weight="600" fill="#94a3b8">{_esc(big_label)}</text>
      <text x="{bar_w}" y="0" text-anchor="end" font-size="14" font-weight="600" fill="#94a3b8">{_esc(big_size)}</text>
      <rect x="0" y="14" width="{bar_w}" height="20" rx="10" fill="#cbd5e1"/>
    </g>

    <g transform="translate(32, 218)">
      <rect x="0" y="0" width="14" height="14" rx="3" fill="{accent}" fill-opacity="0.15"/>
      <text x="22" y="11" font-size="12" font-weight="500" fill="#475569">edge-deployable · single GPU inference</text>
    </g>
  </g>'''


def _graphic_matryoshka(dim_main: str, dim_options: list[str], score: str, score_label: str, accent: str) -> str:
    """Embedding - Matryoshka 동심원"""
    cx = RIGHT_W // 3
    cy = (HERO_BOTTOM - HERO_TOP) // 2
    radii = [88, 68, 48, 28]
    parts = [f'  <g transform="translate({RIGHT_X}, {HERO_TOP})">']
    parts.append(f'    <rect x="0" y="0" width="{RIGHT_W}" height="{HERO_BOTTOM - HERO_TOP}" rx="14" fill="{accent}" fill-opacity="0.04"/>')
    parts.append(f'    <g transform="translate({cx}, {cy})">')
    for i, r in enumerate(radii):
        op = 0.18 + i * 0.16
        parts.append(f'      <circle cx="0" cy="0" r="{r}" fill="{accent}" fill-opacity="{op:.2f}"/>')
    parts.append(f'      <text x="0" y="6" text-anchor="middle" font-size="22" font-weight="800" fill="white">{_esc(dim_main)}</text>')
    parts.append('    </g>')
    info_x = cx + 130
    parts.append(f'    <g transform="translate({info_x}, 50)">')
    parts.append(f'      <text x="0" y="0" font-size="10" font-weight="700" fill="{accent}" letter-spacing="1.5">TRUNCATABLE DIMS</text>')
    for i, d in enumerate(dim_options[:4]):
        y = 26 + i * 24
        parts.append(f'      <rect x="0" y="{y - 12}" width="80" height="20" rx="4" fill="{accent}" fill-opacity="0.1"/>')
        parts.append(f'      <text x="40" y="{y + 3}" text-anchor="middle" font-size="13" font-weight="700" fill="{accent}">{_esc(d)}</text>')
    parts.append(f'      <text x="0" y="160" font-size="10" font-weight="700" fill="#94a3b8" letter-spacing="1.5">{_esc(score_label).upper()}</text>')
    parts.append(f'      <text x="0" y="200" font-size="40" font-weight="900" fill="#0f172a" letter-spacing="-1.5">{_esc(score)}</text>')
    parts.append('    </g>')
    parts.append('  </g>')
    return "\n".join(parts)


def _graphic_modalities(mods: list[str], accent: str) -> str:
    """Multimodal - 모달리티 그리드"""
    box_w = (RIGHT_W - 64 - 16) // 2
    box_h = 90
    parts = [f'  <g transform="translate({RIGHT_X}, {HERO_TOP})">']
    parts.append(f'    <rect x="0" y="0" width="{RIGHT_W}" height="{HERO_BOTTOM - HERO_TOP}" rx="14" fill="{accent}" fill-opacity="0.04"/>')
    parts.append(f'    <text x="32" y="40" font-size="11" font-weight="700" fill="{accent}" letter-spacing="1.5">SUPPORTED MODALITIES</text>')
    for i, m in enumerate(mods[:4]):
        col = i % 2
        row = i // 2
        x = 32 + col * (box_w + 16)
        y = 70 + row * (box_h + 16)
        parts.append(f'''    <g transform="translate({x}, {y})">
      <rect x="0" y="0" width="{box_w}" height="{box_h}" rx="10" fill="white" stroke="{accent}" stroke-opacity="0.3" stroke-width="1.5"/>
      <circle cx="32" cy="{box_h//2}" r="20" fill="{accent}" fill-opacity="0.15"/>
      <text x="32" y="{box_h//2 + 6}" text-anchor="middle" font-size="18" font-weight="800" fill="{accent}">{_esc(m[0]).upper()}</text>
      <text x="64" y="{box_h//2 + 6}" font-size="16" font-weight="700" fill="#0f172a">{_esc(m)}</text>
    </g>''')
    parts.append('  </g>')
    return "\n".join(parts)


def _graphic_aws_flow(trigger: str, action: str, output: str, accent: str) -> str:
    """AWS - Trigger → Service → Output"""
    box_w = 130
    box_h = 100
    gap = 26
    total_w = box_w * 3 + gap * 2
    start_x = (RIGHT_W - total_w) // 2
    cy = (HERO_BOTTOM - HERO_TOP) // 2 - 20
    parts = [f'  <g transform="translate({RIGHT_X}, {HERO_TOP})">']
    parts.append(f'    <rect x="0" y="0" width="{RIGHT_W}" height="{HERO_BOTTOM - HERO_TOP}" rx="14" fill="{accent}" fill-opacity="0.04"/>')
    parts.append(f'    <text x="32" y="40" font-size="11" font-weight="700" fill="{accent}" letter-spacing="1.5">EVENT FLOW</text>')

    boxes = [
        (start_x + 0, "TRIGGER", trigger, "#94a3b8"),
        (start_x + box_w + gap, "SERVICE", action, accent),
        (start_x + 2 * (box_w + gap), "OUTPUT", output, "#94a3b8"),
    ]
    for x, label, value, color in boxes:
        is_main = (color == accent)
        bg = f'{accent}' if is_main else 'white'
        bg_op = '0.1' if is_main else '1'
        parts.append(f'''    <g transform="translate({x}, {cy})">
      <rect x="0" y="0" width="{box_w}" height="{box_h}" rx="12" fill="{bg}" fill-opacity="{bg_op}" stroke="{color}" stroke-opacity="0.5" stroke-width="1.5"/>
      <text x="{box_w//2}" y="28" text-anchor="middle" font-size="10" font-weight="700" fill="{color}" letter-spacing="1.5">{label}</text>
      <text x="{box_w//2}" y="62" text-anchor="middle" font-size="14" font-weight="700" fill="#0f172a">{_esc(_clip(value, 14))}</text>
    </g>''')
    # 화살표
    arrow_y = cy + box_h // 2
    for i in range(2):
        ax = start_x + (i + 1) * box_w + i * gap + 4
        parts.append(f'    <line x1="{ax}" y1="{arrow_y}" x2="{ax + gap - 8}" y2="{arrow_y}" stroke="{accent}" stroke-width="2" marker-end="url(#arr)"/>')
    parts.append('  </g>')
    return "\n".join(parts)


def _graphic_pipeline_flow(steps: list[dict], accent: str) -> str:
    """RAG/Pipeline - 단계 박스"""
    n = min(len(steps), 4)
    box_w = (RIGHT_W - 64 - (n - 1) * 14) // n
    box_h = 110
    cy = (HERO_BOTTOM - HERO_TOP) // 2 - 30
    parts = [f'  <g transform="translate({RIGHT_X}, {HERO_TOP})">']
    parts.append(f'    <rect x="0" y="0" width="{RIGHT_W}" height="{HERO_BOTTOM - HERO_TOP}" rx="14" fill="{accent}" fill-opacity="0.04"/>')
    parts.append(f'    <text x="32" y="40" font-size="11" font-weight="700" fill="{accent}" letter-spacing="1.5">PIPELINE STEPS</text>')
    for i, step in enumerate(steps[:n]):
        x = 32 + i * (box_w + 14)
        title_e = _esc(_clip(step.get("title", ""), 14))
        desc_e = _esc(_clip(step.get("desc", ""), 22))
        parts.append(f'''    <g transform="translate({x}, {cy})">
      <rect x="0" y="0" width="{box_w}" height="{box_h}" rx="12" fill="white" stroke="{accent}" stroke-opacity="0.35" stroke-width="1.5"/>
      <circle cx="22" cy="22" r="13" fill="{accent}" fill-opacity="0.18"/>
      <text x="22" y="27" text-anchor="middle" font-size="12" font-weight="800" fill="{accent}">{i+1}</text>
      <text x="{box_w//2}" y="62" text-anchor="middle" font-size="13" font-weight="700" fill="#0f172a">{title_e}</text>
      <text x="{box_w//2}" y="84" text-anchor="middle" font-size="10" font-weight="500" fill="#64748b">{desc_e}</text>
    </g>''')
        if i < n - 1:
            ax = 32 + (i + 1) * box_w + i * 14 + 1
            parts.append(f'    <line x1="{ax}" y1="{cy + box_h//2}" x2="{ax + 12}" y2="{cy + box_h//2}" stroke="{accent}" stroke-width="2" marker-end="url(#arr)"/>')
    parts.append('  </g>')
    return "\n".join(parts)


def _graphic_paper_diff(bench: str, ours: str, baseline: str, diff: str, accent: str) -> str:
    """Paper Review - 차이 시각화"""
    return f'''  <g transform="translate({RIGHT_X}, {HERO_TOP})">
    <rect x="0" y="0" width="{RIGHT_W}" height="{HERO_BOTTOM - HERO_TOP}" rx="14" fill="{accent}" fill-opacity="0.04"/>
    <text x="32" y="40" font-size="11" font-weight="700" fill="{accent}" letter-spacing="1.5">{_esc(bench).upper()}</text>

    <g transform="translate(32, 76)">
      <text x="0" y="0" font-size="11" font-weight="600" fill="#94a3b8" letter-spacing="0.8">OURS</text>
      <text x="0" y="48" font-size="56" font-weight="900" fill="#0f172a" letter-spacing="-2">{_esc(ours)}</text>
      <rect x="0" y="64" width="{RIGHT_W - 64}" height="6" rx="3" fill="#e2e8f0"/>
      <rect x="0" y="64" width="{int((RIGHT_W - 64) * 0.85)}" height="6" rx="3" fill="{accent}"/>
    </g>

    <g transform="translate(32, 168)">
      <text x="0" y="0" font-size="11" font-weight="600" fill="#94a3b8" letter-spacing="0.8">BASELINE</text>
      <text x="0" y="28" font-size="28" font-weight="700" fill="#94a3b8">{_esc(baseline)}</text>
      <rect x="0" y="40" width="{int((RIGHT_W - 64) * 0.62)}" height="6" rx="3" fill="#cbd5e1"/>
    </g>

    <g transform="translate({RIGHT_W - 184}, 178)">
      <rect x="0" y="0" width="160" height="56" rx="12" fill="#10b981" fill-opacity="0.14"/>
      <text x="80" y="28" text-anchor="middle" font-size="22" font-weight="900" fill="#10b981" letter-spacing="-0.5">{_esc(diff)}</text>
      <text x="80" y="46" text-anchor="middle" font-size="10" font-weight="600" fill="#10b981" fill-opacity="0.75" letter-spacing="0.5">ABSOLUTE GAIN</text>
    </g>
  </g>'''


# ──────────────────────────────────────────────────────────────────
# 좌측 hero info — spec 라벨
# ──────────────────────────────────────────────────────────────────

def _hero_left_label(accent: str) -> str:
    return f'  <text x="{LEFT_X}" y="{HERO_TOP - 14}" font-size="10" font-weight="700" fill="{accent}" letter-spacing="1.5">SPECIFICATIONS</text>'


# ──────────────────────────────────────────────────────────────────
# EVIDENCE 블록 (카테고리별 데이터 테이블/차트)
# (LEFT_X, EVIDENCE_TOP) ~ (W - LEFT_X, EVIDENCE_BOTTOM) 풀폭 사용
# ──────────────────────────────────────────────────────────────────

def _evidence_container(title: str, accent: str, body_inner: str) -> str:
    inner_w = W - 2 * LEFT_X
    h = EVIDENCE_BOTTOM - EVIDENCE_TOP
    return f'''  <g transform="translate({LEFT_X}, {EVIDENCE_TOP})">
    <rect x="0" y="0" width="{inner_w}" height="{h}" rx="14" fill="white" stroke="#e2e8f0" stroke-width="1"/>
    <text x="22" y="28" font-size="10" font-weight="700" fill="{accent}" letter-spacing="1.5">{_esc(title).upper()}</text>
    {body_inner}
  </g>'''


def _evidence_bench_bars(rows: list[dict], accent: str) -> str:
    """벤치마크 가로 막대 (LLM/MoE/Paper)
    rows: [{"name": "SWE-bench", "value": "82.0", "scale": 0.82, "note": "+3.8 pp"}, ...]
    """
    inner_w = W - 2 * LEFT_X
    bar_max = inner_w - 360  # 라벨/숫자 영역 제외
    parts = []
    for i, r in enumerate(rows[:4]):
        y = 56 + i * 24
        scale = max(0.0, min(1.0, float(r.get("scale", 0))))
        bar_w = int(bar_max * scale)
        parts.append(f'    <text x="22" y="{y}" font-size="12" font-weight="600" fill="#0f172a">{_esc(r.get("name", ""))}</text>')
        parts.append(f'    <rect x="160" y="{y - 11}" width="{bar_max}" height="14" rx="3" fill="#f1f5f9"/>')
        parts.append(f'    <rect x="160" y="{y - 11}" width="{bar_w}" height="14" rx="3" fill="{accent}"/>')
        parts.append(f'    <text x="{160 + bar_max + 12}" y="{y}" font-size="13" font-weight="700" fill="#0f172a">{_esc(r.get("value", ""))}</text>')
        if r.get("note"):
            parts.append(f'    <text x="{160 + bar_max + 96}" y="{y}" font-size="11" font-weight="500" fill="#10b981">{_esc(r["note"])}</text>')
    return _evidence_container("Benchmark scoreboard", accent, "\n".join(parts))


def _evidence_table(headers: list[str], rows: list[list[str]], accent: str, title: str = "Comparison") -> str:
    """범용 데이터 테이블 (MoE 구성, RAG 비교, AWS 사용 패턴 등)"""
    inner_w = W - 2 * LEFT_X
    parts = []
    n_cols = len(headers)
    col_w = (inner_w - 44) // n_cols
    # 헤더
    for i, h in enumerate(headers):
        x = 22 + i * col_w
        parts.append(f'    <text x="{x}" y="56" font-size="10" font-weight="700" fill="#94a3b8" letter-spacing="1">{_esc(h).upper()}</text>')
    parts.append(f'    <line x1="22" y1="64" x2="{inner_w - 22}" y2="64" stroke="#e2e8f0" stroke-width="1"/>')
    # 데이터 행 (간격 24px로 압축, 컨테이너 140px 내에 안전하게)
    for r_idx, row in enumerate(rows[:3]):
        y = 82 + r_idx * 24
        for c_idx, cell in enumerate(row[:n_cols]):
            x = 22 + c_idx * col_w
            is_first = (c_idx == 0)
            color = "#0f172a" if not is_first else accent
            weight = "700" if is_first else "600"
            parts.append(f'    <text x="{x}" y="{y}" font-size="13" font-weight="{weight}" fill="{color}">{_esc(_clip(str(cell), col_w // 8))}</text>')
        if r_idx < len(rows[:3]) - 1:
            parts.append(f'    <line x1="22" y1="{y + 6}" x2="{inner_w - 22}" y2="{y + 6}" stroke="#f1f5f9" stroke-width="1"/>')
    return _evidence_container(title, accent, "\n".join(parts))


def _evidence_stack(title: str, items: list[dict], accent: str) -> str:
    """수직 스택 표시 (Multimodal 인코더, AWS 패턴 등)
    items: [{"label": "Vision Encoder", "value": "SigLIP-400M", "note": "frozen"}, ...]
    """
    inner_w = W - 2 * LEFT_X
    parts = []
    n = min(len(items), 3)
    col_w = (inner_w - 44 - 16 * (n - 1)) // n
    for i, it in enumerate(items[:n]):
        x = 22 + i * (col_w + 16)
        parts.append(f'''    <g transform="translate({x}, 50)">
      <rect x="0" y="0" width="{col_w}" height="74" rx="10" fill="{accent}" fill-opacity="0.05" stroke="{accent}" stroke-opacity="0.2" stroke-width="1"/>
      <text x="14" y="22" font-size="10" font-weight="700" fill="{accent}" letter-spacing="1.2">{_esc(it.get("label", "")).upper()}</text>
      <text x="14" y="46" font-size="15" font-weight="700" fill="#0f172a">{_esc(_clip(it.get("value", ""), col_w // 8))}</text>
      <text x="14" y="64" font-size="11" font-weight="500" fill="#64748b">{_esc(_clip(it.get("note", ""), col_w // 7))}</text>
    </g>''')
    return _evidence_container(title, accent, "\n".join(parts))


# ──────────────────────────────────────────────────────────────────
# 메인 entry point
# ──────────────────────────────────────────────────────────────────

def render_card(
    *,
    category: str,
    name: str,
    org: str,
    year: str | int,
    subtitle: str,
    specs: list[tuple[str, str]],
    concepts: list[str],
    graphic_type: str,
    graphic_args: dict,
    kpis: list[dict] | None = None,
    evidence_type: str | None = None,
    evidence_args: dict | None = None,
    lineage: str = "",
) -> str:
    """카테고리 공통 카드 생성기.

    graphic_type: 'big_metric' | 'donut' | 'size_bar' | 'matryoshka'
                  | 'modalities' | 'aws_flow' | 'pipeline' | 'paper_diff'

    kpis: 하단 KPI 스트립용 [{"label": "...", "value": "...", "sub": "..."}, ...] (3-4개)

    evidence_type: 'bench_bars' | 'table' | 'stack'
    evidence_args: 카테고리별 데이터
    """
    accent = ACCENT.get(category, ACCENT["default"])
    kpis = kpis or []

    parts = [_open()]
    parts.append(_defs(accent))
    parts.append(_bg())
    parts.append(_card())

    # HEADER
    parts.append(_meta_line(category, org, year, accent, lineage))
    parts.append(_headline_block(name, subtitle))

    # HERO: 좌측 specs + 우측 graphic
    parts.append(_hero_left_label(accent))
    parts.append(_spec_list(specs, y_offset=HERO_TOP))

    g = graphic_type
    a = graphic_args
    if g == "big_metric":
        parts.append(_graphic_big_metric(a["value"], a["label"], a["sub_label"], accent))
    elif g == "donut":
        parts.append(_graphic_donut(a["active"], a["total"], accent))
    elif g == "size_bar":
        parts.append(_graphic_size_bar(a["small_label"], a["small_size"], a["big_label"], a["big_size"], accent))
    elif g == "matryoshka":
        parts.append(_graphic_matryoshka(a["dim_main"], a["dim_options"], a["score"], a["score_label"], accent))
    elif g == "modalities":
        parts.append(_graphic_modalities(a["mods"], accent))
    elif g == "aws_flow":
        parts.append(_graphic_aws_flow(a["trigger"], a["action"], a["output"], accent))
    elif g == "pipeline":
        parts.append(_graphic_pipeline_flow(a["steps"], accent))
    elif g == "paper_diff":
        parts.append(_graphic_paper_diff(a["bench"], a["ours"], a["baseline"], a["diff"], accent))

    # EVIDENCE 블록 (카테고리별 추가 데이터)
    if evidence_type and evidence_args:
        e = evidence_args
        if evidence_type == "bench_bars":
            parts.append(_evidence_bench_bars(e["rows"], accent))
        elif evidence_type == "table":
            parts.append(_evidence_table(e["headers"], e["rows"], accent, e.get("title", "Comparison")))
        elif evidence_type == "stack":
            parts.append(_evidence_stack(e.get("title", "Components"), e["items"], accent))

    # KPI strip
    if kpis:
        parts.append(_kpi_strip(kpis, accent))

    # FOOTER
    parts.append(_footer(concepts, accent))
    parts.append("</svg>")
    return "\n".join(parts)
