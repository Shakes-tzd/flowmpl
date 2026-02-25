#!/usr/bin/env python3
"""Build sketch icon SVG assets for flowmpl notebook examples.

Workflow per icon
-----------------
1. Generate a pure B&W PNG via Gemini (gemini-3-pro-image-preview), 1:1 aspect ratio.
2. Threshold the PNG to strict binary (Pillow), save as PBM.
3. Trace PBM → SVG via potrace CLI (must be on PATH: ``brew install potrace``).
4. Save PNG + SVG to ``notebooks/assets/icons/``.

The resulting SVGs store paths with ``fill="#000000"``; use
``flowmpl.load_icon(path, color=…)`` at runtime to recolor and rasterise.

Usage
-----
Run from the flowmpl project root::

    # Vectorize existing PNGs only (no Gemini calls):
    uv run --with google-genai notebooks/build_icons.py --vectorize-only

    # Generate fresh B&W PNGs + vectorize (overwrites existing PNGs):
    uv run --with google-genai notebooks/build_icons.py

    # Force regenerate specific icons:
    uv run --with google-genai notebooks/build_icons.py --only bolt solar_panel

API key
-------
Reads ``NANOBANANA_GEMINI_API_KEY`` (or ``GEMINI_API_KEY``) from
``~/DevProjects/Systems/.env`` or the current environment.

Requirements
------------
* ``brew install potrace``  — bitmap-to-SVG tracer
* ``uv pip install google-genai pillow``  — image generation + PIL thresholding
  (google-genai is NOT a flowmpl runtime dep; install separately for this script)
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ICONS_DIR   = Path(__file__).parent / "assets" / "icons"
SYSTEMS_ENV = Path.home() / "DevProjects" / "Systems" / ".env"

# ── Icon definitions: (stem, gemini_prompt) ────────────────────────────────────
# Prompts request pure black ink on pure white — no gray, no texture, no text.
ICONS: list[tuple[str, str]] = [
    (
        "server",
        "Pure black ink line art icon of a rack-mounted server unit with cable ports. "
        "Bold clean outlines only, pure white background, no gray tones, no shading, "
        "no text labels, isolated icon suitable for vectorization.",
    ),
    (
        "cpu",
        "Pure black ink line art icon of a square CPU chip with pins on all sides. "
        "Bold clean outlines only, pure white background, no gray tones, no shading, "
        "no text labels, isolated icon suitable for vectorization.",
    ),
    (
        "database",
        "Pure black ink line art icon of a cylindrical database stack (three stacked disks). "
        "Bold clean outlines only, pure white background, no gray tones, no shading, "
        "no text labels, isolated icon suitable for vectorization.",
    ),
    (
        "moneybag",
        "Pure black ink line art icon of a money bag with a dollar sign on it. "
        "Bold clean outlines only, pure white background, no gray tones, no shading, "
        "no text labels, isolated icon suitable for vectorization.",
    ),
    (
        "coins",
        "Pure black ink line art icon of a stack of round coins. "
        "Bold clean outlines only, pure white background, no gray tones, no shading, "
        "no text labels, isolated icon suitable for vectorization.",
    ),
    (
        "shield",
        "Pure black ink line art icon of a shield with a checkmark inside. "
        "Bold clean outlines only, pure white background, no gray tones, no shading, "
        "no text labels, isolated icon suitable for vectorization.",
    ),
    (
        "factory",
        "Pure black ink line art icon of an industrial factory building with two smokestacks. "
        "Bold clean outlines only, pure white background, no gray tones, no shading, "
        "no text labels, isolated icon suitable for vectorization.",
    ),
    (
        "cloud",
        "Pure black ink line art icon of a cloud shape (fluffy rounded silhouette). "
        "Bold clean outlines only, pure white background, no gray tones, no shading, "
        "no text labels, isolated icon suitable for vectorization.",
    ),
    (
        "bank",
        "Pure black ink line art icon of a government bank or federal building with "
        "large columns and a triangular roof. Bold clean outlines only, pure white "
        "background, no gray tones, no shading, no text labels, isolated icon.",
    ),
    (
        "arrow",
        "Pure black ink line art of a single large thick arrow pointing straight to "
        "the right, horizontal. Bold filled arrow shape with rectangular shaft and "
        "triangular head, pure white background, no gray tones, no shading, no text, "
        "isolated icon suitable for vectorization.",
    ),
    (
        "bolt",
        "Pure black ink line art icon of a lightning bolt. Bold clean outlines only, "
        "pure white background, no gray tones, no shading, no text labels, "
        "isolated icon suitable for vectorization.",
    ),
    (
        "solar_panel",
        "Pure black ink line art icon of a solar panel array (grid of cells). "
        "Bold clean outlines only, pure white background, no gray tones, no shading, "
        "no text labels, isolated icon suitable for vectorization.",
    ),
    (
        "wind_turbine",
        "Pure black ink line art icon of a wind turbine with three blades on a tower. "
        "Bold clean outlines only, pure white background, no gray tones, no shading, "
        "no text labels, isolated icon suitable for vectorization.",
    ),
]


# ── Environment helpers ────────────────────────────────────────────────────────

def _load_env() -> None:
    if SYSTEMS_ENV.exists():
        with open(SYSTEMS_ENV) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip(); v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v


def _get_api_key() -> str:
    key = os.environ.get("NANOBANANA_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("Error: no API key. Set NANOBANANA_GEMINI_API_KEY in .env or environment.")
    return key


# ── Image generation ───────────────────────────────────────────────────────────

def _generate_bw_png(prompt: str, out_path: Path) -> bool:
    """Call Gemini to generate a pure B&W PNG and save to out_path."""
    try:
        from google import genai          # noqa: PLC0415
        from google.genai import types    # noqa: PLC0415
    except ImportError:
        sys.exit(
            "google-genai not installed.\n"
            "Run:  uv run --with google-genai notebooks/build_icons.py"
        )

    client   = genai.Client(api_key=_get_api_key())
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    config   = types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="1:1", image_size="1K"),
        response_modalities=["IMAGE", "TEXT"],
    )

    for chunk in client.models.generate_content_stream(
        model="gemini-3-pro-image-preview",
        contents=contents,
        config=config,
    ):
        if chunk.parts is None:
            continue
        part = chunk.parts[0]
        if part.inline_data and part.inline_data.data:
            import mimetypes  # noqa: PLC0415
            ext = mimetypes.guess_extension(part.inline_data.mime_type) or ".png"
            tmp = out_path.parent / f".tmp_gen{ext}"
            tmp.write_bytes(part.inline_data.data)
            shutil.move(str(tmp), str(out_path))
            return True
        if hasattr(part, "text") and part.text:
            print(f"    model: {part.text}", file=sys.stderr)

    return False


# ── Vectorization ──────────────────────────────────────────────────────────────

def _png_to_svg_potrace(png_path: Path, svg_path: Path, threshold: int = 180) -> None:
    """Threshold PNG to binary and trace to SVG via potrace CLI."""
    from PIL import Image  # noqa: PLC0415

    # Threshold to strict binary — removes paper texture and gray tones
    img = Image.open(png_path).convert("L")
    img = img.point(lambda x: 0 if x < threshold else 255).convert("1")

    pbm_path = png_path.with_suffix(".pbm")
    img.save(str(pbm_path))

    try:
        subprocess.run(
            ["potrace", str(pbm_path), "-s", "-o", str(svg_path), "--tight"],
            check=True,
            capture_output=True,
        )
    finally:
        pbm_path.unlink(missing_ok=True)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build sketch icon SVG assets (Gemini B&W PNG → potrace SVG).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--vectorize-only", action="store_true",
        help="Skip Gemini generation; only (re)vectorize existing PNGs to SVG.",
    )
    parser.add_argument(
        "--only", nargs="+", metavar="STEM",
        help="Process only these icon stems (e.g. bolt solar_panel).",
    )
    parser.add_argument(
        "--threshold", type=int, default=180,
        help="Pixel brightness threshold for B&W conversion (0–255, default 180).",
    )
    args = parser.parse_args()

    if not args.vectorize_only:
        _load_env()

    if shutil.which("potrace") is None:
        sys.exit("potrace not found on PATH.\nInstall:  brew install potrace")

    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    icons = ICONS
    if args.only:
        icons = [(s, p) for s, p in ICONS if s in args.only]
        if not icons:
            sys.exit(f"No icons matched: {args.only}")

    ok = True
    for stem, prompt in icons:
        print(f"\n[{stem}]")
        png_path = ICONS_DIR / f"{stem}.png"
        svg_path = ICONS_DIR / f"{stem}.svg"

        # ── Step 1: Generate PNG ───────────────────────────────────────────
        if args.vectorize_only:
            if not png_path.exists():
                print(f"  SKIP — no PNG at {png_path}", file=sys.stderr)
                ok = False
                continue
            print(f"  Using existing {png_path.name}")
        else:
            print(f"  Generating PNG via Gemini…")
            if not _generate_bw_png(prompt, png_path):
                print(f"  FAILED (Gemini returned no image)", file=sys.stderr)
                ok = False
                continue
            print(f"  Saved {png_path.name}")

        # ── Step 2: Vectorize PNG → SVG ────────────────────────────────────
        print(f"  Vectorizing → {svg_path.name}…")
        try:
            _png_to_svg_potrace(png_path, svg_path, threshold=args.threshold)
            print(f"  OK  ({svg_path.stat().st_size // 1024} KB)")
        except subprocess.CalledProcessError as exc:
            print(f"  potrace failed: {exc.stderr.decode()}", file=sys.stderr)
            ok = False

    print()
    if ok:
        print(f"Done — {len(icons)} icon(s) in {ICONS_DIR}")
    else:
        print("Finished with errors.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
