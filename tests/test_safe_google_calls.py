import glob
import os
import ssl
import sys

import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import omni_env


def test_ssl_context_verifies_certificates():
    ctx = omni_env.google_ssl_context()
    assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname is True


def test_gemini_key_goes_in_header():
    assert omni_env.gemini_headers("k123") == {"x-goog-api-key": "k123", "Content-Type": "application/json"}


def test_no_script_disables_ssl_or_puts_key_in_url():
    for path in glob.glob(os.path.join(SCRIPTS_DIR, "*.py")):
        src = open(path, encoding="utf-8").read()
        assert "CERT_NONE" not in src, path
        assert "check_hostname = False" not in src, path
        assert "?key=" not in src, path


@pytest.mark.skipif(not os.path.exists(os.path.join(PROJECT_DIR, "characters", "Nu-25t.png")), reason="ảnh nhân vật không có trong git")
def test_large_image_shrunk_for_ai_original_untouched(tmp_path):
    import shutil
    src = tmp_path / "big.png"
    shutil.copy(os.path.join(PROJECT_DIR, "characters", "Nu-25t.png"), src)  # 2752 px
    before = src.read_bytes()
    data, mime = omni_env.image_for_ai(str(src))
    assert mime == "image/jpeg" and data[:3] == b"\xff\xd8\xff" and len(data) < len(before)
    out = tmp_path / "ai.jpg"
    out.write_bytes(data)
    assert max(omni_env._image_size(str(out))) == 1600
    assert src.read_bytes() == before


def test_small_image_sent_as_is(tmp_path):
    import subprocess
    small = tmp_path / "s.png"
    subprocess.run(["sips", "-s", "format", "png", "-z", "100", "100",
                    os.path.join(PROJECT_DIR, "characters", "Nu-25t.png"), "--out", str(small)],
                   check=False, capture_output=True)
    if not small.exists():
        pytest.skip("không tạo được ảnh nhỏ")
    data, mime = omni_env.image_for_ai(str(small))
    assert data == small.read_bytes() and mime == "image/png"


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


class TestOmniKeyOrder:
    def test_prefers_omni_key_then_video_then_generic(self, monkeypatch):
        monkeypatch.setattr(omni_env, "read_env_file", lambda *a, **k: {})
        monkeypatch.setenv("GEMINI_OMNI_API_KEY", "k_omni")
        monkeypatch.setenv("GEMINI_VIDEO_API_KEY", "k_video")
        monkeypatch.setenv("GEMINI_API_KEY", "k_generic")
        assert omni_env.gemini_api_key() == "k_omni"
        monkeypatch.delenv("GEMINI_OMNI_API_KEY")
        assert omni_env.gemini_api_key() == "k_video"
        monkeypatch.delenv("GEMINI_VIDEO_API_KEY")
        assert omni_env.gemini_api_key() == "k_generic"
