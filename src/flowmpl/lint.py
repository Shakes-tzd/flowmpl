"""SWD chart audit — check matplotlib figures against Storytelling with Data principles."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import matplotlib.figure
    import matplotlib.axes


# ───────────────────────────────────────────────────────────────────────────
# Result types
# ───────────────────────────────────────────────────────────────────────────


class Severity(Enum):
    """Severity level for a lint result."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class LintResult:
    """Single check outcome with severity, rule name, and human-readable message."""

    severity: Severity
    rule: str
    message: str


# ───────────────────────────────────────────────────────────────────────────
# Gray / muted detection helpers
# ───────────────────────────────────────────────────────────────────────────

# Colors considered "muted" / gray context tones — includes common grays,
# light-grays, and silver-ish tones expressed as hex or named colors.
_GRAY_NAMES = frozenset({
    "gray", "grey", "silver", "lightgray", "lightgrey",
    "darkgray", "darkgrey", "dimgray", "dimgrey", "gainsboro",
    "whitesmoke",
})

_GRAY_HEX_RE = re.compile(
    r"^#([0-9a-fA-F])\1\1\1\1\1$"  # #RRGGBB where R==G==B
    r"|^#([0-9a-fA-F])\2\2$",       # #RGB shorthand
)


def _is_gray(color: object) -> bool:
    """Return True if *color* looks like a gray / muted tone."""
    if not isinstance(color, str):
        return False
    c = color.strip().lower()
    if c in _GRAY_NAMES:
        return True
    if _GRAY_HEX_RE.match(c):
        return True
    # Catch common muted hex values (#888888, #cccccc, etc.) that the strict
    # regex already handles. Also catch near-grays like #889988 by checking
    # if all RGB channels are within 0x20 of each other.
    if c.startswith("#") and len(c) == 7:
        try:
            r = int(c[1:3], 16)
            g = int(c[3:5], 16)
            b = int(c[5:7], 16)
            spread = max(r, g, b) - min(r, g, b)
            return spread <= 0x20
        except ValueError:
            pass
    return False


# ───────────────────────────────────────────────────────────────────────────
# Title verb heuristic
# ───────────────────────────────────────────────────────────────────────────

# Small word-list of common "insight verbs" that distinguish a real title
# from a bare axis-label-style title like "Revenue" or "Q3 Sales".
_INSIGHT_VERBS = frozenset({
    "is", "are", "was", "were", "has", "have", "had",
    "do", "does", "did",
    "rise", "rises", "rose", "risen",
    "fall", "falls", "fell", "fallen",
    "grow", "grows", "grew", "grown",
    "drop", "drops", "dropped",
    "increase", "increases", "increased",
    "decrease", "decreases", "decreased",
    "decline", "declines", "declined",
    "exceed", "exceeds", "exceeded",
    "outpace", "outpaces", "outpaced",
    "lead", "leads", "led",
    "lag", "lags", "lagged",
    "remain", "remains", "remained",
    "shift", "shifts", "shifted",
    "surge", "surges", "surged",
    "spike", "spikes", "spiked",
    "climb", "climbs", "climbed",
    "plummet", "plummets", "plummeted",
    "double", "doubles", "doubled",
    "triple", "triples", "tripled",
    "shrink", "shrinks", "shrank", "shrunk",
    "flatten", "flattens", "flattened",
    "recover", "recovers", "recovered",
    "dominate", "dominates", "dominated",
    "show", "shows", "showed", "shown",
    "reveal", "reveals", "revealed",
    "suggest", "suggests", "suggested",
    "indicate", "indicates", "indicated",
    "account", "accounts", "accounted",
    "represent", "represents", "represented",
    "continue", "continues", "continued",
    "accelerate", "accelerates", "accelerated",
    "slow", "slows", "slowed",
    "peak", "peaks", "peaked",
    "hit", "hits",
    "reach", "reaches", "reached",
    "need", "needs", "needed",
    "should", "could", "would", "will", "may", "might", "must",
    "drive", "drives", "drove", "driven",
    "cause", "causes", "caused",
    "beat", "beats",
    "miss", "misses", "missed",
    "stall", "stalls", "stalled",
    "gain", "gains", "gained",
    "lose", "loses", "lost",
    "outperform", "outperforms", "outperformed",
    "underperform", "underperforms", "underperformed",
})


def _title_has_verb(title: str) -> bool:
    """Return True if *title* contains at least one insight verb."""
    words = {w.lower().strip(".,;:!?\"'()") for w in title.split()}
    return bool(words & _INSIGHT_VERBS)


# ───────────────────────────────────────────────────────────────────────────
# Individual check functions
# ───────────────────────────────────────────────────────────────────────────


def _check_spines(ax: matplotlib.axes.Axes) -> LintResult:
    """Clutter: prefer only left + bottom spines visible."""
    right_visible = ax.spines["right"].get_visible()
    top_visible = ax.spines["top"].get_visible()
    if right_visible or top_visible:
        sides = [s for s, v in [("right", right_visible), ("top", top_visible)] if v]
        return LintResult(
            Severity.WARNING,
            "spines",
            f"Visible {'+'.join(sides)} spine(s) add clutter — remove with "
            f"ax.spines['{sides[0]}'].set_visible(False).",
        )
    return LintResult(Severity.PASS, "spines", "Only left+bottom spines visible.")


def _check_grid(ax: matplotlib.axes.Axes) -> LintResult:
    """Clutter: grids are usually unnecessary chart junk."""
    # Matplotlib stores grid visibility on the major tick objects.
    x_grid = any(
        line.get_visible() for line in ax.xaxis.get_gridlines()
    )
    y_grid = any(
        line.get_visible() for line in ax.yaxis.get_gridlines()
    )
    if x_grid or y_grid:
        return LintResult(
            Severity.WARNING,
            "grid",
            "Grid lines visible — consider removing to reduce clutter "
            "(ax.grid(False)).",
        )
    return LintResult(Severity.PASS, "grid", "No grid lines — clean canvas.")


def _check_legend_frame(ax: matplotlib.axes.Axes) -> LintResult:
    """Clutter: legend box borders are unnecessary."""
    legend = ax.get_legend()
    if legend is None:
        return LintResult(Severity.PASS, "legend_frame", "No legend present.")
    if legend.get_frame_on():
        return LintResult(
            Severity.WARNING,
            "legend_frame",
            "Legend has a border frame — remove with legend.set_frame_on(False) "
            "or pass frameon=False.",
        )
    return LintResult(Severity.PASS, "legend_frame", "Legend frame is off.")


def _collect_data_colors(ax: matplotlib.axes.Axes) -> set[str]:
    """Extract distinct face/edge colors used by data-bearing artists on *ax*."""
    import matplotlib.colors as mcolors

    colors: set[str] = set()

    def _normalize(c: object) -> str | None:
        """Convert a color-like value to a hex string, or None."""
        try:
            rgba = mcolors.to_rgba(c)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            return None
        # Skip fully transparent
        if rgba[3] == 0.0:
            return None
        return mcolors.to_hex(rgba[:3])

    # Collect non-data artists to skip: the axes background patch and
    # any legend patches / legend-container artists.
    skip_artists = {ax.patch}  # axes background
    legend = ax.get_legend()
    if legend is not None:
        skip_artists.update(legend.get_children())
        skip_artists.update(legend.get_patches())
        skip_artists.update(legend.get_lines())
        skip_artists.add(legend.get_frame())

    for artist in ax.get_children():
        if artist in skip_artists:
            continue

        # Lines (plot, axhline)
        from matplotlib.lines import Line2D

        if isinstance(artist, Line2D):
            # Skip grid lines and axis lines
            if artist.get_linestyle() == "None" and not artist.get_marker():
                continue
            h = _normalize(artist.get_color())
            if h:
                colors.add(h)
            continue

        # Bars, filled areas — collections
        from matplotlib.collections import PatchCollection, PolyCollection

        if isinstance(artist, (PatchCollection, PolyCollection)):
            for fc in artist.get_facecolors():
                h = _normalize(fc)
                if h:
                    colors.add(h)
            continue

        # Individual patches (bar, Rectangle, Wedge)
        from matplotlib.patches import Patch

        if isinstance(artist, Patch):
            # Skip spines and axes frame
            if type(artist).__name__ == "Spine":
                continue
            h = _normalize(artist.get_facecolor())
            if h:
                colors.add(h)

    return colors


def _check_color_count(ax: matplotlib.axes.Axes) -> LintResult:
    """Color: too many distinct data colors overwhelm the reader."""
    colors = _collect_data_colors(ax)
    n = len(colors)
    if n <= 4:
        return LintResult(
            Severity.PASS,
            "color_count",
            f"{n} distinct data color(s) — within SWD guideline (<=4).",
        )
    if n <= 6:
        return LintResult(
            Severity.WARNING,
            "color_count",
            f"{n} distinct data colors — consider reducing to <=4 for clarity.",
        )
    return LintResult(
        Severity.FAIL,
        "color_count",
        f"{n} distinct data colors — too many; simplify the color palette.",
    )


def _check_context_gray(ax: matplotlib.axes.Axes) -> LintResult:
    """Color: at least one element should use gray to push context to background."""
    colors = _collect_data_colors(ax)
    if not colors:
        return LintResult(
            Severity.PASS,
            "context_gray",
            "No data colors detected.",
        )
    has_gray = any(_is_gray(c) for c in colors)
    if has_gray:
        return LintResult(
            Severity.PASS,
            "context_gray",
            "Gray/muted color found — good use of preattentive contrast.",
        )
    return LintResult(
        Severity.WARNING,
        "context_gray",
        "All data colors are vivid — consider graying out context elements "
        "to make the focal point stand out.",
    )


def _check_has_title(fig: matplotlib.figure.Figure) -> LintResult:
    """Title: every chart needs a title telling the reader what to look at."""
    # Check suptitle
    suptitle = fig._suptitle  # noqa: SLF001
    if suptitle is not None and suptitle.get_text().strip():
        return LintResult(Severity.PASS, "has_title", "Figure has a suptitle.")

    # Check per-axes titles
    for ax in fig.get_axes():
        if ax.get_title().strip():
            return LintResult(Severity.PASS, "has_title", "Axes title found.")

    return LintResult(
        Severity.FAIL,
        "has_title",
        "No title found — add fig.suptitle() or ax.set_title() to orient "
        "the reader.",
    )


def _get_title_text(fig: matplotlib.figure.Figure) -> str | None:
    """Return the first non-empty title string found on *fig*, or None."""
    suptitle = fig._suptitle  # noqa: SLF001
    if suptitle is not None and suptitle.get_text().strip():
        return suptitle.get_text().strip()
    for ax in fig.get_axes():
        t = ax.get_title().strip()
        if t:
            return t
    return None


def _check_title_insight(fig: matplotlib.figure.Figure) -> LintResult:
    """Title: an insightful title contains a verb conveying the takeaway."""
    title = _get_title_text(fig)
    if title is None:
        # has_title will already flag this; don't double-penalize.
        return LintResult(
            Severity.WARNING,
            "title_insight",
            "No title to evaluate — add one first.",
        )
    if _title_has_verb(title):
        return LintResult(
            Severity.PASS,
            "title_insight",
            f"Title contains an insight verb — \"{title}\".",
        )
    return LintResult(
        Severity.WARNING,
        "title_insight",
        f"Title \"{title}\" reads like a label — add a verb to convey "
        f"the takeaway (e.g. 'Revenue grew 15% in Q3').",
    )


def _check_has_source(fig: matplotlib.figure.Figure) -> LintResult:
    """Annotation: a source note near the bottom builds credibility."""
    for txt in fig.texts:
        # Figure-level text positions are in figure coordinates (0–1).
        _, y = txt.get_position()
        if y < 0.05:
            return LintResult(
                Severity.PASS,
                "has_source",
                "Source annotation found near bottom of figure.",
            )
    # Also check axes-level text objects positioned via figure transforms
    for ax in fig.get_axes():
        for txt in ax.texts:
            # Axes text positions are in data coords by default, but some
            # users place them via transform=fig.transFigure.
            try:
                display_coords = txt.get_transform().transform(txt.get_position())
                fig_coords = fig.transFigure.inverted().transform(display_coords)
                if fig_coords[1] < 0.05:
                    return LintResult(
                        Severity.PASS,
                        "has_source",
                        "Source annotation found near bottom of figure.",
                    )
            except Exception:  # noqa: BLE001
                continue
    return LintResult(
        Severity.WARNING,
        "has_source",
        "No source note found near the bottom — add one with "
        "fig.text(0.5, 0.01, 'Source: …').",
    )


def _check_legend_placement(ax: matplotlib.axes.Axes) -> LintResult:
    """Layout: legend should sit below the axes, not over data."""
    legend = ax.get_legend()
    if legend is None:
        return LintResult(
            Severity.PASS,
            "legend_placement",
            "No legend present.",
        )
    # Try to determine if the legend is below the axes.
    bbox = legend.get_window_extent()
    ax_bbox = ax.get_window_extent()
    # If the legend's top edge is below the axes' bottom edge → below.
    # If the legend overlaps the axes data area → warning.
    if bbox.y1 <= ax_bbox.y0:
        return LintResult(
            Severity.PASS,
            "legend_placement",
            "Legend is positioned below the axes.",
        )
    # Check overlap with axes area
    if bbox.y0 >= ax_bbox.y0 and bbox.y1 <= ax_bbox.y1:
        return LintResult(
            Severity.WARNING,
            "legend_placement",
            "Legend overlaps the data area — consider placing it below "
            "the axes with legend_below() or loc='upper center', "
            "bbox_to_anchor=(0.5, -0.05).",
        )
    return LintResult(
        Severity.PASS,
        "legend_placement",
        "Legend placement appears acceptable.",
    )


def _check_dual_axes(fig: matplotlib.figure.Figure) -> LintResult:
    """Layout: dual y-axes (twinx) mislead readers with different scales."""
    axes = fig.get_axes()
    if len(axes) < 2:
        return LintResult(Severity.PASS, "dual_axes", "Single axes — no dual-axis risk.")

    # twinx() creates a second Axes that shares the x-axis with the first
    # AND occupies the same position (overlapping bounding boxes).
    # Distinguish from sharex=True subplots by checking spatial overlap:
    # twinx axes share the same position, while sharex panels do not.
    for i, ax_a in enumerate(axes):
        for ax_b in axes[i + 1 :]:
            try:
                shared = ax_a.get_shared_x_axes().joined(ax_a, ax_b)
            except AttributeError:
                shared = False
            if not shared:
                continue
            # Check if axes overlap spatially (same position = twinx).
            # Use the axes position in figure coordinates.
            pos_a = ax_a.get_position()
            pos_b = ax_b.get_position()
            overlap_x = pos_a.x0 < pos_b.x1 and pos_b.x0 < pos_a.x1
            overlap_y = pos_a.y0 < pos_b.y1 and pos_b.y0 < pos_a.y1
            # Substantial overlap → twinx pattern (not just adjacent panels)
            if overlap_x and overlap_y:
                overlap_area = (
                    (min(pos_a.x1, pos_b.x1) - max(pos_a.x0, pos_b.x0))
                    * (min(pos_a.y1, pos_b.y1) - max(pos_a.y0, pos_b.y0))
                )
                smaller_area = min(pos_a.width * pos_a.height, pos_b.width * pos_b.height)
                if smaller_area > 0 and overlap_area / smaller_area > 0.5:
                    return LintResult(
                        Severity.FAIL,
                        "dual_axes",
                        "Dual y-axes detected (twinx) — readers struggle to compare "
                        "values across two different scales. Use separate panels instead.",
                    )

    return LintResult(
        Severity.PASS,
        "dual_axes",
        "No dual-axis pattern detected.",
    )


def _check_pie_overload(ax: matplotlib.axes.Axes) -> LintResult:
    """Anti-pattern: pie charts with many wedges are hard to read."""
    from matplotlib.patches import Wedge

    wedges = [
        child for child in ax.get_children() if isinstance(child, Wedge)
    ]
    if not wedges:
        return LintResult(
            Severity.PASS,
            "pie_overload",
            "Not a pie chart.",
        )
    n = len(wedges)
    if n <= 3:
        return LintResult(
            Severity.PASS,
            "pie_overload",
            f"Pie chart with {n} wedge(s) — acceptable.",
        )
    return LintResult(
        Severity.FAIL,
        "pie_overload",
        f"Pie chart with {n} wedges — too many to compare angles accurately. "
        f"Use a horizontal bar chart instead.",
    )


def _check_no_3d(ax: matplotlib.axes.Axes) -> LintResult:
    """Anti-pattern: 3D projections distort data perception."""
    if ax.name == "3d":
        return LintResult(
            Severity.FAIL,
            "no_3d",
            "3D projection detected — 3D charts distort perception of values. "
            "Use a 2D alternative.",
        )
    return LintResult(Severity.PASS, "no_3d", "2D projection — no distortion risk.")


# ───────────────────────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────────────────────


def lint(fig: matplotlib.figure.Figure) -> list[LintResult]:
    """Run all SWD checks against a matplotlib *fig* and return results.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to audit. The figure must be rendered (call
        ``fig.canvas.draw()`` or ``plt.tight_layout()`` first if legend
        bounding boxes are needed).

    Returns
    -------
    list[LintResult]
        One result per check, ordered by category.

    Example
    -------
    ::

        import matplotlib.pyplot as plt
        from flowmpl.lint import lint, lint_summary

        fig, ax = plt.subplots()
        ax.bar(["A", "B", "C"], [3, 7, 5])
        ax.set_title("Sales grew 12% in Q3")

        results = lint(fig)
        print(lint_summary(results))
    """
    results: list[LintResult] = []

    axes = fig.get_axes()

    # Figure-level checks (run regardless of axes count)
    results.append(_check_has_title(fig))
    results.append(_check_title_insight(fig))
    results.append(_check_has_source(fig))
    results.append(_check_dual_axes(fig))

    if not axes:
        # Nothing more to check on an empty figure.
        return results

    # Per-axes checks — run on every axes and keep worst severity per rule.
    per_ax_checks = [
        _check_spines,
        _check_grid,
        _check_legend_frame,
        _check_color_count,
        _check_context_gray,
        _check_legend_placement,
        _check_pie_overload,
        _check_no_3d,
    ]

    # Aggregate: for each rule, keep the result with the worst severity.
    _severity_rank = {Severity.PASS: 0, Severity.WARNING: 1, Severity.FAIL: 2}
    worst: dict[str, LintResult] = {}

    for ax in axes:
        for check_fn in per_ax_checks:
            result = check_fn(ax)
            prev = worst.get(result.rule)
            if prev is None or _severity_rank[result.severity] > _severity_rank[prev.severity]:
                worst[result.rule] = result

    # Maintain stable ordering matching the check list.
    rule_order = [fn.__name__.removeprefix("_check_") for fn in per_ax_checks]
    for rule in rule_order:
        if rule in worst:
            results.append(worst[rule])

    return results


def lint_summary(results: list[LintResult]) -> str:
    """Format *results* into a human-readable report string.

    Parameters
    ----------
    results : list[LintResult]
        Output from :func:`lint`.

    Returns
    -------
    str
        Multi-line report with pass/warn/fail counts and per-rule details.
    """
    if not results:
        return "No lint results."

    _ICONS = {
        Severity.PASS: "PASS",
        Severity.WARNING: "WARN",
        Severity.FAIL: "FAIL",
    }

    lines: list[str] = []
    lines.append("SWD Chart Audit")
    lines.append("=" * 50)

    passes = sum(1 for r in results if r.severity is Severity.PASS)
    warnings = sum(1 for r in results if r.severity is Severity.WARNING)
    fails = sum(1 for r in results if r.severity is Severity.FAIL)

    lines.append(f"  {passes} passed | {warnings} warning(s) | {fails} failure(s)")
    lines.append("-" * 50)

    for r in results:
        label = _ICONS[r.severity]
        lines.append(f"  [{label}] {r.rule}: {r.message}")

    lines.append("=" * 50)

    if fails:
        lines.append("Result: FAIL — fix failures before presenting.")
    elif warnings:
        lines.append("Result: REVIEW — address warnings for a cleaner chart.")
    else:
        lines.append("Result: PASS — chart follows SWD principles.")

    return "\n".join(lines)
