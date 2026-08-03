#!/usr/bin/env python3
"""
Omni Video - Archive & Clean Completed Product Videos with QA & Prompt Evolution
Tự động quét các thư mục sản phẩm trong Product_Assets/:
1. Nếu đã có file video .mp4 -> Phân tích chất lượng QA bằng Gemini Video Understanding API.
2. Tự động Sao Lưu (Backup) & Tinh chỉnh Nâng Cấp Master Prompt theo bài học QA.
3. Xóa ảnh character và file info.json.
4. Di chuyển toàn bộ thư mục sản phẩm hoàn thành về /Volumes/Media/Omni-Video/Product_Assets/
5. Cập nhật trạng thái Master Prompt trên Google Sheet thành "Đã tạo Video".
"""

import os
import shutil
import glob
import json
import urllib.request
import ssl

from video_qa_analyzer import analyze_video_quality
from prompt_evolution_engine import backup_current_prompt, evolve_prompt_from_qa

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
TARGET_MEDIA_DIR = "/Volumes/Media/Omni-Video/Product_Assets"
WEBHOOK_URL = os.environ.get("OMNI_GAS_WEBHOOK_URL", "")

def get_known_character_filenames():
    char_names = set()
    if os.path.exists(CHARACTERS_DIR):
        for ext in ["*.png", "*.jpg", "*.webp", "*.jpeg"]:
            for filepath in glob.glob(os.path.join(CHARACTERS_DIR, ext)):
                char_names.add(os.path.basename(filepath).lower())
    char_names.update(["nu-25t.png", "nam-25t.png", "nu-23t.png"])
    return char_names

def update_google_sheet_video_status(item_id):
    if not WEBHOOK_URL:
        return

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    payload = {
        "action": "update_status",
        "itemId": item_id,
        "status": "Đã tạo Video"
    }

    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "text/plain;charset=utf-8"}
    )

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  📊 Đã cập nhật trạng thái Google Sheet cho mã {item_id} thành 'Đã tạo Video':", data.get("message", "Thành công"))
    except Exception as e:
        print(f"  ⚠️ Lỗi cập nhật Sheet cho mã {item_id}:", e)

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
        video_file = mp4_files[0]

        # 1. Chạy phân tích QA video bằng Gemini Video Understanding API
        qa_report = analyze_video_quality(video_file, item_path)

        # 2. Tự động Sao Lưu (Backup) & Tự Học Nâng Cấp Master Prompt
        qa_score = 100
        if qa_report:
            qa_score = qa_report.get("total_score", 100)
            evolve_prompt_from_qa(item_path, qa_report)
        else:
            backup_current_prompt(item_path)

        # 🛑 CHỐT CHẶN CHẤT LƯỢNG (QA GATE): Nếu video dưới 70 điểm -> GIỮ NGUYÊN KHÔNG MOVE
        if qa_score < 70:
            print(f"🛑 CHÚ Ý: VideoSP {item_id} chưa đạt chuẩn QA (Điểm: {qa_score}/100 < 70 điểm tối thiểu).")
            print(f"   👉 Giữ nguyên thư mục tại Product_Assets/{item_id}/ để anh/chị xem lỗi và làm lại video!")
            print(f"   💡 Prompt đã được AI tự nâng cấp bài học để sửa lỗi cho lần sinh tiếp theo.")
            continue

        # 3. Xóa file info.json nếu có
        info_file = os.path.join(item_path, "info.json")
        if os.path.exists(info_file):
            try:
                os.remove(info_file)
                print(f"  🗑️ Đã xóa: info.json")
            except Exception as e:
                print(f"  ⚠️ Lỗi xóa info.json: {e}")

        # 4. Xóa ảnh character trong thư mục sản phẩm
        for f in os.listdir(item_path):
            f_lower = f.lower()
            if f_lower in known_chars or ("nu-" in f_lower) or ("nam-" in f_lower) or ("character" in f_lower):
                char_file_path = os.path.join(item_path, f)
                try:
                    os.remove(char_file_path)
                    print(f"  🗑️ Đã xóa ảnh character: {f}")
                except Exception as e:
                    print(f"  ⚠️ Lỗi xóa ảnh character {f}: {e}")

        # 5. Kiểm tra và di chuyển thư mục sang /Volumes/Media/Omni-Video/Product_Assets/
        try:
            os.makedirs(TARGET_MEDIA_DIR, exist_ok=True)
            dest_item_path = os.path.join(TARGET_MEDIA_DIR, item_id)

            if os.path.exists(dest_item_path):
                for f in os.listdir(item_path):
                    src_f = os.path.join(item_path, f)
                    dst_f = os.path.join(dest_item_path, f)
                    if os.path.isfile(src_f):
                        shutil.move(src_f, dst_f)
                    elif os.path.isdir(src_f):
                        dst_dir = os.path.join(dest_item_path, f)
                        os.makedirs(dst_dir, exist_ok=True)
                        for sub_f in os.listdir(src_f):
                            shutil.move(os.path.join(src_f, sub_f), os.path.join(dst_dir, sub_f))
                shutil.rmtree(item_path)
            else:
                shutil.move(item_path, dest_item_path)

            print(f"  🚚 Đã di chuyển thành công: Product_Assets/{item_id} -> {dest_item_path}")
            
            # 6. Tự động cập nhật Google Sheet thành "Đã tạo Video"
            update_google_sheet_video_status(item_id)
            archived_count += 1

        except Exception as e:
            print(f"  ❌ Không thể di chuyển tới ổ đĩa Media ({TARGET_MEDIA_DIR}): {e}")
            print("     (Vui lòng kiểm tra ổ đĩa /Volumes/Media/ đã được kết nối chưa)")

    return archived_count

if __name__ == "__main__":
    print("============================================================")
    print("🚀 OMNI VIDEO - TỰ ĐỘNG QA, NÂNG CẤP PROMPT & LƯU VỀ Ổ MEDIA")
    print("============================================================")
    print(f"📁 Thư mục đích: {TARGET_MEDIA_DIR}\n")
    
    count = archive_completed_folders()
    print("\n============================================================")
    if count > 0:
        print(f"✅ HOÀN TẤT! Đã đánh giá QA, tự nâng cấp Prompt, di chuyển và cập nhật Google Sheet cho {count} sản phẩm.")
    else:
        print("ℹ️ Chưa có thư mục sản phẩm nào chứa file video .mp4 mới.")
    print("============================================================")
