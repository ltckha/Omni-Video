# 📜 CLAUDE.md - SỔ TAY VẬN HÀNH DỰ ÁN OMNI-VIDEO

> **Chào Claude, bạn đang cùng Kha Lưu (Project Owner) vận hành hệ thống Omni-Video.**  
> Tài liệu này là **Hiến pháp tối cao** bắt buộc bạn phải đọc và tuân thủ 100% trong suốt quá trình làm việc trong repository này.

---

## 🚨 1. CÁC QUY TẮC CỐT LÕI HÀNG ĐẦU (STRICT GOVERNANCE RULES)

1. **LUÔN LUÔN THẢO LUẬN & THỐNG NHẤT VỚI ANH KHA TRƯỚC KHI THỰC HIỆN:**
   - Trước khi sửa code, thêm module, đổi cấu hình, hay chạy lệnh, **bắt buộc phải trình bày giải pháp kỹ thuật chi tiết và được anh Kha đồng ý trước**.
   - Không tự ý suy đoán, không tự tiện thay đổi luồng dữ liệu.

2. **GIT — THEO LUẬT CHUNG (`~/Developer/Ecosystem-Hub/docs/LUAT_CHUNG.md` luật 1):**
   - Chỉ commit trên máy (`main`); không nhánh riêng / Pull Request; không tự push.
   - Máy tự đẩy lúc 2:30 sáng (launchd `vn.giayhainancy.daygit` chạy `~/Developer/Ecosystem-Hub/commands/push_all.command --tu-dong`; repo còn file sửa dở / lệch origin / nghi bí mật thì bị bỏ qua, 8:00 báo anh), hoặc anh nhắn **"đẩy"** → quét bí mật (`.env`, `config/service_account.json`, token, cookie) rồi push thẳng `main`. Ban ngày không hỏi / nhắc anh "đẩy".
   - Cấm `git commit -am` / `git add -A` / `git add .`. Luôn `git add` từng file. Cuối mỗi việc không để file sửa dở chưa commit.

3. **MÔ HÌNH PHỐI HỢP:**
   - **Claude Cowork (Cloud):** Đảm nhận tư duy vĩ mô: Quy hoạch kiến trúc, phản biện logic mã nguồn, viết prompt Gemini Omni, lập kế hoạch hành động.
   - **Claude Code (Local Mac M4):** Kỹ sư trưởng thực thi hiện trường: Chạy lệnh terminal, kích hoạt môi trường ảo Python `venv`, chạy script di chuyển file, gọi API.

4. **MỖI REPO MỘT PHIÊN THỰC THI:**
   - Chỉ phiên **"Thực thi – Omni-Video"** được sửa code và commit trong repo này.
   - Việc cần đụng repo khác (Auto-Video-Factory, Video-Post, HNC_Master) → nhắn phiên Thực thi của repo đó, không tự sửa chéo.

5. **TRI THỨC BRAND — NGUỒN DUY NHẤT LÀ AUTO-VIDEO-FACTORY:**
   - Tên chuẩn, mã brand, bí danh, luật brand (vd. cấm chữ "ASMR") chỉ lấy từ `Auto-Video-Factory/knowledge/brands/`. Cần gì về brand → hỏi/nhắn phiên Thực thi AVF.
   - Tab Sheet `brands` sinh từ nguồn đó; repo này chỉ đọc. Video Omni (video AI) mặc định đăng **YenYen Deals** (anh Kha chốt 15/10/2026): `determine_default_brand` trả `official_name` của `yenyen_deals` đọc từ tab `brands` theo tên cột; đọc lỗi thì để trống + ghi log. Không thêm brand viết cứng.

---

## 🎬 2. TỔNG QUAN KIẾN TRÚC OMNI-VIDEO

Hệ thống tự động hóa thu thập nguyên liệu sản phẩm Shopee, đồng bộ Google Sheets, sinh Master Prompt UGC 10s và video cho **Gemini Omni**, lưu trữ thành phẩm về ổ đĩa NAS:

1. **Chrome Extension Curator (`Alt + S`):** Di chuột lên ảnh sản phẩm Shopee, bấm `Alt + S` để tự động bóc tách Item ID, Tên sản phẩm, Giá, Đã bán, Tên Shop và tải ảnh HD nguyên bản. Không còn cấu hình Webhook (Zero Apps Script).
2. **Native Messaging Host (`scripts/omni_native_host.py`):** Tự động chuyển ảnh tải về vào đúng thư mục `Product_Assets/<Mã_SP>/`, tạo `info.json` và ghi hàng lên Sheet.
3. **Google Sheets API v4 (`scripts/sheet_sync.py`, `gspread`):** Đồng bộ trực tiếp qua Service Account `config/service_account.json` (Spreadsheet ID: `1Xg67qhp1J_Izt7v5uDKRgKjdEZapX9giKJ_ym0OMJN4`, tab `src_omni`, tên cũ `Omni-Video` vẫn đọc được). Luôn map cột theo tên header. Cột `shopee_link` (15/10/2026): cuối Import.command, `scripts/fill_aff_links.py --apply` tự điền link s.shopee.vn từ tab `aff_links` (AVF giữ) khi `aff_id = job_id`, `active = yes`; chỉ ô trống hoặc chưa phải s.shopee.vn, không đè, không xoá. Cột `season` + status `Hết mùa` (P4, 17/10/2026): `scripts/season.py` gắn mã mùa theo từ khoá tên SP (`config/mua_vu.json`), mùa đã qua thì status = "Hết mùa" (Video-Post bỏ qua), mùa quay lại thì trả "Đã tạo Video" / "Đã chọn ảnh"; chạy cuối Import.command, đổi > 10 dòng thì dừng chờ anh (`--apply --yes`). Popup extension nhắc mùa đang diễn ra / sắp tới (14 ngày). Cột `product_code` (15/10/2026): mã mẫu HNC khi video làm cho hàng Hiệu giày Hải Nancy, còn hàng Shopee tiếp thị liên kết để trống; code không tự điền và không ghi đè ô đã điền (Video-Post chép sang master để nối video với web giayhainancy.vn).
4. **Gemini AI UGC Master Prompt Generator (`scripts/generate_ugc_prompt.py`):** Phân tích ảnh đa phương thức + tên sản phẩm, chọn 1 trong 9 góc sáng tạo, nạp luật chung từ `config/prompt_rules.json`, xuất `Product_Assets/<Mã_SP>/<Mã_SP>.txt`. Model ưu tiên: `gemini-3.8-flash` ➔ `3.6-flash` ➔ `3.7-flash` ➔ `3.5-flash-lite` ➔ `2.5-flash` (cấm `-preview`; không dùng `3.5-flash` vì lượt bị đếm vào hạn mức 3.6).
5. **Sinh Video trên Google Flow (bán tự động, ưu tiên — 15 credit/video, 0 phí API):** popup extension liệt kê SP có prompt chưa có video → "Tạo video" (1 cú bấm / 1 video, anh Kha chọn 15/10/2026): `chrome-extension/flow_page.js` dán 1 lần mọi ảnh trong thư mục SP vào ô câu lệnh của dự án Flow đang mở (1 = ảnh SP lớn nhất, 2 = người mẫu — khớp Input Image 1/2 trong kịch bản, 3.. = ảnh SP còn lại, tối đa 7; ảnh > 2 MB tự thu nhỏ bằng `sips`) rồi dán kịch bản `.txt`, rồi tự bấm Tạo → Phê duyệt 15 credit → chờ video → Tải 720p (tên `<Mã_SP>.mp4`, Chrome hỏi Save thì anh bấm Save) → native host chuyển vào `Product_Assets/<Mã_SP>/` (`scripts/flow_helper.py`); Move.command vẫn tự gom `~/Downloads/<Mã_SP>.mp4`. Dự án Flow đặt sẵn video 9:16, x1, Omni 1.1 Flash. Mỗi lần 1 SP do anh chọn, không chạy lô; bước nào quá hạn thì dừng báo anh làm tay; gặp CAPTCHA thì dừng.
5b. **Sinh Video bằng API (dự phòng) (`Video.command` / `scripts/generate_omni_video.py`):** Gọi `gemini-omni-1.1-flash` với prompt `.txt` + ảnh sản phẩm + ảnh nhân vật, xuất `<Mã_SP>.mp4` dọc 9:16. API trả phí, có khóa PIN (`OMNI_SECURITY_PIN`).
6. **Clean & Move Completed Videos (`Move.command` / `scripts/archive_completed_videos.py`):** Quét các thư mục đã có video `.mp4` (cả trong `~/Downloads`), tùy chọn chạy QA (`video_qa_analyzer.py`), dọn file thừa và di chuyển thư mục về `/Volumes/Media/Omni-Video/`. Cập nhật cột Output File trên Sheet.
7. **Spark Sync (`scripts/drive_sync.py`):** Trao đổi `anti-spark_omni.md`, `IDEAS.md` với Spark 100% qua Google Drive API v3 (Service Account, scope `drive`), không dùng đường dẫn CloudStorage cục bộ (`~/Library/CloudStorage/...`). Hàm: `read_drive_file(filename)`, `write_drive_file(filename, content)`, `append_to_anti_spark_log(log_entry)`.

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
- File cấu hình: `.env` (`GEMINI_OMNI_API_KEY`, `GEMINI_API_KEY`, `OMNI_SECURITY_PIN`, ...). **Khoá Gemini riêng của Omni** (anh Kha chốt 16/10/2026): mọi lệnh gọi Gemini (sinh kịch bản, QA, video API) lấy khoá qua `scripts/omni_env.py` — `.env` thắng `~/.zshrc` (khoá chung của repo khác), ưu tiên `GEMINI_OMNI_API_KEY` rồi mới `GEMINI_API_KEY`. Các file `.command` nạp `~/.zshrc` trước, `.env` sau.
- Luật prompt dùng chung: `config/prompt_rules.json` (nạp toàn bộ vào mọi prompt — không đặt luật riêng cho một kịch bản ở đây).
- File Service Account: `config/service_account.json` (Google Sheets & Google Drive API).
- Thư mục kho lưu trữ NAS: `/Volumes/Media/Omni-Video/`.

---

## 🔁 4. QUY TRÌNH 1-CLICK HẰNG NGÀY

| Bước | Anh bấm | Script | Việc làm |
|---|---|---|---|
| 1 | `Import.command` | `auto_organize_downloads.py` ➔ `import_csv_to_gsheet.py` ➔ `fill_aff_links.py --apply` ➔ `rank_products.py` | Gom ảnh từ `~/Downloads` vào `Product_Assets/<Mã_SP>/`, nhập CSV Shopee lên tab `src_omni`, tự điền link s.shopee.vn (+ giá / % hoa hồng / shop nếu ô trống) từ `aff_links`, in gợi ý SP nên làm video xếp theo hoa hồng (đ) × lượt bán |
| 1b | `Links.command` (khi có SP chưa có link s.shopee.vn) | `make_batch_links.py` | Tạo `~/Downloads/Omni_BatchCustomLinks_<ngày giờ>.xlsx` (mẫu Shopee `config/templates/shopee_batch_custom_links.xlsx`, Sub_id1 = job_id) → anh tải lên Shopee Affiliate, thả file kết quả vào `~/agent_mailbox/auto-video-factory/affiliate/links/` → AVF nạp `aff_links` → Import.command điền `shopee_link` |
| 2 | `Prompt.command` | `generate_ugc_prompt.py` | Sinh `<Mã_SP>.txt` + copy ảnh nhân vật |
| 2b | `python scripts/make_variants.py <Mã_SP> --count 3` (khi muốn nhiều kịch bản / SP) | `make_variants.py` → `generate_ugc_prompt.py` | P6: tạo `Product_Assets/<Mã_SP>-2/`, `-3/` (copy ảnh + info.json), thêm dòng `src_omni` job_id `<Mã_SP>-N`, sinh kịch bản khác góc (1 lượt Gemini / bản; `--dry` chạy thử). Video `<Mã_SP>-N.mp4`; link tiếp thị dùng của mã gốc nếu chưa có riêng |
| 3 | Extension → **Tạo video** (dự án Flow đang mở) | `flow_page.js` + `flow_helper.py` qua native host | Dán ảnh + kịch bản, tự bấm Tạo → Phê duyệt 15 credit → chờ → Tải `<Mã_SP>.mp4` vào `Product_Assets/<Mã_SP>/` |
| 3b | `Video.command` (dự phòng) | `generate_omni_video.py` | Sinh video bằng Gemini Omni API (trả phí, có PIN) |
| 4 | `Move.command` (sau khi anh xem video) | `archive_completed_videos.py` | Dọn thư mục có `.mp4`, chuyển về `/Volumes/Media/Omni-Video/`, cập nhật Sheet |

- **Lấy sản phẩm:** trên Shopee rê chuột lên ảnh nét nhất, bấm `Alt+S` (hoặc chuột phải "Lưu ảnh SP cho Omni UGC") → extension tải ảnh, native host (`com.omni.video.curator`) chuyển vào `Product_Assets/<Mã_SP>/`, lưu `info.json`, ghi dòng lên `src_omni`.
- **Kiểm thử:** `python -m pytest tests/` (0 mạng, 0 Gemini) — bắt buộc sau mỗi lần sửa code.
- **Thay đổi giao diện / khung hình / phụ đề / hiệu ứng thị giác:** tạo ảnh xem trước cho anh duyệt trước khi áp dụng.
