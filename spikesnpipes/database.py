import json
import sqlite3
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS scalars (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    tag       TEXT    NOT NULL,
    step      INTEGER NOT NULL,
    value     REAL    NOT NULL,
    x_value   REAL,
    wall_time REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_scalars_tag_step ON scalars (tag, step);

CREATE TABLE IF NOT EXISTS images (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    tag       TEXT    NOT NULL,
    step      INTEGER NOT NULL,
    idx       INTEGER NOT NULL,
    path      TEXT    NOT NULL,
    format    TEXT    NOT NULL,
    width     INTEGER,
    height    INTEGER,
    wall_time REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_images_tag_step ON images (tag, step);

CREATE TABLE IF NOT EXISTS videos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    tag       TEXT    NOT NULL,
    step      INTEGER NOT NULL,
    idx       INTEGER NOT NULL,
    path      TEXT    NOT NULL,
    format    TEXT    NOT NULL,
    wall_time REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_videos_tag_step ON videos (tag, step);

CREATE TABLE IF NOT EXISTS texts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    tag       TEXT    NOT NULL,
    step      INTEGER NOT NULL,
    idx       INTEGER NOT NULL,
    content   TEXT    NOT NULL,
    wall_time REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_texts_tag_step ON texts (tag, step);

CREATE TABLE IF NOT EXISTS audios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tag         TEXT    NOT NULL,
    step        INTEGER NOT NULL,
    idx         INTEGER NOT NULL,
    path        TEXT    NOT NULL,
    format      TEXT    NOT NULL,
    duration    REAL,
    sample_rate INTEGER,
    wall_time   REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_audios_tag_step ON audios (tag, step);

CREATE TABLE IF NOT EXISTS sections (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL UNIQUE,
    section_type TEXT    NOT NULL,
    config       TEXT    NOT NULL DEFAULT '{}',
    description  TEXT    NOT NULL DEFAULT '',
    created_at   REAL    NOT NULL
);
"""


def _sanitise_tag(tag: str) -> str:
    return tag.replace("/", "_").replace(" ", "_")


# ---------------------------------------------------------------------------
# DatabaseWriter
# ---------------------------------------------------------------------------

class DatabaseWriter:
    """Append-only writer used by the training process."""

    def __init__(self, log_dir: str | Path) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self.log_dir / "spikes.db"
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._migrate()

    def _migrate(self) -> None:
        cols = {
            r[1]
            for r in self._conn.execute(
                "PRAGMA table_info(sections)"
            ).fetchall()
        }
        if "description" not in cols:
            self._conn.execute(
                "ALTER TABLE sections "
                "ADD COLUMN description TEXT NOT NULL DEFAULT ''"
            )
            self._conn.commit()

    # -- scalars ------------------------------------------------------------

    def add_scalar(
        self,
        tag: str,
        step: int,
        value: float,
        x_value: float | None = None,
        wall_time: float | None = None,
    ) -> None:
        wt = wall_time or time.time()
        self._conn.execute(
            "INSERT INTO scalars (tag, step, value, x_value, wall_time) "
            "VALUES (?, ?, ?, ?, ?)",
            (tag, step, value, x_value, wt),
        )
        self._conn.commit()

    # -- images -------------------------------------------------------------

    def add_image_record(
        self,
        tag: str,
        step: int,
        idx: int,
        rel_path: str,
        fmt: str,
        width: int | None = None,
        height: int | None = None,
        wall_time: float | None = None,
    ) -> None:
        wt = wall_time or time.time()
        self._conn.execute(
            "INSERT INTO images "
            "(tag, step, idx, path, format, width, height, wall_time) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tag, step, idx, rel_path, fmt, width, height, wt),
        )
        self._conn.commit()

    # -- videos -------------------------------------------------------------

    def add_video_record(
        self,
        tag: str,
        step: int,
        idx: int,
        rel_path: str,
        fmt: str,
        wall_time: float | None = None,
    ) -> None:
        wt = wall_time or time.time()
        self._conn.execute(
            "INSERT INTO videos "
            "(tag, step, idx, path, format, wall_time) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (tag, step, idx, rel_path, fmt, wt),
        )
        self._conn.commit()

    # -- texts --------------------------------------------------------------

    def add_text_record(
        self,
        tag: str,
        step: int,
        idx: int,
        content: str,
        wall_time: float | None = None,
    ) -> None:
        wt = wall_time or time.time()
        self._conn.execute(
            "INSERT INTO texts (tag, step, idx, content, wall_time) "
            "VALUES (?, ?, ?, ?, ?)",
            (tag, step, idx, content, wt),
        )
        self._conn.commit()

    # -- audios -------------------------------------------------------------

    def add_audio_record(
        self,
        tag: str,
        step: int,
        idx: int,
        rel_path: str,
        fmt: str,
        duration: float | None = None,
        sample_rate: int | None = None,
        wall_time: float | None = None,
    ) -> None:
        wt = wall_time or time.time()
        self._conn.execute(
            "INSERT INTO audios "
            "(tag, step, idx, path, format, duration, "
            "sample_rate, wall_time) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tag, step, idx, rel_path, fmt,
             duration, sample_rate, wt),
        )
        self._conn.commit()

    def audios_dir(self, tag: str) -> Path:
        d = self.log_dir / "audios" / _sanitise_tag(tag)
        d.mkdir(parents=True, exist_ok=True)
        return d

    # -- sections -----------------------------------------------------------

    def upsert_section(
        self,
        name: str,
        section_type: str,
        config: dict | None = None,
        description: str = "",
    ) -> None:
        cfg = json.dumps(config or {})
        now = time.time()
        self._conn.execute(
            "INSERT INTO sections "
            "(name, section_type, config, description, created_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET "
            "section_type=excluded.section_type, "
            "config=excluded.config, "
            "description=excluded.description",
            (name, section_type, cfg, description, now),
        )
        self._conn.commit()

    # -- media dirs ---------------------------------------------------------

    def images_dir(self, tag: str) -> Path:
        d = self.log_dir / "images" / _sanitise_tag(tag)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def videos_dir(self, tag: str) -> Path:
        d = self.log_dir / "videos" / _sanitise_tag(tag)
        d.mkdir(parents=True, exist_ok=True)
        return d

    # -- lifecycle ----------------------------------------------------------

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# ---------------------------------------------------------------------------
# DatabaseReader
# ---------------------------------------------------------------------------

class DatabaseReader:
    """Read-only access used by the Streamlit dashboard."""

    def __init__(self, log_dir: str | Path) -> None:
        self.log_dir = Path(log_dir)
        db_path = self.log_dir / "spikes.db"
        self._conn = sqlite3.connect(
            f"file:{db_path}?mode=ro",
            uri=True,
        )
        self._conn.row_factory = sqlite3.Row

    # -- tag discovery ------------------------------------------------------

    def scalar_tags(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT tag FROM scalars ORDER BY tag"
        ).fetchall()
        return [r["tag"] for r in rows]

    def image_tags(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT tag FROM images ORDER BY tag"
        ).fetchall()
        return [r["tag"] for r in rows]

    def video_tags(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT tag FROM videos ORDER BY tag"
        ).fetchall()
        return [r["tag"] for r in rows]

    def text_tags(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT tag FROM texts ORDER BY tag"
        ).fetchall()
        return [r["tag"] for r in rows]

    # -- scalars ------------------------------------------------------------

    def read_scalars(
        self,
        tag: str,
        after_step: int | None = None,
    ) -> list[dict]:
        if after_step is not None:
            rows = self._conn.execute(
                "SELECT step, value, x_value, wall_time "
                "FROM scalars WHERE tag = ? AND step > ? "
                "ORDER BY step",
                (tag, after_step),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT step, value, x_value, wall_time "
                "FROM scalars WHERE tag = ? ORDER BY step",
                (tag,),
            ).fetchall()
        return [dict(r) for r in rows]

    # -- images -------------------------------------------------------------

    def read_images(
        self,
        tag: str,
        step: int | None = None,
    ) -> list[dict]:
        if step is not None:
            rows = self._conn.execute(
                "SELECT step, idx, path, format, width, height, "
                "wall_time FROM images "
                "WHERE tag = ? AND step = ? ORDER BY idx",
                (tag, step),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT step, idx, path, format, width, height, "
                "wall_time FROM images "
                "WHERE tag = ? ORDER BY step, idx",
                (tag,),
            ).fetchall()
        return [dict(r) for r in rows]

    def image_steps(self, tag: str) -> list[int]:
        rows = self._conn.execute(
            "SELECT DISTINCT step FROM images "
            "WHERE tag = ? ORDER BY step",
            (tag,),
        ).fetchall()
        return [r["step"] for r in rows]

    # -- videos -------------------------------------------------------------

    def read_videos(
        self,
        tag: str,
        step: int | None = None,
    ) -> list[dict]:
        if step is not None:
            rows = self._conn.execute(
                "SELECT step, idx, path, format, wall_time "
                "FROM videos WHERE tag = ? AND step = ? "
                "ORDER BY idx",
                (tag, step),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT step, idx, path, format, wall_time "
                "FROM videos WHERE tag = ? "
                "ORDER BY step, idx",
                (tag,),
            ).fetchall()
        return [dict(r) for r in rows]

    def video_steps(self, tag: str) -> list[int]:
        rows = self._conn.execute(
            "SELECT DISTINCT step FROM videos "
            "WHERE tag = ? ORDER BY step",
            (tag,),
        ).fetchall()
        return [r["step"] for r in rows]

    # -- texts --------------------------------------------------------------

    def read_texts(
        self,
        tag: str,
        step: int | None = None,
    ) -> list[dict]:
        if step is not None:
            rows = self._conn.execute(
                "SELECT step, idx, content, wall_time "
                "FROM texts WHERE tag = ? AND step = ? "
                "ORDER BY idx",
                (tag, step),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT step, idx, content, wall_time "
                "FROM texts WHERE tag = ? "
                "ORDER BY step, idx",
                (tag,),
            ).fetchall()
        return [dict(r) for r in rows]

    def text_steps(self, tag: str) -> list[int]:
        rows = self._conn.execute(
            "SELECT DISTINCT step FROM texts "
            "WHERE tag = ? ORDER BY step",
            (tag,),
        ).fetchall()
        return [r["step"] for r in rows]

    # -- audios -------------------------------------------------------------

    def audio_tags(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT tag FROM audios ORDER BY tag"
        ).fetchall()
        return [r["tag"] for r in rows]

    def read_audios(
        self,
        tag: str,
        step: int | None = None,
    ) -> list[dict]:
        if step is not None:
            rows = self._conn.execute(
                "SELECT step, idx, path, format, duration, "
                "sample_rate, wall_time FROM audios "
                "WHERE tag = ? AND step = ? ORDER BY idx",
                (tag, step),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT step, idx, path, format, duration, "
                "sample_rate, wall_time FROM audios "
                "WHERE tag = ? ORDER BY step, idx",
                (tag,),
            ).fetchall()
        return [dict(r) for r in rows]

    def audio_steps(self, tag: str) -> list[int]:
        rows = self._conn.execute(
            "SELECT DISTINCT step FROM audios "
            "WHERE tag = ? ORDER BY step",
            (tag,),
        ).fetchall()
        return [r["step"] for r in rows]

    # -- sections -----------------------------------------------------------

    def read_sections(self) -> list[dict]:
        try:
            rows = self._conn.execute(
                "SELECT name, section_type, config, description, "
                "created_at FROM sections ORDER BY created_at"
            ).fetchall()
        except sqlite3.OperationalError:
            rows = self._conn.execute(
                "SELECT name, section_type, config, created_at "
                "FROM sections ORDER BY created_at"
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["config"] = json.loads(d["config"])
            d.setdefault("description", "")
            result.append(d)
        return result

    # -- lifecycle ----------------------------------------------------------

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
