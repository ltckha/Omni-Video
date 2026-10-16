import os
import sys
import tempfile
import base64
import pytest

# Add scripts/ directory to sys.path
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from generate_omni_video import (
    get_omni_api_key,
    verify_security_pin,
    get_image_mime_type,
    find_prompt_file,
    find_product_image,
    find_character_image,
    build_omni_payload,
    extract_video_data_from_response
)

class TestOmniApiKeyResolution:
    @pytest.fixture(autouse=True)
    def no_env_file(self, monkeypatch):
        import omni_env
        monkeypatch.setattr(omni_env, "read_env_file", lambda *a, **k: {})

    def test_prefers_gemini_omni_api_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_OMNI_API_KEY", "key_omni_123")
        monkeypatch.setenv("GEMINI_VIDEO_API_KEY", "key_video_456")
        monkeypatch.setenv("GEMINI_API_KEY", "key_default_789")
        assert get_omni_api_key() == "key_omni_123"

    def test_falls_back_to_gemini_video_api_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_OMNI_API_KEY", raising=False)
        monkeypatch.setenv("GEMINI_VIDEO_API_KEY", "key_video_456")
        monkeypatch.setenv("GEMINI_API_KEY", "key_default_789")
        assert get_omni_api_key() == "key_video_456"

    def test_falls_back_to_default_gemini_api_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_OMNI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_VIDEO_API_KEY", raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "key_default_789")
        assert get_omni_api_key() == "key_default_789"


class TestImageMimeType:
    def test_mime_types(self):
        assert get_image_mime_type("image.webp") == "image/webp"
        assert get_image_mime_type("photo.jpeg") == "image/jpeg"
        assert get_image_mime_type("photo.jpg") == "image/jpeg"
        assert get_image_mime_type("avatar.png") == "image/png"
        assert get_image_mime_type("unknown.xyz") == "image/jpeg"


class TestFileDiscovery:
    def test_find_prompt_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            std_prompt = os.path.join(temp_dir, "12345.txt")
            with open(std_prompt, "w") as f:
                f.write("test prompt")
            assert find_prompt_file(temp_dir, "12345") == std_prompt

    def test_find_prompt_file_legacy_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            legacy_prompt = os.path.join(temp_dir, "master_prompt.txt")
            with open(legacy_prompt, "w") as f:
                f.write("legacy prompt")
            assert find_prompt_file(temp_dir, "99999") == legacy_prompt

    def test_find_product_image_ignores_character(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            char_img = os.path.join(temp_dir, "Nu-25t.png")
            prod_img = os.path.join(temp_dir, "12345_1789.webp")
            with open(char_img, "w") as f:
                f.write("char")
            with open(prod_img, "w") as f:
                f.write("prod")

            assert find_product_image(temp_dir) == prod_img
            assert find_character_image(temp_dir) == char_img


class TestBuildOmniPayload:
    def test_build_payload_structure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prod_path = os.path.join(temp_dir, "product.webp")
            with open(prod_path, "wb") as f:
                f.write(b"fake_image_bytes")

            payload = build_omni_payload(
                prompt_text="A cinematic UGC video",
                product_image_path=prod_path,
                aspect_ratio="9:16",
                resolution="720p"
            )

            assert payload["model"] == "gemini-omni-1.1-flash"
            assert payload["response_format"]["aspect_ratio"] == "9:16"
            assert payload["response_format"]["resolution"] == "720p"
            assert isinstance(payload["input"], list)
            assert len(payload["input"]) == 2  # 1 image + 1 text
            assert payload["input"][0]["type"] == "image"
            assert payload["input"][1]["type"] == "text"
            assert payload["input"][1]["text"] == "A cinematic UGC video"


class TestExtractVideoData:
    def test_extract_from_output_video_field(self):
        dummy_mp4 = b"fake_mp4_content"
        b64_video = base64.b64encode(dummy_mp4).decode("utf-8")
        resp = {"output_video": {"data": b64_video}}

        data = extract_video_data_from_response(resp)
        assert data == dummy_mp4

    def test_extract_from_steps_array(self):
        dummy_mp4 = b"fake_mp4_from_steps"
        b64_video = base64.b64encode(dummy_mp4).decode("utf-8")
        resp = {
            "steps": [
                {"type": "user_input", "content": [{"type": "text", "text": "foo"}]},
                {
                    "type": "model_output",
                    "content": [
                        {"type": "video", "data": b64_video, "mime_type": "video/mp4"}
                    ]
                }
            ]
        }

        data = extract_video_data_from_response(resp)
        assert data == dummy_mp4

    def test_returns_none_when_no_video(self):
        resp = {"steps": [{"type": "model_output", "content": [{"type": "text", "text": "hello"}]}]}
        assert extract_video_data_from_response(resp) is None


class TestVerifySecurityPin:
    def test_pin_not_set_allows_execution(self, monkeypatch):
        monkeypatch.delenv("OMNI_SECURITY_PIN", raising=False)
        monkeypatch.delenv("OMNI_PIN", raising=False)
        monkeypatch.delenv("OMNI_BYPASS_PIN", raising=False)
        assert verify_security_pin() is True

    def test_bypass_flag_allows_execution(self, monkeypatch):
        monkeypatch.setenv("OMNI_SECURITY_PIN", "9999")
        monkeypatch.setenv("OMNI_BYPASS_PIN", "1")
        assert verify_security_pin() is True

    def test_correct_pin_succeeds(self, monkeypatch):
        monkeypatch.setenv("OMNI_SECURITY_PIN", "8888")
        monkeypatch.delenv("OMNI_BYPASS_PIN", raising=False)
        monkeypatch.setattr("builtins.input", lambda prompt="": "8888")
        monkeypatch.setattr("getpass.getpass", lambda prompt="": "8888")
        assert verify_security_pin() is True

    def test_incorrect_pin_fails(self, monkeypatch):
        monkeypatch.setenv("OMNI_SECURITY_PIN", "8888")
        monkeypatch.delenv("OMNI_BYPASS_PIN", raising=False)
        monkeypatch.setattr("builtins.input", lambda prompt="": "0000")
        monkeypatch.setattr("getpass.getpass", lambda prompt="": "0000")
        assert verify_security_pin(max_attempts=1) is False


class TestOmniEnvFileWins:
    """.env của Omni thắng ~/.zshrc (khoá chung các repo) — anh Kha chốt 16/10/2026."""

    def test_env_file_omni_key_beats_shell_key(self, monkeypatch):
        import omni_env
        monkeypatch.setenv("GEMINI_API_KEY", "shared_zshrc_key")
        monkeypatch.delenv("GEMINI_OMNI_API_KEY", raising=False)
        assert omni_env.gemini_api_key({"GEMINI_OMNI_API_KEY": "omni_file_key", "GEMINI_API_KEY": "x"}) == "omni_file_key"

    def test_env_file_generic_key_beats_shell_key(self, monkeypatch):
        import omni_env
        monkeypatch.setenv("GEMINI_OMNI_API_KEY", "shell_omni")
        assert omni_env.gemini_api_key({"GEMINI_API_KEY": "file_generic"}) == "file_generic"

    def test_falls_back_to_shell_when_env_file_empty(self, monkeypatch):
        import omni_env
        monkeypatch.delenv("GEMINI_OMNI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_VIDEO_API_KEY", raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "shell_key")
        assert omni_env.gemini_api_key({}) == "shell_key"

    def test_read_env_file_parses_export_and_quotes(self, tmp_path):
        import omni_env
        f = tmp_path / ".env"
        f.write_text('# c\nexport GEMINI_OMNI_API_KEY="abc"\nGEMINI_API_KEY=\nX=1\n', encoding="utf-8")
        assert omni_env.read_env_file(str(f)) == {"GEMINI_OMNI_API_KEY": "abc", "X": "1"}
