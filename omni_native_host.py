#!/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
"""
Omni Video - Chrome Native Messaging Host (Super Robust File Sorter)
Tự động tìm mọi file ảnh bắt đầu bằng <itemId> trong ~/Downloads,
di chuyển vào /Users/khan/Developer/Omni-Video/Product_Assets/<itemId>/ rồi TẮT HOÀN TOÀN.
"""

import sys
import os
import json
import struct
import shutil
import glob
import time

DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
PROJECT_ASSETS_DIR = "/Users/khan/Developer/Omni-Video/Product_Assets"

def read_message():
    try:
        raw_length = sys.stdin.buffer.read(4)
        if not raw_length or len(raw_length) < 4:
            return None
        message_length = struct.unpack('@I', raw_length)[0]
        message = sys.stdin.buffer.read(message_length).decode('utf-8')
        return json.loads(message)
    except Exception:
        return None

def send_message(message):
    try:
        encoded = json.dumps(message).encode('utf-8')
        sys.stdout.buffer.write(struct.pack('@I', len(encoded)))
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
    except Exception:
        pass

def main():
    msg = read_message()
    if not msg:
        sys.exit(0)

    item_id = str(msg.get("itemId", "")).strip()
    filename = str(msg.get("filename", "")).strip()

    if item_id:
        target_dir = os.path.join(PROJECT_ASSETS_DIR, item_id)
        os.makedirs(target_dir, exist_ok=True)
        
        # Quét tìm tất cả file ảnh khớp với mã item_id trong ~/Downloads
        for attempt in range(40):
            # Tìm file chính xác hoặc file bắt đầu bằng item_id (trừ file tạm .crdownload)
            matching_files = [
                f for f in glob.glob(os.path.join(DOWNLOADS_DIR, f"{item_id}*"))
                if not f.endswith(".crdownload") and not f.endswith(".tmp")
            ]
            
            if matching_files:
                for src_path in matching_files:
                    f_name = os.path.basename(src_path)
                    target_path = os.path.join(target_dir, f_name)
                    try:
                        time.sleep(0.1) # Chờ ghi đĩa hoàn tất
                        shutil.move(src_path, target_path)
                        send_message({"status": "success", "movedTo": target_path})
                        sys.exit(0)
                    except Exception as e:
                        send_message({"status": "error", "message": str(e)})
                        sys.exit(0)
            
            time.sleep(0.25)

    send_message({"status": "error", "message": f"Không tìm thấy file của mã {item_id} trong Downloads"})
    sys.exit(0)

if __name__ == "__main__":
    main()
