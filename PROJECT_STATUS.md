# 🎥 Omni-Video - Project Status & Architecture

> **Cập nhật mới nhất:** 17/08/2026

---

## 1. 🌟 Kiến Trúc Hiện Tại (Current Architecture)

### 📊 Direct Google Sheets API v4 (100% Zero Google Apps Script)
* **Kết nối:** Dùng trực tiếp Google Sheets API v4 qua thư viện `gspread` kết hợp khóa xác thực `config/service_account.json`.
* **Spreadsheet ID:** `1Xg67qhp1J_Izt7v5uDKRgKjdEZapX9giKJ_ym0OMJN4`
* **Module điều khiển:**
  * [`scripts/sheet_sync.py`](scripts/sheet_sync.py): Đồng bộ sản phẩm vào Tab `Omni-Video`.
  * [`scripts/omni_native_host.py`](scripts/omni_native_host.py): Chrome Native Messaging Host tiếp nhận ảnh từ trình duyệt, di chuyển file vào `Product_Assets/<itemId>/`, tạo `info.json` và gọi thẳng `sheet_sync.py` để ghi vào Google Sheets API v4.
  * [`scripts/generate_ugc_prompt.py`](scripts/generate_ugc_prompt.py): Đọc danh sách sản phẩm trực tiếp từ Google Sheets API v4 mà không qua Webhook.

### 🧠 Chiến Lược Phân Bổ Mô Hình Gemini AI
* **Sinh Kịch Bản UGC & Video QA Analysis:**
  * Ưu tiên: `gemini-3.7-flash` (Flagship) ➔ `gemini-3.6-flash` ➔ `gemini-3.5-flash` ➔ `gemini-3.5-flash-lite` ➔ `gemini-2.5-flash`.
  * Không sử dụng các model gắn hậu tố `-preview`.

---

## 2. 📸 Chrome Extension Workflow (Cào Sản Phẩm & Ảnh)

* **Phím tắt:** `Alt+S` (hoặc chuột phải chọn "Lưu ảnh SP cho Omni UGC").
* **Quy trình hoạt động:**
  1. Trình duyệt tải ảnh CDN về `~/Downloads`.
  2. Background Service Worker gửi thông điệp tới Native Host (`com.omni.video.curator`).
  3. `omni_native_host.py` chuyển ảnh vào `Product_Assets/<itemId>/`, lưu `info.json` và bắn dữ liệu trực tiếp lên Tab `Omni-Video` qua Google Sheets API v4.
  4. **Không cần cấu hình Webhook URL trong popup:** Tiện ích chạy độc lập, tự động 100%.

---

## 3. 🛡️ Quy Tắc Làm Việc Của AI Assistant
1. **BẮT BUỘC THẢO LUẬN TRƯỚC KHI LÀM (`always_consult_user_first.md`):** Luôn trình bày kế hoạch và xin ý kiến duyệt từ User trước khi sửa code hoặc chạy lệnh.
2. **KHÔNG TỰ Ý PUSH GIT:** Chỉ thực hiện lệnh push Git khi User yêu cầu rõ ràng.
