#!/usr/bin/env python3
"""
Omni Video - Archive & Clean Completed Product Videos
Tự động quét các thư mục sản phẩm trong Product_Assets/ (và ~/Downloads/<Mã_SP>.mp4):
1. Thư mục đã có video .mp4 -> xoá ảnh character, info.json, prompt_backups/.
2. Di chuyển toàn bộ thư mục sản phẩm hoàn thành về /Volumes/Media/Omni-Video/<Mã_SP>/
3. Cập nhật trạng thái trên Google Sheet thành "Đã tạo Video" + video_path.
Trước khi chuyển, mở tờ ảnh 10 khung <Mã_SP>_xem.jpg (N17) để anh Kha xem: Enter = Move, b = bỏ qua.
(Chế độ QA Gemini + tự học prompt đã chuyển vào archive/ ngày 21/10/2026.)
"""

import os
import sys
import shutil
import glob
import json
import urllib.request
import ssl


def _load_env_file():
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_file = os.path.join(project_dir, ".env")
    if not os.path.exists(env_file):
        return
    try:
        with open(env_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.replace("export", "").strip()
                val = val.strip().strip('"').strip("'")
                if val and (key not in os.environ or not os.environ[key]):
                    os.environ[key] = val
    except Exception:
        pass

_load_env_file()

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
CHARACTERS_DIR = os.path.join(PROJECT_DIR, "characters")
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
TARGET_MEDIA_DIR = "/Volumes/Media/Omni-Video"

def get_known_character_filenames():
    char_names = set()
    if os.path.exists(CHARACTERS_DIR):
        for ext in ["*.png", "*.jpg", "*.webp", "*.jpeg"]:
            for filepath in glob.glob(os.path.join(CHARACTERS_DIR, ext)):
                char_names.add(os.path.basename(filepath).lower())
    char_names.update(["nu-25t.png", "nam-25t.png", "nu-23t.png"])
    return char_names

def find_video_for_item(item_id, item_path):
    """
    Tìm file video .mp4 cho sản phẩm:
    1. Kiểm tra trực tiếp trong Product_Assets/<item_id>/
    2. Nếu chưa có, tự động quét trong ~/Downloads/ tìm file có tên khớp/chứa <item_id>
    Trả về (video_file_path, is_from_downloads)
    """
    # 1. Tìm trong thư mục Product_Assets/<item_id>/
    local_mp4s = glob.glob(os.path.join(item_path, "*.mp4")) + glob.glob(os.path.join(item_path, "*.MP4"))
    if local_mp4s:
        return local_mp4s[0], False

    # 2. Tìm trong thư mục ~/Downloads/
    if os.path.exists(DOWNLOADS_DIR):
        exact_dl = os.path.join(DOWNLOADS_DIR, f"{item_id}.mp4")
        if os.path.exists(exact_dl):
            return exact_dl, True
        exact_dl_upper = os.path.join(DOWNLOADS_DIR, f"{item_id}.MP4")
        if os.path.exists(exact_dl_upper):
            return exact_dl_upper, True

        dl_mp4s = glob.glob(os.path.join(DOWNLOADS_DIR, f"*{item_id}*.mp4")) + glob.glob(os.path.join(DOWNLOADS_DIR, f"*{item_id}*.MP4"))
        if dl_mp4s:
            return dl_mp4s[0], True

    return None, False

def update_google_sheet_video_status(item_id, output_file=None):
    try:
        from sheet_sync import update_status_by_item_id
        update_status_by_item_id(item_id, "Đã tạo Video", video_path=output_file)
    except Exception as e:
        print(f"  ⚠️ Lỗi cập nhật Sheet cho mã {item_id}:", e)

def safe_move_file(src: str, dst: str):
    """
    Safely moves a single file across filesystems / network shares (SMB/NAS).
    Bypasses macOS fcopyfile / copystat / xattr issues that cause [Errno 22] Invalid argument.
    """
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

    # Stream copy without copying xattr/flags to avoid EINVAL on SMB
    with open(src, "rb") as fsrc:
        with open(dst, "wb") as fdst:
            shutil.copyfileobj(fsrc, fdst, length=1024 * 1024)
    os.remove(src)

def safe_move_path(src_path: str, dst_path: str):
    """
    Recursively moves a file or directory across filesystems / network shares (SMB/NAS).
    """
    if os.path.isfile(src_path):
        safe_move_file(src_path, dst_path)
    elif os.path.isdir(src_path):
        os.makedirs(dst_path, exist_ok=True)
        for item in os.listdir(src_path):
            s = os.path.join(src_path, item)
            d = os.path.join(dst_path, item)
            safe_move_path(s, d)
        try:
            shutil.rmtree(src_path)
        except Exception:
            pass

def review_video(item_id, item_path, video_file, ask=input, show=None):
    """N17 (anh Kha chốt 28/10): tờ ảnh 10 khung trước khi Move. Trả về True = Move, False = bỏ qua.
    Tờ ảnh đi theo thư mục lên NAS; bỏ qua thì xoá tờ ảnh để thư mục chỉ còn nguyên liệu (làm lại không lẫn ảnh SP)."""
    sheet = os.path.join(item_path, f"{item_id}_xem.jpg")
    try:
        from contact_sheet import make_sheet
        make_sheet(video_file, sheet)
        (show or _open_for_review)(sheet)
        print(f"  🖼️ Tờ ảnh 10 khung: {sheet}")
    except Exception as e:
        sheet = None
        print(f"  ⚠️ Không tạo được tờ ảnh ({e}) — anh xem thẳng video: {video_file}")
    answer = ask("  👉 Enter = Move · b = bỏ qua (để làm lại): ").strip().lower()
    if answer.startswith("b"):
        if sheet and os.path.exists(sheet):
            os.remove(sheet)
        print("  ⏭️ Bỏ qua, thư mục giữ nguyên.")
        return False
    return True


def _open_for_review(path):
    """Mở tờ ảnh bằng Preview rồi đưa cửa sổ Terminal lên lại để anh bấm Enter / b."""
    import subprocess
    subprocess.run(["open", path], check=False)
    subprocess.run(["osascript", "-e", "delay 1", "-e", 'tell application "Terminal" to activate'],
                   check=False, capture_output=True)


def archive_completed_folders(review=None):
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
        
        # Tìm file video từ Product_Assets hoặc trực tiếp từ ~/Downloads/
        video_file, is_from_downloads = find_video_for_item(item_id, item_path)
        
        if not video_file:
            continue

        if is_from_downloads:
            print(f"\n🎬 Phát hiện video MP4 tại Downloads: {os.path.basename(video_file)} (Mã SP: {item_id})")
        else:
            print(f"\n🎬 Phát hiện video MP4 hoàn thành tại mã SP: {item_id}")

        if review and not review(item_id, item_path, video_file):
            continue

        # 3. Xóa thư mục prompt_backups nếu có (vì sản phẩm đã thành công)
        backups_dir = os.path.join(item_path, "prompt_backups")
        if os.path.exists(backups_dir):
            try:
                shutil.rmtree(backups_dir)
                print(f"  🗑️ Đã xóa thư mục backup thừa: prompt_backups/")
            except Exception as e:
                pass

        # 4. Xóa file info.json nếu có
        info_file = os.path.join(item_path, "info.json")
        if os.path.exists(info_file):
            try:
                os.remove(info_file)
                print(f"  🗑️ Đã xóa: info.json")
            except Exception as e:
                print(f"  ⚠️ Lỗi xóa info.json: {e}")

        # 5. Xóa ảnh character trong thư mục sản phẩm
        for f in os.listdir(item_path):
            f_lower = f.lower()
            if f_lower in known_chars or ("nu-" in f_lower) or ("nam-" in f_lower) or ("character" in f_lower):
                char_file_path = os.path.join(item_path, f)
                try:
                    os.remove(char_file_path)
                    print(f"  🗑️ Đã xóa ảnh character: {f}")
                except Exception as e:
                    print(f"  ⚠️ Lỗi xóa ảnh character {f}: {e}")

        # 6. Kiểm tra và di chuyển an toàn sang /Volumes/Media/Omni-Video/<item_id>/
        try:
            os.makedirs(TARGET_MEDIA_DIR, exist_ok=True)
            dest_item_path = os.path.join(TARGET_MEDIA_DIR, item_id)
            os.makedirs(dest_item_path, exist_ok=True)

            target_mp4_name = f"{item_id}.mp4"
            dest_video_path = os.path.join(dest_item_path, target_mp4_name)

            # A. Di chuyển file video an toàn từ nguồn (Downloads hoặc Product_Assets) sang Media
            safe_move_file(video_file, dest_video_path)

            # B. Di chuyển tất cả các file nguyên liệu còn lại trong Product_Assets/<item_id>/
            for f in os.listdir(item_path):
                src_f = os.path.join(item_path, f)
                dst_f = os.path.join(dest_item_path, f)
                safe_move_path(src_f, dst_f)

            if os.path.exists(item_path):
                try:
                    shutil.rmtree(item_path)
                except Exception:
                    pass

            print(f"  🚚 Đã dọn dẹp và di chuyển trọn bộ về: {dest_item_path}")
            print(f"  🎬 Video hoàn thiện: {dest_video_path}")
            
            # 7. Tự động cập nhật Google Sheet thành "Đã tạo Video" & lưu đường dẫn Cột 13 (Output File)
            update_google_sheet_video_status(item_id, output_file=dest_video_path)
            archived_count += 1


        except Exception as e:
            print(f"  ❌ Không thể di chuyển tới ổ đĩa Media ({TARGET_MEDIA_DIR}): {e}")
            print("     (Vui lòng kiểm tra ổ đĩa /Volumes/Media/ đã được kết nối chưa)")

    return archived_count

if __name__ == "__main__":
    print("============================================================")
    print("🚀 OMNI VIDEO - DI CHUYỂN VIDEO VỀ Ổ MEDIA")
    print("============================================================")
    print(f"📁 Thư mục đích: {TARGET_MEDIA_DIR}\n")
    
    # Chạy từ Move.command (có cửa sổ Terminal) thì hỏi từng video; chạy nền thì Move như cũ
    count = archive_completed_folders(review=review_video if sys.stdin.isatty() else None)
    print("\n============================================================")
    if count > 0:
        print(f"✅ HOÀN TẤT! Đã di chuyển và cập nhật Google Sheet cho {count} sản phẩm.")
    else:
        print("ℹ️ Chưa có thư mục sản phẩm nào chứa file video .mp4 mới.")
    print("============================================================")
