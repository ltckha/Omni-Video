#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - Tự điền link tiếp thị liên kết (s.shopee.vn) cho tab src_omni từ bảng chung `aff_links` (AVF giữ).
Anh Kha chốt 15/10/2026 (kế hoạch Ecosystem-Hub/docs/ke_hoach/omni-video/2026-10-15_link_yenyen_tu_aff_links.md).

- Ghép chính xác: aff_links.aff_id == src_omni.job_id (đều là item_id Shopee), active = yes, link là s.shopee.vn.
- Chỉ ghi ô shopee_link đang trống hoặc chưa phải link s.shopee.vn. Không đè link s.shopee.vn đã có, không xoá gì.
- P3 (17/10): ô price / commission_rate / shop_name đang trống thì lấy từ aff_links (price / commission_rate / shop).
- Đọc/ghi theo tên cột hàng 1. Bảng aff_links trống thì không làm gì. 0 Gemini.

Dùng: python scripts/fill_aff_links.py            # chạy thử, chỉ báo số ô sẽ ghi
      python scripts/fill_aff_links.py --apply    # ghi thật (Import.command gọi ở cuối)
"""

import re
import sys
import logging
from typing import Dict, List, Tuple

import gspread

from sheet_sync import get_gspread_client, get_omni_worksheet, SPREADSHEET_ID

logger = logging.getLogger(__name__)

AFF_LINKS_TAB = "aff_links"
AFFILIATE_HOST = "s.shopee.vn"
ACTIVE_VALUES = {"yes", "y", "true", "1", "có", "x"}


def base_item_id(job_id: str) -> str:
    """P6: job_id <itemId>-N (bản kịch bản thứ N) dùng link / thông tin của mã gốc khi chưa có riêng."""
    return re.sub(r"-\d+$", "", str(job_id or "").strip())


def is_affiliate_link(link: str) -> bool:
    return AFFILIATE_HOST in str(link or "").lower()


def load_aff_links(values: List[List[str]]) -> Dict[Tuple[str, str], str]:
    """(aff_id, sub_id) -> link, chỉ dòng active và link s.shopee.vn. Tab chưa có cột sub_id thì sub_id = "".
    AVF 17/10: khoá dòng aff_links = aff_id + sub_id; sub_id trống = link gốc; sub_id = job_id src_omni (itemId hoặc <itemId>-N)."""
    if not values:
        return {}
    headers = [str(h).strip().lower() for h in values[0]]
    try:
        id_i, link_i, active_i = headers.index("aff_id"), headers.index("link"), headers.index("active")
    except ValueError:
        logger.error(f"Tab {AFF_LINKS_TAB} thiếu cột aff_id / link / active — bỏ qua.")
        return {}
    sub_i = headers.index("sub_id") if "sub_id" in headers else -1
    cell = lambda row, i: str(row[i]).strip() if 0 <= i < len(row) else ""
    links = {}
    for row in values[1:]:
        aff_id, link = cell(row, id_i), cell(row, link_i)
        if aff_id and is_affiliate_link(link) and cell(row, active_i).lower() in ACTIVE_VALUES:
            links[(aff_id, cell(row, sub_i))] = link
    return links


def find_link(links: Dict, job_id: str) -> str:
    """Link cho 1 dòng src_omni: đúng Sub_id = job_id → link gốc (sub_id trống) → link của bản gốc (Sub_id = itemId)."""
    item = base_item_id(job_id)
    for key in ((item, job_id), (item, ""), (item, item)):
        if key in links:
            return links[key]
    return ""


# P3 (17/10): ô src_omni đang trống thì lấy thêm từ aff_links (cột src_omni -> cột aff_links)
INFO_FIELDS = {"price": "price", "commission_rate": "commission_rate", "shop_name": "shop"}


def load_aff_info(values: List[List[str]]) -> Dict[str, Dict[str, str]]:
    """aff_id -> {price, commission_rate, shop} (chỉ ô có giá trị), mọi dòng aff_links."""
    if not values:
        return {}
    headers = [str(h).strip().lower() for h in values[0]]
    if "aff_id" not in headers:
        return {}
    id_i = headers.index("aff_id")
    info = {}
    for row in values[1:]:
        aff_id = str(row[id_i]).strip() if id_i < len(row) else ""
        if not aff_id:
            continue
        fields = {}
        for src in INFO_FIELDS.values():
            if src in headers:
                i = headers.index(src)
                val = str(row[i]).strip() if i < len(row) else ""
                if val:
                    fields[src] = val
        if fields:
            info[aff_id] = fields
    return info


def plan_info_writes(omni_values: List[List[str]], info: Dict[str, Dict[str, str]]) -> List[Tuple[int, int, str, str]]:
    """Ô giá / % hoa hồng / tên shop đang TRỐNG trong src_omni mà aff_links có -> (dòng, cột, job_id, giá trị). Không đè."""
    if not omni_values or not info:
        return []
    headers = [str(h).strip().lower() for h in omni_values[0]]
    if "job_id" not in headers:
        return []
    id_i = headers.index("job_id")
    writes = []
    for r, row in enumerate(omni_values[1:], start=2):
        job_id = str(row[id_i]).strip() if id_i < len(row) else ""
        key = job_id if job_id in info else base_item_id(job_id)
        for dst, src in INFO_FIELDS.items():
            if dst not in headers or src not in info.get(key, {}):
                continue
            c = headers.index(dst)
            if not (str(row[c]).strip() if c < len(row) else ""):
                writes.append((r, c + 1, job_id, info[key][src]))
    return writes


def plan_writes(omni_values: List[List[str]], links: Dict[Tuple[str, str], str]) -> List[Tuple[int, int, str, str]]:
    """Các ô cần ghi: (số dòng sheet, số cột sheet, job_id, link). Chỉ ô shopee_link trống / chưa phải s.shopee.vn."""
    if not omni_values or not links:
        return []
    headers = [str(h).strip().lower() for h in omni_values[0]]
    if "job_id" not in headers or "shopee_link" not in headers:
        logger.error("Tab src_omni thiếu cột job_id / shopee_link — bỏ qua.")
        return []
    id_i, link_i = headers.index("job_id"), headers.index("shopee_link")
    writes = []
    for r, row in enumerate(omni_values[1:], start=2):
        job_id = str(row[id_i]).strip() if id_i < len(row) else ""
        current = str(row[link_i]).strip() if link_i < len(row) else ""
        link = find_link(links, job_id)
        if link and not is_affiliate_link(current):
            writes.append((r, link_i + 1, job_id, link))
    return writes


def run(apply: bool = False) -> int:
    gc = get_gspread_client()
    if not gc:
        print("❌ Không kết nối được Google Sheet.")
        return 0
    sh = gc.open_by_key(SPREADSHEET_ID)
    try:
        aff_values = sh.worksheet(AFF_LINKS_TAB).get_all_values()
    except gspread.exceptions.WorksheetNotFound:
        print(f"ℹ️ Chưa có tab {AFF_LINKS_TAB} — bỏ qua bước điền link.")
        return 0
    links = load_aff_links(aff_values)
    info = load_aff_info(aff_values)
    if not links and not info:
        print(f"ℹ️ Bảng {AFF_LINKS_TAB} chưa có dữ liệu — không điền gì.")
        return 0
    ws = get_omni_worksheet(sh)
    omni_values = ws.get_all_values()
    link_writes = plan_writes(omni_values, links)
    info_writes = plan_info_writes(omni_values, info)
    writes = link_writes + info_writes
    print(f"🔗 {len(links)} link trong {AFF_LINKS_TAB}; {len(link_writes)} ô shopee_link + {len(info_writes)} ô giá / % hoa hồng / shop sẽ được điền trong {ws.title}.")
    for row, _, job_id, link in link_writes:
        print(f"   - dòng {row} · {job_id} → {link}")
    if apply and writes:
        ws.batch_update(
            [{"range": gspread.utils.rowcol_to_a1(row, col), "values": [[link]]} for row, col, _, link in writes],
            value_input_option="USER_ENTERED",
        )
        print(f"✅ Đã điền {len(writes)} link.")
    elif writes:
        print("ℹ️ Chạy thử — chưa ghi. Thêm --apply để ghi thật.")
    return len(writes)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run(apply="--apply" in sys.argv)
