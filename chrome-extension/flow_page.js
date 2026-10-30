// Omni Video - 1 cú bấm / 1 video trên dự án Google Flow (anh Kha chọn 15/10/2026):
// dán 1 lần mọi ảnh trong thư mục SP (1 = ảnh SP chính, 2 = người mẫu, 3.. = ảnh SP còn lại, tối đa 7) -> kịch bản .txt
// -> bấm Tạo -> Phê duyệt 15 credit -> chờ video xong -> Tải 720p (background đặt tên <itemId>.mp4) -> Xong.
// Mỗi lần chỉ 1 sản phẩm do anh Kha chọn; không chạy lô. Bước nào quá hạn thì dừng, báo để anh làm tay.

(function () {
  const CHIP_LABEL = "Thành phần";

  function promptBox() {
    const boxes = [...document.querySelectorAll('[role=textbox][contenteditable=true]')].filter((b) => b.offsetParent !== null);
    return boxes[boxes.length - 1] || null;
  }

  function chipCount() {
    return [...document.querySelectorAll("button")].filter(
      (b) => b.getAttribute("aria-label") === CHIP_LABEL || b.textContent.trim().startsWith(CHIP_LABEL)
    ).length;
  }

  function b64ToBytes(b64) {
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return bytes;
  }

  function paste(box, dataTransfer) {
    box.focus();
    box.dispatchEvent(new ClipboardEvent("paste", { clipboardData: dataTransfer, bubbles: true, cancelable: true }));
  }

  async function waitFor(check, timeoutMs) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      if (check()) return true;
      await new Promise((r) => setTimeout(r, 300));
    }
    return false;
  }

  // Dán cả 2 ảnh trong 1 lần (như anh Kha kéo thả 2 ảnh cùng lúc); thứ tự: ảnh SP (1) rồi người mẫu (2)
  async function pasteImages(box, files) {
    const before = chipCount();
    const dt = new DataTransfer();
    for (const file of files) dt.items.add(new File([b64ToBytes(file.b64)], file.name, { type: file.mime }));
    paste(box, dt);
    // 7 ảnh (6 giày + người mẫu) tải lên lâu hơn 2–3 ảnh → chờ tới 90 giây (30/10: 3J658N kẹt sau khi dán ảnh)
    return waitFor(() => chipCount() >= before + files.length, 90000);
  }

  function showToast(msg, isError) {
    const div = document.createElement("div");
    div.textContent = msg;
    div.style.cssText = `position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:2147483647;
      background:${isError ? "#d32f2f" : "#2e7d32"};color:#fff;padding:10px 16px;border-radius:6px;
      font:13px -apple-system,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.4);max-width:80%;`;
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 7000);
  }

  async function fill(message) {
    const box = promptBox();
    if (!box) return { status: "error", message: "Không thấy ô câu lệnh — anh mở một dự án Flow (vd Omni-Video)." };
    if (box.innerText.trim() || chipCount() > 0) {
      return { status: "error", message: "Ô câu lệnh đang có nội dung — anh xoá trống rồi bấm lại." };
    }
    const byslot = Object.fromEntries(message.files.map((f) => [f.slot, f]));
    const images = message.files.filter((f) => f.slot !== "script");  // đã xếp: SP chính, người mẫu, SP còn lại
    if (!(await pasteImages(box, images))) {
      return { status: "error", message: `Flow chưa nhận đủ ${images.length} ảnh (đang có ${chipCount()}) — anh tải lại trang Flow rồi thử lại.` };
    }
    // Flow vẽ lại ô câu lệnh khi gắn ảnh (và có thể khoá ô khi ảnh còn đang tải lên) -> tìm lại ô mới rồi dán
    // kịch bản, thử lại tới ~60 giây
    const scriptText = new TextDecoder().decode(b64ToBytes(byslot.script.b64));
    const hasScript = () => { const b = promptBox(); return b && b.innerText.trim().length > 50; };
    for (let attempt = 0; attempt < 15 && !hasScript(); attempt++) {
      await new Promise((r) => setTimeout(r, attempt < 3 ? 1000 : 3000));
      const current = promptBox();
      if (!current) continue;
      const dt = new DataTransfer();
      dt.setData("text/plain", scriptText);
      paste(current, dt);
      await waitFor(hasScript, 3000);
    }
    if (!hasScript()) {
      const b = promptBox();
      console.warn("[Omni] chưa dán được kịch bản", { chips: chipCount(), box: !!b, text: b ? b.innerText.length : -1 });
      return { status: "error", message: `Đã gắn ${chipCount()}/${images.length} ảnh nhưng chưa dán được kịch bản (ô câu lệnh ${b ? "có" : "không thấy"}) — anh mở Product_Assets/${message.itemId}/${message.itemId}.txt dán tay rồi bấm Tạo.` };
    }
    return { status: "success" };
  }

  // ===== Tự chạy các bước sau khi điền =====
  const visible = (el) => el && el.offsetParent !== null;
  const byLabel = (label) => [...document.querySelectorAll(`button[aria-label="${label}"]`)].filter(visible);
  const approveRadios = () => [...document.querySelectorAll("[role=radio]")].filter((r) => r.textContent.trim().endsWith("Phê duyệt") && !r.textContent.includes("Luôn"));
  const videoCards = () => [...document.querySelectorAll("div.video-container.clickable")].filter((d) => {
    const img = d.querySelector("img");
    return img && /flow-content\.google/.test(img.src || "");
  });
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  async function step(name, check, timeoutMs) {
    const el = await new Promise(async (resolve) => {
      const start = Date.now();
      while (Date.now() - start < timeoutMs) {
        const found = check();
        if (found) return resolve(found);
        await sleep(1000);
      }
      resolve(null);
    });
    if (!el) throw new Error(`quá hạn ở bước "${name}" — anh làm tay tiếp giúp em`);
    return el;
  }

  // Chỉ nhận nút Phê duyệt / video XUẤT HIỆN SAU khi bấm Tạo: chụp danh sách phần tử cũ ngay trước khi bấm,
  // phần tử mới phải không nằm trong danh sách cũ và đứng sau tin nhắn cũ cuối cùng (khung trò chuyện có đồ của phiên trước).
  const isNew = (el, oldSet) => !oldSet.has(el);
  const after = (el, ref) => !ref || (ref.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING);

  async function autoRun(itemId, output) {
    try {
      const submit = await step("bấm Tạo", () => byLabel("Bắt đầu tạo").filter((b) => !b.disabled).pop(), 60000);
      await sleep(3000);  // chờ ảnh tải lên xong
      const oldRadios = new Set(approveRadios());
      const oldCards = new Set(videoCards());
      submit.click();
      chrome.runtime.sendMessage({ action: "FLOW_RESULT", ok: true, message: `⏳ Mã ${itemId}: đã bấm Tạo trên Flow.` });
      showToast(`⏳ Mã ${itemId}: đã bấm Tạo, chờ Flow hỏi phê duyệt…`);

      const radio = await step("Phê duyệt", () => approveRadios().filter((r) => isNew(r, oldRadios) && r.getAttribute("aria-checked") !== "true").pop(), 120000);
      await sleep(1000);
      radio.click();
      const approvedAt = Date.now();
      showToast(`⏳ Mã ${itemId}: đã Phê duyệt 15 credit, đang tạo video (vài phút) — để tab này mở…`);

      // Video mới: không có trong danh sách cũ, nằm sau nút Phê duyệt vừa bấm, và ít nhất 60 giây sau khi phê duyệt
      const card = await step("chờ video xong", () => Date.now() - approvedAt > 60000 &&
        videoCards().filter((c) => isNew(c, oldCards) && after(c, radio)).pop(), 15 * 60000);
      await sleep(3000);
      card.click();

      const dl = await step("mở Tải xuống", () => byLabel("Tải nội dung nghe nhìn xuống")[0], 30000);
      await sleep(1000);
      dl.click();
      const item720 = await step("chọn 720p", () => [...document.querySelectorAll("[role=menuitem]")].find((m) => m.textContent.includes("720p")), 10000);
      item720.click();
      showToast(`✅ Mã ${itemId}: đang tải video về Downloads/${output} (Chrome hỏi Save thì anh bấm Save).`);

      await sleep(5000);
      const done = byLabel("Đã chỉnh sửa xong cảnh")[0];
      if (done) done.click();
    } catch (e) {
      showToast(`⚠️ Mã ${itemId}: ${e.message}`, true);
      chrome.runtime.sendMessage({ action: "FLOW_RESULT", ok: false, message: `⚠️ Mã ${itemId}: ${e.message}` });
    }
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action !== "FLOW_FILL") return false;
    fill(message).then((resp) => {
      showToast(resp.status === "success"
        ? `✅ Đã điền mã ${message.itemId}: ${message.files.length - 1} ảnh + kịch bản. Đang tự bấm Tạo…`
        : `⚠️ ${resp.message}`, resp.status !== "success");
      sendResponse(resp);
      if (resp.status === "success" && message.autoRun) autoRun(message.itemId, message.output || `${message.itemId}.mp4`);
    });
    return true;
  });
})();
