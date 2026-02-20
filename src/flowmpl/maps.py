"""Geographic visualization — scatter points on US state boundary maps.

Optional dependency: geopandas>=1.0, requests>=2.31.
Install via: pip install flowmpl[maps]
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from flowmpl.design import COLORS, FIGSIZE, FONTS, SCATTER_DEFAULTS
from flowmpl.helpers import chart_title

if TYPE_CHECKING:
    from collections.abc import Sequence


# ---------------------------------------------------------------------------
# State boundary data
# ---------------------------------------------------------------------------

_SHAPEFILE_DIR = Path(__file__).resolve().parent / "_data" / "cb_2024_us_state_20m"
_SHAPEFILE_URL = (
    "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_20m.zip"
)

# FIPS codes for non-continental states/territories to exclude
_EXCLUDE_FIPS = {
    "02", "15", "60", "66", "69", "72", "78",  # AK, HI, AS, GU, MP, PR, VI
}


def _get_states_gdf():
    """Load continental US state boundaries, downloading if needed."""
    try:
        import geopandas as gpd
        import requests
    except ImportError as e:
        raise ImportError(
            "us_scatter_map requires geopandas and requests. "
            "Install with: pip install flowmpl[maps]"
        ) from e

    shp_file = _SHAPEFILE_DIR / "cb_2024_us_state_20m.shp"
    if not shp_file.exists():
        resp = requests.get(_SHAPEFILE_URL, timeout=60)
        resp.raise_for_status()
        _SHAPEFILE_DIR.mkdir(parents=True, exist_ok=True)
        _shapefile_dir_resolved = _SHAPEFILE_DIR.resolve()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for member in zf.namelist():
                member_path = (_SHAPEFILE_DIR / member).resolve()
                if not str(member_path).startswith(str(_shapefile_dir_resolved)):
                    raise ValueError(f"Unsafe ZIP path rejected: {member}")
            zf.extractall(_SHAPEFILE_DIR)

    gdf = gpd.read_file(shp_file)
    return gdf[~gdf["STATEFP"].isin(_EXCLUDE_FIPS)]


def us_scatter_map(
    lats: Sequence[float],
    lons: Sequence[float],
    colors: Sequence[str] | str,
    sizes: Sequence[float] | float,
    title: str,
    *,
    legend_handles: list | None = None,
    figsize: tuple[float, float] = FIGSIZE["map"],
    alpha: float = SCATTER_DEFAULTS["alpha"],
    edgecolors: str = "white",
    linewidth: float = 0.5,
) -> plt.Figure:
    """Plot scatter points on a US continental map with state boundaries.

    Parameters
    ----------
    lats : sequence of float
        Latitude values (decimal degrees).
    lons : sequence of float
        Longitude values (decimal degrees).
    colors : str or sequence of str
        Color(s) for each point.
    sizes : float or sequence of float
        Size(s) for each point.
    title : str
        Insight-driven chart title.
    legend_handles : list, optional
        Matplotlib legend handles to display.
    figsize : tuple
        Figure size.
    alpha : float
        Point transparency.
    edgecolors : str
        Edge color for scatter points.
    linewidth : float
        Edge linewidth for scatter points.

    Returns
    -------
    matplotlib.figure.Figure
    """
    states = _get_states_gdf()

    fig, ax = plt.subplots(figsize=figsize)
    states.plot(ax=ax, color=COLORS["background"], edgecolor=COLORS["muted"], linewidth=0.7)

    ax.scatter(
        lons, lats, c=colors, s=sizes, alpha=alpha,
        edgecolors=edgecolors, linewidth=linewidth, zorder=3,
    )

    ax.set_xlim(-125, -66)
    ax.set_ylim(24, 50)
    ax.set_axis_off()

    if legend_handles:
        labels = [h.get_label() for h in legend_handles]
        ncol = min(len(legend_handles), 5)
        ax.legend(
            handles=legend_handles, labels=labels,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.03),
            ncol=ncol,
            fontsize=FONTS["legend"],
            frameon=False,
            markerscale=1.3,
        )

    plt.tight_layout()
    chart_title(fig, title)
    return fig
