"""Flow diagram renderer — stocks-and-flows / causal-chain node-edge charts.

Nodes are auto-sized to their text labels (no manual width/height tuning).
Edges use a compass-sector routing heuristic with explicit face-override support
for cases where geometry alone would misclassify the connection.

Routing heuristic (direction from src → dst):
  |vy| < 0.25|vx|  →  near-horizontal (E/W):   straight line, side faces
  |vx| < 0.25|vy|  →  near-vertical   (N/S):   straight line, top/bottom faces
  |vy| < 0.75|vx|  →  primarily horizontal:     EXIT top/bottom, land side face (elbow)
  else             →  primarily vertical/steep:  EXIT side, land top/bottom face (elbow)

When multiple edges share the same source or destination face they are spread
symmetrically along that face to avoid arrowhead stacking.
"""

from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from flowmpl.design import COLORS, CONTEXT
from flowmpl.helpers import chart_title, legend_below


def flow_diagram(
    nodes: dict[str, tuple[str, float, float, str, str]],
    edges: list[dict],
    *,
    figsize: tuple[float, float] = (18, 6),
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    font_size: int | None = None,
    edge_font_size: int | None = None,
    pad: float = 0.2,
    box_pad: float = 0.1,
    corner_radius: float = 0.4,
    legend_handles: list | None = None,
    legend_ncol: int | None = None,
    max_autoscale: float | None = 1.5,
    title: str | None = None,
) -> plt.Figure:
    """Draw a stocks-and-flows style flow diagram with auto-sized rounded nodes.

    Nodes are sized to exactly contain their text labels by measuring actual
    rendered text extents — no manual width/height tuning required.

    Parameters
    ----------
    nodes : dict[str, tuple]
        Mapping of ``node_key → (label, cx, cy, fill_color, text_color)``.
        ``cx``, ``cy`` are node centre coordinates in data units.
    edges : list[dict]
        Each dict must have ``src`` and ``dst`` (node keys) and may include:

        - ``label`` (str): text shown at the midpoint of the arrow
        - ``dashed`` (bool): dashed linestyle (default ``False``)
        - ``curve`` (float): ``arc3`` radius; positive bows left of direction,
          negative bows right (default ``0``)
        - ``color`` (str): override color for arrow and label
        - ``exit`` (str): override which face the arrow exits from —
          ``"top"``, ``"bottom"``, ``"left"``, or ``"right"``. When set,
          bypasses the direction-ratio heuristic for the source end.
        - ``entry`` (str): override which face the arrow arrives at — same
          values as ``exit``. Use together with ``exit`` to force elbow
          routing when geometry alone would misclassify the connection.

    figsize : tuple[float, float]
        Figure size in inches. Default ``(18, 6)``.
    xlim, ylim : tuple[float, float] or None
        Axis limits. If ``None``, auto-computed from node centres + margin.
    font_size : int or None
        Node label font size. Defaults to 12.
    edge_font_size : int or None
        Edge label font size. Defaults to 11.
    pad : float
        Padding (data units) added around measured text extent (default 0.2).
    box_pad : float
        ``FancyBboxPatch`` ``pad`` — controls corner rounding (default 0.1).
    corner_radius : float
        Radius of the rounded elbow corner for primarily-horizontal /
        primarily-vertical arrows, in data units (default 0.4). Converted to
        display units at draw time.
    legend_handles : list or None
        If provided, passed to ``legend_below()``.
    legend_ncol : int or None
        Legend column count. Defaults to ``len(legend_handles)``.
    max_autoscale : float or None
        Cap on how much the auto-spacing is allowed to grow the node y-range.
        A value of 1.5 means the total y-range may expand by at most 50% of
        its original size. Set to ``None`` to disable the cap.

    Returns
    -------
    matplotlib.figure.Figure
        Pass to ``save_fig(fig, path)`` and display with ``mo.image()``.

    Examples
    --------
    >>> nodes = {
    ...     "a": ("Source\\nNode", 1.0, 0.0, CONTEXT, COLORS["text_dark"]),
    ...     "b": ("Target\\nNode", 5.0, 0.0, COLORS["negative"], "#fff"),
    ... }
    >>> edges = [{"src": "a", "dst": "b", "label": "flows to"}]
    >>> fig = flow_diagram(nodes, edges)
    """
    from flowmpl.design import FLOW_EDGE_FONT_SIZE, FONTS  # local to avoid circular at module level

    _fs = font_size if font_size is not None else FONTS["annotation"] - 2
    _efs = edge_font_size if edge_font_size is not None else FLOW_EDGE_FONT_SIZE

    fig, ax = plt.subplots(figsize=figsize)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.12)

    if xlim is None:
        xs = [v[1] for v in nodes.values()]
        xlim = (min(xs) - 3.0, max(xs) + 3.0)
    if ylim is None:
        ys = [v[2] for v in nodes.values()]
        ylim = (min(ys) - 1.2, max(ys) + 1.2)

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")

    # Pass 1 — draw text invisibly to measure real pixel extents
    _txt: dict[str, plt.Text] = {}
    for k, (lbl, cx, cy, _fc, tc) in nodes.items():
        _txt[k] = ax.text(
            cx, cy, lbl, ha="center", va="center",
            fontsize=_fs, fontweight="bold", linespacing=1.35,
            color=tc, alpha=0, zorder=4,
        )
    fig.canvas.draw()
    _ren = fig.canvas.get_renderer()
    _inv = ax.transData.inverted()

    # Convert each text's pixel bbox → data-coord half-widths / half-heights
    _hw: dict[str, float] = {}
    _hh: dict[str, float] = {}
    for k, t in _txt.items():
        bb = t.get_window_extent(renderer=_ren)
        p0 = _inv.transform((bb.x0, bb.y0))
        p1 = _inv.transform((bb.x1, bb.y1))
        _hw[k] = abs(p1[0] - p0[0]) / 2 + pad
        _hh[k] = abs(p1[1] - p0[1]) / 2 + pad

    # Normalize widths within each x-column so aligned nodes look uniform
    _col_keys: dict[float, list[str]] = {}
    for k, (_, cx, _, _, _) in nodes.items():
        _col_keys.setdefault(round(cx, 6), []).append(k)
    for _keys in _col_keys.values():
        _max_hw = max(_hw[k] for k in _keys)
        for k in _keys:
            _hw[k] = _max_hw

    # ---- Auto-space tiers (edge-aware) ----
    _ys_all = sorted(set(round(v[2], 6) for v in nodes.values()))
    if len(_ys_all) > 1:
        _dpu_y = (ylim[1] - ylim[0]) / figsize[1]
        _lbl_clearance = (_efs / 72) * _dpu_y * 3.0 + 0.5

        _elhh: dict[int, float] = {}
        for _ei, _e in enumerate(edges):
            _elbl = _e.get("label", "")
            if _elbl:
                _enl = _elbl.count("\n") + 1
                _elhh[_ei] = _enl * (_efs / 72) * _dpu_y * 1.35 / 2 + 0.05

        _new_y: dict[float, float] = {_ys_all[0]: _ys_all[0]}
        _y_changed = False
        for _ti in range(1, len(_ys_all)):
            _y_lo, _y_hi = _ys_all[_ti - 1], _ys_all[_ti]
            _lo_nds = [k for k in nodes if round(nodes[k][2], 6) == _y_lo]
            _hi_nds = [k for k in nodes if round(nodes[k][2], 6) == _y_hi]
            _req = (max(_hh[k] for k in _hi_nds)
                    + max(_hh[k] for k in _lo_nds)
                    + _lbl_clearance)

            for _ei, _e in enumerate(edges):
                _es, _ed = _e["src"], _e["dst"]
                _esy = round(nodes[_es][2], 6)
                _edy = round(nodes[_ed][2], 6)
                _crosses = (
                    (_esy == _y_lo and _edy == _y_hi)
                    or (_esy == _y_hi and _edy == _y_lo)
                )
                if not _crosses or _ei not in _elhh:
                    continue
                _evx = nodes[_ed][1] - nodes[_es][1]
                _evy = nodes[_ed][2] - nodes[_es][2]
                _fe = _e.get("exit")
                _fn = _e.get("entry")
                _near_vert = (
                    _fe is None and _fn is None
                    and abs(_evy) > 1e-9
                    and abs(_evx) < abs(_evy) * 0.25
                )
                _prim_vert = (
                    (_fe in ("top", "bottom") and _fn in ("left", "right"))
                    or (
                        _fe is None and _fn is None
                        and not _near_vert
                        and abs(_evx) > 1e-9
                        and abs(_evy) >= abs(_evx) * 0.75
                    )
                )
                if not (_near_vert or _prim_vert):
                    continue
                _src_k = _es if _esy == _y_hi else _ed
                _dst_k = _ed if _esy == _y_hi else _es
                if _near_vert:
                    _e_req = _hh[_src_k] + _hh[_dst_k] + 2 * _elhh[_ei] + 0.6
                else:
                    _e_req = _hh[_src_k] + 2 * _hh[_dst_k] + 2 * _elhh[_ei] + 0.2
                _req = max(_req, _e_req)

            _placed = _new_y[_y_lo] + max(_y_hi - _y_lo, _req)
            _new_y[_y_hi] = _placed
            if abs(_placed - _y_hi) > 1e-9:
                _y_changed = True

        # Cap total expansion
        if max_autoscale is not None and len(_ys_all) > 1:
            _orig_range = _ys_all[-1] - _ys_all[0]
            if _orig_range > 1e-9:
                _total_shift = _new_y[_ys_all[-1]] - _ys_all[-1]
                _max_shift = _orig_range * (max_autoscale - 1.0)
                if _total_shift > _max_shift:
                    _sf = _max_shift / _total_shift if _total_shift > 0 else 0.0
                    _new_y = {_y: _y + (_new_y[_y] - _y) * _sf for _y in _ys_all}
                    _y_changed = any(abs(_new_y[_y] - _y) > 1e-9 for _y in _ys_all)

        if _y_changed:
            _shift = _new_y[_ys_all[-1]] - _ys_all[-1]
            _old_y_range = ylim[1] - ylim[0]
            _new_y_range = _old_y_range + _shift
            _y_scale = _new_y_range / _old_y_range
            ylim = (ylim[0], ylim[0] + _new_y_range)
            figsize = (figsize[0], figsize[1] * _y_scale)
            fig.set_size_inches(*figsize)
            ax.set_ylim(*ylim)
            nodes = {
                k: (v[0], v[1], _new_y[round(v[2], 6)], v[3], v[4])
                for k, v in nodes.items()
            }
            for k, _t in _txt.items():
                _t.set_position((nodes[k][1], nodes[k][2]))

    # Convert corner_radius from data units to display units
    _t0 = ax.transData.transform((0.0, 0.0))
    _t1 = ax.transData.transform((corner_radius, 0.0))
    _rad_px = float(abs(_t1[0] - _t0[0]))

    # Pass 2 — draw boxes behind text, then make text visible
    for k, (_lbl, cx, cy, fc, _tc) in nodes.items():
        ec = CONTEXT if fc == COLORS["background"] else "none"
        lw = 1.2 if fc == COLORS["background"] else 0
        ax.add_patch(mpatches.FancyBboxPatch(
            (cx - _hw[k], cy - _hh[k]),
            2 * _hw[k], 2 * _hh[k],
            boxstyle=f"round,pad={box_pad}",
            facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3,
        ))
        _txt[k].set_alpha(1.0)

    # ---- Pass 1: compute compass-based routing for every edge ----
    _tip = box_pad + 0.01
    _routes: list[dict] = []
    for edge in edges:
        src = edge["src"]
        dst = edge["dst"]
        sx, sy = nodes[src][1], nodes[src][2]
        dx, dy = nodes[dst][1], nodes[dst][2]
        vx, vy = dx - sx, dy - sy
        x1, y1 = sx, sy

        _forced_exit = edge.get("exit")
        _forced_entry = edge.get("entry")
        _face_angle = {"right": 0, "left": 180, "top": 90, "bottom": -90}

        if abs(vy) < abs(vx) * 0.25:
            # Near-horizontal: straight, side faces
            if vx >= 0:
                x2, y2 = dx - _hw[dst] - _tip, dy
                _exit_angle = _entry_angle = 0
                _entry_face, _exit_face = "left", "right"
            else:
                x2, y2 = dx + _hw[dst] + _tip, dy
                _exit_angle = _entry_angle = 180
                _entry_face, _exit_face = "right", "left"
        elif abs(vx) < abs(vy) * 0.25:
            # Near-vertical: straight, top/bottom faces
            if vy >= 0:
                x2, y2 = dx, dy - _hh[dst] - _tip
                _exit_angle = _entry_angle = 90
                _entry_face, _exit_face = "bottom", "top"
            else:
                x2, y2 = dx, dy + _hh[dst] + _tip
                _exit_angle = _entry_angle = -90
                _entry_face, _exit_face = "top", "bottom"
        elif abs(vy) < abs(vx) * 0.75:
            # Primarily horizontal: EXIT top/bottom of source, enter side of dest.
            _exit_angle = 90 if vy >= 0 else -90
            _exit_face = "top" if vy >= 0 else "bottom"
            if vx >= 0:
                x2, y2 = dx - _hw[dst] - _tip, dy
                _entry_angle = 0
                _entry_face = "left"
            else:
                x2, y2 = dx + _hw[dst] + _tip, dy
                _entry_angle = 180
                _entry_face = "right"
        else:
            # Primarily vertical: EXIT side of source, enter top/bottom of dest.
            _exit_angle = 0 if vx >= 0 else 180
            _exit_face = "right" if vx >= 0 else "left"
            if vy >= 0:
                x2, y2 = dx, dy - _hh[dst] - _tip
                _entry_angle = 90
                _entry_face = "bottom"
            else:
                x2, y2 = dx, dy + _hh[dst] + _tip
                _entry_angle = -90
                _entry_face = "top"

            # Degenerate elbow: horizontal arm shorter than corner radius
            if abs(x2 - x1) < corner_radius * 1.5:
                if vy >= 0:
                    x2, y2 = dx, dy - _hh[dst] - _tip
                    _exit_angle = _entry_angle = 90
                    _entry_face, _exit_face = "bottom", "top"
                else:
                    x2, y2 = dx, dy + _hh[dst] + _tip
                    _exit_angle = _entry_angle = -90
                    _entry_face, _exit_face = "top", "bottom"

        # Apply single-sided forced face overrides (post-heuristic)
        if _forced_exit is not None:
            _exit_face = _forced_exit
            _exit_angle = _face_angle[_forced_exit]
        if _forced_entry is not None:
            _entry_face = _forced_entry
            _entry_angle = _face_angle[_forced_entry]
            if _forced_entry == "left":
                x2, y2 = dx - _hw[dst] - _tip, dy
            elif _forced_entry == "right":
                x2, y2 = dx + _hw[dst] + _tip, dy
            elif _forced_entry == "top":
                x2, y2 = dx, dy + _hh[dst] + _tip
            else:  # bottom
                x2, y2 = dx, dy - _hh[dst] - _tip

        _routes.append({
            "edge": edge, "src": src, "dst": dst,
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "exit_angle": _exit_angle, "entry_angle": _entry_angle,
            "entry_face": _entry_face, "exit_face": _exit_face,
        })

    # ---- Pass 2: spread arrowheads / tails on shared faces ----
    _entry_buckets: dict[tuple, list[int]] = {}
    _exit_buckets: dict[tuple, list[int]] = {}
    for _i, _r in enumerate(_routes):
        if _r["edge"].get("curve", 0.0) == 0:
            _entry_buckets.setdefault((_r["dst"], _r["entry_face"]), []).append(_i)
            _exit_buckets.setdefault((_r["src"], _r["exit_face"]), []).append(_i)

    for (_nk, _face), _idxs in _entry_buckets.items():
        if len(_idxs) < 2:
            continue
        _n = len(_idxs)
        _ndx, _ndy = nodes[_nk][1], nodes[_nk][2]
        if _face in ("top", "bottom"):
            _idxs.sort(key=lambda _ii: nodes[_routes[_ii]["src"]][1])
            _sp = _hw[_nk] * 0.5
            _y2 = _ndy + _hh[_nk] + _tip if _face == "top" else _ndy - _hh[_nk] - _tip
            for _k, _ii in enumerate(_idxs):
                _routes[_ii]["x2"] = _ndx - _sp + 2 * _sp * _k / (_n - 1)
                _routes[_ii]["y2"] = _y2
        else:
            _idxs.sort(key=lambda _ii: nodes[_routes[_ii]["src"]][2], reverse=True)
            _sp = _hh[_nk] * 0.5
            _x2 = _ndx - _hw[_nk] - _tip if _face == "left" else _ndx + _hw[_nk] + _tip
            for _k, _ii in enumerate(_idxs):
                _routes[_ii]["x2"] = _x2
                _routes[_ii]["y2"] = _ndy + _sp - 2 * _sp * _k / (_n - 1)

    for (_nk, _face), _idxs in _exit_buckets.items():
        if len(_idxs) < 2:
            continue
        _n = len(_idxs)
        _nsx, _nsy = nodes[_nk][1], nodes[_nk][2]
        if _face in ("top", "bottom"):
            _idxs.sort(key=lambda _ii: nodes[_routes[_ii]["dst"]][1])
            _sp = _hw[_nk] * 0.5
            for _k, _ii in enumerate(_idxs):
                _routes[_ii]["x1"] = _nsx - _sp + 2 * _sp * _k / (_n - 1)
        else:
            _idxs.sort(key=lambda _ii: nodes[_routes[_ii]["dst"]][2], reverse=True)
            _sp = _hh[_nk] * 0.5
            for _k, _ii in enumerate(_idxs):
                _routes[_ii]["y1"] = _nsy + _sp - 2 * _sp * _k / (_n - 1)

    # ---- Pass 3: draw all edges ----
    for _r in _routes:
        edge = _r["edge"]
        src, dst = _r["src"], _r["dst"]
        lbl = edge.get("label", "")
        dashed = edge.get("dashed", False)
        curve = edge.get("curve", 0.0)
        color = edge.get("color", COLORS["text_dark"])
        x1, y1 = _r["x1"], _r["y1"]
        x2, y2 = _r["x2"], _r["y2"]
        _exit_angle = _r["exit_angle"]
        _entry_angle = _r["entry_angle"]

        _parallel = (_exit_angle == _entry_angle) or (abs(_exit_angle - _entry_angle) == 180)
        if curve != 0:
            _conn = f"arc3,rad={curve}"
        elif _parallel:
            _conn = "arc3,rad=0"
        else:
            _conn = f"angle,angleA={_exit_angle},angleB={_entry_angle},rad={_rad_px:.0f}"

        ax.annotate(
            "",
            xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=1.8,
                linestyle="--" if dashed else "solid",
                connectionstyle=_conn,
                mutation_scale=14,
            ),
            zorder=2,
        )
        if lbl:
            if not _parallel and curve == 0:
                if abs(_exit_angle) in (0, 180):
                    _fx = x1 + _hw[src] if _exit_angle == 0 else x1 - _hw[src]
                    _vis_h = abs(x2 - _fx)
                    _vis_v = abs(y2 - y1)
                    if _vis_v > _vis_h:
                        mx, my = x2, (y1 + y2) / 2
                    else:
                        mx, my = (_fx + x2) / 2, y1
                else:
                    _fy = y1 + _hh[src] if _exit_angle == 90 else y1 - _hh[src]
                    _vis_v = abs(y2 - _fy)
                    _vis_h = abs(x2 - x1)
                    if _vis_h > _vis_v:
                        mx, my = (x1 + x2) / 2, y2
                    else:
                        mx, my = x1, (_fy + y2) / 2
            else:
                _ef = _r.get("exit_face")
                if _ef == "bottom":
                    _f1x, _f1y = x1, y1 - _hh[src]
                elif _ef == "top":
                    _f1x, _f1y = x1, y1 + _hh[src]
                elif _ef == "right":
                    _f1x, _f1y = x1 + _hw[src], y1
                elif _ef == "left":
                    _f1x, _f1y = x1 - _hw[src], y1
                else:
                    _f1x, _f1y = x1, y1
                if curve != 0:
                    # arc3 label at visual arc midpoint: B(0.5) = 0.25*P0 + 0.5*P1 + 0.25*P2
                    _p0 = np.array([_f1x, _f1y])
                    _p2 = np.array([x2, y2])
                    _chord = _p2 - _p0
                    _chord_len = np.linalg.norm(_chord)
                    _perp = np.array([-_chord[1], _chord[0]]) / (_chord_len + 1e-9)
                    _p1 = (_p0 + _p2) / 2 + curve * _chord_len * _perp
                    _mid = 0.25 * _p0 + 0.5 * _p1 + 0.25 * _p2
                    mx, my = float(_mid[0]), float(_mid[1])
                else:
                    mx, my = (_f1x + x2) / 2, (_f1y + y2) / 2
            ax.text(
                mx, my, lbl, ha="center", va="center",
                fontsize=_efs, fontweight="bold", color=color,
                bbox=dict(
                    boxstyle="round,pad=0.15",
                    fc=COLORS["background"], ec="none", alpha=0.95,
                ),
                zorder=5,
            )

    if legend_handles:
        ncol = legend_ncol if legend_ncol is not None else len(legend_handles)
        legend_below(ax, handles=legend_handles, ncol=ncol, fontsize=_fs)

    if title is not None:
        chart_title(fig, title)

    return fig
