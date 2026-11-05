#!/usr/bin/env bash
# 用法: x-card.sh <status-url-or-id> <out.png>
# 依赖: 有 playwright 的工程（PW_ROOT 指向其 node_modules）
set -euo pipefail
ARG="${1:?usage: x-card.sh <status-url|id> <out.png>}"
OUT="${2:?usage: x-card.sh <status-url|id> <out.png>}"
ID=$(echo "$ARG" | sed -n 's|.*status/\([0-9]\{5,\}\).*|\1|p')
[ -z "$ID" ] && ID="$ARG"
TOOLS="${X_CARD_TOOLS:-$HOME/dsh-video-remotion/news-video/tools/tweet-card.mjs}"
node "$TOOLS" "https://x.com/i/status/$ID" "$OUT"
