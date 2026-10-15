#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - Google Flow helper (bán tự động, anh Kha tự bấm Tạo / Tải trên Flow).
1. list_pending_items(): sản phẩm đã có prompt <itemId>.txt nhưng chưa có <itemId>.mp4.
2. prepare_flow_bundle(): copy 3 file (ảnh người mẫu, ảnh sản phẩm, kịch bản .txt) vào
   ~/Downloads/Omni-Flow/<itemId>/ để kéo thả vào công cụ Omni-Studio Pro trên Flow.
3. collect_flow_video(): video tải về ~/Downloads/<itemId>.mp4 -> Product_Assets/<itemId>/<itemId>.mp4.
Không gọi API, không đụng Google Sheet (Move.command cập nhật Sheet như cũ).
"""

import os
import json
import glob
import base64
import shutil
from typing import Optional, List, Dict

from generate_omni_video import find_prompt_file, find_character_image, get_image_mime_type

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
FLOW_STAGING_DIR = os.path.join(DOWNLOADS_DIR, "Omni-Flow")


def _product_title(item_dir: str) -> str:
    info_path = os.path.join(item_dir, "info.json")
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
        return str(info.get("productName") or info.get("title") or "").strip()
    except Exception:
        return ""


def find_best_product_image(item_dir: str) -> Optional[str]:
    """Ảnh sản phẩm lớn nhất (nét nhất) trong thư mục, bỏ ảnh nhân vật."""
    candidates = []
    for ext in ("*.webp", "*.jpg", "*.jpeg", "*.png"):
        for f in glob.glob(os.path.join(item_dir, ext)):
            fname = os.path.basename(f).lower()
            if not fname.startswith("nu-") and not fname.startswith("nam-") and "character" not in fname:
                candidates.append(f)
    return max(candidates, key=os.path.getsize) if candidates else None


def get_flow_assets(item_id: str, assets_dir: str = ASSETS_DIR) -> Dict[str, str]:
    """Đường dẫn 3 file cho Omni-Studio Pro: character / product / script. Thiếu file nào thì báo lỗi."""
    item_dir = os.path.join(assets_dir, item_id)
    if not os.path.isdir(item_dir):
        raise FileNotFoundError(f"Không có thư mục Product_Assets/{item_id}")
    assets = {
        "character": find_character_image(item_dir),
        "product": find_best_product_image(item_dir),
        "script": find_prompt_file(item_dir, item_id),
    }
    labels = {"script": "kịch bản .txt", "product": "ảnh sản phẩm", "character": "ảnh người mẫu"}
    missing = [labels[k] for k in ("script", "product", "character") if not assets[k]]
    if missing:
        raise FileNotFoundError(f"Mã {item_id} thiếu: {', '.join(missing)}")
    return assets


def encode_flow_files(item_id: str, assets_dir: str = ASSETS_DIR, chunk_size: int = 700_000) -> List[Dict]:
    """Native messaging giới hạn 1 MB/tin -> mã base64 rồi chia nhỏ. Trả danh sách tin: 1 tin meta + các tin chunk."""
    assets = get_flow_assets(item_id, assets_dir)
    files, chunks = [], []
    for slot, path in assets.items():
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        parts = [b64[i:i + chunk_size] for i in range(0, len(b64), chunk_size)] or [""]
        mime = "text/plain" if slot == "script" else get_image_mime_type(path)
        name = f"{item_id}.txt" if slot == "script" else os.path.basename(path)
        files.append({"slot": slot, "name": name, "mime": mime, "chunks": len(parts)})
        chunks += [{"type": "chunk", "slot": slot, "index": i, "data": part} for i, part in enumerate(parts)]
    return [{"type": "meta", "itemId": item_id, "files": files}] + chunks


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
        items.append({"itemId": item_id, "title": _product_title(item_dir), "mtime": os.path.getmtime(item_dir)})
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return [{"itemId": i["itemId"], "title": i["title"]} for i in items]


def prepare_flow_bundle(item_id: str, assets_dir: str = ASSETS_DIR, staging_root: str = FLOW_STAGING_DIR) -> str:
    """Copy ảnh người mẫu / ảnh SP / kịch bản vào thư mục tạm, đánh số theo thứ tự ô trong Omni-Studio Pro."""
    assets = get_flow_assets(item_id, assets_dir)
    character, product, prompt = assets["character"], assets["product"], assets["script"]

    bundle_dir = os.path.join(staging_root, item_id)
    if os.path.isdir(bundle_dir):
        shutil.rmtree(bundle_dir)
    os.makedirs(bundle_dir)
    shutil.copy2(character, os.path.join(bundle_dir, f"1_nguoi_mau_{os.path.basename(character)}"))
    shutil.copy2(product, os.path.join(bundle_dir, f"2_san_pham_{os.path.basename(product)}"))
    shutil.copy2(prompt, os.path.join(bundle_dir, f"3_kich_ban_{item_id}.txt"))
    return bundle_dir


def collect_flow_video(item_id: str, assets_dir: str = ASSETS_DIR, downloads_dir: str = DOWNLOADS_DIR,
                       staging_root: str = FLOW_STAGING_DIR) -> Optional[str]:
    """Chuyển ~/Downloads/<itemId>.mp4 vào Product_Assets/<itemId>/<itemId>.mp4 và xoá thư mục tạm."""
    src = os.path.join(downloads_dir, f"{item_id}.mp4")
    item_dir = os.path.join(assets_dir, item_id)
    if not os.path.isfile(src) or not os.path.isdir(item_dir):
        return None
    dst = os.path.join(item_dir, f"{item_id}.mp4")
    if os.path.exists(dst):
        raise FileExistsError(f"Product_Assets/{item_id}/{item_id}.mp4 đã có — không ghi đè")
    shutil.move(src, dst)
    shutil.rmtree(os.path.join(staging_root, item_id), ignore_errors=True)
    return dst
