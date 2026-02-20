"""Chart helper functions — annotations, reference lines, legends, color patterns.

All functions accept matplotlib Axes or Figure objects and modify them in-place
or return color lists. Nothing here creates figures — see charts.py and flow.py
for figure-creating functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from flowmpl.design import COLORS, CONTEXT, FONTS, LEGEND_DEFAULTS

if TYPE_CHECKING:
    from collections.abc import Sequence


def focus_colors(
    items: Sequence[str],
    focus: str | set[str],
    color_map: dict[str, str],
    *,
    context: str | None = None,
) -> list[str]:
    """Apply SWD gray+accent pattern to a list of items.

    Items in *focus* get their mapped color; everything else gets context gray.
    Works with any color mapping (COMPANY_COLORS, FUEL_COLORS, CATEGORICAL
    by index, etc.).

    Parameters
    ----------
    items : sequence of str
        Item keys in the order they appear on the chart.
    focus : str or set of str
        Which items should be colored (the story).
    color_map : dict
        Mapping from item key to color hex string.
    context : str, optional
        Override the default CONTEXT gray.

    Returns
    -------
    list[str]
        One color per item — accent for focus, gray for context.

    Example
    -------
    >>> focus_colors(
    ...     ["MSFT", "AMZN", "GOOGL", "META"],
    ...     focus="AMZN",
    ...     color_map=COMPANY_COLORS,
    ... )
    ['#c0c0c0', '#ff9900', '#c0c0c0', '#c0c0c0']
    """
    ctx = context or CONTEXT
    if isinstance(focus, str):
        focus = {focus}
    return [
        color_map.get(item, ctx) if item in focus else ctx
        for item in items
    ]


def chart_title(
    fig: plt.Figure,
    title: str,
    *,
    fontsize: int | None = None,
    color: str | None = None,
) -> None:
    """Add a subtle, left-aligned insight title to a figure.

    Designed to coexist with Marimo H1 headings: small enough not to
    dominate in the notebook, but present for standalone PNG use.
    Positioned above the axes area using fig.text().

    Parameters
    ----------
    fig : matplotlib Figure
    title : str
        Insight-driven title (e.g., "Capex doubled in two years").
    fontsize : int, optional
        Override default (FONTS["caption"]).
    color : str, optional
        Override default (COLORS["text_light"]).
    """
    fig.suptitle(
        title,
        fontsize=fontsize or FONTS["suptitle"],
        color=color or COLORS["text_light"],
        fontstyle="italic",
        x=0.02, ha="left",
    )
    # Re-run layout so tight_layout accounts for the suptitle; without this
    # the suptitle overlaps the top of the axes area.
    try:
        fig.tight_layout(rect=[0, 0, 1, 0.94])
    except Exception:
        pass  # no-op if figure uses constrained_layout


def annotate_point(
    ax: plt.Axes,
    text: str,
    xy: tuple[float, float],
    xytext: tuple[float, float],
    *,
    color: str | None = None,
    fontsize: int | None = None,
    arrowstyle: str = "->",
    arrow_lw: float = 1.5,
    bbox: bool = True,
    ha: str = "center",
    **kwargs: object,
) -> None:
    """Annotate a data point with consistent arrow + text styling.

    Parameters
    ----------
    ax : Axes
        Target axes.
    text : str
        Annotation text.
    xy : (x, y)
        Point to annotate (data coordinates).
    xytext : (x, y)
        Text position (data coordinates).
    color : str, optional
        Text and arrow color.  Defaults to COLORS["text_light"].
    fontsize : int, optional
        Font size.  Defaults to FONTS["annotation"].
    arrowstyle : str
        Matplotlib arrow style string.
    arrow_lw : float
        Arrow line width.
    bbox : bool
        Whether to draw a rounded box behind the text.
    ha : str
        Horizontal alignment.
    **kwargs
        Forwarded to ax.annotate().
    """
    color = color or COLORS["text_light"]
    fontsize = fontsize or FONTS["annotation"]

    bbox_props = (
        {"boxstyle": "round,pad=0.3", "fc": "white", "ec": color, "alpha": 0.8}
        if bbox
        else None
    )

    ax.annotate(
        text,
        xy=xy,
        xytext=xytext,
        fontsize=fontsize,
        fontweight="bold",
        color=color,
        ha=ha,
        arrowprops={"arrowstyle": arrowstyle, "color": color, "lw": arrow_lw},
        bbox=bbox_props,
        **kwargs,
    )


def reference_line(
    ax: plt.Axes,
    value: float,
    orientation: str = "h",
    *,
    label: str | None = None,
    color: str | None = None,
    linestyle: str = "--",
    linewidth: float = 1.5,
    alpha: float = 0.7,
    label_pos: str = "right",
) -> None:
    """Add a labeled reference line (horizontal or vertical).

    Parameters
    ----------
    ax : Axes
        Target axes.
    value : float
        Position of the line.
    orientation : "h" or "v"
        Horizontal or vertical line.
    label : str, optional
        Text label placed near the line.
    color : str, optional
        Line and label color.  Defaults to COLORS["reference"].
    linestyle : str
        Line style.
    linewidth : float
        Line width.
    alpha : float
        Line transparency.
    label_pos : "left" or "right" (for h) / "top" or "bottom" (for v)
        Where to place the label text.
    """
    color = color or COLORS["reference"]
    line_fn = ax.axhline if orientation == "h" else ax.axvline
    line_fn(value, color=color, linestyle=linestyle, linewidth=linewidth, alpha=alpha)

    if label:
        if orientation == "h":
            _x = ax.get_xlim()[1] if label_pos == "right" else ax.get_xlim()[0]
            _ha = "right" if label_pos == "right" else "left"
            ax.text(
                _x, value, f" {label} ",
                fontsize=FONTS["small"], color=color, fontweight="bold",
                va="bottom", ha=_ha,
            )
        else:
            _y = ax.get_ylim()[1] if label_pos == "top" else ax.get_ylim()[0]
            _va = "top" if label_pos == "top" else "bottom"
            ax.text(
                value, _y, f" {label} ",
                fontsize=FONTS["small"], color=color, fontweight="bold",
                va=_va, ha="left",
            )


def legend_below(
    ax: plt.Axes,
    *,
    ncol: int | None = None,
    handles: list | None = None,
    labels: list[str] | None = None,
    **kwargs: object,
) -> None:
    """Place legend below the axes in a horizontal column layout.

    Works with save_fig's ``bbox_inches='tight'`` to auto-expand the
    saved figure so the legend is never clipped.

    Parameters
    ----------
    ax : Axes
        The axes whose legend to relocate.
    ncol : int, optional
        Number of columns.  Defaults to ``min(len(handles), 5)``.
    handles, labels : optional
        Explicit legend handles/labels.  When *None*, pulled from *ax*.
    **kwargs
        Forwarded to ``ax.legend()``.
    """
    if handles is None:
        h, lab = ax.get_legend_handles_labels()
        handles = h
        if labels is None:
            labels = lab
    elif labels is None:
        labels = [h.get_label() for h in handles]
    if not handles:
        return
    if ncol is None:
        ncol = min(len(handles), 5)
    old = ax.get_legend()
    if old:
        old.remove()
    _anchor = kwargs.pop("bbox_to_anchor", (0.5, -0.15))
    _fontsize = kwargs.pop("fontsize", FONTS["legend"])
    _merged = {**LEGEND_DEFAULTS, **kwargs}
    ax.legend(
        handles, labels,
        loc="upper center",
        bbox_to_anchor=_anchor,
        ncol=ncol,
        fontsize=_fontsize,
        frameon=False,
        **_merged,
    )
