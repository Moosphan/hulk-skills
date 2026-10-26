# Clean Voice

用自然语言从音视频文件或链接中提取人声、去背景音乐、清理录音噪声，并按时间、句子或内容裁剪。适配 **Claude Code、Codex、DeepSeek Harness（dsh）**，三端共用同一 `SKILL.md` 和处理核心。

自然语言由宿主助手理解，再调用本项目CLI；不需要另配一个LLM API。音频分离、降噪和转写在本机运行。模型效果依素材而异，重叠对白、唱声、混响或音效可能残留；不承诺从重叠说话声中完美单独提取某位旁白。

## 安装到助手

解压后在 `clean-voice` 目录执行其中一项：

```bash
python3 scripts/install.py --target claude
python3 scripts/install.py --target codex
python3 scripts/install.py --target dsh
```

Windows将 `python3` 换为 `py -3`。同时安装三端用 `--target all`；预览目标用 `--dry-run`。Claude默认 `~/.claude/skills/clean-voice`，Codex默认 `~/.agents/skills/clean-voice`（设置 `CODEX_HOME` 时为其下 `skills`），DeepSeek Harness默认 `~/.dsh/skills/clean-voice`。Codex旧版可通过 `--destination ~/.codex/skills` 显式安装。自定义路径传的是**skills父目录**，不是最终skill目录。安装后新开对话或刷新技能列表；版本不同会影响热加载。

每个安装目录都是完整、可独立运行的项目副本。默认不覆盖既有skill；`--replace` 会先将旧版移到同一skills父目录的 `.clean-voice-backups`，再替换。不改宿主配置文件、不写API密钥。

## 准备运行环境

Python3.10+与FFmpeg/ffprobe，新环境推荐Python3.11（新版yt-dlp已提示3.10弃用）。先进入项目或已安装skill目录：

```bash
python3 scripts/voice.py doctor
python3 scripts/voice.py setup --component all
```

只做提取/时间裁剪不需准备ML依赖。仅录音降噪可只准备 `denoise`，去伴奏只准备 `separation`，按句子编辑另需 `transcribe`，B站以外的链接下载另需 `download`。FFmpeg安装示例：macOS `brew install ffmpeg`；Windows `winget install Gyan.FFmpeg` 后重开终端；Debian/Ubuntu `sudo apt install ffmpeg python3-venv`。

模型和虚拟环境不在项目包内；首次准备需要联网和数GB空间。已有模型/环境可以复用，详见 [环境配置](references/setup.md)。

## 自然语言示例

- “帮我去掉这段录音的杂音，尽量保留原来的声音。”
- “提取这个B站链接的人声，不要背景音乐，导出WAV和能直接试听的文件。”
- “只保留视频15秒到1分10秒，再删除30到35秒。”
- “把开头5秒和最后10秒剪掉，然后去伴奏。”
- “先转写，只保留介绍项目原理的部分。”
- “删掉第二次说‘这句重新来’的那一句，其他内容保持顺序。”
- “压缩超过0.8秒的静音，但保留句子两侧的自然停顿。”

Claude Code可显式输入 `/clean-voice`，Codex可输入 `$clean-voice`；dsh可按其版本的技能选择入口加载，或自然语言请求。技能正文不绑定任何宿主专有工具名。dsh目录结构已依据本机DeepSeek Harness现有skill核对；三端安装目录与独立CLI经过测试，不等于已在三个模型会话中逐个实测自然语言触发。

## 直接使用 CLI

```bash
python3 scripts/voice.py process --input "录音.m4a" --output "result/clean-recording" --mode denoise
python3 scripts/voice.py process --input "https://www.bilibili.com/bangumi/play/ep250974" --output "result/narration" --mode clean
python3 scripts/voice.py process --input "video.mp4" --output "result/cut" --mode extract --keep "15-01:10" --remove "30-35"
python3 scripts/voice.py transcribe --input "recording.wav" --output "result/transcript" --language zh
python3 scripts/voice.py process --input "recording.wav" --output "result/sentence" --mode clean --transcript "result/transcript/transcript.json" --keep-text "今天我们介绍这个项目"
```

| 模式 | 用途 |
| --- | --- |
| `clean` | 去伴奏 + 神经语音降噪 |
| `separate` | 仅分离人声，保留44.1kHz立体声输出 |
| `denoise` | 清理录音噪声，不先做伴奏分离 |
| `extract` | 只提取音轨/裁剪，不做神经处理 |

`--denoiser spectral` 提供轻量FFmpeg降噪；不会静默替代神经降噪。`--no-normalize`保留当前处理阶段音量。默认两遍响度归一目标-18LUFS、真峰值-1.5dB，WAV为24bit；`clean`神经降噪受16kHz模型带宽限制。输出始终为新目录，不能覆盖原文件或已有成品。

### 输出

`voice.m4a`试听，`voice.wav`剪辑，`original.wav`完整原音轨，`report.json`包含原时间区间、处理模式、导出位置、时长、解码与峰值检查；`work/`保留中间文件便于复查。成功时stdout给结构化JSON，过程进度发到stderr。只有全部导出验证通过，报告才会标记 `complete`。

按内容剪辑需先参考 [裁剪规则](references/editing.md)。支持来源与访问限制见 [来源说明](references/sources.md)。

## 开发与打包

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package.py --output "../clean-voice.zip"
```

测试使用临时目录和合成媒体，不修改用户原始录音。完整发行ZIP包含skill、源码、文档和测试；不包含模型、凭证、用户音频或虚拟环境。可选 `pip install -e .` 获得 `clean-voice` 命令，普通skill用法无需pip安装项目本体。

项目结构：`clean_voice/`处理核心和隔离worker，`scripts/`宿主可直接调用的入口与安装打包，`references/`按需指导，`agents/openai.yaml`为Codex界面元数据。

## License

本项目采用 [MIT License](LICENSE)。第三方工具与模型遵循各自许可证，详见 [第三方说明](THIRD-PARTY.md)。
