import json
import os
import sys

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts"))

import hang_cho
import hang_tiem

HEAD = [["nhóm"] * 6, ["product_code", "product_name", "product_color", "content_files", "web_in_stock", "gioi_tinh"]]


def row(code, name="Giày tây nam {c}", color="Đen", files="IMG", stock=""):
    return [code, name.format(c=code), color, files, stock, "nam"]


def setup(tmp_path):
    d = {k: tmp_path / k for k in ("assets", "dl", "media")}
    for p in d.values():
        p.mkdir()
    return d


def fake_make(calls, no_image=()):
    def make(code, r, lien, extra, assets_dir, media_dir, downloads_dir):
        calls.append((code, lien))
        if code in no_image:
            return None
        item = os.path.join(assets_dir, code)
        os.makedirs(item)
        hang_tiem.write_info(item, dict(hang_tiem.build_info(code, r), **extra))
        return item
    return make


def test_fills_to_five_newest_first_with_filters(tmp_path):
    d = setup(tmp_path)
    values = HEAD + [row("A1"), row("A2", files="VIDEO, IMG"), row("A3", stock="no"), row("A4", name="Túi xách {c}"),
                     row("A5", color=""), row("A6"), row("A7"), row("A8"), row("A9"), row("B1"), row("B2")]
    (d["dl"] / "B1.mp4").write_bytes(b"v")          # đang chờ HNC gom
    (d["assets"] / "A9").mkdir()                     # mã anh làm tay
    calls, logs = [], []
    added = hang_cho.run(values_fn=lambda: values, make=fake_make(calls, no_image={"A8"}), assets_dir=str(d["assets"]),
                         downloads_dir=str(d["dl"]), media_dir=str(d["media"]),
                         ledger_path=str(tmp_path / "ledger.json"), log_fn=logs.append)
    assert [c for c, _ in calls] == ["B2", "A8", "A7", "A6", "A1"] and all(l for _, l in calls)  # kiểu liền
    assert added == ["B2", "A7", "A6", "A1"]
    assert any("A8" in l and "không có ảnh" in l for l in logs)
    assert json.load(open(tmp_path / "ledger.json")) == added


def test_keeps_exactly_five_and_ignores_manual(tmp_path):
    d = setup(tmp_path)
    for i in range(5):
        item = d["assets"] / f"Q{i}"
        item.mkdir()
        hang_tiem.write_info(str(item), {"hang_tiem": True, "hang_cho": True})
    manual = d["assets"] / "M1"
    manual.mkdir()
    hang_tiem.write_info(str(manual), {"hang_tiem": True})
    calls = []
    hang_cho.run(values_fn=lambda: HEAD + [row("Z1")], make=fake_make(calls), assets_dir=str(d["assets"]),
                 downloads_dir=str(d["dl"]), media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"),
                 log_fn=lambda m: None)
    assert calls == [] and manual.exists()


def test_downloaded_item_frees_slot_after_hnc_gom(tmp_path):
    d = setup(tmp_path)
    item = d["assets"] / "Q1"
    item.mkdir()
    hang_tiem.write_info(str(item), {"hang_tiem": True, "hang_cho": True, "da_tai": "2026-10-30 10:00"})
    hang_cho.save_ledger(["Q1"], str(tmp_path / "l.json"))  # Q1 do hàng chờ tạo trước đó → không tạo lại
    calls = []
    hang_cho.run(values_fn=lambda: HEAD + [row("Q1"), row("Z1")], make=fake_make(calls), assets_dir=str(d["assets"]),
                 downloads_dir=str(d["dl"]), media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"),
                 log_fn=lambda m: None)
    assert not item.exists() and [c for c, _ in calls] == ["Z1"]  # Q1 đã dọn, bù Z1


def test_no_media_or_sheet_error_does_nothing(tmp_path):
    d = setup(tmp_path)
    item = d["assets"] / "Q1"
    item.mkdir()
    hang_tiem.write_info(str(item), {"hang_tiem": True, "hang_cho": True, "da_tai": "x"})
    logs = []
    kw = dict(make=fake_make([]), assets_dir=str(d["assets"]), downloads_dir=str(d["dl"]),
              ledger_path=str(tmp_path / "l.json"), log_fn=logs.append)
    assert hang_cho.run(values_fn=lambda: HEAD, media_dir=str(tmp_path / "khong_co"), **kw) == []
    def boom():
        raise RuntimeError("mất mạng")
    assert hang_cho.run(values_fn=boom, media_dir=str(d["media"]), **kw) == []
    assert item.exists() and len(logs) == 2 and all("⏸" in l for l in logs)
