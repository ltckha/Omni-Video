#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - P6 (anh Kha 17/10/2026): 2–3 kịch bản / sản phẩm, mỗi bản 1 job_id riêng <itemId>-N.
- Mỗi bản = 1 thư mục Product_Assets/<itemId>-N/ (copy ảnh SP + info.json) → Flow / Move / Sheet dùng như SP thường
  (video <itemId>-N.mp4, NAS /Volumes/Media/Omni-Video/<itemId>-N/).
- Thêm dòng src_omni job_id = <itemId>-N (theo tên cột), rồi sinh kịch bản khác góc với bản gốc và các bản trước.
- Link tiếp thị: fill_aff_links lấy link của mã gốc khi chưa có link riêng.

Dùng: python scripts/make_variants.py <itemId> [--count 3] [--dry]
  --count: tổng số bản kể cả bản gốc (2 hoặc 3, mặc định 2). Mỗi bản mới tốn 1 lượt Gemini.
  --dry: chỉ báo sẽ làm gì (không tạo thư mục, không ghi Sheet, không gọi Gemini).
"""

import glob
import json
import os
import shutil
import sys
from typing import List

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
MAX_VARIANTS = 3


def is_character_image(name: str) -> bool:
    n = name.lower()
    return n.startswith("nu-") or n.startswith("nam-") or "character" in n


def product_images(item_dir: str) -> List[str]:
    files = []
    for ext in ("*.webp", "*.jpg", "*.jpeg", "*.png"):
        files += [f for f in glob.glob(os.path.join(item_dir, ext)) if not is_character_image(os.path.basename(f))]
    return sorted(files)


def variant_ids(item_id: str, count: int) -> List[str]:
    count = max(2, min(MAX_VARIANTS, count))
    return [f"{item_id}-{n}" for n in range(2, count + 1)]


def prepare_variant_dir(base_dir: str, variant_id: str, assets_dir: str = ASSETS_DIR) -> str:
    """Copy ảnh SP + info.json (đánh dấu variantOf, bỏ story_angle của bản gốc). Không copy kịch bản / video / ảnh nhân vật."""
    vdir = os.path.join(assets_dir, variant_id)
    os.makedirs(vdir, exist_ok=True)
    base_id = os.path.basename(base_dir)
    for f in product_images(base_dir):
        name = os.path.basename(f).replace(base_id, variant_id, 1) if os.path.basename(f).startswith(base_id) else os.path.basename(f)
        shutil.copy2(f, os.path.join(vdir, name))
    info_path = os.path.join(base_dir, "info.json")
    info = {}
    if os.path.exists(info_path):
        with open(info_path, encoding="utf-8") as fh:
            info = json.load(fh)
    info.pop("story_angle", None)
    info["variantOf"] = base_id
    with open(os.path.join(vdir, "info.json"), "w", encoding="utf-8") as fh:
        json.dump(info, fh, ensure_ascii=False, indent=2)
    return vdir


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    item_id = args[0].strip()
    count = int(sys.argv[sys.argv.index("--count") + 1]) if "--count" in sys.argv else 2
    dry = "--dry" in sys.argv
    base_dir = os.path.join(ASSETS_DIR, item_id)
    if not os.path.isdir(base_dir):
        print(f"❌ Không có thư mục Product_Assets/{item_id} (SP đã Move sang NAS thì chép lại thư mục về trước).")
        return 1
    if not product_images(base_dir):
        print(f"❌ Product_Assets/{item_id} không có ảnh sản phẩm.")
        return 1
    base_info = {}
    if os.path.exists(os.path.join(base_dir, "info.json")):
        with open(os.path.join(base_dir, "info.json"), encoding="utf-8") as fh:
            base_info = json.load(fh)
    used = [base_info["story_angle"]] if base_info.get("story_angle") else []
    todo = [v for v in variant_ids(item_id, count) if not os.path.exists(os.path.join(ASSETS_DIR, v, f"{v}.txt"))]
    print(f"🎭 {item_id}: sẽ tạo {len(todo)} bản kịch bản mới: {', '.join(todo) or '(đã đủ)'}")
    if dry or not todo:
        if todo:
            print("ℹ️ Chạy thử — chưa tạo thư mục, chưa ghi Sheet, chưa gọi Gemini. Bỏ --dry để làm thật.")
        return 0

    sys.path.insert(0, os.path.dirname(__file__))
    from sheet_sync import sync_product_to_sheet
    import generate_ugc_prompt as gen

    for vid in todo:
        vdir = prepare_variant_dir(base_dir, vid)
        with open(os.path.join(vdir, "info.json"), encoding="utf-8") as fh:
            vinfo = json.load(fh)
        if not sync_product_to_sheet(vinfo, vid):
            print(f"⚠️ {vid}: chưa thêm được dòng src_omni — dừng.")
            return 1
        angle = gen.generate_prompt_for_item(vid, vdir, exclude_angles=used)
        if not angle:
            print(f"⚠️ {vid}: chưa sinh được kịch bản (Gemini bận?) — chạy lại lệnh này sau.")
            return 1
        used.append(angle)
        print(f"✅ {vid}: góc {angle}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
