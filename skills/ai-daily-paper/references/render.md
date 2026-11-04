# L4 渲染层：合成、音频、质检

## 音频

1. `gen_voice.py --root <project>`，speed 0.95
2. **每句重置 seed 7**（脚本已内置）
3. 拼接时句间 0.3–0.45s 静音
4. 成片 loudnorm `I=-14:TP=-1.5:LRA=11`

## 渲染

```bash
cd ~/dsh-video-remotion/news-video
npx remotion render NewsVideoPaper    out/am.mp4 --codec=h264 --crf=18 --audio-codec=aac --audio-bitrate=192k
npx remotion render NewsVideoPaperPM  out/pm.mp4 --codec=h264 --crf=18 --audio-codec=aac --audio-bitrate=192k
```

## 拼完整版（正文 + 榜单页 + 片尾）

榜单页单独渲染后，按顺序 concat；段落用同一编码参数，避免时长翻倍：

```bash
ffmpeg -i A.mp4 -i board.mp4 -i C.mp4 \
 -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" \
 -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac -b:a 192k full.mp4
```

## 质检清单

- [ ] 页眉/页脚/进度条字号 ≥18，竖屏可读
- [ ] 标题不折行、不压图
- [ ] 进度条文字常驻且居中
- [ ] 引证卡无第三方网页导航/广告
- [ ] 榜单有来源 + 日期 + 口径
- [ ] 音量 -14 LUFS，无爆音
- [ ] 时长：早报 60–90s，晚报 90–120s
