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

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyxBWA7eJjmi0vn9etRyainI3rrHbAQAN_Uc7tI14sMyyJLftBSnQLJjm5o0WTamS20Rg/exec"

def upload_csv_to_gsheet(csv_filepath):
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

    # Bỏ qua xác thực SSL certificate trên macOS nếu thiếu certs
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
        # Tìm file csv mới nhất trong thư mục hiện tại
        csv_files = glob.glob("*.csv")
        if csv_files:
            csv_files.sort(key=os.path.getmtime, reverse=True)
            target_csv = csv_files[0]

    if target_csv:
        upload_csv_to_gsheet(target_csv)
    else:
        print("Vui lòng chỉ định file CSV. Ví dụ: python3 import_csv_to_gsheet.py my_data.csv")
