"""
src/adaptive_behavior/make_panels_example.py

Generates placeholder panel PDFs so the document compiles before real figures
exist. Each placeholder is sized at its exact display width (from PANEL_MM in
style.py) so the 7pt label text proves fonts will be correct in the final PDF.

Run from the repo root:   python -m adaptive_behavior.make_panels_example
"""

import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import sys
from adaptive_behavior.style import panel_fig, save_panel, PANEL_MM

_MM_PER_CHAR_PER_PT = 0.30


def _wrap(text, w_mm, fontsize):
    chars = max(4, int(w_mm / (fontsize * _MM_PER_CHAR_PER_PT)))
    return "\n".join(textwrap.wrap(text, width=chars))


def _placeholder(panel_key, path, description):
    w_mm, h_mm = PANEL_MM[panel_key]
    fig, ax = panel_fig(panel_key, h_mm=h_mm)

    ax.add_patch(plt.Rectangle((0, 0), 1, 1,
                                transform=ax.transAxes,
                                facecolor="#f4f4f4", edgecolor="#bbbbbb",
                                linewidth=0.5, zorder=0))

    letter = panel_key.split("_")[-1].upper()
    ax.text(0.5, 0.68, _wrap(f"{letter}  {w_mm:.0f}×{h_mm:.0f}mm", w_mm, 7),
            transform=ax.transAxes,
            fontsize=7, va="center", ha="center", color="#555555", clip_on=True)
    ax.text(0.5, 0.42, _wrap(description, w_mm, 6),
            transform=ax.transAxes,
            fontsize=6, va="center", ha="center", color="#888888", clip_on=True)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    save_panel(fig, path, pad=0)
    print("wrote", path)


# ---------------------------------------------------------------------------
# Update these lists to match your actual panels once the pptx is ready.

FIG1_PANELS = [
    ("fig1_A", "figures/fig1/panels/fig1_A.pdf", "Ethogram: patch visits across session"),
    ("fig1_B", "figures/fig1/panels/fig1_B.pdf", "P(stop) at first odor site by patch type"),
    ("fig1_C", "figures/fig1/panels/fig1_C.pdf", "Mean velocity at first-site odor onset"),
    ("fig1_D", "figures/fig1/panels/fig1_D.pdf", "Cumulative stop number per patch"),
    ("fig1_E", "figures/fig1/panels/fig1_E.pdf", "Mean velocity at last odor site before leaving"),
    ("fig1_F", "figures/fig1/panels/fig1_F.pdf", "P(leave) after consecutive reward omissions"),
    ("fig1_G", "figures/fig1/panels/fig1_G.pdf", "Mean velocity: reward omitted at first site"),
    ("fig1_H", "figures/fig1/panels/fig1_H.pdf", "TODO: describe panel H"),
]

FIG2_PANELS = [
    ("fig2_A", "figures/fig2/panels/fig2_A.pdf", "MVT schematic: local vs. global reward rate"),
    ("fig2_B", "figures/fig2/panels/fig2_B.pdf", "Depletion curves: High and Low patches"),
    ("fig2_C", "figures/fig2/panels/fig2_C.pdf", "Bayesian MVT model diagram"),
    ("fig2_D", "figures/fig2/panels/fig2_D.pdf", "Six leaving metrics — mice (N=24)"),
    ("fig2_E", "figures/fig2/panels/fig2_E.pdf", "Six leaving metrics — model"),
    ("fig2_F", "figures/fig2/panels/fig2_F.pdf", "P(reward) at leaving vs. inter-patch distance — mice"),
    ("fig2_G", "figures/fig2/panels/fig2_G.pdf", "P(reward) at leaving vs. inter-patch distance — model"),
    ("fig2_H", "figures/fig2/panels/fig2_H.pdf", "PCA trajectories of population activity"),
    ("fig2_I", "figures/fig2/panels/fig2_I.pdf", "Population PSTHs: heterogeneous cell types"),
]

if __name__ == "__main__":
    for key, path, desc in FIG1_PANELS + FIG2_PANELS:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _placeholder(key, path, desc)
