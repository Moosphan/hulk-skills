import hashlib
import importlib
import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / "录音 with spaces.wav"
        with wave.open(str(self.source), "wb") as target:
            target.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            target.writeframes(b"".join(struct.pack("<h", int(5000 * math.sin(2 * math.pi * 440 * index / 16000))) for index in range(64000)))

    def run_cli(self, *arguments):
        self.assertTrue((ROOT / "scripts/voice.py").is_file(), "shared CLI must exist")
        return subprocess.run([sys.executable, str(ROOT / "scripts/voice.py"), *map(str, arguments)], capture_output=True, text=True)

    def test_extract_cut_and_report_preserve_input(self):
        before = hashlib.sha256(self.source.read_bytes()).hexdigest()
        output = self.folder / "result"
        result = self.run_cli("process", "--input", self.source, "--output", output, "--mode", "extract", "--keep", "0-1", "--keep", "2-4", "--remove", "2.5-3", "--no-normalize")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((output / "report.json").read_text())
        self.assertAlmostEqual(report["output_duration"], 2.5, places=2)
        self.assertEqual(report["source_ranges"], [[0, 1], [2, 2.5], [3, 4]])
        self.assertTrue((output / "voice.m4a").is_file())
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), before)

    def test_video_input_extracts_audio(self):
        video = self.folder / "video.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=size=64x64:rate=10:duration=4", "-i", str(self.source), "-c:v", "mpeg4", "-c:a", "aac", "-shortest", str(video)], check=True)
        result = self.run_cli("process", "--input", video, "--output", self.folder / "video-result", "--mode", "extract")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_existing_output_is_never_overwritten(self):
        output = self.folder / "result"
        output.mkdir()
        marker = output / "keep.txt"
        marker.write_text("keep")
        result = self.run_cli("process", "--input", self.source, "--output", output, "--mode", "extract")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(), "keep")

    def test_invalid_ranges_do_not_produce_successful_export(self):
        output = self.folder / "bad"
        result = self.run_cli("process", "--input", self.source, "--output", output, "--mode", "extract", "--keep", "5-6")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((output / "voice.wav").exists())

    def test_text_edit_checks_source_fingerprint(self):
        output = self.folder / "text"
        transcript = self.folder / "transcript.json"
        transcript.write_text(json.dumps({"audio_sha256": "wrong", "words": [{"word": "hello", "start": 0.5, "end": 1.5}]}))
        result = self.run_cli("process", "--input", self.source, "--output", output, "--mode", "extract", "--transcript", transcript, "--keep-text", "hello")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fingerprint", result.stderr.lower())

    def test_missing_file_has_actionable_error(self):
        result = self.run_cli("process", "--input", self.folder / "missing.wav", "--output", self.folder / "missing", "--mode", "extract")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing", result.stderr.lower())

    def test_text_edit_exports_the_selected_sentence(self):
        output = self.folder / "text-valid"
        transcript = self.folder / "words.json"
        transcript.write_text(json.dumps({"words": [{"word": "你好，", "start": 0.5, "end": 1}, {"word": "世界", "start": 1, "end": 1.5}]}))
        result = self.run_cli("process", "--input", self.source, "--output", output, "--mode", "extract", "--transcript", transcript, "--keep-text", "你好世界", "--text-padding", "0")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((output / "report.json").read_text())
        self.assertAlmostEqual(report["output_duration"], 1, places=2)

    def test_spectral_denoise_preserves_native_sample_rate(self):
        source = self.folder / "48k.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(self.source), "-ar", "48000", str(source)], check=True)
        output = self.folder / "spectral"
        result = self.run_cli("process", "--input", source, "--output", output, "--mode", "denoise", "--denoiser", "spectral")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((output / "report.json").read_text())
        self.assertEqual(report["validation"]["voice.wav"]["sample_rate"], 48000)

    def test_silence_removal_preserves_non_silent_audio(self):
        silent = self.folder / "silence.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "1", str(silent)], check=True)
        combined = self.folder / "gaps.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(silent), "-i", str(self.source), "-filter_complex", "[0:a][1:a][0:a]concat=n=3:v=0:a=1", str(combined)], check=True)
        output = self.folder / "no-gaps"
        result = self.run_cli("process", "--input", combined, "--output", output, "--mode", "extract", "--remove-silence")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((output / "report.json").read_text())
        self.assertAlmostEqual(report["output_duration"], 4.3, delta=0.03)


class SourceTests(unittest.TestCase):
    def sources(self):
        self.assertTrue((ROOT / "clean_voice/sources.py").is_file(), "source adapter must exist")
        return importlib.import_module("clean_voice.sources")

    def test_public_bilibili_uses_best_audio(self):
        payload = {"code": 0, "result": {"is_drm": False, "is_preview": 0, "dash": {"audio": [{"bandwidth": 64, "baseUrl": "https://example.org/low"}, {"bandwidth": 256, "baseUrl": "https://example.org/high"}]}}}
        self.assertEqual(self.sources().bilibili_audio_url("https://www.bilibili.com/bangumi/play/ep250974", lambda url: payload), "https://example.org/high")

    def test_access_errors_and_drm_are_not_bypassed(self):
        adapter = self.sources()
        for payload in [{"code": -10403, "message": "region restricted"}, {"code": 0, "result": {"is_drm": True}}, {"code": 0, "result": {"is_preview": 1}}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                adapter.bilibili_audio_url("https://www.bilibili.com/bangumi/play/ep250974", lambda url: payload)


if __name__ == "__main__":
    unittest.main()
