#!/bin/bash
# 用法: bash x-video.sh <video.twimg.com 链接> <开始秒> <时长秒> <输出路径>
# 说明: 截无声片段，避免压掉旁白
set -e
URL="$1"; SS="${2:-0}"; T="${3:-10}"; OUT="${4:-clip.mp4}"
curl -sL --max-time 180 -A "Mozilla/5.0" "$URL" -o /tmp/x-raw.mp4
ffmpeg -y -v error -ss "$SS" -t "$T" -i /tmp/x-raw.mp4 -an -vf "scale=1280:-2" -c:v libx264 -crf 22 -preset veryfast "$OUT"
echo "ok $OUT"
