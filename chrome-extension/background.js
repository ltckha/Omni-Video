// Omni Video - Background Service Worker (Native Messaging -> Google Sheets API v4)

const NATIVE_HOST_NAME = "com.omni.video.curator";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "save-shopee-image-context",
    title: "📸 Lưu ảnh SP cho Omni UGC (Alt+S)",
    contexts: ["image", "page", "link"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "save-shopee-image-context" && tab && tab.id) {
    chrome.tabs.sendMessage(tab.id, { action: "GET_SELECTED_IMAGE" });
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "TRIGGER_SAVE_IMAGE" && message.payload) {
    let tabId = sender.tab ? sender.tab.id : null;
    processSaveWorkflow(message.payload, tabId);
    sendResponse({ status: "processing" });
  } else if (message.action === "FLOW_LIST") {
    chrome.runtime.sendNativeMessage(NATIVE_HOST_NAME, { action: "FLOW_LIST" }, (resp) => {
      sendResponse(chrome.runtime.lastError ? { status: "error", message: chrome.runtime.lastError.message } : resp);
    });
  } else if (message.action === "FLOW_FILL" && message.itemId) {
    fillFlowTool(message.itemId).then(sendResponse);
  } else if (message.action === "FLOW_RESULT") {  // flow_page.js báo kết quả / lỗi các bước tự chạy
    setFlowResult(message.ok, message.message);
    if (!message.ok) chrome.storage.local.remove("flowActiveItem");
    sendResponse({ status: "success" });
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

async function fillFlowTool(itemId) {
  const resp = await fillFlowToolInner(itemId);
  if (!resp || resp.status !== "success") {
    setFlowResult(false, `⚠️ Mã ${itemId}: ${(resp && resp.message) || "lỗi không rõ"}`);
  }
  return resp;
}

async function fillFlowToolInner(itemId) {
  const projectTab = await pickFlowTab();
  if (!projectTab) {
    return { status: "error", message: "Chưa mở dự án Google Flow — anh mở dự án (vd Omni-Video) trước." };
  }
  const loaded = await loadFlowFiles(itemId);
  if (loaded.status !== "success") return loaded;
  await chrome.tabs.update(projectTab.id, { active: true });
  let resp;
  try {
    // Đặt trước tên file tải về: <itemId>.mp4, hàng tiệm <MÃ>_2.mp4… theo native host (content script tự chạy tới bước Tải)
    await chrome.storage.local.set({ flowActiveItem: { itemId: itemId, output: loaded.output || `${itemId}.mp4`, since: Date.now() } });
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
const flowDownloads = {};  // downloadId -> itemId

function isFlowVideoDownload(item) {
  const isVideo = (item.mime || "").startsWith("video/") || /\.mp4$/i.test(item.filename || "");
  const fromFlow = FLOW_SOURCE_PATTERN.test(`${item.referrer || ""} ${item.url || ""} ${item.finalUrl || ""}`);
  return isVideo && fromFlow;
}

chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
  chrome.storage.local.get(["flowActiveItem"], (stored) => {
    const active = stored.flowActiveItem;
    if (active && Date.now() - active.since < FLOW_ACTIVE_MAX_AGE_MS && isFlowVideoDownload(item)) {
      flowDownloads[item.id] = active.itemId;
      chrome.storage.local.remove("flowActiveItem");
      suggest({ filename: active.output || `${active.itemId}.mp4`, conflictAction: "uniquify" });
    } else {
      suggest();
    }
  });
  return true;
});

chrome.downloads.onChanged.addListener((delta) => {
  const itemId = flowDownloads[delta.id];
  if (!itemId || !delta.state || delta.state.current !== "complete") return;
  delete flowDownloads[delta.id];
  chrome.runtime.sendNativeMessage(NATIVE_HOST_NAME, { action: "FLOW_COLLECT", itemId: itemId }, (resp) => {
    const ok = !chrome.runtime.lastError && resp && resp.status === "success";
    const detail = chrome.runtime.lastError ? chrome.runtime.lastError.message : (resp && resp.message) || "";
    const message = ok ? `✅ Đã lưu video: ${resp.movedTo || itemId + ".mp4"}` : `⚠️ Chưa chuyển được video ${itemId}: ${detail}`;
    setFlowResult(ok, message);
  });
});

async function processSaveWorkflow(payloadData, tabId) {
  let itemId = payloadData.itemId || ("SP_" + Date.now());
  let cdnUrl = payloadData.cdnUrl;

  if (!cdnUrl) {
    sendToastToTab(tabId, "⚠️ Lỗi: Không tìm thấy URL ảnh CDN!", true);
    return;
  }

  let ext = ".jpg";
  let lowerUrl = cdnUrl.toLowerCase();
  if (lowerUrl.includes(".webp")) {
    ext = ".webp";
  } else if (lowerUrl.includes(".png")) {
    ext = ".png";
  } else if (lowerUrl.includes(".jpeg")) {
    ext = ".jpeg";
  } else if (lowerUrl.includes(".jpg")) {
    ext = ".jpg";
  } else if (lowerUrl.includes("susercontent.com")) {
    ext = ".webp";
  }

  let filename = `${itemId}_${Date.now()}${ext}`;

  // 1. Tải ảnh từ Chrome Downloads
  chrome.downloads.download({
    url: cdnUrl,
    filename: filename,
    conflictAction: "uniquify",
    saveAs: false
  }, (downloadId) => {
    if (chrome.runtime.lastError) {
      let dlErr = chrome.runtime.lastError.message;
      console.error("Lỗi chrome.downloads:", dlErr);
      sendToastToTab(tabId, `⚠️ Lỗi Tải Ảnh: ${dlErr}`, true);
      return;
    }

    console.log("✅ Đã tải ảnh ID:", downloadId, "Tên file:", filename);

    // 2. Kích hoạt Native Host chuyển ảnh + lưu thông tin info.json
    chrome.runtime.sendNativeMessage(
      NATIVE_HOST_NAME,
      { itemId: itemId, filename: filename, info: payloadData },
      (nativeResp) => {
        if (chrome.runtime.lastError) {
          let hostErr = chrome.runtime.lastError.message;
          let currentExtId = chrome.runtime.id;
          console.error("Lỗi Native Host:", hostErr, "ID hiện tại:", currentExtId);
          sendToastToTab(tabId, `⚠️ Lỗi Native Host: ${hostErr}`, true);
        } else if (nativeResp && nativeResp.status === "success") {
          console.log("✅ Native Host di chuyển thành công:", nativeResp);
          sendToastToTab(tabId, `✅ Đã lưu ảnh vào /Product_Assets/${itemId}/`);
        } else {
          let errDetail = nativeResp ? nativeResp.message : "Không tìm thấy file tải về";
          sendToastToTab(tabId, `⚠️ Native Host: ${errDetail}`, true);
        }
      }
    );
  });
}

function sendToastToTab(tabId, msg, isError = false) {
  if (tabId) {
    chrome.tabs.sendMessage(tabId, { action: "SHOW_TOAST", msg: msg, isError: isError }).catch(() => {});
  }
}

