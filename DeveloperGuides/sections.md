# Evaluation Sections — Developer Guide

Ready-to-go section types for common ML evaluation workflows.
Each section defines what data to log (Writer API), how to store it
(database tags), and how to render it (dashboard layout).

---

## Taxonomy

Every DL task gets a **pair** of section types:

| Variant        | Purpose                                          |
|----------------|--------------------------------------------------|
| **Eval**       | Inspect results: input → output (+ optional GT). One output column per run. |
| **Comparison** | Detailed A/B: input + outputs from two runs with advanced comparison tools (toggle/flicker, pixel diff, synced zoom, word diff, etc.). Designed for model compression, distillation, acceleration, and any scenario where you need to spot per-pixel or per-word differences. |

Plus two standalone categories:

| Category         | Purpose                                        |
|------------------|------------------------------------------------|
| **Specialised**  | Detection, segmentation — task-specific overlays. |
| **Custom**       | `row`, `scalars` — user-defined widget layouts.  |

---

## Database additions

### `audios` table (new)

Required for ASR, TTS, voice conversion, and any audio workflow.

| column      | type    | notes                               |
|-------------|---------|-------------------------------------|
| id          | INTEGER | primary key                         |
| tag         | TEXT    | hierarchical name                   |
| step        | INTEGER | global step                         |
| idx         | INTEGER | position inside the batch (0-based) |
| path        | TEXT    | relative path from log dir          |
| format      | TEXT    | `wav`, `mp3`, `flac`, …             |
| duration    | REAL    | duration in seconds (nullable)      |
| sample_rate | INTEGER | sample rate in Hz (nullable)        |
| wall_time   | REAL    |                                     |

Index: `(tag, step)`.

Directory layout:

```
sp_logs/
├── audios/
│   └── ASR_Audio/
│       ├── step_0100_000.wav
│       └── step_0100_001.wav
```

### Writer API addition

```python
writer.add_audio("ASR/Audio", audio=waveform_np, step=100, sr=16000)
writer.add_audios("ASR/Audio", audios=[wav0, wav1], step=100, sr=16000)
```

Accepts numpy arrays (`samples,` or `samples × channels`), file paths,
or bytes. Saved as WAV by default.

---

## Shared concepts

### Step slider

All non-scalar sections include a log-scale step slider
(10 fixed stops, see `dashboard.md § Step slider`).

### Multi-run behaviour

Every generation section has two modes:

| Runs selected | Behaviour                                     |
|---------------|-----------------------------------------------|
| 1             | Input on left, output on right.               |
| 2+            | Input on left, one output column per run.     |

Input columns (prompt, reference image, ground truth) are always
shared — they come from the **first selected run** (inputs should be
identical across runs).

### Ground truth

Generation sections support an optional `ground_truth_tag`. When
present, a "Reference" column appears between input and outputs,
highlighted with a subtle border.

---

## Generation sections

### 1. `text_to_image` — prompt → generated image

Use cases: Stable Diffusion, DALL-E, Midjourney, ControlNet (text-only).

```
┌─ Text to Image ───────────────────────────────────────────┐
│  Step: [◄ 0 · 500 · 2k · 5k · 10k ● 20k ►]              │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Prompt      │  │  run_01     │  │  run_02     │       │
│  │              │  │             │  │             │       │
│  │  "a red car  │  │  [image]    │  │  [image]    │       │
│  │   on a       │  │             │  │             │       │
│  │   mountain"  │  │             │  │             │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                            │
│  Sample: [◄ 0  1  2  3 ►]  (batch index within step)      │
└────────────────────────────────────────────────────────────┘
```

**Config:**

```python
writer.create_text_to_image_section(
    "DiffusionEval",
    prompt_tag="Diff/Prompt",
    output_tag="Diff/Output",
    ground_truth_tag="Diff/GroundTruth",   # optional
)
```

**Storage:**

| Data      | Table  | Tag             |
|-----------|--------|-----------------|
| Prompt    | texts  | `Diff/Prompt`   |
| Output    | images | `Diff/Output`   |
| Reference | images | `Diff/GroundTruth` |

---

### 2. `text_to_text` — input text → output text

Use cases: Translation, summarization, LLM completion, code generation.

```
┌─ Text to Text ────────────────────────────────────────────┐
│  Step: [◄ 0 · 500 · 2k ● 5k ►]                           │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Input       │  │  Reference  │  │  run_01     │       │
│  │              │  │  (GT)       │  │             │       │
│  │  "Translate  │  │  "bonjour"  │  │  "salut le  │       │
│  │   hello      │  │             │  │   monde"    │       │
│  │   world"     │  │             │  │             │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                            │
│  Sample: [◄ 0  1  2 ►]   ☐ Show diff against reference    │
└────────────────────────────────────────────────────────────┘
```

When "Show diff" is enabled, changed words in each output are
highlighted (green = added, red = removed) relative to ground truth.

**Config:**

```python
writer.create_text_to_text_section(
    "Translation",
    input_tag="MT/Source",
    output_tag="MT/Output",
    ground_truth_tag="MT/Reference",   # optional
)
```

**Storage:**

| Data      | Table | Tag            |
|-----------|-------|----------------|
| Input     | texts | `MT/Source`    |
| Output    | texts | `MT/Output`    |
| Reference | texts | `MT/Reference` |

---

### 3. `text_to_video` — prompt → generated video

Use cases: Video generation (Sora, CogVideo, etc.).

```
┌─ Text to Video ───────────────────────────────────────────┐
│  Step: [◄ 0 · 1k · 5k ● 10k ►]                           │
│                                                            │
│  Prompt: "a dog running on a beach at sunset"              │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  ▶ run_01         │  │  ▶ run_02         │               │
│  │  [video player]   │  │  [video player]   │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                            │
│  Sample: [◄ 0  1 ►]                                        │
└────────────────────────────────────────────────────────────┘
```

Prompt is displayed as a full-width text block above the video columns
since videos need more horizontal space.

**Config:**

```python
writer.create_text_to_video_section(
    "VideoGen",
    prompt_tag="VGen/Prompt",
    output_tag="VGen/Output",
    ground_truth_tag="VGen/Reference",   # optional
)
```

---

### 4. `text_image_to_image` — prompt + reference image → output image

Use cases: Image editing (InstructPix2Pix), inpainting, style transfer,
ControlNet with reference, super-resolution with prompt.

```
┌─ Text+Image → Image ─────────────────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]                                 │
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Prompt    │ │ Input    │ │ run_01   │ │ run_02   │    │
│  │           │ │ Image    │ │          │ │          │    │
│  │ "make it  │ │ [image]  │ │ [image]  │ │ [image]  │    │
│  │  sunset"  │ │          │ │          │ │          │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│                                                            │
│  Sample: [◄ 0  1  2 ►]                                    │
└────────────────────────────────────────────────────────────┘
```

**Config:**

```python
writer.create_text_image_to_image_section(
    "ImageEdit",
    prompt_tag="Edit/Prompt",
    input_image_tag="Edit/Input",
    output_tag="Edit/Output",
    ground_truth_tag="Edit/GroundTruth",   # optional
)
```

**Storage:**

| Data         | Table  | Tag              |
|--------------|--------|------------------|
| Prompt       | texts  | `Edit/Prompt`    |
| Input image  | images | `Edit/Input`     |
| Output image | images | `Edit/Output`    |
| Ground truth | images | `Edit/GroundTruth` |

---

### 5. `text_image_to_video` — prompt + reference image → video

Use cases: Image-to-video animation, video generation from keyframe.

```
┌─ Text+Image → Video ─────────────────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]                                 │
│                                                            │
│  ┌──────────────────┐  Prompt: "animate the character"     │
│  │ Input Image      │                                      │
│  │ [image]          │                                      │
│  └──────────────────┘                                      │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ ▶ run_01          │  │ ▶ run_02          │               │
│  │ [video player]    │  │ [video player]    │               │
│  └──────────────────┘  └──────────────────┘               │
└────────────────────────────────────────────────────────────┘
```

Input image and prompt are shown above; video outputs below in columns.

**Config:**

```python
writer.create_text_image_to_video_section(
    "ImgAnimate",
    prompt_tag="Anim/Prompt",
    input_image_tag="Anim/Input",
    output_tag="Anim/Output",
)
```

---

### 6. `text_image_to_text` — prompt + image → output text

Use cases: VQA, VLM evaluation, image captioning with instructions,
visual grounding.

```
┌─ Text+Image → Text ──────────────────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]                                 │
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Image    │ │ Prompt   │ │ run_01   │ │ run_02   │    │
│  │          │ │          │ │          │ │          │    │
│  │ [image]  │ │"describe │ │"a cat    │ │"a pet    │    │
│  │          │ │ this     │ │ sitting  │ │ on a     │    │
│  │          │ │ image"   │ │ on sofa" │ │ couch"   │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│                                                            │
│  Sample: [◄ 0  1  2 ►]  ☐ Show diff against reference     │
└────────────────────────────────────────────────────────────┘
```

**Config:**

```python
writer.create_text_image_to_text_section(
    "VLM",
    prompt_tag="VLM/Prompt",
    input_image_tag="VLM/Image",
    output_tag="VLM/Output",
    ground_truth_tag="VLM/GroundTruth",   # optional
)
```

---

### 7. `audio_to_text` — ASR section

Use cases: Speech recognition, audio transcription, whisper eval.

```
┌─ ASR ─────────────────────────────────────────────────────┐
│  Step: [◄ 0 · 500 · 2k ● 5k ►]                           │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ #  │ Audio          │ Ground Truth │ run_01        │   │
│  │────┼────────────────┼──────────────┼───────────────│   │
│  │ 0  │ ▶ ■■■■░░ 3.2s  │ hello world  │ helo wrld     │   │
│  │ 1  │ ▶ ■■░░░░ 2.1s  │ good morning │ good morning  │   │
│  │ 2  │ ▶ ■■■■■░ 4.8s  │ how are you  │ how are u     │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Metrics:  WER: 12.3%  CER: 5.1%  (computed on the fly)   │
└────────────────────────────────────────────────────────────┘
```

Renders as a table with one row per sample in the batch. Audio is
playable inline via `st.audio`. When multiple runs are selected,
one prediction column per run is added.

**Config:**

```python
writer.create_asr_section(
    "ASR",
    audio_tag="ASR/Audio",
    ground_truth_tag="ASR/GroundTruth",
    prediction_tag="ASR/Prediction",
)
```

**Storage:**

| Data         | Table  | Tag                |
|--------------|--------|--------------------|
| Audio input  | audios | `ASR/Audio`        |
| Ground truth | texts  | `ASR/GroundTruth`  |
| Prediction   | texts  | `ASR/Prediction`   |

**Metrics** (computed on the fly in the dashboard):

| Metric | Formula                          |
|--------|----------------------------------|
| WER    | Word Error Rate (edit distance)  |
| CER    | Character Error Rate             |

Highlighted diffs: words that differ from ground truth are shown
in red in the prediction column.

---

### 8. `text_to_audio` — TTS section

Use cases: Text-to-speech, voice synthesis evaluation.

```
┌─ TTS ─────────────────────────────────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]                                  │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ #  │ Input Text     │ Reference     │ run_01       │   │
│  │────┼────────────────┼───────────────┼──────────────│   │
│  │ 0  │ hello world    │ ▶ ■■■░░ 1.2s  │ ▶ ■■░░ 1.1s  │   │
│  │ 1  │ good morning   │ ▶ ■■■■░ 1.5s  │ ▶ ■■■░ 1.4s  │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

**Config:**

```python
writer.create_tts_section(
    "TTS",
    input_tag="TTS/Text",
    output_tag="TTS/Audio",
    reference_tag="TTS/Reference",   # optional reference audio
)
```

---

## Comparison sections

### 9. `image_comparison` — advanced image comparison

Use cases: Super-resolution, image editing quality, model compression
artifacts, acceleration quality loss, A/B testing outputs.

This is the most feature-rich section. Provides four viewing modes
and synchronized navigation.

```
┌─ Image Comparison ────────────────────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]    Sample: [◄ 0  1  2 ►]       │
│                                                            │
│  Mode: ○ Side-by-side  ● Toggle  ○ Pixel diff  ○ Slider   │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │               ┌─────────────────┐                    │  │
│  │               │                 │                    │  │
│  │               │   [image A]     │                    │  │
│  │               │                 │                    │  │
│  │               └─────────────────┘                    │  │
│  │                                                      │  │
│  │  Showing: [A ⇄ B]   (click to swap / hold to peek)  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  Zoom: [Fit] [100%] [200%] [400%]   Pan: drag to scroll   │
│  Image A: [run_01 ▾]    Image B: [run_02 ▾]               │
└────────────────────────────────────────────────────────────┘
```

#### Viewing modes

**Side-by-side** (default):
Two images next to each other. Zoom and pan are synchronised —
scrolling or zooming one image applies the same transform to the other.

```
┌──────────────────┐  ┌──────────────────┐
│  [image A]       │  │  [image B]       │
│  run_01          │  │  run_02          │
└──────────────────┘  └──────────────────┘
```

**Toggle (flicker)**:
A single image view with a toggle button. Pressing the button
instantly swaps between image A and image B in the exact same
position and zoom level. The visual "flicker" makes even subtle
pixel-level differences immediately obvious — your eye catches the
change because the image occupies the same space.

```
┌─────────────────────────────┐
│                              │
│       [image A or B]         │
│                              │
│                              │
└─────────────────────────────┘
  Showing: [A ⇄ B]   ← toggle button (or hold to peek)
```

Interaction:
- **Hold** the "⇄ Hold to overlay" button — the left panel
  instantly shows image B. Release → reverts to image A.
- Implemented as client-side JavaScript (mousedown/mouseup),
  so the swap is truly instant — no Streamlit rerun, no server
  round-trip. Works even when the dashboard is loaded from a
  remote server.

**Pixel diff**:
Computes `|image_A - image_B|` per pixel and displays the absolute
difference. A colour scale from black (identical) to bright red
(maximum difference) makes artifacts clearly visible.

Options:
- `☐ Amplify ×10` — multiplies diff by 10 to reveal subtle changes.
- Tooltip shows per-pixel RGB values on hover.

**Slider** (curtain):
A vertical divider splits the view. Left half shows image A, right
half shows image B. The divider is draggable. Inspired by
before/after sliders common in image editing tools.

#### Zoom and pan

All modes support synchronized zoom. Scale buttons apply to both
images simultaneously.

| Button | Behaviour                             |
|--------|---------------------------------------|
| Fit    | Scale to fit the container (default). |
| 100%   | 1:1 pixel mapping.                    |
| 200%   | 2× zoom, centered on current view.    |
| 400%   | 4× zoom for pixel-level inspection.   |

Pan: click-and-drag scrolls both images in lockstep (like FastStone
Image Viewer's compare mode).

#### Implementation notes

- Overlay and slider use `streamlit-image-comparison` or custom
  HTML/CSS/JS component rendered via `st.components.v1.html`.
- Pixel diff is computed server-side with numpy:
  ```python
  diff = np.abs(img_a.astype(float) - img_b.astype(float))
  diff_uint8 = np.clip(diff * amplify, 0, 255).astype(np.uint8)
  ```
- Zoom/pan state is shared via Streamlit session state keyed by
  section name.

**Config:**

```python
writer.create_image_comparison_section(
    "EditComparison",
    image_tag="Edit/Output",
    prompt_tag="Edit/Prompt",            # optional, shown above
    ground_truth_tag="Edit/GroundTruth", # optional, selectable as A/B
)
```

When `prompt_tag` is provided, the prompt text is displayed above the
comparison view as a full-width block.

---

### 10. `video_comparison` — synchronised video comparison

Use cases: Video generation quality, frame interpolation, codec
comparison, temporal consistency evaluation.

```
┌─ Video Comparison ────────────────────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]                                  │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ ▶ run_01          │  │ ▶ run_02          │               │
│  │ [video player]    │  │ [video player]    │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                            │
│  ☑ Synchronise playback    Frame: [◄ 0 ──●── 120 ►]       │
└────────────────────────────────────────────────────────────┘
```

- Playback sync via JS: play/pause/seek one player → mirrors to all.
- Frame slider for manual frame-by-frame stepping.

**Config:**

```python
writer.create_video_comparison_section(
    "VideoCompare",
    video_tag="VGen/Output",
    prompt_tag="VGen/Prompt",   # optional
)
```

---

### 11. `text_comparison` — text diff comparison

Use cases: LLM output comparison, translation quality, summarisation.

```
┌─ Text Comparison ─────────────────────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]   Sample: [◄ 0  1 ►]           │
│                                                            │
│  Input: "Translate: The cat sat on the mat."               │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Reference     │  │ run_01       │  │ run_02       │    │
│  │               │  │              │  │              │    │
│  │ "Le chat      │  │ "Le chat     │  │ "Le chat     │    │
│  │  était assis  │  │  s'est assis │  │  était assis │    │
│  │  sur le       │  │  sur le      │  │  sur la      │    │
│  │  tapis."      │  │  tapis."     │  │  natte."     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                            │
│  ☐ Highlight diff vs. reference                            │
└────────────────────────────────────────────────────────────┘
```

Diff highlighting uses word-level alignment. Changed words get
a coloured background (red = deletion, green = insertion,
yellow = substitution) relative to the reference column.

**Config:**

```python
writer.create_text_comparison_section(
    "TranslationCompare",
    input_tag="MT/Source",
    output_tag="MT/Output",
    ground_truth_tag="MT/Reference",   # optional
)
```

---

## Additional section types

### 12. `audio_comparison` — audio A/B comparison

Use cases: TTS quality, voice conversion, audio enhancement.

```
┌─ Audio Comparison ────────────────────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]   Sample: [◄ 0  1 ►]           │
│                                                            │
│  Text: "Hello, how are you today?"                         │
│                                                            │
│  Reference:  ▶ ■■■■░░░░ 2.3s                               │
│                                                            │
│  run_01:     ▶ ■■■░░░░░ 2.1s                               │
│  run_02:     ▶ ■■■■░░░░ 2.4s                               │
│                                                            │
│  ☐ Show waveform   ☐ Show spectrogram                      │
└────────────────────────────────────────────────────────────┘
```

Optional waveform/spectrogram visualisation rendered as Plotly charts.

**Config:**

```python
writer.create_audio_comparison_section(
    "VoiceCompare",
    audio_tag="VC/Output",
    text_tag="VC/Text",             # optional
    reference_tag="VC/Reference",   # optional
)
```

---

### 13. `detection` — object detection visualisation

Use cases: YOLO, DETR, any bounding-box model evaluation.

```
┌─ Detection ───────────────────────────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]   Sample: [◄ 0  1  2 ►]        │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Ground Truth      │  │ run_01            │               │
│  │ [image + boxes]   │  │ [image + boxes]   │               │
│  │  cat: 0.98        │  │  cat: 0.92        │               │
│  │  dog: 0.95        │  │  dog: 0.87        │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                            │
│  Confidence: [0.5 ───●─── 1.0]   ☑ Show labels            │
│  Metrics: mAP@0.5: 0.82  mAP@0.75: 0.71                   │
└────────────────────────────────────────────────────────────┘
```

Bounding boxes are rendered as overlays on images. A confidence
threshold slider filters displayed boxes. Boxes are colour-coded by
class.

**Storage:** Detections are stored as JSON text entries:

```python
writer.add_text("Det/Predictions", text=json.dumps({
    "boxes": [[x1,y1,x2,y2], ...],
    "labels": ["cat", "dog", ...],
    "scores": [0.92, 0.87, ...],
}), step=100)
```

**Config:**

```python
writer.create_detection_section(
    "Detection",
    image_tag="Det/Image",
    prediction_tag="Det/Predictions",
    ground_truth_tag="Det/GroundTruth",   # optional
)
```

---

### 14. `segmentation` — mask overlay visualisation

Use cases: Semantic segmentation, instance segmentation, panoptic.

```
┌─ Segmentation ────────────────────────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]   Sample: [◄ 0  1 ►]           │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Ground Truth      │  │ run_01            │               │
│  │ [image + mask     │  │ [image + mask     │               │
│  │  overlay]         │  │  overlay]         │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                            │
│  Opacity: [0% ───●─── 100%]   Class: [All ▾]              │
│  Metrics: mIoU: 0.76                                       │
└────────────────────────────────────────────────────────────┘
```

Masks are stored as PNG images (class index encoded as pixel value).
Colour palette for classes is defined in section config.

**Config:**

```python
writer.create_segmentation_section(
    "Segmentation",
    image_tag="Seg/Image",
    prediction_tag="Seg/Prediction",
    ground_truth_tag="Seg/GroundTruth",
    class_names=["background", "person", "car", "tree"],
)
```

---

## Full section type reference — eval / comparison pairs

Every DL task has an **eval** section and a matching **comparison**
section. Use eval for inspecting results; use comparison when you need
to spot per-pixel or per-word differences (compression, distillation,
acceleration, A/B testing).

### Pair table

| DL Task               | Eval section            | Comparison section               | Output type |
|-----------------------|-------------------------|----------------------------------|-------------|
| Text → Image          | `text_to_image`         | `text_to_image_comparison`       | image       |
| Text → Text           | `text_to_text`          | `text_to_text_comparison`        | text        |
| Text → Video          | `text_to_video`         | `text_to_video_comparison`       | video       |
| Text → Audio          | `text_to_audio`         | `text_to_audio_comparison`       | audio       |
| Audio → Text          | `audio_to_text`         | `audio_to_text_comparison`       | text        |
| Text+Image → Image    | `text_image_to_image`   | `text_image_to_image_comparison` | image       |
| Text+Image → Video    | `text_image_to_video`   | `text_image_to_video_comparison` | video       |
| Text+Image → Text     | `text_image_to_text`    | `text_image_to_text_comparison`  | text        |

### What each variant does

**Eval section** — inspect results from one or more runs:
- Input on the left, one output column per selected run on the right.
- Optional ground truth column between input and outputs.
- Quick visual overview of model quality across many samples.

**Comparison section** — detailed A/B between exactly two runs:
- Shows shared input (prompt, image, audio).
- Two outputs side-by-side with **advanced comparison tools** specific
  to the output type:

| Output type | Comparison tools                                           |
|-------------|------------------------------------------------------------|
| **image**   | Toggle/flicker, pixel diff (with amplify), curtain slider, synced zoom (Fit/100%/200%/400%), synced pan |
| **video**   | Synchronised playback, frame-by-frame stepping             |
| **text**    | Word-level diff highlighting (green=added, red=removed, yellow=changed) |
| **audio**   | A/B playback toggle, optional waveform/spectrogram overlay |

Example — model compression comparison for image generation:

```
┌─ Diffusion Compression Comparison ────────────────────────┐
│  Step: [◄ 0 · 1k ● 5k ►]   Sample: [◄ 0  1  2 ►]        │
│                                                            │
│  Prompt: "a red car on a mountain road at sunset"          │
│                                                            │
│  Mode: ● Side-by-side  ○ Toggle  ○ Pixel diff  ○ Slider   │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ run_original      │  │ run_compressed    │               │
│  │ [image]           │  │ [image]           │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                            │
│  Zoom: [Fit] [100%] [200%] [400%]                          │
│  A: [run_original ▾]    B: [run_compressed ▾]              │
└────────────────────────────────────────────────────────────┘
```

### Standalone sections (no pair)

| Type           | Purpose                                    |
|----------------|--------------------------------------------|
| `detection`    | Bounding box overlay + confidence slider   |
| `segmentation` | Mask overlay + class filtering             |
| `row`          | Custom widget layout (user-defined)        |
| `scalars`      | Line charts (auto-discovered)              |

---

## Writer API summary

### Data logging

```python
# Scalars
writer.add_scalar(tag, step, val, x=None)

# Media
writer.add_images(tag, images, step, fmt="png")
writer.add_video(tag, video, step, fmt="mp4")
writer.add_videos(tag, videos, step, fmt="mp4")
writer.add_text(tag, text, step)
writer.add_audio(tag, audio, step, sr=16000, fmt="wav")      # new
writer.add_audios(tag, audios, step, sr=16000, fmt="wav")    # new
```

### Eval section constructors

```python
writer.create_text_to_image_section(name, prompt_tag, output_tag, ground_truth_tag=None)
writer.create_text_to_text_section(name, input_tag, output_tag, ground_truth_tag=None)
writer.create_text_to_video_section(name, prompt_tag, output_tag, ground_truth_tag=None)
writer.create_text_to_audio_section(name, input_tag, output_tag, reference_tag=None)
writer.create_audio_to_text_section(name, audio_tag, prediction_tag, ground_truth_tag=None)
writer.create_text_image_to_image_section(name, prompt_tag, input_image_tag, output_tag, ground_truth_tag=None)
writer.create_text_image_to_video_section(name, prompt_tag, input_image_tag, output_tag)
writer.create_text_image_to_text_section(name, prompt_tag, input_image_tag, output_tag, ground_truth_tag=None)
```

### Comparison section constructors

Each comparison section wraps the same task but adds advanced tools.
The `output_tag` is the same tag used for both runs — the dashboard
resolves it against each selected run's database.

```python
writer.create_text_to_image_comparison(name, prompt_tag, output_tag, ground_truth_tag=None)
writer.create_text_to_text_comparison(name, input_tag, output_tag, ground_truth_tag=None)
writer.create_text_to_video_comparison(name, prompt_tag, output_tag, ground_truth_tag=None)
writer.create_text_to_audio_comparison(name, input_tag, output_tag, reference_tag=None)
writer.create_audio_to_text_comparison(name, audio_tag, prediction_tag, ground_truth_tag=None)
writer.create_text_image_to_image_comparison(name, prompt_tag, input_image_tag, output_tag, ground_truth_tag=None)
writer.create_text_image_to_video_comparison(name, prompt_tag, input_image_tag, output_tag)
writer.create_text_image_to_text_comparison(name, prompt_tag, input_image_tag, output_tag, ground_truth_tag=None)
```

### Standalone section constructors

```python
writer.create_detection_section(name, image_tag, prediction_tag, ground_truth_tag=None)
writer.create_segmentation_section(name, image_tag, prediction_tag, ground_truth_tag=None, class_names=None)
writer.create_row_section(name, *widget_types)
```

### Section config JSON stored in database

All section configs follow the same pattern — tag references stored as
JSON in the `sections.config` column:

```json
{
    "section_type": "text_to_image_comparison",
    "prompt_tag": "Edit/Prompt",
    "input_image_tag": "Edit/Input",
    "output_tag": "Edit/Output",
    "ground_truth_tag": "Edit/GroundTruth"
}
```

The dashboard reads the config, resolves each tag against the run's
database, and renders the appropriate layout. Comparison sections
use the same tags but switch to the comparison renderer with
toggle/diff/zoom tools.

---

## Implementation priority

### Phase 1 — Core eval + comparison foundation

1. `audios` table + `add_audio` / `add_audios` in Writer
2. `audio_to_text` eval (ASR) — table with audio player, GT, predictions
3. `text_to_image` eval — most common generation eval
4. `text_to_image_comparison` — toggle/flicker, pixel diff, zoom (flagship)
5. `text_to_text` eval — covers LLM / translation / summarisation

### Phase 2 — Multi-modal eval + comparison

6. `text_image_to_image` eval — editing workflows
7. `text_image_to_image_comparison` — editing quality A/B
8. `text_image_to_text` eval — VLM / VQA
9. `text_to_video` eval — video generation
10. `text_to_audio` eval (TTS)

### Phase 3 — Remaining comparisons + specialised

11. `text_to_text_comparison` — word diff
12. `text_to_video_comparison` — synced playback
13. `text_to_audio_comparison` — A/B audio
14. `audio_to_text_comparison` — ASR A/B
15. `text_image_to_video` eval + comparison
16. `text_image_to_text_comparison` — VLM A/B
17. `detection` — bbox overlay
18. `segmentation` — mask overlay

---

## File mapping (updated)

| File              | Responsibilities                                  |
|-------------------|---------------------------------------------------|
| `database.py`     | + `audios` table, `add_audio_record`, `read_audios`, `audio_tags`, `audio_steps` |
| `__init__.py`     | + `add_audio`, `add_audios`, + all `create_*_section` and `create_*_comparison` methods |
| `dashboard.py`    | + routing for all new section types               |
| `images.py`       | + eval renderers for image-output sections        |
| `video.py`        | + eval renderers for video-output sections        |
| `text.py`         | + eval renderers for text-output sections, word diff |
| `table.py`        | + `render_asr_section`, `render_tts_section` (with audio player) |
| `audio.py`        | **new** — `save_audio`, `render_audio_player`, waveform/spectrogram |
| `comparison.py`   | **new** — comparison renderers: toggle/flicker, pixel diff, curtain slider, synced zoom/pan, frame sync, word diff display |
| `detection.py`    | **new** — bbox rendering on images                |
