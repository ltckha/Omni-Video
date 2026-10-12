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

from generate_ugc_prompt import lookup_product_name, select_character_for_product, is_footwear_product, is_valid_prompt_structure
from archive_completed_videos import find_video_for_item

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


class TestIsFootwearProduct:
    def test_detects_footwear_keywords(self):
        footwear_samples = [
            "Giày Tây Nam Da Bò Cao Cấp",
            "Bọc Giày Đi Mưa Silicon Chống Trượt",
            "Dép quai ngang nữ đế êm chống trơn",
            "Ủng đi mưa cổ cao chống nước",
            "Tất vớ cổ ngắn kháng khuẩn khử mùi",
            "Men running sneakers breathable lightweight",
            "Women leather boots high ankle"
        ]
        for name in footwear_samples:
            assert is_footwear_product(name) is True, f"Failed to detect footwear in '{name}'"

    def test_non_footwear_products_return_false(self):
        non_footwear_samples = [
            "Sữa Chống Nắng Vô Cơ Sen Hậu Giang - Tone up Pink Cocoon 50ml",
            "Đai Chống Gù Lưng Rung Cảm Biến Điện Tử Thông Minh",
            "Lồng đèn con thỏ hottrend chơi trung thu",
            "Hộp cơm cắm điện cao cấp inox 2 tầng",
            "Ruốc nấm hương chay ngon thượng hạng",
            "Bình giữ nhiệt Lock&Lock 500ml",
            "Áo thun cotton form rộng unisex"
        ]
        for name in non_footwear_samples:
            assert is_footwear_product(name) is False, f"Incorrectly marked non-footwear as footwear: '{name}'"

    def test_footwear_accessories_and_devices_return_false(self):
        accessories_samples = [
            "Máy Sấy Giày Dép Khử Khuẩn UV Thông Minh Hẹn Giờ",
            "Túi Đựng Giày Dép Du Lịch 3 Ngăn Chống Thấm Nước XIMO TDG04",
            "Kệ để giày dép 5 tầng khung inox gấp gọn",
            "Chai xịt vệ sinh bọt tuyết làm sạch giày da Sneaker",
            "Hộp đựng giày dép trong suốt nắp hút nam châm",
            "Xi đánh giày đen bóng cao cấp Kiwi",
            "Bàn chải cọ giày chuyên dụng lông mềm",
            "Xịt khử mùi giày dép quế bạc hà 100ml",
            "Dây giày dẹt co giãn thông minh không cần buộc",
            "Miếng lót giày thể thao êm chân giảm chấn"
        ]
        for name in accessories_samples:
            assert is_footwear_product(name) is False, f"Incorrectly marked accessory/device as wearable footwear: '{name}'"

    def test_empty_or_none_returns_false(self):
        assert is_footwear_product("") is False
        assert is_footwear_product(None) is False


class TestFindVideoForItem:
    def test_finds_video_in_local_item_dir(self, monkeypatch):
        with tempfile.TemporaryDirectory() as temp_dir:
            item_path = os.path.join(temp_dir, "123456")
            os.makedirs(item_path, exist_ok=True)
            dummy_mp4 = os.path.join(item_path, "sample_video.mp4")
            with open(dummy_mp4, "w") as f:
                f.write("dummy")

            path, is_dl = find_video_for_item("123456", item_path)
            assert path == dummy_mp4
            assert is_dl is False

    def test_finds_video_in_downloads_dir(self, monkeypatch):
        with tempfile.TemporaryDirectory() as temp_assets:
            with tempfile.TemporaryDirectory() as temp_downloads:
                import archive_completed_videos
                monkeypatch.setattr(archive_completed_videos, "DOWNLOADS_DIR", temp_downloads)

                item_path = os.path.join(temp_assets, "998877")
                os.makedirs(item_path, exist_ok=True)

                dl_mp4 = os.path.join(temp_downloads, "998877.mp4")
                with open(dl_mp4, "w") as f:
                    f.write("dummy")

                path, is_dl = find_video_for_item("998877", item_path)
                assert path == dl_mp4
                assert is_dl is True

    def test_returns_none_when_no_video_exists(self, monkeypatch):
        with tempfile.TemporaryDirectory() as temp_assets:
            with tempfile.TemporaryDirectory() as temp_downloads:
                import archive_completed_videos
                monkeypatch.setattr(archive_completed_videos, "DOWNLOADS_DIR", temp_downloads)

                item_path = os.path.join(temp_assets, "000111")
                os.makedirs(item_path, exist_ok=True)

                path, is_dl = find_video_for_item("000111", item_path)
                assert path is None
                assert is_dl is False


class TestIsValidPromptStructure:
    def test_valid_full_prompt(self):
        valid_prompt = """[ASSETS]:
- Product: Attached image
- Character: Attached image (Lock facial identity, Voice: Nu-25t)

[PROMPT]:
- Visual: A dynamic tracking shot of the host reviewing the product in an office.
- Voiceover (Vietnamese): "Món này tiện lợi cực kỳ luôn mọi người ơi!"

[CONSTRAINTS]:
- 9:16 vertical, 10s, photorealistic UGC, 60fps, clean footage.
- No text on screen."""
        assert is_valid_prompt_structure(valid_prompt) is True

    def test_valid_product_centric_prompt(self):
        product_centric_prompt = """[ASSETS]:
- Product (Primary Subject - Input Image 1): Portable UV shoe dryer with purple LED air vents. Must maintain 100% visual fidelity to Input Image 1.
- Character / Presenter (Secondary Subject - Input Image 2): Nu-25t.png (Lock facial identity & voice, Voice: Nu-25t) acting as the product reviewer.

[PROMPT]:
- Visual: A crisp, center-framed close-up of the attached portable UV shoe dryer (Input Image 1) held prominently at chest level occupying 45% of the vertical 9:16 frame, with the presenter softly visible in the background speaking with natural Vietnamese lip-sync.
- Voiceover (Vietnamese): "Mùa mưa này giày ướt chỉ cần cắm máy này 10 phút là khô ráo thơm tho liền nha mọi người!"

[CONSTRAINTS]:
- 9:16 vertical, 10s, photorealistic UGC, 60fps, clean footage with zero text/subtitles/typography/watermarks/logos.
- Accurate on-camera Vietnamese lip-sync matching the spoken voiceover; natural mouth movement and expressive facial gestures.
- No mid-frame object vanishing or morphing."""
        assert is_valid_prompt_structure(product_centric_prompt) is True

    def test_valid_warehouse_gift_prompt(self):
        warehouse_gift_prompt = """[ASSETS]:
- Product (Primary Subject - Input Image 1): Electric fabric shaver with white ergonomic handle and honeycomb mesh. Must maintain 100% visual fidelity to Input Image 1.
- Character / Recipient (Secondary Subject - Input Image 2): Nu-25t.png (Lock facial identity & voice, stylish office outfit, Voice: Nu-25t) acting as the grateful recipient.

[PROMPT]:
- Visual: A single continuous medium close-up where a hand presents the electric fabric shaver (Input Image 1) into frame, and Nu-25t smoothly receives and cradles it at chest level occupying 45% frame, speaking directly with heartfelt Vietnamese lip-sync against a subtle background with stacked cartons.
- Voiceover (Vietnamese): "Trời ơi, món quà này bạn tặng là thứ mình trân quý nhất lúc này luôn, cảm ơn bạn nhiều lắm nha!"

[CONSTRAINTS]:
- 9:16 vertical, 10s, photorealistic UGC, 60fps, clean footage with zero text/subtitles/typography/watermarks/logos.
- Accurate on-camera Vietnamese lip-sync matching the spoken voiceover; natural mouth movement and expressive facial gestures.
- No mid-frame object vanishing or morphing."""
        assert is_valid_prompt_structure(warehouse_gift_prompt) is True

    def test_truncated_prompt_fails(self):
        truncated = "[ASSETS]:\n- Product: Attached image\n- Character: Attached image ("
        assert is_valid_prompt_structure(truncated) is False

    def test_missing_constraints_fails(self):
        missing_constraints = """[ASSETS]:
- Product: Attached image
- Character: Attached image

[PROMPT]:
- Visual: A dynamic tracking shot.
- Voiceover (Vietnamese): "Hello everyone! This is a test." """
        assert is_valid_prompt_structure(missing_constraints) is False

    def test_empty_or_short_prompt_fails(self):
        assert is_valid_prompt_structure("") is False
        assert is_valid_prompt_structure(None) is False
        assert is_valid_prompt_structure("too short") is False


class TestSelectStoryAngle:
    def test_select_gift_story_angle_for_gift_keywords(self):
        from generate_ugc_prompt import select_story_angle
        angle_name, angle_desc = select_story_angle("Set quà tặng 20/10 cho bạn gái")
        assert "SURPRISE GIFT" in angle_name or len(angle_name) > 0

    def test_select_general_story_angle(self):
        from generate_ugc_prompt import select_story_angle
        angle_name, angle_desc = select_story_angle("Bọc giày đi mưa silicon chống trượt")
        assert len(angle_name) > 0
        assert len(angle_desc) > 0


class TestAntiRepetitionAndNoStaticExamples:
    def test_get_recent_voiceovers(self, monkeypatch):
        from generate_ugc_prompt import get_recent_voiceovers
        with tempfile.TemporaryDirectory() as temp_assets:
            import generate_ugc_prompt
            monkeypatch.setattr(generate_ugc_prompt, "ASSETS_DIR", temp_assets)

            item1 = os.path.join(temp_assets, "111")
            os.makedirs(item1, exist_ok=True)
            with open(os.path.join(item1, "111.txt"), "w", encoding="utf-8") as f:
                f.write('[PROMPT]:\n- Voiceover (Vietnamese): "Hương sen Hậu Giang thơm mát mê quá!"\n')

            item2 = os.path.join(temp_assets, "222")
            os.makedirs(item2, exist_ok=True)
            with open(os.path.join(item2, "222.txt"), "w", encoding="utf-8") as f:
                f.write('[PROMPT]:\n- Voiceover (Vietnamese): "Màu son bùn nhung mịn lên môi cực xinh!"\n')

            vos = get_recent_voiceovers(limit=5)
            assert len(vos) == 2
            assert "Hương sen Hậu Giang thơm mát mê quá!" in vos
            assert "Màu son bùn nhung mịn lên môi cực xinh!" in vos

    def test_no_static_dialogue_examples_in_script_source(self):
        """Ensure no static dialogue examples exist in prompt directives."""
        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "generate_ugc_prompt.py")
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Ensure the old repetitive sentence is completely gone
        assert "Trời ơi, món quà này bạn tặng là thứ mình trân quý nhất" not in content
        assert "Món này tiện lợi cực kỳ luôn mọi người ơi" not in content




def test_gemini_model_chain_order():
    """3.8 -> 3.6 -> 3.7 -> lite -> 2.5; no gemini-3.5-flash (counted against 3.6 quota), no -preview."""
    import generate_ugc_prompt
    assert generate_ugc_prompt.PREFERRED_MODELS == [
        "gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash",
    ]
    qa_src = open(os.path.join(SCRIPTS_DIR, "video_qa_analyzer.py"), encoding="utf-8").read()
    assert '["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-2.5-flash"]' in qa_src
    for src in (qa_src, open(os.path.join(SCRIPTS_DIR, "generate_ugc_prompt.py"), encoding="utf-8").read()):
        assert '"gemini-3.5-flash"' not in src
        assert "-preview" not in src
