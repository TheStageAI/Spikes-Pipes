"""Table-based section renderers (ASR, TTS, LLM, diffusion, VLM).

These are structured as two-dimensional grids where fixed columns hold
shared inputs (prompt, audio, ground truth) and one additional column
is added per selected run for model outputs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from spikesnpipes.database import DatabaseReader

# ---------------------------------------------------------------------------
# Row section
# ---------------------------------------------------------------------------


def render_row_section(
    readers: dict[str, DatabaseReader],
    name: str,
    config: dict,
    colors: dict[str, str],
) -> None:
    from spikesnpipes.images import step_slider

    widgets = config.get("widgets", [])
    if not widgets:
        st.info(f"Section '{name}' has no widgets configured.")
        return

    run_names = list(readers.keys())
    chosen_run = st.selectbox(
        "Run", run_names, key=f"row_run_{name}"
    )
    reader = readers[chosen_run]

    all_steps: set[int] = set()
    for tag in reader.image_tags():
        all_steps.update(reader.image_steps(tag))
    for tag in reader.text_tags():
        all_steps.update(reader.text_steps(tag))

    if not all_steps:
        st.info("No data yet.")
        return

    chosen_step = step_slider(
        sorted(all_steps), key=f"row_step_{name}"
    )
    if chosen_step is None:
        return

    cols = st.columns(len(widgets))
    for j, wtype in enumerate(widgets):
        with cols[j]:
            st.caption(wtype)
            if wtype == "image":
                _render_first_image(reader, chosen_step, j)
            elif wtype == "text":
                _render_first_text(reader, chosen_step, j)
            elif wtype == "video":
                _render_first_video(reader, chosen_step, j)
            else:
                st.info(f"Widget type '{wtype}' not yet supported.")


def _render_first_image(
    reader: "DatabaseReader", step: int, idx: int
) -> None:
    for tag in reader.image_tags():
        rows = reader.read_images(tag, step=step)
        if rows and idx < len(rows):
            img_path = reader.log_dir / rows[idx]["path"]
            if img_path.exists():
                st.image(str(img_path), width="stretch")
                return
    st.caption("(no image)")


def _render_first_text(
    reader: "DatabaseReader", step: int, idx: int
) -> None:
    for tag in reader.text_tags():
        rows = reader.read_texts(tag, step=step)
        if rows and idx < len(rows):
            st.text(rows[idx]["content"])
            return
    st.caption("(no text)")


def _render_first_video(
    reader: "DatabaseReader", step: int, idx: int
) -> None:
    for tag in reader.video_tags():
        rows = reader.read_videos(tag, step=step)
        if rows and idx < len(rows):
            vid_path = reader.log_dir / rows[idx]["path"]
            if vid_path.exists():
                st.video(str(vid_path))
                return
    st.caption("(no video)")


# ---------------------------------------------------------------------------
# Generic table section (ASR / TTS / LLM / diffusion / VLM)
# ---------------------------------------------------------------------------


def render_table_section(
    readers: dict[str, DatabaseReader],
    name: str,
    section_type: str,
    config: dict,
    colors: dict[str, str],
) -> None:
    from spikesnpipes.images import step_slider

    all_steps: set[int] = set()
    for reader in readers.values():
        for tag in reader.text_tags():
            all_steps.update(reader.text_steps(tag))
        for tag in reader.image_tags():
            all_steps.update(reader.image_steps(tag))

    if not all_steps:
        st.info(f"No data for section '{name}' yet.")
        return

    chosen_step = step_slider(
        sorted(all_steps), key=f"tbl_{name}"
    )
    if chosen_step is None:
        return

    if section_type == "asr":
        _render_asr(readers, config, chosen_step, colors)
    elif section_type == "tts":
        _render_tts(readers, config, chosen_step, colors)
    elif section_type == "llm":
        _render_llm(readers, config, chosen_step, colors)
    elif section_type == "diffusion":
        _render_diffusion(readers, config, chosen_step, colors)
    elif section_type == "vlm":
        _render_vlm(readers, config, chosen_step, colors)
    else:
        st.info(
            f"Table section type '{section_type}' "
            f"is not implemented yet."
        )


# ---------------------------------------------------------------------------
# Concrete table renderers
# ---------------------------------------------------------------------------


def _read_texts_for_tag(
    readers: dict[str, "DatabaseReader"],
    tag: str | None,
    step: int,
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    if not tag:
        return result
    for run_name, reader in readers.items():
        rows = reader.read_texts(tag, step=step)
        result[run_name] = [r["content"] for r in rows]
    return result


def _render_asr(
    readers: dict[str, "DatabaseReader"],
    config: dict,
    step: int,
    colors: dict[str, str],
) -> None:
    gt_tag = config.get("ground_truth_tag")
    pred_tag = config.get("prediction_tag")

    gt = _read_texts_for_tag(readers, gt_tag, step)
    preds = _read_texts_for_tag(readers, pred_tag, step)

    first_run = next(iter(readers))
    n_rows = max(len(gt.get(first_run, [])), 1)

    header_cols = ["#", "Ground Truth"] + list(readers.keys())
    st.markdown(
        "| " + " | ".join(header_cols) + " |"
    )
    st.markdown(
        "| " + " | ".join(["---"] * len(header_cols)) + " |"
    )
    for i in range(n_rows):
        gt_text = gt.get(first_run, [""])[i] if i < len(
            gt.get(first_run, [])
        ) else ""
        row_cells = [str(i), gt_text]
        for run_name in readers:
            p = preds.get(run_name, [])
            row_cells.append(p[i] if i < len(p) else "")
        st.markdown("| " + " | ".join(row_cells) + " |")


def _render_tts(
    readers: dict[str, "DatabaseReader"],
    config: dict,
    step: int,
    colors: dict[str, str],
) -> None:
    input_tag = config.get("input_tag")
    inputs = _read_texts_for_tag(readers, input_tag, step)
    first_run = next(iter(readers))
    n_rows = max(len(inputs.get(first_run, [])), 1)

    st.caption(
        f"Input tag: {input_tag or '(not set)'} — "
        f"output audio rendering is a stub"
    )
    for i in range(n_rows):
        txt = inputs.get(first_run, [""])[i] if i < len(
            inputs.get(first_run, [])
        ) else ""
        st.text(f"[{i}] {txt}")


def _render_llm(
    readers: dict[str, "DatabaseReader"],
    config: dict,
    step: int,
    colors: dict[str, str],
) -> None:
    prompt_tag = config.get("prompt_tag")
    output_tag = config.get("output_tag")

    prompts = _read_texts_for_tag(readers, prompt_tag, step)
    outputs = _read_texts_for_tag(readers, output_tag, step)

    first_run = next(iter(readers))
    n_rows = max(len(prompts.get(first_run, [])), 1)

    header = ["#", "Prompt"] + list(readers.keys())
    st.markdown("| " + " | ".join(header) + " |")
    st.markdown(
        "| " + " | ".join(["---"] * len(header)) + " |"
    )
    for i in range(n_rows):
        p = prompts.get(first_run, [""])[i] if i < len(
            prompts.get(first_run, [])
        ) else ""
        cells = [str(i), p]
        for run_name in readers:
            o = outputs.get(run_name, [])
            cells.append(o[i] if i < len(o) else "")
        st.markdown("| " + " | ".join(cells) + " |")


def _render_diffusion(
    readers: dict[str, "DatabaseReader"],
    config: dict,
    step: int,
    colors: dict[str, str],
) -> None:
    prompt_tag = config.get("prompt_tag")
    output_tag = config.get("output_tag")
    prompts = _read_texts_for_tag(readers, prompt_tag, step)

    first_run = next(iter(readers))
    n_rows = max(len(prompts.get(first_run, [])), 1)

    for i in range(n_rows):
        p = prompts.get(first_run, [""])[i] if i < len(
            prompts.get(first_run, [])
        ) else ""
        st.markdown(f"**Prompt:** {p}")

        cols = st.columns(len(readers))
        for j, (run_name, reader) in enumerate(
            readers.items()
        ):
            with cols[j]:
                st.caption(run_name)
                if output_tag:
                    imgs = reader.read_images(
                        output_tag, step=step
                    )
                    if imgs and i < len(imgs):
                        path = (
                            reader.log_dir / imgs[i]["path"]
                        )
                        if path.exists():
                            st.image(
                                str(path),
                                width="stretch",
                            )
                            continue
                st.caption("(no output)")


def _render_vlm(
    readers: dict[str, "DatabaseReader"],
    config: dict,
    step: int,
    colors: dict[str, str],
) -> None:
    image_tag = config.get("image_tag")
    prompt_tag = config.get("prompt_tag")
    output_tag = config.get("output_tag")

    prompts = _read_texts_for_tag(readers, prompt_tag, step)
    outputs = _read_texts_for_tag(readers, output_tag, step)

    first_run = next(iter(readers))
    first_reader = readers[first_run]
    n_rows = max(len(prompts.get(first_run, [])), 1)

    for i in range(n_rows):
        cols = st.columns([1, 1] + [1] * len(readers))

        with cols[0]:
            st.caption("Input")
            if image_tag:
                imgs = first_reader.read_images(
                    image_tag, step=step
                )
                if imgs and i < len(imgs):
                    path = first_reader.log_dir / imgs[i]["path"]
                    if path.exists():
                        st.image(
                            str(path),
                            width="stretch",
                        )

        with cols[1]:
            st.caption("Prompt")
            p = prompts.get(first_run, [""])[i] if i < len(
                prompts.get(first_run, [])
            ) else ""
            st.text(p)

        for j, run_name in enumerate(readers):
            with cols[2 + j]:
                st.caption(run_name)
                o = outputs.get(run_name, [])
                st.text(o[i] if i < len(o) else "")
