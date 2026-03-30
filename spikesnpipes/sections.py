"""Generic eval and comparison section renderers.

Every DL-task section type (text_to_image, audio_to_text, …) is described
by a :class:`SectionSpec` that maps config keys to widget types.  The two
public renderers — :func:`render_eval_section` and
:func:`render_comparison_section` — use that spec to build the layout
automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from spikesnpipes.database import DatabaseReader

from spikesnpipes.images import step_slider


# -------------------------------------------------------------------
# Spec registry
# -------------------------------------------------------------------


@dataclass(frozen=True)
class SectionSpec:
    inputs: tuple[tuple[str, str], ...]
    output: tuple[str, str]
    gt: tuple[str, str] | None = None


EVAL_SPECS: dict[str, SectionSpec] = {
    "text_to_image": SectionSpec(
        inputs=(("prompt_tag", "text"),),
        output=("output_tag", "image"),
        gt=("ground_truth_tag", "image"),
    ),
    "text_to_text": SectionSpec(
        inputs=(("input_tag", "text"),),
        output=("output_tag", "text"),
        gt=("ground_truth_tag", "text"),
    ),
    "text_to_video": SectionSpec(
        inputs=(("prompt_tag", "text"),),
        output=("output_tag", "video"),
        gt=("ground_truth_tag", "video"),
    ),
    "text_to_audio": SectionSpec(
        inputs=(("input_tag", "text"),),
        output=("output_tag", "audio"),
        gt=("reference_tag", "audio"),
    ),
    "audio_to_text": SectionSpec(
        inputs=(("audio_tag", "audio"),),
        output=("prediction_tag", "text"),
        gt=("ground_truth_tag", "text"),
    ),
    "text_image_to_image": SectionSpec(
        inputs=(("prompt_tag", "text"), ("input_image_tag", "image")),
        output=("output_tag", "image"),
        gt=("ground_truth_tag", "image"),
    ),
    "text_image_to_video": SectionSpec(
        inputs=(("prompt_tag", "text"), ("input_image_tag", "image")),
        output=("output_tag", "video"),
    ),
    "text_image_to_text": SectionSpec(
        inputs=(("prompt_tag", "text"), ("input_image_tag", "image")),
        output=("output_tag", "text"),
        gt=("ground_truth_tag", "text"),
    ),
}

COMPARISON_TYPES: set[str] = {
    f"{k}_comparison" for k in EVAL_SPECS
}

DEFAULT_DESCRIPTIONS: dict[str, str] = {
    "text_to_image": (
        "Text-to-image generation. Shows the text prompt alongside "
        "the generated image for each run."
    ),
    "text_to_image_comparison": (
        "A/B comparison of text-to-image outputs. Toggle between "
        "two runs to spot pixel-level differences, or use pixel diff."
    ),
    "text_to_text": (
        "Text-to-text evaluation (translation, summarisation, LLM). "
        "Shows input text and model output for each run."
    ),
    "text_to_text_comparison": (
        "A/B comparison of text outputs with word-level diff "
        "highlighting. Green = added, red = removed."
    ),
    "text_to_video": (
        "Text-to-video generation. Shows the text prompt and "
        "generated video for each run."
    ),
    "text_to_video_comparison": (
        "Side-by-side video comparison between two runs."
    ),
    "text_to_audio": (
        "Text-to-audio synthesis (TTS). Shows input text and "
        "generated audio for each run."
    ),
    "text_to_audio_comparison": (
        "A/B audio comparison between two TTS runs."
    ),
    "audio_to_text": (
        "Audio-to-text recognition (ASR). Shows input audio, "
        "ground truth transcript, and model prediction for each run."
    ),
    "audio_to_text_comparison": (
        "A/B comparison of ASR predictions with word-level diff."
    ),
    "text_image_to_image": (
        "Conditional image generation (editing, inpainting, style "
        "transfer). Shows prompt, input image, and output for each run."
    ),
    "text_image_to_image_comparison": (
        "A/B comparison of image editing outputs. Toggle/flicker "
        "between two runs with synchronized zoom and pan."
    ),
    "text_image_to_video": (
        "Image-to-video animation. Shows prompt, source image, and "
        "generated video for each run."
    ),
    "text_image_to_text": (
        "Visual question answering (VLM). Shows image, question, "
        "and model answer for each run."
    ),
    "text_image_to_text_comparison": (
        "A/B comparison of VLM answers with word-level diff."
    ),
}


# -------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------


def _steps_for_tag(
    reader: "DatabaseReader", tag: str, wtype: str
) -> list[int]:
    if wtype == "text":
        return reader.text_steps(tag)
    if wtype == "image":
        return reader.image_steps(tag)
    if wtype == "video":
        return reader.video_steps(tag)
    if wtype == "audio":
        return reader.audio_steps(tag)
    return []


def _collect_steps(
    readers: dict[str, "DatabaseReader"],
    config: dict,
    spec: SectionSpec,
) -> list[int]:
    tags: list[tuple[str, str]] = []
    for key, wtype in spec.inputs:
        t = config.get(key)
        if t:
            tags.append((t, wtype))
    out_tag = config.get(spec.output[0])
    if out_tag:
        tags.append((out_tag, spec.output[1]))
    if spec.gt:
        gt_tag = config.get(spec.gt[0])
        if gt_tag:
            tags.append((gt_tag, spec.gt[1]))

    steps: set[int] = set()
    for reader in readers.values():
        for tag, wtype in tags:
            steps.update(_steps_for_tag(reader, tag, wtype))
    return sorted(steps)


def _count_samples(
    reader: "DatabaseReader",
    tag: str | None,
    wtype: str,
    step: int,
) -> int:
    if not tag:
        return 0
    if wtype == "text":
        return len(reader.read_texts(tag, step=step))
    if wtype == "image":
        return len(reader.read_images(tag, step=step))
    if wtype == "video":
        return len(reader.read_videos(tag, step=step))
    if wtype == "audio":
        return len(reader.read_audios(tag, step=step))
    return 0


def _render_widget(
    reader: "DatabaseReader",
    tag: str,
    wtype: str,
    step: int,
    idx: int = 0,
) -> bool:
    """Render one widget item. Returns True on success."""
    if wtype == "text":
        rows = reader.read_texts(tag, step=step)
        if rows and idx < len(rows):
            st.markdown(rows[idx]["content"])
            return True
    elif wtype == "image":
        rows = reader.read_images(tag, step=step)
        if rows and idx < len(rows):
            path = reader.log_dir / rows[idx]["path"]
            if path.exists():
                st.image(str(path), width="stretch")
                return True
    elif wtype == "video":
        rows = reader.read_videos(tag, step=step)
        if rows and idx < len(rows):
            path = reader.log_dir / rows[idx]["path"]
            if path.exists():
                st.video(str(path))
                return True
    elif wtype == "audio":
        rows = reader.read_audios(tag, step=step)
        if rows and idx < len(rows):
            path = reader.log_dir / rows[idx]["path"]
            if path.exists():
                st.audio(str(path))
                return True
    st.caption("(no data)")
    return False


# -------------------------------------------------------------------
# Eval renderer
# -------------------------------------------------------------------


def render_eval_section(
    readers: dict[str, "DatabaseReader"],
    section_type: str,
    config: dict,
    colors: dict[str, str],
    section_key: str = "",
) -> None:
    spec = EVAL_SPECS.get(section_type)
    if not spec:
        st.info(f"Unknown eval section type: {section_type}")
        return

    steps = _collect_steps(readers, config, spec)
    if not steps:
        st.info("No data yet.")
        return

    chosen = step_slider(steps, key=f"eval_{section_key}")
    if chosen is None:
        return

    first_reader = next(iter(readers.values()))
    out_tag = config.get(spec.output[0])
    n_samples = max(
        _count_samples(
            first_reader, out_tag, spec.output[1], chosen
        ),
        1,
    )
    sample_idx = 0
    if n_samples > 1:
        sample_idx = st.slider(
            "Sample",
            0,
            n_samples - 1,
            0,
            key=f"smp_{section_key}",
        )

    has_gt = spec.gt is not None and config.get(spec.gt[0])
    n_cols = len(spec.inputs) + (1 if has_gt else 0) + len(readers)
    cols = st.columns(n_cols)
    ci = 0

    for key, wtype in spec.inputs:
        tag = config.get(key)
        with cols[ci]:
            label = key.replace("_tag", "").replace("_", " ").title()
            st.caption(label)
            if tag:
                _render_widget(
                    first_reader, tag, wtype, chosen, sample_idx
                )
            else:
                st.caption("(not set)")
        ci += 1

    if has_gt:
        gt_key, gt_type = spec.gt  # type: ignore[misc]
        with cols[ci]:
            st.caption("Reference")
            gt_tag = config.get(gt_key)
            if gt_tag:
                _render_widget(
                    first_reader, gt_tag, gt_type, chosen,
                    sample_idx,
                )
        ci += 1

    for run_name, reader in readers.items():
        with cols[ci]:
            color = colors.get(run_name, "#FFF")
            st.markdown(
                f"<span style='color:{color}'>"
                f"<b>{run_name}</b></span>",
                unsafe_allow_html=True,
            )
            if out_tag:
                _render_widget(
                    reader, out_tag, spec.output[1], chosen,
                    sample_idx,
                )
        ci += 1


# -------------------------------------------------------------------
# Comparison renderer
# -------------------------------------------------------------------


def render_comparison_section(
    readers: dict[str, "DatabaseReader"],
    section_type: str,
    config: dict,
    colors: dict[str, str],
    section_key: str = "",
) -> None:
    base_type = section_type.removesuffix("_comparison")
    spec = EVAL_SPECS.get(base_type)
    if not spec:
        st.info(f"Unknown comparison type: {section_type}")
        return

    run_names = list(readers.keys())
    if len(run_names) < 2:
        st.warning("Need at least 2 runs for comparison.")
        render_eval_section(
            readers, base_type, config, colors, section_key
        )
        return

    steps = _collect_steps(readers, config, spec)
    if not steps:
        st.info("No data yet.")
        return

    chosen = step_slider(steps, key=f"cmp_{section_key}")
    if chosen is None:
        return

    first_reader = next(iter(readers.values()))
    out_tag = config.get(spec.output[0])
    n_samples = max(
        _count_samples(
            first_reader, out_tag, spec.output[1], chosen
        ),
        1,
    )
    sample_idx = 0
    if n_samples > 1:
        sample_idx = st.slider(
            "Sample",
            0,
            n_samples - 1,
            0,
            key=f"csmp_{section_key}",
        )

    sc1, sc2 = st.columns(2)
    with sc1:
        run_a = st.selectbox(
            "Run A", run_names, index=0,
            key=f"cmp_a_{section_key}",
        )
    with sc2:
        run_b = st.selectbox(
            "Run B", run_names,
            index=min(1, len(run_names) - 1),
            key=f"cmp_b_{section_key}",
        )

    for key, wtype in spec.inputs:
        tag = config.get(key)
        if tag:
            label = key.replace("_tag", "").replace("_", " ").title()
            st.caption(label)
            _render_widget(
                readers[run_a], tag, wtype, chosen, sample_idx
            )

    if spec.gt:
        gt_tag = config.get(spec.gt[0])
        if gt_tag:
            st.caption("Reference")
            _render_widget(
                readers[run_a], gt_tag, spec.gt[1], chosen,
                sample_idx,
            )

    out_key, out_type = spec.output
    tag = config.get(out_key)
    if not tag:
        st.info("Output tag not configured.")
        return

    from spikesnpipes import comparison as cmp

    ra, rb = readers[run_a], readers[run_b]

    if out_type == "image":
        imgs_a = ra.read_images(tag, step=chosen)
        imgs_b = rb.read_images(tag, step=chosen)
        ok = (
            imgs_a and sample_idx < len(imgs_a)
            and imgs_b and sample_idx < len(imgs_b)
        )
        if ok:
            pa = ra.log_dir / imgs_a[sample_idx]["path"]
            pb = rb.log_dir / imgs_b[sample_idx]["path"]
            if pa.exists() and pb.exists():
                cmp.render_image_compare(
                    pa, pb, run_a, run_b, section_key
                )
                return
        st.info("No output images for this step/sample.")

    elif out_type == "text":
        ta = ra.read_texts(tag, step=chosen)
        tb = rb.read_texts(tag, step=chosen)
        t_a = ta[sample_idx]["content"] if (
            ta and sample_idx < len(ta)
        ) else ""
        t_b = tb[sample_idx]["content"] if (
            tb and sample_idx < len(tb)
        ) else ""
        ref = None
        if spec.gt:
            gt_tag = config.get(spec.gt[0])
            if gt_tag:
                ref_rows = ra.read_texts(gt_tag, step=chosen)
                if ref_rows and sample_idx < len(ref_rows):
                    ref = ref_rows[sample_idx]["content"]
        cmp.render_text_compare(
            t_a, t_b, run_a, run_b, section_key, reference=ref
        )

    elif out_type == "video":
        va = ra.read_videos(tag, step=chosen)
        vb = rb.read_videos(tag, step=chosen)
        ok = (
            va and sample_idx < len(va)
            and vb and sample_idx < len(vb)
        )
        if ok:
            pa = ra.log_dir / va[sample_idx]["path"]
            pb = rb.log_dir / vb[sample_idx]["path"]
            if pa.exists() and pb.exists():
                cmp.render_video_compare(
                    pa, pb, run_a, run_b, section_key
                )
                return
        st.info("No output videos for this step/sample.")

    elif out_type == "audio":
        aa = ra.read_audios(tag, step=chosen)
        ab = rb.read_audios(tag, step=chosen)
        ok = (
            aa and sample_idx < len(aa)
            and ab and sample_idx < len(ab)
        )
        if ok:
            pa = ra.log_dir / aa[sample_idx]["path"]
            pb = rb.log_dir / ab[sample_idx]["path"]
            if pa.exists() and pb.exists():
                cmp.render_audio_compare(
                    pa, pb, run_a, run_b, section_key
                )
                return
        st.info("No output audio for this step/sample.")
