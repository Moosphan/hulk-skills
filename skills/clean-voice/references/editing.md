# 自然语言裁剪

自然语言由宿主助手解析；CLI 不内置第二个大模型。所有区间都落在原始音轨上，再统一裁剪，最后分离/降噪。这样先处理用户真正需要的片段，降低推理耗时。

## 时间裁剪

`--keep`、`--remove` 可重复，支持秒数、`MM:SS`、`HH:MM:SS`、小数秒，终点支持 `end`。区间越界、反向、无音频剩余会失败。保留区间按原时间排序并合并，不表达片段重排。删除区间不会导致后续时间坐标漂移。

例如“保留15秒到1分10秒，再删除30到35秒”：

```bash
python scripts/voice.py process --input "video.mp4" --output "result/clip" --mode clean --keep "15-01:10" --remove "30-35"
```

先检查剪辑计划可加 `--plan-only`：会读取/解码输入并写原音和报告，不运行模型，也不导出最终人声。实际执行使用另一个新输出目录。

## 按句子或内容裁剪

```bash
python scripts/voice.py transcribe --input "recording.m4a" --output "result/transcript" --language zh
```

读取 `transcript.json` 的 `text`、`segments`、`words`。转写有识别误差，标点并非精确切点。根据用户要保留的真实语义选择源区间，必要时留约60–150ms的语音边界。不要仅凭转写推断听感，重复内容不确定时让用户选择。

直接按已识别句子裁剪：

```bash
python scripts/voice.py process --input "recording.m4a" --output "result/sentence" --mode clean --transcript "result/transcript/transcript.json" --keep-text "今天我们介绍这个项目"
python scripts/voice.py process --input "recording.m4a" --output "result/remove-sentence" --mode extract --transcript "result/transcript/transcript.json" --remove-text "这句重新来" --occurrence 2
```

也可省略 `--transcript`，脚本会先自动转写。`--keep-text` / `--remove-text` 支持重复；按 NFKC 规范化并忽略空白、标点和大小写，匹配跨词的中英文内容。同一句重复出现时默认报错，`--occurrence` 为从1开始的出现次数，并同时作用于该命令的所有短语；复杂重复内容应改用明确时间区间。

“从某句开始，到另一句结束”“只保留解释原理的部分”“删除所有嗯啊”需要助手阅读转写后选择多个区间，再交给 `--keep` / `--remove`，不能用未经核对的关键词批量删除。`--transcript` 含有 `audio_sha256` 时会验证来源；换输入后应重新转写。

Whisper 默认 `small` 多语言模型；`--asr-model base`、`small` 或本地 `.pt` 路径可选。`.en` 模型只适合英文，不应用于中文内容。

## 静音压缩

`--remove-silence` 是音量阈值检测，不是语义 VAD。默认阈值 -40dB、持续0.6秒，保留语音两侧0.15秒。噪声较大时先去噪再用降噪成品作为新的输入，时间轴随之变为该新文件；不要继续套用旧源时间。人声较轻时阈值过高会误删，需按实际录音调整。

```bash
python scripts/voice.py process --input "voice.wav" --output "result/no-silence" --mode extract --remove-silence --silence-threshold -45 --silence-minimum 0.8 --silence-padding 0.2
```
