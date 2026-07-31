#!/usr/bin/env python3
"""
Omni Video - Gemini Multimodal AI UGC Master Prompt Generator (V2 - Conversational UGC Copywriting)
Tự động tinh lọc Tên sản phẩm Shopee dài thành tên ngắn gọn, loại bỏ từ khóa rác trong lời thoại
và tạo Master Prompt mượt mà 100% theo quy chuẩn omni-ugc-creator.md.
"""

import sys
import os
import glob
import urllib.request
import json
import ssl
import base64
import mimetypes

def load_env_if_needed():
    if "GEMINI_API_KEY" not in os.environ or not os.environ["GEMINI_API_KEY"]:
        for env_file in [os.path.expanduser("~/.zshrc"), os.path.expanduser("~/.zshenv"), os.path.expanduser("~/.bash_profile")]:
            if os.path.exists(env_file):
                try:
                    with open(env_file, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if "GEMINI_API_KEY" in line and "=" in line and not line.strip().startswith("#"):
                                val = line.split("=", 1)[1].strip()
                                val = val.replace("export", "").strip()
                                val = val.strip('"').strip("'")
                                if val:
                                    os.environ["GEMINI_API_KEY"] = val
                                    break
                except Exception:
                    pass

load_env_if_needed()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
CHARACTERS_DIR = os.path.join(PROJECT_DIR, "characters")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyxBWA7eJjmi0vn9etRyainI3rrHbAQAN_Uc7tI14sMyyJLftBSnQLJjm5o0WTamS20Rg/exec"

PRODUCTS_CACHE = None

def fetch_products_from_google_sheet():
    global PRODUCTS_CACHE
    if PRODUCTS_CACHE is not None:
        return PRODUCTS_CACHE

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    payload = {"action": "get_all_products"}
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                PRODUCTS_CACHE = data.get("products", {})
                print(f"📊 Đã tải thành công dữ liệu {len(PRODUCTS_CACHE)} sản phẩm từ Google Sheet!")
                return PRODUCTS_CACHE
    except Exception as e:
        print("⚠️ Không thể kết nối Google Sheet Webhook:", e)

    PRODUCTS_CACHE = {}
    return PRODUCTS_CACHE

def lookup_product_name(item_id, item_dir):
    products_map = fetch_products_from_google_sheet()
    if item_id in products_map:
        title = products_map[item_id].get("productName", "")
        if title and title != "Sản phẩm mới":
            return title

    info_path = os.path.join(item_dir, "info.json")
    if os.path.exists(info_path):
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                info = json.load(f)
                if info.get("productName"):
                    return info["productName"]
        except Exception:
            pass

    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv")) + glob.glob(os.path.join(PROJECT_DIR, "*.csv"))
    for csv_file in csv_files:
        try:
            with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if item_id in line:
                        parts = line.split(",")
                        if len(parts) > 1:
                            t = parts[1].strip().strip('"')
                            if t and not t.startswith("Mã"):
                                return t
        except Exception:
            pass

    return "Sản phẩm Shopee"

def get_available_characters():
    chars = []
    if os.path.exists(CHARACTERS_DIR):
        for ext in ["*.png", "*.jpg", "*.webp", "*.jpeg"]:
            for filepath in glob.glob(os.path.join(CHARACTERS_DIR, ext)):
                chars.append(os.path.basename(filepath))
    return chars

def get_image_mime_type(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".webp":
        return "image/webp"
    elif ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    elif ext == ".png":
        return "image/png"
    return "image/jpeg"

def call_gemini_multimodal_api(prompt_text, image_filepath=None):
    if not GEMINI_API_KEY:
        print("❌ Lỗi: Không tìm thấy GEMINI_API_KEY trong biến môi trường!")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    parts = []
    
    if image_filepath and os.path.exists(image_filepath):
        try:
            with open(image_filepath, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
                mime_type = get_image_mime_type(image_filepath)
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": img_b64
                    }
                })
                print(f"📸 Đã đính kèm ảnh Multimodal ({mime_type}) vào Gemini AI...")
        except Exception as e:
            print("⚠️ Không thể đọc file ảnh:", e)

    parts.append({"text": prompt_text})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95
        }
    }

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("❌ Lỗi gọi Gemini API:", e)
        return None

def update_google_sheet_status(item_id):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    payload = {
        "action": "update_status",
        "itemId": item_id,
        "status": "Đã tạo Prompt"
    }

    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "text/plain;charset=utf-8"}
    )

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"📊 Đã cập nhật trạng thái Google Sheet cho mã {item_id}:", data.get("message", "Thành công"))
    except Exception as e:
        print(f"⚠️ Lỗi cập nhật Sheet cho mã {item_id}:", e)

def generate_prompt_for_item(item_id, item_dir):
    print(f"\n🎬 Đang xử lý sinh Master Prompt chuẩn cho Mã SP: {item_id}...")
    
    images = []
    for ext in ["*.webp", "*.jpg", "*.png", "*.jpeg"]:
        images.extend(glob.glob(os.path.join(item_dir, ext)))

    image_path = images[0] if images else None
    main_product_img_name = os.path.basename(image_path) if image_path else "Product Image"
    
    raw_product_name = lookup_product_name(item_id, item_dir)
    print(f"📦 Tên sản phẩm Shopee: \"{raw_product_name}\"")

    characters = get_available_characters()
    selected_char = characters[0] if characters else "Friendly Reviewer"

    system_directive = f"""You are an expert AI Video Director and Marketing Copywriter specializing in 10-second UGC (User-Generated Content) Review videos for Gemini Omni.

Look closely at the attached main product image AND analyze the full Shopee title: "{raw_product_name}".

CRITICAL UGC COPYWRITING & PROMPT RULES:
1. CORE PRODUCT CONCEPT: First, simplify the long Shopee title into a natural 2-4 word product category (e.g. "Dép sục siêu nhẹ", "Gôm tẩy da lộn", "Xịt bọt vệ sinh giày").
2. CONVERSATIONAL VIETNAMESE VOICEOVER (STRICT):
   - DO NOT EVER repeat long Shopee listing keywords, technical specs, or model numbers (like KO1, EVA, 5cm, extraParams, etc.) in the Vietnamese subtitles/voiceovers.
   - Write natural, emotional, everyday spoken Vietnamese used by real viral TikTok/Reels reviewers (e.g., "Đi mưa mà mang đôi sục này thì êm dã man!", "Chân mỏi nhức cả ngày, phải thử ngay đôi này!").
3. ANCHOR PRODUCT TO ATTACHED IMAGE:
   - In [ATTACHED ASSETS], reference the main product as "Attached product image ({main_product_img_name})" so Omni visually maintains 100% appearance from the image file.

STRICTLY FOLLOW THIS MASTER PROMPT STRUCTURE:

---
[ATTACHED ASSETS & CREATIVE DIRECTIVES]:
- Main Product: Attached product image ({main_product_img_name})
- Secondary Product / Prop: AI Creative Freedom: [Describe the EXACT specific pain point or dirty/damaged item interacting with this product]
- Character: Attached image characters/{selected_char} (Friendly reviewer matching target audience)
- Environment: AI Creative Freedom: [Contextually appropriate realistic environment]

Task: Generate a 10-second high-converting UGC review video seamlessly combining the main product, secondary prop, character, and environment.

FIXED CONSTRAINTS (STRICT):
- Video Duration: Exactly 10 seconds.
- Aspect Ratio: 9:16 Vertical format.
- Visual Consistency: Maintain 100% exact visual appearance for attached main product and character images.

CREATIVE FREEDOM FOR OMNI:
- For missing/unattached assets: Full creative freedom to generate realistic, contextually appropriate character, secondary props, or environment.
- Motion & Audio: High freedom for audio lip-sync, realistic facial expressions, natural hand gestures, dynamic camera movement, and warm natural lighting.

SCENE BREAKDOWN (10 SECONDS):
0-3s (Hook & Problem):
- Visual: [Write a vivid cinematic visual description in English showing character struggling with the problem]
- Subtitle/Voiceover (Vietnamese): "[Write a short, catchy, natural 0-3s opening hook in conversational Vietnamese - NO long Shopee titles or model codes!]"

3-10s (Solution & Product Demo):
- Visual: [Write a vivid cinematic visual description in English showing character applying/using main product with instant transformation result]
- Subtitle/Voiceover (Vietnamese): "[Write a high-impact, emotional benefit statement in conversational Vietnamese for 3-10s - NO long Shopee titles or model codes!]"

STYLE GUIDELINES:
- Photorealistic UGC review style, natural handheld camera feel, fluid motion, 60fps, realistic audio lip-sync.
---

Generate ONLY the final Master Prompt text inside a clean markdown block. Keep Vietnamese voiceovers natural and engaging. Do not include meta explanations."""

    generated_text = call_gemini_multimodal_api(system_directive, image_path)
    if generated_text:
        clean_text = generated_text.replace("```markdown", "").replace("```text", "").replace("```", "").strip()
        
        output_file = os.path.join(item_dir, "master_prompt.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(clean_text)
            
        print(f"✅ Đã lưu Master Prompt tinh lọc thành công tại: {output_file}")
        print("\n--- NỘI DUNG MASTER PROMPT TINH LỌC ---")
        print(clean_text[:550] + "...\n---------------------------------------")
        
        update_google_sheet_status(item_id)
        return True
    return False

def main():
    if not os.path.exists(ASSETS_DIR):
        print(f"❌ Thư mục {ASSETS_DIR} không tồn tại!")
        return

    if len(sys.argv) > 1:
        target_id = sys.argv[1].strip()
        item_dir = os.path.join(ASSETS_DIR, target_id)
        if os.path.exists(item_dir):
            generate_prompt_for_item(target_id, item_dir)
        else:
            print(f"❌ Không tìm thấy thư mục của mã SP: {target_id}")
    else:
        item_dirs = [d for d in os.listdir(ASSETS_DIR) if os.path.isdir(os.path.join(ASSETS_DIR, d))]
        if not item_dirs:
            print("ℹ️ Thư mục Product_Assets/ chưa có sản phẩm nào.")
            return

        print(f"🚀 Phát hiện {len(item_dirs)} thư mục sản phẩm. Bắt đầu sinh Master Prompt Multimodal...")
        count = 0
        for item_id in item_dirs:
            item_dir = os.path.join(ASSETS_DIR, item_id)
            if generate_prompt_for_item(item_id, item_dir):
                count += 1
        print(f"\n🎉 Hoàn tất! Đã sinh {count} Master Prompt chuẩn thành công!")

if __name__ == "__main__":
    main()
