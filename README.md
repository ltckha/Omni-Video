# 🎬 Omni Video — Sản phẩm Shopee → video UGC 10 giây (YenYen Deals)

Chi tiết quy trình, sơ đồ, đọc / ghi gì: [`docs/KIEN_TRUC.md`](docs/KIEN_TRUC.md). Luật làm việc: [`CLAUDE.md`](CLAUDE.md).

## 5 bước hằng ngày
1. **Lấy sản phẩm:** trên Shopee rê chuột lên ảnh nét nhất, bấm **`Alt + S`**.
2. **`Import.command`:** gom ảnh, nhập CSV Shopee Affiliate, điền link tiếp thị, gắn mùa, in gợi ý SP nên làm. Còn SP thiếu link thì Finder mở sẵn file `Omni_BatchCustomLinks_….xlsx` → tải lên affiliate.shopee.vn (Custom Link hàng loạt) → thả file kết quả vào `~/agent_mailbox/auto-video-factory/affiliate/links/`.
3. **`Prompt.command`:** sinh kịch bản `<Mã_SP>.txt`.
4. **Tạo video:** mở dự án Flow (ô câu lệnh trống) → bấm extension → **Tạo video** ở 1 SP → Chrome hỏi Save thì bấm Save. Mỗi video 15 credit.
5. **`Move.command`:** mỗi video mở tờ ảnh 10 khung → ổn bấm Enter (thư mục SP chuyển về NAS, Sheet ghi "Đã tạo Video"), lỗi gõ `b` rồi Enter (giữ lại để làm lại).

**Hàng tiệm (giày Hiệu giày Hải Nancy):** `HangTiem.command` → gõ mã → Enter = 1 cảnh liền, gõ `4` = 4 cảnh; bối cảnh tự đổi theo loại giày (ảnh + kịch bản ghép sẵn, 0 Gemini) → Flow **Tạo video**. Video để nguyên `~/Downloads/<mã>.mp4` cho Kho hàng gom, không qua `src_omni`, không Move.

## Cài đặt (1 lần)
- Python: `python3 -m venv venv && ./venv/bin/pip install gspread google-auth requests certifi pytest`.
- `.env` (mẫu `.env.example`): `GEMINI_OMNI_API_KEY` (hoặc `GEMINI_API_KEY`). `config/service_account.json`: khoá Service Account Google Sheets. Cả hai không commit.
- Extension: `chrome://extensions` → bật **Developer mode** → **Load unpacked** → chọn `chrome-extension/`. Native host `com.omni.video.curator` (`~/Library/Application Support/Google/Chrome/NativeMessagingHosts/`) trỏ tới `scripts/omni_native_host.py`. Sửa code extension xong bấm **Reload** rồi tải lại trang Flow.
- Dự án Flow: video mặc định 9:16, x1, Omni 1.1 Flash, "Xác nhận trước khi tạo: Luôn luôn".
- Kiểm thử: `./venv/bin/python -m pytest tests/`.
