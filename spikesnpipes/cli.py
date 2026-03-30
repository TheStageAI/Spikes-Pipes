from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="spikesnpipes",
        description="Spikes & Pipes — experiment dashboard",
    )
    parser.add_argument(
        "--logdir",
        type=str,
        default="sp_logs",
        help="Root directory containing run sub-directories "
        "(default: sp_logs)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
    )
    args = parser.parse_args()

    dashboard = str(Path(__file__).parent / "dashboard.py")
    logdir = os.path.abspath(args.logdir)

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        dashboard,
        f"--server.address={args.host}",
        f"--server.port={args.port}",
        "--theme.base=dark",
        "--theme.primaryColor=#FFF844",
        "--theme.backgroundColor=#141414",
        "--theme.secondaryBackgroundColor=#1A1A1A",
        "--theme.textColor=#FFFFFF",
        "--",
        f"--logdir={logdir}",
    ]

    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
