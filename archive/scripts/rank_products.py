#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - P3 (anh Kha 17/10/2026): gợi ý nên làm video sản phẩm nào trước, xếp theo
hoa hồng (đ) × lượt bán. Chỉ đọc tab src_omni theo tên cột, 0 Gemini.
Hoa hồng (đ) lấy cột `commission`; trống thì = giá × `commission_rate`.

Dùng: python scripts/rank_products.py [--all] [--top N]
  mặc định: chỉ sản phẩm chưa có video; --all: mọi dòng.
"""

import re
import sys
from typing import Dict, List, Optional


def parse_money(text: str) -> Optional[float]:
    """'₫22.196' -> 22196; '116,8k' -> 116800; '₫99.000 - ₫120.000' -> 99000."""
    s = str(text or "").strip().lower().split("-")[0].replace("₫", "").replace("đ", "").replace(" ", "")
    if not s:
        return None
    mult = 1
    if s.endswith("k"):
        mult, s = 1_000, s[:-1].replace(",", ".")
    elif s.endswith("tr"):
        mult, s = 1_000_000, s[:-2].replace(",", ".")
    else:
        s = s.replace(".", "").replace(",", "")
    try:
        return float(s) * mult
    except ValueError:
        return None


def parse_count(text: str) -> Optional[float]:
    """'70k+' -> 70000; '1,2k' -> 1200; '2tr' -> 2000000; '350' -> 350."""
    s = str(text or "").strip().lower().replace("+", "").replace(" ", "")
    m = re.match(r"^([\d.,]+)(k|tr)?$", s)
    if not m:
        return None
    num, unit = m.group(1), m.group(2)
    num = num.replace(",", ".") if unit else num.replace(".", "").replace(",", "")
    try:
        return float(num) * {"k": 1_000, "tr": 1_000_000}.get(unit, 1)
    except ValueError:
        return None


def parse_rate(text: str) -> Optional[float]:
    m = re.search(r"([\d.,]+)\s*%", str(text or ""))
    return float(m.group(1).replace(",", ".")) / 100 if m else None


def score_row(row: Dict[str, str]) -> Optional[float]:
    commission = parse_money(row.get("commission", ""))
    if commission is None:
        price, rate = parse_money(row.get("price", "")), parse_rate(row.get("commission_rate", ""))
        commission = price * rate if price is not None and rate is not None else None
    sold = parse_count(row.get("sales_count", ""))
    return commission * sold if commission is not None and sold is not None else None


def rank(values: List[List[str]], only_without_video: bool = True) -> Dict[str, list]:
    if not values:
        return {"ranked": [], "missing": []}
    headers = [str(h).strip().lower() for h in values[0]]
    ranked, missing = [], []
    for row in values[1:]:
        rec = {h: (str(row[i]).strip() if i < len(row) else "") for i, h in enumerate(headers)}
        if not rec.get("job_id"):
            continue
        if only_without_video and (rec.get("video_path") or rec.get("status") == "Đã tạo Video"):
            continue
        s = score_row(rec)
        (ranked if s is not None else missing).append((s, rec))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return {"ranked": ranked, "missing": [r for _, r in missing]}


def main() -> int:
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from sheet_sync import get_gspread_client, get_omni_worksheet, SPREADSHEET_ID
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 15
    only_new = "--all" not in sys.argv
    gc = get_gspread_client()
    if not gc:
        print("❌ Không kết nối được Google Sheet.")
        return 1
    result = rank(get_omni_worksheet(gc.open_by_key(SPREADSHEET_ID)).get_all_values(), only_without_video=only_new)
    scope = "chưa có video" if only_new else "mọi dòng"
    print(f"💰 Gợi ý làm video ({scope}) — xếp theo hoa hồng (đ) × lượt bán:")
    if not result["ranked"]:
        print("   (chưa có sản phẩm nào đủ giá / hoa hồng / lượt bán)")
    for i, (s, r) in enumerate(result["ranked"][:top], start=1):
        print(f"  {i:>2}. {r['job_id']} · {s:,.0f} · {r.get('commission') or r.get('commission_rate', '')} × {r.get('sales_count', '')} · {r.get('title', '')[:50]}")
    if result["missing"]:
        print(f"   ℹ️ {len(result['missing'])} sản phẩm thiếu giá / hoa hồng / lượt bán (chưa xếp được).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
