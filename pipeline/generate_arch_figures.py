#!/usr/bin/env python3
"""
Claude API를 사용한 ArchitectureEntry 다이어그램 SVG 생성 → PNG 변환

Claude가 SVG 코드를 생성하고, cairosvg로 PNG 변환.
장점: 텍스트 100% 정확, 일관된 스타일, 결정적 출력.

사용법:
  python generate_arch_figures.py                        # 전체 생성 (figure 없는 것만)
  python generate_arch_figures.py --slug transformer     # 특정 아키텍처만
  python generate_arch_figures.py --slug transformer --force  # 기존 이미지 덮어쓰기
  python generate_arch_figures.py --dry-run              # 미리보기
  python generate_arch_figures.py --model claude-sonnet-4-6  # 모델 변경
"""
import json
import os
import re
import sys
import time
import argparse
from pathlib import Path

import anthropic
import cairosvg

# ── 설정 ──────────────────────────────────────────────────────────────
ARCH_DIR = Path(__file__).parent / 'data' / 'architectures_written'
DEFAULT_MODEL = 'claude-sonnet-4-6'
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
MAX_RETRIES = 3
RETRY_DELAY = 5  # 초
OUTPUT_WIDTH = 1920  # PNG 출력 너비 (px)


# ── 프롬프트 ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a world-class technical diagram designer specializing in ML/AI architecture diagrams,
inspired by Sebastian Raschka's publication-quality style. You generate detailed, professional
SVG code that looks like diagrams from academic papers and blog posts.

CRITICAL SVG RULES:
1. Output ONLY valid SVG code wrapped in <svg>...</svg> tags. No markdown, no explanation.
2. Use viewBox="0 0 1200 1600" for vertical (model architecture) or "0 0 1600 1000" for horizontal (technique/agent) layouts.
3. Font rules:
   - Title: font-size="42" font-weight="bold" font-family="Arial, Helvetica, sans-serif"
   - Subtitle (specs): font-size="18" font-family="monospace"
   - Block labels: font-size="16" font-weight="bold"
   - Detail text inside blocks: font-size="14"
   - Annotations/numbers outside: font-size="16" font-weight="bold" fill="#E74C3C" (red for key numbers)

DESIGN STYLE (Sebastian Raschka inspired):
4. Main architecture stack: Place in a large rounded rectangle with light blue fill (#D6EAF8) and gray border.
5. Expanded sub-component views: Show 1-2 key internal components (e.g., attention mechanism, SSM block)
   in SEPARATE dotted-border boxes to the RIGHT of the main stack, connected by dotted arrows.
6. Key numbers MUST appear prominently:
   - Parameter count next to the title in bold
   - Vocabulary size, embedding dim, context length as labeled annotations
   - Layer count as "N ×" with a bracket on the left side of the repeating block
   - Number of attention heads, hidden dim inside expanded views
7. Color scheme:
   - Main stack background: #D6EAF8 (light blue)
   - Attention/Self-Attention blocks: #4A90D9 (blue) with white text
   - FFN/MLP blocks: #E8833A (orange) with white text
   - Normalization blocks: #A8D5A2 (light green) with dark text
   - Embedding/Input: #9B59B6 (purple) with white text
   - Output/Head: #E74C3C (red) with white text
   - SSM blocks: #1ABC9C (teal) with white text
   - Gating/Router: #F39C12 (amber) with white text
   - Diffusion process: #F59E0B (amber)
   - Agent blocks: #84CC16 (lime)
   - Vision blocks: #EC4899 (pink) with white text
   - Residual connections: dashed gray lines
   - Sub-component expanded boxes: white fill, dashed #666 border
   - Annotations (key numbers): #E74C3C (red) bold text
8. Block styling:
   - Rounded rectangles with rx="8", clear padding
   - Residual connections shown as "+" circle symbols with bypass arrows
   - Data flow arrows: solid #34495E with proper arrowheads
   - Use "×N" notation with curly brace for repeated layers
9. Layout principles:
   - Bottom-to-top flow for model architectures
   - Left-to-right flow for techniques/pipelines
   - Generous spacing between blocks (at least 20px)
   - Every block must have readable text at 600px display width
   - Show the INTERNAL structure of at least one key component in an expanded view
10. Technical accuracy: Match the actual architecture described. Show correct data flow,
    skip connections, and component relationships."""

MODEL_ARCH_TEMPLATE = """\
Generate a detailed, publication-quality SVG architecture diagram for {name}.

=== SPECIFICATIONS ===
Organization: {organization} | Released: {release_date}
Parameters: {param_scale}
Type: {decoder_type} | Layers: {num_layers} | Heads: {num_heads} | Hidden dim: {hidden_dim}
Attention: {attention_type} | Norm: {normalization} | Activation: {activation}
Position encoding: {position_encoding}

=== KEY INNOVATION ===
{key_detail_short}

=== LAYOUT (Sebastian Raschka style) ===

LEFT SIDE — Main Architecture Stack (inside light blue #D6EAF8 rounded rect):
1. Bottom: "Tokenized text" label → "Token embedding layer" (purple block)
   - Show "Embedding size of {hidden_dim}" as red bold annotation to the left
2. Below the repeating block: show "×{num_layers} Layers" with a curly brace on the left
3. Inside the repeating block (bottom to top):
   - "{normalization}" (light green)
   - "{attention_label}" (blue block, darker shade)
   - "+" residual connection circle
   - "{normalization}" (light green)
   - "FFN" or "MLP" (orange block)
   - "+" residual connection circle
4. Top: "Final {normalization}" → "Linear output layer"
   - Show "Vocabulary size of ..." as annotation at the top

RIGHT SIDE — Expanded View (dotted border box, connected to main stack with dotted arrow):
Show the internal structure of {attention_label}:
- Input splits into Q, K, V via Linear projections
- Show the attention computation: Scaled Dot-Product Attention
- Show the output Linear projection
- Include dimension annotations where known

TITLE: "{name} ({param_scale})" in large bold at the very top.

{extra_component}"""

TECHNIQUE_TEMPLATE = """\
Generate a detailed, publication-quality SVG diagram for the {name} technique.

=== SPECIFICATIONS ===
Organization: {organization} | Released: {release_date}
Description: {description_short}

=== KEY MECHANISM ===
{key_detail_short}

=== LAYOUT ===

Use viewBox="0 0 1600 1000" (horizontal layout).

LEFT SIDE — Standard/Before approach:
- Show the baseline method this technique improves upon
- Label with specific operations and dimensions

CENTER — The {name} technique:
- Show the core mechanism as a detailed flow diagram
- Include mathematical operations (formulas as text)
- Show data dimensions at each step

RIGHT SIDE — Result/Comparison:
- Show the improvement or output
- If applicable: performance comparison or efficiency gains

BOTTOM — Key insight box with dotted border explaining the main innovation.

TITLE: "{name}" in large bold at the top.
Include organization and date as subtitle."""

MOE_TEMPLATE = """\
Generate a detailed, publication-quality SVG architecture diagram for {name} (Mixture of Experts).

=== SPECIFICATIONS ===
Organization: {organization} | Released: {release_date}
Parameters: {param_scale}
Layers: {num_layers} | Heads: {num_heads} | Hidden dim: {hidden_dim}
Experts: {num_experts} total, {active_experts} active per token
Attention: {attention_type} | Activation: {activation}

=== KEY INNOVATION ===
{key_detail_short}

=== LAYOUT (Sebastian Raschka style) ===

LEFT SIDE — Main Architecture Stack (light blue #D6EAF8 background):
1. Bottom: Token embedding (purple)
2. Repeating block with "×{num_layers} Layers" brace:
   - {normalization} (light green)
   - Attention block (blue)
   - "+" residual
   - {normalization} (light green)
   - MoE block (amber #F39C12): Router → fan-out to experts → weighted sum
   - "+" residual
3. Top: Final norm → Linear output

Show annotations: "{num_experts} experts, {active_experts} active" in red bold.

RIGHT SIDE — Expanded MoE Block (dotted border):
- Router/Gating network at top
- Show {num_experts} expert FFN blocks (highlight {active_experts} active ones in orange, rest in gray)
- Arrows from router to selected experts with "Top-{active_experts}" label
- Weighted sum at bottom

TITLE: "{name} ({param_scale})" in large bold."""

HYBRID_TEMPLATE = """\
Generate a detailed, publication-quality SVG architecture diagram for {name} (Hybrid model).

=== SPECIFICATIONS ===
Organization: {organization} | Released: {release_date}
Parameters: {param_scale}
Layers: {num_layers} | Heads: {num_heads} | Hidden dim: {hidden_dim}
Attention: {attention_type} | Activation: {activation}

=== KEY INNOVATION ===
{key_detail_short}

=== LAYOUT (Sebastian Raschka style) ===

LEFT SIDE — Main Architecture Stack (light blue background):
1. Bottom: Token embedding (purple)
2. Show the ALTERNATING layer pattern explicitly:
   - Attention layers (blue blocks)
   - SSM/Linear attention layers (teal #1ABC9C blocks)
   - If MoE: show expert routing in relevant layers
3. Show the ratio pattern at the BOTTOM RIGHT in a table-like box:
   "Layer 1: Linear attention → MoE"
   "Layer 2: Linear attention → MoE"
   "Layer N: Full attention → MoE"
4. Top: Final norm → Linear output

RIGHT SIDE — Expanded views (dotted borders):
- Show one Attention block detail
- Show one SSM/Linear block detail
- Connected to main stack with dotted arrows

TITLE: "{name} ({param_scale})" in large bold.
Show key numbers as red bold annotations."""

SSM_TEMPLATE = """\
Generate a detailed, publication-quality SVG architecture diagram for {name} (State Space Model).

=== SPECIFICATIONS ===
Organization: {organization} | Released: {release_date}
Parameters: {param_scale}

=== KEY INNOVATION ===
{key_detail_short}

=== LAYOUT (Sebastian Raschka style) ===

LEFT SIDE — Main Architecture Stack (light blue background):
1. Bottom: "Tokenized text" → "Token embedding layer" (purple)
   - Annotation: embedding dimension in red bold
2. Repeating block with "×N Layers" brace:
   - RMSNorm (light green)
   - SSM Block (teal #1ABC9C, darker shade)
   - "+" residual connection
   - RMSNorm (light green)
   - MLP/FFN (orange)
   - "+" residual connection
3. Top: Final norm → Linear output

RIGHT SIDE — Expanded SSM Block (dotted border):
Show the INTERNAL structure:
- Input x → Linear projections
- Conv1d (if applicable, red/coral block)
- σ activation
- Show state equation: x(t) = Ax(t-1) + Bu(t), y(t) = Cx(t)
- If selective: show Δ, B, C as input-dependent (arrows from input)
- Multiplicative gate (×) with SiLU
- Linear output projection

Show "Linear Complexity O(n)" vs "Attention O(n²)" comparison annotation.

TITLE: "{name} ({param_scale})" in large bold.
Use teal (#1ABC9C) as primary color for SSM-specific blocks."""

DIFFUSION_TEMPLATE = """\
Generate a detailed, publication-quality SVG diagram for {name} (Diffusion Model).

=== SPECIFICATIONS ===
Organization: {organization} | Released: {release_date}
Parameters: {param_scale}

=== KEY INNOVATION ===
{key_detail_short}

=== LAYOUT (Sebastian Raschka style) ===
Use viewBox="0 0 1600 1200".

TOP SECTION — Diffusion Process (horizontal flow):
- Left: Clean image x₀ (show as a small image placeholder with border)
- Forward process arrows with "Add noise" label: x₀ → x₁ → ... → xₜ
  (show 4-5 stages with progressively noisier placeholder squares)
- Center: Pure noise xₜ
- Reverse process arrows with "Denoise" label: xₜ → ... → x₀
  (show progressively cleaner stages)

BOTTOM LEFT — Denoiser Network (light blue background box):
- If U-Net based: Show encoder-decoder with skip connections
  - Encoder: progressively smaller blocks (downsampling)
  - Bottleneck
  - Decoder: progressively larger blocks (upsampling)
  - Skip connections as horizontal arrows
- If DiT based: Show transformer blocks with adaptive norm

BOTTOM RIGHT — Conditioning (dotted border expanded view):
- Text encoder (if text-conditioned): CLIP/T5 → text embeddings
- Cross-attention mechanism connecting text to denoiser
- Timestep embedding
- Show how conditioning enters the denoiser

Use amber (#F59E0B) for diffusion process blocks, blue (#4A90D9) for attention.
TITLE: "{name} ({param_scale})" in large bold."""

AGENT_TEMPLATE = """\
Generate a detailed, publication-quality SVG diagram for {name} (AI Agent/Framework).

=== SPECIFICATIONS ===
Organization: {organization} | Released: {release_date}

=== KEY INNOVATION ===
{key_detail_short}

=== LAYOUT (Sebastian Raschka style) ===
Use viewBox="0 0 1600 1000" (horizontal).

LEFT — Agent Core (light green #E8F5E9 background box):
- User/Orchestrator at top
- Agent Core: Observe → Think → Act loop (show as circular flow)
- Memory/State store below

CENTER — Communication Layer (white box with dotted border):
- If protocol: show message format, transport layer
- If tool-use: show tool connections (API, Code, Search, Browser)
- Show the specific protocol/API (REST, JSON-RPC, SSE etc.)

RIGHT — External Components:
- If multi-agent: show Remote Agent with its own core
- If tool-using: show tool icons/blocks
- Environment/User interaction

BOTTOM — Key features table or lifecycle diagram in a boxed section.

Use lime (#84CC16) for agent blocks, blue (#4A90D9) for communication,
orange (#E8833A) for tools.
TITLE: "{name}" in large bold."""

VISION_TEMPLATE = """\
Generate a detailed, publication-quality SVG architecture diagram for {name} (Vision Model).

=== SPECIFICATIONS ===
Organization: {organization} | Released: {release_date}
Parameters: {param_scale}

=== KEY INNOVATION ===
{key_detail_short}

=== LAYOUT (Sebastian Raschka style) ===

LEFT SIDE — Input Processing:
- Show input image being split into patches (grid overlay on image)
- Linear embedding / patch projection
- Show patch size and resulting sequence length as annotations

CENTER — Main Vision Stack (light pink #FDE8EF background):
- Patch embedding (purple)
- If ViT: transformer blocks with self-attention
- If hierarchical: show multi-scale stages with decreasing resolution
- Show "×N Layers" with brace
- CLS token or global pooling at top

RIGHT SIDE — Expanded View (dotted border):
- Show internal structure of key block (attention, etc.)
- If segmentation: show mask decoder + prompt encoder
- If detection: show object queries

TITLE: "{name} ({param_scale})" in large bold.
Use pink (#EC4899) for vision-specific blocks."""

MULTIMODAL_TEMPLATE = """\
Generate a detailed, publication-quality SVG architecture diagram for {name} (Multimodal Model).

=== SPECIFICATIONS ===
Organization: {organization} | Released: {release_date}
Parameters: {param_scale}

=== KEY INNOVATION ===
{key_detail_short}

=== LAYOUT (Sebastian Raschka style) ===
Use viewBox="0 0 1600 1200".

LEFT — Input Modalities (separate boxes for each):
- Image input → Vision Encoder (pink #EC4899 background box)
  - Show ViT/CNN architecture briefly
  - Output: visual tokens/features
- Text input → Text Tokenizer
  - Show token sequence

CENTER — Fusion Mechanism (rose #FB7185 background box with dotted border):
- If cross-attention: show Q from one modality, K/V from another
- If projection: show linear projection layer
- If Q-Former: show learnable queries + cross-attention
- Label the specific fusion method used

RIGHT — LLM Backbone (light blue background):
- Show transformer decoder blocks
- Show how visual tokens are integrated (prepended, interleaved, etc.)
- Output: generated text/response

BOTTOM — Training stages if multi-stage (e.g., Stage 1: Alignment, Stage 2: Instruction tuning)

TITLE: "{name} ({param_scale})" in large bold.
Show key numbers (visual tokens, text tokens, etc.) as red bold annotations."""


def classify_architecture(data: dict) -> str:
    """아키텍처 유형 분류"""
    category = data.get('architecture_category', '')
    decoder_type = data.get('decoder_type', '')
    param_scale = data.get('param_scale', '').lower()

    # 카테고리 기반 분류 (우선)
    if category == 'agent':
        return 'agent'
    if category == 'ssm' or decoder_type == 'ssm':
        return 'ssm'
    if category == 'diffusion' or decoder_type in ('diffusion_unet', 'diffusion_dit'):
        return 'diffusion'
    if category == 'vision' or decoder_type == 'vision_encoder':
        return 'vision'
    if category == 'multimodal' or decoder_type == 'multimodal':
        return 'multimodal'

    # 기존 분류 로직
    if decoder_type == 'technique' or category == 'technique':
        return 'technique'
    if 'n/a' in param_scale and ('알고리즘' in param_scale or '방법' in param_scale
                                  or '파인튜닝' in param_scale):
        return 'technique'
    if decoder_type == 'sparse_moe':
        return 'moe'
    if decoder_type in ('sparse_hybrid', 'hybrid_ssm'):
        return 'hybrid'
    return 'model'


def get_attention_label(data: dict) -> str:
    """어텐션 메커니즘 라벨"""
    attn = data.get('attention_type', '')
    if 'GQA' in attn:
        return 'Grouped Query Attention (GQA)'
    if 'MQA' in attn:
        return 'Multi-Query Attention (MQA)'
    if 'MHA' in attn:
        return 'Multi-Head Attention (MHA)'
    if 'MLA' in attn:
        return 'Multi-Head Latent Attention (MLA)'
    return attn or 'Self-Attention'


def get_extra_component(data: dict) -> str:
    """아키텍처 고유 추가 컴포넌트"""
    slug = data.get('slug', '')
    extras = {
        'transformer': 'Show both Encoder and Decoder stacks side by side with cross-attention between them.',
        'bert': 'Show [CLS] token and bidirectional arrows. MLM + NSP heads at output.',
        'vit': 'Show image being split into patches at input, linear projection before embedding.',
        'llava': 'Show Vision Encoder (ViT) on left feeding into a projection layer, then into the LLM decoder.',
        'instructgpt': 'Show 3-stage pipeline: SFT → Reward Model → PPO, side by side.',
        'chinchilla': 'Show scaling law curve: compute budget vs model size vs data size trade-off.',
        'mamba': 'Replace attention block with Selective SSM block (teal #1ABC9C). Show selection mechanism.',
    }
    return extras.get(slug, 'No extra components needed.')


def truncate(text: str, max_len: int = 200) -> str:
    """텍스트를 max_len으로 잘라내기"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + '...'


def build_prompt(data: dict) -> str:
    """아키텍처 데이터로 프롬프트 구성"""
    arch_type = classify_architecture(data)

    common = {
        'name': data.get('name', ''),
        'organization': data.get('organization', ''),
        'release_date': data.get('release_date', ''),
        'param_scale': data.get('param_scale', ''),
        'num_layers': data.get('num_layers', 'N/A'),
        'num_heads': data.get('num_heads', 'N/A'),
        'hidden_dim': data.get('hidden_dim', 'N/A'),
        'attention_type': data.get('attention_type', ''),
        'normalization': data.get('normalization', ''),
        'activation': data.get('activation', ''),
        'position_encoding': data.get('position_encoding', ''),
        'description_short': truncate(data.get('description', ''), 200),
        'key_detail_short': truncate(data.get('key_detail', ''), 250),
        'decoder_type': data.get('decoder_type', ''),
        'num_experts': data.get('num_experts', 'N/A'),
        'active_experts': data.get('active_experts', 'N/A'),
        'attention_label': get_attention_label(data),
        'extra_component': get_extra_component(data),
    }

    templates = {
        'technique': TECHNIQUE_TEMPLATE,
        'moe': MOE_TEMPLATE,
        'hybrid': HYBRID_TEMPLATE,
        'model': MODEL_ARCH_TEMPLATE,
        'ssm': SSM_TEMPLATE,
        'diffusion': DIFFUSION_TEMPLATE,
        'agent': AGENT_TEMPLATE,
        'vision': VISION_TEMPLATE,
        'multimodal': MULTIMODAL_TEMPLATE,
    }

    return templates[arch_type].format(**common)


def extract_svg(text: str) -> str | None:
    """응답 텍스트에서 SVG 코드 추출"""
    # ```svg ... ``` 블록
    match = re.search(r'```(?:svg|xml)?\s*\n(.*?)```', text, re.DOTALL)
    if match:
        svg = match.group(1).strip()
        if svg.startswith('<svg'):
            return svg

    # <svg ... </svg> 직접 매칭
    match = re.search(r'(<svg[\s\S]*?</svg>)', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return None


def generate_figure(client, model: str, prompt: str, output_path: Path) -> bool:
    """Claude API로 SVG 생성 → PNG 변환 후 저장"""
    svg_path = output_path.with_suffix('.svg')

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text
            svg_code = extract_svg(text)

            if not svg_code:
                print(f"      [WARN] SVG 추출 실패 (시도 {attempt}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                continue

            # SVG 저장
            output_path.parent.mkdir(parents=True, exist_ok=True)
            svg_path.write_text(svg_code, encoding='utf-8')

            # SVG → PNG 변환
            cairosvg.svg2png(
                bytestring=svg_code.encode('utf-8'),
                write_to=str(output_path),
                output_width=OUTPUT_WIDTH,
                background_color='white',
            )
            return True

        except anthropic.RateLimitError:
            wait = RETRY_DELAY * attempt * 2
            print(f"      [RATE] 레이트 리밋, {wait}초 대기 (시도 {attempt}/{MAX_RETRIES})")
            time.sleep(wait)

        except Exception as e:
            print(f"      [ERROR] 시도 {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return False


def main():
    parser = argparse.ArgumentParser(description='Claude API 기반 아키텍처 다이어그램 생성 (SVG→PNG)')
    parser.add_argument('--slug', type=str, help='특정 아키텍처 slug만 생성')
    parser.add_argument('--force', action='store_true', help='기존 이미지 덮어쓰기')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL,
                        help=f'Claude 모델 (기본: {DEFAULT_MODEL})')
    args = parser.parse_args()

    # API 클라이언트 초기화
    api_key = os.environ.get('ANTHROPIC_API_KEY', API_KEY)
    client = None
    if not args.dry_run:
        client = anthropic.Anthropic(api_key=api_key)

    # 대상 디렉토리 수집
    if args.slug:
        slugs = [s.strip() for s in args.slug.split(',')]
        dirs = [ARCH_DIR / s for s in slugs]
        for d in dirs:
            if not d.exists():
                print(f"디렉토리 없음: {d}")
                sys.exit(1)
    else:
        dirs = sorted(d for d in ARCH_DIR.iterdir() if d.is_dir())

    total = len(dirs)
    generated = 0
    skipped = 0
    failed = 0

    print(f"대상 아키텍처: {total}개 (모델: {args.model})")
    print("=" * 60)

    for i, arch_dir in enumerate(dirs, 1):
        entry_json = arch_dir / 'entry.json'
        if not entry_json.exists():
            print(f"  [{i}/{total}] [SKIP] entry.json 없음: {arch_dir.name}")
            skipped += 1
            continue

        with open(entry_json, encoding='utf-8') as f:
            data = json.load(f)

        name = data.get('name', arch_dir.name)
        slug = arch_dir.name
        arch_type = classify_architecture(data)
        output_path = arch_dir / 'figures' / 'architecture.png'

        # 기존 이미지 체크
        if output_path.exists() and not args.force:
            print(f"  [{i}/{total}] [SKIP] 이미 존재: {slug}")
            skipped += 1
            continue

        prompt = build_prompt(data)

        if args.dry_run:
            print(f"  [{i}/{total}] [DRY-RUN] {name} (type={arch_type})")
            print(f"    출력: {output_path}")
            print(f"    프롬프트 길이: {len(prompt)}자")
            continue

        print(f"  [{i}/{total}] [GENERATE] {name} (type={arch_type})...")
        success = generate_figure(client, args.model, prompt, output_path)

        if success:
            generated += 1
            size_kb = output_path.stat().st_size / 1024
            print(f"    -> 저장: {output_path.name} ({size_kb:.0f}KB)")
        else:
            failed += 1
            print(f"    -> [FAIL] 생성 실패: {slug}")

        # API 레이트 리밋 방지
        if i < total:
            time.sleep(1)

    print("=" * 60)
    print(f"완료: 생성 {generated}개, 스킵 {skipped}개, 실패 {failed}개")


if __name__ == '__main__':
    main()
