# The figures of the paper (same numbering).
#   python scripts/make_figures.py

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
METRICS_DIR = os.path.join(ROOT, "results", "metrics")
OUT_DIR = os.path.join(ROOT, "results", "figures")

MODELS = ["qwen3.5-9b", "gemma-4-12b", "llama-3.1-8b", "domestic-yak-8b"]
MODEL_NAMES = {"qwen3.5-9b": "Qwen3.5 9B", "gemma-4-12b": "Gemma 4 12B",
               "llama-3.1-8b": "Llama 3.1 8B", "domestic-yak-8b": "Domestic-Yak 8B"}
LANG_NAMES = {"en": "English", "mk": "Macedonian"}
LANGS = ["en", "mk"]
CATEGORIES = ["content", "situation", "style", "format"]
LEVELS = [1, 2, 3, 4, 5]
EN_COLOR = "#4C72B0"
MK_COLOR = "#DD8452"


def read_csv(name):
    with open(os.path.join(METRICS_DIR, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))


def label_bars(ax, bars, fmt):
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, fmt % height,
                ha="center", va="bottom", fontsize=7)


def by_level_figure(levels, metric, ylabel, name):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, lang in zip(axes, LANGS):
        for model in MODELS:
            values = [float(levels[("A", model, lang, lv)][metric]) * 100 for lv in LEVELS]
            ax.plot(LEVELS, values, marker="o", label=MODEL_NAMES[model])
        ax.set_title(LANG_NAMES[lang] + ", Analysis A")
        ax.set_xlabel("Level (number of constraints)")
        ax.set_xticks(LEVELS)
        ax.set_ylim(0, 100)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel(ylabel)
    axes[1].legend(fontsize=8)
    save(fig, name)


def en_vs_mk_figure(summary):
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    x = list(range(len(MODELS)))
    width = 0.38
    panels = [
        ("hsr", "HSR (%)", 100, "%.1f"),
        ("ssr", "SSR (%)", 100, "%.1f"),
        ("csl", "CSL (levels)", 1, "%.2f"),
    ]
    for ax, (metric, ylabel, scale, fmt) in zip(axes, panels):
        ax.set_title(ylabel.split(" ")[0] + ", Analysis A")
        en = [float(summary[("A", m, "en")][metric]) * scale for m in MODELS]
        mk = [float(summary[("A", m, "mk")][metric]) * scale for m in MODELS]
        bars_en = ax.bar([i - width / 2 for i in x], en, width, label="English", color=EN_COLOR)
        bars_mk = ax.bar([i + width / 2 for i in x], mk, width, label="Macedonian", color=MK_COLOR)
        label_bars(ax, bars_en, fmt)
        label_bars(ax, bars_mk, fmt)
        ax.set_xticks(x)
        ax.set_xticklabels([MODEL_NAMES[m] for m in MODELS], rotation=20, fontsize=8)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 100 if scale == 100 else 5)
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend(fontsize=8)
    save(fig, "fig2_en_vs_mk.png")


def category_heatmap(cats):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for ax, lang in zip(axes, LANGS):
        grid = []
        for model in MODELS:
            grid.append([float(cats[("A", model, lang, c)]["hsr"]) * 100 for c in CATEGORIES])
        image = ax.imshow(grid, cmap="Blues", vmin=0, vmax=100)
        for i in range(len(MODELS)):
            for j in range(len(CATEGORIES)):
                color = "white" if grid[i][j] > 60 else "black"
                ax.text(j, i, "%.0f" % grid[i][j], ha="center", va="center", color=color, fontsize=9)
        ax.set_xticks(range(len(CATEGORIES)))
        ax.set_xticklabels([c.capitalize() for c in CATEGORIES])
        ax.set_yticks(range(len(MODELS)))
        ax.set_yticklabels([MODEL_NAMES[m] for m in MODELS])
        ax.set_title(LANG_NAMES[lang] + ", HSR (%), Analysis A")
    fig.colorbar(image, ax=axes, shrink=0.8)
    path = os.path.join(OUT_DIR, "fig4_category_heatmap.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))


def a_vs_b_figure(summary):
    fig, axes = plt.subplots(2, 1, figsize=(10, 7.5))
    labels = []
    for model in MODELS:
        for lang in LANGS:
            labels.append(MODEL_NAMES[model] + " " + lang.upper())
    x = list(range(len(labels)))
    width = 0.38
    for ax, metric, ylabel in zip(axes, ["hsr", "ssr"], ["HSR (%)", "SSR (%)"]):
        a = [float(summary[("A", m, l)][metric]) * 100 for m in MODELS for l in LANGS]
        b = [float(summary[("B", m, l)][metric]) * 100 for m in MODELS for l in LANGS]
        bars_a = ax.bar([i - width / 2 for i in x], a, width, label="A: truncated = fail", color="#55A868")
        bars_b = ax.bar([i + width / 2 for i in x], b, width, label="B: truncated left out", color="#8172B2")
        label_bars(ax, bars_a, "%.1f")
        label_bars(ax, bars_b, "%.1f")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=8, rotation=25, ha="right")
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 100)
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend(fontsize=8)
    save(fig, "fig6_analysis_a_vs_b.png")


def truncation_figure(trunc):
    fig, ax = plt.subplots(figsize=(7, 4))
    x = list(range(len(MODELS)))
    width = 0.38
    values = {}
    for lang in LANGS:
        values[lang] = []
        for model in MODELS:
            total = sum(int(r["n_truncated"]) for r in trunc if r["model"] == model and r["lang"] == lang)
            values[lang].append(total)
    bars_en = ax.bar([i - width / 2 for i in x], values["en"], width, label="English", color=EN_COLOR)
    bars_mk = ax.bar([i + width / 2 for i in x], values["mk"], width, label="Macedonian", color=MK_COLOR)
    label_bars(ax, bars_en, "%d")
    label_bars(ax, bars_mk, "%d")
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_NAMES[m] for m in MODELS], fontsize=8)
    ax.set_ylabel("Truncated responses (% of 100)")
    ax.set_ylim(0, 50)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=8)
    save(fig, "fig1_truncation.png")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    levels = {(r["analysis"], r["model"], r["lang"], int(r["level"])): r for r in read_csv("level_metrics.csv")}
    summary = {(r["analysis"], r["model"], r["lang"]): r for r in read_csv("summary_metrics.csv")}
    cats = {(r["analysis"], r["model"], r["lang"], r["category"]): r for r in read_csv("category_metrics.csv")}
    trunc = read_csv("truncation.csv")

    truncation_figure(trunc)
    en_vs_mk_figure(summary)
    by_level_figure(levels, "hsr", "HSR (%)", "fig3_hsr_by_level.png")
    category_heatmap(cats)
    by_level_figure(levels, "ssr", "SSR (%)", "fig5_ssr_by_level.png")
    a_vs_b_figure(summary)


if __name__ == "__main__":
    main()
