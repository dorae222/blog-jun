#!/usr/bin/env python3
"""
ML 모듈 코드 블록을 분류하고, 실행/검색 대체를 통해 출력을 생성합니다.

코드 블록 분류:
- execute_figure: matplotlib/seaborn → 실행 필수 (figure 생성)
- execute_print: print/display → 실행
- precompute: 표준 데이터셋 + 표준 메트릭 → 검색 대체 가능
- no_output: import, fit, setup → 스킵

사용법:
    python -m pipeline.generators.ml_outputs --slug ml-overview --classify
    python -m pipeline.generators.ml_outputs --slug ml-overview --execute
    python -m pipeline.generators.ml_outputs --wave 1
    python -m pipeline.generators.ml_outputs --all --classify
"""
import argparse
import io
import json
import re
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ML_DIR = Path("pipeline/data/ml_written")
MEDIA_DIR = Path("backend/media")

# 표준 데이터셋 패턴 (검색 대체 가능)
STANDARD_DATASETS = {
    'load_iris', 'load_wine', 'load_digits', 'load_breast_cancer',
    'load_boston', 'load_diabetes', 'fetch_california_housing',
    'make_classification', 'make_regression', 'make_blobs',
    'make_moons', 'make_circles',
}


def extract_code_blocks(content: str) -> list[dict]:
    """마크다운에서 python 코드 블록 추출."""
    pattern = re.compile(r'```python\s*\n(.*?)```', re.DOTALL)
    blocks = []
    for i, match in enumerate(pattern.finditer(content)):
        blocks.append({
            'index': i,
            'code': match.group(1).strip(),
            'start': match.start(),
            'end': match.end(),
        })
    return blocks


def classify_block(code: str) -> str:
    """코드 블록의 출력 유형 판정."""
    lines = code.strip().split('\n')

    # Figure 생성 감지
    fig_patterns = ['plt.show()', 'plt.savefig(', 'fig.show()', 'fig.savefig(',
                    'sns.heatmap(', 'sns.pairplot(', 'sns.catplot(', 'sns.scatterplot(']
    if any(p in code for p in fig_patterns):
        return 'execute_figure'

    # Print/Display 출력 감지
    if re.search(r'\bprint\s*\(', code) or 'display(' in code:
        # 표준 데이터셋이면 precompute 가능
        if any(ds in code for ds in STANDARD_DATASETS):
            return 'precompute'
        return 'execute_print'

    # 표준 메트릭 + 표준 데이터셋 조합
    std_metrics = ['classification_report', 'confusion_matrix', 'accuracy_score',
                   'mean_squared_error', 'r2_score', 'cross_val_score']
    if any(m in code for m in std_metrics) and any(ds in code for ds in STANDARD_DATASETS):
        return 'precompute'

    # Import, fit, setup만 → 출력 없음
    if all(line.strip().startswith(('import ', 'from ', '#', '')) or
           '.fit(' in line or '= ' in line
           for line in lines if line.strip()):
        return 'no_output'

    return 'no_output'


FONT_PREAMBLE = """\
import matplotlib
matplotlib.rcParams['font.family'] = 'Noto Sans CJK JP'
matplotlib.rcParams['axes.unicode_minus'] = False
"""

def _sanitize_font(code: str) -> str:
    """macOS 전용 폰트를 Linux 호환 폰트로 치환."""
    code = code.replace("AppleGothic", "Noto Sans CJK JP")
    code = code.replace("Malgun Gothic", "Noto Sans CJK JP")
    return code


def execute_block(
    code: str,
    namespace: dict,
    output_dir: Path,
    fig_prefix: str,
    fig_counter: int,
    timeout: int = 60,
) -> dict:
    """코드 블록 실행, stdout과 figure 수집."""
    stdout_capture = io.StringIO()
    figures_saved = []

    # 한글 폰트 강제 설정 + macOS 폰트 치환
    code = _sanitize_font(code)

    # matplotlib figure 자동 저장 설정
    plt.close('all')

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(io.StringIO()):
            exec(FONT_PREAMBLE, namespace)
            exec(code, namespace)

        # 열린 figure 저장
        for i, fig_num in enumerate(plt.get_fignums()):
            fig = plt.figure(fig_num)
            fig_path = output_dir / f"{fig_prefix}_fig_{fig_counter + i}.png"
            fig_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(fig_path, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            figures_saved.append(fig_path.name)
        plt.close('all')

    except Exception as e:
        return {
            'stdout': '',
            'figures': [],
            'error': f"{type(e).__name__}: {e}",
        }

    return {
        'stdout': stdout_capture.getvalue().strip(),
        'figures': figures_saved,
        'error': None,
    }


def inject_outputs(content: str, blocks: list[dict], results: list[dict], slug: str) -> str:
    """코드 블록 뒤에 출력 블록/figure 이미지를 삽입."""
    # 뒤에서부터 삽입 (offset 유지)
    for block, result in reversed(list(zip(blocks, results))):
        if not result:
            continue

        insert_text = ""

        # stdout → ```output 블록
        if result.get('stdout'):
            insert_text += f"\n\n```output\n{result['stdout']}\n```"

        # figure → 이미지 참조
        for fig_name in result.get('figures', []):
            caption = fig_name.replace('.png', '').replace('_', ' ').title()
            insert_text += f"\n\n![{caption}](/media/figures/outputs/{slug}/{fig_name})"

        # error → 주석
        if result.get('error'):
            insert_text += f"\n\n<!-- Execution error: {result['error']} -->"

        if insert_text:
            content = content[:block['end']] + insert_text + content[block['end']:]

    return content


def process_module(slug: str, execute: bool = False, dry_run: bool = False) -> dict:
    """단일 ML 모듈 처리."""
    # 디렉토리 찾기
    module_dir = None
    for d in sorted(ML_DIR.iterdir()):
        if d.is_dir() and (d / "content.json").exists():
            with open(d / "content.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("slug") == slug:
                module_dir = d
                break

    if not module_dir:
        return {"slug": slug, "status": "not_found"}

    with open(module_dir / "content.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    content = data.get("content", "")
    blocks = extract_code_blocks(content)

    # 분류
    classifications = []
    for block in blocks:
        block_type = classify_block(block['code'])
        classifications.append({
            'index': block['index'],
            'type': block_type,
            'code_preview': block['code'][:80].replace('\n', ' '),
        })

    stats = {}
    for c in classifications:
        stats[c['type']] = stats.get(c['type'], 0) + 1

    if not execute:
        return {
            "slug": slug,
            "status": "classified",
            "total_blocks": len(blocks),
            "stats": stats,
            "blocks": classifications,
        }

    # 실행
    output_dir = MEDIA_DIR / "figures" / "outputs" / slug
    namespace = {}
    results = []
    fig_counter = 1

    for block, cls in zip(blocks, classifications):
        if cls['type'] == 'no_output':
            # setup 코드도 namespace에 실행 (변수 공유)
            try:
                exec(_sanitize_font(block['code']), namespace)
            except Exception:
                pass
            results.append(None)
            continue

        if cls['type'] in ('execute_figure', 'execute_print'):
            result = execute_block(
                block['code'], namespace, output_dir,
                slug, fig_counter,
            )
            fig_counter += len(result.get('figures', []))
            results.append(result)
        elif cls['type'] == 'precompute':
            # precompute는 실행도 시도 (성공하면 결과 사용)
            result = execute_block(
                block['code'], namespace, output_dir,
                slug, fig_counter,
            )
            if result.get('error'):
                results.append({'stdout': '<!-- Pre-computed result needed -->', 'figures': [], 'error': None})
            else:
                fig_counter += len(result.get('figures', []))
                results.append(result)
        else:
            results.append(None)

    # 출력 삽입
    if not dry_run:
        updated_content = inject_outputs(content, blocks, results, slug)
        data["content"] = updated_content
        with open(module_dir / "content.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    executed = sum(1 for r in results if r and not r.get('error'))
    errors = sum(1 for r in results if r and r.get('error'))
    figures = sum(len(r.get('figures', [])) for r in results if r)

    return {
        "slug": slug,
        "status": "executed",
        "total_blocks": len(blocks),
        "executed": executed,
        "errors": errors,
        "figures_generated": figures,
        "stats": stats,
    }


# Wave 분류
WAVE_1_SLUGS = [
    "ml-overview", "ml-workflow", "bias-variance-tradeoff",
    "linear-algebra-for-ml", "probability-bayes", "information-theory",
    "optimization-theory", "data-preprocessing", "feature-engineering",
    "imbalanced-data", "linear-regression", "polynomial-regression",
    "regularization", "logistic-regression", "softmax-regression",
    "naive-bayes", "decision-tree", "knn", "svm",
    "random-forest", "gradient-boosting", "xgboost", "lightgbm",
    "catboost", "stacking-blending", "kmeans-clustering",
    "hierarchical-clustering", "dbscan", "pca", "t-sne-umap",
    "cross-validation", "hyperparameter-tuning", "evaluation-metrics",
    "ab-testing", "causal-inference",
]

WAVE_2_SLUGS = [
    "anomaly-detection", "time-series-basics", "arima",
    "recommendation-system", "nlp-basics", "text-preprocessing",
    "word-embedding", "automl", "feature-store",
]

WAVE_3_SLUGS = [
    "bayesian-optimization", "genetic-algorithm", "reinforcement-learning-basics",
    "model-interpretability", "fairness-in-ml", "ml-system-design",
    "mlflow-experiment-tracking",
]


def main():
    parser = argparse.ArgumentParser(description="ML 모듈 코드 블록 분류 및 실행")
    parser.add_argument("--slug", help="단일 모듈 slug")
    parser.add_argument("--classify", action="store_true", help="분류만 (실행 안 함)")
    parser.add_argument("--execute", action="store_true", help="분류 + 실행")
    parser.add_argument("--wave", type=int, choices=[1, 2, 3], help="Wave별 실행")
    parser.add_argument("--all", action="store_true", help="전체 모듈")
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 확인만")
    args = parser.parse_args()

    if args.slug:
        result = process_module(
            args.slug,
            execute=args.execute and not args.classify,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.wave:
        slugs = {1: WAVE_1_SLUGS, 2: WAVE_2_SLUGS, 3: WAVE_3_SLUGS}[args.wave]
        print(f"Wave {args.wave}: {len(slugs)}개 모듈")
        for slug in slugs:
            result = process_module(
                slug,
                execute=args.execute and not args.classify,
                dry_run=args.dry_run,
            )
            status = result.get('status', 'unknown')
            stats = result.get('stats', {})
            print(f"  {slug}: {status} {stats}")

    elif args.all:
        for d in sorted(ML_DIR.iterdir()):
            if d.is_dir() and (d / "content.json").exists():
                with open(d / "content.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                slug = data.get("slug", d.name)
                result = process_module(
                    slug,
                    execute=args.execute and not args.classify,
                    dry_run=args.dry_run,
                )
                status = result.get('status', 'unknown')
                stats = result.get('stats', {})
                print(f"  {slug}: {status} {stats}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
