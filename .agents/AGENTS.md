# Project Rules & Customizations for Omni-Video

- **ALWAYS DISCUSS BEFORE EXECUTION (BẮT BUỘC THẢO LUẬN TRƯỚC KHI THỰC HIỆN)**:
  - Trước khi thực hiện bất kỳ thay đổi nào về mã nguồn, cấu trúc kịch bản prompt, quy trình tự động hóa hay sửa đổi file trong dự án, Assistant BẮT BUỘC phải giải thích nguyên nhân, phương án triển khai và HỎI Ý KIẾN / THẢO LUẬN với người dùng trước.
  - Tuyệt đối KHÔNG tự ý chỉnh sửa code hoặc thực thi lệnh thay đổi dự án khi chưa nhận được sự xác nhận và đồng ý từ người dùng.

- **GIT: CHỈ NHÁNH RIÊNG + PULL REQUEST (luật chung 4 repo, 11/10/2026)**:
  - Không push thẳng `main`; `main` chỉ đổi khi anh Kha bấm Merge trên GitHub.
  - Cấm `git commit -am` / `git add -A` / `git add .`; chỉ phiên "Thực thi – Omni-Video" được commit/push.
  - Chi tiết: `.agents/rules/git_branch_pr_only.md`.

- **ALWAYS USE GOOGLE DRIVE API V3 FOR SPARK (GIAO TIẾP VỚI SPARK 100% QUA GOOGLE DRIVE API V3)**:
  - Mọi thao tác trao đổi dữ liệu hai chiều, đọc/ghi nhật ký (`anti-spark_omni.md`), sổ tay ý tưởng & nhiệm vụ (`IDEAS.md`) với Spark BẮT BUỘC 100% thực hiện qua Google Drive API v3 (`scripts/drive_sync.py`).
  - Hoàn toàn độc lập, tuyệt đối KHÔNG phụ thuộc hay truy cập qua đường dẫn thư mục đồng bộ cục bộ trên macOS (`/Users/khan/Library/CloudStorage/...`).

