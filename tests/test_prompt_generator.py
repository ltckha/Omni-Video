import os
import sys
import json
import tempfile
import pytest

# Add scripts/ directory to sys.path
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from generate_ugc_prompt import lookup_product_name, select_character_for_product

class TestLookupProductName:
    def test_lookup_from_info_json_with_product_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            info_path = os.path.join(temp_dir, "info.json")
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump({"productName": "Giày Tây Nam Da Bò Cao Cấp", "price": "450.000đ"}, f)
            
            result = lookup_product_name("123456789", temp_dir)
            assert result == "Giày Tây Nam Da Bò Cao Cấp"

    def test_lookup_from_info_json_with_title_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            info_path = os.path.join(temp_dir, "info.json")
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump({"title": "Bọc Giày Đi Mưa Silicon Chống Trượt"}, f)
            
            result = lookup_product_name("987654321", temp_dir)
            assert result == "Bọc Giày Đi Mưa Silicon Chống Trượt"

    def test_lookup_default_fallback_when_no_info_and_no_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = lookup_product_name("non_existent_item_id_999999", temp_dir)
            assert result == "Sản phẩm Shopee"


class TestSelectCharacterForProduct:
    def test_select_male_character_for_male_product(self):
        male_titles = [
            "Giày lười nam công sở đế cao su êm chân",
            "Áo sơ mi nam Oxford tay dài lịch lãm",
            "Men leather wallet premium gift box",
            "Quần âu nam dáng slimfit cao cấp"
        ]
        for title in male_titles:
            char = select_character_for_product(title)
            assert "nam" in char.lower(), f"Failed for title: '{title}', got: '{char}'"

    def test_select_female_character_for_female_product(self):
        female_titles = [
            "Đầm xòe nữ vintage dáng dài mùa hè",
            "Váy hoa nhí nữ tiểu thư cổ vuông",
            "Giày cao gót nữ 7cm mũi nhọn đính đá"
        ]
        for title in female_titles:
            char = select_character_for_product(title)
            assert "nu" in char.lower(), f"Failed for title: '{title}', got: '{char}'"

    def test_select_female_character_for_unisex_or_general_product(self):
        unisex_titles = [
            "Bọc giày đi mưa silicon co giãn chống nước",
            "Bình giữ nhiệt inox 304 dung tích 800ml",
            "Dù che mưa gấp gọn tự động chống tia UV"
        ]
        for title in unisex_titles:
            char = select_character_for_product(title)
            assert "nu" in char.lower(), f"Failed for title: '{title}', got: '{char}'"

    def test_select_character_with_none_or_empty_string(self):
        char_empty = select_character_for_product("")
        assert char_empty in ["Nu-25t.png", "Nu-23t.png", "Nam-25t.png", "Friendly Reviewer"]

        char_none = select_character_for_product(None)
        assert char_none in ["Nu-25t.png", "Nu-23t.png", "Nam-25t.png", "Friendly Reviewer"]
