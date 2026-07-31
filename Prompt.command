#!/bin/bash
# Script 1-Click tự động sinh Master Prompt UGC 10s cho toàn bộ sản phẩm bằng Gemini AI

cd "$(dirname "$0")"

echo "============================================================"
echo "🎬 OMNI VIDEO - TỰ ĐỘNG TẠO MASTER PROMPT UGC 10S BẰNG GEMINI AI"
echo "============================================================"
echo ""

# Sourcing biến môi trường từ ~/.zshrc hoặc ~/.zshenv
source ~/.zshrc 2>/dev/null
source ~/.zshenv 2>/dev/null

python3 scripts/generate_ugc_prompt.py

echo ""
echo "============================================================"
echo "✅ HOÀN TẤT! Nhấn phím Enter để đóng cửa sổ này."
echo "============================================================"
read -r
