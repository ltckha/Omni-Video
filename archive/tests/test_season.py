import os
import sys
from datetime import date

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from season import load_config, detect_season, season_state, plan_changes, reminders

CFG = load_config()
BY_ID = {s["id"]: s for s in CFG["seasons"]}


def test_config_seasons_are_valid():
    ids = [s["id"] for s in CFG["seasons"]]
    assert len(ids) == len(set(ids))
    for s in CFG["seasons"]:
        assert s.get("keywords") and ("windows" in s or ("start" in s and "end" in s))


def test_detect_season_whole_phrase_without_accents():
    assert detect_season("Ủng Đi Mưa Silicon Cổ Cao", CFG["seasons"]) == "mua_mua"
    assert detect_season("Lồng Đèn Cá Chép Trung Thu", CFG["seasons"]) == "trung_thu"
    assert detect_season("[Set Quà Son Môi 20/10] Combo", CFG["seasons"]) == "phu_nu_vn_20_10"
    assert detect_season("Bộ chi tiết lắp ráp", CFG["seasons"]) is None          # "tiet" không phải "tet"
    assert detect_season("Bánh mì ủng hộ", CFG["seasons"]) is None                # "ủng hộ" không phải mùa mưa


def test_season_state_recurring_and_cross_year():
    rain = BY_ID["mua_mua"]
    assert season_state(rain, date(2026, 10, 17), 14) == "active"
    assert season_state(rain, date(2026, 12, 1), 14) == "off"
    assert season_state(rain, date(2027, 4, 20), 14) == "upcoming"
    xmas = BY_ID["giang_sinh"]
    assert season_state(xmas, date(2026, 11, 20), 14) == "upcoming"
    tet = BY_ID["tet"]
    assert season_state(tet, date(2027, 1, 20), 14) == "active"


def test_plan_tags_and_marks_off_season_and_restores():
    values = [["job_id", "title", "status", "video_path", "season"],
              ["1", "Lồng đèn trung thu", "Đã tạo Video", "/x/1.mp4", ""],   # gắn mùa + hết mùa
              ["2", "Ủng đi mưa", "Hết mùa", "/x/2.mp4", "mua_mua"],         # mùa mưa đang diễn ra -> trả lại
              ["3", "Ô gấp", "Hết mùa", "", ""],                              # gắn mùa + trả lại "Đã chọn ảnh"
              ["4", "Máy cạo lông", "Đã tạo Video", "/x/4.mp4", ""]]          # không mùa
    plan = plan_changes(values, CFG, date(2026, 10, 17))
    assert plan["missing_cols"] == []
    assert plan["season"] == [(2, 5, "1", "trung_thu"), (4, 5, "3", "mua_mua")]
    assert plan["status"] == [(2, 3, "1", "Hết mùa"), (3, 3, "2", "Đã tạo Video"), (4, 3, "3", "Đã chọn ảnh")]


def test_plan_reports_missing_season_column_without_writing_season():
    plan = plan_changes([["job_id", "title", "status"], ["1", "Lồng đèn trung thu", "Đã tạo Video"]], CFG, date(2026, 10, 17))
    assert plan["missing_cols"] == ["season"]
    assert plan["season"] == [(2, 0, "1", "trung_thu")]   # cột 0 = chưa có cột, main() không ghi ô này


def test_reminders_mention_active_and_upcoming():
    lines = reminders(CFG, date(2026, 10, 28))
    assert any("Mùa mưa" in l and "Đang" in l for l in lines)
    assert any("11/11" in l and "Sắp tới" in l for l in lines)
