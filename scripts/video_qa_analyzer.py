#!/usr/bin/env python3
"""
Omni Video - Video Quality Assurance (QA) Analyzer via Gemini Video Understanding API
Tự động tải video .mp4 lên Gemini Files API, thẩm định chất lượng video theo 5 tiêu chí:
1. Product Fidelity (Độ bảo toàn sản phẩm)
2. Character Consistency (Độ nhất quán nhân vật)
3. Artifact & Morphing (Né rác điểm ảnh, dị dạng)
4. Motion Naturalness (Độ tự nhiên chuyển động)
5. Story Continuity (Độ mượt kịch bản)

Tự động dọn dẹp (delete) file khỏi Gemini Files API sau khi phân tích xong.
"""

import os
import sys
import glob
import json
import time
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

def get_api_key():
    return os.environ.get("GEMINI_API_KEY", "")

def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def upload_video_to_gemini_files(video_path):
    """
    Tải video .mp4 lên Gemini Files API bằng Resumable Protocol
    Returns (file_name, file_uri)
    """
    if not os.path.exists(video_path):
        print(f"❌ File video không tồn tại: {video_path}")
        return None, None

    file_size = os.path.getsize(video_path)
    file_display_name = os.path.basename(video_path)
    mime_type = "video/mp4"

    ctx = get_ssl_context()

    # Bước 1: Khởi tạo Resumable Upload
    init_url = "https://generativelanguage.googleapis.com/upload/v1beta/files"
    init_headers = {
        "x-goog-api-key": get_api_key(),
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(file_size),
        "X-Goog-Upload-Header-Content-Type": mime_type,
        "Content-Type": "application/json"
    }
    init_data = json.dumps({"file": {"display_name": file_display_name}}).encode("utf-8")

    req = urllib.request.Request(init_url, data=init_data, headers=init_headers, method="POST")

    upload_url = None
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            upload_url = resp.headers.get("x-goog-upload-url") or resp.headers.get("X-Goog-Upload-Url")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Upload Gemini Files API: {e}")
        return None, None

    if not upload_url:
        print("❌ Không nhận được upload_url từ Gemini API")
        return None, None

    # Bước 2: Tải dữ liệu nhị phân của video lên
    with open(video_path, "rb") as vf:
        video_bytes = vf.read()

    upload_headers = {
        "Content-Length": str(file_size),
        "X-Goog-Upload-Offset": "0",
        "X-Goog-Upload-Command": "upload, finalize"
    }

    req_upload = urllib.request.Request(upload_url, data=video_bytes, headers=upload_headers, method="POST")
    
    file_name = None
    file_uri = None
    try:
        with urllib.request.urlopen(req_upload, context=ctx) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            file_info = resp_data.get("file", {})
            file_name = file_info.get("name")
            file_uri = file_info.get("uri")
    except Exception as e:
        print(f"❌ Lỗi tải dữ liệu video lên Gemini Files API: {e}")
        return None, None

    # Bước 3: Polling trạng thái cho tới khi ACTIVE
    print(f"⏳ Đang chờ Gemini xử lý video ({file_display_name})...")
    status_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={get_api_key()}"

    max_attempts = 30
    for attempt in range(max_attempts):
        req_status = urllib.request.Request(status_url)
        try:
            with urllib.request.urlopen(req_status, context=ctx) as resp:
                status_data = json.loads(resp.read().decode("utf-8"))
                state = status_data.get("state")
                if state == "ACTIVE":
                    print(f"✅ Video đã sẵn sàng phân tích AI! (URI: {file_uri})")
                    return file_name, file_uri
                elif state == "FAILED":
                    print("❌ Gemini báo xử lý video thất bại (FAILED).")
                    return None, None
        except Exception:
            pass
        time.sleep(3)

    print("⚠️ Quá thời gian chờ xử lý video trên Gemini API.")
    return file_name, file_uri

def delete_gemini_file(file_name):
    """
    Xóa file video khỏi Gemini Files API sau khi dùng xong
    """
    if not file_name:
        return
    url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={get_api_key()}"
    req = urllib.request.Request(url, method="DELETE")
    ctx = get_ssl_context()
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            print(f"🧹 Đã xóa dọn dẹp video khỏi Gemini Files API ({file_name}).")
    except Exception as e:
        pass

def analyze_video_quality(video_path, item_dir):
    """
    Phân tích chất lượng video QA bằng Gemini Multimodal Understanding
    """
    api_key = get_api_key()
    if not api_key:
        print("❌ Lỗi: Không tìm thấy GEMINI_API_KEY trong .env")
        return None

    print(f"\n🔍 BẮT ĐẦU PHÂN TÍCH CHẤT LƯỢNG VIDEO (QA INSPECTION): {os.path.basename(video_path)}")

    file_name, file_uri = upload_video_to_gemini_files(video_path)
    if not file_uri:
        return None

    qa_prompt = """You are a Professional Quality Assurance (QA) Video Inspector for AI-generated UGC product review videos.

Analyze the attached video carefully frame-by-frame, evaluating visual quality, item stability, and storytelling smoothness.

CRITICAL DEFECT TO WATCH FOR:
- **MID-FRAME POP-OUT / VANISHING ARTIFACTS (🔴 SEVERE FAILURE)**: In a single continuous shot, if a shoe or object suddenly pops out of existence, vanishes into thin air, or instantly morphs mid-frame without a natural physical removal action or camera cut, DEDUCT AT LEAST 10-15 POINTS from `artifact_free` and `motion_naturalness` (Total score MUST be < 70 FAIL).
- **VALID CINEMATIC CUTS (🟢 OK / ALLOWED)**: Switching camera angle or cutting to a clean new shot (e.g., cutting from a medium shot of uncomfortable heels to a close-up shot of feet wearing the slides) is a NORMAL, VALID VIDEO EDITING TECHNIQUE. DO NOT penalize clean camera cuts!

SCORING METRICS (0-20 points each, total max 100):
1. `product_fidelity` (0-20): Is the main product accurate in shape/color/sole without severe design morphing?
2. `character_consistency` (0-20): Does the character maintain consistent facial features and realistic appearance?
3. `artifact_free` (0-20): Is the video free of pixel glitches, vanishing objects mid-shot, melted feet, or extra toes?
4. `motion_naturalness` (0-20): Are human movements physically plausible and smooth?
5. `narrative_flow` (0-20): Is the video storytelling smooth and enjoyable from 0 to 10 seconds?

OUTPUT FORMAT:
Return ONLY a valid JSON object matching this exact schema (no markdown, no extra commentary):

{
  "total_score": 58,
  "verdict": "FAIL",
  "scores": {
    "product_fidelity": 18,
    "character_consistency": 18,
    "artifact_free": 6,
    "motion_naturalness": 6,
    "narrative_flow": 10
  },
  "detected_flaws": [
    "Mid-frame vanishing artifact at 0:03: high heel shoe pops out of existence mid-shot without physical action or camera cut."
  ],
  "recommendations_for_prompt": [
    "Strictly prohibit mid-shot object pop-out or vanishing artifacts; require clean camera cut or physical removal."
  ]
}
"""

    ctx = get_ssl_context()
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "file_data": {
                            "file_uri": file_uri,
                            "mime_type": "video/mp4"
                        }
                    },
                    {
                        "text": qa_prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    report_data = None
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            report_data = json.loads(clean_text)
    except Exception as e:
        print(f"⚠️ Lỗi gọi Gemini QA Video API: {e}")

    # Xóa file video trên Gemini Files API ngay lập tức
    delete_gemini_file(file_name)

    if report_data:
        report_file = os.path.join(item_dir, "qa_report.json")
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"📊 Đã lưu báo cáo QA thành công tại: {report_file}")
        except Exception as e:
            print(f"⚠️ Lỗi lưu qa_report.json: {e}")

        # Hiển thị điểm số đẹp mắt ra terminal
        score = report_data.get("total_score", 0)
        verdict = report_data.get("verdict", "UNKNOWN")
        print("\n============================================================")
        print(f"⭐ BÁO CÁO ĐÁNH GIÁ CHẤT LƯỢNG VIDEO (QA REPORT)")
        print("============================================================")
        print(f"🏆 ĐIỂM TỔNG THỂ: {score}/100 - XẾP LOẠI: {verdict}")
        scores = report_data.get("scores", {})
        print(f"  • Độ bảo toàn SP (Product Fidelity): {scores.get('product_fidelity', 0)}/20")
        print(f"  • Nhất quán nhân vật (Character Consistency): {scores.get('character_consistency', 0)}/20")
        print(f"  • Né rác/Dị dạng (Artifact Free): {scores.get('artifact_free', 0)}/20")
        print(f"  • Chuyển động tự nhiên (Motion Naturalness): {scores.get('motion_naturalness', 0)}/20")
        print(f"  • Độ mượt kịch bản (Narrative Flow): {scores.get('narrative_flow', 0)}/20")
        
        flaws = report_data.get("detected_flaws", [])
        if flaws:
            print("\n🔍 LỖI PHÁT HIỆN:")
            for fl in flaws:
                print(f"  ⚠️ {fl}")
        print("============================================================\n")

    return report_data

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
        if os.path.isdir(target_path):
            mp4s = glob.glob(os.path.join(target_path, "*.mp4")) + glob.glob(os.path.join(target_path, "*.MP4"))
            if mp4s:
                analyze_video_quality(mp4s[0], target_path)
            else:
                print(f"❌ Không tìm thấy file .mp4 trong {target_path}")
        elif os.path.isfile(target_path):
            analyze_video_quality(target_path, os.path.dirname(target_path))
    else:
        print("Cách dùng: python3 scripts/video_qa_analyzer.py <đường_dẫn_thư_mục_hoặc_file_mp4>")
