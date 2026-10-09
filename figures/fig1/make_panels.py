"""
figures/fig1/make_panels.py
Generate all Figure 1 panels and save to figures/fig1/panels/.

Run from the repo root:
    python figures/fig1/make_panels.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tools.style import panel_fig, save_panel, PALETTE

PANELS_DIR = os.path.join(os.path.dirname(__file__), "panels")


# ---------------------------------------------------------------------------
# Panel A — Ethogram of patch visits across a session
# ---------------------------------------------------------------------------
def panel_A():
    fig, ax = panel_fig("fig1_A")

    # TODO: load session data and plot ethogram

    save_panel(fig, os.path.join(PANELS_DIR, "fig1_A.pdf"))


# ---------------------------------------------------------------------------
# Panel B — P(stop) at first odor site by patch type
# ---------------------------------------------------------------------------
def panel_B():
    fig, ax = panel_fig("fig1_B")

    # TODO: load stop probability data and plot bar/scatter

    save_panel(fig, os.path.join(PANELS_DIR, "fig1_B.pdf"))


# ---------------------------------------------------------------------------
# Panel C — Mean velocity at first-site odor onset by patch type
# ---------------------------------------------------------------------------
def panel_C():
    fig, ax = panel_fig("fig1_C")

    # TODO: load velocity traces and plot mean ± SEM by patch type

    save_panel(fig, os.path.join(PANELS_DIR, "fig1_C.pdf"))


# ---------------------------------------------------------------------------
# Panel D — Cumulative stop number per patch
# ---------------------------------------------------------------------------
def panel_D():
    fig, ax = panel_fig("fig1_D")

    # TODO: load stop count data and plot CDF

    save_panel(fig, os.path.join(PANELS_DIR, "fig1_D.pdf"))


# ---------------------------------------------------------------------------
# Panel E — Mean velocity at last odor site before leaving
# ---------------------------------------------------------------------------
def panel_E():
    fig, ax = panel_fig("fig1_E")

    # TODO: load pre-leaving velocity data and plot

    save_panel(fig, os.path.join(PANELS_DIR, "fig1_E.pdf"))


# ---------------------------------------------------------------------------
# Panel F — P(leave) after consecutive reward omissions
# ---------------------------------------------------------------------------
def panel_F():
    fig, ax = panel_fig("fig1_F")

    # TODO: load omission streak data; plot P(leave) by streak length and patch type

    save_panel(fig, os.path.join(PANELS_DIR, "fig1_F.pdf"))


# ---------------------------------------------------------------------------
# Panel G — Mean velocity: reward omitted at first site
# ---------------------------------------------------------------------------
def panel_G():
    fig, ax = panel_fig("fig1_G")

    # TODO: load omission velocity traces and plot

    save_panel(fig, os.path.join(PANELS_DIR, "fig1_G.pdf"))


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
    print("Fig 1 panels written to", PANELS_DIR)
