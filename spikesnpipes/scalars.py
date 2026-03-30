from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import plotly.graph_objects as go
import streamlit as st

if TYPE_CHECKING:
    from spikesnpipes.database import DatabaseReader

MAX_POINTS_PER_LINE = 128

# ---------------------------------------------------------------------------
# Downsampling
# ---------------------------------------------------------------------------


def _downsample(
    x: np.ndarray,
    y: np.ndarray,
    n_out: int = MAX_POINTS_PER_LINE,
) -> tuple[np.ndarray, np.ndarray]:
    if len(x) <= n_out:
        return x, y

    try:
        import lttb as _lttb

        data = np.column_stack([x, y]).astype(np.float64)
        sampled = _lttb.downsample(data, n_out)
        return sampled[:, 0], sampled[:, 1]
    except Exception:
        indices = np.unique(
            np.linspace(0, len(x) - 1, n_out, dtype=int)
        )
        return x[indices], y[indices]


# ---------------------------------------------------------------------------
# Smoothing (EMA)
# ---------------------------------------------------------------------------


def _smooth_ema(values: np.ndarray, weight: float) -> np.ndarray:
    if weight <= 0 or len(values) == 0:
        return values
    out = np.empty_like(values)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = weight * out[i - 1] + (1 - weight) * values[i]
    return out


# ---------------------------------------------------------------------------
# Public renderer
# ---------------------------------------------------------------------------


def render_scalars_section(
    readers: dict[str, DatabaseReader],
    tags: list[str],
    colors: dict[str, str],
) -> None:
    ctrl1, ctrl2 = st.columns([1, 1])
    with ctrl1:
        x_mode = st.radio(
            "X-axis",
            ["Step", "Custom (x_value)", "Wall time"],
            horizontal=True,
            key=f"sp_xaxis_{'_'.join(tags[:2])}",
        )
    with ctrl2:
        smoothing = st.slider(
            "Smoothing",
            0.0,
            0.99,
            0.6,
            key=f"sp_smooth_{'_'.join(tags[:2])}",
        )

    n_cols = min(len(tags), 2)
    cols = st.columns(n_cols)

    for i, tag in enumerate(tags):
        with cols[i % n_cols]:
            tag_suffix = tag.split("/", 1)[-1] if "/" in tag else tag
            st.markdown(
                f"**{tag_suffix}**",
            )

            fig = go.Figure()

            for run_name, reader in readers.items():
                rows = reader.read_scalars(tag)
                if not rows:
                    continue

                steps = np.array(
                    [r["step"] for r in rows], dtype=np.float64
                )
                values = np.array(
                    [r["value"] for r in rows], dtype=np.float64
                )

                if x_mode == "Custom (x_value)":
                    x = np.array(
                        [
                            r["x_value"]
                            if r["x_value"] is not None
                            else r["step"]
                            for r in rows
                        ],
                        dtype=np.float64,
                    )
                elif x_mode == "Wall time":
                    x = np.array(
                        [r["wall_time"] for r in rows],
                        dtype=np.float64,
                    )
                else:
                    x = steps

                x, values = _downsample(x, values)

                fig.add_trace(
                    go.Scattergl(
                        x=x,
                        y=values,
                        mode="lines",
                        line=dict(
                            color=colors[run_name], width=1
                        ),
                        opacity=0.2,
                        name=f"{run_name} (raw)",
                        showlegend=False,
                    )
                )

                y_smooth = _smooth_ema(values, smoothing)
                fig.add_trace(
                    go.Scattergl(
                        x=x,
                        y=y_smooth,
                        mode="lines",
                        line=dict(
                            color=colors[run_name], width=2
                        ),
                        name=run_name,
                    )
                )

            fig.update_layout(
                height=280,
                margin=dict(l=40, r=10, t=10, b=30),
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.15,
                    xanchor="left",
                    x=0,
                    font=dict(size=11),
                ),
            )

            st.plotly_chart(fig, width="stretch")
