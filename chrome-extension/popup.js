// Omni Video - Popup: chuẩn bị sản phẩm cho Google Flow (anh Kha tự bấm Tạo / Tải trên Flow)

document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("flowStatus");
  const listEl = document.getElementById("flowList");

  chrome.action.setBadgeText({ text: "" });

  function render(active, lastResult) {
    let lines = [];
    if (lastResult && lastResult.message) lines.push(lastResult.message);
    if (active && active.itemId) {
      lines.push(`Đang làm mã <b>${active.itemId}</b>: kiểm tra Omni-Studio Pro → bấm Tạo Video → bấm Tải. Video sẽ tự lưu đúng thư mục.`);
    }
    statusEl.innerHTML = lines.join("<br>") || "Chọn sản phẩm cần làm video.";
  }

  function refreshStatus() {
    chrome.storage.local.get(["flowActiveItem", "flowLastResult"], (s) => render(s.flowActiveItem, s.flowLastResult));
  }

  chrome.runtime.sendMessage({ action: "FLOW_LIST" }, (resp) => {
    refreshStatus();
    if (!resp || resp.status !== "success") {
      listEl.textContent = `⚠️ ${resp ? resp.message : "Không kết nối được Native Host"}`;
      return;
    }
    if (!resp.items.length) {
      listEl.textContent = "Không có sản phẩm nào đang chờ video.";
      return;
    }
    resp.items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "flow-item";
      const label = document.createElement("span");
      label.textContent = `${item.itemId} ${item.title || ""}`;
      label.title = label.textContent;
      const fillBtn = document.createElement("button");
      fillBtn.textContent = "Điền vào Flow";
      fillBtn.title = "Tự điền ảnh người mẫu, ảnh SP, kịch bản + giọng miền Nam vào Omni-Studio Pro đang mở";
      fillBtn.addEventListener("click", () => {
        fillBtn.disabled = true;
        statusEl.textContent = `Đang điền mã ${item.itemId}…`;
        chrome.runtime.sendMessage({ action: "FLOW_FILL", itemId: item.itemId }, (r) => {
          fillBtn.disabled = false;
          if (r && r.status === "success") {
            chrome.storage.local.remove("flowLastResult", refreshStatus);
          } else {
            statusEl.textContent = `⚠️ ${r ? (r.message || (r.failed || []).join("; ")) : "Lỗi kết nối"}`;
          }
        });
      });

      const btn = document.createElement("button");
      btn.textContent = "Finder";
      btn.title = "Dự phòng: mở Finder với 3 file để kéo thả tay";
      btn.style.background = "#555";
      btn.addEventListener("click", () => {
        btn.disabled = true;
        chrome.runtime.sendMessage({ action: "FLOW_PREPARE", itemId: item.itemId }, (r) => {
          btn.disabled = false;
          if (r && r.status === "success") {
            chrome.storage.local.remove("flowLastResult", refreshStatus);
          } else {
            statusEl.textContent = `⚠️ ${r ? r.message : "Lỗi Native Host"}`;
          }
        });
      });
      row.appendChild(label);
      row.appendChild(fillBtn);
      row.appendChild(btn);
      listEl.appendChild(row);
    });
  });
});
