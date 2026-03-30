from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from typing import Any

    from spikesnpipes.database import DatabaseReader

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Writer helper
# ---------------------------------------------------------------------------


def save_video(video: Any, dest: Path, fmt: str = "mp4") -> None:
    """Save *video* to *dest*.

    Accepts a file path (copied as-is) or a numpy array (T*H*W*C uint8)
    written frame-by-frame via imageio.
    """
    if isinstance(video, (str, Path)):
        shutil.copy2(Path(video), dest)
        return

    if hasattr(video, "shape"):
        try:
            import imageio.v3 as iio
        except ImportError as exc:
            raise ImportError(
                "imageio is required for video logging: "
                "pip install imageio[ffmpeg]"
            ) from exc

        iio.imwrite(
            dest, video, extension=f".{fmt}", codec="libx264",
        )
        return

    raise TypeError(f"Unsupported video type: {type(video)}")


# ---------------------------------------------------------------------------
# Dashboard renderer
# ---------------------------------------------------------------------------


def render_video_gallery(
    readers: dict[str, DatabaseReader],
    tag: str,
) -> None:
    from spikesnpipes.images import step_slider

    all_steps: set[int] = set()
    for reader in readers.values():
        all_steps.update(reader.video_steps(tag))

    if not all_steps:
        st.info("No videos recorded yet.")
        return

    chosen = step_slider(sorted(all_steps), key=f"vid_{tag}")
    if chosen is None:
        return

    for run_name, reader in readers.items():
        rows = reader.read_videos(tag, step=chosen)
        if not rows:
            continue

        st.markdown(f"**{run_name}** — step {chosen}")
        cols = st.columns(min(len(rows), 3))
        for j, row in enumerate(rows):
            vid_path = reader.log_dir / row["path"]
            with cols[j % len(cols)]:
                if vid_path.exists():
                    st.video(str(vid_path))
                else:
                    st.warning(f"Missing: {row['path']}")
