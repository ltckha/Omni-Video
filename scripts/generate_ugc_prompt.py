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

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_env_if_needed():
    if "GEMINI_API_KEY" not in os.environ or not os.environ["GEMINI_API_KEY"]:
        for env_file in [os.path.join(PROJECT_DIR, ".env"), os.path.expanduser("~/.zshrc"), os.path.expanduser("~/.zshenv"), os.path.expanduser("~/.bash_profile")]:
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
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
CHARACTERS_DIR = os.path.join(PROJECT_DIR, "characters")
DATA_DIR = os.path.join(PROJECT_DIR, "data")

# Danh sách mô hình Flash ưu tiên
PREFERRED_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash"
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

def is_valid_prompt_structure(text: str) -> bool:
    """Kiểm tra tính toàn vẹn của Master Prompt sinh ra (đủ 3 phần bắt buộc và độ dài chuẩn)."""
    if not text or len(text.strip()) < 150:
        return False
    clean = text.replace("```markdown", "").replace("```text", "").replace("```", "").strip()
    required_sections = ["[ASSETS]", "[PROMPT]", "[CONSTRAINTS]"]
    return all(sec in clean for sec in required_sections)

def get_recent_voiceovers(limit=5):
    """Quét các file prompt gần đây để lấy danh sách voiceover đã dùng nhằm tránh lặp lại."""
    voiceovers = []
    if not os.path.exists(ASSETS_DIR):
        return voiceovers
    txt_files = glob.glob(os.path.join(ASSETS_DIR, "*", "*.txt"))
    for fpath in sorted(txt_files, key=os.path.getmtime, reverse=True):
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for line in content.splitlines():
                    if "Voiceover (Vietnamese):" in line or "Voiceover:" in line:
                        vo = line.split(":", 1)[1].strip().strip('"')
                        if vo and vo not in voiceovers:
                            voiceovers.append(vo)
                            if len(voiceovers) >= limit:
                                return voiceovers
        except Exception:
            pass
    return voiceovers

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
            "temperature": 0.95,
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
                with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    if is_valid_prompt_structure(text):
                        print(f"⚡ Đã sinh Master Prompt thành công bằng Mô hình Flash: {model_name}")
                        return text
                    else:
                        print(f"⚠️ Mô hình {model_name} sinh prompt bị thiếu cấu trúc (độ dài: {len(text)} ký tự), đang chuyển tiếp...")
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

def is_footwear_product(product_name: str) -> bool:
    """Xác định sản phẩm có thuộc nhóm ngành hàng giày dép/bọc giày mang vào chân hay không."""
    if not product_name:
        return False
    name_lower = product_name.lower()

    # Các từ khóa loại trừ: thiết bị điện tử, phụ kiện, dụng cụ vệ sinh, hộp/tủ/túi chứa đựng giày dép
    exclude_keywords = [
        "máy sấy", "kệ", "hộp", "tủ", "nước lau", "chai xịt", "xịt", "vệ sinh",
        "xi đánh", "xi ", "bàn chải", "viên khử mùi", "sáp khử mùi", "máy khử mùi",
        "dây giày", "túi đựng", "túi", "dụng cụ", "miếng lót", "lót giày",
        "khay", "giá để", "cây đón gót", "đón gót"
    ]
    if any(ex in name_lower for ex in exclude_keywords):
        return False

    footwear_keywords = [
        "giày", "dép", "ủng", "bọc giày", "bao giày", "vớ", "tất",
        "shoe", "shoes", "boot", "boots", "sneaker", "sneakers",
        "sandal", "sandals", "slipper", "slippers", "clog", "crocs",
        "footwear"
    ]
    return any(kw in name_lower for kw in footwear_keywords)

def select_story_angle(product_name: str):
    """Lựa chọn góc tiếp cận sáng tạo phù hợp cho sản phẩm, linh hoạt giữa quà tặng và các góc review thực chiến."""
    p_lower = (product_name or "").lower()
    gift_keywords = ["quà", "gift", "set quà", "combo quà", "tặng người yêu", "tặng bạn", "tặng mẹ", "20/10", "8/3", "valentine"]
    is_gift_related = any(kw in p_lower for kw in gift_keywords)

    ugc_angles = [
        ("SURPRISE GIFT & HIGH-EQ MOMENT (MÓN QUÀ BẤT NGỜ & TÌNH CẢM TINH TẾ)",
         "Tình huống trao tặng món quà bất ngờ trong bối cảnh đời thường tự nhiên (văn phòng, bàn làm việc, quán cafe, phòng khách...), người nhận đón nhận với sự xúc động chân thành, nâng niu sản phẩm và dành lời khen ngợi tinh tế đúng vào đặc tính sản phẩm."),
        ("REVERSE EXPECTATION (TƯỞNG KHÔNG NGON MÀ NGON KHÔNG TƯỞNG)",
         "Đảo ngược kỳ vọng ban đầu: Nghĩ là món đồ bình thường/mua thử cho vui ai ngờ mê luôn vì tiện lợi và chất lượng bất ngờ."),
        ("EXTREME STRESS TEST (THỬ THÁCH THỰC TẾ CỰC HẠN)",
         "Hành động kịch tính trực diện: Thử độ bền, chống nước, chống bám bẩn hoặc test hiệu năng trực tiếp trước ống kính."),
        ("LIFEHACK & ON-THE-GO (MẸO BỎ TÚI CỨU CÁNH)",
         "Phong cách tiện lợi mang theo người/bỏ túi: Bí quyết cứu nguy siêu tốc cho dân công sở, sinh viên, người bận rộn."),
        ("BEFORE VS AFTER (SO SÁNH TƯƠNG PHẢN TRỰC DIỆN)",
         "Tạo đối lập mạnh mẽ: So sánh trước và sau khi dùng sản phẩm một cách trực quan, rõ nét."),
        ("RELATABLE REGRET (HỐI HẬN VÌ KHÔNG BIẾT SỚM HƠN)",
         "Tâm lý tiếc nuối chân thực: Chia sẻ trải nghiệm thật vì sao nếu biết món này sớm hơn thì đã tiết kiệm được bao nhiêu thời gian/công sức."),
        ("FRIEND GOSSIP & SOCIAL PROOF (AI CŨNG HỎI MUA Ở ĐÂU)",
         "Câu chuyện đời thường gần gũi: Vừa dùng thử/mang đi làm mà đồng nghiệp, bạn bè ai cũng tò mò hỏi xin địa chỉ mua."),
        ("DAY IN MY LIFE / REALISTIC POV (GÓC NHÌN THỰC TẾ)",
         "Theo chân nhân vật trải nghiệm sản phẩm trong nhịp sống hằng ngày với góc nhìn gần gũi, chân thực."),
        ("AESTHETIC LIFESTYLE & SENSORY SATISFACTION (THỜI TRANG & CẢM GIÁC THƯ THÁI)",
         "Tôn vinh vẻ đẹp thiết kế, cảm giác sảng khoái và phong cách sống hiện đại khi trải nghiệm sản phẩm.")
    ]

    import random
    if is_gift_related and random.random() < 0.7:
        return ugc_angles[0]
    return random.choice(ugc_angles)

def generate_prompt_for_item(item_id, item_dir):
    print(f"\n🎬 Đang xử lý sinh Master Prompt UGC cho Mã SP: {item_id}...")
    
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

    # Nạp các voiceover gần đây để chống lặp lại từ ngữ
    recent_vos = get_recent_voiceovers(limit=5)
    anti_repetition_text = ""
    if recent_vos:
        anti_repetition_text = "\n[CRITICAL ANTI-REPETITION CONSTRAINT]:\nDO NOT reuse or closely resemble any of these recent voiceovers:\n" + "\n".join(f"- \"{vo}\"" for vo in recent_vos) + "\n"

    # Lựa chọn góc sáng tạo đa dạng
    suggested_angle_name, suggested_angle_desc = select_story_angle(raw_product_name)
    print(f"💡 Góc sáng tạo: {suggested_angle_name}")

    # Phân loại ngữ cảnh: Chỉ áp dụng luật đối xứng giày khi sản phẩm thực sự là giày dép mang vào chân
    is_footwear = is_footwear_product(raw_product_name)
    if is_footwear:
        safety_rules_text = """3. ZERO-TOLERANCE SAFETY:
   - Absolutely NO on-screen text, floating subtitles, words, price tags, typography, or logos rendered onto the video frames.
   - Absolutely NO peeling, pulling, or manual slipping off shoe covers on camera.
   - Both feet must always wear the exact same footwear state simultaneously."""
        constraints_block = """[CONSTRAINTS]:
- 9:16 vertical, 10s, photorealistic UGC, 60fps, clean footage with zero text/subtitles/typography/watermarks/logos.
- Accurate on-camera Vietnamese lip-sync matching the spoken voiceover; natural mouth movement and expressive facial gestures.
- No peeling/pulling/slipping off covers on camera; no intricate finger actions.
- Both feet must wear the exact same footwear state simultaneously.
- No mid-frame object vanishing or morphing."""
    else:
        safety_rules_text = """3. ZERO-TOLERANCE SAFETY:
   - Absolutely NO on-screen text, floating subtitles, words, price tags, typography, or logos rendered onto the video frames.
   - Absolutely NO mid-frame object vanishing or morphing in a single continuous shot."""
        constraints_block = """[CONSTRAINTS]:
- 9:16 vertical, 10s, photorealistic UGC, 60fps, clean footage with zero text/subtitles/typography/watermarks/logos.
- Accurate on-camera Vietnamese lip-sync matching the spoken voiceover; natural mouth movement and expressive facial gestures.
- No mid-frame object vanishing or morphing."""

    system_directive = f"""You are a World-Class Viral Video Creative Director and Marketing Copywriter specializing in 10-second high-converting UGC (User-Generated Content) videos for Gemini Omni.

Look closely at the attached main product image (Input Image 1) AND analyze the full Shopee title: "{raw_product_name}".

{central_rules_text}
{anti_repetition_text}

CREATIVE TARGET FOR THIS VIDEO:
- Story Hook & Creative Angle: **{suggested_angle_name}**
- Angle Core Premise: {suggested_angle_desc}
- Presenter / Recipient: {selected_char} (Voice: {voice_profile})

CRITICAL ARCHITECTURE RULES (SINGLE CONTINUOUS SHOT & PRODUCT-CENTRIC):
1. SINGLE CONTINUOUS CAMERA TAKE (ONE-TAKE FLOW):
   - The entire 10-second video MUST be described as ONE single continuous camera take without any fragmented scene cuts, multi-beats, whip-pans, or timestamps.
2. PRODUCT IS THE PRIMARY SUBJECT (40-50% VERTICAL FRAME COVERAGE):
   - The visual MUST feature a crisp, center-framed close-up demonstration or presentation of the specific physical product held prominently at chest level, occupying 40-50% of the vertical 9:16 frame.
   - Smooth physical demonstration or appreciative handling maintaining 100% geometric shape, material, and color fidelity to Input Image 1.
   - The setting (office desk, coffee table, vanity table, cozy living space, or street scene) should be authentic, atmospheric, and natural.
   - The character ({selected_char}) actively interacts with the product while speaking with continuous, natural Vietnamese lip-sync.

3. CHARISMATIC VIETNAMESE VOICEOVER & ON-CAMERA LIP-SYNC (STRICTLY PRODUCT-ANCHORED & DYNAMIC):
   - Compose a completely original, natural, emotional 0-10s Vietnamese voiceover (12-20 words).
   - The voiceover MUST specifically highlight the real utility, texture, scent, color, or tangible benefit of "{raw_product_name}".
   - Do NOT use generic template placeholders or repetitive canned phrases. The spoken line must feel spontaneous, authentic, and tailor-made for this exact product.

{safety_rules_text}

STRICTLY GENERATE THE FINAL MASTER PROMPT IN THIS EXACT CLEAN ULTRA-LEAN FORMAT:

```markdown
[ASSETS]:
- Product (Primary Subject - Input Image 1): [Specific physical product noun, form factor, and key identifying colors/materials from Input Image 1]. Must maintain 100% visual fidelity to Input Image 1.
- Character / Presenter (Secondary Subject - Input Image 2): {selected_char} (Lock facial identity & voice, diverse stylish outfit, Voice: {voice_profile}) acting as the presenter/recipient.

[PROMPT]:
- Visual: [1-2 concise sentences describing a single continuous one-take shot with the product as the primary subject held or demonstrated at center stage occupying 40-50% of the vertical 9:16 frame in a natural setting, with {selected_char} actively speaking with continuous natural Vietnamese lip-sync]
- Voiceover (Vietnamese): "[Natural, captivating, product-specific conversational 0-10s voiceover in Vietnamese]"

{constraints_block}
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

    # Phân tích tham số dòng lệnh
    target_id = None
    force_all = False

    for arg in sys.argv[1:]:
        if arg in ["--force", "-f"]:
            force_all = True
        elif not arg.startswith("-"):
            target_id = arg.strip()

    if target_id:
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
            
            if force_all:
                pending_items.append(item_id)
            elif item_status in ["Đã tạo Prompt", "Đã tạo Video"] or has_valid_prompt:
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
