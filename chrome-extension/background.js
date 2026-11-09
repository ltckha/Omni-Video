// Omni Video - Background Service Worker: "Tạo video" hàng tiệm trên Google Flow (Native Messaging).
// Phần lưu ảnh Shopee (Alt+S, menu chuột phải) đã cất 1/11/2026: archive/chrome-extension/content.js, archive/README.md.

const NATIVE_HOST_NAME = "com.omni.video.curator";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "FLOW_LIST") {
    chrome.runtime.sendNativeMessage(NATIVE_HOST_NAME, { action: "FLOW_LIST" }, (resp) => {
      sendResponse(chrome.runtime.lastError ? { status: "error", message: chrome.runtime.lastError.message } : resp);
    });
  } else if (message.action === "FLOW_FILL" && message.itemId) {
    // từ khung nổi trên trang Flow (flow_page.js) → dùng đúng tab đó; từ popup → chọn tab Flow
    fillFlowTool(message.itemId, sender.tab ? sender.tab.id : null).then(sendResponse);
  } else if (message.action === "FLOW_RESULT") {  // flow_page.js báo kết quả / lỗi các bước tự chạy
    setFlowResult(message.ok, message.message);
    if (message.ok) return sendResponse({ status: "success" });
    // chỉ xoá tên đặt sẵn của đúng mã báo lỗi (5/11: lỗi của mã cũ từng xoá mất tên của mã đang làm)
    chrome.storage.local.get(["flowActiveItem"], (st) => {
      const active = st.flowActiveItem;
      if (active && (!message.itemId || active.itemId === message.itemId)) chrome.storage.local.remove("flowActiveItem");
      sendResponse({ status: "success" });
    });
  } else if (message.action === "FLOW_SNAPSHOT") {
    chrome.runtime.sendNativeMessage(NATIVE_HOST_NAME, { action: "FLOW_SNAPSHOT", label: message.label, snapshot: message.snapshot }, (resp) => {
      sendResponse(chrome.runtime.lastError ? { status: "error", message: chrome.runtime.lastError.message } : resp);
    });
  } else if (message.action === "FLOW_REARM") {  // nút "Tải lại video": đặt lại tên file cho mã vừa làm rồi tải bù
    chrome.storage.local.get(["flowLastItem", "flowActiveItem"], async (st) => {
      const last = st.flowLastItem || st.flowActiveItem;  // mã đang dở từ bản extension cũ chỉ có flowActiveItem
      if (!last || !last.itemId) return sendResponse({ status: "error", message: "Chưa có mã nào vừa làm." });
      await chrome.storage.local.set({ flowActiveItem: { itemId: last.itemId, output: last.output, since: Date.now() } });
      sendResponse({ status: "success", itemId: last.itemId, output: last.output, beforeChatKey: last.beforeChatKey });
    });
  } else if (message.action === "FLOW_CLEAR") {
    chrome.storage.local.remove("flowActiveItem", () => sendResponse({ status: "success" }));
  }
  return true;
});

// ===== Google Flow: tự điền ô câu lệnh dự án Flow (anh Kha tự bấm Tạo / Phê duyệt / Tải) =====
function loadFlowFiles(itemId) {
  return new Promise((resolve) => {
    const port = chrome.runtime.connectNative(NATIVE_HOST_NAME);
    let meta = null;
    const parts = {};
    let finished = false;
    const finish = (result) => { if (!finished) { finished = true; resolve(result); try { port.disconnect(); } catch (e) {} } };
    port.onMessage.addListener((msg) => {
      if (msg.type === "meta") {
        meta = msg;
      } else if (msg.type === "chunk") {
        (parts[msg.slot] = parts[msg.slot] || [])[msg.index] = msg.data;
      } else if (msg.type === "done" && meta) {
        finish({ status: "success", output: meta.output, files: meta.files.map((f) => ({ ...f, b64: (parts[f.slot] || []).join("") })) });
      } else if (msg.status === "error") {
        finish({ status: "error", message: msg.message });
      }
    });
    port.onDisconnect.addListener(() => {
      finish({ status: "error", message: chrome.runtime.lastError ? chrome.runtime.lastError.message : "Native Host ngắt kết nối" });
    });
    port.postMessage({ action: "FLOW_FILES", itemId: itemId });
  });
}

// Popup đóng ngay khi tab Flow được đưa lên trước → mọi lỗi phải lưu flowLastResult để mở lại popup còn thấy (30/10)
function setFlowResult(ok, message) {
  chrome.storage.local.set({ flowLastResult: { ok: ok, message: message, at: Date.now() } });
  chrome.action.setBadgeBackgroundColor({ color: ok ? "#2e7d32" : "#d32f2f" });
  chrome.action.setBadgeText({ text: ok ? "OK" : "!" });
}

// Nhiều tab dự án Flow: ưu tiên tab đang mở trong cửa sổ vừa dùng, rồi tab Flow vừa xem gần nhất (không lấy [0])
async function pickFlowTab() {
  const isProject = (t) => /^https:\/\/flow\.google\.com\/project\//.test(t.url || "") && !/\/tool\//.test(t.url || "");
  const [current] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  if (current && isProject(current)) return current;
  const tabs = (await chrome.tabs.query({ url: "https://flow.google.com/project/*" })).filter(isProject);
  tabs.sort((a, b) => (b.lastAccessed || 0) - (a.lastAccessed || 0));
  return tabs[0] || null;
}

async function fillFlowTool(itemId, tabId) {
  const resp = await fillFlowToolInner(itemId, tabId);
  if (!resp || resp.status !== "success") {
    setFlowResult(false, `⚠️ Mã ${itemId}: ${(resp && resp.message) || "lỗi không rõ"}`);
  }
  return resp;
}

async function fillFlowToolInner(itemId, tabId) {
  const projectTab = tabId ? await chrome.tabs.get(tabId) : await pickFlowTab();
  if (!projectTab) {
    return { status: "error", message: "Chưa mở dự án Google Flow — anh mở dự án (vd Omni-Video) trước." };
  }
  const loaded = await loadFlowFiles(itemId);
  if (loaded.status !== "success") return loaded;
  await chrome.tabs.update(projectTab.id, { active: true });
  let resp;
  try {
    // Đặt trước tên file tải về: <itemId>.mp4, hàng tiệm <MÃ>_2.mp4… theo native host (content script tự chạy tới bước Tải)
    const output = loaded.output || `${itemId}.mp4`;
    // flowLastItem giữ lại cả khi lỗi (flowActiveItem bị xoá) → nút "Tải lại video" trên khung nổi
    await chrome.storage.local.set({ flowActiveItem: { itemId: itemId, output: output, since: Date.now() }, flowLastItem: { itemId: itemId, output: output } });
    resp = await chrome.tabs.sendMessage(projectTab.id, { action: "FLOW_FILL", itemId: itemId, output: loaded.output, files: loaded.files, autoRun: true });
  } catch (e) {
    resp = { status: "error", message: "Trang Flow chưa nạp extension — anh tải lại trang Flow (Cmd+R) rồi bấm lại." };
  }
  if (!resp || resp.status !== "success") {
    await chrome.storage.local.remove("flowActiveItem");
  }
  return resp;
}

// ===== Google Flow (bán tự động): video tải từ Flow -> <itemId>.mp4 -> Product_Assets/<itemId>/ =====
const FLOW_ACTIVE_MAX_AGE_MS = 6 * 60 * 60 * 1000;
const FLOW_SOURCE_PATTERN = /flow\.google\.com|labs\.google|usercontent\.goog|googleusercontent\.com|storage\.googleapis\.com/;
// downloadId -> itemId, lưu trong storage: service worker MV3 bị tắt khi Chrome hỏi chỗ lưu → biến trong bộ nhớ mất,
// tải xong không ghi sổ (9/11: omni12_JH8918N_15s.mp4 tải đúng tên nhưng không có da_tai)
const flowDlKey = (id) => `flowDl_${id}`;

function isFlowVideoDownload(item) {
  const isVideo = (item.mime || "").startsWith("video/") || /\.mp4$/i.test(item.filename || "");
  const fromFlow = FLOW_SOURCE_PATTERN.test(`${item.referrer || ""} ${item.url || ""} ${item.finalUrl || ""}`);
  return isVideo && fromFlow;
}

chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
  // báo "đã bắt đầu tải" ngay ở đây: Chrome bật "Hỏi vị trí lưu" thì onCreated chỉ tới sau khi anh bấm Save
  if (isFlowVideoDownload(item)) chrome.storage.local.set({ flowDownloadStartedAt: Date.now() });
  chrome.storage.local.get(["flowActiveItem"], (stored) => {
    const active = stored.flowActiveItem;
    if (active && Date.now() - active.since < FLOW_ACTIVE_MAX_AGE_MS && isFlowVideoDownload(item)) {
      chrome.storage.local.set({ [flowDlKey(item.id)]: active.itemId });
      chrome.storage.local.remove("flowActiveItem");
      suggest({ filename: active.output || `${active.itemId}.mp4`, conflictAction: "uniquify" });
    } else {
      suggest();
    }
  });
  return true;
});

// flow_page.js biết lượt bấm Tải xuống đã ăn (không bấm thêm, tránh tải trùng)
chrome.downloads.onCreated.addListener(() => chrome.storage.local.set({ flowDownloadStartedAt: Date.now() }));

chrome.downloads.onChanged.addListener(async (delta) => {
  if (!delta.state || !["complete", "interrupted"].includes(delta.state.current)) return;
  const key = flowDlKey(delta.id);
  const itemId = (await chrome.storage.local.get([key]))[key];
  if (!itemId) return;
  await chrome.storage.local.remove(key);
  if (delta.state.current !== "complete") return;
  chrome.runtime.sendNativeMessage(NATIVE_HOST_NAME, { action: "FLOW_COLLECT", itemId: itemId }, (resp) => {
    const ok = !chrome.runtime.lastError && resp && resp.status === "success";
    const detail = chrome.runtime.lastError ? chrome.runtime.lastError.message : (resp && resp.message) || "";
    const message = ok ? `✅ Đã lưu video: ${resp.movedTo || itemId + ".mp4"}` : `⚠️ Chưa chuyển được video ${itemId}: ${detail}`;
    setFlowResult(ok, message);
    if (ok) chrome.storage.local.remove("flowLastItem");  // đã lưu → ẩn nút "Tải lại video" (tránh tải trùng)
  });
});
