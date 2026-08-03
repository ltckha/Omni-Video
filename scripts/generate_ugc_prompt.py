#!/usr/bin/env python3
"""
Omni Video - Gemini Multimodal AI UGC Master Prompt Generator (V6 - Flash Models Only)
Chuyên dùng các mô hình Flash tốc độ cao (Gemini 3.5 Flash & 2.5 Flash), loại bỏ hoàn toàn mô hình Pro.
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

# Danh sách mô hình THUẦN FLASH (Chỉ dùng Flash, không dùng Pro)
PREFERRED_MODELS = [
    "gemini-3.5-flash",
    "gemini-2.5-flash"
]

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

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

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

    # Thử các mô hình Flash (Gemini 3.5 Flash -> Gemini 2.5 Flash)
    for model_name in PREFERRED_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"⚡ Đã sinh Master Prompt thành công bằng Mô hình Flash: {model_name}")
                return text
        except Exception as e:
            print(f"🔄 Mô hình {model_name} chưa hỗ trợ hoặc bận ({e}), tự động chuyển sang Flash tiếp theo...")

    print("❌ Lỗi: Tất cả mô hình Gemini Flash API đều không phản hồi.")
    return None

def update_google_sheet_status(item_id):
    if not WEBHOOK_URL:
        return

    products_map = fetch_products_from_google_sheet()
    if item_id in products_map:
        current_status = products_map[item_id].get("status", "")
        if current_status == "Đã tạo Video":
            print(f"ℹ️ Mã {item_id} đang ở trạng thái 'Đã tạo Video', giữ nguyên trên Google Sheet.")
            return

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

    selected_char = select_character_for_product(raw_product_name)
    print(f"👤 Nhân vật được chọn phù hợp: {selected_char}")

    system_directive = f"""You are an expert AI Video Director and Marketing Copywriter specializing in 10-second UGC (User-Generated Content) Review videos for Gemini Omni.

Look closely at the attached main product image AND analyze the full Shopee title: "{raw_product_name}".

CRITICAL VOICEOVER-FIRST STORYTELLING RULES:
1. VOICEOVER IS THE MASTER ANCHOR:
   - First, create an extremely relatable, emotional, natural 0-3s Vietnamese hook (e.g., "Chân mỏi nhừ sau ngày dài đi giày nặng nề?").
2. ENGLISH VISUAL MUST 100% DRAMATIZE THE VOICEOVER:
   - The English Visual description MUST EXACTLY match every detail in the Vietnamese voiceover!
   - Example: If the Voiceover says "đi giày nặng nề" (wearing heavy shoes), the 0-3s Visual MUST show the character wearing and taking off heavy, stiff work shoes/sneakers (NOT sandals!). Then at 3-10s, slipping into the comfortable main product slides!
3. PERFECT OBJECT CONSISTENCY:
   - Whatever item/pain point is mentioned in Vietnamese MUST be the EXACT item depicted in the English Visual scene.
4. NO SHOPEE SPAM KEYWORDS:
   - DO NOT repeat long Shopee model codes or SEO keywords in Vietnamese voiceovers. Keep it conversational, viral, and natural.
5. SECONDARY PROP MUST MATCH THE CHARACTER'S IDENTITY:
   - Look at the attached character reference image carefully (gender, age, style, body type).
   - The secondary prop / pain-point item MUST be visually and contextually consistent with that character.
   - If the character is female, describe the prop using realistic FEMALE-coded items (e.g., "tight high-heeled ankle boots", "narrow pointed flats", "worn-out fashion sneakers") — NEVER generic unisex/male-coded terms like "work boots", "chunky leather sneakers", or "formal boots" unless the character is clearly male.
   - If the character is male, use male-coded items instead. Mismatched gender/style between character and prop is a critical failure.
6. AVOID COMPLEX FINE-MOTOR HAND ACTIONS:
   - AI video generation struggles with intricate hand-object interactions (unlacing, tying, buttoning, zipping).
   - Describe simple, robust actions instead: "kicks off her shoes", "slips her feet out", "steps out of them" — NOT "struggling to unlace" or multi-step manual actions.
7. DIVERSE & CONTEXTUALLY FITTING ENVIRONMENT SELECTION:
   - DO NOT default to an indoor living room unless the product is strictly for indoor home use.
   - Dynamically choose vibrant, photorealistic indoor or outdoor environments matching the product's natural lifestyle context:
     * Outdoor/Casual sandals/footwear & fashion: Sunny beach boardwalk, resort poolside, outdoor garden cafe, bustling city street sidewalk, sunlit park pathway.
     * Sports/Activewear: Green park running trail, urban outdoor plaza, modern gym, athletic field.
     * Work/Office fashion: Modern office hallway, stylish urban coffee shop, city street backdrop.
     * Home/Indoor items: Sunlit apartment balcony, modern kitchen, cozy entryway/living room.
8. AI VIDEO MOTION SAFETY TIERS & CINEMATIC CUT STRATEGY:
   - GOLDEN RULE: The more AI morphs an object's geometry during motion, the higher the artifact/distortion risk. NEVER force AI to render multi-step continuous physical transformations in a single shot.
   - PRIORITIZE SAFE ACTIONS (🟢):
     * 🟢 SAFE (PRIORITY): Standing/sitting still, gentle smile, looking at product, touching product lightly, slow natural walking, slow body turn, extending foot forward, standing up slowly, camera pan/tilt/tracking, or close-up of feet ALREADY wearing the product.
     * 🟡 MEDIUM RISK (Keep simple): Gently slipping feet into slides, picking up slipper, taking off shoes, sitting down/standing up slowly, holding product and turning.
     * 🔴 HIGH FAILURE RISK (STRICTLY AVOID): Kicking off shoes violently, running, jumping, fast spinning, throwing/catching objects, taking off AND putting on shoes in a single continuous motion, complex multi-hand interactions, aggressive 360 camera spins.
   - CINEMATIC CUT TECHNIQUE (DÙNG CUT ĐỂ CHE KHÓ):
     * Instead of describing 4-5 continuous physical actions ("taking off heels, bending down, putting on slides, standing up"), use clean cinematic cuts or focus on clean state transitions.
     * Example: "0-3s: Character sitting with a tired expression looking down at stiff shoes. 3-10s: Cut to a close-up of her feet ALREADY wearing the soft NESTY clogs. She takes two slow, natural, comfortable steps forward."

STRICTLY FOLLOW THIS MASTER PROMPT STRUCTURE:

---
[ATTACHED ASSETS & CREATIVE DIRECTIVES]:
- Main Product: Attached product image ({main_product_img_name})
- Secondary Product / Prop: AI Creative Freedom: [Describe the EXACT specific pain point item that matches the Vietnamese hook AND matches the character's gender/style, e.g., for a female character: "tight high-heeled ankle boots" — NOT generic "work shoes"]
- Character: Attached image characters/{selected_char} (Friendly reviewer matching target audience)
- Environment: AI Creative Freedom: [Select a vibrant, highly fitting indoor or outdoor environment based on product usage scenario — e.g., sunny beach resort boardwalk, outdoor garden cafe, bustling city sidewalk, green park trail, or modern sunlit space]

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
- Visual: [Write a vivid cinematic visual description in English showing character acting out the exact problem stated in the Vietnamese voiceover]
- Subtitle/Voiceover (Vietnamese): "[Write a short, catchy 0-3s opening hook in conversational Vietnamese - e.g., 'Chân mỏi nhừ sau ngày dài đi giày nặng nề?']"

3-10s (Solution & Product Demo):
- Visual: [Write a vivid cinematic visual description in English showing character taking off the problem item and stepping/using main product with instant relief transformation]
- Subtitle/Voiceover (Vietnamese): "[Write a high-impact, emotional benefit statement in conversational Vietnamese for 3-10s - e.g., 'Đổi sang đôi dép đúc siêu nhẹ này đi, êm như bước trên mây!']"

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

        # Tự động copy ảnh nhân vật đã chọn vào thư mục sản phẩm
        if selected_char:
            char_src_path = os.path.join(CHARACTERS_DIR, selected_char)
            if os.path.exists(char_src_path):
                char_dest_path = os.path.join(item_dir, selected_char)
                try:
                    import shutil
                    shutil.copy2(char_src_path, char_dest_path)
                    print(f"📸 Đã copy ảnh nhân vật {selected_char} vào {item_dir}/")
                except Exception as e:
                    print(f"⚠️ Không thể copy ảnh nhân vật: {e}")

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
