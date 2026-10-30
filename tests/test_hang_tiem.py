import json
import os
import sys

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import hang_tiem
from hang_tiem import sanpham_rows, prepare, build_info, cleanup, read_info, is_hang_tiem

import pytest


@pytest.fixture(autouse=True)
def _scene_state(tmp_path, monkeypatch):
    """Không đụng file xoay vòng bối cảnh thật (data/.hang_tiem_boi_canh.json)."""
    monkeypatch.setattr(hang_tiem, "SCENE_STATE", str(tmp_path / "boi_canh.json"))


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


def test_web_images_until_404_saved_as_jpg(tmp_path, monkeypatch):
    from hang_tiem import download_shop_web_images
    jpg = b"\xff\xd8\xff" + b"0" * 10
    urls = []
    def fake_fetch(url):
        urls.append(url)
        return jpg if len(urls) <= 3 else None
    saved = download_shop_web_images("32837N", str(tmp_path), fetch=fake_fetch)
    assert [os.path.basename(p) for p in saved] == ["32837N_web_01.jpg", "32837N_web_02.jpg", "32837N_web_03.jpg"]
    assert urls[0] == "https://giayhainancy.vn/img/32837N/1-1000.webp" and len(urls) == 4


def test_webp_converted_to_jpg_with_sips(tmp_path):
    import shutil, subprocess
    import pytest
    if not shutil.which("sips"):
        pytest.skip("không có sips")
    png = tmp_path / "a.png"
    subprocess.run(["sips", "-s", "format", "png", "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericDocumentIcon.icns",
                    "--out", str(png)], capture_output=True)
    if not png.exists():
        pytest.skip("không tạo được ảnh mẫu")
    out = tmp_path / "b.jpg"
    hang_tiem._save_as_jpg(png.read_bytes(), str(out))
    assert out.read_bytes()[:3] == b"\xff\xd8\xff"


def test_script_built_from_template_without_gemini(tmp_path):
    cfg = hang_tiem.load_config()
    info = build_info("32837D", dict(ROW, product_name="Giày mọi nam xỏ chân da bò hạt mềm 32837D",
                                     product_color="Đen", chat_lieu_de="phylon"))
    text = hang_tiem.build_script(info, cfg)
    for part in ("[ASSETS]", "[PROMPT]", "[CONSTRAINTS]", "men's slip-on loafers in black", "soft pebbled cowhide leather",
                 "lightweight phylon foam", cfg["boi_canh"]["nhom"]["tay"][0]["setting"], "Natural footsteps on stone",
                 cfg["model"]["nam"]):
        assert part in text
    assert "Shopee" not in text and "{" not in text
    assert "dress shoes" not in text and "only source of truth" in text
    assert "full-body" not in text and "knees down" in text and "own footwear" in text
    plain = hang_tiem.build_script(build_info("X", dict(ROW, product_name="Giày tây nam da bò X")), cfg)
    assert "men's shoes in brown" in plain and "dress shoes" not in plain
    female = hang_tiem.build_script(build_info("X", dict(ROW, gioi_tinh="nữ")), cfg)
    assert cfg["model"]["nu"] in female and "women's slip-on loafers in brown" in female


def test_write_script_copies_model_by_gender(tmp_path):
    chars = tmp_path / "chars"
    chars.mkdir()
    for name in ("Nam-25t.png", "Nu-23t.png", "Nu-25t.png"):
        (chars / name).write_bytes(b"x")
    d = tmp_path / "JH8918N"
    d.mkdir()
    (d / "info.json").write_text(json.dumps(build_info("JH8918N", ROW)))
    path = hang_tiem.write_script("JH8918N", str(d), characters_dir=str(chars))
    assert path.endswith("JH8918N.txt") and (d / "Nam-25t.png").exists() and not (d / "Nu-25t.png").exists()


def test_prompt_command_uses_template_for_shop_item(tmp_path, monkeypatch):
    import generate_ugc_prompt as g
    d = tmp_path / "JH8918N"
    d.mkdir()
    (d / "info.json").write_text(json.dumps(build_info("JH8918N", ROW)))
    monkeypatch.setattr(g, "call_gemini_multimodal_api", lambda *a, **k: (_ for _ in ()).throw(AssertionError("không được gọi Gemini")))
    assert g.generate_prompt_for_item("JH8918N", str(d)) == "Hàng tiệm"
    assert (d / "JH8918N.txt").exists()


# --- kiểu liền (HangTiem --lien, 30/10) ---
SHAPES = {"JH8918N_1.jpg": (1.40, 0.65), "JH8918N_2.jpg": (0.83, 0.79), "JH8918N_4.jpg": (1.61, 0.74),
          "JH8918N_6.jpg": (1.51, 0.61), "JH8918N_7.jpg": (2.23, 0.72), "JH8918N_8.jpg": (2.47, 0.70),
          "JH8918N_9.jpg": (2.71, 0.82), "JH8918N_10.jpg": (2.0, 0.9)}


def test_pick_lien_images_all_angles_front_first_sole_last(tmp_path):
    for name in list(SHAPES)[:7]:  # số đo thật của ảnh JH8918N
        (tmp_path / name).write_bytes(b"x")
    (tmp_path / "Nam-25t.png").write_bytes(b"x")
    shape = lambda p: SHAPES[os.path.basename(p)]
    # 7 ảnh giày, tối đa 6: bỏ JH8918N_4 (chéo 3/4 gần trùng ảnh 6)
    assert hang_tiem.pick_lien_images(str(tmp_path), shape=shape) == [
        "JH8918N_2.jpg", "JH8918N_6.jpg", "JH8918N_1.jpg", "JH8918N_7.jpg", "JH8918N_8.jpg", "JH8918N_9.jpg"]
    (tmp_path / "JH8918N_10.jpg").write_bytes(b"x")  # đế = số cuối theo số, không theo chữ (10 sau 9)
    picked = hang_tiem.pick_lien_images(str(tmp_path), shape=shape)
    assert len(picked) == 6 and picked[-1] == "JH8918N_10.jpg"


def test_lien_script_single_shot_no_object_negatives():
    cfg = hang_tiem.load_config()
    info = dict(build_info("JH8918N", ROW), kieu="lien", anh_lien=["a.jpg"] * 6)
    text = hang_tiem.build_script(info, cfg)
    assert "single continuous shot" in text and "first 6 reference images" in text
    assert "last reference image is the male model" in text
    assert "men's slip-on loafers in brown" in text and "Input Image" not in text and "{" not in text
    for word in ("laces", "buckle", "dress shoes", "[ASSETS]"):
        assert word not in text


def test_lien_write_script_crops_model_and_orders_paste(tmp_path):
    import shutil as sh
    import pytest
    if not os.path.exists(hang_tiem.FFMPEG):
        pytest.skip("không có ffmpeg")
    from flow_helper import encode_flow_files
    item = tmp_path / "JH8918N"
    item.mkdir()
    chars = tmp_path / "chars"
    chars.mkdir()
    src = os.path.join(PROJECT_DIR, "characters", "Nam-25t.png")
    sh.copy(src, chars / "Nam-25t.png")
    for i in range(1, 9):
        sh.copy(src, item / f"JH8918N_{i}.jpg")  # nội dung không quan trọng, chỉ cần ảnh đọc được
    hang_tiem.write_info(str(item), dict(build_info("JH8918N", ROW), kieu="lien"))
    hang_tiem.write_script("JH8918N", str(item), characters_dir=str(chars))
    info = read_info(str(item))
    assert len(info["anh_lien"]) == 6 and info["nguoi_mau_lien"] == "Nam-25t_tren.jpg"
    assert "first 6 reference images" in (item / "JH8918N.txt").read_text(encoding="utf-8")
    assert not (item / "Nam-25t.png").exists()  # không chép ảnh toàn thân (lộ giày người mẫu)
    slots = [f["slot"] for f in encode_flow_files("JH8918N", assets_dir=str(tmp_path))[0]["files"]]
    assert slots == ["product"] + [f"product_{i}" for i in range(2, 7)] + ["character", "script"]


def test_scene_rotates_per_shoe_group():
    cfg = hang_tiem.load_config()
    tay = build_info("A", ROW)
    sneaker = build_info("B", dict(ROW, product_name="Giày thể thao nam B"))
    heels = build_info("C", dict(ROW, product_name="Giày cao gót C", gioi_tinh="nữ"))
    names = [sc["ten"] for sc in cfg["boi_canh"]["nhom"]["tay"]]
    picked = [hang_tiem.pick_scene(tay, cfg) for _ in range(len(names) + 1)]
    assert picked == names + names[:1]  # 2 mã liền nhau không trùng, hết vòng quay lại
    assert hang_tiem.pick_scene(sneaker, cfg) == cfg["boi_canh"]["nhom"]["the_thao"][0]["ten"]
    assert hang_tiem.scene_group(heels, cfg) == "nu"
    assert hang_tiem.scene_group(build_info("D", dict(ROW, product_name="Giày D", gioi_tinh="nữ")), cfg) == "nu"
    assert hang_tiem.scene_group(build_info("E", dict(ROW, product_name="Dép nam E")), cfg) == "tay"


def test_lace_up_type():
    cfg = hang_tiem.load_config()
    info = build_info("G", dict(ROW, product_name="Giày tây nam cột dây Hải Nancy da bò cao cấp G2506N"))
    assert hang_tiem.describe_shoe(info, cfg)["type"] == "men's lace-up shoes"
    info["kieu_giay_tay"] = "Derby (buộc dây hở), đục lỗ (brogue)"
    assert hang_tiem.describe_shoe(info, cfg)["type"] == "men's lace-up shoes (Derby, brogue)"


def test_scene_text_and_sound_follow_chosen_scene():
    cfg = hang_tiem.load_config()
    scene = cfg["boi_canh"]["nhom"]["tay"][1]
    info = dict(build_info("A", ROW), kieu="lien", anh_lien=["a.jpg"] * 6, boi_canh=scene["ten"])
    text = hang_tiem.build_script(info, cfg)
    assert scene["setting"] in text and scene["sound"] in text and scene["walk"] in text
    assert "stone" not in text
    four = hang_tiem.build_script(dict(info, kieu="4_canh"), cfg)
    assert scene["setting"] in four and scene["sound"] in four and "stone" not in four


def test_lien_is_default_style(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(hang_tiem, "cleanup", lambda: [])
    monkeypatch.setattr(hang_tiem, "read_sanpham", lambda codes: {c: ROW for c in codes})
    monkeypatch.setattr(hang_tiem, "ASSETS_DIR", str(tmp_path))
    def fake_prepare(code, row):
        d = tmp_path / code
        d.mkdir(exist_ok=True)
        hang_tiem.write_info(str(d), build_info(code, row))
        return str(d)
    monkeypatch.setattr(hang_tiem, "prepare", fake_prepare)
    monkeypatch.setattr(hang_tiem, "write_script", lambda code, d, **kw: seen.setdefault(code, read_info(d)["kieu"]))
    hang_tiem.main(["jh8918n"])
    hang_tiem.main(["--4-canh", "X1"])
    assert seen == {"JH8918N": "lien", "X1": "4_canh"}



def test_combo_rotation_skips_used_and_disabled_motion():
    cfg = hang_tiem.load_config()
    slip = build_info("A", ROW)  # xỏ chân
    lace = build_info("B", dict(ROW, product_name="Giày tây nam cột dây B"))
    assert "mang_giay" not in hang_tiem.motions_for(slip, cfg)  # bat: false → chỉ gọi tay
    assert hang_tiem.motions_for(lace, cfg) == ["lui_ra", "tien_vao", "song_hanh", "vong_quanh"]
    first = hang_tiem.pick_combo(slip, cfg)
    second = hang_tiem.pick_combo(slip, cfg, used=[first])
    assert first != second and first[0] != second[0] and first[1] != second[1]  # 2 lần liền khác cả kiểu lẫn cảnh
    all_combos = hang_tiem.combos_for(slip, cfg)
    assert hang_tiem.pick_combo(slip, cfg, used=all_combos) is None


def test_each_motion_text_and_popup_label():
    cfg = hang_tiem.load_config()
    scene = cfg["boi_canh"]["nhom"]["tay"][1]
    for motion in ("lui_ra", "tien_vao", "song_hanh", "vong_quanh", "mang_giay"):
        info = dict(build_info("A", ROW), kieu="lien", anh_lien=["a"] * 6, chuyen_dong=motion, boi_canh=scene["ten"])
        text = hang_tiem.build_script(info, cfg)
        assert cfg["lien"]["chuyen_dong"][motion]["camera"].format(walk=scene["walk"]) in text
        assert "single continuous shot" in text and "{" not in text
    assert hang_tiem.popup_label(info, cfg) == "mang_giay · sảnh khách sạn"


def test_manual_motion_overrides_rotation(tmp_path):
    item = tmp_path / "A"
    item.mkdir()
    (item / "A_1.jpg").write_bytes(b"x")
    hang_tiem.write_info(str(item), dict(build_info("A", ROW), kieu="lien"))
    hang_tiem.write_script("A", str(item), characters_dir=str(tmp_path / "none"), motion="mang_giay")
    assert read_info(str(item))["chuyen_dong"] == "mang_giay"



def test_video_name_numbers_after_existing_videos(tmp_path):
    media, dl = tmp_path / "media", tmp_path / "dl"
    (media / "JH8918N").mkdir(parents=True)
    dl.mkdir()
    assert hang_tiem.video_name("JH8918N", str(media), str(dl)) == "JH8918N_1.mp4"
    (media / "JH8918N" / "JH8918N.mp4").write_bytes(b"v")  # tên cũ không hậu tố = 1 video
    (media / "JH8918N" / "JH8918N_1.jpg").write_bytes(b"i")  # ảnh không tính
    assert hang_tiem.video_name("JH8918N", str(media), str(dl)) == "JH8918N_2.mp4"
    (dl / "JH8918N_2.mp4").write_bytes(b"v")
    (dl / "JH8918N_20.mp4.crdownload").write_bytes(b"v")
    assert hang_tiem.video_name("JH8918N", str(media), str(dl)) == "JH8918N_3.mp4"
    (dl / "JH8918N_4.mp4").write_bytes(b"v")  # có lỗ: 3 video → số 4 đã có → 5
    assert hang_tiem.video_name("JH8918N", str(media), str(dl)) == "JH8918N_5.mp4"


def test_collect_and_cleanup_use_numbered_name(tmp_path):
    from flow_helper import collect_flow_video, encode_flow_files
    assets, dl = tmp_path / "assets", tmp_path / "dl"
    item = assets / "JH8918N"
    item.mkdir(parents=True)
    dl.mkdir()
    (item / "JH8918N.txt").write_text("x")
    (item / "JH8918N_1.jpg").write_bytes(b"i")
    hang_tiem.write_info(str(item), dict(build_info("JH8918N", ROW), kieu="lien", anh_lien=["JH8918N_1.jpg"],
                                         ten_video="JH8918N_2.mp4"))
    assert encode_flow_files("JH8918N", assets_dir=str(assets))[0]["output"] == "JH8918N_2.mp4"
    (dl / "JH8918N.mp4").write_bytes(b"old")
    assert collect_flow_video("JH8918N", str(assets), str(dl)) is None  # video cũ không phải của mục này
    (dl / "JH8918N_2.mp4").write_bytes(b"new")
    assert collect_flow_video("JH8918N", str(assets), str(dl)) == str(dl / "JH8918N_2.mp4")
    assert cleanup(str(assets), str(dl)) == []  # _2 còn ở Downloads
    os.remove(dl / "JH8918N_2.mp4")
    assert cleanup(str(assets), str(dl)) == ["JH8918N"]
