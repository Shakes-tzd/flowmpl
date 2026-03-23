"""Publication export — one-call figure output for journals, web, and presentations.

Pre-defined targets handle DPI, size limits, color-mode, and format for common
venues (PRS, JPRAS, Annals, Nature) plus web/presentation/poster contexts.

Optional dependency: Pillow>=9.0 (required only for CMYK raster conversion).
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import matplotlib.pyplot as plt


@dataclass(frozen=True)
class ExportTarget:
    """Specification for a publication or display target.

    Parameters
    ----------
    name : str
        Human-readable target name (e.g. "PRS", "Web").
    dpi : int
        Output resolution in dots per inch.
    max_width_inches : float
        Maximum figure width allowed by the target.
    max_height_inches : float
        Maximum figure height allowed by the target.
    default_format : str
        File format when none is specified (e.g. "tiff", "png", "pdf").
    color_mode : str
        Color space — ``"rgb"`` or ``"cmyk"``.
    """

    name: str
    dpi: int
    max_width_inches: float
    max_height_inches: float
    default_format: str
    color_mode: str  # "rgb" or "cmyk"


# ---------------------------------------------------------------------------
# Pre-defined targets
# ---------------------------------------------------------------------------

TARGETS: dict[str, ExportTarget] = {
    "prs": ExportTarget("PRS", 300, 7.0, 9.5, "tiff", "cmyk"),
    "jpras": ExportTarget("JPRAS", 300, 6.7, 9.4, "tiff", "cmyk"),
    "annals": ExportTarget("Annals", 300, 7.0, 9.0, "tiff", "cmyk"),
    "nature": ExportTarget("Nature", 300, 7.1, 9.5, "pdf", "cmyk"),
    "web": ExportTarget("Web", 150, 12.0, 8.0, "png", "rgb"),
    "presentation": ExportTarget("Slides", 200, 13.33, 7.5, "png", "rgb"),
    "poster": ExportTarget("Poster", 300, 48.0, 36.0, "pdf", "cmyk"),
}


# ---------------------------------------------------------------------------
# Raster formats eligible for CMYK conversion via PIL
# ---------------------------------------------------------------------------

_RASTER_FORMATS = {"tiff", "tif", "png", "jpg", "jpeg", "bmp"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_target(target: str | ExportTarget) -> ExportTarget:
    """Look up a target by key or pass through an ExportTarget instance.

    Parameters
    ----------
    target : str or ExportTarget
        If a string, must be a key in ``TARGETS`` (case-insensitive).

    Returns
    -------
    ExportTarget

    Raises
    ------
    KeyError
        If the string key is not found in ``TARGETS``.
    """
    if isinstance(target, ExportTarget):
        return target
    key = target.lower()
    if key not in TARGETS:
        available = ", ".join(sorted(TARGETS))
        raise KeyError(
            f"Unknown export target {target!r}. Available: {available}. "
            "Pass an ExportTarget instance for custom targets."
        )
    return TARGETS[key]


def _scale_to_fit(
    fig: plt.Figure,
    max_width: float,
    max_height: float,
) -> None:
    """Proportionally shrink the figure if it exceeds max dimensions.

    The figure is only scaled *down*, never up.  Aspect ratio is preserved.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to resize.
    max_width : float
        Maximum allowed width in inches.
    max_height : float
        Maximum allowed height in inches.
    """
    w, h = fig.get_size_inches()
    scale = min(max_width / w, max_height / h, 1.0)
    if scale < 1.0:
        fig.set_size_inches(w * scale, h * scale)


def _convert_to_cmyk(src_path: Path, dst_path: Path) -> None:
    """Convert an RGB raster image to CMYK using Pillow.

    Parameters
    ----------
    src_path : Path
        Source RGB image file.
    dst_path : Path
        Destination path for the CMYK image.

    Raises
    ------
    ImportError
        If Pillow is not installed.
    """
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "Pillow is required for CMYK conversion. "
            "Install it with:  pip install 'Pillow>=9.0'  "
            "or:  pip install 'flowmpl[icons]'"
        ) from exc

    with Image.open(src_path) as img:
        cmyk_img = img.convert("CMYK")
        cmyk_img.save(dst_path)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def export(
    fig: plt.Figure,
    path: str | Path,
    *,
    target: str | ExportTarget = "web",
    dpi: int | None = None,
    format: str | None = None,  # noqa: A002 — shadows builtin intentionally
    max_width: float | None = None,
    max_height: float | None = None,
    cmyk: bool | None = None,
    tight: bool = True,
    transparent: bool = False,
    pad_inches: float = 0.1,
) -> Path:
    """Export a matplotlib figure to disk with publication-ready settings.

    Resolves a target specification, applies optional parameter overrides,
    scales the figure to fit within size limits, and saves to the requested
    format.  For raster targets that require CMYK, an intermediate RGB file
    is saved first and then converted via Pillow.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to export.
    path : str or Path
        Output file path.  If the path has no extension the target's
        ``default_format`` is appended automatically.  Parent directories
        are created if they do not exist.
    target : str or ExportTarget, default ``"web"``
        Publication target.  Pass a key from ``TARGETS`` (e.g. ``"prs"``,
        ``"nature"``) or an ``ExportTarget`` instance for custom targets.
    dpi : int, optional
        Override the target's DPI.
    format : str, optional
        Override the target's default file format (e.g. ``"png"``).
    max_width : float, optional
        Override the target's maximum width in inches.
    max_height : float, optional
        Override the target's maximum height in inches.
    cmyk : bool, optional
        Force or suppress CMYK conversion.  When ``None`` (default), the
        target's ``color_mode`` is used.
    tight : bool, default True
        Use ``bbox_inches="tight"`` when saving.
    transparent : bool, default False
        Save with a transparent background.
    pad_inches : float, default 0.1
        Padding when ``tight=True``.

    Returns
    -------
    pathlib.Path
        Resolved path of the saved file.

    Raises
    ------
    KeyError
        If *target* is a string not found in ``TARGETS``.
    ImportError
        If CMYK conversion is requested but Pillow is not installed.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> ax.plot([1, 2, 3])
    >>> path = export(fig, "figures/my_chart", target="prs")
    >>> path.suffix
    '.tiff'
    """
    spec = _resolve_target(target)

    # --- Resolve overrides --------------------------------------------------
    resolved_dpi = dpi if dpi is not None else spec.dpi
    resolved_fmt = (format or "").lower() if format else spec.default_format
    resolved_max_w = max_width if max_width is not None else spec.max_width_inches
    resolved_max_h = max_height if max_height is not None else spec.max_height_inches
    use_cmyk = cmyk if cmyk is not None else (spec.color_mode == "cmyk")

    # --- Resolve output path ------------------------------------------------
    out = Path(path)
    if not out.suffix:
        out = out.with_suffix(f".{resolved_fmt}")
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    # --- Scale figure to fit target limits ----------------------------------
    _scale_to_fit(fig, resolved_max_w, resolved_max_h)

    # --- Build savefig kwargs -----------------------------------------------
    save_kwargs: dict = {
        "dpi": resolved_dpi,
        "format": resolved_fmt,
        "transparent": transparent,
    }
    if tight:
        save_kwargs["bbox_inches"] = "tight"
        save_kwargs["pad_inches"] = pad_inches

    # --- Save (with optional CMYK conversion) -------------------------------
    needs_cmyk = use_cmyk and resolved_fmt in _RASTER_FORMATS

    if needs_cmyk:
        # Save RGB to a temp file, then convert to CMYK at the final path.
        with tempfile.NamedTemporaryFile(
            suffix=f".{resolved_fmt}", delete=False
        ) as tmp:
            tmp_path = Path(tmp.name)
        try:
            fig.savefig(str(tmp_path), **save_kwargs)
            _convert_to_cmyk(tmp_path, out)
        finally:
            tmp_path.unlink(missing_ok=True)
    else:
        fig.savefig(str(out), **save_kwargs)

    return out


def list_targets() -> str:
    """Return a formatted table of all pre-defined export targets.

    Returns
    -------
    str
        Human-readable table with columns for key, name, DPI, max size,
        format, and color mode.

    Examples
    --------
    >>> print(list_targets())
    Key            Name      DPI   Max Size (in)    Format   Color
    -------------- --------- ----- ---------------- -------- -----
    annals         Annals      300     7.0 x  9.0    tiff     cmyk
    ...
    """
    header = (
        f"{'Key':<15s} {'Name':<10s} {'DPI':>5s}   {'Max Size (in)':>16s}"
        f"   {'Format':<8s} {'Color':<5s}"
    )
    sep = (
        f"{'-' * 15} {'-' * 10} {'-' * 5}   {'-' * 16}"
        f"   {'-' * 8} {'-' * 5}"
    )
    rows = [header, sep]
    for key in sorted(TARGETS):
        t = TARGETS[key]
        size = f"{t.max_width_inches:5.1f} x {t.max_height_inches:5.1f}"
        rows.append(
            f"{key:<15s} {t.name:<10s} {t.dpi:5d}   {size:>16s}"
            f"   {t.default_format:<8s} {t.color_mode:<5s}"
        )
    return "\n".join(rows)


def figure_info(fig: plt.Figure) -> dict:
    """Return diagnostic information about a figure's current state.

    Useful for verifying size and DPI before or after calling ``export()``.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to inspect.

    Returns
    -------
    dict
        Keys: ``width_inches``, ``height_inches``, ``dpi``,
        ``width_px``, ``height_px``.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots(figsize=(10, 6))
    >>> info = figure_info(fig)
    >>> info["width_inches"]
    10.0
    """
    w, h = fig.get_size_inches()
    dpi = fig.get_dpi()
    return {
        "width_inches": round(w, 4),
        "height_inches": round(h, 4),
        "dpi": int(dpi),
        "width_px": int(round(w * dpi)),
        "height_px": int(round(h * dpi)),
    }
