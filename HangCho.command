#!/bin/bash
# Hàng chờ hàng tiệm (30/10/2026): chạy tay đúng việc lịch 13:30 làm — dọn mã HNC đã gom, bù cho đủ 5 mã chờ
# (SANPHAM mới nhất trước, kiểu liền, bối cảnh xoay vòng, 0 Gemini). Nhật ký: data/logs/hang_cho.log

cd "$(dirname "$0")"

echo "============================================================"
echo "👞 OMNI VIDEO - HÀNG CHỜ HÀNG TIỆM (giữ 5 mã chờ)"
echo "============================================================"
echo ""

PYTHON_EXEC="python3"
if [ -f "./venv/bin/python3" ]; then
  PYTHON_EXEC="./venv/bin/python3"
fi

$PYTHON_EXEC scripts/hang_cho.py

echo ""
echo "============================================================"
echo "✅ HOÀN TẤT! Mở Flow, bấm extension → Tạo video. Nhấn Enter để đóng."
echo "============================================================"
read -r
(sleep 0.1 && osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1) &
exit 0
