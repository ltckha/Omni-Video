#!/bin/bash
# Script 1-Click tự động dọn dẹp (xóa ảnh character, info.json) và di chuyển thư mục sản phẩm có video MP4 về /Volumes/Media/Omni-Video/

cd "$(dirname "$0")"

echo "============================================================"
echo "🚚 OMNI VIDEO - DI CHUYỂN THƯ MỤC VIDEO HOÀN THÀNH VỀ Ổ MEDIA"
echo "============================================================"
echo ""
echo "Vui lòng chọn chế độ di chuyển:"
echo "  [1] Move thẳng luôn - Siêu tốc (MẶC ĐỊNH - TỰ ĐỘNG CHẠY SAU 10 GIÂY)"
echo "  [2] Kiểm tra QA chất lượng video trước khi Move"
echo ""

# Đếm ngược 10s timeout read: Không thao tác gì sẽ tự động chọn [1]
choice=""
read -t 10 -p "👉 Nhập lựa chọn (1 hoặc 2, tự động chọn [1] sau 10s): " choice || choice="1"

if [ -z "$choice" ]; then
  choice="1"
fi

# Sourcing biến môi trường nếu cần
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
source ~/.zshrc 2>/dev/null
source ~/.zshenv 2>/dev/null

PYTHON_EXEC="python3"
if [ -f "./venv/bin/python3" ]; then
  PYTHON_EXEC="./venv/bin/python3"
fi

echo ""
if [ "$choice" = "2" ]; then
  echo "🔍 Đã chọn: [2] Kiểm tra QA chất lượng video rồi mới Move..."
  $PYTHON_EXEC scripts/archive_completed_videos.py
else
  echo "⚡ Đã chọn: [1] Move thẳng luôn (Bỏ qua kiểm tra QA - Siêu tốc)..."
  $PYTHON_EXEC scripts/archive_completed_videos.py --skip-qa
fi

echo ""
echo "============================================================"
echo "✅ HOÀN TẤT! Nhấn phím Enter để đóng cửa sổ này."
echo "============================================================"
read -r
(sleep 0.1 && osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1) &
exit 0
