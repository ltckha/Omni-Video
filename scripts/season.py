#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - P4 lịch mùa (anh Kha 17/10/2026). Cấu hình: config/mua_vu.json.
- Gắn mùa cho dòng src_omni (cột `season`, mã mùa) theo từ khoá trong tên SP — chỉ ô đang trống.
- Hết mùa (đã qua đợt gần nhất, chưa tới lúc nhắc đợt sau) -> status = "Hết mùa" (Video-Post bỏ qua khi đăng).
- Mùa quay lại (đang diễn ra / sắp tới) mà status = "Hết mùa" -> trả lại "Đã tạo Video" (có video_path) hoặc "Đã chọn ảnh".
- In mùa đang diễn ra / sắp tới (trong remind_days_before ngày).

Dùng: python scripts/season.py            # chạy thử, chỉ báo
      python scripts/season.py --apply    # ghi (> 10 dòng đổi thì dừng, cần thêm --yes sau khi anh Kha đồng ý)
Đọc / ghi theo tên cột hàng 1, chỉ ô đổi. 0 Gemini.
"""

import json
import os
import re
import sys
import unicodedata
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "mua_vu.json")
STATUS_OFF_SEASON = "Hết mùa"
STATUS_DONE = "Đã tạo Video"
STATUS_NEW = "Đã chọn ảnh"
BULK_LIMIT = 10


def load_config(path: str = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fold(text: str) -> str:
    s = unicodedata.normalize("NFD", str(text or "").lower().replace("đ", "d"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def detect_season(title: str, seasons: List[dict]) -> Optional[str]:
    """Mã mùa đầu tiên có từ khoá xuất hiện nguyên cụm trong tên SP (đã bỏ dấu)."""
    t = f" {fold(title)} "
    for s in seasons:
        for kw in s.get("keywords", []):
            if re.search(r"(?<![a-z0-9])" + re.escape(fold(kw)) + r"(?![a-z0-9])", t):
                return s["id"]
    return None


def windows(season: dict, today: date) -> List[Tuple[date, date]]:
    """Các đợt quanh hôm nay: windows cố định, hoặc MM-DD lặp cho năm trước / năm nay / năm sau."""
    if "windows" in season:
        return [(date.fromisoformat(a), date.fromisoformat(b)) for a, b in season["windows"]]
    out = []
    for y in (today.year - 1, today.year, today.year + 1):
        sm, sd = map(int, season["start"].split("-"))
        em, ed = map(int, season["end"].split("-"))
        start = date(y, sm, sd)
        end = date(y + 1 if (em, ed) < (sm, sd) else y, em, ed)
        out.append((start, end))
    return out


def season_state(season: dict, today: date, remind_days: int) -> str:
    """'active' | 'upcoming' (trong remind_days ngày tới) | 'off' (đã qua, chưa tới lúc nhắc) | 'unknown' (chưa có lịch)."""
    ws = windows(season, today)
    if any(a <= today <= b for a, b in ws):
        return "active"
    if any(today < a <= today + timedelta(days=remind_days) for a, _ in ws):
        return "upcoming"
    if any(b < today for _, b in ws):
        return "off"
    return "unknown"


def reminders(cfg: dict, today: date) -> List[str]:
    remind = int(cfg.get("remind_days_before", 14))
    lines = []
    for s in cfg["seasons"]:
        for a, b in windows(s, today):
            if a <= today <= b:
                lines.append(f"🟢 Đang trong mùa {s['name']} (tới {b:%d/%m}, còn {(b - today).days} ngày)")
            elif today < a <= today + timedelta(days=remind):
                lines.append(f"⏰ Sắp tới mùa {s['name']} ({a:%d/%m}, còn {(a - today).days} ngày) — làm video sớm")
    return lines


def plan_changes(values: List[List[str]], cfg: dict, today: date) -> Dict[str, list]:
    """{'season': [(dòng, cột, job_id, mã mùa)], 'status': [(dòng, cột, job_id, status mới)], 'missing_cols': [...]}"""
    out = {"season": [], "status": [], "missing_cols": []}
    if not values:
        return out
    headers = [str(h).strip().lower() for h in values[0]]
    for c in ("job_id", "title", "status", "season"):
        if c not in headers:
            out["missing_cols"].append(c)
    if any(c in out["missing_cols"] for c in ("job_id", "title", "status")):
        return out
    by_id = {s["id"]: s for s in cfg["seasons"]}
    remind = int(cfg.get("remind_days_before", 14))
    col = {c: headers.index(c) for c in headers}
    cell = lambda row, c: str(row[col[c]]).strip() if c in col and col[c] < len(row) else ""
    for r, row in enumerate(values[1:], start=2):
        job_id = cell(row, "job_id")
        if not job_id:
            continue
        season_id = cell(row, "season")
        if not season_id:
            season_id = detect_season(cell(row, "title"), cfg["seasons"]) or ""
            if season_id:
                out["season"].append((r, col.get("season", -1) + 1, job_id, season_id))
        if season_id not in by_id:
            continue
        state = season_state(by_id[season_id], today, remind)
        status = cell(row, "status")
        if state == "off" and status != STATUS_OFF_SEASON:
            out["status"].append((r, col["status"] + 1, job_id, STATUS_OFF_SEASON))
        elif state in ("active", "upcoming") and status == STATUS_OFF_SEASON:
            back = STATUS_DONE if cell(row, "video_path") else STATUS_NEW
            out["status"].append((r, col["status"] + 1, job_id, back))
    return out


def main() -> int:
    sys.path.insert(0, os.path.dirname(__file__))
    import gspread
    from sheet_sync import get_gspread_client, get_omni_worksheet, SPREADSHEET_ID
    apply, yes = "--apply" in sys.argv, "--yes" in sys.argv
    cfg, today = load_config(), date.today()
    for line in reminders(cfg, today):
        print(line)
    gc = get_gspread_client()
    if not gc:
        print("❌ Không kết nối được Google Sheet.")
        return 1
    ws = get_omni_worksheet(gc.open_by_key(SPREADSHEET_ID))
    plan = plan_changes(ws.get_all_values(), cfg, today)
    if plan["missing_cols"]:
        print(f"⚠️ Tab {ws.title} thiếu cột: {', '.join(plan['missing_cols'])} — chưa gắn mùa được (cần anh Kha đồng ý thêm cột).")
    print(f"🗓️ Gắn mùa: {len(plan['season'])} ô · Đổi trạng thái theo mùa: {len(plan['status'])} dòng")
    for _, _, job_id, v in plan["season"]:
        print(f"   - {job_id} → mùa {v}")
    for _, _, job_id, v in plan["status"]:
        print(f"   - {job_id} → status \"{v}\"")
    writes = [w for w in plan["season"] if w[1] > 0] + plan["status"]
    rows_changed = len({w[0] for w in writes})
    if not apply or not writes:
        if writes:
            print("ℹ️ Chạy thử — chưa ghi. Thêm --apply để ghi.")
        return 0
    if rows_changed > BULK_LIMIT and not yes:
        print(f"⏸️ {rows_changed} dòng sẽ đổi (> {BULK_LIMIT}) — dừng, chờ anh Kha đồng ý rồi chạy lại với --apply --yes.")
        return 0
    ws.batch_update([{"range": gspread.utils.rowcol_to_a1(r, c), "values": [[v]]} for r, c, _, v in writes],
                    value_input_option="USER_ENTERED")
    print(f"✅ Đã ghi {len(writes)} ô ({rows_changed} dòng).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
