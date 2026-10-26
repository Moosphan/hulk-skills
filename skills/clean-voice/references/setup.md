# 安装与运行

Python 3.10+，建议3.10或3.11；FFmpeg 与 ffprobe 必须在 PATH。Windows `py -3`、macOS/Linux `python3` 都可启动脚本。CLI本体仅依赖标准库，提取和时间裁剪不需安装神经模型。

```bash
python scripts/voice.py doctor
python scripts/voice.py setup --component separation
python scripts/voice.py setup --component denoise
python scripts/voice.py setup --component transcribe
python scripts/voice.py setup --component download
```

`setup --component all` 一次准备全部。每类依赖在独立 venv 内，避免 Demucs 与 ModelScope 互相影响。默认位于 `~/.cache/clean-voice`，`--cache-dir` 或 `CLEAN_VOICE_CACHE` 可修改。依赖版本见 `clean_voice/requirements/`；机器和 Python 版本影响可安装的 Torch wheel。安装失败应保留 pip 的具体错误，而非修改宿主应用依赖。

人声分离用 HTDemucs-ft 的 vocals 专用 checkpoint，约84MB，默认复用标准 Hugging Face 缓存中的同一权重；无缓存时 setup 下载。语音降噪用 ModelScope ZipEnhancer，权重约8.5MB。Python/Torch等运行时通常需要数GB空间。Whisper首次使用默认small模型还需约0.5GB网络下载，可以指定已有本地 `.pt` 文件。发行包不包含权重、虚拟环境或用户音频。

## 复用现有环境

以下参数接在 `doctor`、`process`、`transcribe` 或 `setup` 子命令之后：

- `--separation-python` / `CLEAN_VOICE_SEPARATION_PYTHON`
- `--denoise-python` / `CLEAN_VOICE_DENOISE_PYTHON`
- `--transcribe-python` / `CLEAN_VOICE_TRANSCRIBE_PYTHON`
- `--download-python` / `CLEAN_VOICE_DOWNLOAD_PYTHON`
- `--separation-model` / `CLEAN_VOICE_SEPARATION_MODEL`：`04573f0d.safetensors` 文件
- `--denoise-model` / `CLEAN_VOICE_DENOISE_MODEL`：含 `configuration.json` 与 `pytorch_model.bin` 的目录

显式 Python 路径优先，其次自管 venv，再次当前Python（仅在必需模块存在时）。显式模型不存在会报错。`doctor` 报告实际解析结果，`not installed` 不能当作可用。

当前推理固定CPU，默认4线程，可用 `--threads` 调整；避免部分 Apple MPS 算子限制导致失败。对长素材先按需求裁剪。分离会将选择后的音频载入内存，超长录音应按自然章节分批处理。ZipEnhancer以2秒窗、0.5秒重叠加权拼接，保留最后不足一窗的尾音，并逐窗输出真实进度。

`clean` / 神经 `denoise` 导出16kHz单声道人声（模型有效带宽限制）；M4A重采样到44.1kHz不增加细节。要保留更完整的高频和立体声可选 `separate`，或将分离文件作为对照试听。不要把升采样宣传为恢复原始音质。
