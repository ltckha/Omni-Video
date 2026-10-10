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

from sheet_sync import determine_default_brand, sync_product_to_sheet, backfill_empty_brands_on_sheet


class TestSheetSyncBrands:
    def test_determine_default_brand_footwear_nancy(self):
        assert determine_default_brand("Giày da nam cao cấp", "Hiệu Giày Hải Nancy") == "Hiệu giày Hải Nancy"
        assert determine_default_brand("Dép da nam xịn", "Shop NancyShoes") == "Hiệu giày Hải Nancy"

    def test_determine_default_brand_general_product(self):
        assert determine_default_brand("Máy cạo lông xù", "Shop Gia Dụng") == "Mua Chuẩn Xài Lâu"
        assert determine_default_brand("Lồng đèn Capybara", "Đồ chơi trẻ em") == "Mua Chuẩn Xài Lâu"

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

        mock_ws.update.assert_called_once()
        updated_values = mock_ws.update.call_args[1]["values"][0]

        # Verify that brand fields were preserved from existing_row!
        assert updated_values[5] == "Mua Chuẩn Xài Lâu"  # brand_fb
        assert updated_values[6] == "Mua Chuẩn Xài Lâu"  # brand_yt
        assert updated_values[7] == "Mua Chuẩn Xài Lâu"  # brand_ig
        assert updated_values[8] == "Mua Chuẩn Xài Lâu"  # brand_tt
        assert updated_values[9] == "Mua Chuẩn Xài Lâu"  # brand_shopee
        assert updated_values[10] == "Mua Chuẩn Xài Lâu" # brand_zalo

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
        assert appended_values[5] == "Mua Chuẩn Xài Lâu"
        assert appended_values[6] == "Mua Chuẩn Xài Lâu"
