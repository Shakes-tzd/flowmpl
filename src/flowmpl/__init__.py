"""flowmpl — Matplotlib design system and flow diagram renderer.

Provides a cohesive design system (colors, typography, sizing), chart helpers,
and a sophisticated flow diagram renderer with auto-routing and face-override support.

Optional dependencies:
  pip install flowmpl[charts]  # pandas — for chart functions
  pip install flowmpl[maps]    # geopandas + requests — for us_scatter_map
  pip install flowmpl[all]     # all optional deps
"""

from flowmpl.charts import (
    annotated_series,
    horizontal_bar_ranking,
    multi_panel,
    stacked_bar,
    waterfall_chart,
)
from flowmpl.design import (
    BAR_DEFAULTS,
    COLORS,
    CONTEXT,
    FIGSIZE,
    FLOW_FONT_SIZE,
    FONTS,
    LEGEND_DEFAULTS,
    SCATTER_DEFAULTS,
)
from flowmpl.flow import flow_diagram
from flowmpl.helpers import (
    annotate_point,
    chart_title,
    focus_colors,
    legend_below,
    reference_line,
)
from flowmpl.maps import us_scatter_map
from flowmpl.palettes import (
    CATEGORICAL,
    COMPANY_COLORS,
    COMPANY_LABELS,
    FUEL_COLORS,
    company_color,
    company_label,
    fuel_color,
)

__all__ = [
    # Design tokens
    "COLORS",
    "CONTEXT",
    "FIGSIZE",
    "FLOW_FONT_SIZE",
    "FONTS",
    "BAR_DEFAULTS",
    "LEGEND_DEFAULTS",
    "SCATTER_DEFAULTS",
    # Palettes
    "CATEGORICAL",
    "COMPANY_COLORS",
    "COMPANY_LABELS",
    "FUEL_COLORS",
    "company_color",
    "company_label",
    "fuel_color",
    # Helpers
    "annotate_point",
    "chart_title",
    "focus_colors",
    "legend_below",
    "reference_line",
    # Charts
    "annotated_series",
    "horizontal_bar_ranking",
    "multi_panel",
    "stacked_bar",
    "waterfall_chart",
    # Maps
    "us_scatter_map",
    # Flow
    "flow_diagram",
]
