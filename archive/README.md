# Lưu trữ (21/10/2026, anh Kha duyệt "Sắp xếp lại hệ thống")

Không còn dùng hằng ngày, gỡ khỏi menu. Lấy lại thì `git mv` về chỗ cũ (`scripts/`, `config/`, `tests/`, gốc repo).

| File | Trước đây làm gì | Thay bằng |
|---|---|---|
| `Video.command`, `scripts/generate_omni_video.py` | Sinh video bằng Gemini Omni API (trả phí, PIN) | Google Flow — extension "Tạo video" |
| `scripts/video_qa_analyzer.py`, `scripts/prompt_evolution_engine.py`, `config/global_learned_rules.json` | Move chế độ [2]: Gemini chấm video, tự học prompt (bài học ghi ra nhưng không nơi nào đọc lại) | Anh xem video trước khi bấm Move |
| `scripts/drive_sync.py` | Trao đổi `anti-spark_omni.md`, `IDEAS.md` với Spark qua Drive API v3 | Hộp thư Cowork chung (luật chung 9) |
| `tests/test_omni_video_generator.py`, `tests/test_drive_sync.py` | Test của các file trên (không chạy nữa) | — |
