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
   - Tự động cập nhật 2 cột mới: `Link ảnh CDN chọn lọc`, `File ảnh lưu local` và cập nhật `Trạng thái Master Prompt`.

4. **Gemini AI UGC Master Prompt Generator (`scripts/generate_ugc_prompt.py`):**
   - Tự động nhìn ảnh Multimodal + Tên sản phẩm để sinh Master Prompt 10s chuẩn theo `omni-ugc-creator.md`.
   - Khóa cứng cấu trúc 2 bước (0–3s Hook & 3–10s Demo) với lời thoại Tiếng Việt tự nhiên chuẩn UGC TikTok/Reels.

---

## 🔐 Cấu Hình Bảo Mật Môi Trường (.env)

Dự án **không** hardcode API key hay Webhook URL trong mã nguồn public. Bạn cần cấu hình:

1. Copy `.env.example` thành `.env` ở thư mục gốc dự án.
2. Điền `GEMINI_API_KEY` (lấy tại [Google AI Studio](https://aistudio.google.com/apikey)).
3. Deploy `scripts/google_apps_script.js` thành Google Apps Script Web App của riêng bạn (Deploy → New deployment → Web app), copy URL `.../exec` dán vào `OMNI_GAS_WEBHOOK_URL` trong `.env`.
4. Mở popup của Chrome Extension (bấm icon tiện ích) và dán cùng URL Webhook đó vào ô cấu hình, bấm "Lưu Cấu Hình".

> File `.env` đã nằm trong `.gitignore` nên sẽ **KHÔNG BAO GIỜ** bị commit lên Git.

---

## 📁 Cấu Trúc Dự Án (Project Structure)

```text
Omni-Video/
├── omni-ugc-creator.md          # Quy chuẩn Master Prompt UGC 10s cho Gemini Omni
├── README.md                    # Tài liệu hướng dẫn hệ thống
├── .env.example                 # File mẫu cấu hình biến môi trường
├── Import.command              # 🚀 File 1-Click Import CSV & đồng bộ dữ liệu
├── Prompt.command              # 🎬 File 1-Click sinh Master Prompt hàng loạt bằng Gemini AI
├── characters/                  # 👤 Thư mục chứa hình ảnh nhân vật/KOLs mẫu (Nam, Nữ)
├── sample_media/                # 🎥 Thư mục chứa các video & hình ảnh mẫu thử nghiệm
├── data/                        # 📊 Thư mục chứa các file dữ liệu CSV xuất từ Shopee Affiliate
├── scripts/                     # ⚙️ Thư mục chứa toàn bộ mã nguồn xử lý & backend
│   ├── google_apps_script.js    # Mã nguồn Google Apps Script (Webhook & Google Sheets API)
│   ├── import_csv_to_gsheet.py  # Script Python import file CSV & lọc trùng sâu
│   ├── generate_ugc_prompt.py   # Script Gemini AI Multimodal sinh Master Prompt 10s
│   ├── auto_organize_downloads.py # Script tự động di chuyển ảnh vào Product_Assets/<Mã_SP>/
│   ├── omni_native_host.py      # Native Messaging Host Python (Di chuyển ảnh 0.1s)
│   └── run_native_host.sh       # Shell script wrapper khởi chạy Native Host trên macOS
├── chrome-extension/            # 🧩 Tiện ích mở rộng Chrome
└── Product_Assets/              # 📦 Thư mục lưu trữ ảnh/video nguyên liệu sản phẩm
    └── <Mã_SP>/                 # Thư mục riêng của từng sản phẩm chứa ảnh HD & master_prompt.txt
```

---

## 🚀 Quy Trình Sử Dụng 2 Bước Nhanh Gọn

1. **Nhấp đúp `Import.command`:** Đồng bộ file CSV và chuyển toàn bộ ảnh từ Downloads về `Product_Assets/<Mã_SP>/`.
2. **Nhấp đúp `Prompt.command`:** Gemini AI tự động soi ảnh + thông tin SP để tạo Master Prompt 10s tại `Product_Assets/<Mã_SP>/master_prompt.txt`.
