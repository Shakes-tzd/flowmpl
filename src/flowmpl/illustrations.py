"""AI-generated whiteboard illustrations via Gemini.

Converts a narrative description into a whiteboard-style sketch PNG using
Google's Gemini image-generation model.  Uses a **hybrid prompt** strategy:
the caller supplies the *story* the image must convey plus an optional list
of *concrete visual objects* to draw from; the model decides what to keep and
how to compose the scene.

This approach was found to produce significantly better results than either:
  - Element-by-element layout specs (model ignores the story)
  - Story-only prompts (model invents arbitrary metaphors)

Optional dependency: ``google-genai>=1.0``

    uv pip install flowmpl[gemini]    # or: pip install flowmpl[gemini]

API-key resolution order (first match wins):

1. ``api_key`` parameter
2. ``GEMINI_API_KEY`` environment variable
3. ``NANOBANANA_GEMINI_API_KEY`` environment variable
4. ``~/DevProjects/Systems/.env`` file (``KEY=value`` format)

Usage
-----
::

    from flowmpl.illustrations import generate_illustration

    generate_illustration(
        story=\"\"\"
            When compute gets dramatically cheaper people use far more of it
            and total spending rises.  Price fell 97 % in 14 months; total
            infrastructure spend kept climbing.  The Jevons paradox —
            originally observed with Victorian coal and steam engines.
        \"\"\",
        vocabulary=[
            "price tag with bold downward arrow",
            "stack of server towers with upward arrow",
            "Victorian steam engine silhouette in background",
            "large question mark at the centre",
        ],
        out_path="notebooks/assets/jevons.png",
    )

Batch usage::

    from flowmpl.illustrations import generate_illustrations

    specs = [
        dict(label="jevons",   story="...", vocabulary=[...], out_path="..."),
        dict(label="capex_gap", story="...", vocabulary=[...], out_path="..."),
    ]
    paths = generate_illustrations(specs)
"""

from __future__ import annotations

import io
import os
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_MODEL = "gemini-2.0-flash-exp-image-generation"

_STYLE_INSTRUCTIONS: dict[str, str] = {
    "whiteboard": (
        "Whiteboard-style illustration. "
        "Black ink on cream/off-white paper. "
        "Hand-drawn sketch aesthetic. "
        "Sparse, analytical, confident ink strokes. "
        "ABSOLUTELY NO words, letters, numbers, or text of any kind anywhere in the image. "
        "Pure visual composition only."
    ),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_api_key(api_key: str | None) -> str:
    """Resolve Gemini API key from parameter, env, or .env file."""
    if api_key:
        return api_key
    key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("NANOBANANA_GEMINI_API_KEY")
    )
    if not key:
        env_file = Path.home() / "DevProjects" / "Systems" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip("'\"")
                if k in ("GEMINI_API_KEY", "NANOBANANA_GEMINI_API_KEY"):
                    key = v
                    break
    if not key:
        raise RuntimeError(
            "No Gemini API key found.  Set GEMINI_API_KEY in the environment "
            "or pass api_key= to generate_illustration()."
        )
    return key


def _build_prompt(
    story: str,
    vocabulary: list[str] | None,
    style: str,
) -> str:
    """Compose the full hybrid prompt from story, vocabulary, and style."""
    style_block = _STYLE_INSTRUCTIONS.get(style)
    if style_block is None:
        raise ValueError(
            f"Unknown illustration style {style!r}.  "
            f"Available: {list(_STYLE_INSTRUCTIONS)}"
        )

    parts = [style_block, "", story.strip()]

    if vocabulary:
        items = "\n".join(f"- {v}" for v in vocabulary)
        parts += [
            "",
            "Visual vocabulary you may draw from (use what serves the story, "
            "invent freely beyond this list):",
            items,
        ]

    parts += [
        "",
        "CRITICAL: Zero text. Zero labels. Zero captions. "
        "Concrete objects and clear composition only.",
    ]
    return "\n".join(parts)


def _call_gemini(
    prompt: str,
    out_path: Path,
    model: str,
    api_key: str,
) -> None:
    """Call Gemini image generation and write PNG to out_path."""
    try:
        from google import genai  # noqa: PLC0415
        from google.genai import types  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "google-genai is required for illustrations.\n"
            "Install via: uv pip install flowmpl[gemini]"
        ) from exc

    client = genai.Client(api_key=api_key)
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    config = types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])

    for chunk in client.models.generate_content_stream(
        model=model, contents=contents, config=config
    ):
        if chunk.parts is None:
            continue
        part = chunk.parts[0]
        if part.inline_data and part.inline_data.data:
            import mimetypes  # noqa: PLC0415
            ext = mimetypes.guess_extension(part.inline_data.mime_type) or ".png"
            tmp = out_path.with_suffix(ext)
            tmp.write_bytes(part.inline_data.data)
            if tmp != out_path:
                shutil.move(str(tmp), str(out_path))
            return

    raise RuntimeError(
        f"Gemini returned no image for model={model!r}.  "
        "The model may have declined the prompt or returned text only."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_illustration(
    story: str,
    *,
    vocabulary: list[str] | None = None,
    out_path: str | Path | None = None,
    style: str = "whiteboard",
    model: str = _DEFAULT_MODEL,
    api_key: str | None = None,
    delay: float = 0.0,
) -> bytes:
    """Generate a single whiteboard-style illustration via Gemini.

    Parameters
    ----------
    story:
        Narrative description of what the image must communicate.  Write this
        as a paragraph explaining the *analytical idea* — not a list of visual
        elements.  The model performs best when it understands the story first.
    vocabulary:
        Optional list of concrete visual objects (e.g. ``["price tag with
        downward arrow", "stack of servers"]``) the model may draw from.
        These are suggestions, not requirements — the model selects what serves
        the composition.
    out_path:
        Where to write the PNG.  Parent directories are created automatically.
        If ``None``, the raw PNG bytes are returned but nothing is written.
    style:
        Visual style preset.  Currently only ``"whiteboard"`` is supported.
    model:
        Gemini model name.  Default: ``gemini-2.0-flash-exp-image-generation``.
    api_key:
        Gemini API key.  If omitted, resolved from environment / .env file.
    delay:
        Seconds to sleep after the call (useful when calling in a loop to
        respect rate limits).

    Returns
    -------
    bytes
        Raw PNG bytes of the generated image.
    """
    resolved_key = _load_api_key(api_key)
    prompt = _build_prompt(story, vocabulary, style)

    # Determine output path
    dest: Path | None = Path(out_path) if out_path is not None else None
    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        _call_gemini(prompt, dest, model, resolved_key)
        if delay > 0:
            time.sleep(delay)
        return dest.read_bytes()

    # No out_path: write to a temp file, read back bytes, delete
    import tempfile  # noqa: PLC0415
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        _call_gemini(prompt, tmp_path, model, resolved_key)
        data = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)
    if delay > 0:
        time.sleep(delay)
    return data


def generate_illustrations(
    specs: list[dict],
    *,
    style: str = "whiteboard",
    model: str = _DEFAULT_MODEL,
    api_key: str | None = None,
    delay: float = 4.0,
) -> list[Path]:
    """Generate multiple illustrations sequentially, respecting rate limits.

    Parameters
    ----------
    specs:
        List of dicts, each with keys:

        * ``story`` (str, required) — narrative description
        * ``out_path`` (str | Path, required) — destination PNG path
        * ``vocabulary`` (list[str], optional) — visual object suggestions
        * ``label`` (str, optional) — human-readable name for progress logging

    style, model, api_key:
        Shared overrides applied to every spec.
    delay:
        Seconds to sleep between requests.  Defaults to 4 s to stay within
        Gemini free-tier rate limits.

    Returns
    -------
    list[Path]
        Resolved paths of the written PNG files (same order as specs).
    """
    resolved_key = _load_api_key(api_key)
    results: list[Path] = []

    for i, spec in enumerate(specs):
        label = spec.get("label") or f"illustration {i + 1}/{len(specs)}"
        story = spec["story"]
        vocab = spec.get("vocabulary")
        dest = Path(spec["out_path"])

        print(f"[{label}] generating…")
        generate_illustration(
            story,
            vocabulary=vocab,
            out_path=dest,
            style=style,
            model=model,
            api_key=resolved_key,
            delay=delay if i < len(specs) - 1 else 0.0,
        )
        print(f"  ✓ {dest}")
        results.append(dest)

    return results


# ---------------------------------------------------------------------------
# Post-processing: background removal
# ---------------------------------------------------------------------------

def remove_background(
    img: Path | bytes,
    *,
    lo: int = 30,
    hi: int = 225,
) -> bytes:
    """Remove the light background from a whiteboard-style PNG.

    Applies a luminance-based soft alpha mask: dark ink strokes become fully
    opaque, the cream/white background becomes fully transparent, and
    anti-aliased edges receive partial transparency for clean compositing.

    Parameters
    ----------
    img:
        Source image as a file path or raw PNG bytes.
    lo:
        Luminance threshold below which pixels are fully opaque (ink). 0–255.
    hi:
        Luminance threshold above which pixels are fully transparent (bg). 0–255.

    Returns
    -------
    bytes
        PNG bytes with an alpha channel (RGBA).  The light background is
        transparent; ink strokes retain their full opacity.
    """
    try:
        import numpy as np  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "Pillow is required for remove_background.\n"
            "Install via: uv pip install flowmpl[gemini]"
        ) from exc

    if isinstance(img, (str, Path)):
        pil = Image.open(img).convert("RGBA")
    else:
        pil = Image.open(io.BytesIO(img)).convert("RGBA")

    data = np.array(pil, dtype=np.float32)
    r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b

    # Soft mask: lum<=lo → alpha=255, lum>=hi → alpha=0, linear between
    span = float(hi - lo)
    alpha = np.clip((hi - lum) / span * 255.0, 0.0, 255.0).astype(np.uint8)
    data[:, :, 3] = alpha

    out = Image.fromarray(data.astype(np.uint8), mode="RGBA")
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Post-processing: annotation compositing
# ---------------------------------------------------------------------------

def annotate_illustration(
    img: Path | bytes,
    annotations: list[dict],
    *,
    out_path: str | Path | None = None,
    figsize: tuple[float, float] | None = None,
    bg_color: str | None = None,
    dpi: int = 150,
) -> bytes:
    """Composite a (transparent) illustration with matplotlib text annotations.

    Renders the sketch image on a matplotlib figure and overlays analytical
    callout text using the flowmpl design system typography.

    Parameters
    ----------
    img:
        Source image — file path or raw bytes.  Pass the output of
        :func:`remove_background` to get clean transparent-background compositing.
    annotations:
        List of annotation dicts.  Each dict supports:

        * ``text`` (str) — annotation text; ``\\n`` for line breaks
        * ``xy`` (tuple[float, float]) — text anchor in axes-fraction coords (0–1)
        * ``target`` (tuple[float, float] | None) — arrow tip in axes-fraction;
          when set, draws a thin connecting arrow from text to target
        * ``color`` (str) — hex color; defaults to ``COLORS["text_light"]``
        * ``fontsize`` (int) — defaults to ``FONTS["annotation"]`` (14)
        * ``ha`` (str) — horizontal alignment; default ``"left"``
        * ``va`` (str) — vertical alignment; default ``"center"``
        * ``style`` (str) — ``"plain"`` (default) or ``"box"`` (rounded bbox)

    out_path:
        Where to write the final PNG.  Parent dirs created automatically.
        If ``None``, raw PNG bytes are returned but nothing is written to disk.
    figsize:
        Figure size in inches.  Inferred from image aspect ratio when ``None``.
    bg_color:
        Background hex color (e.g. ``"#f5f1eb"`` for cream).  ``None`` → white.
    dpi:
        Output resolution.  Default 150.

    Returns
    -------
    bytes
        PNG bytes of the composited figure.
    """
    try:
        import numpy as np  # noqa: PLC0415
        from PIL import Image as _PILImage  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "Pillow is required for annotate_illustration.\n"
            "Install via: uv pip install flowmpl[gemini]"
        ) from exc

    import matplotlib.pyplot as plt  # noqa: PLC0415

    from flowmpl.design import COLORS, FONTS, PAPER  # noqa: PLC0415

    # Load image
    if isinstance(img, (str, Path)):
        pil = _PILImage.open(img).convert("RGBA")
    else:
        pil = _PILImage.open(io.BytesIO(img)).convert("RGBA")

    img_array = np.array(pil)
    h, w = img_array.shape[:2]

    if figsize is None:
        figsize = (10.0, 10.0 * h / w)

    fig, ax = plt.subplots(figsize=figsize)

    # Background
    fig.patch.set_facecolor(bg_color if bg_color else PAPER)
    ax.set_facecolor(bg_color if bg_color else PAPER)

    ax.imshow(img_array, aspect="auto", interpolation="antialiased")
    ax.set_axis_off()

    # Annotation defaults
    default_color = COLORS["text_dark"]
    default_fs = FONTS["annotation"]

    for ann in annotations:
        text = ann["text"]
        xy = ann["xy"]                          # text position, axes-fraction
        target = ann.get("target")              # arrow tip, axes-fraction (optional)
        color = ann.get("color", default_color)
        fs = ann.get("fontsize", default_fs)
        ha = ann.get("ha", "left")
        va = ann.get("va", "center")
        style = ann.get("style", "plain")

        bbox_props = None
        if style == "box":
            bbox_props = {
                "boxstyle": "round,pad=0.35",
                "fc": PAPER,
                "ec": color,
                "alpha": 0.88,
                "linewidth": 0.8,
            }

        if target is not None:
            ax.annotate(
                text,
                xy=target,
                xytext=xy,
                xycoords="axes fraction",
                textcoords="axes fraction",
                fontsize=fs,
                color=color,
                ha=ha,
                va=va,
                bbox=bbox_props,
                arrowprops={
                    "arrowstyle": "->",
                    "color": color,
                    "lw": 1.2,
                    "connectionstyle": "arc3,rad=0.0",
                },
            )
        else:
            ax.text(
                xy[0], xy[1], text,
                transform=ax.transAxes,
                fontsize=fs,
                color=color,
                ha=ha,
                va=va,
                bbox=bbox_props,
                linespacing=1.5,
            )

    plt.tight_layout(pad=0.3)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    data = buf.read()

    if out_path is not None:
        dest = Path(out_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    return data
