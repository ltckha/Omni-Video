import os
import sys

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from rank_products import parse_money, parse_count, parse_rate, score_row, rank


def test_parsers_handle_shopee_formats():
    assert parse_money("₫22.196") == 22196
    assert parse_money("116,8k") == 116800
    assert parse_money("₫99.000 - ₫120.000") == 99000
    assert parse_money("") is None
    assert parse_count("70k+") == 70000
    assert parse_count("1,2k") == 1200
    assert parse_count("2tr") == 2_000_000
    assert parse_count("350") == 350
    assert parse_count("abc") is None
    assert parse_rate("19%") == 0.19
    assert parse_rate("") is None


def test_score_uses_commission_or_price_times_rate():
    assert score_row({"commission": "₫10.000", "sales_count": "2k"}) == 20_000_000
    assert score_row({"price": "100k", "commission_rate": "10%", "sales_count": "100"}) == 1_000_000
    assert score_row({"price": "100k", "sales_count": "100"}) is None


def test_rank_orders_and_skips_rows_with_video():
    values = [["job_id", "title", "commission", "sales_count", "status", "video_path"],
              ["1", "A", "₫1.000", "10", "Đã chọn ảnh", ""],
              ["2", "B", "₫5.000", "10", "Đã chọn ảnh", ""],
              ["3", "C", "₫9.000", "99", "Đã tạo Video", "/x/3.mp4"],
              ["4", "D", "", "", "Đã chọn ảnh", ""]]
    r = rank(values)
    assert [x[1]["job_id"] for x in r["ranked"]] == ["2", "1"]
    assert [x["job_id"] for x in r["missing"]] == ["4"]
    assert [x[1]["job_id"] for x in rank(values, only_without_video=False)["ranked"]] == ["3", "2", "1"]
