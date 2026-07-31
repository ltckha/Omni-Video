---
name: omni-ugc-creator
description: Tạo Master Prompt video 10 giây phong cách UGC/Review từ các nguồn ảnh (Sản phẩm chính, Đạo cụ/Sản phẩm phụ, Nhân vật, Bối cảnh) cho Gemini Omni. Hỗ trợ linh hoạt khi thiếu nguyên liệu để Omni tự sáng tạo.
---
# Omni UGC Video Creator (Multi-Asset Review)

Tạo Master Prompt video 10 giây cho Gemini Omni phong cách UGC/Review kết hợp linh hoạt các lớp ảnh: Sản phẩm chính, Đạo cụ/Sản phẩm phụ, Nhân vật và Bối cảnh.

## When to Use

Sử dụng kỹ năng này khi người dùng:
- Cung cấp hoặc yêu cầu tạo video từ các ảnh đính kèm (Sản phẩm chính + Đạo cụ/Sản phẩm phụ + Nhân vật + Bối cảnh).
- Yêu cầu tạo video AI dạng người thật review/trải nghiệm sản phẩm có nhép miệng (lip-sync) và cử chỉ tự nhiên.
- Chỉ có 1 hoặc 2 nguồn ảnh (ví dụ: chỉ có ảnh sản phẩm chính) và muốn Omni tự sáng tạo các yếu tố còn thiếu (nhân vật, đạo cụ tương tác, bối cảnh).

## Workflow 2 Bước

### BƯỚC 1: SƠ CHẾ & PHÂN LOẠI NGUYÊN LIỆU (FLEXIBLE ASSETS)
Phân loại rõ từng nguyên liệu theo 4 nhóm:
1. **Sản phẩm chính (Main Product):** Sản phẩm cốt lõi cần quảng cáo (ví dụ: keo dán giày, serum, tai nghe...).
2. **Đạo cụ / Sản phẩm phụ (Secondary Object / Prop):** Vật thể tương tác chính để minh họa công dụng sản phẩm (ví dụ: đôi giày/dép bị hỏng cần dán, làn da, điện thoại...). *Nếu không có ảnh đính kèm, yêu cầu Omni tự sáng tạo.*
3. **Nhân vật / KOL (Character):** Diện mạo, trang phục, biểu cảm của người trải nghiệm. *Nếu không có ảnh đính kèm, yêu cầu Omni tự tạo nhân vật phù hợp tệp khách hàng mục tiêu.*
4. **Bối cảnh (Environment):** Không gian diễn ra cảnh quay (vườn cây, căn bếp, góc làm việc, cửa hàng...). *Nếu không có ảnh đính kèm, yêu cầu Omni tự tạo bối cảnh chân thực.*

---

### BƯỚC 2: CÔNG THỨC KHÓA CỨNG & MASTER PROMPT UGC 10S

```text
[ATTACHED ASSETS & CREATIVE DIRECTIVES]:
- Main Product: [Image X description OR "Generate photorealistic product based on..."]
- Secondary Product / Prop: [Image X description OR "AI Creative Freedom: [e.g., worn-out sneaker needing repair]"]
- Character: [Image X description OR "AI Creative Freedom: Friendly reviewer matching target audience"]
- Environment: [Image X description OR "AI Creative Freedom: Realistic home/workshop setting matching context"]

Task: Generate a 10-second high-converting UGC review video seamlessly combining the main product, secondary prop, character, and environment.

FIXED CONSTRAINTS (STRICT):
- Video Duration: Exactly 10 seconds.
- Aspect Ratio: 9:16 Vertical format.
- Visual Consistency: Maintain 100% exact visual appearance for any attached images provided in inputs.

CREATIVE FREEDOM FOR OMNI:
- For missing/unattached assets: Full creative freedom to generate realistic, contextually appropriate character, secondary props, or environment.
- Motion & Audio: High freedom for audio lip-sync, realistic facial expressions, natural hand gestures, dynamic camera movement, and warm natural lighting.

SCENE BREAKDOWN (10 SECONDS):
0-3s (Hook & Problem):
- Visual: [Character interacting with problem/prop, e.g., showing damaged item or pain point]
- Subtitle/Voiceover (Vietnamese): [Catchy opening hook statement]

3-10s (Solution & Product Demo):
- Visual: [Action shot showing character using main product on prop/problem with clear result/transformation]
- Subtitle/Voiceover (Vietnamese): [Core product benefit & value statement]

STYLE GUIDELINES:
- Photorealistic UGC review style, natural handheld camera feel, fluid motion, 60fps, realistic audio lip-sync.
```

---

## Gotchas
- **Bảo toàn tính nhất quán:** Nếu người dùng có cung cấp ảnh nguyên liệu nào, bắt buộc giữ 100% diện mạo/chi tiết của ảnh đó trong video.
- **Tự động lấp đầy:** Khi thiếu ảnh nguyên liệu nào (nhân vật, bối cảnh, đạo cụ phụ), ghi rõ câu lệnh yêu cầu Omni tự sáng tạo để đảm bảo khung hình tự nhiên, hợp ngữ cảnh.
- **Ngôn ngữ:** Chỉ dẫn bối cảnh/chuyển động/đạo cụ viết bằng tiếng Anh; giữ phần lời thoại/phụ đề bằng tiếng Việt ngắn gọn.
