#!/usr/bin/env python3
"""
57개 논문의 architecture.svg 파일을 자동 생성하는 스크립트.

각 논문의 content.json에서 제목을 읽고, 논문 그룹(LLM, MoE, RLHF 등)에 따라
적절한 아키텍처 다이어그램 SVG를 생성한다.

Usage:
    python pipeline/generate_paper_svgs.py
"""
import json
import os
import textwrap
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PAPERS_DIR = BASE_DIR / "data" / "papers_written"

# ── 색상 팔레트 ──────────────────────────────────────────────────────────
PURPLE = "#9B59B6"
BLUE = "#4A90D9"
LIGHT_BLUE = "#5DADE2"
ORANGE = "#E8833A"
GREEN = "#A8D5A2"
RED = "#E74C3C"
YELLOW = "#F39C12"
DARK_TEXT = "#2C3E50"
MID_TEXT = "#555"
LIGHT_TEXT = "#777"
BG_LIGHT = "#F8F9FA"
BG_PURPLE = "#F3E8F9"
BG_BLUE = "#E8F4FD"
BG_ORANGE = "#FDF0E6"
BG_GREEN = "#EAF7E8"
BG_RED = "#FDECEC"
BG_YELLOW = "#FEF5E7"

# ── 논문 그룹 매핑 ──────────────────────────────────────────────────────
PAPER_GROUPS = {
    # 1. LLM Architecture
    1: "llm", 2: "llm", 3: "llm", 5: "llm", 6: "llm",
    7: "llm", 8: "llm_moe", 11: "llm", 12: "llm", 13: "llm",
    14: "llm", 15: "llm", 16: "llm",
    # 2. MoE
    9: "moe", 10: "moe", 38: "moe", 39: "moe",
    # 3. Alignment/RLHF
    4: "rlhf", 27: "rlhf", 28: "rlhf", 51: "rlhf", 57: "rlhf",
    # 4. Attention Techniques
    19: "attention", 20: "attention", 21: "attention", 22: "attention",
    33: "attention", 36: "attention", 37: "attention",
    # 5. Efficient Training
    23: "efficient", 24: "efficient",
    # 6. Scaling Laws
    17: "scaling", 18: "scaling", 34: "scaling", 40: "scaling",
    54: "scaling", 55: "scaling",
    # 7. RAG/Retrieval
    25: "rag", 26: "rag", 41: "rag", 42: "rag", 43: "rag",
    # 8. SSM
    31: "ssm", 32: "ssm",
    # 9. Vision/Multimodal
    29: "vision", 30: "vision",
    # 10. Prompting/ICL
    44: "prompting", 45: "prompting", 46: "prompting",
    47: "prompting", 48: "prompting", 49: "prompting", 56: "prompting",
    # 11. Security/Analysis
    50: "tool", 52: "security", 53: "security",
    # 12. Reasoning
    35: "reasoning",
}

# ── LLM 모델별 상세 사양 ────────────────────────────────────────────────
LLM_SPECS = {
    1: {  # Attention Is All You Need
        "name": "Transformer",
        "attention": "Multi-Head Attention",
        "pos_enc": "Sinusoidal Positional Encoding",
        "norm": "Post-LN (LayerNorm)",
        "ffn": "Position-wise FFN",
        "layers": "6 (Encoder) + 6 (Decoder)",
        "heads": "8",
        "d_model": "512",
        "params": "65M",
        "extra": "Encoder-Decoder Architecture",
    },
    2: {  # BERT
        "name": "BERT",
        "attention": "Multi-Head Self-Attention (Bidirectional)",
        "pos_enc": "Learned Position Embedding",
        "norm": "Post-LN (LayerNorm)",
        "ffn": "GELU FFN",
        "layers": "12 (Base) / 24 (Large)",
        "heads": "12 / 16",
        "d_model": "768 / 1024",
        "params": "110M / 340M",
        "extra": "Encoder-only, MLM + NSP",
    },
    3: {  # GPT-3
        "name": "GPT-3",
        "attention": "Multi-Head Attention (Causal)",
        "pos_enc": "Learned Position Embedding",
        "norm": "Pre-LN (LayerNorm)",
        "ffn": "GELU FFN",
        "layers": "96",
        "heads": "96",
        "d_model": "12288",
        "params": "175B",
        "extra": "Decoder-only, Few-Shot ICL",
    },
    5: {  # LLaMA
        "name": "LLaMA",
        "attention": "Multi-Head Attention",
        "pos_enc": "RoPE (Rotary)",
        "norm": "Pre-RMSNorm",
        "ffn": "SwiGLU FFN",
        "layers": "32 (7B) / 80 (65B)",
        "heads": "32 / 64",
        "d_model": "4096 / 8192",
        "params": "7B / 13B / 33B / 65B",
        "extra": "Decoder-only, Open Source",
    },
    6: {  # LLaMA 2
        "name": "LLaMA 2",
        "attention": "Grouped-Query Attention (GQA)",
        "pos_enc": "RoPE (Rotary)",
        "norm": "Pre-RMSNorm",
        "ffn": "SwiGLU FFN",
        "layers": "32 / 40 / 80",
        "heads": "32 / 40 / 64",
        "d_model": "4096 / 5120 / 8192",
        "params": "7B / 13B / 70B",
        "extra": "GQA (70B), RLHF Chat Models",
    },
    7: {  # Mistral 7B
        "name": "Mistral 7B",
        "attention": "Sliding Window Attention + GQA",
        "pos_enc": "RoPE (Rotary)",
        "norm": "Pre-RMSNorm",
        "ffn": "SwiGLU FFN",
        "layers": "32",
        "heads": "32 (Q) / 8 (KV)",
        "d_model": "4096",
        "params": "7.3B",
        "extra": "Rolling KV Cache, Window=4096",
    },
    8: {  # Mixtral
        "name": "Mixtral 8x7B",
        "attention": "Sliding Window Attention + GQA",
        "pos_enc": "RoPE (Rotary)",
        "norm": "Pre-RMSNorm",
        "ffn": "Sparse MoE (8 experts, top-2)",
        "layers": "32",
        "heads": "32 (Q) / 8 (KV)",
        "d_model": "4096",
        "params": "46.7B (12.9B active)",
        "extra": "MoE FFN, Token-level routing",
    },
    11: {  # Qwen2
        "name": "Qwen2",
        "attention": "Grouped-Query Attention (GQA)",
        "pos_enc": "RoPE (Rotary)",
        "norm": "Pre-RMSNorm",
        "ffn": "SwiGLU FFN",
        "layers": "24-80",
        "heads": "16-64",
        "d_model": "2048-8192",
        "params": "0.5B-72B",
        "extra": "Dual-chunk Attention, YARN",
    },
    12: {  # Qwen2.5
        "name": "Qwen2.5",
        "attention": "Grouped-Query Attention (GQA)",
        "pos_enc": "RoPE (Rotary)",
        "norm": "Pre-RMSNorm",
        "ffn": "SwiGLU FFN",
        "layers": "24-80",
        "heads": "16-64",
        "d_model": "2048-8192",
        "params": "0.5B-72B",
        "extra": "18T tokens, Improved Coding/Math",
    },
    13: {  # Yi
        "name": "Yi",
        "attention": "Grouped-Query Attention (GQA)",
        "pos_enc": "RoPE (Rotary)",
        "norm": "Pre-RMSNorm",
        "ffn": "SwiGLU FFN",
        "layers": "32 / 60",
        "heads": "32 / 64",
        "d_model": "4096 / 7168",
        "params": "6B / 34B",
        "extra": "200K context, NTKI RoPE",
    },
    14: {  # Gemma
        "name": "Gemma",
        "attention": "Multi-Query Attention (MQA) / MHA",
        "pos_enc": "RoPE (Rotary)",
        "norm": "Pre-RMSNorm",
        "ffn": "GeGLU FFN",
        "layers": "18 / 28",
        "heads": "8 / 16",
        "d_model": "2048 / 3072",
        "params": "2B / 7B",
        "extra": "Based on Gemini, Multi-Query (2B)",
    },
    15: {  # Phi-3
        "name": "Phi-3",
        "attention": "Grouped-Query Attention (GQA)",
        "pos_enc": "RoPE (Rotary, LongRoPE)",
        "norm": "Pre-RMSNorm",
        "ffn": "SwiGLU FFN",
        "layers": "32",
        "heads": "32",
        "d_model": "3072",
        "params": "3.8B",
        "extra": "High-quality data focus, 128K ctx",
    },
    16: {  # OLMo
        "name": "OLMo",
        "attention": "Multi-Head Attention",
        "pos_enc": "RoPE (Rotary)",
        "norm": "Non-parametric LN",
        "ffn": "SwiGLU FFN",
        "layers": "32",
        "heads": "32",
        "d_model": "4096",
        "params": "1B / 7B / 65B",
        "extra": "Fully Open (data+code+weights)",
    },
}


# ── SVG 헬퍼 함수 ──────────────────────────────────────────────────────

def svg_header():
    """공통 SVG 헤더 (viewBox, defs)."""
    return textwrap.dedent("""\
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1600"
         font-family="Arial, Helvetica, sans-serif">
      <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto" fill="{dark}">
          <polygon points="0 0, 10 3.5, 0 7"/>
        </marker>
        <marker id="arrowhead-blue" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto" fill="{blue}">
          <polygon points="0 0, 10 3.5, 0 7"/>
        </marker>
        <marker id="arrowhead-red" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto" fill="{red}">
          <polygon points="0 0, 10 3.5, 0 7"/>
        </marker>
      </defs>

      <!-- 배경 -->
      <rect width="1200" height="1600" fill="white"/>
    """).format(dark=DARK_TEXT, blue=BLUE, red=RED)


def svg_footer():
    """공통 SVG 푸터 (서명)."""
    return textwrap.dedent("""\
      <text x="600" y="1580" text-anchor="middle"
            font-size="14" fill="#AAA">made by dorae222</text>
    </svg>
    """)


def svg_title(title, y=60, font_size=28):
    """논문 제목 텍스트 (자동 줄바꿈)."""
    # 긴 제목은 65자 기준 줄바꿈
    lines = []
    if len(title) > 65:
        words = title.split()
        current = ""
        for w in words:
            if len(current) + len(w) + 1 > 65:
                lines.append(current.strip())
                current = w + " "
            else:
                current += w + " "
        if current.strip():
            lines.append(current.strip())
    else:
        lines = [title]

    parts = []
    for i, line in enumerate(lines):
        ly = y + i * (font_size + 6)
        parts.append(
            f'  <text x="600" y="{ly}" text-anchor="middle" '
            f'font-size="{font_size}" font-weight="bold" '
            f'fill="{DARK_TEXT}">{_escape(line)}</text>'
        )
    return "\n".join(parts), y + len(lines) * (font_size + 6)


def _escape(s):
    """XML 특수 문자 이스케이프."""
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _rect(x, y, w, h, fill, rx=12, stroke=None, stroke_dash=False):
    """둥근 사각형."""
    s = f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="2"'
        if stroke_dash:
            s += ' stroke-dasharray="8,4"'
    s += "/>"
    return s


def _text(x, y, text, size=16, fill=DARK_TEXT, anchor="middle", weight="normal"):
    """텍스트 요소."""
    return (f'  <text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}">{_escape(text)}</text>')


def _arrow(x1, y1, x2, y2, color=DARK_TEXT, dashed=False):
    """화살표 선."""
    s = (f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
         f'stroke="{color}" stroke-width="2" marker-end="url(#arrowhead)"')
    if dashed:
        s += ' stroke-dasharray="8,4"'
    s += "/>"
    return s


def _line(x1, y1, x2, y2, color=DARK_TEXT, dashed=False, width=2):
    """일반 선 (화살표 없음)."""
    s = (f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
         f'stroke="{color}" stroke-width="{width}"')
    if dashed:
        s += ' stroke-dasharray="8,4"'
    s += "/>"
    return s


def _box_with_text(x, y, w, h, bg, text, text_color=DARK_TEXT, rx=12,
                   font_size=16, font_weight="bold", stroke=None):
    """배경 박스 + 중앙 텍스트."""
    parts = [_rect(x, y, w, h, bg, rx=rx, stroke=stroke)]
    parts.append(_text(x + w // 2, y + h // 2 + font_size // 3,
                       text, size=font_size, fill=text_color, weight=font_weight))
    return "\n".join(parts)


def _labeled_box(x, y, w, h, bg, label, sublabel=None, rx=12,
                 label_size=16, sublabel_size=13, stroke=None):
    """라벨 + 서브라벨이 있는 박스."""
    parts = [_rect(x, y, w, h, bg, rx=rx, stroke=stroke)]
    if sublabel:
        parts.append(_text(x + w // 2, y + h // 2 - 2,
                           label, size=label_size, weight="bold"))
        parts.append(_text(x + w // 2, y + h // 2 + sublabel_size + 4,
                           sublabel, size=sublabel_size, fill=MID_TEXT))
    else:
        parts.append(_text(x + w // 2, y + h // 2 + label_size // 3,
                           label, size=label_size, weight="bold"))
    return "\n".join(parts)


# ── 템플릿: LLM Architecture ───────────────────────────────────────────

def generate_llm_svg(paper_id, title, specs):
    """LLM 아키텍처 (Decoder-only/Encoder-only) 다이어그램 생성."""
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)

    cy += 10

    # ── 모델 스펙 테이블 ──
    spec_y = cy
    parts.append(_rect(100, spec_y, 1000, 180, BG_LIGHT, rx=16, stroke="#DDD"))
    parts.append(_text(600, spec_y + 28, f"{specs['name']} Architecture Specifications",
                       size=18, weight="bold", fill=BLUE))

    spec_items = [
        ("Attention", specs["attention"]),
        ("Position Encoding", specs["pos_enc"]),
        ("Normalization", specs["norm"]),
        ("FFN", specs["ffn"]),
        ("Layers / Heads", f"{specs['layers']} layers, {specs['heads']} heads"),
        ("Parameters", specs["params"]),
    ]
    for i, (k, v) in enumerate(spec_items):
        row = i // 2
        col = i % 2
        sx = 140 + col * 480
        sy = spec_y + 50 + row * 38
        parts.append(_text(sx, sy, f"{k}:", size=14, fill=MID_TEXT, anchor="start", weight="bold"))
        parts.append(_text(sx + 170, sy, v, size=14, fill=DARK_TEXT, anchor="start"))

    cy = spec_y + 200

    # ── 아키텍처 다이어그램 ──
    parts.append(_text(600, cy, "Architecture Diagram", size=20, weight="bold", fill=DARK_TEXT))
    cy += 30

    # Input Embedding
    parts.append(_box_with_text(300, cy, 600, 55, BG_PURPLE, "Input Embedding", PURPLE))
    parts.append(_text(600, cy + 70, specs["pos_enc"], size=13, fill=LIGHT_TEXT))
    cy_embed = cy + 27

    cy += 85
    parts.append(_arrow(600, cy - 10, 600, cy + 5))
    cy += 10

    # Transformer Block (반복)
    block_h = 350
    parts.append(_rect(200, cy, 800, block_h, BG_BLUE, rx=16, stroke=BLUE))
    parts.append(_text(600, cy + 28, f"Transformer Block  x N  ({specs['layers']} layers)",
                       size=18, weight="bold", fill=BLUE))

    # 블록 내부: Norm → Attention → Add → Norm → FFN → Add
    iy = cy + 50

    # LayerNorm 1
    parts.append(_box_with_text(350, iy, 500, 40, BG_GREEN, specs["norm"], GREEN, rx=8))
    iy += 50
    parts.append(_arrow(600, iy - 8, 600, iy + 5))
    iy += 10

    # Attention
    parts.append(_box_with_text(350, iy, 500, 50, BG_BLUE,
                                specs["attention"], BLUE, rx=10))
    # Q K V 라벨
    parts.append(_text(430, iy + 65, "Q", size=13, fill=LIGHT_BLUE, weight="bold"))
    parts.append(_text(600, iy + 65, "K", size=13, fill=LIGHT_BLUE, weight="bold"))
    parts.append(_text(770, iy + 65, "V", size=13, fill=LIGHT_BLUE, weight="bold"))
    iy += 75
    parts.append(_arrow(600, iy - 5, 600, iy + 8))

    # Residual connection 1
    res_x = 870
    parts.append(_line(res_x, cy + 50, res_x, iy + 15, PURPLE, dashed=True))
    parts.append(_text(res_x + 15, iy - 10, "+ residual", size=11, fill=PURPLE,
                       anchor="start"))
    iy += 15

    # Add & Norm
    parts.append(_box_with_text(350, iy, 500, 35, "#E8F8E8", "Add & Normalize",
                                GREEN, rx=8, font_size=14))
    iy += 45
    parts.append(_arrow(600, iy - 8, 600, iy + 5))
    iy += 10

    # FFN
    parts.append(_box_with_text(350, iy, 500, 50, BG_ORANGE, specs["ffn"], ORANGE, rx=10))
    iy += 60
    parts.append(_arrow(600, iy - 8, 600, iy + 5))

    # Residual connection 2
    parts.append(_line(res_x, iy - 60, res_x, iy + 12, ORANGE, dashed=True))
    parts.append(_text(res_x + 15, iy, "+ residual", size=11, fill=ORANGE, anchor="start"))
    iy += 10

    # Add & Norm
    parts.append(_box_with_text(350, iy, 500, 35, "#E8F8E8", "Add & Normalize",
                                GREEN, rx=8, font_size=14))

    cy += block_h + 15
    parts.append(_arrow(600, cy, 600, cy + 15))
    cy += 20

    # Output Head
    if paper_id == 2:  # BERT
        parts.append(_box_with_text(300, cy, 600, 55, BG_RED,
                                    "[CLS] Output / Token Predictions", RED))
    elif paper_id == 1:  # Transformer
        parts.append(_box_with_text(300, cy, 600, 55, BG_RED,
                                    "Linear + Softmax Output", RED))
    else:
        parts.append(_box_with_text(300, cy, 600, 55, BG_RED,
                                    "LM Head (Linear + Softmax)", RED))
    cy += 70

    # Extra note
    if specs.get("extra"):
        parts.append(_rect(200, cy, 800, 50, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 30, specs["extra"], size=15, weight="bold", fill=YELLOW))
        cy += 65

    # ── Key Features 요약 ──
    cy += 10
    parts.append(_text(600, cy, "Key Design Choices", size=20, weight="bold", fill=DARK_TEXT))
    cy += 10

    features = [
        (PURPLE, "Embedding", specs["pos_enc"]),
        (BLUE, "Attention", specs["attention"]),
        (ORANGE, "FFN", specs["ffn"]),
        (GREEN, "Normalization", specs["norm"]),
        (RED, "Scale", f"d_model={specs['d_model']}, {specs['params']} params"),
    ]
    for color, label, desc in features:
        cy += 35
        parts.append(_rect(200, cy - 20, 20, 20, color, rx=4))
        parts.append(_text(235, cy - 2, f"{label}:", size=14, fill=DARK_TEXT,
                           anchor="start", weight="bold"))
        parts.append(_text(370, cy - 2, desc, size=14, fill=MID_TEXT, anchor="start"))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: MoE ────────────────────────────────────────────────────────

MOE_SPECS = {
    8: {"name": "Mixtral 8x7B", "experts": "8", "topk": "2",
        "router": "Token-level Linear Router",
        "expert_type": "SwiGLU FFN (7B each)", "active": "12.9B of 46.7B",
        "extra": "Sliding Window Attention + GQA, Router load balancing"},
    9: {"name": "DeepSeek-V2", "experts": "160", "topk": "6",
        "router": "Device-limited Expert Routing",
        "expert_type": "Fine-grained Expert FFN",
        "active": "21B of 236B",
        "extra": "MLA (Multi-head Latent Attention), DeepSeekMoE"},
    10: {"name": "DeepSeek-V3", "experts": "256", "topk": "8",
         "router": "Auxiliary-loss-free Load Balancing",
         "expert_type": "Fine-grained Expert FFN + 1 Shared",
         "active": "37B of 671B",
         "extra": "Multi-Token Prediction, FP8 Training"},
    38: {"name": "Switch Transformer", "experts": "Up to 2048", "topk": "1",
         "router": "Simplified Top-1 Router",
         "expert_type": "Standard FFN per Expert",
         "active": "~1 Expert active",
         "extra": "Simplified MoE, Capacity Factor, 1.6T params"},
    39: {"name": "Sparse Expert Models (Survey)", "experts": "N (variable)", "topk": "K",
         "router": "Various Routing Strategies",
         "expert_type": "FFN Experts (Various)",
         "active": "Top-K of N",
         "extra": "Comprehensive survey of MoE approaches"},
}


def generate_moe_svg(paper_id, title):
    """MoE 아키텍처 다이어그램 생성."""
    specs = MOE_SPECS.get(paper_id, MOE_SPECS[38])
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 15

    # Spec box
    parts.append(_rect(100, cy, 1000, 140, BG_LIGHT, rx=16, stroke="#DDD"))
    parts.append(_text(600, cy + 28, f"{specs['name']} - Mixture of Experts",
                       size=18, weight="bold", fill=BLUE))
    spec_items = [
        ("Experts", specs["experts"]),
        ("Top-K", specs["topk"]),
        ("Router", specs["router"]),
        ("Active Params", specs["active"]),
    ]
    for i, (k, v) in enumerate(spec_items):
        row = i // 2
        col = i % 2
        sx = 150 + col * 460
        sy = cy + 55 + row * 35
        parts.append(_text(sx, sy, f"{k}:", size=14, fill=MID_TEXT, anchor="start", weight="bold"))
        parts.append(_text(sx + 140, sy, v, size=14, fill=DARK_TEXT, anchor="start"))
    cy += 160

    # Architecture flow
    parts.append(_text(600, cy, "MoE Architecture Flow", size=20, weight="bold"))
    cy += 30

    # Input
    parts.append(_box_with_text(350, cy, 500, 50, BG_PURPLE, "Input Tokens", PURPLE))
    cy += 60
    parts.append(_arrow(600, cy, 600, cy + 15))
    cy += 20

    # Self-Attention
    parts.append(_box_with_text(350, cy, 500, 50, BG_BLUE, "Self-Attention Layer", BLUE))
    cy += 60
    parts.append(_arrow(600, cy, 600, cy + 15))
    cy += 20

    # Router
    parts.append(_rect(300, cy, 600, 70, BG_YELLOW, rx=14, stroke=YELLOW))
    parts.append(_text(600, cy + 28, "Router / Gating Network", size=18,
                       weight="bold", fill=YELLOW))
    parts.append(_text(600, cy + 50, specs["router"], size=13, fill=MID_TEXT))
    router_bottom = cy + 70

    cy = router_bottom + 15

    # Expert selection arrows
    n_show = min(int(specs["experts"]) if specs["experts"].isdigit() else 4, 6)
    expert_w = 140
    total_w = n_show * expert_w + (n_show - 1) * 20
    start_x = 600 - total_w // 2

    for i in range(n_show):
        ex = start_x + i * (expert_w + 20)
        # Arrow from router
        ax = ex + expert_w // 2
        parts.append(_arrow(ax, router_bottom + 2, ax, cy + 5))
        # Expert box
        is_active = i < int(specs["topk"]) if specs["topk"].isdigit() else i < 2
        bg = BG_ORANGE if is_active else "#F0F0F0"
        border = ORANGE if is_active else "#CCC"
        parts.append(_rect(ex, cy + 8, expert_w, 70, bg, rx=10, stroke=border))
        parts.append(_text(ex + expert_w // 2, cy + 35, f"Expert {i+1}",
                           size=14, weight="bold", fill=ORANGE if is_active else "#AAA"))
        parts.append(_text(ex + expert_w // 2, cy + 55, "FFN",
                           size=12, fill=MID_TEXT if is_active else "#CCC"))

    if not specs["experts"].isdigit() or int(specs["experts"]) > n_show:
        parts.append(_text(start_x + total_w + 30, cy + 45, "...",
                           size=24, fill=MID_TEXT, weight="bold"))

    # Top-K label
    parts.append(_rect(start_x - 10, cy + 85, total_w + 20, 28, "none", rx=6,
                       stroke=ORANGE, stroke_dash=True))
    parts.append(_text(600, cy + 105, f"Top-{specs['topk']} Selection (active)",
                       size=13, fill=ORANGE, weight="bold"))

    cy += 125
    # Weighted Sum
    parts.append(_arrow(600, cy, 600, cy + 18))
    cy += 22
    parts.append(_box_with_text(350, cy, 500, 50, BG_GREEN,
                                "Weighted Sum of Expert Outputs", GREEN))
    cy += 60
    parts.append(_arrow(600, cy, 600, cy + 18))
    cy += 22

    # Output
    parts.append(_box_with_text(350, cy, 500, 50, BG_RED, "Output", RED))
    cy += 70

    # Extra
    if specs.get("extra"):
        parts.append(_rect(150, cy, 900, 50, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 30, specs["extra"], size=14, weight="bold", fill=YELLOW))
        cy += 65

    # Key concepts
    cy += 10
    parts.append(_text(600, cy, "Key Concepts", size=20, weight="bold"))
    cy += 10
    concepts = [
        (YELLOW, "Router", "Determines which experts process each token"),
        (ORANGE, "Experts", specs["expert_type"]),
        (GREEN, "Output", f"Weighted combination of top-{specs['topk']} expert outputs"),
        (BLUE, "Efficiency", f"Only {specs['active']} parameters active per token"),
    ]
    for color, label, desc in concepts:
        cy += 35
        parts.append(_rect(200, cy - 20, 20, 20, color, rx=4))
        parts.append(_text(235, cy - 2, f"{label}:", size=14, anchor="start", weight="bold"))
        parts.append(_text(370, cy - 2, desc, size=14, fill=MID_TEXT, anchor="start"))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: RLHF / Alignment ──────────────────────────────────────────

RLHF_SPECS = {
    4: {"name": "InstructGPT",
        "stages": ["SFT on Demonstrations", "Reward Model Training", "PPO Optimization"],
        "details": [
            "Fine-tune GPT-3 on human demonstrations",
            "Train RM on human preference comparisons",
            "Optimize policy with PPO against RM",
        ],
        "extra": "RLHF pipeline: 1.3B outperforms 175B GPT-3"},
    27: {"name": "Constitutional AI (CAI)",
         "stages": ["SL-CAI: Supervised Stage", "RL-CAI: RL Stage", "Constitutional Principles"],
         "details": [
             "AI critiques + revises own outputs using principles",
             "RLAIF: AI-generated preference labels for RM",
             "Set of rules defining harmless behavior",
         ],
         "extra": "Harmlessness from AI Feedback, no human harm labels needed"},
    28: {"name": "DPO (Direct Preference Optimization)",
         "stages": ["Preference Data Collection", "DPO Training", "Direct Policy Optimization"],
         "details": [
             "Pairs of (chosen, rejected) responses",
             "Implicit reward via Bradley-Terry model",
             "No separate reward model needed",
         ],
         "extra": "Loss: -log sigma(beta * (log pi(yw|x) - log pi(yl|x) - log pi_ref))"},
    51: {"name": "Self-Rewarding LM",
         "stages": ["Initial SFT Model", "Self-Instruction Creation", "Self-Reward + DPO"],
         "details": [
             "Fine-tune base model with seed data",
             "Model generates new instruction-response pairs",
             "Model scores own outputs, trains via DPO iteratively",
         ],
         "extra": "Iterative self-improvement without human feedback"},
    57: {"name": "Training Helpful & Harmless",
         "stages": ["Helpful RLHF", "Harmless RLHF", "Combined Optimization"],
         "details": [
             "Train on helpfulness preference data",
             "Train on harmlessness (red-teaming) data",
             "Balance helpfulness vs. harmlessness tension",
         ],
         "extra": "Anthropic: tension between helpfulness and harmlessness"},
}


def generate_rlhf_svg(paper_id, title):
    """RLHF / Alignment 파이프라인 다이어그램 생성."""
    specs = RLHF_SPECS.get(paper_id, RLHF_SPECS[4])
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 15

    parts.append(_text(600, cy, f"{specs['name']} Pipeline",
                       size=20, weight="bold", fill=BLUE))
    cy += 35

    # Stage boxes
    stage_colors = [
        (BG_BLUE, BLUE),
        (BG_ORANGE, ORANGE),
        (BG_GREEN, GREEN),
    ]

    for i, (stage, detail) in enumerate(zip(specs["stages"], specs["details"])):
        bg, color = stage_colors[i % len(stage_colors)]

        # Stage number circle
        parts.append(f'  <circle cx="230" cy="{cy + 55}" r="25" fill="{color}"/>')
        parts.append(_text(230, cy + 62, str(i + 1), size=22, fill="white", weight="bold"))

        # Stage box
        parts.append(_rect(270, cy + 10, 780, 90, bg, rx=14, stroke=color))
        parts.append(_text(660, cy + 45, stage, size=18, weight="bold", fill=color))
        parts.append(_text(660, cy + 70, detail, size=13, fill=MID_TEXT))

        cy += 110

        # Arrow between stages
        if i < len(specs["stages"]) - 1:
            parts.append(_arrow(600, cy, 600, cy + 18))
            cy += 22

    cy += 20

    # Visual detail section
    if paper_id == 28:  # DPO
        parts.append(_text(600, cy, "DPO vs RLHF Comparison", size=20, weight="bold"))
        cy += 30
        # RLHF path
        parts.append(_rect(100, cy, 480, 200, BG_ORANGE, rx=14, stroke=ORANGE))
        parts.append(_text(340, cy + 28, "Traditional RLHF", size=16, weight="bold", fill=ORANGE))
        rlhf_steps = ["1. Collect preferences", "2. Train Reward Model",
                      "3. Run PPO against RM", "4. Complex, unstable"]
        for j, step in enumerate(rlhf_steps):
            parts.append(_text(340, cy + 60 + j * 35, step, size=14, fill=MID_TEXT))

        # DPO path
        parts.append(_rect(620, cy, 480, 200, BG_GREEN, rx=14, stroke=GREEN))
        parts.append(_text(860, cy + 28, "Direct Preference Optimization",
                           size=16, weight="bold", fill=GREEN))
        dpo_steps = ["1. Collect preferences", "2. Direct policy optimization",
                     "3. No separate RM needed", "4. Simple, stable training"]
        for j, step in enumerate(dpo_steps):
            parts.append(_text(860, cy + 60 + j * 35, step, size=14, fill=MID_TEXT))
        cy += 220

    elif paper_id == 4:  # InstructGPT
        parts.append(_text(600, cy, "RLHF Training Flow", size=20, weight="bold"))
        cy += 30
        flow_items = [
            ("Human\nDemonstrations", BG_PURPLE, PURPLE),
            ("SFT Model", BG_BLUE, BLUE),
            ("Human\nPreferences", BG_YELLOW, YELLOW),
            ("Reward\nModel", BG_ORANGE, ORANGE),
            ("PPO\nOptimization", BG_GREEN, GREEN),
            ("Final\nPolicy", BG_RED, RED),
        ]
        fw = 150
        fx = 100
        for j, (label, bg, color) in enumerate(flow_items):
            parts.append(_rect(fx, cy, fw, 70, bg, rx=10, stroke=color))
            lines = label.split("\n")
            for li, ln in enumerate(lines):
                parts.append(_text(fx + fw // 2, cy + 30 + li * 20, ln,
                                   size=13, weight="bold", fill=color))
            if j < len(flow_items) - 1:
                parts.append(_arrow(fx + fw + 3, cy + 35, fx + fw + 22, cy + 35))
            fx += fw + 25
        cy += 100

    elif paper_id == 27:  # CAI
        parts.append(_text(600, cy, "Constitutional AI Process", size=20, weight="bold"))
        cy += 30
        parts.append(_rect(150, cy, 900, 160, BG_LIGHT, rx=14, stroke="#DDD"))
        cai_flow = [
            ("Generate", "Model produces response"),
            ("Critique", "Model critiques using principles"),
            ("Revise", "Model revises based on critique"),
            ("RLAIF", "AI labels preferences for RM"),
        ]
        fx = 180
        for j, (label, desc) in enumerate(cai_flow):
            parts.append(_rect(fx, cy + 20, 180, 60, BG_BLUE if j < 3 else BG_GREEN,
                               rx=10))
            parts.append(_text(fx + 90, cy + 48, label, size=14, weight="bold", fill=BLUE))
            parts.append(_text(fx + 90, cy + 100, desc, size=11, fill=MID_TEXT))
            if j < len(cai_flow) - 1:
                parts.append(_arrow(fx + 183, cy + 50, fx + 208, cy + 50))
            fx += 210
        cy += 180

    else:
        cy += 10

    # Extra
    cy += 15
    if specs.get("extra"):
        parts.append(_rect(150, cy, 900, 50, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 30, specs["extra"], size=14, weight="bold", fill=YELLOW))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: Attention Techniques ───────────────────────────────────────

def generate_attention_svg(paper_id, title):
    """Attention 기법 다이어그램 생성."""
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 20

    if paper_id == 19:  # RoPE
        parts.append(_text(600, cy, "Rotary Position Embedding (RoPE)", size=20,
                           weight="bold", fill=BLUE))
        cy += 35

        parts.append(_rect(100, cy, 1000, 130, BG_LIGHT, rx=16, stroke="#DDD"))
        parts.append(_text(600, cy + 25, "Core Idea: Encode position through rotation of query/key vectors",
                           size=15, fill=MID_TEXT))
        parts.append(_text(600, cy + 55, "f(q, m) . f(k, n) = g(q, k, m-n)",
                           size=18, weight="bold", fill=PURPLE))
        parts.append(_text(600, cy + 80, "Relative position encoded via rotation matrix multiplication",
                           size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 105, "Naturally decays with relative distance, extends to any sequence length",
                           size=13, fill=LIGHT_TEXT))
        cy += 150

        # Rotation diagram
        parts.append(_text(600, cy, "2D Rotation Visualization", size=18, weight="bold"))
        cy += 25

        # Query vector rotation
        parts.append(_rect(150, cy, 400, 250, BG_PURPLE, rx=14))
        parts.append(_text(350, cy + 25, "Query at position m", size=16, weight="bold", fill=PURPLE))
        parts.append(f'  <circle cx="350" cy="{cy + 140}" r="80" fill="none" stroke="{PURPLE}" stroke-width="2" stroke-dasharray="5,3"/>')
        parts.append(_arrow(350, cy + 140, 410, cy + 90, PURPLE))
        parts.append(_text(420, cy + 85, "q_m", size=14, fill=PURPLE, weight="bold"))
        parts.append(_text(350, cy + 235, "Rotate by m*theta", size=13, fill=MID_TEXT))

        # Key vector rotation
        parts.append(_rect(650, cy, 400, 250, BG_BLUE, rx=14))
        parts.append(_text(850, cy + 25, "Key at position n", size=16, weight="bold", fill=BLUE))
        parts.append(f'  <circle cx="850" cy="{cy + 140}" r="80" fill="none" stroke="{BLUE}" stroke-width="2" stroke-dasharray="5,3"/>')
        parts.append(_arrow(850, cy + 140, 910, cy + 100, BLUE))
        parts.append(_text(920, cy + 95, "k_n", size=14, fill=BLUE, weight="bold"))
        parts.append(_text(850, cy + 235, "Rotate by n*theta", size=13, fill=MID_TEXT))

        cy += 270
        parts.append(_arrow(600, cy, 600, cy + 20))
        cy += 25
        parts.append(_box_with_text(250, cy, 700, 55, BG_GREEN,
                                    "Dot product depends only on (m - n)", GREEN))
        cy += 75

        # Properties
        parts.append(_text(600, cy, "RoPE Properties", size=18, weight="bold"))
        cy += 10
        props = [
            (PURPLE, "Relative", "Position info encoded as relative distance"),
            (BLUE, "Flexible", "No maximum sequence length limitation"),
            (GREEN, "Efficient", "Can be computed as element-wise multiplication"),
            (ORANGE, "Compatible", "Works with linear attention mechanisms"),
        ]
        for color, label, desc in props:
            cy += 35
            parts.append(_rect(200, cy - 20, 20, 20, color, rx=4))
            parts.append(_text(235, cy - 2, f"{label}:", size=14, anchor="start", weight="bold"))
            parts.append(_text(380, cy - 2, desc, size=14, fill=MID_TEXT, anchor="start"))

    elif paper_id == 20:  # GQA
        parts.append(_text(600, cy, "Grouped-Query Attention (GQA)", size=20,
                           weight="bold", fill=BLUE))
        cy += 35

        # Three attention types comparison
        types = [
            ("Multi-Head\nAttention (MHA)", "H heads Q\nH heads K\nH heads V",
             BG_BLUE, BLUE, 4, 4),
            ("Multi-Query\nAttention (MQA)", "H heads Q\n1 head K\n1 head V",
             BG_ORANGE, ORANGE, 4, 1),
            ("Grouped-Query\nAttention (GQA)", "H heads Q\nG groups K\nG groups V",
             BG_GREEN, GREEN, 4, 2),
        ]

        bw = 320
        bx = 80
        for (name, desc, bg, color, n_q, n_kv) in types:
            parts.append(_rect(bx, cy, bw, 350, bg, rx=14, stroke=color))
            name_lines = name.split("\n")
            for li, ln in enumerate(name_lines):
                parts.append(_text(bx + bw // 2, cy + 25 + li * 22, ln,
                                   size=16, weight="bold", fill=color))

            # Draw Q heads
            qy = cy + 75
            head_w = 50
            head_gap = 10
            total_qw = n_q * head_w + (n_q - 1) * head_gap
            qx_start = bx + (bw - total_qw) // 2
            parts.append(_text(bx + 30, qy + 15, "Q:", size=13, fill=MID_TEXT,
                               anchor="start", weight="bold"))
            for hi in range(n_q):
                hx = qx_start + hi * (head_w + head_gap)
                parts.append(_rect(hx, qy, head_w, 30, LIGHT_BLUE, rx=6))

            # Draw KV heads
            kvy = cy + 150
            total_kvw = n_kv * head_w + (n_kv - 1) * head_gap
            kvx_start = bx + (bw - total_kvw) // 2
            parts.append(_text(bx + 30, kvy + 15, "KV:", size=13, fill=MID_TEXT,
                               anchor="start", weight="bold"))
            for hi in range(n_kv):
                hx = kvx_start + hi * (head_w + head_gap)
                parts.append(_rect(hx, kvy, head_w, 30, ORANGE, rx=6))

            # Draw connections
            for qi in range(n_q):
                qhx = qx_start + qi * (head_w + head_gap) + head_w // 2
                kvi = qi * n_kv // n_q
                kvhx = kvx_start + kvi * (head_w + head_gap) + head_w // 2
                parts.append(_line(qhx, qy + 30, kvhx, kvy, color, dashed=True, width=1))

            # Description
            desc_lines = desc.split("\n")
            for li, ln in enumerate(desc_lines):
                parts.append(_text(bx + bw // 2, cy + 240 + li * 22, ln,
                                   size=13, fill=MID_TEXT))

            # Memory label
            mem = "Baseline" if n_kv == n_q else f"KV Cache: {n_kv}/{n_q}x"
            parts.append(_text(bx + bw // 2, cy + 320, mem,
                               size=14, weight="bold", fill=color))

            bx += bw + 30

        cy += 380

        # Summary
        parts.append(_rect(150, cy, 900, 55, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 22, "GQA: Best trade-off between quality (MHA) and speed (MQA)",
                           size=15, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 44, "Groups of Q heads share K/V heads, reducing KV cache by G factor",
                           size=13, fill=MID_TEXT))

    elif paper_id in (21, 22):  # FlashAttention
        version = "2" if paper_id == 22 else ""
        parts.append(_text(600, cy, f"FlashAttention{'-2' if version else ''}: IO-Aware Exact Attention",
                           size=20, weight="bold", fill=BLUE))
        cy += 35

        # Problem
        parts.append(_rect(100, cy, 1000, 80, BG_RED, rx=14, stroke=RED))
        parts.append(_text(600, cy + 25, "Problem: Standard Attention is Memory-Bound",
                           size=16, weight="bold", fill=RED))
        parts.append(_text(600, cy + 55, "O(N^2) memory for attention matrix, slow HBM reads/writes",
                           size=14, fill=MID_TEXT))
        cy += 100

        # Solution: Tiling
        parts.append(_text(600, cy, "Solution: Tiling + Online Softmax", size=18, weight="bold"))
        cy += 30

        # Memory hierarchy
        parts.append(_rect(100, cy, 450, 300, BG_ORANGE, rx=14, stroke=ORANGE))
        parts.append(_text(325, cy + 25, "Standard Attention", size=16, weight="bold", fill=ORANGE))
        # Show HBM reads
        std_steps = [
            "1. Load Q, K from HBM",
            "2. Compute S = QK^T in HBM",
            "3. Write S to HBM (N x N)",
            "4. Load S, compute softmax",
            "5. Write P to HBM (N x N)",
            "6. Load P, V, compute O",
            "7. Write O to HBM",
        ]
        for j, step in enumerate(std_steps):
            parts.append(_text(130, cy + 60 + j * 32, step, size=13, fill=MID_TEXT, anchor="start"))
        parts.append(_text(325, cy + 280, "HBM Access: O(N^2)", size=14, weight="bold", fill=RED))

        parts.append(_rect(650, cy, 450, 300, BG_GREEN, rx=14, stroke=GREEN))
        parts.append(_text(875, cy + 25, f"FlashAttention{'-2' if version else ''} (Tiled)",
                           size=16, weight="bold", fill=GREEN))
        flash_steps = [
            "1. Divide Q, K, V into blocks",
            "2. Load blocks to SRAM",
            "3. Compute block attention in SRAM",
            "4. Online softmax (running max)",
            "5. Accumulate output incrementally",
            "6. Write final O to HBM",
            "7. No N x N matrix materialized!",
        ]
        for j, step in enumerate(flash_steps):
            parts.append(_text(680, cy + 60 + j * 32, step, size=13, fill=MID_TEXT, anchor="start"))
        parts.append(_text(875, cy + 280, "HBM Access: O(N^2 d / M)",
                           size=14, weight="bold", fill=GREEN))
        cy += 320

        if paper_id == 22:
            cy += 15
            parts.append(_rect(150, cy, 900, 55, BG_YELLOW, rx=12, stroke=YELLOW))
            parts.append(_text(600, cy + 22, "FlashAttention-2 Improvements",
                               size=15, weight="bold", fill=YELLOW))
            parts.append(_text(600, cy + 44,
                               "Better work partitioning, fewer non-matmul FLOPs, ~2x speedup",
                               size=13, fill=MID_TEXT))
            cy += 65

        # Memory hierarchy diagram
        cy += 15
        parts.append(_text(600, cy, "GPU Memory Hierarchy", size=18, weight="bold"))
        cy += 25
        # SRAM (fast, small)
        parts.append(_rect(350, cy, 500, 50, BG_GREEN, rx=10, stroke=GREEN))
        parts.append(_text(600, cy + 20, "SRAM (On-chip)", size=14, weight="bold", fill=GREEN))
        parts.append(_text(600, cy + 40, "~20 MB, ~19 TB/s", size=12, fill=MID_TEXT))
        cy += 60
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20
        # HBM (slow, large)
        parts.append(_rect(300, cy, 600, 50, BG_ORANGE, rx=10, stroke=ORANGE))
        parts.append(_text(600, cy + 20, "HBM (High Bandwidth Memory)", size=14,
                           weight="bold", fill=ORANGE))
        parts.append(_text(600, cy + 40, "~40-80 GB, ~1.5-3 TB/s", size=12, fill=MID_TEXT))

    elif paper_id == 33:  # Layer Norm
        parts.append(_text(600, cy, "Layer Normalization in Transformers", size=20,
                           weight="bold", fill=BLUE))
        cy += 35

        # Pre-LN vs Post-LN comparison
        configs = [
            ("Post-LN (Original)", [
                ("Attention", BG_BLUE, BLUE),
                ("Add", BG_GREEN, GREEN),
                ("LayerNorm", BG_GREEN, GREEN),
                ("FFN", BG_ORANGE, ORANGE),
                ("Add", BG_GREEN, GREEN),
                ("LayerNorm", BG_GREEN, GREEN),
            ]),
            ("Pre-LN (Improved)", [
                ("LayerNorm", BG_GREEN, GREEN),
                ("Attention", BG_BLUE, BLUE),
                ("Add", BG_GREEN, GREEN),
                ("LayerNorm", BG_GREEN, GREEN),
                ("FFN", BG_ORANGE, ORANGE),
                ("Add", BG_GREEN, GREEN),
            ]),
        ]
        for ci, (cname, layers) in enumerate(configs):
            cx = 180 + ci * 480
            parts.append(_rect(cx, cy, 400, 500, BG_LIGHT, rx=16, stroke="#DDD"))
            parts.append(_text(cx + 200, cy + 28, cname, size=18, weight="bold",
                               fill=BLUE if ci == 0 else GREEN))
            ly = cy + 55
            for lname, bg, color in layers:
                parts.append(_box_with_text(cx + 40, ly, 320, 40, bg, lname, color,
                                            rx=8, font_size=14))
                ly += 50
                if ly < cy + 490:
                    parts.append(_arrow(cx + 200, ly - 8, cx + 200, ly + 5))
                    ly += 8

            # Residual lines
            parts.append(_line(cx + 380, cy + 60, cx + 380, ly - 50, PURPLE, dashed=True))
            parts.append(_text(cx + 385, cy + 160, "residual", size=11, fill=PURPLE,
                               anchor="start"))

        cy += 530

        parts.append(_rect(150, cy, 900, 80, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 25, "Key Finding", size=16, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 50, "Pre-LN enables stable training without warmup,",
                           size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 70, "Post-LN may achieve better final performance with careful tuning",
                           size=13, fill=LIGHT_TEXT))

    elif paper_id == 36:  # Speculative Decoding
        parts.append(_text(600, cy, "Speculative Decoding", size=20, weight="bold", fill=BLUE))
        cy += 35

        # Standard vs Speculative
        parts.append(_rect(100, cy, 480, 280, BG_ORANGE, rx=14, stroke=ORANGE))
        parts.append(_text(340, cy + 25, "Standard Autoregressive", size=16,
                           weight="bold", fill=ORANGE))
        ty = cy + 55
        for i in range(5):
            parts.append(_box_with_text(180, ty, 320, 35, "#FFF5EC",
                                        f"Token {i+1}: Full model forward pass",
                                        ORANGE, rx=6, font_size=12))
            ty += 42
        parts.append(_text(340, cy + 265, "5 sequential forward passes", size=13,
                           fill=RED, weight="bold"))

        parts.append(_rect(620, cy, 480, 280, BG_GREEN, rx=14, stroke=GREEN))
        parts.append(_text(860, cy + 25, "Speculative Decoding", size=16,
                           weight="bold", fill=GREEN))
        # Draft model
        parts.append(_rect(680, cy + 50, 360, 70, BG_BLUE, rx=10, stroke=BLUE))
        parts.append(_text(860, cy + 75, "Draft Model (small, fast)", size=14,
                           weight="bold", fill=BLUE))
        parts.append(_text(860, cy + 95, "Generate K draft tokens", size=12, fill=MID_TEXT))
        parts.append(_arrow(860, cy + 125, 860, cy + 145))
        # Verification
        parts.append(_rect(680, cy + 148, 360, 70, BG_ORANGE, rx=10, stroke=ORANGE))
        parts.append(_text(860, cy + 173, "Target Model (large)", size=14,
                           weight="bold", fill=ORANGE))
        parts.append(_text(860, cy + 193, "Verify all K tokens in parallel", size=12, fill=MID_TEXT))
        parts.append(_text(860, cy + 265, "1 + 1 forward passes for K tokens!",
                           size=13, fill=GREEN, weight="bold"))
        cy += 300

        # Acceptance criterion
        cy += 15
        parts.append(_rect(150, cy, 900, 70, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 22, "Acceptance: Modified Rejection Sampling",
                           size=16, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 48, "Accept draft token with prob min(1, p_target/p_draft)",
                           size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 65, "Guarantees identical output distribution to target model",
                           size=12, fill=LIGHT_TEXT))

    elif paper_id == 37:  # PagedAttention
        parts.append(_text(600, cy, "PagedAttention / vLLM", size=20, weight="bold", fill=BLUE))
        cy += 35

        # Problem: KV Cache fragmentation
        parts.append(_rect(100, cy, 1000, 80, BG_RED, rx=14, stroke=RED))
        parts.append(_text(600, cy + 25, "Problem: KV Cache Memory Fragmentation",
                           size=16, weight="bold", fill=RED))
        parts.append(_text(600, cy + 55, "Contiguous allocation wastes memory, limits batch size and throughput",
                           size=14, fill=MID_TEXT))
        cy += 100

        # Solution: Paging
        parts.append(_text(600, cy, "Solution: Virtual Memory Paging for KV Cache",
                           size=18, weight="bold"))
        cy += 30

        # Page table diagram
        parts.append(_rect(100, cy, 450, 280, BG_ORANGE, rx=14, stroke=ORANGE))
        parts.append(_text(325, cy + 25, "Contiguous (Traditional)", size=16,
                           weight="bold", fill=ORANGE))
        # Show wasted memory blocks
        by = cy + 55
        block_colors = [BLUE, BLUE, BLUE, "#DDD", "#DDD", ORANGE, ORANGE, "#DDD"]
        labels = ["Seq 1", "Seq 1", "Seq 1", "Waste", "Waste", "Seq 2", "Seq 2", "Waste"]
        for j in range(8):
            bx = 130 + (j % 4) * 90
            bby = by + (j // 4) * 70
            parts.append(_rect(bx, bby, 80, 55, block_colors[j], rx=4))
            parts.append(_text(bx + 40, bby + 32, labels[j], size=11, fill="white"
                               if block_colors[j] != "#DDD" else MID_TEXT, weight="bold"))
        parts.append(_text(325, cy + 255, "Internal + external fragmentation",
                           size=13, fill=RED, weight="bold"))

        parts.append(_rect(650, cy, 450, 280, BG_GREEN, rx=14, stroke=GREEN))
        parts.append(_text(875, cy + 25, "PagedAttention", size=16, weight="bold", fill=GREEN))
        by = cy + 55
        block_colors2 = [BLUE, ORANGE, BLUE, GREEN, BLUE, ORANGE, GREEN, GREEN]
        labels2 = ["Seq 1", "Seq 2", "Seq 1", "Seq 3", "Seq 1", "Seq 2", "Seq 3", "Seq 3"]
        for j in range(8):
            bx = 680 + (j % 4) * 90
            bby = by + (j // 4) * 70
            parts.append(_rect(bx, bby, 80, 55, block_colors2[j], rx=4))
            parts.append(_text(bx + 40, bby + 32, labels2[j], size=11, fill="white",
                               weight="bold"))
        parts.append(_text(875, cy + 255, "Non-contiguous, no fragmentation",
                           size=13, fill=GREEN, weight="bold"))
        cy += 300

        parts.append(_rect(150, cy, 900, 55, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 22, "Result: Near-zero waste, 2-4x throughput improvement",
                           size=15, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 44, "Block table maps logical KV positions to physical GPU memory blocks",
                           size=13, fill=MID_TEXT))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: Efficient Training (LoRA/QLoRA) ────────────────────────────

def generate_efficient_svg(paper_id, title):
    """LoRA / QLoRA 다이어그램 생성."""
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 20

    is_qlora = paper_id == 24

    parts.append(_text(600, cy, f"{'QLoRA' if is_qlora else 'LoRA'}: Low-Rank Adaptation",
                       size=20, weight="bold", fill=BLUE))
    cy += 40

    # Core idea
    parts.append(_rect(100, cy, 1000, 80, BG_LIGHT, rx=16, stroke="#DDD"))
    parts.append(_text(600, cy + 25, "Core Idea: W = W_0 + Delta_W = W_0 + B * A",
                       size=18, weight="bold", fill=PURPLE))
    parts.append(_text(600, cy + 55, "Freeze original weights W_0, only train low-rank matrices B and A",
                       size=14, fill=MID_TEXT))
    cy += 100

    # Architecture diagram
    # Frozen weight path
    parts.append(_rect(100, cy, 450, 400, BG_BLUE, rx=16, stroke=BLUE))
    parts.append(_text(325, cy + 30, "Frozen Pretrained Weights",
                       size=18, weight="bold", fill=BLUE))

    # W_0 matrix
    parts.append(_rect(175, cy + 60, 300, 120, "#D6E9F8", rx=10, stroke=BLUE))
    parts.append(_text(325, cy + 110, "W_0", size=28, weight="bold", fill=BLUE))
    parts.append(_text(325, cy + 140, f"d x d {'(NF4 Quantized)' if is_qlora else '(frozen)'}",
                       size=13, fill=MID_TEXT))

    # Input arrow
    parts.append(_box_with_text(200, cy + 220, 250, 45, BG_PURPLE, "h = W_0 * x", PURPLE))
    parts.append(_arrow(325, cy + 180, 325, cy + 218))

    parts.append(_text(325, cy + 310, "No gradient updates",
                       size=14, fill=BLUE, weight="bold"))
    if is_qlora:
        parts.append(_text(325, cy + 340, "4-bit NormalFloat (NF4)",
                           size=13, fill=MID_TEXT))
        parts.append(_text(325, cy + 365, "Double Quantization", size=13, fill=MID_TEXT))

    # LoRA adapter path
    parts.append(_rect(650, cy, 450, 400, BG_ORANGE, rx=16, stroke=ORANGE))
    parts.append(_text(875, cy + 30, "LoRA Adapter (Trainable)",
                       size=18, weight="bold", fill=ORANGE))

    # A matrix (down-projection)
    parts.append(_rect(720, cy + 60, 120, 80, "#FDE8D0", rx=8, stroke=ORANGE))
    parts.append(_text(780, cy + 95, "A", size=22, weight="bold", fill=ORANGE))
    parts.append(_text(780, cy + 125, "d x r", size=12, fill=MID_TEXT))

    # r label
    parts.append(_text(875, cy + 105, "rank r", size=16, weight="bold", fill=RED))
    parts.append(_text(875, cy + 125, "(e.g., 4-64)", size=12, fill=LIGHT_TEXT))

    # B matrix (up-projection)
    parts.append(_rect(960, cy + 60, 120, 80, "#FDE8D0", rx=8, stroke=ORANGE))
    parts.append(_text(1020, cy + 95, "B", size=22, weight="bold", fill=ORANGE))
    parts.append(_text(1020, cy + 125, "r x d", size=12, fill=MID_TEXT))

    # Arrow from A to B
    parts.append(_arrow(842, cy + 100, 958, cy + 100))

    # Delta W
    parts.append(_box_with_text(730, cy + 190, 280, 45, BG_YELLOW,
                                "Delta_W = B * A", YELLOW))
    parts.append(_arrow(875, cy + 145, 875, cy + 188))

    parts.append(_box_with_text(730, cy + 260, 280, 45, BG_ORANGE,
                                "Delta_h = (B*A) * x", ORANGE))
    parts.append(_arrow(875, cy + 237, 875, cy + 258))

    parts.append(_text(875, cy + 340, f"Trainable: {2}*d*r params",
                       size=14, fill=ORANGE, weight="bold"))
    parts.append(_text(875, cy + 365, "~0.01% of total", size=13, fill=MID_TEXT))

    cy += 420

    # Merge
    parts.append(_arrow(325, cy - 20, 500, cy + 20))
    parts.append(_arrow(875, cy - 20, 700, cy + 20))
    parts.append(_box_with_text(350, cy + 25, 500, 55, BG_GREEN,
                                "Output: h + Delta_h = (W_0 + BA) * x", GREEN))
    cy += 100

    # Comparison table
    parts.append(_text(600, cy, "Parameter Efficiency", size=20, weight="bold"))
    cy += 30

    if is_qlora:
        rows = [
            ("Full Fine-tuning", "100%", "16-bit", BG_RED),
            ("LoRA", "~0.01%", "16-bit", BG_ORANGE),
            ("QLoRA", "~0.01%", "4-bit (NF4)", BG_GREEN),
        ]
    else:
        rows = [
            ("Full Fine-tuning", "100%", "All weights", BG_RED),
            ("LoRA (r=8)", "~0.01%", "Low-rank adapters only", BG_GREEN),
            ("LoRA (r=64)", "~0.08%", "Higher rank = more capacity", BG_ORANGE),
        ]

    for method, pct, detail, bg in rows:
        parts.append(_rect(200, cy, 800, 40, bg, rx=8))
        parts.append(_text(350, cy + 26, method, size=14, weight="bold", anchor="start"))
        parts.append(_text(650, cy + 26, pct, size=14, fill=MID_TEXT))
        parts.append(_text(800, cy + 26, detail, size=13, fill=LIGHT_TEXT, anchor="start"))
        cy += 50

    if is_qlora:
        cy += 10
        parts.append(_rect(150, cy, 900, 55, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 22, "QLoRA: Fine-tune 65B model on single 48GB GPU",
                           size=15, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 44, "Paged Optimizers + NF4 + Double Quantization",
                           size=13, fill=MID_TEXT))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: Scaling Laws ──────────────────────────────────────────────

SCALING_SPECS = {
    17: {"name": "Scaling Laws", "type": "Neural Scaling Laws",
         "finding": "Performance scales as power laws with model size, data, and compute",
         "formula": "L(N) ~ N^(-alpha_N), L(D) ~ D^(-alpha_D), L(C) ~ C^(-alpha_C)",
         "detail": "N = parameters, D = dataset size, C = compute (FLOPs)"},
    18: {"name": "Chinchilla", "type": "Compute-Optimal Training",
         "finding": "Models should be trained on ~20x more tokens than parameters",
         "formula": "Optimal: N_opt ~ C^0.5, D_opt ~ C^0.5",
         "detail": "70B params + 1.4T tokens beats 280B + 300B tokens"},
    34: {"name": "Sheared LLaMA", "type": "Structured Pruning",
         "finding": "Prune large models to smaller sizes, then continue pretraining",
         "formula": "Prune LLaMA-2-7B to 1.3B/2.7B, then train on 50B tokens",
         "detail": "Targeted structured pruning + dynamic batch loading"},
    40: {"name": "Scaling Data-Constrained", "type": "Data-Constrained Scaling",
         "finding": "With limited unique data, returns diminish with repeated epochs",
         "formula": "L(N, D, R) where R = number of repetitions",
         "detail": "Value of repeated data < fresh data, but still helps"},
    54: {"name": "Architecture & Objectives", "type": "Architecture Comparison",
         "finding": "Encoder-decoder with denoising obj. works best for many tasks",
         "formula": "Compared: Enc-Dec, Dec-only, Prefix LM",
         "detail": "Systematic comparison of architectures and objectives"},
    55: {"name": "Scaling Instruction FT", "type": "Instruction Scaling",
         "finding": "Instruction finetuning scales with #tasks, model size, and CoT",
         "formula": "Performance improves log-linearly with number of tasks",
         "detail": "1.8K tasks, PaLM 540B + CoT = new SOTA"},
}


def generate_scaling_svg(paper_id, title):
    """Scaling Laws 다이어그램 생성."""
    specs = SCALING_SPECS.get(paper_id, SCALING_SPECS[17])
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 20

    parts.append(_text(600, cy, specs["type"], size=20, weight="bold", fill=BLUE))
    cy += 35

    # Key finding box
    parts.append(_rect(100, cy, 1000, 100, BG_LIGHT, rx=16, stroke="#DDD"))
    parts.append(_text(600, cy + 25, "Key Finding", size=16, weight="bold", fill=BLUE))
    parts.append(_text(600, cy + 55, specs["finding"], size=15, fill=DARK_TEXT))
    parts.append(_text(600, cy + 80, specs["detail"], size=13, fill=MID_TEXT))
    cy += 120

    # Scaling curve visualization
    parts.append(_text(600, cy, "Scaling Relationship", size=18, weight="bold"))
    cy += 25

    # Axes
    ax_left = 200
    ax_right = 1000
    ax_top = cy + 20
    ax_bottom = cy + 350
    ax_width = ax_right - ax_left
    ax_height = ax_bottom - ax_top

    # Background
    parts.append(_rect(ax_left - 20, ax_top - 20, ax_width + 60, ax_height + 60,
                       BG_LIGHT, rx=12))

    # Y axis
    parts.append(_line(ax_left, ax_top, ax_left, ax_bottom, DARK_TEXT))
    parts.append(_text(ax_left - 15, ax_top + ax_height // 2,
                       "Performance (Loss)", size=14, fill=MID_TEXT))
    # X axis
    parts.append(_line(ax_left, ax_bottom, ax_right, ax_bottom, DARK_TEXT))

    if paper_id in (17, 18):
        # Power law curves
        parts.append(_text(600, ax_bottom + 25, "Scale (log)", size=14, fill=MID_TEXT))

        # Curve points (power law decay)
        curves = [
            ("Model Size (N)", BLUE, [(0, 0.95), (0.15, 0.7), (0.3, 0.55),
                                       (0.5, 0.4), (0.7, 0.3), (0.9, 0.22), (1.0, 0.18)]),
            ("Dataset Size (D)", ORANGE, [(0, 0.9), (0.15, 0.68), (0.3, 0.52),
                                           (0.5, 0.38), (0.7, 0.28), (0.9, 0.21), (1.0, 0.17)]),
            ("Compute (C)", GREEN, [(0, 0.92), (0.15, 0.65), (0.3, 0.48),
                                     (0.5, 0.35), (0.7, 0.26), (0.9, 0.19), (1.0, 0.15)]),
        ]

        for label, color, points in curves:
            path_d = ""
            for i, (px, py) in enumerate(points):
                x = ax_left + px * ax_width
                y = ax_top + py * ax_height
                if i == 0:
                    path_d += f"M {x} {y}"
                else:
                    path_d += f" L {x} {y}"
            parts.append(f'  <path d="{path_d}" fill="none" stroke="{color}" '
                         f'stroke-width="3"/>')

        # Legend
        legend_y = ax_top + 20
        for label, color, _ in curves:
            parts.append(_line(ax_right - 250, legend_y, ax_right - 210, legend_y, color, width=3))
            parts.append(_text(ax_right - 200, legend_y + 5, label, size=13, fill=color,
                               anchor="start", weight="bold"))
            legend_y += 25

        if paper_id == 18:
            # Chinchilla optimal line
            parts.append(_line(ax_left + ax_width * 0.4, ax_top,
                               ax_left + ax_width * 0.4, ax_bottom, RED, dashed=True))
            parts.append(_text(ax_left + ax_width * 0.4, ax_top - 5,
                               "Chinchilla Optimal", size=13, fill=RED, weight="bold"))
    else:
        # Generic scaling visualization
        parts.append(_text(600, ax_bottom + 25, "Scale", size=14, fill=MID_TEXT))
        points = [(0, 0.9), (0.1, 0.7), (0.2, 0.55), (0.35, 0.42),
                  (0.5, 0.32), (0.7, 0.24), (0.85, 0.18), (1.0, 0.14)]
        path_d = ""
        for i, (px, py) in enumerate(points):
            x = ax_left + px * ax_width
            y = ax_top + py * ax_height
            if i == 0:
                path_d += f"M {x} {y}"
            else:
                path_d += f" L {x} {y}"
        parts.append(f'  <path d="{path_d}" fill="none" stroke="{BLUE}" stroke-width="3"/>')
        parts.append(_text(ax_right - 100, ax_top + 30, specs["name"], size=14,
                           fill=BLUE, weight="bold"))

    cy = ax_bottom + 50

    # Formula box
    parts.append(_rect(150, cy, 900, 60, BG_PURPLE, rx=12, stroke=PURPLE))
    parts.append(_text(600, cy + 35, specs["formula"], size=16, weight="bold", fill=PURPLE))
    cy += 80

    # Key takeaways
    parts.append(_text(600, cy, "Key Takeaways", size=18, weight="bold"))
    cy += 10

    if paper_id == 17:
        takeaways = [
            (BLUE, "Smooth power laws govern scaling behavior"),
            (ORANGE, "Larger models are more sample-efficient"),
            (GREEN, "Optimal allocation: most compute to model size"),
        ]
    elif paper_id == 18:
        takeaways = [
            (BLUE, "Current LLMs are significantly undertrained"),
            (ORANGE, "Chinchilla 70B matches Gopher 280B with 4x more data"),
            (GREEN, "Optimal ratio: ~20 tokens per parameter"),
        ]
    elif paper_id == 34:
        takeaways = [
            (BLUE, "Structured pruning preserves architecture compatibility"),
            (ORANGE, "Dynamic batch loading balances domain proportions"),
            (GREEN, "Sheared-LLaMA-2.7B outperforms models trained from scratch"),
        ]
    elif paper_id == 40:
        takeaways = [
            (BLUE, "Unique data is more valuable than repeated data"),
            (ORANGE, "Returns from repeating diminish but remain positive"),
            (GREEN, "Data augmentation can partially compensate"),
        ]
    elif paper_id == 54:
        takeaways = [
            (BLUE, "Encoder-decoder generally performs best"),
            (ORANGE, "Denoising objectives outperform LM objectives"),
            (GREEN, "Architecture choice matters as much as scale"),
        ]
    else:  # 55
        takeaways = [
            (BLUE, "Instruction finetuning scales with number of tasks"),
            (ORANGE, "Chain-of-thought data is crucial for reasoning"),
            (GREEN, "Benefits both seen and unseen tasks"),
        ]

    for color, text in takeaways:
        cy += 35
        parts.append(_rect(200, cy - 20, 20, 20, color, rx=4))
        parts.append(_text(235, cy - 2, text, size=14, fill=MID_TEXT, anchor="start"))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: RAG ────────────────────────────────────────────────────────

RAG_SPECS = {
    25: {"name": "RAG", "type": "Retrieval-Augmented Generation",
         "retriever": "DPR (Dense Passage Retrieval)",
         "generator": "BART-Large", "index": "FAISS",
         "extra": "End-to-end training of retriever + generator"},
    26: {"name": "Self-RAG", "type": "Self-Reflective RAG",
         "retriever": "Contriever-MS MARCO",
         "generator": "LLaMA-2-7B/13B", "index": "Learned retrieval tokens",
         "extra": "Reflection tokens: [Retrieve], [IsRel], [IsSup], [IsUse]"},
    41: {"name": "REALM", "type": "Retrieval-Augmented LM Pre-Training",
         "retriever": "BERT-based Dense Retriever",
         "generator": "BERT (masked LM)", "index": "MIPS (Max Inner Product)",
         "extra": "Pre-train with retrieval, asynchronous index refresh"},
    42: {"name": "In-Context RALM", "type": "In-Context Retrieval-Augmented LM",
         "retriever": "BM25 / Contriever",
         "generator": "GPT-2/3, LLaMA, etc.", "index": "Off-the-shelf",
         "extra": "Prepend retrieved docs to context, no fine-tuning needed"},
    43: {"name": "ARES", "type": "Automated RAG Evaluation",
         "retriever": "Evaluates any retriever",
         "generator": "LLM Judge (GPT-3.5/4)", "index": "PPI statistical method",
         "extra": "Context Relevance, Answer Faithfulness, Answer Relevance"},
}


def generate_rag_svg(paper_id, title):
    """RAG 아키텍처 다이어그램 생성."""
    specs = RAG_SPECS.get(paper_id, RAG_SPECS[25])
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 20

    parts.append(_text(600, cy, specs["type"], size=20, weight="bold", fill=BLUE))
    cy += 35

    if paper_id == 43:
        # ARES is evaluation framework, not a RAG pipeline
        parts.append(_text(600, cy, "RAG Evaluation Framework", size=18, weight="bold"))
        cy += 30

        # Three evaluation dimensions
        dims = [
            ("Context Relevance", "Is the retrieved context relevant to the query?", BG_BLUE, BLUE),
            ("Answer Faithfulness", "Is the answer grounded in the retrieved context?", BG_ORANGE, ORANGE),
            ("Answer Relevance", "Does the answer address the original query?", BG_GREEN, GREEN),
        ]
        for dim_name, dim_desc, bg, color in dims:
            parts.append(_rect(200, cy, 800, 70, bg, rx=14, stroke=color))
            parts.append(_text(600, cy + 28, dim_name, size=16, weight="bold", fill=color))
            parts.append(_text(600, cy + 52, dim_desc, size=13, fill=MID_TEXT))
            cy += 85

        # Pipeline
        parts.append(_text(600, cy + 10, "ARES Pipeline", size=18, weight="bold"))
        cy += 40
        steps = [
            ("LLM Judge", "Generate labels\nfor RAG triples", BG_BLUE, BLUE),
            ("Classifier", "Train lightweight\nclassifier on labels", BG_ORANGE, ORANGE),
            ("PPI", "Prediction-Powered\nInference for CI", BG_GREEN, GREEN),
        ]
        sx = 150
        for sname, sdesc, bg, color in steps:
            parts.append(_rect(sx, cy, 280, 120, bg, rx=12, stroke=color))
            parts.append(_text(sx + 140, cy + 30, sname, size=16, weight="bold", fill=color))
            lines = sdesc.split("\n")
            for li, ln in enumerate(lines):
                parts.append(_text(sx + 140, cy + 60 + li * 22, ln, size=13, fill=MID_TEXT))
            if sx < 700:
                parts.append(_arrow(sx + 283, cy + 60, sx + 308, cy + 60))
            sx += 310
        cy += 150
    else:
        # Standard RAG pipeline
        parts.append(_text(600, cy, "Architecture Pipeline", size=18, weight="bold"))
        cy += 30

        # Query
        parts.append(_box_with_text(350, cy, 500, 50, BG_PURPLE,
                                    "Input Query / Question", PURPLE))
        cy += 60
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Retriever
        parts.append(_rect(200, cy, 800, 120, BG_BLUE, rx=14, stroke=BLUE))
        parts.append(_text(600, cy + 25, "Retriever", size=18, weight="bold", fill=BLUE))
        parts.append(_text(600, cy + 55, specs["retriever"], size=14, fill=MID_TEXT))

        # Document store
        parts.append(_rect(780, cy + 10, 200, 50, BG_LIGHT, rx=8, stroke="#CCC"))
        parts.append(_text(880, cy + 40, f"Index: {specs['index']}", size=12,
                           fill=MID_TEXT, weight="bold"))

        if paper_id == 26:  # Self-RAG
            parts.append(_rect(220, cy + 75, 180, 35, BG_YELLOW, rx=8))
            parts.append(_text(310, cy + 97, "[Retrieve] token", size=12,
                               fill=YELLOW, weight="bold"))
            parts.append(_rect(420, cy + 75, 160, 35, BG_YELLOW, rx=8))
            parts.append(_text(500, cy + 97, "[IsRel] check", size=12,
                               fill=YELLOW, weight="bold"))

        parts.append(_text(600, cy + 105, f"Top-k relevant passages retrieved",
                           size=13, fill=LIGHT_TEXT))
        cy += 130
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Retrieved Documents
        parts.append(_rect(250, cy, 700, 100, BG_LIGHT, rx=14, stroke="#DDD"))
        parts.append(_text(600, cy + 22, "Retrieved Documents / Passages",
                           size=16, weight="bold", fill=DARK_TEXT))
        # Show sample docs
        for j in range(3):
            dx = 290 + j * 220
            parts.append(_rect(dx, cy + 40, 200, 45, BG_BLUE, rx=8))
            parts.append(_text(dx + 100, cy + 67, f"Passage {j+1}", size=13,
                               fill=BLUE, weight="bold"))
        cy += 110
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Generator
        parts.append(_rect(200, cy, 800, 100, BG_ORANGE, rx=14, stroke=ORANGE))
        parts.append(_text(600, cy + 25, "Generator / Reader", size=18,
                           weight="bold", fill=ORANGE))
        parts.append(_text(600, cy + 55, specs["generator"], size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 80, "Generates answer conditioned on query + retrieved passages",
                           size=13, fill=LIGHT_TEXT))

        if paper_id == 26:  # Self-RAG critique tokens
            parts.append(_rect(750, cy + 60, 230, 30, BG_YELLOW, rx=8))
            parts.append(_text(865, cy + 80, "[IsSup] [IsUse] critique",
                               size=11, fill=YELLOW, weight="bold"))
        cy += 110
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Answer
        parts.append(_box_with_text(350, cy, 500, 50, BG_GREEN,
                                    "Generated Answer", GREEN))
        cy += 70

    # Extra
    if specs.get("extra"):
        parts.append(_rect(150, cy, 900, 50, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 30, specs["extra"], size=14, weight="bold", fill=YELLOW))
        cy += 65

    # Key components
    cy += 5
    parts.append(_text(600, cy, "Key Components", size=18, weight="bold"))
    cy += 10
    components = [
        (BLUE, "Retriever", specs["retriever"]),
        (ORANGE, "Generator", specs["generator"]),
        (GREEN, "Index", specs["index"]),
    ]
    for color, label, desc in components:
        cy += 35
        parts.append(_rect(200, cy - 20, 20, 20, color, rx=4))
        parts.append(_text(235, cy - 2, f"{label}:", size=14, anchor="start", weight="bold"))
        parts.append(_text(380, cy - 2, desc, size=14, fill=MID_TEXT, anchor="start"))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: SSM ────────────────────────────────────────────────────────

def generate_ssm_svg(paper_id, title):
    """SSM (Mamba/Jamba) 다이어그램 생성."""
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 20

    if paper_id == 31:  # Mamba
        parts.append(_text(600, cy, "Selective State Space Model", size=20,
                           weight="bold", fill=BLUE))
        cy += 35

        # Problem with Transformers
        parts.append(_rect(100, cy, 1000, 70, BG_RED, rx=14, stroke=RED))
        parts.append(_text(600, cy + 22, "Transformer Limitation: O(N^2) attention complexity",
                           size=15, weight="bold", fill=RED))
        parts.append(_text(600, cy + 50, "Mamba Solution: O(N) linear-time with selective state spaces",
                           size=14, fill=MID_TEXT))
        cy += 90

        # SSM core equation
        parts.append(_rect(150, cy, 900, 80, BG_PURPLE, rx=14, stroke=PURPLE))
        parts.append(_text(600, cy + 25, "State Space Model: h'(t) = Ah(t) + Bx(t), y(t) = Ch(t)",
                           size=16, weight="bold", fill=PURPLE))
        parts.append(_text(600, cy + 55, "Discretized: h_k = A_bar * h_{k-1} + B_bar * x_k",
                           size=14, fill=MID_TEXT))
        cy += 100

        # Mamba Block
        parts.append(_text(600, cy, "Mamba Block Architecture", size=18, weight="bold"))
        cy += 25

        parts.append(_rect(200, cy, 800, 420, BG_BLUE, rx=16, stroke=BLUE))
        parts.append(_text(600, cy + 25, "Mamba Block", size=18, weight="bold", fill=BLUE))

        # Input
        iy = cy + 50
        parts.append(_box_with_text(300, iy, 600, 40, BG_PURPLE,
                                    "Input (B, L, D)", PURPLE, rx=8, font_size=14))
        iy += 50

        # Two branches: Linear projection + Conv + SSM
        parts.append(_arrow(450, iy, 450, iy + 15))
        parts.append(_arrow(750, iy, 750, iy + 15))
        iy += 20

        # Branch 1: Conv + SSM
        parts.append(_rect(280, iy, 340, 55, BG_ORANGE, rx=10, stroke=ORANGE))
        parts.append(_text(450, iy + 22, "Linear Projection", size=14,
                           weight="bold", fill=ORANGE))
        parts.append(_text(450, iy + 42, "Expand D to E*D", size=12, fill=MID_TEXT))
        iy_left = iy + 65
        parts.append(_arrow(450, iy + 57, 450, iy_left + 5))

        parts.append(_rect(280, iy_left + 8, 340, 45, BG_ORANGE, rx=10, stroke=ORANGE))
        parts.append(_text(450, iy_left + 35, "Conv1D + SiLU", size=14,
                           weight="bold", fill=ORANGE))
        iy_left += 63
        parts.append(_arrow(450, iy_left, 450, iy_left + 15))

        parts.append(_rect(280, iy_left + 18, 340, 75, BG_GREEN, rx=10, stroke=GREEN))
        parts.append(_text(450, iy_left + 42, "Selective SSM", size=15,
                           weight="bold", fill=GREEN))
        parts.append(_text(450, iy_left + 65, "Input-dependent A, B, C, delta",
                           size=12, fill=MID_TEXT))
        parts.append(_text(450, iy_left + 82, "(Selection Mechanism)", size=11, fill=LIGHT_TEXT))
        iy_left += 100

        # Branch 2: Gate
        parts.append(_rect(660, iy, 220, 55, BG_YELLOW, rx=10, stroke=YELLOW))
        parts.append(_text(770, iy + 22, "Linear Projection", size=14,
                           weight="bold", fill=YELLOW))
        parts.append(_text(770, iy + 42, "Gate branch", size=12, fill=MID_TEXT))

        # Merge (multiply)
        iy_merge = iy_left + 20
        parts.append(_arrow(450, iy_left, 550, iy_merge))
        parts.append(_arrow(770, iy + 57, 650, iy_merge))

        parts.append(f'  <circle cx="600" cy="{iy_merge}" r="18" fill="{BG_YELLOW}" '
                     f'stroke="{YELLOW}" stroke-width="2"/>')
        parts.append(_text(600, iy_merge + 6, "x", size=18, weight="bold", fill=YELLOW))

        iy = iy_merge + 25
        parts.append(_arrow(600, iy, 600, iy + 15))
        iy += 18
        parts.append(_box_with_text(350, iy, 500, 40, BG_PURPLE,
                                    "Output Projection (D)", PURPLE, rx=8, font_size=14))

        cy += 440
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Key advantage
        parts.append(_rect(150, cy, 900, 55, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 22, "Key: Selection mechanism makes parameters input-dependent",
                           size=15, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 44, "Unlike fixed SSM, Mamba adapts A, B, C, delta per token",
                           size=13, fill=MID_TEXT))

    elif paper_id == 32:  # Jamba
        parts.append(_text(600, cy, "Hybrid Transformer-Mamba Architecture", size=20,
                           weight="bold", fill=BLUE))
        cy += 35

        # Architecture overview
        parts.append(_rect(100, cy, 1000, 100, BG_LIGHT, rx=16, stroke="#DDD"))
        parts.append(_text(600, cy + 25, "Jamba = Transformer Layers + Mamba Layers + MoE",
                           size=16, weight="bold", fill=BLUE))
        parts.append(_text(600, cy + 55, "Interleave attention and SSM layers for best of both worlds",
                           size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 80, "52B total params, 12B active (MoE with top-2 of 16 experts)",
                           size=13, fill=LIGHT_TEXT))
        cy += 120

        # Layer pattern
        parts.append(_text(600, cy, "Layer Pattern (1:7 ratio)", size=18, weight="bold"))
        cy += 25

        layer_pattern = [
            ("Mamba", BG_GREEN, GREEN),
            ("Mamba", BG_GREEN, GREEN),
            ("Mamba", BG_GREEN, GREEN),
            ("Mamba", BG_GREEN, GREEN),
            ("Mamba", BG_GREEN, GREEN),
            ("Mamba", BG_GREEN, GREEN),
            ("Mamba", BG_GREEN, GREEN),
            ("Attention", BG_BLUE, BLUE),
        ]

        lx = 130
        lw = 110
        for j, (lname, bg, color) in enumerate(layer_pattern):
            parts.append(_rect(lx, cy, lw, 50, bg, rx=8, stroke=color))
            parts.append(_text(lx + lw // 2, cy + 30, lname, size=12,
                               weight="bold", fill=color))
            if j < len(layer_pattern) - 1:
                parts.append(_arrow(lx + lw + 3, cy + 25, lx + lw + 17, cy + 25))
            lx += lw + 20

        cy += 65
        parts.append(_text(600, cy, "... repeated across all layers", size=13, fill=LIGHT_TEXT))
        cy += 25

        # Hybrid block detail
        parts.append(_rect(150, cy, 400, 300, BG_GREEN, rx=14, stroke=GREEN))
        parts.append(_text(350, cy + 25, "Mamba Layer", size=16, weight="bold", fill=GREEN))
        mamba_items = ["RMSNorm", "Mamba SSM Block", "Residual Connection"]
        my = cy + 55
        for item in mamba_items:
            parts.append(_box_with_text(200, my, 300, 40, "#D8F0D4", item, GREEN,
                                        rx=8, font_size=13))
            my += 55

        parts.append(_rect(650, cy, 400, 300, BG_BLUE, rx=14, stroke=BLUE))
        parts.append(_text(850, cy + 25, "Attention Layer", size=16, weight="bold", fill=BLUE))
        attn_items = ["RMSNorm", "Grouped-Query Attention", "MoE FFN (top-2/16)"]
        ay = cy + 55
        for item in attn_items:
            bg_item = BG_ORANGE if "MoE" in item else "#D0E4F5"
            parts.append(_box_with_text(700, ay, 300, 40, bg_item, item,
                                        ORANGE if "MoE" in item else BLUE,
                                        rx=8, font_size=13))
            ay += 55

        cy += 320
        parts.append(_rect(150, cy, 900, 55, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 22, "256K context window with Mamba efficiency + Attention quality",
                           size=15, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 44, "First production hybrid SSM-Transformer model",
                           size=13, fill=MID_TEXT))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: Vision/Multimodal ──────────────────────────────────────────

def generate_vision_svg(paper_id, title):
    """Vision Transformer / Multimodal 다이어그램 생성."""
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 20

    if paper_id == 29:  # ViT
        parts.append(_text(600, cy, "Vision Transformer (ViT)", size=20,
                           weight="bold", fill=BLUE))
        cy += 40

        # Image to patches
        parts.append(_text(600, cy, "Image Tokenization", size=18, weight="bold"))
        cy += 25

        # Input image
        img_x, img_y = 150, cy
        parts.append(_rect(img_x, img_y, 240, 240, "#E8E8E8", rx=8, stroke="#AAA"))
        parts.append(_text(img_x + 120, img_y + 125, "Input Image", size=14, fill=MID_TEXT))
        # Grid lines (4x4 patches)
        for i in range(1, 4):
            parts.append(_line(img_x + i * 60, img_y, img_x + i * 60, img_y + 240, "#CCC"))
            parts.append(_line(img_x, img_y + i * 60, img_x + 240, img_y + i * 60, "#CCC"))
        parts.append(_text(img_x + 120, img_y + 260, "Split into 16x16 patches",
                           size=13, fill=LIGHT_TEXT))

        # Arrow
        parts.append(_arrow(img_x + 245, img_y + 120, img_x + 300, img_y + 120))

        # Patch embeddings
        pe_x = img_x + 310
        parts.append(_rect(pe_x, img_y, 300, 240, BG_PURPLE, rx=12, stroke=PURPLE))
        parts.append(_text(pe_x + 150, img_y + 25, "Patch Embeddings", size=16,
                           weight="bold", fill=PURPLE))

        # Patch sequence
        for i in range(4):
            for j in range(4):
                px = pe_x + 20 + j * 68
                py = img_y + 45 + i * 45
                parts.append(_rect(px, py, 60, 35, "#E8D5F5", rx=4))
                parts.append(_text(px + 30, py + 22, f"P{i*4+j+1}", size=10,
                                   fill=PURPLE, weight="bold"))

        # [CLS] token + Position Embeddings
        cls_x = pe_x + 320
        parts.append(_arrow(pe_x + 305, img_y + 120, cls_x + 10, img_y + 120))

        parts.append(_rect(cls_x + 15, img_y, 300, 240, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(cls_x + 165, img_y + 25, "+ Position Emb", size=14,
                           weight="bold", fill=YELLOW))
        parts.append(_rect(cls_x + 30, img_y + 50, 60, 35, BG_RED, rx=4, stroke=RED))
        parts.append(_text(cls_x + 60, img_y + 72, "[CLS]", size=11,
                           fill=RED, weight="bold"))
        for i in range(3):
            px = cls_x + 100 + i * 65
            parts.append(_rect(px, img_y + 50, 60, 35, BG_BLUE, rx=4))
            parts.append(_text(px + 30, img_y + 72, f"E{i+1}", size=10,
                               fill=BLUE, weight="bold"))
        parts.append(_text(cls_x + 165, img_y + 110, "...", size=18, fill=MID_TEXT))
        parts.append(_text(cls_x + 165, img_y + 150, "Learnable 1D pos", size=12, fill=MID_TEXT))
        parts.append(_text(cls_x + 165, img_y + 175, "embeddings added", size=12, fill=MID_TEXT))

        cy = img_y + 280
        parts.append(_arrow(600, cy, 600, cy + 18))
        cy += 22

        # Transformer Encoder
        parts.append(_rect(250, cy, 700, 200, BG_BLUE, rx=16, stroke=BLUE))
        parts.append(_text(600, cy + 25, "Transformer Encoder x L", size=18,
                           weight="bold", fill=BLUE))

        iy = cy + 50
        parts.append(_box_with_text(320, iy, 560, 40, BG_GREEN,
                                    "Layer Norm + Multi-Head Self-Attention", GREEN,
                                    rx=8, font_size=13))
        iy += 50
        parts.append(_arrow(600, iy, 600, iy + 8))
        iy += 12
        parts.append(_box_with_text(320, iy, 560, 40, BG_GREEN,
                                    "Layer Norm + MLP (GELU)", GREEN, rx=8, font_size=13))
        iy += 50
        parts.append(_text(600, cy + 185, "Residual connections around each sub-layer",
                           size=12, fill=LIGHT_TEXT))

        cy += 210
        parts.append(_arrow(600, cy, 600, cy + 18))
        cy += 22

        # Classification head
        parts.append(_box_with_text(350, cy, 500, 55, BG_RED,
                                    "MLP Head on [CLS] token", RED))
        cy += 70

        # Key innovation
        parts.append(_rect(150, cy, 900, 55, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 22, "Key: Standard Transformer on image patches, no convolutions",
                           size=15, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 44, "Scales well with data: ViT-H/14 achieves 88.55% on ImageNet",
                           size=13, fill=MID_TEXT))

    elif paper_id == 30:  # LLaVA
        parts.append(_text(600, cy, "Visual Instruction Tuning (LLaVA)", size=20,
                           weight="bold", fill=BLUE))
        cy += 40

        # Architecture
        parts.append(_text(600, cy, "LLaVA Architecture", size=18, weight="bold"))
        cy += 25

        # Image input path
        parts.append(_rect(100, cy, 400, 400, BG_PURPLE, rx=16, stroke=PURPLE))
        parts.append(_text(300, cy + 25, "Visual Path", size=18, weight="bold", fill=PURPLE))

        iy = cy + 50
        parts.append(_box_with_text(150, iy, 300, 50, "#E8E8E8", "Input Image", "#888"))
        iy += 60
        parts.append(_arrow(300, iy, 300, iy + 12))
        iy += 15
        parts.append(_box_with_text(150, iy, 300, 50, BG_BLUE,
                                    "CLIP ViT-L/14", BLUE))
        parts.append(_text(300, iy + 65, "Visual Encoder (frozen)", size=12, fill=LIGHT_TEXT))
        iy += 75
        parts.append(_arrow(300, iy, 300, iy + 12))
        iy += 15
        parts.append(_box_with_text(150, iy, 300, 55, BG_ORANGE,
                                    "Linear Projection W", ORANGE))
        parts.append(_text(300, iy + 70, "Align visual to language space", size=12, fill=LIGHT_TEXT))

        # Text input path
        parts.append(_rect(700, cy, 400, 400, BG_BLUE, rx=16, stroke=BLUE))
        parts.append(_text(900, cy + 25, "Language Path", size=18, weight="bold", fill=BLUE))

        ty = cy + 50
        parts.append(_box_with_text(750, ty, 300, 50, BG_YELLOW,
                                    "Text Instruction", YELLOW))
        ty += 60
        parts.append(_arrow(900, ty, 900, ty + 12))
        ty += 15
        parts.append(_box_with_text(750, ty, 300, 50, BG_PURPLE,
                                    "Token Embedding", PURPLE))

        # Merge point
        merge_y = cy + 420
        parts.append(_arrow(300, cy + 400, 500, merge_y + 25))
        parts.append(_arrow(900, cy + 400, 700, merge_y + 25))

        parts.append(_rect(350, merge_y, 500, 55, BG_GREEN, rx=14, stroke=GREEN))
        parts.append(_text(600, merge_y + 22, "Concatenate Visual + Text Tokens",
                           size=15, weight="bold", fill=GREEN))
        parts.append(_text(600, merge_y + 44, "[IMG_1...IMG_N] + [TEXT_1...TEXT_M]",
                           size=13, fill=MID_TEXT))

        cy = merge_y + 65
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # LLM
        parts.append(_box_with_text(300, cy, 600, 60, BG_ORANGE,
                                    "LLaMA / Vicuna (Language Model)", ORANGE))
        parts.append(_text(600, cy + 75, "Generates text response", size=13, fill=LIGHT_TEXT))
        cy += 85
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Output
        parts.append(_box_with_text(350, cy, 500, 50, BG_RED,
                                    "Generated Response", RED))
        cy += 65

        # Training stages
        parts.append(_rect(100, cy, 1000, 80, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 22, "Two-Stage Training",
                           size=16, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 48,
                           "Stage 1: Pre-train projection (CC3M, frozen LLM)",
                           size=13, fill=MID_TEXT))
        parts.append(_text(600, cy + 68,
                           "Stage 2: Fine-tune end-to-end on visual instruction data",
                           size=13, fill=MID_TEXT))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: Prompting / ICL ────────────────────────────────────────────

PROMPTING_SPECS = {
    44: {"name": "Rethinking Demonstrations",
         "desc": "Format and label space matter more than correct labels",
         "flow": ["Input Format", "Label Space", "Distribution", "LLM", "Prediction"],
         "extra": "Random labels perform nearly as well as correct labels in ICL"},
    45: {"name": "T0 (Multitask Prompted)",
         "desc": "Train on diverse prompted tasks for zero-shot generalization",
         "flow": ["Diverse Tasks", "Prompt Templates", "T5 Training", "Zero-Shot Transfer"],
         "extra": "T0 (11B) matches GPT-3 (175B) on zero-shot tasks"},
    46: {"name": "FLAN",
         "desc": "Instruction-tuned models generalize to unseen task types",
         "flow": ["62 NLP Tasks", "Instruction Templates", "Fine-tune LM", "Zero-Shot Eval"],
         "extra": "Instruction tuning on diverse tasks improves zero-shot performance"},
    47: {"name": "Chatbot Arena",
         "desc": "Open platform for evaluating LLMs via human pairwise preferences",
         "flow": ["User Query", "Random Model Pair", "Side-by-Side Comparison", "Elo Rating"],
         "extra": "Crowdsourced evaluation with Bradley-Terry model and Elo ratings"},
    48: {"name": "AgentBench",
         "desc": "Benchmark for evaluating LLMs as autonomous agents",
         "flow": ["Environment", "LLM Agent", "Action Selection", "Evaluation"],
         "extra": "8 environments: OS, DB, Web, Game, etc. GPT-4 leads significantly"},
    49: {"name": "MEGAVERSE",
         "desc": "Multilingual benchmark across languages, modalities, and tasks",
         "flow": ["Multi-lang Input", "LLM Processing", "Cross-lingual Transfer", "Evaluation"],
         "extra": "Evaluates LLMs on 83 languages across multiple NLP tasks"},
    56: {"name": "Chain-of-Thought",
         "desc": "Step-by-step reasoning in prompts unlocks complex reasoning",
         "flow": ["Question", "Few-Shot Examples with CoT", "LLM", "Step-by-Step Answer"],
         "extra": "Emergent ability at scale: significant gains with 100B+ models"},
}


def generate_prompting_svg(paper_id, title):
    """Prompting / ICL 다이어그램 생성."""
    specs = PROMPTING_SPECS.get(paper_id, PROMPTING_SPECS[56])
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 20

    parts.append(_text(600, cy, specs["desc"], size=16, fill=MID_TEXT))
    cy += 35

    # Main flow
    parts.append(_text(600, cy, "Pipeline / Process", size=20, weight="bold"))
    cy += 30

    flow_colors = [
        (BG_PURPLE, PURPLE), (BG_BLUE, BLUE), (BG_ORANGE, ORANGE),
        (BG_GREEN, GREEN), (BG_RED, RED),
    ]

    flow = specs["flow"]
    n = len(flow)
    box_w = min(220, (900 - (n - 1) * 25) // n)
    total_w = n * box_w + (n - 1) * 25
    start_x = 600 - total_w // 2

    for i, step in enumerate(flow):
        bg, color = flow_colors[i % len(flow_colors)]
        fx = start_x + i * (box_w + 25)
        parts.append(_rect(fx, cy, box_w, 65, bg, rx=12, stroke=color))
        # Handle long step names
        if len(step) > 18:
            words = step.split()
            mid = len(words) // 2
            parts.append(_text(fx + box_w // 2, cy + 25, " ".join(words[:mid]),
                               size=13, weight="bold", fill=color))
            parts.append(_text(fx + box_w // 2, cy + 43, " ".join(words[mid:]),
                               size=13, weight="bold", fill=color))
        else:
            parts.append(_text(fx + box_w // 2, cy + 38, step,
                               size=14, weight="bold", fill=color))
        if i < n - 1:
            parts.append(_arrow(fx + box_w + 3, cy + 32, fx + box_w + 20, cy + 32))
    cy += 85

    # Detailed content based on paper
    if paper_id == 56:  # Chain-of-Thought
        parts.append(_text(600, cy, "Chain-of-Thought Prompting", size=20, weight="bold"))
        cy += 30

        # Standard vs CoT
        parts.append(_rect(100, cy, 480, 350, BG_ORANGE, rx=14, stroke=ORANGE))
        parts.append(_text(340, cy + 25, "Standard Prompting", size=16,
                           weight="bold", fill=ORANGE))
        std = [
            "Q: Roger has 5 tennis balls.",
            "He buys 2 more cans of 3.",
            "How many does he have?",
            "",
            "A: The answer is 11.",
        ]
        for j, line in enumerate(std):
            parts.append(_text(150, cy + 65 + j * 28, line, size=13, fill=MID_TEXT,
                               anchor="start"))
        parts.append(_text(340, cy + 260, "Direct answer", size=14, fill=RED, weight="bold"))
        parts.append(_text(340, cy + 290, "(may fail on complex reasoning)",
                           size=12, fill=LIGHT_TEXT))

        parts.append(_rect(620, cy, 480, 350, BG_GREEN, rx=14, stroke=GREEN))
        parts.append(_text(860, cy + 25, "Chain-of-Thought Prompting", size=16,
                           weight="bold", fill=GREEN))
        cot = [
            "Q: Roger has 5 tennis balls.",
            "He buys 2 more cans of 3.",
            "How many does he have?",
            "",
            "A: Roger started with 5 balls.",
            "2 cans of 3 = 6 tennis balls.",
            "5 + 6 = 11.",
            "The answer is 11.",
        ]
        for j, line in enumerate(cot):
            parts.append(_text(660, cy + 65 + j * 28, line, size=13, fill=MID_TEXT,
                               anchor="start"))
        parts.append(_text(860, cy + 310, "Step-by-step reasoning",
                           size=14, fill=GREEN, weight="bold"))
        parts.append(_text(860, cy + 335, "(enables complex reasoning)",
                           size=12, fill=LIGHT_TEXT))
        cy += 370

    elif paper_id == 47:  # Chatbot Arena
        parts.append(_text(600, cy, "Chatbot Arena Evaluation Flow", size=20, weight="bold"))
        cy += 30

        # User flow
        parts.append(_rect(150, cy, 900, 300, BG_LIGHT, rx=16, stroke="#DDD"))
        parts.append(_text(600, cy + 25, "Pairwise Comparison Process", size=18,
                           weight="bold", fill=BLUE))

        iy = cy + 55
        # User query
        parts.append(_box_with_text(350, iy, 500, 40, BG_PURPLE,
                                    "User sends query", PURPLE, rx=8, font_size=14))
        iy += 55

        # Two models
        parts.append(_rect(220, iy, 330, 50, BG_BLUE, rx=10, stroke=BLUE))
        parts.append(_text(385, iy + 30, "Model A (anonymous)", size=14,
                           weight="bold", fill=BLUE))

        parts.append(_rect(650, iy, 330, 50, BG_ORANGE, rx=10, stroke=ORANGE))
        parts.append(_text(815, iy + 30, "Model B (anonymous)", size=14,
                           weight="bold", fill=ORANGE))
        iy += 65

        # User votes
        parts.append(_box_with_text(300, iy, 600, 40, BG_GREEN,
                                    "User votes: A wins / B wins / Tie", GREEN,
                                    rx=8, font_size=14))
        iy += 55
        parts.append(_box_with_text(350, iy, 500, 40, BG_RED,
                                    "Update Elo Ratings", RED, rx=8, font_size=14))
        cy += 320

    elif paper_id == 48:  # AgentBench
        parts.append(_text(600, cy, "AgentBench: 8 Environments", size=20, weight="bold"))
        cy += 25

        envs = ["Operating System", "Database", "Knowledge Graph", "Card Game",
                "Digital Game", "Web Shopping", "Web Browsing", "Lateral Thinking"]
        env_colors = [BLUE, ORANGE, GREEN, PURPLE, RED, YELLOW, LIGHT_BLUE, "#9B59B6"]

        for i, (env, color) in enumerate(zip(envs, env_colors)):
            row = i // 4
            col = i % 4
            ex = 130 + col * 250
            ey = cy + row * 70
            parts.append(_rect(ex, ey, 220, 55, BG_LIGHT, rx=10, stroke=color))
            parts.append(_text(ex + 110, ey + 33, env, size=13, weight="bold", fill=color))
        cy += 165

    else:
        # Generic detail for other prompting papers
        parts.append(_text(600, cy, "Method Overview", size=20, weight="bold"))
        cy += 30
        parts.append(_rect(150, cy, 900, 200, BG_LIGHT, rx=16, stroke="#DDD"))

        if paper_id == 44:  # Rethinking demonstrations
            points = [
                "Input-label pairing format matters for ICL",
                "Label space definition enables prediction",
                "Correct input-label mapping is NOT necessary",
                "Random labels achieve comparable performance",
                "ICL works through format learning, not task learning",
            ]
        elif paper_id == 45:  # T0
            points = [
                "Convert diverse NLP tasks into prompted text format",
                "Train single T5 model on all tasks with templates",
                "Multiple prompt templates per task for robustness",
                "Zero-shot generalization to held-out task categories",
                "T0 (11B) competitive with GPT-3 (175B) zero-shot",
            ]
        elif paper_id == 46:  # FLAN
            points = [
                "Cluster 62 NLP datasets into 12 task types",
                "Instruction-tune on all but held-out cluster",
                "10 instruction templates per task",
                "Evaluate zero-shot on held-out cluster",
                "FLAN 137B outperforms GPT-3 175B zero-shot",
            ]
        elif paper_id == 49:  # MEGAVERSE
            points = [
                "Evaluate LLMs across 83 languages",
                "Multiple task types: NLU, NLG, Reasoning",
                "Cross-lingual transfer evaluation",
                "GPT-4 leads across languages",
                "Significant gap for low-resource languages",
            ]
        else:
            points = [specs["desc"]]

        for j, point in enumerate(points):
            parts.append(_text(200, cy + 30 + j * 32, f"  {j+1}. {point}", size=14,
                               fill=MID_TEXT, anchor="start"))
        cy += 220

    # Extra
    cy += 10
    if specs.get("extra"):
        parts.append(_rect(150, cy, 900, 50, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 30, specs["extra"], size=14, weight="bold", fill=YELLOW))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: Security / Analysis ────────────────────────────────────────

def generate_security_svg(paper_id, title):
    """Security / Data Analysis 다이어그램 생성."""
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 20

    if paper_id == 52:  # Detecting pretraining data
        parts.append(_text(600, cy, "Membership Inference for LLMs", size=20,
                           weight="bold", fill=BLUE))
        cy += 35

        # Pipeline
        parts.append(_text(600, cy, "Detection Pipeline", size=18, weight="bold"))
        cy += 30

        # Target text
        parts.append(_box_with_text(350, cy, 500, 50, BG_PURPLE,
                                    "Target Text (was it in training data?)", PURPLE))
        cy += 60
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Compute perplexity
        parts.append(_rect(200, cy, 800, 120, BG_BLUE, rx=14, stroke=BLUE))
        parts.append(_text(600, cy + 25, "Compute Model Perplexity",
                           size=16, weight="bold", fill=BLUE))
        parts.append(_text(600, cy + 55, "Lower perplexity = model has seen this text?",
                           size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 80, "But: some text is inherently easy to predict",
                           size=13, fill=LIGHT_TEXT))
        cy += 130
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Min-K% method
        parts.append(_rect(200, cy, 800, 120, BG_ORANGE, rx=14, stroke=ORANGE))
        parts.append(_text(600, cy + 25, "Min-K% Prob Method", size=16,
                           weight="bold", fill=ORANGE))
        parts.append(_text(600, cy + 55, "Average log-likelihood of K% least likely tokens",
                           size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 80, "Normalizes for text difficulty, reference-free",
                           size=13, fill=LIGHT_TEXT))
        cy += 130
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Decision
        parts.append(_rect(250, cy, 700, 70, BG_GREEN, rx=14, stroke=GREEN))
        parts.append(_text(600, cy + 22, "Classification: Member / Non-member",
                           size=16, weight="bold", fill=GREEN))
        parts.append(_text(600, cy + 50, "Threshold-based decision on Min-K% score",
                           size=14, fill=MID_TEXT))
        cy += 90

        parts.append(_rect(150, cy, 900, 55, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 22, "Tested on WikiMIA benchmark with known member/non-member split",
                           size=14, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 44, "Min-K% outperforms reference-based and loss-based methods",
                           size=13, fill=MID_TEXT))

    elif paper_id == 53:  # Scalable Extraction
        parts.append(_text(600, cy, "Training Data Extraction Attack", size=20,
                           weight="bold", fill=RED))
        cy += 35

        parts.append(_text(600, cy, "Attack Pipeline", size=18, weight="bold"))
        cy += 30

        # Step 1: Generate lots of text
        parts.append(_rect(200, cy, 800, 90, BG_BLUE, rx=14, stroke=BLUE))
        parts.append(_text(600, cy + 25, "Step 1: Generate Candidate Texts",
                           size=16, weight="bold", fill=BLUE))
        parts.append(_text(600, cy + 55, "Prompt model to generate many text continuations",
                           size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 75, "Divergent prompts to maximize extraction",
                           size=12, fill=LIGHT_TEXT))
        cy += 100
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Step 2: Score by memorization
        parts.append(_rect(200, cy, 800, 90, BG_ORANGE, rx=14, stroke=ORANGE))
        parts.append(_text(600, cy + 25, "Step 2: Score Candidates",
                           size=16, weight="bold", fill=ORANGE))
        parts.append(_text(600, cy + 55, "Compare perplexity ratio between target and reference model",
                           size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 75, "Low ratio = likely memorized training data",
                           size=12, fill=LIGHT_TEXT))
        cy += 100
        parts.append(_arrow(600, cy, 600, cy + 15))
        cy += 20

        # Step 3: Verify
        parts.append(_rect(200, cy, 800, 90, BG_RED, rx=14, stroke=RED))
        parts.append(_text(600, cy + 25, "Step 3: Verify Extraction",
                           size=16, weight="bold", fill=RED))
        parts.append(_text(600, cy + 55, "Check against known training data sources",
                           size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 75, "Extracted PII, code, URLs, verbatim text",
                           size=12, fill=LIGHT_TEXT))
        cy += 110

        parts.append(_rect(150, cy, 900, 55, BG_YELLOW, rx=12, stroke=YELLOW))
        parts.append(_text(600, cy + 22, "Extracted ~1% of training data from ChatGPT with $200 budget",
                           size=14, weight="bold", fill=YELLOW))
        parts.append(_text(600, cy + 44, "Simple prompt: 'Repeat this word forever: poem poem poem...'",
                           size=13, fill=MID_TEXT))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: Toolformer ────────────────────────────────────────────────

def generate_tool_svg(paper_id, title):
    """Toolformer 다이어그램 생성."""
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 20

    parts.append(_text(600, cy, "Language Models Can Teach Themselves to Use Tools",
                       size=18, weight="bold", fill=BLUE))
    cy += 35

    # Pipeline
    parts.append(_text(600, cy, "Self-Supervised Tool Learning Pipeline",
                       size=20, weight="bold"))
    cy += 30

    steps = [
        ("1. Sample API Calls", "LM generates potential API call positions",
         "For each position, sample multiple API calls", BG_BLUE, BLUE),
        ("2. Execute APIs", "Actually call the external tools/APIs",
         "Calculator, Search, Translation, Calendar, QA", BG_ORANGE, ORANGE),
        ("3. Filter by Usefulness", "Keep only helpful API calls",
         "Compare loss with vs without API result", BG_GREEN, GREEN),
        ("4. Fine-tune on Augmented Data", "Train model on text with API annotations",
         "Model learns when and how to call tools", BG_PURPLE, PURPLE),
    ]

    for sname, sdesc, sdetail, bg, color in steps:
        parts.append(_rect(200, cy, 800, 90, bg, rx=14, stroke=color))
        parts.append(_text(600, cy + 25, sname, size=16, weight="bold", fill=color))
        parts.append(_text(600, cy + 52, sdesc, size=14, fill=MID_TEXT))
        parts.append(_text(600, cy + 75, sdetail, size=12, fill=LIGHT_TEXT))
        cy += 100
        if sname != steps[-1][0]:
            parts.append(_arrow(600, cy, 600, cy + 10))
            cy += 15

    cy += 15

    # Available tools
    parts.append(_text(600, cy, "Available External Tools", size=18, weight="bold"))
    cy += 25

    tools = [
        ("Calculator", "Math computations", BG_BLUE, BLUE),
        ("Q&A System", "Wikipedia QA", BG_ORANGE, ORANGE),
        ("Search", "Web search API", BG_GREEN, GREEN),
        ("Translator", "MT system", BG_PURPLE, PURPLE),
        ("Calendar", "Date/time info", BG_YELLOW, YELLOW),
    ]
    tx = 110
    tw = 180
    for tname, tdesc, bg, color in tools:
        parts.append(_rect(tx, cy, tw, 65, bg, rx=10, stroke=color))
        parts.append(_text(tx + tw // 2, cy + 25, tname, size=14, weight="bold", fill=color))
        parts.append(_text(tx + tw // 2, cy + 48, tdesc, size=11, fill=MID_TEXT))
        tx += tw + 20
    cy += 85

    # Example
    parts.append(_rect(150, cy, 900, 70, BG_YELLOW, rx=12, stroke=YELLOW))
    parts.append(_text(600, cy + 22, "Example: 'The population of NYC is [QA(population NYC)] 8.3M.'",
                       size=14, weight="bold", fill=YELLOW))
    parts.append(_text(600, cy + 50, "Model inserts API calls inline, results replace the call",
                       size=13, fill=MID_TEXT))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 템플릿: Reasoning (Logic-LM) ──────────────────────────────────────

def generate_reasoning_svg(paper_id, title):
    """Logic-LM 다이어그램 생성."""
    parts = [svg_header()]
    title_text, cy = svg_title(title, y=55)
    parts.append(title_text)
    cy += 20

    parts.append(_text(600, cy, "LLM + Symbolic Solver Integration", size=20,
                       weight="bold", fill=BLUE))
    cy += 40

    # Pipeline
    parts.append(_text(600, cy, "Logic-LM Pipeline", size=18, weight="bold"))
    cy += 30

    # Natural Language → LLM → Formal Logic
    steps = [
        ("Natural Language\nProblem", BG_PURPLE, PURPLE),
        ("LLM\n(Problem Formulation)", BG_BLUE, BLUE),
        ("Formal Logic\nRepresentation", BG_ORANGE, ORANGE),
        ("Symbolic Solver\n(Prover/SMT)", BG_GREEN, GREEN),
        ("Answer\nExtraction", BG_RED, RED),
    ]

    sx = 80
    sw = 190
    for i, (sname, bg, color) in enumerate(steps):
        parts.append(_rect(sx, cy, sw, 80, bg, rx=12, stroke=color))
        lines = sname.split("\n")
        for li, ln in enumerate(lines):
            parts.append(_text(sx + sw // 2, cy + 30 + li * 22, ln,
                               size=13, weight="bold", fill=color))
        if i < len(steps) - 1:
            parts.append(_arrow(sx + sw + 3, cy + 40, sx + sw + 20, cy + 40))
        sx += sw + 23

    cy += 100

    # Self-refinement loop
    parts.append(_text(600, cy, "Self-Refinement Module", size=18, weight="bold"))
    cy += 25

    parts.append(_rect(150, cy, 900, 200, BG_LIGHT, rx=16, stroke="#DDD"))

    parts.append(_box_with_text(200, cy + 20, 250, 50, BG_BLUE,
                                "LLM generates logic", BLUE, rx=10, font_size=13))
    parts.append(_arrow(455, cy + 45, 500, cy + 45))
    parts.append(_box_with_text(505, cy + 20, 250, 50, BG_ORANGE,
                                "Solver attempts proof", ORANGE, rx=10, font_size=13))
    parts.append(_arrow(760, cy + 45, 805, cy + 45))

    parts.append(_rect(810, cy + 20, 200, 50, BG_LIGHT, rx=10, stroke=GREEN))
    parts.append(_text(910, cy + 50, "Success?", size=14, weight="bold", fill=GREEN))

    # Error feedback loop
    parts.append(_line(910, cy + 72, 910, cy + 140, RED, dashed=True))
    parts.append(_line(910, cy + 140, 325, cy + 140, RED, dashed=True))
    parts.append(_arrow(325, cy + 140, 325, cy + 72, RED))
    parts.append(_text(600, cy + 160, "Error message fed back to LLM for correction",
                       size=13, fill=RED, weight="bold"))

    parts.append(_text(600, cy + 185, "Iterative refinement until solver succeeds or max retries",
                       size=12, fill=LIGHT_TEXT))

    cy += 220

    # Supported logic types
    parts.append(_text(600, cy, "Supported Formal Logic Types", size=18, weight="bold"))
    cy += 25

    logic_types = [
        ("First-Order Logic", "Quantifiers, predicates", BG_BLUE, BLUE),
        ("Constraint Satisfaction", "Variables, constraints", BG_ORANGE, ORANGE),
        ("SAT/SMT", "Boolean satisfiability", BG_GREEN, GREEN),
        ("Logic Programming", "Prolog-style rules", BG_PURPLE, PURPLE),
    ]
    lx = 110
    lw = 235
    for lname, ldesc, bg, color in logic_types:
        parts.append(_rect(lx, cy, lw, 65, bg, rx=10, stroke=color))
        parts.append(_text(lx + lw // 2, cy + 25, lname, size=13, weight="bold", fill=color))
        parts.append(_text(lx + lw // 2, cy + 48, ldesc, size=11, fill=MID_TEXT))
        lx += lw + 20
    cy += 85

    parts.append(_rect(150, cy, 900, 50, BG_YELLOW, rx=12, stroke=YELLOW))
    parts.append(_text(600, cy + 30, "LLMs translate NL to logic; solvers ensure correctness",
                       size=14, weight="bold", fill=YELLOW))

    parts.append(svg_footer())
    return "\n".join(parts)


# ── 메인 ──────────────────────────────────────────────────────────────

def generate_svg(paper_id, title):
    """논문 ID에 따라 적절한 SVG 생성."""
    group = PAPER_GROUPS.get(paper_id, "prompting")

    if group == "llm" and paper_id in LLM_SPECS:
        return generate_llm_svg(paper_id, title, LLM_SPECS[paper_id])
    elif group == "llm_moe":
        return generate_moe_svg(paper_id, title)
    elif group == "moe":
        return generate_moe_svg(paper_id, title)
    elif group == "rlhf":
        return generate_rlhf_svg(paper_id, title)
    elif group == "attention":
        return generate_attention_svg(paper_id, title)
    elif group == "efficient":
        return generate_efficient_svg(paper_id, title)
    elif group == "scaling":
        return generate_scaling_svg(paper_id, title)
    elif group == "rag":
        return generate_rag_svg(paper_id, title)
    elif group == "ssm":
        return generate_ssm_svg(paper_id, title)
    elif group == "vision":
        return generate_vision_svg(paper_id, title)
    elif group == "prompting":
        return generate_prompting_svg(paper_id, title)
    elif group == "security":
        return generate_security_svg(paper_id, title)
    elif group == "tool":
        return generate_tool_svg(paper_id, title)
    elif group == "reasoning":
        return generate_reasoning_svg(paper_id, title)
    else:
        return generate_prompting_svg(paper_id, title)


def main():
    """57개 논문의 architecture.svg 생성."""
    generated = 0
    errors = []

    for entry in sorted(os.listdir(PAPERS_DIR)):
        # 숫자로 시작하는 폴더만 처리
        if not entry[0].isdigit():
            continue

        paper_dir = PAPERS_DIR / entry
        content_path = paper_dir / "content.json"

        if not content_path.exists():
            print(f"  SKIP {entry}: content.json 없음")
            continue

        try:
            with open(content_path, encoding="utf-8") as f:
                data = json.load(f)

            paper_id = data["id"]
            title = data["title"]

            # figures 디렉토리 생성
            figures_dir = paper_dir / "figures"
            figures_dir.mkdir(exist_ok=True)

            # SVG 생성
            svg_content = generate_svg(paper_id, title)

            # 저장
            svg_path = figures_dir / "architecture.svg"
            svg_path.write_text(svg_content, encoding="utf-8")

            generated += 1
            print(f"  OK  [{paper_id:>2}] {entry} -> {svg_path.name}")

        except Exception as e:
            errors.append((entry, str(e)))
            print(f"  ERR [{entry}] {e}")

    print(f"\n완료: {generated}개 SVG 생성, {len(errors)}개 오류")
    if errors:
        for entry, err in errors:
            print(f"  - {entry}: {err}")


if __name__ == "__main__":
    main()
