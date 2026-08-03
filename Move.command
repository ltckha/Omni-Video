#!/bin/bash
# Script 1-Click tự động dọn dẹp (xóa ảnh character, info.json) và di chuyển thư mục sản phẩm có video MP4 về /Volumes/Media/Omni-Video/Product_Assets/

cd "$(dirname "$0")"

echo "============================================================"
echo "🚚 OMNI VIDEO - DI CHUYỂN THƯ MỤC VIDEO HOÀN THÀNH VỀ Ổ MEDIA"
echo "============================================================"
echo ""

# Sourcing biến môi trường nếu cần
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
source ~/.zshrc 2>/dev/null
source ~/.zshenv 2>/dev/null

python3 scripts/archive_completed_videos.py

echo ""
echo "============================================================"
echo "✅ HOÀN TẤT! Nhấn phím Enter để đóng cửa sổ này."
echo "============================================================"
read -r
