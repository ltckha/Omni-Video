// Omni Video - Shopee Image Curator Content Script

let lastHoveredImageSrc = null;

// Lắng nghe di chuột bắt ảnh sản phẩm HD
document.addEventListener("mouseover", function (event) {
  let target = event.target;
  let src = extractImageSrc(target);

  if (src && src.includes("susercontent.com")) {
    lastHoveredImageSrc = cleanShopeeImageUrl(src);
    highlightElement(target);
  }
}, true);

// Bắt phím tắt Alt + S (Option + S trên Mac)
window.addEventListener("keydown", function (e) {
  if (e.altKey && (e.key === "s" || e.key === "S" || e.code === "KeyS" || e.keyCode === 83)) {
    e.preventDefault();
    e.stopPropagation();
    
    showToast("🔄 Đang quét thông tin & lấy ảnh sản phẩm...");
    captureAndSendImage();
  }
}, true);

function captureAndSendImage() {
  let info = getShopeeProductInfo();
  let targetSrc = lastHoveredImageSrc;

  // Nếu chưa hover trực tiếp, tự động bắt ảnh sản phẩm chính nét nhất trên trang
  if (!targetSrc) {
    let mainImgs = document.querySelectorAll("img[src*='susercontent.com'], div[style*='susercontent.com'], div[style*='background-image']");
    for (let img of mainImgs) {
      let src = extractImageSrc(img);
      if (src && src.includes("susercontent.com")) {
        targetSrc = cleanShopeeImageUrl(src);
        break;
      }
    }
  }

  if (!targetSrc) {
    showToast("⚠️ Vui lòng di chuột lên bức ảnh sản phẩm cần lưu!", true);
    return;
  }

  chrome.runtime.sendMessage({
    action: "TRIGGER_SAVE_IMAGE",
    payload: {
      success: true,
      cdnUrl: targetSrc,
      itemId: info.itemId,
      shopId: info.shopId,
      productName: info.productName,
      price: info.price,
      salesCount: info.salesCount,
      shopName: info.shopName,
      productUrl: info.productUrl
    }
  });
}

function extractImageSrc(target) {
  if (!target) return null;
  if (target.tagName === "IMG" && (target.currentSrc || target.src)) {
    return target.currentSrc || target.src;
  }
  let curr = target;
  for (let i = 0; i < 4 && curr; i++) {
    if (curr.style && curr.style.backgroundImage) {
      let match = curr.style.backgroundImage.match(/url\(["']?(.*?)["']?\)/);
      if (match) return match[1];
    }
    let childImg = curr.querySelector("img");
    if (childImg && (childImg.currentSrc || childImg.src)) {
      return childImg.currentSrc || childImg.src;
    }
    curr = curr.parentElement;
  }
  return null;
}

function cleanShopeeImageUrl(url) {
  if (!url) return null;
  let cleanUrl = url.split("?")[0];
  cleanUrl = cleanUrl.replace(/_tn$/, "").replace(/_bg$/, "").replace(/_\d+x\d+$/, "");
  if (cleanUrl.startsWith("//")) {
    cleanUrl = "https:" + cleanUrl;
  }
  return cleanUrl;
}

function highlightElement(el) {
  if (!el) return;
  let prevOutline = el.style.outline;
  el.style.outline = "3px solid #ff5722";
  setTimeout(() => {
    el.style.outline = prevOutline;
  }, 1000);
}

function getShopeeProductInfo() {
  let rawUrl = window.location.href;
  let canonical = document.querySelector("link[rel='canonical']")?.href || "";
  let metaUrl = document.querySelector("meta[property='og:url']")?.content || "";
  
  let fullText = decodeURIComponent(rawUrl + " " + canonical + " " + metaUrl);

  let itemId = null;
  let shopId = null;

  let p1 = fullText.match(/i\.(\d+)\.(\d+)/);
  if (p1) {
    shopId = p1[1];
    itemId = p1[2];
  } else {
    let p2 = fullText.match(/product\/(\d+)\/(\d+)/);
    if (p2) {
      shopId = p2[1];
      itemId = p2[2];
    } else {
      let p3 = fullText.match(/itemid=(\d+)/i);
      if (p3) itemId = p3[1];
    }
  }

  let titleEl = document.querySelector("div._44qnta, div.Vb3wB-, h1.product-title, h1, meta[property='og:title']");
  let productName = "";
  if (titleEl) {
    productName = titleEl.content || titleEl.innerText || titleEl.textContent || "";
  }
  if (!productName || productName.includes("Shopee")) {
    productName = document.title.replace("| Shopee Việt Nam", "").trim();
  }

  let priceEl = document.querySelector("div.pqom2P, div.vZ8TOe, div.G27lhz, div._2v0flw, div._3n5t2x, meta[property='product:price:amount']");
  let price = "";
  if (priceEl) {
    price = priceEl.content || priceEl.innerText || "";
    price = price.replace(/\n/g, " ").trim();
  }

  let salesEl = document.querySelector("div.e222fZ, div.rP3t22, div._22oTVb, div.A3T5L-, div.rcP-2H");
  let salesCount = salesEl ? salesEl.innerText.trim() : "";

  let shopEl = document.querySelector("div._2m-i93, div.page-product__shop, a._26s_c2, div.shop-page-shop-name, div.P2r3+g");
  let shopName = shopEl ? shopEl.innerText.trim() : "";

  return {
    itemId: itemId || ("SP_" + new Date().getTime()),
    shopId: shopId,
    productName: productName.trim(),
    price: price,
    salesCount: salesCount,
    shopName: shopName,
    productUrl: rawUrl.split("?")[0]
  };
}

function showToast(msg, isError = false) {
  let oldToast = document.getElementById("omni-curator-toast");
  if (oldToast) oldToast.remove();

  let toast = document.createElement("div");
  toast.id = "omni-curator-toast";
  toast.innerText = msg;
  toast.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    background-color: ${isError ? '#d32f2f' : '#2e7d32'};
    color: #ffffff;
    padding: 12px 20px;
    border-radius: 8px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    font-weight: bold;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    z-index: 999999999;
    transition: opacity 0.3s ease;
  `;

  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "GET_SELECTED_IMAGE") {
    captureAndSendImage();
    sendResponse({ success: true });
  } else if (request.action === "SHOW_TOAST") {
    showToast(request.msg, request.isError);
  }
  return true;
});
