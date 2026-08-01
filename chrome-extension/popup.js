// Omni Video - Popup Script

const DEFAULT_WEBHOOK_URL = "";

document.addEventListener("DOMContentLoaded", () => {
  const webhookInput = document.getElementById("webhookUrl");
  const saveBtn = document.getElementById("saveBtn");
  const statusMsg = document.getElementById("statusMsg");

  // Đọc cấu hình từ chrome.storage.sync
  chrome.storage.sync.get(["gasWebhookUrl"], (stored) => {
    if (stored.gasWebhookUrl) {
      webhookInput.value = stored.gasWebhookUrl;
    } else {
      webhookInput.value = DEFAULT_WEBHOOK_URL;
    }
  });

  // Lưu cấu hình Webhook URL
  saveBtn.addEventListener("click", () => {
    const urlValue = webhookInput.value.trim();
    if (!urlValue) {
      showStatus("⚠️ Vui lòng dán Webhook URL Google Apps Script!", true);
      return;
    }

    chrome.storage.sync.set({ gasWebhookUrl: urlValue }, () => {
      showStatus("✅ Đã lưu cấu hình Webhook URL thành công!");
    });
  });

  function showStatus(msg, isError = false) {
    statusMsg.innerText = msg;
    statusMsg.style.color = isError ? "#d32f2f" : "#2e7d32";
    setTimeout(() => {
      statusMsg.innerText = "";
    }, 3000);
  }
});
