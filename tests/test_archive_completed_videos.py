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


def _fake_sheet(video, out):
    Path(out).write_bytes(b"jpg")
    return out


def test_review_video_enter_moves_and_keeps_sheet(tmp_path, monkeypatch):
    import contact_sheet
    from archive_completed_videos import review_video
    monkeypatch.setattr(contact_sheet, "make_sheet", _fake_sheet)
    shown = []
    assert review_video("123", str(tmp_path), str(tmp_path / "123.mp4"), ask=lambda _: "", show=shown.append)
    assert shown == [str(tmp_path / "123_xem.jpg")] and (tmp_path / "123_xem.jpg").exists()


def test_review_video_b_skips_and_removes_sheet(tmp_path, monkeypatch):
    import contact_sheet
    from archive_completed_videos import review_video
    monkeypatch.setattr(contact_sheet, "make_sheet", _fake_sheet)
    assert not review_video("123", str(tmp_path), str(tmp_path / "123.mp4"), ask=lambda _: "B", show=lambda p: None)
    assert not (tmp_path / "123_xem.jpg").exists()


def test_review_video_still_asks_when_sheet_fails(tmp_path, monkeypatch):
    import contact_sheet
    from archive_completed_videos import review_video

    def boom(video, out):
        raise RuntimeError("Chưa có ffmpeg trên máy.")
    monkeypatch.setattr(contact_sheet, "make_sheet", boom)
    assert review_video("123", str(tmp_path), str(tmp_path / "123.mp4"), ask=lambda _: "", show=lambda p: None)


def test_archive_skips_item_when_review_says_no(tmp_path, monkeypatch):
    import archive_completed_videos as acv
    item = tmp_path / "assets" / "123"
    item.mkdir(parents=True)
    (item / "123.mp4").write_bytes(b"v")
    monkeypatch.setattr(acv, "ASSETS_DIR", str(tmp_path / "assets"))
    monkeypatch.setattr(acv, "TARGET_MEDIA_DIR", str(tmp_path / "nas"))
    assert acv.archive_completed_folders(review=lambda *a: False) == 0
    assert (item / "123.mp4").exists() and not (tmp_path / "nas").exists()
