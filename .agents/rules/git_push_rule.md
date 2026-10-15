# Quy Tắc Git (theo luật chung các repo — nguồn: ~/Developer/Ecosystem-Hub/docs/LUAT_CHUNG.md, luật 1)

1. **Chỉ commit trên máy** (`main`). Không tạo nhánh riêng / Pull Request.
2. **Không tự push.** 21:00 anh Kha bấm `~/Developer/Ecosystem-Hub/commands/push_all.command` để đẩy `main` của mọi repo sạch; hoặc anh nhắn "đẩy" → quét bí mật rồi push thẳng `main`. Ban ngày không hỏi / nhắc anh "đẩy".
3. **Trước khi push:** quét không lọt `.env`, `config/service_account.json`, token, cookie, `browser_profiles`.
4. **Cấm `git commit -am` / `git add -A` / `git add .`:** luôn `git add` từng file.
5. Chỉ phiên "Thực thi – Omni-Video" được commit trong repo này. Cuối mỗi việc không để file sửa dở chưa commit.
