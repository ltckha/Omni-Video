import os
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from contact_sheet import sheet_filter, find_videos, ffmpeg_path, make_sheet


def test_filter_takes_10_frames_evenly():
    assert sheet_filter(10.0) == "fps=1.0000,scale=240:-2,tile=5x2:padding=4:color=white"
    assert sheet_filter(20.0).startswith("fps=0.5000,")


def test_find_videos_in_folder(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "1.mp4").write_bytes(b"x")
    (tmp_path / "2.txt").write_text("x")
    assert find_videos(str(tmp_path)) == [str(tmp_path / "a" / "1.mp4")]


@pytest.mark.skipif(not ffmpeg_path(), reason="chưa có ffmpeg")
def test_make_sheet_on_generated_clip(tmp_path):
    import subprocess
    clip = tmp_path / "t.mp4"
    subprocess.run([ffmpeg_path(), "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=10:size=320x568:rate=10",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    out = make_sheet(str(clip))
    assert out.endswith("t_xem.jpg") and os.path.getsize(out) > 1000
