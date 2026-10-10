#!/bin/bash
# Script 1-Click tự động sinh Video dọc 9:16 bằng Gemini Omni Flash API cho toàn bộ sản phẩm

cd "$(dirname "$0")"

echo "============================================================"
echo "🎥 OMNI VIDEO - TỰ ĐỘNG TẠO VIDEO BẰNG GEMINI OMNI FLASH API"
echo "============================================================"
echo ""

# Sourcing biến môi trường từ .env của project (ưu tiên) hoặc ~/.zshrc / ~/.zshenv
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

$PYTHON_EXEC scripts/generate_omni_video.py "$@"

echo ""
echo "============================================================"
echo "✅ HOÀN TẤT! Nhấn phím Enter để đóng cửa sổ này."
echo "============================================================"
read -r
(sleep 0.1 && osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1) &
exit 0
