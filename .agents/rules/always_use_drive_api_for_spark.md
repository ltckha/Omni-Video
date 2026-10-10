# ALWAYS USE GOOGLE DRIVE API V3 FOR SPARK COMMUNICATION (GIAO TIẾP VỚI SPARK 100% QUA GOOGLE DRIVE API V3)

> **Cập nhật:** 15/09/2026

## 1. Nguyên tắc Cốt lõi
- **100% Cloud-First qua Google Drive API v3:**
  - Mọi thao tác đọc, ghi, cập nhật dữ liệu, nhật ký phối hợp (`anti-spark_omni.md`), sổ tay ý tưởng & nhiệm vụ (`IDEAS.md`) hoặc trao đổi tài nguyên với Spark BẮT BUỘC phải thực hiện thông qua **Google Drive API v3** (sử dụng Service Account tại `config/service_account.json` hoặc module `scripts/drive_sync.py`).
- **Tuyệt đối KHÔNG phụ thuộc vào đường dẫn cục bộ trên macOS:**
  - Không được hardcode hay đọc/ghi trực tiếp qua thư mục local sync như `/Users/khan/Library/CloudStorage/GoogleDrive-ltckha@gmail.com/...`.
  - Mọi hệ thống, script tự động hóa và trợ lý AI phải vận hành hoàn toàn độc lập với ứng dụng Google Drive for Desktop của macOS.

## 2. Tiêu chuẩn Kỹ thuật
- **Authentication:** Sử dụng Service Account `config/service_account.json` với Scope:
  - `https://www.googleapis.com/auth/drive`
- **Module trung tâm:** Sử dụng `scripts/drive_sync.py` để thực hiện:
  - Đọc file: `read_drive_file(filename)`
  - Ghi/Cập nhật file: `write_drive_file(filename, content)`
  - Ghi nhật ký: `append_to_anti_spark_log(log_entry)`
