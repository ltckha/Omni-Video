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
