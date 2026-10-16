"""
src/adaptive_behavior/style.py
--------------
Matplotlib helpers for publication-ready panels.

Panel sizes
-----------
Each panel must be created at its exact display width so LaTeX scales it 1:1
and font sizes are correct. Use PANEL_MM to get the display width:

    from adaptive_behavior.style import panel_fig, save_panel, PALETTE

    fig, ax = panel_fig("fig1_A", h_mm=50)   # correct width automatically
    ax.scatter(x, y, color=PALETTE["high"])
    save_panel(fig, "figures/fig1/panels/fig1_A.pdf")

PANEL_LAYOUT stores each panel's position and size derived from the figure
layout (x, y from upper-left corner; w, h in mm). Run
src/adaptive_behavior/extract_pptx_layout.py on a PowerPoint draft to fill in x/y values.

PANEL_MM is a backward-compatible alias: {key: (w, h)} derived from PANEL_LAYOUT.
"""

import csv
import os
import string

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


def _load_csv_layout(csv_path):
    out = {}
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            out[row["panel"]] = {
                "x": float(row["x_mm"]),
                "y": float(row["y_mm"]),
                "w": float(row["w_mm"]),
                "h": float(row["h_mm"]),
            }
    return out


def _grid_layout(fig_key, n_panels, ncols=3, panel_h_mm=50.0):
    panel_w_mm = round(TEXTWIDTH_MM / ncols, 1)
    out = {}
    for i, letter in enumerate(string.ascii_uppercase[:n_panels]):
        row, col = divmod(i, ncols)
        out[f"{fig_key}_{letter}"] = {
            "x": round(col * panel_w_mm, 1),
            "y": round(row * panel_h_mm, 1),
            "w": panel_w_mm,
            "h": panel_h_mm,
        }
    return out


def _auto_discover_layouts(figures_dir):
    layout = {}
    if not os.path.isdir(figures_dir):
        return layout
    for fig_name in sorted(os.listdir(figures_dir)):
        fig_dir = os.path.join(figures_dir, fig_name)
        if not os.path.isdir(fig_dir):
            continue
        csv_path = os.path.join(fig_dir, "layout.csv")
        if os.path.isfile(csv_path):
            layout.update(_load_csv_layout(csv_path))
            continue
        panels_dir = os.path.join(fig_dir, "panels")
        if not os.path.isdir(panels_dir):
            continue
        letters = {
            fname.rsplit(".", 1)[0][-1]
            for fname in os.listdir(panels_dir)
            if fname.startswith(fig_name + "_")
            and fname.rsplit(".", 1)[-1].lower() in ("pdf", "png")
            and fname.rsplit(".", 1)[0][-1] in string.ascii_uppercase
        }
        if letters:
            max_idx = max(string.ascii_uppercase.index(l) for l in letters)
            layout.update(_grid_layout(fig_name, max_idx + 1))
    return layout


# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------

PANEL_STYLE = {
    "font.family":          "sans-serif",
    "font.sans-serif":      ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size":            7,
    "axes.labelsize":       7,
    "axes.titlesize":       7,
    "xtick.labelsize":      6,
    "ytick.labelsize":      6,
    "legend.fontsize":      6,
    "axes.linewidth":       0.5,
    "lines.linewidth":      0.3,
    "xtick.major.width":    0.5,
    "ytick.major.width":    0.5,
    "xtick.major.size":     2.5,
    "ytick.major.size":     2.5,
    "xtick.direction":      "out",
    "ytick.direction":      "out",
    "xtick.minor.visible":  False,
    "ytick.minor.visible":  False,
    "axes.spines.top":      False,
    "axes.spines.right":    False,
    "axes.grid":            False,
    "pdf.fonttype":         42,
    "ps.fonttype":          42,
    "figure.dpi":           300,
}

PALETTE = {
    "high":  "#d95f02",   # orange
    "low":   "#1b9e77",   # green
    "null":  "#7570b3",   # purple
    "rbar":  "#2d2d2d",   # near-black
}

# ---------------------------------------------------------------------------
# Panel display sizes
# ---------------------------------------------------------------------------
# Single-column abstract on 8.5x11" with 1" margins: ~165 mm text width.

TEXTWIDTH_MM = 165.0

_FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "figures")
PANEL_LAYOUT = _auto_discover_layouts(_FIGURES_DIR)
PANEL_MM = {k: (v["w"], v["h"]) for k, v in PANEL_LAYOUT.items()}


def apply_style():
    matplotlib.rcParams.update(PANEL_STYLE)


# ---------------------------------------------------------------------------
# Figure / axes creation
# ---------------------------------------------------------------------------

def panel_fig(panel_key, h_mm=None, nrows=1, ncols=1, **subplot_kw):
    w_mm, default_h = PANEL_MM[panel_key]
    if h_mm is None:
        h_mm = default_h
    return make_fig(w_mm, h_mm, nrows=nrows, ncols=ncols, **subplot_kw)


def make_fig(w_mm, h_mm, nrows=1, ncols=1, **subplot_kw):
    apply_style()
    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(w_mm / 25.4, h_mm / 25.4),
        **subplot_kw,
    )
    if nrows == 1 and ncols == 1:
        clean_ax(axes)
        return fig, axes
    for ax in np.asarray(axes).flat:
        clean_ax(ax)
    return fig, axes


# ---------------------------------------------------------------------------
# Axis cleanup
# ---------------------------------------------------------------------------

def clean_ax(ax, n_xticks=4, n_yticks=4, trim_spines=False):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", direction="out", width=0.5, length=2.5)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=n_xticks, steps=[1, 2, 5, 10]))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=n_yticks, steps=[1, 2, 5, 10]))
    ax.grid(False)
    if trim_spines:
        _trim_spines(ax)
    return ax


def _trim_spines(ax):
    ax.figure.canvas.draw()
    xticks = ax.get_xticks()
    xticks = xticks[(xticks >= ax.get_xlim()[0]) & (xticks <= ax.get_xlim()[1])]
    yticks = ax.get_yticks()
    yticks = yticks[(yticks >= ax.get_ylim()[0]) & (yticks <= ax.get_ylim()[1])]
    if len(xticks):
        ax.spines["bottom"].set_bounds(xticks[0], xticks[-1])
    if len(yticks):
        ax.spines["left"].set_bounds(yticks[0], yticks[-1])


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------

def save_panel(fig, path, pad=0.3, dpi=300):
    fig.tight_layout(pad=pad)
    fmt = "png" if str(path).lower().endswith(".png") else "pdf"
    fig.savefig(path, format=fmt, dpi=dpi if fmt == "png" else None)
    plt.close(fig)
