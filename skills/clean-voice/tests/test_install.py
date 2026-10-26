import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def test_each_host_gets_a_self_contained_skill(self):
        self.assertTrue((ROOT / "scripts/install.py").is_file(), "portable installer must exist")
        with tempfile.TemporaryDirectory() as temporary:
            for host in ["claude", "codex", "dsh"]:
                destination = Path(temporary) / host
                result = subprocess.run([sys.executable, str(ROOT / "scripts/install.py"), "--target", host, "--destination", str(destination)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                installed = destination / "clean-voice"
                self.assertTrue((installed / "SKILL.md").is_file())
                invocation = subprocess.run([sys.executable, str(installed / "scripts/voice.py"), "--version"], capture_output=True, text=True)
                self.assertEqual(invocation.returncode, 0, invocation.stderr)
                self.assertEqual(invocation.stdout.strip(), "0.1.0")
                repeated = subprocess.run([sys.executable, str(ROOT / "scripts/install.py"), "--target", host, "--destination", str(destination)], capture_output=True, text=True)
                self.assertNotEqual(repeated.returncode, 0)

    def test_package_contains_no_user_audio_or_model_weights(self):
        self.assertTrue((ROOT / "scripts/package.py").is_file(), "packager must exist")
        import zipfile
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "clean-voice.zip"
            result = subprocess.run([sys.executable, str(ROOT / "scripts/package.py"), "--output", str(archive)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                self.assertIn("clean-voice/SKILL.md", names)
                self.assertIn("clean-voice/scripts/worker.py", names)
                self.assertFalse(any(name.endswith((".wav", ".m4a", ".pt", ".safetensors", ".pyc")) for name in names))


if __name__ == "__main__":
    unittest.main()
