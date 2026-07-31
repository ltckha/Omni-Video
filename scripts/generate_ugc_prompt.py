#!/usr/bin/env python3
"""
Omni Video - Gemini AI UGC Master Prompt Generator
Tự động quét sản phẩm trong Product_Assets/<itemId>/, dùng Gemini AI sinh Master Prompt 10s
tuân thủ 100% quy chuẩn omni-ugc-creator.md và lưu file master_prompt.txt.
"""

import sys
import os
import glob
import urllib.request
import json
import ssl
import re

# Đảm bảo nạp môi trường từ ~/.zshrc hoặc ~/.zshenv nếu chạy độc lập
def load_env_if_needed():
    if "GEMINI_API_KEY" not in os.environ:
        for env_file in [os.path.expanduser("~/.zshrc"), os.path.expanduser("~/.zshenv"), os.path.expanduser("~/.bash_profile")]:
            if os.path.exists(env_file):
                try:
                    with open(env_file, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if "GEMINI_API_KEY" in line and "=" in line and not line.strip().startswith("#"):
                                key_val = line.split("=", 1)[1].strip().strip('"').strip("'")
                                os.environ["GEMINI_API_KEY"] = key_val
                                break
                except Exception:
                    pass

load_env_if_needed()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
CHARACTERS_DIR = os.path.join(PROJECT_DIR, "characters")
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyxBWA7eJjmi0vn9etRyainI3rrHbAQAN_Uc7tI14sMyyJLftBSnQLJjm5o0WTamS20Rg/exec"

def get_available_characters():
    chars = []
    if os.path.exists(CHARACTERS_DIR):
        for ext in ["*.png", "*.jpg", "*.webp", "*.jpeg"]:
            for filepath in glob.glob(os.path.join(CHARACTERS_DIR, ext)):
                chars.append(os.path.basename(filepath))
    return chars

def call_gemini_api(prompt_text):
    if not GEMINI_API_KEY:
        print("❌ Lỗi: Không tìm thấy GEMINI_API_KEY trong biến môi trường!")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt_text}]
            }
        ],
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
    print(f"\n🎬 Đang xử lý sinh Master Prompt cho Mã SP: {item_id}...")
    
    # Tìm tất cả ảnh sản phẩm trong thư mục <item_id>/
    images = []
    for ext in ["*.webp", "*.jpg", "*.png", "*.jpeg"]:
        images.extend(glob.glob(os.path.join(item_dir, ext)))

    main_product_img = os.path.basename(images[0]) if images else "Main Product Image"
    characters = get_available_characters()
    selected_char = characters[0] if characters else "Friendly Reviewer"

    # Tạo System Prompt gửi cho Gemini AI
    system_directive = f"""You are an elite AI Video Director and Marketing Copywriter specializing in 10-second UGC (User-Generated Content) Review videos for Gemini Omni.

Your task is to analyze the product with Item ID "{item_id}" (Image: {main_product_img}) and generate a high-converting Master Prompt strictly adhering to the following structure:

---
[ATTACHED ASSETS & CREATIVE DIRECTIVES]:
- Main Product: Attached product image ({main_product_img})
- Secondary Product / Prop: AI Creative Freedom: [Identify the most impactful pain point/prop related to this product, e.g., worn-out shoe, stained leather, dull skin]
- Character: Attached image characters/{selected_char} (Friendly reviewer matching target audience)
- Environment: AI Creative Freedom: [Contextually appropriate environment, e.g., bright home, shoe workshop, studio]

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
- Visual: [Write a vivid cinematic visual description in English showing the character interacting with the pain point/problem item]
- Subtitle/Voiceover (Vietnamese): "[Write a catchy, curiosity-inducing opening hook in Vietnamese for the 0-3s mark]"

3-10s (Solution & Product Demo):
- Visual: [Write a vivid cinematic visual description in English showing the character applying/using the main product with instant result/transformation]
- Subtitle/Voiceover (Vietnamese): "[Write a clear, high-impact core benefit and value statement in Vietnamese for the 3-10s mark]"

STYLE GUIDELINES:
- Photorealistic UGC review style, natural handheld camera feel, fluid motion, 60fps, realistic audio lip-sync.
---

Generate ONLY the final Master Prompt text inside a clean markdown block. Keep Vietnamese voiceovers natural and engaging. Do not include meta explanations."""

    generated_text = call_gemini_api(system_directive)
    if generated_text:
        # Làm sạch bớt markdown code block thừa nếu có
        clean_text = generated_text.replace("```markdown", "").replace("```text", "").replace("```", "").strip()
        
        # Ghi file master_prompt.txt
        output_file = os.path.join(item_dir, "master_prompt.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(clean_text)
            
        print(f"✅ Đã lưu Master Prompt thành công tại: {output_file}")
        print("\n--- NỘI DUNG MASTER PROMPT ---")
        print(clean_text[:400] + "...\n------------------------------")
        
        # Cập nhật Google Sheet
        update_google_sheet_status(item_id)
        return True
    return False

def main():
    if not os.path.exists(ASSETS_DIR):
        print(f"❌ Thư mục {ASSETS_DIR} không tồn tại!")
        return

    # Nếu truyền mã item_id cụ thể từ tham số dòng lệnh
    if len(sys.argv) > 1:
        target_id = sys.argv[1].strip()
        item_dir = os.path.join(ASSETS_DIR, target_id)
        if os.path.exists(item_dir):
            generate_prompt_for_item(target_id, item_dir)
        else:
            print(f"❌ Không tìm thấy thư mục của mã SP: {target_id}")
    else:
        # Quét toàn bộ thư mục trong Product_Assets/
        item_dirs = [d for d in os.listdir(ASSETS_DIR) if os.path.isdir(os.path.join(ASSETS_DIR, d))]
        if not item_dirs:
            print("ℹ️ Thư mục Product_Assets/ chưa có sản phẩm nào.")
            return

        print(f"🚀 Phát hiện {len(item_dirs)} thư mục sản phẩm. Bắt đầu sinh Master Prompt hàng loạt...")
        count = 0
        for item_id in item_dirs:
            item_dir = os.path.join(ASSETS_DIR, item_id)
            if generate_prompt_for_item(item_id, item_dir):
                count += 1
        print(f"\n🎉 Hoàn tất! Đã sinh {count} Master Prompt thành công!")

if __name__ == "__main__":
    main()
