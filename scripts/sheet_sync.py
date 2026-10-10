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

def determine_default_brand(title: str = "", shop_name: str = "") -> str:
    """Returns 'Hiệu giày Hải Nancy' if footwear/nancy keywords match, else 'Mua Chuẩn Xài Lâu'."""
    text = f"{title} {shop_name}".lower()
    if any(k in text for k in ["hải nancy", "hai nancy", "nancyshoes", "giày da nam", "dép da nam"]):
        return "Hiệu giày Hải Nancy"
    return "Mua Chuẩn Xài Lâu"

def sync_product_to_sheet(info: Dict[str, Any], item_id: str) -> bool:
    """Appends or updates product data dynamically mapped to the Column Header names in Row 1.
    GUARANTEES NON-DESTRUCTIVE UPDATES (Never overwrites existing brand channels or fields with empty values).
    """
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

        title_val = info.get("productName") or info.get("title") or ""
        shop_val = info.get("shopName") or info.get("shop_name") or ""
        default_brand = determine_default_brand(title_val, shop_val)

        # Build field dictionary
        product_dict = {
            "job_id": item_id,
            "title": title_val,
            "price": info.get("price") or "",
            "sales_count": info.get("salesCount") or info.get("sales_count") or "",
            "shop_name": shop_val,
            "product_url": info.get("productUrl") or info.get("product_url") or "",
            "shopee_link": info.get("shopeeLink") or info.get("shopee_link") or "",
            "cdn_url": info.get("cdnUrl") or info.get("cdn_url") or "",
            "local_path": info.get("localPath") or f"Product_Assets/{item_id}/",
            "status": info.get("status") or "Đã chọn ảnh",
            "video_path": info.get("videoPath") or info.get("video_path") or "",
            "brand_fb": info.get("brand_fb") or (default_brand if target_row_number <= 0 else ""),
            "brand_yt": info.get("brand_yt") or (default_brand if target_row_number <= 0 else ""),
            "brand_ig": info.get("brand_ig") or (default_brand if target_row_number <= 0 else ""),
            "brand_tt": info.get("brand_tt") or (default_brand if target_row_number <= 0 else ""),
            "brand_shopee": info.get("brand_shopee") or (default_brand if target_row_number <= 0 else ""),
            "brand_zalo": info.get("brand_zalo") or (default_brand if target_row_number <= 0 else ""),
        }

        existing_row = all_values[target_row_number - 1] if (target_row_number > 0 and target_row_number <= len(all_values)) else []

        # Build dynamic row values according to the exact header positions
        row_values = []
        for c_idx, h in enumerate(headers):
            norm_h = normalize_name(h)
            matched_val = ""
            for field_key, val in product_dict.items():
                aliases = FIELD_ALIASES.get(field_key, [field_key])
                if norm_h in [normalize_name(a) for a in aliases]:
                    matched_val = str(val).strip()
                    break

            # Non-destructive preservation: if updating and matched_val is empty, preserve existing cell value!
            if target_row_number > 0:
                if not matched_val and c_idx < len(existing_row):
                    matched_val = existing_row[c_idx]
            else:
                # New row: ensure brand fields are not empty
                is_brand_col = any(norm_h in [normalize_name(a) for a in FIELD_ALIASES[b]] for b in ["brand_fb", "brand_yt", "brand_ig", "brand_tt", "brand_shopee", "brand_zalo"])
                if not matched_val and is_brand_col:
                    matched_val = default_brand

            row_values.append(matched_val)

        if target_row_number > 0:
            # Update existing row safely preserving old values
            ws.update(values=[row_values], range_name=f"A{target_row_number}", value_input_option="USER_ENTERED")
            logger.info(f"Updated product '{item_id}' at row {target_row_number} safely preserving brand channels.")
        else:
            # Append new row with populated default brands
            ws.append_row(row_values, value_input_option="USER_ENTERED")
            logger.info(f"Appended new product '{item_id}' with default brands.")

        return True
    except Exception as e:
        logger.error(f"Error syncing product '{item_id}' to Google Sheets: {e}")
        return False

def backfill_empty_brands_on_sheet() -> int:
    """Scans Tab Omni-Video and populates missing brand columns with appropriate default brand."""
    try:
        gc = get_gspread_client()
        if not gc:
            return 0
        sh = gc.open_by_key(SPREADSHEET_ID)
        try:
            ws = sh.worksheet("Omni-Video")
        except Exception:
            ws = sh.get_worksheet(0)

        all_values = ws.get_all_values()
        if len(all_values) < 2:
            return 0

        headers = [str(h).strip() for h in all_values[0]]
        brand_col_indices = []
        title_idx = -1
        shop_idx = -1

        for idx, h in enumerate(headers):
            norm_h = normalize_name(h)
            if norm_h in [normalize_name(a) for a in FIELD_ALIASES["title"]]:
                title_idx = idx
            if norm_h in [normalize_name(a) for a in FIELD_ALIASES["shop_name"]]:
                shop_idx = idx
            for b in ["brand_fb", "brand_yt", "brand_ig", "brand_tt", "brand_shopee", "brand_zalo"]:
                if norm_h in [normalize_name(a) for a in FIELD_ALIASES[b]]:
                    brand_col_indices.append(idx)
                    break

        if not brand_col_indices:
            return 0

        updated_count = 0
        for r_idx, row in enumerate(all_values[1:], start=2):
            title = row[title_idx] if title_idx != -1 and title_idx < len(row) else ""
            shop = row[shop_idx] if shop_idx != -1 and shop_idx < len(row) else ""
            default_brand = determine_default_brand(title, shop)
            row_needs_update = False
            new_row = list(row)
            while len(new_row) < len(headers):
                new_row.append("")

            for b_idx in brand_col_indices:
                if b_idx < len(new_row) and not str(new_row[b_idx]).strip():
                    new_row[b_idx] = default_brand
                    row_needs_update = True

            if row_needs_update:
                ws.update(values=[new_row], range_name=f"A{r_idx}", value_input_option="USER_ENTERED")
                updated_count += 1
                logger.info(f"Restored brand columns for row {r_idx} (Mã: {row[0] if row else ''}).")

        return updated_count
    except Exception as e:
        logger.error(f"Error backfilling brands: {e}")
        return 0

