import marimo

__generated_with = "0.19.11"
app = marimo.App(
    width="full",
    app_title="DD-001 Illustration Annotation Editor",
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # DD-001 Illustration Annotation Editor

    Each illustration has two cells:

    1. **Annotation spec** — edit `xy`, `text`, `color`, `ha`, `style` directly in code
    2. **Live preview** — re-renders automatically on every change

    **Coordinates** — `xy` and `target` are **axes-fraction**: `(0, 0)` = bottom-left, `(1, 1)` = top-right.

    To add an arrow: set both `xy` (label anchor = arrow base) and `target` (arrow tip) in the **same dict**.
    Moving `xy` moves the label and the arrow together. No separate dicts needed.

    | key | meaning |
    |---|---|
    | `xy` | label position — also the arrow's base |
    | `target` | arrow tip (omit for a floating label with no arrow) |
    | `style` | `"box"` = rounded outline, `"plain"` = bare text |

    Hit **Save annotated** on any panel to write the final PNG to `notebooks/assets/`.
    """)
    return


@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    from flowmpl.illustrations import annotate_illustration, remove_background
    from flowmpl.design import COLORS, FONTS, INK, INK_LIGHT, INK_MID, PAPER

    ASSETS = Path(__file__).parent / "assets"

    # Shared palette shortcuts
    C_DARK  = INK
    C_MID   = INK_MID
    C_LIGHT = INK_LIGHT
    C_POS   = COLORS["positive"]
    C_NEG   = COLORS["negative"]
    C_NEUT  = COLORS["neutral"]
    FS      = FONTS["annotation"]   # 14
    FS_SM   = FONTS["small"]        # 11

    def preview(src_name: str, annotations: list[dict]) -> bytes:
        src = ASSETS / src_name
        transparent = remove_background(src)
        return annotate_illustration(transparent, annotations, dpi=120)

    def save_annotated(src_name: str, annotations: list[dict]) -> Path:
        src = ASSETS / src_name
        stem = src.stem
        dest = ASSETS / f"{stem}_annotated.png"
        transparent = remove_background(src)
        annotate_illustration(transparent, annotations, out_path=dest, dpi=150)
        return dest

    return (
        C_DARK,
        C_LIGHT,
        C_MID,
        C_NEG,
        C_NEUT,
        C_POS,
        FS_SM,
        mo,
        preview,
        save_annotated,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 1 · Off-balance-sheet commitments
    """)
    return


@app.cell
def _(C_LIGHT, C_MID, C_NEG, FS_SM):
    obs_annotations = [
        # Books area — top half. xy = label position (= arrow base), target = arrow tip on the books.
        dict(text="Declared in\nfinancial filings", xy=(0.78, 0.72),
             target=(0.65, 0.62),
             color=C_MID, fontsize=FS_SM, ha="left", va="center", style="box"),
        # Server racks — below waterline. target points into the server rack area.
        dict(text="Off-balance-sheet\ncommitments", xy=(0.78, 0.18),
             target=(0.65, 0.45),
             color=C_NEG, fontsize=FS_SM, ha="left", va="center", style="box"),
        # Stat note — no arrow
        dict(text="Microsoft: +~30% capex added in 3 months (Sep–Nov 2025)\n"
                  "Meta: 80% third-party financed",
             xy=(0.02, 0.94), color=C_LIGHT, fontsize=FS_SM - 1, ha="left", va="bottom"),
    ]
    return (obs_annotations,)


@app.cell
def _(mo, obs_annotations, preview, save_annotated):
    _png = preview("dd001_off_balance_sheet_illus.png", obs_annotations)
    _btn = mo.ui.button(label="Save annotated", on_click=lambda _: save_annotated(
        "dd001_off_balance_sheet_illus.png", obs_annotations))
    mo.vstack([mo.image(_png, width=700), _btn])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 2 · Six demand assumptions
    """)
    return


@app.cell
def _(C_LIGHT, C_MID, C_NEG, C_NEUT, C_POS, FS_SM):
    six_annotations = [
        # Near-term group (top two icons — solid lines)
        dict(text="Near-term\n(proven revenue)", xy=(0.60, 0.10),
             color=C_POS,  fontsize=FS_SM, ha="left", style="box"),
        dict(text="Better search",       xy=(0.82, 0.17), color=C_MID, fontsize=FS_SM, ha="left"),
        dict(text="Enterprise software", xy=(0.82, 0.30), color=C_MID, fontsize=FS_SM, ha="left"),
        # Medium-term (middle two — thin lines)
        dict(text="Medium-term\n(speculative)", xy=(0.60, 0.44),
             color=C_NEUT, fontsize=FS_SM, ha="left", style="box"),
        dict(text="AI assistants",  xy=(0.82, 0.44), color=C_MID, fontsize=FS_SM, ha="left"),
        dict(text="AI companions",  xy=(0.82, 0.56), color=C_MID, fontsize=FS_SM, ha="left"),
        # Long-term (bottom two — dotted lines)
        dict(text="Long-horizon\n(no commercial path)", xy=(0.60, 0.72),
             color=C_NEG,  fontsize=FS_SM, ha="left", style="box"),
        dict(text="Drug discovery",          xy=(0.82, 0.68), color=C_LIGHT, fontsize=FS_SM, ha="left"),
        dict(text="AGI / superintelligence", xy=(0.82, 0.82), color=C_LIGHT, fontsize=FS_SM, ha="left"),
    ]
    return (six_annotations,)


@app.cell
def _(mo, preview, save_annotated, six_annotations):
    _png = preview("dd001_six_demand_assumptions_illus.png", six_annotations)
    _btn = mo.ui.button(label="Save annotated", on_click=lambda _: save_annotated(
        "dd001_six_demand_assumptions_illus.png", six_annotations))
    mo.vstack([mo.image(_png, width=700), _btn])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 3 · Jevons paradox
    """)
    return


@app.cell
def _(C_LIGHT, C_NEG, C_POS, FS_SM):
    jev_annotations = [
        # Price tag (left)
        dict(text="Token cost\n−97%\n($60 → $2.50)", xy=(0.04, 0.78),
             color=C_POS,  fontsize=FS_SM, ha="left", style="box"),
        # Server stack (right)
        dict(text="Infrastructure\nspend: still\nrising", xy=(0.72, 0.20),
             color=C_NEG,  fontsize=FS_SM, ha="left", style="box"),
        # Interpretive question (bottom)
        dict(text="Cheaper compute → more usage → total spend rises\n"
                  "Does AI demand respond strongly enough?",
             xy=(0.50, 0.95), color=C_LIGHT, fontsize=FS_SM - 1,
             ha="center", va="bottom"),
    ]
    return (jev_annotations,)


@app.cell
def _(jev_annotations, mo, preview, save_annotated):
    _png = preview("dd001_jevons_paradox_illus.png", jev_annotations)
    _btn = mo.ui.button(label="Save annotated", on_click=lambda _: save_annotated(
        "dd001_jevons_paradox_illus.png", jev_annotations))
    mo.vstack([mo.image(_png, width=700), _btn])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 4 · Three paths forward
    """)
    return


@app.cell
def _(C_DARK, C_NEG, C_NEUT, C_POS, FS_SM):
    three_annotations = [
        # Centre gauge label
        dict(text="Capex ÷ Cloud\nRevenue ≈ 1×", xy=(0.38, 0.50),
             color=C_DARK, fontsize=FS_SM, ha="center", va="center", style="box"),
        # Lower-left — good path (sun + bar chart)
        dict(text="Ratio falls →\nDemand caught up", xy=(0.02, 0.82),
             color=C_POS,  fontsize=FS_SM, ha="left", style="box"),
        # Upper-left — neutral (hourglass)
        dict(text="Ratio holds →\nWait for more data", xy=(0.02, 0.16),
             color=C_NEUT, fontsize=FS_SM, ha="left", style="box"),
        # Right — warning (crumbling tower)
        dict(text="Ratio rises →\nOverbuilding signal", xy=(0.66, 0.40),
             color=C_NEG,  fontsize=FS_SM, ha="left", style="box"),
    ]
    return (three_annotations,)


@app.cell
def _(mo, preview, save_annotated, three_annotations):
    _png = preview("dd001_three_paths_illus.png", three_annotations)
    _btn = mo.ui.button(label="Save annotated", on_click=lambda _: save_annotated(
        "dd001_three_paths_illus.png", three_annotations))
    mo.vstack([mo.image(_png, width=700), _btn])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Save all four
    """)
    return


@app.cell
def _(
    jev_annotations,
    mo,
    obs_annotations,
    save_annotated,
    six_annotations,
    three_annotations,
):
    def _save_all(_):
        jobs = [
            ("dd001_off_balance_sheet_illus.png",      obs_annotations),
            ("dd001_six_demand_assumptions_illus.png",  six_annotations),
            ("dd001_jevons_paradox_illus.png",          jev_annotations),
            ("dd001_three_paths_illus.png",             three_annotations),
        ]
        saved = [save_annotated(fname, anns) for fname, anns in jobs]
        return [str(p) for p in saved]

    save_all_btn = mo.ui.button(label="Save all annotated PNGs", on_click=_save_all)
    save_all_btn
    return (save_all_btn,)


@app.cell
def _(mo, save_all_btn):
    mo.md(
        "\n".join(f"✓ `{p}`" for p in save_all_btn.value)
        if save_all_btn.value
        else ""
    )
    return


if __name__ == "__main__":
    app.run()
