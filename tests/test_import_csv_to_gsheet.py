import os
import sys
import time
from unittest.mock import patch

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import import_csv_to_gsheet as imp


def _csv(path, mtime):
    path.write_text("Mã sản phẩm,Tên sản phẩm\n1,A\n", encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_pending_csvs_skips_ledger_and_orders_oldest_first(tmp_path):
    root, data = tmp_path, tmp_path / "data"
    data.mkdir()
    now = time.time()
    _csv(root / "moi.csv", now)
    _csv(data / "cu.csv", now - 100)
    _csv(data / "da_nhap.csv", now - 50)
    names = [f.name for f in imp.pending_csvs({"da_nhap.csv": "x"}, root, data)]
    assert names == ["cu.csv", "moi.csv"]


def test_import_all_new_first_run_seeds_existing_data_and_imports_new(tmp_path, monkeypatch):
    root, data = tmp_path, tmp_path / "data"
    data.mkdir()
    now = time.time()
    _csv(data / "cu_trong_data.csv", now - 100)   # có sẵn trước sổ -> coi như đã nhập, không nhập lại
    _csv(root / "a.csv", now - 20)
    _csv(root / "b.csv", now - 10)
    monkeypatch.setattr(imp, "PROJECT_DIR", root)
    monkeypatch.setattr(imp, "DATA_DIR", data)
    monkeypatch.setattr(imp, "IMPORTED_LEDGER", data / ".imported_csv.json")
    called = []
    with patch.object(imp, "upload_csv_to_gsheet", side_effect=lambda f: called.append(f.name) or f.name != "b.csv"):
        assert imp.import_all_new() == 1
    assert called == ["a.csv", "b.csv"]                    # cả 2 file mới, cũ trước
    ledger = imp.json.loads((data / ".imported_csv.json").read_text())
    assert set(ledger) == {"cu_trong_data.csv", "a.csv"}   # b.csv lỗi -> chưa ghi sổ, lần sau thử lại
