# N17 — Tờ ảnh 10 khung xem nhanh video trước khi Move (nghiên cứu, 23/10/2026)

**Kết luận:** làm được, nhanh, 0 Gemini. `scripts/contact_sheet.py` (bản nháp, chưa gắn vào luồng) cắt 10 khung đều trên video 10 s (1 khung / giây), ghép 5 × 2, ra 1 ảnh JPEG ~120–145 KB.

## Thử trên 3 video thật trên NAS (chỉ đọc, ảnh ra thư mục tạm)
| Video | Thời gian | Thấy được |
|---|---|---|
| 27958810119 (nến, bản làm lại) | 1,2 s | hũ + nắp giữ nguyên hình 10/10 khung |
| 29107701098 (son COLORKEY) | 0,6 s | thỏi son giữ hình, cầm 1 tay |
| 41573393497 (set son 20/10) | 0,5 s | hộp quà + 2 món giữ đúng thứ tự, dấu ✦ Flow góc phải |

Lỗi kiểu nắp hũ tách ra ở bản nến lỗi ngày 15/10 lộ rõ ngay ở 3 khung đầu → đủ để anh quyết "Move hay làm lại" trong vài giây, thay cho QA Gemini đã lưu trữ.

## Đề xuất gắn vào luồng (cần anh chọn, đụng luồng đang chạy)
1. **Khi video tải về xong** (native host `FLOW_COLLECT`): tạo `<Mã_SP>_xem.jpg` cạnh video, popup / Finder mở cho anh xem. — Anh thấy ngay sau khi Tạo video.
2. **Trong Move.command:** trước khi chuyển, mở tờ ảnh từng video, anh bấm Enter = Move, gõ `b` = bỏ qua (để làm lại).
3. Cả hai.

Ghi chú: tờ ảnh có hình nhân vật AI → chỉ để trên máy / NAS, không đưa lên trang artifact (luật chung 16).
