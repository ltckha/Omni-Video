#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - N18 (bản nháp, 23/10/2026): xếp sản phẩm trong file Product Offer của Shopee Affiliate
(CSV: Mã sản phẩm, Tên, Giá, Doanh thu / Đã bán, Tên cửa hàng, Tỉ lệ hoa hồng, Hoa hồng, Link sản phẩm, Link ưu đãi)
theo hoa hồng (đ) × lượt bán, đánh dấu SP đã có trong src_omni — để chọn món nên làm TRƯỚC khi Alt+S / Import.
Chỉ đọc (CSV + tab src_omni nếu có mạng), 0 Gemini, không ghi gì.

Dùng: python scripts/rank_offers.py <file.csv> [file2.csv …] [--top 20] [--offline]
"""

import csv
import os
import sys
from typing import Dict, List, Set

sys.path.insert(0, os.path.dirname(__file__))
from rank_products import score_row  # cùng công thức với bảng gợi ý trong Import.command

# tên cột Shopee (đã bỏ khoảng trắng, chữ thường) -> tên cột src_omni
COLUMN_MAP = {
    "mãsảnphẩm": "job_id", "itemid": "job_id",
    "tênsảnphẩm": "title",
    "giá": "price",
    "doanhthu": "sales_count", "đãbán": "sales_count", "lượtbán": "sales_count",
    "têncửahàng": "shop_name",
    "tỉlệhoahồng": "commission_rate", "tỷlệhoahồng": "commission_rate",
    "hoahồng": "commission",
    "linksảnphẩm": "product_url",
    "linkưuđãi": "shopee_link",
}


def norm(h: str) -> str:
    return "".join(str(h).lower().replace("﻿", "").split())


def read_offers(path: str) -> List[Dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return []
    cols = {i: COLUMN_MAP[norm(h)] for i, h in enumerate(rows[0]) if norm(h) in COLUMN_MAP}
    return [{cols[i]: v.strip() for i, v in enumerate(r) if i in cols} for r in rows[1:] if any(c.strip() for c in r)]


def rank_offers(offers: List[Dict[str, str]], existing_ids: Set[str]) -> List[Dict]:
    seen, out = set(), []
    for o in offers:
        jid = o.get("job_id", "")
        if not jid or jid in seen:
            continue
        seen.add(jid)
        out.append({**o, "score": score_row(o), "in_omni": jid in existing_ids})
    return sorted(out, key=lambda x: (x["score"] is None, -(x["score"] or 0)))


def existing_job_ids() -> Set[str]:
    from sheet_sync import get_gspread_client, get_omni_worksheet, SPREADSHEET_ID
    gc = get_gspread_client()
    if not gc:
        return set()
    values = get_omni_worksheet(gc.open_by_key(SPREADSHEET_ID)).get_all_values()
    i = [h.strip().lower() for h in values[0]].index("job_id")
    return {r[i].strip() for r in values[1:] if i < len(r)}


def main() -> int:
    files = [a for a in sys.argv[1:] if not a.startswith("--") and a.endswith(".csv")]
    if not files:
        print(__doc__)
        return 1
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 20
    offers = [o for f in files for o in read_offers(f)]
    existing = set() if "--offline" in sys.argv else existing_job_ids()
    ranked = rank_offers(offers, existing)
    print(f"💰 {len(ranked)} SP trong file — xếp theo hoa hồng (đ) × lượt bán (✔ = đã có trong src_omni):")
    for n, o in enumerate(ranked[:top], start=1):
        score = f"{o['score']:,.0f}" if o["score"] is not None else "?"
        print(f"  {n:>2}. {'✔' if o['in_omni'] else ' '} {o['job_id']} · {score} · {o.get('commission', '')} × {o.get('sales_count', '')} · {o.get('title', '')[:50]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
