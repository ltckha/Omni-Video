// Omni Video - Tự điền ô câu lệnh của dự án Google Flow (đã thử thật 15/10/2026 trên dự án Test Omni):
// dán ảnh sản phẩm (Input Image 1) -> ảnh người mẫu (Input Image 2) -> kịch bản .txt.
// Flow tự tải ảnh lên khi dán. Anh Kha tự bấm Tạo (→) và Phê duyệt 15 credit. Không tự bấm Tạo, không chạy lô.

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

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action !== "FLOW_FILL") return false;
    fill(message).then((resp) => {
      showToast(resp.status === "success"
        ? `✅ Đã điền mã ${message.itemId}: ảnh SP (1) + người mẫu (2) + kịch bản. Anh kiểm tra rồi bấm Tạo (→) và Phê duyệt.`
        : `⚠️ ${resp.message}`, resp.status !== "success");
      sendResponse(resp);
    });
    return true;
  });
})();
