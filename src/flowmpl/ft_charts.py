"""FT Visual Vocabulary chart types — deviation, correlation, distribution, magnitude.

Complements charts.py (change-over-time, part-to-whole, ranking) with the
remaining FT Visual Vocabulary categories. All functions return matplotlib
Figure objects.

Optional dependency: pandas>=2.0 (required by dataframe-based functions).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from flowmpl.design import COLORS, FIGSIZE, FONTS, SCATTER_DEFAULTS
from flowmpl.helpers import chart_title, legend_below
from flowmpl.palettes import CATEGORICAL

if TYPE_CHECKING:
    import pandas as pd


# ═══════════════════════════════════════════════════════════════════════════
# Deviation
# ═══════════════════════════════════════════════════════════════════════════


def diverging_bar(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    title: str,
    *,
    baseline: float = 0,
    positive_color: str = COLORS["positive"],
    negative_color: str = COLORS["negative"],
    xlabel: str = "",
    figsize: tuple[float, float] = FIGSIZE["tall"],
) -> plt.Figure:
    """Horizontal bars diverging from a baseline value.

    Best for showing deviation from a reference point — e.g. profit vs loss,
    above/below average, sentiment scores.

    Parameters
    ----------
    df : DataFrame
        Source data.
    category_col : str
        Column containing category labels (y-axis).
    value_col : str
        Column containing numeric values to plot.
    title : str
        Insight-driven chart title.
    baseline : float
        Value from which bars diverge. Default 0.
    positive_color : str
        Color for bars >= baseline.
    negative_color : str
        Color for bars < baseline.
    xlabel : str
        X-axis label.
    figsize : tuple
        Figure size.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    categories = df[category_col].values
    values = df[value_col].values.astype(float)
    deviations = values - baseline

    y = np.arange(len(categories))
    bar_colors = [
        positive_color if d >= 0 else negative_color for d in deviations
    ]

    ax.barh(y, deviations, color=bar_colors, height=0.6, edgecolor="white")
    ax.axvline(0, color=COLORS["reference"], linewidth=0.8)

    ax.set_yticks(y)
    ax.set_yticklabels(categories)
    ax.set_xlabel(xlabel, fontsize=FONTS["axis_label"])
    ax.invert_yaxis()
    ax.set_ylim(len(categories) - 0.5, -0.5)

    for i, d in enumerate(deviations):
        ha = "left" if d >= 0 else "right"
        offset = max(abs(deviations)) * 0.02 * (1 if d >= 0 else -1)
        ax.text(
            d + offset, i, f"{d:+,.1f}",
            va="center", ha=ha, fontsize=FONTS["value_label"],
        )

    plt.tight_layout()
    chart_title(fig, title)
    return fig


def surplus_deficit_line(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    *,
    baseline: float = 0,
    positive_color: str = COLORS["positive"],
    negative_color: str = COLORS["negative"],
    line_color: str = CATEGORICAL[0],
    ylabel: str = "",
    figsize: tuple[float, float] = FIGSIZE["single"],
) -> plt.Figure:
    """Time series with positive/negative fill relative to a baseline.

    Fills above the baseline in one color and below in another, making
    surplus and deficit periods immediately visible.

    Parameters
    ----------
    df : DataFrame
        Source data.
    x_col : str
        Column for x-axis values (typically dates).
    y_col : str
        Column for y-axis values.
    title : str
        Insight-driven chart title.
    baseline : float
        Reference value separating surplus from deficit. Default 0.
    positive_color : str
        Fill color for values >= baseline.
    negative_color : str
        Fill color for values < baseline.
    line_color : str
        Color of the data line itself.
    ylabel : str
        Y-axis label.
    figsize : tuple
        Figure size.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    x = df[x_col].values
    y = df[y_col].values.astype(float)

    ax.plot(x, y, color=line_color, linewidth=1.5)
    ax.axhline(baseline, color=COLORS["reference"], linewidth=0.8, linestyle="--")

    ax.fill_between(x, y, baseline, where=(y >= baseline),
                    color=positive_color, alpha=0.25, interpolate=True)
    ax.fill_between(x, y, baseline, where=(y < baseline),
                    color=negative_color, alpha=0.25, interpolate=True)

    ax.set_ylabel(ylabel, fontsize=FONTS["axis_label"])
    plt.tight_layout()
    chart_title(fig, title)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# Correlation
# ═══════════════════════════════════════════════════════════════════════════


def scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    *,
    size_col: str | None = None,
    color_col: str | None = None,
    regression: bool = False,
    xlabel: str = "",
    ylabel: str = "",
    size_scale: float = 200.0,
    color_map: dict[str, str] | None = None,
    default_color: str = CATEGORICAL[0],
    figsize: tuple[float, float] = FIGSIZE["square"],
) -> plt.Figure:
    """Scatter plot with optional bubble sizing, color grouping, and regression.

    Supports three modes of increasing complexity:
    1. Plain scatter (x vs y)
    2. Bubble chart (x vs y vs size)
    3. Grouped bubble chart (x vs y vs size vs color)

    Parameters
    ----------
    df : DataFrame
        Source data.
    x_col : str
        Column for x-axis values.
    y_col : str
        Column for y-axis values.
    title : str
        Insight-driven chart title.
    size_col : str, optional
        Column to map to marker area. When None, all markers are equal size.
    color_col : str, optional
        Column whose unique values determine marker color groups.
    regression : bool
        If True, overlay an OLS regression line with R-squared annotation.
    xlabel : str
        X-axis label.
    ylabel : str
        Y-axis label.
    size_scale : float
        Scaling factor for bubble sizes. Default 200.
    color_map : dict, optional
        Mapping of color_col values to hex colors. Falls back to CATEGORICAL.
    default_color : str
        Marker color when color_col is None.
    figsize : tuple
        Figure size.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    x = df[x_col].values.astype(float)
    y = df[y_col].values.astype(float)

    # Sizes
    if size_col is not None:
        raw_sizes = df[size_col].values.astype(float)
        sizes = (raw_sizes / raw_sizes.max()) * size_scale
    else:
        sizes = np.full(len(x), 60.0)

    # Colors
    if color_col is not None:
        groups = df[color_col].values
        unique_groups = list(dict.fromkeys(groups))  # preserve order
        if color_map is None:
            color_map = {
                g: CATEGORICAL[i % len(CATEGORICAL)]
                for i, g in enumerate(unique_groups)
            }
        for group in unique_groups:
            mask = groups == group
            ax.scatter(
                x[mask], y[mask],
                s=sizes[mask],
                color=color_map.get(group, default_color),
                label=str(group),
                **SCATTER_DEFAULTS,
            )
    else:
        ax.scatter(x, y, s=sizes, color=default_color, **SCATTER_DEFAULTS)

    # Regression line
    if regression:
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() > 1:
            coeffs = np.polyfit(x[mask], y[mask], 1)
            poly = np.poly1d(coeffs)
            x_sorted = np.sort(x[mask])
            ax.plot(
                x_sorted, poly(x_sorted),
                color=COLORS["reference"], linewidth=1.5, linestyle="--",
            )
            # R-squared
            y_pred = poly(x[mask])
            ss_res = np.sum((y[mask] - y_pred) ** 2)
            ss_tot = np.sum((y[mask] - np.mean(y[mask])) ** 2)
            r_sq = 1 - ss_res / ss_tot if ss_tot != 0 else 0
            ax.text(
                0.95, 0.05, f"R² = {r_sq:.2f}",
                transform=ax.transAxes, fontsize=FONTS["annotation"],
                ha="right", va="bottom", color=COLORS["text_light"],
            )

    ax.set_xlabel(xlabel, fontsize=FONTS["axis_label"])
    ax.set_ylabel(ylabel, fontsize=FONTS["axis_label"])

    plt.tight_layout()
    if color_col is not None:
        legend_below(ax)
    chart_title(fig, title)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# Ranking
# ═══════════════════════════════════════════════════════════════════════════


def lollipop(
    labels: list[str],
    values: list[float],
    title: str,
    *,
    orientation: str = "horizontal",
    highlight_indices: list[int] | None = None,
    color: str = CATEGORICAL[0],
    highlight_color: str = COLORS["accent"],
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple[float, float] = FIGSIZE["tall"],
) -> plt.Figure:
    """Lollipop chart — a cleaner alternative to bar charts for rankings.

    Draws a stem (line) from the axis to a dot at each value, reducing
    visual clutter compared to filled bars.

    Parameters
    ----------
    labels : list of str
        Category labels.
    values : list of float
        Values for each category.
    title : str
        Insight-driven chart title.
    orientation : str
        "horizontal" (default) or "vertical".
    highlight_indices : list of int, optional
        Indices to highlight in a different color.
    color : str
        Default stem and dot color.
    highlight_color : str
        Color for highlighted items.
    xlabel : str
        X-axis label.
    ylabel : str
        Y-axis label.
    figsize : tuple
        Figure size.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    positions = np.arange(len(labels))

    colors = [color] * len(labels)
    if highlight_indices:
        for idx in highlight_indices:
            if 0 <= idx < len(colors):
                colors[idx] = highlight_color

    if orientation == "horizontal":
        for i, (pos, val) in enumerate(zip(positions, values)):
            ax.hlines(pos, 0, val, color=colors[i], linewidth=1.5)
            ax.plot(val, pos, "o", color=colors[i], markersize=8)
        ax.set_yticks(positions)
        ax.set_yticklabels(labels)
        ax.set_xlabel(xlabel, fontsize=FONTS["axis_label"])
        ax.invert_yaxis()
        ax.set_ylim(len(labels) - 0.5, -0.5)

        for i, v in enumerate(values):
            ax.text(
                v + max(values) * 0.02, i, f"{v:,.0f}",
                va="center", fontsize=FONTS["value_label"],
            )
    else:
        for i, (pos, val) in enumerate(zip(positions, values)):
            ax.vlines(pos, 0, val, color=colors[i], linewidth=1.5)
            ax.plot(pos, val, "o", color=colors[i], markersize=8)
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_ylabel(ylabel, fontsize=FONTS["axis_label"])

        for i, v in enumerate(values):
            ax.text(
                i, v + max(values) * 0.02, f"{v:,.0f}",
                ha="center", va="bottom", fontsize=FONTS["value_label"],
            )

    plt.tight_layout()
    chart_title(fig, title)
    return fig


def slope_chart(
    left_values: list[float],
    right_values: list[float],
    labels: list[str],
    title: str,
    *,
    left_label: str = "Before",
    right_label: str = "After",
    highlight: str | set[str] | None = None,
    color: str = COLORS["muted"],
    highlight_color: str = COLORS["accent"],
    figsize: tuple[float, float] = FIGSIZE["single"],
) -> plt.Figure:
    """Slope chart showing change between two points in time or conditions.

    Lines connect left values to right values for each label, making it
    easy to spot which items improved, declined, or stayed flat.

    Parameters
    ----------
    left_values : list of float
        Values at the starting point.
    right_values : list of float
        Values at the ending point.
    labels : list of str
        Label for each item.
    title : str
        Insight-driven chart title.
    left_label : str
        Column header for the left side.
    right_label : str
        Column header for the right side.
    highlight : str or set of str, optional
        Labels to highlight with accent color.
    color : str
        Default line color for non-highlighted items.
    highlight_color : str
        Color for highlighted items.
    figsize : tuple
        Figure size.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    if highlight is not None and isinstance(highlight, str):
        highlight = {highlight}

    x_left, x_right = 0, 1

    for i, (lv, rv, lab) in enumerate(zip(left_values, right_values, labels)):
        is_focus = highlight is not None and lab in highlight
        c = highlight_color if is_focus else color
        lw = 2.5 if is_focus else 1.2
        alpha = 1.0 if is_focus else 0.5
        zorder = 10 if is_focus else 1

        ax.plot(
            [x_left, x_right], [lv, rv],
            color=c, linewidth=lw, alpha=alpha, zorder=zorder,
        )
        ax.scatter(
            [x_left, x_right], [lv, rv],
            color=c, s=40, zorder=zorder + 1,
        )

        # Labels on right side
        ax.text(
            x_right + 0.03, rv, lab,
            va="center", fontsize=FONTS["value_label"],
            color=c, alpha=alpha, fontweight="bold" if is_focus else "normal",
        )
        # Values on left side
        ax.text(
            x_left - 0.03, lv, f"{lv:,.0f}",
            va="center", ha="right", fontsize=FONTS["value_label"],
            color=c, alpha=alpha,
        )

    ax.set_xlim(-0.15, 1.25)
    ax.set_xticks([x_left, x_right])
    ax.set_xticklabels([left_label, right_label], fontsize=FONTS["axis_label"],
                       fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False, labelleft=False)

    plt.tight_layout()
    chart_title(fig, title)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# Distribution
# ═══════════════════════════════════════════════════════════════════════════


def histogram(
    values: list[float] | np.ndarray,
    title: str,
    *,
    bins: int | str = "auto",
    highlight_range: tuple[float, float] | None = None,
    color: str = CATEGORICAL[0],
    highlight_color: str = COLORS["accent"],
    xlabel: str = "",
    ylabel: str = "Frequency",
    figsize: tuple[float, float] = FIGSIZE["single"],
) -> plt.Figure:
    """Histogram with optional highlighted range.

    Draws a standard histogram and optionally colors a specific range
    of bins differently to draw attention to a region of interest.

    Parameters
    ----------
    values : array-like
        Numeric values to bin.
    title : str
        Insight-driven chart title.
    bins : int or str
        Number of bins or binning strategy (passed to numpy). Default "auto".
    highlight_range : (lo, hi), optional
        Values within [lo, hi] are colored with highlight_color.
    color : str
        Default bar color.
    highlight_color : str
        Color for bars within highlight_range.
    xlabel : str
        X-axis label.
    ylabel : str
        Y-axis label.
    figsize : tuple
        Figure size.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    arr = np.asarray(values, dtype=float)
    counts, bin_edges, patches = ax.hist(
        arr, bins=bins, color=color, edgecolor="white", linewidth=0.5,
    )

    if highlight_range is not None:
        lo, hi = highlight_range
        for patch, left_edge, right_edge in zip(
            patches, bin_edges[:-1], bin_edges[1:]
        ):
            if left_edge >= lo and right_edge <= hi:
                patch.set_facecolor(highlight_color)

    ax.set_xlabel(xlabel, fontsize=FONTS["axis_label"])
    ax.set_ylabel(ylabel, fontsize=FONTS["axis_label"])

    plt.tight_layout()
    chart_title(fig, title)
    return fig


def strip_plot(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    title: str,
    *,
    jitter: float = 0.15,
    color: str = CATEGORICAL[0],
    xlabel: str = "",
    ylabel: str = "",
    marker_size: float = 30.0,
    figsize: tuple[float, float] = FIGSIZE["single"],
) -> plt.Figure:
    """Strip plot — individual data points arranged by category.

    Shows every observation as a dot with vertical jitter, revealing
    distribution shape, outliers, and density without binning.

    Parameters
    ----------
    df : DataFrame
        Source data.
    category_col : str
        Column containing category labels.
    value_col : str
        Column containing numeric values.
    title : str
        Insight-driven chart title.
    jitter : float
        Amount of random vertical jitter. Default 0.15.
    color : str
        Marker color.
    xlabel : str
        X-axis label.
    ylabel : str
        Y-axis label (typically the category axis).
    marker_size : float
        Marker area. Default 30.
    figsize : tuple
        Figure size.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    categories = df[category_col].values
    unique_cats = list(dict.fromkeys(categories))  # preserve order
    cat_to_pos = {cat: i for i, cat in enumerate(unique_cats)}

    positions = np.array([cat_to_pos[c] for c in categories], dtype=float)
    rng = np.random.default_rng(42)
    jittered = positions + rng.uniform(-jitter, jitter, size=len(positions))

    vals = df[value_col].values.astype(float)

    ax.scatter(vals, jittered, s=marker_size, color=color, **SCATTER_DEFAULTS)

    ax.set_yticks(range(len(unique_cats)))
    ax.set_yticklabels(unique_cats)
    ax.set_xlabel(xlabel or value_col, fontsize=FONTS["axis_label"])
    ax.invert_yaxis()
    ax.set_ylim(len(unique_cats) - 0.5, -0.5)

    plt.tight_layout()
    chart_title(fig, title)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# Magnitude
# ═══════════════════════════════════════════════════════════════════════════


def paired_bar(
    df: pd.DataFrame,
    category_col: str,
    val1_col: str,
    val2_col: str,
    title: str,
    *,
    label1: str | None = None,
    label2: str | None = None,
    color1: str = CATEGORICAL[0],
    color2: str = CATEGORICAL[1],
    ylabel: str = "",
    figsize: tuple[float, float] = FIGSIZE["single"],
    rotation: int = 0,
) -> plt.Figure:
    """Grouped (paired) bar chart comparing two values per category.

    Places two bars side by side for each category, making magnitude
    comparisons easy — e.g. budget vs actual, this year vs last year.

    Parameters
    ----------
    df : DataFrame
        Source data.
    category_col : str
        Column containing category labels (x-axis).
    val1_col : str
        Column for the first set of bars.
    val2_col : str
        Column for the second set of bars.
    title : str
        Insight-driven chart title.
    label1 : str, optional
        Legend label for val1_col. Defaults to val1_col.
    label2 : str, optional
        Legend label for val2_col. Defaults to val2_col.
    color1 : str
        Color for the first set of bars.
    color2 : str
        Color for the second set of bars.
    ylabel : str
        Y-axis label.
    figsize : tuple
        Figure size.
    rotation : int
        X-axis label rotation in degrees.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    x = np.arange(len(df[category_col]))
    width = 0.35

    vals1 = df[val1_col].values.astype(float)
    vals2 = df[val2_col].values.astype(float)

    ax.bar(
        x - width / 2, vals1, width,
        color=color1, label=label1 or val1_col, edgecolor="white",
    )
    ax.bar(
        x + width / 2, vals2, width,
        color=color2, label=label2 or val2_col, edgecolor="white",
    )

    ax.set_xticks(x)
    ha = "right" if rotation else "center"
    ax.set_xticklabels(df[category_col], rotation=rotation, ha=ha)
    ax.set_ylabel(ylabel, fontsize=FONTS["axis_label"])

    plt.tight_layout()
    legend_below(ax)
    chart_title(fig, title)
    return fig
