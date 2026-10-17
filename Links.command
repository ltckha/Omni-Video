#!/bin/bash
# P1: tạo file Batch Custom Links (Shopee Affiliate) cho các sản phẩm Omni chưa có link s.shopee.vn

cd "$(dirname "$0")"

echo "============================================================"
echo "🔗 OMNI VIDEO - TẠO FILE BATCH CUSTOM LINKS (SHOPEE AFFILIATE)"
echo "============================================================"
echo ""

source ~/.zshrc 2>/dev/null
source ~/.zshenv 2>/dev/null
# .env của Omni nạp SAU để thắng biến chung trong ~/.zshrc
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

PYTHON_EXEC="python3"
if [ -f "./venv/bin/python3" ]; then
  PYTHON_EXEC="./venv/bin/python3"
fi

$PYTHON_EXEC scripts/make_batch_links.py && open -R "$(ls -t ~/Downloads/Omni_BatchCustomLinks_*.xlsx 2>/dev/null | head -1)" 2>/dev/null

echo ""
echo "============================================================"
echo "✅ HOÀN TẤT! Nhấn phím Enter để đóng cửa sổ này."
echo "============================================================"
read -r
(sleep 0.1 && osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1) &
exit 0
