# Third-party dependencies and model sources

This project invokes separately installed tools and downloads weights only when setup is requested. The distribution does not bundle their code, weights, user audio or login credentials. Refer to each upstream license/model card before redistribution or commercial deployment.

| Component | Purpose | Upstream |
| --- | --- | --- |
| FFmpeg | Decode, trim, concatenate, normalize, encode | https://ffmpeg.org/legal.html |
| Demucs | Speech/vocals separation | https://github.com/facebookresearch/demucs |
| HTDemucs-ft safetensors | Fine-tuned vocals checkpoint | https://huggingface.co/adefossez/HTDemucs-ft |
| ModelScope ZipEnhancer | Acoustic noise suppression | https://modelscope.cn/models/iic/speech_zipenhancer_ans_multiloss_16k_base |
| ModelScope | Local inference and model download | https://github.com/modelscope/modelscope |
| Whisper | Local speech transcription with word timestamps | https://github.com/openai/whisper |
| yt-dlp | Supported-site media acquisition | https://github.com/yt-dlp/yt-dlp |
| PyTorch, NumPy, soundfile, safetensors | Local model runtime and audio arrays | https://pytorch.org/ ; https://numpy.org/ ; https://python-soundfile.readthedocs.io/ ; https://github.com/huggingface/safetensors |

Only process sources the user may access. Network access to the public Bilibili APIs is not a guarantee that arbitrary paid, region-restricted or DRM content can be acquired.
