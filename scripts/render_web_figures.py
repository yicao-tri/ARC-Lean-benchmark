#!/usr/bin/env python3
"""Render ARC-Lean web figures from frozen pilot artifacts.

The script reuses the user's Plot Atlas chart primitives.  It intentionally
shows descriptive pilot estimates without confidence intervals: the public
labels are system-audit labels, not independent expert gold.
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vendor.plot_atlas_minimal import apply_publication_style, grouped_bar, paired_dumbbell, save_figure


MORANDI = {
    "categorical": ["#7C8F8C", "#9C8DA5", "#B98F84", "#A6A07A", "#6E7D92", "#C2A6A1"],
    "start": "#7C8F8C",
    "end": "#B98F84",
    "start_band": "#DDE4E1",
    "end_band": "#EADDD9",
    "neutral": "#D8D3CB",
    "ink": "#394341",
}


def read_table() -> list[dict[str, str]]:
    with (ROOT / "data/frozen/icml_two_regime_pilot_v0.4.csv").open(newline="") as stream:
        return list(csv.DictReader(stream))


def render_public_map(out: Path) -> None:
    rows = read_table()
    names = [
        "Majority prior",
        "Qwen3.5-4B, structured context",
        "Qwen3-8B, sanitized artifacts",
        "Qwen3.5-4B, micro-RAG",
        "ARC w/o promotion ceiling",
        "ARC-Full reference",
    ]
    selected = []
    for name in names:
        row = next(item for item in rows if " ".join(item["method"].split()) == name)
        selected.append(row)
    metrics = [
        ("Overclaim ↓", "public_overclaim_rate"),
        ("Identifiability ↑", "public_identifiability_exact_match"),
        ("Decision ↑", "public_decision_exact_match"),
        ("Joint ↑", "public_joint_exact_match"),
    ]
    matrix = np.array([[100 * float(row[key]) for row in selected] for _, key in metrics])
    apply_publication_style(10.5)
    fig, ax = plt.subplots(figsize=(10.8, 5.2))
    grouped_bar(
        ax,
        [label for label, _ in metrics],
        matrix,
        ["Majority", "4B structured", "8B artifacts", "4B micro-RAG", "ARC no ceiling", "ARC-Full"],
        MORANDI["categorical"],
        ylabel="Pilot exact rate (%)",
    )
    ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.grid(False)
    ax.legend(ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.17), fontsize=8)
    fig.text(
        0.5,
        0.01,
        "Eight public scientific claims; system-audit labels, not independent expert gold.",
        ha="center",
        fontsize=8.5,
        color="#5D6865",
    )
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.18, top=0.78)
    save_figure(fig, out)
    plt.close(fig)


def render_ceiling_ablation(out: Path) -> None:
    seed = json.loads((ROOT / "data/frozen/seed_promotion_ceiling_ablation_v0.1.json").read_text())
    public = json.loads((ROOT / "data/frozen/public_promotion_ceiling_ablation_v0.1.json").read_text())
    categories = ["Engineering seed\nJoint", "Public cases\nJoint", "Engineering seed\nNo-overclaim", "Public cases\nNo-overclaim"]
    full = [100, 100, 100, 100]
    no_ceiling = [
        100 * seed["metrics"]["joint_exact_match"],
        100 * public["metrics"]["joint_exact_match"],
        100 * (1 - seed["metrics"]["overclaim_rate"]),
        100 * (1 - public["metrics"]["overclaim_rate"]),
    ]
    labels = [f"{value:.1f}%" for value in no_ceiling]
    apply_publication_style(10.5)
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    paired_dumbbell(
        ax,
        categories,
        full,
        no_ceiling,
        MORANDI,
        end_labels=labels,
        xlabel="Exact or safe rate (%)",
        xlim=(50, 104),
    )
    ax.grid(False)
    ax.text(100.4, 3.35, "ARC-Full", color=MORANDI["start"], fontsize=9, fontweight="bold")
    ax.text(55.5, 3.35, "without promotion ceiling", color=MORANDI["end"], fontsize=9, fontweight="bold")
    fig.text(
        0.5,
        0.01,
        "Identifiability and empirical decision remain 100%; only the promotion rule changes.",
        ha="center",
        fontsize=8.5,
        color="#5D6865",
    )
    fig.subplots_adjust(left=0.24, right=0.97, bottom=0.17, top=0.90)
    save_figure(fig, out)
    plt.close(fig)


def copy_variants(stem: str) -> None:
    source_png = ROOT / "web/assets" / f"{stem}.png"
    source_svg = ROOT / "web/assets" / f"{stem}.svg"
    for dest_dir in [ROOT / "site/assets", ROOT / "submission_folder/assets/img/submission"]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_png, dest_dir / source_png.name)
        shutil.copy2(source_svg, dest_dir / source_svg.name)


def main() -> None:
    out_dir = ROOT / "web/assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    render_public_map(out_dir / "public_pilot_map.png")
    render_ceiling_ablation(out_dir / "ceiling_ablation.png")
    for stem in ["public_pilot_map", "ceiling_ablation"]:
        copy_variants(stem)
    print("Rendered Morandi web figures from frozen pilot data.")


if __name__ == "__main__":
    main()
