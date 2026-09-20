"""Minimal MIT-licensed snapshot of the Plot Atlas primitives used here.

Source family: the user's local Plot Atlas `grouped_bar`, `paired_dumbbell`,
publication-style, and export helpers. Kept locally so the submission package
can regenerate figures without depending on a private filesystem path.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patheffects
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize


def apply_publication_style(font_size: float = 10.5) -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": font_size,
        "axes.linewidth": 1.25,
        "xtick.major.width": 1.15,
        "ytick.major.width": 1.15,
        "xtick.major.size": 4.5,
        "ytick.major.size": 4.5,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    })


def _bold_ticks(ax) -> None:
    for tick in [*ax.get_xticklabels(), *ax.get_yticklabels()]:
        tick.set_fontweight("bold")


def _clean_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def grouped_bar(ax, xlabels, matrix, series_labels, colors, *, ylabel=None) -> None:
    matrix = np.asarray(matrix, float)
    n_groups, n_series = matrix.shape
    x = np.arange(n_groups)
    width = 0.78 / n_series
    for index in range(n_series):
        offset = (index - (n_series - 1) / 2) * width
        ax.bar(x + offset, matrix[:, index], width=width, color=colors[index % len(colors)],
               edgecolor="#555555", linewidth=0.45, label=series_labels[index])
    ax.set_xticks(x, xlabels)
    if ylabel:
        ax.set_ylabel(ylabel)
    _clean_axes(ax)
    _bold_ticks(ax)


def paired_dumbbell(ax, categories, start, end, palette, *, end_labels, xlabel, xlim) -> None:
    categories = list(categories)
    start = np.asarray(start, float)
    end = np.asarray(end, float)
    y = np.arange(len(categories))[::-1]
    c0, c1 = palette["start"], palette["end"]
    cmap = LinearSegmentedColormap.from_list("morandi_pair", [c0, c1])
    for yi, a, b in zip(y, start, end):
        xs = np.linspace(a, b, 90)
        points = np.column_stack([xs, np.full_like(xs, yi)])
        segments = np.stack([points[:-1], points[1:]], axis=1)
        ax.add_collection(LineCollection(segments, cmap=cmap, norm=Normalize(0, 1),
                                         array=np.linspace(0, 1, len(segments)), lw=1.5, zorder=2))
    ax.scatter(start, y, s=190, color=c0, alpha=0.76, edgecolor=c0, linewidth=1.2, zorder=3)
    ax.scatter(end, y, s=190, color=c1, alpha=0.68, edgecolor=c1, linewidth=1.2, zorder=3)
    for yi, a, b, label in zip(y, start, end, end_labels):
        text = ax.text(a + (b - a) * 0.52, yi + 0.30, label, ha="center", va="bottom",
                       fontsize=8, color=palette["ink"], zorder=5)
        text.set_path_effects([patheffects.withStroke(linewidth=2.5, foreground="white")])
    ax.set_yticks(y, categories)
    ax.set_xlabel(xlabel)
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.4, len(categories) - 0.6)
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    _bold_ticks(ax)


def save_figure(fig, output: Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220, facecolor="white")
    fig.savefig(output.with_suffix(".svg"), facecolor="white")

