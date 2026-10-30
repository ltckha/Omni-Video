#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - Google Flow helper (bán tự động, anh Kha tự bấm Tạo / Tải trên Flow).
1. list_pending_items(): sản phẩm đã có prompt <itemId>.txt nhưng chưa có <itemId>.mp4.
2. encode_flow_files(): 3 file (ảnh SP, ảnh người mẫu, kịch bản .txt) gửi cho extension dán vào Flow.
3. collect_flow_video(): video tải về ~/Downloads/<itemId>.mp4 -> Product_Assets/<itemId>/<itemId>.mp4
   (hàng tiệm: để nguyên ở ~/Downloads cho luồng gom HNC, chỉ đánh dấu đã tải).
Không gọi API, không đụng Google Sheet (Move.command cập nhật Sheet như cũ).
"""

import os
import json
import glob
import base64
import shutil
import subprocess
import tempfile
from typing import Optional, List, Dict

from hang_tiem import read_info, mark_downloaded, output_name


PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHARACTERS_DIR = os.path.join(PROJECT_DIR, "characters")
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")


def get_image_mime_type(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    return {".webp": "image/webp", ".png": "image/png"}.get(ext, "image/jpeg")


def find_prompt_file(item_dir: str, item_id: str) -> Optional[str]:
    """<itemId>.txt, hoặc master_prompt.txt (cũ), hoặc file .txt bất kỳ (trừ prompt_backups)."""
    for name in (f"{item_id}.txt", "master_prompt.txt"):
        path = os.path.join(item_dir, name)
        if os.path.exists(path):
            return path
    txts = [f for f in glob.glob(os.path.join(item_dir, "*.txt")) if "prompt_backups" not in f]
    return txts[0] if txts else None


def find_character_image(item_dir: str) -> Optional[str]:
    """Ảnh nhân vật (Nu-* / Nam-* / *character*) trong thư mục SP, không có thì lấy ảnh đầu trong characters/."""
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        for f in glob.glob(os.path.join(item_dir, ext)):
            name = os.path.basename(f).lower()
            if (name.startswith("nu-") or name.startswith("nam-") or "character" in name) and "_tren" not in name:
                return f
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        chars = sorted(glob.glob(os.path.join(CHARACTERS_DIR, ext)))
        if chars:
            return chars[0]
    return None


def _product_title(item_dir: str) -> str:
    info_path = os.path.join(item_dir, "info.json")
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
        title = str(info.get("productName") or info.get("title") or "").strip()
        if info.get("hang_tiem"):  # anh biết đang tạo bản nào: "· tien_vao · sảnh khách sạn · <tên>"
            from hang_tiem import popup_label
            title = f"· {popup_label(info)} · {title}"
        return title
    except Exception:
        return ""


def find_product_images(item_dir: str) -> List[str]:
    """Mọi ảnh sản phẩm trong thư mục (bỏ ảnh nhân vật), lớn nhất (nét nhất) trước."""
    candidates = []
    for ext in ("*.webp", "*.jpg", "*.jpeg", "*.png"):
        for f in glob.glob(os.path.join(item_dir, ext)):
            fname = os.path.basename(f).lower()
            if not fname.startswith("nu-") and not fname.startswith("nam-") and "character" not in fname:
                candidates.append(f)
    return sorted(candidates, key=os.path.getsize, reverse=True)


def find_best_product_image(item_dir: str) -> Optional[str]:
    """Ảnh sản phẩm lớn nhất (nét nhất) trong thư mục, bỏ ảnh nhân vật."""
    images = find_product_images(item_dir)
    return images[0] if images else None


def get_flow_assets(item_id: str, assets_dir: str = ASSETS_DIR) -> Dict[str, str]:
    """Đường dẫn 3 file cho Omni-Studio Pro: character / product / script. Thiếu file nào thì báo lỗi."""
    item_dir = os.path.join(assets_dir, item_id)
    if not os.path.isdir(item_dir):
        raise FileNotFoundError(f"Không có thư mục Product_Assets/{item_id}")
    products = find_product_images(item_dir)
    assets = {
        "character": find_character_image(item_dir),
        "product": products[0] if products else None,
        "script": find_prompt_file(item_dir, item_id),
    }
    labels = {"script": "kịch bản .txt", "product": "ảnh sản phẩm", "character": "ảnh người mẫu"}
    missing = [labels[k] for k in ("script", "product", "character") if not assets[k]]
    if missing:
        raise FileNotFoundError(f"Mã {item_id} thiếu: {', '.join(missing)}")
    return assets


MAX_FLOW_IMAGES = 7  # Flow nhận tối đa 7 ảnh tham chiếu
PASTE_MAX_BYTES = 2_000_000  # Flow không nhận ảnh dán vào khi quá nặng (ảnh người mẫu PNG ~7 MB bị từ chối)


def shrink_for_paste(path: str, max_bytes: int = PASTE_MAX_BYTES) -> bytes:
    """Ảnh > max_bytes -> JPEG cạnh dài 2048 px, chất lượng 90 bằng `sips` có sẵn của macOS (không cần cài thêm)."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) <= max_bytes:
        return data
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "shrunk.jpg")
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90", "-Z", "2048", path, "--out", out],
                       check=True, capture_output=True)
        with open(out, "rb") as f:
            return f.read()


def encode_flow_files(item_id: str, assets_dir: str = ASSETS_DIR, chunk_size: int = 700_000) -> List[Dict]:
    """Native messaging giới hạn 1 MB/tin -> mã base64 rồi chia nhỏ. Trả danh sách tin: 1 tin meta + các tin chunk."""
    item_dir = os.path.join(assets_dir, item_id)
    info = read_info(item_dir)
    if info.get("kieu") == "lien" and info.get("anh_lien"):
        # hàng tiệm kiểu liền: ảnh giày đủ góc (thẳng → 3/4 → góc khác → đế) → người mẫu cắt từ thắt lưng → kịch bản
        ordered = [("product" if i == 1 else f"product_{i}", os.path.join(item_dir, name))
                   for i, name in enumerate(info["anh_lien"], start=1)]
        if info.get("nguoi_mau_lien"):
            ordered.append(("character", os.path.join(item_dir, info["nguoi_mau_lien"])))
        ordered.append(("script", find_prompt_file(item_dir, item_id)))
        return _encode(item_id, ordered, chunk_size)
    assets = get_flow_assets(item_id, assets_dir)
    # Thứ tự dán = thứ tự Input Image trên Flow: 1 = ảnh SP chính, 2 = người mẫu (khớp kịch bản), 3.. = ảnh SP còn lại
    extras = find_product_images(os.path.join(assets_dir, item_id))[1:MAX_FLOW_IMAGES - 1]
    ordered = [("product", assets["product"]), ("character", assets["character"])]
    ordered += [(f"product_{i}", path) for i, path in enumerate(extras, start=2)]
    ordered.append(("script", assets["script"]))
    return _encode(item_id, ordered, chunk_size)


def _encode(item_id: str, ordered: List, chunk_size: int) -> List[Dict]:
    output = output_name(read_info(os.path.dirname(ordered[-1][1])), item_id)  # ordered[-1] = kịch bản trong thư mục SP
    files, chunks = [], []
    for slot, path in ordered:
        if slot == "script":
            with open(path, "rb") as f:
                data = f.read()
            mime, name = "text/plain", f"{item_id}.txt"
        else:
            data = shrink_for_paste(path)
            shrunk = data[:3] == b"\xff\xd8\xff" and not path.lower().endswith((".jpg", ".jpeg"))
            mime = "image/jpeg" if shrunk else get_image_mime_type(path)
            name = os.path.splitext(os.path.basename(path))[0] + ".jpg" if shrunk else os.path.basename(path)
        b64 = base64.b64encode(data).decode("ascii")
        parts = [b64[i:i + chunk_size] for i in range(0, len(b64), chunk_size)] or [""]
        files.append({"slot": slot, "name": name, "mime": mime, "chunks": len(parts)})
        chunks += [{"type": "chunk", "slot": slot, "index": i, "data": part} for i, part in enumerate(parts)]
    return [{"type": "meta", "itemId": item_id, "output": output, "files": files}] + chunks


def list_pending_items(assets_dir: str = ASSETS_DIR) -> List[Dict[str, str]]:
    """Sản phẩm có prompt nhưng chưa có video, mới nhất trước."""
    items = []
    if not os.path.isdir(assets_dir):
        return items
    for item_id in os.listdir(assets_dir):
        item_dir = os.path.join(assets_dir, item_id)
        if not os.path.isdir(item_dir):
            continue
        if not find_prompt_file(item_dir, item_id):
            continue
        if glob.glob(os.path.join(item_dir, "*.mp4")) or glob.glob(os.path.join(item_dir, "*.MP4")):
            continue
        if read_info(item_dir).get("da_tai"):  # hàng tiệm đã tải video, chờ HNC gom
            continue
        items.append({"itemId": item_id, "title": _product_title(item_dir), "mtime": os.path.getmtime(item_dir)})
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return [{"itemId": i["itemId"], "title": i["title"]} for i in items]


def collect_flow_video(item_id: str, assets_dir: str = ASSETS_DIR, downloads_dir: str = DOWNLOADS_DIR) -> Optional[str]:
    """Chuyển ~/Downloads/<itemId>.mp4 vào Product_Assets/<itemId>/<itemId>.mp4.
    Hàng tiệm: tên tải về là info.json "ten_video" (<MÃ>.mp4 / <MÃ>_2.mp4…); không chuyển — để nguyên cho luồng gom HNC,
    ghi da_tai vào info.json, trả đường dẫn ở Downloads."""
    item_dir = os.path.join(assets_dir, item_id)
    src = os.path.join(downloads_dir, output_name(read_info(item_dir), item_id) if os.path.isdir(item_dir) else f"{item_id}.mp4")
    if not os.path.isfile(src) or not os.path.isdir(item_dir):
        return None
    if read_info(item_dir).get("hang_tiem"):
        mark_downloaded(item_dir)
        return src
    dst = os.path.join(item_dir, f"{item_id}.mp4")
    if os.path.exists(dst):
        raise FileExistsError(f"Product_Assets/{item_id}/{item_id}.mp4 đã có — không ghi đè")
    shutil.move(src, dst)
    return dst
