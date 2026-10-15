import os
import sys
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import gspread
from fill_aff_links import load_aff_links, plan_writes, run

AFF_HDR = ["aff_id", "product_name", "keywords", "link", "commission_rate", "price", "shop", "shop_id",
           "category", "brands", "active", "updated_at", "source_file"]


def aff_row(aff_id, link, active="yes"):
    row = [""] * len(AFF_HDR)
    row[0], row[3], row[10] = aff_id, link, active
    return row


OMNI_HDR = ["job_id", "title", "shopee_link", "brand_fb"]


def test_load_only_active_affiliate_links():
    links = load_aff_links([AFF_HDR,
                            aff_row("1", "https://s.shopee.vn/a"),
                            aff_row("2", "https://s.shopee.vn/b", active="no"),
                            aff_row("3", "https://shopee.vn/product/1/3"),
                            aff_row("", "https://s.shopee.vn/c")])
    assert links == {"1": "https://s.shopee.vn/a"}


def test_empty_table_and_missing_columns_do_nothing():
    assert load_aff_links([]) == {}
    assert load_aff_links([AFF_HDR]) == {}
    assert load_aff_links([["aff_id", "link"], ["1", "https://s.shopee.vn/a"]]) == {}


def test_plan_fills_empty_or_plain_links_never_overwrites_affiliate():
    omni = [OMNI_HDR,
            ["1", "A", "", "YenYen Deals"],                              # trống -> điền
            ["2", "B", "https://shopee.vn/product/9/2", "YenYen Deals"],  # link thường -> điền
            ["3", "C", "https://s.shopee.vn/old", "YenYen Deals"],        # đã có TTLK -> giữ
            ["4", "D", "", "YenYen Deals"]]                               # không có trong aff_links
    links = {"1": "https://s.shopee.vn/n1", "2": "https://s.shopee.vn/n2", "3": "https://s.shopee.vn/n3"}
    assert plan_writes(omni, links) == [(2, 3, "1", "https://s.shopee.vn/n1"), (3, 3, "2", "https://s.shopee.vn/n2")]


def test_plan_handles_short_rows_and_column_order():
    omni = [["shopee_link", "x", "job_id"], ["", "", "7"], [""]]
    assert plan_writes(omni, {"7": "https://s.shopee.vn/z"}) == [(2, 1, "7", "https://s.shopee.vn/z")]


def _client(aff_values, omni_values):
    aff_ws, omni_ws = MagicMock(), MagicMock()
    aff_ws.get_all_values.return_value = aff_values
    omni_ws.get_all_values.return_value = omni_values
    omni_ws.title = "src_omni"
    sh = MagicMock()
    sh.worksheet.side_effect = lambda n: {"aff_links": aff_ws, "src_omni": omni_ws}[n] if n in ("aff_links", "src_omni") else (_ for _ in ()).throw(gspread.exceptions.WorksheetNotFound(n))
    gc = MagicMock()
    gc.open_by_key.return_value = sh
    return gc, omni_ws


@patch("fill_aff_links.get_gspread_client")
def test_run_dry_does_not_write(mock_client):
    gc, omni_ws = _client([AFF_HDR, aff_row("1", "https://s.shopee.vn/a")], [OMNI_HDR, ["1", "A", "", ""]])
    mock_client.return_value = gc
    assert run(apply=False) == 1
    omni_ws.batch_update.assert_not_called()


@patch("fill_aff_links.get_gspread_client")
def test_run_apply_writes_only_planned_cells(mock_client):
    gc, omni_ws = _client([AFF_HDR, aff_row("1", "https://s.shopee.vn/a")], [OMNI_HDR, ["1", "A", "", ""], ["2", "B", "", ""]])
    mock_client.return_value = gc
    assert run(apply=True) == 1
    data = omni_ws.batch_update.call_args[0][0]
    assert data == [{"range": "C2", "values": [["https://s.shopee.vn/a"]]}]


@patch("fill_aff_links.get_gspread_client")
def test_run_with_empty_aff_links_table(mock_client):
    gc, omni_ws = _client([AFF_HDR], [OMNI_HDR, ["1", "A", "", ""]])
    mock_client.return_value = gc
    assert run(apply=True) == 0
    omni_ws.batch_update.assert_not_called()
