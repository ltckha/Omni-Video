#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - N17 (bản nháp, 23/10/2026): tờ ảnh 10 khung để anh Kha xem nhanh video trước khi Move.
Mỗi giây 1 khung, ghép 5 × 2, cạnh ngắn 240 px — thấy được lỗi đồ vật biến dạng / biến mất giữa cảnh
(vd nắp hũ nến tách ra ở video 27958810119 ngày 15/10). Dùng ffmpeg, 0 Gemini, không sửa video.

Dùng: python scripts/contact_sheet.py <video.mp4 | thư mục chứa .mp4> [--out <thư mục>]
  Mặc định ghi <Mã_SP>_xem.jpg cạnh video.
"""

import glob
import os
import shutil
import subprocess
import sys
from typing import List, Optional

COLS, ROWS, TILE_W = 5, 2, 240


def ffmpeg_path() -> Optional[str]:
    return shutil.which("ffmpeg") or next((p for p in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg") if os.path.exists(p)), None)


def video_duration(path: str) -> float:
    probe = (ffmpeg_path() or "ffmpeg").replace("ffmpeg", "ffprobe")
    out = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out or 0)


def sheet_filter(duration: float, cols: int = COLS, rows: int = ROWS, tile_w: int = TILE_W) -> str:
    """Lấy đều cols × rows khung trên toàn video (video 10 s → 1 khung / giây)."""
    n = cols * rows
    fps = n / duration if duration > 0 else 1
    return f"fps={fps:.4f},scale={tile_w}:-2,tile={cols}x{rows}:padding=4:color=white"


def make_sheet(video: str, out_path: Optional[str] = None) -> str:
    ff = ffmpeg_path()
    if not ff:
        raise RuntimeError("Chưa có ffmpeg trên máy.")
    out_path = out_path or os.path.splitext(video)[0] + "_xem.jpg"
    subprocess.run([ff, "-v", "error", "-y", "-i", video, "-vf", sheet_filter(video_duration(video)),
                    "-frames:v", "1", "-q:v", "4", out_path], check=True)
    return out_path


def find_videos(target: str) -> List[str]:
    if os.path.isfile(target):
        return [target]
    return sorted(glob.glob(os.path.join(target, "**", "*.mp4"), recursive=True))


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_dir = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if not args:
        print(__doc__)
        return 1
    videos = find_videos(args[0])
    for v in videos:
        out = os.path.join(out_dir, os.path.splitext(os.path.basename(v))[0] + "_xem.jpg") if out_dir else None
        print(f"🖼️ {make_sheet(v, out)}")
    if not videos:
        print("ℹ️ Không thấy video .mp4 nào.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
