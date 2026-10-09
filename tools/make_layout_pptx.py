"""
tools/make_layout_pptx.py
Create a layout PowerPoint for each figure with named, colored rectangles
representing panel slots. Edit positions/sizes in PowerPoint, then run:

    python tools/extract_pptx_layout.py figures/figN/figN.pptx --figure figN
    python tools/make_fig_tex.py figN --overwrite

Run from the repo root:
    python tools/make_layout_pptx.py
"""

import os
from pptx import Presentation
from pptx.util import Mm, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ---------------------------------------------------------------------------
# Figure layouts
# Each panel: (name, x_mm, y_mm, w_mm, h_mm)
# ---------------------------------------------------------------------------

# Fig 1 — Task design and behavior
# Row 1: A full-width ethogram
# Row 2: B, C, D  (stop prob / velocity onset / cumulative stops)
# Row 3: E, F, G  (pre-leave velocity / omission leaving / omission velocity)
_GAP = 5  # mm gap between panels

FIG1_PANELS = [
    ("fig1_A",   0,          0,          165,  38),   # ethogram — full width
    ("fig1_B",   0,          43,          52,  55),   # P(stop)
    ("fig1_C",   57,         43,          52,  55),   # velocity at onset
    ("fig1_D",   114,        43,          51,  55),   # cumulative stops
    ("fig1_E",   0,          103,         52,  55),   # pre-leave velocity
    ("fig1_F",   57,         103,         52,  55),   # omission leaving
    ("fig1_G",   114,        103,         51,  55),   # omission velocity
]

# Fig 2 — Bayesian MVT
# Row 1: A, B, C  (MVT schematic / depletion curves / model diagram)
# Row 2: D, E     (6 metrics mice / 6 metrics model)  — wider panels
# Row 3: F, G     (distance manipulation mice / model)
# Row 4: H, I     (PCA trajectories / PSTHs)
FIG2_PANELS = [
    ("fig2_A",   0,          0,           52,  52),   # MVT schematic
    ("fig2_B",   57,         0,           52,  52),   # depletion curves
    ("fig2_C",   114,        0,           51,  52),   # model diagram
    ("fig2_D",   0,          57,          80,  55),   # 6 metrics — mice
    ("fig2_E",   85,         57,          80,  55),   # 6 metrics — model
    ("fig2_F",   0,          117,         52,  52),   # distance — mice
    ("fig2_G",   57,         117,         52,  52),   # distance — model
    ("fig2_H",   114,        117,         51,  52),   # PCA trajectories
    ("fig2_I",   0,          174,        165,  52),   # PSTHs — full width
]

# Panel fill colors (light tints so the label is readable)
COLORS = [
    RGBColor(0xD0, 0xE8, 0xF5),  # blue
    RGBColor(0xD0, 0xF0, 0xE0),  # green
    RGBColor(0xF5, 0xE8, 0xD0),  # orange
    RGBColor(0xF0, 0xD0, 0xF0),  # purple
    RGBColor(0xF5, 0xF0, 0xD0),  # yellow
    RGBColor(0xD0, 0xF5, 0xF5),  # cyan
    RGBColor(0xF5, 0xD0, 0xD8),  # pink
    RGBColor(0xE8, 0xE8, 0xE8),  # grey
    RGBColor(0xD8, 0xF0, 0xD8),  # light green
]


def _figure_bounds(panels):
    max_x = max(x + w for _, x, y, w, h in panels)
    max_y = max(y + h for _, x, y, w, h in panels)
    return max_x, max_y


def make_pptx(fig_name, panels, out_dir):
    w_mm, h_mm = _figure_bounds(panels)

    prs = Presentation()
    prs.slide_width  = Mm(w_mm)
    prs.slide_height = Mm(h_mm)

    layout = prs.slide_layouts[6]  # blank
    slide  = prs.slides.add_slide(layout)

    for i, (name, x, y, w, h) in enumerate(panels):
        shape = slide.shapes.add_shape(
            1,  # MSO_SHAPE_TYPE.RECTANGLE
            Mm(x), Mm(y), Mm(w), Mm(h)
        )
        shape.name = name

        fill = shape.fill
        fill.solid()
        fill.fore_color.rgb = COLORS[i % len(COLORS)]

        line = shape.line
        line.color.rgb = RGBColor(0x80, 0x80, 0x80)
        line.width = Pt(0.5)

        tf = shape.text_frame
        tf.word_wrap = False
        p  = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        letter = name.split("_")[-1].upper()
        run.text = f"{letter}\n{w}×{h} mm"
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{fig_name}.pptx")
    prs.save(out_path)
    print(f"wrote {out_path}  ({w_mm:.0f} × {h_mm:.0f} mm slide)")
    return out_path


if __name__ == "__main__":
    make_pptx("fig1", FIG1_PANELS, "figures/fig1")
    make_pptx("fig2", FIG2_PANELS, "figures/fig2")
    print("\nNext steps:")
    print("  1. Open the .pptx files and move/resize panels as needed")
    print("  2. python tools/extract_pptx_layout.py figures/fig1/fig1.pptx --figure fig1")
    print("  3. python tools/make_fig_tex.py fig1 --overwrite")
