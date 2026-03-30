from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from spikesnpipes.database import DatabaseReader

# ---------------------------------------------------------------------------
# Dashboard renderers
# ---------------------------------------------------------------------------


def render_text_section(
    readers: dict[str, DatabaseReader],
    tag: str,
) -> None:
    from spikesnpipes.images import step_slider

    all_steps: set[int] = set()
    for reader in readers.values():
        all_steps.update(reader.text_steps(tag))

    if not all_steps:
        st.info("No text recorded yet.")
        return

    chosen = step_slider(sorted(all_steps), key=f"txt_{tag}")
    if chosen is None:
        return

    for run_name, reader in readers.items():
        rows = reader.read_texts(tag, step=chosen)
        if not rows:
            continue

        st.markdown(f"**{run_name}** — step {chosen}")
        for row in rows:
            st.markdown(row["content"])


def render_text_comparison(
    readers: dict[str, DatabaseReader],
    config: dict,
    colors: dict[str, str],
) -> None:
    from spikesnpipes.images import step_slider

    all_text_tags: set[str] = set()
    for reader in readers.values():
        all_text_tags.update(reader.text_tags())

    if not all_text_tags:
        st.info("No text tags found.")
        return

    chosen_tag = st.selectbox(
        "Tag", sorted(all_text_tags), key="txtcmp_tag"
    )

    all_steps: set[int] = set()
    for reader in readers.values():
        all_steps.update(reader.text_steps(chosen_tag))

    if not all_steps:
        st.info("No text for this tag.")
        return

    chosen_step = step_slider(
        sorted(all_steps), key=f"txtcmp_{chosen_tag}"
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
            rows = reader.read_texts(chosen_tag, step=chosen_step)
            if rows:
                for row in rows:
                    st.markdown(row["content"])
            else:
                st.caption("(no data)")
