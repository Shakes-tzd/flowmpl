"""Domain color palettes and lookup helpers.

Includes energy infrastructure fuel types, hyperscaler company colors
(redistributed across distinct hue bands for chart legibility), and a
general-purpose colorblind-safe categorical palette (Paul Tol).
"""

from __future__ import annotations

from flowmpl.design import COLORS

# ───────────────────────────────────────────────────────────────────────────
# Energy infrastructure — fuel / generation types
# ───────────────────────────────────────────────────────────────────────────

FUEL_COLORS: dict[str, str] = {
    "solar":       "#f0b429",
    "wind":        "#4ecdc4",
    "battery":     "#7b68ee",
    "gas_cc":      "#e74c3c",
    "gas_ct":      "#ff8c69",
    "nuclear":     "#3498db",
    "hydro":       "#2ecc71",
    "coal":        "#555555",
    "biomass":     "#8c564b",
    "geothermal":  "#d4a574",
    "other":       "#bbbbbb",
}


# ───────────────────────────────────────────────────────────────────────────
# Hyperscaler company colors
#
# Brand colors for MSFT / GOOGL / META are all blue, making them
# indistinguishable in charts. Colors are redistributed across hue bands
# using each company's secondary brand palette:
#   MSFT  = sky blue  (primary brand)
#   AMZN  = orange    (primary brand)
#   GOOGL = forest green (from the four-color Google logo)
#   META  = purple    (metaverse/VR branding)
#   NVDA  = lime green (primary brand)
#   ORCL  = red       (primary brand)
#   AAPL  = dark grey (primary brand)
#   TSLA  = Tesla red
# ───────────────────────────────────────────────────────────────────────────

COMPANY_COLORS: dict[str, str] = {
    "MSFT":  "#00a4ef",   # sky blue
    "AMZN":  "#ff9900",   # orange
    "GOOGL": "#34a853",   # Google green
    "META":  "#7b1fa2",   # purple
    "NVDA":  "#76b900",   # lime green
    "ORCL":  "#ea4335",   # red
    "AAPL":  "#555555",   # dark grey
    "TSLA":  "#cc0000",   # Tesla red
}

COMPANY_LABELS: dict[str, str] = {
    "MSFT":  "Microsoft",
    "AMZN":  "Amazon",
    "GOOGL": "Alphabet",
    "META":  "Meta",
    "NVDA":  "Nvidia",
    "ORCL":  "Oracle",
    "AAPL":  "Apple",
    "TSLA":  "Tesla",
}


# ───────────────────────────────────────────────────────────────────────────
# Categorical palette — colorblind-safe (Paul Tol qualitative scheme)
# Use for arbitrary series when no semantic mapping applies.
# ───────────────────────────────────────────────────────────────────────────

CATEGORICAL: list[str] = [
    "#4477AA",   # blue
    "#EE6677",   # red
    "#228833",   # green
    "#CCBB44",   # yellow
    "#66CCEE",   # cyan
    "#AA3377",   # purple
    "#BBBBBB",   # grey
    "#EE8866",   # orange
]


# ───────────────────────────────────────────────────────────────────────────
# Lookup helpers
# ───────────────────────────────────────────────────────────────────────────

def fuel_color(fuel_type: str) -> str:
    """Return color for a fuel/generation type, with graceful fallback."""
    return FUEL_COLORS.get(fuel_type, COLORS["muted"])


def company_color(ticker: str) -> str:
    """Return brand color for a company ticker, with graceful fallback."""
    return COMPANY_COLORS.get(ticker, COLORS["muted"])


def company_label(ticker: str) -> str:
    """Return display name for a company ticker."""
    return COMPANY_LABELS.get(ticker, ticker)
