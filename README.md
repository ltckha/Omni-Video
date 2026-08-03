# 🎬 Omni Video - Shopee Asset Curator & UGC Prompt Generator

Hệ thống tự động hóa toàn diện quy trình thu thập nguyên liệu sản phẩm từ Shopee, lưu trữ phân loại theo mã sản phẩm, đồng bộ Google Sheets, sinh **Master Prompt Video UGC 10 giây** cho **Gemini Omni** và tự động lưu trữ video hoàn thành về ổ đĩa Media.

---

## 📌 Tính Năng Nổi Bật

1. **Chrome Extension Curator (1-Click Shortcut `Alt + S`):**
   - Di chuột lên ảnh sản phẩm HD trên Shopee và nhấn `Alt + S`.
   - Tự động bóc tách **Mã sản phẩm (itemId)**, **Tên sản phẩm**, **Giá**, **Doanh thu / Đã bán** và **Tên cửa hàng (Shop)**.
   - Tải ảnh HD nguyên bản (`.webp` / `.png` / `.jpg`) về máy.

2. **Native Messaging Host (macOS 0.1s Auto-Move):**
   - Kích hoạt tiến trình Python siêu nhẹ bật lên đúng 0.1s để di chuyển file ảnh vào đúng thư mục dự án: `Product_Assets/<Mã_SP>/`.

3. **Google Sheets Sync & Lọc Trùng Sâu:**
   - Bảo toàn dữ liệu 9 cột gốc từ CSV. Tự động cập nhật `Link ảnh CDN chọn lọc`, `File ảnh lưu local` và bảo vệ trạng thái `Đã tạo Video`.

4. **Gemini AI UGC Master Prompt Generator (`scripts/generate_ugc_prompt.py`):**
   - Tự động nhìn ảnh Multimodal + Tên sản phẩm để sinh Master Prompt 10s chuẩn theo `omni-ugc-creator.md`.
   - Tự động chọn nhân vật Nam/Nữ phù hợp và copy ảnh nhân vật vào thư mục sản phẩm.

5. **1-Click Clean & Move Completed Video Folders (`Move.command`):**
   - Tự động quét các thư mục sản phẩm đã tạo xong video `.mp4`.
   - Tự động dọn dẹp sạch sẽ: xóa file ảnh nhân vật mẫu và file `info.json`.
   - Di chuyển toàn bộ thư mục sản phẩm hoàn thành về lưu trữ tại `/Volumes/Media/Omni-Video/Product_Assets/`.

---

## 📁 Cấu Trúc Dự Án (Project Structure)

```text
Omni-Video/
├── omni-ugc-creator.md          # Quy chuẩn Master Prompt UGC 10s cho Gemini Omni
├── README.md                    # Tài liệu hướng dẫn hệ thống
├── .env.example                 # File mẫu cấu hình biến môi trường
├── Import.command              # 🚀 File 1-Click Import CSV & đồng bộ dữ liệu
├── Prompt.command              # 🎬 File 1-Click sinh Master Prompt hàng loạt bằng Gemini AI
├── Move.command                # 🚚 File 1-Click dọn dẹp & di chuyển SP đã tạo xong MP4 về ổ đĩa Media
├── characters/                  # 👤 Thư mục chứa hình ảnh nhân vật/KOLs mẫu (Nam, Nữ)
├── sample_media/                # 🎥 Thư mục chứa các video & hình ảnh mẫu thử nghiệm
├── data/                        # 📊 Thư mục chứa các file dữ liệu CSV xuất từ Shopee Affiliate
├── scripts/                     # ⚙️ Thư mục chứa toàn bộ mã nguồn xử lý & backend
│   ├── google_apps_script.js    # Mã nguồn Google Apps Script (Webhook & Google Sheets API)
│   ├── import_csv_to_gsheet.py  # Script Python import file CSV & lọc trùng sâu
│   ├── generate_ugc_prompt.py   # Script Gemini AI Multimodal sinh Master Prompt 10s
│   ├── archive_completed_videos.py # Script tự động dọn dẹp & di chuyển SP có MP4 về /Volumes/Media/...
│   ├── auto_organize_downloads.py # Script tự động di chuyển ảnh vào Product_Assets/<Mã_SP>/
│   ├── omni_native_host.py      # Native Messaging Host Python (Di chuyển ảnh 0.1s)
│   └── run_native_host.sh       # Shell script wrapper khởi chạy Native Host trên macOS
├── chrome-extension/            # 🧩 Tiện ích mở rộng Chrome
└── Product_Assets/              # 📦 Thư mục lưu trữ ảnh/video nguyên liệu sản phẩm
```

---

## 🚀 Quy Trình Sử Dụng 3 Bước Nhanh Gọn

1. **Nhấp đúp `Import.command`:** Đồng bộ file CSV và chuyển toàn bộ ảnh từ Downloads về `Product_Assets/<Mã_SP>/`.
2. **Nhấp đúp `Prompt.command`:** Gemini AI tự động soi ảnh + thông tin SP để tạo Master Prompt 10s tại `Product_Assets/<Mã_SP>/master_prompt.txt` và copy ảnh nhân vật vào.
3. **Nhấp đúp `Move.command`:** Sau khi dựng video xong và lưu file `.mp4` vào thư mục sản phẩm, nhấp đúp `Move.command` để tự động xóa ảnh nhân vật, xóa `info.json` và di chuyển thư mục về `/Volumes/Media/Omni-Video/Product_Assets/`.

---

## 💡 Roadmap & Ý Tưởng Phát Triển Tương Lai

1. **Hệ Thống Tự Đánh Giá, Tự Học & Nâng Cấp Prompt Video Vòng Lặp Đóng (Closed-Loop Video QA & Prompt Self-Evolution Engine):**
   - **Đánh giá chất lượng Video (Video QA):** Đưa video `.mp4` sau khi khởi tạo qua Gemini Vision API để AI tự động thẩm định, phát hiện các lỗi dị dạng, méo sản phẩm, rác điểm ảnh (morphing) hoặc sai nhận diện nhân vật.
   - **Tự học & Tiến hóa Prompt (Prompt Self-Evolution):** Phân tích các kết quả QA video để tự động đúc kết bài học kinh nghiệm, liên tục tinh chỉnh và nâng cấp cấu trúc Prompt theo thời gian mà không cần con người can thiệp.
   - **Kịch bản liền mạch tự nhiên (Seamless Single-Shot Narrative):** Tích hợp phong cách kể chuyện liền mạch, trôi chảy từ đầu đến cuối vào hệ thống tự học (thay vì gượng ép chia cứng các khối Hook / Solution thô cứng), giúp video UGC sinh ra vừa chuẩn đẹp, vừa đạt độ hoàn thiện cao nhất.
