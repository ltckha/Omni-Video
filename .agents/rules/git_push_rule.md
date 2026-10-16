# Quy Tắc Git (theo luật chung các repo — nguồn: ~/Developer/Ecosystem-Hub/docs/LUAT_CHUNG.md, luật 1)

1. **Chỉ commit trên máy** (`main`). Không tạo nhánh riêng / Pull Request.
2. **Không tự push.** Máy tự đẩy `main` của mọi repo sạch lúc 2:30 sáng (launchd `vn.giayhainancy.daygit` chạy `~/Developer/Ecosystem-Hub/commands/push_all.command --tu-dong`; repo còn file sửa dở, không ở `main`, lệch origin hoặc nghi bí mật thì bị bỏ qua, 8:00 báo anh); hoặc anh nhắn "đẩy" → quét bí mật rồi push thẳng `main`. Ban ngày không hỏi / nhắc anh "đẩy".
3. **Trước khi push:** quét không lọt `.env`, `config/service_account.json`, token, cookie, `browser_profiles`.
4. **Cấm `git commit -am` / `git add -A` / `git add .`:** luôn `git add` từng file.
5. Chỉ phiên "Thực thi – Omni-Video" được commit trong repo này. Cuối mỗi việc không để file sửa dở chưa commit.
