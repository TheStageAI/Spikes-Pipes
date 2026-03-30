from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import streamlit as st

if TYPE_CHECKING:
    from typing import Any

    from spikesnpipes.database import DatabaseReader

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Writer helper
# ---------------------------------------------------------------------------


def save_image(
    image: Any, dest: Path, fmt: str = "png"
) -> tuple[int, int]:
    """Save *image* to *dest* and return (width, height).

    Accepts numpy arrays (H*W*C uint8), PIL Images, or file paths.
    """
    try:
        from PIL import Image as PILImage
    except ImportError as exc:
        raise ImportError(
            "Pillow is required for image logging: "
            "pip install Pillow"
        ) from exc

    if isinstance(image, (str, Path)):
        img = PILImage.open(image)
    elif hasattr(image, "shape"):
        arr = np.asarray(image)
        if arr.ndim == 2:
            img = PILImage.fromarray(arr, mode="L")
        else:
            img = PILImage.fromarray(arr)
    elif isinstance(image, PILImage.Image):
        img = image
    else:
        raise TypeError(f"Unsupported image type: {type(image)}")

    img.save(dest, format=fmt.upper())
    return img.size


# ---------------------------------------------------------------------------
# Step slider (log-scale, shared with other media modules)
# ---------------------------------------------------------------------------

N_STOPS = 10


def _compute_log_stops(
    steps: list[int], n_stops: int = N_STOPS
) -> list[int]:
    if len(steps) <= n_stops:
        return steps
    log_min = np.log1p(steps[0])
    log_max = np.log1p(steps[-1])
    targets = np.linspace(log_min, log_max, n_stops)
    arr = np.array(steps)
    stops: list[int] = []
    for t in targets:
        idx = int(np.argmin(np.abs(np.log1p(arr) - t)))
        stops.append(int(arr[idx]))
    return sorted(set(stops))


def _format_step(s: int) -> str:
    if s >= 1_000_000:
        return f"{s / 1_000_000:.1f}M"
    if s >= 1_000:
        return f"{s / 1_000:.1f}k"
    return str(s)


def step_slider(
    steps: list[int], key: str
) -> int | None:
    """Render a log-scale step select-slider. Returns chosen step."""
    if not steps:
        return None
    stops = _compute_log_stops(sorted(steps))
    if len(stops) == 1:
        st.caption(f"Step {stops[0]}")
        return stops[0]
    return st.select_slider(
        "Step",
        options=stops,
        value=stops[-1],
        format_func=_format_step,
        key=key,
    )


# ---------------------------------------------------------------------------
# Dashboard renderers
# ---------------------------------------------------------------------------


def render_image_gallery(
    readers: dict[str, DatabaseReader],
    tag: str,
    colors: dict[str, str],
) -> None:
    all_steps: set[int] = set()
    for reader in readers.values():
        all_steps.update(reader.image_steps(tag))

    if not all_steps:
        st.info("No images recorded yet.")
        return

    chosen = step_slider(sorted(all_steps), key=f"img_{tag}")
    if chosen is None:
        return

    for run_name, reader in readers.items():
        rows = reader.read_images(tag, step=chosen)
        if not rows:
            continue

        color = colors.get(run_name, "#FFFFFF")
        st.markdown(
            f"**<span style='color:{color}'>{run_name}</span>** "
            f"— step {chosen}",
            unsafe_allow_html=True,
        )

        cols = st.columns(min(len(rows), 4))
        for j, row in enumerate(rows):
            img_path = reader.log_dir / row["path"]
            with cols[j % len(cols)]:
                if img_path.exists():
                    st.image(str(img_path), width="stretch")
                else:
                    st.warning(f"Missing: {row['path']}")


def render_image_comparison(
    readers: dict[str, DatabaseReader],
    config: dict,
    colors: dict[str, str],
) -> None:
    all_image_tags: set[str] = set()
    for reader in readers.values():
        all_image_tags.update(reader.image_tags())

    if not all_image_tags:
        st.info("No image tags found.")
        return

    chosen_tag = st.selectbox(
        "Tag",
        sorted(all_image_tags),
        key="imgcmp_tag",
    )

    all_steps: set[int] = set()
    for reader in readers.values():
        all_steps.update(reader.image_steps(chosen_tag))

    if not all_steps:
        st.info("No images for this tag.")
        return

    chosen_step = step_slider(
        sorted(all_steps), key=f"imgcmp_{chosen_tag}"
    )
    if chosen_step is None:
        return

    cols = st.columns(len(readers))
    for i, (run_name, reader) in enumerate(readers.items()):
        with cols[i]:
            color = colors.get(run_name, "#FFFFFF")
            st.markdown(
                f"**<span style='color:{color}'>"
                f"{run_name}</span>**",
                unsafe_allow_html=True,
            )
            rows = reader.read_images(
                chosen_tag, step=chosen_step
            )
            if rows:
                img_path = reader.log_dir / rows[0]["path"]
                if img_path.exists():
                    st.image(
                        str(img_path),
                        width="stretch",
                    )
                else:
                    st.warning("File missing")
            else:
                st.caption("(no data)")
