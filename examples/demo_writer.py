"""Generate two fake training runs so the dashboard has something to show.

Usage:
    python examples/demo_writer.py
    spikesnpipes --logdir demo_logs
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spikesnpipes as sp


def gradient_image(
    h: int, w: int, channel: int, intensity: float
) -> np.ndarray:
    """Create a simple gradient image for visual testing."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    grad = np.linspace(0, int(255 * intensity), w).astype(
        np.uint8
    )
    img[:, :, channel % 3] = grad[np.newaxis, :]
    cross = np.linspace(0, int(128 * intensity), h).astype(
        np.uint8
    )
    img[:, :, (channel + 1) % 3] += cross[:, np.newaxis]
    return img


def create_run(
    name: str,
    base_dir: str = "demo_logs",
    noise: float = 0.05,
    seed: int = 42,
) -> None:
    rng = np.random.default_rng(seed)
    w = sp.Writer(f"{base_dir}/{name}")

    n_steps = 2000
    for step in range(0, n_steps, 2):
        t = step / n_steps

        loss = 2.0 * np.exp(-4 * t) + noise * rng.normal()
        acc = 1.0 - 0.85 * np.exp(-3 * t) + noise * rng.normal()
        lr = 1e-3 * max(0, 1 - t)

        w.add_scalar("Train/Loss", step=step, val=max(0.0, loss))
        w.add_scalar(
            "Train/Accuracy", step=step, val=np.clip(acc, 0, 1)
        )
        w.add_scalar("Train/LR", step=step, val=lr)

        val_loss = (
            2.2 * np.exp(-3 * t) + noise * 1.5 * rng.normal()
        )
        w.add_scalar("Val/Loss", step=step, val=max(0.0, val_loss))

        if step % 200 == 0:
            images = [
                gradient_image(64, 64, channel=(step // 200 + i), intensity=t)
                for i in range(3)
            ]
            w.add_images("Train/Samples", images=images, step=step)

            w.add_text(
                "Train/Log",
                text=[
                    f"Step {step}: loss={loss:.4f} acc={acc:.4f}",
                    f"lr={lr:.6f}",
                ],
                step=step,
            )

    w.close()
    print(f"  wrote {name}  ({n_steps // 2} scalar steps, "
          f"{n_steps // 200} image steps)")


def main() -> None:
    print("Generating demo data …")
    create_run("run_01", noise=0.04, seed=42)
    create_run("run_02", noise=0.08, seed=123)
    print(f"Done — launch with:\n  spikesnpipes --logdir demo_logs")


if __name__ == "__main__":
    main()
