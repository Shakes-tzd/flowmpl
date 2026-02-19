"""Design system constants — colors, typography, sizing, element defaults.

Single source of truth for all visual decisions. Import these into every
chart module and notebook; never hardcode hex colors, font sizes, or figure
dimensions as magic numbers.
"""

from __future__ import annotations

# ───────────────────────────────────────────────────────────────────────────
# Semantic role colors
# ───────────────────────────────────────────────────────────────────────────

COLORS: dict[str, str] = {
    "positive":   "#228833",   # growth, increase, good (Paul Tol green)
    "negative":   "#EE6677",   # decline, decrease, bad  (Paul Tol red)
    "neutral":    "#888888",   # neither good nor bad
    "accent":     "#c44e52",   # highlight, call attention (warm red)
    "muted":      "#cccccc",   # de-emphasized, fallback
    "reference":  "#999999",   # reference lines, thresholds
    "text_dark":  "#323034",   # primary text on white bg
    "text_light": "#666666",   # secondary text, annotations
    "background": "#f5f5f5",   # map fills, chart backgrounds
    "grid":       "#e0e0e0",   # gridlines
}

# SWD gray+accent base — use for non-focus data elements.
# Everything starts CONTEXT gray; only the story element gets color.
# See helpers.focus_colors() for the standard application pattern.
CONTEXT: str = "#c0c0c0"


# ───────────────────────────────────────────────────────────────────────────
# Typography — font sizes by role
# ───────────────────────────────────────────────────────────────────────────

FONTS: dict[str, int] = {
    "axis_label":  15,   # xlabel, ylabel
    "tick_label":  14,   # xticklabels, yticklabels
    "annotation":  14,   # arrow annotations, callout text
    "value_label": 14,   # value labels on bars / scatter points
    "legend":      13,   # legend entries
    "panel_title": 14,   # subplot panel titles (multi_panel)
    "suptitle":    16,   # figure suptitle
    "caption":     11,   # figure captions, source notes
    "small":       11,   # small annotations, dense charts
}

# Standard font size for flow_diagram() — consistent text appearance
# across all notebooks when displayed at width=850 px.
FLOW_FONT_SIZE: int = 18


# ───────────────────────────────────────────────────────────────────────────
# Figure size presets
# ───────────────────────────────────────────────────────────────────────────

FIGSIZE: dict[str, tuple[float, float]] = {
    "single":    (10, 5),   # default for most charts
    "wide":      (12, 5),   # time series, many categories
    "tall":      (10, 7),   # vertical bar rankings
    "square":    (8,  7),   # scatter, pie
    "double":    (13, 5),   # side-by-side panels (1×2)
    "dashboard": (14, 8),   # 2×2 panel grids
    "map":       (12, 7),   # US scatter maps
    "large":     (16, 9),   # complex multi-panel
}


# ───────────────────────────────────────────────────────────────────────────
# Element defaults — consistent bar / scatter / legend styling
# ───────────────────────────────────────────────────────────────────────────

BAR_DEFAULTS: dict[str, object] = {
    "alpha":      0.85,
    "edgecolor":  "white",
    "linewidth":  0.5,
}

SCATTER_DEFAULTS: dict[str, object] = {
    "alpha":      0.6,
    "edgecolors": "white",
    "linewidth":  0.5,
}

LEGEND_DEFAULTS: dict[str, object] = {
    "handlelength": 1.5,
    "handleheight": 1.5,
}
