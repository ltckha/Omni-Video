#!/bin/bash
# Script tự suy ra vị trí của nó nên KHÔNG cần sửa tay path khi clone dự án về máy khác
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 "$SCRIPT_DIR/omni_native_host.py"
