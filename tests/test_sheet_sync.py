import os
import sys
import pytest
from unittest.mock import patch, MagicMock

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import gspread
from sheet_sync import (
    determine_default_brand, sync_product_to_sheet, backfill_empty_brands_on_sheet,
    get_all_product_statuses, update_status_by_item_id, write_changed_cells, get_omni_worksheet,
)


import sheet_sync

_real_get_brand_official_name = sheet_sync.get_brand_official_name


@pytest.fixture(autouse=True)
def fake_brands_tab():
    """No network: the 'brands' tab lookup returns the official name of yenyen_deals."""
    sheet_sync._brand_name_cache.clear()
    with patch("sheet_sync.get_brand_official_name", side_effect=lambda bid: {"yenyen_deals": "YenYen Deals"}.get(bid, "")):
        yield
    sheet_sync._brand_name_cache.clear()


def _client_with_brands(records):
    brands_ws = MagicMock()
    brands_ws.get_all_records.return_value = records
    sh = MagicMock()
    sh.worksheet.side_effect = lambda name: brands_ws if name == "brands" else MagicMock()
    gc = MagicMock()
    gc.open_by_key.return_value = sh
    return gc, sh


class TestSheetSyncBrands:
    def test_default_brand_is_yenyen_deals_for_any_product(self):
        assert determine_default_brand("Giày da nam cao cấp", "Hiệu Giày Hải Nancy") == "YenYen Deals"
        assert determine_default_brand("Máy cạo lông xù", "Shop Gia Dụng") == "YenYen Deals"

    @patch("sheet_sync.get_gspread_client")
    def test_official_name_read_by_header_and_cached(self, mock_get_client):
        gc, sh = _client_with_brands([
            {"brand_id": "mua_chuan_xai_lau", "official_name": "Mua Chuẩn Xài Lâu"},
            {"brand_id": "yenyen_deals", "official_name": "YenYen Deals"},
        ])
        mock_get_client.return_value = gc
        assert _real_get_brand_official_name("yenyen_deals") == "YenYen Deals"
        assert _real_get_brand_official_name("yenyen_deals") == "YenYen Deals"
        sh.worksheet.assert_called_once_with("brands")

    @patch("sheet_sync.get_gspread_client")
    def test_official_name_empty_when_tab_unreadable(self, mock_get_client):
        gc = MagicMock()
        gc.open_by_key.return_value.worksheet.side_effect = gspread.exceptions.WorksheetNotFound("brands")
        mock_get_client.return_value = gc
        assert _real_get_brand_official_name("yenyen_deals") == ""

    @patch("sheet_sync.get_gspread_client")
    def test_official_name_empty_when_brand_missing(self, mock_get_client):
        gc, _ = _client_with_brands([{"brand_id": "mua_chuan_xai_lau", "official_name": "Mua Chuẩn Xài Lâu"}])
        mock_get_client.return_value = gc
        assert _real_get_brand_official_name("yenyen_deals") == ""

    @patch("sheet_sync.get_gspread_client")
    def test_sync_product_preserves_existing_brands(self, mock_get_client):
        mock_gc = MagicMock()
        mock_sh = MagicMock()
        mock_ws = MagicMock()

        headers = ["job_id", "title", "price", "status", "video_path", "brand_fb", "brand_yt", "brand_ig", "brand_tt", "brand_shopee", "brand_zalo"]
        existing_row = ["12345", "Máy Cạo Lông Xù", "120k", "Đã chọn ảnh", "", "Mua Chuẩn Xài Lâu", "Mua Chuẩn Xài Lâu", "Mua Chuẩn Xài Lâu", "Mua Chuẩn Xài Lâu", "Mua Chuẩn Xài Lâu", "Mua Chuẩn Xài Lâu"]

        mock_ws.get_all_values.return_value = [headers, existing_row]
        mock_sh.worksheet.return_value = mock_ws
        mock_gc.open_by_key.return_value = mock_sh
        mock_get_client.return_value = mock_gc

        info = {
            "productName": "Máy Cạo Lông Xù V2",
            "price": "150k"
            # No brand fields passed
        }

        success = sync_product_to_sheet(info, "12345")
        assert success is True

        # Only changed cells are written (title B2, price C2), never the whole row
        mock_ws.update.assert_not_called()
        mock_ws.batch_update.assert_called_once()
        written = {u["range"]: u["values"][0][0] for u in mock_ws.batch_update.call_args[0][0]}
        assert written == {"B2": "Máy Cạo Lông Xù V2", "C2": "150k"}
        # Brand cells untouched
        assert not any(r[0] in "FGHIJK" for r in written)

    @patch("sheet_sync.get_gspread_client")
    def test_sync_new_product_populates_default_brands(self, mock_get_client):
        mock_gc = MagicMock()
        mock_sh = MagicMock()
        mock_ws = MagicMock()

        headers = ["job_id", "title", "price", "status", "video_path", "brand_fb", "brand_yt", "brand_ig", "brand_tt", "brand_shopee", "brand_zalo"]

        mock_ws.get_all_values.return_value = [headers]  # No existing products
        mock_sh.worksheet.return_value = mock_ws
        mock_gc.open_by_key.return_value = mock_sh
        mock_get_client.return_value = mock_gc

        info = {
            "productName": "Lồng đèn Capybara",
            "price": "80k"
        }

        success = sync_product_to_sheet(info, "99999")
        assert success is True

        mock_ws.append_row.assert_called_once()
        appended_values = mock_ws.append_row.call_args[0][0]

        # Verify that brand fields are populated with default brand
        assert appended_values[5] == "YenYen Deals"
        assert appended_values[6] == "YenYen Deals"


class TestOmniTabGuard:
    """Missing tab 'Omni-Video' must stop with an error, never fall back to tab 0 ('Status')."""

    def _client_without_tab(self, mock_get_client):
        mock_sh = MagicMock()
        mock_sh.worksheet.side_effect = gspread.exceptions.WorksheetNotFound("Omni-Video")
        mock_gc = MagicMock()
        mock_gc.open_by_key.return_value = mock_sh
        mock_get_client.return_value = mock_gc
        return mock_sh

    @patch("sheet_sync.get_gspread_client")
    def test_sync_product_stops_when_tab_missing(self, mock_get_client):
        mock_sh = self._client_without_tab(mock_get_client)
        assert sync_product_to_sheet({"productName": "X"}, "1") is False
        mock_sh.get_worksheet.assert_not_called()

    @patch("sheet_sync.get_gspread_client")
    def test_status_update_stops_when_tab_missing(self, mock_get_client):
        mock_sh = self._client_without_tab(mock_get_client)
        assert update_status_by_item_id("1", "Đã tạo Video") is False
        assert get_all_product_statuses() == {}
        assert backfill_empty_brands_on_sheet() == 0
        mock_sh.get_worksheet.assert_not_called()

    @patch("import_csv_to_gsheet.get_gspread_client")
    def test_import_csv_stops_when_tab_missing(self, mock_get_client, tmp_path):
        import import_csv_to_gsheet
        mock_sh = self._client_without_tab(mock_get_client)
        csv_file = tmp_path / "deals.csv"
        csv_file.write_text("x", encoding="utf-8")
        with patch.object(import_csv_to_gsheet, "parse_csv_file", return_value=[{"job_id": "1"}]), \
             patch.object(import_csv_to_gsheet, "move_csv_to_data_folder") as mock_move, \
             patch.object(import_csv_to_gsheet, "organize_all_root_csvs"):
            import_csv_to_gsheet.upload_csv_to_gsheet(csv_file)
        mock_sh.get_worksheet.assert_not_called()
        mock_move.assert_not_called()


class TestWriteChangedCells:
    def test_writes_only_differing_cells(self):
        ws = MagicMock()
        n = write_changed_cells(ws, 7, ["a", "B", "c", "new"], ["a", "b", "c"])
        assert n == 2
        data = ws.batch_update.call_args[0][0]
        assert data == [{"range": "B7", "values": [["B"]]}, {"range": "D7", "values": [["new"]]}]
        assert ws.batch_update.call_args[1]["value_input_option"] == "USER_ENTERED"

    def test_no_api_call_when_nothing_changed(self):
        ws = MagicMock()
        assert write_changed_cells(ws, 3, ["a", ""], ["a"]) == 0
        ws.batch_update.assert_not_called()

    @patch("sheet_sync.get_gspread_client")
    def test_backfill_writes_only_empty_brand_cells(self, mock_get_client):
        ws = MagicMock()
        headers = ["job_id", "title", "price", "brand_fb", "brand_yt"]
        ws.get_all_values.return_value = [headers, ["1", "Máy cạo lông", "=B2*2", "", "Hiệu giày Hải Nancy"]]
        sh = MagicMock(); sh.worksheet.return_value = ws
        gc = MagicMock(); gc.open_by_key.return_value = sh
        mock_get_client.return_value = gc
        assert backfill_empty_brands_on_sheet() == 1
        ws.update.assert_not_called()
        data = ws.batch_update.call_args[0][0]
        assert data == [{"range": "D2", "values": [["YenYen Deals"]]}]


class TestOmniTabName:
    """Tab is being renamed 'Omni-Video' -> 'src_omni': prefer the new name, accept the legacy one."""

    def _sheet_with_tabs(self, *names):
        tabs = {n: MagicMock(name=n) for n in names}
        sh = MagicMock()
        def lookup(name):
            if name in tabs:
                return tabs[name]
            raise gspread.exceptions.WorksheetNotFound(name)
        sh.worksheet.side_effect = lookup
        return sh, tabs

    def test_prefers_src_omni(self):
        sh, tabs = self._sheet_with_tabs("src_omni", "Omni-Video")
        assert get_omni_worksheet(sh) is tabs["src_omni"]

    def test_falls_back_to_legacy_name(self):
        sh, tabs = self._sheet_with_tabs("Status", "Omni-Video")
        assert get_omni_worksheet(sh) is tabs["Omni-Video"]

    def test_raises_when_neither_exists(self):
        sh, _ = self._sheet_with_tabs("Status")
        with pytest.raises(RuntimeError):
            get_omni_worksheet(sh)
        sh.get_worksheet.assert_not_called()


@patch("sheet_sync.get_gspread_client")
def test_alt_s_again_keeps_existing_status(mock_get_client):
    """P7: bấm Alt+S lại trên SP đã có video không được đặt status về "Đã chọn ảnh"."""
    ws = MagicMock()
    headers = ["job_id", "title", "status", "video_path"]
    ws.get_all_values.return_value = [headers, ["555", "Đèn học", "Đã tạo Video", "/Volumes/Media/Omni-Video/555/555.mp4"]]
    sh = MagicMock(); sh.worksheet.return_value = ws
    gc = MagicMock(); gc.open_by_key.return_value = sh
    mock_get_client.return_value = gc
    assert sync_product_to_sheet({"productName": "Đèn học"}, "555") is True
    ws.batch_update.assert_not_called()  # không có ô nào đổi


@patch("sheet_sync.get_gspread_client")
def test_new_row_still_gets_default_status(mock_get_client):
    ws = MagicMock()
    ws.get_all_values.return_value = [["job_id", "title", "status"]]
    sh = MagicMock(); sh.worksheet.return_value = ws
    gc = MagicMock(); gc.open_by_key.return_value = sh
    mock_get_client.return_value = gc
    assert sync_product_to_sheet({"productName": "Ô gấp"}, "777") is True
    assert ws.append_row.call_args[0][0][2] == "Đã chọn ảnh"
