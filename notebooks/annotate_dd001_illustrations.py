#!/usr/bin/env python3
"""Post-process dd001 whiteboard illustrations: remove background + add annotations.

Pipeline per image:
  1. remove_background()  — cream → transparent, ink strokes stay opaque
  2. annotate_illustration() — overlay analytical callouts with flowmpl typography

Usage:
    uv run --with Pillow notebooks/annotate_dd001_illustrations.py

Outputs (saved alongside originals in notebooks/assets/):
    dd001_off_balance_sheet_annotated.png
    dd001_six_demand_assumptions_annotated.png
    dd001_jevons_paradox_annotated.png
    dd001_three_paths_annotated.png
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from flowmpl.illustrations import annotate_illustration, remove_background

ASSETS = Path(__file__).parent / "assets"

# ── Shared palette (flowmpl design tokens) ──────────────────────────────────
from flowmpl.design import COLORS, FONTS, INK, INK_LIGHT, INK_MID, PAPER  # noqa: E402

C_DARK   = INK           # "#1a1917" — primary ink
C_MID    = INK_MID       # "#4d4a46" — secondary labels
C_LIGHT  = INK_LIGHT     # "#9a9490" — captions / de-emphasised
C_POS    = COLORS["positive"]   # "#228833" — growth / good path
C_NEG    = COLORS["negative"]   # "#EE6677" — risk / bad path
C_NEUT   = COLORS["neutral"]    # "#888888" — neutral / wait

FS_ANN   = FONTS["annotation"]  # 14
FS_SM    = FONTS["small"]       # 11


# ── Helper ───────────────────────────────────────────────────────────────────

def process(src: Path, annotations: list[dict], suffix: str = "_annotated") -> Path:
    """Remove background then annotate; save next to original."""
    transparent = remove_background(src)
    dest = src.with_name(src.stem + suffix + ".png")
    annotate_illustration(transparent, annotations, out_path=dest, dpi=150)
    print(f"  ✓  {dest.name}")
    return dest


# ── 1. Off-balance-sheet ─────────────────────────────────────────────────────
# Image: two ledger books (REPORTED / ACTUAL) above waterline, iceberg body
# with server racks below.  Story: hidden infrastructure obligations that
# don't appear in official capex.

OBS_ANNOTATIONS = [
    # Top-right: label the above-waterline zone
    dict(
        text="Declared in\nfinancial filings",
        xy=(0.78, 0.18),
        color=C_MID,
        fontsize=FS_SM,
        ha="left",
        va="center",
        style="box",
    ),
    # Arrow from label into the books area
    dict(
        text="",
        xy=(0.77, 0.22),
        target=(0.60, 0.28),
        color=C_MID,
        fontsize=FS_SM,
    ),
    # Bottom-right: label the below-waterline zone
    dict(
        text="Off-balance-sheet\ncommitments",
        xy=(0.68, 0.72),
        color=C_NEG,
        fontsize=FS_SM,
        ha="left",
        va="center",
        style="box",
    ),
    # Arrow pointing into the server racks
    dict(
        text="",
        xy=(0.67, 0.70),
        target=(0.50, 0.65),
        color=C_NEG,
        fontsize=FS_SM,
    ),
    # Stat callout bottom-left
    dict(
        text="Microsoft: +~30% capex\nadded in 3 months (Sep–Nov 2025)\nMeta: 80% third-party financed",
        xy=(0.02, 0.92),
        color=C_LIGHT,
        fontsize=FS_SM - 1,
        ha="left",
        va="bottom",
    ),
]

# ── 2. Six demand assumptions ────────────────────────────────────────────────
# Image: money bag at left, six lines fanning right to icons.
# Top two (solid lines): near-term proven revenue.
# Middle two (thin lines): speculative medium-term.
# Bottom two (dotted): long-horizon, no commercial model.

SIX_ANNOTATIONS = [
    # Near-term group label
    dict(
        text="Near-term\n(proven revenue)",
        xy=(0.60, 0.10),
        color=C_POS,
        fontsize=FS_SM,
        ha="left",
        style="box",
    ),
    dict(text="Better search",        xy=(0.82, 0.17), color=C_MID, fontsize=FS_SM, ha="left"),
    dict(text="Enterprise software",  xy=(0.82, 0.30), color=C_MID, fontsize=FS_SM, ha="left"),
    # Medium-term
    dict(
        text="Medium-term\n(speculative)",
        xy=(0.60, 0.44),
        color=C_NEUT,
        fontsize=FS_SM,
        ha="left",
        style="box",
    ),
    dict(text="AI assistants",        xy=(0.82, 0.44), color=C_MID, fontsize=FS_SM, ha="left"),
    dict(text="AI companions",        xy=(0.82, 0.56), color=C_MID, fontsize=FS_SM, ha="left"),
    # Long-term
    dict(
        text="Long-horizon\n(no commercial path)",
        xy=(0.60, 0.72),
        color=C_NEG,
        fontsize=FS_SM,
        ha="left",
        style="box",
    ),
    dict(text="Drug discovery",       xy=(0.82, 0.68), color=C_LIGHT, fontsize=FS_SM, ha="left"),
    dict(text="AGI / superintelligence", xy=(0.82, 0.82), color=C_LIGHT, fontsize=FS_SM, ha="left"),
]

# ── 3. Jevons paradox ────────────────────────────────────────────────────────
# Image: price tag (↓) on left, = sign centre, server stack (↑) on right,
# question mark below centre, faint Victorian engine in background.

JEV_ANNOTATIONS = [
    # Left: token cost stat
    dict(
        text="Token cost\n−97%\n($60 → $2.50)",
        xy=(0.04, 0.75),
        color=C_POS,
        fontsize=FS_SM,
        ha="left",
        style="box",
    ),
    # Right: spend stat
    dict(
        text="Infrastructure\nspend: still\nrising",
        xy=(0.72, 0.75),
        color=C_NEG,
        fontsize=FS_SM,
        ha="left",
        style="box",
    ),
    # Bottom: interpretive question
    dict(
        text="Cheaper compute → more usage → total spend rises\n"
             "Does AI demand respond strongly enough?",
        xy=(0.50, 0.95),
        color=C_LIGHT,
        fontsize=FS_SM - 1,
        ha="center",
        va="bottom",
    ),
]

# ── 4. Three paths ───────────────────────────────────────────────────────────
# Image: central gauge/speedometer dial, three surrounding vignettes:
# sun + bar chart (lower-left), hourglass (upper-left), crumbling tower (right).

THREE_ANNOTATIONS = [
    # Centre gauge label
    dict(
        text="Capex ÷ Cloud\nRevenue ≈ 1×",
        xy=(0.38, 0.50),
        color=C_DARK,
        fontsize=FS_SM,
        ha="center",
        va="center",
        style="box",
    ),
    # Lower-left: good path
    dict(
        text="Ratio falls →\nDemand caught up",
        xy=(0.02, 0.82),
        color=C_POS,
        fontsize=FS_SM,
        ha="left",
        style="box",
    ),
    # Upper-left: neutral
    dict(
        text="Ratio holds →\nWait for more data",
        xy=(0.02, 0.16),
        color=C_NEUT,
        fontsize=FS_SM,
        ha="left",
        style="box",
    ),
    # Right: warning path
    dict(
        text="Ratio rises →\nOverbuilding signal",
        xy=(0.66, 0.40),
        color=C_NEG,
        fontsize=FS_SM,
        ha="left",
        style="box",
    ),
]

# ── Run ───────────────────────────────────────────────────────────────────────

JOBS = [
    ("dd001_off_balance_sheet_illus.png",     OBS_ANNOTATIONS,  "off-balance-sheet"),
    ("dd001_six_demand_assumptions_illus.png", SIX_ANNOTATIONS, "six-demand-assumptions"),
    ("dd001_jevons_paradox_illus.png",         JEV_ANNOTATIONS,  "jevons-paradox"),
    ("dd001_three_paths_illus.png",            THREE_ANNOTATIONS, "three-paths"),
]

outputs: list[Path] = []
for fname, anns, label in JOBS:
    src = ASSETS / fname
    if not src.exists():
        print(f"  ✗  {fname} not found — skipping")
        continue
    print(f"[{label}]")
    outputs.append(process(src, anns))

print(f"\nDone. {len(outputs)} annotated illustrations saved.")

# Open all outputs for inspection
for p in outputs:
    subprocess.run(["open", str(p)], check=False)
