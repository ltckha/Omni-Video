# CLAUDE.md — Luật riêng repo Omni-Video

> Chào Claude, bạn đang cùng Kha Lưu (Project Owner) vận hành Omni-Video.
> **Luật chung mọi repo:** `~/Developer/Ecosystem-Hub/docs/LUAT_CHUNG.md` — thắng file này nếu lệch. File này chỉ ghi luật **riêng** của Omni.
> **Kiến trúc, quy trình, đọc / ghi gì:** [`docs/KIEN_TRUC.md`](docs/KIEN_TRUC.md) (nguồn duy nhất). Cài đặt: `README.md`. Phần đã lưu trữ: `archive/README.md`.

## 1. Cách làm việc
- **Thảo luận trước khi làm:** sửa code, thêm module, đổi cấu hình, chạy lệnh thay đổi dự án → trình bày giải pháp, anh Kha đồng ý rồi mới làm. Không tự đổi luồng dữ liệu.
- **Kiểm thử bắt buộc** sau mỗi lần sửa: `python -m pytest tests/` (0 mạng, 0 Gemini).
- **Thay đổi giao diện / khung hình / hiệu ứng thị giác:** tạo ảnh xem trước cho anh duyệt.
- Git, phiên thực thi, việc mới cần "làm", Chrome của anh: theo luật chung 1, 2, 10, 12.

## 2. Dữ liệu & Sheet
- Tab `src_omni` (tên cũ `Omni-Video`; thiếu cả hai thì báo lỗi dừng, không lấy tab khác). Ghi chỉ ô đổi (`write_changed_cells`). Đọc theo tên cột, đặt tên tab / cột: luật chung 4, 11.
- **Đổi hàng loạt > 10 dòng:** chạy thử, báo anh số dòng, có xác nhận mới ghi.
- **Brand mặc định YenYen Deals** cho video Omni (`official_name` của `yenyen_deals` trong tab `brands`; đọc lỗi thì để trống). Nguồn brand: luật chung 3.
- **Không đăng Shopee Video:** video Omni là video AI (anh Kha 18/10; Video-Post chặn kênh Shopee cho `src_omni`).
- **`product_code`:** Omni không điền, không ghi đè ô đã có.
- **`shopee_link`:** chỉ điền ô trống / chưa phải `s.shopee.vn`, không đè link tiếp thị.

## 3. Gemini & video
- **Khoá:** qua `scripts/omni_env.py` — `.env` thắng `~/.zshrc`, ưu tiên `GEMINI_OMNI_API_KEY`; gửi header `x-goog-api-key`, không bao giờ trong URL; kiểm chứng chỉ SSL đầy đủ (certifi); ảnh gửi AI thu về cạnh dài 1600 px. Gọi tiết kiệm: luật chung 5.
- **Model kịch bản:** `gemini-3.8-flash` ➔ `3.6-flash` ➔ `3.7-flash` ➔ `3.5-flash-lite` ➔ `2.5-flash`; cấm `-preview`; không dùng `gemini-3.5-flash`.
- **Luật prompt chung:** `config/prompt_rules.json` (nạp vào mọi kịch bản; không đặt luật riêng 1 kịch bản ở đây).
- **Google Flow:** 1 cú bấm / 1 video do anh chọn, không chạy lô; giữ bước Phê duyệt 15 credit; gặp CAPTCHA thì dừng.
