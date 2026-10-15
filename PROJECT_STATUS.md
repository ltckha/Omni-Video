# 🎥 Omni-Video - Project Status & Architecture

> **Cập nhật mới nhất:** 10/10/2026

---

## 1. 🌟 Kiến Trúc Hiện Tại (Current Architecture)

### 📊 Direct Google Sheets API v4 (100% Zero Google Apps Script)
* **Kết nối:** Dùng trực tiếp Google Sheets API v4 qua thư viện `gspread` kết hợp khóa xác thực `config/service_account.json`.
* **Spreadsheet ID:** `1Xg67qhp1J_Izt7v5uDKRgKjdEZapX9giKJ_ym0OMJN4` (tab `src_omni`, tên cũ `Omni-Video`; không có cả hai thì báo lỗi dừng).
* **Cột `product_code`** (thêm 15/10/2026, cột cuối): mã mẫu HNC cho video làm hàng Hiệu giày Hải Nancy; hàng Shopee để trống. Video-Post chép sang master để nối video với web giayhainancy.vn.
* **Không còn Webhook:** Đã gỡ toàn bộ URL Apps Script khỏi `scripts/` và `chrome-extension/` (popup chỉ còn hướng dẫn sử dụng).
* **Module điều khiển:**
  * [`scripts/sheet_sync.py`](scripts/sheet_sync.py): Đồng bộ sản phẩm & trạng thái video, map cột theo tên header.
  * [`scripts/omni_native_host.py`](scripts/omni_native_host.py): Chrome Native Messaging Host tiếp nhận ảnh từ trình duyệt, di chuyển file vào `Product_Assets/<itemId>/`, tạo `info.json` và gọi `sheet_sync.py`.
  * [`scripts/import_csv_to_gsheet.py`](scripts/import_csv_to_gsheet.py): Import CSV trong `data/` lên Sheet, lọc trùng.

### ☁️ Google Drive API v3 (Spark Sync)
* [`scripts/drive_sync.py`](scripts/drive_sync.py): Đọc/ghi `anti-spark_omni.md`, `IDEAS.md` với Spark qua Service Account. Không dùng đường dẫn CloudStorage cục bộ của macOS.

### 🧠 Chiến Lược Phân Bổ Mô Hình Gemini AI
* **Sinh Kịch Bản UGC & Video QA Analysis:**
  * Ưu tiên: `gemini-3.8-flash` ➔ `gemini-3.6-flash` ➔ `gemini-3.7-flash` ➔ `gemini-3.5-flash-lite` ➔ `gemini-2.5-flash` (Video QA không dùng lite).
  * Không dùng `gemini-3.5-flash`: lượt bị đếm vào hạn mức của 3.6-flash.
  * Không sử dụng các model gắn hậu tố `-preview`.
* **Sinh Video:** `gemini-omni-1.1-flash` (Interactions API), xuất `.mp4` dọc 9:16, có khóa PIN trước khi gọi API trả phí.

### 📝 Master Prompt UGC
* 9 góc sáng tạo linh hoạt (Surprise Gift & High-EQ Moment, Reverse Expectation, Extreme Stress Test, ...) chọn trong code; bối cảnh do AI tự do biến hóa.
* Luật chung trong [`config/prompt_rules.json`](config/prompt_rules.json) được nạp vào mọi prompt: cấm chữ/logo/watermark, one-take liên tục 10s, sản phẩm chiếm 40-50% khung hình, khóa nhân vật & giọng, luật riêng cho giày dép. Đã gỡ nhóm `HIGH_EQ_WAREHOUSE_GIFT_STORYLINE` (từng ép mọi video vào bối cảnh kho hàng).
* Chống lặp lời thoại: `get_recent_voiceovers(limit=5)`, `temperature: 0.95`.

---

## 2. 🔁 Quy Trình 1-Click macOS

| Bước | File | Script | Việc làm |
|---|---|---|---|
| 1 | `Import.command` | `auto_organize_downloads.py` ➔ `import_csv_to_gsheet.py` | Gom ảnh từ `~/Downloads` vào `Product_Assets/<itemId>/`, import CSV lên Sheet |
| 2 | `Prompt.command` | `generate_ugc_prompt.py` | Sinh `<itemId>.txt` + copy ảnh nhân vật |
| 3 | Popup extension → Google Flow (Omni-Studio Pro) | `flow_helper.py` qua native host | Gom 3 file để kéo thả; anh bấm Tạo/Tải trên Flow; video tự về `Product_Assets/<itemId>/<itemId>.mp4` (15 credit, 0 phí API) |
| 3b | `Video.command` (dự phòng) | `generate_omni_video.py` | Sinh `<itemId>.mp4` bằng Gemini Omni API (tốn phí) |
| 4 | `Move.command` | `archive_completed_videos.py` (+ `video_qa_analyzer.py` nếu chọn QA) | Dọn dẹp & chuyển thư mục có `.mp4` về `/Volumes/Media/Omni-Video/`, cập nhật Output File trên Sheet |

---

## 3. 📸 Chrome Extension Workflow (Cào Sản Phẩm & Ảnh)

* **Phím tắt:** `Alt+S` (hoặc chuột phải chọn "Lưu ảnh SP cho Omni UGC").
* **Quy trình hoạt động:**
  1. Trình duyệt tải ảnh CDN về `~/Downloads`.
  2. Background Service Worker gửi thông điệp tới Native Host (`com.omni.video.curator`).
  3. `omni_native_host.py` chuyển ảnh vào `Product_Assets/<itemId>/`, lưu `info.json` và ghi dữ liệu lên Tab `Omni-Video` qua Google Sheets API v4.

---

## 4. ✅ Kiểm Thử
* `python -m pytest tests/` — 55 test (prompt, omni video, drive sync, sheet sync, archive). Bắt buộc chạy sau mỗi lần sửa code.

---

## 5. 🛡️ Quy Tắc Làm Việc Của AI Assistant
1. **BẮT BUỘC THẢO LUẬN TRƯỚC KHI LÀM (`always_consult_user_first.md`):** Luôn trình bày kế hoạch và xin ý kiến duyệt từ User trước khi sửa code hoặc chạy lệnh.
2. **GIT: CHỈ NHÁNH RIÊNG + PR (`git_branch_pr_only.md`):** Không push thẳng `main`; anh Kha Merge trên GitHub.
3. **SPARK QUA DRIVE API V3 (`always_use_drive_api_for_spark.md`).**
