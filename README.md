# 🎬 Omni Video - Shopee Asset Curator & UGC Prompt Generator

Hệ thống tự động hóa toàn diện quy trình thu thập nguyên liệu sản phẩm từ Shopee, lưu trữ phân loại theo mã sản phẩm, đồng bộ Google Sheets và sinh **Master Prompt Video UGC 10 giây** cho **Gemini Omni**.

---

## 📌 Tính Năng Nổi Bật

1. **Chrome Extension Curator (1-Click Shortcut `Alt + S`):**
   - Di chuột lên ảnh sản phẩm HD trên Shopee và nhấn `Alt + S`.
   - Tự động bóc tách **Mã sản phẩm (itemId)**, **Tên sản phẩm**, **Giá**, **Doanh thu / Đã bán** và **Tên cửa hàng (Shop)**.
   - Tải ảnh HD nguyên bản (`.webp` / `.png` / `.jpg`) về máy.

2. **Native Messaging Host (macOS 0.1s Auto-Move):**
   - Kích hoạt tiến trình Python siêu nhẹ bật lên đúng 0.1s để di chuyển file ảnh vào đúng thư mục dự án: `Product_Assets/<Mã_SP>/`.
   - 0% tiến trình chạy ngầm, không tốn tài nguyên RAM/CPU.

3. **Google Sheets Sync & Lọc Trùng Sâu (Deep Deduplication):**
   - Mã nguồn `google_apps_script.js` bảo toàn nguyên vẹn 100% dữ liệu 9 cột gốc từ CSV (bao gồm *Tỉ lệ hoa hồng* & *Hoa hồng*).
   - Tự động cập nhật 3 cột mới: `Link ảnh CDN chọn lọc`, `File ảnh lưu local`, `Trạng thái Master Prompt`.
   - Tự động lọc bỏ các sản phẩm trùng lặp dựa trên Mã SP và URL link sản phẩm.

4. **Master Prompt UGC 10s Generator (`omni-ugc-creator.md`):**
   - Công thức chuẩn khóa cứng thời lượng 10s, tỉ lệ 9:16 vertical, phân cảnh 0–3s Hook & Problem và 3–10s Solution & Demo.
   - Linh hoạt kích hoạt **AI Creative Freedom** khi thiếu nhân vật, bối cảnh hoặc đạo cụ.

---

## 📁 Cấu Trúc Dự Án (Project Structure)

```text
Omni-Video/
├── omni-ugc-creator.md          # Quy chuẩn Master Prompt UGC 10s cho Gemini Omni
├── README.md                    # Tài liệu hướng dẫn hệ thống
├── google_apps_script.js        # Mã nguồn Google Apps Script (Webhook & Google Sheets API)
├── import_csv_to_gsheet.py      # Script Python import file CSV & lọc trùng sâu
├── omni_native_host.py          # Native Messaging Host Python (Di chuyển ảnh 0.1s)
├── run_native_host.sh           # Shell script wrapper khởi chạy Native Host trên macOS
├── Chay_Import_CSV.command     # File 1-Click nhấp đúp chuột để Import CSV & phân loại ảnh
├── chrome-extension/            # Tiện ích mở rộng Chrome
│   ├── manifest.json            # Manifest V3 (Bao gồm quyền nativeMessaging & permissions)
│   ├── background.js            # Service worker điều phối tải ảnh & gọi Webhook
│   ├── content.js               # Content script bắt phím Alt+S & cào dữ liệu Shopee
│   ├── popup.html               # Giao diện popup cài đặt Webhook URL
│   └── popup.js                 # Xử lý lưu cấu hình Webhook URL
└── Product_Assets/              # Thư mục lưu trữ ảnh/video nguyên liệu sản phẩm
    └── <Mã_SP>/                 # Thư mục riêng của từng sản phẩm chứa ảnh HD
```

---

## 🚀 Hướng Dẫn Cài Đặt (Quick Setup)

### 1. Cài Đặt Google Apps Script (Backend)
1. Mở file Google Sheet (đã import CSV hoặc bảng tính mới).
2. Chọn **Extensions (Tiện ích mở rộng)** -> **Apps Script**.
3. Sao chép nội dung file [`google_apps_script.js`](file:///Users/khan/Developer/Omni-Video/google_apps_script.js) dán đè vào `Code.gs`.
4. Bấm **Deploy (Triển khai)** -> **New deployment (Triển khai mới)**:
   - Type: `Web app`
   - Execute as: `Me`
   - Who has access: `Anyone`
5. Sao chép **Web App URL** thu được.

### 2. Cài Đặt Chrome Extension
1. Mở trình duyệt Chrome, truy cập `chrome://extensions/`.
2. Bật **Developer mode (Chế độ dành cho nhà phát triển)**.
3. Bấm **Load unpacked (Tải tiện ích đã giải nén)** -> Trỏ tới thư mục [`chrome-extension`](file:///Users/khan/Developer/Omni-Video/chrome-extension).
4. Bấm vào icon tiện ích trên thanh công cụ -> Dán **Web App URL** từ Bước 1 -> Bấm **Lưu Cấu Hình**.

---

## 📸 Quy Trình Sử Dụng Hàng Ngày

1. Mở bất kỳ trang sản phẩm Shopee nào.
2. Di chuột lên bức ảnh sản phẩm HD ưng ý và bấm **`Alt + S`**.
3. **Kết quả:**
   - Ảnh sẽ tự động lưu vào thư mục dự án: `Product_Assets/<Mã_SP>/`.
   - Dòng sản phẩm tương ứng trên Google Sheet sẽ tự động nhảy trạng thái sang **"Đã chọn ảnh"** kèm link ảnh CDN và thông tin sản phẩm!
