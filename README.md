# 🎬 Omni Video — Sản phẩm Shopee → video UGC 10 giây

Lấy ảnh + thông tin sản phẩm Shopee, ghi lên Google Sheet (tab `src_omni`), sinh kịch bản (Master Prompt) bằng Gemini, tạo video dọc 9:16 trên **Google Flow** (Omni 1.1 Flash) rồi cất thành phẩm về ổ NAS. Video Omni đăng trang **YenYen Deals**.

> Luật làm việc, kiến trúc chi tiết và lệnh dòng lệnh: xem [CLAUDE.md](CLAUDE.md).

---

## 🚀 Dùng hằng ngày

| Bước | Anh làm | Kết quả |
|---|---|---|
| 0. Lấy sản phẩm | Trên trang Shopee, rê chuột lên ảnh nét nhất, bấm **`Alt + S`** | Ảnh + `info.json` vào `Product_Assets/<Mã_SP>/`, dòng mới trên tab `src_omni` |
| 1. Nhập liệu | Nhấp đúp **`Import.command`** | Gom ảnh từ Tải xuống, nhập CSV Shopee Affiliate (`data/`), tự điền link `s.shopee.vn` từ bảng chung `aff_links` (chỉ ô trống) |
| 2. Kịch bản | Nhấp đúp **`Prompt.command`** | `Product_Assets/<Mã_SP>/<Mã_SP>.txt` + ảnh nhân vật (1 lượt Gemini / SP) |
| 3. Video | Mở dự án Flow (vd **Omni-Video**), ô câu lệnh trống → bấm extension → **Tạo video** ở 1 sản phẩm | Extension dán ảnh + kịch bản, bấm Tạo, Phê duyệt **15 credit**, chờ, tải `<Mã_SP>.mp4` về `Product_Assets/<Mã_SP>/` (Chrome hỏi Save thì bấm Save) |
| 4. Cất | Xem video, ổn thì nhấp đúp **`Move.command`** | Thư mục SP chuyển về `/Volumes/Media/Omni-Video/<Mã_SP>/`, Sheet ghi "Đã tạo Video" + đường dẫn |

- Mỗi lần **Tạo video** chỉ làm 1 sản phẩm; để tab Flow mở đến khi tải xong. Bước nào kẹt thì Flow hiện thông báo đỏ — làm tay tiếp từ bước đó.
- **Dự phòng:** `Video.command` sinh video bằng Gemini Omni API (trả phí, hỏi PIN `OMNI_SECURITY_PIN`).
- Video lỗi: xoá / đổi tên file `.mp4` trong thư mục SP trước khi Move, sinh lại kịch bản bằng `python scripts/generate_ugc_prompt.py <Mã_SP>` nếu cần.

## 🧩 Cài extension Chrome (1 lần)

1. `chrome://extensions` → bật **Developer mode** → **Load unpacked** → chọn thư mục `chrome-extension/`.
2. Native host `com.omni.video.curator` (`~/Library/Application Support/Google/Chrome/NativeMessagingHosts/`) trỏ tới `scripts/omni_native_host.py`.
3. Sau mỗi lần cập nhật code extension: bấm **Reload** ở `chrome://extensions` rồi tải lại trang Flow.

## ⚙️ Cấu hình

- `.env` (không commit, mẫu ở `.env.example`): `GEMINI_API_KEY`, `GEMINI_OMNI_API_KEY`, `OMNI_SECURITY_PIN`.
- `config/service_account.json` (không commit): Google Sheets + Drive API.
- `config/prompt_rules.json`: luật chung nạp vào mọi kịch bản (one-take 10s, sản phẩm cầm sẵn từ đầu, không chữ / logo, giọng miền Nam…).

## 📁 Cấu trúc

```text
Omni-Video/
├── Import.command / Prompt.command / Move.command / Video.command   # 1-Click macOS
├── chrome-extension/      # Alt+S lấy ảnh Shopee; popup "Tạo video" + flow_page.js cho Google Flow
├── scripts/
│   ├── omni_native_host.py        # Native host: nhận ảnh, gửi file cho Flow, thu video tải về
│   ├── sheet_sync.py              # Google Sheets API v4 (tab src_omni, đọc/ghi theo tên cột)
│   ├── import_csv_to_gsheet.py    # Nhập CSV Shopee Affiliate
│   ├── auto_organize_downloads.py # Gom ảnh Tải xuống vào Product_Assets
│   ├── fill_aff_links.py          # Điền link s.shopee.vn từ tab aff_links
│   ├── generate_ugc_prompt.py     # Sinh Master Prompt (Gemini)
│   ├── flow_helper.py             # Chọn / gửi ảnh + kịch bản cho Flow, thu video
│   ├── generate_omni_video.py     # Sinh video bằng API (dự phòng)
│   ├── archive_completed_videos.py, video_qa_analyzer.py, prompt_evolution_engine.py  # Move + QA
│   └── drive_sync.py              # Trao đổi file với Spark qua Drive API v3
├── config/                # prompt_rules.json, global_learned_rules.json (bài học QA), service_account.json
├── characters/            # Ảnh nhân vật Nu-25t, Nu-23t, Nam-25t (không commit)
├── data/                  # CSV Shopee Affiliate (không commit)
├── Product_Assets/        # Nguyên liệu từng SP (không commit)
└── tests/                 # pytest — chạy: python -m pytest tests/
```
