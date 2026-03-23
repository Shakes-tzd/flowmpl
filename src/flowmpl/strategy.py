"""Relationship-aware color strategy — maps FT Visual Vocabulary categories to color schemes."""

from __future__ import annotations

from typing import Sequence

from flowmpl.design import COLORS, CONTEXT
from flowmpl.palettes import CATEGORICAL

# ───────────────────────────────────────────────────────────────────────────
# Valid FT Visual Vocabulary relationship categories
# ───────────────────────────────────────────────────────────────────────────

RELATIONSHIPS: set[str] = {
    "deviation",
    "correlation",
    "ranking",
    "distribution",
    "change_over_time",
    "magnitude",
    "part_to_whole",
    "spatial",
    "flow",
}

# ───────────────────────────────────────────────────────────────────────────
# Chart recommendations per relationship category
# ───────────────────────────────────────────────────────────────────────────

_CHART_MAP: dict[str, list[str]] = {
    "deviation":        ["diverging_bar", "surplus_deficit_line"],
    "correlation":      ["scatter"],
    "ranking":          ["horizontal_bar_ranking", "lollipop", "slope_chart"],
    "distribution":     ["histogram", "strip_plot"],
    "change_over_time": ["annotated_series", "multi_panel"],
    "magnitude":        ["stacked_bar", "paired_bar"],
    "part_to_whole":    ["stacked_bar", "waterfall_chart"],
    "spatial":          ["us_scatter_map"],
    "flow":             ["flow_diagram"],
}


# ───────────────────────────────────────────────────────────────────────────
# Internal helpers
# ───────────────────────────────────────────────────────────────────────────

def _validate_relationship(relationship: str) -> None:
    """Raise ``ValueError`` if *relationship* is not a recognised category."""
    if relationship not in RELATIONSHIPS:
        sorted_names = sorted(RELATIONSHIPS)
        raise ValueError(
            f"Unknown relationship {relationship!r}. "
            f"Must be one of: {', '.join(sorted_names)}"
        )


def _resolve_focus(focus: str | set[str] | None) -> set[str]:
    """Normalise *focus* into a set (or empty set when ``None``)."""
    if focus is None:
        return set()
    if isinstance(focus, str):
        return {focus}
    return set(focus)


def _focus_accent_pattern(
    items: Sequence[str],
    focus: set[str],
    color_map: dict[str, str] | None,
    accent: str,
) -> list[str]:
    """Return accent color for focus items, CONTEXT gray for the rest.

    If *color_map* is provided, focus items use their mapped color instead of
    the default *accent*.
    """
    colors: list[str] = []
    for item in items:
        if item in focus:
            if color_map and item in color_map:
                colors.append(color_map[item])
            else:
                colors.append(accent)
        else:
            colors.append(CONTEXT)
    return colors


# ───────────────────────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────────────────────

def color_strategy(
    relationship: str,
    *,
    values: Sequence[float] | None = None,
    items: Sequence[str] | None = None,
    focus: str | set[str] | None = None,
    color_map: dict[str, str] | None = None,
    positive_color: str | None = None,
    negative_color: str | None = None,
    accent_color: str | None = None,
) -> list[str]:
    """Return a list of colors appropriate for *relationship* and the given data.

    Encodes the FT Visual Vocabulary colour logic: each relationship category
    implies a different mapping from data values / item identity to colour.

    Parameters
    ----------
    relationship : str
        One of the FT Visual Vocabulary categories: ``"deviation"``,
        ``"correlation"``, ``"ranking"``, ``"distribution"``,
        ``"change_over_time"``, ``"magnitude"``, ``"part_to_whole"``,
        ``"spatial"``, or ``"flow"``.
    values : sequence of float, optional
        Numeric data values — required for ``"deviation"`` (sign determines
        colour) and used as the sizing dimension for ``"correlation"``.
    items : sequence of str, optional
        Item / series labels in chart order.  Required for any relationship
        that uses the focus+context pattern (ranking, magnitude, etc.) and
        for ``"change_over_time"`` when cycling categorical colours.
    focus : str or set of str, optional
        Which items should be highlighted.  Everything else receives CONTEXT
        gray.
    color_map : dict mapping str to str, optional
        Item-to-colour overrides.  When supplied alongside *focus*, focus
        items use their mapped colour rather than the default accent.
    positive_color : str, optional
        Override for the positive (>= 0) colour in deviation charts.
        Defaults to ``COLORS["positive"]``.
    negative_color : str, optional
        Override for the negative (< 0) colour in deviation charts.
        Defaults to ``COLORS["negative"]``.
    accent_color : str, optional
        Override for the accent / highlight colour.
        Defaults to ``COLORS["accent"]``.

    Returns
    -------
    list of str
        Hex colour strings, one per data point / item.

    Raises
    ------
    ValueError
        If *relationship* is not recognised, or if required parameters for
        the chosen relationship are missing.

    Examples
    --------
    Deviation chart — colours follow the sign of each value:

    >>> color_strategy("deviation", values=[10, -5, 3, -8])
    ['#228833', '#EE6677', '#228833', '#EE6677']

    Ranking with a single focus item:

    >>> color_strategy(
    ...     "ranking",
    ...     items=["A", "B", "C"],
    ...     focus="B",
    ... )
    ['#c0c0c0', '#b84c2a', '#c0c0c0']
    """
    _validate_relationship(relationship)

    pos = positive_color or COLORS["positive"]
    neg = negative_color or COLORS["negative"]
    accent = accent_color or COLORS["accent"]

    # ── deviation ─────────────────────────────────────────────────────────
    if relationship == "deviation":
        if values is None:
            raise ValueError(
                "The 'deviation' relationship requires the 'values' parameter."
            )
        return [pos if v >= 0 else neg for v in values]

    # ── focus+context family ──────────────────────────────────────────────
    if relationship in {
        "ranking", "magnitude", "distribution",
        "part_to_whole", "spatial", "flow",
    }:
        if items is None:
            raise ValueError(
                f"The {relationship!r} relationship requires the 'items' parameter."
            )
        focus_set = _resolve_focus(focus)
        return _focus_accent_pattern(items, focus_set, color_map, accent)

    # ── correlation ───────────────────────────────────────────────────────
    if relationship == "correlation":
        if focus is not None and items is not None:
            focus_set = _resolve_focus(focus)
            return _focus_accent_pattern(items, focus_set, color_map, accent)
        # No focus → uniform first categorical colour
        n = len(values) if values is not None else (len(items) if items is not None else 0)
        return [CATEGORICAL[0]] * n

    # ── change_over_time ──────────────────────────────────────────────────
    if relationship == "change_over_time":
        if items is None:
            raise ValueError(
                "The 'change_over_time' relationship requires the 'items' parameter."
            )
        focus_set = _resolve_focus(focus)

        if focus_set and color_map:
            # Focus items get their mapped colour, rest get CONTEXT
            return _focus_accent_pattern(items, focus_set, color_map, accent)

        if focus_set:
            # Focus items get accent, rest get CONTEXT
            return _focus_accent_pattern(items, focus_set, None, accent)

        # No focus → cycle through the categorical palette
        n_cat = len(CATEGORICAL)
        return [CATEGORICAL[i % n_cat] for i in range(len(items))]

    # Unreachable — _validate_relationship guards against unknown values
    raise ValueError(f"Unhandled relationship: {relationship!r}")  # pragma: no cover


def suggest_chart(relationship: str) -> list[str]:
    """Return recommended flowmpl chart function names for *relationship*.

    Parameters
    ----------
    relationship : str
        One of the FT Visual Vocabulary categories (see
        :func:`color_strategy` for the full list).

    Returns
    -------
    list of str
        Function names from the ``flowmpl`` package that suit the given
        data relationship.

    Raises
    ------
    ValueError
        If *relationship* is not recognised.

    Examples
    --------
    >>> suggest_chart("deviation")
    ['diverging_bar', 'surplus_deficit_line']

    >>> suggest_chart("correlation")
    ['scatter']
    """
    _validate_relationship(relationship)
    return list(_CHART_MAP[relationship])
