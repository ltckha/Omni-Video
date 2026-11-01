# 🎬 Omni Video — video AI giày tiệm Hiệu giày Hải Nancy (Google Flow)

Chi tiết quy trình, sơ đồ, đọc / ghi gì: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Luật làm việc: [`CLAUDE.md`](CLAUDE.md).
Đường Shopee tiếp thị liên kết đã **tạm cất 1/11/2026** (chưa xoá): [`archive/README.md`](archive/README.md).

## Hằng ngày
1. **Mã chờ có sẵn:** 13:30 hằng ngày máy tự giữ **5 mã chờ** (mới nhất trong tab SANPHAM, còn hàng trên web). Cần bù ngay thì bấm đúp **`Fill_Queue.command`** (cùng việc với lịch 13:30).
2. **Muốn mã cụ thể:** bấm đúp **`Shop_Products.command`** → gõ mã (vd `JH8918N`) → Enter.
3. **Tạo video:** mở dự án Flow (ô câu lệnh trống) → bấm extension → **Tạo video** ở 1 mã. Extension tự dán ảnh + kịch bản, Phê duyệt (15 credit), chờ và tự tải video về `~/Downloads/<MÃ>_n.mp4`. Chrome hỏi Save thì bấm Save.
4. Kho hàng tự gom video vào SANPHAM → Video-Post. Không cần chuyển tay.

## Cài đặt (1 lần)
- Python: `python3 -m venv venv && ./venv/bin/pip install gspread google-auth requests certifi pytest`.
- `config/service_account.json`: khoá Service Account Google Sheets (không commit).
- Extension: `chrome://extensions` → bật **Developer mode** → **Load unpacked** → chọn `chrome-extension/`. Native host `com.omni.video.curator` (`~/Library/Application Support/Google/Chrome/NativeMessagingHosts/`) trỏ tới `scripts/omni_native_host.py`. Sửa code extension xong bấm **Reload** rồi tải lại trang Flow.
- Lịch 13:30: bật `bash launchd/enable_queue_products.sh`, tắt `bash launchd/disable_queue_products.sh`.
- Dự án Flow: video mặc định 9:16, x1, Omni 1.1 Flash, "Xác nhận trước khi tạo: Luôn luôn".
- Kiểm thử: `./venv/bin/python -m pytest tests/`.
