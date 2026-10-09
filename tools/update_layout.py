"""
tools/update_layout.py
----------------------
Re-sync a figure's layout after editing its .pptx file.

Steps performed for each figure:
  1. Extract panel positions/sizes from the .pptx (via extract_pptx_layout.py)
  2. Write layout.csv and layout.tex
  3. Regenerate placeholder PDFs at the new sizes

Usage (run from repo root):
    python tools/update_layout.py fig1
    python tools/update_layout.py fig1 fig2
"""

import argparse
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tools.extract_pptx_layout import extract, write_csv, write_layout_tex
from tools.style import make_fig, save_panel, apply_style
from tools.make_panels_example import FIG1_PANELS, FIG2_PANELS

_MM_PER_CHAR_PER_PT = 0.30

_PANEL_LISTS = {
    "fig1": FIG1_PANELS,
    "fig2": FIG2_PANELS,
}


def _wrap(text, w_mm, fontsize):
    chars = max(4, int(w_mm / (fontsize * _MM_PER_CHAR_PER_PT)))
    return "\n".join(textwrap.wrap(text, width=chars))


def _placeholder(panel_key, path, description, w_mm, h_mm):
    apply_style()
    fig, ax = make_fig(w_mm, h_mm)

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


def update(figure_prefix, slide_index=0):
    pptx_path = os.path.join("figures", figure_prefix, f"{figure_prefix}.pptx")
    if not os.path.exists(pptx_path):
        print(f"ERROR: {pptx_path} not found", file=sys.stderr)
        return

    out_dir = os.path.join("figures", figure_prefix)

    panels = extract(pptx_path, figure_prefix, slide_index)
    write_csv(panels, os.path.join(out_dir, "layout.csv"))
    write_layout_tex(panels, figure_prefix, os.path.join(out_dir, "layout.tex"))

    panel_list = _PANEL_LISTS.get(figure_prefix, [])
    desc_map = {key: desc for key, _, desc in panel_list}
    path_map = {key: path for key, path, _ in panel_list}

    for panel_key, v in panels.items():
        path = path_map.get(panel_key,
                            os.path.join(out_dir, "panels", f"{panel_key}.pdf"))
        desc = desc_map.get(panel_key, panel_key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _placeholder(panel_key, path, desc, v["w"], v["h"])


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("figures", nargs="+",
                        help='Figure prefix(es), e.g. "fig1" or "fig1 fig2"')
    parser.add_argument("--slide", type=int, default=0,
                        help="Slide index (0-based, default 0)")
    args = parser.parse_args()

    for prefix in args.figures:
        print(f"\n=== {prefix} ===")
        update(prefix, slide_index=args.slide)


if __name__ == "__main__":
    main()
