# flowmpl

Matplotlib design system and flow diagram renderer for analytical publications.

Built for research notebooks that combine data visualization with process flow diagrams — the kind of work where you need both a consistent visual language across charts *and* clean auto-routed arrows between labeled boxes.

## Install

```bash
pip install flowmpl           # core: matplotlib + numpy only
pip install flowmpl[charts]   # + pandas (annotated_series, stacked_bar, etc.)
pip install flowmpl[maps]     # + geopandas + requests (us_scatter_map)
pip install flowmpl[all]      # everything
```

## Quick Start

```python
from flowmpl import COLORS, FONTS, flow_diagram

fig = flow_diagram(
    nodes={
        "a": ("Announce", 1.0, 1.0, COLORS["accent"],    "#ffffff"),
        "b": ("Permit",   3.0, 1.0, COLORS["neutral"],   COLORS["text_dark"]),
        "c": ("Build",    5.0, 1.0, COLORS["positive"],  "#ffffff"),
    },
    edges=[
        {"src": "a", "dst": "b", "label": "12–18 mo"},
        {"src": "b", "dst": "c", "label": "24–36 mo"},
    ],
    title="From announcement to operation",
)
fig.savefig("pipeline.png", dpi=150, bbox_inches="tight")
```

## Design System

`flowmpl` ships a complete design system extracted from a production research project:

| Token | Description |
|-------|-------------|
| `COLORS` | Semantic roles: `accent`, `positive`, `negative`, `neutral`, `muted`, `reference`, `background`, `text_dark`, `text_light` |
| `CONTEXT` | SWD gray — use for non-focus elements in gray+accent charts |
| `FONTS` | Font sizes for titles, labels, annotations, legends, captions |
| `FIGSIZE` | Named figure sizes: `standard`, `wide`, `tall`, `map` |
| `CATEGORICAL` | 8-color Paul Tol colorblind-safe palette |
| `FUEL_COLORS` | Energy generation types: solar, wind, battery, gas_cc, gas_ct, nuclear, hydro, coal… |
| `COMPANY_COLORS` | Hyperscaler tickers: MSFT, AMZN, GOOGL, META, NVDA, ORCL, AAPL, TSLA |

## Chart Functions

All functions return `matplotlib.Figure` objects.

```python
from flowmpl import (
    annotated_series,       # time series with annotations + fill
    multi_panel,            # multi-subplot from a single DataFrame
    stacked_bar,            # stacked bar for categorical breakdowns
    waterfall_chart,        # cost allocation / flow breakdowns
    horizontal_bar_ranking, # ranked horizontal bars with highlights
)
```

## Helpers

```python
from flowmpl import (
    focus_colors,    # SWD gray+accent pattern: focus items colored, rest gray
    legend_below,    # place legend below axes (works with bbox_inches='tight')
    annotate_point,  # annotate a data point with arrow + text
    reference_line,  # labeled horizontal or vertical reference line
    chart_title,     # subtle left-aligned insight title (for standalone PNGs)
)
```

### `focus_colors()` example

```python
colors = focus_colors(
    ["MSFT", "AMZN", "GOOGL", "META"],
    focus="AMZN",
    color_map=COMPANY_COLORS,
)
# → ['#c0c0c0', '#ff9900', '#c0c0c0', '#c0c0c0']
```

## Flow Diagram

`flow_diagram()` renders labeled boxes connected by auto-routed arrows. It handles:

- **Auto-routing**: chooses straight or elbow connections based on source/destination geometry
- **Face overrides**: explicit `exit`/`entry` keys bypass the heuristic for complex layouts
- **Auto-spacing**: adjusts vertical spacing to prevent label overlap
- **Face spreading**: distributes multiple edges from the same face to avoid overlaps

### Node format

```python
nodes = {
    "key": (label, cx, cy, fill_color, text_color),
}
```

- `cx`, `cy`: center coordinates in abstract units (the renderer scales to fit)
- Sizes auto-scaled; override with `node_width` / `node_height` params

### Edge format

```python
edges = [
    {"src": "a", "dst": "b"},                           # basic
    {"src": "a", "dst": "b", "label": "2 years"},       # with label
    {"src": "a", "dst": "b", "dashed": True},           # dashed line
    {"src": "a", "dst": "b", "color": "#888"},          # custom color
    {"src": "a", "dst": "b", "exit": "top",   "entry": "left"},  # face override
    {"src": "a", "dst": "b", "exit": "bottom", "entry": "left"}, # force exit face
]
```

### Routing heuristic

The auto-router uses the vector between node centers:

| Condition | Route style |
|-----------|-------------|
| `\|vy\| < 0.25 \* \|vx\|` | Near-horizontal — straight line |
| `\|vx\| < 0.25 \* \|vy\|` | Near-vertical — straight line |
| `\|vy\| < 0.75 \* \|vx\|` | Primarily-horizontal — exit top/bottom, enter side |
| else | Primarily-vertical — exit side, enter top/bottom |

Use explicit `exit`/`entry` overrides when the heuristic produces overlapping arrows
from the same face (e.g., a root node with multiple connections at different angles).

### T-layout example (face overrides)

```python
fig = flow_diagram(
    nodes={
        "r": ("Root",   1.0, 1.5, COLORS["accent"],   "#ffffff"),
        "a": ("Top",    4.5, 3.0, COLORS["positive"], "#ffffff"),
        "m": ("Middle", 4.5, 1.5, COLORS["neutral"],  COLORS["text_dark"]),
        "b": ("Bottom", 4.5, 0.0, CONTEXT,            COLORS["text_dark"]),
    },
    edges=[
        {"src": "r", "dst": "a", "exit": "top",    "entry": "left"},
        {"src": "r", "dst": "m"},                           # straight, no override needed
        {"src": "r", "dst": "b", "exit": "bottom", "entry": "left"},
    ],
    title="Three destinations from one source",
)
```

Without the face overrides, all three arrows would exit from `r`'s right face and overlap.
With `exit="top"` and `exit="bottom"`, each arrow leaves from a different face.

## Map

```python
from flowmpl import us_scatter_map
import matplotlib.patches as mpatches

fig = us_scatter_map(
    lats=[37.7, 40.7, 41.8],
    lons=[-122.4, -74.0, -87.6],
    colors=["#e74c3c", "#3498db", "#2ecc71"],
    sizes=[100, 150, 80],
    title="Three cities",
    legend_handles=[
        mpatches.Patch(color="#e74c3c", label="San Francisco"),
        mpatches.Patch(color="#3498db", label="New York"),
        mpatches.Patch(color="#2ecc71", label="Chicago"),
    ],
)
```

State boundary shapefiles are downloaded from the US Census Bureau on first use and
cached in the package directory.

## License

MIT
