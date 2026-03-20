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
You are a technical diagram designer specializing in ML/AI architecture diagrams.
You generate clean, publication-quality SVG code for neural network architecture diagrams.

CRITICAL SVG rules:
1. Output ONLY valid SVG code wrapped in <svg>...</svg> tags. No markdown, no explanation.
2. Use viewBox for scaling (e.g., viewBox="0 0 960 600" for wide format).
3. All text must use font-family="Arial, Helvetica, sans-serif".
4. Use these exact colors:
   - Attention blocks: #4A90D9 (blue)
   - FFN/MLP blocks: #E8833A (orange)
   - Normalization: #5CB85C (green)
   - Embedding/Input: #9B59B6 (purple)
   - Output/Head: #E74C3C (red)
   - Other/misc: #95A5A6 (gray)
   - Background: white (#FFFFFF)
   - Text: #2C3E50 (dark)
   - Arrows/lines: #34495E
5. Use rounded rectangles (rx="6") for blocks.
6. Use marker-end arrows for data flow.
7. Keep labels concise (max 2-3 words per block).
8. Ensure the diagram is readable at 400px width.
9. Add a title text at the top with the model/technique name.
10. Flow direction: bottom-to-top for model architectures, left-to-right for techniques/algorithms."""

MODEL_ARCH_TEMPLATE = """\
Generate an SVG architecture diagram for the {name} model.

Specs: {organization}, {release_date}
- Type: {decoder_type} | Params: {param_scale}
- Layers: {num_layers}, Heads: {num_heads}, Hidden: {hidden_dim}
- Attention: {attention_type} | Norm: {normalization} | Act: {activation}
- Position: {position_encoding}

Key feature: {key_detail_short}

Layout (bottom-to-top):
1. Input Embedding (purple block) at bottom
2. "×N" stack indicator showing N={num_layers} layers
3. One expanded Transformer block showing:
   - {attention_label} (blue)
   - Add & Norm (green)
   - FFN with {activation} (orange)
   - Add & Norm (green)
   - Residual connections (dashed lines around the block)
4. Output Head (red) at top
5. {extra_component}

Title: "{name}" at top. viewBox="0 0 960 600"."""

TECHNIQUE_TEMPLATE = """\
Generate an SVG diagram for the {name} technique.

Specs: {organization}, {release_date}

Description: {description_short}

Key mechanism: {key_detail_short}

Layout (left-to-right):
1. Show the core mechanism as a flow diagram
2. If applicable, show before/after or standard vs. optimized comparison
3. Label key mathematical operations or transformations
4. Show how it relates to a Transformer block

Title: "{name}" at top. viewBox="0 0 960 600"."""

MOE_TEMPLATE = """\
Generate an SVG architecture diagram for the {name} MoE model.

Specs: {organization}, {release_date}
- Params: {param_scale} | Layers: {num_layers}, Heads: {num_heads}, Hidden: {hidden_dim}
- Experts: {num_experts} total, {active_experts} active per token
- Attention: {attention_type} | Act: {activation}

Key feature: {key_detail_short}

Layout (bottom-to-top):
1. Input Embedding (purple) at bottom
2. Attention block (blue)
3. Add & Norm (green)
4. Router/Gating Network (gray) with arrows fanning out to expert blocks
5. Expert FFN blocks (orange, show {num_experts} experts, highlight {active_experts} active)
6. Weighted sum merge point
7. Add & Norm (green)
8. "×{num_layers}" stack indicator
9. Output Head (red) at top

Title: "{name}" at top. viewBox="0 0 960 600"."""

HYBRID_TEMPLATE = """\
Generate an SVG architecture diagram for the {name} hybrid model.

Specs: {organization}, {release_date}
- Params: {param_scale} | Layers: {num_layers}, Heads: {num_heads}, Hidden: {hidden_dim}
- Attention: {attention_type} | Act: {activation}

Key feature: {key_detail_short}

Layout (bottom-to-top):
1. Input Embedding (purple) at bottom
2. Show alternating block types:
   - Attention blocks (blue) for some layers
   - SSM/Mamba blocks (teal #1ABC9C) for other layers
3. If MoE is involved, show expert routing in relevant layers
4. Show the repeating pattern of hybrid blocks
5. Output Head (red) at top

Title: "{name}" at top. viewBox="0 0 960 600"."""

SSM_TEMPLATE = """\
Generate an SVG architecture diagram for the {name} State Space Model.

Specs: {organization}, {release_date}
- Params: {param_scale}

Key feature: {key_detail_short}

Layout (bottom-to-top):
1. Input Sequence (purple) at bottom
2. State Space block (teal #1ABC9C):
   - Show state transition: x(t) → A·x(t) + B·u(t) → y(t) = C·x(t)
   - If selective mechanism exists, show selection/gating component
3. Show the recurrence pattern with a loop arrow
4. If there's a discretization step, show continuous → discrete conversion
5. Output projection (red) at top
6. Show how sequence length scales linearly (vs quadratic for attention)

Use teal (#1ABC9C) as the primary color for SSM blocks.
Title: "{name}" at top. viewBox="0 0 960 600"."""

DIFFUSION_TEMPLATE = """\
Generate an SVG diagram for the {name} diffusion model/technique.

Specs: {organization}, {release_date}
- Params: {param_scale}

Key feature: {key_detail_short}

Layout (left-to-right):
1. Clean Image x₀ on the left
2. Forward Process arrow (adding noise): x₀ → x₁ → ... → xₜ (show progressively noisier images)
3. Pure Noise xₜ in the middle
4. Reverse Process arrow (denoising): xₜ → ... → x₁ → x₀ (show progressively cleaner images)
5. Denoiser Network block below the reverse process:
   - If U-Net: show encoder-decoder with skip connections
   - If DiT: show transformer blocks with conditioning
6. If text-conditioned: show text encoder feeding into denoiser
7. Show the noise schedule or loss function if relevant

Use amber (#F59E0B) as the primary color for diffusion process blocks.
Title: "{name}" at top. viewBox="0 0 960 600"."""

AGENT_TEMPLATE = """\
Generate an SVG diagram for the {name} AI agent architecture/framework.

Specs: {organization}, {release_date}

Key feature: {key_detail_short}

Layout:
1. Central agent loop: Observe → Think → Act → Observe (circular flow)
2. If multi-agent: show multiple agent nodes with communication arrows
3. If tool-using: show tool connections (API, Code, Search, Browser)
4. If protocol: show client-server or agent-agent communication flow
5. Show memory/state management if applicable
6. Show environment interaction

Use lime (#84CC16) as the primary color for agent blocks.
Title: "{name}" at top. viewBox="0 0 960 600"."""

VISION_TEMPLATE = """\
Generate an SVG architecture diagram for the {name} vision model.

Specs: {organization}, {release_date}
- Params: {param_scale}

Key feature: {key_detail_short}

Layout (bottom-to-top):
1. Input Image at bottom
2. If patch-based: show image split into patches with linear embedding
3. Vision Encoder blocks (pink #EC4899):
   - If ViT-based: show transformer blocks with self-attention
   - If hierarchical: show multi-scale feature maps
4. If segmentation: show mask decoder with prompt inputs
5. If detection: show object queries and bipartite matching
6. Output predictions at top

Use pink (#EC4899) as the primary color for vision blocks.
Title: "{name}" at top. viewBox="0 0 960 600"."""

MULTIMODAL_TEMPLATE = """\
Generate an SVG architecture diagram for the {name} multimodal model.

Specs: {organization}, {release_date}
- Params: {param_scale}

Key feature: {key_detail_short}

Layout:
1. Multiple input modalities on the left (image, text, audio if applicable)
2. Each modality has its own encoder:
   - Vision: ViT encoder (pink #EC4899)
   - Text: Transformer encoder (blue #4A90D9)
   - Audio: Whisper-like encoder (green #5CB85C)
3. Fusion mechanism in the center (cross-attention, projection, Q-Former, etc.)
4. LLM backbone (purple #9B59B6)
5. Output on the right (text generation, image generation, etc.)

Use rose (#FB7185) as the primary color for fusion/multimodal blocks.
Title: "{name}" at top. viewBox="0 0 960 600"."""


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
