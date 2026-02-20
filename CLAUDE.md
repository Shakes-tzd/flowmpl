# CLAUDE.md — flowmpl

**Owner:** Thandolwethu Zwelakhe Dlamini (Shakes)
**GitHub:** https://github.com/Shakes-tzd/flowmpl (public, `master` branch)
**PyPI:** `pip install flowmpl` / `uv pip install flowmpl` — v0.1.0 published

---

## What This Project Is

`flowmpl` is a standalone Matplotlib design system and flow diagram renderer, extracted
from the Systems research project. It provides a cohesive visual language for analytical
publications: design tokens (colors, typography, sizing), standard chart types, a US map
scatter plot, and a sophisticated flow diagram renderer with compass-heuristic auto-routing
and explicit face-override support.

The primary consumer is the Systems project (`../Systems`), which depends on it via a uv
path source. When published to PyPI it becomes independently installable.

---

## Package Structure

```
flowmpl/
├── CLAUDE.md
├── README.md
├── pyproject.toml
└── src/
    └── flowmpl/
        ├── __init__.py      # Full public API re-exports
        ├── design.py        # COLORS, CONTEXT, FONTS, FIGSIZE, BAR/SCATTER/LEGEND defaults
        ├── palettes.py      # FUEL_COLORS, COMPANY_COLORS, CATEGORICAL + lookup helpers
        ├── helpers.py       # focus_colors(), chart_title(), annotate_point(),
        │                    # reference_line(), legend_below()
        ├── charts.py        # annotated_series(), multi_panel(), stacked_bar(),
        │                    # waterfall_chart(), horizontal_bar_ranking()
        │                    # Optional dep: pandas>=2.0
        ├── maps.py          # us_scatter_map()
        │                    # Optional dep: geopandas>=1.0, requests>=2.31
        └── flow.py          # flow_diagram() — 3-pass routing engine
```

---

## Dependencies

| Scope | Package | Why |
|-------|---------|-----|
| Core (mandatory) | `matplotlib>=3.7` | All rendering |
| Core (mandatory) | `numpy>=1.24` | Bar/waterfall math |
| `[charts]` optional | `pandas>=2.0` | `charts.py` DataFrame inputs |
| `[maps]` optional | `geopandas>=1.0` | State boundary rendering |
| `[maps]` optional | `requests>=2.31` | Census shapefile download |

Install:
```bash
uv pip install -e ".[all]"   # dev: all optional deps
uv pip install -e "."        # core only
```

---

## Development Rules

### Python
- **ALWAYS use `uv`** for all Python operations
  - `uv run python script.py` (not `python`)
  - `uv run pytest` (not `pytest`)
  - `uv pip install package` (not `pip install`)

### Code Style
- `ruff` for linting and formatting
- Run: `uv run ruff check src/`
- Auto-fix: `uv run ruff check src/ --fix`
- Import order: `from __future__` → stdlib → third-party → local (ruff enforces this)

### Adding a New Chart Function
1. Add the function to the appropriate module (`charts.py`, `helpers.py`, `flow.py`)
2. Add the export to `__init__.py` (both the `from ... import` and the `__all__` list)
3. Add `TYPE_CHECKING` guard for any optional dependency type hints
4. Run `uv run ruff check src/` — must be clean before committing
5. Test the import: `uv run python -c "from flowmpl import <new_fn>; print('ok')"`

### Adding a New Design Token
All tokens live in `design.py`. Keep them in their logical groups (COLORS, FONTS, FIGSIZE,
defaults). Never hardcode hex values in `charts.py`, `maps.py`, or `flow.py` — import
from `design.py` instead.

---

## Module Responsibilities

| Module | What lives here | What does NOT live here |
|--------|-----------------|------------------------|
| `design.py` | Every color, font size, figure size, and default dict | No chart logic |
| `palettes.py` | Domain-specific color maps and label lookups | No chart logic; imports COLORS from design |
| `helpers.py` | Axis modifiers that take an existing Axes/Figure | No figure creation |
| `charts.py` | Figure-creating functions for standard chart types | No design constants (import them) |
| `maps.py` | US geographic scatter | No non-map chart types |
| `flow.py` | `flow_diagram()` and all routing internals | No other chart types |

---

## flow_diagram() Architecture

`flow_diagram()` runs in three passes:

1. **Measure** — renders text off-screen to measure pixel extents, converts to data units,
   assigns each node a `(x0, y0, x1, y1)` bounding box
2. **Auto-space** — detects vertical crowding using `_ys_all` tier groups, applies
   `_elhh` boosts for edge-label height, caps expansion at `max_autoscale`
3. **Route and draw** — for each edge: selects exit/entry faces via compass heuristic
   or explicit override, spreads multiple edges sharing a face, draws `FancyArrowPatch`
   with `angle` connectionstyle (elbow) or straight `arc3,rad=0`

**Routing heuristic** (`|vx|` and `|vy|` = absolute vector components src→dst):
- `|vy| < 0.25|vx|` → near-horizontal, straight line (left/right faces)
- `|vx| < 0.25|vy|` → near-vertical, straight line (top/bottom faces)
- `|vy| < 0.75|vx|` → primarily-horizontal, elbow (exits top/bottom, enters side)
- else → primarily-vertical, elbow (exits side, enters top/bottom)

**Face overrides** (`exit`/`entry` keys in edge dict) bypass the heuristic entirely.
Use them when multiple edges would otherwise exit the same face and overlap.

---

## Systems Integration

Systems depends on flowmpl from PyPI:

```toml
# Systems/pyproject.toml
dependencies = ["flowmpl[all]>=0.1.0"]
```

`src/plotting.py` in Systems is a compatibility shim — `from flowmpl import ...` only.
Notebooks import from `src.plotting`; the shim forwards everything.

**After changing flowmpl:** publish a new version to PyPI, bump the version pin in
Systems `pyproject.toml`, run `uv sync`, then `bash scripts/test_notebooks.sh` to confirm
no regressions.

---

## Releasing a New Version

1. Make changes, run `uv run ruff check src/ --fix`
2. Bump `version` in `pyproject.toml` (semantic versioning)
3. `uv build`
4. `uv publish`
5. Push to `master`: `git push origin master`
6. In Systems `pyproject.toml`, update the version pin: `"flowmpl[all]>=<new_version>"`
7. `uv sync` in Systems; `bash scripts/test_notebooks.sh` — all must pass

---

## What Not To Do

- Do not add mandatory dependencies beyond `matplotlib` and `numpy` — keep the core
  install lightweight
- Do not import `pandas`, `geopandas`, or `requests` at module level — guard behind
  `TYPE_CHECKING` or import inside the function
- Do not define chart functions in `__init__.py` — it is a re-export surface only
- Do not add `FONTS` as a module-level import in `flow.py` — it is imported locally
  inside `flow_diagram()` to avoid a circular import through the design module
