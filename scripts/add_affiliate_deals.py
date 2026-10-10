import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from scripts.sheet_sync import sync_product_to_sheet

# Danh sách 8 deal chuẩn Shopee Mall 100%, tồn kho dồi dào, lượt bán khủng (>9k - 120k+)
deals = [
    {
        "item_id": "27688886739",
        "title": "Kem Chống Nắng Nâng Tone Mizumi UV Bright Body Serum Lilac SPF50+ PA++++ 120g",
        "price": "199,0k",
        "sales_count": "35k+",
        "shop_name": "Mizumi Official Store (Shopee Mall)",
        "commission_rate": "15%",
        "commission": "₫29.850",
        "product_url": "https://shopee.vn/Kem-Ch%E1%BB%91ng-N%E1%BA%AFng-N%C3%A2ng-Tone-Mizumi-UV-Bright-Body-Serum-Lilac-SPF50-PA-120g-i.193849872.27688886739",
        "shopee_link": "https://shopee.vn/Kem-Ch%E1%BB%91ng-N%E1%BA%AFng-N%C3%A2ng-Tone-Mizumi-UV-Bright-Body-Serum-Lilac-SPF50-PA-120g-i.193849872.27688886739",
        "cdn_url": "",
        "local_path": "Product_Assets/27688886739/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "17892184297",
        "title": "Sữa Tắm Thiên Nhiên PURITÉ Hương Hoa Anh Đào Dưỡng Ẩm Mịn Màng 500ml",
        "price": "159,0k",
        "sales_count": "48k+",
        "shop_name": "Purité de Prôvence Official Store (Shopee Mall)",
        "commission_rate": "14%",
        "commission": "₫22.260",
        "product_url": "https://shopee.vn/-BAO-B%C3%8C-M%E1%BB%9AI-S%E1%BB%AFa-T%E1%BA%AFm-Thi%C3%AAn-Nhi%C3%AAn-PURIT%C3%89-H%C6%B0%C6%A1ng-Hoa-Anh-%C4%90%C3%A0o-Hoa-H%E1%BB%93ng-Hoa-M%E1%BA%ABu-%C4%90%C6%A1n-250ml-500ml-i.779659055.17892184297",
        "shopee_link": "https://shopee.vn/-BAO-B%C3%8C-M%E1%BB%9AI-S%E1%BB%AFa-T%E1%BA%AFm-Thi%C3%AAn-Nhi%C3%AAn-PURIT%C3%89-H%C6%B0%C6%A1ng-Hoa-Anh-%C4%90%C3%A0o-Hoa-H%E1%BB%93ng-Hoa-M%E1%BA%ABu-%C4%90%C6%A1n-250ml-500ml-i.779659055.17892184297",
        "cdn_url": "",
        "local_path": "Product_Assets/17892184297/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "13801034936",
        "title": "Sữa Tắm Gội Romano Classic 2 In 1 Nước Hoa Nam Giới 650g",
        "price": "149,0k",
        "sales_count": "75k+",
        "shop_name": "Romano Official Store (Shopee Mall)",
        "commission_rate": "14%",
        "commission": "₫20.860",
        "product_url": "https://shopee.vn/S%E1%BB%AFa-T%E1%BA%AFm-G%E1%BB%99i-Romano-Classic-2-In-1-S%E1%BB%AFa-T%E1%BA%AFm-G%E1%BB%99i-2-Trong-1-N%C6%B0%E1%BB%9Bc-Hoa-Nam-Gi%E1%BB%9Bi-650G-i.49096610.13801034936",
        "shopee_link": "https://shopee.vn/S%E1%BB%AFa-T%E1%BA%AFm-G%E1%BB%99i-Romano-Classic-2-In-1-S%E1%BB%AFa-T%E1%BA%AFm-G%E1%BB%99i-2-Trong-1-N%C6%B0%E1%BB%9Bc-Hoa-Nam-Gi%E1%BB%9Bi-650G-i.49096610.13801034936",
        "cdn_url": "",
        "local_path": "Product_Assets/13801034936/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "23522549414",
        "title": "Kem Dưỡng Làm Dịu Và Phục Hồi Da La Roche-Posay Cicaplast Baume B5 Soothing Repairing Balm 40ml/100ml",
        "price": "285,0k",
        "sales_count": "120k+",
        "shop_name": "La Roche-Posay Chính Hãng (Shopee Mall)",
        "commission_rate": "12%",
        "commission": "₫34.200",
        "product_url": "https://shopee.vn/La-Roche-Posay-Kem-D%C6%B0%E1%BB%A1ng-L%C3%A0m-D%E1%BB%8Bu-V%C3%A0-Ph%E1%BB%A5c-H%E1%BB%93i-Da-Cicaplast-Baume-B5-Soothing-Repairing-Balm-40Ml-100Ml-i.169424786.23522549414",
        "shopee_link": "https://shopee.vn/La-Roche-Posay-Kem-D%C6%B0%E1%BB%A1ng-L%C3%A0m-D%E1%BB%8Bu-V%C3%A0-Ph%E1%BB%A5c-H%E1%BB%93i-Da-Cicaplast-Baume-B5-Soothing-Repairing-Balm-40Ml-100Ml-i.169424786.23522549414",
        "cdn_url": "",
        "local_path": "Product_Assets/23522549414/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "29657142185",
        "title": "Sữa Rửa Mặt CeraVe Foaming Cleanser 236ml-473ml Cho Da Dầu Mụn Nhạy Cảm",
        "price": "295,0k",
        "sales_count": "85k+",
        "shop_name": "CeraVe Skincare Mall (Shopee Mall)",
        "commission_rate": "12%",
        "commission": "₫35.400",
        "product_url": "https://shopee.vn/S%E1%BB%AFa-R%E1%BB%ADa-M%E1%BA%B7t-CeraVe-Foaming-Cleanser-236-473ml-Ch%C3%ADnh-H%C3%A3ng-Cho-Da-D%E1%BA%A7u-Da-Kh%C3%B4-M%E1%BB%A5n-Nh%E1%BA%A1y-C%E1%BA%A3m-i.945320750.29657142185",
        "shopee_link": "https://shopee.vn/S%E1%BB%AFa-R%E1%BB%ADa-M%E1%BA%B7t-CeraVe-Foaming-Cleanser-236-473ml-Ch%C3%ADnh-H%C3%A3ng-Cho-Da-D%E1%BA%A7u-Da-Kh%C3%B4-M%E1%BB%A5n-Nh%E1%BA%A1y-C%E1%BA%A3m-i.945320750.29657142185",
        "cdn_url": "",
        "local_path": "Product_Assets/29657142185/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "5540642352",
        "title": "Bình Giữ Nhiệt LocknLock Touch Tumbler LHC3270 Dung Tích 400ml Thép SUS316L Cao Cấp",
        "price": "289,0k",
        "sales_count": "9k+",
        "shop_name": "LocknLock K-MALL Official (Shopee Mall)",
        "commission_rate": "14%",
        "commission": "₫40.460",
        "product_url": "https://shopee.vn/B%C3%ACnh-gi%E1%BB%AF-nhi%E1%BB%87t-LocknLock-Touch-Tumbler-LHC3270-dung-t%C3%ADch-400ml-th%C3%A9p-kh%C3%B4ng-g%E1%BB%89-SUS316L-K-MALL-i.16911437.5540642352",
        "shopee_link": "https://shopee.vn/B%C3%ACnh-gi%E1%BB%AF-nhi%E1%BB%87t-LocknLock-Touch-Tumbler-LHC3270-dung-t%C3%ADch-400ml-th%C3%A9p-kh%C3%B4ng-g%E1%BB%89-SUS316L-K-MALL-i.16911437.5540642352",
        "cdn_url": "",
        "local_path": "Product_Assets/5540642352/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "29313519647",
        "title": "Ấm Siêu Tốc Inox 1.8 Lít SUNHOUSE SHD1182 Đun Sôi Cực Nhanh Chống Cạn Nước",
        "price": "139,0k",
        "sales_count": "30k+",
        "shop_name": "Sunhouse Chính Hãng (Shopee Mall)",
        "commission_rate": "12%",
        "commission": "₫16.680",
        "product_url": "https://shopee.vn/%E1%BA%A4M-SI%C3%8AU-T%E1%BB%90C-INOX-1.8-L-SUNHOUSE-SHD1182-H%C3%A0ng-ch%C3%ADnh-h%C3%A3ng-b%E1%BA%A3o-h%C3%A0nh-12-th%C3%A1ng-%C4%90un-s%C3%B4i-t%E1%BB%AB-4-%C4%91%E1%BA%BFn-6-ph%C3%BAt-i.556587954.29313519647",
        "shopee_link": "https://shopee.vn/%E1%BA%A4M-SI%C3%8AU-T%E1%BB%90C-INOX-1.8-L-SUNHOUSE-SHD1182-H%C3%A0ng-ch%C3%ADnh-h%C3%A3ng-b%E1%BA%A3o-h%C3%A0nh-12-th%C3%A1ng-%C4%90un-s%C3%B4i-t%E1%BB%AB-4-%C4%91%E1%BA%BFn-6-ph%C3%BAt-i.556587954.29313519647",
        "cdn_url": "",
        "local_path": "Product_Assets/29313519647/",
        "status": "Chưa chọn ảnh",
        "brand_fb": "Mua Chuẩn Xài Lâu",
        "brand_yt": "Mua Chuẩn Xài Lâu",
        "brand_ig": "Mua Chuẩn Xài Lâu",
        "brand_tt": "Mua Chuẩn Xài Lâu",
        "brand_shopee": "Mua Chuẩn Xài Lâu",
        "brand_zalo": "Mua Chuẩn Xài Lâu"
    },
    {
        "item_id": "29039440059",
        "title": "Nước Dưỡng Tóc Tinh Dầu Bưởi Cocoon 140ml Giảm Gãy Rụng Phục Hồi Tóc Mùa Thu Đông",
        "price": "145,0k",
        "sales_count": "85k+",
        "shop_name": "The Cocoon Original (Shopee Mall)",
        "commission_rate": "15%",
        "commission": "₫21.750",
        "product_url": "https://shopee.vn/N%C6%B0%E1%BB%9Bc-d%C6%B0%E1%BB%A1ng-t%C3%B3c-tinh-d%E1%BA%A7u-b%C6%B0%E1%BB%9Fi-The-Cocoon-140ml-i.695624425.29039440059",
        "shopee_link": "https://shopee.vn/N%C6%B0%E1%BB%9Bc-d%C6%B0%E1%BB%A1ng-t%C3%B3c-tinh-d%E1%BA%A7u-b%C6%B0%E1%BB%9Fi-The-Cocoon-140ml-i.695624425.29039440059",
        "cdn_url": "",
        "local_path": "Product_Assets/29039440059/",
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

print("Hoàn thành đồng bộ %d/%d sản phẩm vào Google Sheet." % (success_count, len(deals)))
