#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - P1 (anh Kha 17/10/2026): tạo file Batch Custom Links (Shopee Affiliate) cho các dòng src_omni
chưa có link tiếp thị s.shopee.vn. Sub_id1 = job_id để đo video nào ra đơn (P2, AVF).

Anh làm tiếp: affiliate.shopee.vn → Custom Link hàng loạt → tải file này lên → tải file kết quả về
→ thả vào ~/agent_mailbox/auto-video-factory/affiliate/links/ → AVF nạp vào aff_links → Import.command
(fill_aff_links.py) điền src_omni.shopee_link.

Dùng: python scripts/make_batch_links.py        # ghi ~/Downloads/Omni_BatchCustomLinks_<ngày giờ>.xlsx
Chỉ đọc Sheet, 0 Gemini. Mẫu file gốc của Shopee: config/templates/shopee_batch_custom_links.xlsx.
"""

import os
import re
import sys
import zipfile
from datetime import datetime
from typing import List, Optional, Tuple
from xml.sax.saxutils import escape

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE = os.path.join(PROJECT_DIR, "config", "templates", "shopee_batch_custom_links.xlsx")
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
AFFILIATE_HOST = "s.shopee.vn"

_URL_PATTERNS = (re.compile(r"/(?:product|opaanlp)/(\d+)/(\d+)"), re.compile(r"[-.]i\.(\d+)\.(\d+)"))


def product_url(raw: str) -> Optional[str]:
    """Chuẩn hoá link sản phẩm về https://shopee.vn/product/<shop_id>/<item_id> (dạng Shopee nhận)."""
    s = str(raw or "")
    for pat in _URL_PATTERNS:
        m = pat.search(s.split("?")[0]) or pat.search(s)
        if m:
            return f"https://shopee.vn/product/{m.group(1)}/{m.group(2)}"
    return None


def pick_rows(values: List[List[str]]) -> Tuple[List[Tuple[str, str]], List[str]]:
    """(danh sách (link sản phẩm, job_id) cần làm link, danh sách job_id không đọc được link sản phẩm)."""
    if not values:
        return [], []
    headers = [str(h).strip().lower() for h in values[0]]
    col = lambda name: headers.index(name) if name in headers else -1
    id_i, url_i, link_i = col("job_id"), col("product_url"), col("shopee_link")
    if id_i < 0 or link_i < 0:
        raise ValueError("Tab src_omni thiếu cột job_id / shopee_link")
    cell = lambda row, i: str(row[i]).strip() if 0 <= i < len(row) else ""
    picked, unreadable, seen = [], [], set()
    for row in values[1:]:
        job_id = cell(row, id_i)
        if not job_id or job_id in seen or AFFILIATE_HOST in cell(row, link_i).lower():
            continue
        seen.add(job_id)
        url = product_url(cell(row, url_i)) or product_url(cell(row, link_i))
        if url:
            picked.append((url, job_id))
        else:
            unreadable.append(job_id)
    return picked, unreadable


def _cell(ref: str, text: str) -> str:
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'


def write_batch_xlsx(rows: List[Tuple[str, str]], out_path: str, template: str = TEMPLATE) -> str:
    """Giữ nguyên mẫu Shopee (tiêu đề hàng 1), thêm dòng: A = Liên kết gốc, B = Sub_id1 (job_id)."""
    with zipfile.ZipFile(template) as src:
        sheet = src.read("xl/worksheets/sheet1.xml").decode("utf-8")
        data_rows = "".join(
            f'<row r="{n}">{_cell(f"A{n}", url)}{_cell(f"B{n}", sub_id)}</row>'
            for n, (url, sub_id) in enumerate(rows, start=2)
        )
        sheet = sheet.replace("</sheetData>", data_rows + "</sheetData>", 1)
        sheet = re.sub(r'<dimension ref="[^"]*"/>', f'<dimension ref="A1:F{len(rows) + 1}"/>', sheet, count=1)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as dst:
            for item in src.infolist():
                data = sheet.encode("utf-8") if item.filename == "xl/worksheets/sheet1.xml" else src.read(item.filename)
                dst.writestr(item, data)
    return out_path


def main() -> int:
    sys.path.insert(0, os.path.dirname(__file__))
    from sheet_sync import get_gspread_client, get_omni_worksheet, SPREADSHEET_ID
    gc = get_gspread_client()
    if not gc:
        print("❌ Không kết nối được Google Sheet.")
        return 1
    ws = get_omni_worksheet(gc.open_by_key(SPREADSHEET_ID))
    rows, unreadable = pick_rows(ws.get_all_values())
    if unreadable:
        print(f"⚠️ {len(unreadable)} dòng không có link sản phẩm đọc được (bỏ qua): {', '.join(unreadable)}")
    if not rows:
        print("✅ Mọi dòng src_omni đã có link s.shopee.vn — không cần tạo file.")
        return 0
    out = os.path.join(DOWNLOADS_DIR, f"Omni_BatchCustomLinks_{datetime.now():%Y%m%d_%H%M}.xlsx")
    write_batch_xlsx(rows, out)
    print(f"✅ Đã tạo {out} ({len(rows)} sản phẩm, Sub_id1 = job_id).")
    print("👉 Tiếp theo: affiliate.shopee.vn → Custom Link hàng loạt → tải file lên → tải file kết quả về")
    print("   → thả vào ~/agent_mailbox/auto-video-factory/affiliate/links/ → sáng hôm sau AVF nạp → bấm Import.command.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
