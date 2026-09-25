"""论文级图表统一风格。所有探索与论文图一律 from style import apply_style 后调用。

原则：黑白可打印优先（灰度可区分）、无网格线 clutter、字号适配双栏版式。
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # 无显示环境，一律落盘
import matplotlib.pyplot as plt

PALETTE = {
    "ec": "#0072B2",        # 蓝：EC 论文
    "all": "#999999",       # 灰：全体论文
    "accent": "#D55E00",    # 朱红：强调/对照
    "green": "#009E73",
    "purple": "#CC79A7",
    "yellow": "#E69F00",
}


def apply_style() -> None:
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.size": 9,
        "axes.titlesize": 9,
        "axes.labelsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.5,
        "legend.frameon": False,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "lines.linewidth": 1.5,
    })


# NC 投稿版式（nature-figure 技能约定，2026-09-18 起）：
# 仅用于 ED 合并图（make_extended.ed_fig2_combined）与 SI 图（make_si_figures.py），
# 在 apply_style() 基础上叠加；冻结主图 fig1–4 与 ed_fig1 仍用上方基准风格。
# 要点：sans-serif（Arial 优先）、PDF 内嵌 TrueType（fonttype 42，文字可编辑）、
# 基准 7pt（渲染字形下限 5pt）、无网格。
NC_RC = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "font.size": 7,
    "axes.titlesize": 8,
    "axes.labelsize": 7,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5,
    "axes.grid": False,
}
