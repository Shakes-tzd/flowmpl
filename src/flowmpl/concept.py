"""Whiteboard explainer frame system — concept, section, comparison, cascade, data moment.

Provides reproducible matplotlib frames in the whiteboard explainer style.
AI-generated sketch illustrations (PNG) are composited with programmatic text,
arrows, and layout via matplotlib primitives.

Style is fully caller-controlled. Start from :func:`concept_style` and override
any key to match your palette and story::

    s = flowmpl.concept_style()
    s["card_color"] = "#2D6A4F"  # dark green card
    s["ink_color"]  = "#FFFFFF"  # white ink on dark card
    fig = flowmpl.concept_frame("My Title", "Body...", style=s)

All frame functions return ``plt.Figure``. Save with ``fig.savefig()``.
No text inside generated images — all labels and titles are added programmatically.
"""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.image import imread
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

from flowmpl.design import (
    CONCEPT_INK,
    CONCEPT_MUTED,
    CONCEPT_WHITE,
    CONCEPT_YELLOW,
)

# ───────────────────────────────────────────────────────────────────────────
# Public style factory
# ───────────────────────────────────────────────────────────────────────────


def concept_style() -> dict[str, object]:
    """Return the default style dict for all concept frame functions.

    All keys are optional overrides — pass a subset to change only what you
    need. Merge with ``|`` and pass as the ``style`` argument::

        s = concept_style()
        s["card_color"]  = "#003049"
        s["ink_color"]   = "#FFFFFF"
        s["accent_color"] = "#EE4B2B"
        fig = concept_frame("Title", "Body", style=s)

    Keys
    ----
    bg_color      Frame background fill.
    card_color    Card / panel fill (concept_frame default: yellow; section_intro default: white).
    ink_color     Text, borders, arrow strokes.
    accent_color  Accent highlights: cascade band, underline bars, badges.
    muted_color   Secondary / caption text.
    stat_fill     Fill colour inside hollow stat letterforms (data_moment_frame).
    left_bg       Left panel background (comparison_frame).
    right_bg      Right panel background (comparison_frame).
    title_size    Card title font size (pt).
    subtitle_size Subtitle / card secondary text font size (pt).
    body_size     Card body paragraph font size (pt).
    label_size    Surrounding icon label font size (pt).
    stat_size        Oversized stat letterform font size (pt).
    stat_stroke      Stroke width on hollow stat letterforms.
    rhetorical_size  Main text font size for rhetorical_frame (pt).
    card_lw          Card border line width.
    arrow_lw         Arrow / connector line width.
    """
    return {
        # Colours
        "bg_color":      CONCEPT_WHITE,
        "card_color":    CONCEPT_YELLOW,
        "ink_color":     CONCEPT_INK,
        "ghost_color":   CONCEPT_INK,   # section number outline — keep independent of ink_color
        "accent_color":  CONCEPT_YELLOW,
        "muted_color":   CONCEPT_MUTED,
        "stat_fill":     CONCEPT_WHITE,
        "left_bg":       CONCEPT_YELLOW,
        "right_bg":      "#E8E8E8",
        # Typography
        "title_size":    28,
        "subtitle_size": 16,
        "body_size":     14,
        "label_size":    12,
        "stat_size":        88,
        "stat_stroke":      12,
        "rhetorical_size":  40,
        # Geometry
        "card_lw":          1.5,
        "arrow_lw":         1.5,
    }


def _s(overrides: dict | None) -> dict:
    """Merge caller overrides onto the default style."""
    return concept_style() | (overrides or {})


# ───────────────────────────────────────────────────────────────────────────
# chart_scene_frame layout zones (axes-fraction bounding boxes)
# ───────────────────────────────────────────────────────────────────────────

CHART_SCENE_LAYOUT: dict[str, tuple[float, float, float, float]] = {
    # Full left panel that hosts the embedded chart
    "chart":        (0.02, 0.06, 0.54, 0.96),
    # Vertical icon strip to the left of the chart
    "left_strip":   (0.00, 0.06, 0.10, 0.96),
    # Horizontal banner above the chart area
    "top_bar":      (0.10, 0.88, 0.54, 0.98),
    # Horizontal banner below the chart area
    "bottom_bar":   (0.10, 0.02, 0.54, 0.12),
    # Transition zone between chart and callout card (de-risking icons)
    "derisk_zone":  (0.44, 0.15, 0.58, 0.88),
    # Space above the callout card (cloud, bank logos, etc.)
    "upper_right":  (0.56, 0.82, 0.98, 0.98),
    # Callout card region — text lives here; avoid placing icons here
    "callout":      (0.56, 0.20, 0.96, 0.80),
}
"""Named bounding-box zones for :func:`chart_scene_frame`.

Each value is ``(x0, y0, x1, y1)`` in axes-fraction coordinates (0–1).
Pass one of these tuples as the ``"bbox"`` key in a ``surrounding_icons``
entry to place an icon inside a semantically named region::

    surrounding_icons=[
        {"path": server_icon, "bbox": CHART_SCENE_LAYOUT["left_strip"]},
        {"path": cloud_icon,  "bbox": CHART_SCENE_LAYOUT["upper_right"]},
    ]

For precise placement within a zone, compute a sub-rectangle manually::

    lx0, ly0, lx1, ly1 = CHART_SCENE_LAYOUT["left_strip"]
    # Place server in the top third of the left strip
    {"path": server_icon, "bbox": (lx0, ly0 + 0.6*(ly1-ly0), lx1, ly1)}
"""


# ───────────────────────────────────────────────────────────────────────────
# Internal compositing primitives
# ───────────────────────────────────────────────────────────────────────────


def _place_asset(
    ax: plt.Axes,
    image: Path | np.ndarray,
    xy: tuple[float, float] | None = None,
    zoom: float = 0.3,
    alpha: float = 1.0,
    bbox: tuple[float, float, float, float] | None = None,
) -> None:
    """Position an image at normalised axes-fraction coordinates (0–1 range).

    ``image`` may be a file path (PNG/JPEG) **or** a numpy RGBA array as
    returned by :func:`flowmpl.load_icon`.

    Placement modes
    ---------------
    bbox (recommended for AI agents)
        Pass ``bbox=(x0, y0, x1, y1)`` in axes-fraction coordinates.  The
        image is PIL-resized to fill the rectangle exactly and placed with
        ``zoom=1.0``.  The placement is geometrically self-describing —
        no calibration renders required.

        Aspect-ratio note: for square icons on a 12 × 6.75 figure the
        display-neutral rectangle has ``x_span ≈ 0.60 × y_span`` (the figure
        is wider than tall).  Equal x and y spans produce a portrait-stretched
        icon.  Use the conversion formula ``x_span = y_span * fig_h / fig_w``
        to preserve a square appearance.

    zoom (legacy)
        Pass ``xy=(cx, cy)`` and ``zoom`` to scale the image relative to its
        natural pixel size.  Requires empirical calibration; prefer ``bbox``
        for new work.
    """
    if bbox is None and xy is None:
        raise ValueError("_place_asset: either xy or bbox must be provided")

    img = image if isinstance(image, np.ndarray) else imread(str(image))

    if bbox is not None:
        x0, y0, x1, y1 = bbox
        # Resize image to fill the bbox exactly.
        # OffsetImage at zoom=1.0 → 1 image pixel = 1 display pixel.
        # Target pixel size = bbox fraction × axes display pixel size.
        fig = ax.get_figure()
        fig_w_in, fig_h_in = fig.get_size_inches()
        dpi = fig.get_dpi()
        pos = ax.get_position()  # axes bounds as figure fraction
        target_w = max(1, int(round((x1 - x0) * pos.width  * fig_w_in * dpi)))
        target_h = max(1, int(round((y1 - y0) * pos.height * fig_h_in * dpi)))

        try:
            from PIL import Image as _PILImage  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "bbox placement requires Pillow.\n"
                "Install it with:  uv pip install 'flowmpl[icons]'"
            ) from exc

        if img.dtype in (np.float32, np.float64):
            img_u8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
        else:
            img_u8 = img.astype(np.uint8)
        pil_img = _PILImage.fromarray(img_u8)
        pil_img = pil_img.resize((target_w, target_h), _PILImage.LANCZOS)
        img = np.array(pil_img).astype(np.float32) / 255.0
        xy = ((x0 + x1) / 2, (y0 + y1) / 2)
        zoom = 1.0  # image already sized to target dimensions

    oi = OffsetImage(img, zoom=zoom, alpha=alpha)
    ab = AnnotationBbox(
        oi, xy,
        xycoords="axes fraction",
        frameon=False,
        box_alignment=(0.5, 0.5),
    )
    ax.add_artist(ab)


def _dashed_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    label: str = "",
    rad: float = 0.2,
    style: dict | None = None,
) -> None:
    """Draw a curved dashed arrow in axes-fraction coordinates."""
    st = _s(style)
    ax.annotate(
        "",
        xy=end, xycoords="axes fraction",
        xytext=start, textcoords="axes fraction",
        arrowprops=dict(
            arrowstyle="-|>",
            connectionstyle=f"arc3,rad={rad}",
            linestyle="dashed",
            color=st["ink_color"],
            lw=st["arrow_lw"],
        ),
    )
    if label:
        mid_x = (start[0] + end[0]) / 2 + rad * 0.1
        mid_y = (start[1] + end[1]) / 2 + abs(rad) * 0.15
        ax.text(
            mid_x, mid_y, label,
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=st["label_size"],
            color=st["muted_color"],
        )


def _card(
    ax: plt.Axes,
    center: tuple[float, float],
    width: float,
    height: float,
    title: str,
    body: str = "",
    style: dict | None = None,
) -> None:
    """Draw a rounded card with title and optional body text.

    Card fill, ink colour, and font sizes all come from ``style``.
    """
    st = _s(style)
    x0 = center[0] - width / 2
    y0 = center[1] - height / 2
    ax.add_patch(mpatches.FancyBboxPatch(
        (x0, y0), width, height,
        boxstyle="round,pad=0.02",
        facecolor=st["card_color"],
        edgecolor=st["ink_color"],
        linewidth=st["card_lw"],
        transform=ax.transAxes,
        zorder=3,
    ))
    title_y = center[1] + (height * 0.13 if body else 0)
    ax.text(
        center[0], title_y, title,
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=st["title_size"],
        fontweight="bold",
        color=st["ink_color"],
        zorder=4,
    )
    if body:
        ax.text(
            center[0], center[1] - height * 0.20, body,
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=st["body_size"],
            color=st["ink_color"],
            zorder=4, multialignment="center",
        )


def _ghost_number(
    ax: plt.Axes,
    number: str,
    xy: tuple[float, float],
    size: int = 220,
    style: dict | None = None,
) -> None:
    """Render a large outlined ghost number (section marker).

    Drawn as a stroked outline whose fill matches the background — caller
    controls both colours via the style dict.
    """
    st = _s(style)
    # Simple semi-transparent text — no path_effects needed.
    # ghost_color should contrast with bg_color; alpha controls how subtle the number appears.
    ax.text(
        xy[0], xy[1], number,
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=size, fontweight="bold",
        color=st["ghost_color"],
        alpha=0.30,
        zorder=1,
    )


# ───────────────────────────────────────────────────────────────────────────
# Public frame functions
# ───────────────────────────────────────────────────────────────────────────


def section_intro_frame(
    number: str,
    title: str,
    subtitle: str = "",
    icon_paths: list[Path] | None = None,
    style: dict | None = None,
    figsize: tuple[float, float] = (12, 6.75),
) -> plt.Figure:
    """Section intro card: large ghost number + centred white card + scattered icons.

    Default style: yellow background, white card.
    Override via ``style``::

        s = concept_style()
        s["bg_color"]   = "#003049"   # dark background
        s["card_color"] = "#F5C842"   # yellow card on dark bg
        s["ink_color"]  = "#FFFFFF"
        fig = section_intro_frame("1", "Title", style=s)

    Args:
        number:     Section number string displayed large as ghost outline.
        title:      Main title inside the card.
        subtitle:   Smaller text below the title inside the card.
        icon_paths: Up to 5 PNG asset paths scattered around the card.
        style:      Style overrides. See :func:`concept_style`.
        figsize:    Figure dimensions in inches.

    Returns:
        plt.Figure
    """
    # Section intro inverts the concept_frame defaults: yellow bg, white card.
    # ghost_color is pinned to CONCEPT_INK before user overrides so the section
    # number remains visible even when ink_color is reassigned to a dark bg colour.
    st = concept_style()
    st["bg_color"]    = CONCEPT_YELLOW
    st["card_color"]  = CONCEPT_WHITE
    st["ghost_color"] = CONCEPT_INK
    st |= (style or {})

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(st["bg_color"])
    ax.set_facecolor(st["bg_color"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    _ghost_number(ax, number, xy=(0.5, 0.5), size=280, style=st)
    _card(ax, center=(0.5, 0.5), width=0.58, height=0.48,
          title=title, body=subtitle, style=st)

    if icon_paths:
        positions = [
            (0.10, 0.78), (0.88, 0.78),
            (0.10, 0.22), (0.88, 0.22),
            (0.50, 0.92),
        ]
        for path, pos in zip(icon_paths[:5], positions):
            _place_asset(ax, path, pos, zoom=0.25, alpha=0.85)

    fig.tight_layout(pad=0)
    return fig


def concept_frame(
    title: str,
    body: str,
    surrounding_icons: dict[str, Path] | None = None,
    arrows: list[dict] | None = None,
    style: dict | None = None,
    figsize: tuple[float, float] = (12, 6.75),
) -> plt.Figure:
    """Concept definition frame: yellow card on white background + icons + arrows.

    Default style: white background, yellow card.
    Override via ``style``::

        s = concept_style()
        s["card_color"] = "#EE4B2B"   # red card
        s["bg_color"]   = "#F5F5F5"
        fig = concept_frame("Title", "Body", style=s)

    Args:
        title:             Bold title inside the card.
        body:              Body paragraph inside the card.
        surrounding_icons: Position key → PNG path. Valid keys:
                           "top_left", "top_right", "bottom_left",
                           "bottom_right", "left", "right".
        arrows:            List of dicts with keys:
                           "start": (x, y), "end": (x, y) in axes fraction,
                           "label": str (optional), "rad": float (optional).
        style:             Style overrides. See :func:`concept_style`.
        figsize:           Figure dimensions in inches.

    Returns:
        plt.Figure
    """
    st = _s(style)

    icon_positions: dict[str, tuple[float, float]] = {
        "top_left":     (0.12, 0.80),
        "top_right":    (0.88, 0.80),
        "bottom_left":  (0.12, 0.20),
        "bottom_right": (0.88, 0.20),
        "left":         (0.07, 0.50),
        "right":        (0.93, 0.50),
    }

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(st["bg_color"])
    ax.set_facecolor(st["bg_color"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    _card(ax, center=(0.5, 0.5), width=0.52, height=0.52,
          title=title, body=body, style=st)

    if surrounding_icons:
        for key, path in surrounding_icons.items():
            pos = icon_positions.get(key)
            if pos is not None:
                _place_asset(ax, path, pos, zoom=0.28)

    if arrows:
        for arrow in arrows:
            _dashed_arrow(
                ax,
                start=tuple(arrow["start"]),
                end=tuple(arrow["end"]),
                label=arrow.get("label", ""),
                rad=arrow.get("rad", 0.2),
                style=st,
            )

    fig.tight_layout(pad=0)
    return fig


def comparison_frame(
    left_title: str,
    left_image: Path,
    left_labels: list[str] = (),
    right_title: str = "",
    right_image: Path | None = None,
    right_labels: list[str] = (),
    divider: str = "zigzag",
    style: dict | None = None,
    figsize: tuple[float, float] = (12, 6.75),
) -> plt.Figure:
    """Split-screen comparison frame (Promise vs Reality, left vs right).

    Panel backgrounds come from ``style["left_bg"]`` and ``style["right_bg"]``.
    Panel titles are uppercased automatically (structural decision for this
    frame type). Override via ``style``::

        s = concept_style()
        s["left_bg"]  = "#2D6A4F"   # dark green left panel
        s["right_bg"] = "#D62828"   # red right panel
        s["ink_color"] = "#FFFFFF"
        fig = comparison_frame("Green Deal", left_img, style=s)

    Args:
        left_title:   Title over the left panel (auto-uppercased).
        left_image:   Scene PNG for the left panel.
        left_labels:  Up to 4 annotation strings for the left panel.
        right_title:  Title over the right panel (auto-uppercased).
        right_image:  Scene PNG for the right panel (None = empty).
        right_labels: Up to 4 annotation strings for the right panel.
        divider:      "zigzag" (sharp lightning bolt) or "line".
        style:        Style overrides. See :func:`concept_style`.
        figsize:      Figure dimensions in inches.

    Returns:
        plt.Figure
    """
    st = _s(style)

    fig = plt.figure(figsize=figsize)
    fig.patch.set_facecolor(st["left_bg"])

    ax_l = fig.add_axes([0.0, 0.0, 0.50, 1.0])
    ax_r = fig.add_axes([0.50, 0.0, 0.50, 1.0])

    for ax, bg in ((ax_l, st["left_bg"]), (ax_r, st["right_bg"])):
        ax.set_facecolor(bg)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

    ax_l.text(0.5, 0.88, left_title.upper(),
              transform=ax_l.transAxes, ha="center", va="top",
              fontsize=st["title_size"] - 6, fontweight="bold",
              color=st["ink_color"])
    if right_title:
        ax_r.text(0.5, 0.88, right_title.upper(),
                  transform=ax_r.transAxes, ha="center", va="top",
                  fontsize=st["title_size"] - 6, fontweight="bold",
                  color=st["ink_color"])

    _place_asset(ax_l, left_image, (0.5, 0.50), zoom=0.40)
    if right_image is not None:
        _place_asset(ax_r, right_image, (0.5, 0.50), zoom=0.40)

    label_ys = [0.30, 0.22, 0.14, 0.06]
    for label, y in zip(left_labels, label_ys):
        ax_l.text(0.5, y, label, transform=ax_l.transAxes,
                  ha="center", va="center", fontsize=st["body_size"],
                  color=st["ink_color"], multialignment="center")
    for label, y in zip(right_labels, label_ys):
        ax_r.text(0.5, y, label, transform=ax_r.transAxes,
                  ha="center", va="center", fontsize=st["body_size"],
                  color=st["ink_color"], multialignment="center")

    # Divider
    if divider == "zigzag":
        # Sharp lightning-bolt zigzag
        n_zags = 16
        ys = np.linspace(0, 1, n_zags + 1)
        xs = np.array([
            0.50 + (0.014 if i % 2 == 0 else -0.014)
            for i in range(n_zags + 1)
        ])
        fig.add_artist(plt.Line2D(
            xs, ys, transform=fig.transFigure,
            color=st["ink_color"], linewidth=2.5, zorder=10,
        ))
    else:
        fig.add_artist(plt.Line2D(
            [0.50, 0.50], [0.0, 1.0], transform=fig.transFigure,
            color=st["ink_color"], linewidth=2, zorder=10,
        ))

    return fig


def cascade_frame(
    steps: list[dict],
    style: dict | None = None,
    figsize: tuple[float, float] = (12, 6.75),
) -> plt.Figure:
    """Horizontal cascade / steps frame.

    Each step shows an optional icon above the step title and body text.
    A tinted accent band (``accent_color`` at low alpha) runs behind the steps.
    Override colours via ``style``::

        s = concept_style()
        s["accent_color"] = "#023E8A"   # navy band
        s["ink_color"]    = "#023E8A"
        fig = cascade_frame(steps, style=s)

    Args:
        steps: List of dicts with keys:
               - "number": displayed in the step title (int or str)
               - "title":  short step title
               - "body":   1–2 line description
               - "icon":   Path to sketch icon PNG (optional)
        style:   Style overrides. See :func:`concept_style`.
        figsize: Figure dimensions in inches.

    Returns:
        plt.Figure
    """
    n = len(steps)
    if n == 0:
        raise ValueError("cascade_frame requires at least one step")

    st = _s(style)

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(st["bg_color"])
    ax.set_facecolor(st["bg_color"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Tinted accent band behind the steps
    ax.add_patch(mpatches.FancyBboxPatch(
        (0.04, 0.08), 0.92, 0.78,
        boxstyle="round,pad=0.01",
        facecolor=st["accent_color"],
        edgecolor="none",
        alpha=0.18,
        transform=ax.transAxes,
        zorder=0,
    ))

    step_w  = 0.88 / n
    x_start = 0.06
    icon_y  = 0.68   # icon centre when present
    title_y = 0.48
    body_y  = 0.30
    arrow_y = 0.48   # arrows sit at title row, not in the empty icon zone

    for i, step in enumerate(steps):
        cx = x_start + i * step_w + step_w / 2

        # Icon
        icon_path = step.get("icon")
        if icon_path is not None:
            _place_asset(ax, icon_path, (cx, icon_y), zoom=0.22)

        # Step title: "1  Title"
        number = step.get("number", i + 1)
        ax.text(
            cx, title_y,
            f"{number}  {step.get('title', '')}",
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=st["body_size"] + 1,
            fontweight="bold",
            color=st["ink_color"],
        )

        # Body text
        ax.text(
            cx, body_y, step.get("body", ""),
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=st["label_size"],
            color=st["ink_color"],
            multialignment="center",
        )

        # Arrow to next step — sits at title row so it's always visible
        if i < n - 1:
            ax_x = cx + step_w * 0.45
            ax.annotate(
                "",
                xy=(ax_x + 0.015, arrow_y),
                xycoords="axes fraction",
                xytext=(ax_x - 0.015, arrow_y),
                textcoords="axes fraction",
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=st["ink_color"],
                    lw=st["arrow_lw"] + 0.5,
                ),
            )

    fig.tight_layout(pad=0.3)
    return fig


def data_moment_frame(
    stat: str,
    surrounding: dict[str, tuple[str, Path | None]] | None = None,
    style: dict | None = None,
    figsize: tuple[float, float] = (12, 6.75),
) -> plt.Figure:
    """Oversized hollow stat callout with surrounding icon + label pairs.

    The stat is rendered as hollow outlined letterforms: ``stat_fill`` colour
    inside, ``ink_color`` stroke outside. A dashed elliptical orbit connects
    the surrounding icons. Override via ``style``::

        s = concept_style()
        s["stat_fill"]    = "#F5C842"   # yellow fill inside letters
        s["ink_color"]    = "#1A1A1A"
        s["accent_color"] = "#F5C842"   # yellow underline bar
        fig = data_moment_frame("$6.7T", style=s)

    Args:
        stat:        Oversized stat string: "$6.7T", "$500M", "12%".
        surrounding: Position → (label, icon_path) mapping.
                     Valid keys: "top_left", "top_right", "bottom_left",
                                 "bottom_right", "left", "right".
                     Example: {"top_right": ("DECADES-LONG\\nPAYMENTS", lock_path)}
        style:       Style overrides. See :func:`concept_style`.
        figsize:     Figure dimensions in inches.

    Returns:
        plt.Figure
    """
    # Positions sit just outside the orbit so labels frame the stat clearly.
    surround_pos: dict[str, tuple[float, float]] = {
        "top_left":     (0.18, 0.80),
        "top_right":    (0.82, 0.80),
        "bottom_left":  (0.18, 0.22),
        "bottom_right": (0.82, 0.22),
        "left":         (0.08, 0.52),
        "right":        (0.92, 0.52),
    }

    st = _s(style)

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(st["bg_color"])
    ax.set_facecolor(st["bg_color"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Dashed orbit sized to pass through the surround_pos coordinates.
    # r_x / r_y are set to the diagonal distance to the corner positions,
    # not derived from figsize, so the orbit frames the labels regardless of
    # aspect ratio.
    r_x, r_y = 0.38, 0.28
    theta = np.linspace(0, 2 * np.pi, 300)
    ax.plot(
        0.50 + r_x * np.cos(theta),
        0.50 + r_y * np.sin(theta),
        ls="--", lw=1.2,
        color=st["ink_color"], alpha=0.30,
        transform=ax.transAxes, zorder=1,
    )

    # Hollow stat text: fill = stat_fill, heavy ink stroke = outlined letters
    ax.text(
        0.50, 0.55, stat,
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=st["stat_size"],
        fontweight="bold",
        color=st["stat_fill"],
        zorder=3,
        path_effects=[
            pe.Stroke(linewidth=st["stat_stroke"], foreground=st["ink_color"]),
            pe.Normal(),
        ],
    )

    # Accent underline bar
    ax.add_patch(mpatches.FancyBboxPatch(
        (0.25, 0.35), 0.50, 0.022,
        boxstyle="round,pad=0.004",
        facecolor=st["accent_color"],
        edgecolor="none",
        transform=ax.transAxes,
        zorder=2,
    ))

    # Surrounding icon + label pairs
    if surrounding:
        for key, (label, icon_path) in surrounding.items():
            pos = surround_pos.get(key)
            if pos is None:
                continue
            if icon_path is not None:
                _place_asset(ax, icon_path, (pos[0], pos[1] + 0.09), zoom=0.22)
            ax.text(
                pos[0], pos[1] - 0.05, label,
                transform=ax.transAxes,
                ha="center", va="center",
                fontsize=st["label_size"],
                fontweight="bold",
                color=st["ink_color"],
                multialignment="center",
            )

    fig.tight_layout(pad=0)
    return fig


def rhetorical_frame(
    text: str,
    ghost_symbol: str = "",
    corner_icons: dict[str, Path] | None = None,
    style: dict | None = None,
    figsize: tuple[float, float] = (12, 6.75),
) -> plt.Figure:
    """Full-bleed rhetorical statement frame — ghost background symbol + large centred text.

    No card. Text spans most of the frame width. An oversized ghost symbol
    sits behind the text as a subtle background motif. Override via ``style``::

        s = concept_style()
        s["bg_color"]        = "#1A1A1A"
        s["ink_color"]       = "#FFFFFF"
        s["ghost_color"]     = "#F5C842"
        s["rhetorical_size"] = 44
        fig = rhetorical_frame(
            "In a world built on\\nderisking, boldness wins.",
            ghost_symbol="$",
            style=s,
        )

    Args:
        text:         Main statement string. Use ``\\n`` for line breaks.
        ghost_symbol: Large background character (``"$"``, ``"→"``, ``"∞"``).
                      Empty string = no ghost.
        corner_icons: Position → PNG path for corner accent icons.
                      Valid keys: ``"top_left"``, ``"top_right"``,
                      ``"bottom_left"``, ``"bottom_right"``.
        style:        Style overrides. See :func:`concept_style`.
        figsize:      Figure dimensions in inches.

    Returns:
        plt.Figure
    """
    st = _s(style)

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(st["bg_color"])
    ax.set_facecolor(st["bg_color"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    if ghost_symbol:
        ax.text(
            0.5, 0.5, ghost_symbol,
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=320, fontweight="bold",
            color=st["ghost_color"],
            alpha=0.08,
            zorder=1,
        )

    ax.text(
        0.5, 0.5, text,
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=st["rhetorical_size"],
        fontweight="bold",
        color=st["ink_color"],
        multialignment="center",
        zorder=3,
    )

    if corner_icons:
        corner_pos: dict[str, tuple[float, float]] = {
            "top_left":     (0.08, 0.88),
            "top_right":    (0.92, 0.88),
            "bottom_left":  (0.08, 0.12),
            "bottom_right": (0.92, 0.12),
        }
        for key, path in corner_icons.items():
            pos = corner_pos.get(key)
            if pos is not None:
                _place_asset(ax, path, pos, zoom=0.22, alpha=0.75)

    fig.tight_layout(pad=0)
    return fig


def chart_scene_frame(
    chart_fig: plt.Figure,
    callout_title: str = "",
    callout_text: str = "",
    surrounding_icons: list[dict] | None = None,
    overlay_arrow: dict | None = None,
    chart_zoom: float = 0.38,
    style: dict | None = None,
    figsize: tuple[float, float] = (12, 6.75),
    debug_layout: bool = False,
) -> plt.Figure:
    """Embed a chart in a scene context: chart left, callout card right.

    The ``chart_fig`` is rasterised and placed on the left ~45 % of the frame.
    A callout card on the right provides a title and narrative body. Override
    via ``style``::

        s = concept_style()
        s["card_color"] = "#F5C842"
        s["ink_color"]  = "#1A1A1A"
        fig = chart_scene_frame(
            my_chart,
            callout_title="The Breakout Moment",
            callout_text="Wind and solar crossed\\n1,000 TWh in 2022.",
            style=s,
        )

    Args:
        chart_fig:         A ``plt.Figure`` to embed on the left side.
        callout_title:     Bold title for the right callout panel.
        callout_text:      Narrative body text for the right callout panel.
        surrounding_icons: List of dicts. Each dict must have ``"path": Path``
                           and either:

                           * ``"bbox": (x0, y0, x1, y1)`` — axes-fraction
                             rectangle **(recommended; AI-legible)**.  The icon
                             is PIL-resized to fill the rectangle exactly.  See
                             :data:`CHART_SCENE_LAYOUT` for predefined zones.
                           * ``"xy": (x, y)`` and optional ``"zoom": float``
                             (legacy; icon centred at xy with given scale).
        overlay_arrow:     Dict with ``"start"`` and ``"end"`` (axes-fraction
                           tuples). Optional ``"label": str``, ``"rad": float``.
        chart_zoom:        OffsetImage zoom for the embedded chart (default 0.38).
        style:             Style overrides. See :func:`concept_style`.
        figsize:           Figure dimensions in inches.
        debug_layout:      When ``True``, draw labeled red-dashed rectangles for
                           every :data:`CHART_SCENE_LAYOUT` zone and blue dash-dot
                           outlines for every icon placed via ``"bbox"``.  Pass
                           ``debug_layout=True`` during design; remove for final
                           output.

    Returns:
        plt.Figure
    """
    st = _s(style)

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(st["bg_color"])
    ax.set_facecolor(st["bg_color"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Rasterise the caller's figure and embed on the left
    buf = io.BytesIO()
    chart_fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    chart_arr = imread(buf)
    oi = OffsetImage(chart_arr, zoom=chart_zoom)
    ab = AnnotationBbox(
        oi, (0.26, 0.52),
        xycoords="axes fraction",
        frameon=False,
        box_alignment=(0.5, 0.5),
    )
    ax.add_artist(ab)

    if surrounding_icons:
        for icon in surrounding_icons:
            _place_asset(
                ax,
                icon["path"],
                xy=tuple(icon["xy"]) if "xy" in icon else None,
                zoom=icon.get("zoom", 0.20),
                bbox=tuple(icon["bbox"]) if "bbox" in icon else None,
            )

    if overlay_arrow:
        _dashed_arrow(
            ax,
            start=tuple(overlay_arrow["start"]),
            end=tuple(overlay_arrow["end"]),
            label=overlay_arrow.get("label", ""),
            rad=overlay_arrow.get("rad", -0.2),
            style=st,
        )

    if callout_title or callout_text:
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.56, 0.20), 0.40, 0.60,
            boxstyle="round,pad=0.02",
            facecolor=st["card_color"],
            edgecolor=st["ink_color"],
            linewidth=st["card_lw"],
            transform=ax.transAxes,
            zorder=3,
        ))
        if callout_title:
            ax.text(
                0.76, 0.68, callout_title,
                transform=ax.transAxes,
                ha="center", va="center",
                fontsize=st["subtitle_size"] + 2,
                fontweight="bold",
                color=st["ink_color"],
                multialignment="center",
                zorder=4,
            )
        if callout_text:
            ax.text(
                0.76, 0.44, callout_text,
                transform=ax.transAxes,
                ha="center", va="center",
                fontsize=st["body_size"],
                color=st["ink_color"],
                multialignment="center",
                zorder=4,
            )

    if debug_layout:
        # Named zone outlines (red dashed)
        for zone_name, (zx0, zy0, zx1, zy1) in CHART_SCENE_LAYOUT.items():
            ax.add_patch(mpatches.FancyBboxPatch(
                (zx0, zy0), zx1 - zx0, zy1 - zy0,
                boxstyle="square,pad=0",
                facecolor="none",
                edgecolor="#CC0000",
                linewidth=0.8,
                linestyle="--",
                transform=ax.transAxes,
                zorder=14,
            ))
            ax.text(
                zx0 + 0.005, zy1 - 0.01, zone_name,
                transform=ax.transAxes,
                ha="left", va="top",
                fontsize=6.5, color="#CC0000",
                alpha=0.85, zorder=15,
            )
        # Icon bbox outlines (blue dash-dot)
        if surrounding_icons:
            for i, icon in enumerate(surrounding_icons):
                if "bbox" in icon:
                    bx0, by0, bx1, by1 = icon["bbox"]
                    ax.add_patch(mpatches.FancyBboxPatch(
                        (bx0, by0), bx1 - bx0, by1 - by0,
                        boxstyle="square,pad=0",
                        facecolor="none",
                        edgecolor="#0055CC",
                        linewidth=1.2,
                        linestyle="-.",
                        transform=ax.transAxes,
                        zorder=14,
                    ))
                    ax.text(
                        (bx0 + bx1) / 2, (by0 + by1) / 2, str(i),
                        transform=ax.transAxes,
                        ha="center", va="center",
                        fontsize=7, color="#0055CC",
                        zorder=15,
                    )

    fig.tight_layout(pad=0)
    return fig
