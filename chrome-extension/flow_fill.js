// Omni Video - Tự điền 3 file vào công cụ "Omni-Studio Pro" trên Google Flow.
// Chạy trong khung (iframe) của công cụ. Chỉ điền + chọn giọng; anh Kha tự bấm "Tạo Video" và "Tải".
// Không tự bấm Tạo, không chạy lô.

(function () {
  const SLOT_LABELS = {
    character: ["NGƯỜI MẪU", "NGUOI MAU"],
    product: ["SẢN PHẨM", "SAN PHAM"],
    script: ["KỊCH BẢN", "KICH BAN"]
  };

  function upper(s) {
    return (s || "").toUpperCase();
  }

  function isCard(el) {
    return !!el.querySelector("input[type=file], textarea") || (/KÉO THẢ|KEO THA/.test(upper(el.textContent)) && el.offsetHeight > 80);
  }

  // Khối (card) nhỏ nhất vừa chứa nhãn (vd "SẢN PHẨM (0)") vừa có ô tải file / ô thả / ô nhập chữ.
  // Chữ nhãn còn xuất hiện ở chỗ khác (vd "Kịch bản: Trống" ở khung trái) -> chọn khối nhỏ nhất.
  function findCard(labels) {
    let best = null;
    for (const el of document.querySelectorAll("body *")) {
      if (el.children.length > 3) continue;
      if (!labels.some((l) => upper(el.textContent).includes(l))) continue;
      let card = el;
      for (let i = 0; i < 8 && card && !isCard(card); i++) card = card.parentElement;
      if (card && isCard(card) && (!best || card.textContent.length < best.textContent.length)) best = card;
    }
    return best;
  }

  function b64ToBytes(b64) {
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return bytes;
  }

  function b64ToFile(file) {
    return new File([b64ToBytes(file.b64)], file.name, { type: file.mime });
  }

  function setNativeValue(el, value) {
    const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, "value").set.call(el, value);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function dropFile(target, fileObj) {
    const dt = new DataTransfer();
    dt.items.add(fileObj);
    for (const type of ["dragenter", "dragover", "drop"]) {
      target.dispatchEvent(new DragEvent(type, { bubbles: true, cancelable: true, dataTransfer: dt }));
    }
  }

  function fillSlot(card, file) {
    const fileObj = b64ToFile(file);
    if (file.slot === "script") {
      const textarea = card.querySelector("textarea");
      if (textarea) {
        setNativeValue(textarea, new TextDecoder().decode(b64ToBytes(file.b64)));
        return "chữ";
      }
    }
    const input = card.querySelector("input[type=file]");
    if (input) {
      const dt = new DataTransfer();
      dt.items.add(fileObj);
      input.files = dt.files;
      input.dispatchEvent(new Event("change", { bubbles: true }));
      return "file";
    }
    const zone = [...card.querySelectorAll("*")].find((el) => /KÉO THẢ|KEO THA/.test(upper(el.textContent)) && el.children.length < 4) || card;
    dropFile(zone, fileObj);
    return "thả";
  }

  // Giọng: chọn giọng miền Nam đúng giới tính nhân vật (Nu-* -> Nữ, Nam-* -> Nam)
  function selectSouthernVoice(characterName) {
    const gender = /^nam-/i.test(characterName) ? "NAM" : "NỮ";
    for (const select of document.querySelectorAll("select")) {
      const option = [...select.options].find((o) => {
        const t = upper(o.textContent);
        return t.includes("MIỀN NAM") && t.includes(`(${gender}`);
      });
      if (option) {
        select.value = option.value;
        select.dispatchEvent(new Event("change", { bubbles: true }));
        return option.textContent.trim();
      }
    }
    return null;
  }

  function showToast(msg, isError) {
    const div = document.createElement("div");
    div.textContent = msg;
    div.style.cssText = `position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:2147483647;
      background:${isError ? "#d32f2f" : "#2e7d32"};color:#fff;padding:10px 16px;border-radius:6px;
      font:13px -apple-system,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.4);max-width:80%;`;
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 6000);
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action !== "FLOW_FILL") return false;
    const cards = {};
    for (const slot of Object.keys(SLOT_LABELS)) {
      cards[slot] = findCard(SLOT_LABELS[slot]);
    }
    // Không phải khung Omni-Studio Pro -> im lặng để khung khác trả lời
    if (!cards.character || !cards.product || !cards.script) return false;

    const filled = [];
    const failed = [];
    for (const file of message.files) {
      try {
        filled.push(`${file.slot}:${fillSlot(cards[file.slot], file)}`);
      } catch (e) {
        failed.push(`${file.slot}: ${e.message}`);
      }
    }
    const character = message.files.find((f) => f.slot === "character");
    const voice = selectSouthernVoice(character ? character.name : "");
    if (!voice) failed.push("giọng: không tìm thấy lựa chọn miền Nam — anh chọn tay");

    const ok = failed.length === 0;
    showToast(ok ? `✅ Đã điền mã ${message.itemId} (giọng ${voice}). Anh kiểm tra rồi bấm Tạo Video.` :
      `⚠️ Mã ${message.itemId}: ${failed.join("; ")}`, !ok);
    sendResponse({ status: ok ? "success" : "partial", filled, failed, voice });
    return false;
  });
})();
