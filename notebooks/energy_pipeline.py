import marimo

__generated_with = "0.19.11"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Energy Transition Dashboard

    A live data pipeline and visualisation demo built with three open-source tools:

    | Layer | Tool | Role |
    |-------|------|------|
    | **Ingest** | [DLT](https://dlthub.com) | Download & normalise two public datasets |
    | **Store** | [DuckDB](https://duckdb.org) | Embedded columnar SQL, zero config |
    | **Visualise** | [flowmpl](https://github.com/Shakes-tzd/flowmpl) | Design-system charts + flow diagram |

    **Data sources**

    - [Our World in Data — Energy](https://github.com/owid/energy-data):
      country-level electricity generation by fuel type, 2000–2022
    - [USGS Wind Turbine Database](https://eerscmap.usgs.gov/uswtdb/):
      70 000+ US wind turbine locations and rated capacities (stratified sample used here)

    Run the **pipeline** cell once — the DuckDB file is cached next to this notebook.
    Subsequent runs skip ingestion and read directly from disk.

    > **Install:** `uv pip install -e ".[all,examples]"` from the project root.
    """)
    return


@app.cell
def _():
    import io
    import zipfile
    from pathlib import Path

    import dlt
    import duckdb
    import matplotlib.patches as mpatches
    import pandas as pd

    from flowmpl import (
        CATEGORICAL,
        COLORS,
        CONTEXT,
        FLOW_EDGE_FONT_SIZE,
        FLOW_FONT_SIZE,
        FUEL_COLORS,
        annotated_series,
        apply_style,
        flow_diagram,
        horizontal_bar_ranking,
        multi_panel,
        stacked_bar,
        us_scatter_map,
        waterfall_chart,
    )

    return (
        CATEGORICAL,
        COLORS,
        CONTEXT,
        FLOW_EDGE_FONT_SIZE,
        FLOW_FONT_SIZE,
        FUEL_COLORS,
        Path,
        annotated_series,
        apply_style,
        dlt,
        duckdb,
        flow_diagram,
        horizontal_bar_ranking,
        io,
        mpatches,
        multi_panel,
        pd,
        stacked_bar,
        us_scatter_map,
        waterfall_chart,
        zipfile,
    )


@app.cell(hide_code=True)
def _(apply_style):
    apply_style()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Pipeline Architecture
    """)
    return


@app.cell
def pipeline_diagram(
    COLORS,
    CONTEXT,
    FLOW_EDGE_FONT_SIZE,
    FLOW_FONT_SIZE,
    flow_diagram,
):
    _nodes = {
        "owid": (
            "OWID Energy\nDataset",
            1.0, 2.0,
            COLORS["accent"], "#ffffff",
        ),
        "usgs": (
            "USGS Wind\nTurbine DB",
            1.0, 0.0,
            COLORS["positive"], "#ffffff",
        ),
        "r_energy": (
            "DLT resource\nworld_energy",
            5.5, 2.0,
            COLORS["neutral"], COLORS["text_dark"],
        ),
        "r_turbines": (
            "DLT resource\nwind_turbines",
            5.5, 0.0,
            COLORS["neutral"], COLORS["text_dark"],
        ),
        "duckdb": (
            "DuckDB\nenergy_dashboard",
            10.5, 1.0,
            COLORS["negative"], "#ffffff",
        ),
        "queries": (
            "SQL\nQueries",
            15.0, 1.0,
            CONTEXT, COLORS["text_dark"],
        ),
        "charts": (
            "flowmpl\nVisualizations",
            19.5, 1.0,
            COLORS["accent"], "#ffffff",
        ),
    }
    _edges = [
        {"src": "owid",       "dst": "r_energy",   "label": "HTTP \ndownload"},
        {"src": "usgs",       "dst": "r_turbines", "label": "HTTP \n+ unzip"},
        {"src": "r_energy",   "dst": "duckdb",     "label": "load",
         "exit": "right", "entry": "top"},
        {"src": "r_turbines", "dst": "duckdb",     "label": "load",
         "exit": "right", "entry": "bottom"},
        {"src": "duckdb",     "dst": "queries",    "label": "query"},
        {"src": "queries",    "dst": "charts",     "label": "DataFrames"},
    ]
    energy_dashboard_pipeline_fig = flow_diagram(
        _nodes,
        _edges,
        figsize=(22, 5),
        font_size=FLOW_FONT_SIZE,
        edge_font_size=FLOW_EDGE_FONT_SIZE,
        title="DLT → DuckDB → flowmpl  ·  energy_dashboard pipeline",
    )
    energy_dashboard_pipeline_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Data Pipeline

    The DLT pipeline below downloads two public datasets and loads them into DuckDB.
    It uses `write_disposition="replace"` so re-running always produces a clean load.
    Delete `energy_dashboard.duckdb` next to this notebook to force a fresh download.
    """)
    return


@app.cell
def pipeline_exec(Path, dlt, io, mo, pd, zipfile):
    _DB_FILE = (mo.notebook_dir() or Path.cwd()) / "energy_dashboard.duckdb"

    if not _DB_FILE.exists():
        import requests as _req

        @dlt.resource(name="world_energy", write_disposition="replace")
        def _world_energy():
            _url = (
                "https://raw.githubusercontent.com/owid/energy-data/"
                "master/owid-energy-data.csv"
            )
            _resp = _req.get(_url, timeout=120)
            _resp.raise_for_status()
            _keep = [
                "country", "year",
                "electricity_generation", "renewables_electricity",
                "solar_electricity", "wind_electricity", "hydro_electricity",
                "nuclear_electricity", "coal_electricity",
                "gas_electricity", "oil_electricity",
            ]
            _df = pd.read_csv(io.StringIO(_resp.text))
            _df = _df[[c for c in _keep if c in _df.columns]]
            _df = _df[_df["year"] >= 2000].dropna(subset=["country", "year"])
            yield from _df.to_dict(orient="records")

        @dlt.resource(name="wind_turbines", write_disposition="replace")
        def _wind_turbines():
            _url = "https://eerscmap.usgs.gov/uswtdb/assets/data/uswtdbCSV.zip"
            _resp = _req.get(_url, timeout=180)
            _resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(_resp.content)) as _zf:
                _csv = next(n for n in _zf.namelist() if n.endswith(".csv"))
                _df = pd.read_csv(
                    _zf.open(_csv),
                    usecols=["xlong", "ylat", "t_cap", "t_manu"],
                    dtype={"t_cap": float},
                )
            _df = _df.dropna(subset=["xlong", "ylat", "t_cap"])
            # Stratified sample: ~200 per capacity tier so the map loads fast
            _tiers = [
                _df[_df["t_cap"] < 1000].sample(
                    min(200, int((_df["t_cap"] < 1000).sum())), random_state=42
                ),
                _df[(_df["t_cap"] >= 1000) & (_df["t_cap"] < 2500)].sample(
                    min(250, int(((_df["t_cap"] >= 1000) & (_df["t_cap"] < 2500)).sum())),
                    random_state=42,
                ),
                _df[_df["t_cap"] >= 2500].sample(
                    min(200, int((_df["t_cap"] >= 2500).sum())), random_state=42
                ),
            ]
            yield from pd.concat(_tiers).to_dict(orient="records")

        _pipe = dlt.pipeline(
            pipeline_name="energy_dashboard",
            destination=dlt.destinations.duckdb(credentials=str(_DB_FILE)),
            dataset_name="energy",
        )
        _pipe.run([_world_energy(), _wind_turbines()])
        _status = f"Pipeline complete — data written to **{_DB_FILE.name}**"
    else:
        _status = (
            f"Using cached DuckDB at **{_DB_FILE.name}** "
            f"({_DB_FILE.stat().st_size / 1e6:.1f} MB) — "
            "delete the file to re-ingest."
        )

    DB_PATH = str(_DB_FILE)
    pipeline_status = _status
    return DB_PATH, pipeline_status


@app.cell(hide_code=True)
def _(mo, pipeline_status):
    mo.callout(mo.md(pipeline_status), kind="success")
    return


@app.cell
def db_connect(DB_PATH, duckdb):
    conn = duckdb.connect(DB_PATH, read_only=True)
    return (conn,)


@app.cell(hide_code=True)
def _(conn, mo):
    _sql_we = "SELECT COUNT(*) FROM energy.world_energy"
    _sql_wt = "SELECT COUNT(*) FROM energy.wind_turbines"
    _we = conn.sql(_sql_we).fetchone()[0]
    _wt = conn.sql(_sql_wt).fetchone()[0]
    mo.md(
        f"**energy.world_energy**: {_we:,} rows &nbsp;·&nbsp; "
        f"**energy.wind_turbines**: {_wt:,} rows (stratified sample)"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## US Wind & Solar: A 10× Surge Since 2010

    Wind and solar together surpassed nuclear generation in the United States in 2020.
    The Inflation Reduction Act (August 2022) locked in a decade of accelerated
    deployment — wind alone exceeded coal generation for the first time that year.
    """)
    return


@app.cell
def ts_data(conn, pd):
    _sql = """
        SELECT year, wind_electricity, solar_electricity
        FROM energy.world_energy
        WHERE country = 'United States'
          AND year BETWEEN 2010 AND 2022
          AND wind_electricity IS NOT NULL
        ORDER BY year
    """
    df_us_ts = conn.sql(_sql).df()
    df_us_ts.index = pd.to_datetime(df_us_ts.pop("year").astype(str), format="%Y")
    df_us_ts = df_us_ts.fillna(0.0)
    return (df_us_ts,)


@app.cell
def ts_chart(FUEL_COLORS, annotated_series, df_us_ts, pd):
    _wind_2022 = float(
        df_us_ts[df_us_ts.index.year == 2022]["wind_electricity"].iloc[0]
    )
    wind_fig_ts = annotated_series(
        df_us_ts,
        columns={
            "wind_electricity": {
                "color": FUEL_COLORS["wind"],
                "label": "Wind (TWh)",
                "linewidth": 2.5,
            },
            "solar_electricity": {
                "color": FUEL_COLORS["solar"],
                "label": "Solar (TWh)",
                "linewidth": 2.5,
            },
        },
        title="US Wind & Solar Electricity Has Grown 10× Since 2010",
        ylabel="Electricity (TWh)",
        annotations=[
            (
                "Inflation\nReduction Act",
                pd.Timestamp("2022-01-01"),
                _wind_2022,
                (pd.Timestamp("2018-06-01"), _wind_2022 + 130),
            ),
        ],
        figsize=(13, 5),
    )
    wind_fig_ts
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2022 Energy Mix by Country

    China's coal generation exceeds the combined output of the other five countries.
    France's nuclear dominance and Germany's balanced renewables portfolio stand out
    among large European economies.
    """)
    return


@app.cell
def mix_data(conn):
    _sql = """
        SELECT country,
               COALESCE(coal_electricity,    0) AS coal,
               COALESCE(gas_electricity,     0) AS gas,
               COALESCE(nuclear_electricity, 0) AS nuclear,
               COALESCE(hydro_electricity,   0) AS hydro,
               COALESCE(wind_electricity,    0) AS wind,
               COALESCE(solar_electricity,   0) AS solar
        FROM energy.world_energy
        WHERE year = 2022
          AND country IN (
              'United States', 'China', 'Germany',
              'India', 'United Kingdom', 'France'
          )
        ORDER BY (
            COALESCE(coal_electricity,    0) +
            COALESCE(gas_electricity,     0) +
            COALESCE(nuclear_electricity, 0) +
            COALESCE(hydro_electricity,   0) +
            COALESCE(wind_electricity,    0) +
            COALESCE(solar_electricity,   0)
        ) DESC
    """
    df_mix = conn.sql(_sql).df()
    return (df_mix,)


@app.cell
def mix_chart(FUEL_COLORS, df_mix, stacked_bar):
    energy_fig_mix = stacked_bar(
        df_mix,
        x_col="country",
        stack_cols={
            "coal":    {"color": FUEL_COLORS["coal"],    "label": "Coal"},
            "gas":     {"color": FUEL_COLORS["gas_cc"],  "label": "Gas"},
            "nuclear": {"color": FUEL_COLORS["nuclear"], "label": "Nuclear"},
            "hydro":   {"color": FUEL_COLORS["hydro"],   "label": "Hydro"},
            "wind":    {"color": FUEL_COLORS["wind"],    "label": "Wind"},
            "solar":   {"color": FUEL_COLORS["solar"],   "label": "Solar"},
        },
        title="China Generated More Coal Power in 2022 Than the Other Five Countries Combined",
        ylabel="Electricity (TWh)",
        figsize=(13, 6),
        rotation=15,
    )
    energy_fig_mix 
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## US Electricity Mix Shift: 2010 → 2022

    Each bar shows the change in generation (TWh) per fuel source over twelve years.
    Coal fell by the largest margin; wind and gas grew the most to fill the gap.

    > Value labels reflect the chart's financial-data design (`$B`);
    > each unit here represents **1 TWh** of generation change.
    """)
    return


@app.cell
def wf_data(conn):
    _sql = """
        WITH y2010 AS (
            SELECT coal_electricity, gas_electricity, nuclear_electricity,
                   hydro_electricity, wind_electricity, solar_electricity
            FROM energy.world_energy
            WHERE country = 'United States' AND year = 2010
        ),
        y2022 AS (
            SELECT coal_electricity, gas_electricity, nuclear_electricity,
                   hydro_electricity, wind_electricity, solar_electricity
            FROM energy.world_energy
            WHERE country = 'United States' AND year = 2022
        )
        SELECT
            COALESCE(y2022.coal_electricity,    0) - COALESCE(y2010.coal_electricity,    0),
            COALESCE(y2022.gas_electricity,     0) - COALESCE(y2010.gas_electricity,     0),
            COALESCE(y2022.nuclear_electricity, 0) - COALESCE(y2010.nuclear_electricity, 0),
            COALESCE(y2022.hydro_electricity,   0) - COALESCE(y2010.hydro_electricity,   0),
            COALESCE(y2022.wind_electricity,    0) - COALESCE(y2010.wind_electricity,    0),
            COALESCE(y2022.solar_electricity,   0) - COALESCE(y2010.solar_electricity,   0)
        FROM y2010, y2022
    """
    _row = conn.sql(_sql).fetchone()
    wf_items = [
        ("Coal",    _row[0]),
        ("Gas",     _row[1]),
        ("Nuclear", _row[2]),
        ("Hydro",   _row[3]),
        ("Wind",    _row[4]),
        ("Solar",   _row[5]),
    ]
    return (wf_items,)


@app.cell
def wf_chart(COLORS, waterfall_chart, wf_items):
    us_energy_mix_fig_wf = waterfall_chart(
        wf_items,
        title="US Electricity Mix Shift 2010 → 2022: Coal Out, Wind and Gas In (TWh Δ)",
        total_label="Net Change",
        figsize=(12, 5),
        positive_color=COLORS["positive"],
        negative_color=COLORS["negative"],
        total_color=COLORS["accent"],
    )
    # Override the hardcoded financial ylabel — values are TWh deltas here
    us_energy_mix_fig_wf.axes[0].set_ylabel("Change (TWh)")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Solar, Wind & Coal: US vs Germany vs China (2010–2022)

    Three countries, three energy strategies. Germany leads on solar relative to grid
    size; the US leads on wind capacity; China is scaling all three sources
    simultaneously — deploying more new renewable capacity per year than the rest of
    the world combined.
    """)
    return


@app.cell
def mp_data(conn, pd):
    _sql = """
        SELECT year,
            MAX(CASE WHEN country = 'United States'
                THEN COALESCE(solar_electricity, 0) END) AS us_solar,
            MAX(CASE WHEN country = 'United States'
                THEN COALESCE(wind_electricity,  0) END) AS us_wind,
            MAX(CASE WHEN country = 'United States'
                THEN COALESCE(coal_electricity,  0) END) AS us_coal,
            MAX(CASE WHEN country = 'Germany'
                THEN COALESCE(solar_electricity, 0) END) AS de_solar,
            MAX(CASE WHEN country = 'Germany'
                THEN COALESCE(wind_electricity,  0) END) AS de_wind,
            MAX(CASE WHEN country = 'Germany'
                THEN COALESCE(coal_electricity,  0) END) AS de_coal,
            MAX(CASE WHEN country = 'China'
                THEN COALESCE(solar_electricity, 0) END) AS cn_solar,
            MAX(CASE WHEN country = 'China'
                THEN COALESCE(wind_electricity,  0) END) AS cn_wind,
            MAX(CASE WHEN country = 'China'
                THEN COALESCE(coal_electricity,  0) END) AS cn_coal
        FROM energy.world_energy
        WHERE country IN ('United States', 'Germany', 'China')
          AND year BETWEEN 2010 AND 2022
        GROUP BY year
        ORDER BY year
    """
    df_mp = conn.sql(_sql).df()
    df_mp.index = pd.to_datetime(df_mp.pop("year").astype(str), format="%Y")
    df_mp = df_mp.fillna(0.0)
    return (df_mp,)


@app.cell
def mp_chart(CATEGORICAL, FUEL_COLORS, df_mp, multi_panel):
    swc_fig_mp = multi_panel(
        df_mp,
        panels=[
            {
                "columns": {
                    "us_solar": {
                        "color": FUEL_COLORS["solar"], "label": "USA", "linewidth": 2,
                    },
                    "de_solar": {
                        "color": CATEGORICAL[0], "label": "Germany", "linewidth": 2,
                    },
                    "cn_solar": {
                        "color": CATEGORICAL[1], "label": "China", "linewidth": 2,
                    },
                },
                "title": "Solar (TWh)",
                "ylabel": "TWh",
            },
            {
                "columns": {
                    "us_wind": {
                        "color": FUEL_COLORS["wind"], "label": "USA", "linewidth": 2,
                    },
                    "de_wind": {
                        "color": CATEGORICAL[0], "label": "Germany", "linewidth": 2,
                    },
                    "cn_wind": {
                        "color": CATEGORICAL[1], "label": "China", "linewidth": 2,
                    },
                },
                "title": "Wind (TWh)",
                "ylabel": "TWh",
            },
            {
                "columns": {
                    "us_coal": {
                        "color": FUEL_COLORS["coal"], "label": "USA", "linewidth": 2,
                    },
                    "de_coal": {
                        "color": CATEGORICAL[0], "label": "Germany", "linewidth": 2,
                    },
                    "cn_coal": {
                        "color": CATEGORICAL[1], "label": "China", "linewidth": 2,
                    },
                },
                "title": "Coal (TWh)",
                "ylabel": "TWh",
            },
        ],
        suptitle="Solar, Wind & Coal  ·  United States vs Germany vs China  (2010–2022)",
        ncols=3,
        figsize=(17, 5),
    )
    swc_fig_mp
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Which Countries Lead on Renewables? (2022)

    Smaller hydro-rich nations dominate the top of the ranking.
    Among large economies, Germany and the United Kingdom stand out —
    both highlighted in the chart below.
    """)
    return


@app.cell
def rank_data(conn):
    _EXCL = ", ".join([
        "'World'", "'Africa'", "'Asia'", "'Europe'",
        "'North America'", "'South America'", "'Oceania'",
        "'European Union (27)'", "'High-income countries'",
        "'Upper-middle-income countries'", "'Lower-middle-income countries'",
        "'Low-income countries'", "'OECD'", "'Non-OECD'",
        "'Asia Pacific'", "'CIS'", "'Middle East'",
        "'Other Africa'", "'Other Asia & Pacific'",
        "'Other CIS'", "'Other Europe'", "'Other Middle East'",
    ])
    _sql = f"""
        SELECT country,
               ROUND(
                   100.0 * COALESCE(renewables_electricity, 0)
                   / NULLIF(electricity_generation, 0),
               1) AS renewable_pct
        FROM energy.world_energy
        WHERE year = 2022
          AND electricity_generation >= 10
          AND country NOT IN ({_EXCL})
          AND renewables_electricity IS NOT NULL
        ORDER BY renewable_pct DESC
        LIMIT 20
    """
    df_rank = conn.sql(_sql).df().dropna()
    rank_labels = df_rank["country"].tolist()
    rank_values = df_rank["renewable_pct"].tolist()
    # Highlight the large economies featured throughout the notebook
    rank_highlight = [
        i for i, c in enumerate(rank_labels)
        if c in {"United States", "Germany", "United Kingdom", "China", "France", "India"}
    ]
    return rank_highlight, rank_labels, rank_values


@app.cell
def rank_chart(
    CATEGORICAL,
    COLORS,
    horizontal_bar_ranking,
    rank_highlight,
    rank_labels,
    rank_values,
):
    top_20_fig_rank = horizontal_bar_ranking(
        rank_labels,
        rank_values,
        title="Top 20 Countries by Renewable Electricity Share, 2022 (%)",
        xlabel="Renewable share of electricity generation (%)",
        color=CATEGORICAL[0],
        highlight_indices=rank_highlight,
        highlight_color=COLORS["accent"],
        figsize=(10, 8),
    )
    top_20_fig_rank
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## US Wind Turbine Installations

    A stratified sample from the USGS Wind Turbine Database, coloured by rated capacity.
    The Great Plains wind corridor (Texas through the Dakotas) is unmistakable;
    offshore projects appear along the East Coast.

    | Colour | Capacity tier |
    |--------|--------------|
    | Gold | < 1 MW (older / small turbines) |
    | Teal | 1 – 2.5 MW (standard utility-scale) |
    | Red | ≥ 2.5 MW (modern large-rotor turbines) |
    """)
    return


@app.cell
def map_data(COLORS, FUEL_COLORS, conn, mpatches):
    _sql = """
        SELECT ylat AS lat, xlong AS lon, t_cap AS capacity_kw
        FROM energy.wind_turbines
        WHERE ylat  BETWEEN 24 AND 50
          AND xlong BETWEEN -125 AND -66
          AND t_cap IS NOT NULL
    """
    df_turbines = conn.sql(_sql).df()

    _c_small = FUEL_COLORS["solar"]    # gold  — < 1 MW
    _c_mid   = FUEL_COLORS["wind"]     # teal  — 1–2.5 MW
    _c_large = COLORS["negative"]      # red   — >= 2.5 MW

    _cap   = df_turbines["capacity_kw"]
    _small = _cap < 1000
    _mid   = (_cap >= 1000) & (_cap < 2500)

    map_lats   = df_turbines["lat"].tolist()
    map_lons   = df_turbines["lon"].tolist()
    map_colors = [
        _c_small if s else (_c_mid if m else _c_large)
        for s, m in zip(_small, _mid)
    ]
    map_sizes = [
        18 if c < 1000 else (32 if c < 2500 else 52)
        for c in _cap
    ]
    map_handles = [
        mpatches.Patch(color=_c_small, label="< 1 MW"),
        mpatches.Patch(color=_c_mid,   label="1 – 2.5 MW"),
        mpatches.Patch(color=_c_large, label=">= 2.5 MW"),
    ]
    return map_colors, map_handles, map_lats, map_lons, map_sizes


@app.cell
def map_chart(
    map_colors,
    map_handles,
    map_lats,
    map_lons,
    map_sizes,
    us_scatter_map,
):
    wind_cap_fig_map = us_scatter_map(
        lats=map_lats,
        lons=map_lons,
        colors=map_colors,
        sizes=map_sizes,
        title="US Wind Turbines by Rated Capacity — USGS Database (stratified sample)",
        legend_handles=map_handles,
        figsize=(14, 8),
        alpha=0.55,
    )
    wind_cap_fig_map
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
