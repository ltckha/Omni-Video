/**
 * Google Apps Script for Omni Video Shopee Image Curator & CSV Importer
 */

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // 1. Xử lý File CSV gửi từ Chay_Import_CSV.command
    if (data.action === "import_csv_text" && data.csvText) {
      var resultMsg = processCSVTextImport(sheet, data.csvText);
      return responseJSON({ status: "success", message: resultMsg });
    }
    
    // 2. Xử lý khi nhấn Alt + S từ Chrome Extension
    var itemId = String(data.itemId || "").trim();
    var cdnUrl = data.cdnUrl || "";
    var localPath = data.localPath || "";
    
    if (!itemId) {
      return responseJSON({ status: "error", message: "Missing itemId" });
    }
    
    // Đảm bảo đường dẫn local dẫn tới Product_Assets
    if (!localPath || !localPath.includes("Product_Assets")) {
      localPath = "/Users/khan/Developer/Omni-Video/Product_Assets/" + itemId + "/";
    } else if (!localPath.endsWith("/")) {
      localPath = localPath.substring(0, localPath.lastIndexOf("/") + 1);
    }
    
    var rows = sheet.getDataRange().getValues();
    var rowIndex = -1;
    
    for (var i = 1; i < rows.length; i++) {
      var cellValue = String(rows[i][0]).trim();
      var cellUrl = String(rows[i][7] || "").trim();
      if (cellValue === itemId || (cellUrl && cellUrl.includes(itemId))) {
        rowIndex = i + 1;
        break;
      }
    }
    
    if (rowIndex > 0) {
      // NẾU SẢN PHẨM ĐÃ CÓ TRÊN SHEET: Giữ nguyên thông tin CSV, chỉ cập nhật link ảnh & local folder
      var currentCdnUrl = sheet.getRange(rowIndex, 10).getValue();
      if (!currentCdnUrl || String(currentCdnUrl).trim() === "") {
        sheet.getRange(rowIndex, 10).setValue(cdnUrl);
      }
      
      sheet.getRange(rowIndex, 11).setValue(localPath);
      sheet.getRange(rowIndex, 12).setValue("Đã chọn ảnh");
      
      return responseJSON({
        status: "success",
        message: "Đã cập nhật thư mục ảnh cho dòng " + rowIndex,
        itemId: itemId
      });
    } else {
      // NẾU LÀ SẢN PHẨM MỚI CHƯA CÓ TRÊN SHEET: Tự động điền đầy đủ thông tin cào được từ trang Shopee
      var newRow = [
        itemId,                             // Col 1 (A): Mã sản phẩm
        data.productName || "Sản phẩm mới", // Col 2 (B): Tên sản phẩm
        data.price || "",                   // Col 3 (C): Giá cào được
        data.salesCount || "",              // Col 4 (D): Doanh thu / Đã bán cào được
        data.shopName || "",                // Col 5 (E): Tên cửa hàng cào được
        "",                                 // Col 6 (F): Tỉ lệ hoa hồng
        "",                                 // Col 7 (G): Hoa hồng
        data.productUrl || "",              // Col 8 (H): Link sản phẩm
        data.productUrl || "",              // Col 9 (I): Link ưu đãi
        cdnUrl,                             // Col 10 (J): Link ảnh CDN
        localPath,                          // Col 11 (K): File ảnh lưu local
        "Đã chọn ảnh"                       // Col 12 (L): Trạng thái Master Prompt
      ];
      sheet.appendRow(newRow);
      
      return responseJSON({
        status: "success",
        message: "Đã thêm mới đầy đủ thông tin cho mã " + itemId,
        itemId: itemId
      });
    }
  } catch (error) {
    return responseJSON({ status: "error", message: error.toString() });
  }
}

function processCSVTextImport(sheet, csvText) {
  var existingData = sheet.getDataRange().getValues();
  var existingItemIds = new Set();
  var existingProductUrls = new Set();
  
  for (var i = 1; i < existingData.length; i++) {
    var itemId = String(existingData[i][0] || "").trim();
    var productUrl = String(existingData[i][7] || "").trim();
    if (itemId) existingItemIds.add(itemId);
    if (productUrl) existingProductUrls.add(productUrl);
  }
  
  var rows = parseCSV(csvText);
  if (rows.length === 0) return "File CSV trống hoặc không đúng định dạng!";
  
  var addedCount = 0;
  var skippedCount = 0;
  
  var startIndex = 0;
  if (rows[0][0] && (rows[0][0].includes("Mã") || rows[0][0].includes("code"))) {
    startIndex = 1;
  }
  
  for (var k = startIndex; k < rows.length; k++) {
    var r = rows[k];
    if (!r || r.length < 2) continue;
    
    var rawItemId = String(r[0] || "").trim();
    var rawProductUrl = String(r[7] || r[8] || "").trim();
    
    var isDuplicate = false;
    if (rawItemId && existingItemIds.has(rawItemId)) isDuplicate = true;
    if (rawProductUrl && existingProductUrls.has(rawProductUrl)) isDuplicate = true;
    
    if (isDuplicate) {
      skippedCount++;
    } else {
      var folderPath = rawItemId ? ("/Users/khan/Developer/Omni-Video/Product_Assets/" + rawItemId + "/") : "";
      
      var newRow = [
        rawItemId,
        r[1] || "",
        r[2] || "",
        r[3] || "",
        r[4] || "",
        r[5] || "",
        r[6] || "",
        r[7] || "",
        r[8] || "",
        "",
        folderPath,
        "Chưa chọn ảnh"
      ];
      
      sheet.appendRow(newRow);
      if (rawItemId) existingItemIds.add(rawItemId);
      if (rawProductUrl) existingProductUrls.add(rawProductUrl);
      addedCount++;
    }
  }
  
  return "✅ Đã thêm " + addedCount + " sản phẩm mới vào Google Sheet! (Đã lọc bỏ " + skippedCount + " sản phẩm bị trùng)";
}

function parseCSV(text) {
  var p = '', c = '', r = [];
  var q = false;
  var row = [''];
  for (var i = 0; i < text.length; i++) {
    c = text[i];
    p = text[i - 1];
    if (c === '"') {
      if (q && text[i + 1] === '"') {
        row[row.length - 1] += '"';
        i++;
      } else {
        q = !q;
      }
    } else if (c === ',' && !q) {
      row.push('');
    } else if ((c === '\r' || c === '\n') && !q) {
      if (c === '\r' && text[i + 1] === '\n') { i++; }
      r.push(row);
      row = [''];
    } else {
      row[row.length - 1] += c;
    }
  }
  if (row.length > 1 || row[0] !== '') r.push(row);
  return r;
}

function responseJSON(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  return ContentService.createTextOutput("Omni UGC Google Apps Script API Server is Running!");
}
