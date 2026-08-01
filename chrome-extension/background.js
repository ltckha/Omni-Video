// Omni Video - Background Service Worker (Tự động hiển thị chính xác Extension ID nếu bị lỗi Native Host)

const DEFAULT_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyxBWA7eJjmi0vn9etRyainI3rrHbAQAN_Uc7tI14sMyyJLftBSnQLJjm5o0WTamS20Rg/exec";
const NATIVE_HOST_NAME = "com.omni.video.curator";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "save-shopee-image-context",
    title: "📸 Lưu ảnh SP cho Omni UGC (Alt+S)",
    contexts: ["image", "page", "link"]
  });
  chrome.storage.sync.set({ gasWebhookUrl: DEFAULT_WEBHOOK_URL });
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
  }
  return true;
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
          sendToastToTab(tabId, `⚠️ Lỗi Native Host: ${hostErr} (ID Chrome của bạn: ${currentExtId})`, true);
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

  // 3. Gửi Webhook POST lên Google Apps Script
  try {
    chrome.storage.sync.get(["gasWebhookUrl"], (stored) => {
      let webhookUrl = stored.gasWebhookUrl || DEFAULT_WEBHOOK_URL;
      fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "text/plain;charset=utf-8" },
        body: JSON.stringify({
          itemId: itemId,
          productName: payloadData.productName,
          price: payloadData.price,
          salesCount: payloadData.salesCount,
          shopName: payloadData.shopName,
          productUrl: payloadData.productUrl,
          cdnUrl: cdnUrl,
          localPath: `/Users/khan/Developer/Omni-Video/Product_Assets/${itemId}/`
        })
      }).then(res => res.json())
        .then(resData => console.log("GAS Result:", resData))
        .catch(err => console.error("Lỗi fetch Webhook GAS:", err));
    });
  } catch (err) {
    console.error("Lỗi kích hoạt Webhook:", err);
  }
}

function sendToastToTab(tabId, msg, isError = false) {
  if (tabId) {
    chrome.tabs.sendMessage(tabId, { action: "SHOW_TOAST", msg: msg, isError: isError }).catch(() => {});
  }
}
