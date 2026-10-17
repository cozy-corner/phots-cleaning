#!/bin/bash
# Register the monthly job with launchd. Safe to re-run (also reloads after editing the plist).
set -euo pipefail

label=local.phots-cleaning
src="$(cd "$(dirname "$0")/.." && pwd)/launchd/$label.plist"
dst="$HOME/Library/LaunchAgents/$label.plist"
domain="gui/$(id -u)"

launchctl bootout "$domain/$label" 2>/dev/null || true
ln -sf "$src" "$dst"
launchctl bootstrap "$domain" "$dst"
launchctl print "$domain/$label" | grep -E '^\s*(path|state) ='
