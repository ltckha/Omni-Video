#!/usr/bin/env python3
"""
Omni Video - Auto File Organizer
Tự động dọn dẹp và phân loại file từ ~/Downloads vào đúng thư mục dự án:
- Ảnh sản phẩm: Product_Assets/<Mã_SP>/
- File dữ liệu CSV: data/
"""

import os
import shutil
import glob
import re

DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
DATA_DIR = os.path.join(PROJECT_DIR, "data")

def organize_files():
    if not os.path.exists(PROJECT_ASSETS_DIR):
        os.makedirs(PROJECT_ASSETS_DIR, exist_ok=True)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

    moved_count = 0

    # 1. Tự động di chuyển các file CSV từ ~/Downloads vào data/
    csv_patterns = [
        os.path.join(DOWNLOADS_DIR, "*.csv"),
        os.path.join(DOWNLOADS_DIR, "Omni-Video", "*.csv")
    ]
    for pattern in csv_patterns:
        for csv_path in glob.glob(pattern):
            if os.path.isfile(csv_path):
                filename = os.path.basename(csv_path)
                target_path = os.path.join(DATA_DIR, filename)
                try:
                    shutil.move(csv_path, target_path)
                    print(f"📄 Đã di chuyển file CSV {filename} -> data/")
                    moved_count += 1
                except Exception as e:
                    print(f"⚠️ Lỗi di chuyển file CSV {filename}: {e}")

    # 2. Tự động quét và di chuyển ảnh sản phẩm vào Product_Assets/<Mã_SP>/
    search_paths = [
        os.path.join(DOWNLOADS_DIR, "*.*"),
        os.path.join(DOWNLOADS_DIR, "Omni-Video", "*.*"),
        os.path.join(DOWNLOADS_DIR, "Omni-Video", "*", "*.*")
    ]

    for pattern in search_paths:
        for filepath in glob.glob(pattern):
            if not os.path.isfile(filepath):
                continue
            filename = os.path.basename(filepath)
            
            match = re.match(r"^(\d+|SP_\d+)_\d+\.(webp|jpg|jpeg|png)$", filename, re.IGNORECASE)
            if not match:
                match = re.match(r"^(\d+|SP_\d+)_.*\.(webp|jpg|jpeg|png)$", filename, re.IGNORECASE)

            if match:
                item_id = match.group(1)
                target_folder = os.path.join(PROJECT_ASSETS_DIR, item_id)
                os.makedirs(target_folder, exist_ok=True)
                
                target_path = os.path.join(target_folder, filename)
                try:
                    shutil.move(filepath, target_path)
                    print(f"📦 Đã di chuyển ảnh {filename} -> Product_Assets/{item_id}/")
                    moved_count += 1
                except Exception as e:
                    print(f"⚠️ Lỗi di chuyển ảnh {filename}: {e}")

    return moved_count

if __name__ == "__main__":
    print("🚀 Đang tự động quét và phân loại file vào thư mục dự án (Product_Assets/ & data/)...")
    count = organize_files()
    if count > 0:
        print(f"✅ Hoàn tất! Đã phân loại {count} file thành công!")
    else:
        print("ℹ️ Không có file mới nào cần di chuyển.")
