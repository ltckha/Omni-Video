#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script quét toàn bộ video đã hoàn thành tại /Volumes/Media/Omni-Video/Product_Assets/
và cập nhật hàng loạt đường dẫn file video vào Cột 13 (Output File) trên Google Sheet.
"""

import os
import sys
import glob
import json
import urllib.request
import ssl

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TARGET_MEDIA_DIR = "/Volumes/Media/Omni-Video/Product_Assets"

def _load_env_file():
    env_file = os.path.join(PROJECT_DIR, ".env")
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
WEBHOOK_URL = os.environ.get("OMNI_GAS_WEBHOOK_URL", "") or os.environ.get("WEBHOOK_URL", "")

def backfill_output_files():
    if not WEBHOOK_URL:
        print("❌ Lỗi: Không tìm thấy OMNI_GAS_WEBHOOK_URL trong .env")
        return

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    search_dirs = []
    if os.path.exists(TARGET_MEDIA_DIR):
        search_dirs.append(TARGET_MEDIA_DIR)
    else:
        print(f"⚠️ Chú ý: Thư mục ổ đĩa Media {TARGET_MEDIA_DIR} hiện chưa được kết nối/mount.")

    local_assets = os.path.join(PROJECT_DIR, "Product_Assets")
    if os.path.exists(local_assets):
        search_dirs.append(local_assets)

    if not search_dirs:
        print("❌ Không tìm thấy thư mục lưu trữ video nào!")
        return

    updated_count = 0
    for target_dir in search_dirs:
        print(f"🔍 Đang quét các file video hoàn thành tại {target_dir}...")
        item_dirs = [d for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]
        
        for item_id in item_dirs:
            item_path = os.path.join(target_dir, item_id)
            mp4s = glob.glob(os.path.join(item_path, "*.mp4")) + glob.glob(os.path.join(item_path, "*.MP4"))
            
            if not mp4s:
                continue

            video_file_path = mp4s[0]
            print(f"📦 Mã SP {item_id} -> File video: {video_file_path}")

            payload = {
                "action": "update_status",
                "itemId": item_id,
                "status": "Đã tạo Video",
                "outputFile": video_file_path
            }

            req = urllib.request.Request(
                WEBHOOK_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "text/plain;charset=utf-8"}
            )

            try:
                with urllib.request.urlopen(req, context=ctx) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    print(f"  ✅ Đã ghi Cột 13 (Output File) cho mã {item_id}:", res_data.get("message", "Thành công"))
                    updated_count += 1
            except Exception as e:
                print(f"  ⚠️ Lỗi gửi Webhook cho mã {item_id}:", e)

    print(f"\n🎉 HOÀN TẤT! Đã đồng bộ đường dẫn Cột 13 (Output File) cho {updated_count} sản phẩm lên Google Sheet.")

if __name__ == "__main__":
    backfill_output_files()
