#!/usr/bin/env python3
"""
Omni Video - Archive & Clean Completed Product Videos
Tự động quét các thư mục sản phẩm trong Product_Assets/:
1. Nếu đã có file video .mp4 -> Xóa ảnh character và file info.json.
2. Di chuyển toàn bộ thư mục sản phẩm hoàn thành về /Volumes/Media/Omni-Video/Product_Assets/
"""

import os
import shutil
import glob

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
CHARACTERS_DIR = os.path.join(PROJECT_DIR, "characters")
TARGET_MEDIA_DIR = "/Volumes/Media/Omni-Video/Product_Assets"

def get_known_character_filenames():
    char_names = set()
    if os.path.exists(CHARACTERS_DIR):
        for ext in ["*.png", "*.jpg", "*.webp", "*.jpeg"]:
            for filepath in glob.glob(os.path.join(CHARACTERS_DIR, ext)):
                char_names.add(os.path.basename(filepath).lower())
    # Bổ sung danh sách tên nhân vật mặc định
    char_names.update(["nu-25t.png", "nam-25t.png", "nu-23t.png"])
    return char_names

def archive_completed_folders():
    if not os.path.exists(ASSETS_DIR):
        print(f"❌ Thư mục {ASSETS_DIR} không tồn tại!")
        return 0

    known_chars = get_known_character_filenames()
    item_dirs = [d for d in os.listdir(ASSETS_DIR) if os.path.isdir(os.path.join(ASSETS_DIR, d))]

    if not item_dirs:
        print("ℹ️ Thư mục Product_Assets/ chưa có sản phẩm nào.")
        return 0

    archived_count = 0

    for item_id in item_dirs:
        item_path = os.path.join(ASSETS_DIR, item_id)
        
        # Tìm file .mp4 trong thư mục sản phẩm
        mp4_files = glob.glob(os.path.join(item_path, "*.mp4")) + glob.glob(os.path.join(item_path, "*.MP4"))
        
        if not mp4_files:
            continue

        print(f"\n🎬 Phát hiện video MP4 hoàn thành tại mã SP: {item_id}")

        # 1. Xóa file info.json nếu có
        info_file = os.path.join(item_path, "info.json")
        if os.path.exists(info_file):
            try:
                os.remove(info_file)
                print(f"  🗑️ Đã xóa: info.json")
            except Exception as e:
                print(f"  ⚠️ Lỗi xóa info.json: {e}")

        # 2. Xóa ảnh character trong thư mục sản phẩm
        for f in os.listdir(item_path):
            f_lower = f.lower()
            if f_lower in known_chars or ("nu-" in f_lower) or ("nam-" in f_lower) or ("character" in f_lower):
                char_file_path = os.path.join(item_path, f)
                try:
                    os.remove(char_file_path)
                    print(f"  🗑️ Đã xóa ảnh character: {f}")
                except Exception as e:
                    print(f"  ⚠️ Lỗi xóa ảnh character {f}: {e}")

        # 3. Kiểm tra và di chuyển thư mục sang /Volumes/Media/Omni-Video/Product_Assets/
        try:
            os.makedirs(TARGET_MEDIA_DIR, exist_ok=True)
            dest_item_path = os.path.join(TARGET_MEDIA_DIR, item_id)

            if os.path.exists(dest_item_path):
                # Nếu đã tồn tại ở ổ đĩa Media -> Di chuyển ghi đè các file mới
                for f in os.listdir(item_path):
                    src_f = os.path.join(item_path, f)
                    dst_f = os.path.join(dest_item_path, f)
                    if os.path.isfile(src_f):
                        shutil.move(src_f, dst_f)
                shutil.rmtree(item_path)
            else:
                shutil.move(item_path, dest_item_path)

            print(f"  🚚 Đã di chuyển thành công: Product_Assets/{item_id} -> {dest_item_path}")
            archived_count += 1
        except Exception as e:
            print(f"  ❌ Không thể di chuyển tới ổ đĩa Media ({TARGET_MEDIA_DIR}): {e}")
            print("     (Vui lòng kiểm tra ổ đĩa /Volumes/Media/ đã được kết nối chưa)")

    return archived_count

if __name__ == "__main__":
    print("============================================================")
    print("🚀 OMNI VIDEO - TỰ ĐỘNG DỌN DẸP & LƯU LẠI THƯ MỤC VIDEO HOÀN THÀNH")
    print("============================================================")
    print(f"📁 Thư mục đích: {TARGET_MEDIA_DIR}\n")
    
    count = archive_completed_folders()
    print("\n============================================================")
    if count > 0:
        print(f"✅ HOÀN TẤT! Đã dọn dẹp và di chuyển {count} thư mục sản phẩm hoàn thành.")
    else:
        print("ℹ️ Chưa có thư mục sản phẩm nào chứa file video .mp4 mới.")
    print("============================================================")
