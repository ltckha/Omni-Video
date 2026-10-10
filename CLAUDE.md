# 📜 CLAUDE.md - SỔ TAY VẬN HÀNH DỰ ÁN OMNI-VIDEO

> **Chào Claude, bạn đang cùng Kha Lưu (Project Owner) và Antigravity vận hành hệ thống Omni-Video.**  
> Tài liệu này là **Hiến pháp tối cao** bắt buộc bạn phải đọc và tuân thủ 100% trong suốt quá trình làm việc trong repository này.

---

## 🚨 1. CÁC QUY TẮC CỐT LÕI HÀNG ĐẦU (STRICT GOVERNANCE RULES)

1. **LUÔN LUÔN THẢO LUẬN & THỐNG NHẤT VỚI ANH KHA TRƯỚC KHI THỰC HIỆN:**
   - Trước khi sửa code, thêm module, đổi cấu hình, hay chạy lệnh, **bắt buộc phải trình bày giải pháp kỹ thuật chi tiết và được anh Kha đồng ý trước**.
   - Không tự ý suy đoán, không tự tiện thay đổi luồng dữ liệu.

2. **TUYỆT ĐỐI KHÔNG TỰ Ý CHẠY `git push`:**
   - Nghiêm cấm chạy `git push` dưới mọi hình thức khi chưa có lệnh trực tiếp từ anh Kha.
   - Chỉ được tạo commit cục bộ (`git commit`) trên máy để lưu tiến độ công việc an toàn.

3. **MÔ HÌNH PHỐI HỢP CẶP BÀI TRÙNG (DUAL-CLAUDE ARCHITECTURE):**
   - **Claude Cowork (Cloud):** Đảm nhận tư duy vĩ mô: Quy hoạch kiến trúc, phản biện logic mã nguồn, viết prompt Gemini Omni, lập kế hoạch hành động.
   - **Claude Code (Local Mac M4):** Kỹ sư trưởng thực thi hiện trường: Chạy lệnh terminal, kích hoạt môi trường ảo Python `venv`, chạy script di chuyển file, gọi API.
   - **Antigravity (IDE Pair-Programmer):** Đồng hành cùng anh Kha tại IDE.

---

## 🎬 2. TỔNG QUAN KIẾN TRÚC OMNI-VIDEO

Hệ thống tự động hóa thu thập nguyên liệu sản phẩm Shopee, đồng bộ Google Sheets, sinh Master Prompt UGC 10s và video cho **Gemini Omni**, lưu trữ thành phẩm về ổ đĩa NAS:

1. **Chrome Extension Curator (`Alt + S`):** Di chuột lên ảnh sản phẩm Shopee, bấm `Alt + S` để tự động bóc tách Item ID, Tên sản phẩm, Giá, Đã bán, Tên Shop và tải ảnh HD nguyên bản. Không còn cấu hình Webhook (Zero Apps Script).
2. **Native Messaging Host (`scripts/omni_native_host.py`):** Tự động chuyển ảnh tải về vào đúng thư mục `Product_Assets/<Mã_SP>/`, tạo `info.json` và ghi hàng lên Sheet.
3. **Google Sheets API v4 (`scripts/sheet_sync.py`, `gspread`):** Đồng bộ trực tiếp qua Service Account `config/service_account.json` (Spreadsheet ID: `1Xg67qhp1J_Izt7v5uDKRgKjdEZapX9giKJ_ym0OMJN4`, Tab `Omni-Video`). Luôn map cột theo tên header.
4. **Gemini AI UGC Master Prompt Generator (`scripts/generate_ugc_prompt.py`):** Phân tích ảnh đa phương thức + tên sản phẩm, chọn 1 trong 9 góc sáng tạo, nạp luật chung từ `config/prompt_rules.json`, xuất `Product_Assets/<Mã_SP>/<Mã_SP>.txt`. Model ưu tiên: `gemini-3.7-flash` ➔ `3.6-flash` ➔ `3.5-flash` ➔ `3.5-flash-lite` ➔ `2.5-flash` (cấm `-preview`).
5. **Sinh Video Omni (`Video.command` / `scripts/generate_omni_video.py`):** Gọi `gemini-omni-1.1-flash` với prompt `.txt` + ảnh sản phẩm + ảnh nhân vật, xuất `<Mã_SP>.mp4` dọc 9:16. API trả phí, có khóa PIN (`OMNI_SECURITY_PIN`).
6. **Clean & Move Completed Videos (`Move.command` / `scripts/archive_completed_videos.py`):** Quét các thư mục đã có video `.mp4` (cả trong `~/Downloads`), tùy chọn chạy QA (`video_qa_analyzer.py`), dọn file thừa và di chuyển thư mục về `/Volumes/Media/Omni-Video/`. Cập nhật cột Output File trên Sheet.
7. **Spark Sync (`scripts/drive_sync.py`):** Trao đổi `anti-spark_omni.md`, `IDEAS.md` với Spark 100% qua Google Drive API v3, không dùng đường dẫn CloudStorage cục bộ.

---

## 🛠️ 3. MÔI TRƯỜNG & LỆNH THỰC THI CHUẨN

### 1. Kích hoạt môi trường ảo Python:
```bash
source venv/bin/activate
```

### 2. Các lệnh điều hành chính:
- **Gom ảnh từ Downloads vào `Product_Assets/` & Import CSV lên Sheet:**
  ```bash
  python scripts/auto_organize_downloads.py && python scripts/import_csv_to_gsheet.py
  # hoặc nhấp đúp: Import.command
  ```
- **Sinh Master Prompt UGC bằng Gemini AI:**
  ```bash
  python scripts/generate_ugc_prompt.py
  # hoặc nhấp đúp: Prompt.command
  ```
- **Sinh video bằng Gemini Omni (tốn phí API):**
  ```bash
  python scripts/generate_omni_video.py [<Mã_SP>]
  # hoặc nhấp đúp: Video.command
  ```
- **Dọn dẹp & Di chuyển video hoàn thành sang NAS:**
  ```bash
  python scripts/archive_completed_videos.py --skip-qa   # bỏ --skip-qa để chạy QA trước
  # hoặc nhấp đúp: Move.command (mặc định [1] = skip QA sau 10s)
  ```
- **Đồng bộ với Spark qua Drive API v3:**
  ```bash
  python scripts/drive_sync.py [read|write|append|test] [args...]
  ```
- **Kiểm thử (bắt buộc sau mỗi lần sửa code):**
  ```bash
  python -m pytest tests/
  ```

### 3. Cấu hình & Biến môi trường:
- File cấu hình: `.env` (`GEMINI_API_KEY`, `GEMINI_OMNI_API_KEY`, `OMNI_SECURITY_PIN`, ...).
- Luật prompt dùng chung: `config/prompt_rules.json` (nạp toàn bộ vào mọi prompt — không đặt luật riêng cho một kịch bản ở đây).
- File Service Account: `config/service_account.json` (Google Sheets & Google Drive API).
- Thư mục kho lưu trữ NAS: `/Volumes/Media/Omni-Video/`.
