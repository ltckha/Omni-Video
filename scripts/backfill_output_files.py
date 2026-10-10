#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script quét toàn bộ video đã hoàn thành tại /Volumes/Media/Omni-Video/
chuẩn hóa tên file thành <item_id>.mp4 và cập nhật hàng loạt đường dẫn file video vào Cột 13 (Output File) trên Google Sheet.
"""

import os
import sys
import glob
import shutil

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TARGET_MEDIA_DIR = "/Volumes/Media/Omni-Video"

# Import direct Google Sheets synchronizer
sys.path.append(os.path.join(PROJECT_DIR, "scripts"))
try:
    from sheet_sync import update_status_by_item_id
except Exception as e:
    print("❌ Lỗi import sheet_sync:", e)
    update_status_by_item_id = None

def safe_move_file(src: str, dst: str):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        try:
            os.remove(dst)
        except Exception:
            pass
    try:
        os.rename(src, dst)
        return
    except OSError:
        pass
    with open(src, "rb") as fsrc:
        with open(dst, "wb") as fdst:
            shutil.copyfileobj(fsrc, fdst, length=1024 * 1024)
    os.remove(src)

def backfill_output_files():
    if not update_status_by_item_id:
        print("❌ Lỗi: Không thể kết nối Google Sheets API v4.")
        return

    search_dirs = []
    if os.path.exists(TARGET_MEDIA_DIR):
        search_dirs.append(TARGET_MEDIA_DIR)
    else:
        print(f"⚠️ Chú ý: Thư mục ổ đĩa Media {TARGET_MEDIA_DIR} hiện chưa được kết nối/mount.")

    local_assets = os.path.join(PROJECT_DIR, "Product_Assets")
    if os.path.exists(local_assets):
        search_dirs.append(local_assets)

    if not search_dirs:
        print("❌ Không tìm thấy thư mục lưu trữ video nào!")
        return

    updated_count = 0
    for target_dir in search_dirs:
        print(f"\n🔍 Đang quét và chuẩn hóa các file video hoàn thành tại {target_dir}...")
        item_dirs = [d for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d)) and not d.startswith(".")]
        
        for item_id in sorted(item_dirs):
            item_path = os.path.join(target_dir, item_id)
            mp4s = glob.glob(os.path.join(item_path, "*.mp4")) + glob.glob(os.path.join(item_path, "*.MP4"))
            
            if not mp4s:
                continue

            current_video_file = mp4s[0]
            standard_video_name = f"{item_id}.mp4"
            standard_video_path = os.path.join(item_path, standard_video_name)


            # Tự động đổi tên file sang chuẩn <item_id>.mp4 nếu chưa đúng
            if os.path.basename(current_video_file) != standard_video_name:
                try:
                    safe_move_file(current_video_file, standard_video_path)
                    print(f"  🔄 Đã đổi tên: {os.path.basename(current_video_file)} -> {standard_video_name}")
                except Exception as e:
                    print(f"  ⚠️ Lỗi đổi tên file: {e}")
                    standard_video_path = current_video_file

            print(f"📦 Mã SP {item_id} -> File video: {standard_video_path}")

            try:
                success = update_status_by_item_id(item_id, "Đã tạo Video", video_path=standard_video_path)
                if success:
                    print(f"  ✅ Đã ghi Cột 13 (Output File) cho mã {item_id}")
                    updated_count += 1
                else:
                    print(f"  ⚠️ Không tìm thấy dòng cho mã {item_id} trên Sheet.")
            except Exception as e:
                print(f"  ❌ Lỗi cập nhật Sheet cho mã {item_id}:", e)

    print(f"\n🎉 HOÀN TẤT! Đã chuẩn hóa và đồng bộ đường dẫn Cột 13 (Output File) cho {updated_count} sản phẩm lên Google Sheet.")

if __name__ == "__main__":
    backfill_output_files()
