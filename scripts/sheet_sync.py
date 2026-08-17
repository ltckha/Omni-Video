"""Direct Google Sheets API v4 Synchronizer for Omni-Video.
100% DYNAMIC HEADER-BASED READ / WRITE ENGINE (Zero fixed-column assumptions).
Uses gspread and config/service_account.json.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

PROJECT_DIR = Path(__file__).resolve().parent.parent
SA_PATH = PROJECT_DIR / "config" / "service_account.json"
SPREADSHEET_ID = "1Xg67qhp1J_Izt7v5uDKRgKjdEZapX9giKJ_ym0OMJN4"

FIELD_ALIASES = {
    "job_id": ["job_id", "itemid", "mã sản phẩm", "sku", "id", "product_id"],
    "title": ["title", "productname", "tên sản phẩm", "tên sp", "tiêu đề"],
    "price": ["price", "giá", "đơn giá"],
    "sales_count": ["salescount", "doanh thu", "lượt bán", "đã bán"],
    "shop_name": ["shopname", "tên cửa hàng", "shop"],
    "product_url": ["producturl", "link", "url", "link sản phẩm"],
    "shopee_link": ["shopee_link", "link ưu đãi", "affiliate link"],
    "cdn_url": ["cdnurl", "link ảnh cdn chọn lọc", "image_url", "link ảnh cdn"],
    "local_path": ["localpath", "file ảnh lưu local", "đường dẫn local"],
    "status": ["status", "trạng thái master prompt", "trạng thái", "master_prompt_status"],
    "video_path": ["video_path", "file video xuất", "đường dẫn video"],
    "brand_fb": ["brand_fb", "fanpage facebook", "brand fb"],
    "brand_yt": ["brand_yt", "kênh youtube", "brand yt"],
    "brand_ig": ["brand_ig", "kênh instagram", "brand ig"],
    "brand_tt": ["brand_tt", "kênh tiktok", "brand tt", "tiktok brand"],
    "brand_shopee": ["brand_shopee", "brand shopee"],
    "brand_zalo": ["brand_zalo", "brand zalo"],
}

def normalize_name(s: str) -> str:
    return "".join(c for c in str(s).lower() if c.isalnum())

def get_gspread_client() -> Optional[gspread.Client]:
    if not SA_PATH.exists():
        logger.error(f"Service Account not found at {SA_PATH}")
        return None
    try:
        creds = Credentials.from_service_account_file(str(SA_PATH), scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        logger.error(f"Failed to authenticate with Service Account: {e}")
        return None

def get_all_product_statuses() -> Dict[str, str]:
    """Returns a dict mapping job_id -> status from Tab Omni-Video."""
    status_map = {}
    try:
        gc = get_gspread_client()
        if not gc:
            return status_map

        sh = gc.open_by_key(SPREADSHEET_ID)
        try:
            ws = sh.worksheet("Omni-Video")
        except Exception:
            ws = sh.get_worksheet(0)

        all_values = ws.get_all_values()
        if not all_values:
            return status_map

        headers = [str(h).strip() for h in all_values[0]]
        id_col_idx = -1
        status_col_idx = -1

        for i, h in enumerate(headers):
            norm_h = normalize_name(h)
            if norm_h in [normalize_name(a) for a in FIELD_ALIASES["job_id"]]:
                id_col_idx = i
            if norm_h in [normalize_name(a) for a in FIELD_ALIASES["status"]]:
                status_col_idx = i

        if id_col_idx == -1 or status_col_idx == -1:
            return status_map

        for row in all_values[1:]:
            if id_col_idx < len(row):
                j_id = str(row[id_col_idx]).strip()
                if j_id:
                    st = str(row[status_col_idx]).strip() if status_col_idx < len(row) else ""
                    status_map[j_id] = st

        return status_map
    except Exception as e:
        logger.error(f"Error fetching product statuses: {e}")
        return status_map

def update_status_by_item_id(item_id: str, new_status: str, video_path: Optional[str] = None) -> bool:
    """Dynamically updates the status column and optionally video_path column for item_id in tab Omni-Video."""
    try:
        gc = get_gspread_client()
        if not gc:
            return False

        sh = gc.open_by_key(SPREADSHEET_ID)
        try:
            ws = sh.worksheet("Omni-Video")
        except Exception:
            ws = sh.get_worksheet(0)

        all_values = ws.get_all_values()
        if not all_values:
            return False

        headers = [str(h).strip() for h in all_values[0]]

        id_col_idx = -1
        status_col_idx = -1
        video_col_idx = -1

        for i, h in enumerate(headers):
            norm_h = normalize_name(h)
            if norm_h in [normalize_name(a) for a in FIELD_ALIASES["job_id"]]:
                id_col_idx = i
            if norm_h in [normalize_name(a) for a in FIELD_ALIASES["status"]]:
                status_col_idx = i
            if norm_h in [normalize_name(a) for a in FIELD_ALIASES["video_path"]]:
                video_col_idx = i

        if id_col_idx == -1:
            return False

        for r_idx, row in enumerate(all_values[1:], start=2):
            if id_col_idx < len(row) and str(row[id_col_idx]).strip() == str(item_id).strip():
                if status_col_idx != -1:
                    ws.update_cell(r_idx, status_col_idx + 1, new_status)
                if video_path and video_col_idx != -1:
                    ws.update_cell(r_idx, video_col_idx + 1, str(video_path))
                print(f"📊 Đã cập nhật trạng thái '{new_status}' trên Google Sheet cho mã {item_id} (dòng {r_idx}).")
                return True

        return False
    except Exception as e:
        logger.error(f"Error updating status for '{item_id}': {e}")
        return False

def sync_product_to_sheet(info: Dict[str, Any], item_id: str) -> bool:
    """Appends or updates product data dynamically mapped to the Column Header names in Row 1."""
    try:
        gc = get_gspread_client()
        if not gc:
            return False

        sh = gc.open_by_key(SPREADSHEET_ID)
        try:
            ws = sh.worksheet("Omni-Video")
        except Exception:
            ws = sh.get_worksheet(0)

        all_values = ws.get_all_values()
        if not all_values:
            return False

        headers = [str(h).strip() for h in all_values[0]]
        
        # Build field dictionary
        product_dict = {
            "job_id": item_id,
            "title": info.get("productName") or info.get("title") or "",
            "price": info.get("price") or "",
            "sales_count": info.get("salesCount") or info.get("sales_count") or "",
            "shop_name": info.get("shopName") or info.get("shop_name") or "",
            "product_url": info.get("productUrl") or info.get("product_url") or "",
            "shopee_link": info.get("shopeeLink") or info.get("shopee_link") or "",
            "cdn_url": info.get("cdnUrl") or info.get("cdn_url") or "",
            "local_path": info.get("localPath") or f"Product_Assets/{item_id}/",
            "status": info.get("status") or "Đã chọn ảnh",
            "video_path": info.get("videoPath") or info.get("video_path") or "",
            "brand_fb": info.get("brand_fb") or "",
            "brand_yt": info.get("brand_yt") or "",
            "brand_ig": info.get("brand_ig") or "",
            "brand_tt": info.get("brand_tt") or "",
            "brand_shopee": info.get("brand_shopee") or "",
            "brand_zalo": info.get("brand_zalo") or "",
        }

        # Find key column index (job_id / itemId)
        id_col_idx = -1
        for i, h in enumerate(headers):
            norm_h = normalize_name(h)
            if norm_h in [normalize_name(a) for a in FIELD_ALIASES["job_id"]]:
                id_col_idx = i
                break

        # Check if item exists in sheet
        target_row_number = -1
        if id_col_idx != -1:
            for r_idx, row in enumerate(all_values[1:], start=2):
                if id_col_idx < len(row) and str(row[id_col_idx]).strip() == str(item_id).strip():
                    target_row_number = r_idx
                    break

        # Build dynamic row values according to the exact header positions
        row_values = []
        for h in headers:
            norm_h = normalize_name(h)
            matched_val = ""
            for field_key, val in product_dict.items():
                aliases = FIELD_ALIASES.get(field_key, [field_key])
                if norm_h in [normalize_name(a) for a in aliases]:
                    matched_val = val
                    break
            row_values.append(matched_val)

        if target_row_number > 0:
            # Update existing row
            ws.update(values=[row_values], range_name=f"A{target_row_number}", value_input_option="USER_ENTERED")
            logger.info(f"Updated product '{item_id}' at row {target_row_number} by header mapping.")
        else:
            # Append new row
            ws.append_row(row_values, value_input_option="USER_ENTERED")
            logger.info(f"Appended new product '{item_id}' by header mapping.")

        return True
    except Exception as e:
        logger.error(f"Error syncing product '{item_id}' to Google Sheets: {e}")
        return False
