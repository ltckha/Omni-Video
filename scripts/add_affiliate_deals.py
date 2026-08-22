import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from scripts.sheet_sync import sync_product_to_sheet

deals = [
    {
        "item_id": "44321903694",
        "title": "Lồng đèn con thỏ hottrend chơi trung thu trang trí nhà cửa phát sáng có đèn LED",
        "price": "28,0k",
        "sales_count": "10k+",
        "shop_name": "Xưởng Lồng Đèn Trung Thu",
        "commission_rate": "18%",
        "commission": "₫5.040",
        "product_url": "https://shopee.vn/L%E1%BB%93ng-%C4%91%C3%A8n-con-th%E1%BB%8F-hottrend-ch%C6%A1i-trung-thu-trang-tr%C3%AD-nh%C3%A0-c%E1%BB%ADa-ti%E1%BB%87m-c%E1%BB%ADa-h%C3%A0ng-%C4%91%E1%BB%81u-%C4%91%C6%B0%E1%BB%A3c-i.143986037.44321903694",
        "shopee_link": "https://shopee.vn/L%E1%BB%93ng-%C4%91%C3%A8n-con-th%E1%BB%8F-hottrend-ch%C6%A1i-trung-thu-trang-tr%C3%AD-nh%C3%A0-c%E1%BB%ADa-ti%E1%BB%87m-c%E1%BB%ADa-h%C3%A0ng-%C4%91%E1%BB%81u-%C4%91%C6%B0%E1%BB%A3c-i.143986037.44321903694",
        "cdn_url": "",
        "local_path": "Product_Assets/44321903694/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "57811649458",
        "title": "Khuôn bánh trung thu lò xo 50g 4 mặt túi tiền tài lộc sắc nét KH216I",
        "price": "35,0k",
        "sales_count": "5k+",
        "shop_name": "Dụng Cụ Làm Bánh Official",
        "commission_rate": "15%",
        "commission": "₫5.250",
        "product_url": "https://shopee.vn/Khu%C3%B4n-b%C3%A1nh-trung-thu-l%C3%B2-xo-50g-4-m%E1%BA%B7t-t%C3%BAi-t-i%E1%BB%81n-t%C3%A0i-l%E1%BB%99c-s%E1%BA%AFc-n%C3%A9t-KH216I-i.1206245333.57811649458",
        "shopee_link": "https://shopee.vn/Khu%C3%B4n-b%C3%A1nh-trung-thu-l%C3%B2-xo-50g-4-m%E1%BA%B7t-t%C3%BAi-t-i%E1%BB%81n-t%C3%A0i-l%E1%BB%99c-s%E1%BA%AFc-n%C3%A9t-KH216I-i.1206245333.57811649458",
        "cdn_url": "",
        "local_path": "Product_Assets/57811649458/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "23806858395",
        "title": "Đai Chống Gù Lưng Rung Cảm Biến Điện Tử Thông Minh Cao Cấp KYPHOSIS-FK211",
        "price": "129,0k",
        "sales_count": "8k+",
        "shop_name": "Kyphosis Store",
        "commission_rate": "16%",
        "commission": "₫20.640",
        "product_url": "https://shopee.vn/%C4%90ai-Ch%E1%BB%91ng-G%C3%B9-L%C6%B0ng-Rung-C%E1%BA%A3m-Bi%E1%BA%BFn-%C4%91i%E1%BB%87n-T%E1%BB%AD-Th%C3%B4ng-Minh-Lo%E1%BA%A1i-Cao-C%E1%BA%A5p-KYPHOSIS-FK211-BH-12-TH%C3%81NG--i.882613688.23806858395",
        "shopee_link": "https://shopee.vn/%C4%90ai-Ch%E1%BB%91ng-G%C3%B9-L%C6%B0ng-Rung-C%E1%BA%A3m-Bi%E1%BA%BFn-%C4%91i%E1%BB%87n-T%E1%BB%AD-Th%C3%B4ng-Minh-Lo%E1%BA%A1i-Cao-C%E1%BA%A5p-KYPHOSIS-FK211-BH-12-TH%C3%81NG--i.882613688.23806858395",
        "cdn_url": "",
        "local_path": "Product_Assets/23806858395/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "23859205708",
        "title": "Hộp cơm cắm điện cao cấp inox 2 tầng không dùng nước giữ trọn hương vị tươi ngon",
        "price": "245,0k",
        "sales_count": "12k+",
        "shop_name": "Gia Dụng Tiện Ích Mall",
        "commission_rate": "12%",
        "commission": "₫29.400",
        "product_url": "https://shopee.vn/H%E1%BB%99p-c%C6%A1m-c%E1%BA%AFm-%C4%91i%E1%BB%87n-cao-c%E1%BA%A5p-1-t%E1%BA%A7ng-2-ng%C4%83n-kh%C3%B4ng-d%C3%B9ng-n%C6%B0%E1%BB%9Bc-gi%E1%BB%AF-tr%E1%BB%8Dn-h%C6%B0%C6%A1ng-v%E1%BB%8B-t%C6%B0%C6%A1i-ngon-i.102406024.23859205708",
        "shopee_link": "https://shopee.vn/H%E1%BB%99p-c%C6%A1m-c%E1%BA%AFm-%C4%91i%E1%BB%87n-cao-c%E1%BA%A5p-1-t%E1%BA%A7ng-2-ng%C4%83n-kh%C3%B4ng-d%C3%B9ng-n%C6%B0%E1%BB%9Bc-gi%E1%BB%AF-tr%E1%BB%8Dn-h%C6%B0%C6%A1ng-v%E1%BB%8B-t%C6%B0%C6%A1i-ngon-i.102406024.23859205708",
        "cdn_url": "",
        "local_path": "Product_Assets/23859205708/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "26759614987",
        "title": "Ruốc nấm hương, ruốc nấm chay ngon thượng hạng ăn liền Túi 300G",
        "price": "49,0k",
        "sales_count": "15k+",
        "shop_name": "Thực Phẩm Chay Cô Điều",
        "commission_rate": "15%",
        "commission": "₫7.350",
        "product_url": "https://shopee.vn/Ru%E1%BB%91c-n%E1%BA%A5m-h%C6%B0%C6%A1ng-ru%E1%BB%91c-n%E1%BA%A5m-chay-ngon-th%C6%B0%E1%BB%A3ng-h%E1%BA%A1ng-T%C3%BAi-300G-i.1234409991.26759614987",
        "shopee_link": "https://shopee.vn/Ru%E1%BB%91c-n%E1%BA%A5m-h%C6%B0%C6%A1ng-ru%E1%BB%91c-n%E1%BA%A5m-chay-ngon-th%C6%B0%E1%BB%A3ng-h%E1%BA%A1ng-T%C3%BAi-300G-i.1234409991.26759614987",
        "cdn_url": "",
        "local_path": "Product_Assets/26759614987/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "22188767638",
        "title": "Xịt Nano Chống Nước Mưa và Sương Mù Kính Mũ Bảo Hiểm, Gương Chiếu Hậu Xe Máy Ô Tô",
        "price": "45,0k",
        "sales_count": "20k+",
        "shop_name": "Auto Care VN",
        "commission_rate": "14%",
        "commission": "₫6.300",
        "product_url": "https://shopee.vn/X%E1%BB%8Bt-Nano-Ch%E1%BB%91ng-N%C6%B0%E1%BB%9Bc-M%C6%B0a-Ch%E1%BB%91ng-s%C6%B0%C6%A1ng-K%C3%ADnh-M%C5%A9-B%E1%BA%A3o-Hi%E1%BB%83m-k%C3%ADnh-g%C6%B0%C6%A1ng-xe-m%C3%A1y-k%C3%ADnh-%C3%B4-t%C3%B4-i.53504342.22188767638",
        "shopee_link": "https://shopee.vn/X%E1%BB%8Bt-Nano-Ch%E1%BB%91ng-N%C6%B0%E1%BB%9Bc-M%C6%B0a-Ch%E1%BB%91ng-s%C6%B0%C6%A1ng-K%C3%ADnh-M%C5%A9-B%E1%BA%A3o-Hi%E1%BB%83m-k%C3%ADnh-g%C6%B0%C6%A1ng-xe-m%C3%A1y-k%C3%ADnh-%C3%B4-t%C3%B4-i.53504342.22188767638",
        "cdn_url": "",
        "local_path": "Product_Assets/22188767638/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "42350039379",
        "title": "Bồn Ngâm Chân Massage Tự Động Gấp Gọn Chế Độ Làm Nóng Sục Khí Đèn Hồng Ngoại",
        "price": "320,0k",
        "sales_count": "9k+",
        "shop_name": "Smart Life Official",
        "commission_rate": "15%",
        "commission": "₫48.000",
        "product_url": "https://shopee.vn/Smart-Life-B%E1%BB%93n-Ng%C3%A2m-Ch%C3%A2n-Massage-T%E1%BB%B1-%C4%90%E1%BB%99ng-G%E1%BA%A5p-G%E1%BB%8Dn-Ch%E1%BA%BF-%C4%90%E1%BB%99-L%C3%A0m-N%C3%B3ng-S%E1%BB%A5c-Kh%C3%AD-T%E1%BB%B1-%C4%90%E1%BB%99ng-M%C3%A0n-H%C3%ACnh-C%E1%BA%A3m-%E1%BB%A8ng-V%E1%BB%9Bi-6-Con-L%C4%83n-i.904573128.42350039379",
        "shopee_link": "https://shopee.vn/Smart-Life-B%E1%BB%93n-Ng%C3%A2m-Ch%C3%A2n-Massage-T%E1%BB%B1-%C4%90%E1%BB%99ng-G%E1%BA%A5p-G%E1%BB%8Dn-Ch%E1%BA%BF-%C4%90%E1%BB%99-L%C3%A0m-N%C3%B3ng-S%E1%BB%A5c-Kh%C3%AD-T%E1%BB%B1-%C4%90%E1%BB%99ng-M%C3%A0n-H%C3%ACnh-C%E1%BA%A3m-%E1%BB%A8ng-V%E1%BB%9Bi-6-Con-L%C4%83n-i.904573128.42350039379",
        "cdn_url": "",
        "local_path": "Product_Assets/42350039379/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "29323746870",
        "title": "Hộp Nụ Trầm Hương Cao Cấp 380g Khói Chảy Ngược Thơm Tự Nhiên Dành Cho Thác Khói",
        "price": "75,0k",
        "sales_count": "18k+",
        "shop_name": "Trầm Hương Phúc An",
        "commission_rate": "20%",
        "commission": "₫15.000",
        "product_url": "https://shopee.vn/H%E1%BB%99p-N%E1%BB%A5-Tr%E1%BA%A7m-H%C6%B0%C6%A1ng-Cao-C%E1%BA%A5p-380g-Kh%C3%B4ng-Ch%E1%BA%A3y-Ng%C6%B0%E1%BB%A3c-N%E1%BB%A5-Tr%E1%BA%A7m-H%C6%B0%C6%A1ng-Th%C6%A1m-T%E1%BB%B1-Nhi%C3%AAn-D%C3%A0nh-Cho-Th%C3%A1c-Kh%C3%B3i-i.650447861.29323746870",
        "shopee_link": "https://shopee.vn/H%E1%BB%99p-N%E1%BB%A5-Tr%E1%BA%A7m-H%C6%B0%C6%A1ng-Cao-C%E1%BA%A5p-380g-Kh%C3%B4ng-Ch%E1%BA%A3y-Ng%C6%B0%E1%BB%A3c-N%E1%BB%A5-Tr%E1%BA%A7m-H%C6%B0%C6%A1ng-Th%C6%A1m-T%E1%BB%B1-Nhi%C3%AAn-D%C3%A0nh-Cho-Th%C3%A1c-Kh%C3%B3i-i.650447861.29323746870",
        "cdn_url": "",
        "local_path": "Product_Assets/29323746870/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    }
]

success_count = 0
for deal in deals:
    item_id = deal["item_id"]
    print(f"Đang đồng bộ deal {item_id}: {deal['title']}...")
    res = sync_product_to_sheet(deal, item_id)
    if res:
        success_count += 1
        print(f"-> Thành công: {item_id}")
    else:
        print(f"-> Thất bại: {item_id}")

print("Hoan thanh dong bo %d/%d san pham vao Google Sheet." % (success_count, len(deals)))
