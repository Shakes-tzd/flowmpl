#!/usr/bin/env python3
"""Ask Gemini to generate the tariff carve-out scene as python-pptx code.

Describes the scene in natural language (colors, icons, chart, arrow) and
lets the model decide on layout/proportions — no exact coordinates given.

The generated code is saved to _gemini_scene.py, executed, and the result
opened.  Compare test_gemini_scene.pptx against test_tariff_scene.pptx to
see how Gemini's interpretation differs from the human-tuned layout.

Usage:
    uv run --with python-pptx --with google-genai notebooks/gemini_generate_scene.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent

# ── API key ────────────────────────────────────────────────────────────────────

def _load_api_key() -> str:
    # Try environment first, then Systems .env
    key = os.environ.get("NANOBANANA_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        env_file = Path.home() / "DevProjects" / "Systems" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip(); v = v.strip().strip("'\"")
                if k in ("NANOBANANA_GEMINI_API_KEY", "GEMINI_API_KEY"):
                    key = v
                    break
    if not key:
        sys.exit("Error: no Gemini API key found. Set GEMINI_API_KEY in environment or Systems/.env")
    return key


# ── Scene description → prompt ─────────────────────────────────────────────────

def _build_prompt() -> str:
    # Resolve icon PNG paths relative to this script
    icons_dir = (HERE / "assets" / "icons").resolve()

    return f"""
You are an expert Python developer using the python-pptx library (version >= 0.6).

Generate a complete, self-contained Python script that creates a PowerPoint slide
representing a "Tariff Carve-Out Policy" analytical scene.

─── SCENE DESCRIPTION ────────────────────────────────────────────────────────

The slide is a visual policy analysis — no text boxes of any kind (no titles,
no labels, no body paragraphs, no callout cards). The design should feel like
a rich infographic that communicates through visual layout alone.

Visual elements to include:

1. BACKGROUND
   Full-slide warm cream fill. Color #F7F3EE.

2. BAR CHART (native editable PPT chart, NOT a picture)
   Clustered column chart. Left-of-center, roughly the left 35% of the slide,
   vertically centered. Two bars:
     - "Pre-Carve-out" : value 150, color #D0D0D0 (light gray)
     - "Post-Carve-out" : value 450, color #F5C842 (yellow)
   No legend. Wide bars (gap_width = 80). No chart border.

3. DIAGONAL ARROW  (block Right Arrow shape, NOT a connector)
   A large, faded, warm-gray block arrow (fill #CCCCAA, no border) pointing
   diagonally from the lower-left area up toward the upper-center-right area.
   It should feel like a background growth motif — big, translucent-feeling,
   sitting behind the icons.

4. ICONS (use add_picture with the PNG files listed below)
   Each icon is a transparent-background PNG on a #F7F3EE slide — they will
   appear naturally on the background without a box around them.
   Do NOT add borders, fills, or shadow to the pictures.

   Place the following icons:
   a. Server (×2): one in a vertical strip at the far left edge of the slide,
      one small instance just above the bar chart
   b. CPU: in the same left vertical strip, below the first server
   c. Database: in the same left vertical strip, below the CPU
   d. Factory: along the bottom of the slide, roughly center-left
   e. Coins: in the center-right area, mid-height
   f. Shield: just below and left of the coins
   g. Cloud: upper-right corner area
   h. Moneybag (×2): near the tip of the diagonal arrow (focal point),
      the two instances slightly offset from each other

   Icon PNG paths (use these exact paths with add_picture):
   - server:   {icons_dir / "server.png"}
   - cpu:      {icons_dir / "cpu.png"}
   - database: {icons_dir / "database.png"}
   - factory:  {icons_dir / "factory.png"}
   - coins:    {icons_dir / "coins.png"}
   - shield:   {icons_dir / "shield.png"}
   - cloud:    {icons_dir / "cloud.png"}
   - moneybag: {icons_dir / "moneybag.png"}

─── TECHNICAL SPECS ──────────────────────────────────────────────────────────

Slide size: 13.333 inches wide × 7.5 inches tall (16:9 widescreen)
Coordinate origin: top-left (standard python-pptx / PowerPoint convention)

Use ONLY these imports:
    from pptx import Presentation
    from pptx.chart.data import ChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Inches, Pt
    from pathlib import Path

Save the output file to:
    {HERE / "test_gemini_scene.pptx"}

─── OUTPUT FORMAT ────────────────────────────────────────────────────────────

Return ONLY the Python code — no markdown fences, no explanations, no comments
beyond what is needed to understand the code. The script must run without
modification using: uv run --with python-pptx <script_path>
""".strip()


# ── Call Gemini ─────────────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> str:
    try:
        from google import genai         # noqa: PLC0415
    except ImportError:
        sys.exit("google-genai not installed.\nRun: uv run --with google-genai ...")

    client = genai.Client(api_key=_load_api_key())

    print("Calling Gemini to generate scene code…")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


# ── Clean code block ────────────────────────────────────────────────────────────

def _extract_code(raw: str) -> str:
    """Strip markdown code fences if present."""
    lines = raw.strip().splitlines()
    # Remove ```python / ``` fences
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────────

def main() -> None:
    prompt = _build_prompt()
    raw    = _call_gemini(prompt)
    code   = _extract_code(raw)

    out_script = HERE / "_gemini_scene.py"
    out_script.write_text(code)
    print(f"Generated code → {out_script}  ({len(code.splitlines())} lines)")

    # Execute the generated script
    print("Running generated code…")
    result = subprocess.run(
        ["uv", "run", "--with", "python-pptx", str(out_script)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("─── STDOUT ───")
        print(result.stdout)
        print("─── STDERR ───")
        print(result.stderr)
        print("\nGenerated code saved to _gemini_scene.py — fix and re-run manually.")
        return

    pptx_out = HERE / "test_gemini_scene.pptx"
    if pptx_out.exists():
        print(f"Saved → {pptx_out}")
        subprocess.run(["open", str(pptx_out)])
    else:
        print("Warning: script ran but PPTX not found.")
        print(result.stdout)


if __name__ == "__main__":
    main()
