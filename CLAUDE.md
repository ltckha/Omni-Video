# CLAUDE.md — Luật làm việc trong repo Omni-Video

> Chào Claude, bạn đang cùng Kha Lưu (Project Owner) vận hành Omni-Video. Luật chung mọi repo: `~/Developer/Ecosystem-Hub/docs/LUAT_CHUNG.md` (thắng file này nếu lệch).
> **Kiến trúc, sơ đồ, quy trình, đọc / ghi gì: [`docs/KIEN_TRUC.md`](docs/KIEN_TRUC.md)** — nguồn duy nhất, đổi cấu trúc thì sửa file đó cùng commit. Hướng dẫn dùng / cài đặt: `README.md`.

## 1. Cách làm việc
1. **Thảo luận trước khi làm:** sửa code, thêm module, đổi cấu hình, chạy lệnh thay đổi dự án → trình bày giải pháp và được anh Kha đồng ý trước. Việc mới cần anh nói "làm" (luật chung 10). Không tự đổi luồng dữ liệu.
2. **Git (luật chung 1):** chỉ commit trên `main`, không nhánh / PR, không tự push (máy tự đẩy 2:30; anh nhắn "đẩy" thì quét bí mật rồi push `main`). `git add` từng file, cấm `-am` / `-A` / `.`. Cuối mỗi việc cây làm việc sạch.
3. **Một phiên thực thi:** chỉ phiên "Thực thi – Omni-Video" sửa code + commit repo này. Việc đụng repo khác → nhắn phiên của repo đó.
4. **Kiểm thử bắt buộc** sau mỗi lần sửa: `python -m pytest tests/` (0 mạng, 0 Gemini). Không gọi Gemini chỉ để thử.
5. **Thay đổi giao diện / khung hình / hiệu ứng thị giác:** tạo ảnh xem trước cho anh duyệt.

## 2. Luật dữ liệu
- **Google Sheet** (Spreadsheet `1Xg67qhp1J_Izt7v5uDKRgKjdEZapX9giKJ_ym0OMJN4`): đọc / ghi theo tên cột hàng 1, chỉ ô đổi (`write_changed_cells`). Tab `src_omni` (tên cũ `Omni-Video`; thiếu cả hai thì báo lỗi dừng, không lấy tab khác). Tab / cột mới: snake_case tiếng Anh.
- **Đổi hàng loạt > 10 dòng** trên Sheet: chạy thử, báo anh số dòng, có xác nhận mới ghi.
- **Brand:** nguồn duy nhất `Auto-Video-Factory/knowledge/brands/` → tab `brands` (chỉ đọc). Video Omni (video AI) mặc định **YenYen Deals** (`official_name` của `yenyen_deals`); đọc lỗi thì để trống. Không viết cứng tên brand.
- **Shopee:** video Omni là video AI → **không đăng Shopee Video** (anh Kha 18/10; Video-Post chặn kênh Shopee cho `src_omni`).
- **`product_code`:** Omni không điền (video YenYen Deals không phải hàng Hiệu giày Hải Nancy), không ghi đè ô đã có.
- **`shopee_link`:** chỉ điền ô trống / chưa phải `s.shopee.vn`, không đè link tiếp thị.

## 3. Luật Gemini & video
- **Khoá:** lấy qua `scripts/omni_env.py` — `.env` thắng `~/.zshrc`, ưu tiên `GEMINI_OMNI_API_KEY`. Khoá gửi trong header `x-goog-api-key`, không bao giờ trong URL. Kiểm chứng chỉ SSL đầy đủ (certifi). Ảnh gửi AI thu về cạnh dài 1600 px.
- **Model kịch bản:** `gemini-3.8-flash` ➔ `3.6-flash` ➔ `3.7-flash` ➔ `3.5-flash-lite` ➔ `2.5-flash`; cấm `-preview`; không dùng `gemini-3.5-flash`.
- **Luật prompt chung:** `config/prompt_rules.json` (nạp vào mọi kịch bản; không đặt luật riêng 1 kịch bản ở đây).
- **Google Flow:** 1 cú bấm / 1 video do anh chọn, không chạy lô; giữ bước Phê duyệt 15 credit; gặp CAPTCHA thì dừng. Chrome của anh chỉ dùng khi anh cho phép (luật chung 12).
- Phần đã lưu trữ (video API, QA Gemini, Spark Drive): `archive/README.md`.
