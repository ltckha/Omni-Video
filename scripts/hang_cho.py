#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - hàng chờ tự động hàng tiệm (anh Kha nói "làm" 30/10/2026 qua Phân tích · Xưởng video).
Giữ đúng SO_MA_CHO mã hàng tiệm đang chờ Tạo video trong Product_Assets, 0 Gemini:
1. Ổ Media (NAS) không cắm / ~/Downloads không đọc được / Sheet lỗi → không làm gì, ghi log, không xoá.
2. hang_tiem.cleanup: dọn mã đã tải video mà HNC đã gom (như HangTiem.command).
3. Đếm mã chờ do hàng chờ tạo (info.json "hang_cho": true, chưa tải video). Mã anh làm tay bằng HangTiem.command
   không tính, không đụng.
4. Thiếu thì lấy thêm từ tab SANPHAM (tiêu đề hàng 2): mã chưa có video trước, MỚI NHẤT trước; hết mã mới thì lấy mã đã
   có video (ít video trước, tối đa TRAN_VIDEO / mã), mỗi lần 1 tổ hợp kiểu chuyển động × bối cảnh CHƯA dùng cho mã đó
   (anh Kha 30/10 "nhiều video ở nhiều bối cảnh"; HNC gom tự đổi tên <MÃ>_2.mp4…). "Mới nhất": tab không có cột ngày → lấy dòng dưới cùng
   trở lên (mã mới được thêm vào cuối tab). Điều kiện: web_in_stock khác "no" (tab chưa có
   cột này thì bỏ qua điều kiện); còn hàng trên web giayhainancy.vn (trang SP có trong sitemap.xml, dữ liệu sản phẩm
   schema.org "availability" = InStock; SANPHAM không có cột tồn kho, trang SP đã gỡ chuyển 301 về danh mục → coi như
   không bán, bỏ qua để không tốn credit); tên SP có loại giày (giày tây / lười / mọi / thể thao…) và có product_color;
   chưa có thư mục Product_Assets, chưa có ~/Downloads/<mã>.mp4; sổ data/.hang_cho_da_lam.json ghi từng lần (mã, kiểu, bối cảnh);
   có ảnh (NAS HNC_Master → web giayhainancy.vn → image_01… SANPHAM). Thiếu ảnh / thông tin → bỏ qua, ghi log.
5. Mỗi mã: kiểu liền, kiểu chuyển động × bối cảnh xoay vòng (hang_tiem.pick_combo), như HangTiem.command.

Chạy: launchd vn.giayhainancy.omni.hangcho 13:30 hằng ngày (sau HNC gom video 13:00), hoặc HangCho.command.
Nhật ký: data/logs/hang_cho.log
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hang_tiem
from hang_tiem import ASSETS_DIR, DOWNLOADS_DIR, HNC_MEDIA_DIR, SANPHAM_HEADER_ROW, SHOE_TYPES, read_info

SO_MA_CHO = 5
TRAN_VIDEO = 3  # tối đa 3 video / mã (Phân tích tạm đặt 30/10, chờ anh Kha duyệt)
SO_MA_THU_TOI_DA = 40  # mỗi lần chạy thử tối đa bấy nhiêu mã (tránh tải web quá nhiều khi nhiều mã thiếu ảnh)
LEDGER = os.path.join(hang_tiem.PROJECT_DIR, "data", ".hang_cho_da_lam.json")
LOG_PATH = os.path.join(hang_tiem.PROJECT_DIR, "data", "logs", "hang_cho.log")


WEB_SITEMAP = "https://giayhainancy.vn/sitemap.xml"
USER_AGENT = "OmniVideo/1.0 (Hieu giay Hai Nancy)"


def fetch_text(url: str) -> str:
    from omni_env import google_ssl_context  # certifi, như tải ảnh web (hang_tiem._fetch_image)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30, context=google_ssl_context()) as r:
        return r.read().decode("utf-8", "replace")


def web_product_urls(sitemap: str) -> Dict[str, str]:
    """Mã (chữ hoa) → link trang SP, từ sitemap web (link dạng …/product/<tên>-<mã>-<số>)."""
    out = {}
    for url in re.findall(r"<loc>([^<]*/product/[^<]*)</loc>", sitemap):
        m = re.search(r"(?:/|-)([a-z0-9]+)-\d+/?$", url.lower())
        if m:
            out.setdefault(m.group(1).upper(), url)
    return out


def web_stock(code: str, urls: Dict[str, str], fetch=fetch_text) -> Optional[str]:
    """None = còn hàng; chuỗi = lý do bỏ qua."""
    url = urls.get(code)
    if not url:
        return "không có trang SP trên web (đã gỡ / chưa đăng)"
    try:
        page = fetch(url)
    except (urllib.error.URLError, OSError) as e:
        return f"lỗi mở trang SP ({e.__class__.__name__})"
    m = re.search(r'"availability"\s*:\s*"(?:https?://schema\.org/)?(\w+)"', page)
    if not m:
        return "trang SP không ghi tình trạng hàng"
    return None if m.group(1) == "InStock" else f"web ghi {m.group(1)}"


def log(msg: str, path: Optional[str] = None) -> None:
    path = path or LOG_PATH
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} {msg}"
    print(line)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_ledger(path: Optional[str] = None) -> List[Dict]:
    """Sổ đã đưa vào hàng chờ: mỗi lần 1 dòng {ma, chuyen_dong, boi_canh} (sổ cũ 30/10 chỉ có mã)."""
    try:
        with open(path or LEDGER, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    return [{"ma": e} if isinstance(e, str) else e for e in data]


def save_ledger(codes: List[Dict], path: Optional[str] = None) -> None:
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
    """Lý do bỏ qua 1 dòng SANPHAM theo thông tin trên Sheet; None = đủ điều kiện (đã có video vẫn được, xem run)."""
    if row.get("web_in_stock", "").strip().lower() == "no":
        return "web hết hàng"
    name = row.get("product_name", "").lower()
    if not any(t in name for t in SHOE_TYPES if t != "giày"):
        return "tên không có loại giày"
    if not row.get("product_color", "").strip():
        return "thiếu màu"
    return None


def video_count(row: Dict[str, str], ledger: List[Dict]) -> int:
    """Số video mã đã có: số lần vào hàng chờ; chưa vào lần nào mà Sheet ghi VIDEO (làm tay / quay thật) = 1."""
    n = sum(1 for e in ledger if e.get("ma") == row["product_code"])
    return n or (1 if "VIDEO" in row.get("content_files", "").upper() else 0)


def ordered(rows: List[Dict[str, str]], ledger: List[Dict]) -> List[Dict[str, str]]:
    """Mã chưa có video trước (mới nhất trước); rồi mã đã có video, ít video trước (cùng số thì mới nhất trước)."""
    counts = {r["product_code"]: video_count(r, ledger) for r in rows}
    return sorted(rows, key=lambda r: counts[r["product_code"]])  # sort ổn định → giữ thứ tự mới nhất trong cùng số


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


def run(values_fn=hang_tiem.read_sanpham_values, make=hang_tiem.make_item, fetch=fetch_text, assets_dir: str = ASSETS_DIR,
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
    try:
        web_urls = web_product_urls(fetch(WEB_SITEMAP))
    except (urllib.error.URLError, OSError) as e:
        log_fn(f"⏸ Lỗi đọc sitemap web ({e.__class__.__name__}) — không kiểm được còn hàng, không làm gì.")
        return []
    for code in hang_tiem.cleanup(assets_dir, downloads_dir):
        log_fn(f"🧹 Dọn {code} (HNC đã gom video).")
    waiting = pending_codes(assets_dir)
    need = SO_MA_CHO - len(waiting)
    if need <= 0:
        log_fn(f"✅ Đủ {len(waiting)} mã chờ: {', '.join(waiting)}")
        return []
    done = load_ledger(ledger_path)
    cfg = hang_tiem.load_config()
    added, tried = [], 0
    for row in ordered(candidates(values), done):
        if len(added) >= need or tried >= SO_MA_THU_TOI_DA:
            break
        code = row["product_code"]
        if os.path.exists(os.path.join(assets_dir, code)) or os.path.exists(os.path.join(downloads_dir, f"{code}.mp4")):
            continue
        if video_count(row, done) >= TRAN_VIDEO or why_not(row):
            continue  # lý do trên Sheet: không ghi log từng dòng (hàng nghìn dòng)
        used = [(e["chuyen_dong"], e["boi_canh"]) for e in done if e.get("ma") == code and e.get("boi_canh")]
        info = hang_tiem.build_info(code, row)
        if not [c for c in hang_tiem.combos_for(info, cfg) if c not in used]:
            continue  # đã dùng hết kiểu × bối cảnh cho mã này
        tried += 1
        stock = web_stock(code, web_urls, fetch)
        if stock:
            log_fn(f"⏭ {code}: {stock} — bỏ qua.")
            continue
        item_dir = make(code, row, True, {"hang_cho": True}, used=used, assets_dir=assets_dir, media_dir=media_dir,
                        downloads_dir=downloads_dir)
        if item_dir:
            got = read_info(item_dir)
            added.append(code)
            done.append({"ma": code, "chuyen_dong": got.get("chuyen_dong"), "boi_canh": got.get("boi_canh"),
                         "ngay": datetime.now().strftime("%Y-%m-%d")})
            save_ledger(done, ledger_path)
            log_fn(f"➕ {code} · {got.get('chuyen_dong')} · {got.get('boi_canh')} (video thứ {len(used) + 1}): "
                   f"{row.get('product_name', '').strip()}")
        else:
            log_fn(f"⏭ {code}: không có ảnh (NAS / web / image_01…) — bỏ qua.")
    waiting = pending_codes(assets_dir)
    log_fn(f"📦 Thêm {len(added)} mã. Đang chờ {len(waiting)}/{SO_MA_CHO}: {', '.join(waiting)}")
    return added


if __name__ == "__main__":
    run()
