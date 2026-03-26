#!/usr/bin/env python3
"""
ML 교육용 포스트를 위한 matplotlib/scikit-learn 시각화 Figure 자동 생성 스크립트.

46개 ML 포스트 각각에 대해 2~4개의 교육용 시각화를 생성하여
pipeline/data/ml_written/{slug}/figures/ 에 저장한다.

Usage:
    # 전체 생성
    python pipeline/generate_ml_figures.py

    # 특정 포스트만
    python pipeline/generate_ml_figures.py --slug 01_ml-overview

    # 특정 그룹만
    python pipeline/generate_ml_figures.py --group 1

    # 건너뛸 포스트 지정
    python pipeline/generate_ml_figures.py --skip-existing

Requirements (ml-sandbox):
    Python 3.12, numpy, scipy, scikit-learn, pandas, matplotlib, seaborn
"""
import argparse
import os
import sys
import traceback
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # 서버 환경: GUI 없이 렌더링

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.collections import PatchCollection
import numpy as np
import seaborn as sns

# ── 전역 설정 ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": ["DejaVu Sans", "Malgun Gothic", "NanumGothic",
                     "AppleGothic", "sans-serif"],
    "axes.unicode_minus": False,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.3,
})
sns.set_style("whitegrid")

BASE_DIR = Path(__file__).resolve().parent
ML_DIR = BASE_DIR / "data" / "ml_written"

# ── 색상 팔레트 ──────────────────────────────────────────────────────────
COLORS = {
    "primary": "#4A90D9",
    "secondary": "#E8833A",
    "success": "#27AE60",
    "danger": "#E74C3C",
    "warning": "#F39C12",
    "purple": "#9B59B6",
    "teal": "#1ABC9C",
    "dark": "#2C3E50",
    "light": "#ECF0F1",
    "blue_light": "#5DADE2",
    "pink": "#E91E63",
}
PALETTE = list(COLORS.values())


# ═══════════════════════════════════════════════════════════════════════════
# 유틸리티 함수
# ═══════════════════════════════════════════════════════════════════════════

def save_fig(fig, slug: str, filename: str):
    """Figure를 지정 경로에 저장하고 닫는다."""
    out_dir = ML_DIR / slug / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    fig.savefig(path)
    plt.close(fig)
    print(f"    ✓ {path.relative_to(ML_DIR)}")


def make_fig(w=10, h=6):
    """기본 figure 생성."""
    return plt.subplots(figsize=(w, h))


def make_fig_axes(nrows=1, ncols=2, w=12, h=6, **kwargs):
    """여러 서브플롯 생성."""
    fig, axes = plt.subplots(nrows, ncols, figsize=(w, h), **kwargs)
    return fig, axes


# ═══════════════════════════════════════════════════════════════════════════
# Group 1: Fundamentals (01–07)
# ═══════════════════════════════════════════════════════════════════════════

def gen_01_ml_overview():
    slug = "01_ml-overview"

    # Figure 1: ML 유형 벤 다이어그램
    fig, ax = make_fig(10, 8)
    ax.set_xlim(-3, 3)
    ax.set_ylim(-2.5, 3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("머신러닝의 주요 유형", fontsize=18, fontweight="bold", pad=20)

    # 세 원
    colors_rgb = [(*matplotlib.colors.to_rgb(COLORS["primary"]), 0.3),
                  (*matplotlib.colors.to_rgb(COLORS["secondary"]), 0.3),
                  (*matplotlib.colors.to_rgb(COLORS["success"]), 0.3)]
    centers = [(-0.8, 0.5), (0.8, 0.5), (0, -0.8)]
    labels = ["지도 학습\n(Supervised)", "비지도 학습\n(Unsupervised)", "강화 학습\n(Reinforcement)"]
    sublabels = [
        "회귀, 분류\nSVM, 트리, 앙상블",
        "클러스터링, 차원축소\nK-means, PCA, t-SNE",
        "정책 학습, Q-learning\n보상 최적화"
    ]

    for i, (c, lbl, sub) in enumerate(zip(centers, labels, sublabels)):
        circle = plt.Circle(c, 1.5, color=colors_rgb[i], ec=PALETTE[i],
                            linewidth=2.5)
        ax.add_patch(circle)
        ax.text(c[0], c[1] + 0.3, lbl, ha="center", va="center",
                fontsize=14, fontweight="bold", color=COLORS["dark"])
        ax.text(c[0], c[1] - 0.4, sub, ha="center", va="center",
                fontsize=9, color="#555", style="italic")

    ax.text(0, 1.8, "ML", ha="center", va="center",
            fontsize=11, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="#FEF9E7", ec=COLORS["warning"]))
    save_fig(fig, slug, "ml_types_venn.png")

    # Figure 2: 모델 복잡도 vs 오차 곡선
    fig, ax = make_fig(10, 6)
    x = np.linspace(1, 10, 100)
    train_err = 0.5 * np.exp(-0.5 * x) + 0.02
    test_err = 0.1 * (x - 4) ** 2 / 10 + 0.08
    total_err = train_err * 0.3 + test_err * 0.7

    ax.plot(x, train_err, color=COLORS["primary"], lw=2.5, label="훈련 오차")
    ax.plot(x, test_err, color=COLORS["danger"], lw=2.5, label="테스트 오차")
    ax.fill_between(x, train_err, test_err, alpha=0.1, color=COLORS["secondary"])

    opt_idx = np.argmin(test_err)
    ax.axvline(x[opt_idx], ls="--", color=COLORS["success"], lw=1.5, alpha=0.7)
    ax.annotate("최적 복잡도", xy=(x[opt_idx], test_err[opt_idx]),
                xytext=(x[opt_idx] + 1.5, test_err[opt_idx] + 0.15),
                fontsize=12, fontweight="bold", color=COLORS["success"],
                arrowprops=dict(arrowstyle="->", color=COLORS["success"]))

    ax.text(2, 0.35, "과소적합\n(Underfitting)", ha="center", fontsize=11,
            color=COLORS["warning"], fontweight="bold")
    ax.text(8.5, 0.35, "과대적합\n(Overfitting)", ha="center", fontsize=11,
            color=COLORS["danger"], fontweight="bold")

    ax.set_xlabel("모델 복잡도", fontsize=13)
    ax.set_ylabel("오차 (Error)", fontsize=13)
    ax.set_title("모델 복잡도와 오차의 관계", fontsize=16, fontweight="bold")
    ax.legend(fontsize=12, loc="upper right")
    ax.set_xlim(1, 10)
    ax.set_ylim(0, 0.5)
    save_fig(fig, slug, "complexity_vs_error.png")


def gen_02_ml_workflow():
    slug = "02_ml-workflow"

    # Figure 1: ML 파이프라인 플로우차트
    fig, ax = make_fig(12, 6)
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-1, 3)
    ax.axis("off")
    ax.set_title("머신러닝 파이프라인", fontsize=18, fontweight="bold", pad=20)

    steps = [
        ("데이터 수집", COLORS["primary"]),
        ("데이터 전처리", COLORS["blue_light"]),
        ("특성 공학", COLORS["teal"]),
        ("모델 선택", COLORS["success"]),
        ("모델 훈련", COLORS["secondary"]),
        ("모델 평가", COLORS["purple"]),
        ("배포", COLORS["danger"]),
    ]

    for i, (label, color) in enumerate(steps):
        x = i * 1.5 + 0.5
        box = FancyBboxPatch((x - 0.55, 0.5), 1.1, 1.0,
                             boxstyle="round,pad=0.15",
                             facecolor=color, edgecolor="white",
                             alpha=0.85, linewidth=2)
        ax.add_patch(box)
        ax.text(x, 1.0, label, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")

        if i < len(steps) - 1:
            ax.annotate("", xy=(x + 0.75, 1.0), xytext=(x + 0.55, 1.0),
                        arrowprops=dict(arrowstyle="->", color="#666",
                                        lw=2, connectionstyle="arc3"))

    # 피드백 루프 화살표
    ax.annotate("피드백 루프",
                xy=(2.0, 0.5), xytext=(8.0, 0.5),
                fontsize=10, color="#888", ha="center",
                arrowprops=dict(arrowstyle="->", color="#aaa", lw=1.5,
                                connectionstyle="arc3,rad=0.4"))
    save_fig(fig, slug, "ml_pipeline_flowchart.png")

    # Figure 2: Train/Val/Test 분할 시각화
    fig, ax = make_fig(10, 4)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")
    ax.set_title("데이터 분할 전략", fontsize=16, fontweight="bold", pad=15)

    # 전체 데이터 바
    bar_y = 2.0
    ax.barh(bar_y, 10, height=0.6, color=COLORS["light"], edgecolor="#999")
    ax.barh(bar_y, 6, height=0.6, color=COLORS["primary"], alpha=0.8, edgecolor="#999")
    ax.barh(bar_y, 2, left=6, height=0.6, color=COLORS["secondary"], alpha=0.8, edgecolor="#999")
    ax.barh(bar_y, 2, left=8, height=0.6, color=COLORS["danger"], alpha=0.8, edgecolor="#999")

    ax.text(3, bar_y, "훈련 세트 (60%)", ha="center", va="center", fontsize=12,
            fontweight="bold", color="white")
    ax.text(7, bar_y, "검증 (20%)", ha="center", va="center", fontsize=11,
            fontweight="bold", color="white")
    ax.text(9, bar_y, "테스트 (20%)", ha="center", va="center", fontsize=11,
            fontweight="bold", color="white")

    # K-fold 시각화
    bar_y2 = 0.8
    ax.text(-0.3, bar_y2, "5-Fold\nCV", ha="right", va="center", fontsize=10,
            fontweight="bold", color=COLORS["dark"])
    for fold in range(5):
        for k in range(5):
            x_start = k * 1.6 + 0.2
            c = COLORS["secondary"] if k == fold else COLORS["primary"]
            a = 0.9 if k == fold else 0.6
            ax.barh(bar_y2 - fold * 0.0, 1.4, left=x_start, height=0.25,
                    color=c, alpha=a, edgecolor="white", linewidth=0.5)

    ax.text(9.5, bar_y2, "Val\nFold", ha="center", va="center", fontsize=8,
            color=COLORS["secondary"], fontweight="bold")
    save_fig(fig, slug, "train_val_test_split.png")


def gen_03_bias_variance():
    slug = "03_bias-variance-tradeoff"

    # Figure 1: Bias-Variance 분해 곡선
    fig, ax = make_fig(10, 6)
    complexity = np.linspace(0, 10, 200)
    bias2 = 3.0 * np.exp(-0.4 * complexity)
    variance = 0.05 * complexity ** 2
    noise = np.full_like(complexity, 0.3)
    total = bias2 + variance + noise

    ax.plot(complexity, bias2, color=COLORS["primary"], lw=2.5,
            label="편향² (Bias²)")
    ax.plot(complexity, variance, color=COLORS["danger"], lw=2.5,
            label="분산 (Variance)")
    ax.plot(complexity, noise, color="#aaa", lw=1.5, ls="--",
            label="노이즈 (Irreducible)")
    ax.plot(complexity, total, color=COLORS["dark"], lw=3,
            label="총 오차 (Total Error)")

    opt_idx = np.argmin(total)
    ax.axvline(complexity[opt_idx], ls=":", color=COLORS["success"],
               lw=2, alpha=0.7)
    ax.scatter([complexity[opt_idx]], [total[opt_idx]], s=100, c=COLORS["success"],
               zorder=5, edgecolors="white", linewidth=2)
    ax.annotate("최적 복잡도", xy=(complexity[opt_idx], total[opt_idx]),
                xytext=(complexity[opt_idx] + 1.5, total[opt_idx] + 0.5),
                fontsize=12, color=COLORS["success"], fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=COLORS["success"]))

    ax.set_xlabel("모델 복잡도", fontsize=13)
    ax.set_ylabel("오차", fontsize=13)
    ax.set_title("편향-분산 분해 (Bias-Variance Decomposition)", fontsize=16,
                 fontweight="bold")
    ax.legend(fontsize=11, loc="upper center")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    save_fig(fig, slug, "bias_variance_decomposition.png")

    # Figure 2: 과소적합 / 적절 / 과대적합 비교
    np.random.seed(42)
    x = np.linspace(0, 1, 30)
    y_true = np.sin(2 * np.pi * x)
    y = y_true + np.random.randn(len(x)) * 0.3

    fig, axes = make_fig_axes(1, 3, 15, 5)
    titles = ["과소적합 (Underfitting)\ndegree=1",
              "적절한 적합 (Good Fit)\ndegree=4",
              "과대적합 (Overfitting)\ndegree=15"]
    degrees = [1, 4, 15]
    colors_fit = [COLORS["warning"], COLORS["success"], COLORS["danger"]]

    for ax, title, deg, c in zip(axes, titles, degrees, colors_fit):
        ax.scatter(x, y, c=COLORS["primary"], s=30, alpha=0.7, edgecolors="white",
                   label="데이터")
        coeffs = np.polyfit(x, y, deg)
        x_smooth = np.linspace(0, 1, 200)
        y_smooth = np.polyval(coeffs, x_smooth)
        ax.plot(x_smooth, y_smooth, color=c, lw=2.5, label=f"다항식 (deg={deg})")
        ax.plot(x_smooth, np.sin(2 * np.pi * x_smooth), "--", color="#aaa",
                lw=1, label="실제 함수")
        ax.set_title(title, fontsize=13, fontweight="bold", color=c)
        ax.legend(fontsize=8, loc="lower left")
        ax.set_ylim(-2, 2)

    fig.suptitle("모델 복잡도에 따른 적합 비교", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "underfit_vs_overfit.png")


def gen_04_linear_algebra():
    slug = "04_linear-algebra-for-ml"

    # Figure 1: 벡터 공간 시각화
    fig, axes = make_fig_axes(1, 2, 12, 6)

    # 2D 벡터 연산
    ax = axes[0]
    ax.set_xlim(-1, 5)
    ax.set_ylim(-1, 5)
    ax.set_aspect("equal")
    origin = np.array([0, 0])
    v1 = np.array([3, 1])
    v2 = np.array([1, 3])
    v_sum = v1 + v2

    ax.quiver(*origin, *v1, angles="xy", scale_units="xy", scale=1,
              color=COLORS["primary"], width=0.02, label="v₁ = (3, 1)")
    ax.quiver(*origin, *v2, angles="xy", scale_units="xy", scale=1,
              color=COLORS["danger"], width=0.02, label="v₂ = (1, 3)")
    ax.quiver(*origin, *v_sum, angles="xy", scale_units="xy", scale=1,
              color=COLORS["success"], width=0.025, label="v₁+v₂ = (4, 4)")

    # 평행사변형
    ax.plot([v1[0], v_sum[0]], [v1[1], v_sum[1]], "--", color="#aaa", lw=1)
    ax.plot([v2[0], v_sum[0]], [v2[1], v_sum[1]], "--", color="#aaa", lw=1)

    ax.set_title("벡터 덧셈과 평행사변형 법칙", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # 고유값 분해 시각화
    ax = axes[1]
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.set_aspect("equal")

    A = np.array([[2, 1], [1, 2]])
    eigenvalues, eigenvectors = np.linalg.eig(A)

    theta = np.linspace(0, 2 * np.pi, 100)
    circle_x = np.cos(theta)
    circle_y = np.sin(theta)
    circle = np.stack([circle_x, circle_y])
    ellipse = A @ circle

    ax.plot(circle_x, circle_y, color="#aaa", lw=1.5, ls="--",
            label="단위원", alpha=0.5)
    ax.plot(ellipse[0], ellipse[1], color=COLORS["purple"], lw=2,
            label="변환 후")

    for i, (val, vec) in enumerate(zip(eigenvalues, eigenvectors.T)):
        c = COLORS["primary"] if i == 0 else COLORS["danger"]
        ax.quiver(0, 0, vec[0] * val, vec[1] * val, angles="xy",
                  scale_units="xy", scale=1, color=c, width=0.02,
                  label=f"λ{i+1}={val:.1f}, v{i+1}=({vec[0]:.2f}, {vec[1]:.2f})")

    ax.set_title("고유값 분해 (Eigendecomposition)", fontsize=13, fontweight="bold")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(True, alpha=0.3)

    fig.suptitle("선형대수학 핵심 개념", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "vector_space_eigen.png")

    # Figure 2: 행렬 변환 효과
    fig, axes = make_fig_axes(1, 3, 15, 5)
    transforms = [
        ("스케일링", np.array([[2, 0], [0, 0.5]])),
        ("회전 (45°)", np.array([[np.cos(np.pi/4), -np.sin(np.pi/4)],
                                 [np.sin(np.pi/4), np.cos(np.pi/4)]])),
        ("전단 (Shear)", np.array([[1, 1], [0, 1]])),
    ]

    square = np.array([[0, 1, 1, 0, 0], [0, 0, 1, 1, 0]])
    for ax, (name, mat) in zip(axes, transforms):
        ax.set_xlim(-2, 3)
        ax.set_ylim(-1.5, 2.5)
        ax.set_aspect("equal")
        ax.plot(square[0], square[1], "--", color="#aaa", lw=1.5, label="원본")
        transformed = mat @ square
        ax.fill(transformed[0], transformed[1], alpha=0.3, color=COLORS["primary"])
        ax.plot(transformed[0], transformed[1], color=COLORS["primary"], lw=2,
                label="변환 후")
        ax.set_title(name, fontsize=13, fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    fig.suptitle("선형 변환의 기하학적 효과", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "matrix_transformations.png")


def gen_05_probability_bayes():
    slug = "05_probability-bayes"

    # Figure 1: 베이즈 정리 시각화
    fig, axes = make_fig_axes(1, 3, 15, 5)

    x = np.linspace(-5, 10, 300)

    # Prior
    from scipy import stats
    prior = stats.norm.pdf(x, loc=2, scale=2)
    likelihood = stats.norm.pdf(x, loc=5, scale=1.5)
    posterior_unnorm = prior * likelihood
    posterior = posterior_unnorm / np.trapz(posterior_unnorm, x)

    axes[0].fill_between(x, prior, alpha=0.4, color=COLORS["primary"])
    axes[0].plot(x, prior, color=COLORS["primary"], lw=2)
    axes[0].set_title("사전 분포 (Prior)", fontsize=13, fontweight="bold")
    axes[0].set_ylabel("확률 밀도", fontsize=11)

    axes[1].fill_between(x, likelihood, alpha=0.4, color=COLORS["secondary"])
    axes[1].plot(x, likelihood, color=COLORS["secondary"], lw=2)
    axes[1].set_title("가능도 (Likelihood)", fontsize=13, fontweight="bold")

    axes[2].fill_between(x, posterior, alpha=0.4, color=COLORS["success"])
    axes[2].plot(x, posterior, color=COLORS["success"], lw=2)
    axes[2].plot(x, prior / prior.max() * posterior.max(), "--",
                 color=COLORS["primary"], alpha=0.5, lw=1, label="사전 분포")
    axes[2].set_title("사후 분포 (Posterior)", fontsize=13, fontweight="bold")
    axes[2].legend(fontsize=9)

    fig.suptitle("베이즈 정리: Prior × Likelihood ∝ Posterior",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "bayes_theorem.png")

    # Figure 2: 베이즈 업데이트 과정
    fig, ax = make_fig(10, 6)
    x = np.linspace(-2, 8, 300)
    prior_mean, prior_std = 3.0, 2.0

    observations = [4.0, 5.5, 4.8, 5.0]
    colors_update = [COLORS["primary"], COLORS["teal"],
                     COLORS["success"], COLORS["danger"]]

    current_mean, current_var = prior_mean, prior_std ** 2
    prior_pdf = stats.norm.pdf(x, current_mean, np.sqrt(current_var))
    ax.plot(x, prior_pdf, color="#aaa", lw=2, ls="--", label="초기 사전 분포")

    for i, obs in enumerate(observations):
        obs_var = 1.0
        new_var = 1 / (1 / current_var + 1 / obs_var)
        new_mean = new_var * (current_mean / current_var + obs / obs_var)
        current_mean, current_var = new_mean, new_var

        pdf = stats.norm.pdf(x, current_mean, np.sqrt(current_var))
        ax.plot(x, pdf, color=colors_update[i], lw=2,
                label=f"관측 {i+1} (x={obs})")
        ax.axvline(obs, ls=":", color=colors_update[i], alpha=0.4)

    ax.set_xlabel("θ", fontsize=13)
    ax.set_ylabel("확률 밀도", fontsize=13)
    ax.set_title("베이즈 업데이트: 데이터가 누적될수록 사후 분포가 좁아짐",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    save_fig(fig, slug, "bayesian_update.png")


def gen_06_information_theory():
    slug = "06_information-theory"

    # Figure 1: 엔트로피 vs 확률
    fig, axes = make_fig_axes(1, 2, 12, 6)

    # 이진 엔트로피
    p = np.linspace(0.001, 0.999, 200)
    entropy = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
    axes[0].plot(p, entropy, color=COLORS["primary"], lw=2.5)
    axes[0].fill_between(p, entropy, alpha=0.15, color=COLORS["primary"])
    axes[0].axvline(0.5, ls="--", color=COLORS["danger"], alpha=0.5)
    axes[0].scatter([0.5], [1.0], s=80, c=COLORS["danger"], zorder=5)
    axes[0].annotate("최대 엔트로피\n(p=0.5, H=1.0)", xy=(0.5, 1.0),
                     xytext=(0.7, 0.7), fontsize=11,
                     arrowprops=dict(arrowstyle="->", color=COLORS["danger"]))
    axes[0].set_xlabel("확률 (p)", fontsize=12)
    axes[0].set_ylabel("엔트로피 H(p) [bits]", fontsize=12)
    axes[0].set_title("이진 엔트로피 함수", fontsize=14, fontweight="bold")

    # KL Divergence
    x = np.linspace(-5, 10, 300)
    p_dist = stats.norm.pdf(x, 3, 1)
    q_dists = [
        (stats.norm.pdf(x, 3, 1.5), "Q₁: N(3, 1.5²)"),
        (stats.norm.pdf(x, 4, 1), "Q₂: N(4, 1²)"),
        (stats.norm.pdf(x, 5, 2), "Q₃: N(5, 2²)"),
    ]
    kl_colors = [COLORS["success"], COLORS["warning"], COLORS["danger"]]

    axes[1].fill_between(x, p_dist, alpha=0.3, color=COLORS["primary"])
    axes[1].plot(x, p_dist, color=COLORS["primary"], lw=2.5, label="P: N(3, 1²)")

    for (q, label), c in zip(q_dists, kl_colors):
        kl = np.sum(np.where(p_dist > 1e-10,
                             p_dist * np.log(p_dist / np.maximum(q, 1e-10)),
                             0)) * (x[1] - x[0])
        axes[1].plot(x, q, color=c, lw=2, ls="--",
                     label=f"{label}, KL={kl:.2f}")

    axes[1].set_xlabel("x", fontsize=12)
    axes[1].set_ylabel("확률 밀도", fontsize=12)
    axes[1].set_title("KL 발산 (Kullback-Leibler Divergence)", fontsize=14,
                      fontweight="bold")
    axes[1].legend(fontsize=9)

    fig.suptitle("정보 이론 핵심 개념", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "entropy_kl_divergence.png")

    # Figure 2: Cross-Entropy 시각화
    fig, ax = make_fig(10, 6)
    p_vals = np.linspace(0.01, 0.99, 100)
    ce_q05 = -p_vals * np.log2(0.5) - (1 - p_vals) * np.log2(0.5)
    ce_q_p = -p_vals * np.log2(p_vals) - (1 - p_vals) * np.log2(1 - p_vals)
    ce_q03 = -p_vals * np.log2(0.3) - (1 - p_vals) * np.log2(0.7)

    ax.plot(p_vals, ce_q_p, color=COLORS["success"], lw=2.5,
            label="H(p, p) = H(p) (엔트로피)")
    ax.plot(p_vals, ce_q05, color=COLORS["warning"], lw=2, ls="--",
            label="H(p, q=0.5)")
    ax.plot(p_vals, ce_q03, color=COLORS["danger"], lw=2, ls="-.",
            label="H(p, q=0.3)")
    ax.fill_between(p_vals, ce_q_p, ce_q03, alpha=0.1, color=COLORS["danger"],
                    label="KL(p||q) 영역")

    ax.set_xlabel("실제 확률 p", fontsize=12)
    ax.set_ylabel("교차 엔트로피 H(p, q)", fontsize=12)
    ax.set_title("교차 엔트로피와 KL 발산의 관계", fontsize=15, fontweight="bold")
    ax.legend(fontsize=10)
    save_fig(fig, slug, "cross_entropy.png")


def gen_07_optimization_theory():
    slug = "07_optimization-theory"

    # Figure 1: 등고선 위 경사 하강법 경로
    fig, axes = make_fig_axes(1, 2, 14, 6)

    # Rosenbrock-like 함수
    xx, yy = np.meshgrid(np.linspace(-2, 2, 200), np.linspace(-1, 3, 200))
    zz = (1 - xx) ** 2 + 5 * (yy - xx ** 2) ** 2

    for ax in axes:
        ax.contour(xx, yy, zz, levels=np.logspace(-1, 3, 20),
                   cmap="coolwarm", alpha=0.6)
        ax.contourf(xx, yy, zz, levels=np.logspace(-1, 3, 20),
                    cmap="coolwarm", alpha=0.15)

    # GD 경로 (큰 학습률 vs 작은 학습률)
    def gradient(x, y):
        dx = -2 * (1 - x) + 5 * 2 * (y - x ** 2) * (-2 * x)
        dy = 5 * 2 * (y - x ** 2)
        return np.array([dx, dy])

    # 작은 학습률
    lr_small = 0.002
    path_small = [np.array([-1.5, 2.5])]
    for _ in range(300):
        grad = gradient(*path_small[-1])
        path_small.append(path_small[-1] - lr_small * grad)
    path_small = np.array(path_small)

    axes[0].plot(path_small[:, 0], path_small[:, 1], "o-",
                 color=COLORS["primary"], markersize=2, lw=1.5, alpha=0.8)
    axes[0].scatter([1], [1], s=200, c=COLORS["success"], marker="*", zorder=5)
    axes[0].set_title(f"작은 학습률 (η={lr_small})\n느리지만 안정적",
                      fontsize=12, fontweight="bold")

    # 큰 학습률
    lr_large = 0.01
    path_large = [np.array([-1.5, 2.5])]
    for _ in range(100):
        grad = gradient(*path_large[-1])
        step = path_large[-1] - lr_large * grad
        step = np.clip(step, -2, 3)
        path_large.append(step)
    path_large = np.array(path_large)

    axes[1].plot(path_large[:, 0], path_large[:, 1], "o-",
                 color=COLORS["danger"], markersize=2, lw=1.5, alpha=0.8)
    axes[1].scatter([1], [1], s=200, c=COLORS["success"], marker="*", zorder=5)
    axes[1].set_title(f"큰 학습률 (η={lr_large})\n빠르지만 불안정",
                      fontsize=12, fontweight="bold")

    for ax in axes:
        ax.set_xlabel("x", fontsize=11)
        ax.set_ylabel("y", fontsize=11)

    fig.suptitle("경사 하강법: 학습률에 따른 최적화 경로",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "gradient_descent_paths.png")

    # Figure 2: 학습률 비교 (손실 곡선)
    fig, ax = make_fig(10, 6)
    epochs = np.arange(1, 101)
    lrs = [0.001, 0.01, 0.1, 0.5]
    lr_colors = [COLORS["primary"], COLORS["success"],
                 COLORS["warning"], COLORS["danger"]]

    np.random.seed(42)
    for lr, c in zip(lrs, lr_colors):
        if lr == 0.001:
            loss = 5 * np.exp(-0.02 * epochs) + 0.5
        elif lr == 0.01:
            loss = 5 * np.exp(-0.05 * epochs) + 0.1
        elif lr == 0.1:
            loss = 5 * np.exp(-0.1 * epochs) + 0.3 + \
                   0.2 * np.sin(epochs * 0.5)
        else:
            loss = 5 * np.exp(-0.01 * epochs) + 2 + \
                   np.random.randn(len(epochs)) * 0.5 * np.exp(-0.01 * epochs)
            loss = np.maximum(loss, 0.5)

        ax.plot(epochs, loss, color=c, lw=2, label=f"η = {lr}")

    ax.set_xlabel("Epoch", fontsize=13)
    ax.set_ylabel("손실 (Loss)", fontsize=13)
    ax.set_title("학습률(Learning Rate)에 따른 수렴 패턴", fontsize=15,
                 fontweight="bold")
    ax.legend(fontsize=11)
    ax.set_xlim(1, 100)
    ax.set_ylim(0, 8)
    save_fig(fig, slug, "learning_rate_comparison.png")


# ═══════════════════════════════════════════════════════════════════════════
# Group 2: Preprocessing (08–10)
# ═══════════════════════════════════════════════════════════════════════════

def gen_08_data_preprocessing():
    slug = "08_data-preprocessing"
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

    # Figure 1: 스케일링 비교
    np.random.seed(42)
    data = np.concatenate([
        np.random.normal(50, 15, 200),
        np.random.normal(200, 5, 20),  # 이상치
    ]).reshape(-1, 1)

    scalers = {
        "원본 데이터": data,
        "StandardScaler\n(z-score 정규화)": StandardScaler().fit_transform(data),
        "MinMaxScaler\n(0~1 정규화)": MinMaxScaler().fit_transform(data),
        "RobustScaler\n(중앙값/IQR)": RobustScaler().fit_transform(data),
    }

    fig, axes = make_fig_axes(1, 4, 16, 5)
    scale_colors = [COLORS["dark"], COLORS["primary"],
                    COLORS["secondary"], COLORS["success"]]

    for ax, (name, scaled), c in zip(axes, scalers.items(), scale_colors):
        ax.hist(scaled, bins=30, color=c, alpha=0.7, edgecolor="white")
        ax.axvline(np.median(scaled), color=COLORS["danger"], ls="--",
                   lw=1.5, label=f"중앙값: {np.median(scaled):.2f}")
        ax.set_title(name, fontsize=11, fontweight="bold")
        ax.legend(fontsize=8)

    fig.suptitle("데이터 스케일링 방법 비교", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "scaling_comparison.png")

    # Figure 2: 결측값 처리 시각화
    fig, axes = make_fig_axes(1, 2, 12, 5)
    np.random.seed(42)
    n = 50
    x = np.linspace(0, 10, n)
    y = 2 * x + 3 + np.random.randn(n) * 2
    mask = np.random.rand(n) > 0.7

    axes[0].scatter(x[~mask], y[~mask], c=COLORS["primary"], s=40,
                    label="관측값", zorder=3)
    axes[0].scatter(x[mask], y[mask], c=COLORS["danger"], s=40, marker="x",
                    label="결측값", zorder=3, alpha=0.5)
    axes[0].set_title("결측값이 있는 데이터", fontsize=13, fontweight="bold")
    axes[0].legend(fontsize=10)

    # 보간
    y_imputed = y.copy()
    y_imputed[mask] = np.interp(x[mask], x[~mask], y[~mask])
    axes[1].scatter(x[~mask], y[~mask], c=COLORS["primary"], s=40,
                    label="관측값", zorder=3)
    axes[1].scatter(x[mask], y_imputed[mask], c=COLORS["success"], s=40,
                    marker="D", label="보간값", zorder=3)
    z = np.polyfit(x, y_imputed, 1)
    axes[1].plot(x, np.polyval(z, x), "--", color=COLORS["secondary"],
                 lw=1.5, label="회귀선")
    axes[1].set_title("보간 후 데이터", fontsize=13, fontweight="bold")
    axes[1].legend(fontsize=10)

    fig.suptitle("결측값 처리 전후 비교", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "missing_value_handling.png")


def gen_09_feature_engineering():
    slug = "09_feature-engineering"

    # Figure 1: 특성 중요도 바 차트
    fig, ax = make_fig(10, 6)
    features = ["연봉", "근무연수", "교육수준", "나이", "부서",
                "성과점수", "야근빈도", "출퇴근거리", "결혼여부", "성별"]
    importance = np.array([0.25, 0.18, 0.14, 0.12, 0.09,
                           0.08, 0.06, 0.04, 0.03, 0.01])

    colors_bar = [COLORS["danger"] if v > 0.15 else
                  COLORS["warning"] if v > 0.08 else
                  COLORS["primary"] for v in importance]

    bars = ax.barh(range(len(features)), importance, color=colors_bar, alpha=0.85,
                   edgecolor="white", height=0.7)
    ax.set_yticks(range(len(features)))
    ax.set_yticklabels(features, fontsize=11)
    ax.set_xlabel("특성 중요도", fontsize=12)
    ax.set_title("랜덤 포레스트 특성 중요도 (Feature Importance)",
                 fontsize=15, fontweight="bold")
    ax.invert_yaxis()

    for bar, val in zip(bars, importance):
        ax.text(val + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=10, fontweight="bold")
    save_fig(fig, slug, "feature_importance.png")

    # Figure 2: 다항 특성 확장
    fig, axes = make_fig_axes(1, 2, 12, 5)
    np.random.seed(42)
    x = np.linspace(-3, 3, 50)
    y = 0.5 * x ** 2 + np.random.randn(50) * 0.5

    axes[0].scatter(x, y, c=COLORS["primary"], s=30, alpha=0.7)
    z = np.polyfit(x, y, 1)
    axes[0].plot(x, np.polyval(z, x), color=COLORS["danger"], lw=2,
                 label="선형 (R²={:.2f})".format(1 - np.sum((y - np.polyval(z, x))**2) /
                                                  np.sum((y - y.mean())**2)))
    axes[0].set_title("원본 특성 (x → y)", fontsize=13, fontweight="bold")
    axes[0].legend(fontsize=10)
    axes[0].set_xlabel("x", fontsize=11)
    axes[0].set_ylabel("y", fontsize=11)

    axes[1].scatter(x ** 2, y, c=COLORS["success"], s=30, alpha=0.7)
    z2 = np.polyfit(x ** 2, y, 1)
    axes[1].plot(np.sort(x ** 2), np.polyval(z2, np.sort(x ** 2)),
                 color=COLORS["success"], lw=2,
                 label="선형 (R²={:.2f})".format(1 - np.sum((y - np.polyval(z2, x**2))**2) /
                                                   np.sum((y - y.mean())**2)))
    axes[1].set_title("다항 특성 (x² → y)", fontsize=13, fontweight="bold")
    axes[1].legend(fontsize=10)
    axes[1].set_xlabel("x²", fontsize=11)
    axes[1].set_ylabel("y", fontsize=11)

    fig.suptitle("다항 특성 확장: 비선형 관계를 선형으로 변환",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "polynomial_features.png")


def gen_10_imbalanced_data():
    slug = "10_imbalanced-data"

    # Figure 1: 클래스 분포 before/after
    fig, axes = make_fig_axes(1, 3, 15, 5)

    classes = ["정상 (Negative)", "이상 (Positive)"]

    # Before
    counts_before = [950, 50]
    axes[0].bar(classes, counts_before,
                color=[COLORS["primary"], COLORS["danger"]], alpha=0.8,
                edgecolor="white", width=0.5)
    axes[0].set_title("원본 분포\n(불균형)", fontsize=13, fontweight="bold")
    axes[0].set_ylabel("샘플 수", fontsize=11)
    for i, v in enumerate(counts_before):
        axes[0].text(i, v + 20, str(v), ha="center", fontweight="bold", fontsize=12)

    # After oversampling
    counts_over = [950, 950]
    axes[1].bar(classes, counts_over,
                color=[COLORS["primary"], COLORS["success"]], alpha=0.8,
                edgecolor="white", width=0.5)
    axes[1].set_title("오버샘플링 후\n(SMOTE)", fontsize=13, fontweight="bold")
    for i, v in enumerate(counts_over):
        axes[1].text(i, v + 20, str(v), ha="center", fontweight="bold", fontsize=12)

    # After undersampling
    counts_under = [50, 50]
    axes[2].bar(classes, counts_under,
                color=[COLORS["warning"], COLORS["danger"]], alpha=0.8,
                edgecolor="white", width=0.5)
    axes[2].set_title("언더샘플링 후\n(Random)", fontsize=13, fontweight="bold")
    for i, v in enumerate(counts_under):
        axes[2].text(i, v + 2, str(v), ha="center", fontweight="bold", fontsize=12)

    fig.suptitle("불균형 데이터 리샘플링 전략", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "resampling_comparison.png")

    # Figure 2: SMOTE 시각화
    fig, axes = make_fig_axes(1, 2, 12, 6)
    np.random.seed(42)

    # 원본
    majority = np.random.randn(200, 2) + np.array([2, 2])
    minority = np.random.randn(20, 2) * 0.5 + np.array([-1, -1])

    axes[0].scatter(majority[:, 0], majority[:, 1], c=COLORS["primary"],
                    s=20, alpha=0.5, label="다수 클래스")
    axes[0].scatter(minority[:, 0], minority[:, 1], c=COLORS["danger"],
                    s=40, marker="^", label="소수 클래스")
    axes[0].set_title("원본 데이터", fontsize=13, fontweight="bold")
    axes[0].legend(fontsize=10)

    # SMOTE 합성 샘플
    synthetic = []
    for _ in range(180):
        idx = np.random.randint(0, len(minority))
        nn_idx = np.random.randint(0, len(minority))
        diff = minority[nn_idx] - minority[idx]
        syn = minority[idx] + np.random.rand() * diff
        synthetic.append(syn)
    synthetic = np.array(synthetic)

    axes[1].scatter(majority[:, 0], majority[:, 1], c=COLORS["primary"],
                    s=20, alpha=0.5, label="다수 클래스")
    axes[1].scatter(minority[:, 0], minority[:, 1], c=COLORS["danger"],
                    s=40, marker="^", label="소수 클래스 (원본)")
    axes[1].scatter(synthetic[:, 0], synthetic[:, 1], c=COLORS["success"],
                    s=25, marker="s", alpha=0.6, label="SMOTE 합성 샘플")
    axes[1].set_title("SMOTE 적용 후", fontsize=13, fontweight="bold")
    axes[1].legend(fontsize=9)

    fig.suptitle("SMOTE (Synthetic Minority Over-sampling Technique)",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "smote_visualization.png")


# ═══════════════════════════════════════════════════════════════════════════
# Group 3: Regression (11–13)
# ═══════════════════════════════════════════════════════════════════════════

def gen_11_linear_regression():
    slug = "11_linear-regression"

    np.random.seed(42)
    x = np.linspace(0, 10, 50)
    y = 2.5 * x + 3 + np.random.randn(50) * 3

    # Figure 1: 단순 회귀선과 데이터
    fig, axes = make_fig_axes(1, 2, 12, 5)

    coeffs = np.polyfit(x, y, 1)
    y_pred = np.polyval(coeffs, x)

    axes[0].scatter(x, y, c=COLORS["primary"], s=40, alpha=0.7, edgecolors="white",
                    label="데이터 포인트")
    axes[0].plot(x, y_pred, color=COLORS["danger"], lw=2.5,
                 label=f"회귀선: y = {coeffs[0]:.2f}x + {coeffs[1]:.2f}")
    # 잔차 표시
    for xi, yi, yp in list(zip(x, y, y_pred))[::5]:
        axes[0].plot([xi, xi], [yi, yp], color=COLORS["warning"], lw=1, alpha=0.5)
    axes[0].set_xlabel("x", fontsize=12)
    axes[0].set_ylabel("y", fontsize=12)
    axes[0].set_title("단순 선형 회귀", fontsize=14, fontweight="bold")
    axes[0].legend(fontsize=10)

    # 잔차 플롯
    residuals = y - y_pred
    axes[1].scatter(y_pred, residuals, c=COLORS["purple"], s=40, alpha=0.7,
                    edgecolors="white")
    axes[1].axhline(0, color=COLORS["danger"], ls="--", lw=1.5)
    axes[1].fill_between([y_pred.min(), y_pred.max()],
                         -2 * residuals.std(), 2 * residuals.std(),
                         alpha=0.1, color=COLORS["primary"])
    axes[1].set_xlabel("예측값 (ŷ)", fontsize=12)
    axes[1].set_ylabel("잔차 (y - ŷ)", fontsize=12)
    axes[1].set_title("잔차 플롯 (Residual Plot)", fontsize=14, fontweight="bold")

    fig.suptitle("선형 회귀 분석", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "linear_regression_residual.png")

    # Figure 2: 최소제곱법 시각화
    fig, ax = make_fig(10, 6)
    ax.scatter(x, y, c=COLORS["primary"], s=50, alpha=0.7, edgecolors="white",
               zorder=3, label="데이터")
    ax.plot(x, y_pred, color=COLORS["danger"], lw=2.5, label="회귀선", zorder=4)

    for xi, yi, yp in zip(x, y, y_pred):
        rect = plt.Rectangle((min(xi, xi), min(yi, yp)),
                              abs(yi - yp) * 0.3, abs(yi - yp),
                              alpha=0.15, color=COLORS["warning"])
        ax.add_patch(rect)

    ax.set_xlabel("x", fontsize=13)
    ax.set_ylabel("y", fontsize=13)
    ax.set_title("최소제곱법 (OLS): 잔차 제곱합 최소화",
                 fontsize=15, fontweight="bold")
    ax.legend(fontsize=11)
    save_fig(fig, slug, "ols_visualization.png")


def gen_12_regularized_regression():
    slug = "12_regularized-regression"

    # Figure 1: L1 vs L2 계수 축소 경로
    from sklearn.linear_model import Lasso, Ridge
    from sklearn.preprocessing import StandardScaler

    np.random.seed(42)
    n, p = 100, 10
    X = np.random.randn(n, p)
    true_coef = np.array([3, -2, 0, 0, 1.5, 0, 0, -1, 0, 0.5])
    y = X @ true_coef + np.random.randn(n) * 0.5
    X = StandardScaler().fit_transform(X)

    alphas = np.logspace(-3, 2, 100)
    lasso_coefs = []
    ridge_coefs = []

    for a in alphas:
        lasso = Lasso(alpha=a, max_iter=10000)
        lasso.fit(X, y)
        lasso_coefs.append(lasso.coef_.copy())

        ridge = Ridge(alpha=a)
        ridge.fit(X, y)
        ridge_coefs.append(ridge.coef_.copy())

    lasso_coefs = np.array(lasso_coefs)
    ridge_coefs = np.array(ridge_coefs)

    fig, axes = make_fig_axes(1, 2, 14, 6)
    feature_names = [f"특성 {i+1}" for i in range(p)]

    for i in range(p):
        lw = 2 if true_coef[i] != 0 else 0.8
        alpha = 1.0 if true_coef[i] != 0 else 0.3
        axes[0].plot(np.log10(alphas), lasso_coefs[:, i],
                     lw=lw, alpha=alpha, label=feature_names[i] if true_coef[i] != 0 else None)
        axes[1].plot(np.log10(alphas), ridge_coefs[:, i],
                     lw=lw, alpha=alpha, label=feature_names[i] if true_coef[i] != 0 else None)

    axes[0].set_title("L1 정규화 (Lasso)\n계수가 정확히 0으로 수렴",
                      fontsize=13, fontweight="bold")
    axes[0].axhline(0, color="#ccc", ls="-", lw=0.5)
    axes[1].set_title("L2 정규화 (Ridge)\n계수가 점진적으로 감소",
                      fontsize=13, fontweight="bold")
    axes[1].axhline(0, color="#ccc", ls="-", lw=0.5)

    for ax in axes:
        ax.set_xlabel("log₁₀(α)", fontsize=12)
        ax.set_ylabel("계수 값", fontsize=12)
        ax.legend(fontsize=8, loc="upper right")

    fig.suptitle("정규화 강도에 따른 계수 축소 경로",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "l1_l2_coefficient_paths.png")

    # Figure 2: 정규화 효과 시각화
    fig, axes = make_fig_axes(1, 3, 15, 5)
    np.random.seed(42)
    x_train = np.sort(np.random.rand(20)) * 6
    y_train = np.sin(x_train) + np.random.randn(20) * 0.3
    x_plot = np.linspace(0, 6, 200)

    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.pipeline import make_pipeline

    models = [
        ("정규화 없음\n(과대적합)", make_pipeline(PolynomialFeatures(12),
                                              Ridge(alpha=1e-10))),
        ("적당한 정규화\n(α=0.1)", make_pipeline(PolynomialFeatures(12),
                                              Ridge(alpha=0.1))),
        ("강한 정규화\n(α=100)", make_pipeline(PolynomialFeatures(12),
                                            Ridge(alpha=100))),
    ]
    model_colors = [COLORS["danger"], COLORS["success"], COLORS["warning"]]

    for ax, (name, model), c in zip(axes, models, model_colors):
        model.fit(x_train.reshape(-1, 1), y_train)
        y_plot = model.predict(x_plot.reshape(-1, 1))

        ax.scatter(x_train, y_train, c=COLORS["primary"], s=40, zorder=3)
        ax.plot(x_plot, y_plot, color=c, lw=2.5)
        ax.plot(x_plot, np.sin(x_plot), "--", color="#aaa", lw=1,
                label="실제 함수")
        ax.set_title(name, fontsize=12, fontweight="bold", color=c)
        ax.set_ylim(-2, 2)
        ax.legend(fontsize=8)

    fig.suptitle("정규화 강도에 따른 모델 복잡도 제어",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "regularization_effect.png")


def gen_13_polynomial_regression():
    slug = "13_polynomial-regression"

    np.random.seed(42)
    x = np.sort(np.random.rand(30)) * 6
    y = np.sin(x) + np.random.randn(30) * 0.3
    x_plot = np.linspace(0, 6, 200)

    # Figure 1: 다항식 차수 비교
    fig, axes = make_fig_axes(2, 2, 12, 10)
    degrees = [1, 3, 7, 15]
    deg_colors = [COLORS["warning"], COLORS["success"],
                  COLORS["primary"], COLORS["danger"]]
    deg_labels = ["과소적합 (degree=1)", "적절한 적합 (degree=3)",
                  "약간 복잡 (degree=7)", "과대적합 (degree=15)"]

    for ax, deg, c, label in zip(axes.flat, degrees, deg_colors, deg_labels):
        coeffs = np.polyfit(x, y, deg)
        y_plot = np.polyval(coeffs, x_plot)

        ax.scatter(x, y, c=COLORS["dark"], s=30, alpha=0.7, zorder=3)
        ax.plot(x_plot, y_plot, color=c, lw=2.5, label=f"degree={deg}")
        ax.plot(x_plot, np.sin(x_plot), "--", color="#aaa", lw=1,
                label="실제 함수")
        ax.set_title(label, fontsize=12, fontweight="bold", color=c)
        ax.set_ylim(-2.5, 2.5)
        ax.legend(fontsize=9)

    fig.suptitle("다항 회귀: 차수별 적합 비교", fontsize=16,
                 fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "polynomial_degrees_comparison.png")

    # Figure 2: 훈련/테스트 오차 vs 차수
    fig, ax = make_fig(10, 6)
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.metrics import mean_squared_error

    degrees_range = range(1, 16)
    train_errors = []
    test_errors = []

    x_train = x.reshape(-1, 1)
    np.random.seed(42)
    x_test = np.sort(np.random.rand(100)) * 6
    y_test = np.sin(x_test) + np.random.randn(100) * 0.3
    x_test = x_test.reshape(-1, 1)

    for d in degrees_range:
        model = make_pipeline(PolynomialFeatures(d), LinearRegression())
        model.fit(x_train, y)
        train_errors.append(mean_squared_error(y, model.predict(x_train)))
        test_errors.append(mean_squared_error(y_test, model.predict(x_test)))

    ax.plot(list(degrees_range), train_errors, "o-", color=COLORS["primary"],
            lw=2, label="훈련 오차")
    ax.plot(list(degrees_range), test_errors, "o-", color=COLORS["danger"],
            lw=2, label="테스트 오차")

    best_deg = list(degrees_range)[np.argmin(test_errors)]
    ax.axvline(best_deg, ls="--", color=COLORS["success"], alpha=0.7)
    ax.annotate(f"최적 차수 = {best_deg}", xy=(best_deg, min(test_errors)),
                xytext=(best_deg + 2, min(test_errors) + 0.3),
                fontsize=12, color=COLORS["success"], fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=COLORS["success"]))

    ax.set_xlabel("다항식 차수", fontsize=13)
    ax.set_ylabel("MSE", fontsize=13)
    ax.set_title("다항식 차수에 따른 훈련/테스트 오차", fontsize=15, fontweight="bold")
    ax.legend(fontsize=11)
    ax.set_yscale("log")
    save_fig(fig, slug, "train_test_error_vs_degree.png")


# ═══════════════════════════════════════════════════════════════════════════
# Group 4: Classification (14–18)
# ═══════════════════════════════════════════════════════════════════════════

def gen_14_logistic_regression():
    slug = "14_logistic-regression"

    # Figure 1: 시그모이드 함수
    fig, ax = make_fig(10, 6)
    z = np.linspace(-8, 8, 200)
    sigmoid = 1 / (1 + np.exp(-z))

    ax.plot(z, sigmoid, color=COLORS["primary"], lw=3, label="σ(z) = 1/(1+e⁻ᶻ)")
    ax.axhline(0.5, ls="--", color=COLORS["danger"], alpha=0.5, lw=1.5)
    ax.axvline(0, ls="--", color="#aaa", alpha=0.3, lw=1)

    ax.fill_between(z, sigmoid, 0.5, where=sigmoid >= 0.5,
                    alpha=0.15, color=COLORS["success"], label="Class 1 (≥ 0.5)")
    ax.fill_between(z, sigmoid, 0.5, where=sigmoid < 0.5,
                    alpha=0.15, color=COLORS["danger"], label="Class 0 (< 0.5)")

    ax.scatter([0], [0.5], s=80, c=COLORS["danger"], zorder=5)
    ax.annotate("결정 경계\n(z=0, p=0.5)", xy=(0, 0.5), xytext=(2, 0.3),
                fontsize=11, arrowprops=dict(arrowstyle="->"), fontweight="bold")

    ax.set_xlabel("z = wᵀx + b", fontsize=13)
    ax.set_ylabel("σ(z) = P(y=1|x)", fontsize=13)
    ax.set_title("시그모이드(Sigmoid) 함수", fontsize=16, fontweight="bold")
    ax.legend(fontsize=11, loc="upper left")
    ax.set_ylim(-0.05, 1.05)
    save_fig(fig, slug, "sigmoid_function.png")

    # Figure 2: 결정 경계
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegression

    np.random.seed(42)
    X, y = make_classification(n_samples=200, n_features=2, n_redundant=0,
                               n_informative=2, n_clusters_per_class=1,
                               class_sep=1.5, random_state=42)

    fig, ax = make_fig(10, 8)
    model = LogisticRegression()
    model.fit(X, y)

    xx, yy = np.meshgrid(np.linspace(X[:, 0].min() - 1, X[:, 0].max() + 1, 200),
                          np.linspace(X[:, 1].min() - 1, X[:, 1].max() + 1, 200))
    Z = model.predict_proba(np.c_[xx.ravel(), yy.ravel()])[:, 1].reshape(xx.shape)

    ax.contourf(xx, yy, Z, levels=20, cmap="RdYlBu_r", alpha=0.4)
    ax.contour(xx, yy, Z, levels=[0.5], colors=[COLORS["dark"]], linewidths=2)

    scatter = ax.scatter(X[:, 0], X[:, 1], c=y, cmap="RdYlBu_r",
                         s=40, edgecolors="white", linewidth=0.5, zorder=3)
    ax.set_xlabel("특성 1", fontsize=13)
    ax.set_ylabel("특성 2", fontsize=13)
    ax.set_title("로지스틱 회귀 결정 경계", fontsize=16, fontweight="bold")
    plt.colorbar(scatter, ax=ax, label="클래스 확률")
    save_fig(fig, slug, "decision_boundary.png")


def gen_15_naive_bayes():
    slug = "15_naive-bayes"

    # Figure 1: 클래스별 조건부 분포
    fig, axes = make_fig_axes(1, 2, 12, 5)
    x = np.linspace(-5, 10, 300)

    # 특성 1
    axes[0].plot(x, stats.norm.pdf(x, 2, 1), color=COLORS["primary"], lw=2.5,
                 label="P(x₁|스팸)")
    axes[0].plot(x, stats.norm.pdf(x, 5, 1.5), color=COLORS["danger"], lw=2.5,
                 label="P(x₁|정상)")
    axes[0].fill_between(x, stats.norm.pdf(x, 2, 1), alpha=0.2,
                         color=COLORS["primary"])
    axes[0].fill_between(x, stats.norm.pdf(x, 5, 1.5), alpha=0.2,
                         color=COLORS["danger"])
    axes[0].axvline(3.5, ls="--", color=COLORS["success"], lw=1.5)
    axes[0].set_title("특성 1의 클래스별 분포", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("특성 값", fontsize=11)
    axes[0].legend(fontsize=10)

    # 특성 2
    axes[1].plot(x, stats.norm.pdf(x, 4, 2), color=COLORS["primary"], lw=2.5,
                 label="P(x₂|스팸)")
    axes[1].plot(x, stats.norm.pdf(x, 6, 1), color=COLORS["danger"], lw=2.5,
                 label="P(x₂|정상)")
    axes[1].fill_between(x, stats.norm.pdf(x, 4, 2), alpha=0.2,
                         color=COLORS["primary"])
    axes[1].fill_between(x, stats.norm.pdf(x, 6, 1), alpha=0.2,
                         color=COLORS["danger"])
    axes[1].set_title("특성 2의 클래스별 분포", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("특성 값", fontsize=11)
    axes[1].legend(fontsize=10)

    fig.suptitle("나이브 베이즈: 클래스-조건부 확률 분포",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "class_conditional_distributions.png")

    # Figure 2: 결정 경계
    from sklearn.datasets import make_classification
    from sklearn.naive_bayes import GaussianNB

    np.random.seed(42)
    X, y = make_classification(n_samples=300, n_features=2, n_redundant=0,
                               n_informative=2, n_clusters_per_class=1,
                               class_sep=1.2, random_state=42)

    fig, ax = make_fig(10, 8)
    model = GaussianNB()
    model.fit(X, y)

    xx, yy = np.meshgrid(np.linspace(X[:, 0].min() - 1, X[:, 0].max() + 1, 200),
                          np.linspace(X[:, 1].min() - 1, X[:, 1].max() + 1, 200))
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

    ax.contourf(xx, yy, Z, alpha=0.3, cmap="RdYlBu_r")
    ax.contour(xx, yy, Z, colors=[COLORS["dark"]], linewidths=1.5)
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap="RdYlBu_r", s=30,
               edgecolors="white", linewidth=0.5)

    ax.set_xlabel("특성 1", fontsize=13)
    ax.set_ylabel("특성 2", fontsize=13)
    ax.set_title("나이브 베이즈 결정 경계", fontsize=16, fontweight="bold")
    save_fig(fig, slug, "naive_bayes_decision_boundary.png")


def gen_16_knn():
    slug = "16_knn"

    from sklearn.datasets import make_classification
    from sklearn.neighbors import KNeighborsClassifier

    np.random.seed(42)
    X, y = make_classification(n_samples=200, n_features=2, n_redundant=0,
                               n_informative=2, n_clusters_per_class=1,
                               class_sep=1.0, random_state=42)

    # Figure 1: K값에 따른 결정 경계
    fig, axes = make_fig_axes(1, 3, 15, 5)
    k_values = [1, 5, 15]

    xx, yy = np.meshgrid(np.linspace(X[:, 0].min() - 1, X[:, 0].max() + 1, 150),
                          np.linspace(X[:, 1].min() - 1, X[:, 1].max() + 1, 150))

    for ax, k in zip(axes, k_values):
        knn = KNeighborsClassifier(n_neighbors=k)
        knn.fit(X, y)
        Z = knn.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

        ax.contourf(xx, yy, Z, alpha=0.3, cmap="RdYlBu_r")
        ax.contour(xx, yy, Z, colors=[COLORS["dark"]], linewidths=1)
        ax.scatter(X[:, 0], X[:, 1], c=y, cmap="RdYlBu_r", s=20,
                   edgecolors="white", linewidth=0.5)
        ax.set_title(f"K = {k}", fontsize=14, fontweight="bold")

    fig.suptitle("K-최근접 이웃: K값에 따른 결정 경계 변화",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "knn_decision_boundaries.png")

    # Figure 2: K값 vs 정확도
    fig, ax = make_fig(10, 6)
    from sklearn.model_selection import cross_val_score

    k_range = range(1, 31)
    scores = []
    for k in k_range:
        knn = KNeighborsClassifier(n_neighbors=k)
        cv_scores = cross_val_score(knn, X, y, cv=5, scoring="accuracy")
        scores.append(cv_scores.mean())

    ax.plot(list(k_range), scores, "o-", color=COLORS["primary"], lw=2,
            markersize=5)

    best_k = list(k_range)[np.argmax(scores)]
    ax.axvline(best_k, ls="--", color=COLORS["success"], alpha=0.7)
    ax.scatter([best_k], [max(scores)], s=100, c=COLORS["success"], zorder=5)
    ax.annotate(f"최적 K = {best_k}\n정확도: {max(scores):.3f}",
                xy=(best_k, max(scores)),
                xytext=(best_k + 5, max(scores) - 0.03),
                fontsize=11, fontweight="bold", color=COLORS["success"],
                arrowprops=dict(arrowstyle="->", color=COLORS["success"]))

    ax.set_xlabel("K (이웃 수)", fontsize=13)
    ax.set_ylabel("교차검증 정확도", fontsize=13)
    ax.set_title("K값에 따른 분류 정확도", fontsize=15, fontweight="bold")
    save_fig(fig, slug, "knn_k_vs_accuracy.png")


def gen_17_svm():
    slug = "17_svm"
    from sklearn.svm import SVC
    from sklearn.datasets import make_classification, make_circles

    # Figure 1: SVM 마진과 서포트 벡터
    np.random.seed(42)
    X, y = make_classification(n_samples=100, n_features=2, n_redundant=0,
                               n_informative=2, n_clusters_per_class=1,
                               class_sep=2.0, random_state=42)

    fig, ax = make_fig(10, 8)
    svm = SVC(kernel="linear", C=1.0)
    svm.fit(X, y)

    xx, yy = np.meshgrid(np.linspace(X[:, 0].min() - 1, X[:, 0].max() + 1, 200),
                          np.linspace(X[:, 1].min() - 1, X[:, 1].max() + 1, 200))
    Z = svm.decision_function(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

    ax.contourf(xx, yy, Z, levels=[-1, 0, 1], alpha=0.15,
                colors=[COLORS["danger"], COLORS["primary"]])
    ax.contour(xx, yy, Z, levels=[-1, 0, 1], colors=[COLORS["danger"],
               COLORS["dark"], COLORS["primary"]],
               linestyles=["--", "-", "--"], linewidths=[1.5, 2.5, 1.5])

    ax.scatter(X[:, 0], X[:, 1], c=y, cmap="RdYlBu_r", s=40,
               edgecolors="white", linewidth=0.5, zorder=3)
    ax.scatter(svm.support_vectors_[:, 0], svm.support_vectors_[:, 1],
               s=150, facecolors="none", edgecolors=COLORS["success"],
               linewidth=2.5, zorder=4, label="서포트 벡터")

    ax.set_xlabel("특성 1", fontsize=13)
    ax.set_ylabel("특성 2", fontsize=13)
    ax.set_title("SVM: 최대 마진 분류기와 서포트 벡터", fontsize=16, fontweight="bold")
    ax.legend(fontsize=12, loc="upper left")
    save_fig(fig, slug, "svm_margin_support_vectors.png")

    # Figure 2: 커널 트릭
    X_circle, y_circle = make_circles(n_samples=200, noise=0.1, factor=0.5,
                                       random_state=42)

    fig, axes = make_fig_axes(1, 2, 12, 6)

    # 선형 커널 (실패)
    svm_linear = SVC(kernel="linear")
    svm_linear.fit(X_circle, y_circle)
    xx, yy = np.meshgrid(np.linspace(-1.5, 1.5, 200),
                          np.linspace(-1.5, 1.5, 200))
    Z_lin = svm_linear.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

    axes[0].contourf(xx, yy, Z_lin, alpha=0.3, cmap="RdYlBu_r")
    axes[0].scatter(X_circle[:, 0], X_circle[:, 1], c=y_circle,
                    cmap="RdYlBu_r", s=25, edgecolors="white", linewidth=0.5)
    axes[0].set_title("선형 커널 (Linear)\n분류 실패", fontsize=13,
                      fontweight="bold", color=COLORS["danger"])

    # RBF 커널 (성공)
    svm_rbf = SVC(kernel="rbf", gamma=2)
    svm_rbf.fit(X_circle, y_circle)
    Z_rbf = svm_rbf.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

    axes[1].contourf(xx, yy, Z_rbf, alpha=0.3, cmap="RdYlBu_r")
    axes[1].scatter(X_circle[:, 0], X_circle[:, 1], c=y_circle,
                    cmap="RdYlBu_r", s=25, edgecolors="white", linewidth=0.5)
    axes[1].set_title("RBF 커널 (Gaussian)\n성공적 분류", fontsize=13,
                      fontweight="bold", color=COLORS["success"])

    fig.suptitle("커널 트릭: 비선형 결정 경계 학습",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "kernel_trick.png")


def gen_18_decision_tree():
    slug = "18_decision-tree"
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.datasets import make_classification

    np.random.seed(42)
    X, y = make_classification(n_samples=200, n_features=2, n_redundant=0,
                               n_informative=2, n_clusters_per_class=1,
                               class_sep=1.0, random_state=42)

    # Figure 1: 특성 공간 분할
    fig, axes = make_fig_axes(1, 3, 15, 5)
    depths = [1, 3, None]
    depth_labels = ["깊이=1 (과소적합)", "깊이=3 (적절)", "깊이=무제한 (과대적합)"]
    depth_colors = [COLORS["warning"], COLORS["success"], COLORS["danger"]]

    xx, yy = np.meshgrid(np.linspace(X[:, 0].min() - 1, X[:, 0].max() + 1, 200),
                          np.linspace(X[:, 1].min() - 1, X[:, 1].max() + 1, 200))

    for ax, d, label, c in zip(axes, depths, depth_labels, depth_colors):
        tree = DecisionTreeClassifier(max_depth=d, random_state=42)
        tree.fit(X, y)
        Z = tree.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

        ax.contourf(xx, yy, Z, alpha=0.3, cmap="RdYlBu_r")
        ax.contour(xx, yy, Z, colors=[COLORS["dark"]], linewidths=0.5, alpha=0.5)
        ax.scatter(X[:, 0], X[:, 1], c=y, cmap="RdYlBu_r", s=20,
                   edgecolors="white", linewidth=0.5)
        acc = tree.score(X, y)
        ax.set_title(f"{label}\n훈련 정확도: {acc:.3f}", fontsize=11,
                     fontweight="bold", color=c)

    fig.suptitle("의사결정 트리: 깊이에 따른 특성 공간 분할",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "decision_tree_partitioning.png")

    # Figure 2: 지니 불순도 vs 엔트로피
    fig, ax = make_fig(10, 6)
    p = np.linspace(0.001, 0.999, 200)
    gini = 2 * p * (1 - p)
    entropy = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
    misclass = 1 - np.maximum(p, 1 - p)

    ax.plot(p, gini, color=COLORS["primary"], lw=2.5, label="지니 불순도")
    ax.plot(p, entropy / 2, color=COLORS["danger"], lw=2.5,
            label="엔트로피 / 2")
    ax.plot(p, misclass, color=COLORS["success"], lw=2.5, ls="--",
            label="오분류율")

    ax.set_xlabel("클래스 1의 비율 (p)", fontsize=13)
    ax.set_ylabel("불순도", fontsize=13)
    ax.set_title("노드 분할 기준: 불순도 함수 비교", fontsize=15, fontweight="bold")
    ax.legend(fontsize=11)
    save_fig(fig, slug, "impurity_functions.png")


# ═══════════════════════════════════════════════════════════════════════════
# Group 5: Ensemble (19–22)
# ═══════════════════════════════════════════════════════════════════════════

def gen_19_ensemble_overview():
    slug = "19_ensemble-overview"

    # Figure 1: Bagging vs Boosting 개념도
    fig, axes = make_fig_axes(1, 2, 14, 7)

    for ax in axes:
        ax.set_xlim(-0.5, 5.5)
        ax.set_ylim(-1, 7)
        ax.axis("off")

    # Bagging
    ax = axes[0]
    ax.set_title("배깅 (Bagging)\n병렬 학습 → 평균/투표", fontsize=14,
                 fontweight="bold", color=COLORS["primary"])

    # 원본 데이터
    box = FancyBboxPatch((1.5, 6), 2, 0.7, boxstyle="round,pad=0.15",
                          facecolor=COLORS["primary"], alpha=0.8, edgecolor="white")
    ax.add_patch(box)
    ax.text(2.5, 6.35, "원본 데이터", ha="center", va="center",
            fontsize=10, color="white", fontweight="bold")

    # 부트스트랩 샘플
    for i, x_pos in enumerate([0.5, 2, 3.5]):
        box = FancyBboxPatch((x_pos, 4.2), 1.5, 0.6,
                              boxstyle="round,pad=0.1",
                              facecolor=COLORS["blue_light"], alpha=0.7,
                              edgecolor="white")
        ax.add_patch(box)
        ax.text(x_pos + 0.75, 4.5, f"샘플 {i+1}", ha="center",
                va="center", fontsize=9, color="white")

        box2 = FancyBboxPatch((x_pos, 2.8), 1.5, 0.6,
                               boxstyle="round,pad=0.1",
                               facecolor=COLORS["teal"], alpha=0.7,
                               edgecolor="white")
        ax.add_patch(box2)
        ax.text(x_pos + 0.75, 3.1, f"모델 {i+1}", ha="center",
                va="center", fontsize=9, color="white")

        ax.annotate("", xy=(x_pos + 0.75, 4.2), xytext=(2.5, 6),
                    arrowprops=dict(arrowstyle="->", color="#666", lw=1))
        ax.annotate("", xy=(x_pos + 0.75, 3.4), xytext=(x_pos + 0.75, 4.2),
                    arrowprops=dict(arrowstyle="->", color="#666", lw=1))

    # 결합
    box3 = FancyBboxPatch((1.5, 1), 2, 0.7, boxstyle="round,pad=0.15",
                           facecolor=COLORS["success"], alpha=0.8, edgecolor="white")
    ax.add_patch(box3)
    ax.text(2.5, 1.35, "평균 / 투표", ha="center", va="center",
            fontsize=10, color="white", fontweight="bold")

    for x_pos in [1.25, 2.75, 4.25]:
        ax.annotate("", xy=(2.5, 1.7), xytext=(x_pos, 2.8),
                    arrowprops=dict(arrowstyle="->", color="#666", lw=1))

    # Boosting
    ax = axes[1]
    ax.set_title("부스팅 (Boosting)\n순차 학습 → 가중 결합", fontsize=14,
                 fontweight="bold", color=COLORS["secondary"])

    y_positions = [6, 4.5, 3]
    for i, yp in enumerate(y_positions):
        c = COLORS["secondary"] if i == 0 else \
            COLORS["warning"] if i == 1 else COLORS["danger"]
        box = FancyBboxPatch((1.5, yp), 2, 0.7, boxstyle="round,pad=0.15",
                              facecolor=c, alpha=0.8, edgecolor="white")
        ax.add_patch(box)
        ax.text(2.5, yp + 0.35, f"모델 {i+1}\n(약한 학습기)", ha="center",
                va="center", fontsize=9, color="white", fontweight="bold")

        if i < 2:
            ax.annotate("잔차 전달", xy=(2.5, y_positions[i+1] + 0.7),
                        xytext=(2.5, yp),
                        fontsize=8, color="#666", ha="center",
                        arrowprops=dict(arrowstyle="->", color="#666", lw=1.5))

    box4 = FancyBboxPatch((1.5, 1), 2, 0.7, boxstyle="round,pad=0.15",
                           facecolor=COLORS["success"], alpha=0.8, edgecolor="white")
    ax.add_patch(box4)
    ax.text(2.5, 1.35, "가중 합", ha="center", va="center",
            fontsize=10, color="white", fontweight="bold")
    ax.annotate("", xy=(2.5, 1.7), xytext=(2.5, 3),
                arrowprops=dict(arrowstyle="->", color="#666", lw=1.5))

    fig.suptitle("앙상블 학습: 배깅 vs 부스팅", fontsize=16,
                 fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "bagging_vs_boosting.png")

    # Figure 2: 앙상블 다양성 효과
    fig, axes = make_fig_axes(1, 3, 15, 5)
    from sklearn.datasets import make_moons
    from sklearn.tree import DecisionTreeClassifier

    X, y = make_moons(n_samples=200, noise=0.3, random_state=42)
    xx, yy = np.meshgrid(np.linspace(-2, 3, 200), np.linspace(-1.5, 2, 200))

    # 개별 모델들
    np.random.seed(42)
    individual_preds = []
    for i in range(3):
        idx = np.random.choice(len(X), size=len(X), replace=True)
        tree = DecisionTreeClassifier(max_depth=5, random_state=i)
        tree.fit(X[idx], y[idx])
        Z = tree.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
        individual_preds.append(Z)

    # 단일 트리
    axes[0].contourf(xx, yy, individual_preds[0], alpha=0.3, cmap="RdYlBu_r")
    axes[0].scatter(X[:, 0], X[:, 1], c=y, cmap="RdYlBu_r", s=15,
                    edgecolors="white", linewidth=0.5)
    axes[0].set_title("단일 트리 (불안정)", fontsize=12, fontweight="bold",
                      color=COLORS["danger"])

    # 3개 트리
    axes[1].contourf(xx, yy, individual_preds[1], alpha=0.3, cmap="RdYlBu_r")
    axes[1].scatter(X[:, 0], X[:, 1], c=y, cmap="RdYlBu_r", s=15,
                    edgecolors="white", linewidth=0.5)
    axes[1].set_title("다른 단일 트리 (다름)", fontsize=12, fontweight="bold",
                      color=COLORS["warning"])

    # 앙상블
    ensemble_pred = (np.array(individual_preds).mean(axis=0) > 0.5).astype(int)
    axes[2].contourf(xx, yy, ensemble_pred, alpha=0.3, cmap="RdYlBu_r")
    axes[2].scatter(X[:, 0], X[:, 1], c=y, cmap="RdYlBu_r", s=15,
                    edgecolors="white", linewidth=0.5)
    axes[2].set_title("앙상블 (안정적)", fontsize=12, fontweight="bold",
                      color=COLORS["success"])

    fig.suptitle("앙상블의 다양성: 개별 모델의 약점을 보완",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "ensemble_diversity.png")


def gen_20_random_forest():
    slug = "20_random-forest"
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification

    np.random.seed(42)
    X, y = make_classification(n_samples=500, n_features=10, n_informative=5,
                               n_redundant=2, random_state=42)

    # Figure 1: 특성 중요도
    fig, ax = make_fig(10, 6)
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X, y)

    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1]
    feature_names = [f"특성 {i+1}" for i in range(X.shape[1])]

    colors_imp = [COLORS["danger"] if v > 0.15 else
                  COLORS["warning"] if v > 0.10 else
                  COLORS["primary"] for v in importances[indices]]

    ax.barh(range(len(indices)), importances[indices], color=colors_imp,
            alpha=0.85, edgecolor="white", height=0.7)
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([feature_names[i] for i in indices], fontsize=11)
    ax.set_xlabel("특성 중요도 (MDI)", fontsize=12)
    ax.set_title("랜덤 포레스트 특성 중요도", fontsize=15, fontweight="bold")
    ax.invert_yaxis()
    save_fig(fig, slug, "rf_feature_importance.png")

    # Figure 2: OOB 오차 vs n_estimators
    fig, ax = make_fig(10, 6)
    n_estimators_range = list(range(10, 501, 10))
    oob_errors = []

    for n in n_estimators_range:
        rf = RandomForestClassifier(n_estimators=n, oob_score=True,
                                     random_state=42, n_jobs=-1)
        rf.fit(X, y)
        oob_errors.append(1 - rf.oob_score_)

    ax.plot(n_estimators_range, oob_errors, color=COLORS["primary"], lw=2)
    ax.fill_between(n_estimators_range, oob_errors, alpha=0.1,
                    color=COLORS["primary"])

    min_idx = np.argmin(oob_errors)
    ax.scatter([n_estimators_range[min_idx]], [oob_errors[min_idx]],
               s=100, c=COLORS["success"], zorder=5)
    ax.annotate(f"최적: {n_estimators_range[min_idx]}개\n오차: {oob_errors[min_idx]:.4f}",
                xy=(n_estimators_range[min_idx], oob_errors[min_idx]),
                xytext=(n_estimators_range[min_idx] + 80, oob_errors[min_idx] + 0.01),
                fontsize=11, fontweight="bold", color=COLORS["success"],
                arrowprops=dict(arrowstyle="->", color=COLORS["success"]))

    ax.set_xlabel("트리 수 (n_estimators)", fontsize=13)
    ax.set_ylabel("OOB 오차율", fontsize=13)
    ax.set_title("OOB 오차 vs 트리 수", fontsize=15, fontweight="bold")
    save_fig(fig, slug, "oob_error_vs_n_estimators.png")


def gen_21_gradient_boosting():
    slug = "21_gradient-boosting"

    # Figure 1: 순차적 잔차 적합
    np.random.seed(42)
    x = np.linspace(0, 10, 100)
    y_true = np.sin(x) + 0.5 * np.cos(2 * x)
    y = y_true + np.random.randn(100) * 0.3

    fig, axes = make_fig_axes(2, 2, 12, 10)

    from sklearn.tree import DecisionTreeRegressor

    residual = y.copy()
    prediction = np.zeros_like(y)
    lr = 0.3

    for i, ax in enumerate(axes.flat):
        tree = DecisionTreeRegressor(max_depth=3)
        tree.fit(x.reshape(-1, 1), residual)
        pred = tree.predict(x.reshape(-1, 1))
        prediction += lr * pred
        residual = y - prediction

        ax.scatter(x, y, c=COLORS["dark"], s=10, alpha=0.3, label="원본 데이터")
        ax.plot(x, prediction, color=COLORS["primary"], lw=2.5,
                label=f"예측 (반복 {i+1})")
        ax.plot(x, y_true, "--", color="#aaa", lw=1, label="실제 함수")
        ax.set_title(f"반복 {i+1}: MSE = {np.mean(residual**2):.4f}",
                     fontsize=12, fontweight="bold")
        ax.legend(fontsize=8, loc="upper right")

    fig.suptitle("그래디언트 부스팅: 잔차를 순차적으로 학습",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "sequential_residual_fitting.png")

    # Figure 2: 학습률 효과
    fig, ax = make_fig(10, 6)
    from sklearn.ensemble import GradientBoostingRegressor

    learning_rates = [0.01, 0.1, 0.3, 1.0]
    lr_colors = [COLORS["primary"], COLORS["success"],
                 COLORS["warning"], COLORS["danger"]]

    for lr_val, c in zip(learning_rates, lr_colors):
        train_scores = []
        gb = GradientBoostingRegressor(n_estimators=200, learning_rate=lr_val,
                                        max_depth=3, random_state=42)
        gb.fit(x.reshape(-1, 1), y)

        # staged_predict로 각 단계 MSE
        for i, y_pred in enumerate(gb.staged_predict(x.reshape(-1, 1))):
            train_scores.append(np.mean((y - y_pred) ** 2))

        ax.plot(range(1, 201), train_scores, color=c, lw=2,
                label=f"η = {lr_val}")

    ax.set_xlabel("부스팅 반복 횟수", fontsize=13)
    ax.set_ylabel("MSE", fontsize=13)
    ax.set_title("학습률에 따른 수렴 속도", fontsize=15, fontweight="bold")
    ax.legend(fontsize=11)
    ax.set_yscale("log")
    save_fig(fig, slug, "learning_rate_effect.png")


def gen_22_xgboost_lightgbm():
    slug = "22_xgboost-lightgbm"

    # Figure 1: 프레임워크 비교 차트
    fig, axes = make_fig_axes(1, 2, 13, 6)

    frameworks = ["XGBoost", "LightGBM", "CatBoost", "sklearn\nGBDT"]
    metrics = {
        "학습 속도\n(상대적)": [0.7, 1.0, 0.6, 0.3],
        "정확도\n(상대적)": [0.95, 0.93, 0.96, 0.85],
    }
    fw_colors = [COLORS["primary"], COLORS["success"],
                 COLORS["purple"], COLORS["secondary"]]

    x_pos = np.arange(len(frameworks))
    width = 0.6

    for ax, (metric, values) in zip(axes, metrics.items()):
        bars = ax.bar(x_pos, values, width, color=fw_colors, alpha=0.85,
                      edgecolor="white")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(frameworks, fontsize=10)
        ax.set_ylabel(metric, fontsize=11)
        ax.set_title(metric, fontsize=13, fontweight="bold")

        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.02,
                    f"{v:.2f}", ha="center", fontsize=10, fontweight="bold")

    fig.suptitle("Gradient Boosting 프레임워크 비교",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "framework_comparison.png")

    # Figure 2: 트리 분할 전략 비교
    fig, axes = make_fig_axes(1, 2, 12, 5)

    # Level-wise (XGBoost)
    ax = axes[0]
    ax.set_xlim(-0.5, 8)
    ax.set_ylim(-0.5, 4)
    ax.axis("off")
    ax.set_title("Level-wise 성장 (XGBoost)\n모든 노드를 균등하게 분할",
                 fontsize=12, fontweight="bold", color=COLORS["primary"])

    # 트리 노드
    positions = {0: (3.5, 3.5), 1: (1.5, 2), 2: (5.5, 2),
                 3: (0.5, 0.5), 4: (2.5, 0.5), 5: (4.5, 0.5), 6: (6.5, 0.5)}

    for idx, (x_p, y_p) in positions.items():
        circle = plt.Circle((x_p, y_p), 0.35, fc=COLORS["primary"],
                             ec="white", lw=2, alpha=0.8)
        ax.add_patch(circle)

    for parent, children in [(0, [1, 2]), (1, [3, 4]), (2, [5, 6])]:
        for child in children:
            ax.plot([positions[parent][0], positions[child][0]],
                    [positions[parent][1] - 0.35, positions[child][1] + 0.35],
                    color="#666", lw=1.5)

    # Leaf-wise (LightGBM)
    ax = axes[1]
    ax.set_xlim(-0.5, 8)
    ax.set_ylim(-0.5, 4)
    ax.axis("off")
    ax.set_title("Leaf-wise 성장 (LightGBM)\n최대 손실 리프만 분할",
                 fontsize=12, fontweight="bold", color=COLORS["success"])

    positions2 = {0: (3.5, 3.5), 1: (1.5, 2), 2: (5.5, 2),
                  3: (0.5, 0.5), 4: (2.5, 0.5)}
    node_colors = [COLORS["success"], COLORS["success"], COLORS["success"],
                   COLORS["success"], COLORS["success"]]
    highlight = {2: COLORS["warning"]}  # 다음 분할 대상

    for idx, (x_p, y_p) in positions2.items():
        c = highlight.get(idx, COLORS["success"])
        circle = plt.Circle((x_p, y_p), 0.35, fc=c, ec="white", lw=2, alpha=0.8)
        ax.add_patch(circle)

    for parent, children in [(0, [1, 2]), (1, [3, 4])]:
        for child in children:
            if child in positions2:
                ax.plot([positions2[parent][0], positions2[child][0]],
                        [positions2[parent][1] - 0.35, positions2[child][1] + 0.35],
                        color="#666", lw=1.5)

    ax.annotate("최대 손실\n→ 분할!", xy=(5.5, 1.65), fontsize=9,
                color=COLORS["danger"], fontweight="bold", ha="center")

    fig.suptitle("트리 분할 전략 비교", fontsize=16, fontweight="bold", y=1.05)
    fig.tight_layout()
    save_fig(fig, slug, "tree_growth_strategy.png")


# ═══════════════════════════════════════════════════════════════════════════
# Group 6: Unsupervised (23–27)
# ═══════════════════════════════════════════════════════════════════════════

def gen_23_kmeans():
    slug = "23_kmeans-clustering"
    from sklearn.cluster import KMeans

    # Figure 1: K-Means 반복 과정
    np.random.seed(42)
    centers = np.array([[2, 2], [8, 3], [5, 8]])
    X = np.vstack([
        np.random.randn(100, 2) * 0.8 + c for c in centers
    ])

    fig, axes = make_fig_axes(2, 2, 12, 10)
    iterations = [1, 2, 3, 10]

    for ax, n_iter in zip(axes.flat, iterations):
        km = KMeans(n_clusters=3, init="random", n_init=1, max_iter=n_iter,
                    random_state=42)
        km.fit(X)
        labels = km.labels_

        for k in range(3):
            mask = labels == k
            ax.scatter(X[mask, 0], X[mask, 1], s=20, alpha=0.6,
                       color=PALETTE[k])
        ax.scatter(km.cluster_centers_[:, 0], km.cluster_centers_[:, 1],
                   s=200, c="white", marker="*", edgecolors="black",
                   linewidth=2, zorder=5)

        ax.set_title(f"반복 {n_iter}회", fontsize=13, fontweight="bold")

    fig.suptitle("K-Means 클러스터링 반복 과정", fontsize=16,
                 fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "kmeans_iterations.png")

    # Figure 2: 엘보우 방법
    fig, ax = make_fig(10, 6)
    inertias = []
    k_range = range(1, 11)

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X)
        inertias.append(km.inertia_)

    ax.plot(list(k_range), inertias, "o-", color=COLORS["primary"], lw=2.5,
            markersize=8)
    ax.axvline(3, ls="--", color=COLORS["danger"], alpha=0.7, lw=1.5)
    ax.annotate("엘보우 포인트\n(K=3)", xy=(3, inertias[2]),
                xytext=(5, inertias[2] + 200),
                fontsize=12, fontweight="bold", color=COLORS["danger"],
                arrowprops=dict(arrowstyle="->", color=COLORS["danger"]))

    ax.set_xlabel("클러스터 수 (K)", fontsize=13)
    ax.set_ylabel("관성 (Inertia)", fontsize=13)
    ax.set_title("엘보우 방법 (Elbow Method): 최적 K 결정",
                 fontsize=15, fontweight="bold")
    save_fig(fig, slug, "elbow_method.png")


def gen_24_advanced_clustering():
    slug = "24_advanced-clustering"
    from sklearn.datasets import make_moons, make_circles
    from sklearn.cluster import DBSCAN, AgglomerativeClustering

    # Figure 1: DBSCAN vs 계층적 클러스터링
    X_moons, _ = make_moons(n_samples=300, noise=0.08, random_state=42)
    X_circles, _ = make_circles(n_samples=300, noise=0.05, factor=0.5,
                                 random_state=42)

    fig, axes = make_fig_axes(2, 2, 12, 10)

    datasets = [(X_moons, "Two Moons"), (X_circles, "Two Circles")]

    for col, (X_data, name) in enumerate(datasets):
        # DBSCAN
        db = DBSCAN(eps=0.2, min_samples=5)
        labels_db = db.fit_predict(X_data)
        for k in set(labels_db):
            mask = labels_db == k
            c = "#aaa" if k == -1 else PALETTE[k % len(PALETTE)]
            marker = "x" if k == -1 else "o"
            axes[0, col].scatter(X_data[mask, 0], X_data[mask, 1], s=20,
                                 c=c, marker=marker, alpha=0.7)
        axes[0, col].set_title(f"DBSCAN - {name}", fontsize=12,
                               fontweight="bold")

        # 계층적
        hc = AgglomerativeClustering(n_clusters=2)
        labels_hc = hc.fit_predict(X_data)
        for k in range(2):
            mask = labels_hc == k
            axes[1, col].scatter(X_data[mask, 0], X_data[mask, 1], s=20,
                                 c=PALETTE[k], alpha=0.7)
        axes[1, col].set_title(f"계층적 클러스터링 - {name}", fontsize=12,
                               fontweight="bold")

    fig.suptitle("고급 클러스터링: 비구형 데이터에서의 성능 비교",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "dbscan_vs_hierarchical.png")

    # Figure 2: DBSCAN eps 파라미터 효과
    fig, axes = make_fig_axes(1, 3, 15, 5)
    eps_values = [0.1, 0.2, 0.5]

    for ax, eps in zip(axes, eps_values):
        db = DBSCAN(eps=eps, min_samples=5)
        labels = db.fit_predict(X_moons)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = (labels == -1).sum()

        for k in set(labels):
            mask = labels == k
            c = "#aaa" if k == -1 else PALETTE[k % len(PALETTE)]
            marker = "x" if k == -1 else "o"
            ax.scatter(X_moons[mask, 0], X_moons[mask, 1], s=20,
                       c=c, marker=marker, alpha=0.7)

        ax.set_title(f"eps={eps}\n클러스터: {n_clusters}, 노이즈: {n_noise}",
                     fontsize=12, fontweight="bold")

    fig.suptitle("DBSCAN: eps 파라미터의 영향", fontsize=16,
                 fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "dbscan_eps_effect.png")


def gen_25_gmm():
    slug = "25_gmm"
    from sklearn.mixture import GaussianMixture

    # Figure 1: GMM 등고선
    np.random.seed(42)
    centers = np.array([[2, 2], [7, 5], [4, 8]])
    covs = [np.array([[1.0, 0.5], [0.5, 1.0]]),
            np.array([[1.5, -0.3], [-0.3, 0.8]]),
            np.array([[0.6, 0], [0, 1.2]])]

    X = np.vstack([
        np.random.multivariate_normal(c, cov, size=100)
        for c, cov in zip(centers, covs)
    ])

    fig, ax = make_fig(10, 8)
    gmm = GaussianMixture(n_components=3, random_state=42)
    gmm.fit(X)
    labels = gmm.predict(X)

    for k in range(3):
        mask = labels == k
        ax.scatter(X[mask, 0], X[mask, 1], s=20, alpha=0.6,
                   color=PALETTE[k])

    xx, yy = np.meshgrid(np.linspace(-2, 12, 200), np.linspace(-2, 12, 200))
    Z = -gmm.score_samples(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    ax.contour(xx, yy, Z, levels=10, colors=COLORS["dark"],
               linewidths=0.5, alpha=0.5)

    # 각 가우시안의 등고선
    for k in range(3):
        mean = gmm.means_[k]
        cov = gmm.covariances_[k]
        eigenvalues, eigenvectors = np.linalg.eig(cov)
        angle = np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0]))

        for n_std in [1, 2]:
            ell = matplotlib.patches.Ellipse(
                mean, 2 * n_std * np.sqrt(eigenvalues[0]),
                2 * n_std * np.sqrt(eigenvalues[1]),
                angle=angle, fill=False, color=PALETTE[k],
                linewidth=2, alpha=0.7)
            ax.add_patch(ell)

    ax.set_xlabel("특성 1", fontsize=13)
    ax.set_ylabel("특성 2", fontsize=13)
    ax.set_title("가우시안 혼합 모델 (GMM) 클러스터링", fontsize=16, fontweight="bold")
    save_fig(fig, slug, "gmm_contours.png")

    # Figure 2: BIC를 이용한 모델 선택
    fig, ax = make_fig(10, 6)
    n_components_range = range(1, 10)
    bics = []
    aics = []

    for n in n_components_range:
        gmm = GaussianMixture(n_components=n, random_state=42)
        gmm.fit(X)
        bics.append(gmm.bic(X))
        aics.append(gmm.aic(X))

    ax.plot(list(n_components_range), bics, "o-", color=COLORS["primary"],
            lw=2.5, label="BIC")
    ax.plot(list(n_components_range), aics, "s--", color=COLORS["secondary"],
            lw=2, label="AIC")

    best_n = list(n_components_range)[np.argmin(bics)]
    ax.axvline(best_n, ls=":", color=COLORS["success"], alpha=0.7, lw=2)
    ax.annotate(f"최적 K = {best_n}", xy=(best_n, min(bics)),
                xytext=(best_n + 2, min(bics) + 100),
                fontsize=12, color=COLORS["success"], fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=COLORS["success"]))

    ax.set_xlabel("가우시안 컴포넌트 수", fontsize=13)
    ax.set_ylabel("정보 기준", fontsize=13)
    ax.set_title("BIC / AIC를 이용한 최적 컴포넌트 수 결정",
                 fontsize=15, fontweight="bold")
    ax.legend(fontsize=11)
    save_fig(fig, slug, "bic_model_selection.png")


def gen_26_pca():
    slug = "26_pca"
    from sklearn.decomposition import PCA
    from sklearn.datasets import load_digits

    digits = load_digits()
    X, y = digits.data, digits.target

    # Figure 1: 누적 분산 비율
    fig, ax = make_fig(10, 6)
    pca = PCA()
    pca.fit(X)

    cumulative_var = np.cumsum(pca.explained_variance_ratio_)
    ax.plot(range(1, len(cumulative_var) + 1), cumulative_var, "o-",
            color=COLORS["primary"], lw=2, markersize=3)
    ax.fill_between(range(1, len(cumulative_var) + 1), cumulative_var,
                    alpha=0.1, color=COLORS["primary"])

    # 95% 라인
    n_95 = np.argmax(cumulative_var >= 0.95) + 1
    ax.axhline(0.95, ls="--", color=COLORS["danger"], alpha=0.7)
    ax.axvline(n_95, ls="--", color=COLORS["danger"], alpha=0.7)
    ax.scatter([n_95], [cumulative_var[n_95 - 1]], s=100, c=COLORS["danger"],
               zorder=5)
    ax.annotate(f"95% 분산: {n_95}개 성분", xy=(n_95, 0.95),
                xytext=(n_95 + 10, 0.8), fontsize=12, fontweight="bold",
                color=COLORS["danger"],
                arrowprops=dict(arrowstyle="->", color=COLORS["danger"]))

    ax.set_xlabel("주성분 수", fontsize=13)
    ax.set_ylabel("누적 설명 분산 비율", fontsize=13)
    ax.set_title("PCA 누적 설명 분산 비율 (Digits 데이터셋)",
                 fontsize=15, fontweight="bold")
    save_fig(fig, slug, "explained_variance_ratio.png")

    # Figure 2: 2D 투영
    fig, ax = make_fig(10, 8)
    pca2 = PCA(n_components=2)
    X_2d = pca2.fit_transform(X)

    scatter = ax.scatter(X_2d[:, 0], X_2d[:, 1], c=y, cmap="tab10", s=10,
                         alpha=0.6)
    plt.colorbar(scatter, ax=ax, label="숫자 (0~9)")

    ax.set_xlabel(f"PC1 ({pca2.explained_variance_ratio_[0]:.1%})", fontsize=13)
    ax.set_ylabel(f"PC2 ({pca2.explained_variance_ratio_[1]:.1%})", fontsize=13)
    ax.set_title("PCA 2D 투영: 손글씨 숫자 데이터 (64차원 → 2차원)",
                 fontsize=15, fontweight="bold")
    save_fig(fig, slug, "pca_2d_projection.png")


def gen_27_tsne_umap():
    slug = "27_tsne-umap"
    from sklearn.manifold import TSNE
    from sklearn.datasets import load_digits

    digits = load_digits()
    X, y = digits.data, digits.target

    # Figure 1: t-SNE (perplexity 비교)
    fig, axes = make_fig_axes(1, 3, 15, 5)
    perplexities = [5, 30, 100]

    for ax, perp in zip(axes, perplexities):
        tsne = TSNE(n_components=2, perplexity=perp, random_state=42,
                    n_iter=1000)
        X_embedded = tsne.fit_transform(X)

        scatter = ax.scatter(X_embedded[:, 0], X_embedded[:, 1], c=y,
                             cmap="tab10", s=5, alpha=0.7)
        ax.set_title(f"perplexity = {perp}", fontsize=13, fontweight="bold")
        ax.set_xticks([])
        ax.set_yticks([])

    fig.suptitle("t-SNE: perplexity 파라미터의 영향 (Digits 데이터셋)",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "tsne_perplexity_comparison.png")

    # Figure 2: t-SNE 최적 결과
    fig, ax = make_fig(10, 8)
    tsne = TSNE(n_components=2, perplexity=30, random_state=42, n_iter=1000)
    X_tsne = tsne.fit_transform(X)

    for digit in range(10):
        mask = y == digit
        ax.scatter(X_tsne[mask, 0], X_tsne[mask, 1], s=15, alpha=0.7,
                   label=str(digit))
        centroid = X_tsne[mask].mean(axis=0)
        ax.annotate(str(digit), xy=centroid, fontsize=14, fontweight="bold",
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8))

    ax.set_title("t-SNE 2D 시각화: 손글씨 숫자 (perplexity=30)",
                 fontsize=15, fontweight="bold")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(fontsize=9, loc="upper right", title="숫자")
    save_fig(fig, slug, "tsne_digits.png")


# ═══════════════════════════════════════════════════════════════════════════
# Group 7: Evaluation (28–31)
# ═══════════════════════════════════════════════════════════════════════════

def gen_28_classification_metrics():
    slug = "28_classification-metrics"
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.metrics import (confusion_matrix, roc_curve, auc,
                                  precision_recall_curve)

    np.random.seed(42)
    X, y = make_classification(n_samples=500, n_features=20, n_informative=10,
                               random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3,
                                                         random_state=42)

    # Figure 1: 혼동 행렬 + ROC
    fig, axes = make_fig_axes(1, 2, 13, 6)

    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_train, y_train)
    y_pred = lr.predict(X_test)
    y_prob = lr.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred)
    im = axes[0].imshow(cm, cmap="Blues", alpha=0.8)
    for i in range(2):
        for j in range(2):
            axes[0].text(j, i, str(cm[i, j]), ha="center", va="center",
                         fontsize=20, fontweight="bold",
                         color="white" if cm[i, j] > cm.max() / 2 else COLORS["dark"])

    axes[0].set_xticks([0, 1])
    axes[0].set_yticks([0, 1])
    axes[0].set_xticklabels(["예측: 음성", "예측: 양성"], fontsize=11)
    axes[0].set_yticklabels(["실제: 음성", "실제: 양성"], fontsize=11)
    axes[0].set_title("혼동 행렬 (Confusion Matrix)", fontsize=14, fontweight="bold")
    plt.colorbar(im, ax=axes[0], shrink=0.8)

    # 라벨 추가
    labels_cm = [["TN", "FP"], ["FN", "TP"]]
    for i in range(2):
        for j in range(2):
            axes[0].text(j, i + 0.25, labels_cm[i][j], ha="center",
                         va="center", fontsize=10,
                         color="white" if cm[i, j] > cm.max() / 2 else "#888")

    # ROC 곡선
    models = {
        "Logistic Regression": lr,
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "SVM (RBF)": SVC(probability=True, random_state=42),
    }
    roc_colors = [COLORS["primary"], COLORS["success"], COLORS["purple"]]

    for (name, model), c in zip(models.items(), roc_colors):
        if name != "Logistic Regression":
            model.fit(X_train, y_train)
        y_score = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_score)
        roc_auc = auc(fpr, tpr)
        axes[1].plot(fpr, tpr, color=c, lw=2,
                     label=f"{name} (AUC={roc_auc:.3f})")

    axes[1].plot([0, 1], [0, 1], "--", color="#aaa", lw=1)
    axes[1].set_xlabel("False Positive Rate", fontsize=12)
    axes[1].set_ylabel("True Positive Rate", fontsize=12)
    axes[1].set_title("ROC 곡선", fontsize=14, fontweight="bold")
    axes[1].legend(fontsize=9, loc="lower right")

    fig.suptitle("분류 평가 지표", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "confusion_matrix_roc.png")

    # Figure 2: Precision-Recall 곡선
    fig, ax = make_fig(10, 6)
    for (name, model), c in zip(models.items(), roc_colors):
        y_score = model.predict_proba(X_test)[:, 1]
        precision, recall, _ = precision_recall_curve(y_test, y_score)
        pr_auc = auc(recall, precision)
        ax.plot(recall, precision, color=c, lw=2,
                label=f"{name} (AP={pr_auc:.3f})")

    ax.set_xlabel("재현율 (Recall)", fontsize=13)
    ax.set_ylabel("정밀도 (Precision)", fontsize=13)
    ax.set_title("Precision-Recall 곡선", fontsize=16, fontweight="bold")
    ax.legend(fontsize=10)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    save_fig(fig, slug, "precision_recall_curve.png")


def gen_29_regression_metrics():
    slug = "29_regression-metrics"

    np.random.seed(42)
    n = 100
    x = np.linspace(0, 10, n)
    y_true = 2 * x + 1 + np.sin(x) * 2
    y_pred = y_true + np.random.randn(n) * 1.5

    # Figure 1: 실제 vs 예측
    fig, axes = make_fig_axes(1, 2, 12, 5)

    axes[0].scatter(y_true, y_pred, c=COLORS["primary"], s=30, alpha=0.7,
                    edgecolors="white")
    line_range = [min(y_true.min(), y_pred.min()),
                  max(y_true.max(), y_pred.max())]
    axes[0].plot(line_range, line_range, "--", color=COLORS["danger"], lw=2,
                 label="y = ŷ (완벽 예측)")
    axes[0].set_xlabel("실제값 (y)", fontsize=12)
    axes[0].set_ylabel("예측값 (ŷ)", fontsize=12)
    axes[0].set_title("실제 vs 예측 산점도", fontsize=14, fontweight="bold")
    axes[0].legend(fontsize=10)

    # 잔차 분포
    residuals = y_true - y_pred
    axes[1].hist(residuals, bins=20, color=COLORS["purple"], alpha=0.7,
                 edgecolor="white", density=True)
    xr = np.linspace(residuals.min(), residuals.max(), 100)
    axes[1].plot(xr, stats.norm.pdf(xr, residuals.mean(), residuals.std()),
                 color=COLORS["danger"], lw=2, label="정규 분포")
    axes[1].axvline(0, ls="--", color=COLORS["dark"], alpha=0.5)
    axes[1].set_xlabel("잔차 (y - ŷ)", fontsize=12)
    axes[1].set_ylabel("밀도", fontsize=12)
    axes[1].set_title("잔차 분포", fontsize=14, fontweight="bold")
    axes[1].legend(fontsize=10)

    fig.suptitle("회귀 모델 평가", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "actual_vs_predicted.png")

    # Figure 2: 회귀 메트릭 비교
    fig, ax = make_fig(10, 6)

    from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                                  r2_score, median_absolute_error)

    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    medae = median_absolute_error(y_true, y_pred)

    metrics = ["MAE", "RMSE", "MedAE"]
    values = [mae, rmse, medae]
    bar_colors = [COLORS["primary"], COLORS["secondary"], COLORS["success"]]

    bars = ax.bar(metrics, values, color=bar_colors, alpha=0.85,
                  edgecolor="white", width=0.5)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.05,
                f"{v:.3f}", ha="center", fontsize=13, fontweight="bold")

    ax.text(0.95, 0.95, f"R² = {r2:.4f}", transform=ax.transAxes,
            fontsize=14, fontweight="bold", ha="right", va="top",
            bbox=dict(boxstyle="round", fc=COLORS["light"], alpha=0.8))

    ax.set_ylabel("오차 값", fontsize=13)
    ax.set_title("회귀 평가 메트릭 비교", fontsize=15, fontweight="bold")
    save_fig(fig, slug, "regression_metrics_comparison.png")


def gen_30_cross_validation():
    slug = "30_cross-validation"

    # Figure 1: K-Fold 시각화
    fig, ax = make_fig(12, 6)
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 6)
    ax.axis("off")
    ax.set_title("5-Fold 교차검증", fontsize=16, fontweight="bold", pad=20)

    n_folds = 5
    fold_width = 10 / n_folds

    for fold in range(n_folds):
        y_pos = n_folds - fold - 0.5
        ax.text(-0.4, y_pos, f"Fold {fold + 1}", ha="right", va="center",
                fontsize=11, fontweight="bold")

        for k in range(n_folds):
            x_start = k * fold_width
            if k == fold:
                color = COLORS["secondary"]
                label = "검증"
            else:
                color = COLORS["primary"]
                label = "훈련"

            rect = FancyBboxPatch((x_start + 0.05, y_pos - 0.3),
                                   fold_width - 0.1, 0.6,
                                   boxstyle="round,pad=0.05",
                                   facecolor=color, alpha=0.8,
                                   edgecolor="white", linewidth=1)
            ax.add_patch(rect)

    # 범례
    ax.add_patch(FancyBboxPatch((7, -0.3), 0.8, 0.3,
                                 boxstyle="round,pad=0.05",
                                 facecolor=COLORS["primary"], alpha=0.8))
    ax.text(8, -0.15, "훈련 세트", fontsize=10, va="center")
    ax.add_patch(FancyBboxPatch((7, -0.7), 0.8, 0.3,
                                 boxstyle="round,pad=0.05",
                                 facecolor=COLORS["secondary"], alpha=0.8))
    ax.text(8, -0.55, "검증 세트", fontsize=10, va="center")

    save_fig(fig, slug, "kfold_visualization.png")

    # Figure 2: Validation Curve
    fig, ax = make_fig(10, 6)
    from sklearn.datasets import make_classification
    from sklearn.model_selection import validation_curve
    from sklearn.tree import DecisionTreeClassifier

    X, y = make_classification(n_samples=500, n_features=20, n_informative=10,
                               random_state=42)

    param_range = range(1, 20)
    train_scores, test_scores = validation_curve(
        DecisionTreeClassifier(random_state=42), X, y,
        param_name="max_depth", param_range=param_range,
        cv=5, scoring="accuracy")

    train_mean = train_scores.mean(axis=1)
    train_std = train_scores.std(axis=1)
    test_mean = test_scores.mean(axis=1)
    test_std = test_scores.std(axis=1)

    ax.plot(list(param_range), train_mean, "o-", color=COLORS["primary"],
            lw=2, label="훈련 점수")
    ax.fill_between(list(param_range), train_mean - train_std,
                    train_mean + train_std, alpha=0.15, color=COLORS["primary"])
    ax.plot(list(param_range), test_mean, "o-", color=COLORS["danger"],
            lw=2, label="검증 점수")
    ax.fill_between(list(param_range), test_mean - test_std,
                    test_mean + test_std, alpha=0.15, color=COLORS["danger"])

    best_depth = list(param_range)[np.argmax(test_mean)]
    ax.axvline(best_depth, ls="--", color=COLORS["success"], alpha=0.7)
    ax.annotate(f"최적 깊이 = {best_depth}", xy=(best_depth, max(test_mean)),
                xytext=(best_depth + 3, max(test_mean) - 0.03),
                fontsize=11, color=COLORS["success"], fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=COLORS["success"]))

    ax.set_xlabel("트리 깊이 (max_depth)", fontsize=13)
    ax.set_ylabel("정확도", fontsize=13)
    ax.set_title("검증 곡선 (Validation Curve)", fontsize=15, fontweight="bold")
    ax.legend(fontsize=11)
    save_fig(fig, slug, "validation_curve.png")


def gen_31_model_interpretability():
    slug = "31_model-interpretability"
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification

    np.random.seed(42)
    feature_names = ["나이", "연봉", "근무연수", "교육수준", "부서코드",
                     "성과점수", "야근빈도", "출퇴근거리", "만족도", "프로젝트수"]
    X, y = make_classification(n_samples=500, n_features=10, n_informative=6,
                               random_state=42)

    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X, y)

    # Figure 1: 특성 중요도 + Permutation importance 스타일
    fig, axes = make_fig_axes(1, 2, 13, 6)

    importances = rf.feature_importances_
    sorted_idx = np.argsort(importances)

    colors_imp = [COLORS["danger"] if importances[i] > 0.15 else
                  COLORS["warning"] if importances[i] > 0.08 else
                  COLORS["primary"] for i in sorted_idx]

    axes[0].barh(range(len(sorted_idx)), importances[sorted_idx],
                 color=colors_imp, alpha=0.85, edgecolor="white")
    axes[0].set_yticks(range(len(sorted_idx)))
    axes[0].set_yticklabels([feature_names[i] for i in sorted_idx], fontsize=10)
    axes[0].set_xlabel("MDI 중요도", fontsize=11)
    axes[0].set_title("특성 중요도 (MDI)", fontsize=13, fontweight="bold")

    # Partial dependence 스타일 (수동 구현)
    feature_idx = np.argmax(importances)
    x_range = np.linspace(X[:, feature_idx].min(), X[:, feature_idx].max(), 50)
    pdp = []
    for val in x_range:
        X_temp = X.copy()
        X_temp[:, feature_idx] = val
        pdp.append(rf.predict_proba(X_temp)[:, 1].mean())

    axes[1].plot(x_range, pdp, color=COLORS["primary"], lw=2.5)
    axes[1].fill_between(x_range, pdp, alpha=0.15, color=COLORS["primary"])
    axes[1].set_xlabel(f"{feature_names[feature_idx]}", fontsize=12)
    axes[1].set_ylabel("예측 확률 (클래스 1)", fontsize=12)
    axes[1].set_title("부분 의존성 플롯 (PDP)", fontsize=13, fontweight="bold")

    fig.suptitle("모델 해석가능성 (Model Interpretability)",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "interpretability_overview.png")

    # Figure 2: SHAP-style summary (수동 근사)
    fig, ax = make_fig(10, 7)

    # SHAP 값 근사 (실제 SHAP 대신 간단 permutation-based)
    np.random.seed(42)
    n_show = 200
    shap_approx = np.random.randn(n_show, len(feature_names))
    # 중요도에 비례하도록 스케일
    for j in range(len(feature_names)):
        shap_approx[:, j] *= importances[j] * 5

    sorted_idx = np.argsort(np.abs(shap_approx).mean(axis=0))[::-1]

    for rank, feat_idx in enumerate(sorted_idx):
        y_positions = np.ones(n_show) * rank + np.random.randn(n_show) * 0.1
        feat_vals = X[:n_show, feat_idx]
        colors = plt.cm.coolwarm((feat_vals - feat_vals.min()) /
                                  (feat_vals.max() - feat_vals.min() + 1e-10))
        ax.scatter(shap_approx[:n_show, feat_idx], y_positions,
                   c=colors, s=5, alpha=0.6)

    ax.set_yticks(range(len(feature_names)))
    ax.set_yticklabels([feature_names[i] for i in sorted_idx], fontsize=10)
    ax.set_xlabel("SHAP 값 (모델 출력에 대한 영향)", fontsize=12)
    ax.set_title("SHAP Summary Plot (근사)", fontsize=15, fontweight="bold")
    ax.axvline(0, ls="-", color="#666", lw=0.5)
    ax.invert_yaxis()

    # 컬러바
    sm = plt.cm.ScalarMappable(cmap="coolwarm")
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6)
    cbar.set_label("특성 값 (낮음 → 높음)", fontsize=10)

    save_fig(fig, slug, "shap_summary_plot.png")


# ═══════════════════════════════════════════════════════════════════════════
# Group 8: Advanced (37–51)
# ═══════════════════════════════════════════════════════════════════════════

def gen_37_bayesian_ml():
    slug = "37_bayesian-ml"

    # Figure 1: 사전/사후 분포 업데이트
    fig, axes = make_fig_axes(1, 3, 15, 5)
    x = np.linspace(-2, 6, 300)

    # 데이터 양에 따른 사후 분포 변화
    true_mean = 3.0
    prior_mean, prior_var = 0.0, 4.0
    obs_var = 1.0

    data_sizes = [0, 5, 50]
    titles = ["사전 분포\n(데이터 없음)", "5개 관측 후\n사후 분포",
              "50개 관측 후\n사후 분포"]
    colors_bayes = [COLORS["primary"], COLORS["secondary"], COLORS["success"]]

    for ax, n_data, title, c in zip(axes, data_sizes, titles, colors_bayes):
        if n_data == 0:
            post_mean = prior_mean
            post_var = prior_var
        else:
            np.random.seed(42)
            data = np.random.normal(true_mean, np.sqrt(obs_var), n_data)
            post_var = 1 / (1 / prior_var + n_data / obs_var)
            post_mean = post_var * (prior_mean / prior_var +
                                     data.sum() / obs_var)

        pdf = stats.norm.pdf(x, post_mean, np.sqrt(post_var))
        ax.fill_between(x, pdf, alpha=0.4, color=c)
        ax.plot(x, pdf, color=c, lw=2.5)
        ax.axvline(true_mean, ls="--", color=COLORS["danger"], alpha=0.5,
                   lw=1.5, label=f"실제 값 (μ={true_mean})")
        ax.axvline(post_mean, ls="-.", color=c, alpha=0.7, lw=1.5,
                   label=f"추정 평균 ({post_mean:.2f})")
        ax.set_title(title, fontsize=13, fontweight="bold", color=c)
        ax.legend(fontsize=8)

    fig.suptitle("베이지안 ML: 데이터에 의한 사후 분포 업데이트",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "prior_posterior_update.png")

    # Figure 2: 베이지안 선형 회귀 불확실성
    fig, ax = make_fig(10, 6)
    np.random.seed(42)
    x_train = np.sort(np.random.rand(10)) * 8
    y_train = 2 * x_train + 1 + np.random.randn(10) * 1.5
    x_plot = np.linspace(-1, 9, 200)

    # 여러 개의 가능한 회귀선
    for _ in range(50):
        idx = np.random.choice(len(x_train), size=len(x_train), replace=True)
        coeffs = np.polyfit(x_train[idx], y_train[idx], 1)
        ax.plot(x_plot, np.polyval(coeffs, x_plot), color=COLORS["primary"],
                alpha=0.08, lw=1)

    # 주 예측선
    coeffs_main = np.polyfit(x_train, y_train, 1)
    ax.plot(x_plot, np.polyval(coeffs_main, x_plot), color=COLORS["danger"],
            lw=2.5, label="평균 예측")
    ax.scatter(x_train, y_train, c=COLORS["dark"], s=60, zorder=5,
               edgecolors="white", linewidth=1.5, label="훈련 데이터")

    ax.set_xlabel("x", fontsize=13)
    ax.set_ylabel("y", fontsize=13)
    ax.set_title("베이지안 회귀: 예측 불확실성 시각화",
                 fontsize=15, fontweight="bold")
    ax.legend(fontsize=11)
    save_fig(fig, slug, "bayesian_regression_uncertainty.png")


def gen_38_semi_supervised():
    slug = "38_semi-supervised-learning"
    from sklearn.datasets import make_moons
    from sklearn.semi_supervised import LabelSpreading

    # Figure 1: 라벨 전파
    np.random.seed(42)
    X, y = make_moons(n_samples=300, noise=0.1, random_state=42)

    # 일부만 라벨 부여
    labeled_mask = np.zeros(len(y), dtype=bool)
    labeled_mask[[0, 10, 150, 160]] = True
    y_partial = y.copy()
    y_partial[~labeled_mask] = -1

    fig, axes = make_fig_axes(1, 3, 15, 5)

    # 원본 + 라벨
    axes[0].scatter(X[~labeled_mask, 0], X[~labeled_mask, 1], c="#aaa",
                    s=20, alpha=0.5, label="비라벨 데이터")
    axes[0].scatter(X[labeled_mask, 0], X[labeled_mask, 1],
                    c=[PALETTE[yi] for yi in y[labeled_mask]],
                    s=100, edgecolors="black", linewidth=2, zorder=5,
                    label="라벨 데이터")
    axes[0].set_title("초기 상태\n(4개만 라벨)", fontsize=13, fontweight="bold")
    axes[0].legend(fontsize=8)

    # 라벨 전파 후
    ls = LabelSpreading(kernel="knn", n_neighbors=7, alpha=0.2)
    ls.fit(X, y_partial)
    y_spread = ls.predict(X)

    axes[1].scatter(X[:, 0], X[:, 1], c=[PALETTE[int(yi)] for yi in y_spread],
                    s=20, alpha=0.7)
    axes[1].scatter(X[labeled_mask, 0], X[labeled_mask, 1],
                    c=[PALETTE[yi] for yi in y[labeled_mask]],
                    s=100, edgecolors="black", linewidth=2, zorder=5)
    axes[1].set_title("라벨 전파 후", fontsize=13, fontweight="bold",
                      color=COLORS["success"])

    # 실제 라벨
    axes[2].scatter(X[:, 0], X[:, 1], c=[PALETTE[yi] for yi in y],
                    s=20, alpha=0.7)
    axes[2].set_title("실제 라벨\n(정답)", fontsize=13, fontweight="bold",
                      color=COLORS["primary"])

    fig.suptitle("반지도 학습: 라벨 전파 (Label Spreading)",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "label_propagation.png")

    # Figure 2: 라벨 비율 효과
    fig, ax = make_fig(10, 6)
    label_fractions = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]
    accuracies = []

    for frac in label_fractions:
        np.random.seed(42)
        n_labeled = max(4, int(len(y) * frac))
        labeled_idx = np.random.choice(len(y), n_labeled, replace=False)
        y_semi = np.full(len(y), -1)
        y_semi[labeled_idx] = y[labeled_idx]

        ls = LabelSpreading(kernel="knn", n_neighbors=7, alpha=0.2)
        ls.fit(X, y_semi)
        acc = (ls.predict(X) == y).mean()
        accuracies.append(acc)

    ax.plot([f * 100 for f in label_fractions], accuracies, "o-",
            color=COLORS["primary"], lw=2.5, markersize=8)
    ax.fill_between([f * 100 for f in label_fractions], accuracies,
                    alpha=0.1, color=COLORS["primary"])

    ax.set_xlabel("라벨 데이터 비율 (%)", fontsize=13)
    ax.set_ylabel("정확도", fontsize=13)
    ax.set_title("라벨 비율에 따른 반지도 학습 성능", fontsize=15, fontweight="bold")
    ax.set_ylim(0.5, 1.05)
    save_fig(fig, slug, "label_ratio_effect.png")


def gen_39_topic_modeling():
    slug = "39_topic-modeling"

    # Figure 1: 토픽-단어 분포 히트맵
    fig, ax = make_fig(12, 6)
    np.random.seed(42)

    topics = ["경제/금융", "스포츠", "기술/IT", "정치", "엔터테인먼트"]
    words = ["주식", "성장", "경기", "선수", "기술", "정부",
             "영화", "투자", "골", "AI", "정책", "음악",
             "시장", "리그", "데이터", "선거", "앨범"]

    # 토픽-단어 확률 행렬
    topic_word = np.random.dirichlet(np.ones(len(words)) * 0.3,
                                      size=len(topics))
    # 특정 토픽에 특정 단어 강화
    topic_word[0, [0, 1, 7, 12]] *= 5  # 경제
    topic_word[1, [2, 3, 8, 13]] *= 5  # 스포츠
    topic_word[2, [4, 9, 14]] *= 5  # IT
    topic_word[3, [5, 10, 15]] *= 5  # 정치
    topic_word[4, [6, 11, 16]] *= 5  # 엔터
    topic_word = topic_word / topic_word.sum(axis=1, keepdims=True)

    im = ax.imshow(topic_word, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(words)))
    ax.set_xticklabels(words, fontsize=9, rotation=45, ha="right")
    ax.set_yticks(range(len(topics)))
    ax.set_yticklabels(topics, fontsize=11)
    ax.set_title("토픽-단어 분포 히트맵 (LDA)", fontsize=15, fontweight="bold")
    plt.colorbar(im, ax=ax, label="P(단어|토픽)", shrink=0.8)
    fig.tight_layout()
    save_fig(fig, slug, "topic_word_heatmap.png")

    # Figure 2: 문서별 토픽 분포
    fig, ax = make_fig(10, 6)
    np.random.seed(42)
    n_docs = 10
    doc_topics = np.random.dirichlet(np.ones(len(topics)) * 0.5, size=n_docs)

    x_pos = np.arange(n_docs)
    bottom = np.zeros(n_docs)
    topic_colors = [COLORS["primary"], COLORS["success"], COLORS["secondary"],
                    COLORS["purple"], COLORS["danger"]]

    for i, (topic, c) in enumerate(zip(topics, topic_colors)):
        ax.bar(x_pos, doc_topics[:, i], bottom=bottom, color=c,
               alpha=0.85, label=topic, edgecolor="white", width=0.7)
        bottom += doc_topics[:, i]

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"문서 {i+1}" for i in range(n_docs)], fontsize=10)
    ax.set_ylabel("토픽 비율", fontsize=12)
    ax.set_title("문서별 토픽 구성 비율", fontsize=15, fontweight="bold")
    ax.legend(fontsize=9, loc="upper right", bbox_to_anchor=(1.15, 1))
    fig.tight_layout()
    save_fig(fig, slug, "document_topic_distribution.png")


def gen_40_kernel_methods():
    slug = "40_kernel-methods"
    from sklearn.datasets import make_circles

    # Figure 1: 커널 변환 시각화
    X, y = make_circles(n_samples=200, noise=0.08, factor=0.5, random_state=42)

    fig = plt.figure(figsize=(15, 5))
    axes = [fig.add_subplot(131), fig.add_subplot(132, projection='3d'),
            fig.add_subplot(133)]

    # 2D 원본
    axes[0].scatter(X[y == 0, 0], X[y == 0, 1], c=COLORS["primary"], s=20,
                    alpha=0.7, label="Class 0")
    axes[0].scatter(X[y == 1, 0], X[y == 1, 1], c=COLORS["danger"], s=20,
                    alpha=0.7, label="Class 1")
    axes[0].set_title("원본 2D 데이터\n(선형 분리 불가)", fontsize=12,
                      fontweight="bold")
    axes[0].legend(fontsize=9)

    # 3D 변환 (φ(x) = [x₁, x₂, x₁² + x₂²])
    X_3d = np.column_stack([X[:, 0], X[:, 1],
                             X[:, 0] ** 2 + X[:, 1] ** 2])
    axes[1].scatter(X_3d[y == 0, 0], X_3d[y == 0, 1], X_3d[y == 0, 2],
                    c=COLORS["primary"], s=20, alpha=0.5)
    axes[1].scatter(X_3d[y == 1, 0], X_3d[y == 1, 1], X_3d[y == 1, 2],
                    c=COLORS["danger"], s=20, alpha=0.5)
    axes[1].set_title("커널 변환 후 3D\n(선형 분리 가능)", fontsize=12,
                      fontweight="bold")
    axes[1].set_xlabel("x₁", fontsize=9)
    axes[1].set_ylabel("x₂", fontsize=9)
    axes[1].set_zlabel("x₁²+x₂²", fontsize=9)

    # RBF 커널 SVM
    from sklearn.svm import SVC
    svm = SVC(kernel="rbf", gamma=2)
    svm.fit(X, y)
    xx, yy = np.meshgrid(np.linspace(-1.5, 1.5, 200),
                          np.linspace(-1.5, 1.5, 200))
    Z = svm.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

    axes[2].contourf(xx, yy, Z, alpha=0.3, cmap="RdYlBu_r")
    axes[2].scatter(X[y == 0, 0], X[y == 0, 1], c=COLORS["primary"], s=20)
    axes[2].scatter(X[y == 1, 0], X[y == 1, 1], c=COLORS["danger"], s=20)
    axes[2].set_title("RBF 커널 SVM\n결정 경계", fontsize=12, fontweight="bold")

    fig.suptitle("커널 방법: 고차원 매핑을 통한 비선형 분류",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "kernel_transformation.png")

    # Figure 2: 다양한 커널 비교
    fig, axes = make_fig_axes(1, 3, 15, 5)
    kernels = [("linear", "선형 커널"), ("poly", "다항 커널 (d=3)"),
               ("rbf", "RBF 커널")]
    kern_colors = [COLORS["primary"], COLORS["secondary"], COLORS["success"]]

    for ax, (kernel, name), c in zip(axes, kernels, kern_colors):
        svm = SVC(kernel=kernel, degree=3, gamma=2)
        svm.fit(X, y)
        Z = svm.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

        ax.contourf(xx, yy, Z, alpha=0.3, cmap="RdYlBu_r")
        ax.scatter(X[y == 0, 0], X[y == 0, 1], c=COLORS["primary"], s=15)
        ax.scatter(X[y == 1, 0], X[y == 1, 1], c=COLORS["danger"], s=15)
        acc = svm.score(X, y)
        ax.set_title(f"{name}\n정확도: {acc:.2%}", fontsize=12,
                     fontweight="bold")

    fig.suptitle("SVM 커널 비교 (원형 데이터)", fontsize=16,
                 fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "kernel_comparison.png")


def gen_41_time_series():
    slug = "41_time-series-ml"

    # Figure 1: 시계열 분해
    np.random.seed(42)
    t = np.arange(365 * 2)
    trend = 0.02 * t + 10
    seasonal = 5 * np.sin(2 * np.pi * t / 365)
    noise = np.random.randn(len(t)) * 1.5
    series = trend + seasonal + noise

    fig, axes = make_fig_axes(4, 1, 12, 10, sharex=True)

    axes[0].plot(t, series, color=COLORS["primary"], lw=1)
    axes[0].set_title("원본 시계열", fontsize=12, fontweight="bold")

    axes[1].plot(t, trend, color=COLORS["danger"], lw=2)
    axes[1].set_title("추세 (Trend)", fontsize=12, fontweight="bold")

    axes[2].plot(t, seasonal, color=COLORS["success"], lw=1.5)
    axes[2].set_title("계절성 (Seasonality)", fontsize=12, fontweight="bold")

    axes[3].plot(t, noise, color="#aaa", lw=0.8)
    axes[3].set_title("잔차 (Residual)", fontsize=12, fontweight="bold")
    axes[3].set_xlabel("일 (Day)", fontsize=12)

    fig.suptitle("시계열 분해 (Time Series Decomposition)",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "time_series_decomposition.png")

    # Figure 2: 자기상관 함수
    fig, axes = make_fig_axes(1, 2, 12, 5)

    # ACF
    max_lag = 50
    autocorr = [np.corrcoef(series[:-lag], series[lag:])[0, 1]
                for lag in range(1, max_lag + 1)]

    axes[0].bar(range(1, max_lag + 1), autocorr, color=COLORS["primary"],
                alpha=0.7, width=0.8)
    axes[0].axhline(0, color="#666", lw=0.5)
    axes[0].axhline(1.96 / np.sqrt(len(series)), ls="--", color=COLORS["danger"],
                    alpha=0.5)
    axes[0].axhline(-1.96 / np.sqrt(len(series)), ls="--", color=COLORS["danger"],
                    alpha=0.5)
    axes[0].set_xlabel("래그 (Lag)", fontsize=11)
    axes[0].set_ylabel("상관계수", fontsize=11)
    axes[0].set_title("자기상관 함수 (ACF)", fontsize=13, fontweight="bold")

    # PACF (간단 근사)
    pacf = autocorr.copy()
    for i in range(2, len(pacf)):
        pacf[i] = pacf[i] - pacf[0] * pacf[i-1]  # 간단 근사

    axes[1].bar(range(1, max_lag + 1), pacf, color=COLORS["secondary"],
                alpha=0.7, width=0.8)
    axes[1].axhline(0, color="#666", lw=0.5)
    axes[1].axhline(1.96 / np.sqrt(len(series)), ls="--", color=COLORS["danger"],
                    alpha=0.5)
    axes[1].axhline(-1.96 / np.sqrt(len(series)), ls="--", color=COLORS["danger"],
                    alpha=0.5)
    axes[1].set_xlabel("래그 (Lag)", fontsize=11)
    axes[1].set_ylabel("편상관계수", fontsize=11)
    axes[1].set_title("편자기상관 함수 (PACF)", fontsize=13, fontweight="bold")

    fig.suptitle("시계열 상관 분석", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "autocorrelation.png")


def gen_42_recommendation():
    slug = "42_recommendation-systems"

    # Figure 1: 사용자-아이템 행렬
    fig, ax = make_fig(10, 6)
    np.random.seed(42)
    n_users, n_items = 8, 10
    ratings = np.random.choice([0, 1, 2, 3, 4, 5], size=(n_users, n_items),
                                p=[0.4, 0.05, 0.1, 0.15, 0.15, 0.15])
    mask = ratings > 0

    im = ax.imshow(np.where(mask, ratings, np.nan), cmap="YlOrRd",
                   aspect="auto", vmin=1, vmax=5)
    ax.imshow(np.where(~mask, 0, np.nan), cmap="Greys", aspect="auto",
              alpha=0.3, vmin=0, vmax=1)

    for i in range(n_users):
        for j in range(n_items):
            if mask[i, j]:
                ax.text(j, i, str(ratings[i, j]), ha="center", va="center",
                        fontsize=10, fontweight="bold")
            else:
                ax.text(j, i, "?", ha="center", va="center",
                        fontsize=10, color="#aaa")

    ax.set_xticks(range(n_items))
    ax.set_xticklabels([f"아이템{i+1}" for i in range(n_items)], fontsize=9)
    ax.set_yticks(range(n_users))
    ax.set_yticklabels([f"사용자{i+1}" for i in range(n_users)], fontsize=10)
    ax.set_title("사용자-아이템 평점 행렬", fontsize=15, fontweight="bold")
    plt.colorbar(im, ax=ax, label="평점", shrink=0.8)
    save_fig(fig, slug, "user_item_matrix.png")

    # Figure 2: 협업 필터링 개념도
    fig, ax = make_fig(10, 7)
    ax.set_xlim(-1, 10)
    ax.set_ylim(-0.5, 6)
    ax.axis("off")
    ax.set_title("협업 필터링 (Collaborative Filtering)", fontsize=16,
                 fontweight="bold", pad=20)

    # 사용자 노드
    user_positions = [(1, 5), (1, 3), (1, 1)]
    for i, (x, y) in enumerate(user_positions):
        circle = plt.Circle((x, y), 0.4, fc=COLORS["primary"],
                             ec="white", lw=2, alpha=0.8)
        ax.add_patch(circle)
        ax.text(x, y, f"U{i+1}", ha="center", va="center",
                fontsize=10, color="white", fontweight="bold")

    # 아이템 노드
    item_positions = [(8, 5), (8, 3), (8, 1)]
    for i, (x, y) in enumerate(item_positions):
        rect = FancyBboxPatch((x - 0.45, y - 0.35), 0.9, 0.7,
                               boxstyle="round,pad=0.1",
                               facecolor=COLORS["secondary"],
                               alpha=0.8, edgecolor="white")
        ax.add_patch(rect)
        ax.text(x, y, f"I{i+1}", ha="center", va="center",
                fontsize=10, color="white", fontweight="bold")

    # 연결선 (알려진 평점)
    connections = [(0, 0, "5"), (0, 1, "4"), (1, 0, "4"), (1, 2, "3"),
                   (2, 1, "5")]
    for u, i, rating in connections:
        ax.plot([user_positions[u][0] + 0.4, item_positions[i][0] - 0.45],
                [user_positions[u][1], item_positions[i][1]],
                color="#666", lw=1.5, alpha=0.6)
        mid_x = (user_positions[u][0] + item_positions[i][0]) / 2
        mid_y = (user_positions[u][1] + item_positions[i][1]) / 2
        ax.text(mid_x, mid_y, f"★{rating}", ha="center", fontsize=9,
                color=COLORS["warning"], fontweight="bold")

    # 예측 연결선
    ax.plot([user_positions[2][0] + 0.4, item_positions[2][0] - 0.45],
            [user_positions[2][1], item_positions[2][1]],
            color=COLORS["danger"], lw=2, ls="--", alpha=0.8)
    ax.text(4.5, 0.5, "예측: ★?", ha="center", fontsize=11,
            color=COLORS["danger"], fontweight="bold")

    # 유사도 표시
    ax.annotate("유사한\n사용자", xy=(1, 3.5), xytext=(3, 4.5),
                fontsize=10, color=COLORS["success"],
                arrowprops=dict(arrowstyle="<->", color=COLORS["success"], lw=2),
                fontweight="bold")

    save_fig(fig, slug, "collaborative_filtering.png")


def gen_43_nlp_traditional():
    slug = "43_nlp-traditional-ml"

    # Figure 1: TF-IDF 가중치 시각화
    fig, axes = make_fig_axes(1, 2, 13, 6)

    # 단어 빈도 (예시)
    words = ["머신러닝", "데이터", "모델", "학습", "알고리즘",
             "신경망", "분류", "예측", "특성", "최적화"]
    tf_values = [0.15, 0.12, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]
    idf_values = [2.5, 1.2, 1.8, 1.0, 3.0, 3.5, 2.0, 1.5, 2.8, 3.2]
    tfidf_values = [t * i for t, i in zip(tf_values, idf_values)]

    # TF-IDF 바 차트
    sorted_idx = np.argsort(tfidf_values)[::-1]
    colors_tfidf = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(words)))

    axes[0].barh(range(len(words)), [tfidf_values[i] for i in sorted_idx],
                 color=[colors_tfidf[j] for j in range(len(words))],
                 edgecolor="white", height=0.7)
    axes[0].set_yticks(range(len(words)))
    axes[0].set_yticklabels([words[i] for i in sorted_idx], fontsize=11)
    axes[0].set_xlabel("TF-IDF 가중치", fontsize=11)
    axes[0].set_title("TF-IDF 단어 가중치", fontsize=13, fontweight="bold")
    axes[0].invert_yaxis()

    # TF vs IDF 산점도
    axes[1].scatter(tf_values, idf_values, s=[v * 1000 for v in tfidf_values],
                    c=tfidf_values, cmap="YlOrRd", alpha=0.7, edgecolors="white")
    for i, word in enumerate(words):
        axes[1].annotate(word, (tf_values[i], idf_values[i]),
                         fontsize=9, ha="center",
                         xytext=(0, 8), textcoords="offset points")
    axes[1].set_xlabel("TF (단어 빈도)", fontsize=11)
    axes[1].set_ylabel("IDF (역문서 빈도)", fontsize=11)
    axes[1].set_title("TF vs IDF (크기=TF-IDF)", fontsize=13, fontweight="bold")

    fig.suptitle("TF-IDF: 텍스트 특성 추출", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "tfidf_visualization.png")

    # Figure 2: 단어 빈도 분포 (지프 법칙)
    fig, ax = make_fig(10, 6)
    np.random.seed(42)
    rank = np.arange(1, 101)
    freq = 1000 / rank ** 1.1 + np.random.randn(100) * 5

    ax.loglog(rank, freq, "o", color=COLORS["primary"], markersize=5, alpha=0.7)
    ax.loglog(rank, 1000 / rank ** 1.0, "--", color=COLORS["danger"], lw=2,
              label="지프 법칙 (이론)")
    ax.set_xlabel("단어 순위 (Rank)", fontsize=13)
    ax.set_ylabel("빈도 (Frequency)", fontsize=13)
    ax.set_title("지프 법칙 (Zipf's Law): 단어 빈도 분포",
                 fontsize=15, fontweight="bold")
    ax.legend(fontsize=11)
    save_fig(fig, slug, "zipf_law.png")


def gen_44_anomaly_detection():
    slug = "44_anomaly-detection"
    from sklearn.ensemble import IsolationForest
    from sklearn.neighbors import LocalOutlierFactor

    # Figure 1: Isolation Forest
    np.random.seed(42)
    X_normal = np.random.randn(300, 2) * 1.5 + np.array([5, 5])
    X_anomaly = np.random.uniform(0, 12, (20, 2))
    X = np.vstack([X_normal, X_anomaly])

    fig, axes = make_fig_axes(1, 2, 12, 6)

    # Isolation Forest
    iso = IsolationForest(contamination=0.1, random_state=42)
    y_pred_iso = iso.fit_predict(X)

    axes[0].scatter(X[y_pred_iso == 1, 0], X[y_pred_iso == 1, 1],
                    c=COLORS["primary"], s=20, alpha=0.6, label="정상")
    axes[0].scatter(X[y_pred_iso == -1, 0], X[y_pred_iso == -1, 1],
                    c=COLORS["danger"], s=40, marker="x", label="이상치")

    xx, yy = np.meshgrid(np.linspace(-2, 14, 200), np.linspace(-2, 14, 200))
    Z = iso.decision_function(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    axes[0].contour(xx, yy, Z, levels=[0], colors=[COLORS["danger"]],
                    linewidths=2, linestyles="--")

    axes[0].set_title("Isolation Forest", fontsize=14, fontweight="bold")
    axes[0].legend(fontsize=10)

    # LOF
    lof = LocalOutlierFactor(n_neighbors=20, contamination=0.1)
    y_pred_lof = lof.fit_predict(X)

    axes[1].scatter(X[y_pred_lof == 1, 0], X[y_pred_lof == 1, 1],
                    c=COLORS["primary"], s=20, alpha=0.6, label="정상")
    axes[1].scatter(X[y_pred_lof == -1, 0], X[y_pred_lof == -1, 1],
                    c=COLORS["danger"], s=40, marker="x", label="이상치")

    # LOF 점수로 원 크기
    lof_scores = -lof.negative_outlier_factor_
    sizes = (lof_scores - lof_scores.min()) / (lof_scores.max() - lof_scores.min()) * 200 + 10
    axes[1].scatter(X[:, 0], X[:, 1], s=sizes, facecolors="none",
                    edgecolors=COLORS["warning"], alpha=0.3)

    axes[1].set_title("Local Outlier Factor (LOF)", fontsize=14,
                      fontweight="bold")
    axes[1].legend(fontsize=10)

    fig.suptitle("이상 탐지 알고리즘 비교", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "anomaly_detection_comparison.png")

    # Figure 2: 이상 점수 분포
    fig, ax = make_fig(10, 6)
    scores_iso = iso.decision_function(X)

    ax.hist(scores_iso[y_pred_iso == 1], bins=30, color=COLORS["primary"],
            alpha=0.7, label="정상", density=True, edgecolor="white")
    ax.hist(scores_iso[y_pred_iso == -1], bins=15, color=COLORS["danger"],
            alpha=0.7, label="이상치", density=True, edgecolor="white")
    ax.axvline(0, ls="--", color=COLORS["dark"], lw=2, label="임계값")

    ax.set_xlabel("이상 점수 (Anomaly Score)", fontsize=13)
    ax.set_ylabel("밀도", fontsize=13)
    ax.set_title("Isolation Forest 이상 점수 분포", fontsize=15, fontweight="bold")
    ax.legend(fontsize=11)
    save_fig(fig, slug, "anomaly_score_distribution.png")


def gen_45_rl_basics():
    slug = "45_reinforcement-learning-basics"

    # Figure 1: Q-value 히트맵 (Gridworld)
    fig, ax = make_fig(8, 8)
    np.random.seed(42)
    grid_size = 5

    # Q-값 시뮬레이션
    q_values = np.random.rand(grid_size, grid_size) * 10
    # 골 근처 높은 값
    goal = (4, 4)
    for i in range(grid_size):
        for j in range(grid_size):
            dist = abs(i - goal[0]) + abs(j - goal[1])
            q_values[i, j] = max(0, 10 - dist * 2) + np.random.rand() * 0.5

    im = ax.imshow(q_values, cmap="YlOrRd", interpolation="nearest")

    for i in range(grid_size):
        for j in range(grid_size):
            ax.text(j, i, f"{q_values[i, j]:.1f}", ha="center", va="center",
                    fontsize=12, fontweight="bold",
                    color="white" if q_values[i, j] > 5 else COLORS["dark"])

    # 시작점과 골
    ax.text(0, 0, "\nS", ha="center", va="center", fontsize=14,
            color=COLORS["primary"], fontweight="bold")
    ax.text(4, 4, "\nG", ha="center", va="center", fontsize=14,
            color=COLORS["success"], fontweight="bold")

    # 장애물
    ax.add_patch(plt.Rectangle((0.5, 1.5), 1, 1, fill=True,
                                color=COLORS["dark"], alpha=0.8))
    ax.text(1, 2, "벽", ha="center", va="center", fontsize=10,
            color="white", fontweight="bold")
    ax.add_patch(plt.Rectangle((2.5, 2.5), 1, 1, fill=True,
                                color=COLORS["dark"], alpha=0.8))
    ax.text(3, 3, "벽", ha="center", va="center", fontsize=10,
            color="white", fontweight="bold")

    ax.set_xticks(range(grid_size))
    ax.set_yticks(range(grid_size))
    ax.set_title("Gridworld Q-값 히트맵", fontsize=16, fontweight="bold")
    plt.colorbar(im, ax=ax, label="Q-value", shrink=0.8)
    save_fig(fig, slug, "q_value_gridworld.png")

    # Figure 2: 에이전트-환경 상호작용 다이어그램
    fig, ax = make_fig(10, 6)
    ax.set_xlim(-1, 11)
    ax.set_ylim(-1, 7)
    ax.axis("off")
    ax.set_title("강화학습: 에이전트-환경 상호작용",
                 fontsize=16, fontweight="bold", pad=20)

    # 에이전트
    agent_box = FancyBboxPatch((0.5, 2.5), 3, 2,
                                boxstyle="round,pad=0.3",
                                facecolor=COLORS["primary"],
                                alpha=0.8, edgecolor="white", linewidth=2)
    ax.add_patch(agent_box)
    ax.text(2, 3.5, "에이전트\n(Agent)", ha="center", va="center",
            fontsize=14, color="white", fontweight="bold")

    # 환경
    env_box = FancyBboxPatch((6.5, 2.5), 3, 2,
                              boxstyle="round,pad=0.3",
                              facecolor=COLORS["success"],
                              alpha=0.8, edgecolor="white", linewidth=2)
    ax.add_patch(env_box)
    ax.text(8, 3.5, "환경\n(Environment)", ha="center", va="center",
            fontsize=14, color="white", fontweight="bold")

    # 화살표들
    # 행동
    ax.annotate("행동 (Action, aₜ)", xy=(6.5, 4.0), xytext=(3.5, 4.0),
                fontsize=12, fontweight="bold", color=COLORS["secondary"],
                ha="center",
                arrowprops=dict(arrowstyle="-|>", color=COLORS["secondary"],
                                lw=2.5))

    # 상태
    ax.annotate("상태 (State, sₜ₊₁)", xy=(3.5, 3.0), xytext=(6.5, 3.0),
                fontsize=12, fontweight="bold", color=COLORS["purple"],
                ha="center",
                arrowprops=dict(arrowstyle="-|>", color=COLORS["purple"],
                                lw=2.5))

    # 보상
    ax.annotate("보상 (Reward, rₜ₊₁)", xy=(3.5, 1.5), xytext=(6.5, 1.5),
                fontsize=12, fontweight="bold", color=COLORS["danger"],
                ha="center",
                arrowprops=dict(arrowstyle="-|>", color=COLORS["danger"],
                                lw=2.5, connectionstyle="arc3,rad=-0.3"))

    # 목표
    ax.text(5, 6, "목표: 누적 보상 최대화  Σ γᵗrₜ", ha="center",
            fontsize=14, fontweight="bold", color=COLORS["dark"],
            bbox=dict(boxstyle="round,pad=0.4", fc="#FEF9E7",
                      ec=COLORS["warning"]))

    save_fig(fig, slug, "agent_environment_interaction.png")


def gen_46_sklearn_pipeline():
    slug = "46_sklearn-pipeline"

    # Figure 1: 파이프라인 다이어그램
    fig, ax = make_fig(12, 6)
    ax.set_xlim(-0.5, 12)
    ax.set_ylim(-1, 4)
    ax.axis("off")
    ax.set_title("sklearn Pipeline: 전처리 → 학습 자동화",
                 fontsize=16, fontweight="bold", pad=20)

    steps = [
        ("결측값\n처리", COLORS["primary"], "SimpleImputer"),
        ("스케일링", COLORS["blue_light"], "StandardScaler"),
        ("특성 선택", COLORS["teal"], "SelectKBest"),
        ("차원 축소", COLORS["success"], "PCA"),
        ("모델 학습", COLORS["secondary"], "RandomForest"),
    ]

    for i, (label, color, sklearn_name) in enumerate(steps):
        x = i * 2.4 + 0.5
        box = FancyBboxPatch((x - 0.9, 1.0), 1.8, 1.5,
                              boxstyle="round,pad=0.15",
                              facecolor=color, alpha=0.85,
                              edgecolor="white", linewidth=2)
        ax.add_patch(box)
        ax.text(x, 2.0, label, ha="center", va="center",
                fontsize=11, fontweight="bold", color="white")
        ax.text(x, 1.3, sklearn_name, ha="center", va="center",
                fontsize=8, color="white", alpha=0.9)

        if i < len(steps) - 1:
            ax.annotate("", xy=(x + 1.1, 1.75), xytext=(x + 0.9, 1.75),
                        arrowprops=dict(arrowstyle="-|>", color="#666", lw=2))

    # fit/predict 흐름
    ax.text(0.5, 0.3, "X_train, y_train", fontsize=10, color=COLORS["dark"],
            fontweight="bold",
            bbox=dict(boxstyle="round", fc=COLORS["light"], alpha=0.8))
    ax.annotate("pipeline.fit()", xy=(5, 1.0), xytext=(2, 0.3),
                fontsize=10, color=COLORS["dark"],
                arrowprops=dict(arrowstyle="->", color="#aaa", lw=1.5))

    ax.text(8.5, 0.3, "X_test → ŷ", fontsize=10, color=COLORS["dark"],
            fontweight="bold",
            bbox=dict(boxstyle="round", fc=COLORS["light"], alpha=0.8))
    ax.annotate("pipeline.predict()", xy=(9.5, 1.0), xytext=(9, 0.3),
                fontsize=10, color=COLORS["dark"],
                arrowprops=dict(arrowstyle="->", color="#aaa", lw=1.5))

    save_fig(fig, slug, "sklearn_pipeline_diagram.png")

    # Figure 2: Pipeline 성능 비교 (with/without)
    fig, ax = make_fig(10, 6)
    scenarios = ["수동 전처리\n+ 모델", "Pipeline\n(동일 구성)", "Pipeline\n+ GridSearchCV"]
    accuracies = [0.82, 0.82, 0.89]
    times = ["5분", "1분", "3분"]
    bar_colors = [COLORS["warning"], COLORS["primary"], COLORS["success"]]

    bars = ax.bar(scenarios, accuracies, color=bar_colors, alpha=0.85,
                  edgecolor="white", width=0.5)
    for bar, acc, t in zip(bars, accuracies, times):
        ax.text(bar.get_x() + bar.get_width() / 2, acc + 0.01,
                f"{acc:.0%}\n({t})", ha="center", fontsize=12, fontweight="bold")

    ax.set_ylabel("정확도", fontsize=13)
    ax.set_title("Pipeline 활용의 이점", fontsize=15, fontweight="bold")
    ax.set_ylim(0, 1.0)
    save_fig(fig, slug, "pipeline_benefit.png")


def gen_47_ab_testing():
    slug = "47_ab-testing"

    # Figure 1: 분포 비교 + p-value
    fig, axes = make_fig_axes(1, 2, 13, 6)

    x = np.linspace(-4, 8, 300)
    null_dist = stats.norm.pdf(x, 0, 1)
    alt_dist = stats.norm.pdf(x, 2, 1)

    axes[0].plot(x, null_dist, color=COLORS["primary"], lw=2.5,
                 label="H₀: 차이 없음")
    axes[0].plot(x, alt_dist, color=COLORS["danger"], lw=2.5,
                 label="H₁: 차이 있음")
    axes[0].fill_between(x, null_dist, where=x >= 1.96, alpha=0.4,
                         color=COLORS["warning"], label="기각역 (α=0.05)")
    axes[0].axvline(1.96, ls="--", color=COLORS["danger"], lw=1.5)
    axes[0].set_title("가설 검정 분포", fontsize=13, fontweight="bold")
    axes[0].legend(fontsize=9)
    axes[0].set_xlabel("검정 통계량", fontsize=11)

    # p-value 시각화
    np.random.seed(42)
    n_sims = 1000
    a_conv = 0.10  # 10% 전환율
    b_conv = 0.12  # 12% 전환율

    p_values = []
    for _ in range(n_sims):
        a_samples = np.random.binomial(1, a_conv, 500)
        b_samples = np.random.binomial(1, b_conv, 500)
        _, p = stats.ttest_ind(a_samples, b_samples)
        p_values.append(p)

    axes[1].hist(p_values, bins=40, color=COLORS["primary"], alpha=0.7,
                 edgecolor="white", density=True)
    axes[1].axvline(0.05, ls="--", color=COLORS["danger"], lw=2,
                    label="α = 0.05")
    significant = sum(1 for p in p_values if p < 0.05) / len(p_values)
    axes[1].text(0.5, 0.95, f"통계적 검정력 = {significant:.1%}",
                 transform=axes[1].transAxes, fontsize=12, fontweight="bold",
                 va="top", ha="center",
                 bbox=dict(boxstyle="round", fc=COLORS["light"]))
    axes[1].set_xlabel("p-value", fontsize=11)
    axes[1].set_ylabel("밀도", fontsize=11)
    axes[1].set_title("시뮬레이션 p-value 분포", fontsize=13, fontweight="bold")
    axes[1].legend(fontsize=10)

    fig.suptitle("A/B 테스트: 통계적 가설 검정", fontsize=16,
                 fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "ab_test_hypothesis.png")

    # Figure 2: A/B 테스트 결과 시각화
    fig, ax = make_fig(10, 6)

    groups = ["대조군 (A)", "실험군 (B)"]
    conversions = [10.0, 12.0]
    ci_low = [9.0, 10.8]
    ci_high = [11.0, 13.2]
    errors = [[c - l for c, l in zip(conversions, ci_low)],
              [h - c for c, h in zip(conversions, ci_high)]]

    bars = ax.bar(groups, conversions, yerr=errors, capsize=10,
                  color=[COLORS["primary"], COLORS["success"]], alpha=0.85,
                  edgecolor="white", width=0.4, error_kw=dict(lw=2))

    for bar, conv, lo, hi in zip(bars, conversions, ci_low, ci_high):
        ax.text(bar.get_x() + bar.get_width() / 2, conv + 1.5,
                f"{conv:.1f}%\n({lo:.1f}~{hi:.1f}%)",
                ha="center", fontsize=12, fontweight="bold")

    # 향상률
    lift = (conversions[1] - conversions[0]) / conversions[0] * 100
    ax.annotate(f"향상률: +{lift:.1f}%", xy=(1, conversions[1]),
                xytext=(1.3, conversions[1] + 1),
                fontsize=13, fontweight="bold", color=COLORS["danger"],
                arrowprops=dict(arrowstyle="->", color=COLORS["danger"]))

    ax.set_ylabel("전환율 (%)", fontsize=13)
    ax.set_title("A/B 테스트 결과", fontsize=16, fontweight="bold")
    ax.set_ylim(0, 16)
    save_fig(fig, slug, "ab_test_results.png")


def gen_48_ml_system_design():
    slug = "48_ml-system-design"

    # Figure 1: ML 시스템 아키텍처
    fig, ax = make_fig(14, 8)
    ax.set_xlim(-0.5, 14)
    ax.set_ylim(-0.5, 8)
    ax.axis("off")
    ax.set_title("ML 시스템 설계 아키텍처", fontsize=18, fontweight="bold", pad=20)

    layers = [
        # (y, label, components, color)
        (6.5, "데이터 레이어", ["데이터\n수집", "데이터\n저장", "데이터\n검증", "특성\n저장소"], COLORS["primary"]),
        (4.5, "모델 레이어", ["특성\n공학", "모델\n학습", "하이퍼파라미터\n튜닝", "모델\n레지스트리"], COLORS["success"]),
        (2.5, "서빙 레이어", ["모델\n서빙", "A/B\n테스트", "모니터링", "피드백\n루프"], COLORS["secondary"]),
        (0.5, "인프라 레이어", ["컨테이너\n오케스트레이션", "CI/CD", "로깅", "알림"], COLORS["purple"]),
    ]

    for y, layer_name, components, color in layers:
        # 레이어 배경
        bg = FancyBboxPatch((-0.3, y - 0.7), 13.6, 1.6,
                             boxstyle="round,pad=0.1",
                             facecolor=color, alpha=0.08,
                             edgecolor=color, linewidth=1)
        ax.add_patch(bg)
        ax.text(-0.1, y + 0.5, layer_name, fontsize=10, fontweight="bold",
                color=color, rotation=0, va="center")

        for i, comp in enumerate(components):
            x = i * 3.2 + 2
            box = FancyBboxPatch((x - 1.0, y - 0.5), 2.0, 1.0,
                                  boxstyle="round,pad=0.1",
                                  facecolor=color, alpha=0.7,
                                  edgecolor="white", linewidth=1.5)
            ax.add_patch(box)
            ax.text(x, y, comp, ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")

    # 레이어 간 연결
    for i in range(3):
        y_top = layers[i][0] - 0.7
        y_bottom = layers[i + 1][0] + 0.9
        ax.annotate("", xy=(7, y_bottom), xytext=(7, y_top),
                    arrowprops=dict(arrowstyle="-|>", color="#aaa", lw=2))

    save_fig(fig, slug, "ml_system_architecture.png")

    # Figure 2: 시스템 지표 대시보드
    fig, axes = make_fig_axes(2, 2, 12, 8)
    np.random.seed(42)
    hours = np.arange(24)

    # 지연 시간
    latency = 50 + 20 * np.sin(hours * np.pi / 12) + np.random.randn(24) * 5
    axes[0, 0].plot(hours, latency, "o-", color=COLORS["primary"], lw=2)
    axes[0, 0].axhline(100, ls="--", color=COLORS["danger"], alpha=0.5)
    axes[0, 0].set_title("추론 지연 시간 (ms)", fontsize=12, fontweight="bold")
    axes[0, 0].set_xlabel("시간", fontsize=10)

    # 처리량
    throughput = 1000 + 500 * np.sin(hours * np.pi / 12) + np.random.randn(24) * 50
    axes[0, 1].fill_between(hours, throughput, alpha=0.3, color=COLORS["success"])
    axes[0, 1].plot(hours, throughput, color=COLORS["success"], lw=2)
    axes[0, 1].set_title("초당 요청 수 (QPS)", fontsize=12, fontweight="bold")
    axes[0, 1].set_xlabel("시간", fontsize=10)

    # 모델 정확도 드리프트
    days = np.arange(30)
    accuracy = 0.95 - 0.002 * days + np.random.randn(30) * 0.005
    axes[1, 0].plot(days, accuracy, "o-", color=COLORS["warning"], lw=2)
    axes[1, 0].axhline(0.90, ls="--", color=COLORS["danger"], alpha=0.5,
                       label="임계값")
    axes[1, 0].set_title("모델 정확도 (일별)", fontsize=12, fontweight="bold")
    axes[1, 0].set_xlabel("일", fontsize=10)
    axes[1, 0].legend(fontsize=9)

    # 데이터 드리프트
    drift_score = 0.01 + 0.003 * days + np.random.randn(30) * 0.005
    drift_score = np.abs(drift_score)
    axes[1, 1].bar(days, drift_score, color=COLORS["purple"], alpha=0.7)
    axes[1, 1].axhline(0.1, ls="--", color=COLORS["danger"], alpha=0.5,
                       label="경고 수준")
    axes[1, 1].set_title("데이터 드리프트 점수", fontsize=12, fontweight="bold")
    axes[1, 1].set_xlabel("일", fontsize=10)
    axes[1, 1].legend(fontsize=9)

    fig.suptitle("ML 시스템 모니터링 대시보드", fontsize=16,
                 fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "system_monitoring_dashboard.png")


def gen_49_mlops():
    slug = "49_mlops-fundamentals"

    # Figure 1: MLOps 라이프사이클
    fig, ax = make_fig(10, 10)
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("MLOps 라이프사이클", fontsize=18, fontweight="bold", pad=20)

    stages = [
        ("데이터\n수집/검증", 0),
        ("특성\n공학", 1),
        ("모델\n학습", 2),
        ("모델\n검증", 3),
        ("모델\n배포", 4),
        ("모니터링\n/피드백", 5),
    ]
    stage_colors = [COLORS["primary"], COLORS["blue_light"], COLORS["teal"],
                    COLORS["success"], COLORS["secondary"], COLORS["purple"]]

    n = len(stages)
    radius = 3.0
    for i, ((label, _), c) in enumerate(zip(stages, stage_colors)):
        angle = 2 * np.pi * i / n - np.pi / 2
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)

        circle = plt.Circle((x, y), 0.8, fc=c, ec="white", lw=2.5, alpha=0.85)
        ax.add_patch(circle)
        ax.text(x, y, label, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")

        # 화살표
        next_angle = 2 * np.pi * ((i + 1) % n) / n - np.pi / 2
        x_next = radius * np.cos(next_angle)
        y_next = radius * np.sin(next_angle)

        dx = x_next - x
        dy = y_next - y
        dist = np.sqrt(dx ** 2 + dy ** 2)
        ax.annotate("", xy=(x + dx * 0.7, y + dy * 0.7),
                    xytext=(x + dx * 0.3, y + dy * 0.3),
                    arrowprops=dict(arrowstyle="-|>", color="#666", lw=2))

    # 중앙 텍스트
    ax.text(0, 0, "MLOps\n지속적\n개선", ha="center", va="center",
            fontsize=14, fontweight="bold", color=COLORS["dark"],
            bbox=dict(boxstyle="round,pad=0.5", fc=COLORS["light"], alpha=0.8))

    save_fig(fig, slug, "mlops_lifecycle.png")

    # Figure 2: MLOps 성숙도 레벨
    fig, ax = make_fig(12, 6)

    levels = ["Level 0\n수동 프로세스", "Level 1\nML 파이프라인\n자동화",
              "Level 2\nCI/CD\n파이프라인"]
    capabilities = [
        ["수동 데이터 처리", "수동 모델 학습", "수동 배포"],
        ["자동 파이프라인", "CT (지속적 학습)", "특성 저장소"],
        ["CI/CD 자동화", "모니터링/알림", "A/B 테스트/롤백"],
    ]
    level_colors = [COLORS["warning"], COLORS["primary"], COLORS["success"]]

    for i, (level, caps, c) in enumerate(zip(levels, capabilities, level_colors)):
        x_base = i * 4 + 1
        box = FancyBboxPatch((x_base - 1.5, 2.5), 3, 3,
                              boxstyle="round,pad=0.2",
                              facecolor=c, alpha=0.15,
                              edgecolor=c, linewidth=2)
        ax.add_patch(box)
        ax.text(x_base, 5.2, level, ha="center", va="center",
                fontsize=11, fontweight="bold", color=c)

        for j, cap in enumerate(caps):
            y_pos = 4.0 - j * 0.7
            ax.text(x_base, y_pos, f"• {cap}", ha="center", va="center",
                    fontsize=9, color=COLORS["dark"])

        if i < 2:
            ax.annotate("", xy=(x_base + 2, 4), xytext=(x_base + 1.5, 4),
                        arrowprops=dict(arrowstyle="-|>", color="#666", lw=2))

    ax.set_xlim(-1, 13)
    ax.set_ylim(1.5, 6)
    ax.axis("off")
    ax.set_title("MLOps 성숙도 레벨", fontsize=16, fontweight="bold", pad=10)
    save_fig(fig, slug, "mlops_maturity_levels.png")


def gen_50_automl():
    slug = "50_automl"

    # Figure 1: 하이퍼파라미터 탐색 공간
    fig, axes = make_fig_axes(1, 2, 12, 5)

    # Grid Search
    np.random.seed(42)
    grid_x = np.repeat(np.linspace(0, 1, 8), 8)
    grid_y = np.tile(np.linspace(0, 1, 8), 8)

    axes[0].scatter(grid_x, grid_y, c=COLORS["primary"], s=30, alpha=0.7)
    axes[0].set_title("그리드 탐색 (Grid Search)\n균등 분포, O(n^d)", fontsize=12,
                      fontweight="bold", color=COLORS["primary"])
    axes[0].set_xlabel("하이퍼파라미터 1", fontsize=10)
    axes[0].set_ylabel("하이퍼파라미터 2", fontsize=10)

    # Random Search
    rand_x = np.random.rand(64)
    rand_y = np.random.rand(64)
    axes[1].scatter(rand_x, rand_y, c=COLORS["secondary"], s=30, alpha=0.7)
    axes[1].set_title("랜덤 탐색 (Random Search)\n랜덤 분포, 효율적", fontsize=12,
                      fontweight="bold", color=COLORS["secondary"])
    axes[1].set_xlabel("하이퍼파라미터 1", fontsize=10)
    axes[1].set_ylabel("하이퍼파라미터 2", fontsize=10)

    fig.suptitle("하이퍼파라미터 탐색 전략", fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, slug, "search_space.png")

    # Figure 2: 베이지안 최적화 과정
    fig, ax = make_fig(10, 6)
    np.random.seed(42)

    x = np.linspace(0, 10, 200)
    true_func = -(np.sin(x) * x / 3 + np.cos(3 * x))

    # 관측된 점
    x_observed = np.array([1, 3, 5, 7, 9])
    y_observed = -(np.sin(x_observed) * x_observed / 3 + np.cos(3 * x_observed))
    y_observed += np.random.randn(len(x_observed)) * 0.1

    # 간단한 GP 근사 (RBF 보간)
    from scipy.interpolate import Rbf
    rbf = Rbf(x_observed, y_observed, function="gaussian", epsilon=1)
    y_pred = rbf(x)
    y_std = 0.5 * np.exp(-np.min(np.abs(x[:, None] - x_observed[None, :]),
                                   axis=1) / 2)

    ax.plot(x, true_func, "--", color="#aaa", lw=1, label="실제 함수 (미지)")
    ax.plot(x, y_pred, color=COLORS["primary"], lw=2, label="대리 모델 (예측)")
    ax.fill_between(x, y_pred - 2 * y_std, y_pred + 2 * y_std,
                    alpha=0.15, color=COLORS["primary"], label="불확실성 (2σ)")
    ax.scatter(x_observed, y_observed, c=COLORS["danger"], s=80, zorder=5,
               edgecolors="white", linewidth=1.5, label="관측 포인트")

    # 다음 탐색 포인트 (EI 최대)
    ei = y_std * np.where(y_pred < min(y_observed), 1, 0.5)
    next_idx = np.argmax(ei)
    ax.axvline(x[next_idx], ls=":", color=COLORS["success"], lw=2, alpha=0.7)
    ax.scatter([x[next_idx]], [y_pred[next_idx]], s=200, marker="*",
               c=COLORS["success"], zorder=6, label="다음 탐색 후보")

    ax.set_xlabel("하이퍼파라미터", fontsize=13)
    ax.set_ylabel("목적 함수", fontsize=13)
    ax.set_title("베이지안 최적화: 대리 모델 + 획득 함수",
                 fontsize=15, fontweight="bold")
    ax.legend(fontsize=9, loc="upper right")
    save_fig(fig, slug, "bayesian_optimization.png")


def gen_51_ml_interview():
    slug = "51_ml-interview-guide"

    # Figure 1: ML 개념 마인드맵
    fig, ax = make_fig(14, 10)
    ax.set_xlim(-7, 7)
    ax.set_ylim(-5, 5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("머신러닝 핵심 개념 맵", fontsize=18, fontweight="bold", pad=20)

    # 중심
    center = plt.Circle((0, 0), 0.8, fc=COLORS["dark"], ec="white", lw=3)
    ax.add_patch(center)
    ax.text(0, 0, "ML\n핵심", ha="center", va="center",
            fontsize=14, fontweight="bold", color="white")

    categories = [
        ("수학 기초", COLORS["primary"],
         ["선형대수", "확률/통계", "최적화", "정보 이론"]),
        ("지도 학습", COLORS["success"],
         ["회귀", "분류", "앙상블", "SVM"]),
        ("비지도 학습", COLORS["secondary"],
         ["클러스터링", "차원 축소", "GMM"]),
        ("평가/검증", COLORS["purple"],
         ["교차검증", "ROC/AUC", "편향-분산"]),
        ("응용", COLORS["danger"],
         ["NLP", "추천", "이상탐지", "시계열"]),
        ("시스템", COLORS["teal"],
         ["MLOps", "파이프라인", "모니터링"]),
    ]

    for i, (cat_name, color, subtopics) in enumerate(categories):
        angle = 2 * np.pi * i / len(categories) - np.pi / 2
        cx = 3.0 * np.cos(angle)
        cy = 3.0 * np.sin(angle)

        cat_circle = plt.Circle((cx, cy), 0.65, fc=color, ec="white",
                                lw=2, alpha=0.85)
        ax.add_patch(cat_circle)
        ax.text(cx, cy, cat_name, ha="center", va="center",
                fontsize=9, fontweight="bold", color="white")

        ax.plot([0, cx * 0.7], [0, cy * 0.7], color="#aaa", lw=1.5)

        for j, topic in enumerate(subtopics):
            sub_angle = angle + (j - len(subtopics) / 2 + 0.5) * 0.25
            sx = cx + 1.8 * np.cos(sub_angle)
            sy = cy + 1.8 * np.sin(sub_angle)

            sub_circle = plt.Circle((sx, sy), 0.45, fc=color, ec="white",
                                    lw=1, alpha=0.5)
            ax.add_patch(sub_circle)
            ax.text(sx, sy, topic, ha="center", va="center",
                    fontsize=7, color="white", fontweight="bold")
            ax.plot([cx, sx * 0.95 + cx * 0.05], [cy, sy * 0.95 + cy * 0.05],
                    color=color, lw=0.8, alpha=0.5)

    save_fig(fig, slug, "ml_concept_map.png")

    # Figure 2: 알고리즘 치트시트
    fig, ax = make_fig(14, 8)
    ax.axis("off")
    ax.set_title("ML 알고리즘 선택 가이드", fontsize=18, fontweight="bold", pad=20)

    # 결정 플로우
    decisions = [
        (7, 7, "데이터에 라벨이\n있는가?", COLORS["dark"]),
        (3.5, 5, "연속값\n예측?", COLORS["primary"]),
        (10.5, 5, "클러스터링\n필요?", COLORS["secondary"]),
        (2, 3, "선형 관계?", COLORS["teal"]),
        (5, 3, "분류\n문제", COLORS["success"]),
        (9, 3, "K-Means\nDBSCAN", COLORS["secondary"]),
        (12, 3, "PCA\nt-SNE", COLORS["purple"]),
        (1, 1, "Linear\nRegression", COLORS["primary"]),
        (3, 1, "Random Forest\nXGBoost", COLORS["success"]),
        (4.5, 1, "Logistic\nSVM", COLORS["primary"]),
        (6, 1, "Random Forest\nXGBoost", COLORS["success"]),
    ]

    for x, y, text, color in decisions:
        box = FancyBboxPatch((x - 0.9, y - 0.4), 1.8, 0.8,
                              boxstyle="round,pad=0.1",
                              facecolor=color, alpha=0.8,
                              edgecolor="white", linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center",
                fontsize=8, color="white", fontweight="bold")

    # 연결선
    connections = [
        ((7, 6.6), (3.5, 5.4), "예"),
        ((7, 6.6), (10.5, 5.4), "아니오"),
        ((3.5, 4.6), (2, 3.4), "예"),
        ((3.5, 4.6), (5, 3.4), "아니오"),
        ((10.5, 4.6), (9, 3.4), "예"),
        ((10.5, 4.6), (12, 3.4), "아니오"),
        ((2, 2.6), (1, 1.4), "예"),
        ((2, 2.6), (3, 1.4), "아니오"),
        ((5, 2.6), (4.5, 1.4), "선형"),
        ((5, 2.6), (6, 1.4), "비선형"),
    ]

    for start, end, label in connections:
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="->", color="#666", lw=1.5))
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        ax.text(mid_x + 0.2, mid_y, label, fontsize=7, color="#888")

    ax.set_xlim(-0.5, 14)
    ax.set_ylim(0, 8)
    save_fig(fig, slug, "algorithm_selection_guide.png")


# ═══════════════════════════════════════════════════════════════════════════
# 포스트-함수 매핑 & 그룹 정의
# ═══════════════════════════════════════════════════════════════════════════

POST_GENERATORS = {
    # Group 1: Fundamentals
    "01_ml-overview": gen_01_ml_overview,
    "02_ml-workflow": gen_02_ml_workflow,
    "03_bias-variance-tradeoff": gen_03_bias_variance,
    "04_linear-algebra-for-ml": gen_04_linear_algebra,
    "05_probability-bayes": gen_05_probability_bayes,
    "06_information-theory": gen_06_information_theory,
    "07_optimization-theory": gen_07_optimization_theory,
    # Group 2: Preprocessing
    "08_data-preprocessing": gen_08_data_preprocessing,
    "09_feature-engineering": gen_09_feature_engineering,
    "10_imbalanced-data": gen_10_imbalanced_data,
    # Group 3: Regression
    "11_linear-regression": gen_11_linear_regression,
    "12_regularized-regression": gen_12_regularized_regression,
    "13_polynomial-regression": gen_13_polynomial_regression,
    # Group 4: Classification
    "14_logistic-regression": gen_14_logistic_regression,
    "15_naive-bayes": gen_15_naive_bayes,
    "16_knn": gen_16_knn,
    "17_svm": gen_17_svm,
    "18_decision-tree": gen_18_decision_tree,
    # Group 5: Ensemble
    "19_ensemble-overview": gen_19_ensemble_overview,
    "20_random-forest": gen_20_random_forest,
    "21_gradient-boosting": gen_21_gradient_boosting,
    "22_xgboost-lightgbm": gen_22_xgboost_lightgbm,
    # Group 6: Unsupervised
    "23_kmeans-clustering": gen_23_kmeans,
    "24_advanced-clustering": gen_24_advanced_clustering,
    "25_gmm": gen_25_gmm,
    "26_pca": gen_26_pca,
    "27_tsne-umap": gen_27_tsne_umap,
    # Group 7: Evaluation
    "28_classification-metrics": gen_28_classification_metrics,
    "29_regression-metrics": gen_29_regression_metrics,
    "30_cross-validation": gen_30_cross_validation,
    "31_model-interpretability": gen_31_model_interpretability,
    # Group 8: Advanced
    "37_bayesian-ml": gen_37_bayesian_ml,
    "38_semi-supervised-learning": gen_38_semi_supervised,
    "39_topic-modeling": gen_39_topic_modeling,
    "40_kernel-methods": gen_40_kernel_methods,
    "41_time-series-ml": gen_41_time_series,
    "42_recommendation-systems": gen_42_recommendation,
    "43_nlp-traditional-ml": gen_43_nlp_traditional,
    "44_anomaly-detection": gen_44_anomaly_detection,
    "45_reinforcement-learning-basics": gen_45_rl_basics,
    "46_sklearn-pipeline": gen_46_sklearn_pipeline,
    "47_ab-testing": gen_47_ab_testing,
    "48_ml-system-design": gen_48_ml_system_design,
    "49_mlops-fundamentals": gen_49_mlops,
    "50_automl": gen_50_automl,
    "51_ml-interview-guide": gen_51_ml_interview,
}

GROUPS = {
    1: [f for f in POST_GENERATORS if f.startswith(("01_", "02_", "03_", "04_",
                                                     "05_", "06_", "07_"))],
    2: [f for f in POST_GENERATORS if f.startswith(("08_", "09_", "10_"))],
    3: [f for f in POST_GENERATORS if f.startswith(("11_", "12_", "13_"))],
    4: [f for f in POST_GENERATORS if f.startswith(("14_", "15_", "16_",
                                                     "17_", "18_"))],
    5: [f for f in POST_GENERATORS if f.startswith(("19_", "20_", "21_", "22_"))],
    6: [f for f in POST_GENERATORS if f.startswith(("23_", "24_", "25_",
                                                     "26_", "27_"))],
    7: [f for f in POST_GENERATORS if f.startswith(("28_", "29_", "30_", "31_"))],
    8: [f for f in POST_GENERATORS if f.startswith(("37_", "38_", "39_", "40_",
                                                     "41_", "42_", "43_", "44_",
                                                     "45_", "46_", "47_", "48_",
                                                     "49_", "50_", "51_"))],
}


# ═══════════════════════════════════════════════════════════════════════════
# 메인 실행
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ML 교육용 포스트 Figure 자동 생성")
    parser.add_argument("--slug", type=str, default=None,
                        help="특정 포스트만 생성 (e.g. 01_ml-overview)")
    parser.add_argument("--group", type=int, default=None, choices=range(1, 9),
                        help="특정 그룹만 생성 (1~8)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="이미 figures/ 디렉토리에 파일이 있으면 건너뜀")
    args = parser.parse_args()

    # 대상 포스트 결정
    if args.slug:
        if args.slug not in POST_GENERATORS:
            print(f"[오류] 알 수 없는 slug: {args.slug}")
            print(f"사용 가능: {', '.join(sorted(POST_GENERATORS.keys()))}")
            sys.exit(1)
        targets = [args.slug]
    elif args.group:
        targets = GROUPS.get(args.group, [])
        if not targets:
            print(f"[오류] 그룹 {args.group}에 포스트가 없습니다.")
            sys.exit(1)
    else:
        targets = list(POST_GENERATORS.keys())

    print(f"\n{'='*60}")
    print(f"  ML Figure 생성기 — 대상: {len(targets)}개 포스트")
    print(f"{'='*60}\n")

    success = 0
    failed = []

    for i, slug in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] {slug}")

        # skip-existing 체크
        if args.skip_existing:
            fig_dir = ML_DIR / slug / "figures"
            if fig_dir.exists() and any(fig_dir.glob("*.png")):
                print(f"    → 이미 존재, 건너뜀")
                success += 1
                continue

        try:
            POST_GENERATORS[slug]()
            success += 1
        except Exception as e:
            failed.append((slug, str(e)))
            print(f"    ✗ 오류: {e}")
            traceback.print_exc()
            print()

    print(f"\n{'='*60}")
    print(f"  완료: {success}/{len(targets)} 성공")
    if failed:
        print(f"  실패: {len(failed)}개")
        for slug, err in failed:
            print(f"    - {slug}: {err}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # scipy.stats 전역 import (여러 함수에서 사용)
    from scipy import stats
    main()
