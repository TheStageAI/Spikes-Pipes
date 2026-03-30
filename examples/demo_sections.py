"""Generate demo data that exercises every section type.

Usage:
    python examples/demo_sections.py
    spikesnpipes --logdir demo_sections
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spikesnpipes as sp

STEPS = [0, 100, 500, 1000, 2000]
SR = 16000
PROMPTS = [
    "a red car on a mountain road at sunset",
    "a fluffy cat sitting on a windowsill",
    "an astronaut riding a horse on mars",
]
TRANSLATIONS_SRC = [
    "Hello, how are you today?",
    "The weather is beautiful.",
    "I love programming in Python.",
]
TRANSLATIONS_REF = [
    "Bonjour, comment allez-vous aujourd'hui ?",
    "Le temps est magnifique.",
    "J'adore programmer en Python.",
]
ASR_TRANSCRIPTS = [
    "the quick brown fox jumps over the lazy dog",
    "hello world this is a test",
    "speech recognition is fascinating technology",
]
VLM_QUESTIONS = [
    "What objects are in this image?",
    "Describe the colours you see.",
    "How many shapes are visible?",
]


def _make_image(
    h: int, w: int, run_idx: int, step: int, sample: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Produce an image that is visually distinct per run, step, sample."""
    img = np.zeros((h, w, 3), dtype=np.uint8)

    base_color = (
        np.array([30, 100, 220])
        if run_idx == 0
        else np.array([220, 60, 30])
    )

    t = step / 2000
    y_grid, x_grid = np.mgrid[0:h, 0:w].astype(np.float32)
    freq = 3.0 + sample * 1.5 + t * 2
    pattern = np.sin(x_grid / w * freq * np.pi) * np.cos(
        y_grid / h * freq * np.pi
    )
    pattern = (pattern * 0.5 + 0.5)

    for c in range(3):
        val = base_color[c] * pattern * (0.4 + t * 0.6)
        noise = rng.integers(-8, 9, size=(h, w))
        img[:, :, c] = np.clip(val + noise, 0, 255).astype(np.uint8)

    return img


def _make_video(
    n_frames: int, h: int, w: int, run_idx: int, step: int,
) -> np.ndarray:
    """Produce a short video clip distinct per run and step.

    Returns uint8 array of shape (n_frames, h, w, 3).
    A coloured bar sweeps across the frame; colour and speed
    differ between runs.
    """
    frames = np.zeros((n_frames, h, w, 3), dtype=np.uint8)
    base = (
        np.array([30, 100, 220])
        if run_idx == 0
        else np.array([220, 60, 30])
    )
    bar_w = w // 5
    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)
        progress = step / 2000
        brightness = 0.4 + 0.6 * progress
        x_center = int(t * (w + bar_w)) - bar_w // 2
        x0 = max(0, x_center - bar_w // 2)
        x1 = min(w, x_center + bar_w // 2)
        bg = (base * 0.15 * brightness).astype(np.uint8)
        frames[i, :, :] = bg
        if x1 > x0:
            frames[i, :, x0:x1] = (base * brightness).astype(np.uint8)
    return frames


def _sine_wave(freq: float, duration: float = 1.0) -> np.ndarray:
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    return (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def create_run(
    name: str,
    base_dir: str,
    run_idx: int,
    seed: int,
) -> None:
    rng = np.random.default_rng(seed)
    w = sp.Writer(f"{base_dir}/{name}")

    noise = 0.04 if run_idx == 0 else 0.08

    # ---- scalars ----------------------------------------------------------
    for step in range(0, 2001, 2):
        t = step / 2000
        loss = 2.0 * np.exp(-4 * t) + noise * rng.normal()
        w.add_scalar("Train/Loss", step=step, val=max(0.0, loss))
        val_loss = 2.2 * np.exp(-3 * t) + noise * 1.5 * rng.normal()
        w.add_scalar("Val/Loss", step=step, val=max(0.0, val_loss))
        lr = 1e-3 * max(0, 1 - t)
        w.add_scalar("Train/LR", step=step, val=lr)

    hue_offset = run_idx * 0.3

    # ---- data for sections (per step) ------------------------------------
    for step in STEPS:
        t = step / 2000

        # text_to_image: one prompt + one output per step
        w.add_text("Diff/Prompt", text=PROMPTS[0], step=step)
        w.add_images(
            "Diff/Output",
            images=[_make_image(128, 128, run_idx, step, 0, rng)],
            step=step,
        )

        # text_to_text: one source → one output per step
        src, ref = TRANSLATIONS_SRC[0], TRANSLATIONS_REF[0]
        w.add_text("MT/Source", text=src, step=step)
        w.add_text("MT/Reference", text=ref, step=step)
        words = ref.split()
        if run_idx == 1 and len(words) > 2:
            words[2] = words[2][::-1]
        w.add_text("MT/Output", text=" ".join(words), step=step)

        # audio_to_text (ASR): one audio + GT + prediction per step
        freq_asr = 220 + step * 0.1 + run_idx * 110
        w.add_audio(
            "ASR/Audio",
            audio=_sine_wave(freq_asr, 1.5),
            step=step, sr=SR,
        )
        gt = ASR_TRANSCRIPTS[0]
        w.add_text("ASR/GroundTruth", text=gt, step=step)
        pred_words = gt.split()
        if run_idx == 1 and len(pred_words) > 3:
            pred_words[3] = pred_words[3][:2]
        w.add_text(
            "ASR/Prediction", text=" ".join(pred_words), step=step,
        )

        # text_to_audio (TTS): one text → one audio per step
        w.add_text("TTS/Text", text=TRANSLATIONS_SRC[0], step=step)
        freq_tts = 330 + run_idx * 200 + step * 0.05
        w.add_audio(
            "TTS/Audio",
            audio=_sine_wave(freq_tts, 2.0),
            step=step, sr=SR,
        )

        # text_image_to_image: prompt + shared input → output
        w.add_text(
            "Edit/Prompt", text=f"edit: {PROMPTS[0]}", step=step
        )
        fixed_rng = np.random.default_rng(777)
        inp = _make_image(128, 128, 0, 0, 0, fixed_rng)
        w.add_images("Edit/Input", images=[inp], step=step)
        out = _make_image(128, 128, run_idx, step, 1, rng)
        w.add_images("Edit/Output", images=[out], step=step)

        # text_image_to_text (VLM): image + question → answer
        vlm_img = _make_image(128, 128, run_idx, step, 2, rng)
        w.add_images("VLM/Image", images=[vlm_img], step=step)
        w.add_text("VLM/Prompt", text=VLM_QUESTIONS[0], step=step)
        answer = (
            f"Blue sinusoidal pattern, step {step}"
            if run_idx == 0
            else f"Red sinusoidal pattern, step {step}"
        )
        w.add_text("VLM/Output", text=answer, step=step)

        # plain images for gallery
        gallery = [
            _make_image(64, 64, run_idx, step, j, rng)
            for j in range(4)
        ]
        w.add_images("Train/Samples", images=gallery, step=step)

        # text_to_video: prompt → generated video clip (16:9)
        w.add_text("VGen/Prompt", text=PROMPTS[0], step=step)
        vid = _make_video(24, 144, 256, run_idx, step)
        w.add_video("VGen/Output", video=vid, step=step)

        # text_image_to_video: prompt + still → animated clip (16:9)
        w.add_text("Anim/Prompt", text=f"animate: {PROMPTS[0]}", step=step)
        still = _make_image(64, 64, run_idx, step, 0, rng)
        w.add_images("Anim/Input", images=[still], step=step)
        anim = _make_video(24, 144, 256, run_idx, step)
        w.add_video("Anim/Output", video=anim, step=step)

    # ---- register sections ------------------------------------------------
    w.create_text_to_image_section(
        "Diffusion Eval",
        prompt_tag="Diff/Prompt",
        output_tag="Diff/Output",
        description=(
            "Stable Diffusion v2.1 text-to-image generation. "
            "Evaluating prompt adherence and visual quality "
            "across model variants."
        ),
    )
    w.create_text_to_image_comparison(
        "Diffusion Comparison",
        prompt_tag="Diff/Prompt",
        output_tag="Diff/Output",
        description=(
            "Pixel-level A/B comparison of diffusion outputs. "
            "Use **toggle** to flicker between original and "
            "compressed model, or **pixel diff** to see deltas."
        ),
    )
    w.create_text_to_text_section(
        "Translation Eval",
        input_tag="MT/Source",
        output_tag="MT/Output",
        ground_truth_tag="MT/Reference",
        description=(
            "English → French machine translation. "
            "Comparing model output against human reference."
        ),
    )
    w.create_text_to_text_comparison(
        "Translation Comparison",
        input_tag="MT/Source",
        output_tag="MT/Output",
        ground_truth_tag="MT/Reference",
        description=(
            "Word-level diff between original and compressed "
            "translation models. Highlights regressions in "
            "translation quality."
        ),
    )
    w.create_audio_to_text_section(
        "ASR Eval",
        audio_tag="ASR/Audio",
        prediction_tag="ASR/Prediction",
        ground_truth_tag="ASR/GroundTruth",
        description=(
            "Automatic speech recognition evaluation. "
            "Listen to input audio and compare predicted "
            "transcript against ground truth."
        ),
    )
    w.create_audio_to_text_comparison(
        "ASR Comparison",
        audio_tag="ASR/Audio",
        prediction_tag="ASR/Prediction",
        ground_truth_tag="ASR/GroundTruth",
        description=(
            "A/B comparison of ASR predictions. Word-level diff "
            "shows where the compressed model drops or changes words."
        ),
    )
    w.create_text_to_audio_section(
        "TTS Eval",
        input_tag="TTS/Text",
        output_tag="TTS/Audio",
        description=(
            "Text-to-speech synthesis evaluation. "
            "Compare audio naturalness across model variants."
        ),
    )
    w.create_text_to_audio_comparison(
        "TTS Comparison",
        input_tag="TTS/Text",
        output_tag="TTS/Audio",
        description=(
            "Side-by-side TTS audio playback. "
            "Listen to both runs for the same input text."
        ),
    )
    w.create_text_image_to_image_section(
        "Image Edit Eval",
        prompt_tag="Edit/Prompt",
        input_image_tag="Edit/Input",
        output_tag="Edit/Output",
        description=(
            "Instruction-based image editing. Shows the edit "
            "prompt, source image, and edited output per run."
        ),
    )
    w.create_text_image_to_image_comparison(
        "Image Edit Comparison",
        prompt_tag="Edit/Prompt",
        input_image_tag="Edit/Input",
        output_tag="Edit/Output",
        description=(
            "A/B comparison of image edits. Toggle between "
            "original and compressed model outputs to check "
            "for artefacts introduced by compression."
        ),
    )
    w.create_text_image_to_text_section(
        "VLM Eval",
        prompt_tag="VLM/Prompt",
        input_image_tag="VLM/Image",
        output_tag="VLM/Output",
        description=(
            "Vision-language model evaluation. "
            "Shows image, question, and model answer per run."
        ),
    )
    w.create_text_image_to_text_comparison(
        "VLM Comparison",
        prompt_tag="VLM/Prompt",
        input_image_tag="VLM/Image",
        output_tag="VLM/Output",
        description=(
            "A/B comparison of VLM answers. Word-level diff "
            "highlights semantic changes between model variants."
        ),
    )
    w.create_text_to_video_section(
        "Video Gen Eval",
        prompt_tag="VGen/Prompt",
        output_tag="VGen/Output",
        description=(
            "Text-to-video generation. Shows the prompt and "
            "generated clip for each run."
        ),
    )
    w.create_text_to_video_comparison(
        "Video Gen Comparison",
        prompt_tag="VGen/Prompt",
        output_tag="VGen/Output",
        description=(
            "Synchronized A/B video playback. Single play button "
            "controls both clips; use frame stepping to inspect "
            "frame-level differences."
        ),
    )
    w.create_text_image_to_video_section(
        "Animation Eval",
        prompt_tag="Anim/Prompt",
        input_image_tag="Anim/Input",
        output_tag="Anim/Output",
        description=(
            "Image animation evaluation. Shows prompt, source "
            "still, and animated output per run."
        ),
    )
    w.create_text_image_to_video_comparison(
        "Animation Comparison",
        prompt_tag="Anim/Prompt",
        input_image_tag="Anim/Input",
        output_tag="Anim/Output",
        description=(
            "Synchronized A/B comparison of animated clips. "
            "Verify temporal consistency between model variants."
        ),
    )

    w.close()
    print(f"  ✓ {name}")


def main() -> None:
    base = "demo_sections"
    print("Generating comprehensive section demo …")
    create_run("original", base, run_idx=0, seed=42)
    create_run("compressed", base, run_idx=1, seed=99)
    print(
        f"\nDone — launch with:\n"
        f"  spikesnpipes --logdir {base}"
    )


if __name__ == "__main__":
    main()
