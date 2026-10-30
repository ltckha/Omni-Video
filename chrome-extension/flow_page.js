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

  function chips() {
    return [...document.querySelectorAll("button")].filter(
      (b) => b.getAttribute("aria-label") === CHIP_LABEL || b.textContent.trim().startsWith(CHIP_LABEL)
    );
  }

  function chipCount() {
    return chips().length;
  }

  // Ảnh đã tải lên xong thật chưa (30/10: đủ ô ảnh nhưng ảnh còn đang tải → Tạo hỏng). Không chỉ đếm ô:
  // - không có vòng xoay / thanh tiến độ / aria-busy / lớp mờ trong ô ảnh và khung chứa các ô;
  // - ảnh trong ô (nếu ô có <img>) đã nạp: src blob:/https:/data:, complete, naturalWidth > 0.
  const BUSY = '[role=progressbar],[aria-busy="true"],circle[stroke-dasharray],[class*="progress" i],[class*="spinner" i],[class*="loading" i],[class*="uploading" i]';
  function uploadState(expected) {
    const list = chips();
    const scopes = [...new Set(list.map((c) => c.parentElement).filter(Boolean))];
    const busy = scopes.some((el) => [...el.querySelectorAll(BUSY)].some((x) => x.offsetParent !== null || x.tagName === "circle"));
    const anyImg = list.some((c) => c.querySelector("img"));
    const loaded = list.filter((c) => {
      if (parseFloat(getComputedStyle(c).opacity) < 0.95) return false;
      const img = c.querySelector("img");
      if (!img) return !anyImg;
      return /^(blob:|https:|data:)/.test(img.src || "") && img.complete && img.naturalWidth > 0
        && parseFloat(getComputedStyle(img).opacity) >= 0.95;
    }).length;
    return { ready: list.length >= expected && loaded >= expected && !busy, loaded, total: list.length, busy };
  }

  // Chờ ảnh tải xong và giữ ổn định stableMs liền; quá hạn → trả trạng thái để báo lỗi (không bấm Tạo)
  async function waitUploaded(expected, timeoutMs = 120000, stableMs = 4000) {
    const start = Date.now();
    let since = 0;
    let st = uploadState(expected);
    while (Date.now() - start < timeoutMs) {
      st = uploadState(expected);
      if (st.ready) {
        since = since || Date.now();
        if (Date.now() - since >= stableMs) return { ok: true, ...st };
      } else {
        since = 0;
      }
      await new Promise((r) => setTimeout(r, 500));
    }
    console.warn("[Omni] ảnh chưa tải xong", st, chips().map((c) => c.outerHTML.slice(0, 400)));
    return { ok: false, ...st };
  }

  const notUploadedMsg = (st, expected) =>
    `ảnh chưa tải xong ${Math.min(st.loaded, expected)}/${expected}${st.busy ? " (Flow còn đang tải)" : ""} sau 120 giây — chưa bấm Tạo, không tốn credit. Anh xoá ảnh trong ô câu lệnh rồi bấm lại.`;

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
    const up = await waitUploaded(images.length);
    if (!up.ok) return { status: "error", message: notUploadedMsg(up, images.length) };
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

  async function autoRun(itemId, output, nImages) {
    try {
      // kiểm lại ngay trước khi bấm Tạo: ảnh vẫn tải xong + ổn định, nút Tạo không bị khoá
      const up = await waitUploaded(nImages);
      if (!up.ok) throw new Error(notUploadedMsg(up, nImages));
      const submit = await step("bấm Tạo", () => byLabel("Bắt đầu tạo").filter((b) => !b.disabled && b.getAttribute("aria-disabled") !== "true").pop(), 60000);
      await sleep(3000);
      const oldRadios = new Set(approveRadios());
      const oldCards = new Set(videoCards());
      submit.click();
      chrome.runtime.sendMessage({ action: "FLOW_RESULT", ok: true, message: `⏳ Mã ${itemId}: đã bấm Tạo trên Flow.` });
      showToast(`⏳ Mã ${itemId}: đã bấm Tạo, chờ Flow hỏi phê duyệt…`);

      // 30/10: dự án cũ "Test Omni" bị kẹt phiên tác nhân — gửi đi mà không có phản hồi → báo rõ sau 90 giây
      const radio = await step("Phê duyệt", () => approveRadios().filter((r) => isNew(r, oldRadios) && r.getAttribute("aria-checked") !== "true").pop(), 90000)
        .catch(() => { throw new Error("dự án Flow không phản hồi sau 90 giây (không thấy hỏi Phê duyệt) — anh thử tạo dự án Flow mới rồi bấm lại"); });
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
      saveSnapshot(`loi_${itemId}`);
    }
  }

  // ===== Ghi cấu trúc trang (chỉ đọc, không bấm) → data/logs/flow_snapshot_*.json qua native host (30/10: Flow đổi
  // sang giao diện "Tác nhân", extension kẹt ở "Phê duyệt"). Tự ghi khi tự chạy bị lỗi; nút 📋 trong khung để ghi tay.
  function snapshot() {
    const vis = (el) => el.offsetParent !== null;
    const short = (t, n = 80) => (t || "").replace(/\s+/g, " ").trim().slice(0, n);
    const pick = (sel, n = 150) => [...document.querySelectorAll(sel)].filter(vis).slice(-n);
    return {
      url: location.href, at: new Date().toISOString(),
      buttons: pick("button,[role=button]", 250).filter((b) => !b.closest("#" + PANEL_ID)).map((b) => ({
        aria: b.getAttribute("aria-label"), text: short(b.textContent, 60), disabled: !!b.disabled || b.getAttribute("aria-disabled") === "true",
        pressed: b.getAttribute("aria-pressed"), cls: short(b.className && b.className.baseVal !== undefined ? "" : b.className, 80) })),
      roles: pick("[role=radio],[role=dialog],[role=alertdialog],[role=menuitem],[role=option],[role=checkbox],[role=switch],[role=tab],[role=status],[role=alert],[role=log]")
        .map((el) => ({ role: el.getAttribute("role"), aria: el.getAttribute("aria-label"), checked: el.getAttribute("aria-checked"), text: short(el.textContent, 120) })),
      textboxes: pick("[contenteditable=true],textarea").map((el) => ({ aria: el.getAttribute("aria-label"), len: (el.innerText || el.value || "").length })),
      chips: chipCount(), videoCards: videoCards().length,
      media: pick("video,img", 60).map((m) => ({ tag: m.tagName, src: (m.currentSrc || m.src || "").slice(0, 90), w: m.naturalWidth || m.videoWidth || 0 })),
      tail: short(document.body.innerText.slice(-4000), 4000),
    };
  }

  function saveSnapshot(label) {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage({ action: "FLOW_SNAPSHOT", label, snapshot: snapshot() }, (r) => resolve(r));
      } catch (e) { resolve({ status: "error", message: e.message }); }
    });
  }

  // ===== Khung nổi hàng chờ trên trang dự án Flow (30/10): giống popup — mã · tên file · kiểu · bối cảnh, nút Tạo video,
  // dòng trạng thái flowLastResult. Để làm được cả khi không mở được popup (vd Claude in Chrome). id cố định để tìm:
  // #omni-flow-panel, nút button[data-item-id="<mã>"], trạng thái #omni-flow-status, danh sách #omni-flow-list.
  const PANEL_ID = "omni-flow-panel";
  const isProjectPage = () => /^\/project\//.test(location.pathname) && !/\/tool\//.test(location.pathname);

  function panelStatus() {
    const el = document.getElementById("omni-flow-status");
    if (!el) return;
    chrome.storage.local.get(["flowActiveItem", "flowLastResult"], (st) => {
      const lines = [];
      if (st.flowLastResult && st.flowLastResult.message) lines.push(st.flowLastResult.message);
      if (st.flowActiveItem && st.flowActiveItem.itemId) lines.push(`Đang làm mã ${st.flowActiveItem.itemId} (${st.flowActiveItem.output || ""})…`);
      el.textContent = lines.join("\n") || "Chọn mã cần làm video.";
      el.style.color = st.flowLastResult && st.flowLastResult.ok === false ? "#ff8a80" : "#e0e0e0";
    });
  }

  function panelList() {
    const list = document.getElementById("omni-flow-list");
    if (!list) return;
    chrome.runtime.sendMessage({ action: "FLOW_LIST" }, (resp) => {
      list.textContent = "";
      if (!resp || resp.status !== "success") {
        list.textContent = `⚠️ ${resp ? resp.message : "Không kết nối được Native Host"}`;
        return;
      }
      if (!resp.items.length) list.textContent = "Không có mã nào đang chờ video.";
      else if (!window.__omniPanelExpanded) {  // có mã thì bung danh sách (1 lần mỗi lần tải trang)
        window.__omniPanelExpanded = true;
        const panel = document.getElementById(PANEL_ID);
        if (panel && panel.expand) panel.expand();
      }
      resp.items.forEach((item) => {
        const row = document.createElement("div");
        row.style.cssText = "display:flex;gap:6px;align-items:center;margin:4px 0;";
        const label = document.createElement("span");
        label.textContent = `${item.itemId} ${item.title || ""}`;
        label.title = label.textContent;
        label.style.cssText = "flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";
        const btn = document.createElement("button");
        btn.textContent = "Tạo video";
        btn.dataset.itemId = item.itemId;
        btn.style.cssText = "background:#1a73e8;color:#fff;border:0;border-radius:4px;padding:3px 8px;cursor:pointer;font:12px sans-serif;";
        btn.addEventListener("click", () => {
          btn.disabled = true;
          document.getElementById("omni-flow-status").textContent = `Đang làm mã ${item.itemId}…`;
          chrome.runtime.sendMessage({ action: "FLOW_FILL", itemId: item.itemId }, () => {
            btn.disabled = false;
            panelStatus();
          });
        });
        row.appendChild(label);
        row.appendChild(btn);
        list.appendChild(row);
      });
    });
  }

  function ensurePanel() {
    const existing = document.getElementById(PANEL_ID);
    if (!isProjectPage()) {
      if (existing) existing.remove();
      return;
    }
    if (existing) return;
    const panel = document.createElement("div");
    panel.id = PANEL_ID;
    // góc TRÁI dưới: khung chat tác nhân của Flow chiếm bên phải và che danh sách (30/10)
    panel.style.cssText = `position:fixed;left:12px;bottom:12px;z-index:2147483647;width:360px;max-width:calc(100vw - 24px);
      max-height:45vh;display:flex;flex-direction:column;
      background:#202124;color:#e0e0e0;border:1px solid #5f6368;border-radius:8px;padding:8px 10px;
      font:12px -apple-system,sans-serif;box-shadow:0 2px 10px rgba(0,0,0,.5);`;
    const head = document.createElement("div");
    head.style.cssText = "display:flex;justify-content:space-between;align-items:center;font-weight:600;flex:0 0 auto;";
    head.textContent = "🎬 Omni · hàng chờ";
    const tools = document.createElement("span");
    const refresh = document.createElement("button");
    refresh.id = "omni-flow-refresh";
    refresh.textContent = "↻";
    const toggle = document.createElement("button");
    toggle.id = "omni-flow-toggle";
    toggle.textContent = "–";
    const snap = document.createElement("button");
    snap.id = "omni-flow-snapshot";
    snap.textContent = "📋";
    snap.title = "Ghi cấu trúc trang Flow lúc này (chỉ đọc, không bấm gì) để sửa extension";
    snap.addEventListener("click", async () => {
      const r = await saveSnapshot("tay");
      document.getElementById("omni-flow-status").textContent = r && r.status === "success" ? `📋 Đã ghi ${r.path.split("/").pop()}` : `⚠️ Chưa ghi được: ${r ? r.message : ""}`;
    });
    for (const b of [snap, refresh, toggle]) {
      b.style.cssText = "background:none;color:#e0e0e0;border:1px solid #5f6368;border-radius:4px;margin-left:4px;cursor:pointer;";
      tools.appendChild(b);
    }
    head.appendChild(tools);
    const body = document.createElement("div");
    body.id = "omni-flow-body";
    body.style.cssText = "overflow-y:auto;min-height:0;flex:1 1 auto;";
    const status = document.createElement("div");
    status.id = "omni-flow-status";
    status.style.cssText = "white-space:pre-line;margin:6px 0;";
    const list = document.createElement("div");
    list.id = "omni-flow-list";
    body.appendChild(status);
    body.appendChild(list);
    panel.appendChild(head);
    panel.appendChild(body);
    document.body.appendChild(panel);
    let collapsed = false;
    try { collapsed = localStorage.getItem("omniFlowPanelCollapsed") === "1"; } catch (e) {}
    const applyCollapsed = () => { body.style.display = collapsed ? "none" : "block"; toggle.textContent = collapsed ? "+" : "–"; };
    panel.expand = () => { collapsed = false; applyCollapsed(); };
    applyCollapsed();
    toggle.addEventListener("click", () => {
      collapsed = !collapsed;
      try { localStorage.setItem("omniFlowPanelCollapsed", collapsed ? "1" : "0"); } catch (e) {}
      applyCollapsed();
    });
    refresh.addEventListener("click", () => { panelStatus(); panelList(); });
    panelStatus();
    panelList();
  }

  chrome.storage.onChanged.addListener((changes) => {
    if (changes.flowLastResult || changes.flowActiveItem) panelStatus();
    if (changes.flowLastResult && changes.flowLastResult.newValue && /Đã lưu video/.test(changes.flowLastResult.newValue.message || "")) panelList();
  });
  ensurePanel();
  setInterval(ensurePanel, 2000);  // Flow đổi trang không tải lại (SPA)

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action !== "FLOW_FILL") return false;
    fill(message).then((resp) => {
      showToast(resp.status === "success"
        ? `✅ Đã điền mã ${message.itemId}: ${message.files.length - 1} ảnh + kịch bản. Đang tự bấm Tạo…`
        : `⚠️ ${resp.message}`, resp.status !== "success");
      sendResponse(resp);
      if (resp.status === "success" && message.autoRun) autoRun(message.itemId, message.output || `${message.itemId}.mp4`,
        message.files.filter((f) => f.slot !== "script").length);
    });
    return true;
  });
})();
