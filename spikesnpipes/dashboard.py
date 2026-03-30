from __future__ import annotations

import argparse
from pathlib import Path

import plotly.io as pio
import streamlit as st

from spikesnpipes.database import DatabaseReader
from spikesnpipes import scalars as scalar_mod
from spikesnpipes import images as image_mod
from spikesnpipes import video as video_mod
from spikesnpipes import text as text_mod
from spikesnpipes import table as table_mod
from spikesnpipes.sections import (
    EVAL_SPECS,
    COMPARISON_TYPES,
    DEFAULT_DESCRIPTIONS,
    render_eval_section,
    render_comparison_section,
)

# ---------------------------------------------------------------------------
# Palette — 16 perceptually distinct colours for dark backgrounds.
# Alternates warm/cool hues so neighbouring runs are easy to tell apart.
# ---------------------------------------------------------------------------

RUN_COLORS = [
    "#FFF844",  # Yellow  (primary accent)
    "#5E9CFB",  # Blue
    "#FD3F40",  # Red
    "#3CD077",  # Green
    "#FF885A",  # Orange
    "#B57BFF",  # Purple
    "#FFB347",  # Amber
    "#00CED1",  # Teal
    "#FF69B4",  # Pink
    "#A6E22E",  # Lime
    "#E07A3E",  # Burnt orange
    "#48D1CC",  # Mint
    "#E04A6A",  # Rose
    "#7BB8FF",  # Sky
    "#C8E64A",  # Chartreuse
    "#B388FF",  # Lavender
]

_LOGO_PATH = Path(__file__).parent / "static" / "logo.svg"

# ---------------------------------------------------------------------------
# Plotly theme (applied once)
# ---------------------------------------------------------------------------


def _apply_plotly_theme() -> None:
    tpl = pio.templates["plotly_dark"]
    tpl.layout.paper_bgcolor = "#141414"
    tpl.layout.plot_bgcolor = "#141414"
    tpl.layout.font.color = "#9F9F9F"
    tpl.layout.font.family = "Inter, sans-serif"
    tpl.layout.colorway = RUN_COLORS
    tpl.layout.xaxis.gridcolor = "#303030"
    tpl.layout.yaxis.gridcolor = "#303030"
    pio.templates.default = tpl


_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, p, h1, h2, h3, h4, h5, h6,
span, div, label, input, button, textarea, select,
.stMarkdown, .stText, .stCaption {
    font-family: 'Inter', sans-serif;
}
hr {
    border: none;
    border-top: 0.5px solid #303030;
    margin: 0;
}
</style>
"""


# ---------------------------------------------------------------------------
# Run discovery
# ---------------------------------------------------------------------------


def _discover_runs(root: Path) -> dict[str, Path]:
    runs: dict[str, Path] = {}
    if (root / "spikes.db").exists():
        runs[root.name] = root
        return runs
    if not root.is_dir():
        return runs
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d / "spikes.db").exists():
            runs[d.name] = d
    return runs


# ---------------------------------------------------------------------------
# Arg parsing (Streamlit passes everything after --)
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logdir", type=str, default="sp_logs")
    args, _ = parser.parse_known_args()
    return args


# ---------------------------------------------------------------------------
# Anchor helpers for sidebar navigation
# ---------------------------------------------------------------------------


def _to_anchor(label: str) -> str:
    return (
        label.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace("(", "")
        .replace(")", "")
    )


def _anchor(label: str) -> None:
    slug = _to_anchor(label)
    st.markdown(
        f'<div id="{slug}"></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title="Spikes & Pipes",
        page_icon=":bar_chart:",
        layout="wide",
    )
    _apply_plotly_theme()

    args = _parse_args()
    root = Path(args.logdir).resolve()

    # ---- logo -------------------------------------------------------------
    if _LOGO_PATH.exists():
        st.logo(_LOGO_PATH, size="large")

    # ---- sidebar ----------------------------------------------------------
    with st.sidebar:
        logdir_input = st.text_input("Log directory", str(root))
        root = Path(logdir_input)

        runs = _discover_runs(root)

        if not runs:
            st.warning(f"No runs found in {root}")
            st.stop()

        # -- run checkboxes in a collapsible dropdown -----------------------
        with st.expander("Runs", expanded=True):
            btn_cols = st.columns(2)
            with btn_cols[0]:
                if st.button("All", width="stretch"):
                    for name in runs:
                        st.session_state[f"run_{name}"] = True
            with btn_cols[1]:
                if st.button("None", width="stretch"):
                    for name in runs:
                        st.session_state[f"run_{name}"] = False

            selected: list[str] = []
            for name in runs:
                key = f"run_{name}"
                if key not in st.session_state:
                    st.session_state[key] = True
                checked = st.checkbox(
                    name,
                    key=key,
                )
                if checked:
                    selected.append(name)

        st.divider()

        auto_refresh = st.toggle("Auto-refresh", value=False)
        if auto_refresh:
            interval_s = st.selectbox(
                "Interval (s)", [1, 2, 5, 10], index=2
            )
            try:
                from streamlit_autorefresh import (
                    st_autorefresh,
                )

                st_autorefresh(
                    interval=int(interval_s) * 1000,
                    key="sp_refresh",
                )
            except ImportError:
                st.caption(
                    "`pip install streamlit-autorefresh` "
                    "to enable auto-refresh"
                )

    if not selected:
        st.info("Select at least one run from the sidebar.")
        st.stop()

    # ---- open readers -----------------------------------------------------
    readers: dict[str, DatabaseReader] = {}
    colors: dict[str, str] = {}
    for i, name in enumerate(selected):
        readers[name] = DatabaseReader(runs[name])
        colors[name] = RUN_COLORS[i % len(RUN_COLORS)]

    # ---- collect tags across runs -----------------------------------------
    all_scalar_tags: set[str] = set()
    all_image_tags: set[str] = set()
    all_video_tags: set[str] = set()
    all_text_tags: set[str] = set()
    all_audio_tags: set[str] = set()
    all_sections: list[dict] = []

    for reader in readers.values():
        all_scalar_tags.update(reader.scalar_tags())
        all_image_tags.update(reader.image_tags())
        all_video_tags.update(reader.video_tags())
        all_text_tags.update(reader.text_tags())
        all_audio_tags.update(reader.audio_tags())
        all_sections.extend(reader.read_sections())

    scalar_groups: dict[str, list[str]] = {}
    for tag in sorted(all_scalar_tags):
        prefix = tag.split("/")[0] if "/" in tag else tag
        scalar_groups.setdefault(prefix, []).append(tag)

    # ---- build ordered section list for navigation ------------------------
    nav_sections: list[tuple[str, str]] = []  # (label, anchor)

    if scalar_groups:
        nav_sections.append(("Scalars", "scalars"))
    if all_image_tags:
        nav_sections.append(("Images", "images"))
    if all_video_tags:
        nav_sections.append(("Videos", "videos"))
    if all_text_tags:
        nav_sections.append(("Text", "text"))
    if all_audio_tags:
        nav_sections.append(("Audio", "audio"))

    seen_nav: set[str] = set()
    for section in all_sections:
        name = section["name"]
        if name in seen_nav:
            continue
        seen_nav.add(name)
        stype = section["section_type"]
        label = f"{name}  ({stype})"
        nav_sections.append((label, _to_anchor(label)))

    # ---- sidebar navigation -----------------------------------------------
    _SECTION_ICONS = {
        "scalars": "📈",
        "images": "🖼",
        "videos": "🎬",
        "text": "📝",
        "audio": "🔊",
    }

    def _icon_for(label: str) -> str:
        for prefix, icon in _SECTION_ICONS.items():
            if prefix in label.lower():
                return icon
        return "◆"

    nav_items = "\n".join(
        f'<a href="#{anchor}" class="sp-nav-item">'
        f'<span class="sp-nav-icon">{_icon_for(label)}</span>'
        f'<span class="sp-nav-label">{label}</span>'
        f"</a>"
        for label, anchor in nav_sections
    )

    nav_css = """
<style>
.sp-nav-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    margin: 2px 0;
    border-radius: 6px;
    color: #9F9F9F;
    text-decoration: none;
    font-size: 13px;
    transition: background 0.15s, color 0.15s;
}
.sp-nav-item:hover {
    background: #303030;
    color: #FFF844;
    text-decoration: none;
}
.sp-nav-icon {
    font-size: 14px;
    opacity: 0.8;
    flex-shrink: 0;
}
.sp-nav-item:hover .sp-nav-icon {
    opacity: 1;
}
.sp-nav-label {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
"""

    with st.sidebar:
        st.divider()
        st.caption("Sections")
        st.markdown(
            nav_css + nav_items, unsafe_allow_html=True
        )

    # ---- global CSS (Inter font) ------------------------------------------
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)

    # ---- project title on main page ---------------------------------------
    project_name = root.name.replace("_", " ").replace("-", " ").upper()
    st.title(project_name)

    # ---- Scalars ----------------------------------------------------------
    if scalar_groups:
        _anchor("Scalars")
        st.header("Scalars", divider="gray")
        for group, tags in scalar_groups.items():
            with st.expander(group, expanded=True):
                scalar_mod.render_scalars_section(
                    readers, tags, colors,
                )

    # ---- Images -----------------------------------------------------------
    if all_image_tags:
        _anchor("Images")
        st.header("Images", divider="gray")
        for tag in sorted(all_image_tags):
            with st.expander(tag, expanded=True):
                image_mod.render_image_gallery(
                    readers, tag, colors,
                )

    # ---- Videos -----------------------------------------------------------
    if all_video_tags:
        _anchor("Videos")
        st.header("Videos", divider="gray")
        for tag in sorted(all_video_tags):
            with st.expander(tag, expanded=True):
                video_mod.render_video_gallery(readers, tag)

    # ---- Text -------------------------------------------------------------
    if all_text_tags:
        _anchor("Text")
        st.header("Text", divider="gray")
        for tag in sorted(all_text_tags):
            with st.expander(tag, expanded=True):
                text_mod.render_text_section(readers, tag)

    # ---- Audio ------------------------------------------------------------
    if all_audio_tags:
        _anchor("Audio")
        st.header("Audio", divider="gray")
        from spikesnpipes.images import step_slider as _step_slider
        for tag in sorted(all_audio_tags):
            with st.expander(tag, expanded=True):
                a_steps: set[int] = set()
                for reader in readers.values():
                    a_steps.update(reader.audio_steps(tag))
                if not a_steps:
                    st.info("No audio yet.")
                    continue
                chosen_a = _step_slider(
                    sorted(a_steps), key=f"aud_{tag}"
                )
                if chosen_a is None:
                    continue
                for rn, reader in readers.items():
                    rows = reader.read_audios(tag, step=chosen_a)
                    if not rows:
                        continue
                    color = colors.get(rn, "#FFF")
                    st.markdown(
                        f"**<span style='color:{color}'>"
                        f"{rn}</span>** — step {chosen_a}",
                        unsafe_allow_html=True,
                    )
                    for row in rows:
                        p = reader.log_dir / row["path"]
                        if p.exists():
                            st.audio(str(p))

    # ---- explicit sections ------------------------------------------------
    seen: set[str] = set()
    for section in all_sections:
        name = section["name"]
        if name in seen:
            continue
        seen.add(name)
        stype = section["section_type"]
        config = section["config"]
        desc = section.get("description", "") or DEFAULT_DESCRIPTIONS.get(
            stype, ""
        )

        label = f"{name}  ({stype})"
        _anchor(label)
        with st.expander(label, expanded=True):
            if desc:
                st.caption(desc)
            if stype == "row":
                table_mod.render_row_section(
                    readers, name, config, colors,
                )
            elif stype == "image_comparison":
                image_mod.render_image_comparison(
                    readers, config, colors,
                )
            elif stype == "text_comparison":
                text_mod.render_text_comparison(
                    readers, config, colors,
                )
            elif stype in (
                "asr", "tts", "llm", "diffusion", "vlm",
            ):
                table_mod.render_table_section(
                    readers, name, stype, config, colors,
                )
            elif stype in EVAL_SPECS:
                render_eval_section(
                    readers, stype, config, colors,
                    section_key=name,
                )
            elif stype in COMPARISON_TYPES:
                render_comparison_section(
                    readers, stype, config, colors,
                    section_key=name,
                )
            else:
                st.info(f"Unknown section type: {stype}")

    # ---- cleanup ----------------------------------------------------------
    for reader in readers.values():
        reader.close()


if __name__ == "__main__":
    main()
