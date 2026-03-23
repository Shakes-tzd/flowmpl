"""flowmpl — Matplotlib design system and flow diagram renderer.

Provides a cohesive design system (colors, typography, sizing), chart helpers,
and a sophisticated flow diagram renderer with auto-routing and face-override support.

Optional dependencies:
  pip install flowmpl[charts]  # pandas — for chart functions
  pip install flowmpl[maps]    # geopandas + requests — for us_scatter_map
  pip install flowmpl[icons]   # pyconify + cairosvg — for fetch_icon
  pip install flowmpl[gemini]  # google-genai — for generate_illustration
  pip install flowmpl[all]     # all optional deps
"""

from flowmpl.charts import (
    annotated_series,
    horizontal_bar_ranking,
    multi_panel,
    stacked_bar,
    waterfall_chart,
)
from flowmpl.concept import (
    CHART_SCENE_LAYOUT,
    bbox_to_corners,
    cascade_frame,
    chart_scene_frame,
    comparison_frame,
    concept_frame,
    concept_style,
    data_moment_frame,
    rhetorical_frame,
    section_intro_frame,
)
from flowmpl.design import (
    BAR_DEFAULTS,
    COLORS,
    CONCEPT_INK,
    CONCEPT_MUTED,
    CONCEPT_WHITE,
    CONCEPT_YELLOW,
    CONTEXT,
    FIGSIZE,
    FLOW_EDGE_FONT_SIZE,
    FLOW_FONT_SIZE,
    FONTS,
    INK,
    INK_LIGHT,
    INK_MID,
    LEGEND_DEFAULTS,
    PAPER,
    RULE,
    SCATTER_DEFAULTS,
    apply_style,
)
from flowmpl.export import (
    TARGETS,
    ExportTarget,
    export,
    figure_info,
    list_targets,
)
from flowmpl.flow import flow_diagram
from flowmpl.ft_charts import (
    diverging_bar,
    histogram,
    lollipop,
    paired_bar,
    scatter,
    slope_chart,
    strip_plot,
    surplus_deficit_line,
)
from flowmpl.helpers import (
    add_brand_mark,
    add_rule,
    add_source,
    annotate_point,
    chart_title,
    focus_colors,
    legend_below,
    reference_line,
)
from flowmpl.icons import fetch_icon, load_icon
from flowmpl.lint import LintResult, Severity, lint, lint_summary
from flowmpl.strategy import RELATIONSHIPS, color_strategy, suggest_chart
from flowmpl.illustrations import (
    annotate_illustration,
    generate_illustration,
    generate_illustrations,
    remove_background,
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
    # Style
    "apply_style",
    # Design tokens
    "COLORS",
    "CONTEXT",
    "FIGSIZE",
    "FLOW_EDGE_FONT_SIZE",
    "FLOW_FONT_SIZE",
    "FONTS",
    "BAR_DEFAULTS",
    "LEGEND_DEFAULTS",
    "SCATTER_DEFAULTS",
    # Site identity tokens
    "PAPER",
    "INK",
    "INK_MID",
    "INK_LIGHT",
    "RULE",
    # Palettes
    "CATEGORICAL",
    "COMPANY_COLORS",
    "COMPANY_LABELS",
    "FUEL_COLORS",
    "company_color",
    "company_label",
    "fuel_color",
    # Helpers
    "add_brand_mark",
    "add_rule",
    "add_source",
    "annotate_point",
    "chart_title",
    "fetch_icon",
    "load_icon",
    "focus_colors",
    "legend_below",
    "reference_line",
    # Charts
    "annotated_series",
    "horizontal_bar_ranking",
    "multi_panel",
    "stacked_bar",
    "waterfall_chart",
    # FT Visual Vocabulary charts
    "diverging_bar",
    "histogram",
    "lollipop",
    "paired_bar",
    "scatter",
    "slope_chart",
    "strip_plot",
    "surplus_deficit_line",
    # Maps
    "us_scatter_map",
    # Illustrations
    "generate_illustration",
    "generate_illustrations",
    "remove_background",
    "annotate_illustration",
    # Flow
    "flow_diagram",
    # Concept frames
    "bbox_to_corners",
    "cascade_frame",
    "chart_scene_frame",
    "comparison_frame",
    "concept_frame",
    "concept_style",
    "data_moment_frame",
    "rhetorical_frame",
    "section_intro_frame",
    # Concept design tokens
    "CONCEPT_INK",
    "CONCEPT_MUTED",
    "CONCEPT_WHITE",
    "CONCEPT_YELLOW",
    # Concept layout
    "CHART_SCENE_LAYOUT",
    # Export
    "export",
    "ExportTarget",
    "TARGETS",
    "list_targets",
    "figure_info",
    # Lint
    "lint",
    "lint_summary",
    "LintResult",
    "Severity",
    # Strategy
    "color_strategy",
    "suggest_chart",
    "RELATIONSHIPS",
]
