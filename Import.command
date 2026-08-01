#!/bin/bash
# Script tự động chạy Import CSV & Phân loại ảnh vào thư mục dự án khi nhấp đúp chuột

cd "$(dirname "$0")"

echo "============================================================"
echo "🚀 OMNI VIDEO - ĐỒNG BỘ CSV & PHÂN LOẠI ẢNH VỀ DỰ ÁN"
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

# 1. Di chuyển toàn bộ ảnh từ Downloads về đúng Product_Assets/<Mã_SP>/
python3 scripts/auto_organize_downloads.py

echo ""
# 2. Chạy Import CSV & Lọc trùng sản phẩm trên Google Sheet
python3 scripts/import_csv_to_gsheet.py

echo ""
echo "============================================================"
echo "✅ HOÀN TẤT! Nhấn phím Enter để đóng cửa sổ này."
echo "============================================================"
read -r
