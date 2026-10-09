"""
figures/fig2/make_panels.py
Generate all Figure 2 panels and save to figures/fig2/panels/.

Run from the repo root:
    python figures/fig2/make_panels.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tools.style import panel_fig, save_panel, PALETTE

PANELS_DIR = os.path.join(os.path.dirname(__file__), "panels")


# ---------------------------------------------------------------------------
# Panel A — MVT schematic: local vs. global reward rate
# ---------------------------------------------------------------------------
def panel_A():
    fig, ax = panel_fig("fig2_A")

    # TODO: draw MVT schematic diagram

    save_panel(fig, os.path.join(PANELS_DIR, "fig2_A.pdf"))


# ---------------------------------------------------------------------------
# Panel B — Depletion curves: High and Low patches
# ---------------------------------------------------------------------------
def panel_B():
    fig, ax = panel_fig("fig2_B")

    # TODO: plot exponential depletion curves for high (p0=0.9) and low (p0=0.6)
    #       add dashed MVT leaving threshold

    save_panel(fig, os.path.join(PANELS_DIR, "fig2_B.pdf"))


# ---------------------------------------------------------------------------
# Panel C — Bayesian MVT model diagram
# ---------------------------------------------------------------------------
def panel_C():
    fig, ax = panel_fig("fig2_C")

    # TODO: draw model schematic (posterior update + Thompson sampling rule)

    save_panel(fig, os.path.join(PANELS_DIR, "fig2_C.pdf"))


# ---------------------------------------------------------------------------
# Panel D — Six leaving metrics: mice (N=24)
# ---------------------------------------------------------------------------
def panel_D():
    fig, ax = panel_fig("fig2_D")

    # TODO: load behavioral data; plot six metrics (P(reward) at leaving, etc.)
    #       highlight n.s. comparison for P(reward)

    save_panel(fig, os.path.join(PANELS_DIR, "fig2_D.pdf"))


# ---------------------------------------------------------------------------
# Panel E — Six leaving metrics: model
# ---------------------------------------------------------------------------
def panel_E():
    fig, ax = panel_fig("fig2_E")

    # TODO: load model simulation data; plot same six metrics as panel D

    save_panel(fig, os.path.join(PANELS_DIR, "fig2_E.pdf"))


# ---------------------------------------------------------------------------
# Panel F — P(reward) at leaving vs. inter-patch distance: mice
# ---------------------------------------------------------------------------
def panel_F():
    fig, ax = panel_fig("fig2_F")

    # TODO: load distance manipulation data; plot P(reward) at leaving vs. distance

    save_panel(fig, os.path.join(PANELS_DIR, "fig2_F.pdf"))


# ---------------------------------------------------------------------------
# Panel G — P(reward) at leaving vs. inter-patch distance: model
# ---------------------------------------------------------------------------
def panel_G():
    fig, ax = panel_fig("fig2_G")

    # TODO: load model simulation for distance manipulation; plot same as F

    save_panel(fig, os.path.join(PANELS_DIR, "fig2_G.pdf"))


# ---------------------------------------------------------------------------
# Panel H — PCA trajectories of population activity
# ---------------------------------------------------------------------------
def panel_H():
    fig, ax = panel_fig("fig2_H")

    # TODO: load neural data; run PCA; plot trajectories by task epoch / patch type

    save_panel(fig, os.path.join(PANELS_DIR, "fig2_H.pdf"))


# ---------------------------------------------------------------------------
# Panel I — Population PSTHs: heterogeneous cell types
# ---------------------------------------------------------------------------
def panel_I():
    fig, ax = panel_fig("fig2_I")

    # TODO: load spiking data; compute PSTHs; plot heatmap or mean traces by cell type

    save_panel(fig, os.path.join(PANELS_DIR, "fig2_I.pdf"))


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs(PANELS_DIR, exist_ok=True)
    panel_A()
    panel_B()
    panel_C()
    panel_D()
    panel_E()
    panel_F()
    panel_G()
    panel_H()
    panel_I()
    print("Fig 2 panels written to", PANELS_DIR)
