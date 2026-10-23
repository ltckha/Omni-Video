# N18 — Gợi ý SP nên làm ngay từ file Product Offer (nghiên cứu, 23/10/2026)

**Kết luận:** làm được, 0 Gemini. `scripts/rank_offers.py` (bản nháp, chỉ đọc) đọc file CSV Product Offer của Shopee Affiliate (cùng mẫu file trong `data/`), xếp theo hoa hồng (đ) × lượt bán — cùng công thức với bảng gợi ý cuối Import.command — và đánh dấu ✔ SP đã có trong `src_omni`.

## Thử trên 3 file thật trong `data/` (DépNestyT1, bocgiaydimuaT1, ungdimuaT1)
- 31 SP trong file; phần lớn đã có trong `src_omni`.
- **SP hạng 3 chưa có trong Omni:** 44121618131 (dép NESTY NE54, hoa hồng ₫35.378 × 30k+). Tiếp theo: 41053395377 (NE38, ₫26.676 × 20k+). → Đang để sót SP tiền cao.

## Đề xuất gắn vào luồng (cần anh chọn)
1. Import.command in thêm "Top 10 SP chưa làm" từ mọi CSV trong `data/` + `~/Downloads` (chỉ in, không ghi). — ít rủi ro nhất.
2. Import chỉ nhập lên Sheet top N theo điểm thay vì cả file (giảm dòng rác).
3. Lệnh riêng `python scripts/rank_offers.py <file.csv>` như hiện tại, anh chạy khi có file mới.

## N29 — Import chỉ nhập 1 CSV (bản sửa soạn sẵn, 23/10)
Nguyên nhân: mỗi lần Import chỉ nhập file CSV mới nhất, rồi `organize_all_root_csvs()` chuyển **mọi** CSV ở gốc repo (kể cả chưa nhập) vào `data/`; lần sau lại chọn file mới nhất → file cũ hơn không bao giờ lên Sheet.
Bản sửa đã có trong `scripts/import_csv_to_gsheet.py`, **chưa bật**: `python scripts/import_csv_to_gsheet.py --all-new` nhập mọi CSV chưa có trong sổ `data/.imported_csv.json` (cũ trước), file lỗi thì để lần sau thử lại. Lần đầu chạy ghi sẵn mọi file đang có trong `data/` là "đã nhập" để dòng anh đã xoá tay không quay lại. Bật = đổi 1 dòng trong Import.command (thêm `--all-new`), sau khi anh trả lời V133. 5 SP NESTY còn thiếu: nếu anh không xoá tay thì chạy `python scripts/import_csv_to_gsheet.py data/DépNestyT1.csv`.
