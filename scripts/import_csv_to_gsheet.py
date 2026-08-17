#!/usr/bin/env python3
"""
Omni Video - Direct CSV Importer to Google Sheets API v4
Tự động đọc mọi file CSV (Shopee / TikTok), lọc trùng lặp sản phẩm thông minh,
dò tìm Header động của Tab 'Omni-Video' và ghi trực tiếp qua Google Sheets API v4 (Service Account).
Sau khi import xong, tự động di chuyển toàn bộ file CSV vào thư mục data/.
"""

import sys
import os
import glob
import csv
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ensure scripts directory is in sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR / "scripts"))

from sheet_sync import get_gspread_client, SPREADSHEET_ID, FIELD_ALIASES, normalize_name

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_DIR / "data"

# Extended CSV aliases for Shopee / TikTok CSV export formats
CSV_FIELD_ALIASES = {
    "job_id": ["mã sản phẩm", "itemid", "job_id", "mã sp", "id", "sku", "product id"],
    "title": ["tên sản phẩm", "title", "tên sp", "product name", "tiêu đề"],
    "price": ["giá", "price", "đơn giá", "giá bán"],
    "sales_count": ["doanh thu", "salescount", "sales_count", "lượt bán", "đã bán"],
    "shop_name": ["tên cửa hàng", "shopname", "shop_name", "tên shop", "cửa hàng"],
    "commission_rate": ["tỉ lệ hoa hồng", "tỷ lệ hoa hồng", "commission rate", "hoa hồng %"],
    "commission": ["hoa hồng", "commission", "tiền hoa hồng"],
    "product_url": ["link sản phẩm", "producturl", "link", "url", "product link"],
    "shopee_link": ["link ưu đãi", "shopeelink", "shopee_link", "affiliate link", "link rút gọn"],
}

def move_csv_to_data_folder(csv_filepath: Path):
    """Di chuyển file CSV đã import vào thư mục data/"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target_path = DATA_DIR / csv_filepath.name
    if csv_filepath.resolve() != target_path.resolve():
        try:
            shutil.move(str(csv_filepath), str(target_path))
            print(f"📦 Đã tự động di chuyển file CSV '{csv_filepath.name}' vào thư mục data/")
        except Exception as e:
            print(f"⚠️ Không thể di chuyển file CSV {csv_filepath.name} vào data/: {e}")

def organize_all_root_csvs():
    """Di chuyển tất cả các file CSV ở thư mục gốc dự án vào data/"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for root_csv in PROJECT_DIR.glob("*.csv"):
        target_path = DATA_DIR / root_csv.name
        if root_csv.resolve() != target_path.resolve():
            try:
                shutil.move(str(root_csv), str(target_path))
                print(f"📦 Đã di chuyển file CSV '{root_csv.name}' từ thư mục gốc vào data/")
            except Exception:
                pass

def parse_csv_file(csv_path: Path) -> List[Dict[str, str]]:
    """Đọc file CSV và trả về danh sách dict chuẩn hóa."""
    items = []
    if not csv_path.exists():
        return items

    with open(csv_path, "r", encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows or len(rows) < 2:
        return items

    raw_headers = [str(h).strip() for h in rows[0]]
    
    # Map CSV column index to normalized field name
    col_mapping = {}
    for idx, raw_h in enumerate(raw_headers):
        norm_h = normalize_name(raw_h)
        for field_key, aliases in CSV_FIELD_ALIASES.items():
            if norm_h in [normalize_name(a) for a in aliases]:
                col_mapping[idx] = field_key
                break

    for row in rows[1:]:
        if not row or not any(row):
            continue
        item_dict = {}
        for idx, field_key in col_mapping.items():
            if idx < len(row):
                item_dict[field_key] = row[idx].strip()
        
        job_id = item_dict.get("job_id", "")
        if job_id:
            items.append(item_dict)

    return items

def upload_csv_to_gsheet(csv_filepath: Path):
    print(f"📄 Đang đọc file CSV: {csv_filepath.name}...")
    new_items = parse_csv_file(csv_filepath)
    
    if not new_items:
        print("⚠️ File CSV trống hoặc không tìm thấy dữ liệu hợp lệ.")
        return

    print(f"🔍 Đã trích xuất {len(new_items)} dòng sản phẩm từ CSV.")
    print("🚀 Đang kết nối trực tiếp Google Sheets API v4 (Zero Webhooks)...")

    gc = get_gspread_client()
    if not gc:
        print("❌ Lỗi: Không thể kết nối Google Sheets qua Service Account.")
        return

    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
        try:
            ws = sh.worksheet("Omni-Video")
        except Exception:
            ws = sh.get_worksheet(0)

        all_values = ws.get_all_values()
        if not all_values:
            print("❌ Tab Omni-Video chưa có Header.")
            return

        headers = [str(h).strip() for h in all_values[0]]
        
        # Find key column index (job_id) in Sheet
        id_col_idx = -1
        for i, h in enumerate(headers):
            norm_h = normalize_name(h)
            if norm_h in [normalize_name(a) for a in FIELD_ALIASES["job_id"]]:
                id_col_idx = i
                break

        existing_ids = set()
        if id_col_idx != -1:
            for row in all_values[1:]:
                if id_col_idx < len(row) and row[id_col_idx].strip():
                    existing_ids.add(row[id_col_idx].strip())

        # Filter duplicates and build dynamic row values aligned to Sheet headers
        rows_to_append = []
        skipped_count = 0

        for item in new_items:
            item_id = item.get("job_id", "").strip()
            if item_id in existing_ids:
                skipped_count += 1
                continue
            
            existing_ids.add(item_id)
            
            # Map item fields to the exact columns of Tab Omni-Video
            row_data = []
            for h in headers:
                norm_h = normalize_name(h)
                if norm_h in [normalize_name(a) for a in FIELD_ALIASES.get("status", [])]:
                    row_data.append("Chưa chọn ảnh")
                    continue
                matched_val = ""
                for field_key, val in item.items():
                    aliases = CSV_FIELD_ALIASES.get(field_key, [field_key])
                    if norm_h in [normalize_name(a) for a in aliases]:
                        matched_val = val
                        break
                row_data.append(matched_val)
            
            rows_to_append.append(row_data)

        if rows_to_append:
            ws.append_rows(rows_to_append, value_input_option="USER_ENTERED")
            print(f"✨ Kết quả: Đã thêm mới thành công {len(rows_to_append)} sản phẩm vào Google Sheet!")
        else:
            print("✨ Kết quả: Tất cả sản phẩm trong CSV đã tồn tại trên Sheet (Không có sản phẩm mới).")

        if skipped_count > 0:
            print(f"ℹ️ Đã tự động lọc bỏ {skipped_count} sản phẩm bị trùng lặp.")

        # Di chuyển file CSV đã xử lý vào data/
        move_csv_to_data_folder(csv_filepath)

    except Exception as e:
        print(f"❌ Lỗi khi đồng bộ lên Google Sheets: {e}")

    organize_all_root_csvs()

if __name__ == "__main__":
    target_csv = None
    if len(sys.argv) > 1:
        target_csv = Path(sys.argv[1])
    else:
        # Scan in data/ and root
        candidates = list(PROJECT_DIR.glob("*.csv")) + list(DATA_DIR.glob("*.csv"))
        if candidates:
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            target_csv = candidates[0]

    if target_csv and target_csv.exists():
        upload_csv_to_gsheet(target_csv)
    else:
        print("ℹ️ Không tìm thấy file CSV mới nào để import.")
