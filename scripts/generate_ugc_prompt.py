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

def select_character_for_product(product_name):
    """
    Tự động phân tích tên sản phẩm và chọn nhân vật phù hợp theo quy tắc:
    - Nam-25t: Nhân vật Nam 25 tuổi
    - Nu-25t: Nhân vật Nữ 25 tuổi
    - Nu-23t: Nhân vật Nữ 23 tuổi
    """
    chars = get_available_characters()
    if not chars:
        return "Friendly Reviewer"

    p_lower = (product_name or "").lower()

    # Nếu tên sản phẩm có chứa từ khóa đồ Nam -> Chọn nhân vật Nam
    male_keywords = ["nam", "men", "man", "đàn ông", "giày nam", "dép nam", "áo nam", "quần nam"]
    is_male_product = any(kw in p_lower for kw in male_keywords) and not any(kw in p_lower for kw in ["nữ", "women", "girl"])

    if is_male_product:
        for c in chars:
            if "nam" in c.lower():
                return c

    # Nếu là đồ Nữ hoặc sản phẩm chung -> Ưu tiên chọn nhân vật Nữ (Nu-25t hoặc Nu-23t)
    for c in chars:
        if "nu-25t" in c.lower() or "nu_25t" in c.lower():
            return c
    for c in chars:
        if "nu" in c.lower():
            return c

    return chars[0]

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

    # Nạp các bài học kinh nghiệm từ Hồ sơ Hệ thống chung (Global System Memory)
    global_rules_file = os.path.join(PROJECT_DIR, "scripts", "global_learned_rules.json")
    learned_constraints_text = ""
    if os.path.exists(global_rules_file):
        try:
            with open(global_rules_file, "r", encoding="utf-8") as f:
                learned_rules = json.load(f)
                if learned_rules:
                    learned_constraints_text = "\nSYSTEM LEARNED NEGATIVE CONSTRAINTS (AUTONOMOUS QA FEEDBACK):\n" + "\n".join([f"- AVOID: {r}" for r in learned_rules]) + "\n"
        except Exception:
            pass

    system_directive = f"""You are an expert AI Video Director and Marketing Copywriter specializing in 10-second UGC (User-Generated Content) Review videos for Gemini Omni.

Look closely at the attached main product image AND analyze the full Shopee title: "{raw_product_name}".

CRITICAL VOICEOVER-FIRST STORYTELLING RULES:
1. DYNAMIC STORYTELLING MODE SELECTION (FLEXIBLE):
   Dynamically analyze the product title and image to select ONE of the following two high-converting UGC storytelling structures:
   - **MODE A: Hook & Problem Transformation (0-3s Hook + 3-10s Solution)**: Best for products solving an explicit pain point (e.g. stiff uncomfortable heels, tired feet, shoe cleaning).
   - **MODE B: Seamless Single-Shot Narrative (0-10s Continuous Flow)**: Best for lifestyle, fashion, or aesthetic products. Describes a smooth, fluid 0-10s continuous storytelling experience without rigid Hook/Problem division.

2. VOICEOVER & VISUAL DRAMATIZATION:
   - The English Visual description MUST 100% DRAMATIZE and align with every detail mentioned in the Vietnamese voiceover!
   - Keep Vietnamese voiceovers conversational, viral, emotional, and natural.

3. PERFECT OBJECT CONSISTENCY:
   - Whatever item/pain point is mentioned in Vietnamese MUST be the EXACT item depicted in the English Visual scene.

4. NO SHOPEE SPAM KEYWORDS:
   - DO NOT repeat long Shopee model codes or SEO keywords in Vietnamese voiceovers.

5. SECONDARY PROP MUST MATCH THE CHARACTER'S IDENTITY:
   - Look at the attached character reference image carefully (gender, age, style, body type).
   - If a secondary prop/pain point is used, describe it matching the character's gender/style (e.g., female character gets female-coded footwear like heels/flats).

6. AVOID COMPLEX FINE-MOTOR HAND ACTIONS:
   - AI video generation struggles with intricate hand-object interactions (unlacing, tying, buttoning).
   - Describe simple, robust actions instead: "kicks off her shoes", "slips her feet out", "steps forward" — NOT multi-step manual actions.

7. DIVERSE OUTFIT & ENVIRONMENT SELECTION (DO NOT LOCK OUTFIT TO IMAGE):
   - **CHARACTER FACE & IDENTITY LOCK**: Lock 100% of the character's facial features, age, skin tone, and hair from `characters/{selected_char}`.
   - **OUTFIT CREATIVE FREEDOM**: DO NOT lock her outfit/clothing to the picture! Dynamically design a stylish, diverse, modern outfit matching the product scenario (e.g., trendy summer casual wear, chic resort outfit, active athletic park wear, modern city street fashion, cozy loungewear).
   - **ENVIRONMENT DIVERSITY**: Dynamically choose vibrant, photorealistic indoor or outdoor environments matching the product's natural lifestyle context.

8. AI VIDEO MOTION SAFETY TIERS & CINEMATIC CUT STRATEGY:
   - GOLDEN RULE: The more AI morphs an object's geometry during motion, the higher the artifact/distortion risk. NEVER force AI to render multi-step continuous physical transformations in a single shot.
   - Use clean CINEMATIC CUTS between different scenes/shots to ensure safe visual transitions.

9. ABSOLUTELY NO SHOP LOGOS, WATERMARKS, OR ON-SCREEN GRAPHIC OVERLAYS:
   - STRICTLY IGNORE any seller shop logos, text watermarks, discount badges, store icons, or promotional overlays present on the input Shopee image.
   - Keep the video 100% photorealistic UGC footage with ZERO graphic logo overlays.
{learned_constraints_text}
STRICTLY FOLLOW THIS MASTER PROMPT STRUCTURE:

---
[ATTACHED ASSETS & CREATIVE DIRECTIVES]:
- Main Product: Attached product image ({main_product_img_name})
- Secondary Product / Prop: AI Creative Freedom: [Describe pain-point prop if using Mode A, or lifestyle prop if using Mode B]
- Character: Attached image characters/{selected_char} (Maintain facial identity & age, but generate stylish diverse outfit suitable for the scenario)
- Environment: AI Creative Freedom: [Select a vibrant, highly fitting indoor or outdoor environment — e.g., sunny beach resort boardwalk, outdoor garden cafe, bustling city sidewalk, green park trail]

Task: Generate a 10-second high-converting UGC review video seamlessly combining the main product, secondary prop, character, and environment.

FIXED CONSTRAINTS (STRICT):
- Video Duration: Exactly 10 seconds.
- Aspect Ratio: 9:16 Vertical format.
- Visual Consistency: Maintain 100% exact visual appearance for attached main product, and maintain character's FACIAL IDENTITY (while allowing creative outfit/clothing variation).
- Clean Footage: No video watermark logos, no shop logo overlays, no text artifacts.

CREATIVE FREEDOM FOR OMNI:
- For missing/unattached assets: Full creative freedom to generate realistic, contextually appropriate character outfit, secondary props, or environment.
- Motion & Audio: High freedom for audio lip-sync, realistic facial expressions, natural hand gestures, dynamic camera movement, and warm natural lighting.

SCENE BREAKDOWN (10 SECONDS):
[You can choose EITHER Structure A (Hook & Solution) OR Structure B (Seamless Narrative):]

[IF USING STRUCTURE A (Hook & Solution):]
0-3s (Hook & Problem):
- Visual: [Vivid visual description in English showing character acting out the problem/hook]
- Subtitle/Voiceover (Vietnamese): "[Short, catchy 0-3s opening hook in conversational Vietnamese]"

3-10s (Solution & Product Demo):
- Visual: [Vivid visual description in English showing product transformation/use]
- Subtitle/Voiceover (Vietnamese): "[High-impact benefit statement in conversational Vietnamese]"

[IF USING STRUCTURE B (Seamless Narrative):]
0-10s (Seamless Narrative Showcase):
- Visual: [Vivid continuous visual description in English describing a smooth 0-10s storytelling showcase/experience of the character using/wearing the main product]
- Subtitle/Voiceover (Vietnamese): "[Fluid, natural 0-10s continuous review voiceover in conversational Vietnamese]"

STYLE GUIDELINES:
- Photorealistic UGC review style, natural handheld camera feel, fluid motion, 60fps, realistic audio lip-sync.
- ABSOLUTELY NO shop logos, video watermark icons, corner brand tags, or text overlays.
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
