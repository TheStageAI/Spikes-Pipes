# Database Design

Local SQLite database that stores experiment data for the Streamlit
dashboard. Each **log directory** contains one `spikes.db` file and a
media tree for images/videos.

## Directory layout

```
sp_logs/
├── spikes.db              # SQLite database (WAL mode)
├── images/
│   └── Train_OutputExamples/
│       ├── step_0100_000.png
│       └── step_0100_001.png
└── videos/
    └── Train_Preview/
        └── step_0100_000.mp4
```

- Tag names are sanitised (`/` → `_`) for directory names.
- Media files follow the pattern `step_{step:04d}_{idx:03d}.{ext}`.

## Schema

### scalars

| column    | type    | notes                                      |
|-----------|---------|--------------------------------------------|
| id        | INTEGER | primary key                                |
| tag       | TEXT    | hierarchical name, e.g. `Train/Loss`       |
| step      | INTEGER | global step                                |
| value     | REAL    | scalar value                               |
| x_value   | REAL    | custom x-axis value; NULL → use step       |
| wall_time | REAL    | `time.time()` when recorded                |

Index: `(tag, step)`.

### images

| column    | type    | notes                                      |
|-----------|---------|--------------------------------------------|
| id        | INTEGER | primary key                                |
| tag       | TEXT    | hierarchical name                          |
| step      | INTEGER | global step                                |
| idx       | INTEGER | position inside the batch (0-based)        |
| path      | TEXT    | relative path from log dir                 |
| format    | TEXT    | `png`, `jpg`, …                            |
| width     | INTEGER | pixel width                                |
| height    | INTEGER | pixel height                               |
| wall_time | REAL    |                                             |

Index: `(tag, step)`.

### videos

| column    | type    | notes                                      |
|-----------|---------|--------------------------------------------|
| id        | INTEGER | primary key                                |
| tag       | TEXT    | hierarchical name                          |
| step      | INTEGER | global step                                |
| idx       | INTEGER | position inside the batch                  |
| path      | TEXT    | relative path from log dir                 |
| format    | TEXT    | `mp4`, `webm`, …                           |
| wall_time | REAL    |                                             |

Index: `(tag, step)`.

### texts

| column    | type    | notes                                      |
|-----------|---------|--------------------------------------------|
| id        | INTEGER | primary key                                |
| tag       | TEXT    | hierarchical name                          |
| step      | INTEGER | global step                                |
| idx       | INTEGER | position inside the batch                  |
| content   | TEXT    | raw text content                           |
| wall_time | REAL    |                                             |

Index: `(tag, step)`.

### sections

| column       | type    | notes                                   |
|--------------|---------|-----------------------------------------|
| id           | INTEGER | primary key                             |
| name         | TEXT    | unique section identifier               |
| section_type | TEXT    | `row`, `image_comparison`, `asr`, …     |
| config       | TEXT    | JSON blob with widget layout            |
| created_at   | REAL    |                                         |

## Writer API (training process)

```python
import spikesnpipes as sp

writer = sp.Writer("sp_logs/run_01")

writer.add_scalar("Train/Loss", step=100, val=0.42)
writer.add_scalar("Train/LR", step=100, val=3e-4, x=0.42)

writer.add_images("Train/Output", images=[arr0, arr1], step=100)
writer.add_video("Train/Preview", video=arr, step=100)
writer.add_text("Train/Transcript", text=["hello", "world"], step=100)

writer.create_section("Train/OutputExample", "row", ["image", "image"])
writer.create_section("Train/ASR", "asr")

writer.close()
```

- `Writer` opens the database with WAL journal mode so the Streamlit
  reader can query concurrently without blocking writes.
- Images accept numpy arrays (`H×W×C`, uint8), PIL Images, or file
  paths. They are saved as PNG by default.
- Videos accept numpy arrays (`T×H×W×C`, uint8) or file paths.
- `add_text` accepts a single string or a list of strings.

## Reader API (Streamlit dashboard)

```python
from spikesnpipes.database import DatabaseReader

db = DatabaseReader("sp_logs/run_01")

tags = db.scalar_tags()                # ["Train/Loss", "Train/LR"]
rows = db.read_scalars("Train/Loss")   # list of (step, value, x_value, wall_time)
imgs = db.read_images("Train/Output", step=100)  # list of image paths

db.close()
```

- Reader opens the database in **read-only** mode.
- Dashboard polls for new data on a configurable interval.

## Concurrency model

- SQLite WAL mode allows one writer + many readers.
- Writer holds a single persistent connection for the lifetime of
  training.
- Each Streamlit session opens its own read-only connection.
- No external database server required — everything is local files.
