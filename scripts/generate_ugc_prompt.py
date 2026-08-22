#!/usr/bin/env python3
"""
Omni Video - Gemini Multimodal AI UGC Master Prompt Generator (V6 - Direct Google Sheets API v4)
Chuyên dùng các mô hình Flash tốc độ cao, giao tiếp trực tiếp qua Direct API v4.
"""

import sys
import os
import glob
import urllib.request
import json
import ssl
import base64
import time
import select
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
WEBHOOK_URL = os.environ.get("OMNI_GAS_WEBHOOK_URL", "https://script.google.com/macros/s/AKfycbxFF8hp9WpoUROqikUQGSqyxMxhCxcQ--3nwrNxYBNa4dD7M5C58PQqSo_EBy6hX4ao/exec")

# Danh sách mô hình Flash ưu tiên
PREFERRED_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash"
]

def lookup_product_name(item_id, item_dir):
    """Ưu tiên đọc tên sản phẩm trực tiếp từ info.json nội bộ trên máy (Siêu tốc)."""
    info_path = os.path.join(item_dir, "info.json")
    if os.path.exists(info_path):
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                info = json.load(f)
                name = info.get("productName") or info.get("title") or info.get("name")
                if name and name != "Sản phẩm mới":
                    return name
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
    chars = get_available_characters()
    if not chars:
        return "Friendly Reviewer"

    p_lower = (product_name or "").lower()

    male_keywords = ["nam", "men", "man", "đàn ông", "giày nam", "dép nam", "áo nam", "quần nam"]
    is_male_product = any(kw in p_lower for kw in male_keywords) and not any(kw in p_lower for kw in ["nữ", "women", "girl"])

    if is_male_product:
        for c in chars:
            if "nam" in c.lower():
                return c

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

    for model_name in PREFERRED_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"⚡ Đã sinh Master Prompt thành công bằng Mô hình Flash: {model_name}")
                    return text
            except urllib.error.HTTPError as http_err:
                err_msg = http_err.read().decode("utf-8", errors="ignore")
                print(f"🔄 Mô hình {model_name} trả về lỗi ({http_err.code}): {err_msg[:180]}")
                if http_err.code in [503, 429] and attempt == 0:
                    print("  ⏳ Máy chủ bận, chờ 2 giây và thử lại...")
                    time.sleep(2)
                    continue
                break
            except Exception as e:
                print(f"🔄 Mô hình {model_name} chưa hỗ trợ hoặc bận ({e}), tự động chuyển sang Flash tiếp theo...")
                break

    print("❌ Lỗi: Tất cả mô hình Gemini Flash API đều không phản hồi.")
    return None

def update_google_sheet_status(item_id):
    try:
        from sheet_sync import update_status_by_item_id
        update_status_by_item_id(item_id, "Đã tạo Prompt")
    except Exception as e:
        print(f"⚠️ Lỗi cập nhật Sheet cho mã {item_id}:", e)

def load_central_prompt_rules():
    """Tự động nạp toàn bộ danh sách quy tắc và điều cấm kỵ từ config/prompt_rules.json."""
    rules_path = os.path.join(PROJECT_DIR, "config", "prompt_rules.json")
    if not os.path.exists(rules_path):
        return ""
    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        lines = ["\n[MANDATORY ZERO-TOLERANCE COMPLIANCE & NEGATIVE CONSTRAINTS (STRICT)]:\nYOU MUST STRICTLY OBEY EVERY SINGLE RULE BELOW WITHOUT EXCEPTION:"]
        for category, items in data.items():
            lines.append(f"\n>>> {category.upper()}:")
            if isinstance(items, list):
                for item in items:
                    lines.append(f"  * {item}")
            elif isinstance(items, dict):
                for k, v in items.items():
                    lines.append(f"  * {k}: {v}")
        return "\n".join(lines) + "\n"
    except Exception as e:
        print("⚠️ Không thể đọc config/prompt_rules.json:", e)
        return ""

CHARACTER_VOICE_PROFILES = {
    "Nu-25t.png": "A 25-year-old Vietnamese female voice speaking Southern Vietnamese accent, gentle, soft, warm, relaxed, conversational tone, clear articulation. (Stability: 0.60, Clarity: 0.75, Style Exaggeration: 0.15)",
    "Nu-23t.png": "A 23-year-old Vietnamese female voice speaking Southern Vietnamese accent, cheerful, energetic, bright, youthful, conversational tone, clear articulation. (Stability: 0.55, Clarity: 0.80, Style Exaggeration: 0.20)",
    "Nam-25t.png": "A 25-year-old Vietnamese male voice speaking Southern Vietnamese accent, charismatic, confident, warm, relaxed, conversational tone, clear articulation. (Stability: 0.65, Clarity: 0.75, Style Exaggeration: 0.15)"
}

def generate_prompt_for_item(item_id, item_dir):
    print(f"\n🎬 Đang xử lý sinh Master Prompt chuẩn cho Mã SP: {item_id}...")
    
    images = []
    for ext in ["*.webp", "*.jpg", "*.png", "*.jpeg"]:
        images.extend(glob.glob(os.path.join(item_dir, ext)))

    image_path = images[0] if images else None
    
    raw_product_name = lookup_product_name(item_id, item_dir)
    print(f"📦 Tên sản phẩm Shopee: \"{raw_product_name}\"")

    selected_char = select_character_for_product(raw_product_name)
    print(f"👤 Nhân vật được chọn phù hợp: {selected_char}")

    voice_profile = CHARACTER_VOICE_PROFILES.get(
        selected_char,
        "A 25-year-old Vietnamese female voice speaking Southern Vietnamese accent, gentle, soft, warm, relaxed, conversational tone, clear articulation. (Stability: 0.60, Clarity: 0.75, Style Exaggeration: 0.15)"
    )

    # Nạp toàn bộ các quy tắc sắt đá trung tâm từ config/prompt_rules.json
    central_rules_text = load_central_prompt_rules()

    # Bộ 8 góc tiếp cận UGC Viral đa dạng hóa kịch bản
    ugc_angles = [
        ("REVERSE EXPECTATION (TƯỞNG KHÔNG NGON MÀ NGON KHÔNG TƯỞNG)", "Đảo ngược kỳ vọng ban đầu: Nghĩ là món đồ bình thường/mua thử cho vui ai ngờ mê luôn vì tiện lợi và bền đẹp bất ngờ."),
        ("EXTREME STRESS TEST (THỬ THÁCH THỰC TẾ CỰC HẠN)", "Hành động kịch tính trực diện: Dẫm nước ngập, dầm mưa lớn, test độ co giãn chống thấm ngay trước ống kính để chứng minh độ bền."),
        ("LIFEHACK & ON-THE-GO (MẸO BỎ TÚI CỨU CÁNH MÙA MƯA)", "Phong cách tiện lợi bỏ cốp xe/túi xách: Bí quyết cứu nguy đôi giày trong 3 giây cho dân công sở, sinh viên, người đi làm."),
        ("BEFORE VS AFTER (SO SÁNH TƯƠNG PHẢN TRỰC DIỆN)", "Tạo đối lập mạnh: Một bên chịu cảnh dơ bẩn ướt sũng - một bên khô ráo tinh tươm sạch sẽ như vừa mở hộp."),
        ("RELATABLE REGRET (HỐI HẬN VÌ KHÔNG BIẾT SỚM HƠN)", "Tâm lý tiếc nuối chân thực: 'Biết món này sớm hơn thì tháng trước đã không phải bỏ xó đôi giày yêu thích'."),
        ("FRIEND GOSSIP & SOCIAL PROOF (AI CŨNG HỎI MUA Ở ĐÂU)", "Câu chuyện đời thường gần gũi: 'Hôm nay mang đi làm/dạo phố mà đồng nghiệp cứ hỏi xin link mãi vì quá xịn'."),
        ("DAY IN MY LIFE / REALISTIC POV (GÓC NHÌN THỰC TẾ)", "Theo chân nhân vật trải nghiệm dạo phố, đi làm, đi cafe bất chấp thời tiết với góc nhìn POV chân thực."),
        ("AESTHETIC LIFESTYLE & SENSORY SATISFACTION (THỜI TRANG & CẢM GIÁC)", "Phối đồ phong cách, bước đi tự tin sảng khoái, chất liệu cao cấp bảo vệ tuyệt đối và tôn dáng.")
    ]
    import random
    suggested_angle_name, suggested_angle_desc = random.choice(ugc_angles)

    system_directive = f"""You are a World-Class Viral Video Creative Director and Marketing Copywriter specializing in 10-second high-converting UGC (User-Generated Content) Review videos for Gemini Omni.

Look closely at the attached main product image AND analyze the full Shopee title: "{raw_product_name}".

{central_rules_text}

CREATIVE TARGET FOR THIS VIDEO:
- Primary UGC Story Angle: **{suggested_angle_name}**
- Angle Core Concept: {suggested_angle_desc}
- Character Voice Profile: {voice_profile}

CRITICAL RULES:
1. ULTRA-LEAN & CONCISE PROMPT:
   - Do NOT write long, micro-managed visual descriptions. Let the AI video diffusion model naturally synthesize fluid cinematic physics.
   - Simply write 1-2 punchy, dynamic sentences describing a single-shot continuous handheld tracking shot or POV of the character walking / showcasing the attached product.
   - Do NOT over-describe product colors or textures in text — the video model extracts 100% of product visual details directly from the attached image.

2. CHARISMATIC VIETNAMESE VOICEOVER & ON-CAMERA LIP-SYNC:
   - Write a natural, viral, conversational 0-10s Vietnamese voiceover sharing a genuine review matching the story angle and character voice profile.
   - The Visual description MUST explicitly show the character actively speaking to the camera with accurate, expressive Vietnamese lip-sync matching the spoken words.

3. ZERO-TOLERANCE SAFETY:
   - Absolutely NO on-screen text, floating subtitles, words, price tags, typography, or logos rendered onto the video frames.
   - Absolutely NO peeling, pulling, or manual slipping off shoe covers on camera.
   - Both feet must always wear the exact same footwear state simultaneously.

STRICTLY GENERATE THE FINAL MASTER PROMPT IN THIS EXACT CLEAN ULTRA-LEAN FORMAT:

```markdown
[ASSETS]:
- Product: Attached image
- Character: Attached image (Lock facial identity & voice, diverse stylish outfit, Voice: {voice_profile})

[PROMPT]:
- Visual: [1-2 concise, vivid sentences describing a dynamic handheld tracking shot / POV of the character walking or showcasing the attached product while actively speaking to the camera with expressive, accurate Vietnamese lip-sync and fluid mouth articulation]
- Voiceover (Vietnamese): "[Natural, captivating, conversational 0-10s review voiceover in Vietnamese]"

[CONSTRAINTS]:
- 9:16 vertical, 10s, photorealistic UGC, 60fps, clean footage with zero text/subtitles/typography/watermarks/logos.
- Accurate on-camera Vietnamese lip-sync matching the spoken voiceover; natural mouth movement and expressive facial gestures.
- No peeling/pulling/slipping off covers on camera; no intricate finger actions.
- Both feet must wear the exact same footwear state simultaneously.
- No mid-frame object vanishing or morphing.
```

Generate ONLY the clean markdown block above. Do not include any explanations."""

    generated_text = call_gemini_multimodal_api(system_directive, image_path)
    if generated_text:
        clean_text = generated_text.replace("```markdown", "").replace("```text", "").replace("```", "").strip()
        
        output_file = os.path.join(item_dir, f"{item_id}.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(clean_text)
            
        print(f"✅ Đã lưu Master Prompt tinh lọc thành công tại: {output_file}")

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

def prompt_user_continue_with_timeout(current, total, timeout=10):
    print(f"\n------------------------------------------------------------")
    print(f"📌 Đã hoàn thành {current}/{total} sản phẩm.")
    print("Vui lòng chọn:")
    print("  [1] Tiếp tục sinh Prompt cho sản phẩm tiếp theo")
    print("  [2] Thoát ra (MẶC ĐỊNH - TỰ ĐỘNG THOÁT SAU 10 GIÂY)")
    print(f"\n👉 Nhập lựa chọn (1 hoặc 2, tự động chọn [2] thoát sau {timeout}s): ", end="", flush=True)

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
        all_dirs = [d for d in os.listdir(ASSETS_DIR) if os.path.isdir(os.path.join(ASSETS_DIR, d))]
        if not all_dirs:
            print("ℹ️ Thư mục Product_Assets/ chưa có sản phẩm nào.")
            return

        print(f"🔍 Quét thư mục: Tìm thấy {len(all_dirs)} thư mục sản phẩm trong Product_Assets/.")
        print("📊 Đang kiểm tra trạng thái tiến trình trên Google Sheet...")

        # Lấy trạng thái hiện tại từ Google Sheet
        status_map = {}
        try:
            from sheet_sync import get_all_product_statuses
            status_map = get_all_product_statuses()
        except Exception as e:
            print("⚠️ Không thể kết nối Google Sheet để kiểm tra trạng thái:", e)

        pending_items = []
        skipped_items = []

        for item_id in sorted(all_dirs):
            item_status = status_map.get(item_id, "")
            prompt_file = os.path.join(ASSETS_DIR, item_id, f"{item_id}.txt")
            legacy_prompt_file = os.path.join(ASSETS_DIR, item_id, "master_prompt.txt")
            has_valid_prompt = (os.path.exists(prompt_file) and os.path.getsize(prompt_file) > 100) or \
                               (os.path.exists(legacy_prompt_file) and os.path.getsize(legacy_prompt_file) > 100)
            
            # Nếu Sheet ghi đã tạo prompt/video hoặc local đã có prompt hợp lệ
            if item_status in ["Đã tạo Prompt", "Đã tạo Video"] or has_valid_prompt:
                skipped_items.append((item_id, item_status or "Đã có file prompt .txt"))
            else:
                pending_items.append(item_id)

        if skipped_items:
            print(f"ℹ️ Đã tự động BỎ QUA {len(skipped_items)} sản phẩm đã hoàn thành Prompt/Video:")
            for s_id, s_st in skipped_items:
                print(f"   - Mã SP {s_id}: [{s_st}]")

        if not pending_items:
            print("\n✨ TẤT CẢ sản phẩm trong Product_Assets/ đều đã được tạo Prompt hoặc hoàn thành Video! Không có sản phẩm nào cần xử lý.")
            return

        print(f"\n🚀 Phát hiện {len(pending_items)} sản phẩm cần tạo Master Prompt: {', '.join(pending_items)}")
        count = 0
        total_items = len(pending_items)

        for idx, item_id in enumerate(pending_items, start=1):
            item_dir = os.path.join(ASSETS_DIR, item_id)
            if generate_prompt_for_item(item_id, item_dir):
                count += 1

            if idx < total_items:
                should_continue = prompt_user_continue_with_timeout(idx, total_items, timeout=10)
                if not should_continue:
                    break

        print(f"\n🎉 Hoàn tất đợt xử lý! Đã sinh thành công {count} Master Prompt chuẩn!")

if __name__ == "__main__":
    main()
