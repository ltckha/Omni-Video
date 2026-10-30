#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - chế độ hàng tiệm (anh Kha nói "làm" 30/10/2026 qua Phân tích · Xưởng video).
Video Flow cho giày tiệm Hiệu giày Hải Nancy, theo mã tiệm (vd JH8918N):
1. Tạo Product_Assets/<mã>/: ảnh từ NAS /Volumes/Media/HNC_Master/<mã>/ (chỉ ảnh), không có thì tải image_01… của tab SANPHAM.
2. info.json lấy tên / màu / chất liệu từ SANPHAM + cờ hang_tiem = true. KHÔNG tạo dòng src_omni (Video-Post nhận video qua SANPHAM).
3. Sau khi tải từ Flow, video để nguyên ~/Downloads/<mã>.mp4 cho luồng gom của HNC; thư mục tạm tự dọn khi video đã rời Downloads.

Dùng: python scripts/hang_tiem.py <mã> [<mã> …]    (HangTiem.command hỏi mã rồi chạy lệnh này)
"""

import glob
import json
import os
import shutil
import sys
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
HNC_MEDIA_DIR = "/Volumes/Media/HNC_Master"

# Sheet HNC_Control_Center, tab SANPHAM: tên cột kỹ thuật ở HÀNG 2 (hàng 1 là tên nhóm) — luật chung 4
SANPHAM_SHEET_ID = "1U0b6_aVJJ93i5-V1RV1jUsQ9dhLYCY9BcJMI7R6J2C0"
SANPHAM_TAB = "SANPHAM"
SANPHAM_HEADER_ROW = 2
SANPHAM_IMAGE_COLUMNS = [f"image_{i:02d}" for i in range(1, 11)]
INFO_FIELDS = ("product_color", "chat_lieu", "chat_lieu_de", "kieu_giay_tay", "gioi_tinh")

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def read_info(item_dir: str) -> Dict:
    try:
        with open(os.path.join(item_dir, "info.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write_info(item_dir: str, info: Dict) -> None:
    with open(os.path.join(item_dir, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


def is_hang_tiem(item_dir: str) -> bool:
    return bool(read_info(item_dir).get("hang_tiem"))


def sanpham_rows(values: List[List[str]], codes: List[str]) -> Dict[str, Dict[str, str]]:
    """Dòng SANPHAM theo product_code (tiêu đề ở hàng SANPHAM_HEADER_ROW)."""
    headers = [h.strip() for h in values[SANPHAM_HEADER_ROW - 1]]
    wanted = set(codes)
    found = {}
    for row in values[SANPHAM_HEADER_ROW:]:
        d = dict(zip(headers, row))
        code = d.get("product_code", "").strip()
        if code in wanted and code not in found:
            found[code] = d
    return found


def read_sanpham(codes: List[str]) -> Dict[str, Dict[str, str]]:
    from sheet_sync import get_gspread_client
    gc = get_gspread_client()
    if not gc:
        raise RuntimeError("Không kết nối được Google Sheets (Service Account).")
    values = gc.open_by_key(SANPHAM_SHEET_ID).worksheet(SANPHAM_TAB).get_all_values()
    return sanpham_rows(values, codes)


def nas_images(code: str, media_dir: str = HNC_MEDIA_DIR) -> List[str]:
    folder = os.path.join(media_dir, code)
    return sorted(f for f in glob.glob(os.path.join(folder, "*")) if f.lower().endswith(IMAGE_EXTS))


def download_web_images(code: str, row: Dict[str, str], item_dir: str) -> List[str]:
    from omni_env import google_ssl_context
    ctx = google_ssl_context()
    saved = []
    for i, col in enumerate(SANPHAM_IMAGE_COLUMNS, start=1):
        url = (row.get(col) or "").strip()
        if not url.startswith("http"):
            continue
        try:
            with urllib.request.urlopen(url, timeout=30, context=ctx) as resp:
                if not (resp.headers.get("Content-Type") or "").startswith("image/"):
                    continue
                data = resp.read()
        except Exception as e:
            print(f"  ⚠️ Không tải được {col}: {e}")
            continue
        path = os.path.join(item_dir, f"{code}_web_{i:02d}.jpg")
        with open(path, "wb") as f:
            f.write(data)
        saved.append(path)
    return saved


def build_info(code: str, row: Dict[str, str], old: Optional[Dict] = None) -> Dict:
    info = dict(old or {})
    info.pop("da_tai", None)  # chạy lại = làm lại video → hiện lại trong popup
    info.update({"itemId": code, "productName": (row.get("product_name") or code).strip(), "hang_tiem": True})
    for field in INFO_FIELDS:
        info[field] = (row.get(field) or "").strip()
    return info


def prepare(code: str, row: Dict[str, str], assets_dir: str = ASSETS_DIR, media_dir: str = HNC_MEDIA_DIR,
            downloads_dir: str = DOWNLOADS_DIR, fetch_web=download_web_images) -> Optional[str]:
    """Tạo / làm mới Product_Assets/<mã>/. Trả đường dẫn thư mục, hoặc None nếu mã không có ảnh."""
    item_dir = os.path.join(assets_dir, code)
    existed = os.path.isdir(item_dir)
    os.makedirs(item_dir, exist_ok=True)
    have = [f for f in glob.glob(os.path.join(item_dir, "*")) if f.lower().endswith(IMAGE_EXTS)
            and not os.path.basename(f).lower().startswith(("nu-", "nam-"))]
    if not have:
        for src in nas_images(code, media_dir):
            shutil.copy2(src, os.path.join(item_dir, os.path.basename(src)))
            have.append(src)
        if not have:
            have = fetch_web(code, row, item_dir)
    if not have:
        if not existed:
            shutil.rmtree(item_dir, ignore_errors=True)
        return None
    write_info(item_dir, build_info(code, row, read_info(item_dir)))
    if os.path.exists(os.path.join(downloads_dir, f"{code}.mp4")):
        print(f"  ⚠️ ~/Downloads/{code}.mp4 đang có sẵn — video mới sẽ bị Chrome đặt tên khác. Chờ HNC gom xong rồi hãy Tạo video.")
    return item_dir


def mark_downloaded(item_dir: str) -> None:
    info = read_info(item_dir)
    info["da_tai"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    write_info(item_dir, info)


def cleanup(assets_dir: str = ASSETS_DIR, downloads_dir: str = DOWNLOADS_DIR) -> List[str]:
    """Xoá thư mục hàng tiệm đã tải video và video đã rời ~/Downloads (HNC đã gom)."""
    removed = []
    if not os.path.isdir(assets_dir):
        return removed
    for code in sorted(os.listdir(assets_dir)):
        item_dir = os.path.join(assets_dir, code)
        info = read_info(item_dir) if os.path.isdir(item_dir) else {}
        if info.get("hang_tiem") and info.get("da_tai") and not os.path.exists(os.path.join(downloads_dir, f"{code}.mp4")):
            shutil.rmtree(item_dir, ignore_errors=True)
            removed.append(code)
    return removed


def main(argv: List[str]) -> int:
    codes = list(dict.fromkeys(c.strip().upper() for c in argv if c.strip() and not c.startswith("-")))
    for code in cleanup():
        print(f"🧹 Đã dọn Product_Assets/{code}/ (video đã được HNC gom).")
    if not codes:
        print(__doc__)
        return 1
    rows = read_sanpham(codes)
    ok = []
    for code in codes:
        row = rows.get(code)
        if not row:
            print(f"❌ {code}: không có trong tab SANPHAM — bỏ qua.")
            continue
        if prepare(code, row):
            ok.append(code)
            print(f"✅ {code}: {row.get('product_name', '').strip()}")
        else:
            print(f"❌ {code}: chưa có ảnh (NAS HNC_Master / image_01… trống) — bỏ qua.")
    print(f"\n📦 Sẵn sàng {len(ok)}/{len(codes)} mã. Bước tiếp: bấm Prompt.command, rồi Tạo video trên Flow.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))
