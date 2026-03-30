"""Spikes & Pipes – Streamlit based open-source experiments dashboard."""

from __future__ import annotations

__version__ = "0.1.0"

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

from spikesnpipes.database import DatabaseWriter


class Writer:
    """High-level writer for logging experiment data.

    Usage::

        import spikesnpipes as sp

        w = sp.Writer("sp_logs/run_01")
        w.add_scalar("Train/Loss", step=100, val=0.42)
        w.add_images("Train/Output", images=[arr0, arr1], step=100)
        w.close()
    """

    def __init__(self, log_dir: str | Path = "sp_logs") -> None:
        self._db = DatabaseWriter(log_dir)

    # -- scalars ------------------------------------------------------------

    def add_scalar(
        self,
        tag: str,
        *,
        step: int,
        val: float,
        x: float | None = None,
    ) -> None:
        self._db.add_scalar(tag, step=step, value=val, x_value=x)

    # -- images -------------------------------------------------------------

    def add_images(
        self,
        tag: str,
        *,
        images: list[Any],
        step: int,
        fmt: str = "png",
    ) -> None:
        from spikesnpipes.images import save_image

        out_dir = self._db.images_dir(tag)
        for idx, img in enumerate(images):
            fname = f"step_{step:04d}_{idx:03d}.{fmt}"
            dest = out_dir / fname
            w, h = save_image(img, dest, fmt=fmt)
            rel = str(dest.relative_to(self._db.log_dir))
            self._db.add_image_record(
                tag, step=step, idx=idx,
                rel_path=rel, fmt=fmt, width=w, height=h,
            )

    # -- videos -------------------------------------------------------------

    def add_video(
        self,
        tag: str,
        *,
        video: Any,
        step: int,
        fmt: str = "mp4",
    ) -> None:
        from spikesnpipes.video import save_video

        out_dir = self._db.videos_dir(tag)
        fname = f"step_{step:04d}_000.{fmt}"
        dest = out_dir / fname
        save_video(video, dest, fmt=fmt)
        rel = str(dest.relative_to(self._db.log_dir))
        self._db.add_video_record(
            tag, step=step, idx=0, rel_path=rel, fmt=fmt,
        )

    def add_videos(
        self,
        tag: str,
        *,
        videos: list[Any],
        step: int,
        fmt: str = "mp4",
    ) -> None:
        from spikesnpipes.video import save_video

        out_dir = self._db.videos_dir(tag)
        for idx, vid in enumerate(videos):
            fname = f"step_{step:04d}_{idx:03d}.{fmt}"
            dest = out_dir / fname
            save_video(vid, dest, fmt=fmt)
            rel = str(dest.relative_to(self._db.log_dir))
            self._db.add_video_record(
                tag, step=step, idx=idx, rel_path=rel, fmt=fmt,
            )

    # -- audio --------------------------------------------------------------

    def add_audio(
        self,
        tag: str,
        *,
        audio: Any,
        step: int,
        sr: int = 16000,
        fmt: str = "wav",
    ) -> None:
        from spikesnpipes.audio import save_audio

        out_dir = self._db.audios_dir(tag)
        fname = f"step_{step:04d}_000.{fmt}"
        dest = out_dir / fname
        duration = save_audio(audio, dest, sr=sr, fmt=fmt)
        rel = str(dest.relative_to(self._db.log_dir))
        self._db.add_audio_record(
            tag, step=step, idx=0, rel_path=rel, fmt=fmt,
            duration=duration, sample_rate=sr,
        )

    def add_audios(
        self,
        tag: str,
        *,
        audios: list[Any],
        step: int,
        sr: int = 16000,
        fmt: str = "wav",
    ) -> None:
        from spikesnpipes.audio import save_audio

        out_dir = self._db.audios_dir(tag)
        for idx, aud in enumerate(audios):
            fname = f"step_{step:04d}_{idx:03d}.{fmt}"
            dest = out_dir / fname
            duration = save_audio(aud, dest, sr=sr, fmt=fmt)
            rel = str(dest.relative_to(self._db.log_dir))
            self._db.add_audio_record(
                tag, step=step, idx=idx, rel_path=rel, fmt=fmt,
                duration=duration, sample_rate=sr,
            )

    # -- text ---------------------------------------------------------------

    def add_text(
        self,
        tag: str,
        *,
        text: str | list[str],
        step: int,
    ) -> None:
        items = [text] if isinstance(text, str) else text
        for idx, t in enumerate(items):
            self._db.add_text_record(tag, step=step, idx=idx, content=t)

    # -- sections -----------------------------------------------------------

    def _upsert(
        self, name: str, stype: str, cfg: dict[str, Any],
        description: str,
    ) -> None:
        self._db.upsert_section(name, stype, cfg, description)

    def create_section(
        self, name: str, section_type: str,
        widgets: list[str] | None = None,
        description: str = "",
    ) -> None:
        config = {"widgets": widgets} if widgets else {}
        self._upsert(name, section_type, config, description)

    def create_row_section(
        self, name: str, *widget_types: str,
        description: str = "",
    ) -> None:
        cfg = {"widgets": list(widget_types)} if widget_types else {}
        self._upsert(name, "row", cfg, description)

    def create_image_comparison(
        self, name: str = "ImageComparison",
        description: str = "",
    ) -> None:
        self._upsert(name, "image_comparison", {}, description)

    def create_text_comparison(
        self, name: str = "TextComparison",
        description: str = "",
    ) -> None:
        self._upsert(name, "text_comparison", {}, description)

    def create_video_comparison(
        self, name: str = "VideoComparison",
        description: str = "",
    ) -> None:
        self._upsert(name, "video_comparison", {}, description)

    def create_asr_section(
        self, name: str = "ASR", description: str = "",
    ) -> None:
        self._upsert(name, "asr", {}, description)

    def create_tts_section(
        self, name: str = "TTS", description: str = "",
    ) -> None:
        self._upsert(name, "tts", {}, description)

    # -- generation eval sections -------------------------------------------

    def create_text_to_image_section(
        self, name: str, *, prompt_tag: str, output_tag: str,
        ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "prompt_tag": prompt_tag,
            "output_tag": output_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(name, "text_to_image", cfg, description)

    def create_text_to_text_section(
        self, name: str, *, input_tag: str, output_tag: str,
        ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "input_tag": input_tag,
            "output_tag": output_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(name, "text_to_text", cfg, description)

    def create_text_to_video_section(
        self, name: str, *, prompt_tag: str, output_tag: str,
        ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "prompt_tag": prompt_tag,
            "output_tag": output_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(name, "text_to_video", cfg, description)

    def create_text_to_audio_section(
        self, name: str, *, input_tag: str, output_tag: str,
        reference_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "input_tag": input_tag,
            "output_tag": output_tag,
        }
        if reference_tag:
            cfg["reference_tag"] = reference_tag
        self._upsert(name, "text_to_audio", cfg, description)

    def create_audio_to_text_section(
        self, name: str, *, audio_tag: str, prediction_tag: str,
        ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "audio_tag": audio_tag,
            "prediction_tag": prediction_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(name, "audio_to_text", cfg, description)

    def create_text_image_to_image_section(
        self, name: str, *, prompt_tag: str, input_image_tag: str,
        output_tag: str, ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "prompt_tag": prompt_tag,
            "input_image_tag": input_image_tag,
            "output_tag": output_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(name, "text_image_to_image", cfg, description)

    def create_text_image_to_video_section(
        self, name: str, *, prompt_tag: str, input_image_tag: str,
        output_tag: str, description: str = "",
    ) -> None:
        self._upsert(name, "text_image_to_video", {
            "prompt_tag": prompt_tag,
            "input_image_tag": input_image_tag,
            "output_tag": output_tag,
        }, description)

    def create_text_image_to_text_section(
        self, name: str, *, prompt_tag: str, input_image_tag: str,
        output_tag: str, ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "prompt_tag": prompt_tag,
            "input_image_tag": input_image_tag,
            "output_tag": output_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(name, "text_image_to_text", cfg, description)

    # -- comparison sections ------------------------------------------------

    def create_text_to_image_comparison(
        self, name: str, *, prompt_tag: str, output_tag: str,
        ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "prompt_tag": prompt_tag,
            "output_tag": output_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(
            name, "text_to_image_comparison", cfg, description
        )

    def create_text_to_text_comparison(
        self, name: str, *, input_tag: str, output_tag: str,
        ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "input_tag": input_tag,
            "output_tag": output_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(
            name, "text_to_text_comparison", cfg, description
        )

    def create_text_to_video_comparison(
        self, name: str, *, prompt_tag: str, output_tag: str,
        description: str = "",
    ) -> None:
        self._upsert(
            name, "text_to_video_comparison", {
                "prompt_tag": prompt_tag,
                "output_tag": output_tag,
            }, description
        )

    def create_text_to_audio_comparison(
        self, name: str, *, input_tag: str, output_tag: str,
        description: str = "",
    ) -> None:
        self._upsert(
            name, "text_to_audio_comparison", {
                "input_tag": input_tag,
                "output_tag": output_tag,
            }, description
        )

    def create_audio_to_text_comparison(
        self, name: str, *, audio_tag: str, prediction_tag: str,
        ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "audio_tag": audio_tag,
            "prediction_tag": prediction_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(
            name, "audio_to_text_comparison", cfg, description
        )

    def create_text_image_to_image_comparison(
        self, name: str, *, prompt_tag: str, input_image_tag: str,
        output_tag: str, ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "prompt_tag": prompt_tag,
            "input_image_tag": input_image_tag,
            "output_tag": output_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(
            name, "text_image_to_image_comparison",
            cfg, description
        )

    def create_text_image_to_video_comparison(
        self, name: str, *, prompt_tag: str, input_image_tag: str,
        output_tag: str, description: str = "",
    ) -> None:
        self._upsert(
            name, "text_image_to_video_comparison", {
                "prompt_tag": prompt_tag,
                "input_image_tag": input_image_tag,
                "output_tag": output_tag,
            }, description
        )

    def create_text_image_to_text_comparison(
        self, name: str, *, prompt_tag: str, input_image_tag: str,
        output_tag: str, ground_truth_tag: str | None = None,
        description: str = "",
    ) -> None:
        cfg: dict[str, Any] = {
            "prompt_tag": prompt_tag,
            "input_image_tag": input_image_tag,
            "output_tag": output_tag,
        }
        if ground_truth_tag:
            cfg["ground_truth_tag"] = ground_truth_tag
        self._upsert(
            name, "text_image_to_text_comparison",
            cfg, description
        )

    # -- lifecycle ----------------------------------------------------------

    def close(self) -> None:
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
