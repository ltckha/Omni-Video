#!/usr/bin/env python3
"""
Script tự động đẩy dữ liệu từ file CSV bất kỳ lên Google Sheet
Tự động lọc bỏ các sản phẩm bị trùng lặp dựa trên Mã SP & Link sản phẩm.
Sau khi import xong, tự động di chuyển toàn bộ file CSV vào thư mục data/.
"""

import sys
import os
import glob
import urllib.request
import json
import ssl
import shutil

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
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_DIR, "data")

def move_csv_to_data_folder(csv_filepath):
    """Di chuyển file CSV đã import vào thư mục data/"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

    abs_path = os.path.abspath(csv_filepath)
    filename = os.path.basename(abs_path)
    target_path = os.path.join(DATA_DIR, filename)

    if abs_path != target_path:
        try:
            shutil.move(abs_path, target_path)
            print(f"📦 Đã tự động di chuyển file CSV {filename} vào thư mục data/")
        except Exception as e:
            print(f"⚠️ Không thể di chuyển file CSV {filename} vào data/: {e}")

def organize_all_root_csvs():
    """Di chuyển tất cả các file CSV ở thư mục gốc dự án vào data/"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        
    for root_csv in glob.glob(os.path.join(PROJECT_DIR, "*.csv")):
        filename = os.path.basename(root_csv)
        target_path = os.path.join(DATA_DIR, filename)
        if root_csv != target_path:
            try:
                shutil.move(root_csv, target_path)
                print(f"📦 Đã di chuyển file CSV {filename} từ thư mục gốc vào data/")
            except Exception as e:
                pass

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
            
            # Tự động di chuyển file CSV đã import xong vào thư mục data/
            move_csv_to_data_folder(csv_filepath)
    except Exception as e:
        print("❌ Lỗi khi gửi dữ liệu:", e)

    organize_all_root_csvs()

if __name__ == "__main__":
    target_csv = None
    if len(sys.argv) > 1:
        target_csv = sys.argv[1]
    else:
        # Ưu tiên quét file CSV trong data/ trước, sau đó tới thư mục gốc và ~/Downloads
        csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv")) + glob.glob(os.path.join(PROJECT_DIR, "*.csv"))
        if csv_files:
            csv_files.sort(key=os.path.getmtime, reverse=True)
            target_csv = csv_files[0]

    if target_csv:
        upload_csv_to_gsheet(target_csv)
    else:
        print("ℹ️ Không tìm thấy file CSV nào để import.")
