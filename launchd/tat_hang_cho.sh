#!/bin/bash
# Tắt lịch hàng chờ hàng tiệm.
LABEL=vn.giayhainancy.omni.hangcho
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
echo "Đã tắt $LABEL."
