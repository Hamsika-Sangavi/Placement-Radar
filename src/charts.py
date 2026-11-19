"""Plotly figure builders. Colours follow one simple rule set:

* blue   = the default series (magnitude)
* orange = the one thing to look at (Hyderabad, the selected role, the gap)
* gray   = context
* heatmaps use a single-hue blue ramp, light to dark
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

BLUE = "#7C5CFC"
ORANGE = "#A78BFA"
GRAY = "#2D2B3D"
INK = "#E8E6F0"
INK_2 = "#8B87A0"
GRID = "#252338"
SURFACE = "#13111C"
BLUE_RAMP = ["#1a1530", "#2d2555", "#4a3d8f", "#7C5CFC", "#B8A5FF"]

FONT = dict(family="DM Sans, -apple-system, Segoe UI, Roboto, sans-serif", size=13, color=INK_2)


def _base(fig: go.Figure, height: int = 380, title: str | None = None, legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height,
        title=dict(text=title, x=0, xanchor="left", font=dict(size=16, color=INK)) if title else None,
        font=FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=48, t=56 if title else 16, b=24),
        showlegend=legend,
        legend=dict(orientation="h", y=1.08, x=0, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#1C1932", font_size=13, font_color="#E8E6F0", bordercolor="#252338"),
    )
    fig.update_xaxes(showline=False, zeroline=False, gridcolor=GRID, tickfont=dict(color=INK_2))
    fig.update_yaxes(showline=False, zeroline=False, tickfont=dict(color=INK_2))
    return fig


def hbar(
    labels,
    values,
    title: str,
    fmt: str = "{:,.0f}",
    highlight: str | None = None,
    hover: list[str] | None = None,
    height: int | None = None,
    xtitle: str | None = None,
    integer_ticks: bool = False,
) -> go.Figure:
    """Horizontal bar, largest on top, value labels at the bar end. One orange highlight at most."""
    labels, values = list(labels), list(values)
    colors = [ORANGE if (highlight is not None and l == highlight) else BLUE for l in labels]
    fig = go.Figure(
        go.Bar(
            x=values[::-1],
            y=labels[::-1],
            orientation="h",
            marker=dict(color=colors[::-1], cornerradius=4),
            text=[fmt.format(v) for v in values][::-1],
            textposition="outside",
            textfont=dict(color=INK_2, size=12),
            cliponaxis=False,
            hovertext=hover[::-1] if hover else None,
            hovertemplate="%{hovertext}<extra></extra>" if hover else "%{y}: %{text}<extra></extra>",
        )
    )
    fig.update_layout(bargap=0.35)
    fig.update_xaxes(showgrid=True, title=xtitle, range=[0, max(values) * 1.22 if values else 1])
    if integer_ticks:
        fig.update_xaxes(dtick=1)
    fig.update_yaxes(showgrid=False, ticklabelstandoff=10)
    return _base(fig, height or max(260, 30 * len(labels) + 80), title)


def vbar(labels, values, title: str, fmt: str = "{:,.0f}", highlight: str | None = None, height: int = 340,
         ytitle: str | None = None) -> go.Figure:
    labels, values = list(labels), list(values)
    colors = [ORANGE if (highlight is not None and l == highlight) else BLUE for l in labels]
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors, cornerradius=4),
            text=[fmt.format(v) for v in values],
            textposition="outside",
            textfont=dict(color=INK_2, size=12),
            cliponaxis=False,
            hovertemplate="%{x}: %{text}<extra></extra>",
        )
    )
    fig.update_layout(bargap=0.35)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, title=ytitle, range=[0, max(values) * 1.22 if values else 1])
    fig.update_xaxes(showgrid=False)
    return _base(fig, height, title)


def heatmap(matrix: pd.DataFrame, title: str, height: int = 420) -> go.Figure:
    """matrix: rows = roles, columns = skills, values = share (0-1)."""
    z = matrix.values * 100
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=list(matrix.columns),
            y=list(matrix.index),
            colorscale=[[i / (len(BLUE_RAMP) - 1), c] for i, c in enumerate(BLUE_RAMP)],
            zmin=0,
            zmax=max(80, float(z.max())),
            xgap=2,
            ygap=2,
            colorbar=dict(title="% of jobs", thickness=10, outlinewidth=0, ticksuffix="%",
                         tickfont=dict(color="#8B87A0"), title_font=dict(color="#8B87A0")),
            hovertemplate="%{y} · %{x}<br>%{z:.0f}% of postings<extra></extra>",
            text=[[f"{v:.0f}" for v in row] for row in z],
            texttemplate="%{text}",
            textfont=dict(size=11, color="#e0e0e0"),
        )
    )
    fig.update_xaxes(side="top", tickangle=-35, showgrid=False)
    fig.update_yaxes(autorange="reversed", showgrid=False, ticklabelstandoff=8)
    _base(fig, height, title)
    fig.update_layout(margin=dict(l=8, r=24, t=120, b=8))
    return fig


def dumbbell(df: pd.DataFrame, label: str, a: str, b: str, a_name: str, b_name: str, title: str,
             height: int | None = None) -> go.Figure:
    """Two values per row joined by a line. a = baseline (gray), b = the group of interest (orange)."""
    d = df.iloc[::-1]
    fig = go.Figure()
    for _, r in d.iterrows():
        fig.add_trace(go.Scatter(x=[r[a], r[b]], y=[r[label]] * 2, mode="lines",
                                 line=dict(color=GRID, width=3), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=d[a], y=d[label], mode="markers", name=a_name,
                             marker=dict(color=GRAY, size=11, line=dict(color=SURFACE, width=2)),
                             hovertemplate="%{y}<br>" + a_name + ": %{x:.0f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=d[b], y=d[label], mode="markers", name=b_name,
                             marker=dict(color=ORANGE, size=11, line=dict(color=SURFACE, width=2)),
                             hovertemplate="%{y}<br>" + b_name + ": %{x:.0f}%<extra></extra>"))
    fig.update_xaxes(title="% of postings that mention the skill", ticksuffix="%", rangemode="tozero")
    fig.update_yaxes(showgrid=False)
    return _base(fig, height or max(300, 30 * len(d) + 100), title, legend=True)
