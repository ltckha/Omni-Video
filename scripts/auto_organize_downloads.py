#!/usr/bin/env python3
"""
Omni Video - Auto File Organizer
Tự động dọn dẹp và chuyển toàn bộ ảnh tải về từ ~/Downloads vào đúng thư mục dự án:
/Users/khan/Developer/Omni-Video/Product_Assets/<Mã_SP>/
"""

import os
import shutil
import glob
import re

DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
PROJECT_DOWNLOAD_DIR = "/Users/khan/Developer/Omni-Video/Product_Assets"

def organize_files():
    if not os.path.exists(PROJECT_DOWNLOAD_DIR):
        os.makedirs(PROJECT_DOWNLOAD_DIR, exist_ok=True)

    search_paths = [
        os.path.join(DOWNLOADS_DIR, "*.*"),
        os.path.join(DOWNLOADS_DIR, "Omni-Video", "*.*"),
        os.path.join(DOWNLOADS_DIR, "Omni-Video", "*", "*.*")
    ]

    moved_count = 0
    for pattern in search_paths:
        for filepath in glob.glob(pattern):
            if not os.path.isfile(filepath):
                continue
            filename = os.path.basename(filepath)
            
            match = re.match(r"^(\d+|SP_\d+)_\d+\.(webp|jpg|jpeg|png)$", filename, re.IGNORECASE)
            if match:
                item_id = match.group(1)
                target_folder = os.path.join(PROJECT_DOWNLOAD_DIR, item_id)
                os.makedirs(target_folder, exist_ok=True)
                
                target_path = os.path.join(target_folder, filename)
                try:
                    shutil.move(filepath, target_path)
                    print(f"📦 Đã chuyển file {filename} -> {target_path}")
                    moved_count += 1
                except Exception as e:
                    print(f"⚠️ Lỗi chuyển file {filename}: {e}")

    return moved_count

if __name__ == "__main__":
    print("🚀 Đang tự động quét và phân loại ảnh vào thư mục dự án Product_Assets...")
    count = organize_files()
    if count > 0:
        print(f"✅ Hoàn tất! Đã di chuyển {count} file ảnh vào /Users/khan/Developer/Omni-Video/Product_Assets/")
    else:
        print("ℹ️ Không có file ảnh mới nào cần di chuyển.")
