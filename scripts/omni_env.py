# -*- coding: utf-8 -*-
"""Chọn khoá Gemini cho Omni (anh Kha chốt 16/10/2026: mỗi dự án 1 khoá riêng).
Thứ tự: .env của Omni thắng biến môi trường (~/.zshrc có khoá chung của repo khác);
trong mỗi nguồn ưu tiên GEMINI_OMNI_API_KEY rồi mới GEMINI_API_KEY."""

import os
from typing import Dict

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KEY_ORDER = ("GEMINI_OMNI_API_KEY", "GEMINI_VIDEO_API_KEY", "GEMINI_API_KEY")


def read_env_file(path: str = os.path.join(PROJECT_DIR, ".env")) -> Dict[str, str]:
    values = {}
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.replace("export", "").strip()
                val = val.strip().strip('"').strip("'")
                if val:
                    values[key] = val
    except OSError:
        pass
    return values


def gemini_api_key(env_file_values: Dict[str, str] = None) -> str:
    file_values = read_env_file() if env_file_values is None else env_file_values
    for source in (file_values, os.environ):
        for name in KEY_ORDER:
            if (source.get(name) or "").strip():
                return source[name].strip()
    return ""


# ===== Gọi Google an toàn (anh Kha "sửa đi" 18/10/2026) =====
import ssl
import subprocess
import tempfile

AI_IMAGE_MAX_SIDE = 1600   # ảnh gửi Gemini: cạnh dài tối đa (px), giống web Yen
AI_IMAGE_QUALITY = 85      # JPEG


def google_ssl_context() -> ssl.SSLContext:
    """Kiểm chứng chỉ SSL đầy đủ. Python.org trên Mac chưa có kho chứng chỉ hệ thống -> dùng certifi (có sẵn trong venv)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def gemini_headers(api_key: str = None, content_type: str = "application/json") -> Dict[str, str]:
    """Khoá Gemini đi trong header x-goog-api-key, không nằm trong URL (tránh lộ qua log / lịch sử)."""
    headers = {"x-goog-api-key": api_key if api_key is not None else gemini_api_key()}
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _image_size(path: str):
    try:
        out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                             check=True, capture_output=True, text=True).stdout
        w = int(out.split("pixelWidth:")[1].split()[0])
        h = int(out.split("pixelHeight:")[1].split()[0])
        return w, h
    except Exception:
        return None


def image_for_ai(path: str, max_side: int = AI_IMAGE_MAX_SIDE, quality: int = AI_IMAGE_QUALITY):
    """(bytes, mime) của ảnh gửi Gemini: cạnh dài > max_side thì thu về max_side, JPEG chất lượng `quality` (sips của macOS).
    File gốc giữ nguyên. Không đọc được kích thước / sips lỗi thì gửi file gốc."""
    with open(path, "rb") as f:
        original = f.read()
    ext = os.path.splitext(path)[1].lower()
    mime = {".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    size = _image_size(path)
    if not size or max(size) <= max_side:
        return original, mime
    try:
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "ai.jpg")
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality), "-Z", str(max_side), path, "--out", out],
                           check=True, capture_output=True)
            with open(out, "rb") as f:
                return f.read(), "image/jpeg"
    except Exception:
        return original, mime
