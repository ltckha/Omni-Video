// Omni Video - Popup: chuẩn bị sản phẩm cho Google Flow (anh Kha tự bấm Tạo / Tải trên Flow)

document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("flowStatus");
  const listEl = document.getElementById("flowList");

  chrome.action.setBadgeText({ text: "" });

  function render(active, lastResult) {
    let lines = [];
    if (lastResult && lastResult.message) lines.push(lastResult.message);
    if (active && active.itemId) {
      lines.push(`Đang làm mã <b>${active.itemId}</b>: extension đang tự Tạo → Phê duyệt → chờ → Tải trên tab Flow (để tab Flow mở). Chrome hỏi Save thì anh bấm Save.`);
    }
    statusEl.innerHTML = lines.join("<br>") || "Chọn sản phẩm cần làm video.";
  }

  function refreshStatus() {
    chrome.storage.local.get(["flowActiveItem", "flowLastResult"], (s) => render(s.flowActiveItem, s.flowLastResult));
  }

  chrome.runtime.sendMessage({ action: "FLOW_LIST" }, (resp) => {
    refreshStatus();
    if (resp && resp.seasons && resp.seasons.length) {
      const box = document.createElement("div");
      box.className = "flow-status";
      box.textContent = resp.seasons.join("\n");
      box.style.whiteSpace = "pre-line";
      statusEl.parentNode.insertBefore(box, statusEl);
    }
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
      fillBtn.textContent = "Tạo video";
      fillBtn.title = "Tự điền + bấm Tạo + Phê duyệt 15 credit + tải <mã>.mp4 trên dự án Flow đang mở";
      fillBtn.addEventListener("click", () => {
        fillBtn.disabled = true;
        statusEl.textContent = `Đang làm mã ${item.itemId}…`;
        chrome.runtime.sendMessage({ action: "FLOW_FILL", itemId: item.itemId }, (r) => {
          fillBtn.disabled = false;
          if (r && r.status === "success") {
            chrome.storage.local.remove("flowLastResult", refreshStatus);
          } else {
            statusEl.textContent = `⚠️ ${r ? (r.message || (r.failed || []).join("; ")) : "Lỗi kết nối"}`;
          }
        });
      });

      row.appendChild(label);
      row.appendChild(fillBtn);
      listEl.appendChild(row);
    });
  });
});
