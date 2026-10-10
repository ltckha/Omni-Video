import os
import sys
import tempfile
import pytest
from pathlib import Path

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from archive_completed_videos import safe_move_file, safe_move_path


def test_safe_move_file():
    with tempfile.TemporaryDirectory() as tmp_dir:
        src = os.path.join(tmp_dir, "src.mp4")
        dst = os.path.join(tmp_dir, "dest_dir", "dest.mp4")

        with open(src, "wb") as f:
            f.write(b"video content bytes 12345")

        safe_move_file(src, dst)

        assert not os.path.exists(src)
        assert os.path.exists(dst)
        with open(dst, "rb") as f:
            assert f.read() == b"video content bytes 12345"


def test_safe_move_path():
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_folder = os.path.join(tmp_dir, "product_123")
        dst_folder = os.path.join(tmp_dir, "media_archive", "product_123")

        os.makedirs(src_folder, exist_ok=True)
        file1 = os.path.join(src_folder, "prompt.txt")
        with open(file1, "w", encoding="utf-8") as f:
            f.write("test prompt content")

        safe_move_path(src_folder, dst_folder)

        assert not os.path.exists(src_folder)
        assert os.path.exists(os.path.join(dst_folder, "prompt.txt"))
        with open(os.path.join(dst_folder, "prompt.txt"), "r", encoding="utf-8") as f:
            assert f.read() == "test prompt content"
