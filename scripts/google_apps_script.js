/**
 * Google Apps Script for Omni Video Shopee Image Curator & CSV Importer & Master Prompt Generator
 * Đã bảo vệ trạng thái "Đã tạo Video" cao nhất không bị đè ngược lại.
 */

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // 1. Lấy danh sách toàn bộ sản phẩm trên Sheet để Python đọc Tên SP & Trạng thái
    if (data.action === "get_all_products") {
      var rows = sheet.getDataRange().getValues();
      var productsMap = {};
      for (var i = 1; i < rows.length; i++) {
        var itemId = String(rows[i][0]).trim();
        if (itemId) {
          productsMap[itemId] = {
            itemId: itemId,
            productName: String(rows[i][1] || "").trim(),
            price: String(rows[i][2] || "").trim(),
            salesCount: String(rows[i][3] || "").trim(),
            shopName: String(rows[i][4] || "").trim(),
            productUrl: String(rows[i][7] || "").trim(),
            cdnUrl: String(rows[i][9] || "").trim(),
            localPath: String(rows[i][10] || "").trim(),
            status: String(rows[i][11] || "").trim()
          };
        }
      }
      return responseJSON({ status: "success", products: productsMap });
    }
    
    // 2. Cập nhật trạng thái Master Prompt (Ví dụ: "Đã tạo Prompt")
    if (data.action === "update_status" && data.itemId) {
      var targetItemId = String(data.itemId).trim();
      var newStatus = data.status || "Đã tạo Prompt";
      var rows = sheet.getDataRange().getValues();
      for (var j = 1; j < rows.length; j++) {
        if (String(rows[j][0]).trim() === targetItemId) {
          var currentStatus = String(rows[j][11] || "").trim();
          // BẢO VỆ: Nếu trạng thái hiện tại đã là "Đã tạo Video", KHÔNG cho phép đè ngược lại
          if (currentStatus === "Đã tạo Video") {
            return responseJSON({ status: "success", message: "Giữ nguyên trạng thái 'Đã tạo Video' cho mã " + targetItemId });
          }
          sheet.getRange(j + 1, 12).setValue(newStatus);
          return responseJSON({ status: "success", message: "Đã cập nhật trạng thái dòng " + (j + 1) });
        }
      }
      return responseJSON({ status: "error", message: "Không tìm thấy mã SP " + targetItemId });
    }
    
    // 3. Xử lý Import File CSV gửi từ Import.command
    if (data.action === "import_csv_text" && data.csvText) {
      var resultMsg = processCSVTextImport(sheet, data.csvText);
      return responseJSON({ status: "success", message: resultMsg });
    }
    
    // 4. Xử lý khi nhấn Alt + S từ Chrome Extension
    var itemId = String(data.itemId || "").trim();
    var cdnUrl = data.cdnUrl || "";
    
    if (!itemId) {
      return responseJSON({ status: "error", message: "Missing itemId" });
    }
    
    var localPath = "Product_Assets/" + itemId + "/";
    
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
      var currentCdnUrl = sheet.getRange(rowIndex, 10).getValue();
      if (!currentCdnUrl || String(currentCdnUrl).trim() === "") {
        sheet.getRange(rowIndex, 10).setValue(cdnUrl);
      }
      sheet.getRange(rowIndex, 11).setValue(localPath);
      
      // BẢO VỆ: Chỉ cập nhật "Đã chọn ảnh" nếu trạng thái hiện tại chưa phải "Đã tạo Video" hoặc "Đã tạo Prompt"
      var currentStatus = String(sheet.getRange(rowIndex, 12).getValue() || "").trim();
      if (currentStatus !== "Đã tạo Video" && currentStatus !== "Đã tạo Prompt") {
        sheet.getRange(rowIndex, 12).setValue("Đã chọn ảnh");
      }
      
      return responseJSON({
        status: "success",
        message: "Đã cập nhật thư mục ảnh cho dòng " + rowIndex,
        itemId: itemId
      });
    } else {
      // Sản phẩm mới chưa có trên Sheet -> Thêm dòng mới
      var newRow = [
        itemId,
        data.productName || "Sản phẩm mới",
        data.price || "",
        data.salesCount || "",
        data.shopName || "",
        "",
        "",
        data.productUrl || "",
        data.productUrl || "",
        cdnUrl,
        localPath,
        "Đã chọn ảnh"
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
      var folderPath = rawItemId ? ("Product_Assets/" + rawItemId + "/") : "";
      
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
