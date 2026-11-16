import json
import os
import sys

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts"))

import queue_products
import shop_products

import pytest
from datetime import datetime


@pytest.fixture(autouse=True)
def _sizes_file_in_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(queue_products, "SIZES", str(tmp_path / "sizes.json"))  # không ghi vào data/ thật


HEAD = [["nhóm"] * 6, ["product_code", "product_name", "product_color", "content_files", "web_in_stock", "gioi_tinh"]]


def fake_fetch(out_of_stock=(), not_on_web=(), sizes=None):
    """Web giả: sitemap có mọi mã A*/B*/Q*/Z* trừ not_on_web; trang SP ghi InStock / OutOfStock."""
    codes = [f"{p}{i}" for p in "ABQZ" for i in range(10)]
    def fetch(url):
        if url == queue_products.WEB_SITEMAP:
            return "".join(f"<url><loc>https://giayhainancy.vn/product/giay-tay-nam-{c.lower()}-{n}</loc></url>"
                           for n, c in enumerate(codes) if c not in not_on_web)
        code = url.rsplit("-", 2)[-2].upper()
        state = "OutOfStock" if code in out_of_stock else "InStock"
        n = (sizes or {}).get(code, 3)  # số size còn hàng; nút hết size chỉ có data-wait
        btns = "".join(f'<button data-size="{38 + i}">{38 + i}</button>' for i in range(n)) + '<button class="no" data-wait="50">50</button>'
        return (f'<script type="application/ld+json">{{"offers":{{"availability":"https://schema.org/{state}"}}}}</script>'
                f'<div class="sizes">{btns}</div>')
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
        shop_products.write_info(item, dict(shop_products.build_info(code, r), **extra, chuyen_dong="lui_ra",
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
    added = queue_products.run(values_fn=lambda: values, make=fake_make(calls, no_image={"A8"}), fetch=fake_fetch(), assets_dir=str(d["assets"]),
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
        shop_products.write_info(str(item), {"hang_tiem": True, "hang_cho": True})
    manual = d["assets"] / "M1"
    manual.mkdir()
    shop_products.write_info(str(manual), {"hang_tiem": True})
    calls = []
    queue_products.run(values_fn=lambda: HEAD + [row("Z1")], make=fake_make(calls), fetch=fake_fetch(), assets_dir=str(d["assets"]),
                 downloads_dir=str(d["dl"]), media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"),
                 log_fn=lambda m: None)
    assert calls == [] and manual.exists()


def test_downloaded_item_frees_slot_after_hnc_gom(tmp_path):
    d = setup(tmp_path)
    item = d["assets"] / "Q1"
    item.mkdir()
    shop_products.write_info(str(item), {"hang_tiem": True, "hang_cho": True, "da_tai": "2026-10-30 10:00"})
    queue_products.save_ledger(["Q1"], str(tmp_path / "l.json"))  # Q1 do hàng chờ tạo trước đó → không tạo lại
    calls = []
    queue_products.run(values_fn=lambda: HEAD + [row("Q1"), row("Z1")], make=fake_make(calls), fetch=fake_fetch(), assets_dir=str(d["assets"]),
                 downloads_dir=str(d["dl"]), media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"),
                 log_fn=lambda m: None)
    assert [c for c, _ in calls] == ["Z1", "Q1"]  # Q1 đã dọn; mã mới Z1 trước, rồi Q1 làm video thứ 2
    assert queue_products.load_ledger(str(tmp_path / "l.json"))[-1]["ma"] == "Q1"


def test_no_media_or_sheet_error_does_nothing(tmp_path):
    d = setup(tmp_path)
    item = d["assets"] / "Q1"
    item.mkdir()
    shop_products.write_info(str(item), {"hang_tiem": True, "hang_cho": True, "da_tai": "x"})
    logs = []
    kw = dict(make=fake_make([]), fetch=fake_fetch(), assets_dir=str(d["assets"]), downloads_dir=str(d["dl"]),
              ledger_path=str(tmp_path / "l.json"), log_fn=logs.append)
    assert queue_products.run(values_fn=lambda: HEAD, media_dir=str(tmp_path / "khong_co"), **kw) == []
    def boom():
        raise RuntimeError("mất mạng")
    assert queue_products.run(values_fn=boom, media_dir=str(d["media"]), **kw) == []
    assert item.exists() and len(logs) == 2 and all("⏸" in l for l in logs)


def test_skips_out_of_stock_or_not_on_web(tmp_path):
    d = setup(tmp_path)
    calls, logs = [], []
    added = queue_products.run(values_fn=lambda: HEAD + [row("A1"), row("A2"), row("A3")], make=fake_make(calls),
                         fetch=fake_fetch(out_of_stock={"A3"}, not_on_web={"A2"}), assets_dir=str(d["assets"]),
                         downloads_dir=str(d["dl"]), media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"),
                         log_fn=logs.append)
    assert added == ["A1"] and [c for c, _ in calls] == ["A1"]
    assert any("A3" in l and "OutOfStock" in l for l in logs) and any("A2" in l and "chưa có trang SP" in l for l in logs)


def test_sitemap_error_does_nothing(tmp_path):
    import urllib.error
    d = setup(tmp_path)
    def broken(url):
        raise urllib.error.URLError("mất mạng")
    logs = []
    assert queue_products.run(values_fn=lambda: HEAD + [row("A1")], make=fake_make([]), fetch=broken,
                        assets_dir=str(d["assets"]), downloads_dir=str(d["dl"]), media_dir=str(d["media"]),
                        ledger_path=str(tmp_path / "l.json"), log_fn=logs.append) == []
    assert "sitemap" in logs[0]


def test_web_product_urls_parses_code_from_link():
    sm = ("<loc>https://giayhainancy.vn/product/giay-tay-nam-cot-day-da-bo-cao-cap-3j658n-4755</loc>"
          "<loc>https://giayhainancy.vn/product/mh642v-101135</loc><loc>https://giayhainancy.vn/product-cat/x-6</loc>")
    assert queue_products.web_product_urls(sm) == {"3J658N": "https://giayhainancy.vn/product/giay-tay-nam-cot-day-da-bo-cao-cap-3j658n-4755",
                                             "MH642V": "https://giayhainancy.vn/product/mh642v-101135"}


def test_cap_three_videos_and_unused_combo(tmp_path):
    d = setup(tmp_path)
    ledger = str(tmp_path / "l.json")
    queue_products.save_ledger([{"ma": "Q1", "chuyen_dong": "lui_ra", "boi_canh": "pho_co"}] * 3
                         + [{"ma": "Q2", "chuyen_dong": "lui_ra", "boi_canh": "pho_co"}], ledger)
    seen = {}
    def make(code, r, lien, extra, used=(), **kw):
        seen[code] = list(used)
        return None
    queue_products.run(values_fn=lambda: HEAD + [row("Q1"), row("Q2")], make=make, fetch=fake_fetch(),
                 assets_dir=str(d["assets"]), downloads_dir=str(d["dl"]), media_dir=str(d["media"]),
                 ledger_path=ledger, log_fn=lambda m: None)
    assert seen == {"Q2": [("lui_ra", "pho_co")]}  # Q1 đủ 3 video → bỏ; Q2 tránh tổ hợp đã dùng


def test_old_ledger_of_codes_still_reads():
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), "l.json")
    with open(path, "w") as f:
        json.dump(["A1", "B2"], f)
    assert queue_products.load_ledger(path) == [{"ma": "A1"}, {"ma": "B2"}]


def test_queue_after_existing_video_reaches_a2(tmp_path):
    d = setup(tmp_path)
    calls = []
    added = queue_products.run(values_fn=lambda: HEAD + [row("A2", files="VIDEO, IMG"), row("A1")], make=fake_make(calls),
                         fetch=fake_fetch(), assets_dir=str(d["assets"]), downloads_dir=str(d["dl"]),
                         media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"), log_fn=lambda m: None)
    assert added == ["A1", "A2"]  # mã chưa có video trước, mã đã có video sau


def test_shift_note_ok_and_stop():
    assert queue_products.shift_note(["📦 Thêm 2 mã"], ["A", "B"], 5) == ("ok", "thêm 2 mã, chờ 5")
    assert queue_products.shift_note(["⏸ Lỗi đọc tab SANPHAM (X) — không làm gì.", "⏸ khác"], [], 3) == \
        ("loi", "Lỗi đọc tab SANPHAM (X) — không làm gì.")


def test_main_writes_shift_only_with_flag(monkeypatch):
    shifts = []
    monkeypatch.setattr(queue_products, "run", lambda log_fn=None: (log_fn("⏸ Không thấy ổ Media") if log_fn else None) or [])
    monkeypatch.setattr(queue_products, "log", lambda msg: None)
    monkeypatch.setattr(queue_products, "write_shift", lambda kq, note: shifts.append((kq, note)))
    queue_products.main([])
    assert shifts == []
    queue_products.main(["--log-health"])
    assert shifts == [("loi", "Không thấy ổ Media")]


def test_many_newer_codes_without_web_page_do_not_use_up_the_cap(tmp_path):
    """16/11: mã mới nhất đều chưa lên web; > 40 mã như vậy không được chặn việc quét lùi tới mã cũ hơn còn hàng."""
    d = setup(tmp_path)
    newer = [row(f"N{i:03d}") for i in range(queue_products.SO_MA_THU_TOI_DA + 30)]
    older = [row(f"A{i}") for i in range(1, 7)]  # có trong sitemap giả
    calls, logs = [], []
    added = queue_products.run(values_fn=lambda: HEAD + older + newer, make=fake_make(calls),
                               fetch=fake_fetch(), assets_dir=str(d["assets"]),  # mã N… không có trong sitemap giả
                               downloads_dir=str(d["dl"]), media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"),
                               log_fn=logs.append)
    assert len(added) == 5 and all(c.startswith("A") for c in added)
    assert sum("chưa có trang SP" in l for l in logs) == 1  # 1 dòng gộp, không 70 dòng


def test_more_in_stock_sizes_first_among_same_video_count(tmp_path):
    d = setup(tmp_path)
    calls = []
    sz = {"A1": 2, "A2": 7, "A3": 5, "A4": 1, "A5": 6, "A6": 4, "A7": 3}
    added = queue_products.run(values_fn=lambda: HEAD + [row(f"A{i}") for i in range(1, 8)], make=fake_make(calls),
                               fetch=fake_fetch(sizes=sz), assets_dir=str(d["assets"]), downloads_dir=str(d["dl"]),
                               media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"), log_fn=lambda m: None)
    assert added == ["A2", "A5", "A3", "A6", "A7"]  # 7, 6, 5, 4, 3 size; A1 (2) và A4 (1) ở lại


def test_web_sizes_counts_only_in_stock_buttons():
    page = '<div class="sizes"><button data-size="38">38</button><button class="no" data-wait="39">39</button><button data-size="40">40</button></div>'
    assert queue_products.web_sizes(page) == {"38", "40"}
    assert queue_products.web_sizes("<p>không có size</p>") == set()


def run_args(d, tmp_path, values, calls, fetch):
    return dict(values_fn=lambda: values, make=fake_make(calls), fetch=fetch, assets_dir=str(d["assets"]),
                downloads_dir=str(d["dl"]), media_dir=str(d["media"]), ledger_path=str(tmp_path / "l.json"),
                log_fn=lambda m: None)


def test_restock_is_detected_from_previous_run_and_saved(tmp_path):
    import json
    d = setup(tmp_path)
    rows = HEAD + [row("A1", files="VIDEO")]
    queue_products.run(**run_args(d, tmp_path, rows, [], fake_fetch(sizes={"A1": 2})))   # lần 1: size 38, 39
    book = json.load(open(queue_products.SIZES))
    assert book["A1"]["sizes"] == ["38", "39"] and "restock" not in book["A1"]
    import shutil
    shutil.rmtree(d["assets"] / "A1")  # mỗi mã 1 mục chờ: bỏ mục lần 1 để lần 2 xét lại mã này
    queue_products.run(**run_args(d, tmp_path, rows, [], fake_fetch(sizes={"A1": 4})))   # lần 2: thêm 40, 41
    book = json.load(open(queue_products.SIZES))
    assert book["A1"]["added"] == ["40", "41"] and book["A1"]["restock"] == datetime.now().strftime("%Y-%m-%d")


def test_restocked_code_goes_right_after_codes_without_video(tmp_path, monkeypatch):
    import json
    from datetime import timedelta
    d = setup(tmp_path)
    monkeypatch.setattr(queue_products, "SO_MA_CHO", 4)
    today = datetime.now()
    ago = lambda n: (today - timedelta(days=n)).strftime("%Y-%m-%d")
    json.dump({"A6": {"sizes": ["38"], "at": ago(1), "restock": ago(1), "added": ["38"]},
               "A5": {"sizes": [str(38 + i) for i in range(6)], "at": ago(20), "restock": ago(20), "added": ["38"]}},  # quá 14 ngày: không ưu tiên
              open(queue_products.SIZES, "w"))
    vid = {f"A{i}" for i in (4, 5, 6, 7)}
    rows = HEAD + [row(f"A{i}", files="VIDEO" if f"A{i}" in vid else "IMG") for i in range(1, 8)]
    calls = []
    added = queue_products.run(**run_args(d, tmp_path, rows, calls, fake_fetch(sizes={"A4": 6, "A5": 6, "A6": 1, "A7": 6})))
    assert added[:3] == ["A1", "A2", "A3"] or sorted(added[:3]) == ["A1", "A2", "A3"]
    assert added[3] == "A6"  # có video, ít size, nhưng mới bù size → trước A4 / A5 / A7
