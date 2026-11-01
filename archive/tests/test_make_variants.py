import json
import os
import sys
from unittest.mock import patch

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import make_variants
from make_variants import variant_ids, prepare_variant_dir
from fill_aff_links import base_item_id, plan_writes


def test_variant_ids_capped_2_to_3():
    assert variant_ids("123", 2) == ["123-2"]
    assert variant_ids("123", 3) == ["123-2", "123-3"]
    assert variant_ids("123", 9) == ["123-2", "123-3"]
    assert variant_ids("123", 1) == ["123-2"]


def test_prepare_variant_dir_copies_product_images_and_info_only(tmp_path):
    base = tmp_path / "123"
    base.mkdir()
    (base / "123_a.webp").write_bytes(b"a")
    (base / "123_b.jpeg").write_bytes(b"b")
    (base / "Nu-25t.png").write_bytes(b"c")
    (base / "123.txt").write_text("prompt", encoding="utf-8")
    (base / "123.mp4").write_bytes(b"v")
    (base / "info.json").write_text(json.dumps({"productName": "Đèn", "story_angle": "X"}), encoding="utf-8")
    vdir = prepare_variant_dir(str(base), "123-2", assets_dir=str(tmp_path))
    assert sorted(os.listdir(vdir)) == ["123-2_a.webp", "123-2_b.jpeg", "info.json"]
    info = json.load(open(os.path.join(vdir, "info.json"), encoding="utf-8"))
    assert info == {"productName": "Đèn", "variantOf": "123"}


def test_variant_rows_fall_back_to_base_affiliate_link():
    assert base_item_id("123-2") == "123" and base_item_id("123") == "123"
    omni = [["job_id", "shopee_link"], ["123", ""], ["123-2", ""], ["123-3", "https://s.shopee.vn/own"]]
    assert plan_writes(omni, {("123", ""): "https://s.shopee.vn/base"}) == [
        (2, 2, "123", "https://s.shopee.vn/base"), (3, 2, "123-2", "https://s.shopee.vn/base")]


def test_dry_run_creates_nothing(tmp_path, monkeypatch, capsys):
    base = tmp_path / "123"
    base.mkdir()
    (base / "123_a.webp").write_bytes(b"a")
    monkeypatch.setattr(make_variants, "ASSETS_DIR", str(tmp_path))
    monkeypatch.setattr(sys, "argv", ["make_variants.py", "123", "--count", "3", "--dry"])
    assert make_variants.main() == 0
    assert sorted(os.listdir(tmp_path)) == ["123"]
    assert "123-2, 123-3" in capsys.readouterr().out


def test_select_story_angle_excludes_used_angles():
    import generate_ugc_prompt as gen
    first = gen.select_story_angle("Máy cạo lông")[0]
    for _ in range(30):
        assert gen.select_story_angle("Máy cạo lông", exclude=[first])[0] != first
