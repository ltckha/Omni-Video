#!/bin/bash
# Chế độ hàng tiệm (30/10/2026): video Flow cho giày tiệm Hiệu giày Hải Nancy theo mã tiệm (vd JH8918N).
# Tạo Product_Assets/<mã>/ (ảnh NAS HNC_Master → web giayhainancy.vn → image_01… SANPHAM, info.json hàng tiệm,
# kịch bản ghép từ config/hang_tiem.json, 0 Gemini). Không tạo dòng src_omni.

cd "$(dirname "$0")"

echo "============================================================"
echo "👞 OMNI VIDEO - HÀNG TIỆM (Hiệu giày Hải Nancy)"
echo "============================================================"
echo ""

PYTHON_EXEC="python3"
if [ -f "./venv/bin/python3" ]; then
  PYTHON_EXEC="./venv/bin/python3"
fi

read -r -p "Nhập mã giày (cách nhau dấu cách), rồi Enter: " CODES
read -r -p "Kiểu video: Enter = 4 cảnh · gõ 2 = 1 cảnh liền (máy lùi dần từ giày ra người mẫu): " KIEU
KIEU_ARG=""
if [ "$KIEU" = "2" ]; then
  KIEU_ARG="--lien"
fi
echo ""
# shellcheck disable=SC2086
$PYTHON_EXEC scripts/hang_tiem.py $KIEU_ARG $CODES

echo ""
echo "============================================================"
echo "✅ HOÀN TẤT! Nhấn phím Enter để đóng cửa sổ này."
echo "============================================================"
read -r
(sleep 0.1 && osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1) &
exit 0
