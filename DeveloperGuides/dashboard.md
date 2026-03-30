# Dashboard Specification

Streamlit application that reads experiment data from one or more
log directories and renders it as a set of configurable sections.

## Launch

```bash
spikesnpipes --logdir sp_logs          # single root, auto-discover runs
spikesnpipes --logdir sp_logs/run_01 --logdir sp_logs/run_02
```

Streamlit is started under the hood:

```bash
streamlit run spikesnpipes/dashboard.py -- --logdir sp_logs
```

## Page structure

```
┌─────────────────────────────────────────────────────────┐
│  SIDEBAR                     │  MAIN AREA               │
│                              │                           │
│  ┌────────────────────────┐  │  ┌───────────────────┐   │
│  │ Root directory          │  │  │ Scalars / Train   │   │
│  │ [sp_logs           ]   │  │  │  (line charts)    │   │
│  └────────────────────────┘  │  └───────────────────┘   │
│                              │                           │
│  Runs                        │  ┌───────────────────┐   │
│  ☑ run_01                    │  │ Scalars / Val      │   │
│  ☑ run_02                    │  │  (line charts)    │   │
│  ☐ run_03                    │  └───────────────────┘   │
│                              │                           │
│  ┌────────────────────────┐  │  ┌───────────────────┐   │
│  │ Refresh  ○ Auto  ● Off │  │  │ Images / Output   │   │
│  │ Interval [5s ▾]       │  │  │  (gallery + step) │   │
│  └────────────────────────┘  │  └───────────────────┘   │
│                              │                           │
│  Section filter              │  ┌───────────────────┐   │
│  ☑ Scalars                   │  │ ASR Section        │   │
│  ☑ Images                    │  │  (table)          │   │
│  ☑ ASR                       │  └───────────────────┘   │
│  ☐ TTS                       │                           │
│  ...                         │  ...                      │
└─────────────────────────────────────────────────────────┘
```

### Sidebar

| Widget             | Purpose                                          |
|--------------------|--------------------------------------------------|
| Root directory     | Text input; base path for run discovery.         |
| Run multi-select   | Checkboxes for each run found under root.        |
|                    | Selecting multiple runs enables comparison mode. |
| Auto-refresh       | Toggle + interval (1 s / 2 s / 5 s / 10 s).     |
| Section filter     | Checkboxes to show/hide section types.           |
| Step range slider  | Global step range filter applied to all media.   |

### Main area

Vertical list of **sections**, each rendered as a collapsible
`st.expander` (expanded by default). Sections appear in this order:

1. **Auto-discovered scalar sections** — grouped by tag prefix.
2. **Auto-discovered media sections** — tags without explicit sections.
3. **Explicit sections** — from the `sections` table, in creation order.

---

## Section types

### 1. `scalars`  — line charts

Auto-created: the dashboard groups all scalar tags by their first
path component (`Train/*`, `Val/*`, …) and creates one section per
group.

```
┌─ Scalars / Train ──────────────────────────────────────┐
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ Train/Loss       │  │ Train/LR         │            │
│  │  ╭──╮            │  │        ╭──       │            │
│  │  │   ╰──────     │  │  ─────╯          │            │
│  │  run_01 ── run_02│  │  run_01 ── run_02│            │
│  └──────────────────┘  └──────────────────┘            │
│                                                         │
│  X-axis: ○ Step  ● Custom (x_value)  ○ Wall time       │
│  Smoothing: [0.6 ────●───── ]                           │
└─────────────────────────────────────────────────────────┘
```

- Each tag → one chart. Charts arranged in a responsive grid
  (2–3 columns depending on viewport).
- When multiple runs are selected, each run is a separate line on the
  same chart, colour-coded by run name.
- X-axis toggle: step (default), custom `x_value`, or wall time.
- Optional exponential smoothing slider.

### 2. `row`  — side-by-side widgets

User-defined via `create_row_section("name", "image", "text", …)`.

```
┌─ Train/OutputExample ──────────────────────────────────┐
│  Step: [◄ 100 ─────●───── 500 ►]                       │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  [image]         │  │  [image]         │            │
│  │  Train/Input:0   │  │  Train/Output:0  │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                         │
│  Run: [run_01 ▾]                                        │
└─────────────────────────────────────────────────────────┘
```

- Columns are defined by the `widgets` list in section config.
- Widget types: `image`, `text`, `video`, `audio`, `scalar`.
- A step slider scrubs through available steps.
- Run dropdown when multiple runs are active (shows one run at a time
  in row mode, since columns are already used for widgets).

### 3. `image_comparison`  — cross-run image comparison

```
┌─ ImageComparison ──────────────────────────────────────┐
│  Tag: [Train/Output ▾]                                  │
│  Step: [◄ 100 ─────●───── 500 ►]                       │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  [image]         │  │  [image]         │            │
│  │  run_01          │  │  run_02          │            │
│  └──────────────────┘  └──────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

- One column per selected run.
- Same tag + step, different runs → visual diff.
- Step slider to scrub through time.

### 4. `text_comparison`  — cross-run text diff

```
┌─ TextComparison ───────────────────────────────────────┐
│  Tag: [Train/Transcript ▾]                              │
│  Step: [◄ 100 ─────●───── 500 ►]                       │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  run_01           │  │  run_02          │            │
│  │  "hello world"    │  │  "hello wrld"    │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                         │
│  ☐ Show inline diff                                     │
└─────────────────────────────────────────────────────────┘
```

- One column per run. Optional inline diff highlighting.

### 5. `video_comparison`  — cross-run video comparison

Same layout as image comparison but with `st.video` players.
Synchronised playback when possible.

### 6. `asr`  — speech recognition table

```
┌─ ASR ──────────────────────────────────────────────────┐
│  Step: [◄ 100 ─────●───── 500 ►]                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  #  │ Audio          │ Ground Truth │ run_01    │   │
│  │─────┼────────────────┼──────────────┼───────────│   │
│  │  0  │ ▶ sample_0.wav │ hello world  │ helo wrld │   │
│  │  1  │ ▶ sample_1.wav │ good morning │ good morn │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Columns: audio tag, ground-truth text tag, then one   │
│  prediction column per selected run.                    │
└─────────────────────────────────────────────────────────┘
```

Section config specifies which tags map to audio vs ground-truth vs
prediction:

```python
writer.create_section("ASR", "asr", config={
    "audio_tag":        "ASR/Audio",
    "ground_truth_tag": "ASR/GroundTruth",
    "prediction_tag":   "ASR/Prediction",
})
```

### 7. `tts`  — text-to-speech table

```
┌─ TTS ──────────────────────────────────────────────────┐
│  Step: [◄ 100 ─────●───── 500 ►]                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  #  │ Input Text     │ run_01 Audio │ run_02    │   │
│  │─────┼────────────────┼──────────────┼───────────│   │
│  │  0  │ hello world    │ ▶ out_0.wav  │ ▶ out.wav │   │
│  │  1  │ good morning   │ ▶ out_1.wav  │ ▶ out.wav │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

Config:

```python
writer.create_section("TTS", "tts", config={
    "input_tag":  "TTS/InputText",
    "output_tag": "TTS/OutputAudio",
})
```

### 8. `llm`  — language model generation table

```
┌─ LLM ─────────────────────────────────────────────────┐
│  Step: [◄ 100 ─────●───── 500 ►]                      │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  #  │ Prompt              │ run_01    │ run_02   │   │
│  │─────┼─────────────────────┼───────────┼──────────│   │
│  │  0  │ Translate: hello    │ bonjour   │ salut    │   │
│  │  1  │ Summarise: ...      │ ...       │ ...      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

Config:

```python
writer.create_section("LLM", "llm", config={
    "prompt_tag": "LLM/Prompt",
    "output_tag": "LLM/Output",
})
```

### 9. `diffusion`  — image / video generation table

```
┌─ Diffusion ────────────────────────────────────────────┐
│  Step: [◄ 100 ─────●───── 500 ►]                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  #  │ Prompt       │ run_01 Output │ run_02     │   │
│  │─────┼──────────────┼───────────────┼────────────│   │
│  │  0  │ "a red car"  │ [image]       │ [image]    │   │
│  │  1  │ "sunset"     │ [image]       │ [image]    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

Config:

```python
writer.create_section("Diffusion", "diffusion", config={
    "prompt_tag": "Diff/Prompt",
    "output_tag": "Diff/Output",       # images or videos
})
```

### 10. `vlm`  — vision-language model table

```
┌─ VLM ─────────────────────────────────────────────────┐
│  Step: [◄ 100 ─────●───── 500 ►]                      │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  #  │ Input Image │ Prompt    │ run_01  │ run_02 │  │
│  │─────┼─────────────┼───────────┼─────────┼────────│  │
│  │  0  │ [image]     │ describe  │ a cat…  │ a pet… │  │
│  │  1  │ [image]     │ count     │ three   │ 3 obj  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

Config:

```python
writer.create_section("VLM", "vlm", config={
    "image_tag":  "VLM/InputImage",
    "prompt_tag": "VLM/Prompt",
    "output_tag": "VLM/Output",
})
```

---

## Colour palette (TheStage.AI)

All dashboard colours are taken from the official TheStage.AI design
system so the tool feels native to the ecosystem.

### Main colours

| Token              | Hex       | Usage                              |
|--------------------|-----------|------------------------------------|
| `--white-01`       | `#FFFFFF` | Main text and headers.             |
| `--black`          | `#0C0C0C` | Page background.                   |
| `--gray-06`        | `#1A1A1A` | Cards, banners, sidebar.           |
| `--yellow`         | `#FFF844` | Buttons and accents (primary).     |

### Secondary colours

| Token              | Hex       | Usage                              |
|--------------------|-----------|------------------------------------|
| `--gray-01`        | `#E5E5E5` | Secondary text.                    |
| `--gray-02`        | `#D9D9D9` | Secondary text.                    |
| `--gray-025`       | `#9F9F9F` | Buttons and accents, axis labels.  |
| `--gray-03`        | `#646464` | Secondary text.                    |
| `--gray-04`        | `#575757` | Card elements, hover buttons, tags.|
| `--gray-05`        | `#303030` | Card elements, strokes, grid lines.|
| `--gray-07`        | `#131313` | Cards, banners, chart background.  |

### Accent colours

| Name   | Hex       | Usage                              |
|--------|-----------|------------------------------------|
| Green  | `#3CD077` | Statuses text, success icons.      |
| Purple | `#B57BFF` | Statuses text, links in docs.      |
| Red    | `#FD3F40` | Statuses text, delete buttons.     |
| Orange | `#FF885A` | Statuses text, error captions.     |
| Blue   | `#5E9CFB` | Statuses text.                     |

### Run colour sequence

When multiple runs are selected, each run is assigned a colour from
this ordered palette. Alternates warm/cool hues so adjacent runs are
easy to tell apart.

| Index | Hex       | Name          |
|-------|-----------|---------------|
| 0     | `#FFF844` | Yellow        |
| 1     | `#5E9CFB` | Blue          |
| 2     | `#FD3F40` | Red           |
| 3     | `#3CD077` | Green         |
| 4     | `#FF885A` | Orange        |
| 5     | `#B57BFF` | Purple        |
| 6     | `#FFB347` | Amber         |
| 7     | `#00CED1` | Teal          |
| 8     | `#FF69B4` | Pink          |
| 9     | `#A6E22E` | Lime          |
| 10    | `#E07A3E` | Burnt orange  |
| 11    | `#48D1CC` | Mint          |
| 12    | `#E04A6A` | Rose          |
| 13    | `#7BB8FF` | Sky           |
| 14    | `#C8E64A` | Chartreuse    |
| 15    | `#B388FF` | Lavender      |

If more than 16 runs are selected, colours cycle.

### Plotly theme

Applied once at dashboard startup:

```python
import plotly.io as pio

SP_TEMPLATE = pio.templates["plotly_dark"]
SP_TEMPLATE.layout.paper_bgcolor = "#131313"
SP_TEMPLATE.layout.plot_bgcolor = "#131313"
SP_TEMPLATE.layout.font.color = "#9F9F9F"
SP_TEMPLATE.layout.font.family = "Inter, sans-serif"
SP_TEMPLATE.layout.colorway = [
    "#FFF844", "#5E9CFB", "#FD3F40", "#3CD077",
    "#FF885A", "#B57BFF", "#FFB347", "#00CED1",
    "#FF69B4", "#A6E22E", "#E07A3E", "#48D1CC",
    "#E04A6A", "#7BB8FF", "#C8E64A", "#B388FF",
]
SP_TEMPLATE.layout.xaxis.gridcolor = "#303030"
SP_TEMPLATE.layout.yaxis.gridcolor = "#303030"
pio.templates.default = SP_TEMPLATE
```

### Streamlit theming

Passed via CLI flags at launch:

```bash
--theme.base=dark
--theme.primaryColor=#FFF844
--theme.backgroundColor=#0C0C0C
--theme.secondaryBackgroundColor=#1A1A1A
--theme.textColor=#FFFFFF
```

---

## Plotting defaults (Plotly)

All scalar charts use **Plotly** with the `Scattergl` trace type (WebGL).
Rendered via `st.plotly_chart(fig, use_container_width=True)`.

### Downsampling

Even though Scattergl can render ~100 k points, we downsample to keep
the UI snappy across many charts and runs.

| Parameter             | Default | Notes                            |
|-----------------------|---------|----------------------------------|
| `MAX_POINTS_PER_LINE` | 128     | Per-run, per-tag.                |
| `DOWNSAMPLE_METHOD`   | `lttb`  | Largest-Triangle-Three-Buckets.  |
| `FALLBACK_METHOD`     | `every_nth` | When lttb dep is missing.    |

**LTTB** (Largest-Triangle-Three-Buckets) is the default because it
preserves the visual shape of the curve — peaks, valleys, and trends
stay visible even at high compression ratios.  If the `lttb` package
is not installed, fall back to simple every-Nth sampling.

Decision flow:

```
total points for (tag, run) <= MAX_POINTS_PER_LINE?
  yes → render all points, no downsampling
  no  → apply LTTB to reduce to MAX_POINTS_PER_LINE
```

When smoothing is enabled, downsampling runs **before** the EMA so the
smoothed curve still has exactly `MAX_POINTS_PER_LINE` points.

### Chart defaults

| Setting                | Value                          |
|------------------------|--------------------------------|
| Trace type             | `Scattergl`, mode `lines`      |
| Hover mode             | `x unified`                    |
| Legend                  | Run name + tag suffix          |
| Y-axis                 | Auto-range                     |
| X-axis                 | Step (default), x_value, or wall_time |
| Smoothing              | EMA, weight 0.0 – 0.99, default 0.6 |
| Grid columns           | 2 on wide viewports, 1 on narrow |
| Height per chart       | 300 px                         |

### Smoothing

Exponential moving average applied client-side after downsampling:

```
smoothed[0] = raw[0]
smoothed[i] = weight * smoothed[i-1] + (1 - weight) * raw[i]
```

Both the raw (faint, 20 % opacity) and smoothed (solid) lines are
shown on the same chart so the user can see noise and trend together.

---

## Step slider (log-scale)

All non-scalar sections (images, videos, text, comparison tables)
include a **step slider** to navigate through logged steps.

### Problem

Training runs log thousands of steps. A linear slider would pack most
of the interesting recent steps into a tiny sliver at the right end.

### Solution — 10 fixed stops in log space

The slider always shows exactly **10 selectable stops** (default).
Stops are computed in log space so that more of them land near the
end of training where recent results matter most.

Algorithm, given sorted available steps `S = [s_0, s_1, …, s_N]`:

```python
import numpy as np

def compute_slider_stops(
    steps: list[int],
    n_stops: int = 10,
) -> list[int]:
    if len(steps) <= n_stops:
        return steps

    log_min = np.log1p(steps[0])
    log_max = np.log1p(steps[-1])
    targets = np.linspace(log_min, log_max, n_stops)

    arr = np.array(steps)
    stops = []
    for t in targets:
        idx = np.argmin(np.abs(np.log1p(arr) - t))
        stops.append(int(arr[idx]))

    return sorted(set(stops))
```

Example — run with steps 0 – 100 000 (10 stops):

```
stops:  0   12   135   1100   4600   12000   28000   55000   82000   100000
        ·      ·      ·       ·       ·        ·        ·       ··      ··
```

The first few stops are spread far apart (early training, less
interesting) while the last four stops cover only the final 45 % of
steps (recent results, high detail).

### Slider widget

```
Step: [◄  0 · 135 · 1100 · 4600 · 12k · 28k · 55k · 82k ● 100k  ►]
                                                           ↑ current
```

- `st.select_slider` with the computed stops as options.
- Labels are abbreviated (`12000` → `12k`, `1100` → `1.1k`).
- Left/right arrow buttons for single-stop navigation.
- The label always shows the exact step value.

### Defaults

| Parameter          | Default | Notes                              |
|--------------------|---------|------------------------------------|
| `SLIDER_STOPS`     | 10      | Number of selectable positions.    |
| `SLIDER_SCALE`     | `log`   | `log` or `linear`.                 |
| `SLIDER_DEFAULT`   | last    | Slider starts at the latest step.  |

The stop count and scale are configurable per section. For short runs
(fewer steps than `SLIDER_STOPS`), every available step is shown.

---

## Run discovery and comparison

### Discovery

Given `--logdir sp_logs`, the dashboard scans for subdirectories
that contain a `spikes.db` file:

```
sp_logs/
├── run_01/spikes.db   →  run "run_01"
├── run_02/spikes.db   →  run "run_02"
└── run_03/spikes.db   →  run "run_03"
```

If the path itself contains `spikes.db`, it is treated as a single
run named after the directory.

### Multi-run state

```python
# session_state
st.session_state.selected_runs: list[str]     # checked in sidebar
st.session_state.run_readers: dict[str, DatabaseReader]
st.session_state.run_colours: dict[str, str]  # consistent palette
```

### Comparison rules

| Section type     | Multi-run behaviour                          |
|------------------|----------------------------------------------|
| scalars          | Overlay lines on same chart, colour by run.  |
| row              | Dropdown to pick one run (columns = widgets).|
| image_comparison | One column per run, same step + tag.         |
| text_comparison  | One column per run, optional inline diff.    |
| video_comparison | One column per run.                          |
| asr              | Fixed columns + one prediction col per run.  |
| tts              | Fixed columns + one output col per run.      |
| llm              | Fixed prompt col + one output col per run.   |
| diffusion        | Fixed prompt col + one output col per run.   |
| vlm              | Fixed image+prompt cols + one col per run.   |

---

## Tag grouping

Tags use `/` as hierarchy separator.

- **First component** is the group key: `Train/Loss` → group `Train`.
- Scalars auto-group by this key into separate expander sections.
- Media tags without an explicit section are auto-grouped the same way
  and rendered as simple galleries / text viewers.

When a section's config references a tag (e.g. `"prompt_tag": "LLM/Prompt"`),
the dashboard resolves it against each selected run's database.
Missing tags for a run produce an empty cell, not an error.

---

## Auto-refresh

```python
if st.session_state.auto_refresh:
    st_autorefresh(
        interval=st.session_state.refresh_interval_ms,
        key="data_refresh",
    )
```

On each refresh cycle the dashboard:
1. Re-scans the root directory for new/removed runs.
2. For each selected run, queries for new data since last known step.
3. Appends new points to in-memory dataframes held in session state.
4. Re-renders only sections whose data changed (Streamlit handles
   this via its normal diff mechanism).

---

## File mapping

| File              | Responsibility                                |
|-------------------|-----------------------------------------------|
| `dashboard.py`    | Streamlit entry point, page layout, sidebar.  |
| `scalars.py`      | `render_scalars_section()` — chart rendering. |
| `images.py`       | `render_image_*()` helpers for all image UIs. |
| `video.py`        | `render_video_*()` helpers.                   |
| `text.py`         | `render_text_*()` helpers, inline diff.       |
| `table.py`        | `render_table_section()` — ASR/TTS/LLM/etc.  |
| `database.py`     | `DatabaseReader` used by all renderers.       |
| `cli.py`          | Argument parsing, launches Streamlit.         |
