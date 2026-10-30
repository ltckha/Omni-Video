#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - hàng chờ tự động hàng tiệm (anh Kha nói "làm" 30/10/2026 qua Phân tích · Xưởng video).
Giữ đúng SO_MA_CHO mã hàng tiệm đang chờ Tạo video trong Product_Assets, 0 Gemini:
1. Ổ Media (NAS) không cắm / ~/Downloads không đọc được / Sheet lỗi → không làm gì, ghi log, không xoá.
2. hang_tiem.cleanup: dọn mã đã tải video mà HNC đã gom (như HangTiem.command).
3. Đếm mã chờ do hàng chờ tạo (info.json "hang_cho": true, chưa tải video). Mã anh làm tay bằng HangTiem.command
   không tính, không đụng.
4. Thiếu thì lấy thêm từ tab SANPHAM (tiêu đề hàng 2), MỚI NHẤT trước: tab không có cột ngày → lấy dòng dưới cùng
   trở lên (mã mới được thêm vào cuối tab). Điều kiện: content_files chưa có VIDEO; web_in_stock khác "no" (tab chưa có
   cột này thì bỏ qua điều kiện); tên SP có loại giày (giày tây / lười / mọi / thể thao…) và có product_color;
   chưa có thư mục Product_Assets, chưa có ~/Downloads/<mã>.mp4, chưa từng vào hàng chờ (data/.hang_cho_da_lam.json);
   có ảnh (NAS HNC_Master → web giayhainancy.vn → image_01… SANPHAM). Thiếu ảnh / thông tin → bỏ qua, ghi log.
5. Mỗi mã: kiểu mặc định (liền) + bối cảnh xoay vòng, như HangTiem.command.

Chạy: launchd vn.giayhainancy.omni.hangcho 13:30 hằng ngày (sau HNC gom video 13:00), hoặc HangCho.command.
Nhật ký: data/logs/hang_cho.log
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hang_tiem
from hang_tiem import ASSETS_DIR, DOWNLOADS_DIR, HNC_MEDIA_DIR, SANPHAM_HEADER_ROW, SHOE_TYPES, read_info

SO_MA_CHO = 5
SO_MA_THU_TOI_DA = 40  # mỗi lần chạy thử tối đa bấy nhiêu mã (tránh tải web quá nhiều khi nhiều mã thiếu ảnh)
LEDGER = os.path.join(hang_tiem.PROJECT_DIR, "data", ".hang_cho_da_lam.json")
LOG_PATH = os.path.join(hang_tiem.PROJECT_DIR, "data", "logs", "hang_cho.log")


def log(msg: str, path: Optional[str] = None) -> None:
    path = path or LOG_PATH
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} {msg}"
    print(line)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_ledger(path: Optional[str] = None) -> List[str]:
    try:
        with open(path or LEDGER, "r", encoding="utf-8") as f:
            return list(json.load(f))
    except (OSError, ValueError):
        return []


def save_ledger(codes: List[str], path: Optional[str] = None) -> None:
    path = path or LEDGER
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(codes, f, ensure_ascii=False, indent=1)


def pending_codes(assets_dir: str = ASSETS_DIR) -> List[str]:
    """Mã hàng chờ đang chờ Tạo video (chưa tải video)."""
    out = []
    if not os.path.isdir(assets_dir):
        return out
    for code in sorted(os.listdir(assets_dir)):
        info = read_info(os.path.join(assets_dir, code)) if os.path.isdir(os.path.join(assets_dir, code)) else {}
        if info.get("hang_cho") and not info.get("da_tai"):
            out.append(code)
    return out


def why_not(row: Dict[str, str]) -> Optional[str]:
    """Lý do bỏ qua 1 dòng SANPHAM theo thông tin trên Sheet; None = đủ điều kiện."""
    if "VIDEO" in row.get("content_files", "").upper():
        return "đã có video"
    if row.get("web_in_stock", "").strip().lower() == "no":
        return "web hết hàng"
    name = row.get("product_name", "").lower()
    if not any(t in name for t in SHOE_TYPES if t != "giày"):
        return "tên không có loại giày"
    if not row.get("product_color", "").strip():
        return "thiếu màu"
    return None


def candidates(values: List[List[str]]) -> List[Dict[str, str]]:
    """Dòng SANPHAM mới nhất trước (dòng dưới cùng lên trên; tab không có cột ngày)."""
    headers = [h.strip() for h in values[SANPHAM_HEADER_ROW - 1]]
    rows, seen = [], set()
    for raw in reversed(values[SANPHAM_HEADER_ROW:]):
        row = dict(zip(headers, raw))
        code = row.get("product_code", "").strip().upper()
        if code and code not in seen:
            seen.add(code)
            rows.append(dict(row, product_code=code))
    return rows


def run(values_fn=hang_tiem.read_sanpham_values, make=hang_tiem.make_item, assets_dir: str = ASSETS_DIR,
        downloads_dir: str = DOWNLOADS_DIR, media_dir: str = HNC_MEDIA_DIR, ledger_path: Optional[str] = None,
        log_fn=log) -> List[str]:
    if not os.path.isdir(media_dir):
        log_fn(f"⏸ Không thấy {media_dir} (ổ Media chưa cắm?) — không làm gì.")
        return []
    try:
        os.listdir(downloads_dir)
    except OSError as e:
        log_fn(f"⏸ Không đọc được {downloads_dir} ({e.__class__.__name__}) — không dọn, không thêm.")
        return []
    try:
        values = values_fn()
    except Exception as e:  # Sheet lỗi / mất mạng
        log_fn(f"⏸ Lỗi đọc tab SANPHAM ({e.__class__.__name__}: {e}) — không làm gì.")
        return []
    for code in hang_tiem.cleanup(assets_dir, downloads_dir):
        log_fn(f"🧹 Dọn {code} (HNC đã gom video).")
    waiting = pending_codes(assets_dir)
    need = SO_MA_CHO - len(waiting)
    if need <= 0:
        log_fn(f"✅ Đủ {len(waiting)} mã chờ: {', '.join(waiting)}")
        return []
    done = load_ledger(ledger_path)
    added, tried = [], 0
    for row in candidates(values):
        if len(added) >= need or tried >= SO_MA_THU_TOI_DA:
            break
        code = row["product_code"]
        if code in done or os.path.exists(os.path.join(assets_dir, code)) \
                or os.path.exists(os.path.join(downloads_dir, f"{code}.mp4")):
            continue
        reason = why_not(row)
        if reason:
            continue  # lý do trên Sheet: không ghi log từng dòng (hàng nghìn dòng)
        tried += 1
        if make(code, row, True, {"hang_cho": True}, assets_dir=assets_dir, media_dir=media_dir,
                downloads_dir=downloads_dir):
            added.append(code)
            done.append(code)
            save_ledger(done, ledger_path)
            log_fn(f"➕ {code}: {row.get('product_name', '').strip()}")
        else:
            log_fn(f"⏭ {code}: không có ảnh (NAS / web / image_01…) — bỏ qua.")
    waiting = pending_codes(assets_dir)
    log_fn(f"📦 Thêm {len(added)} mã. Đang chờ {len(waiting)}/{SO_MA_CHO}: {', '.join(waiting)}")
    return added


if __name__ == "__main__":
    run()
