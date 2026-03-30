from __future__ import annotations

import shutil
import wave
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from typing import Any


def save_audio(
    audio: Any, dest: Path, sr: int = 16000, fmt: str = "wav"
) -> float:
    """Save *audio* to *dest* and return duration in seconds.

    Accepts numpy arrays (float32 in -1..1, or int16),
    file paths, or raw bytes.
    """
    if isinstance(audio, (str, Path)):
        shutil.copy2(Path(audio), dest)
        try:
            with wave.open(str(dest), "r") as wf:
                return wf.getnframes() / wf.getframerate()
        except Exception:
            return 0.0

    if isinstance(audio, bytes):
        dest.write_bytes(audio)
        return 0.0

    arr = np.asarray(audio)
    if arr.dtype in (np.float32, np.float64):
        arr = np.clip(arr, -1.0, 1.0)
        arr = (arr * 32767).astype(np.int16)
    elif arr.dtype != np.int16:
        arr = arr.astype(np.int16)

    n_channels = 1 if arr.ndim == 1 else arr.shape[-1]

    with wave.open(str(dest), "w") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(arr.tobytes())

    n_frames = len(arr) if arr.ndim == 1 else arr.shape[0]
    return n_frames / sr
