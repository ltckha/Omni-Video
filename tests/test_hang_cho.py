import json
import os
import sys

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts"))

import hang_cho
import hang_tiem

HEAD = [["nhóm"] * 6, ["product_code", "product_name", "product_color", "content_files", "web_in_stock", "gioi_tinh"]]


def fake_fetch(out_of_stock=(), not_on_web=()):
    """Web giả: sitemap có mọi mã A*/B*/Q*/Z* trừ not_on_web; trang SP ghi InStock / OutOfStock."""
    codes = [f"{p}{i}" for p in "ABQZ" for i in range(10)]
    def fetch(url):
        if url == hang_cho.WEB_SITEMAP:
            return "".join(f"<url><loc>https://giayhainancy.vn/product/giay-tay-nam-{c.lower()}-{n}</loc></url>"
                           for n, c in enumerate(codes) if c not in not_on_web)
        code = url.rsplit("-", 2)[-2].upper()
        state = "OutOfStock" if code in out_of_stock else "InStock"
        return f'<script type="application/ld+json">{{"offers":{{"availability":"https://schema.org/{state}"}}}}</script>'
    return fetch


def row(code, name="Giày tây nam {c}", color="Đen", files="IMG", stock=""):
    return [code, name.format(c=code), color, files, stock, "nam"]


def setup(tmp_path):
    d = {k: tmp_path / k for k in ("assets", "dl", "media")}
    for p in d.values():
        p.mkdir()
    return d


def fake_make(calls, no_image=()):
    def make(code, r, lien, extra, used=(), assets_dir=None, media_dir=None, downloads_dir=None):
        calls.append((code, lien))
        if code in no_image:
            return None
        item = os.path.join(assets_dir, code)
        os.makedirs(item)
        hang_tiem.write_info(item, dict(hang_tiem.build_info(code, r), **extra, chuyen_dong="lui_ra",
                                        boi_canh=f"bc{len(used)}"))
        return item
    return make


def test_fills_to_five_newest_first_with_filters(tmp_path):
    d = setup(tmp_path)
    values = HEAD + [row("A1"), row("A2", files="VIDEO, IMG"), row("A3", stock="no"), row("A4", name="Túi xách {c}"),
                     row("A5", color=""), row("A6"), row("A7"), row("A8"), row("A9"), row("B1"), row("B2")]
    (d["dl"] / "B1.mp4").write_bytes(b"v")          # video cũ chờ HNC gom: vẫn vào được (tên mới B1_2.mp4)
    (d["assets"] / "A9").mkdir()                     # mã anh làm tay
    calls, logs = [], []
    added = hang_cho.run(values_fn=lambda: values, make=fake_make(calls, no_image={"A8"}), fetch=fake_fetch(), assets_dir=str(d["assets"]),
                         downloads_dir=str(d["dl"]), media_dir=str(d["media"]),
                         ledger_path=str(tmp_path / "ledger.json"), log_fn=logs.append)
    # mã chưa có video trước (mới nhất trước), rồi mới tới A2 (đã có video trên Sheet)
    assert [c for c, _ in calls] == ["B2", "B1", "A8", "A7", "A6", "A1"] and all(l for _, l in calls)  # kiểu liền
    assert added == ["B2", "B1", "A7", "A6", "A1"]
    assert any("A8" in l and "không có ảnh" in l for l in logs)
    assert [e["ma"] for e in json.load(open(tmp_path / "ledger.json"))] == added


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
    hang_cho.run(values_fn=lambda: HEAD + [row("Z1")], make=fake_make(calls), fetch=fake_fetch(), assets_dir=str(d["assets"]),
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
    hang_cho.run(values_fn=lambda: HEAD + [row("Q1"), row("Z1")], make=fake_make(calls), fetch=fake_fetch(), assets_dir=str(d["assets"]),
                 downloads_dir=str(d["dl"]), media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"),
                 log_fn=lambda m: None)
    assert [c for c, _ in calls] == ["Z1", "Q1"]  # Q1 đã dọn; mã mới Z1 trước, rồi Q1 làm video thứ 2
    assert hang_cho.load_ledger(str(tmp_path / "l.json"))[-1]["ma"] == "Q1"


def test_no_media_or_sheet_error_does_nothing(tmp_path):
    d = setup(tmp_path)
    item = d["assets"] / "Q1"
    item.mkdir()
    hang_tiem.write_info(str(item), {"hang_tiem": True, "hang_cho": True, "da_tai": "x"})
    logs = []
    kw = dict(make=fake_make([]), fetch=fake_fetch(), assets_dir=str(d["assets"]), downloads_dir=str(d["dl"]),
              ledger_path=str(tmp_path / "l.json"), log_fn=logs.append)
    assert hang_cho.run(values_fn=lambda: HEAD, media_dir=str(tmp_path / "khong_co"), **kw) == []
    def boom():
        raise RuntimeError("mất mạng")
    assert hang_cho.run(values_fn=boom, media_dir=str(d["media"]), **kw) == []
    assert item.exists() and len(logs) == 2 and all("⏸" in l for l in logs)


def test_skips_out_of_stock_or_not_on_web(tmp_path):
    d = setup(tmp_path)
    calls, logs = [], []
    added = hang_cho.run(values_fn=lambda: HEAD + [row("A1"), row("A2"), row("A3")], make=fake_make(calls),
                         fetch=fake_fetch(out_of_stock={"A3"}, not_on_web={"A2"}), assets_dir=str(d["assets"]),
                         downloads_dir=str(d["dl"]), media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"),
                         log_fn=logs.append)
    assert added == ["A1"] and [c for c, _ in calls] == ["A1"]
    assert any("A3" in l and "OutOfStock" in l for l in logs) and any("A2" in l and "không có trang SP" in l for l in logs)


def test_sitemap_error_does_nothing(tmp_path):
    import urllib.error
    d = setup(tmp_path)
    def broken(url):
        raise urllib.error.URLError("mất mạng")
    logs = []
    assert hang_cho.run(values_fn=lambda: HEAD + [row("A1")], make=fake_make([]), fetch=broken,
                        assets_dir=str(d["assets"]), downloads_dir=str(d["dl"]), media_dir=str(d["media"]),
                        ledger_path=str(tmp_path / "l.json"), log_fn=logs.append) == []
    assert "sitemap" in logs[0]


def test_web_product_urls_parses_code_from_link():
    sm = ("<loc>https://giayhainancy.vn/product/giay-tay-nam-cot-day-da-bo-cao-cap-3j658n-4755</loc>"
          "<loc>https://giayhainancy.vn/product/mh642v-101135</loc><loc>https://giayhainancy.vn/product-cat/x-6</loc>")
    assert hang_cho.web_product_urls(sm) == {"3J658N": "https://giayhainancy.vn/product/giay-tay-nam-cot-day-da-bo-cao-cap-3j658n-4755",
                                             "MH642V": "https://giayhainancy.vn/product/mh642v-101135"}


def test_cap_three_videos_and_unused_combo(tmp_path):
    d = setup(tmp_path)
    ledger = str(tmp_path / "l.json")
    hang_cho.save_ledger([{"ma": "Q1", "chuyen_dong": "lui_ra", "boi_canh": "pho_co"}] * 3
                         + [{"ma": "Q2", "chuyen_dong": "lui_ra", "boi_canh": "pho_co"}], ledger)
    seen = {}
    def make(code, r, lien, extra, used=(), **kw):
        seen[code] = list(used)
        return None
    hang_cho.run(values_fn=lambda: HEAD + [row("Q1"), row("Q2")], make=make, fetch=fake_fetch(),
                 assets_dir=str(d["assets"]), downloads_dir=str(d["dl"]), media_dir=str(d["media"]),
                 ledger_path=ledger, log_fn=lambda m: None)
    assert seen == {"Q2": [("lui_ra", "pho_co")]}  # Q1 đủ 3 video → bỏ; Q2 tránh tổ hợp đã dùng


def test_old_ledger_of_codes_still_reads():
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), "l.json")
    with open(path, "w") as f:
        json.dump(["A1", "B2"], f)
    assert hang_cho.load_ledger(path) == [{"ma": "A1"}, {"ma": "B2"}]


def test_queue_after_existing_video_reaches_a2(tmp_path):
    d = setup(tmp_path)
    calls = []
    added = hang_cho.run(values_fn=lambda: HEAD + [row("A2", files="VIDEO, IMG"), row("A1")], make=fake_make(calls),
                         fetch=fake_fetch(), assets_dir=str(d["assets"]), downloads_dir=str(d["dl"]),
                         media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"), log_fn=lambda m: None)
    assert added == ["A1", "A2"]  # mã chưa có video trước, mã đã có video sau
