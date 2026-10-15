import os
import sys
import json
import pytest

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from flow_helper import list_pending_items, collect_flow_video, get_flow_assets


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


def test_flow_assets_reports_missing_files(tmp_path):
    assets = tmp_path / "Product_Assets"
    _make_item(assets, "111", prompt=False)
    with pytest.raises(FileNotFoundError, match="kịch bản"):
        get_flow_assets("111", str(assets))


def test_collect_moves_video_into_item_folder(tmp_path):
    assets = tmp_path / "Product_Assets"
    _make_item(assets, "111")
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "111.mp4").write_bytes(b"mp4")
    moved = collect_flow_video("111", str(assets), str(downloads))
    assert moved == str(assets / "111" / "111.mp4")
    assert not (downloads / "111.mp4").exists()


def test_collect_returns_none_when_not_downloaded_yet(tmp_path):
    assets = tmp_path / "Product_Assets"
    _make_item(assets, "111")
    (tmp_path / "Downloads").mkdir()
    assert collect_flow_video("111", str(assets), str(tmp_path / "Downloads")) is None


def test_collect_never_overwrites_existing_video(tmp_path):
    assets = tmp_path / "Product_Assets"
    _make_item(assets, "111", video=True)
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "111.mp4").write_bytes(b"new")
    with pytest.raises(FileExistsError):
        collect_flow_video("111", str(assets), str(downloads))
    assert (assets / "111" / "111.mp4").read_bytes() == b"mp4"


def test_best_product_image_is_largest_non_character(tmp_path):
    from flow_helper import find_best_product_image
    d = tmp_path / "111"
    d.mkdir()
    (d / "111_small.webp").write_bytes(b"x" * 10)
    (d / "111_big.jpeg").write_bytes(b"x" * 1000)
    (d / "Nu-25t.png").write_bytes(b"x" * 5000)
    assert find_best_product_image(str(d)).endswith("111_big.jpeg")


def test_encode_flow_files_chunks_reassemble(tmp_path):
    import base64
    from flow_helper import encode_flow_files
    assets = tmp_path / "Product_Assets"
    d = _make_item(assets, "111")
    (d / "Nu-25t.png").write_bytes(bytes(range(256)) * 40)  # 10 KB
    msgs = encode_flow_files("111", str(assets), chunk_size=1000)
    meta = msgs[0]
    assert meta["type"] == "meta"
    assert [f["slot"] for f in meta["files"]] == ["product", "character", "script"]
    char = next(f for f in meta["files"] if f["slot"] == "character")
    parts = [m for m in msgs[1:] if m["slot"] == "character"]
    assert len(parts) == char["chunks"] > 1
    assert all(len(m["data"]) <= 1000 for m in msgs[1:])
    assert base64.b64decode("".join(m["data"] for m in parts)) == (d / "Nu-25t.png").read_bytes()
    script = next(f for f in meta["files"] if f["slot"] == "script")
    assert script["name"] == "111.txt" and script["mime"] == "text/plain"


@pytest.mark.skipif(not os.path.exists(os.path.join(PROJECT_DIR, "characters", "Nu-25t.png")), reason="ảnh nhân vật không có trong git")
def test_large_character_image_is_shrunk_to_jpeg(tmp_path):
    import base64, shutil
    from flow_helper import encode_flow_files
    assets = tmp_path / "Product_Assets"
    d = _make_item(assets, "111")
    shutil.copy(os.path.join(PROJECT_DIR, "characters", "Nu-25t.png"), d / "Nu-25t.png")  # ~7 MB
    msgs = encode_flow_files("111", str(assets))
    char = next(f for f in msgs[0]["files"] if f["slot"] == "character")
    assert char["name"] == "Nu-25t.jpg" and char["mime"] == "image/jpeg"
    data = base64.b64decode("".join(m["data"] for m in msgs[1:] if m["slot"] == "character"))
    assert data[:3] == b"\xff\xd8\xff" and len(data) < 2_000_000


def test_all_product_images_ordered_and_capped(tmp_path):
    from flow_helper import encode_flow_files
    assets = tmp_path / "Product_Assets"
    d = _make_item(assets, "111")  # 111_1.webp (3 bytes) + Nu-25t.png
    for i in range(2, 10):  # 8 more product images, bigger index = bigger file
        (d / f"111_{i}.jpeg").write_bytes(b"x" * (100 * i))
    meta = encode_flow_files("111", str(assets))[0]
    slots = [f["slot"] for f in meta["files"]]
    names = [f["name"] for f in meta["files"]]
    assert slots[:2] == ["product", "character"] and slots[-1] == "script"
    assert len(slots) - 1 == 7  # Flow max 7 images
    assert names[0] == "111_9.jpeg" and names[1] == "Nu-25t.png"
    assert names[2:7] == ["111_8.jpeg", "111_7.jpeg", "111_6.jpeg", "111_5.jpeg", "111_4.jpeg"]
