# Validation record

Date: 2026-10-26. Tests ran on the current macOS host with Python3.10 and local FFmpeg. This record distinguishes executable verification from untested host/model behavior.

- 25 unit/integration tests passed: interval arithmetic, invalid/empty edits, Chinese phrase matching, repeated phrases, source fingerprints, real audio/video extraction, silence boundaries, native-rate spectral denoising, output preservation, source access errors, pre-download playlist rejection, three host installation targets and archive contents.
- The skill-creator `quick_validate.py` frontmatter/resource validation passed.
- A public Bilibili episode URL was downloaded, source seconds30–35 selected, HTDemucs-ft vocals separated, ZipEnhancer denoised, and WAV/M4A exported. Both exports decoded successfully and passed duration, finite-sample and peak checks.
- Local speech was transcribed with the cached Whisper `base.en` model, then an actual sentence was selected from that transcript and exported. Chinese phrase selection has automated tests; a fresh multilingual Whisper model was not downloaded for this validation.
- Generic HTTP media acquisition was tested through yt-dlp against a temporary local HTTP server serving a generated speech file, followed by extraction and trimming.
- `setup --component download` was run in a new isolated environment and completed. Existing local inference runtimes/models were reused for separation, denoising and transcription; fresh installation of every ML dependency on Windows/Linux has not been tested.
- A Python wheel was successfully built with the isolated build backend; worker code and requirement resources are included. The skill ZIP is the recommended end-user distribution.
- Claude Code, Codex and dsh installer targets were tested using temporary directories. Each resulting skill ran its CLI independently. Real natural-language invocation in three separate assistant sessions was not performed.

No subjective listening quality score is asserted by these checks. The models can retain overlapping speech, singing, reverb or effects. Neural denoising uses a16kHz mono model, so its output does not retain full-band stereo fidelity. The release archive excludes test audio, transcripts, model weights, credentials and virtual environments.

Host references: https://code.claude.com/docs/en/skills ; https://learn.chatgpt.com/docs/build-skills . DeepSeek Harness installation is based on its existing local `~/.dsh/skills/<name>/SKILL.md` layout.
