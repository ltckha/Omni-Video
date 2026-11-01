import os
import sys

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from rank_offers import read_offers, rank_offers


def test_reads_shopee_offer_csv_and_ranks(tmp_path):
    f = tmp_path / "offer.csv"
    f.write_text("﻿Mã sản phẩm,Tên sản phẩm,Giá,Doanh thu,Tên cửa hàng,Tỉ lệ hoa hồng,Hoa hồng,Link sản phẩm,Link ưu đãi\n"
                 "1,Ủng A,\"6,0k\",3k+,Shop A,7%,₫420,https://shopee.vn/product/9/1,https://s.shopee.vn/a\n"
                 "2,Dép B,\"190,0k\",20k+,Shop B,19%,₫36.100,https://shopee.vn/product/9/2,\n"
                 "2,Dép B trùng,,,,,,,\n"
                 "3,Không số,,,,,,,\n", encoding="utf-8")
    offers = read_offers(str(f))
    assert offers[0]["job_id"] == "1" and offers[0]["commission"] == "₫420" and offers[0]["sales_count"] == "3k+"
    ranked = rank_offers(offers, existing_ids={"1"})
    assert [r["job_id"] for r in ranked] == ["2", "1", "3"]
    assert ranked[0]["score"] == 36100 * 20000 and ranked[1]["in_omni"] is True and ranked[2]["score"] is None
