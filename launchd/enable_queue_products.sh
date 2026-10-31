#!/bin/bash
# Bật lịch hàng chờ hàng tiệm (vn.giayhainancy.omni.hangcho, 13:30 hằng ngày).
set -e
LABEL=vn.giayhainancy.omni.hangcho
DST="$HOME/Library/LaunchAgents/$LABEL.plist"
mkdir -p "$(dirname "$0")/../data/logs"
cp "$(dirname "$0")/$LABEL.plist" "$DST"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$DST"
echo "Đã bật $LABEL (13:30 hằng ngày)."
