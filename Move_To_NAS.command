#!/bin/bash
# Script 1-Click tự động dọn dẹp (xóa ảnh character, info.json) và di chuyển thư mục sản phẩm có video MP4 về /Volumes/Media/Omni-Video/

cd "$(dirname "$0")"

echo "============================================================"
echo "🚚 OMNI VIDEO - DI CHUYỂN THƯ MỤC VIDEO HOÀN THÀNH VỀ Ổ MEDIA"
echo "============================================================"
echo ""
# Sourcing biến môi trường nếu cần
source ~/.zshrc 2>/dev/null
source ~/.zshenv 2>/dev/null
# .env của Omni nạp SAU để thắng biến chung trong ~/.zshrc (khoá Gemini riêng của Omni)
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

PYTHON_EXEC="python3"
if [ -f "./venv/bin/python3" ]; then
  PYTHON_EXEC="./venv/bin/python3"
fi

echo ""
$PYTHON_EXEC scripts/archive_completed_videos.py

echo ""
echo "============================================================"
echo "✅ HOÀN TẤT! Nhấn phím Enter để đóng cửa sổ này."
echo "============================================================"
read -r
(sleep 0.1 && osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1) &
exit 0
