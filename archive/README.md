# Lưu trữ (21/10/2026, anh Kha duyệt "Sắp xếp lại hệ thống")

Không còn dùng hằng ngày, gỡ khỏi menu. Lấy lại thì `git mv` về chỗ cũ (`scripts/`, `config/`, `tests/`, gốc repo).

| File | Trước đây làm gì | Thay bằng |
|---|---|---|
| `scripts/generate_omni_video.py` (nút `Video.command` đã xoá 31/10, lấy lại từ git) | Sinh video bằng Gemini Omni API (trả phí, PIN) | Google Flow — extension "Tạo video" |
| `scripts/video_qa_analyzer.py`, `scripts/prompt_evolution_engine.py`, `config/global_learned_rules.json` | Move chế độ [2]: Gemini chấm video, tự học prompt (bài học ghi ra nhưng không nơi nào đọc lại) | Anh xem video trước khi bấm Move |
| `scripts/drive_sync.py` | Trao đổi `anti-spark_omni.md`, `IDEAS.md` với Spark qua Drive API v3 | Hộp thư Cowork chung (luật chung 9) |
| `tests/test_omni_video_generator.py`, `tests/test_drive_sync.py` | Test của các file trên (không chạy nữa) | — |

## Đường Shopee tiếp thị liên kết — TẠM CẤT (1/11/2026, anh Kha "làm" qua Phân tích · Xưởng video)

Video AI nay chỉ làm **hàng tiệm** Hiệu giày Hải Nancy (`Shop_Products.command`, `Fill_Queue.command`, lịch 13:30). Đường Shopee (10 bước tay / 2 ngày, không còn món làm dở) **cất, chưa xoá**. Tab Sheet `src_omni` để nguyên (Video-Post vẫn đọc video cũ).

| File cất | Trước đây làm gì |
|---|---|
| `Import_Products.command` | Gom ảnh Downloads, nhập CSV Shopee vào `src_omni`, điền link tiếp thị, tạo file Custom Link, nhắc mùa, bảng gợi ý |
| `Write_Prompts.command` | Sinh kịch bản bằng Gemini cho món Shopee |
| `Move_To_NAS.command` | Chuyển thư mục món có video sang NAS `Media/Omni-Video/`, cập nhật Sheet |
| `scripts/import_csv_to_gsheet.py`, `auto_organize_downloads.py`, `fill_aff_links.py`, `make_batch_links.py`, `rank_products.py`, `rank_offers.py`, `season.py`, `make_variants.py`, `generate_ugc_prompt.py`, `archive_completed_videos.py`, `contact_sheet.py` | Các bước của 3 nút trên |
| `config/seasons.json`, `config/templates/shopee_batch_custom_links.xlsx` | Lịch mùa, mẫu file Custom Link |
| `tests/test_<tên script>.py` | Test của các script trên |
| `chrome-extension/content.js` | Extension: chụp ảnh SP Shopee bằng Alt+S / chuột phải (manifest, background, popup đã bỏ phần này từ v2.0.0) |

Vẫn giữ trong repo: `config/prompt_rules.json` (CLAUDE.md §3 còn nhắc), `scripts/sheet_sync.py` (hàng tiệm đọc Sheet qua đây).

**Lấy lại:**
1. `git mv` từng file về chỗ cũ (gốc repo, `scripts/`, `tests/`, `config/`, `chrome-extension/`).
2. Extension: thêm lại vào `manifest.json` khối `content_scripts` cho `*://shopee.vn/*` (content.js), `host_permissions` shopee / susercontent, quyền `contextMenus`, lệnh `save-shopee-image` (Alt+S). Lấy phần lưu ảnh cũ của `background.js` và `popup.html` từ git (bản v1.9.0, commit trước 1/11).
3. Native host: lấy lại nhánh lưu ảnh + `sync_product_to_sheet` của `scripts/omni_native_host.py` từ git.
