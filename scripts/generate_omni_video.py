#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - Standalone Video Generation using Gemini Omni Flash API
Mô hình: gemini-omni-1.1-flash (Interactions API)
Tự động nạp:
1. File prompt: Product_Assets/<itemId>/<itemId>.txt
2. Ảnh sản phẩm: Product_Assets/<itemId>/<itemId>_*.webp/jpeg/png
3. Ảnh nhân vật: Product_Assets/<itemId>/Nu-*.png hoặc characters/
Xuất video: Product_Assets/<itemId>/<itemId>.mp4 (Tỷ lệ 9:16 dọc)
"""

import os
import sys
import glob
import json
import base64
import time
import select
import getpass
import urllib.request
import urllib.error
import ssl
from typing import Optional, List, Dict, Any, Tuple

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
CHARACTERS_DIR = os.path.join(PROJECT_DIR, "characters")

def load_env():
    """Nạp biến môi trường từ .env."""
    env_file = os.path.join(PROJECT_DIR, ".env")
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

load_env()

def get_omni_api_key() -> str:
    """
    Ưu tiên lấy API key chuyên dụng cho video:
    1. GEMINI_OMNI_API_KEY
    2. GEMINI_VIDEO_API_KEY
    3. GEMINI_API_KEY
    """
    return (
        os.environ.get("GEMINI_OMNI_API_KEY") or
        os.environ.get("GEMINI_VIDEO_API_KEY") or
        os.environ.get("GEMINI_API_KEY") or
        ""
    ).strip()

def verify_security_pin(max_attempts: int = 3) -> bool:
    """
    Kiểm tra mã PIN bảo mật trước khi gọi API trả phí.
    Mã PIN được cấu hình trong .env: OMNI_SECURITY_PIN (hoặc OMNI_PIN)
    """
    if os.environ.get("OMNI_BYPASS_PIN", "").lower() in ["1", "true", "yes"]:
        return True

    expected_pin = (
        os.environ.get("OMNI_SECURITY_PIN") or
        os.environ.get("OMNI_PIN") or
        ""
    ).strip()

    # Nếu không đặt mã PIN trong .env, cho phép tiếp tục
    if not expected_pin:
        return True

    print("\n============================================================")
    print("🔒 BẢO MẬT TÀI KHOẢN TRẢ PHÍ (GEMINI OMNI API)")
    print("============================================================")
    print("⚠️ Bạn đang chuẩn bị gọi API Gemini Omni Flash có tính phí.")

    for attempt in range(1, max_attempts + 1):
        try:
            if sys.stdin.isatty():
                entered_pin = getpass.getpass(f"👉 Vui lòng nhập mã PIN bảo mật (Lần {attempt}/{max_attempts}): ").strip()
            else:
                entered_pin = input(f"👉 Vui lòng nhập mã PIN bảo mật (Lần {attempt}/{max_attempts}): ").strip()
        except Exception:
            entered_pin = ""

        if entered_pin == expected_pin:
            print("✅ Xác thực mã PIN thành công! Tiếp tục tiến trình...\n")
            return True
        else:
            print("❌ Mã PIN không chính xác!")

    print("\n🛑 Đã vượt quá số lần nhập PIN cho phép. Hủy bỏ tiến trình để bảo vệ tài khoản.")
    return False

def get_image_mime_type(filepath: str) -> str:
    """Xác định MIME type của file ảnh."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".webp":
        return "image/webp"
    elif ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    elif ext == ".png":
        return "image/png"
    return "image/jpeg"

def find_prompt_file(item_dir: str, item_id: str) -> Optional[str]:
    """Tìm file prompt <itemId>.txt hoặc master_prompt.txt."""
    std_file = os.path.join(item_dir, f"{item_id}.txt")
    if os.path.exists(std_file):
        return std_file
    legacy_file = os.path.join(item_dir, "master_prompt.txt")
    if os.path.exists(legacy_file):
        return legacy_file
    txts = [f for f in glob.glob(os.path.join(item_dir, "*.txt")) if "prompt_backups" not in f]
    return txts[0] if txts else None

def find_product_image(item_dir: str) -> Optional[str]:
    """Tìm ảnh sản phẩm chính trong thư mục."""
    for ext in ["*.webp", "*.jpg", "*.jpeg", "*.png"]:
        for f in glob.glob(os.path.join(item_dir, ext)):
            fname = os.path.basename(f).lower()
            if not fname.startswith("nu-") and not fname.startswith("nam-") and "character" not in fname:
                return f
    return None

def find_character_image(item_dir: str) -> Optional[str]:
    """Tìm ảnh nhân vật trong thư mục sản phẩm hoặc thư mục characters/."""
    for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
        for f in glob.glob(os.path.join(item_dir, ext)):
            fname = os.path.basename(f).lower()
            if fname.startswith("nu-") or fname.startswith("nam-") or "character" in fname:
                return f
    # Fallback kiểm tra trong thư mục characters/
    if os.path.exists(CHARACTERS_DIR):
        for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
            chars = glob.glob(os.path.join(CHARACTERS_DIR, ext))
            if chars:
                return chars[0]
    return None

def build_omni_payload(
    prompt_text: str,
    product_image_path: Optional[str] = None,
    character_image_path: Optional[str] = None,
    aspect_ratio: str = "9:16",
    resolution: str = "720p"
) -> Dict[str, Any]:
    """Tạo payload chuẩn theo định dạng Google Interactions API cho Gemini Omni."""
    inputs: List[Dict[str, Any]] = []

    # Đính kèm ảnh sản phẩm
    if product_image_path and os.path.exists(product_image_path):
        try:
            with open(product_image_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
                mime_type = get_image_mime_type(product_image_path)
                inputs.append({
                    "type": "image",
                    "data": b64_data,
                    "mime_type": mime_type
                })
        except Exception as e:
            print(f"  ⚠️ Không thể đọc ảnh sản phẩm {product_image_path}: {e}")

    # Đính kèm ảnh nhân vật
    if character_image_path and os.path.exists(character_image_path):
        try:
            with open(character_image_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
                mime_type = get_image_mime_type(character_image_path)
                inputs.append({
                    "type": "image",
                    "data": b64_data,
                    "mime_type": mime_type
                })
        except Exception as e:
            print(f"  ⚠️ Không thể đọc ảnh nhân vật {character_image_path}: {e}")

    # Đính kèm prompt text
    inputs.append({
        "type": "text",
        "text": prompt_text
    })

    payload = {
        "model": "gemini-omni-1.1-flash",
        "input": inputs if len(inputs) > 1 else prompt_text,
        "response_format": {
            "type": "video",
            "aspect_ratio": aspect_ratio,
            "resolution": resolution
        }
    }
    return payload

def extract_video_data_from_response(response_data: Dict[str, Any]) -> Optional[bytes]:
    """Trích xuất dữ liệu binary MP4 từ phản hồi API của Gemini Omni."""
    # 1. Kiểm tra trường tiện ích output_video
    if "output_video" in response_data and isinstance(response_data["output_video"], dict):
        video_b64 = response_data["output_video"].get("data")
        if video_b64:
            return base64.b64decode(video_b64)

    # 2. Kiểm tra trong mảng steps (REST raw format)
    steps = response_data.get("steps", [])
    for step in steps:
        if isinstance(step, dict) and step.get("type") == "model_output":
            contents = step.get("content", [])
            for c in contents:
                if isinstance(c, dict) and c.get("type") == "video":
                    video_b64 = c.get("data")
                    if video_b64:
                        return base64.b64decode(video_b64)

    return None

def call_omni_video_api(payload: Dict[str, Any], api_key: str, max_retries: int = 2) -> Optional[bytes]:
    """Gửi yêu cầu tạo video tới Gemini Omni Flash API qua REST Interactions Endpoint."""
    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={api_key}"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={
            "Content-Type": "application/json"
        }
    )

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  ⚡ Đang kết nối Gemini Omni Flash (gemini-omni-1.1-flash) [Lần {attempt}/{max_retries}]...")
            with urllib.request.urlopen(req, context=ctx, timeout=180) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                video_bytes = extract_video_data_from_response(resp_json)
                if video_bytes:
                    return video_bytes
                else:
                    print("  ⚠️ Phản hồi từ Omni không chứa dữ liệu video hợp lệ.")
                    return None
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            print(f"  ❌ Lỗi HTTP {http_err.code} từ Gemini Omni:")
            try:
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message", err_body)
                print(f"     👉 Chi tiết: {err_msg[:250]}")
            except Exception:
                print(f"     👉 {err_body[:250]}")

            if http_err.code in [429, 503] and attempt < max_retries:
                print("  ⏳ Máy chủ bận hoặc giới hạn tạm thời, chờ 5 giây và thử lại...")
                time.sleep(5)
                continue
            break
        except Exception as e:
            print(f"  ❌ Lỗi kết nối API: {e}")
            if attempt < max_retries:
                time.sleep(3)
                continue
            break

    return None

def generate_video_for_item(item_id: str, item_dir: str) -> bool:
    """Sinh video cho một sản phẩm cụ thể từ prompt <itemId>.txt."""
    print(f"\n🎬 ============================================================")
    print(f"🎥 BẮT ĐẦU TẠO VIDEO CHO MÃ SP: {item_id}")
    print(f"📁 Thư mục: {item_dir}")
    print(f"============================================================")

    api_key = get_omni_api_key()
    if not api_key:
        print("❌ Lỗi: Chưa cấu hình GEMINI_OMNI_API_KEY hoặc GEMINI_API_KEY trong file .env!")
        return False

    prompt_path = find_prompt_file(item_dir, item_id)
    if not prompt_path:
        print(f"❌ Không tìm thấy file prompt ({item_id}.txt) trong {item_dir}!")
        return False

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_text = f.read().strip()

    product_img = find_product_image(item_dir)
    char_img = find_character_image(item_dir)

    print(f"📝 File Prompt: {os.path.basename(prompt_path)}")
    print(f"📦 Ảnh sản phẩm: {os.path.basename(product_img) if product_img else 'Không có'}")
    print(f"👤 Ảnh nhân vật: {os.path.basename(char_img) if char_img else 'Không có'}")

    payload = build_omni_payload(
        prompt_text=prompt_text,
        product_image_path=product_img,
        character_image_path=char_img,
        aspect_ratio="9:16",
        resolution="720p"
    )

    start_time = time.time()
    video_bytes = call_omni_video_api(payload, api_key=api_key)
    elapsed = time.time() - start_time

    if video_bytes:
        output_video_path = os.path.join(item_dir, f"{item_id}.mp4")
        with open(output_video_path, "wb") as f:
            f.write(video_bytes)

        size_mb = len(video_bytes) / (1024 * 1024)
        print(f"🎉 TẠO VIDEO THÀNH CÔNG! ({elapsed:.1f}s, Dung lượng: {size_mb:.2f} MB)")
        print(f"💾 File video đã lưu: {output_video_path}")
        return True
    else:
        print(f"❌ Không thể tạo video cho mã {item_id}.")
        return False

def prompt_continue_with_timeout(current: int, total: int, timeout: int = 10) -> bool:
    print(f"\n------------------------------------------------------------")
    print(f"📌 Đã xử lý {current}/{total} sản phẩm.")
    print("Vui lòng chọn:")
    print("  [1] Tiếp tục tạo video cho sản phẩm tiếp theo")
    print("  [2] Thoát ra (MẶC ĐỊNH - TỰ ĐỘNG THOÁT SAU 10 GIÂY)")
    print(f"\n👉 Nhập lựa chọn (1 hoặc 2, tự động chọn [2] sau {timeout}s): ", end="", flush=True)

    try:
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            ans = sys.stdin.readline().strip().lower()
            if ans == "1":
                print("⚡ Đã chọn [1]: Tiếp tục sản phẩm tiếp theo...\n")
                return True
            else:
                print("🛑 Đã chọn [2]: Dừng tiến trình và thoát.\n")
                return False
        else:
            print(f"\n⏱️ Hết {timeout} giây không thao tác. Tự động chọn [2] Thoát ra.\n")
            return False
    except Exception:
        print("\n🛑 Đã dừng tiến trình.")
        return False

def main():
    print("============================================================")
    print("🚀 OMNI VIDEO - CÔNG CỤ SINH VIDEO GEMINI OMNI FLASH (9:16)")
    print("============================================================")

    if not verify_security_pin():
        return

    if not os.path.exists(ASSETS_DIR):
        print(f"❌ Thư mục {ASSETS_DIR} không tồn tại!")
        return

    # Chế độ 1: Tạo video cho mã sản phẩm cụ thể truyền từ tham số dòng lệnh
    if len(sys.argv) > 1:
        target_id = sys.argv[1].strip()
        item_dir = os.path.join(ASSETS_DIR, target_id)
        if os.path.exists(item_dir):
            generate_video_for_item(target_id, item_dir)
        else:
            print(f"❌ Không tìm thấy thư mục của mã SP: {target_id}")
        return

    # Chế độ 2: Quét các sản phẩm có prompt nhưng chưa có video trong Product_Assets/
    all_dirs = [d for d in os.listdir(ASSETS_DIR) if os.path.isdir(os.path.join(ASSETS_DIR, d))]
    if not all_dirs:
        print("ℹ️ Thư mục Product_Assets/ chưa có sản phẩm nào.")
        return

    pending_items = []
    skipped_items = []

    for item_id in sorted(all_dirs):
        item_dir = os.path.join(ASSETS_DIR, item_id)
        mp4_files = glob.glob(os.path.join(item_dir, "*.mp4")) + glob.glob(os.path.join(item_dir, "*.MP4"))
        prompt_file = find_prompt_file(item_dir, item_id)

        if mp4_files:
            skipped_items.append((item_id, "Đã có file video .mp4"))
        elif not prompt_file:
            skipped_items.append((item_id, "Chưa có file prompt .txt"))
        else:
            pending_items.append(item_id)

    if skipped_items:
        print(f"ℹ️ Đã tự động BỎ QUA {len(skipped_items)} sản phẩm:")
        for s_id, reason in skipped_items:
            print(f"   - Mã SP {s_id}: [{reason}]")

    if not pending_items:
        print("\n✨ Không có sản phẩm nào đang chờ tạo video (Tất cả đều đã có video hoặc chưa tạo prompt).")
        return

    print(f"\n🚀 Phát hiện {len(pending_items)} sản phẩm sẵn sàng tạo video: {', '.join(pending_items)}")
    
    count = 0
    total = len(pending_items)
    for idx, item_id in enumerate(pending_items, start=1):
        item_dir = os.path.join(ASSETS_DIR, item_id)
        if generate_video_for_item(item_id, item_dir):
            count += 1

        if idx < total:
            if not prompt_continue_with_timeout(idx, total, timeout=10):
                break

    print(f"\n🎉 HOÀN TẤT! Đã tạo thành công {count}/{total} video.")

if __name__ == "__main__":
    main()
