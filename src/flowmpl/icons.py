"""Icon fetching utilities — SVG icons from the Iconify ecosystem and local SVG assets.

Provides two loaders:

* :func:`fetch_icon` — pulls icons from 200+ open-source sets via the Iconify
  API (Tabler, Lucide, Phosphor, Font Awesome Free, Bootstrap Icons, …).
* :func:`load_icon` — loads a locally stored SVG file (e.g. produced by
  ``notebooks/build_icons.py``), recolors it, and returns a rasterised RGBA
  array.  Use this for hand-drawn sketch assets where you want to change ink
  color at runtime.

Both functions return matplotlib-ready RGBA numpy arrays cached on disk so
subsequent calls are instant.

Optional dependencies (``uv pip install flowmpl[icons]``):

* ``pyconify>=0.1``  — Iconify API wrapper with local disk caching
* ``cairosvg>=2.7``  — SVG → PNG rasterisation

``cairosvg`` also requires the ``libcairo`` system library:

* macOS:          ``brew install cairo``
* Debian / Ubuntu: ``sudo apt install libcairo2-dev``

Recommended icon sets
---------------------
+------------------+-------+-------+-----------------------------------------------+
| Set prefix       | Count | Lic.  | Strengths                                     |
+==================+=======+=======+===============================================+
| ``tabler``       | 6 000 | MIT   | Energy, tech, finance, policy — best coverage |
| ``lucide``       | 1 600 | ISC   | Clean outline stroke, general purpose         |
| ``ph``           | 7 400 | MIT   | 6 weight variants (thin → bold)               |
| ``fa-solid``     | 1 000 | CC-BY | Widely recognised; attribution required       |
| ``bi``           | 1 900 | MIT   | Bootstrap Icons                               |
+------------------+-------+-------+-----------------------------------------------+

Quick reference — icons used in energy / data-centre analysis
-------------------------------------------------------------
``tabler:solar-panel``, ``tabler:building-wind-turbine``, ``tabler:bolt``,
``tabler:battery``, ``tabler:server``, ``tabler:cpu``, ``tabler:database``,
``tabler:moneybag``, ``tabler:coins``, ``tabler:building-bank``,
``tabler:shield``, ``tabler:building-factory-2``, ``tabler:cloud``,
``tabler:lock``, ``lucide:factory``, ``lucide:landmark``, ``lucide:globe``
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from matplotlib.image import imread

if TYPE_CHECKING:
    pass


# Default disk cache — respects XDG on Linux, uses ~/.cache on macOS/Windows
_DEFAULT_CACHE: Path = Path.home() / ".cache" / "flowmpl" / "icons"


def fetch_icon(
    prefix: str,
    name: str,
    *,
    size: int = 128,
    color: str = "#1A1A1A",
    cache_dir: Path | None = None,
) -> np.ndarray:
    """Fetch an SVG icon and return a matplotlib-ready RGBA numpy array.

    Icons are pulled from the Iconify API (or local cache) and rasterised
    to PNG.  The array can be passed directly to
    :class:`~matplotlib.offsetbox.OffsetImage` or to the ``image``
    argument of :func:`flowmpl.concept._place_asset`.

    Requires ``flowmpl[icons]``::

        uv pip install 'flowmpl[icons]'

    Parameters
    ----------
    prefix : str
        Iconify icon-set prefix, e.g. ``"tabler"``, ``"lucide"``,
        ``"ph"`` (Phosphor), ``"bi"`` (Bootstrap), ``"fa-solid"``.
    name : str
        Icon name within the set, e.g. ``"solar-panel"``, ``"bolt"``,
        ``"server"``, ``"moneybag"``.
    size : int
        Raster output width in pixels (height matches).  Default 128.
    color : str
        Icon stroke / fill colour as a CSS hex string.
        Default ``"#1A1A1A"`` (near-black ink).
    cache_dir : Path, optional
        Override the default cache directory
        (``~/.cache/flowmpl/icons``).

    Returns
    -------
    np.ndarray
        RGBA array of shape ``(H, W, 4)``, dtype ``float32``, values in
        ``[0, 1]``.  Suitable for :class:`~matplotlib.offsetbox.OffsetImage`.

    Raises
    ------
    ImportError
        If ``pyconify`` or ``cairosvg`` are not installed.
    ValueError
        If the icon cannot be found on Iconify (bad prefix or name).

    Examples
    --------
    >>> from flowmpl import fetch_icon, CONCEPT_INK
    >>> bolt  = fetch_icon("tabler", "bolt",         color=CONCEPT_INK)
    >>> solar = fetch_icon("tabler", "solar-panel",  color="#F5C842", size=96)
    >>> srv   = fetch_icon("lucide", "server",        color="#52B788")

    Use in a concept frame::

        from flowmpl import concept_style, data_moment_frame, fetch_icon
        bolt_icon = fetch_icon("tabler", "bolt", color="#1A1A1A")
        fig = data_moment_frame(
            "639 TWh",
            surrounding={"top_right": ("US WIND 2022", bolt_icon)},
        )
    """
    try:
        import pyconify  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "fetch_icon requires pyconify.\n"
            "Install it with:  uv pip install 'flowmpl[icons]'"
        ) from exc

    try:
        import cairosvg  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "fetch_icon requires cairosvg.\n"
            "Install it with:  uv pip install 'flowmpl[icons]'\n"
            "cairosvg also needs the libcairo system library:\n"
            "  macOS:           brew install cairo\n"
            "  Debian / Ubuntu: sudo apt install libcairo2-dev"
        ) from exc

    # ── Cache key ──────────────────────────────────────────────────────────
    color_norm = color.lstrip("#").lower()
    key        = hashlib.sha1(
        f"{prefix}/{name}/{size}/{color_norm}".encode()
    ).hexdigest()[:12]
    cache_root = cache_dir or _DEFAULT_CACHE
    cache_path = cache_root / prefix / f"{name}-{key}.png"

    if cache_path.exists():
        return imread(str(cache_path)).astype("float32")

    # ── Fetch SVG from Iconify ─────────────────────────────────────────────
    svg_bytes = pyconify.svg(prefix, name, color=color, height=size)
    if not svg_bytes:
        raise ValueError(
            f"Icon not found on Iconify: {prefix}:{name}\n"
            "Browse available icons at https://icon-sets.iconify.design/"
        )

    # ── Rasterise SVG → PNG ────────────────────────────────────────────────
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=size)

    # ── Persist to cache ───────────────────────────────────────────────────
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(png_bytes)

    return imread(io.BytesIO(png_bytes)).astype("float32")


def load_icon(
    path: Path | str,
    *,
    color: str = "#1A1A1A",
    size: int = 256,
    cache_dir: Path | None = None,
) -> np.ndarray:
    """Load a local SVG icon, recolor its ink, and return a matplotlib-ready RGBA array.

    Designed for hand-drawn sketch SVGs produced by ``notebooks/build_icons.py``
    (potrace output from Gemini-generated B&W PNGs).  The SVG's black fills are
    replaced with ``color``; cairosvg rasterises to a transparent-background PNG.

    Requires ``flowmpl[icons]``::

        uv pip install 'flowmpl[icons]'

    Parameters
    ----------
    path : Path | str
        Path to the local SVG file.
    color : str
        Ink colour as a CSS hex string.  Default ``"#1A1A1A"`` (near-black).
    size : int
        Raster output width in pixels.  Default 256.
    cache_dir : Path, optional
        Override the default cache directory
        (``~/.cache/flowmpl/icons/svg/``).

    Returns
    -------
    np.ndarray
        RGBA array of shape ``(H, W, 4)``, dtype ``float32``, values in
        ``[0, 1]``.  Suitable for :class:`~matplotlib.offsetbox.OffsetImage`.

    Raises
    ------
    ImportError
        If ``cairosvg`` is not installed.
    FileNotFoundError
        If ``path`` does not exist.

    Examples
    --------
    >>> from pathlib import Path
    >>> from flowmpl import load_icon, FUEL_COLORS
    >>> icons_dir = Path("notebooks/assets/icons")
    >>> bolt  = load_icon(icons_dir / "bolt.svg",        color=FUEL_COLORS["wind"])
    >>> solar = load_icon(icons_dir / "solar_panel.svg", color=FUEL_COLORS["solar"])
    """
    try:
        import cairosvg  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "load_icon requires cairosvg.\n"
            "Install it with:  uv pip install 'flowmpl[icons]'"
        ) from exc

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SVG not found: {path}")

    # ── Cache key (invalidates when file changes) ──────────────────────────
    color_norm = color.lstrip("#").lower()
    mtime      = int(path.stat().st_mtime)
    key        = hashlib.sha1(
        f"{path.stem}/{color_norm}/{size}/{mtime}".encode()
    ).hexdigest()[:12]
    cache_root = cache_dir or (_DEFAULT_CACHE / "svg")
    cache_path = cache_root / f"{path.stem}-{key}.png"

    if cache_path.exists():
        return imread(str(cache_path)).astype("float32")

    # ── Recolor SVG ────────────────────────────────────────────────────────
    svg_text = _recolor_svg(path.read_text(), color)

    # ── Rasterise SVG → PNG ────────────────────────────────────────────────
    png_bytes = cairosvg.svg2png(bytestring=svg_text.encode(), output_width=size)

    # ── Persist to cache ───────────────────────────────────────────────────
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(png_bytes)

    return imread(io.BytesIO(png_bytes)).astype("float32")


def _recolor_svg(svg_text: str, color: str) -> str:
    """Replace black fills in a potrace SVG with ``color``.

    potrace outputs ``fill="#000000"`` on the root ``<g>`` element; all
    ``<path>`` children inherit it.  A targeted string substitution is
    sufficient and avoids XML namespace mangling.
    """
    # potrace always emits fill="#000000"; handle common variants defensively
    for black in ('#000000', '#010101', '#0d0d0d', '"black"'):
        svg_text = svg_text.replace(f'fill="{black}"', f'fill="{color}"')
        svg_text = svg_text.replace(f"fill='{black}'", f"fill='{color}'")
    return svg_text
