// Omni Video - 1 cú bấm / 1 video trên dự án Google Flow (anh Kha chọn 15/10/2026):
// dán ảnh sản phẩm (Input Image 1) -> ảnh người mẫu (Input Image 2) -> kịch bản .txt (Flow tự tải ảnh khi dán)
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

  async function pasteImage(box, file) {
    const before = chipCount();
    const dt = new DataTransfer();
    dt.items.add(new File([b64ToBytes(file.b64)], file.name, { type: file.mime }));
    paste(box, dt);
    return waitFor(() => chipCount() > before, 15000);
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
    for (const slot of ["product", "character"]) {
      if (!(await pasteImage(box, byslot[slot]))) {
        return { status: "error", message: `Flow không nhận ảnh ${slot === "product" ? "sản phẩm" : "người mẫu"} — anh tải lại trang Flow rồi thử lại.` };
      }
    }
    const dt = new DataTransfer();
    dt.setData("text/plain", new TextDecoder().decode(b64ToBytes(byslot.script.b64)));
    paste(box, dt);
    if (!(await waitFor(() => box.innerText.trim().length > 50, 3000))) {
      return { status: "error", message: "Đã gắn 2 ảnh nhưng chưa dán được kịch bản — anh dán tay file .txt." };
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

  async function autoRun(itemId, before) {
    try {
      const submit = await step("bấm Tạo", () => byLabel("Bắt đầu tạo").filter((b) => !b.disabled).pop(), 60000);
      await sleep(1500);
      submit.click();
      showToast(`⏳ Mã ${itemId}: đã bấm Tạo, chờ Flow hỏi phê duyệt…`);

      const radio = await step("Phê duyệt", () => approveRadios().length > before.approvals && approveRadios().pop(), 90000);
      radio.click();
      showToast(`⏳ Mã ${itemId}: đã Phê duyệt 15 credit, đang tạo video (vài phút)…`);

      const card = await step("chờ video xong", () => videoCards().length > before.videos && videoCards().pop(), 15 * 60000);
      await sleep(2000);
      card.click();

      const dl = await step("mở Tải xuống", () => byLabel("Tải nội dung nghe nhìn xuống")[0], 30000);
      dl.click();
      const item720 = await step("chọn 720p", () => [...document.querySelectorAll("[role=menuitem]")].find((m) => m.textContent.includes("720p")), 10000);
      item720.click();
      showToast(`✅ Mã ${itemId}: đang tải video về Downloads/${itemId}.mp4 (Chrome hỏi Save thì anh bấm Save).`);

      await sleep(4000);
      const done = byLabel("Đã chỉnh sửa xong cảnh")[0];
      if (done) done.click();
    } catch (e) {
      showToast(`⚠️ Mã ${itemId}: ${e.message}`, true);
    }
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action !== "FLOW_FILL") return false;
    const before = { approvals: approveRadios().length, videos: videoCards().length };
    fill(message).then((resp) => {
      showToast(resp.status === "success"
        ? `✅ Đã điền mã ${message.itemId}: ảnh SP (1) + người mẫu (2) + kịch bản. Đang tự bấm Tạo…`
        : `⚠️ ${resp.message}`, resp.status !== "success");
      sendResponse(resp);
      if (resp.status === "success" && message.autoRun) autoRun(message.itemId, before);
    });
    return true;
  });
})();
