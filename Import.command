#!/bin/bash
# Script tự động chạy Import CSV & Phân loại ảnh vào thư mục dự án khi nhấp đúp chuột

cd "$(dirname "$0")"

echo "============================================================"
echo "🚀 OMNI VIDEO - ĐỒNG BỘ CSV & PHÂN LOẠI ẢNH VỀ DỰ ÁN"
echo "============================================================"
echo ""

# Sourcing biến môi trường từ .env của project (ưu tiên) hoặc ~/.zshrc / ~/.zshenv
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

# 1. Di chuyển toàn bộ ảnh từ Downloads về đúng Product_Assets/<Mã_SP>/
$PYTHON_EXEC scripts/auto_organize_downloads.py

echo ""
# 2. Chạy Direct Import CSV & Lọc trùng sản phẩm trên Google Sheets API v4
$PYTHON_EXEC scripts/import_csv_to_gsheet.py

echo ""
# 3. Tự điền link TTLK s.shopee.vn từ bảng chung aff_links (chỉ ô trống / chưa phải s.shopee.vn)
$PYTHON_EXEC scripts/fill_aff_links.py --apply

echo ""
# 3b. Còn SP chưa có link s.shopee.vn -> tạo file Batch Custom Links trong Tải về (gộp Links.command 21/10)
$PYTHON_EXEC scripts/make_batch_links.py && NEW_BATCH="$(ls -t ~/Downloads/Omni_BatchCustomLinks_*.xlsx 2>/dev/null | head -1)"
if [ -n "$NEW_BATCH" ] && [ "$(find "$NEW_BATCH" -mmin -2 2>/dev/null)" ]; then open -R "$NEW_BATCH"; fi

echo ""
# 4. Lịch mùa: gắn mùa, đổi "Hết mùa" / trả lại (đổi > 10 dòng thì dừng chờ anh Kha), nhắc mùa sắp tới
$PYTHON_EXEC scripts/season.py --apply

echo ""
# 5. Gợi ý nên làm video sản phẩm nào trước (hoa hồng × lượt bán) — chỉ đọc
$PYTHON_EXEC scripts/rank_products.py

echo ""
echo "============================================================"
echo "✅ HOÀN TẤT! Nhấn phím Enter để đóng cửa sổ này."
echo "============================================================"
read -r
(sleep 0.1 && osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1) &
exit 0
