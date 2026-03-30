<p align="center">
  <img src="spikesnpipes/static/spikes_logo.png" alt="Spikes & Pipes" width="280">
</p>

Local-first experiment dashboard for deep learning. Log metrics, media, and
structured evaluation data from your training scripts, then compare runs
in a rich Streamlit UI — scalars, images, video, audio, text, with built-in
A/B comparison tools (toggle/flicker, pixel diff, word diff, synced zoom,
synced video playback).

---

## Install

```bash
pip install -e .
```

## Quick start

```bash
python examples/demo_sections.py      # generates two demo runs
spikesnpipes --logdir demo_sections    # open http://localhost:8501
```

---

## What's inside

### Training logging

Log data from your training loop. The dashboard auto-discovers tags and
renders them.

| What | API | Formats |
|------|-----|---------|
| [Scalars](#scalars) | `add_scalar` | loss, lr, metrics — any float |
| [Images](#images) | `add_images` | numpy `uint8`/`float32`, PIL, file path |
| [Video](#video) | `add_video`, `add_videos` | numpy `uint8 (T,H,W,3)`, file path |
| [Audio](#audio) | `add_audio`, `add_audios` | numpy `float32`/`int16`, file path, bytes |
| [Text](#text) | `add_text` | plain text or markdown |

### Evaluation sections

Structured layouts for inspecting model outputs across runs. Shows all
selected runs side-by-side with a step slider.

| Section | Use case |
|---------|----------|
| [Text → Image eval](#eval-t2i) | Diffusion, text-to-image generation |
| [Text → Text eval](#eval-t2t) | Translation, LLM, summarisation |
| [Audio → Text eval](#eval-a2t) | ASR / speech recognition |
| [Text → Audio eval](#eval-t2a) | TTS / speech synthesis |
| [Text + Image → Image eval](#eval-ti2i) | Editing, inpainting, style transfer |
| [Text + Image → Text eval](#eval-ti2t) | VLM, visual QA |
| [Text → Video eval](#eval-t2v) | Video generation |
| [Text + Image → Video eval](#eval-ti2v) | Image animation |

### Comparison sections

Built for **model compression, acceleration, and distillation** engineers.
When you optimise a model (quantize, prune, distil), you need to verify
the compressed version still matches the original. Comparison sections give
you precise A/B tools to catch regressions that metrics alone might miss.

| Section | Tools |
|---------|-------|
| [Text → Image comparison](#cmp-t2i) | Toggle/flicker, pixel diff ×10, synced zoom & pan |
| [Text → Text comparison](#cmp-t2t) | Word-level diff (green = added, red = removed) |
| [Audio → Text comparison](#cmp-a2t) | Word-level diff |
| [Text → Audio comparison](#cmp-t2a) | A/B playback |
| [Text + Image → Image comparison](#cmp-ti2i) | Toggle/flicker, pixel diff ×10, synced zoom & pan |
| [Text + Image → Text comparison](#cmp-ti2t) | Word-level diff |
| [Text → Video comparison](#cmp-t2v) | Synced playback, frame stepping, speed control |
| [Text + Image → Video comparison](#cmp-ti2v) | Synced playback, frame stepping, speed control |

---

## Training logging

Add this to your training script:

```python
import spikesnpipes as sp

w = sp.Writer("runs/my_run")

for step in range(num_steps):
    w.add_scalar("Train/Loss", step=step, val=loss)

w.close()
```

### Scalars

```python
w.add_scalar("Train/Loss", step=100, val=0.42)
w.add_scalar("Train/LR", step=100, val=3e-4, x=0.42)  # custom x-axis
```

### Images

```python
w.add_images("Gen/Output", images=[output_img], step=step)
w.add_images("Gen/Batch", images=[img1, img2, img3], step=step)
```

Accepted inputs per image:

| Type | Range |
|------|-------|
| numpy `uint8` `(H,W,3)` | 0 – 255 |
| numpy `float32` `(H,W,3)` | 0.0 – 1.0, auto-scaled to 0–255 |
| `PIL.Image` | saved directly |
| `str` / `Path` | copied from disk |

### Video

```python
w.add_video("Gen/Video", video=frames, step=step)
w.add_videos("Gen/Videos", videos=[v1, v2], step=step)
```

| Type | Range |
|------|-------|
| numpy `uint8` `(T, H, W, 3)` | 0 – 255, saved as mp4 |
| `str` / `Path` | copied from disk |

### Audio

```python
w.add_audio("TTS/Output", audio=waveform, step=step, sr=16000)
w.add_audios("ASR/Batch", audios=[wav1, wav2], step=step, sr=16000)
```

| Type | Range |
|------|-------|
| numpy `float32` | -1.0 to 1.0, saved as WAV |
| numpy `int16` | raw PCM, saved as WAV |
| `str` / `Path` | copied from disk |
| `bytes` | written as-is |

### Text

```python
w.add_text("Train/Log", text="epoch 1 done", step=step)
w.add_text("LLM/Output", text="markdown **works** here", step=step)
```

---

## Evaluation sections

Eval sections show model outputs for all selected runs side-by-side.
Add the `add_*` calls to your training/eval loop, then register the
section once.

<a id="eval-t2i"></a>

### Text → Image eval

```python
w.add_text("Gen/Prompt", text=prompt, step=step)
w.add_images("Gen/Output", images=[generated_image], step=step)

w.create_text_to_image_section("Diffusion Eval",
    prompt_tag="Gen/Prompt", output_tag="Gen/Output")
```

<a id="eval-t2t"></a>

### Text → Text eval

```python
w.add_text("MT/Source", text=source, step=step)
w.add_text("MT/Output", text=model_output, step=step)
w.add_text("MT/Ref", text=reference, step=step)          # optional

w.create_text_to_text_section("Translation Eval",
    input_tag="MT/Source", output_tag="MT/Output",
    ground_truth_tag="MT/Ref")
```

<a id="eval-a2t"></a>

### Audio → Text eval

```python
w.add_audio("ASR/Audio", audio=waveform, step=step, sr=16000)
w.add_text("ASR/GT", text=transcript, step=step)
w.add_text("ASR/Pred", text=prediction, step=step)

w.create_audio_to_text_section("ASR Eval",
    audio_tag="ASR/Audio", prediction_tag="ASR/Pred",
    ground_truth_tag="ASR/GT")
```

<a id="eval-t2a"></a>

### Text → Audio eval

```python
w.add_text("TTS/Text", text=input_text, step=step)
w.add_audio("TTS/Audio", audio=synthesised_wav, step=step, sr=22050)

w.create_text_to_audio_section("TTS Eval",
    input_tag="TTS/Text", output_tag="TTS/Audio")
```

<a id="eval-ti2i"></a>

### Text + Image → Image eval

```python
w.add_text("Edit/Prompt", text=instruction, step=step)
w.add_images("Edit/Input", images=[source_image], step=step)
w.add_images("Edit/Output", images=[edited_image], step=step)

w.create_text_image_to_image_section("Edit Eval",
    prompt_tag="Edit/Prompt", input_image_tag="Edit/Input",
    output_tag="Edit/Output")
```

<a id="eval-ti2t"></a>

### Text + Image → Text eval

```python
w.add_text("VLM/Question", text=question, step=step)
w.add_images("VLM/Image", images=[input_image], step=step)
w.add_text("VLM/Answer", text=model_answer, step=step)

w.create_text_image_to_text_section("VLM Eval",
    prompt_tag="VLM/Question", input_image_tag="VLM/Image",
    output_tag="VLM/Answer")
```

<a id="eval-t2v"></a>

### Text → Video eval

```python
w.add_text("VGen/Prompt", text=prompt, step=step)
w.add_video("VGen/Output", video=generated_frames, step=step)

w.create_text_to_video_section("Video Gen",
    prompt_tag="VGen/Prompt", output_tag="VGen/Output")
```

<a id="eval-ti2v"></a>

### Text + Image → Video eval

```python
w.add_text("Anim/Prompt", text=prompt, step=step)
w.add_images("Anim/Input", images=[still_image], step=step)
w.add_video("Anim/Output", video=animated_frames, step=step)

w.create_text_image_to_video_section("Animate Eval",
    prompt_tag="Anim/Prompt", input_image_tag="Anim/Input",
    output_tag="Anim/Output")
```

---

## Comparison sections

Comparison sections are designed for engineers working on **model
compression, acceleration, and distillation**. You have a reference model
and a compressed variant — you need to verify the outputs still match.

### How it works

You run the same script for each model. Each run logs to its own
directory using the same tag names. The dashboard discovers both and
lets you A/B them.

**Your eval script:**

```python
# eval.py
import argparse
import spikesnpipes as sp

parser = argparse.ArgumentParser()
parser.add_argument("--run_name", required=True)
args = parser.parse_args()

w = sp.Writer(f"runs/{args.run_name}")

# register comparison section (same tags for every run)
w.create_text_to_image_comparison("Diffusion Compare",
    prompt_tag="Gen/Prompt", output_tag="Gen/Output")

# your eval loop
for step, (prompt, image) in enumerate(eval_results):
    w.add_text("Gen/Prompt", text=prompt, step=step)
    w.add_images("Gen/Output", images=[image], step=step)

w.close()
```

**Run it for each model:**

```bash
python eval.py --run_name original
python eval.py --run_name compressed
```

**Launch the dashboard:**

```bash
spikesnpipes --logdir runs
```

```
runs/
├── original/       ← reference model outputs
│   └── spikes.db
└── compressed/     ← compressed model outputs
    └── spikes.db
```

The dashboard shows both runs. Pick Run A and Run B, then use toggle,
pixel diff, word diff, or synced zoom to spot regressions.

<a id="cmp-t2i"></a>

### Text → Image comparison

```python
w.add_text("Gen/Prompt", text=prompt, step=step)
w.add_images("Gen/Output", images=[generated_image], step=step)

w.create_text_to_image_comparison("Diffusion Compare",
    prompt_tag="Gen/Prompt", output_tag="Gen/Output")
```

Toggle/flicker between original and compressed outputs. Pixel diff
with ×10 amplification. Synced zoom at 100%/200%/400% with mouse-drag
panning.

<a id="cmp-t2t"></a>

### Text → Text comparison

```python
w.add_text("MT/Source", text=source, step=step)
w.add_text("MT/Output", text=model_output, step=step)
w.add_text("MT/Ref", text=reference, step=step)          # optional

w.create_text_to_text_comparison("Translation Compare",
    input_tag="MT/Source", output_tag="MT/Output",
    ground_truth_tag="MT/Ref")
```

Word-level diff highlighting: green = added, red = removed.

<a id="cmp-a2t"></a>

### Audio → Text comparison

```python
w.add_audio("ASR/Audio", audio=waveform, step=step, sr=16000)
w.add_text("ASR/GT", text=transcript, step=step)
w.add_text("ASR/Pred", text=prediction, step=step)

w.create_audio_to_text_comparison("ASR Compare",
    audio_tag="ASR/Audio", prediction_tag="ASR/Pred",
    ground_truth_tag="ASR/GT")
```

<a id="cmp-t2a"></a>

### Text → Audio comparison

```python
w.add_text("TTS/Text", text=input_text, step=step)
w.add_audio("TTS/Audio", audio=synthesised_wav, step=step, sr=22050)

w.create_text_to_audio_comparison("TTS Compare",
    input_tag="TTS/Text", output_tag="TTS/Audio")
```

A/B playback — listen to both outputs for the same input.

<a id="cmp-ti2i"></a>

### Text + Image → Image comparison

```python
w.add_text("Edit/Prompt", text=instruction, step=step)
w.add_images("Edit/Input", images=[source_image], step=step)
w.add_images("Edit/Output", images=[edited_image], step=step)

w.create_text_image_to_image_comparison("Edit Compare",
    prompt_tag="Edit/Prompt", input_image_tag="Edit/Input",
    output_tag="Edit/Output")
```

Toggle/flicker, pixel diff, synced zoom — same tools as Text → Image.

<a id="cmp-ti2t"></a>

### Text + Image → Text comparison

```python
w.add_text("VLM/Question", text=question, step=step)
w.add_images("VLM/Image", images=[input_image], step=step)
w.add_text("VLM/Answer", text=model_answer, step=step)

w.create_text_image_to_text_comparison("VLM Compare",
    prompt_tag="VLM/Question", input_image_tag="VLM/Image",
    output_tag="VLM/Answer")
```

<a id="cmp-t2v"></a>

### Text → Video comparison

```python
w.add_text("VGen/Prompt", text=prompt, step=step)
w.add_video("VGen/Output", video=generated_frames, step=step)

w.create_text_to_video_comparison("Video Compare",
    prompt_tag="VGen/Prompt", output_tag="VGen/Output")
```

Synced playback with a single play button, frame-by-frame stepping, and
speed control (0.25× – 2×).

<a id="cmp-ti2v"></a>

### Text + Image → Video comparison

```python
w.add_text("Anim/Prompt", text=prompt, step=step)
w.add_images("Anim/Input", images=[still_image], step=step)
w.add_video("Anim/Output", video=animated_frames, step=step)

w.create_text_image_to_video_comparison("Animate Compare",
    prompt_tag="Anim/Prompt", input_image_tag="Anim/Input",
    output_tag="Anim/Output")
```

Synced playback — same controls as Text → Video comparison.

---

### Section descriptions

Every `create_*` method accepts an optional `description` (markdown):

```python
w.create_text_to_image_comparison("Diffusion Compare",
    prompt_tag="Gen/Prompt", output_tag="Gen/Output",
    description="Comparing SD v1.5 vs quantized INT8 variant.")
```

---

## CLI reference

```
spikesnpipes --logdir <path>          # required
             --host 0.0.0.0           # default: localhost
             --port 8501              # default: 8501
```

---

## Full demo

```bash
python examples/demo_sections.py
spikesnpipes --logdir demo_sections
```

Creates two runs (`original` and `compressed`) with scalars, images,
video, text, audio, and every section type listed above.
