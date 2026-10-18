"""src/adaptive_behavior/make_fig_tex.py
Generate figures/figN/figN.tex from figures/figN/layout.csv.

Usage (run from repo root):
    python -m adaptive_behavior.make_fig_tex fig3
    python -m adaptive_behavior.make_fig_tex fig3 fig4 fig6
    python -m adaptive_behavior.make_fig_tex fig3 --overwrite   # replace existing .tex
"""
import argparse
import csv
import math
import re
from pathlib import Path

_ROMAN = {
    "1": "I",  "2": "II", "3": "III", "4": "IV",  "5": "V",
    "6": "VI", "7": "VII","8": "VIII","9": "IX",   "10": "X",
}


def _roman(n: str) -> str:
    return _ROMAN[str(n)]


def _panel_letter(panel_name: str) -> str:
    """'fig3_A' -> 'A',  'fig3_AB' -> 'AB'"""
    m = re.match(r"fig\d+_([A-Za-z]+)$", panel_name)
    if not m:
        raise ValueError(f"Cannot parse panel letter from: {panel_name!r}")
    return m.group(1).upper()


def _fig_number(fig_name: str) -> str:
    m = re.match(r"fig(\d+)$", fig_name, re.IGNORECASE)
    if not m:
        raise ValueError(f"Cannot parse figure number from: {fig_name!r}")
    return m.group(1)


def _extract_caption(tex_path: Path) -> str | None:
    """Return the existing \\caption{...} block, or None if not found."""
    try:
        text = tex_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    m = re.search(r"(\\caption\{.*?)(?=\n\s*\\label\{fig:)", text, re.DOTALL)
    return "  " + m.group(1) if m else None  # tolerate a hand-unindented \caption


# Figures kept at their natural (pptx) size instead of being scaled to \linewidth
NATURAL_SIZE_FIGURES = {"fig2", "fig3"}  # fig2 = single-image design, fig3 = multi-panel design (see main.tex toggle)
# Figures whose caption sits to the right of the figure instead of below it
# Figures whose image and caption are separate floats (image first, caption on the next page)
SPLIT_CAPTION_FIGURES = {"fig2", "fig3"}
# Figures whose panels get no automatic bold letter overlay (letters are drawn in the panel itself)
NO_PANEL_LABEL_FIGURES = {"fig2"}
# Letters of panels drawn inside the first panel's image: invisible labels so captions can \subref them
EXTRA_LABEL_LETTERS = {"fig2": "BCDEFGHIJKLMNOPQR"}
# Negative space above the image float of a split figure (mm) to pull it up under the previous caption
FIG_TOP_VSPACE_MM = {"fig2": -13, "fig3": -13}
SIDE_CAPTION_FIGURES = set()  # fig2 now keeps its caption below the wide figure; add a name here for a side caption


def make_tex(fig_name: str, overwrite: bool = False) -> None:
    fig_dir     = Path("figures") / fig_name
    fig_dir_tex = fig_dir.as_posix()          # forward slashes for LaTeX
    csv_path    = fig_dir / "layout.csv"
    tex_path    = fig_dir / f"{fig_name}.tex"

    if not csv_path.exists():
        print(f"  ERROR: {csv_path} not found — run update_layout.py first")
        return
    if tex_path.exists() and not overwrite:
        print(f"  {tex_path} already exists — use --overwrite to replace")
        return

    # Preserve the existing caption if one is already written
    existing_caption = _extract_caption(tex_path) if tex_path.exists() else None

    with open(csv_path, newline="") as f:
        panels = list(csv.DictReader(f))

    # Sort panels in alphabetical order (A, B, C, …) regardless of pptx shape order
    panels.sort(key=lambda p: _panel_letter(p["panel"]))

    # Shapes named figN_Z, figN_ZZ, ... are frames drawn in the pptx around groups of
    # panels: not lettered panels. If panels/figN_Z.pdf exists (made in the notebook)
    # include it as a plain image, otherwise fall back to a plain rectangle
    frame_shapes = [p for p in panels if set(_panel_letter(p["panel"])) == {"Z"}]
    panels = [p for p in panels if p not in frame_shapes]
    frame_nodes = []
    for p in frame_shapes:
        x, y = float(p["x_mm"]), float(p["y_mm"])
        w, h = float(p["w_mm"]), float(p["h_mm"])
        pdf = fig_dir / "panels" / f"{p['panel']}.pdf"
        if pdf.exists():
            frame_nodes.append(
                f"    \\node[anchor=north west] at ({x:.1f}mm, {-y:.1f}mm) "
                f"{{\\includegraphics[width={w:.1f}mm,height={h:.1f}mm]{{{fig_dir_tex}/panels/{p['panel']}.pdf}}}};"
                f"  % frame {p['panel']}"
            )
        else:
            frame_nodes.append(
                f"    \\draw[line width=0.4pt] ({x:.1f}mm, {-y:.1f}mm) "
                f"rectangle ({x + w:.1f}mm, {-(y + h):.1f}mm);  % frame {p['panel']}"
            )

    num = _fig_number(fig_name)
    rom = _roman(num)

    nodes = []
    caption_entries = []

    for p in panels:
        name   = p["panel"]           # e.g. fig3_A
        letter = _panel_letter(name)  # e.g. A
        prefix = f"Fig{rom}{letter}"  # e.g. FigIIIA
        label  = f"fig:{num}-{letter.lower()}"

        graphic = f"\\panelgraphic[width=\\linewidth]{{{fig_dir_tex}/panels/{name}.pdf}}"
        if fig_name not in NO_PANEL_LABEL_FIGURES:
            graphic = f"\\panel{{{letter}}}{{{graphic}}}"   # overlay the bold panel letter
        nodes.append(
            f"    \\node[anchor=north west] at (\\{prefix}X, -\\{prefix}Y) {{%\n"
            f"      \\begin{{subfigure}}[t]{{\\{prefix}W}}%\n"
            f"        {graphic}%\n"
            f"        \\phantomsubcaption\\label{{{label}}}%\n"
            # panels drawn inside this image (not separate shapes): define their labels
            # too, so \subref{fig:N-x} in the caption resolves to the letter
            + "".join(f"        \\phantomsubcaption\\label{{fig:{num}-{c.lower()}}}%\n"
                      for c in EXTRA_LABEL_LETTERS.get(fig_name, "") if letter == "A")
            + f"      \\end{{subfigure}}}};"
        )
        caption_entries.append(f"    (\\subref{{{label}}}) Placeholder caption for panel {letter}.")

    node_block    = "\n\n".join(frame_nodes + nodes)
    caption_block = "\n".join(caption_entries)

    if existing_caption:
        caption_tex = existing_caption
        print(f"  preserving existing caption")
    else:
        caption_tex = (
            f"  \\caption{{\\textbf{{Title here.}}\n"
            f"{caption_block}}}"
        )

    # 10 pt captions for every figure
    # \footnotesize is exactly 10 pt in the 12 pt article class used by main.tex
    caption_size = "  \\captionsetup{font=footnotesize}  % 10 pt caption (footnotesize at 12 pt base)\n"
    side_caption = fig_name in SIDE_CAPTION_FIGURES
    if fig_name in NATURAL_SIZE_FIGURES:
        wrap_name = "makebox"
        fig_w_mm = math.ceil(max(float(p["x_mm"]) + float(p["w_mm"]) for p in panels + frame_shapes))
        # outer box = exactly \linewidth, so a figure wider than the text area is centered
        # symmetrically (overflowing both margins) instead of only to the right
        open_wrap = (f"\\makebox[\\linewidth][c]{{\\makebox[{fig_w_mm}mm][c]{{%"
                     f"  % natural size (no scaling), centered")
        align_block = "  \\centering  % centered\n" + caption_size
    else:
        wrap_name = "resizebox"
        open_wrap = "\\resizebox{\\linewidth}{!}{%"
        align_block = "  \\centering\n" + caption_size

    tikz_opts = "inner sep=0pt, outer sep=0pt"
    if side_caption:
        # A tikzpicture's baseline is its bottom edge, which would drop the caption
        # column below the figure. Put the baseline ~one cap height under the top
        # edge so the caption's first line sits level with the top of the figure.
        tikz_opts += ", baseline={([yshift=-7pt]current bounding box.north)}"

    tikz_block = (
        f"  {open_wrap}\n"
        f"  \\begin{{tikzpicture}}[{tikz_opts}]\n"
        f"\n"
        f"{node_block}\n"
        f"\n"
        f"  \\end{{tikzpicture}}}}{'}' if wrap_name == 'makebox' else ''}% end {wrap_name}\n"
    )
    caption_label = f"{caption_tex}\n  \\label{{fig:{num}}}\n"
    if side_caption:
        # figure on the left, caption in the remaining width on the right
        body = (
            f"  \\begin{{minipage}}[t]{{{fig_w_mm}mm}}%\n"
            f"{tikz_block}"
            f"  \\end{{minipage}}\\hfill%\n"
            f"  \\begin{{minipage}}[t]{{\\dimexpr\\linewidth-{fig_w_mm}mm-4mm\\relax}}%\n"
            f"{caption_label}"
            f"  \\end{{minipage}}\n"
        )
    else:
        body = f"{tikz_block}\n{caption_label}"

    tex = (
        f"% {fig_dir_tex}/{fig_name}.tex — auto-generated by src/adaptive_behavior/make_fig_tex.py\n"
        f"%\n"
        f"% Layout driven by exact PowerPoint coordinates from layout.tex.\n"
        f"% To regenerate this file after editing the pptx:\n"
        f"%   python -m adaptive_behavior.update_layout {fig_name}\n"
        f"%   python -m adaptive_behavior.make_fig_tex {fig_name} --overwrite\n"
        f"\n"
        f"\\input{{{fig_dir_tex}/layout.tex}}\n"
        f"\n"
        + (
            # image in an [H] float (sits right under the previous figure's caption),
            # caption in its own float; the image-only float steps the counter, undo it
            f"\\begin{{figure}}[H]\n"
            + (f"  \\vspace{{{FIG_TOP_VSPACE_MM[fig_name]}mm}}   % pulls the figure up; adjust to taste\n"
               if fig_name in FIG_TOP_VSPACE_MM else "")
            + f"{align_block}"
            f"  \\setcounter{{subfigure}}{{0}}\n"
            f"{tikz_block}"
            f"\\end{{figure}}\n"
            f"\n"
            f"\\addtocounter{{figure}}{{-1}}  % the image-only figure above steps the counter\n"
            f"\n"
            f"\\begin{{figure}}[H]\n"
            f"{caption_size}"
            f"{caption_label}"
            f"\\end{{figure}}\n"
            if fig_name in SPLIT_CAPTION_FIGURES else
            f"\\begin{{figure}}[p]\n"
            f"{align_block}"
            f"  \\setcounter{{subfigure}}{{0}}\n"
            f"{body}"
            f"\\end{{figure}}\n"
        )
    )

    tex_path.write_text(tex, encoding="utf-8")
    print(f"  wrote {tex_path}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate figN.tex from layout.csv",
        epilog="Run from the repo root. Use --overwrite to replace an existing .tex.",
    )
    ap.add_argument("figures", nargs="+", help="Figure name(s), e.g. fig3 fig6")
    ap.add_argument("--overwrite", action="store_true",
                    help="Replace existing .tex files (default: skip)")
    args = ap.parse_args()

    for fig in args.figures:
        print(f"=== {fig} ===")
        make_tex(fig, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
