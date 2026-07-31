// Omni Video - Popup Script

const DEFAULT_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyxBWA7eJjmi0vn9etRyainI3rrHbAQAN_Uc7tI14sMyyJLftBSnQLJjm5o0WTamS20Rg/exec";

document.addEventListener("DOMContentLoaded", () => {
  const webhookInput = document.getElementById("webhookUrl");
  const saveBtn = document.getElementById("saveBtn");
  const statusDiv = document.getElementById("status");

  // Đọc cấu hình URL đã lưu (hoặc dùng mặc định đã cài đặt sẵn)
  chrome.storage.sync.get(["gasWebhookUrl"], (result) => {
    webhookInput.value = result.gasWebhookUrl || DEFAULT_WEBHOOK_URL;
  });

  // Lưu URL khi bấm nút
  saveBtn.addEventListener("click", () => {
    const url = webhookInput.value.trim() || DEFAULT_WEBHOOK_URL;
    chrome.storage.sync.set({ gasWebhookUrl: url }, () => {
      statusDiv.style.display = "block";
      setTimeout(() => {
        statusDiv.style.display = "none";
      }, 2000);
    });
  });
});
