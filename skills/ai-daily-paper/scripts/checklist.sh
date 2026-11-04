#!/usr/bin/env bash
# 日报发布前自检
set -e
V="${1:?usage: checklist.sh <video.mp4>}"
echo "== 文件 =="; ls -lh "$V"
echo "== 时长 =="; ffprobe -v error -show_entries format=duration -of csv=p=0 "$V"
echo "== 响度 =="; ffmpeg -hide_banner -i "$V" -af loudnorm=print_format=summary -f null - 2>&1 | tail -8
echo "== 分辨率 =="; ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 "$V"
