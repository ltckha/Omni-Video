#!/usr/bin/env python3
"""
Script tự động đẩy dữ liệu từ file CSV bất kỳ lên Google Sheet
Tự động lọc bỏ các sản phẩm bị trùng lặp dựa trên Mã SP & Link sản phẩm.
"""

import sys
import os
import glob
import urllib.request
import json
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

WEBHOOK_URL = os.environ.get("OMNI_GAS_WEBHOOK_URL", "")

def upload_csv_to_gsheet(csv_filepath):
    if not WEBHOOK_URL:
        print("❌ Chưa cấu hình OMNI_GAS_WEBHOOK_URL trong file .env. Xem README.md để thiết lập.")
        return

    if not os.path.exists(csv_filepath):
        print(f"❌ File không tồn tại: {csv_filepath}")
        return

    print(f"📄 Đang đọc file CSV: {os.path.basename(csv_filepath)}...")
    with open(csv_filepath, 'r', encoding='utf-8', errors='ignore') as f:
        csv_content = f.read()

    payload = {
        "action": "import_csv_text",
        "csvText": csv_content
    }

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'text/plain;charset=utf-8'}
    )

    print("🚀 Đang gửi dữ liệu lên Google Sheet & xử lý lọc trùng...")
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            print("✨ Kết quả:", res_data.get("message", res_data))
    except Exception as e:
        print("❌ Lỗi khi gửi dữ liệu:", e)

if __name__ == "__main__":
    target_csv = None
    if len(sys.argv) > 1:
        target_csv = sys.argv[1]
    else:
        csv_files = glob.glob(os.path.join(os.path.dirname(__file__), "..", "data", "*.csv")) + glob.glob("*.csv")
        if csv_files:
            csv_files.sort(key=os.path.getmtime, reverse=True)
            target_csv = csv_files[0]

    if target_csv:
        upload_csv_to_gsheet(target_csv)
    else:
        print("Vui lòng chỉ định file CSV. Ví dụ: python3 scripts/import_csv_to_gsheet.py data/my_data.csv")
