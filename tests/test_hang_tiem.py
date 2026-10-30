import json
import os
import sys

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import hang_tiem
from hang_tiem import sanpham_rows, prepare, build_info, cleanup, read_info, is_hang_tiem

ROW = {"product_code": "JH8918N", "product_name": "Giày tây nam xỏ chân da bò JH8918N", "product_color": "Nâu",
       "chat_lieu": "da bò", "chat_lieu_de": "cao su nhiệt TPR", "kieu_giay_tay": "", "gioi_tinh": "nam"}


def test_sanpham_rows_reads_headers_on_row_2():
    values = [["nhóm", "nhóm"], ["product_code", "product_name"], ["A1", "Giày A"], ["B2", "Giày B"]]
    assert sanpham_rows(values, ["B2", "X"]) == {"B2": {"product_code": "B2", "product_name": "Giày B"}}


def test_prepare_copies_only_nas_images_and_writes_info(tmp_path):
    nas = tmp_path / "nas" / "JH8918N"
    nas.mkdir(parents=True)
    (nas / "JH8918N_1.jpg").write_bytes(b"img")
    (nas / "JH8918N.mp4").write_bytes(b"video")
    item_dir = prepare("JH8918N", ROW, assets_dir=str(tmp_path / "assets"), media_dir=str(tmp_path / "nas"),
                       downloads_dir=str(tmp_path / "dl"), fetch_web=lambda *a: [])
    assert sorted(os.listdir(item_dir)) == ["JH8918N_1.jpg", "info.json"]
    info = read_info(item_dir)
    assert info["hang_tiem"] is True and info["productName"] == ROW["product_name"] and info["chat_lieu_de"] == "cao su nhiệt TPR"


def test_prepare_falls_back_to_web_images(tmp_path):
    def fake_web(code, row, item_dir):
        path = os.path.join(item_dir, f"{code}_web_01.jpg")
        open(path, "wb").write(b"img")
        return [path]
    item_dir = prepare("JH8918N", ROW, assets_dir=str(tmp_path / "assets"), media_dir=str(tmp_path / "nas"),
                       downloads_dir=str(tmp_path / "dl"), fetch_web=fake_web)
    assert os.path.exists(os.path.join(item_dir, "JH8918N_web_01.jpg"))


def test_prepare_without_images_skips_and_leaves_nothing(tmp_path):
    assert prepare("32837D", ROW, assets_dir=str(tmp_path / "assets"), media_dir=str(tmp_path / "nas"),
                   downloads_dir=str(tmp_path / "dl"), fetch_web=lambda *a: []) is None
    assert not (tmp_path / "assets" / "32837D").exists()


def test_build_info_rerun_clears_downloaded_mark():
    info = build_info("JH8918N", ROW, {"da_tai": "2026-10-30 10:00", "story_angle": "x"})
    assert "da_tai" not in info and info["story_angle"] == "x" and info["gioi_tinh"] == "nam"


def _shop_item(assets, code, da_tai=None):
    d = assets / code
    d.mkdir(parents=True)
    info = {"hang_tiem": True}
    if da_tai:
        info["da_tai"] = da_tai
    (d / "info.json").write_text(json.dumps(info))
    return d


def test_cleanup_only_after_video_left_downloads(tmp_path):
    assets, dl = tmp_path / "assets", tmp_path / "dl"
    dl.mkdir()
    _shop_item(assets, "A1", da_tai="x")
    _shop_item(assets, "B2", da_tai="x")
    (dl / "B2.mp4").write_bytes(b"v")
    _shop_item(assets, "C3")  # chưa tải video
    (assets / "11111111111").mkdir()  # SP Shopee
    assert cleanup(str(assets), str(dl)) == ["A1"]
    assert sorted(os.listdir(assets)) == ["11111111111", "B2", "C3"]


def test_collect_keeps_shop_video_in_downloads(tmp_path):
    from flow_helper import collect_flow_video, list_pending_items
    assets, dl = tmp_path / "assets", tmp_path / "dl"
    dl.mkdir()
    d = _shop_item(assets, "JH8918N")
    (d / "JH8918N.txt").write_text("kịch bản")
    assert [i["itemId"] for i in list_pending_items(str(assets))] == ["JH8918N"]
    (dl / "JH8918N.mp4").write_bytes(b"v")
    assert collect_flow_video("JH8918N", str(assets), str(dl)) == str(dl / "JH8918N.mp4")
    assert (dl / "JH8918N.mp4").exists() and read_info(str(d)).get("da_tai")
    assert list_pending_items(str(assets)) == []


def test_move_skips_shop_folder(tmp_path, monkeypatch):
    import archive_completed_videos as acv
    assets, dl = tmp_path / "assets", tmp_path / "dl"
    dl.mkdir()
    d = _shop_item(assets, "JH8918N")
    (dl / "JH8918N.mp4").write_bytes(b"v")
    monkeypatch.setattr(acv, "ASSETS_DIR", str(assets))
    monkeypatch.setattr(acv, "DOWNLOADS_DIR", str(dl))
    monkeypatch.setattr(acv, "TARGET_MEDIA_DIR", str(tmp_path / "nas"))
    assert acv.archive_completed_folders() == 0
    assert d.exists() and (dl / "JH8918N.mp4").exists() and is_hang_tiem(str(d))


def test_hang_tiem_directive_uses_config_and_gender():
    from generate_ugc_prompt import build_hang_tiem_directive, load_hang_tiem_config, load_central_prompt_rules
    cfg = load_hang_tiem_config()
    rules = load_central_prompt_rules(only=cfg["central_rule_sections"])
    assert "FORBIDDEN_ACTIONS" in rules and "CHARACTER_AND_VOICE_STANDARDS" not in rules
    text = build_hang_tiem_directive(build_info("JH8918N", ROW), cfg, rules)
    assert cfg["setting"] in text and cfg["model"]["nam"] in text and "cao su nhiệt TPR" in text
    assert "Shopee" not in text
    female = build_hang_tiem_directive(build_info("X", dict(ROW, gioi_tinh="nữ")), cfg, rules)
    assert cfg["model"]["nu"] in female
