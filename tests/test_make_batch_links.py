import os
import re
import sys
import zipfile

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from make_batch_links import product_url, pick_rows, write_batch_xlsx

HDR = ["job_id", "title", "product_url", "shopee_link"]


def test_product_url_normalizes_both_shopee_formats():
    assert product_url("https://shopee.vn/product/921100480/23630396929") == "https://shopee.vn/product/921100480/23630396929"
    assert product_url("https://shopee.vn/Den-hoc-i.123.456?sp_atk=x") == "https://shopee.vn/product/123/456"
    assert product_url("https://s.shopee.vn/abc") is None
    assert product_url("") is None


def test_pick_rows_skips_affiliate_links_and_duplicates():
    values = [HDR,
              ["1", "A", "https://shopee.vn/product/9/1", ""],                     # chưa có link -> lấy
              ["2", "B", "https://shopee.vn/x-i.9.2", "https://shopee.vn/product/9/2"],  # link thường -> lấy
              ["3", "C", "https://shopee.vn/product/9/3", "https://s.shopee.vn/ok"],  # đã TTLK -> bỏ
              ["1", "A", "https://shopee.vn/product/9/1", ""],                     # trùng -> bỏ
              ["4", "D", "", ""]]                                                  # không đọc được link
    picked, unreadable = pick_rows(values)
    assert picked == [("https://shopee.vn/product/9/1", "1"), ("https://shopee.vn/product/9/2", "2")]
    assert unreadable == ["4"]


def test_written_xlsx_keeps_shopee_header_and_rows(tmp_path):
    out = write_batch_xlsx([("https://shopee.vn/product/9/1", "1"), ("https://shopee.vn/product/9/2", "2&x")], str(tmp_path / "b.xlsx"))
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        sheet = z.read("xl/worksheets/sheet1.xml").decode()
        shared = z.read("xl/sharedStrings.xml").decode()
    assert "Liên kết gốc" in shared and "Sub_id1" in shared
    assert '<dimension ref="A1:F3"/>' in sheet
    assert '<c r="A2" t="inlineStr"><is><t>https://shopee.vn/product/9/1</t></is></c>' in sheet
    assert '<c r="B3" t="inlineStr"><is><t>2&amp;x</t></is></c>' in sheet
    assert len(re.findall(r"<row ", sheet)) == 3
