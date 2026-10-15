import os
import sys
import json
import pytest

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from flow_helper import list_pending_items, prepare_flow_bundle, collect_flow_video


def _make_item(assets, item_id, prompt=True, video=False, character=True, title="Nồi cơm mini"):
    d = assets / item_id
    d.mkdir(parents=True)
    (d / f"{item_id}_1.webp").write_bytes(b"img")
    if character:
        (d / "Nu-25t.png").write_bytes(b"char")
    if prompt:
        (d / f"{item_id}.txt").write_text("[ASSETS]\n[PROMPT]\n[CONSTRAINTS]", encoding="utf-8")
    if video:
        (d / f"{item_id}.mp4").write_bytes(b"mp4")
    (d / "info.json").write_text(json.dumps({"productName": title}), encoding="utf-8")
    return d


def test_list_pending_items_only_prompt_without_video(tmp_path):
    assets = tmp_path / "Product_Assets"
    _make_item(assets, "111")
    _make_item(assets, "222", video=True)
    _make_item(assets, "333", prompt=False)
    assert list_pending_items(str(assets)) == [{"itemId": "111", "title": "Nồi cơm mini"}]


def test_prepare_bundle_copies_three_numbered_files(tmp_path):
    assets = tmp_path / "Product_Assets"
    _make_item(assets, "111")
    staging = tmp_path / "Omni-Flow"
    bundle = prepare_flow_bundle("111", str(assets), str(staging))
    assert sorted(os.listdir(bundle)) == ["1_nguoi_mau_Nu-25t.png", "2_san_pham_111_1.webp", "3_kich_ban_111.txt"]
    # originals untouched
    assert sorted(os.listdir(assets / "111")) == ["111.txt", "111_1.webp", "Nu-25t.png", "info.json"]


def test_prepare_bundle_reports_missing_files(tmp_path):
    assets = tmp_path / "Product_Assets"
    _make_item(assets, "111", prompt=False)
    with pytest.raises(FileNotFoundError, match="kịch bản"):
        prepare_flow_bundle("111", str(assets), str(tmp_path / "Omni-Flow"))


def test_collect_moves_video_and_cleans_staging(tmp_path):
    assets = tmp_path / "Product_Assets"
    _make_item(assets, "111")
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "111.mp4").write_bytes(b"mp4")
    staging = tmp_path / "Omni-Flow"
    prepare_flow_bundle("111", str(assets), str(staging))
    moved = collect_flow_video("111", str(assets), str(downloads), str(staging))
    assert moved == str(assets / "111" / "111.mp4")
    assert not (downloads / "111.mp4").exists()
    assert not (staging / "111").exists()


def test_collect_returns_none_when_not_downloaded_yet(tmp_path):
    assets = tmp_path / "Product_Assets"
    _make_item(assets, "111")
    (tmp_path / "Downloads").mkdir()
    assert collect_flow_video("111", str(assets), str(tmp_path / "Downloads"), str(tmp_path / "Omni-Flow")) is None


def test_collect_never_overwrites_existing_video(tmp_path):
    assets = tmp_path / "Product_Assets"
    _make_item(assets, "111", video=True)
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "111.mp4").write_bytes(b"new")
    with pytest.raises(FileExistsError):
        collect_flow_video("111", str(assets), str(downloads), str(tmp_path / "Omni-Flow"))
    assert (assets / "111" / "111.mp4").read_bytes() == b"mp4"
